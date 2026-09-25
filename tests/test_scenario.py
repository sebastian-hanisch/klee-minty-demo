"""Instanzen: Chvátals Würfel von Hand, ε-Form, Störungen (Nullen, Determinismus, σ = 0), Zufallsinstanzen."""

import numpy as np
import pytest
from scipy.optimize import linprog

import kle_scenario as S


def _highs(inst, zero_objective=False):
    A, b, c = inst.arrays()
    if zero_objective:
        c = np.zeros_like(c)
    ub_a, ub_b, eq_a, eq_b = [], [], [], []
    for i, s in enumerate(inst.senses):
        if s == S.LE:
            ub_a.append(A[i]), ub_b.append(b[i])
        elif s == S.GE:
            ub_a.append(-A[i]), ub_b.append(-b[i])
        else:
            eq_a.append(A[i]), eq_b.append(b[i])
    return linprog(-c, A_ub=np.array(ub_a) if ub_a else None, b_ub=ub_b or None, A_eq=np.array(eq_a) if eq_a else None, b_eq=eq_b or None, bounds=(0, None), method="highs")


def reference_status(inst):
    """Status laut HiGHS; bei zulässigen, unbeschränkten LPs meldet HiGHS gelegentlich "unzulässig" (Präsolve), darum wird über ein Zulässigkeitsproblem ohne Zielfunktion abgesichert."""
    h = _highs(inst)
    if h.status == 0:
        return "optimal"
    return "infeasible" if _highs(inst, zero_objective=True).status == 2 else "unbounded"


def test_cube_matches_the_hand_computed_chvatal_form_for_n_2_and_3():
    two = S.klee_minty_instance(2)
    assert two.A == ((1.0, 0.0), (4.0, 1.0)) and two.b == (5.0, 25.0) and two.c == (2.0, 1.0)
    three = S.klee_minty_instance(3)
    assert three.A == ((1.0, 0.0, 0.0), (4.0, 1.0, 0.0), (8.0, 4.0, 1.0)) and three.b == (5.0, 25.0, 125.0) and three.c == (4.0, 2.0, 1.0)
    assert three.senses == (S.LE,) * 3 and (three.m, three.n) == (3, 3) and three.kind == "klee_minty"


@pytest.mark.parametrize("n", range(1, 15))
def test_cube_has_the_general_pattern_and_integer_entries(n):
    inst = S.klee_minty_instance(n)
    A = np.array(inst.A)
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            assert A[i - 1, j - 1] == (2.0 ** (i - j + 1) if j < i else (1.0 if j == i else 0.0))
    assert inst.b == tuple(5.0 ** i for i in range(1, n + 1)) and inst.c == tuple(2.0 ** (n - j) for j in range(1, n + 1))
    assert all(v == int(v) for v in inst.b + inst.c + tuple(A.ravel())) and 5.0 ** n < 2.0 ** 53 and inst.b[-1] < 2.0 ** 53


def test_eps_form_has_the_documented_rows():
    inst = S.klee_minty_eps_instance(3)
    eps = 1.0 / 3.0
    assert inst.m == 5 and inst.n == 3 and inst.c == (0.0, 0.0, 1.0) and inst.b == (1.0, 0.0, 1.0, 0.0, 1.0)
    assert inst.A[0] == (1.0, 0.0, 0.0) and inst.A[1] == (eps, -1.0, 0.0) and inst.A[2] == (eps, 1.0, 0.0) and inst.A[3] == (0.0, eps, -1.0) and inst.A[4] == (0.0, eps, 1.0)
    assert inst.kind == "klee_minty_eps" and S.klee_minty_eps_instance(5, 0.25).A[1][0] == 0.25


def test_zero_noise_returns_the_cube_numbers_for_both_kinds():
    for n in (2, 5, 9):
        base = S.klee_minty_instance(n)
        for kind in S.NOISE_KINDS:
            inst = S.generate(kind, n, 0.0, 7)
            assert (inst.A, inst.b, inst.c, inst.senses) == (base.A, base.b, base.c, base.senses) and inst.kind == kind


def test_multiplicative_noise_keeps_the_zeros_and_the_origin_feasible():
    base = S.klee_minty_instance(8)
    for seed in range(20):
        inst = S.generate("perturbed_mult", 8, 0.1, seed)
        A, A0 = np.array(inst.A), np.array(base.A)
        assert ((A == 0) == (A0 == 0)).all() and min(inst.b) > 0 and (np.array(inst.c) > 0).all()
        assert (A != A0)[A0 != 0].all()


def test_additive_noise_fills_the_zeros_and_scales_with_the_row_maximum():
    base = S.klee_minty_instance(8)
    A0 = np.array(base.A)
    diffs = []
    for seed in range(20):
        inst = S.generate("perturbed_add", 8, 0.01, seed)
        A = np.array(inst.A)
        assert (A[A0 == 0] != 0).all()
        diffs.append(np.abs(A - A0)[-1].mean() / np.abs(A0[-1]).max())
    assert 0.004 < float(np.mean(diffs)) < 0.02          # Größenordnung sigma * E|z| = 0.008


def test_generation_is_deterministic_and_seed_dependent_and_hashable():
    for kind in ("perturbed_mult", "perturbed_add", "random"):
        a = S.generate(kind, 6, 0.1, 3)
        assert a == S.generate(kind, 6, 0.1, 3) and a != S.generate(kind, 6, 0.1, 4) and hash(a) == hash(S.generate(kind, 6, 0.1, 3))
    assert S.generate("klee_minty", 6, 0.3, 1) == S.generate("klee_minty", 6, 0.0, 99)
    assert S.generate("klee_minty_eps", 6, 0.3, 1) == S.klee_minty_eps_instance(6)


def test_random_instances_are_feasible_bounded_and_row_zero_is_dense():
    for seed in range(30):
        for n in (2, 6, 12, 14):
            inst = S.random_instance(n, n, 0.5, seed)
            A = np.array(inst.A)
            assert (A >= 0).all() and (A[0] > 0).all() and (A.sum(axis=1) > 0).all() and _highs(inst).status == 0


def test_kinds_and_labels_are_consistent_and_unknown_kind_raises():
    assert set(S.KIND_LABELS) == set(S.KINDS) and set(S.NOISE_KINDS) <= set(S.KINDS)
    with pytest.raises(ValueError):
        S.generate("nope", 3, 0.0, 1)
