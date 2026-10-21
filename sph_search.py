"""DPLL-Suche mit Varianten: Einheitspropagation an oder aus, drei Verzweigungsregeln (reines Python).

Jede Regel ist eine eigene Funktion mit expliziten Ein- und Ausgaben (DEMO-PLAYBOOK §1b); `solve` ruft sie nur der Reihe nach auf. Ein *Knoten* ist ein Aufruf der Suche,
gezählt wird immer in Knoten, nie in Sekunden. Die Variante „Einheitspropagation an, häufigste Variable“ ist dieselbe Suche wie `sph_dpll.dpll` (Kopie aus Stück 3) und liefert
dieselbe Knotenzahl (Regressionstest).

Eine Formel ist eine Liste von Klauseln, eine Klausel ein Tupel von Literalen: +v für „Variable v“, -v für „nicht v“."""

from dataclasses import dataclass, field

RULES = {"first": "erste Variable", "frequent": "häufigste Variable", "jw": "Jeroslow–Wang"}


@dataclass(frozen=True)
class TreeNode:
    """Ein Knoten des Suchbaums (nur bei kleinen Läufen aufgezeichnet)."""
    id: int
    parent: int | None
    depth: int
    decision: tuple | None     # (Variable, Wert), die zu diesem Knoten geführt hat; None an der Wurzel
    status: str                # "branch" (hat verzweigt), "dead" (Widerspruch), "solved" (alle Klauseln erfüllt), "aborted" (Budget)


@dataclass(frozen=True)
class SearchResult:
    satisfiable: bool | None       # None: Budget erreicht, keine Antwort
    assignment: dict | None        # erfüllende (teilweise) Belegung bei Erfolg
    nodes: int                     # Aufrufe der Suche
    aborted: bool
    units: int                     # erzwungene Einheitsschritte
    branches: int                  # Knoten, die verzweigt haben (Entscheidungen)
    dead_ends: int                 # Knoten mit Widerspruch
    tree: tuple = ()               # aufgezeichnete Knoten (leer, wenn nicht aufgezeichnet oder zu groß)
    tree_truncated: bool = False


def simplify(clauses, assignment, use_units: bool):
    """Klauseln vereinfachen: erfüllte fallen weg, falsche Literale werden gestrichen; mit `use_units` erzwingt eine Einheitsklausel ihr Literal (bis zum Fixpunkt).
    Rückgabe (offene Klauseln, Belegung, erzwungene Schritte); bei einer leeren Klausel (Widerspruch) ist der erste Wert None, die erzwungenen Schritte zählen trotzdem."""
    clauses = list(clauses)
    forced = 0
    while True:
        unit = None
        remaining = []
        for clause in clauses:
            if any(assignment.get(abs(lit)) is not None and assignment[abs(lit)] == (lit > 0) for lit in clause):
                continue
            rest = tuple(lit for lit in clause if assignment.get(abs(lit)) is None)
            if not rest:
                return None, assignment, forced
            if use_units and len(rest) == 1 and unit is None:
                unit = rest[0]
            remaining.append(rest)
        clauses = remaining
        if unit is None:
            return clauses, assignment, forced
        assignment = dict(assignment)
        assignment[abs(unit)] = unit > 0
        forced += 1


def choose_first(clauses) -> tuple[int, bool]:
    """Die kleinste Variable, die in den offenen Klauseln noch vorkommt; zuerst wahr."""
    return min(abs(lit) for clause in clauses for lit in clause), True


def choose_frequent(clauses) -> tuple[int, bool]:
    """Die Variable mit den meisten Vorkommen in den offenen Klauseln (Gleichstand: kleinere Nummer); zuerst wahr."""
    count: dict[int, int] = {}
    for clause in clauses:
        for lit in clause:
            count[abs(lit)] = count.get(abs(lit), 0) + 1
    return max(count, key=lambda v: (count[v], -v)), True


