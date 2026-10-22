"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier."""

import sph_evaluation as ev
import sph_search as S


def _analysis(result, n=2, m=9, **settings):
    return ev.Analysis(ev.Settings(n=n, m=m, **settings), tuple([(1, 2, 3)] * m), result)


def _result(sat, nodes, aborted=False, units=0, branches=0, dead=0):
    return S.SearchResult(sat, {} if sat else None, nodes, aborted, units, branches, dead)


def test_run_verdict_satisfiable_names_ratio_and_statistics():
    kind, text = ev.verdict_run(_analysis(_result(True, 14, units=66, branches=7, dead=6)))
    assert kind == "success" and "**erfüllbar**" in text and "m/n = 4,5" in text
    assert "14 Knoten: 7 Verzweigungen, 6 Sackgassen und 66 erzwungene Einheitsschritte" in text


def test_run_verdict_unsatisfiable_is_an_info():
    kind, text = ev.verdict_run(_analysis(_result(False, 1_234, units=2, branches=0, dead=1), n=3, m=18))
    assert kind == "info" and "**unerfüllbar**" in text and "m/n = 6,0" in text and "1.234 Knoten" in text


def test_run_verdict_aborted_is_a_warning_with_the_budget():
    kind, text = ev.verdict_run(_analysis(_result(None, 10_001, aborted=True), budget=10_000))
    assert kind == "warning" and "Knotenbudget von 10.000 reicht nicht" in text and "nach 10.001 Knoten ab" in text and "sagt nichts über die Formel" in text


def _rows(n, ratios, sats, medians):
    return [{"n": n, "ratio": r, "count": 40, "sat": s, "median": md, "max": md + 1} for r, s, md in zip(ratios, sats, medians)]


def test_phase_verdict_with_hand_values():
    by_n = {20: _rows(20, (3.0, 4.5, 6.0), (40, 20, 2), (8, 14, 15)), 30: _rows(30, (3.0, 4.5, 6.0), (40, 30, 0), (10, 30, 20))}
    kind, text = ev.verdict_phase(by_n)
    assert kind == "info"
    assert "Bei m/n = 3,0 sind 100 % der Formeln erfüllbar, bei m/n = 6,0 nur 0 bis 5 %" in text
    assert "bei n = 20 / 30 bei m/n = 4,50 / 5,00" in text and "4,27" in text and "nicht bewiesen" in text
    assert "bei n = 30 bei m/n = 4,50 (Median 30 Knoten)" in text


def test_phase_verdict_shows_a_dash_when_there_is_no_crossing():
    by_n = {20: _rows(20, (3.0, 6.0), (40, 40), (8, 9))}
    assert "bei m/n = –" in ev.verdict_phase(by_n)[1]


def test_growth_verdict_with_hand_values():
    rows = [{"n": 20, "median": 14.0}, {"n": 70, "median": 317.0}]
    kind, text = ev.verdict_growth(rows)
    assert kind == "info" and "Beim Verhältnis 4,5" in text
    assert "im Median 14 Knoten bei n = 20 und 317 bei n = 70" in text and "das 23-Fache" in text and "×1,9 je zehn zusätzliche Variablen" in text and "über 2 Größen" in text


def _lever(units, rule, median, aborted, count=20):
    return {"units": units, "rule": rule, "median": median, "max": median, "aborted": aborted, "count": count}


def test_levers_verdict_with_hand_values():
    rows = [_lever(True, "first", 66.0, 0), _lever(True, "frequent", 19.5, 0), _lever(True, "jw", 13.0, 0),
            _lever(False, "first", 10001.0, 18), _lever(False, "frequent", 2859.0, 1), _lever(False, "jw", 291.0, 0)]
    kind, text = ev.verdict_levers(rows)
    assert kind == "info"
    assert "im Median 10.001 statt 66 Knoten" in text and "Faktor 152 (untere Schranke" in text and "18 von 20 Läufen am Budget abgebrochen" in text
    assert "von 66 auf 13 Knoten (Faktor 5,1)" in text


def test_levers_verdict_without_aborts_has_no_lower_bound_note():
    rows = [_lever(True, "first", 60.0, 0), _lever(True, "frequent", 20.0, 0), _lever(True, "jw", 10.0, 0),
            _lever(False, "first", 600.0, 0), _lever(False, "frequent", 200.0, 0), _lever(False, "jw", 100.0, 0)]
    text = ev.verdict_levers(rows)[1]
    assert "Faktor 10" in text and "untere Schranke" not in text and "0 von 20 Läufen" in text


def test_structure_verdict_unperturbed_and_perturbed():
    ref = {"n": 30, "m": 150, "median": 26.0}
    kind, text = ev.verdict_structure({"pm": 0, "median": 239, "count": 1, "sat": 0}, 239, 5, ref)
    assert kind == "info" and "mit 5 Fächern (6 Tauben)" in text and "**unerfüllbar** und braucht 239 Knoten" in text and "n = 30, m = 150" in text and "im Median 26 Knoten" in text
    kind, text = ev.verdict_structure({"pm": 10, "median": 17.0, "count": 10, "sat": 10}, 239, 5, ref)
    assert "Bei 1 % umgedrehten Vorzeichen" in text and "im Median 17 statt 239 Knoten" in text and "10 von 10 Störungen sind **erfüllbar**" in text
    assert "macht die Formel also leicht" in text and "ändert dabei aber ihre Antwort" in text and "keine Glättung" in text
    text = ev.verdict_structure({"pm": 5, "median": 200.0, "count": 10, "sat": 5}, 239, 5, ref)[1]
    assert "Bei 0,5 %" in text and "noch kaum leichter" in text and "ändert dabei aber oft ihre Antwort" in text
    text = ev.verdict_structure({"pm": 500, "median": 3.0, "count": 10, "sat": 0}, 239, 5, ref)[1]
    assert "macht die Formel also leicht" in text and "alle bleiben unerfüllbar" in text and "ändert dabei" not in text
