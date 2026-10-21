"""Kennzahlen, Messreihen und Verdikte (alle Verdikte sind reine Funktionen (Art, Text), DEMO-PLAYBOOK §12)."""

from dataclasses import dataclass
from statistics import median

import sph_constants as C
import sph_search as S
from sph_scenario import random_formula
from sph_structure import perturb, pigeonhole


@dataclass(frozen=True, kw_only=True)
class Settings:
    n: int = C.DEFAULT_N
    m: int = C.DEFAULT_M
    seed: int = C.DEFAULT_SEED
    units: bool = C.DEFAULT_UNITS
    rule: str = C.DEFAULT_RULE
    budget: int = C.DEFAULT_BUDGET
    h: int = C.DEFAULT_H
    pm: int = C.DEFAULT_PER_MILLE


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    formula: tuple
    result: S.SearchResult


# --- Zahlen im deutschen Format ------------------------------------------------------------------------------------------------------------------


def fmt_int(n: int) -> str:
    """Ganze Zahl mit Punkt als Tausendertrenner (1.720.350)."""
    return f"{n:,}".replace(",", ".")


def fmt_num(x: float, digits: int = 1) -> str:
    """Dezimalzahl mit Komma (22,7)."""
    return f"{x:.{digits}f}".replace(".", ",")


def fmt_median(x: float) -> str:
    """Median als ganze Zahl, wenn er eine ist, sonst mit einer Nachkommastelle und Komma (52,5; nie stillschweigend gerundet)."""
    return fmt_int(int(x)) if x == int(x) else fmt_num(x, 1)


def fmt_percent(x: float) -> str:
    """Prozentzahl ohne Nachkommastelle, wenn sie ganz ist, sonst mit einer und Komma (2,5; nie stillschweigend gerundet)."""
    return fmt_int(int(x)) if x == int(x) else fmt_num(x, 1)


def pct_range(shares: list[float]) -> str:
    """Anteile (0 bis 1) als „100 %“ bei gleichen Werten, sonst „0 bis 5 %“."""
    lo, hi = fmt_percent(100 * min(shares)), fmt_percent(100 * max(shares))
    return f"{lo} %" if lo == hi else f"{lo} bis {hi} %"


def fmt_pm(pm: int) -> str:
    """Promille als Prozent mit Komma und ohne überflüssige Nachkommastelle (5 -> „0,5 %“, 10 -> „1 %“)."""
    return f"{pm / 10:g}".replace(".", ",") + " %"


def fmt_share(count: int, total: int) -> str:
    """Anteil als Prozentzahl (28 von 40 = 70 %, 1 von 40 = 2,5 %)."""
    return f"{fmt_percent(100 * count / total)} %"


# --- Einzelanalyse -------------------------------------------------------------------------------------------------------------------------------


def analyse(settings: Settings) -> Analysis:
    formula = tuple(random_formula(settings.n, settings.m, settings.seed))
    result = S.solve(formula, settings.units, settings.rule, settings.budget, trace_limit=C.TREE_LIMIT)
    return Analysis(settings, formula, result)


def validation_errors(a: Analysis) -> list[str]:
    """Ergebnis vor der Anzeige prüfen (DEMO-PLAYBOOK §1d): eine gemeldete Belegung erfüllt die Formel; bei n <= 16 stimmt die Antwort mit der Brute-Force-Probe überein."""
    errors = []
    r = a.result
    if r.satisfiable and not S.is_satisfying(a.formula, r.assignment):
        errors.append("Die gemeldete Belegung erfüllt die Formel nicht.")
    if a.settings.n <= 16 and not r.aborted:
        truth = S.brute_force_sat(a.settings.n, a.formula) is not None
        if truth != r.satisfiable:
            errors.append("Die Antwort der Suche widerspricht der Brute-Force-Probe.")
    if r.nodes != r.branches + r.dead_ends + (1 if r.satisfiable else 0) and not r.aborted:
        errors.append("Die Knotenstatistik ist nicht stimmig.")
    return errors


