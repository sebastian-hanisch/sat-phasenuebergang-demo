"""Jede Zahl der README steht hier und wird über dieselben Auswertungsfunktionen wie in der App nachgerechnet (DEMO-PLAYBOOK §4).

Alle Formeln kommen aus dem eigenen SplitMix64-Generator (plattform- und versionsunabhängig); Zähler und Mediane sind exakte Werte, Schnittpunkte der Interpolation als Band."""

import pytest

import sph_constants as C
import sph_evaluation as ev
import sph_search as S
from sph_structure import pigeonhole

# --- Befund 1: Phasenübergang ---------------------------------------------------------------------------------------------------------------------

PHASE = {
    20: dict(
        sat=[40, 39, 39, 37, 35, 32, 22, 19, 12, 8, 7, 3, 2],
        median=[8.0, 9.0, 8.0, 12.0, 12.0, 11.5, 14.5, 14.5, 15.0, 14.0, 14.0, 15.0, 15.0],
        max=[18, 19, 26, 31, 25, 27, 30, 23, 27, 25, 23, 23, 25], cross=4.667, peak=(5.0, 15.0)),
    30: dict(
        sat=[40, 40, 40, 39, 36, 27, 20, 13, 10, 7, 3, 2, 0],
        median=[12.0, 11.0, 11.5, 11.5, 14.5, 17.0, 24.5, 30.0, 25.0, 23.0, 24.0, 21.0, 21.0],
        max=[25, 30, 36, 71, 61, 52, 61, 63, 51, 51, 43, 45, 47], cross=4.5, peak=(4.75, 30.0)),
    40: dict(
        sat=[40, 40, 40, 38, 33, 29, 21, 8, 4, 3, 1, 1, 1],
        median=[13.0, 14.0, 15.0, 17.5, 24.0, 38.5, 45.0, 52.5, 50.0, 49.0, 44.0, 41.0, 34.0],
        max=[31, 31, 44, 131, 153, 157, 129, 97, 89, 83, 73, 67, 59], cross=4.519, peak=(4.75, 52.5)),
}


@pytest.fixture(scope="module")
def phase():
    """Die Messreihe läuft einmal je Testlauf (rund 18 Sekunden)."""
    return ev.sweep_phase()


def test_claim_phase_transition_table(phase):
    """README, Phasenübergang (40 feste Formeln je Zelle, m/n = 3,0 bis 6,0 in Schritten von 0,25): erfüllbare Formeln, Median und Maximum der Knoten je Größe."""
    assert list(phase) == [20, 30, 40] and C.PHASE_RATIOS == tuple(3.0 + 0.25 * i for i in range(13))
    for n, expected in PHASE.items():
        rows = phase[n]
        assert [r["sat"] for r in rows] == expected["sat"], n
        assert [r["median"] for r in rows] == expected["median"], n
        assert [r["max"] for r in rows] == expected["max"], n
        assert all(r["count"] == 40 for r in rows)


def test_claim_fifty_percent_crossing_and_peak(phase):
    """README: der 50-%-Schnitt liegt bei n = 20 / 30 / 40 bei m/n = 4,67 / 4,50 / 4,52, die teuerste Suche bei 5,00 / 4,75 / 4,75 (Median 15 / 30 / 52,5 Knoten)."""
    for n, expected in PHASE.items():
        assert ev.crossing(phase[n]) == pytest.approx(expected["cross"], abs=0.01), n
        p = ev.peak(phase[n])
        assert (p["ratio"], p["median"]) == expected["peak"], n
    assert all(ev.crossing(phase[n]) > C.THRESHOLD_PREDICTION for n in phase)        # alle über der Vorhersage 4,27


def test_claim_satisfiable_share_never_rises_with_the_ratio(phase):
    """README: bei gleichem Zufalls-Seed kann „erfüllbar“ nur kippen: der Anteil ist in m/n nicht steigend; bei m/n = 3 sind 40 von 40 (n = 30, 40) bzw. 40 von 40 (n = 20) erfüllbar."""
    for n, rows in phase.items():
        sats = [r["sat"] for r in rows]
        assert sats == sorted(sats, reverse=True), n
        assert rows[0]["sat"] == 40


# --- Befund 2: Wachstum ---------------------------------------------------------------------------------------------------------------------------


def test_claim_growth_of_the_search():
    """README (m/n = 4,5, 20 Formeln je n): Median 14 / 31 / 48 / 84 / 143 / 317 Knoten, Maximum 33 / 55 / 82 / 201 / 329 / 607 für n = 20 bis 70; erfüllbar 14 / 6 / 10 / 6 / 9 / 3 von 20."""
    g = ev.sweep_growth()
    assert [r["n"] for r in g] == [20, 30, 40, 50, 60, 70]
    assert [r["median"] for r in g] == [14.0, 31.0, 48.0, 84.0, 143.0, 317.0]
    assert [r["max"] for r in g] == [33, 55, 82, 201, 329, 607]
    assert [r["sat"] for r in g] == [14, 6, 10, 6, 9, 3]
    assert g[-1]["median"] / g[0]["median"] == pytest.approx(22.64, abs=0.01)         # das 23-Fache


# --- Befund 3: Hebel ------------------------------------------------------------------------------------------------------------------------------


