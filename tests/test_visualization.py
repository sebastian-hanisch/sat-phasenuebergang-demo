"""Abbildungen: Baumpositionen, Farben, gesperrte Achsen; PDF baut mit Umlauten und bei Abbruch."""

import sph_constants as C
import sph_evaluation as ev
import sph_search as S
import sph_visualization as V
from sph_pdf_export import build_pdf


def test_tree_positions_by_hand(branchy):
    tree = S.solve(branchy, True, "frequent", trace_limit=20).tree                   # Wurzel, zwei Kinder (3 Knoten)
    pos = V.tree_positions(tree)
    assert pos == {1: (0.0, -1.0), 2: (1.0, -1.0), 0: (0.5, 0.0)}                    # Blätter nummeriert, Wurzel in der Mitte, y = -Tiefe


def test_tree_positions_of_a_deeper_tree(square):
    tree = S.solve(square, False, "first", trace_limit=20).tree                      # 7 Knoten: Wurzel, zwei Kinder, vier Enkel
    pos = V.tree_positions(tree)
    assert len(pos) == 7 and sorted(x for x, _ in pos.values() if _ == -2.0) == [0.0, 1.0, 2.0, 3.0]
    assert pos[0][1] == 0.0 and pos[0][0] == sum(pos[i][0] for i in (1, 4)) / 2


def test_tree_figure_colors_statuses_and_locks_axes(branchy):
    fig = V.build_tree(S.solve(branchy, True, "frequent", trace_limit=20).tree)
    names = [t.name for t in fig.data[1:]]
    assert names == ["verzweigt", "Sackgasse", "gelöst"]
    assert [t.marker.color for t in fig.data[1:]] == [C.COLOR_BRANCH, C.COLOR_DEAD, C.COLOR_SOLVED]
    assert len(fig.layout.annotations) == 2 and {a.text for a in fig.layout.annotations} == {"x2", "¬x2"}
    assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_tree_figure_marks_an_aborted_run(chain):
    fig = V.build_tree(S.solve(chain, False, "first", budget=3, trace_limit=20).tree)
    assert "Budget erreicht" in [t.name for t in fig.data]


def test_charts_lock_their_axes_and_have_the_expected_series():
    phase = ev.sweep_phase(sizes=(8, 10), ratios=(3.0, 4.5), seeds=(1, 2, 3), budget=5_000)
    growth = ev.sweep_growth(sizes=(10, 20), seeds=(1, 2), budget=5_000)
    struct = ev.structure_rows(3, per_milles=(0, 10, 500), seeds=(1, 2), budget=5_000)
    ref = ev.random_reference((12, 40, (1, 2)), budget=5_000)
    figs = (V.build_phase_share(phase), V.build_phase_nodes(phase), V.build_growth(growth), V.build_structure(struct, struct[0]["median"], ref))
    for fig in figs:
        assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange
    assert len(figs[0].data) == 2 and len(figs[1].data) == 2 and len(figs[2].data) == 2 and len(figs[3].data) == 1
    assert figs[2].layout.yaxis.type == "log" and figs[3].layout.yaxis.type == "log" and figs[3].layout.xaxis.type == "log"
    assert list(figs[3].data[0].x) == [1.0, 50.0]                                      # nur gestörte Werte (> 0), in Prozent


def test_pdf_builds_for_satisfiable_unsatisfiable_and_aborted_runs():
    sat = build_pdf(ev.analyse(ev.Settings()))
    assert sat[:5] == b"%PDF-" and len(sat) > 1000
    assert build_pdf(ev.analyse(ev.Settings(**C.PRESETS["Überbestimmt (m/n = 6)"])))[:5] == b"%PDF-"
    assert build_pdf(ev.analyse(ev.Settings(**C.PRESETS["Ohne Einheitspropagation"])))[:5] == b"%PDF-"
    assert build_pdf(ev.analyse(ev.Settings(n=C.N_MAX, m=C.M_MAX)))[:5] == b"%PDF-"        # mehr als 150 Klauseln