# --- Messreihen ----------------------------------------------------------------------------------------------------------------------------------


def sweep_phase(sizes=C.PHASE_N, ratios=C.PHASE_RATIOS, seeds=C.SWEEP_SEEDS, budget: int = C.PHASE_BUDGET) -> dict[int, list[dict]]:
    """Anteil erfüllbarer Formeln und Knoten der Suche über das Verhältnis m/n, je Größe n (feste Formeln; gleiche Seeds über alle m: die Formel wächst, Klauseln kommen dazu)."""
    out: dict[int, list[dict]] = {}
    for n in sizes:
        rows = []
        for ratio in ratios:
            m = round(ratio * n)
            sat, nodes = 0, []
            for seed in seeds:
                r = S.solve(random_formula(n, m, seed), True, "frequent", budget)
                sat += bool(r.satisfiable)
                nodes.append(r.nodes)
            rows.append({"n": n, "ratio": ratio, "m": m, "count": len(seeds), "sat": sat, "median": median(nodes), "max": max(nodes)})
        out[n] = rows
    return out


def crossing(rows: list[dict]) -> float | None:
    """Verhältnis, bei dem der Anteil erfüllbarer Formeln durch 50 % fällt (lineare Interpolation zwischen zwei Messpunkten); None, wenn er nie von ≥ 50 % auf < 50 % fällt."""
    for a, b in zip(rows, rows[1:]):
        fa, fb = a["sat"] / a["count"], b["sat"] / b["count"]
        if fa >= 0.5 > fb:
            return a["ratio"] + (fa - 0.5) / (fa - fb) * (b["ratio"] - a["ratio"])
    return None


def peak(rows: list[dict]) -> dict:
    """Die Zeile mit dem größten Median der Knoten (bei Gleichstand das kleinere Verhältnis)."""
    return max(rows, key=lambda r: (r["median"], -r["ratio"]))


def sweep_growth(sizes=C.GROWTH_N, ratio: float = C.GROWTH_RATIO, seeds=C.GROWTH_SEEDS, budget: int = C.GROWTH_BUDGET) -> list[dict]:
    """Knoten der Suche über n beim festen Verhältnis m/n (Median und Maximum über feste Formeln)."""
    rows = []
    for n in sizes:
        nodes, sat = [], 0
        for seed in seeds:
            r = S.solve(random_formula(n, round(ratio * n), seed), True, "frequent", budget)
            nodes.append(r.nodes)
            sat += bool(r.satisfiable)
        rows.append({"n": n, "count": len(seeds), "sat": sat, "median": median(nodes), "max": max(nodes)})
    return rows


def sweep_levers(n: int = C.LEVER_N, m: int = C.LEVER_M, seeds=C.LEVER_SEEDS, budget: int = C.LEVER_BUDGET) -> list[dict]:
    """Knoten der Suche je Variante (Einheitspropagation an/aus × Verzweigungsregel) auf denselben Formeln; abgebrochene Läufe zählen mit dem Budget."""
    rows = []
    for units in (True, False):
        for rule in S.RULES:
            nodes, aborted = [], 0
            for seed in seeds:
                r = S.solve(random_formula(n, m, seed), units, rule, budget)
                nodes.append(r.nodes)
                aborted += r.aborted
            rows.append({"units": units, "rule": rule, "count": len(seeds), "median": median(nodes), "max": max(nodes), "aborted": aborted})
    return rows


def structure_rows(h: int, per_milles=C.PER_MILLE, seeds=C.STRUCT_SEEDS, budget: int = C.STRUCT_BUDGET) -> list[dict]:
    """Schubfach-Formel mit h Fächern, jedes Literal mit Wahrscheinlichkeit pm/1000 umgedreht: Median der Knoten, Anteil erfüllbarer Störungen (mehrere feste Störungen je Wert)."""
    base, _ = pigeonhole(h)
    rows = []
    for pm in per_milles:
        nodes, sat, aborted = [], 0, 0
        for seed in (seeds if pm else seeds[:1]):
            r = S.solve(perturb(base, pm, seed), True, "frequent", budget)
            nodes.append(r.nodes)
            sat += bool(r.satisfiable)
            aborted += r.aborted
        rows.append({"pm": pm, "count": len(nodes), "sat": sat, "median": median(nodes), "max": max(nodes), "aborted": aborted})
    return rows


