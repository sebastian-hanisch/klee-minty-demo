# Klee-Minty – der Würfel, auf dem der Simplex alle Ecken besucht – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-klee-minty-demo.streamlit.app/)**

Drittes Stück der **Lineare-Programmierung-Reihe** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning", Kind von [pivotregeln-demo](https://github.com/sebastian-hanisch/pivotregeln-demo). Auf den zufälligen Instanzen der ersten beiden Stücke brauchte der Simplex wenige Pivots (etwa einen halben je Ressource). Geht das immer so? **Klee und Minty (1972)** bauten einen **verformten Würfel** in n Dimensionen, auf dem die Dantzig-Regel von Ecke zu Ecke über **alle 2ⁿ Ecken** läuft. Die Demo verwendet Chvátals Form des Würfels (maximiere Σⱼ 2ⁿ⁻ʲ xⱼ unter 2 · Σ über j < i von 2ⁱ⁻ʲ xⱼ, plus xᵢ, höchstens 5ⁱ) und stellt vier Fragen, alle gemessen: **(1) Der Würfel** – wie sieht der Pfad aus, und stimmen 2ⁿ − 1 Pivots? **(2) Pivots über n** – wie schneiden die anderen Regeln aus Stück 2 auf demselben Würfel ab, verglichen mit dem typischen Fall? **(3) Störung** – wie schnell zerstört Rauschen in den Daten den Würfel, und hängt das davon ab, wie man stört? **(4) Aufwand** – Pivots und Rechenoperationen aller Regeln bei einem n.

**Einordnung in die Reihe:** die Reihe hat elf Stücke, dies ist das dritte (Details in `lp-planung/PLAN.md` des Portfolio-Ordners):

```
Tableau-Simplex (Wurzel)                                                                  [gebaut: tableau-simplex-demo]
 ├─ Pivotregeln & Entartung                                                               [gebaut: pivotregeln-demo]
 │    └─ Simplex im schlimmsten und im typischen Fall (Klee-Minty)                        [DIESES STÜCK]
 ├─ Revised Simplex ─ Präsolve, Skalierung & Numerik                                     [gebaut: revised-simplex-demo, praesolve-demo]
 ├─ Dualität & Sensitivität ─ Dualer Simplex & Neuoptimierung                            [gebaut: lp-dualitaet-demo, dualer-simplex-demo]
 ├─ Ellipsoid-Methode (Kontrast: polynomial in der Theorie)                              [gebaut: ellipsoid-demo]
 └─ Innere Punkte ─ PDLP (Verfahren erster Ordnung) ─ Crossover & Simplex gegen Innere Punkte gegen PDLP  [gebaut: innere-punkte-demo, pdlp-demo, crossover-demo]
```

Ergebnis in Kürze: **Der Würfel ist ein Würfel für die Dantzig-Regel, nicht für den Simplex.** Dantzig braucht auf Chvátals Würfel genau **2ⁿ − 1 Pivots** (n = 1 bis 14 gemessen: bei n = 14 sind es 16 383 Pivots und 13,8 Millionen Operationen für ein LP mit 14 Bedingungen), der **größte Zuwachs** und **Steepest Edge** brauchen **einen einzigen Pivot** (bei n = 12: 913 und 937 Operationen gegen 2 559 375). **Bland** ist auf dem Würfel weiter exponentiell, aber langsamer: **2 F(n+1) − 1 Pivots** mit den Fibonacci-Zahlen (n = 12: 465, n = 14: 1 219). Die **Zufallsregel** braucht bei n = 12 im Median 19 Pivots (Spanne 1 bis 43 über 30 Seeds). Auf **zufälligen Instanzen** braucht Dantzig im Median nur 1,5 bis 6,5 Pivots (n = 2 bis 14). Ob das **Rauschen** den Würfel zerstört, hängt von der Art ab: **multiplikatives** Rauschen (jede von null verschiedene Zahl mal 1 + σ z; die Nullen bleiben) lässt den Würfelpfad bis σ = 0,01 vollständig unverändert und drückt die Pivots bei n = 12 erst ab σ = 0,03 (3 745), 0,1 (562) und 0,3 (64); **additives** Rauschen (auch auf den Nullen) senkt sie schon bei σ = 10⁻⁶ auf 933,5 und bei 10⁻⁴ auf 116.

