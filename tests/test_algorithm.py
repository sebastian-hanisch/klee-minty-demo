"""Korrektheitskette: Würfel-Struktur, Dantzig braucht 2^n - 1 Pivots und besucht jede Ecke, ganzzahlige Tableaus, schnelle == einfache Pivotschleife, Bland = 2F(n+1) - 1, alle Regeln == HiGHS, Grenze."""

import numpy as np
import pytest

import kle_algorithm as A
import kle_scenario as S
from tests.test_scenario import _highs, reference_status


def _solve(inst, **kw):
    return A.tableau_simplex(inst, **kw)


@pytest.mark.parametrize("n", range(1, 15))
def test_cube_optimum_is_five_to_the_n_and_matches_highs(n):
    inst = S.klee_minty_instance(n)
    r = _solve(inst)
    assert r.status == "optimal" and r.obj == 5.0 ** n
    assert r.x == (0.0,) * (n - 1) + (5.0 ** n,)
    assert -_highs(inst).fun == pytest.approx(5.0 ** n, rel=1e-9)
    assert A.primal_violation(inst, r.x) < 1e-6 and A.dual_violation(inst, r.duals) < 1e-6
    assert float(np.dot(r.duals, np.array(inst.b))) == pytest.approx(r.obj, rel=1e-9)


@pytest.mark.parametrize("n", range(1, 15))
def test_dantzig_takes_exactly_two_to_the_n_minus_one_pivots(n):
    r = _solve(S.klee_minty_instance(n))
    assert r.total_pivots == 2 ** n - 1 and len(r.pivots) == 2 ** n - 1


@pytest.mark.parametrize("n", range(2, 5))
def test_dantzig_visits_every_vertex_once_along_edges_with_rising_objective(n):
    inst = S.klee_minty_instance(n)
    verts = A.vertices_nd(inst)
    assert len(verts) == 2 ** n
    r = _solve(inst)
    path = [(0.0,) * n] + [p.x for p in r.pivots]
    keys = [tuple(round(v, 9) for v in x) for x in path]
    assert len(set(keys)) == 2 ** n and set(keys) == {v[0] for v in verts}
    tight = dict(verts)
    for a, b in zip(keys, keys[1:]):
        assert len(tight[a] & tight[b]) >= n - 1                      # Nachbarn im Würfelgraphen
    objs = [0.0] + [p.obj for p in r.pivots]
    assert all(y > x for x, y in zip(objs, objs[1:]))
    assert not any(p.degenerate for p in r.pivots) and all(p.ties == 1 for p in r.pivots)


def test_vertex_edges_of_the_cube_form_the_cube_graph():
    for n in (2, 3, 4):
        verts = A.vertices_nd(S.klee_minty_instance(n))
        edges = A.vertex_edges(verts)
        assert len(edges) == n * 2 ** (n - 1)                          # der n-Würfel hat n 2^(n-1) Kanten
        deg = [0] * len(verts)
        for i, j in edges:
            deg[i] += 1
            deg[j] += 1
        assert set(deg) == {n}
    with pytest.raises(ValueError):
        A.vertices_nd(S.klee_minty_instance(5))


def test_tableaus_stay_integer_on_the_cube():
    for n in range(2, 7):
        r = _solve(S.klee_minty_instance(n), keep=True)
        assert r.snapshots
        for snap in r.snapshots:
            T = np.array(snap["T"])
            assert (T == np.round(T)).all(), n


def _simple_pivot(T, row, col):
    T[row] /= T[row, col]
    for i in range(T.shape[0]):
        if i != row:
            T[i] -= T[i, col] * T[row]


@pytest.mark.parametrize("rule", A.RULES)
def test_fast_pivot_loop_equals_the_simple_loop(rule, monkeypatch):
    insts = [S.klee_minty_instance(n) for n in (3, 6, 8)] + [S.generate("perturbed_mult", 7, 0.1, s) for s in range(3)] + [S.generate("perturbed_add", 7, 0.01, s) for s in range(3)] + [S.random_instance(8, 8, 0.5, s) for s in range(3)]
    fast = [_solve(i, rule=rule, seed="4") for i in insts]
    monkeypatch.setattr(A, "_pivot", _simple_pivot)
    for inst, f in zip(insts, fast):
        s = _solve(inst, rule=rule, seed="4")
        assert (s.status, s.total_pivots) == (f.status, f.total_pivots)
        assert [(p.enter, p.leave_var) for p in s.pivots] == [(p.enter, p.leave_var) for p in f.pivots]
        if f.status == "optimal":
            assert s.obj == pytest.approx(f.obj, rel=1e-9)


