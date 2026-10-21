"""Strukturierte und gestörte Formeln (reines Python): Schubfach-Formeln, Vorzeichen-Störung, zufällige Umbenennung der Variablen.

**Wichtig zur Störung:** Das Umdrehen von Vorzeichen ändert die Formel und kann ihre Antwort ändern (unerfüllbar wird erfüllbar). Es ist deshalb keine Glättung desselben
Problems im Sinn der geglätteten Analyse, sondern ein Wechsel in eine andere Instanzfamilie. Die Umbenennung der Variablen ändert die Antwort nie."""

import itertools

from sph_scenario import SplitMix64


def pigeonhole(h: int) -> tuple[list[tuple[int, ...]], int]:
    """h + 1 Tauben in h Fächer: Variable (Taube i, Fach j) = i·h + j + 1. Klauseln: jede Taube sitzt in einem Fach (Länge h); kein Fach hat zwei Tauben (Länge 2). Unerfüllbar.
    Rückgabe (Klauseln, Zahl der Variablen). Keine 3-KNF."""
    pigeons = h + 1

    def var(i, j):
        return i * h + j + 1

    clauses = [tuple(var(i, j) for j in range(h)) for i in range(pigeons)]
    for j in range(h):
        for a, b in itertools.combinations(range(pigeons), 2):
            clauses.append((-var(a, j), -var(b, j)))
    return clauses, pigeons * h


def perturb(formula, per_mille: int, seed: int) -> list[tuple[int, ...]]:
    """Jedes Literal wird unabhängig mit Wahrscheinlichkeit per_mille / 1000 umgedreht (deterministisch aus dem Seed). Bei 0 bleibt die Formel gleich, bei 1000 wird jedes Literal umgedreht."""
    if not 0 <= per_mille <= 1000:
        raise ValueError("per_mille liegt zwischen 0 und 1000")
    rng = SplitMix64(seed)
    return [tuple(-lit if rng.below(1000) < per_mille else lit for lit in clause) for clause in formula]


def rename_variables(formula, n: int, seed: int) -> list[tuple[int, ...]]:
    """Variablen 1..n zufällig umnummerieren (Permutation, deterministisch aus dem Seed). Erfüllbarkeit ändert sich nie; nur die Reihenfolge, in der die Suche Gleichstände auflöst."""
    rng = SplitMix64(seed)
    order = list(range(1, n + 1))
    for i in range(n - 1):
        j = i + rng.below(n - i)
        order[i], order[j] = order[j], order[i]
    new = {v: order[v - 1] for v in range(1, n + 1)}
    return [tuple(new[abs(lit)] if lit > 0 else -new[abs(lit)] for lit in clause) for clause in formula]
