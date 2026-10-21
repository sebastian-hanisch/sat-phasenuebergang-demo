"""Kennzahlen, Prüfung vor der Anzeige, Messreihen-Funktionen an kleinen Läufen und Handwerten."""

import dataclasses

import pytest

import sph_constants as C
import sph_evaluation as ev
import sph_search as S
from sph_scenario import random_formula


def test_number_formats():
    assert ev.fmt_int(999) == "999" and ev.fmt_int(1000) == "1.000" and ev.fmt_int(1720350) == "1.720.350"
    assert ev.fmt_num(22.66) == "22,7" and ev.fmt_num(4.5, 2) == "4,50"
    assert ev.fmt_pm(5) == "0,5 %" and ev.fmt_pm(10) == "1 %" and ev.fmt_pm(0) == "0 %" and ev.fmt_pm(200) == "20 %"
    assert ev.fmt_median(52.5) == "52,5" and ev.fmt_median(14.0) == "14" and ev.fmt_median(1306.0) == "1.306" and ev.fmt_median(19.5) == "19,5"
    assert ev.pct_range([1.0, 1.0]) == "100 %" and ev.pct_range([0.0, 0.05]) == "0 bis 5 %" and ev.pct_range([0.4, 0.75, 0.5]) == "40 bis 75 %"
    assert ev.fmt_share(1, 40) == "2,5 %" and ev.fmt_percent(7.0) == "7" and ev.fmt_percent(0.0) == "0"
    assert ev.fmt_share(28, 40) == "70 %" and ev.fmt_share(0, 40) == "0 %" and ev.fmt_share(40, 40) == "100 %"


def test_settings_are_keyword_only():
    with pytest.raises(TypeError):
        ev.Settings(20, 90, 35)                                  # nie positional (Memory feedback_settings_dataclass_keyword_args)


def test_default_analysis_is_consistent():
    a = ev.analyse(ev.Settings())
    assert a.result.satisfiable is not None and not a.result.aborted and ev.validation_errors(a) == []
    assert len(a.formula) == C.DEFAULT_M and a == ev.analyse(ev.Settings())


def test_analysis_records_the_tree_for_small_runs_only():
    small = ev.analyse(ev.Settings(n=6, m=14, seed=1))
    assert small.result.tree and not small.result.tree_truncated and len(small.result.tree) == small.result.nodes
    big = ev.analyse(ev.Settings(n=30, m=128, seed=35, units=False, rule="first", budget=C.BUDGETS[1]))
    assert big.result.aborted and big.result.tree_truncated and len(big.result.tree) == C.TREE_LIMIT


def test_validation_catches_broken_results():
    a = ev.analyse(ev.Settings(n=8, m=20, seed=3))
    assert ev.validation_errors(a) == []
    liar = dataclasses.replace(a, result=dataclasses.replace(a.result, satisfiable=not a.result.satisfiable))
    assert any("Brute-Force" in e or "erfüllt die Formel nicht" in e for e in ev.validation_errors(liar))
    bad_model = dataclasses.replace(a, result=dataclasses.replace(a.result, satisfiable=True, assignment={v: False for v in range(1, 9)}))
    errors = ev.validation_errors(bad_model)
    assert errors and all(isinstance(e, str) for e in errors)
    broken_count = dataclasses.replace(a, result=dataclasses.replace(a.result, nodes=a.result.nodes + 5))
    assert any("Knotenstatistik" in e for e in ev.validation_errors(broken_count))


def test_validation_is_skipped_for_aborted_runs_and_large_n():
    aborted = ev.analyse(ev.Settings(n=30, m=128, seed=35, units=False, rule="first", budget=C.BUDGETS[0]))
    assert aborted.result.aborted and ev.validation_errors(aborted) == []
    big = ev.analyse(ev.Settings(n=60, m=270, seed=2))
    assert ev.validation_errors(big) == []


def test_crossing_by_hand():
    rows = [{"ratio": 4.0, "sat": 8, "count": 10}, {"ratio": 5.0, "sat": 2, "count": 10}]
    assert ev.crossing(rows) == pytest.approx(4.5)                       # 0,8 -> 0,2: 50 % in der Mitte
    assert ev.crossing([{"ratio": 3.0, "sat": 10, "count": 10}, {"ratio": 4.0, "sat": 10, "count": 10}]) is None      # fällt nie unter 50 %
    assert ev.crossing([{"ratio": 3.0, "sat": 4, "count": 10}, {"ratio": 4.0, "sat": 1, "count": 10}]) is None        # beginnt schon darunter
    exact = [{"ratio": 3.0, "sat": 10, "count": 10}, {"ratio": 4.0, "sat": 5, "count": 10}, {"ratio": 5.0, "sat": 0, "count": 10}]
    assert ev.crossing(exact) == pytest.approx(4.0)                      # genau 50 % bei 4,0: der Schnitt liegt dort, nicht bei 3,0


def test_peak_by_hand():
    rows = [{"ratio": 3.0, "median": 5}, {"ratio": 4.0, "median": 9}, {"ratio": 5.0, "median": 9}, {"ratio": 6.0, "median": 2}]
    assert ev.peak(rows)["ratio"] == 4.0                                  # bei Gleichstand das kleinere Verhältnis


def test_sweep_phase_structure_and_monotonicity():
    by_n = ev.sweep_phase(sizes=(8,), ratios=(3.0, 4.5, 6.0), seeds=tuple(range(20)), budget=10_000)
    rows = by_n[8]
    assert [r["m"] for r in rows] == [24, 36, 48] and all(r["count"] == 20 for r in rows)
    assert rows[0]["sat"] >= rows[1]["sat"] >= rows[2]["sat"]            # erfüllbar ist in m nicht steigend (Präfix-Formeln)
    assert all(r["median"] >= 1 and r["max"] >= r["median"] for r in rows)


def test_sweep_growth_levers_and_structure_on_tiny_runs():
    g = ev.sweep_growth(sizes=(10, 20), ratio=4.5, seeds=(1, 2, 3), budget=5_000)
    assert [r["n"] for r in g] == [10, 20] and all(r["count"] == 3 and 0 <= r["sat"] <= 3 for r in g)
    lev = ev.sweep_levers(n=10, m=43, seeds=(1, 2), budget=2_000)
    assert [(r["units"], r["rule"]) for r in lev] == [(u, k) for u in (True, False) for k in S.RULES] and all(r["count"] == 2 for r in lev)
    st_rows = ev.structure_rows(3, per_milles=(0, 10, 500), seeds=(1, 2), budget=5_000)
    assert [r["pm"] for r in st_rows] == [0, 10, 500] and st_rows[0]["count"] == 1 and st_rows[0]["sat"] == 0 and st_rows[1]["count"] == 2
    assert st_rows[0]["median"] == 11                                    # h = 3: 11 Knoten (Stück 3)


def test_rename_effect_and_reference_structure():
    e = ev.rename_effect(n=12, seeds=(1, 2, 3))
    assert e["count"] == 3 and 0 <= e["changed"] <= 3
    ref = ev.random_reference((12, 40, (1, 2, 3)), budget=5_000)
    assert ref["count"] == 3 and ref["median"] >= 1