| Frage | Ergebnis (Chvátal-Form: ganze Zahlen, alle Tableaus exakt in Gleitkomma; Pivotzahlen auf dem ungestörten Würfel sind exakt, gestörte Läufe **Median über 20 Störungen**, Seeds 300000–300019, Zufallsinstanzen Median über 30 Instanzen, Seeds 200000–200029; Aufwand in Gleitkomma-Operationen des dichten Tableaus) |
|---|---|
| **Stimmt der Würfel?** | ✅ Optimum 5ⁿ bei x = (0, …, 0, 5ⁿ), gegen HiGHS für n = 1 bis 14; das Polytop hat 2ⁿ Ecken (Aufzählung n = 2 bis 4) und n · 2ⁿ⁻¹ Kanten (Würfelgraph, jede Ecke Grad n) |
| **Dantzig: 2ⁿ − 1 Pivots** | ✅ **Exakt** für n = 1 bis 14. Der Pfad besucht jede der 2ⁿ Ecken genau einmal (n = 2 bis 4 nachgeprüft), aufeinanderfolgende Ecken sind Nachbarn, der Zielwert steigt streng, kein Nullschritt, kein Gleichstand im Quotiententest. Alle Tableau-Einträge bleiben ganzzahlig (n = 2 bis 6) |
| **Andere Regeln auf dem Würfel** | Größter Zuwachs und Steepest Edge: **1 Pivot** für jedes n = 2 bis 14. Bland: 3, 5, 9, 15, 25, 41, 67, 109, 177, 287, 465, 753, 1 219 Pivots (n = 2 bis 14), gleich **2 F(n+1) − 1** (n = 1 bis 13 nachgeprüft), Wachstum mit Basis φ ≈ 1,618 statt 2. Zufall (Median über 30 Seeds): 1, 3, 5, 5, 9, 10, 9, 13, 15, 20, 19, 24, 27 |
| **Schlimmst gegen typisch** | Dantzig auf Zufallsinstanzen (n Ressourcen, n Dienste, Dichte 0,5), Median: 1,5 / 2 / 2 / 3 / 3 / 3 / 4 / 5 / 5,5 / 6 / 5 / 6,5 / 6 Pivots für n = 2 bis 14, auf dem Würfel 3 bis 16 383. Bei n = 12 sind es 5 gegen 4 095 |
| **Rauschen, multiplikativ** | Der Würfelpfad ist bis σ = 0,01 **unverändert** (n = 8, 10, 12: 255 / 1 023 / 4 095). σ = 0,03: 255 / 1 007 / 3 745; σ = 0,1: 104 / 342,5 / 562; σ = 0,3: 18,5 / 44 / 64. Kein Lauf wird unbeschränkt |
| **Rauschen, additiv** | Schon σ = 10⁻⁶ verkürzt den Pfad: 255 / 709,5 / 933,5 (n = 8, 10, 12); σ = 10⁻⁴: 106 / 110,5 / 116; σ = 10⁻² : 20 / 20 / 28; σ = 0,1: 7,5 / 9 / 13. **Ab σ = 0,03 werden einzelne Instanzen unbeschränkt** (n = 8: 1 von 20, n = 12 bei σ = 0,1: 1 von 20, bei 0,3: 2 von 20): die Nullen tragen nicht mehr |
| **Form der Formulierung** | Die ursprüngliche **ε-Form** des Würfels (x₁ ≤ 1, ε xᵢ₋₁ ≤ xᵢ ≤ 1 − ε xᵢ₋₁, ε = 1/3) braucht in der Standardform x ≥ 0 nur **1 Pivot** bei jeder Regel (n = 2 bis 14): nicht jede Umformulierung des Polytops ist ein schlimmster Fall, es kommt auf die Formulierung an |

## Was die Demo zeigt

1. **Vier Schritte** (Schritt-Slider): **Der Würfel** (n = 2: das verformte Viereck mit dem Pfad; n = 3: der 3D-Würfel mit Pfad-Regler über alle Pivots; größere n: Zielwert nach jedem Pivot) → **Pivots über n** (log-Achse: Dantzig, Bland, größter Zuwachs, Steepest Edge, Zufall mit Band und Dantzig auf Zufallsinstanzen gegen 2ⁿ − 1, auf Abruf) → **Störung** (Pivots über die Störstärke σ für die gewählte Regel, multiplikativ und additiv im selben Diagramm, Band 10. bis 90. Perzentil, auf Abruf für n = 8, 10, 12) → **Aufwand** (Tabelle und Balken aller fünf Regeln auf der gewählten Instanz).
2. **Kennzahlen des gewählten Laufs:** Pivots, Ecken 2ⁿ, Operationen, Ergebnis.
3. **Instanzen:** Chvátals Würfel, ε-Form, gestörter Würfel (multiplikativ, additiv), Zufallsinstanz.

