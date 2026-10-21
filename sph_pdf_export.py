"""PDF-Export (fpdf2, Kernschriften): Einstellungen, Ergebnis der Suche und die Klauseln. Kein Gedankenstrich und kein Euro-Zeichen (Kernschriften)."""

from fpdf import FPDF

import sph_constants as C
import sph_evaluation as ev
from sph_scenario import literal_name


def _text(value: str) -> str:
    """Zeichen, die die Kernschriften nicht kennen, ersetzen (Gedankenstrich, Pfeile, Fettdruck-Markierung, mathematische Zeichen)."""
    table = {"–": "-", "—": "-", "→": "->", "**": "", "€": "EUR", "·": "*", "³": "^3", "≤": "<=", "≥": ">=", "∨": "v", "¬": "-", "∧": "&", "×": "x", "„": '"', "“": '"'}
    for old, new in table.items():
        value = value.replace(old, new)
    return value


def _para(pdf: FPDF, height: float, text: str) -> None:
    """Absatz über die volle Breite; danach steht der Cursor wieder am linken Rand (fpdf2 setzt ihn sonst an den rechten Rand)."""
    pdf.multi_cell(0, height, _text(text), new_x="LMARGIN", new_y="NEXT")


def build_pdf(a: ev.Analysis) -> bytes:
    s, r = a.settings, a.result
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _text("SAT in der Praxis: DPLL und Phasenübergang"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    _para(pdf, 5.5, f"Variablen: {s.n}   Klauseln: {s.m}   Verhältnis m/n: {ev.fmt_num(s.m / s.n)}   Zufalls-Seed: {s.seed}\n"
                    f"Einheitspropagation: {'an' if s.units else 'aus'}   Verzweigungsregel: {C.RULES[s.rule]}   Knotenbudget: {ev.fmt_int(s.budget)}")
    pdf.ln(1)
    kind, verdict = ev.verdict_run(a)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Ergebnis", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    _para(pdf, 5.5, verdict)
    if r.assignment is not None:
        values = ", ".join(f"x{v}={'wahr' if val else 'falsch'}" for v, val in sorted(r.assignment.items()))
        _para(pdf, 5.5, "Gefundene Belegung (nicht genannte Variablen sind frei): " + values)
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Klauseln", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for i, clause in enumerate(a.formula[:150]):
        _para(pdf, 4.8, f"{i + 1}: (" + " v ".join(literal_name(lit) for lit in clause) + ")")
    if len(a.formula) > 150:
        _para(pdf, 4.8, f"... und {len(a.formula) - 150} weitere Klauseln")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    _para(pdf, 4.5, "Aufwand in Knoten der Suche, nicht in Sekunden. Sebastian Hanisch - Operations Research und Machine Learning.")
    return bytes(pdf.output())
