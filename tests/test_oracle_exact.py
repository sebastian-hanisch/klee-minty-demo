"""Unabhängiges Orakel: ein exakter Simplex in rationaler Arithmetik (Fraction, eigene Schleife ohne gemeinsamen Code mit der Demo) für Standard-LPs max c·x, A x <= b, b >= 0.
Verglichen wird der **komplette Pivotpfad** (eintretende und austretende Variable je Pivot) aller vier deterministischen Regeln auf dem Würfel, seiner ε-Form, Zufallsinstanzen und gestörten Würfeln,
dazu die Pivotzahlen aus geschlossener Form (Dantzig 2^n − 1, Bland 2 F(n+1) − 1)."""

from fractions import Fraction as F

import pytest

import kle_algorithm as A
import kle_scenario as S

RULES = ("dantzig", "bland", "greatest", "steepest")


def _exact(inst, rule, binary=True):
    fr = (lambda v: F(float(v))) if binary else (lambda v: F(str(float(v))))
    m, n = inst.m, inst.n
    nc = n + m
    T = [[fr(v) for v in inst.A[i]] + [F(1) if k == i else F(0) for k in range(m)] + [fr(inst.b[i])] for i in range(m)]
    cost = [fr(v) for v in inst.c] + [F(0)] * m
    basis = [n + i for i in range(m)]
    path = []
    while True:
        r = [sum((cost[basis[i]] * T[i][j] for i in range(m)), F(0)) - cost[j] for j in range(nc)]
        cand = [j for j in range(nc) if r[j] < 0]
        if not cand:
            x = [F(0)] * nc
            for i, j in enumerate(basis):
                x[j] = T[i][nc]
            return "optimal", path, sum(cost[j] * x[j] for j in range(n))
        if rule == "bland":
            e = cand[0]
        elif rule == "dantzig":
            e = min(cand, key=lambda j: (r[j], j))
        elif rule == "steepest":
            e = max(cand, key=lambda j: (r[j] * r[j] / (1 + sum(T[i][j] ** 2 for i in range(m))), -j))
        else:                                                                                  # größter Zuwachs je Kandidat (unbeschränkte Richtung zuerst)
            best = bg = None
            for j in cand:
                pos = [i for i in range(m) if T[i][j] > 0]
                if not pos:
                    best = j
                    break
                g = -r[j] * min(T[i][nc] / T[i][j] for i in pos)
                if bg is None or g > bg:
                    best, bg = j, g
            e = best
        pos = [i for i in range(m) if T[i][e] > 0]
        if not pos:
            return "unbounded", path, None
        rmin = min(T[i][nc] / T[i][e] for i in pos)
        leave = min((i for i in pos if T[i][nc] / T[i][e] == rmin), key=lambda i: basis[i])
        p = T[leave][e]
        T[leave] = [v / p for v in T[leave]]
        for i in range(m):
            if i != leave and T[i][e] != 0:
                f = T[i][e]
                T[i] = [T[i][k] - f * T[leave][k] for k in range(nc + 1)]
        path.append((e, basis[leave]))
        basis[leave] = e


def _same_path(inst, rule, binary=True):
    status, path, obj = _exact(inst, rule, binary)
    r = A.tableau_simplex(inst, rule=rule)
    assert r.status == status, (inst.kind, inst.n, rule)
    assert [(p.enter, p.leave_var) for p in r.pivots] == path, (inst.kind, inst.n, rule)
    if status == "optimal":
        assert r.obj == pytest.approx(float(obj), rel=1e-9, abs=1e-9)
    return len(path)


@pytest.mark.parametrize("rule", RULES)
def test_every_rule_follows_the_exact_rational_path_on_the_cube_and_its_epsilon_form(rule):
    for n in range(2, 9):
        _same_path(S.klee_minty_instance(n), rule)
        _same_path(S.klee_minty_eps_instance(n), rule)


def test_pivot_counts_of_dantzig_and_bland_match_the_closed_forms_on_the_cube():
    fib = [0, 1]
    for _ in range(14):
        fib.append(fib[-1] + fib[-2])
    for n in range(2, 11):
        inst = S.klee_minty_instance(n)
        assert _exact(inst, "dantzig")[1].__len__() == 2 ** n - 1 == A.tableau_simplex(inst, rule="dantzig").total_pivots
        assert _exact(inst, "bland")[1].__len__() == 2 * fib[n + 1] - 1 == A.tableau_simplex(inst, rule="bland").total_pivots


@pytest.mark.parametrize("rule", RULES)
def test_every_rule_follows_the_exact_path_on_random_and_perturbed_instances(rule):
    total = 0
    for seed in range(12):
        total += _same_path(S.random_instance(2 + seed % 6, 2 + seed % 6, 0.5, seed), rule, binary=False)
        for kind in ("perturbed_mult", "perturbed_add"):
            for sigma in (1e-2, 0.1):
                total += _same_path(S.generate(kind, 4 + seed % 3, sigma, seed), rule)
    assert total > 50