Presets (10): Der Würfel (n = 3), Das Quadrat (n = 2), n = 10: 1 023 Pivots, Steepest Edge: ein Pivot, Bland: 465 Pivots, Zufallsregel auf dem Würfel, Multiplikative Störung, Additive Störung, ε-Form: ein Pivot, Typisch gegen schlimmst.

## Messwerte der Presets

| Preset | Einstellungen | Ergebnis |
|---|---|---|
| **Der Würfel (n = 3)** | Chvátal, Dantzig | 8 Ecken, 7 Pivots (2³ − 1), Optimum 125 |
| **Das Quadrat (n = 2)** | Chvátal, Dantzig | 4 Ecken, 3 Pivots, Optimum 25 |
| **n = 10: 1 023 Pivots** | Chvátal, Dantzig | 1 024 Ecken, 1 023 Pivots, 451 143 Operationen |
| **Steepest Edge: ein Pivot** | n = 10, Steepest Edge | 1 Pivot (661 Operationen) |
| **Bland: 465 Pivots** | n = 12, Bland | 465 Pivots statt 4 095 bei Dantzig |
| **Zufallsregel auf dem Würfel** | n = 12, Zufall, Seed 35 | Seed 0: 3 Pivots; Median über 30 Seeds 19 |
| **Multiplikative Störung** | n = 12, σ = 0,1, Seed 35 | 671 Pivots (Median über 20 Störungen 562) |
| **Additive Störung** | n = 12, σ = 10⁻⁴, Seed 35 | 132 Pivots (Median über 20 Störungen 116) |
| **ε-Form: ein Pivot** | ε = 1/3, n = 8 | 1 Pivot |
| **Typisch gegen schlimmst** | Zufallsinstanz n = 12, Seed 35 | 5 Pivots gegen 4 095 auf dem Würfel |

## Modell und Verfahren

- **Instanz** (`kle_scenario.py`): das Kaskaden-Modell aus dem Reihen-Vehikel: Dienst i belastet die Ressourcen ab Stufe i, jeweils doppelt so stark wie der vorherige (Chvátals Form), Bestand 5ⁱ, Deckungsbeitrag 2ⁿ⁻ʲ. Dazu die ε-Form des Originals, gestörte Würfel (multiplikativ: jede von null verschiedene Zahl mal max(0,1; 1 + σ z); additiv: zu jedem Koeffizienten σ mal dem größten Betrag seiner Zeile mal z, zu jedem Deckungsbeitrag σ mal dem größten Deckungsbeitrag mal z, Bestände multiplikativ) und Zufallsinstanzen (wie in den Vorgängerstücken).
- **Simplex** (`kle_algorithm.py`): der Kern aus Stück 2 (fünf Regeln, Zwei-Phasen-Start) mit **schneller Pivotschleife** (nur Zeilen mit Eintrag ≠ 0 werden eliminiert; das Ergebnis ist mit der einfachen Schleife identisch, per Test) und einer **Pivot-Grenze** (`limit`), damit die Demo nie ewig rechnet. Zusätzlich die Ecken-Aufzählung für n ≤ 4 (jede Auswahl von n aus den 2n Grenzen; Nachbarn teilen n − 1 bindende Grenzen) und die Formel 2 F(n+1) − 1 für Bland.
- **Aufwand:** ein Pivot kostet (Spalten + 1) + 2 · m · (Spalten + 1) Operationen, dazu die Preisgebung der Regel (wie in Stück 2). Ein Näherungsmaß, keine Laufzeit.

## Was nicht funktioniert hat / Grenzen

