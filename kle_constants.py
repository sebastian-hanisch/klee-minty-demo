"""Konstanten der Demo Klee-Minty: Regler-Bereiche, feste Instanzen, Presets (Werte aus der Vormessung)."""
N_MIN, N_MAX, DEFAULT_N = 2, 14, 3
SIGMA_OPTIONS = (0.0, 1e-6, 1e-4, 1e-3, 1e-2, 3e-2, 1e-1, 3e-1)
DEFAULT_SIGMA = 1e-1
SEED_MAX = 999999
DEFAULT_SEED = 35
RULE_LABELS = {"dantzig": "Dantzig (kleinste reduzierte Kosten)", "greatest": "Größter Zuwachs", "steepest": "Steepest Edge", "bland": "Bland (kleinster Index)", "random": "Zufall"}
RULE_SHORT = {"dantzig": "Dantzig", "greatest": "Größter Zuwachs", "steepest": "Steepest Edge", "bland": "Bland", "random": "Zufall"}
DEFAULT_RULE = "dantzig"
STEPS = {1: "1 · Der Würfel", 2: "2 · Pivots über n", 3: "3 · Störung", 4: "4 · Aufwand"}
CURVE_NS = tuple(range(2, 15))
SMOOTH_NS = (8, 10, 12)
SMOOTH_SEEDS = tuple(range(300000, 300020))
TYPICAL_SEEDS = tuple(range(200000, 200030))
RANDOM_RULE_SEEDS = tuple(str(s) for s in range(30))

PRESETS = {
    "Der Würfel (n = 3)": {"kind": "klee_minty", "n": 3, "rule": "dantzig", "step": 1, "path_i": 7},
    "Das Quadrat (n = 2)": {"kind": "klee_minty", "n": 2, "rule": "dantzig", "step": 1, "path_i": 3},
    "n = 10: 1 023 Pivots": {"kind": "klee_minty", "n": 10, "rule": "dantzig", "step": 1},
    "Steepest Edge: ein Pivot": {"kind": "klee_minty", "n": 10, "rule": "steepest", "step": 4},
    "Bland: 465 Pivots": {"kind": "klee_minty", "n": 12, "rule": "bland", "step": 4},
    "Zufallsregel auf dem Würfel": {"kind": "klee_minty", "n": 12, "rule": "random", "seed": 35, "step": 4},
    "Multiplikative Störung": {"kind": "perturbed_mult", "n": 12, "sigma": 0.1, "seed": 35, "rule": "dantzig", "step": 3},
    "Additive Störung": {"kind": "perturbed_add", "n": 12, "sigma": 1e-4, "seed": 35, "rule": "dantzig", "step": 3},
    "ε-Form: ein Pivot": {"kind": "klee_minty_eps", "n": 8, "rule": "dantzig", "step": 1},
    "Typisch gegen schlimmst": {"kind": "random", "n": 12, "seed": 35, "rule": "dantzig", "step": 2},
}
PRESET_HELP = {
    "Der Würfel (n = 3)": "Chvátals Würfel mit drei Diensten: Dantzig läuft über alle 8 Ecken und braucht 2³ − 1 = 7 Pivots. Der Pivot-Regler zeigt den Pfad Ecke für Ecke.",
    "Das Quadrat (n = 2)": "Der kleinste Würfel: ein verformtes Viereck mit 4 Ecken; Dantzig braucht 3 Pivots und besucht alle vier.",
    "n = 10: 1 023 Pivots": "Zehn Dienste: der Würfel hat 1 024 Ecken, Dantzig braucht 1 023 Pivots (2¹⁰ − 1) für ein LP mit nur 10 Bedingungen.",
    "Steepest Edge: ein Pivot": "Auf demselben Würfel mit n = 10 findet Steepest Edge (wie der größte Zuwachs) das Optimum mit 1 Pivot statt 1 023: die Regel sieht die Länge der Kante.",
    "Bland: 465 Pivots": "Bland auf dem Würfel mit n = 12: 465 Pivots statt 4 095 bei Dantzig, aber immer noch exponentiell (2·F(n+1) − 1 mit den Fibonacci-Zahlen).",
    "Zufallsregel auf dem Würfel": "Zufallsregel, n = 12: mit Seed 0 nur 3 Pivots, im Median über 30 Seeds 19 (Spanne in der Tabelle) gegen 4 095 bei Dantzig.",
    "Multiplikative Störung": "Jede von null verschiedene Zahl mal (1 + 0,1 z): Dantzig braucht bei n = 12 statt 4 095 nur noch 671 Pivots. Schritt 3 zeigt die Kurve über die Störstärke.",
    "Additive Störung": "Additives Rauschen 1e-4 (auch auf den Nullen): Dantzig braucht bei n = 12 nur noch 132 Pivots. Schritt 3 vergleicht beide Störungsarten.",
    "ε-Form: ein Pivot": "Die ursprüngliche ε-Form des Würfels (ε = 1/3, n = 8): mit x ≥ 0 als Standardform braucht schon Dantzig 1 Pivot; die Form der Formulierung entscheidet.",
    "Typisch gegen schlimmst": "Zufallsinstanz mit 12 Ressourcen: Dantzig braucht 5 Pivots, auf dem Würfel 4 095. Schritt 2 zeigt beide Kurven über n.",
}
