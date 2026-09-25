"""Auswertung: Analyse, Regeltabelle, Kurve über n (Würfel gegen typischer Fall), Glättungskurve."""

import math


import kle_algorithm as A
import kle_constants as C
import kle_evaluation as ev
import kle_scenario as S


def test_analyse_returns_certificate_and_vertices_only_for_small_n():
    a = ev.analyse(ev.Settings("klee_minty", 3))
    assert a.status == "optimal" and a.cube_vertices == 8 and len(a.vertices) == 8
    assert a.certificate["primal"] < 1e-9 and a.certificate["dual"] < 1e-9 and a.certificate["gap"] < 1e-6
    b = ev.analyse(ev.Settings("klee_minty", 6))
    assert b.vertices == [] and b.res.total_pivots == 63 and b.cube_vertices == 64
    assert ev.analyse(ev.Settings("klee_minty", 3)) is a                    # zwischengespeichert


def test_analyse_uses_the_chosen_rule_and_reports_non_optimal_status():
    assert ev.analyse(ev.Settings("klee_minty", 10, rule="steepest")).res.total_pivots == 1
    found = [ev.analyse(ev.Settings("perturbed_add", 8, 0.3, s)) for s in range(40)]
    assert any(a.status == "unbounded" and a.certificate is None for a in found) and any(a.status == "optimal" for a in found)


def test_rule_table_has_all_rules_and_the_random_band():
    t = ev.rule_table("klee_minty", 8, 0.0, 35)
    assert list(t) == list(A.RULES)
    assert (t["dantzig"]["pivots"], t["greatest"]["pivots"], t["steepest"]["pivots"], t["bland"]["pivots"]) == (255, 1, 1, 67)
    r = t["random"]
    assert r["pivots_min"] <= r["pivots_median"] <= r["pivots_max"] and r["pivots_max"] < 100
    assert all(x["status"] == "optimal" and x["flops"] >= x["price_flops"] >= 0 for x in t.values())
    assert t["steepest"]["price_flops"] > 0 and t["dantzig"]["price_flops"] == 0


def test_cube_curve_matches_the_closed_forms_and_the_typical_case_is_tiny():
    rows = ev.cube_curve()
    assert [r["n"] for r in rows] == list(C.CURVE_NS)
    for r in rows:
        n = r["n"]
        assert r["dantzig"] == r["cube_bound"] == 2 ** n - 1 and r["vertices"] == 2 ** n
        assert r["bland"] == A.bland_pivots_on_cube(n) and r["greatest"] == r["steepest"] == 1
        assert r["random_lo"] <= r["random"] <= r["random_hi"] and r["random"] < r["dantzig"] + 1
        assert r["typical"] <= 7 and (n < 5 or r["typical"] < r["bland"])
    assert rows[-1]["dantzig"] == 16383 and ev.cube_curve() is rows


def test_smoothing_curve_columns_and_counts():
    rows = ev.smoothing_curve("perturbed_add", 8, "dantzig")
    assert [r["sigma"] for r in rows] == list(C.SIGMA_OPTIONS)
    for r in rows:
        assert r["solved"] + r["unbounded"] + r["limit"] == r["n_runs"] == len(C.SMOOTH_SEEDS) and r["cube_bound"] == 255
        assert r["pivots_lo"] <= r["pivots"] <= r["pivots_hi"]
    assert rows[0]["pivots"] == 255 and rows[0]["pivots_lo"] == rows[0]["pivots_hi"] == 255
    assert next(r for r in rows if r["sigma"] == 0.3)["unbounded"] >= 1


def test_multiplicative_smoothing_keeps_the_cube_until_a_few_percent():
    rows = {r["sigma"]: r for r in ev.smoothing_curve("perturbed_mult", 8, "dantzig")}
    assert all(rows[s]["pivots"] == 255 for s in (0.0, 1e-6, 1e-4, 1e-3, 1e-2))
    assert rows[0.1]["pivots"] < 0.5 * 255 and rows[0.3]["pivots"] < rows[0.1]["pivots"] and all(r["unbounded"] == 0 for r in rows.values())


def test_all_nan_column_when_nothing_is_solved_and_sigma_labels():
    assert math.isnan(ev._stats([])[0]) and ev._stats([3, 5, None, float("inf")])[0] == 4.0
    assert [ev.sigma_label(s) for s in C.SIGMA_OPTIONS] == ["0", "1e-6", "1e-4", "1e-3", "0.01", "0.03", "0.1", "0.3"]
    assert ev.instance_of(ev.Settings("klee_minty_eps", 4)) == S.klee_minty_eps_instance(4)
