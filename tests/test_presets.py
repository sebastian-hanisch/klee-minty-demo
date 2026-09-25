"""Presets: gültige Werte und jede Zahl im Hilfetext gegen die echten Auswertungsfunktionen (Pivotzahlen auf dem ungestörten Würfel sind exakt; gestörte Läufe sind je Seed deterministisch)."""


import kle_constants as C
import kle_evaluation as ev
from kle_presets import PRESET_KEYS, SETTING_SPECS


def _settings(name):
    p = C.PRESETS[name]
    return ev.Settings(p["kind"], p["n"], p.get("sigma", C.DEFAULT_SIGMA), p.get("seed", C.DEFAULT_SEED), p["rule"])


def _res(name):
    return ev.analyse(_settings(name)).res


def _has(name, *values):
    for v in values:
        assert v in C.PRESET_HELP[name], (name, v)


def test_every_preset_has_valid_values_and_a_help_text():
    assert list(C.PRESETS) == list(C.PRESET_HELP) and len(C.PRESETS) == 10
    for name, p in C.PRESETS.items():
        assert set(p) <= set(PRESET_KEYS) and {"kind", "n", "rule", "step"} <= set(p), name
        for key, state_key in PRESET_KEYS.items():
            if key in p and state_key in SETTING_SPECS:
                spec = SETTING_SPECS[state_key]
                assert spec.caster(p[key]) == p[key], (name, key)
                if spec.lo is not None:
                    assert spec.lo <= p[key] <= spec.hi, (name, key)
        assert C.PRESET_HELP[name].strip()
        if "path_i" in p:
            assert p["step"] == 1 and p["n"] <= 3 and 0 < p["path_i"] <= 2 ** p["n"] - 1


def test_help_cube_n3_and_n2_and_n10():
    r = _res("Der Würfel (n = 3)")
    assert r.total_pivots == 7 == C.PRESETS["Der Würfel (n = 3)"]["path_i"] and r.obj == 125.0
    _has("Der Würfel (n = 3)", "8 Ecken", "2³ − 1 = 7 Pivots")
    assert _res("Das Quadrat (n = 2)").total_pivots == 3 == C.PRESETS["Das Quadrat (n = 2)"]["path_i"]
    _has("Das Quadrat (n = 2)", "4 Ecken", "3 Pivots")
    assert _res("n = 10: 1 023 Pivots").total_pivots == 1023
    _has("n = 10: 1 023 Pivots", "1 024 Ecken", "1 023 Pivots (2¹⁰ − 1)", "10 Bedingungen")


def test_help_steepest_bland_random():
    assert _res("Steepest Edge: ein Pivot").total_pivots == 1
    _has("Steepest Edge: ein Pivot", "n = 10", "1 Pivot statt 1 023")
    assert _res("Bland: 465 Pivots").total_pivots == 465
    dz = ev.analyse(ev.Settings("klee_minty", 12)).res.total_pivots
    assert dz == 4095
    _has("Bland: 465 Pivots", "n = 12", "465 Pivots statt 4 095")
    t = ev.rule_table("klee_minty", 12, 0.0, 35)
    assert t["random"]["pivots"] == 3 and t["random"]["pivots_median"] == 19.0
    _has("Zufallsregel auf dem Würfel", "n = 12", "Seed 0 nur 3 Pivots", "Median über 30 Seeds 19", "4 095")


def test_help_noise_presets():
    m = _res("Multiplikative Störung")
    assert m.status == "optimal" and m.total_pivots == 671
    _has("Multiplikative Störung", "0,1 z", "n = 12", "4 095", "671 Pivots")
    a = _res("Additive Störung")
    assert a.status == "optimal" and a.total_pivots == 132
    _has("Additive Störung", "1e-4", "n = 12", "132 Pivots")


def test_help_eps_form_and_typical_case():
    r = _res("ε-Form: ein Pivot")
    assert r.status == "optimal" and r.total_pivots == 1
    _has("ε-Form: ein Pivot", "ε = 1/3", "n = 8", "1 Pivot")
    t = _res("Typisch gegen schlimmst")
    assert t.status == "optimal" and t.total_pivots == 5
    _has("Typisch gegen schlimmst", "12 Ressourcen", "5 Pivots", "4 095")
