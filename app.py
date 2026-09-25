"""Klee-Minty – der Würfel, auf dem der Simplex alle Ecken besucht - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Drittes Stück der Lineare-Programmierung-Reihe der "Konzepte"-Reihe: Auf zufälligen Instanzen braucht der Simplex wenige Pivots (Stück 1 und 2). Klee und Minty (1972) bauten einen verformten Würfel, auf dem die
Dantzig-Regel alle 2^n Ecken durchläuft. Die Demo misst, wie die anderen Regeln auf demselben Würfel abschneiden und wie schnell zufällige Störungen ihn zerstören.

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import kle_algorithm as A
import kle_constants as C
import kle_evaluation as ev
import kle_scenario as S
from kle_evaluation import Settings, analyse
from kle_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    store_from_widget,
    sync_query_params,
)
from kle_visualization import (
    build_cube3d,
    build_curves,
    build_progress,
    build_rule_bars,
    build_smoothing,
    build_square,
)

st.set_page_config(page_title="Klee-Minty – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _curves():
    return ev.cube_curve()


@st.cache_data(show_spinner=False)
def _smoothing(n, rule):
    return {"mult": ev.smoothing_curve("perturbed_mult", n, rule), "add": ev.smoothing_curve("perturbed_add", n, rule)}


def thousands(x):
    return f"{int(round(x)):,}".replace(",", " ")


def num(x, digits=2):
    return f"{x:.{digits}f}"


STATUS_TEXT = {"optimal": "Optimum", "infeasible": "unzulässig", "unbounded": "unbeschränkt", "cycled": "kreist", "limit": "Pivot-Grenze erreicht"}

st.title("🧊 Klee-Minty – der Würfel, auf dem der Simplex alle Ecken besucht")
st.markdown(
    """
**Drittes Stück der Lineare-Programmierung-Reihe.** Auf den zufälligen Instanzen der ersten beiden Stücke brauchte der Simplex wenige Pivots (etwa einen halben je Ressource). Geht das immer so? **Klee und Minty (1972)** bauten einen **verformten Würfel**
in n Dimensionen: die Dantzig-Regel läuft von Ecke zu Ecke über **alle 2ⁿ Ecken**, ein Hamiltonpfad durch den Würfel. Vier Fragen, alle gemessen: **(1) Der Würfel** - wie sieht der Pfad aus, und stimmen 2ⁿ − 1 Pivots? **(2) Pivots über n** - wie schneiden die anderen
Regeln aus Stück 2 auf demselben Würfel ab, verglichen mit dem typischen Fall? **(3) Störung** - wie schnell zerstört Rauschen in den Daten den Würfel, und hängt das davon ab, wie man stört? **(4) Aufwand** - Pivots und Rechenoperationen aller Regeln bei einem n.
"""
)
st.caption("Kind von [Pivotregeln und Entartung](https://github.com/sebastian-hanisch/pivotregeln-demo). Folgestücke (Revised Simplex, Dualität, Innere Punkte, PDLP) sind [noch nicht gebaut].")

with st.expander("So funktioniert der Würfel", expanded=True):
    st.markdown(
        """
1. **Chvátals Form:** Dienst i belastet die Ressourcen ab Stufe i, jeweils doppelt so stark wie der vorherige: max Σⱼ 2ⁿ⁻ʲ xⱼ unter 2 · Σ über j < i von 2ⁱ⁻ʲ xⱼ, plus xᵢ, höchstens 5ⁱ (i = 1..n), x ≥ 0. Der Ursprung ist zulässig, das Optimum ist x = (0, ..., 0, 5ⁿ).
   Die Zulässigkeitsmenge ist ein verformter Würfel mit 2ⁿ Ecken, und der Zielwert steigt entlang eines Pfads, der jede Ecke genau einmal besucht.