def random_reference(reference=C.STRUCT_REFERENCE, budget: int = C.STRUCT_BUDGET) -> dict:
    """Eine Zufallsformel mittlerer Größe zum Vergleich: Median der Knoten über feste Formeln."""
    n, m, seeds = reference
    nodes = [S.solve(random_formula(n, m, seed), True, "frequent", budget).nodes for seed in seeds]
    return {"n": n, "m": m, "count": len(seeds), "median": median(nodes)}


def rename_effect(n: int = 30, ratio: float = C.GROWTH_RATIO, seeds=C.GROWTH_SEEDS[:10]) -> dict:
    """Randnotiz: die zufällige Umbenennung der Variablen ändert die Antwort nie, die Knotenzahl nur durch Gleichstände (Median vorher und nachher, Zahl der Formeln mit anderer Knotenzahl)."""
    from sph_structure import rename_variables
    before, after, changed = [], [], 0
    for seed in seeds:
        f = random_formula(n, round(ratio * n), seed)
        a = S.solve(f)
        b = S.solve(rename_variables(f, n, seed + 1))
        assert a.satisfiable == b.satisfiable
        before.append(a.nodes)
        after.append(b.nodes)
        changed += a.nodes != b.nodes
    return {"n": n, "count": len(seeds), "median_before": median(before), "median_after": median(after), "changed": changed}


# --- Verdikte (rein) -----------------------------------------------------------------------------------------------------------------------------


def verdict_run(a: Analysis) -> tuple[str, str]:
    """Ergebnis eines Laufs: erfüllbar oder nicht mit Knoten, Einheitsschritten, Verzweigungen und Sackgassen, oder Abbruch durch das Budget."""
    s, r = a.settings, a.result
    if r.aborted:
        return "warning", (f"Das Knotenbudget von {fmt_int(s.budget)} reicht nicht: die Suche brach nach {fmt_int(r.nodes)} Knoten ab, ohne die Formel zu entscheiden. "
                           "Ein Abbruch sagt nichts über die Formel: mit Einheitspropagation oder einem größeren Budget wäre sie vielleicht entschieden.")
    word = "erfüllbar" if r.satisfiable else "unerfüllbar"
    return "success" if r.satisfiable else "info", (
        f"Die Formel ist **{word}** (Verhältnis m/n = {fmt_num(len(a.formula) / s.n)}). Die Suche braucht {fmt_int(r.nodes)} Knoten: {fmt_int(r.branches)} Verzweigungen, "
        f"{fmt_int(r.dead_ends)} Sackgassen und {fmt_int(r.units)} erzwungene Einheitsschritte."
    )


def verdict_phase(by_n: dict[int, list[dict]]) -> tuple[str, str]:
    """Phasenübergang: Anteil erfüllbar am kleinsten und größten Verhältnis, 50-%-Schnitt und Spitze des Aufwands je Größe."""
    sizes = sorted(by_n)
    first_shares = [by_n[n][0]["sat"] / by_n[n][0]["count"] for n in sizes]
    last_shares = [by_n[n][-1]["sat"] / by_n[n][-1]["count"] for n in sizes]
    r0, r1 = by_n[sizes[0]][0]["ratio"], by_n[sizes[0]][-1]["ratio"]
    cuts = [crossing(by_n[n]) for n in sizes]
    cut_text = " / ".join("–" if c is None else fmt_num(c, 2) for c in cuts)
    last = by_n[sizes[-1]]
    pk = peak(last)
    return "info", (
        f"Bei m/n = {fmt_num(r0)} sind {pct_range(first_shares)} der Formeln erfüllbar, bei m/n = {fmt_num(r1)} nur {pct_range(last_shares)}. "
        f"Der 50-%-Schnitt liegt bei n = {' / '.join(str(n) for n in sizes)} bei m/n = {cut_text}; die Vorhersage der Literatur für sehr große n ist {fmt_num(C.THRESHOLD_PREDICTION, 2)} "
        f"(für k = 3 nicht bewiesen). Am teuersten ist die Suche bei n = {sizes[-1]} bei m/n = {fmt_num(pk['ratio'], 2)} (Median {fmt_median(pk['median'])} Knoten)."
    )


