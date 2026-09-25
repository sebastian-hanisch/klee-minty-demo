"""Plotly-Abbildungen: Würfel mit Simplex-Pfad (n = 2 und n = 3), Zielwert je Pivot, Pivots über n (log), Glättung, Regelbalken.
Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht zoomen; die 3D-Ansicht hat eine feste Kamera."""

import numpy as np
import plotly.graph_objects as go

import kle_algorithm as A

TEAL, ORANGE, RED, BLUE, GREY, PURPLE = "#2F6B65", "#e8a13a", "#d62728", "#1f4e9c", "#8a8f98", "#7b3fbf"
RULE_COLORS = {"dantzig": TEAL, "greatest": ORANGE, "steepest": PURPLE, "bland": RED, "random": GREY}
RULE_NAMES = {"dantzig": "Dantzig", "greatest": "Größter Zuwachs", "steepest": "Steepest Edge", "bland": "Bland", "random": "Zufall"}
RULES = ("dantzig", "greatest", "steepest", "bland", "random")


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height, legend_y=-0.25):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=legend_y), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def path_points(res, n):
    """Punkte des Pfads: Start im Ursprung, dann die Basislösung nach jedem Pivot."""
    return [(0.0,) * n] + [p.x for p in res.pivots]


def build_square(inst, vertices, res, k):
    """n = 2: Zulässigkeitsmenge (Viereck), Ecken, Pfad bis Pivot k."""
    pts = [v[0] for v in vertices]
    ctr = np.mean(pts, axis=0)
    order = sorted(range(len(pts)), key=lambda i: float(np.arctan2(pts[i][1] - ctr[1], pts[i][0] - ctr[0])))
    poly = [pts[i] for i in order]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[p[0] for p in poly] + [poly[0][0]], y=[p[1] for p in poly] + [poly[0][1]], mode="lines", fill="toself", fillcolor="rgba(47,107,101,0.13)", line=dict(color=GREY, width=1.5), name="zulässig",
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="markers", marker=dict(size=9, color="white", line=dict(width=1.5, color=GREY)), name="Ecken", hoverinfo="skip"))
    path = path_points(res, 2)
    k = max(0, min(k, len(path) - 1))
    if k:
        fig.add_trace(go.Scatter(x=[p[0] for p in path[:k + 1]], y=[p[1] for p in path[:k + 1]], mode="lines+markers", line=dict(color=ORANGE, width=4), marker=dict(size=8), name="Simplex-Pfad", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[path[k][0]], y=[path[k][1]], mode="markers", marker=dict(size=15, color=ORANGE, line=dict(width=2, color="white")), name="aktuelle Ecke", hoverinfo="skip"))
    fig.update_xaxes(title_text=inst.names[0])
    fig.update_yaxes(title_text=inst.names[1])
    return _base(fig, 420, legend_y=-0.3)


def build_cube3d(inst, vertices, res, k):
    """n = 3: Kanten und Ecken des Polytops, Pfad bis Pivot k in Orange (feste Kamera)."""
    edges = A.vertex_edges(vertices)
    pts = [v[0] for v in vertices]
    fig = go.Figure()
    xs, ys, zs = [], [], []
    for i, j in edges:
        xs += [pts[i][0], pts[j][0], None]
        ys += [pts[i][1], pts[j][1], None]
        zs += [pts[i][2], pts[j][2], None]
    fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode="lines", line=dict(color=GREY, width=3), name="Kanten", hoverinfo="skip"))
    fig.add_trace(go.Scatter3d(x=[p[0] for p in pts], y=[p[1] for p in pts], z=[p[2] for p in pts], mode="markers", marker=dict(size=4, color="white", line=dict(width=1.5, color=GREY)), name="Ecken", hoverinfo="skip"))
    path = path_points(res, 3)
    k = max(0, min(k, len(path) - 1))
    if k:
        fig.add_trace(go.Scatter3d(x=[p[0] for p in path[:k + 1]], y=[p[1] for p in path[:k + 1]], z=[p[2] for p in path[:k + 1]], mode="lines+markers", line=dict(color=ORANGE, width=8), marker=dict(size=4, color=ORANGE),
                                   name="Simplex-Pfad", hoverinfo="skip"))
    fig.add_trace(go.Scatter3d(x=[path[k][0]], y=[path[k][1]], z=[path[k][2]], mode="markers", marker=dict(size=9, color=ORANGE, line=dict(width=2, color="white")), name="aktuelle Ecke", hoverinfo="skip"))
    fig.update_layout(height=470, margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=-0.05), scene=dict(xaxis_title=inst.names[0], yaxis_title=inst.names[1], zaxis_title=inst.names[2],
                                                                                                        camera=dict(eye=dict(x=1.55, y=-1.6, z=0.9))))
    return fig