2. **Warum Dantzig hineinläuft:** die Regel wählt immer die Spalte mit den kleinsten reduzierten Kosten und ist blind für die Länge des Schritts. Auf dem verformten Würfel ist jede lokal beste Kante eine kurze; der lange Weg zur besten Ecke bleibt unsichtbar.
3. **Die anderen Regeln:** der größte Zuwachs und Steepest Edge sehen die Länge des Schritts, Bland und Zufall wählen ohne Blick auf die Kosten. Was sie auf diesem Würfel tun, wird gemessen, nicht angenommen.
4. **Störung:** Zufallsrauschen auf den Daten kann den Würfel zerstören. **Multiplikativ:** jede von null verschiedene Zahl mal (1 + σ z), die Nullen bleiben; **additiv:** zu jeder Zahl, auch zu den Nullen, kommt σ mal dem größten Betrag ihrer Zeile mal z (wie im Modell der geglätteten Analyse von Spielman und Teng).
        """
    )

if C.PRESETS:
    st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
    preset_names = list(C.PRESETS.keys())
    for row in (preset_names[:4], preset_names[4:7], preset_names[7:]):
        if not row:
            continue
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            with col:
                st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

ss = st.session_state
with st.sidebar:
    st.header("⚙️ Einstellungen")
    kind = st.selectbox("Instanz", options=list(S.KINDS), format_func=lambda v: S.KIND_LABELS[v], key="kind_select",
                        help="Der Würfel und seine ε-Form sind fest; gestörte Würfel und Zufallsinstanzen hängen vom Seed ab.")
    n = st.slider("Dienste n (= Ressourcen)", *bounds("n_slider"), key="n_slider", help="Dimension des Würfels: 2ⁿ Ecken. Bis n = 3 gibt es die Zeichnung.")
    if kind in S.NOISE_KINDS:
        sigma = st.select_slider("Störstärke σ", options=list(C.SIGMA_OPTIONS), value=float(ss["sigma_select"]), key="sigma_widget", on_change=store_from_widget, args=("sigma_select",), format_func=ev.sigma_label,
                                 help="Relative Stärke des Rauschens; 0 = der ungestörte Würfel.")
    else:
        sigma = 0.0
    rule = st.selectbox("Pivotregel", options=list(C.RULE_LABELS), format_func=lambda v: C.RULE_LABELS[v], key="rule_select",
                        help="Wirkt auf den gewählten Lauf (Schritt 1, 4 und die Störungskurve); Schritt 2 vergleicht alle Regeln.")
    if kind in S.NOISE_KINDS or kind == "random" or rule == "random":
        seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), value=int(ss["seed_input"]), key="seed_widget", step=1, on_change=store_from_widget, args=("seed_input",),
                               help="Seed der Störung bzw. der Zufallsinstanz bzw. der Zufallsregel.")
        st.button("🎲 Neuer Seed", width="stretch", on_click=randomize_seed)
    else:
        seed = C.DEFAULT_SEED

sync_query_params({"kind_select": kind, "n_slider": int(ss["n_slider"]), "sigma_select": float(ss["sigma_select"]), "seed_input": int(ss["seed_input"]), "rule_select": rule, "kle_step": int(ss["kle_step"])})

settings = Settings(kind, int(n), float(sigma), int(seed), rule)
with st.spinner("Rechne..."):
    a = analyse(settings)
inst, res = a.inst, a.res

# --- In Aktion ---------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Alle Ecken besuchen")
step = st.select_slider("Schritt", options=list(C.STEPS), key="kle_step", format_func=lambda s: C.STEPS[s])

if res.status != "optimal":
    st.warning(f"Ergebnis: **{STATUS_TEXT[res.status]}** nach {res.total_pivots} Pivots" + (" (die Pivot-Grenze verhindert, dass die Demo ewig rechnet)." if res.status == "limit" else "."))

if step == 1:
    total = len(res.pivots)
    if inst.n <= 3 and a.vertices:
        if "path_i" in ss:
            ss["path_i"] = min(max(0, int(ss["path_i"])), total)
        k = st.slider("Pivot", 0, total, key="path_i", help="0 = Start im Ursprung; jeder weitere Schritt läuft eine Kante entlang.") if total > 0 else 0
        if k == 0:
            st.markdown(f"**Start:** Ursprung. Das Polytop hat **{len(a.vertices)} Ecken**; {C.RULE_SHORT[rule]} braucht insgesamt **{total} Pivots**.")
        else:
            p = res.pivots[k - 1]
            st.markdown(f"**Pivot {k} von {total}:** Ecke ({', '.join(num(v, 1) for v in p.x)}), Zielwert {num(p.obj, 1)}.")
        if inst.n == 2:
            st.plotly_chart(build_square(inst, a.vertices, res, k), width="stretch", key=f"s1_square_{k}")
        else:
            st.plotly_chart(build_cube3d(inst, a.vertices, res, k), width="stretch", key=f"s1_cube_{k}")
        st.caption("Grau = Kanten des Polytops, weiß = Ecken, orange = Pfad des Simplex bis zum gewählten Pivot. Beim Klee-Minty-Würfel mit der Dantzig-Regel besucht der Pfad jede Ecke genau einmal.")
    else:
        st.markdown(f"**n = {inst.n}:** {C.RULE_SHORT[rule]} braucht **{thousands(res.total_pivots)} Pivots**, das Polytop hat {thousands(2 ** inst.n)} Ecken" + (f" (2ⁿ − 1 = {thousands(2 ** inst.n - 1)})." if kind == "klee_minty" else "."))
        st.info("Die Zeichnung des Polytops gibt es bis n = 3. Darüber zeigt der Schritt den Zielwert nach jedem Pivot.")
        st.plotly_chart(build_progress(res), width="stretch", key="s1_progress")
        st.caption("Zielwert nach jedem Pivot (Start = 0): auf dem Würfel steigt er über 2ⁿ − 1 kleine Stufen.")
elif step == 2:
    st.markdown("Pivots über n für alle Regeln auf **Chvátals Würfel** (n = 2 bis 14), dazu die Zufallsregel (Median und Band über 30 Seeds) und Dantzig auf **Zufallsinstanzen** (Median über 30 Instanzen) - alle Achsen logarithmisch (🔬 auf Abruf).")
    if st.button("Kurven berechnen (dauert einige Sekunden)", key="curve_start"):
        ss["curve_done"] = True
    if ss.get("curve_done"):
        with st.spinner("Rechne..."):
            rows = _curves()
        st.plotly_chart(build_curves(rows), width="stretch", key="s2_curves")
        last = rows[-1]
        st.caption(f"Bei n = {last['n']}: Dantzig {thousands(last['dantzig'])} Pivots (= 2ⁿ − 1), Bland {thousands(last['bland'])}, Zufall im Median {last['random']:.0f} (10. bis 90. Perzentil {last['random_lo']:.0f} bis {last['random_hi']:.0f}), "
                   f"Größter Zuwachs und Steepest Edge {last['greatest']} und {last['steepest']}; auf Zufallsinstanzen braucht Dantzig im Median {last['typical']:.1f}.")
        df = pd.DataFrame([{"n": r["n"], "2ⁿ − 1": r["cube_bound"], "Dantzig": r["dantzig"], "Bland": r["bland"], "Zufall (Median)": r["random"], "Größter Zuwachs": r["greatest"], "Steepest Edge": r["steepest"],
                            "Dantzig, Zufallsinstanz": r["typical"]} for r in rows])
        st.dataframe(df, hide_index=True, width="stretch")
elif step == 3:
    st.markdown("Pivots der gewählten Regel auf dem **gestörten Würfel** über die Störstärke σ, für die **multiplikative** und die **additive** Störung (20 Störungen je Stufe, Median und Band; 🔬 auf Abruf).")
    smooth_n = st.radio("Dimension n des Würfels", C.SMOOTH_NS, index=1, horizontal=True, key="smooth_n", help="Größere n dauern länger, weil Dantzig auf dem ungestörten Würfel 2ⁿ − 1 Pivots braucht.")
    if st.button("Störungskurven berechnen (n = 12 dauert bis zu einer halben Minute)", key="smooth_start"):
        ss["smooth_done"] = ss.get("smooth_done", set()) | {(smooth_n, rule)}
    if (smooth_n, rule) in ss.get("smooth_done", set()):
        with st.spinner("Rechne..."):
            curves = _smoothing(smooth_n, rule)
        st.plotly_chart(build_smoothing({"multiplikativ (Nullen bleiben)": curves["mult"], "additiv (jede Zahl)": curves["add"]}, smooth_n, rule), width="stretch", key=f"s3_smooth_{smooth_n}_{rule}")
        bound = 2 ** smooth_n - 1
        for name, rows in (("multiplikativ", curves["mult"]), ("additiv", curves["add"])):
            hit = next((r["sigma"] for r in rows if r["pivots"] == r["pivots"] and r["pivots"] < 0.5 * bound), None)
            st.markdown(f"**{name}:** " + (f"Ab σ = {ev.sigma_label(hit)} liegt der Median unter der Hälfte der Würfel-Pivots ({bound})." if hit is not None else "auch bei der größten Störung liegt der Median nicht unter der Hälfte der Würfel-Pivots."))
        st.caption("Gepunktet: 2ⁿ − 1. Läufe, die unbeschränkt enden (die Störung kann den Würfel öffnen), sind nicht in den Medianen: "
                   + "; ".join(f"{name} σ = {ev.sigma_label(r['sigma'])}: {r['unbounded']} von {r['n_runs']}" for name, rows in (("multiplikativ", curves["mult"]), ("additiv", curves["add"])) for r in rows if r["unbounded"]) + ".")
else:
    table = ev.rule_table(kind, int(n), float(sigma), int(seed))
    rows = []
    for r in A.RULES:
        x = table[r]
        rows.append({"Regel": C.RULE_SHORT[r], "Ergebnis": STATUS_TEXT[x["status"]], "Pivots": x["pivots"], "Operationen": thousands(x["flops"]), "davon Preisgebung": thousands(x["price_flops"]),
                     "Median über 30 Seeds": f"{table[r]['pivots_median']:.0f} (Spanne {table[r]['pivots_min']} bis {table[r]['pivots_max']})" if r == "random" else "-"})
    st.markdown(f"**Alle fünf Regeln auf dieser Instanz** ({S.KIND_LABELS[kind].split(' (')[0]}, n = {inst.n}; die Zufallsregel mit Seed 0):")
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.plotly_chart(build_rule_bars(table), width="stretch", key="s4_bars")
    st.caption("Pivots je Regel (logarithmische Achse); bei der Zufallsregel der Median über 30 Seeds. Rechenoperationen im dichten Tableau, Preisgebung mitgezählt; ein Näherungsmaß, keine Laufzeit.")

st.markdown("---")

# --- Kennzahlen --------------------------------------------------------------------------------------------------------------------------------

st.markdown("## ⚙️ Der gewählte Lauf")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Pivots", thousands(res.total_pivots), delta=C.RULE_SHORT[rule], delta_color="off")
m2.metric("Ecken 2ⁿ", thousands(2 ** inst.n), delta=f"n = {inst.n}", delta_color="off")
m3.metric("Operationen", thousands(res.total_flops), delta=f"{thousands(res.flops_per_pivot)} je Pivot", delta_color="off")
m4.metric("Ergebnis", num(res.obj) if res.status == "optimal" and abs(res.obj) < 1e7 else (f"{res.obj:.3g}" if res.status == "optimal" else "-"), delta=STATUS_TEXT[res.status], delta_color="off")

st.markdown("---")

# --- Grenzen -----------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Der Standardwürfel ist "der" schlimmste Fall.** | Er ist es nur für die Dantzig-Regel: Größter Zuwachs und Steepest Edge lösen ihn mit 1 Pivot, die Zufallsregel im Median mit 19 (n = 12). Für jede einfache Regel gibt es einen eigenen verformten Würfel (Jeroslow 1973 für den größten Zuwachs, Goldfarb und Sit 1979 für Steepest Edge) - hier nur genannt, nicht gebaut. | Regel-Varianten, Zufallsregeln |
| **Exponentiell viele Pivots heißt: LP ist schwer.** | Nein: die Schranke gilt für die Regel, nicht für das Problem. Ellipsoid-Methode und Innere Punkte lösen jedes LP in polynomialer Zeit (folgende Stücke der Reihe, noch nicht gebaut). | Ellipsoid, Innere Punkte |
| **Ein Würfel taucht in der Praxis auf.** | Er ist konstruiert; schon kleines Rauschen löst ihn auf (Schritt 3). Zufällige Instanzen brauchen im Median 1,5 bis 6,5 Pivots (n = 2 bis 14). Eine echte Praxis-Statistik ist das nicht: die Zufallsinstanzen sind synthetisch. | Geglättete Analyse |
| **Multiplikativ und additiv sind gleich stark.** | Sie sind es nicht: additives Rauschen ist relativ zum größten Eintrag der Zeile skaliert und trifft auch die Nullen; deshalb wirken gleiche σ-Werte sehr verschieden. Ein Vergleich gilt nur je Störungsart. | Modellwahl der Störung |
| **Die Form der Formulierung ist gleichgültig.** | Die ε-Form des Originals (x ≥ 0, ε = 1/3) löst Dantzig mit 1 Pivot; erst die Chvátal-Form ist der Würfel für dieses Standardformat. | Umformulierung, Präsolve |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Chvátals Klee-Minty-Würfel.** $\max \sum_{j=1}^n 2^{n-j} x_j$ unter $2 \sum_{j<i} 2^{i-j} x_j + x_i \le 5^i$ für $i = 1, \dots, n$ und $x \ge 0$. Das Polytop ist ein verformter Würfel mit $2^n$ Ecken, das Optimum ist $x = (0, \dots, 0, 5^n)$ mit dem Wert $5^n$.
Alle Koeffizienten sind ganz, und für $n \le 14$ bleibt jedes Tableau in Gleitkomma exakt ($5^{14} < 2^{53}$).

**Dantzig-Regel.** Ab dem Ursprung besucht die Regel jede Ecke genau einmal: $2^n - 1$ Pivots (Klee und Minty 1972; hier für $n \le 14$ nachgemessen). Eine Regel ist nur so gut wie ihr Blick auf die nächste Kante; das Polytop hat aber jede Kante lokal "steil".

**Bland-Regel auf dem Würfel.** Gemessen: $2 F_{n+1} - 1$ Pivots mit den Fibonacci-Zahlen $F_1 = F_2 = 1$ (für $n \le 13$ exakt nachgemessen), also exponentiell mit Basis $\varphi \approx 1.618$.

**Störung.** Multiplikativ: $a_{ij} \mapsto a_{ij}(1 + \sigma z)$ mit $z \sim N(0, 1)$, Nullen bleiben null. Additiv: $a_{ij} \mapsto a_{ij} + \sigma \max_k |a_{ik}| \, z_{ij}$ für jede Zahl einschließlich der Nullen (Modell der geglätteten Analyse, Spielman und Teng 2004).

**Literatur.** Klee, V., & Minty, G. J. (1972). *How good is the simplex algorithm?* In O. Shisha (Hrsg.), Inequalities III, 159-175. Academic Press. Spielman, D. A., & Teng, S.-H. (2004). *Smoothed analysis of algorithms: Why the simplex algorithm usually takes polynomial time.*
Journal of the ACM 51(3), 385-463. Bach, E., & Huiberts, S. (2025). *Optimal smoothed analysis of the simplex method.* arXiv:2504.04197 (FOCS 2025), nur genannt: verbessert die Schranke für die geglättete Zahl der Pivots.

Implementiert in `kle_algorithm.py` (Simplex mit fünf Regeln, Ecken-Aufzählung), `kle_scenario.py` (Würfel, Störungen, Zufallsinstanzen), `kle_evaluation.py` (Kurven über n, Glättung, Regeltabelle).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
