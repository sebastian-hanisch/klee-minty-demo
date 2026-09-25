"""Auswertung: Würfel-Läufe, Kurven über n, Glättung, typischer Fall und Regeltabelle."""

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

import kle_algorithm as A
import kle_constants as C
import kle_scenario as S

INF = math.inf
PIVOT_LIMIT = 100_000


@dataclass(frozen=True)
class Settings:
    kind: str = "klee_minty"
    n: int = C.DEFAULT_N
    sigma: float = C.DEFAULT_SIGMA
    seed: int = C.DEFAULT_SEED
    rule: str = "dantzig"


@lru_cache(maxsize=256)
def instance_of(settings):
    return S.generate(settings.kind, settings.n, settings.sigma, settings.seed)


@dataclass
class Analysis:
    settings: Settings
    inst: object
    res: object
    vertices: list                     # [(x, bindende Bedingungen)] für n <= 4, sonst leer

    @property
    def status(self):
        return self.res.status

    @property
    def cube_vertices(self):
        return 2 ** self.inst.n

    @property
    def certificate(self):
        if self.res.status != "optimal":
            return None
        b = np.array(self.inst.b)
        return {"primal": A.primal_violation(self.inst, self.res.x), "dual": A.dual_violation(self.inst, self.res.duals), "gap": abs(self.res.obj - float(np.dot(self.res.duals, b)))}


@lru_cache(maxsize=64)
def analyse(settings):
    inst = instance_of(settings)
    res = A.tableau_simplex(inst, rule=settings.rule, seed=str(settings.seed), max_pivots=PIVOT_LIMIT)
    return Analysis(settings, inst, res, A.vertices_nd(inst) if inst.n <= 4 else [])


def _stats(values):
    values = [v for v in values if v is not None and v == v and v != INF]
    if not values:
        return float("nan"), float("nan"), float("nan")
    return float(np.median(values)), float(np.percentile(values, 10)), float(np.percentile(values, 90))


def run(inst, rule="dantzig", seed="0"):
    r = A.tableau_simplex(inst, rule=rule, seed=seed, max_pivots=PIVOT_LIMIT)
    return {"status": r.status, "pivots": r.total_pivots, "flops": r.total_flops, "price_flops": r.price_flops, "obj": r.obj}


@lru_cache(maxsize=64)
def rule_table(kind, n, sigma, seed):
    """Alle fünf Regeln auf derselben Instanz (Zufallsregel mit Seed 0 und Median über 30 Seeds)."""
    inst = S.generate(kind, n, sigma, seed)
    out = {rule: run(inst, rule) for rule in A.RULES}
    rr = [run(inst, "random", s) for s in C.RANDOM_RULE_SEEDS]
    out["random"]["pivots_median"] = float(np.median([x["pivots"] for x in rr]))
    out["random"]["pivots_min"], out["random"]["pivots_max"] = min(x["pivots"] for x in rr), max(x["pivots"] for x in rr)
    return out


@lru_cache(maxsize=16)
def cube_curve(ns=C.CURVE_NS):
    """Pivots über n auf Chvátals Würfel für alle Regeln (Zufall: Median und Spanne über 30 Seeds); dazu die Ecken 2^n und der typische Fall (Zufallsinstanzen)."""
    rows = []
    for n in ns:
        inst = S.klee_minty_instance(n)
        row = {"n": n, "vertices": 2 ** n, "cube_bound": 2 ** n - 1}
        for rule in ("dantzig", "greatest", "steepest", "bland"):
            row[rule] = run(inst, rule)["pivots"]
        rr = [run(inst, "random", s)["pivots"] for s in C.RANDOM_RULE_SEEDS]
        row["random"], row["random_lo"], row["random_hi"] = _stats(rr)
        row["typical"] = float(np.median([run(S.random_instance(n, n, 0.5, s), "dantzig")["pivots"] for s in C.TYPICAL_SEEDS]))
        rows.append(row)
    return rows


@lru_cache(maxsize=32)
def smoothing_curve(kind, n, rule="dantzig", sigmas=C.SIGMA_OPTIONS, seeds=C.SMOOTH_SEEDS):
    """Pivots über die Störstärke sigma auf dem gestörten Würfel (Median, 10./90. Perzentil über `seeds`); Läufe mit anderem Ausgang als "optimal" (unbeschränkt, Grenze) getrennt gezählt."""
    rows = []
    for sigma in sigmas:
        results = [run(S.generate(kind, n, sigma, s), rule, str(s)) for s in seeds]
        ok = [r for r in results if r["status"] == "optimal"]
        med, lo, hi = _stats([r["pivots"] for r in ok])
        rows.append({"sigma": sigma, "pivots": med, "pivots_lo": lo, "pivots_hi": hi, "solved": len(ok), "unbounded": sum(r["status"] == "unbounded" for r in results),
                     "limit": sum(r["status"] == "limit" for r in results), "n_runs": len(results), "cube_bound": 2 ** n - 1})
    return rows


def sigma_label(sigma):
    return "0" if sigma == 0 else (f"{sigma:g}" if sigma >= 0.01 else f"{sigma:.0e}".replace("e-0", "e-"))