def verdict_growth(rows: list[dict]) -> tuple[str, str]:
    """Wachstum der Suche beim festen Verhältnis: Median der kleinsten und größten Größe und der mittlere Faktor je zehn zusätzliche Variablen."""
    a, b = rows[0], rows[-1]
    factor = (b["median"] / a["median"]) ** (10 / (b["n"] - a["n"]))
    return "info", (
        f"Beim Verhältnis {fmt_num(C.GROWTH_RATIO)} braucht die Suche im Median {fmt_median(a['median'])} Knoten bei n = {a['n']} und {fmt_median(b['median'])} bei n = {b['n']}: "
        f"das {fmt_int(round(b['median'] / a['median']))}-Fache, im Mittel ×{fmt_num(factor)} je zehn zusätzliche Variablen. Das passt zu einem exponentiellen Trend "
        f"(über {len(rows)} Größen gemessen, kein Beweis)."
    )


def verdict_levers(rows: list[dict]) -> tuple[str, str]:
    """Was ein Löser trägt: Wirkung der Einheitspropagation und der Verzweigungsregel auf denselben Formeln; abgebrochene Läufe machen die Faktoren zu unteren Schranken."""
    by = {(r["units"], r["rule"]): r for r in rows}
    on_first, off_first = by[(True, "first")], by[(False, "first")]
    on_jw = by[(True, "jw")]
    factor_units = off_first["median"] / on_first["median"]
    factor_rule = on_first["median"] / on_jw["median"]
    lower = " (untere Schranke: abgebrochene Läufe zählen nur mit dem Budget)" if off_first["aborted"] else ""
    return "info", (
        f"Ohne Einheitspropagation braucht die Regel „erste Variable“ im Median {fmt_median(off_first['median'])} statt {fmt_median(on_first['median'])} Knoten: "
        f"Faktor {fmt_int(round(factor_units))}{lower}, {off_first['aborted']} von {off_first['count']} Läufen am Budget abgebrochen. "
        f"Die Verzweigungsregel wirkt schwächer: mit Einheitspropagation sinkt der Median von „erste Variable“ auf Jeroslow–Wang von {fmt_median(on_first['median'])} auf {fmt_median(on_jw['median'])} Knoten (Faktor {fmt_num(factor_rule)})."
    )


def verdict_structure(row: dict, base_nodes: int, h: int, reference: dict) -> tuple[str, str]:
    """Struktur gegen Zufall gegen Störung für den gewählten Promillewert; die Einschränkung (die Störung ändert die Antwort) steht immer im Text."""
    if row["pm"] == 0:
        return "info", (f"Die ungestörte Schubfach-Formel mit {h} Fächern ({h + 1} Tauben) ist **unerfüllbar** und braucht {fmt_int(base_nodes)} Knoten; eine Zufallsformel mittlerer Größe "
                        f"(n = {reference['n']}, m = {reference['m']}) braucht im Median {fmt_median(reference['median'])} Knoten. Strukturell harte Formeln sind schwerer als typische Zufallsformeln gleicher Größenordnung.")
    return "info", (
        f"Bei {fmt_pm(row['pm'])} umgedrehten Vorzeichen braucht die Suche im Median {fmt_median(row['median'])} statt {fmt_int(base_nodes)} Knoten, "
        f"{row['sat']} von {row['count']} Störungen sind **erfüllbar**. Die Störung macht die Formel also leicht, **ändert dabei aber oft ihre Antwort**: sie ist keine Glättung "
        "desselben Problems, sondern ein Wechsel in eine andere Instanzfamilie."
    )
