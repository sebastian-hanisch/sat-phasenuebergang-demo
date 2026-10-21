"""Konstanten: Regler-Grenzen, Rechengrenzen, Messreihen-Parameter, Farben und Presets.

Rechengrenze am Regler-Maximum (DEMO-PLAYBOOK §1c): n = 60 mit m = 400 Klauseln ist eine überbestimmte Formel (m/n ≈ 6,7); ein Lauf kostet bei Einheitspropagation wenige
Knoten, ohne sie kann das Knotenbudget (BUDGETS) erreicht werden, dann bricht die Suche ab. Beim Verhältnis 4,5 braucht n = 60 im Median rund 140 Knoten."""

from sph_search import RULES

N_MIN, N_MAX, DEFAULT_N = 5, 60, 20
M_MIN, M_MAX, DEFAULT_M = 3, 400, 90
SEED_MAX, DEFAULT_SEED = 999999, 35
BUDGETS = (1_000, 10_000, 100_000)         # Knoten der Suche
DEFAULT_BUDGET = 10_000
DEFAULT_UNITS = True
DEFAULT_RULE = "frequent"
PIGEON_H = (3, 4, 5, 6)                    # Fächer der Schubfach-Formel (h + 1 Tauben)
DEFAULT_H = 5
PER_MILLE = (0, 5, 10, 20, 50, 100, 200, 500)   # Störung: Promille der umgedrehten Vorzeichen
DEFAULT_PER_MILLE = 0
TREE_LIMIT = 60                            # so viele Knoten zeichnet die App höchstens als Suchbaum

# Messreihen (alle Instanzen aus dem eigenen Generator: auf jeder Plattform dieselben)
SWEEP_SEEDS = tuple(range(100000, 100040))  # 40 feste Formeln je Zelle: nie ein einzelner Seed als Befund
PHASE_N = (20, 30, 40)
PHASE_RATIOS = tuple(3.0 + 0.25 * i for i in range(13))     # Verhältnis m/n von 3,0 bis 6,0
PHASE_BUDGET = 300_000
GROWTH_N = (20, 30, 40, 50, 60, 70)
GROWTH_RATIO = 4.5
GROWTH_SEEDS = tuple(range(500, 520))       # 20 feste Formeln je Größe
GROWTH_BUDGET = 400_000
LEVER_N, LEVER_M = 30, 128                  # Verhältnis 4,27
LEVER_SEEDS = tuple(range(1000, 1020))
LEVER_BUDGET = 10_000                       # kleiner als der Reglerbereich erlaubt, damit die Messreihe in Sekunden läuft; abgebrochene Läufe zählen mit dem Budget
STRUCT_SEEDS = tuple(range(777, 787))       # 10 Störungen je Promillewert
STRUCT_BUDGET = 50_000
STRUCT_REFERENCE = (30, 150, tuple(range(4000, 4010)))   # Zufallsformel zum Vergleich: n, m, Seeds
THRESHOLD_PREDICTION = 4.27                 # Vorhersage für n -> unendlich bei k = 3 (nicht bewiesen); nur zur Einordnung

COLOR_NODE = "#8D99A6"
COLOR_BRANCH = "#4c78a8"
COLOR_DEAD = "#C0392B"
COLOR_SOLVED = "#2F6B65"
COLOR_ABORTED = "#B8860B"
COLOR_SERIES = ("#2F6B65", "#4c78a8", "#B8860B", "#C0392B")

PRESETS = {
    "Standardfall (Voreinstellung)": {"n": DEFAULT_N, "m": DEFAULT_M, "seed": DEFAULT_SEED, "units": True, "rule": "frequent", "budget": DEFAULT_BUDGET, "h": DEFAULT_H, "pm": 0},
    "Lehrbeispiel (6 Variablen)": {"n": 6, "m": 14, "seed": 1, "units": True, "rule": "frequent", "budget": DEFAULT_BUDGET, "h": DEFAULT_H, "pm": 0},
    "Locker (m/n = 3)": {"n": 30, "m": 90, "seed": DEFAULT_SEED, "units": True, "rule": "frequent", "budget": DEFAULT_BUDGET, "h": DEFAULT_H, "pm": 0},
    "Am Übergang (m/n = 4,5)": {"n": 40, "m": 180, "seed": DEFAULT_SEED, "units": True, "rule": "frequent", "budget": DEFAULT_BUDGET, "h": DEFAULT_H, "pm": 0},
    "Überbestimmt (m/n = 6)": {"n": 40, "m": 240, "seed": DEFAULT_SEED, "units": True, "rule": "frequent", "budget": DEFAULT_BUDGET, "h": DEFAULT_H, "pm": 0},
    "Ohne Einheitspropagation": {"n": 30, "m": 128, "seed": DEFAULT_SEED, "units": False, "rule": "first", "budget": DEFAULT_BUDGET, "h": DEFAULT_H, "pm": 0},
    "Schubfach, leicht gestört": {"n": DEFAULT_N, "m": DEFAULT_M, "seed": DEFAULT_SEED, "units": True, "rule": "frequent", "budget": DEFAULT_BUDGET, "h": 6, "pm": 10},
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "20 Variablen, 90 Klauseln (m/n = 4,5), Einheitspropagation, häufigste Variable.",
    "Lehrbeispiel (6 Variablen)": "6 Variablen, 14 Klauseln: ein kleiner Suchbaum, den man Knoten für Knoten lesen kann.",
    "Locker (m/n = 3)": "Wenige Regeln je Entscheidung: fast immer erfüllbar, die Suche braucht wenig.",
    "Am Übergang (m/n = 4,5)": "40 Variablen, 180 Klauseln: erfüllbar oder nicht, beides ist möglich, die Suche ist hier am teuersten.",
    "Überbestimmt (m/n = 6)": "Sehr viele Regeln: fast immer unerfüllbar, aber ein Widerspruch zeigt sich früh.",
    "Ohne Einheitspropagation": "Dieselbe Formel ohne den größten Hebel und mit der einfachsten Verzweigungsregel: das Knotenbudget kann erreicht werden.",
    "Schubfach, leicht gestört": "6 Fächer, 7 Tauben, 1 % der Vorzeichen umgedreht: die Formel ändert dadurch meist ihre Antwort und wird leicht.",
}
