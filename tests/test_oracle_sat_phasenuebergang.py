"""Orakel-Test: die DPLL-Varianten und die Messreihen gegen unabhängige Rechenwege (DEMO-PLAYBOOK §12, ORACLE-PLAYBOOK).

- Jede der sechs Varianten (Einheitspropagation an/aus × drei Verzweigungsregeln) gegen Brute Force über alle 2^n Belegungen: Erfüllbarkeit und gefundene Belegung.
- Alle Varianten stimmen in der Antwort überein; die Variante (an, häufigste) hat die Knotenzahl der Kopie aus Stück 3 (Regressions-Test in test_search.py).
- Die Messreihe des Phasenübergangs zählt dieselben erfüllbaren Formeln wie die Brute-Force-Probe, und „erfüllbar“ ist bei gleichem Zufalls-Seed in m nicht steigend.
- Beide Seiten (erfüllbar UND unerfüllbar) werden ausgeführt. Im Repo laufen kleine Fassungen (unter 10 s); der große Lauf im Scratch-Ordner ist in der README genannt."""

import itertools

import pytest

import sph_evaluation as ev
import sph_search as S
from sph_scenario import random_formula
from sph_structure import perturb, pigeonhole, rename_variables

VARIANTS = [(units, rule) for units in (True, False) for rule in S.RULES]


def test_every_variant_matches_brute_force_and_returns_a_model():
    unsat = sat = 0
    for seed in range(120):
        n = 3 + seed % 6
        f = random_formula(n, 1 + (seed * 7) % (7 * n), 3000 + seed)
        truth = S.brute_force_sat(n, f) is not None
        sat += truth
        unsat += not truth
        for units, rule in VARIANTS:
            r = S.solve(f, units, rule, budget=200_000)
            assert not r.aborted and r.satisfiable == truth, (n, seed, units, rule)
            if truth:
                assert S.is_satisfying(f, r.assignment), (n, seed, units, rule)
            else:
                assert r.assignment is None
    assert sat > 10 and unsat > 10, (sat, unsat)


def test_pigeonhole_and_its_perturbations_match_brute_force():
    base, nv = pigeonhole(3)                                                  # 12 Variablen: alle Belegungen aufzählbar
    for pm in (0, 10, 100, 300, 1000):
        for seed in range(6):
            f = perturb(base, pm, seed)
            truth = S.brute_force_sat(nv, f) is not None
            for units, rule in VARIANTS:
                assert S.solve(f, units, rule).satisfiable == truth, (pm, seed, units, rule)


def test_renaming_keeps_the_answer_for_every_variant():
    for seed in range(30):
        n = 4 + seed % 5
        f = random_formula(n, 4 * n, 700 + seed)
        g = rename_variables(f, n, seed)
        for units, rule in VARIANTS:
            assert S.solve(f, units, rule).satisfiable == S.solve(g, units, rule).satisfiable, (n, seed, units, rule)


def test_phase_sweep_counts_the_same_satisfiable_formulas_as_brute_force():
    seeds = tuple(range(25))
    by_n = ev.sweep_phase(sizes=(8,), ratios=(3.0, 4.0, 5.0, 6.0), seeds=seeds, budget=50_000)
    for row in by_n[8]:
        brute = sum(S.brute_force_sat(8, random_formula(8, row["m"], seed)) is not None for seed in seeds)
        assert row["sat"] == brute, row
    sats = [r["sat"] for r in by_n[8]]
    assert sats == sorted(sats, reverse=True) and sats[0] > sats[-1]


def test_satisfiability_is_monotone_in_the_number_of_clauses():
    """Bei gleichem Zufalls-Seed ist die Formel mit m Klauseln ein Anfang der mit m + 1: erfüllbar kann nur kippen, nie zurückkehren."""
    for seed in range(40):
        n = 7
        answers = [S.solve(random_formula(n, m, seed)).satisfiable for m in range(1, 50)]
        first_false = answers.index(False) if False in answers else len(answers)
        assert all(a is True for a in answers[:first_false]) and all(a is False for a in answers[first_false:]), seed


def test_growth_and_lever_rows_count_the_runs_they_report():
    lev = ev.sweep_levers(n=10, m=43, seeds=tuple(range(6)), budget=3_000)
    for row in lev:
        nodes = [S.solve(random_formula(10, 43, s), row["units"], row["rule"], 3_000).nodes for s in range(6)]
        assert row["median"] == sorted(nodes)[2:4][0] / 2 + sorted(nodes)[2:4][1] / 2 and row["max"] == max(nodes)
    g = ev.sweep_growth(sizes=(12,), ratio=4.5, seeds=tuple(range(5)), budget=10_000)[0]
    nodes = sorted(S.solve(random_formula(12, 54, s), True, "frequent", 10_000).nodes for s in range(5))
    assert g["median"] == nodes[2] and g["max"] == nodes[-1]
    assert g["sat"] == sum(S.brute_force_sat(12, random_formula(12, 54, s)) is not None for s in range(5))
