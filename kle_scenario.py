"""Instanzen der Demo Klee-Minty: Kaskaden-Ressourcen als LP  max c·x,  A x <= b,  x >= 0. Der Würfel von Klee und Minty (1972) in Chvátals Form, seine ε-Form, gestörte Würfel und zufällige Instanzen."""

import random
from dataclasses import dataclass

import numpy as np

KINDS = ("klee_minty", "klee_minty_eps", "perturbed_mult", "perturbed_add", "random")
KIND_LABELS = {"klee_minty": "Klee-Minty-Würfel (Chvátal)", "klee_minty_eps": "Klee-Minty-Würfel (ε-Form des Originals)", "perturbed_mult": "Gestörter Würfel, multiplikativ (Nullen bleiben)",
               "perturbed_add": "Gestörter Würfel, additiv (jede Zahl, auch die Nullen)", "random": "Zufallsinstanz (typischer Fall)"}
NOISE_KINDS = ("perturbed_mult", "perturbed_add")
LE, GE, EQ = "<=", ">=", "="


@dataclass(frozen=True)
class Instance:
    A: tuple                      # m Zeilen mit je n Koeffizienten (Tupel, damit die Instanz hashbar bleibt)
    b: tuple
    c: tuple
    senses: tuple                 # je Zeile "<=", ">=" oder "="
    names: tuple                  # Namen der n Entscheidungsvariablen (Dienste)
    row_names: tuple              # Namen der m Bedingungen (Ressourcen)
    kind: str = "custom"

    @property
    def m(self):
        return len(self.b)

    @property
    def n(self):
        return len(self.c)

    def arrays(self):
        return np.array(self.A, dtype=float).reshape(self.m, self.n), np.array(self.b, dtype=float), np.array(self.c, dtype=float)


def _inst(A, b, c, senses, names, row_names, kind):
    return Instance(tuple(tuple(float(v) for v in row) for row in A), tuple(float(v) for v in b), tuple(float(v) for v in c), tuple(senses), tuple(names), tuple(row_names), kind)


def _names(m, n):
    return [f"Dienst {j + 1}" for j in range(n)], [f"Ressource {i + 1}" for i in range(m)]


def klee_minty_instance(n):
    """Chvátals Form des Klee-Minty-Würfels: max Summe_j 2^(n-j) x_j unter 2 Summe_(j<i) 2^(i-j) x_j + x_i <= 5^i (i = 1..n), x >= 0. Dienst i belastet die Ressourcen ab Stufe i, jeweils doppelt so stark wie
    der vorherige. Alle Zahlen sind ganz und für n <= 14 in Gleitkomma exakt (5^14 < 2^53)."""
    A = [[2.0 ** (i - j + 1) if j < i else (1.0 if j == i else 0.0) for j in range(1, n + 1)] for i in range(1, n + 1)]
    names, row_names = _names(n, n)
    return _inst(A, [5.0 ** i for i in range(1, n + 1)], [2.0 ** (n - j) for j in range(1, n + 1)], [LE] * n, names, row_names, "klee_minty")


def klee_minty_eps_instance(n, eps=1.0 / 3.0):
    """ε-Form des Originals (Klee und Minty 1972): max x_n unter 0 <= x_1 <= 1 und eps x_(i-1) <= x_i <= 1 - eps x_(i-1). Als LP mit x >= 0: x_1 <= 1; eps x_(i-1) - x_i <= 0; x_i + eps x_(i-1) <= 1."""
    rows, b, row_names = [[1.0] + [0.0] * (n - 1)], [1.0], ["Stufe 1 oben"]
    for i in range(2, n + 1):
        lo = [0.0] * n
        lo[i - 2], lo[i - 1] = eps, -1.0
        hi = [0.0] * n
        hi[i - 2], hi[i - 1] = eps, 1.0
        rows += [lo, hi]
        b += [0.0, 1.0]
        row_names += [f"Stufe {i} unten", f"Stufe {i} oben"]
    names, _ = _names(len(rows), n)
    return _inst(rows, b, [0.0] * (n - 1) + [1.0], [LE] * len(rows), names, row_names, "klee_minty_eps")