def test_claim_what_a_solver_carries():
    """README (n = 30, m = 128, 20 Formeln, Budget 10.000): Median der Knoten (Abbrüche): an: erste 66, häufigste 19,5, Jeroslow–Wang 13; aus: erste 10.001 (18), häufigste 2.859 (1), Jeroslow–Wang 291 (0)."""
    got = {(r["units"], r["rule"]): (r["median"], r["max"], r["aborted"]) for r in ev.sweep_levers()}
    assert got == {
        (True, "first"): (66.0, 277, 0), (True, "frequent"): (19.5, 47, 0), (True, "jw"): (13.0, 33, 0),
        (False, "first"): (10001.0, 10001, 18), (False, "frequent"): (2859.0, 10001, 1), (False, "jw"): (291.0, 1019, 0),
    }


# --- Befund 4: Struktur, Zufall, Störung ----------------------------------------------------------------------------------------------------------


def test_claim_pigeonhole_without_perturbation():
    """README: Schubfach-Formeln (unerfüllbar): h = 3 bis 6: 11 / 47 / 239 / 1.439 Knoten; eine Zufallsformel (n = 30, m = 150, 10 feste Formeln) braucht im Median 26 Knoten."""
    for h, nodes in {3: 11, 4: 47, 5: 239, 6: 1439}.items():
        r = S.solve(pigeonhole(h)[0])
        assert r.satisfiable is False and r.nodes == nodes
    ref = ev.random_reference()
    assert (ref["n"], ref["m"], ref["count"], ref["median"]) == (30, 150, 10, 26.0)


def test_claim_perturbed_pigeonhole_h5_and_h6():
    """README (10 feste Störungen je Wert): Median der Knoten / erfüllbar bei 0,5 / 1 / 2 / 5 / 10 / 20 / 50 % umgedrehten Vorzeichen; h = 5: 200 (5), 16,5 (10), 5 (10), 5 (10), 8 (10), 8,5 (5), 3 (0); h = 6: 198 (10), 7 (10), 6,5 (10), 8 (10), 14 (10), 11 (0), 3 (0)."""
    h5 = [(r["pm"], r["median"], r["max"], r["sat"]) for r in ev.structure_rows(5)]
    assert h5 == [(0, 239, 239, 0), (5, 200.0, 239, 5), (10, 16.5, 53, 10), (20, 5.0, 17, 10), (50, 5.0, 12, 10), (100, 8.0, 15, 10), (200, 8.5, 15, 5), (500, 3.0, 7, 0)]
    h6 = [(r["pm"], r["median"], r["max"], r["sat"]) for r in ev.structure_rows(6)]
    assert h6 == [(0, 1439, 1439, 0), (5, 198.0, 1205, 10), (10, 7.0, 246, 10), (20, 6.5, 246, 10), (50, 8.0, 18, 10), (100, 14.0, 23, 10), (200, 11.0, 21, 0), (500, 3.0, 5, 0)]


def test_claim_the_perturbation_changes_the_answer():
    """README: schon bei 1 % umgedrehten Vorzeichen sind alle 10 Störungen der Schubfach-Formeln mit 5 und 6 Fächern erfüllbar: die Störung ändert die Antwort (keine Glättung desselben Problems)."""
    for h in (5, 6):
        row = next(r for r in ev.structure_rows(h) if r["pm"] == 10)
        assert row["sat"] == row["count"] == 10


def test_claim_renaming_changes_nodes_but_not_the_median():
    """README (Randnotiz, n = 30, m/n = 4,5, 10 Formeln): die Umbenennung der Variablen ändert die Knotenzahl bei 7 von 10 Formeln, der Median bleibt 29."""
    e = ev.rename_effect()
    assert (e["count"], e["changed"], e["median_before"], e["median_after"]) == (10, 7, 29.0, 29.0)


# --- Presets (Einzelinstanzen) --------------------------------------------------------------------------------------------------------------------


def test_claim_presets_are_single_instances_with_these_values():
    """README, Preset-Tabelle: erfüllbar?, Knoten, Einheitsschritte, Verzweigungen, Sackgassen, Abbruch je Preset."""
    got = {}
    for name, p in C.PRESETS.items():
        r = ev.analyse(ev.Settings(**p)).result
        got[name] = (r.satisfiable, r.nodes, r.units, r.branches, r.dead_ends, r.aborted)
    assert got == {
        "Standardfall (Voreinstellung)": (True, 14, 66, 7, 6, False),
        "Lehrbeispiel (6 Variablen)": (True, 3, 4, 2, 0, False),
        "Locker (m/n = 3)": (True, 8, 24, 6, 1, False),
        "Am Übergang (m/n = 4,5)": (True, 42, 257, 23, 18, False),
        "Überbestimmt (m/n = 6)": (False, 25, 130, 12, 13, False),
        "Ohne Einheitspropagation": (None, 10001, 0, 5006, 4994, True),
        "Schubfach, leicht gestört": (True, 14, 66, 7, 6, False),
    }


def test_claim_h8_is_not_in_the_app_and_unit_is_nodes():
    """README: die App rechnet bis n = 70 (Messreihe) bzw. n = 60 (Regler); Aufwand in Knoten, nie in Sekunden."""
    assert C.N_MAX == 60 and max(C.GROWTH_N) == 70
    text = ev.verdict_run(ev.analyse(ev.Settings()))[1]
    assert "Sekunden" not in text and "Knoten" in text