def choose_jeroslow_wang(clauses) -> tuple[int, bool]:
    """Jeroslow–Wang: jedes Vorkommen in einer Klausel der Länge L zählt 2^-L; gewählt wird die Variable mit der größten Summe beider Vorzeichen (Gleichstand: kleinere Nummer),
    zuerst mit dem Vorzeichen, das mehr Gewicht trägt (Gleichstand: wahr)."""
    pos: dict[int, float] = {}
    neg: dict[int, float] = {}
    for clause in clauses:
        weight = 2.0 ** -len(clause)
        for lit in clause:
            table = pos if lit > 0 else neg
            table[abs(lit)] = table.get(abs(lit), 0.0) + weight
    variables = set(pos) | set(neg)
    v = max(variables, key=lambda x: (pos.get(x, 0.0) + neg.get(x, 0.0), -x))
    return v, pos.get(v, 0.0) >= neg.get(v, 0.0)


CHOOSERS = {"first": choose_first, "frequent": choose_frequent, "jw": choose_jeroslow_wang}


class _Budget(Exception):
    """Das Knotenbudget ist aufgebraucht."""


def solve(formula, use_units: bool = True, rule: str = "frequent", budget: int | None = None, trace_limit: int = 0) -> SearchResult:
    """DPLL mit gewählter Regel. `budget`: höchste Zahl von Knoten (danach `aborted=True`). `trace_limit` > 0 zeichnet den Suchbaum auf, solange er höchstens so viele Knoten hat."""
    if rule not in CHOOSERS:
        raise ValueError(f"unbekannte Verzweigungsregel: {rule}")
    choose = CHOOSERS[rule]
    stats = {"nodes": 0, "units": 0, "branches": 0, "dead": 0}
    tree: list[TreeNode] = []
    truncated = [False]

    def record(node_id, parent, depth, decision, status):
        if trace_limit <= 0:
            return
        if node_id >= trace_limit:
            truncated[0] = True
            return
        tree.append(TreeNode(node_id, parent, depth, decision, status))

    def search(clauses, assignment, parent, depth, decision):
        node_id = stats["nodes"]
        stats["nodes"] += 1
        if budget is not None and stats["nodes"] > budget:
            record(node_id, parent, depth, decision, "aborted")
            raise _Budget
        clauses, assignment, forced = simplify(clauses, assignment, use_units)
        stats["units"] += forced
        if clauses is None:
            stats["dead"] += 1
            record(node_id, parent, depth, decision, "dead")
            return None
        if not clauses:
            record(node_id, parent, depth, decision, "solved")
            return assignment
        stats["branches"] += 1
        record(node_id, parent, depth, decision, "branch")
        v, first = choose(clauses)
        for value in (first, not first):
            trial = dict(assignment)
            trial[v] = value
            found = search(clauses, trial, node_id, depth + 1, (v, value))
            if found is not None:
                return found
        return None

    try:
        found = search([tuple(c) for c in formula], {}, None, 0, None)
        satisfiable, aborted = found is not None, False
    except _Budget:
        found, satisfiable, aborted = None, None, True
    return SearchResult(satisfiable, found, stats["nodes"], aborted, stats["units"], stats["branches"], stats["dead"], tuple(tree), truncated[0])


# --- Prüfer und Referenz --------------------------------------------------------------------------------------------------------------------------


def is_satisfying(formula, assignment) -> bool:
    """Unabhängiger Prüfer: jede Klausel hat ein wahres Literal; eine Variable ohne Eintrag zählt als falsch."""
    return all(any(assignment.get(abs(lit), False) == (lit > 0) for lit in clause) for clause in formula)


def brute_force_sat(n: int, formula):
    """Alle 2^n Belegungen durchprobieren (Orakel für n <= 16): die erste erfüllende Belegung oder None."""
    for bits in range(1 << n):
        assignment = {v: bool(bits >> (v - 1) & 1) for v in range(1, n + 1)}
        if is_satisfying(formula, assignment):
            return assignment
    return None