def perturbed_mult_instance(base, sigma, seed):
    """Jede von null verschiedene Zahl (Koeffizient, Bestand, Deckungsbeitrag) mal (1 + sigma z) mit z aus der Standardnormalverteilung, Faktor mindestens 0.1: die Struktur (Nullen) bleibt, der Ursprung bleibt zulässig
    (b > 0). Mit sigma = 0 kommt der Würfel unverändert zurück."""
    rng = random.Random(f"kle-perturb-mult-{seed}-{base.n}")

    def f(v):
        return v if v == 0.0 else v * max(0.1, 1.0 + sigma * rng.gauss(0.0, 1.0))
    return _inst([[f(v) for v in row] for row in base.A], [f(v) for v in base.b], [f(v) for v in base.c], base.senses, base.names, base.row_names, "perturbed_mult")


def perturbed_add_instance(base, sigma, seed):
    """Im Stil der geglätteten Analyse (Spielman und Teng): zu JEDEM Koeffizienten (auch den Nullen) kommt sigma mal dem größten Betrag seiner Zeile mal z, zu jedem Deckungsbeitrag sigma mal dem größten Deckungsbeitrag
    mal z; die Bestände werden wie oben multiplikativ gestört (Faktor mindestens 0.1). Die Instanz kann dadurch unbeschränkt werden (die Nullen tragen nicht mehr)."""
    rng = random.Random(f"kle-perturb-add-{seed}-{base.n}")
    A = []
    for row in base.A:
        r = max(abs(v) for v in row)
        A.append([v + sigma * r * rng.gauss(0.0, 1.0) for v in row])
    cmax = max(abs(v) for v in base.c)
    c = [v + sigma * cmax * rng.gauss(0.0, 1.0) for v in base.c]
    b = [v * max(0.1, 1.0 + sigma * rng.gauss(0.0, 1.0)) for v in base.b]
    return _inst(A, b, c, base.senses, base.names, base.row_names, "perturbed_add")


def random_instance(m, n, density, seed):
    """Wie in den Vorgängerstücken: nichtnegative Verbrauchskoeffizienten, alle Bedingungen <=, Gesamtkapazität in Zeile 0 dicht, damit alles beschränkt bleibt."""
    rng = random.Random(f"kle-random-{m}-{n}-{density}-{seed}")
    names, row_names = _names(m, n)
    c = [round(rng.uniform(1.0, 10.0), 2) for _ in range(n)]
    A = [[round(rng.uniform(0.5, 5.0), 2) if rng.random() < density else 0.0 for _ in range(n)] for _ in range(m)]
    for j in range(n):
        A[0][j] = round(rng.uniform(0.5, 5.0), 2)
    for i in range(m):
        if not any(A[i]):
            A[i][rng.randrange(n)] = round(rng.uniform(0.5, 5.0), 2)
    b = [round(rng.uniform(40.0, 120.0), 1) for _ in range(m)]
    return _inst(A, b, c, [LE] * m, names, row_names, "random")


def generate(kind, n, sigma=0.0, seed=0, eps=1.0 / 3.0, density=0.5):
    """Instanz je (kind, n, sigma, seed, eps, density); der Würfel und seine ε-Form sind fest, gestörte und zufällige Instanzen hängen vom Seed ab."""
    if kind == "klee_minty":
        return klee_minty_instance(n)
    if kind == "klee_minty_eps":
        return klee_minty_eps_instance(n, eps)
    if kind == "perturbed_mult":
        return perturbed_mult_instance(klee_minty_instance(n), sigma, seed)
    if kind == "perturbed_add":
        return perturbed_add_instance(klee_minty_instance(n), sigma, seed)
    if kind == "random":
        return random_instance(n, n, density, seed)
    raise ValueError(kind)
