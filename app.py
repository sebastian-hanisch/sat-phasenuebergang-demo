"""SAT in der Praxis: DPLL und Phasenübergang - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Viertes Stück der Komplexitätsklassen-Reihe: warum 3-SAT trotz NP-Vollständigkeit oft leicht ist und wo die schweren Formeln liegen. Aufwand in Knoten der DPLL-Suche.
Aufbau und Regeln stehen im DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import sph_constants as C
from sph_evaluation import (
    Settings,
    analyse,
    crossing,
    fmt_int,
    fmt_median,
    fmt_num,
    fmt_pm,
    fmt_share,
    peak,
    random_reference,
    rename_effect,
    structure_rows,
    sweep_growth,
    sweep_levers,
    sweep_phase,
    validation_errors,
    verdict_growth,
    verdict_levers,
    verdict_phase,
    verdict_run,
    verdict_structure,
)
from sph_layout import dunkles_design, kopf_css
from sph_pdf_export import build_pdf
from sph_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from sph_scenario import literal_name
from sph_visualization import build_growth, build_phase_nodes, build_phase_share, build_structure, build_tree

st.set_page_config(page_title="SAT in der Praxis – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _phase():
    return sweep_phase()


@st.cache_data(show_spinner=False)
def _growth():
    return sweep_growth()


@st.cache_data(show_spinner=False)
def _levers():
    return sweep_levers()


@st.cache_data(show_spinner=False)
def _structure(h):
    return structure_rows(h)


@st.cache_data(show_spinner=False)
def _reference():
    return random_reference()


@st.cache_data(show_spinner=False)
def _rename():
    return rename_effect()


@st.cache_data(show_spinner=False)
def _pdf(settings):
    return build_pdf(analyse(settings))


def _md_table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _clause_text(clause):
    return "(" + " ∨ ".join(literal_name(lit) for lit in clause) + ")"


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in sph_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧮 SAT in der Praxis: DPLL und Phasenübergang")
st.markdown(
    """
3-SAT ist **NP-vollständig**, und trotzdem lösen einfache Verfahren viele Formeln in wenigen Schritten. Wo sind die **schweren** Formeln, und was trägt ein Löser? Die Demo löst Zufallsformeln
aus **Zusammenladeregeln** (jede Regel: „mindestens eine von drei Aussagen gilt“) mit der **DPLL-Suche** aus Stück 3 und zählt die **Knoten der Suche**. Sie zeigt den **Phasenübergang**
(ab einem bestimmten Verhältnis m/n von Regeln zu Entscheidungen kippt die Erfüllbarkeit), den **Hebel** der Einheitspropagation und den Unterschied zwischen **Zufall, Struktur und Störung**.
Viertes Stück der Komplexitätsklassen-Reihe; die Fall-Demos behandeln einzelne Anwendungen, hier steht eine Frage der Komplexitätstheorie im Mittelpunkt.

