"""Die Suche gegen Handrechnung an den Mini-Formeln (conftest), Varianten einzeln, Statistik und Aufzeichnung (DEMO-PLAYBOOK §1b)."""

import pytest

import sph_dpll as D
import sph_search as S
from sph_scenario import random_formula


def test_simplify_by_hand():
    clauses, asg, forced = S.simplify([(1,), (-1, 2), (2, 3)], {}, True)
    assert asg == {1: True, 2: True} and clauses == [] and forced == 2
    assert S.simplify([(1,), (-1,)], {}, True)[0] is None                       # Einheitsklauseln widersprechen sich: Widerspruch, ein Schritt war erzwungen
    assert S.simplify([(1,), (-1,)], {}, True)[2] == 1
    clauses, asg, forced = S.simplify([(1, 2, 3)], {1: False}, True)
    assert clauses == [(2, 3)] and asg == {1: False} and forced == 0
    clauses, asg, forced = S.simplify([(1,), (-1, 2)], {}, False)               # ohne Einheitspropagation bleibt alles offen
    assert clauses == [(1,), (-1, 2)] and asg == {} and forced == 0
    assert S.simplify([(1, 2)], {1: False, 2: False}, False)[0] is None         # leere Klausel ist auch ohne Einheitspropagation ein Widerspruch


def test_choosers_by_hand():
    assert S.choose_first([(5, 6), (-3, 7)]) == (3, True)
    assert S.choose_frequent([(1, 2), (2, 3), (3, 4)]) == (2, True)             # 2 und 3 je zweimal: die kleinere
    assert S.choose_frequent([(5, 6), (-6, 7)]) == (6, True)
    assert S.choose_jeroslow_wang([(1, 2), (-2, 3), (-2, -3)]) == (2, False)    # x2: 0,25 positiv, 0,5 negativ
    assert S.choose_jeroslow_wang([(1,), (2, 3)]) == (1, True)                  # kurze Klauseln wiegen mehr: 0,5 gegen 0,25 je Variable
    assert S.choose_jeroslow_wang([(1, 2)]) == (1, True)                        # Gleichstand: kleinere Nummer, wahr


def test_chain_by_hand(chain):
    r = S.solve(chain, True, "frequent")
    assert (r.satisfiable, r.nodes, r.units, r.branches, r.dead_ends) == (False, 1, 2, 0, 1)
    for rule in S.RULES:
        r = S.solve(chain, False, rule)
        assert (r.satisfiable, r.nodes, r.branches, r.dead_ends) == (False, 5, 2, 3), rule


def test_square_by_hand(square):
    assert S.solve(square, True, "frequent").nodes == 3
    assert S.solve(square, False, "frequent").nodes == 7
    assert S.solve(square, True, "first").nodes == 3


def test_branchy_by_hand_node_counts_per_variant(branchy):
    nodes = {(u, rule): S.solve(branchy, u, rule).nodes for u in (True, False) for rule in S.RULES}
    assert nodes[(True, "first")] == 4 and nodes[(True, "frequent")] == 3 and nodes[(True, "jw")] == 2
    assert nodes[(False, "first")] == 6
    for key in nodes:
        assert S.solve(branchy, *key).satisfiable is True
        assert S.is_satisfying(branchy, S.solve(branchy, *key).assignment)


def test_default_variant_is_the_dpll_of_stueck_3():
    """(Einheitspropagation an, häufigste Variable) == Kopie aus Stück 3: gleiche Antwort, gleiche Knotenzahl."""
    for seed in range(150):
        n = 4 + seed % 8
        f = random_formula(n, 1 + (seed * 5) % (6 * n), 900 + seed)
        a, b = D.dpll(f), S.solve(f)
        assert (a.satisfiable, a.nodes) == (b.satisfiable, b.nodes), (n, seed)


def test_rule_validation(chain):
    with pytest.raises(ValueError):
        S.solve(chain, True, "zufall")


def test_budget_aborts_and_reports(chain):
    r = S.solve(chain, False, "first", budget=3)
    assert r.aborted and r.satisfiable is None and r.assignment is None and r.nodes == 4          # der vierte Aufruf überschreitet das Budget
    assert not S.solve(chain, False, "first", budget=5).aborted
    assert S.solve(chain, False, "first", budget=5).nodes == 5
    assert S.solve(chain, False, "first", budget=4).aborted


def test_statistics_add_up():
    for seed in range(40):
        r = S.solve(random_formula(10, 40, seed), True, "frequent")
        solved = 1 if r.satisfiable else 0
        assert r.nodes == r.branches + r.dead_ends + solved, seed         # jeder Knoten verzweigt, scheitert oder löst


def test_trace_records_the_tree(branchy):
    r = S.solve(branchy, True, "frequent", trace_limit=50)
    assert [t.id for t in r.tree] == [0, 1, 2] and not r.tree_truncated
    assert r.tree[0].parent is None and r.tree[0].depth == 0 and r.tree[0].decision is None and r.tree[0].status == "branch"
    assert r.tree[1].decision == (2, True) and r.tree[1].status == "dead" and r.tree[1].parent == 0
    assert r.tree[2].decision == (2, False) and r.tree[2].status == "solved"


def test_trace_is_truncated_for_large_trees_and_empty_when_off(square):
    r = S.solve(square, False, "first", trace_limit=4)
    assert r.tree_truncated and len(r.tree) == 4
    assert S.solve(square, False, "first").tree == () and not S.solve(square, False, "first").tree_truncated


def test_trace_marks_the_aborted_node(chain):
    r = S.solve(chain, False, "first", budget=3, trace_limit=20)
    assert r.tree[-1].status == "aborted"


def test_prover_and_brute_force_by_hand():
    assert S.is_satisfying([(1, -2)], {1: True}) and S.is_satisfying([(1, -2)], {}) is True          # fehlende Variable zählt als falsch: ¬x2 ist wahr
    assert not S.is_satisfying([(1,)], {}) and S.is_satisfying([], {})
    assert S.brute_force_sat(2, [(1,), (2,)]) == {1: True, 2: True}
    assert S.brute_force_sat(1, [(1,), (-1,)]) is None