def build_progress(res):
    """Zielwert nach jedem Pivot (Start = 0)."""
    ys = [0.0] + [p.obj for p in res.pivots]
    fig = go.Figure(go.Scatter(x=list(range(len(ys))), y=ys, mode="lines", line=dict(color=TEAL, width=2.5, shape="hv"), name="Zielwert"))
    fig.update_xaxes(title_text="Pivot")
    fig.update_yaxes(title_text="Zielwert")
    return _base(fig, 320, legend_y=-0.3)


def build_curves(rows):
    """Pivots über n (logarithmische Achse): Würfel je Regel, Zufallsregel als Median mit Band, 2^n - 1 und der typische Fall auf Zufallsinstanzen."""
    ns = [r["n"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ns, y=[r["cube_bound"] for r in rows], mode="lines", line=dict(color="black", width=1.5, dash="dot"), name="2ⁿ − 1 (alle Ecken)"))
    fig.add_trace(go.Scatter(x=ns + ns[::-1], y=[r["random_hi"] for r in rows] + [r["random_lo"] for r in rows][::-1], mode="lines", fill="toself", fillcolor="rgba(138,143,152,0.15)", line=dict(width=0),
                             showlegend=False, hoverinfo="skip"))
    for rule in ("dantzig", "bland", "greatest", "steepest"):
        fig.add_trace(go.Scatter(x=ns, y=[r[rule] for r in rows], mode="lines+markers", line=dict(color=RULE_COLORS[rule], width=2.5), name=f"{RULE_NAMES[rule]} auf dem Würfel"))
    fig.add_trace(go.Scatter(x=ns, y=[r["random"] for r in rows], mode="lines+markers", line=dict(color=GREY, width=2.5), name="Zufall auf dem Würfel (Median)"))
    fig.add_trace(go.Scatter(x=ns, y=[r["typical"] for r in rows], mode="lines+markers", line=dict(color=BLUE, width=2.5, dash="dash"), name="Dantzig auf Zufallsinstanzen (Median)"))
    fig.update_xaxes(title_text="n (Dienste = Ressourcen)", dtick=1)
    fig.update_yaxes(title_text="Pivots (logarithmisch)", type="log")
    return _base(fig, 420, legend_y=-0.4)


def build_smoothing(series, n, rule):
    """`series` = {Name: Zeilen von smoothing_curve}: Pivots über die Störstärke (Median, Band 10. bis 90. Perzentil) gegen die Ecken-Grenze 2^n - 1."""
    fig = go.Figure()
    colors = [TEAL, RED]
    for (name, rows), color in zip(series.items(), colors):
        xs = [_label(r["sigma"]) for r in rows]
        lo = [None if r["pivots_lo"] != r["pivots_lo"] else r["pivots_lo"] for r in rows]
        hi = [None if r["pivots_hi"] != r["pivots_hi"] else r["pivots_hi"] for r in rows]
        rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
        if all(v is not None for v in lo + hi):
            fig.add_trace(go.Scatter(x=xs + xs[::-1], y=hi + lo[::-1], mode="lines", fill="toself", fillcolor=f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.13)", line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=xs, y=[None if r["pivots"] != r["pivots"] else r["pivots"] for r in rows], mode="lines+markers", line=dict(color=color, width=2.5), name=name, connectgaps=False))
    xs = [_label(r["sigma"]) for r in next(iter(series.values()))]
    fig.add_trace(go.Scatter(x=xs, y=[2 ** n - 1] * len(xs), mode="lines", line=dict(color="black", width=1.5, dash="dot"), name="2ⁿ − 1"))
    fig.update_xaxes(title_text="Störstärke σ", type="category")
    fig.update_yaxes(title_text=f"Pivots ({RULE_NAMES[rule]}, logarithmisch)", type="log")
    return _base(fig, 400, legend_y=-0.4)


def _label(sigma):
    return "0" if sigma == 0 else (f"{sigma:g}" if sigma >= 0.01 else f"{sigma:.0e}".replace("e-0", "e-"))


def build_rule_bars(table):
    """Pivots je Regel (logarithmisch); bei der Zufallsregel der Median über 30 Seeds."""
    rules = [r for r in RULES if r in table]
    ys = [table[r]["pivots_median"] if r == "random" else table[r]["pivots"] for r in rules]
    fig = go.Figure(go.Bar(x=[RULE_NAMES[r] for r in rules], y=ys, marker_color=[RULE_COLORS[r] for r in rules], text=[f"{v:g}" for v in ys], textposition="outside"))
    fig.update_yaxes(title_text="Pivots (logarithmisch)", type="log")
    return _base(fig, 320, legend_y=-0.3)