Weiter unten: die Experimente **🔬 Wo kippt die Erfüllbarkeit?**, **🔬 Wie wächst die Suche?**, **🔬 Was trägt ein Löser?** und **🔬 Warum der schlimmste Fall nicht die Praxis ist**,
dann **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert DPLL", expanded=True):
    st.markdown(
        """
1. **Einheitsklausel.** Hat eine Klausel nur noch ein freies Literal, ist es erzwungen: es muss wahr sein, sonst ist die Klausel verletzt. Das vereinfacht alle anderen Klauseln und kann weitere Klauseln zu Einheitsklauseln machen (**Einheitspropagation**).
2. **Verzweigen.** Bleibt keine Einheitsklausel, wählt die Suche eine Variable und probiert zuerst einen Wert, dann den anderen. Welche Variable, bestimmt die **Verzweigungsregel**: die erste, die häufigste oder nach Jeroslow–Wang (kurze Klauseln zählen mehr).
3. **Sackgasse.** Eine leere Klausel heißt Widerspruch: die Suche geht einen Schritt zurück. Sind alle Klauseln erfüllt, ist die Formel gelöst.
4. **Aufwand.** Gezählt wird der **Knoten**, ein Aufruf der Suche. Das ist ein Maß für die Größe des Suchbaums, keine Laufzeit.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Formel**")
    n = st.slider("Variablen n", *bounds("n_slider"), key="n_slider", help="Ja/Nein-Entscheidungen. Bis 60 werden die Läufe live gerechnet.")
    m = st.slider("Klauseln m", *bounds("m_slider"), key="m_slider",
                  help="Regeln der Form „mindestens eine von drei Aussagen“. Das Verhältnis m/n entscheidet über die Schwierigkeit. Wächst m bei gleichem Zufalls-Seed, kommen Klauseln hinzu, die früheren bleiben.")
    seed = st.number_input("Zufalls-Seed der Formel", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Formel generieren", width="stretch", on_click=randomize_seed)
    st.markdown("**Löser**")
    units = st.toggle("Einheitspropagation", key="units_toggle", help="Erzwungene Literale sofort setzen. Ausgeschaltet sucht die Suche auch dort, wo nichts zu suchen ist.")
    rule = st.selectbox("Verzweigungsregel", list(C.RULES), format_func=C.RULES.get, key="rule_select", help="Welche Variable die Suche als nächste wählt.")
    budget = st.select_slider("Knotenbudget", options=list(C.BUDGETS), format_func=fmt_int, key="budget_select", help="Die Suche bricht ab, bevor sie mehr Knoten besucht.")
    st.markdown("**Struktur (Experiment 4)**")
    h = st.select_slider("Fächer h der Schubfach-Formel", options=list(C.PIGEON_H), key="h_select", help="h + 1 Tauben sollen in h Fächer: unerfüllbar, aber strukturell schwer für diese Suche.")
    pm = st.select_slider("Störung: umgedrehte Vorzeichen", options=list(C.PER_MILLE), format_func=fmt_pm, key="pm_select",
                          help="Anteil der Literale der Schubfach-Formel, deren Vorzeichen umgedreht wird. Das kann die Antwort ändern.")

sync_query_params({"n_slider": int(n), "m_slider": int(m), "seed_input": int(seed), "units_toggle": bool(units), "rule_select": rule, "budget_select": int(budget), "h_select": int(h), "pm_select": int(pm)})

settings = Settings(n=int(n), m=int(m), seed=int(seed), units=bool(units), rule=rule, budget=int(budget), h=int(h), pm=int(pm))
a = _analysis(settings)
r = a.result
for message in validation_errors(a):
    st.error(message)

# --- Lauf ---------------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Eine Formel, ein Suchlauf")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Knoten der Suche", fmt_int(r.nodes) + (" (Abbruch)" if r.aborted else ""), help="Aufrufe der Suche; bei Abbruch das Budget.")
c2.metric("Einheitsschritte", fmt_int(r.units), help="Von der Einheitspropagation erzwungene Literale.")
c3.metric("Verzweigungen", fmt_int(r.branches), help="Knoten, an denen die Suche eine Variable wählen musste.")
c4.metric("Sackgassen", fmt_int(r.dead_ends), help="Knoten mit einem Widerspruch (leere Klausel).")
vkind, vtext = verdict_run(a)
getattr(st, vkind)(vtext)
if r.tree and not r.tree_truncated and not r.aborted:
    st.plotly_chart(build_tree(r.tree), width="stretch", key="tree_fig")
    st.caption("Suchbaum: blau = hat verzweigt, rot = Sackgasse, grün = gelöst. An den Kanten steht die Entscheidung der Verzweigung (x oder nicht x).")
else:
    st.caption(f"Den Suchbaum zeigt die App bis {C.TREE_LIMIT} Knoten; dieser Lauf hat mehr oder wurde abgebrochen.")
if r.assignment is not None:
    st.markdown("**Gefundene Belegung** (nicht genannte Variablen sind frei): " + ", ".join(f"x{v} = {'wahr' if val else 'falsch'}" for v, val in sorted(r.assignment.items())))
with st.expander("Die Klauseln"):
    st.markdown("\n".join(f"{i + 1}. {_clause_text(c)}" for i, c in enumerate(a.formula)))
if st.button("📄 PDF erstellen"):
    st.session_state["pdf_for"] = settings
if st.session_state.get("pdf_for") == settings:
    st.download_button("⬇️ PDF herunterladen", data=_pdf(settings), file_name="sat-in-der-praxis.pdf", mime="application/pdf")

st.markdown("## ❓ Kernfrage: Warum ist eine NP-vollständige Frage so oft schnell entschieden?")
st.markdown(
    "Weil „NP-vollständig“ den **schlimmsten Fall** meint. Die Experimente zeigen, wo die Suche wirklich teuer wird (am Phasenübergang), was dagegen hilft (Einheitspropagation, gute Regeln) "
    "und dass strukturell harte Formeln etwas anderes sind als Zufallsformeln."
)

st.markdown("---")

# --- Experimente --------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wo kippt die Erfüllbarkeit, und wo ist die Suche am teuersten?")
st.caption(f"Je Größe und Verhältnis {len(C.SWEEP_SEEDS)} feste Formeln (SWEEP_SEEDS), dieselben Seeds über alle Verhältnisse: die Formel wächst, Klauseln kommen dazu, deshalb kann „erfüllbar“ nur kippen, nie zurückkehren. "
           f"Die Messreihe rechnet rund 20 Sekunden.")
if st.button("▶️ Messreihe Phasenübergang rechnen"):
    st.session_state["phase_on"] = True
if st.session_state.get("phase_on"):
    with st.spinner("Rechne den Phasenübergang (3 Größen, 13 Verhältnisse, 40 Formeln) …"):
        phase = _phase()
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(build_phase_share(phase), width="stretch", key="phase_share_chart")
    with g2:
        st.plotly_chart(build_phase_nodes(phase), width="stretch", key="phase_nodes_chart")
    st.markdown(_md_table(
        ["n", "50-%-Schnitt bei m/n", "teuerste Suche bei m/n", "Median dort (Knoten)", f"erfüllbar bei m/n = {fmt_num(C.PHASE_RATIOS[0])}", f"erfüllbar bei m/n = {fmt_num(C.PHASE_RATIOS[-1])}"],
        [[n, "–" if crossing(rows) is None else fmt_num(crossing(rows), 2), fmt_num(peak(rows)["ratio"], 2), fmt_median(peak(rows)["median"]),
          fmt_share(rows[0]["sat"], rows[0]["count"]), fmt_share(rows[-1]["sat"], rows[-1]["count"])] for n, rows in phase.items()],
    ))
    vkind, vtext = verdict_phase(phase)
    getattr(st, vkind)(vtext)

st.markdown("---")

st.subheader("🔬 Experiment: Wie wächst die Suche?")
st.caption(f"Knoten der Suche über n beim festen Verhältnis m/n = {fmt_num(C.GROWTH_RATIO)} (am Übergang), {len(C.GROWTH_SEEDS)} feste Formeln je Größe, logarithmische Achse. Rund 15 Sekunden.")
if st.button("▶️ Messreihe Wachstum rechnen"):
    st.session_state["growth_on"] = True
if st.session_state.get("growth_on"):
    with st.spinner("Rechne das Wachstum …"):
        growth = _growth()
    st.plotly_chart(build_growth(growth), width="stretch", key="growth_chart")
    st.markdown(_md_table(
        ["n", "Median (Knoten)", "Maximum", "erfüllbar"],
        [[x["n"], fmt_median(x["median"]), fmt_int(x["max"]), f"{x['sat']} von {x['count']}"] for x in growth],
    ))
    vkind, vtext = verdict_growth(growth)
    getattr(st, vkind)(vtext)

st.markdown("---")

st.subheader("🔬 Experiment: Was trägt ein Löser?")
st.caption(f"Dieselben {len(C.LEVER_SEEDS)} Formeln (n = {C.LEVER_N}, m = {C.LEVER_M}, m/n = {fmt_num(C.LEVER_M / C.LEVER_N, 2)}) mit allen sechs Varianten: Einheitspropagation an oder aus, drei Verzweigungsregeln. "
           f"Das Budget der Messreihe ist {fmt_int(C.LEVER_BUDGET)} Knoten, abgebrochene Läufe zählen mit dem Budget (untere Schranke). Rund 8 Sekunden.")
if st.button("▶️ Messreihe Löser-Hebel rechnen"):
    st.session_state["levers_on"] = True
if st.session_state.get("levers_on"):
    with st.spinner("Rechne die sechs Varianten …"):
        levers = _levers()
    table = {(x["units"], x["rule"]): x for x in levers}
    st.markdown(_md_table(
        ["Einheitspropagation"] + [C.RULES[k] for k in C.RULES],
        [["an" if units_ else "aus"] + [f"{fmt_median(table[(units_, k)]['median'])} ({table[(units_, k)]['aborted']} Abbrüche)" for k in C.RULES] for units_ in (True, False)],
    ))
    vkind, vtext = verdict_levers(levers)
    getattr(st, vkind)(vtext)

st.markdown("---")

st.subheader("🔬 Experiment: Warum der schlimmste Fall nicht die Praxis ist")
st.caption(
    "Drei Familien: die **Schubfach-Formel** (h + 1 Tauben passen nicht in h Fächer: unerfüllbar, strukturell hart für diese Suche), eine **Zufallsformel** mittlerer Größe und die "
    "Schubfach-Formel mit **Störung** (jedes Vorzeichen mit der gewählten Wahrscheinlichkeit umgedreht, 10 feste Störungen je Wert). **Achtung:** Die Störung ändert die Formel und oft ihre Antwort. "
    "Sie ist keine Glättung desselben Problems; bei Simplex (Klee-Minty-Demo der Lineare-Programmierung-Reihe) ändert die Störung den Optimalwert kaum, hier kippt sie die Erfüllbarkeit."
)
srows = _structure(settings.h)
reference = _reference()
base_nodes = srows[0]["median"]
st.plotly_chart(build_structure(srows, base_nodes, reference), width="stretch", key="structure_chart")
st.markdown(_md_table(
    ["Umgedrehte Vorzeichen", "Median (Knoten)", "Maximum", "erfüllbar"],
    [["ungestört" if x["pm"] == 0 else fmt_pm(x["pm"]), fmt_median(x["median"]), fmt_int(x["max"]), "nein (unerfüllbar)" if x["pm"] == 0 else f"{x['sat']} von {x['count']}"] for x in srows],
))
chosen = next(x for x in srows if x["pm"] == settings.pm)
vkind, vtext = verdict_structure(chosen, base_nodes, settings.h, reference)
getattr(st, vkind)(vtext)
rename = _rename()
st.caption(f"Randnotiz: eine zufällige Umbenennung der Variablen ändert die Antwort nie, die Knotenzahl aber nur durch Gleichstände: bei {rename['changed']} von {rename['count']} Formeln "
           f"(n = {rename['n']}, m/n = {fmt_num(C.GROWTH_RATIO)}) war sie danach eine andere, der Median blieb {fmt_median(rename['median_before'])} bzw. {fmt_median(rename['median_after'])} Knoten.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Zufalls-3-SAT ist eine Instanzfamilie** | Aussagen über den Phasenübergang und das Wachstum gelten für diese Formeln, diese Suche und diese Größen (n bis 70), nicht für alle Formeln. Industrielle Formeln haben Struktur. | – |
| **Endliches n** | Der 50-%-Schnitt liegt bei diesen Größen über der Vorhersage 4,27 der Literatur für sehr große n. Diese Zahl ist für k = 3 nur eine Vorhersage, bewiesen ist die Schwelle nur für große k. | – |
| **Knoten sind keine Laufzeit** | Ein Knoten kostet je nach Formelgröße verschieden viel; die Zählung vergleicht Suchbäume, nicht Rechner. | – |
| **Ein einfaches DPLL steht für „den Löser“** | Moderne SAT-Löser lernen aus Widersprüchen (Klausellernen) und lösen Industrieformeln mit Millionen Variablen. Die Demo baut das nicht. Auch ein Löser mit Klausellernen braucht auf Zufallsformeln am Übergang mit n mehr Konflikte (Scratch-Probe mit OR-Tools CP-SAT, nicht Teil dieser Demo, keine Zahl). | – |
| **Die Störung glättet das Problem** | Das Umdrehen von Vorzeichen ändert die Formel und oft ihre Antwort: es ist ein Wechsel in eine leichte Familie, keine Glättung im Sinn der geglätteten Analyse. | `klee-minty-demo` (dort bleibt der Optimalwert fast gleich) |
| **Aufwand wächst exponentiell** | Der Trend über sechs Größen passt dazu, ist aber kein Beweis. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(r"**Formel.** Eine 3-KNF-Formel über den Variablen $x_1, \dots, x_n$ hat $m$ Klauseln mit je drei Literalen; das **Verhältnis** $\alpha = m / n$ steuert die Schwierigkeit.")
    st.markdown(r"**DPLL.** Die Suche $\operatorname{DPLL}(F)$ vereinfacht $F$, erzwingt Einheitsklauseln und verzweigt sonst:")
    st.latex(r"\operatorname{DPLL}(F) = \begin{cases} \text{falsch} & \text{wenn } F \text{ eine leere Klausel enthält} \\ \text{wahr} & \text{wenn } F \text{ keine Klausel enthält} \\ \operatorname{DPLL}(F[x \mapsto 1]) \vee \operatorname{DPLL}(F[x \mapsto 0]) & \text{sonst (Verzweigung auf } x\text{)} \end{cases}")
    st.markdown(r"**Jeroslow–Wang.** Jedes Vorkommen eines Literals $\ell$ in einer Klausel $C$ der Länge $|C|$ zählt $2^{-|C|}$; gewählt wird die Variable mit dem größten Gesamtgewicht, zuerst mit dem schwereren Vorzeichen:")
    st.latex(r"J(\ell) = \sum_{C \ni \ell} 2^{-|C|}, \qquad x^\ast = \arg\max_x \big( J(x) + J(\neg x) \big)")
    st.markdown(
        r"""
**Monotonie.** Bei gleichem Zufalls-Seed ist die Formel mit $m$ Klauseln ein Anfang der Formel mit $m + 1$ Klauseln. Eine erfüllbare Formel kann durch eine weitere Klausel unerfüllbar werden, nie umgekehrt: der
Anteil erfüllbarer Formeln ist in $m$ **nicht steigend**.

**Störung.** Jedes Literal wird unabhängig mit Wahrscheinlichkeit $p$ umgedreht: $\ell \mapsto \neg \ell$. Das ändert die Formel, nicht nur ihre Darstellung.

| Annahme | Bedeutung | Wer setzt an |
|---|---|---|
| Drei verschiedene Variablen je Klausel | keine Klausel enthält x und nicht x oder eine Wiederholung | – |
| Zuerst wahr probieren | die Reihenfolge der Werte ist festgelegt (bei Jeroslow–Wang das schwerere Vorzeichen zuerst) | – |
| Gleichstand: kleinere Variablennummer | die Suche ist deterministisch | – |
| Suchbaum als Beleg | die Baumgröße einer bestimmten Suche ist nur ein Maß für die Schwierigkeit | Stück 3 (Zertifikate) |

**Folgestücke.** Stück 5 der Reihe (Zahlen: pseudopolynomiell, FPTAS) fragt, wo bei NP-schweren Problemen die Härte steckt, wenn Zahlen im Spiel sind; Stück 6 (Approximation) und Stück 7 (parametrisierte Komplexität) zeigen weitere Auswege.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
