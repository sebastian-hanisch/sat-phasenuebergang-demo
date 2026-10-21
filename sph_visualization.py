"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import sph_constants as C
from sph_scenario import literal_name


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.22), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


STATUS_COLOR = {"branch": C.COLOR_BRANCH, "dead": C.COLOR_DEAD, "solved": C.COLOR_SOLVED, "aborted": C.COLOR_ABORTED}
STATUS_NAME = {"branch": "verzweigt", "dead": "Sackgasse", "solved": "gelöst", "aborted": "Budget erreicht"}


def tree_positions(tree) -> dict[int, tuple[float, float]]:
    """Positionen der Baumknoten: y = -Tiefe; x = laufende Nummer der Blätter von links nach rechts, innere Knoten in der Mitte ihrer Kinder."""
    children: dict[int, list[int]] = {}
    for node in tree:
        if node.parent is not None:
            children.setdefault(node.parent, []).append(node.id)
    depth = {node.id: node.depth for node in tree}
    x: dict[int, float] = {}
    counter = [0]

    def place(node_id):
        kids = [k for k in children.get(node_id, []) if k in depth]
        if not kids:
            x[node_id] = float(counter[0])
            counter[0] += 1
        else:
            for k in kids:
                place(k)
            x[node_id] = sum(x[k] for k in kids) / len(kids)

    roots = [node.id for node in tree if node.parent is None]
    for r in roots:
        place(r)
    return {i: (x[i], -float(depth[i])) for i in x}


def build_tree(tree):
    """Suchbaum: Knoten nach Ausgang gefärbt (verzweigt blau, Sackgasse rot, gelöst grün, Budget gelb); an den Kanten steht die Entscheidung (x oder nicht x)."""
    pos = tree_positions(tree)
    fig = go.Figure()
    xs, ys = [], []
    for node in tree:
        if node.parent is not None and node.parent in pos and node.id in pos:
            xs += [pos[node.parent][0], pos[node.id][0], None]
            ys += [pos[node.parent][1], pos[node.id][1], None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="rgba(120,120,120,0.6)", width=1.5), hoverinfo="skip", showlegend=False))
    for status in ("branch", "dead", "solved", "aborted"):
        nodes = [n for n in tree if n.status == status and n.id in pos]
        if not nodes:
            continue
        fig.add_trace(go.Scatter(
            x=[pos[n.id][0] for n in nodes], y=[pos[n.id][1] for n in nodes], mode="markers",
            marker=dict(size=14, color=STATUS_COLOR[status], line=dict(width=1, color="white")), name=STATUS_NAME[status],
            hovertext=[f"Knoten {n.id + 1}" + ("" if n.decision is None else f": {literal_name(n.decision[0] if n.decision[1] else -n.decision[0])}") for n in nodes], hoverinfo="text",
        ))
    for node in tree:
        if node.decision is not None and node.parent in pos and node.id in pos:
            mx = (pos[node.parent][0] + pos[node.id][0]) / 2
            my = (pos[node.parent][1] + pos[node.id][1]) / 2
            fig.add_annotation(x=mx, y=my, text=literal_name(node.decision[0] if node.decision[1] else -node.decision[0]), showarrow=False, font=dict(size=10),
                               bgcolor="rgba(255,255,255,0.85)")
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _base(fig, 120 + 60 * (1 + max((n.depth for n in tree), default=0)))


def build_phase_share(by_n):
    """Anteil erfüllbarer Formeln über das Verhältnis m/n, je Größe n; die waagerechte Linie ist 50 %."""
    fig = go.Figure()
    for color, n in zip(C.COLOR_SERIES, sorted(by_n)):
        rows = by_n[n]
        fig.add_trace(go.Scatter(x=[r["ratio"] for r in rows], y=[100 * r["sat"] / r["count"] for r in rows], mode="lines+markers", name=f"n = {n}",
                                 line=dict(color=color, width=2.5), hovertemplate="m/n = %{x}: %{y:.0f} % erfüllbar<extra></extra>"))
    fig.add_hline(y=50, line=dict(color="gray", width=1, dash="dot"))
    fig.update_xaxes(title_text="Verhältnis m/n", dtick=0.5)
    fig.update_yaxes(title_text="erfüllbare Formeln (%)", range=[-3, 103])
    return _base(fig, 320)


def build_phase_nodes(by_n):
    """Median der Knoten über das Verhältnis m/n, je Größe n."""
    fig = go.Figure()
    for color, n in zip(C.COLOR_SERIES, sorted(by_n)):
        rows = by_n[n]
        fig.add_trace(go.Scatter(x=[r["ratio"] for r in rows], y=[r["median"] for r in rows], mode="lines+markers", name=f"n = {n}",
                                 line=dict(color=color, width=2.5), hovertemplate="m/n = %{x}: Median %{y:,.0f} Knoten<extra></extra>"))
    fig.update_xaxes(title_text="Verhältnis m/n", dtick=0.5)
    fig.update_yaxes(title_text="Median der Knoten", rangemode="tozero")
    return _base(fig, 320)


def build_growth(rows):
    """Median und Maximum der Knoten über n beim festen Verhältnis (logarithmisch)."""
    xs = [r["n"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["median"] for r in rows], mode="lines+markers", name="Median", line=dict(color=C.COLOR_SERIES[0], width=3),
                             hovertemplate="n = %{x}: %{y:,.0f} Knoten<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["max"] for r in rows], mode="lines", name="Maximum", line=dict(color=C.COLOR_SERIES[0], width=1.5, dash="dot"),
                             hovertemplate="n = %{x}: %{y:,.0f} Knoten<extra></extra>"))
    fig.update_xaxes(title_text="Variablen n", dtick=10)
    fig.update_yaxes(title_text="Knoten der Suche (log)", type="log")
    return _base(fig, 340)


def build_structure(rows, base_nodes, reference):
    """Median der Knoten über die Störung (Promille umgedrehter Vorzeichen), dazu die ungestörte Formel und die Zufallsformel als Linien."""
    pts = [r for r in rows if r["pm"] > 0]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[r["pm"] / 10 for r in pts], y=[max(r["median"], 1) for r in pts], mode="lines+markers", name="gestörte Schubfach-Formel (Median)",
                             line=dict(color=C.COLOR_SERIES[3], width=3), hovertemplate="%{x} % umgedreht: Median %{y:,.0f} Knoten<extra></extra>"))
    fig.add_hline(y=base_nodes, line=dict(color=C.COLOR_SERIES[2], width=1.5, dash="dash"), annotation_text="ungestört", annotation_position="top left")
    fig.add_hline(y=max(reference["median"], 1), line=dict(color=C.COLOR_SERIES[0], width=1.5, dash="dot"), annotation_text="Zufallsformel", annotation_position="bottom left")
    fig.update_xaxes(title_text="umgedrehte Vorzeichen (%)", type="log")
    fig.update_yaxes(title_text="Knoten der Suche (log)", type="log")
    return _base(fig, 340)
