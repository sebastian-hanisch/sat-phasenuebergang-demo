"""Die kopierten Bausteine aus Stück 3 (Entscheidung 2026-10-21: wörtlich kopieren, Quelle im Kopf der Datei): Vergleich mit dem Original, solange es im Portfolio-Ordner liegt."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SOURCES = {"sph_dpll.py": ("reduktionskette-demo", "red_dpll.py"), "sph_scenario.py": ("reduktionskette-demo", "red_scenario.py")}


@pytest.mark.parametrize("copy", list(SOURCES))
def test_copy_is_verbatim_apart_from_the_header(copy):
    folder, original = SOURCES[copy]
    source = ROOT.parent / folder / original
    if not source.exists():
        pytest.skip("Original liegt nicht im Portfolio-Ordner")
    mine = (ROOT / copy).read_text(encoding="utf-8").splitlines()
    assert mine[0].startswith(f"# Wörtliche Kopie von {folder}/{original}")
    assert mine[1:] == source.read_text(encoding="utf-8").splitlines(), "die Kopie weicht vom Original ab: Änderungen gehören ins Original, danach neu kopieren"


def test_copied_dpll_still_decides_the_pigeonhole_formulas():
    """Die Kopie läuft für sich (Schubfach-Knotenzahlen aus Stück 3): 3, 11, 47 Knoten für h = 2, 3, 4."""
    import sph_dpll as D
    from sph_structure import pigeonhole
    for h, nodes in ((2, 3), (3, 11), (4, 47)):
        clauses, _ = pigeonhole(h)
        r = D.dpll(clauses)
        assert not r.satisfiable and r.nodes == nodes, h