- **Vorab-Hypothese "andere Regeln entkommen dem Standardwürfel nicht" – widerlegt für den größten Zuwachs, Steepest Edge und Zufall, bestätigt für Bland.** Der Standardwürfel ist ein schlimmster Fall für Dantzig, nicht für den Simplex. Für jede einfache Regel gibt es einen eigenen verformten Würfel (Jeroslow 1973 für den größten Zuwachs, Goldfarb und Sit 1979 für Steepest Edge): hier nur genannt, nicht gebaut. Aussagen über "die Regel X ist exponentiell" gelten je Instanzfamilie.
- **Vorab-Hypothese "kleine Störung zerstört den Würfel" – nur halb bestätigt.** Multiplikatives Rauschen lässt den Pfad bis σ = 0,01 unverändert, weil die Nullen null bleiben und die Zeilenstruktur trägt; erst ab einigen Prozent bricht er ein. Additives Rauschen (auch auf den Nullen, das Modell der geglätteten Analyse) zerstört ihn schon bei 10⁻⁶ teilweise. Die σ-Werte beider Arten sind **nicht vergleichbar** (additiv ist relativ zum größten Eintrag der Zeile skaliert).
- **Additives Rauschen kann die Instanz unbeschränkt machen** (ab σ = 0,03); solche Läufe stehen nicht in den Medianen und werden je Stufe ausgewiesen.
- **Die Schranke gilt für die Regel, nicht für das Problem.** Ellipsoid-Methode und Innere Punkte lösen jedes LP polynomial (folgende Stücke). Ob es eine Simplex-Regel mit polynomial vielen Pivots gibt, ist offen (die strenge Polynomialität ist ungelöst).
- **Der Würfel ist konstruiert.** Er taucht in der Praxis nicht auf; die Zufallsinstanzen sind synthetisch, sie zeigen also nicht, wie viele Pivots echte LPs brauchen. Die geglättete Analyse (Spielman und Teng 2004) erklärt, warum die Pivotzahl unter Rauschen polynomial bleibt; die bislang beste Schranke stammt von Bach und Huiberts (2025) – hier nur genannt, nicht nachgerechnet.
- **Nur die fünf einfachen Regeln aus Stück 2**, kein Devex, keine Randomisierung nach Kalai/Matoušek/Sharir–Welzl (subexponentielle Schranken), n höchstens 14 (5¹⁴ < 2⁵³, sonst ist die Gleitkomma-Arithmetik nicht mehr exakt).
- **Störungsläufe nur für n = 8, 10, 12** (Rechenzeit); die Kurven für n = 14 wären mit 16 383 Pivots je ungestörtem Lauf langsam.

## Verifikation

- `tests/test_algorithm.py`: Würfel-Struktur (n = 1 bis 14), Optimum 5ⁿ gegen HiGHS, **Dantzig 2ⁿ − 1 Pivots exakt** (n = 1 bis 14), Pfad besucht jede Ecke einmal entlang von Kanten mit steigendem Zielwert (n = 2 bis 4), ganzzahlige Tableaus, **schnelle == einfache Pivotschleife** (jede Regel, Würfel, gestörte und zufällige Instanzen), **Bland = 2 F(n+1) − 1**, größter Zuwachs und Steepest Edge lösen den Würfel mit 1 Pivot, jede Regel gleich dem HiGHS-Optimum auf über 200 gestörten, ε- und Zufallsinstanzen (auch unbeschränkte), Pivot-Grenze, ε-Form, Determinismus und Buchführung.
- `tests/test_scenario.py`, `test_evaluation.py`, `test_presets.py` (jede Zahl der Hilfetexte), `test_claims.py` (jede Zahl aus README und App über die echten `ev.*`-Funktionen), `test_app.py` (Streamlit-AppTest: Voreinstellung, jedes Preset, jeder Schritt für jede Instanz, jede Regel, Pfad-Regler für n = 2 und 3, Randwerte, Permalink-Grenzen, bedingte Regler, Kurven und Störungskurven auf Abruf, Footer).
- Für die Prüfung genügt **pytest**; `scipy` dient nur als Gegenprobe (`requirements-dev.txt`), die App braucht nur numpy.

## Lokal starten

```bash
python -m venv venv && venv/Scripts/activate  # Windows; Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Tests: `pip install -r requirements-dev.txt` und `python -m pytest tests/ -W error::SyntaxWarning`.

## Literatur

- Klee, V., & Minty, G. J. (1972). *How good is the simplex algorithm?* In O. Shisha (Hrsg.), Inequalities III, 159–175. Academic Press.
- Chvátal, V. (1983). *Linear Programming.* W. H. Freeman (die hier verwendete Form des Würfels).
- Jeroslow, R. G. (1973). *The simplex algorithm with the pivot rule of maximizing criterion improvement.* Discrete Mathematics 4, 367–377.
- Goldfarb, D., & Sit, W. Y. (1979). *Worst case behavior of the steepest edge simplex method.* Discrete Applied Mathematics 1, 277–285.
- Spielman, D. A., & Teng, S.-H. (2004). *Smoothed analysis of algorithms: Why the simplex algorithm usually takes polynomial time.* Journal of the ACM 51(3), 385–463.
- Bach, E., & Huiberts, S. (2025). *Optimal smoothed analysis of the simplex method.* arXiv:2504.04197 (nur genannt).

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Lineare Programmierung: vom Tableau zum Crossover](https://sebastianhanisch.net/konzepte-lineare-programmierung.html).
