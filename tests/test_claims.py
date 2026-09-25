"""Jede Zahl aus README und App-Texten gegen die echten Auswertungsfunktionen (dieselben, die die App aufruft)."""

from pathlib import Path


import kle_algorithm as A
import kle_constants as C
import kle_evaluation as ev

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
APP_SRC = (Path(__file__).resolve().parent.parent / "app.py").read_text(encoding="utf-8")


def _has(*values):
    for v in values:
        assert v in README, v


def _smooth(kind, n):
    return {r["sigma"]: r for r in ev.smoothing_curve(kind, n, "dantzig")}


def test_cube_headline_numbers():
    row = {r["n"]: r for r in ev.cube_curve()}
    assert row[14]["dantzig"] == 16383 and row[12]["dantzig"] == 4095
    t14 = ev.rule_table("klee_minty", 14, 0.0, 35)
    assert t14["dantzig"]["flops"] == 13778103 and t14["dantzig"]["pivots"] == 16383
    t12 = ev.rule_table("klee_minty", 12, 0.0, 35)
    assert (t12["dantzig"]["flops"], t12["greatest"]["flops"], t12["steepest"]["flops"]) == (2559375, 913, 937)
    assert (row[12]["bland"], row[14]["bland"]) == (465, 1219) and A.bland_pivots_on_cube(14) == 1219 == 2 * 610 - 1
    assert row[12]["random"] == 19.0 and (t12["random"]["pivots_min"], t12["random"]["pivots_max"]) == (1, 43)
    _has("16 383 Pivots", "13,8 Millionen Operationen", "913 und 937 Operationen gegen 2 559 375", "n = 12: 465, n = 14: 1 219", "im Median 19 Pivots (Spanne 1 bis 43")


def test_bland_random_and_typical_series_in_the_table():
    rows = ev.cube_curve()
    assert [r["bland"] for r in rows] == [3, 5, 9, 15, 25, 41, 67, 109, 177, 287, 465, 753, 1219]
    assert [r["random"] for r in rows] == [1, 3, 5, 5, 9, 10, 9, 13, 15, 20, 19, 24, 27]
    assert [r["typical"] for r in rows] == [1.5, 2, 2, 3, 3, 3, 4, 5, 5.5, 6, 5, 6.5, 6]
    assert all(r["greatest"] == r["steepest"] == 1 for r in rows)
    _has("3, 5, 9, 15, 25, 41, 67, 109, 177, 287, 465, 753, 1 219", "1, 3, 5, 5, 9, 10, 9, 13, 15, 20, 19, 24, 27", "1,5 / 2 / 2 / 3 / 3 / 3 / 4 / 5 / 5,5 / 6 / 5 / 6,5 / 6", "1,5 bis 6,5 Pivots")
    assert "im Median 1,5 bis 6,5 Pivots (n = 2 bis 14)" in APP_SRC


def test_multiplicative_series():
    m = {n: _smooth("perturbed_mult", n) for n in C.SMOOTH_NS}
    assert [m[n][0.01]["pivots"] for n in C.SMOOTH_NS] == [255, 1023, 4095]
    assert [m[n][0.03]["pivots"] for n in C.SMOOTH_NS] == [255, 1007, 3745]
    assert [m[n][0.1]["pivots"] for n in C.SMOOTH_NS] == [104, 342.5, 562]
    assert [m[n][0.3]["pivots"] for n in C.SMOOTH_NS] == [18.5, 44, 64]
    assert all(r["unbounded"] == 0 for n in C.SMOOTH_NS for r in m[n].values())
    _has("255 / 1 023 / 4 095", "255 / 1 007 / 3 745", "104 / 342,5 / 562", "18,5 / 44 / 64", "Kein Lauf wird unbeschränkt")


def test_additive_series_and_unbounded_counts():
    a = {n: _smooth("perturbed_add", n) for n in C.SMOOTH_NS}
    assert [a[n][1e-6]["pivots"] for n in C.SMOOTH_NS] == [255, 709.5, 933.5]
    assert [a[n][1e-4]["pivots"] for n in C.SMOOTH_NS] == [106, 110.5, 116]
    assert [a[n][1e-2]["pivots"] for n in C.SMOOTH_NS] == [20, 20, 28]
    assert [a[n][0.1]["pivots"] for n in C.SMOOTH_NS] == [7.5, 9, 13]
    assert a[8][0.03]["unbounded"] == 1 and a[12][0.1]["unbounded"] == 1 and a[12][0.3]["unbounded"] == 2 and a[12][0.01]["unbounded"] == 0
    _has("255 / 709,5 / 933,5", "106 / 110,5 / 116", "20 / 20 / 28", "7,5 / 9 / 13", "n = 8: 1 von 20", "bei 0,3: 2 von 20")


def test_preset_table_numbers():
    assert ev.analyse(ev.Settings("klee_minty", 10)).res.total_flops == 451143
    assert ev.analyse(ev.Settings("klee_minty", 10, rule="steepest")).res.total_flops == 661
    assert ev.analyse(ev.Settings("klee_minty", 2)).res.obj == 25.0 and ev.analyse(ev.Settings("klee_minty", 3)).res.obj == 125.0
    assert _smooth("perturbed_mult", 12)[0.1]["pivots"] == 562 and _smooth("perturbed_add", 12)[1e-4]["pivots"] == 116
    _has("451 143 Operationen", "661 Operationen", "Median über 20 Störungen 562", "Median über 20 Störungen 116", "Optimum 125", "Optimum 25")


def test_edge_count_and_epsilon_form_statements():
    _has("n · 2ⁿ⁻¹ Kanten", "nur **1 Pivot** bei jeder Regel (n = 2 bis 14)", "2 F(n+1) − 1", "5¹⁴ < 2⁵³")
    assert 5 ** 14 < 2 ** 53


def test_app_limits_table_numbers_match_measurements():
    t = ev.rule_table("klee_minty", 12, 0.0, 35)
    assert t["greatest"]["pivots"] == t["steepest"]["pivots"] == 1 and t["random"]["pivots_median"] == 19.0
    assert "die Zufallsregel im Median mit 19 (n = 12)" in APP_SRC and "lösen ihn mit 1 Pivot" in APP_SRC


def test_literature_lines_are_in_the_readme_and_the_app():
    _has("Klee, V., & Minty, G. J. (1972)", "Jeroslow, R. G. (1973)", "Goldfarb, D., & Sit, W. Y. (1979)", "Spielman, D. A., & Teng, S.-H. (2004)", "Bach, E., & Huiberts, S. (2025)", "arXiv:2504.04197")
    for s in ("Klee, V., & Minty, G. J. (1972)", "Spielman, D. A., & Teng, S.-H. (2004)", "arXiv:2504.04197"):
        assert s in APP_SRC
