# SAT in der Praxis: DPLL und Phasenübergang – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-sat-phasenuebergang-demo.streamlit.app/)** -->

Viertes Stück der **Komplexitätsklassen-Reihe** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, Fortsetzung von Stück 3 ([reduktionskette-demo](https://github.com/sebastian-hanisch/reduktionskette-demo)). Anders als die Fall-Demos (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt sie **eine Frage der Komplexitätstheorie** an einem wachsenden Beispiel: Stück 3 hat gezeigt, dass die Formel selbst in wenigen DPLL-Knoten entschieden ist, während die Graphlöser am Budget scheitern. Dieses Stück fragt nach dem Grund: **Warum sind Zufallsformeln von 3-SAT, obwohl NP-vollständig, bei kleinem n (bis 70) für eine einfache Suche so oft schnell entschieden, und wo sind die schweren Formeln?** DPLL und Formelgenerator sind wörtliche Kopien aus Stück 3.

## Warum dieses Problem

„NP-vollständig“ meint den **schlimmsten Fall**. Wie schwer eine Zufallsformel für eine einfache Suche ist, hängt stark vom **Verhältnis m/n** ab (Regeln je Entscheidung): wenige Regeln, fast immer erfüllbar und leicht; sehr viele, fast immer unerfüllbar, und die Suche wird billiger als am Übergang (bei n = 40 um etwa ein Drittel), aber nicht so billig wie bei wenigen Regeln; dazwischen kippt die Erfüllbarkeit (**Phasenübergang**), und die Suche ist am teuersten. Die Demo misst das, zeigt, was einem Löser trägt (Einheitspropagation, Verzweigungsregel), und stellt **Zufall, Struktur und Störung** gegenüber. Der letzte Teil ist die empirische Antwort auf „NP-schwer heißt nicht jede Instanz schwer“ und die Brücke zur geglätteten Analyse; **mit einer Einschränkung**, die sich beim Messen ergab: die Störung hilft stark, ändert aber die Antwort (siehe Befunde).

## Modell

- **Formel.** 3-KNF über n Variablen mit m Klauseln, je drei verschiedene Variablen mit zufälligem Vorzeichen (eigener SplitMix64-Generator, deshalb auf jeder Plattform dieselben Formeln). Wächst m bei gleichem Zufalls-Seed, kommen Klauseln hinzu, die früheren bleiben: „erfüllbar“ kann dann nur kippen, nie zurückkehren.
- **Suche.** DPLL: Einheitsklauseln erzwingen, sonst auf einer Variablen verzweigen (zuerst wahr), Widerspruch = Sackgasse. Varianten: Einheitspropagation an oder aus; Verzweigungsregel erste Variable, häufigste Variable oder Jeroslow–Wang (jedes Vorkommen in einer Klausel der Länge L zählt 2^−L).
- **Aufwand.** Gezählt wird der **Knoten der Suche** (ein Aufruf), nie die Laufzeit; Einheitsschritte, Verzweigungen und Sackgassen werden einzeln ausgewiesen. Ein Knotenbudget bricht die Suche ab; abgebrochene Läufe zählen mit dem Budget (untere Schranke).
- **Struktur und Störung.** Schubfach-Formel (h + 1 Tauben in h Fächer, unerfüllbar); Störung = jedes Literal mit Wahrscheinlichkeit p umdrehen. **Die Störung ändert die Formel und oft ihre Antwort**; sie ist keine Glättung desselben Problems.
- Mathematik und Annahmentabelle: Expander **📐 Mathematische Formulierung** in der App.

## Methodik

| Baustein | Datei | Anmerkung |
|---|---|---|
| DPLL-Suche mit Varianten, Suchbaum-Aufzeichnung, Prüfer, Brute-Force-Probe | `sph_search.py` | eigene Einheiten: Vereinfachen, drei Verzweigungsregeln, `solve` komponiert nur |
| Schubfach-Formeln, Vorzeichen-Störung, Umbenennung der Variablen | `sph_structure.py` | die Umbenennung ändert die Antwort nie |
| DPLL aus Stück 3 | `sph_dpll.py` | **wörtliche Kopie** von reduktionskette-demo/red_dpll.py (Commit ba24648); Regressionstest: die Variante „an, häufigste Variable“ liefert dieselbe Knotenzahl |
| SplitMix64, Zufallsformel, Zufallsgraph | `sph_scenario.py` | **wörtliche Kopie** von reduktionskette-demo/red_scenario.py (Commit ba24648) |
| Messreihen, Interpolation, Verdikte | `sph_evaluation.py` | Phasenübergang, Wachstum, Löser-Hebel, Struktur; alle Verdikte als reine Funktionen |

Experimente in der App: **Wo kippt die Erfüllbarkeit, und wo ist die Suche am teuersten?**, **Wie wächst die Suche?**, **Was trägt ein Löser?**, **Warum der schlimmste Fall nicht die Praxis ist**; die drei Messreihen laufen auf Knopfdruck (rund 20, 15 und 8 Sekunden).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`. Messreihen: 40 feste Formeln je Zelle (`SWEEP_SEEDS`), Wachstum und Hebel 20 feste Formeln, Störung 10 feste Störungen je Wert; die Zahlen der Presets sind Einzelinstanzen und als solche ausgewiesen.

| Frage | Befund |
|---|---|
| **Wo kippt die Erfüllbarkeit?** | Der Anteil erfüllbarer Formeln fällt von 100 % bei m/n = 3,00 (alle 40 von 40 bei n = 20, 30, 40; bei n = 20 schon 39 von 40 ab 3,25) auf 5 % (n = 20), 0 % (n = 30) und 2,5 % (n = 40) bei m/n = 6,00. Der 50-%-Schnitt (linear interpoliert) liegt bei n = 20 / 30 / 40 bei m/n = 4,67 / 4,50 / 4,52 (`test_claim_phase_transition_table`, `test_claim_fifty_percent_crossing_and_peak`). |
| **Wie hängt der Schnitt von der Formelmenge ab?** | Die Vormessung mit den Seeds 0 bis 39 ergab 4,39 bis 4,50, die festen Seeds dieser Demo 4,50 bis 4,67: der Schnitt streut bei 40 Formeln um etwa ±0,1 bis ±0,15 (bei n = 20 am stärksten). Er ist **eine Messung, kein Wert**, und kein Trend zur Vorhersage 4,27 ist bei diesen kleinen n erkennbar. |
| **Wo ist die Suche am teuersten?** | Bei m/n = 5,00 (n = 20), 4,75 (n = 30 und 40): Median 15 / 30 / 52,5 Knoten. Die Spitze ist flach und breit: mit anderen Formelmengen lag die Median-Spitze bei diesen n zwischen m/n = 4,5 und 5,25 (unabhängige Nachprüfung, nicht Teil der Tests). Bei m/n = 3 braucht die Suche im Median 8 / 12 / 13 Knoten, bei 6 15 / 21 / 34. |
| **Wie wächst die Suche?** | Bei m/n = 4,5 und n = 20 / 30 / 40 / 50 / 60 / 70: Median 14 / 31 / 48 / 84 / 143 / 317 Knoten, Maximum 33 / 55 / 82 / 201 / 329 / 607; erfüllbar 14 / 6 / 10 / 6 / 9 / 3 von 20. Das 23-Fache für das 3,5-Fache an Variablen, im Mittel ×1,9 je zehn zusätzliche Variablen; mit anderen Formelmengen etwa das 17- bis 23-Fache und ×1,8 bis ×1,9 (unabhängige Nachprüfung, nicht Teil der Tests), also etwa das 20-Fache. Der Median mischt erfüllbare und unerfüllbare Formeln, deren Anteil mit n sinkt (14 auf 3 von 20). Ein exponentieller Trend über sechs Größen, **kein Beweis** (`test_claim_growth_of_the_search`). |
| **Was trägt ein Löser?** | n = 30, m = 128 (m/n = 4,27), Budget 10.000, Median der Knoten (Abbrüche von 20): mit Einheitspropagation 66 / 19,5 / 13 (erste / häufigste / Jeroslow–Wang), ohne sie 10.001 (18) / 2.859 (1) / 291 (0). Der Faktor der Einheitspropagation ist bei „erste Variable“ mindestens 152 (untere Schranke: 18 von 20 Läufen erreichen das Budget), bei Jeroslow–Wang 22; als Größenordnung mindestens 20 bis 150, je nach Regel, und einzelne Mediane weichen mit anderen Formelmengen bis etwa um den Faktor 2 ab (unabhängige Nachprüfung). Mit Einheitspropagation wirkt die Verzweigungsregel mit Faktor 5,1 (66 gegen 13), ohne sie mindestens mit Faktor 34 (10.001 gegen 291) (`test_claim_what_a_solver_carries`). |
| **Struktur gegen Zufall** | Schubfach-Formeln (unerfüllbar) mit h = 3 / 4 / 5 / 6 Fächern: 11 / 47 / 239 / 1.439 Knoten; eine Zufallsformel mittlerer Größe (n = 30, m = 150, 10 feste Formeln) im Median 26 (`test_claim_pigeonhole_without_perturbation`). |
| **Hilft die Störung?** | **Ja, aber sie ändert die Antwort.** Schubfach h = 5, Median der Knoten (erfüllbar von 10) bei 0,5 / 1 / 2 / 5 / 10 / 20 / 50 % umgedrehten Vorzeichen: 200 (5), 16,5 (10), 5 (10), 5 (10), 8 (10), 8,5 (5), 3 (0); h = 6: 198 (10), 7 (10), 6,5 (10), 8 (10), 14 (10), 11 (0), 3 (0), gegen 239 bzw. 1.439 ungestört. Bei 0,5 % ist die Formel noch kaum leichter (Median 200 gegen 239 Knoten). Schon bei 1 % sind in dieser Messung (10 feste Störungen) alle erfüllbar und im Median in 16,5 (h = 5) bzw. 7 (h = 6) Knoten gelöst; bei anderen Störungen bleibt ein Teil (h = 5: etwa 17 von 100) unerfüllbar und ebenso schwer wie das Original (unabhängige Nachprüfung, nicht Teil der Tests). Bei hohem Anteil wird die Formel wieder unerfüllbar, aber zufallsähnlich und leicht. Es ist **keine** Glättung desselben Problems (`test_claim_perturbed_pigeonhole_h5_and_h6`, `test_claim_the_perturbation_changes_the_answer`). |
| **Randnotiz: Umbenennung** | Eine zufällige Umbenennung der Variablen ändert die Antwort nie (0 Abweichungen), die Knotenzahl bei 7 von 10 Formeln (n = 30, m/n = 4,5); der Median bleibt 29 (`test_claim_renaming_changes_nodes_but_not_the_median`). |
| **Presets (Einzelinstanzen)** | Standardfall (n = 20, m = 90): erfüllbar, 14 Knoten (66 Einheitsschritte, 7 Verzweigungen, 6 Sackgassen). Lehrbeispiel (n = 6, m = 14): 3 Knoten. Locker (n = 30, m = 90): 8. Am Übergang (n = 40, m = 180): erfüllbar, 42. Überbestimmt (n = 40, m = 240): unerfüllbar, 25. Ohne Einheitspropagation (n = 30, m = 128, erste Variable): Abbruch nach 10.001 Knoten (`test_claim_presets_are_single_instances_with_these_values`). |

## Ehrliche Grenzen

- **Zufalls-3-SAT ist eine Instanzfamilie, bei kleinem n.** Die Aussagen zu Phasenübergang und Wachstum gelten für diese Formeln, diese einfache Suche und n bis 70; sie sagen nichts über Industrieformeln und nichts über n → ∞.
- **Die Vorhersage 4,27 ist für k = 3 nicht bewiesen.** Bewiesen ist die Erfüllbarkeitsschwelle von Zufalls-k-SAT nur für große k (Ding, Sly, Sun, Annals of Mathematics 2022; geprüft). Die Demo misst endliches n und nennt 4,27 nur zur Einordnung; die gemessenen 50-%-Schnitte liegen bei diesen n darüber.
- **Der exponentielle Trend ist kein Beweis.** Sechs Größen, 20 Formeln je Größe; die Maxima streuen stark (n = 50: Maximum 201 bei Median 84).
- **Die Störung ist keine Glättung.** Das Umdrehen von Vorzeichen ändert die Formel und oft ihre Antwort, bei Simplex ([klee-minty-demo](https://github.com/sebastian-hanisch/klee-minty-demo)) ändert die Störung die Pivotzahl (Median über 20 Störungen), hier die Erfüllbarkeit. Die Demo zeigt, dass kleine Störungen eine strukturell harte Formel leicht machen, aber nicht, dass dieselbe Instanz „im Mittel leicht“ wäre.
- **Ein einfaches DPLL steht nicht für „den Löser“.** Moderne SAT-Löser lernen aus Widersprüchen (Klausellernen) und lösen Industrieformeln mit Millionen Variablen; die Demo baut das nicht. Eine Scratch-Probe mit OR-Tools CP-SAT zeigte, dass auch ein solcher Löser auf Zufallsformeln am Übergang mit n mehr Konflikte braucht; die Zahlen sind plattform- und versionsabhängig und stehen deshalb weder hier noch in der App.
- **Knoten sind keine Laufzeit.** Ein Knoten kostet je nach Formelgröße verschieden viel.
- **Die Hebel-Messreihe läuft mit Budget 10.000.** Abgebrochene Läufe zählen mit dem Budget; die Faktoren der Einheitspropagation sind daher untere Schranken.

## Befunde und Korrekturen gegenüber dem Plan

- **Hypothese H6 widerlegt (im Plan bereits vermerkt):** „Störung hilft bei strukturell harten SAT-Formeln nicht“ stimmt nicht; sie hilft stark, ändert aber die Antwort.
- **Andere Seeds, andere Schnitte:** Die Vormessung lieferte für den 50-%-Schnitt 4,39 bis 4,50 (Seeds 0 bis 39), diese Demo mit festen Seeds 4,50 bis 4,67; die Hebel-Faktoren der Vormessung (rund 26 bis 1.000, 30 Formeln, Budget 200.000) sind hier mit Budget 10.000 untere Schranken (mindestens 152 bei „erste Variable“).
- **Kein Löser mit Klausellernen live** (Nutzerentscheidung): nur der Einordnungssatz oben, ohne Zahlen. Die Hypothese H7 des Plans entfällt damit als Befund.
- **n = 80 und 100 nicht in der Demo:** Die Vormessung ging bis n = 100 (Median 1.306 Knoten); die App rechnet bis n = 70 (Messreihe) bzw. 60 (Regler), die größeren Größen wären nur vorgerechnet und nicht live nachvollziehbar gewesen und sind deshalb weggelassen.
- **Median wird nie stillschweigend gerundet:** der Median über 40 Formeln kann ein halber Wert sein (52,5 Knoten); die App zeigt ihn mit Komma.
- **Das Preset „Schubfach, leicht gestört“ ändert nur Experiment 4:** die Hauptansicht zeigt weiter die Zufallsformel des Standardfalls.

## Verifikation

- **Kern:** jede Einheit gegen Handrechnung an den Mini-Formeln (`tests/conftest.py`): Vereinfachen, die drei Verzweigungsregeln, Knoten, Einheitsschritte, Verzweigungen und Sackgassen je Variante (`tests/test_search.py`); Schubfach, Störung, Umbenennung (`tests/test_structure.py`); Suchbaum-Aufzeichnung samt Abbruch.
- **Orakel** (`tests/test_oracle_sat_phasenuebergang.py`): alle sechs Varianten gegen Brute Force (Erfüllbarkeit und gefundene Belegung), erfüllbare **und** unerfüllbare Formeln; die Messreihe zählt dieselben erfüllbaren Formeln wie die Brute-Force-Probe; „erfüllbar“ ist in m nicht steigend. Im Repo laufen kleine Fassungen; der **große Lauf im Scratch-Ordner** (420 Formeln, 348 erfüllbar und 72 unerfüllbar, 2.520 Läufe der sechs Varianten, keine abgebrochen; 1.080 Läufe an gestörten Schubfach-Formeln mit h = 3; 120 Formeln mit Umbenennung) fand **0 Abweichungen**.
- **Kopien** (`tests/test_copies.py`): wortgleich mit dem Original, solange es im Portfolio-Ordner liegt; die Variante „an, häufigste Variable“ stimmt mit der Kopie aus Stück 3 auf 150 Formeln in Antwort und Knotenzahl überein.
- **Prüfung vor der Anzeige:** `validation_errors` prüft die gemeldete Belegung, bei n ≤ 16 die Antwort gegen Brute Force und die Knotenstatistik (`tests/test_evaluation.py`).
- **Verdikte** als reine Funktionen, jede Zahl im Text an handgesetzten Werten (`tests/test_verdicts.py`); **Claims:** jede Zahl dieser README (`tests/test_claims.py`).
- **Presets:** vollständig, gültige Werte, erstes Preset gleich Standard, jedes Preset zeigt, was seine Hilfe verspricht (`tests/test_presets.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Button einschließlich der drei Messreihen, jeder Regler am Minimum und Maximum, alle zugleich), Permalink mit Begrenzung und unlesbaren Werten (auch Wahrheitswert und Regel), Abbruchanzeige, Layout, Footer.
- **Browser:** Standardansicht mit Suchbaum, Messreihen Phasenübergang und Wachstum per Klick; keine Konsolenmeldung.
- **Mutationsprüfung (Vollauf über `sph_search.py`, `sph_structure.py` und `sph_evaluation.py`, 120 Stellen, die das Werkzeug über die Orakel-Tests erreicht):** 120 gefangen, 0 überlebt. Ausgenommen sind die zwei wörtlichen Kopien (ihre Tests liegen in Stück 3); Darstellung, PDF, Presets und Oberfläche werden vom Werkzeug nicht mutiert (abgesichert durch Rauch-, Verdikt- und Claims-Tests).

## Einordnung und Quellen (anhand der Quellen geprüft)

DPLL: Davis, Logemann und Loveland, *A machine program for theorem-proving*, Communications of the ACM 5 (1962), S. 394 bis 397. Phasenübergang: Cheeseman, Kanefsky und Taylor, *Where the really hard problems are*, IJCAI 1991 (Seiten in den Quellen uneinheitlich, deshalb nicht genannt); Mitchell, Selman und Levesque, *Hard and easy distributions of SAT problems*, AAAI 1992, S. 459 bis 465. Verzweigungsregel: Jeroslow und Wang, *Solving propositional satisfiability problems*, Annals of Mathematics and Artificial Intelligence 1 (1990), S. 167 bis 187 (laut DIMACS-Bibliographie; Inhalt nicht eingesehen, die Regel ist hier nach der Beschreibung im Quelltext umgesetzt). Schwelle von Zufalls-k-SAT: Ding, Sly und Sun, *Proof of the satisfiability conjecture for large k*, Annals of Mathematics 196 (2022). Geglättete Analyse: Spielman und Teng (STOC 2001, Simplex) sowie Englert, Röglin und Vöcking (ACM Transactions on Algorithms 2016, 2-opt). Dass die Schubfach-Formeln für Resolution-basierte Verfahren exponentiell schwer sind (Haken 1985), ist nicht nachgeschlagen und steht nicht als Aussage in der Demo; gemessen sind nur die Knotenzahlen dieser Suche.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: ein Suchlauf mit Suchbaum, vier Experimente, Annahmentabelle, Formeln |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `sph_constants.py` | Regler-Grenzen, Rechengrenzen, Messreihen-Parameter, Farben, Presets |
| `sph_dpll.py` | wörtliche Kopie: DPLL aus Stück 3 (Regressionsreferenz) |
| `sph_evaluation.py` | Analyse, Messreihen (Phasenübergang, Wachstum, Hebel, Struktur), Interpolation, Prüfung vor der Anzeige, Verdikte |
| `sph_layout.py` | Fester Kopf (Stylesheet) |
| `sph_pdf_export.py` | PDF-Bericht (fpdf2) |
| `sph_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `sph_scenario.py` | wörtliche Kopie: SplitMix64, Zufallsformel, Zufallsgraph aus Stück 3 |
| `sph_search.py` | DPLL-Varianten, Suchbaum, Prüfer, Brute-Force-Probe |
| `sph_structure.py` | Schubfach-Formeln, Vorzeichen-Störung, Umbenennung |
| `sph_visualization.py` | Plotly-Abbildungen: Suchbaum, Phasenübergang, Wachstum, Störung (Achsen gesperrt) |
| `tests/` | Mini-Formeln, Orakel, Kopien, Suche, Struktur, Verdikte, Claims, Presets, Layout, AppTest-Smoke-Test, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **CDCL (Klausellernen) und Industrie-Instanzen:** eigene Verfahren, nicht Gegenstand dieses Stücks; nur als Einordnung genannt.
- **Lokalsuche für SAT (etwa WalkSAT):** ein anderes Verfahren mit anderen Stärken.
- **Eine Glättung, die die Antwort erhält:** die Störung der Demo ändert die Antwort; ein Modell, das sie erhält, wäre ein eigenes Messprogramm (die Umbenennung der Variablen erhält sie, ändert aber nur die Auflösung von Gleichständen).
- **Größen über n = 70:** nicht live nachvollziehbar in Python.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
