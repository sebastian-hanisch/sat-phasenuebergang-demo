"""Schubfach-Formeln, Vorzeichen-Störung und Umbenennung."""

import pytest

import sph_search as S
from sph_scenario import random_formula
from sph_structure import perturb, pigeonhole, rename_variables


def test_pigeonhole_sizes_by_hand():
    f, nv = pigeonhole(2)                           # 3 Tauben, 2 Fächer: 6 Variablen, 3 lange + 2 · 3 kurze Klauseln
    assert nv == 6 and len(f) == 9 and f[:3] == [(1, 2), (3, 4), (5, 6)] and (-1, -3) in f and (-2, -6) in f
    f, nv = pigeonhole(5)
    assert nv == 30 and len(f) == 6 + 5 * 15


def test_pigeonhole_is_unsatisfiable_with_known_node_counts():
    assert S.brute_force_sat(6, pigeonhole(2)[0]) is None and S.brute_force_sat(12, pigeonhole(3)[0]) is None
    for h, nodes in {2: 3, 3: 11, 4: 47, 5: 239, 6: 1439}.items():
        r = S.solve(pigeonhole(h)[0])
        assert r.satisfiable is False and r.nodes == nodes, h


def test_perturb_boundaries_and_determinism():
    f = random_formula(10, 20, 3)
    assert perturb(f, 0, 1) == f
    assert perturb(f, 1000, 1) == [tuple(-lit for lit in c) for c in f]
    assert perturb(f, 100, 5) == perturb(f, 100, 5) and perturb(f, 100, 5) != perturb(f, 100, 6)
    with pytest.raises(ValueError):
        perturb(f, 1001, 1)
    with pytest.raises(ValueError):
        perturb(f, -1, 1)


def test_perturb_flips_about_the_requested_share():
    f = random_formula(30, 400, 2)                  # 1 200 Literale
    g = perturb(f, 100, 9)
    flipped = sum(a != b for ca, cb in zip(f, g) for a, b in zip(ca, cb))
    assert 80 < flipped < 160                       # 10 % von 1 200 = 120
    assert all(abs(a) == abs(b) for ca, cb in zip(f, g) for a, b in zip(ca, cb))       # nur Vorzeichen, nie die Variable


def test_perturb_can_change_the_answer():
    """Die Störung ist keine Glättung desselben Problems: eine unerfüllbare Schubfach-Formel wird bei kleiner Störung erfüllbar."""
    base, nv = pigeonhole(5)
    assert S.solve(base).satisfiable is False
    answers = [S.solve(perturb(base, 10, seed)).satisfiable for seed in range(10)]
    assert True in answers                          # mindestens eine Störung ändert die Antwort (nicht jede: manchmal fällt kein Umdrehen auf eine wirksame Stelle)
    assert all(S.solve(perturb(base, 200, seed)).satisfiable is not None for seed in range(3))


def test_rename_variables_keeps_the_answer_and_is_a_permutation():
    for seed in range(40):
        n = 4 + seed % 6
        f = random_formula(n, 3 * n, seed)
        g = rename_variables(f, n, seed + 1)
        assert (S.brute_force_sat(n, f) is None) == (S.brute_force_sat(n, g) is None), seed
        assert {abs(lit) for c in g for lit in c} <= set(range(1, n + 1))
        assert [tuple(1 if lit > 0 else -1 for lit in c) for c in f] == [tuple(1 if lit > 0 else -1 for lit in c) for c in g]       # Vorzeichen bleiben
    assert rename_variables([(1, 2, 3)], 3, 5) == rename_variables([(1, 2, 3)], 3, 5)
    assert sorted(abs(x) for x in rename_variables([(1, 2, 3)], 3, 7)[0]) == [1, 2, 3]
