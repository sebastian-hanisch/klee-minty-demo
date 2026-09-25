"""AppTest-Rauchtests: Voreinstellung, jedes Preset, jeder Schritt für jede Instanz und Regel, Pfad-Regler, Randwerte, Permalink-Grenzen, bedingte Regler, Kurven auf Abruf, Footer."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import kle_algorithm as A
import kle_constants as C
import kle_scenario as S

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(step=1, **state):
    at = AppTest.from_file(APP, default_timeout=240)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    if step != 1:
        at.select_slider(key="kle_step").set_value(step).run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def _metric(at, label):
    return next(m for m in at.metric if m.label.startswith(label))


def test_default_run_shows_the_three_service_cube():
    at = _run()
    _ok(at)
    assert {"Pivots", "Ecken 2ⁿ", "Operationen", "Ergebnis"} <= {m.label for m in at.metric}
    assert _metric(at, "Pivots").value == "7" and _metric(at, "Ecken 2ⁿ").value == "8" and _metric(at, "Ergebnis").value == "125.00"
    assert at.get("plotly_chart")


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_button_runs(name):
    at = _run()
    next(b for b in at.button if b.key == f"preset_{name}").click().run()
    _ok(at)
    p = C.PRESETS[name]
    ss = at.session_state
    assert (ss["kind_select"], ss["n_slider"], ss["kle_step"], ss["rule_select"]) == (p["kind"], p["n"], p["step"], p["rule"])
    if "sigma" in p:
        assert ss["sigma_select"] == p["sigma"]
    if "path_i" in p:
        assert ss["path_i"] == p["path_i"]


@pytest.mark.parametrize("step", [1, 2, 3, 4])
@pytest.mark.parametrize("kind", list(S.KINDS))
def test_every_step_runs_for_every_kind(step, kind):
    at = _run(kind_select=kind, n_slider=3 if step == 1 else 6, sigma_select=0.1, kle_step=step)
    _ok(at)
    assert at.session_state["kle_step"] == step


@pytest.mark.parametrize("rule", A.RULES)
def test_every_rule_runs_on_every_step_and_a_bigger_cube(rule):
    for step in (1, 4):
        for n in (2, 3, 6, 10):
            _ok(_run(step=step, n_slider=n, rule_select=rule))


def test_path_slider_moves_through_the_cube_for_n_2_and_3():
    for n, total in ((2, 3), (3, 7)):
        at = _run(n_slider=n)
        _ok(at)
        slider = next(s for s in at.slider if s.key == "path_i")
        assert slider.max == total
        for k in (0, 1, total):
            at.slider(key="path_i").set_value(k).run()
            _ok(at)
        assert at.get("plotly_chart")


def test_larger_n_shows_the_objective_curve_and_a_note_instead_of_the_drawing():
    at = _run(n_slider=6)
    _ok(at)
    assert any("Die Zeichnung des Polytops gibt es bis n = 3" in i.value for i in at.info) and not any(s.key == "path_i" for s in at.slider)
    assert _metric(at, "Pivots").value == "63"


def test_rule_table_has_all_five_rules_on_the_cube():
    at = _run(step=4, n_slider=8)
    _ok(at)
    table = at.dataframe[0].value
    assert list(table["Regel"]) == ["Dantzig", "Größter Zuwachs", "Steepest Edge", "Bland", "Zufall"] and list(table["Pivots"])[:4] == [255, 1, 1, 67]


@pytest.mark.parametrize("kw", [dict(n_slider=C.N_MIN), dict(n_slider=C.N_MAX), dict(n_slider=C.N_MAX, rule_select="bland"), dict(n_slider=C.N_MAX, rule_select="random"),
                                dict(kind_select="perturbed_add", n_slider=C.N_MAX, sigma_select=C.SIGMA_OPTIONS[-1]), dict(kind_select="perturbed_mult", n_slider=C.N_MIN, sigma_select=C.SIGMA_OPTIONS[0]),
                                dict(kind_select="klee_minty_eps", n_slider=C.N_MAX), dict(kind_select="random", n_slider=C.N_MAX)])
def test_extreme_settings_run(kw):
    for step in (1, 4):
        _ok(_run(step=step, **kw))


def test_dice_button_changes_the_seed_when_the_seed_control_is_visible():
    at = _run(kind_select="perturbed_mult")
    old = at.session_state["seed_input"]
    next(b for b in at.button if b.label == "🎲 Neuer Seed").click().run()
    _ok(at)
    assert at.session_state["seed_input"] != old and at.session_state["seed_widget"] == at.session_state["seed_input"]


def test_permalink_values_are_clamped_and_invalid_choices_fall_back_to_the_default():
    at = AppTest.from_file(APP, default_timeout=240)
    for k, v in dict(n="99", sigma="0.42", step="9", kind="nope", rule="nope", seed="-4").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert (ss["n_slider"], ss["sigma_select"], ss["kle_step"], ss["kind_select"], ss["rule_select"], ss["seed_input"]) == (C.N_MAX, C.DEFAULT_SIGMA, 1, "klee_minty", C.DEFAULT_RULE, 0)


def test_permalink_accepts_valid_values():
    at = AppTest.from_file(APP, default_timeout=240)
    for k, v in dict(kind="perturbed_add", n="9", sigma="0.001", seed="7", rule="bland", step="3").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert (ss["kind_select"], ss["n_slider"], ss["sigma_select"], ss["seed_input"], ss["rule_select"], ss["kle_step"]) == ("perturbed_add", 9, 0.001, 7, "bland", 3)


def test_sidebar_shows_the_controls_that_belong_to_the_instance():
    cube = _run()
    assert not any(w.key == "sigma_widget" for w in cube.select_slider) and not any(n.key == "seed_widget" for n in cube.number_input)
    noisy = _run(kind_select="perturbed_mult")
    assert any(w.key == "sigma_widget" for w in noisy.select_slider) and any(n.key == "seed_widget" for n in noisy.number_input)
    rnd = _run(kind_select="random")
    assert not any(w.key == "sigma_widget" for w in rnd.select_slider) and any(n.key == "seed_widget" for n in rnd.number_input)
    rule = _run(rule_select="random")
    assert any(n.key == "seed_widget" for n in rule.number_input)


def test_changing_kind_and_rule_on_later_steps_does_not_crash():
    for step in (2, 3, 4):
        at = _run(step=step)
        _ok(at)
        for kw in (dict(kind_select="perturbed_mult"), dict(kind_select="perturbed_add", sigma_select=0.3), dict(kind_select="random"), dict(rule_select="steepest"), dict(rule_select="random"), dict(n_slider=14),
                   dict(kind_select="klee_minty_eps")):
            for k, v in kw.items():
                at.session_state[k] = v
            at.run()
            _ok(at)


def test_curves_and_smoothing_on_demand():
    at = _run(step=2)
    next(b for b in at.button if b.key == "curve_start").click().run()
    _ok(at)
    assert any("16 383" in c.value for c in at.caption) and at.dataframe
    at = _run(step=3, rule_select="dantzig")
    next(b for b in at.button if b.key == "smooth_start").click().run()
    _ok(at)
    assert any("Ab σ" in m.value for m in at.markdown) and at.get("plotly_chart")


def test_footer_limits_and_literature_are_present():
    at = _run()
    assert any("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in c.value for c in at.caption)
    assert any("Wo die Annahmen enden" in s.value for s in at.subheader)
    assert any("Klee, V., & Minty, G. J. (1972)" in m.value and "Spielman, D. A., & Teng, S.-H. (2004)" in m.value and "Bach, E., & Huiberts, S. (2025)" in m.value for m in at.markdown)
