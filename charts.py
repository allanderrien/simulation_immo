"""
Fonctions de visualisation Plotly pour la simulation immobilière.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# ─── Palette ─────────────────────────────────────────────────────────────────
C_ACHAT    = "#2563EB"
C_LOCATION = "#16A34A"
C_INTERETS = "#EF4444"
C_NEUTRE   = "#94A3B8"

# ─── Style commun ────────────────────────────────────────────────────────────
_FONT       = dict(color="#111111", family="sans-serif")
_TITLE_FONT = dict(color="#111111", size=15)
_AXIS_FONT  = dict(color="#111111", size=12)
_TICK_FONT  = dict(color="#111111", size=11)
_LEGEND     = dict(orientation="h", yanchor="bottom", y=1.02,
                   xanchor="right", x=1, font=dict(color="#111111", size=11))
_GRID       = "#E2E8F0"


def _base_layout(title: str, height: int, r_margin: int = 20) -> dict:
    return dict(
        title=dict(text=title, font=_TITLE_FONT),
        font=_FONT,
        hovermode="x unified",
        legend=_LEGEND,
        height=height,
        margin=dict(l=70, r=r_margin, t=70, b=50),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )


def _style_axes(fig: go.Figure, x_title: str, y_title: str) -> None:
    """Style axes pour un go.Figure simple (sans make_subplots)."""
    fig.update_xaxes(
        title_text=x_title,
        title_font=_AXIS_FONT,
        tickfont=_TICK_FONT,
        tickmode="linear", dtick=5,
        showgrid=True, gridcolor=_GRID,
        linecolor="#CBD5E1", linewidth=1,
    )
    fig.update_yaxes(
        title_text=y_title,
        title_font=_AXIS_FONT,
        tickfont=_TICK_FONT,
        tickformat=",.0f",
        showgrid=True, gridcolor=_GRID,
        linecolor="#CBD5E1", linewidth=1,
    )


def _style_axes_subplots(fig: go.Figure, x_title: str,
                         y_title: str, y2_title: str) -> None:
    """Style axes pour une figure make_subplots avec axe Y secondaire."""
    fig.update_xaxes(
        title_text=x_title,
        title_font=_AXIS_FONT,
        tickfont=_TICK_FONT,
        tickmode="linear", dtick=5,
        showgrid=True, gridcolor=_GRID,
        linecolor="#CBD5E1", linewidth=1,
    )
    fig.update_layout(
        yaxis=dict(
            title_text=y_title,
            title_font=_AXIS_FONT,
            tickfont=_TICK_FONT,
            tickformat=",.0f",
            showgrid=True, gridcolor=_GRID,
            linecolor="#CBD5E1", linewidth=1,
        ),
        yaxis2=dict(
            title_text=y2_title,
            title_font=_AXIS_FONT,
            tickfont=_TICK_FONT,
            tickformat=",.0f",
            showgrid=False,
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────

def chart_patrimoine(df_A: pd.DataFrame, df_B: pd.DataFrame,
                     reel: bool = False) -> go.Figure:
    col   = "patrimoine_net_reel" if reel else "patrimoine_net_nominal"
    label = "Patrimoine net — euros constants" if reel else "Patrimoine net — euros courants"

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_A["annee"], y=df_A[col],
        name="Achat (equity + portefeuille net)",
        mode="lines+markers",
        line=dict(color=C_ACHAT, width=2.5),
        marker=dict(size=4),
        hovertemplate="<b>Achat</b> — %{x}<br>%{y:,.0f} €<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df_B["annee"], y=df_B[col],
        name="Location + Stratégie (portefeuille net)",
        mode="lines+markers",
        line=dict(color=C_LOCATION, width=2.5),
        marker=dict(size=4),
        hovertemplate="<b>Location</b> — %{x}<br>%{y:,.0f} €<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=pd.concat([df_A["annee"], df_A["annee"][::-1]]),
        y=pd.concat([df_A[col], df_B[col][::-1]]),
        fill="toself",
        fillcolor="rgba(37,99,235,0.07)",
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=False,
        hoverinfo="skip",
    ))

    fig.update_layout(**_base_layout(label, 430))
    _style_axes(fig, "Année", "€")
    return fig


def chart_mensualites(df_A: pd.DataFrame, df_B: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_A["annee"], y=df_A["cout_mensuel"],
        name="Coût mensuel — Achat",
        mode="lines", line=dict(color=C_ACHAT, width=2),
        hovertemplate="<b>Achat</b> — %{x}<br>%{y:,.0f} €/mois<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df_B["annee"], y=df_B["loyer_nominal"],
        name="Loyer revalorisé — Location",
        mode="lines", line=dict(color=C_LOCATION, width=2),
        hovertemplate="<b>Loyer</b> — %{x}<br>%{y:,.0f} €/mois<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df_A["annee"], y=df_A["delta_mensuel"],
        name="Delta → Stratégie (Achat)",
        mode="lines", line=dict(color=C_ACHAT, width=1.5, dash="dot"),
        hovertemplate="<b>Delta Achat</b> — %{x}<br>%{y:,.0f} €/mois<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df_B["annee"], y=df_B["delta_mensuel"],
        name="Delta → Stratégie (Location)",
        mode="lines", line=dict(color=C_LOCATION, width=1.5, dash="dot"),
        hovertemplate="<b>Delta Location</b> — %{x}<br>%{y:,.0f} €/mois<extra></extra>",
    ))

    fig.add_hline(y=0, line_dash="solid", line_color=C_NEUTRE, line_width=1)

    fig.update_layout(**_base_layout("Coûts mensuels et delta investi dans la stratégie", 380))
    _style_axes(fig, "Année", "€ / mois")
    return fig


def chart_couts_cumules(df_A: pd.DataFrame, df_B: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_A["annee"], y=df_A["cum_cout"],
        name="Total sorti — Achat",
        mode="lines", fill="tozeroy",
        fillcolor="rgba(37,99,235,0.10)",
        line=dict(color=C_ACHAT, width=2),
        hovertemplate="<b>Achat cumulé</b> — %{x}<br>%{y:,.0f} €<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df_B["annee"], y=df_B["cum_cout"],
        name="Loyers cumulés — Location",
        mode="lines", fill="tozeroy",
        fillcolor="rgba(22,163,74,0.10)",
        line=dict(color=C_LOCATION, width=2),
        hovertemplate="<b>Loyers cumulés</b> — %{x}<br>%{y:,.0f} €<extra></extra>",
    ))

    fig.update_layout(**_base_layout("Cash total sorti (hors investissement)", 350))
    _style_axes(fig, "Année", "€ cumulés")
    return fig


def chart_amortissement(df_A: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=df_A["annee"], y=df_A["equity_immo"],
        name="Equity (valeur nette)",
        marker_color=C_ACHAT,
        hovertemplate="%{x}<br>Equity : %{y:,.0f} €<extra></extra>",
    ), secondary_y=False)

    fig.add_trace(go.Bar(
        x=df_A["annee"], y=df_A["cap_restant_du"],
        name="Capital restant dû",
        marker_color="#93C5FD",
        hovertemplate="%{x}<br>CRD : %{y:,.0f} €<extra></extra>",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df_A["annee"], y=df_A["cum_interets"],
        name="Intérêts cumulés payés",
        mode="lines+markers", marker=dict(size=4),
        line=dict(color=C_INTERETS, width=2, dash="dot"),
        hovertemplate="%{x}<br>Intérêts cumulés : %{y:,.0f} €<extra></extra>",
    ), secondary_y=True)

    fig.update_layout(**_base_layout("Amortissement du crédit", 400, r_margin=80))
    fig.update_layout(barmode="stack")
    _style_axes_subplots(fig, "Année", "€", "Intérêts cumulés (€)")
    return fig


def chart_portefeuille(df_A: pd.DataFrame, df_B: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_A["annee"], y=df_A["portfolio_net"],
        name="Portefeuille net — Achat",
        mode="lines", fill="tozeroy",
        fillcolor="rgba(37,99,235,0.10)",
        line=dict(color=C_ACHAT, width=2),
        hovertemplate="<b>Portef. Achat</b> — %{x}<br>%{y:,.0f} €<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df_B["annee"], y=df_B["portfolio_net"],
        name="Portefeuille net — Location",
        mode="lines", fill="tozeroy",
        fillcolor="rgba(22,163,74,0.10)",
        line=dict(color=C_LOCATION, width=2),
        hovertemplate="<b>Portef. Location</b> — %{x}<br>%{y:,.0f} €<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df_A["annee"], y=df_A["total_investi"],
        name="Total investi — Achat",
        mode="lines", line=dict(color=C_ACHAT, width=1.5, dash="dash"),
        hovertemplate="<b>Total investi Achat</b> — %{x}<br>%{y:,.0f} €<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df_B["annee"], y=df_B["total_investi"],
        name="Total investi — Location",
        mode="lines", line=dict(color=C_LOCATION, width=1.5, dash="dash"),
        hovertemplate="<b>Total investi Location</b> — %{x}<br>%{y:,.0f} €<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df_A["annee"], y=df_A["flat_tax"],
        name="Flat tax — Achat (liquidation simulée)",
        mode="lines", line=dict(color=C_ACHAT, width=1, dash="dot"),
        hovertemplate="<b>Flat tax Achat</b> — %{x}<br>%{y:,.0f} €<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df_B["annee"], y=df_B["flat_tax"],
        name="Flat tax — Location (liquidation simulée)",
        mode="lines", line=dict(color=C_LOCATION, width=1, dash="dot"),
        hovertemplate="<b>Flat tax Location</b> — %{x}<br>%{y:,.0f} €<extra></extra>",
    ))

    fig.update_layout(**_base_layout("Portefeuille stratégie (net de flat tax à liquidation)", 380))
    _style_axes(fig, "Année", "€")
    return fig
