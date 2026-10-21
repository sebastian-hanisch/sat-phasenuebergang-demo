"""Gemeinsame Fixtures: Mini-Formeln, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def chain():
    """(x1) ∧ (¬x1 ∨ x2) ∧ (¬x2): unerfüllbar.

    Handrechnung mit Einheitspropagation: x1 wird erzwungen, dann x2, dann ist (¬x2) leer: ein Knoten, zwei erzwungene Schritte, eine Sackgasse an der Wurzel.
    Ohne Einheitspropagation (Regel erste/häufigste/Jeroslow–Wang, alle wählen x1 zuerst wahr): Wurzel verzweigt auf x1; x1 = wahr (Knoten 2) lässt (x2) und (¬x2) offen und verzweigt auf x2;
    x2 = wahr (Knoten 3) und x2 = falsch (Knoten 4) enden in Sackgassen; x1 = falsch (Knoten 5) ist eine Sackgasse: 5 Knoten, 2 Verzweigungen, 3 Sackgassen."""
    return [(1,), (-1, 2), (-2,)]


@pytest.fixture
def square():
    """(x1 ∨ x2) ∧ (¬x1 ∨ x2) ∧ (x1 ∨ ¬x2) ∧ (¬x1 ∨ ¬x2): unerfüllbar (alle Vorzeichenmuster über zwei Variablen).

    Handrechnung mit Einheitspropagation: Wurzel verzweigt auf x1 (beide Variablen kommen je viermal vor, Gleichstand: kleinere Nummer); x1 = wahr erzwingt x2 = wahr und scheitert an (¬x1 ∨ ¬x2),
    x1 = falsch ebenso: 3 Knoten. Ohne Einheitspropagation: x1 = wahr lässt (x2), (¬x2) offen, verzweigt auf x2 und scheitert zweimal (Knoten 2 bis 4), x1 = falsch ebenso (Knoten 5 bis 7): 7 Knoten."""
    return [(1, 2), (-1, 2), (1, -2), (-1, -2)]


@pytest.fixture
def branchy():
    """(x1 ∨ x2) ∧ (¬x2 ∨ x3) ∧ (¬x2 ∨ ¬x3): erfüllbar, nur mit x2 = falsch und dann x1 = wahr.

    Handrechnung mit Einheitspropagation (alle Klauseln haben Länge 2, an der Wurzel keine Einheitsklausel):
    - erste Variable: x1 = wahr (Knoten 2), dann auf x2 verzweigen: x2 = wahr (Knoten 3) erzwingt x3 und scheitert an (¬x3); x2 = falsch (Knoten 4) erfüllt alles: 4 Knoten.
    - häufigste Variable: x2 kommt dreimal vor: x2 = wahr scheitert sofort (Knoten 2), x2 = falsch erzwingt x1 und löst (Knoten 3): 3 Knoten.
    - Jeroslow–Wang: x2 trägt das größte Gewicht (0,75), das negative Vorzeichen mehr (0,5 gegen 0,25), also zuerst x2 = falsch: erzwingt x1 und löst, 2 Knoten.
    Ohne Einheitspropagation, Regel erste Variable: x1 = wahr (Knoten 2); x2 = wahr (Knoten 3) lässt (x3), (¬x3) offen und verzweigt auf x3: Knoten 4 und 5 scheitern; x2 = falsch (Knoten 6) löst: 6 Knoten."""
    return [(1, 2), (-2, 3), (-2, -3)]