@pytest.mark.parametrize("n", range(1, 14))
def test_bland_takes_two_fibonacci_minus_one_pivots_on_the_cube(n):
    r = _solve(S.klee_minty_instance(n), rule="bland")
    assert r.status == "optimal" and r.total_pivots == A.bland_pivots_on_cube(n)


def test_bland_formula_values():
    assert [A.bland_pivots_on_cube(n) for n in range(1, 14)] == [1, 3, 5, 9, 15, 25, 41, 67, 109, 177, 287, 465, 753]


@pytest.mark.parametrize("rule", ["greatest", "steepest"])
def test_greatest_improvement_and_steepest_edge_escape_the_standard_cube(rule):
    for n in range(2, 15):
        assert _solve(S.klee_minty_instance(n), rule=rule).total_pivots == 1


def test_random_rule_is_deterministic_per_seed_and_far_below_the_cube():
    inst = S.klee_minty_instance(12)
    a, b = _solve(inst, rule="random", seed="3"), _solve(inst, rule="random", seed="3")
    assert (a.total_pivots, [p.enter for p in a.pivots]) == (b.total_pivots, [p.enter for p in b.pivots])
    counts = [_solve(inst, rule="random", seed=str(s)).total_pivots for s in range(30)]
    assert len(set(counts)) > 5 and max(counts) < 200 and all(_solve(inst, rule="random", seed=str(s)).status == "optimal" for s in range(3))


@pytest.mark.parametrize("rule", A.RULES)
def test_every_rule_reaches_the_highs_optimum_on_perturbed_eps_and_random_instances(rule):
    checked = 0
    insts = []
    for seed in range(40):
        insts += [S.generate("perturbed_mult", 6, 0.1, seed), S.generate("perturbed_mult", 5, 0.3, seed), S.generate("perturbed_add", 6, 0.01, seed), S.generate("perturbed_add", 5, 0.3, seed),
                  S.random_instance(6, 6, 0.5, seed)]
    insts += [S.klee_minty_eps_instance(n) for n in range(2, 8)] + [S.klee_minty_instance(n) for n in range(2, 9)]
    seen = set()
    for inst in insts:
        r, ref = _solve(inst, rule=rule), reference_status(inst)
        assert r.status == ref, (inst.kind, rule)
        seen.add(r.status)
        if ref == "optimal":
            h = _highs(inst)
            assert r.obj == pytest.approx(-h.fun, rel=1e-7, abs=1e-7)
            assert A.primal_violation(inst, r.x) < 1e-6
            checked += 1
    assert checked >= 200 and seen == {"optimal", "unbounded"}      # additives Rauschen kann den Würfel öffnen; beide Ausgänge kommen vor


def test_pivot_limit_returns_limit_never_optimal():
    inst = S.klee_minty_instance(10)
    r = _solve(inst, max_pivots=10)
    assert r.status == "limit" and r.total_pivots <= 11
    full = _solve(inst, max_pivots=2000)
    assert full.status == "optimal" and full.total_pivots == 1023


def test_epsilon_form_is_solved_in_one_pivot_by_every_rule():
    for n in range(2, 15):
        for rule in A.RULES:
            r = _solve(S.klee_minty_eps_instance(n), rule=rule)
            assert r.status == "optimal" and r.total_pivots == 1 and r.obj == pytest.approx(1.0)


def test_zero_noise_gives_the_cube_pivot_count():
    for kind in S.NOISE_KINDS:
        assert _solve(S.generate(kind, 9, 0.0, 5)).total_pivots == 511


def test_small_noise_keeps_the_multiplicative_cube_path_but_breaks_the_additive_one():
    mult = [_solve(S.generate("perturbed_mult", 10, 1e-3, s)).total_pivots for s in range(10)]
    add = [_solve(S.generate("perturbed_add", 10, 1e-4, s)).total_pivots for s in range(10)]
    assert set(mult) == {1023} and max(add) < 300


def test_determinism_and_bookkeeping():
    inst = S.klee_minty_instance(9)
    a, b = _solve(inst), _solve(inst)
    assert (a.total_pivots, a.total_flops, a.obj) == (b.total_pivots, b.total_flops, b.obj)
    assert a.total_flops == a.total_pivots * a.flops_per_pivot and a.price_flops == 0
    assert a.m == 9 and [p.k for p in a.pivots] == list(range(1, a.total_pivots + 1))


def test_random_instances_need_few_pivots():
    counts = [_solve(S.random_instance(12, 12, 0.5, s)).total_pivots for s in range(30)]
    assert float(np.median(counts)) < 12
