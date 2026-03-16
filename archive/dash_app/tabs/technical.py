# =============================================================================
# TECHNICAL TAB - "The Evidence" — Charts with verdicts
# =============================================================================

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc

from components import COLORS, FONTS, SHADOWS, LABEL_STYLE, card, label, spacer


# =============================================================================
# SHARED HELPERS
# =============================================================================

def _chart_layout(height=280):
    """Standard plotly layout matching dashboard chart style."""
    return dict(
        height=height,
        margin=dict(l=10, r=10, t=10, b=30),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
        font=dict(family=FONTS["primary"], size=11, color=COLORS["text_secondary"]),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
            font=dict(size=11, color=COLORS["text_primary"]),
        ),
    )


def _chart_axes(fig, y_prefix=""):
    """Apply standard axis styling."""
    fig.update_xaxes(
        showgrid=False, showline=True, linecolor=COLORS["border"],
        tickfont=dict(size=10, color=COLORS["muted"]),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor="#F1F5F9",
        tickfont=dict(size=10, color=COLORS["muted"]),
        tickprefix=y_prefix,
    )


def _verdict_badge(text, color):
    """Pill-shaped verdict badge."""
    return html.Span(text, style={
        "display": "inline-block",
        "padding": "3px 14px",
        "borderRadius": "20px",
        "background": color,
        "color": "white",
        "fontSize": "11px",
        "fontWeight": 700,
        "fontFamily": FONTS["primary"],
        "letterSpacing": "0.04em",
        "verticalAlign": "middle",
    })


def _chart_card(title, graph, verdict_text, verdict_color, explanation):
    """Card containing title + verdict badge, chart, and explanation."""
    return card([
        html.Div([
            html.Span(title, style={
                **LABEL_STYLE,
                "marginBottom": "0",
                "marginRight": "10px",
                "display": "inline-block",
                "verticalAlign": "middle",
            }),
            _verdict_badge(verdict_text, verdict_color),
        ], style={"marginBottom": "10px"}),
        graph,
        html.Div(explanation, style={
            "fontSize": "11px",
            "color": COLORS["muted"],
            "lineHeight": "1.4",
            "fontFamily": FONTS["primary"],
            "marginTop": "8px",
        }),
    ])


def _find_ema_crossovers(df):
    """Find EMA20/EMA50 crossover points (Paper 1)."""
    if "EMA20" not in df.columns or "EMA50" not in df.columns:
        return [], []
    golden, death = [], []
    e20 = df["EMA20"].values
    e50 = df["EMA50"].values
    dates = df["Date"].values
    prices = df["Close"].values
    for i in range(1, len(df)):
        if pd.isna(e20[i]) or pd.isna(e50[i]) or pd.isna(e20[i - 1]) or pd.isna(e50[i - 1]):
            continue
        if e20[i - 1] <= e50[i - 1] and e20[i] > e50[i]:
            golden.append((dates[i], prices[i]))
        if e20[i - 1] >= e50[i - 1] and e20[i] < e50[i]:
            death.append((dates[i], prices[i]))
    return golden, death


# =============================================================================
# RENDER
# =============================================================================

def render(stock_data, price_data):
    paper1_details = stock_data.get("paper1_details") or {}
    rl_prediction = stock_data.get("rl_prediction")
    rsi_value = stock_data.get("rsi_value")

    # Use 1Y of data for charts
    chart_data = price_data.tail(252).copy()
    dates = chart_data["Date"].tolist()

    children = []

    # =========================================================================
    # SECTION 1: DECISION PIPELINE (3 stacked charts)
    # =========================================================================

    # --- Chart 1: EMA Crossover ---
    ema_fig = go.Figure()

    # Price line
    ema_fig.add_trace(go.Scatter(
        x=dates, y=chart_data["Close"].tolist(), name="Price",
        line=dict(color=COLORS["heading"], width=2), mode="lines",
    ))
    # EMA-20
    if "EMA20" in chart_data.columns:
        ema_fig.add_trace(go.Scatter(
            x=dates, y=chart_data["EMA20"].tolist(), name="EMA-20",
            line=dict(color=COLORS["teal"], width=1.5), mode="lines",
        ))
    # EMA-50
    if "EMA50" in chart_data.columns:
        ema_fig.add_trace(go.Scatter(
            x=dates, y=chart_data["EMA50"].tolist(), name="EMA-50",
            line=dict(color=COLORS["coral"], width=1.5), mode="lines",
        ))

    # Annotate crossover points
    golden_pts, death_pts = _find_ema_crossovers(chart_data)
    for d, p in golden_pts:
        ema_fig.add_annotation(
            x=d, y=float(p), text="\u2191 Golden", showarrow=True,
            arrowhead=2, arrowwidth=2, arrowcolor=COLORS["success"],
            font=dict(size=9, color=COLORS["success"]), bgcolor="white",
            bordercolor=COLORS["success"], borderwidth=1, ax=0, ay=-30,
        )
    for d, p in death_pts:
        ema_fig.add_annotation(
            x=d, y=float(p), text="\u2193 Death", showarrow=True,
            arrowhead=2, arrowwidth=2, arrowcolor=COLORS["danger_red"],
            font=dict(size=9, color=COLORS["danger_red"]), bgcolor="white",
            bordercolor=COLORS["danger_red"], borderwidth=1, ax=0, ay=30,
        )

    ema_fig.update_layout(**_chart_layout(280), showlegend=True)
    _chart_axes(ema_fig, y_prefix="$")

    # Verdict
    ct = paper1_details.get("crossover_type", "none")
    if ct == "golden_cross":
        ema_verdict, ema_color = "Golden Cross", COLORS["success"]
        ema_explain = "EMA-20 has crossed above EMA-50 — short-term momentum is turning bullish. This is the primary buy trigger in the Paper 1 strategy."
    elif ct == "death_cross":
        ema_verdict, ema_color = "Death Cross", COLORS["danger_red"]
        ema_explain = "EMA-20 has crossed below EMA-50 — short-term momentum is turning bearish. This is the primary sell trigger in the Paper 1 strategy."
    else:
        ema_verdict, ema_color = "No Crossover", COLORS["muted"]
        trend = paper1_details.get("ema_trend", "neutral")
        ema_explain = f"No EMA crossover event detected. Current EMA trend bias: {trend}. The system falls back to composite scoring."

    children.append(_chart_card(
        "EMA CROSSOVER",
        dcc.Graph(figure=ema_fig, config={"displayModeBar": False}, style={"height": "280px"}),
        ema_verdict, ema_color, ema_explain,
    ))
    children.append(spacer())

    # --- Chart 2: Volume Confirmation ---
    vol_fig = go.Figure()
    if "Volume" in chart_data.columns:
        close_vals = chart_data["Close"].values
        prev_close = np.roll(close_vals, 1)
        prev_close[0] = close_vals[0]
        vol_colors = [
            "rgba(16, 185, 129, 0.5)" if c >= p else "rgba(255, 107, 107, 0.5)"
            for c, p in zip(close_vals, prev_close)
        ]
        vol_fig.add_trace(go.Bar(
            x=dates, y=chart_data["Volume"].tolist(), name="Volume",
            marker_color=vol_colors, showlegend=False,
        ))
    if "Volume_SMA20" in chart_data.columns:
        vol_fig.add_trace(go.Scatter(
            x=dates, y=chart_data["Volume_SMA20"].tolist(), name="Volume SMA-20",
            line=dict(color=COLORS["teal"], width=2), mode="lines",
        ))

    vol_fig.update_layout(**_chart_layout(280), showlegend=True)
    _chart_axes(vol_fig)

    atv_confirmed = paper1_details.get("atv_confirmed", False)
    if ct in ("golden_cross", "death_cross"):
        if atv_confirmed:
            vol_verdict, vol_color = "Volume Confirms", COLORS["success"]
            vol_explain = "ATV slope is rising in the direction of the crossover — volume is confirming the trend signal."
        else:
            vol_verdict, vol_color = "Volume Diverging", COLORS["warning"]
            vol_explain = "ATV slope does not confirm the crossover — volume divergence weakens the signal."
    else:
        vol_verdict, vol_color = "No Signal", COLORS["muted"]
        vol_explain = "No crossover to confirm. Volume is shown for context."

    children.append(_chart_card(
        "VOLUME CONFIRMATION",
        dcc.Graph(figure=vol_fig, config={"displayModeBar": False}, style={"height": "280px"}),
        vol_verdict, vol_color, vol_explain,
    ))
    children.append(spacer())

    # --- Chart 3: RSI Gate ---
    rsi_fig = go.Figure()
    # Shaded zones
    rsi_fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239, 68, 68, 0.06)", line_width=0)
    rsi_fig.add_hrect(y0=0, y1=30, fillcolor="rgba(16, 185, 129, 0.06)", line_width=0)

    if "RSI" in chart_data.columns:
        rsi_fig.add_trace(go.Scatter(
            x=dates, y=chart_data["RSI"].tolist(), name="RSI",
            line=dict(color=COLORS["teal"], width=2), mode="lines",
            showlegend=False,
        ))

    # Horizontal reference lines
    rsi_fig.add_hline(y=70, line=dict(color=COLORS["danger_red"], dash="dash", width=1))
    rsi_fig.add_hline(y=30, line=dict(color=COLORS["success"], dash="dash", width=1))
    rsi_fig.add_hline(y=50, line=dict(color="#9CA3AF", dash="dot", width=1))

    # Current RSI marker
    rsi_safe = rsi_value if rsi_value is not None and not pd.isna(rsi_value) else 50
    if "RSI" in chart_data.columns and len(dates) > 0:
        rsi_fig.add_trace(go.Scatter(
            x=[dates[-1]], y=[rsi_safe], mode="markers+text",
            marker=dict(size=8, color=COLORS["teal"], line=dict(width=2, color="white")),
            text=[f"{rsi_safe:.0f}"], textposition="top center",
            textfont=dict(size=10, color=COLORS["teal"], family=FONTS["primary"]),
            showlegend=False,
        ))

    rsi_fig.update_layout(**_chart_layout(280), showlegend=False)
    rsi_fig.update_yaxes(range=[0, 100], showgrid=True, gridcolor="#F1F5F9",
                          tickfont=dict(size=10, color=COLORS["muted"]))
    rsi_fig.update_xaxes(showgrid=False, showline=True, linecolor=COLORS["border"],
                          tickfont=dict(size=10, color=COLORS["muted"]))

    rsi_gate = paper1_details.get("rsi_gate", "n/a")
    if rsi_gate == "passed":
        rsi_verdict, rsi_color = "Gate Passed", COLORS["success"]
        rsi_explain = f"RSI at {rsi_safe:.0f} is within acceptable range. The signal is not blocked."
    elif rsi_gate == "blocked_overbought":
        rsi_verdict, rsi_color = "Blocked \u2014 Overbought", COLORS["danger_red"]
        rsi_explain = f"RSI at {rsi_safe:.0f} exceeds 70 (overbought). Buy signal is blocked to prevent chasing."
    elif rsi_gate == "blocked_oversold":
        rsi_verdict, rsi_color = "Blocked \u2014 Oversold", COLORS["danger_red"]
        rsi_explain = f"RSI at {rsi_safe:.0f} is below 30 (oversold). Sell signal is blocked to prevent panic selling."
    else:
        rsi_verdict, rsi_color = "No Gate Applied", COLORS["muted"]
        rsi_explain = f"RSI at {rsi_safe:.0f}. No crossover-based signal to gate."

    children.append(_chart_card(
        "RSI GATE",
        dcc.Graph(figure=rsi_fig, config={"displayModeBar": False}, style={"height": "280px"}),
        rsi_verdict, rsi_color, rsi_explain,
    ))
    children.append(spacer())

    # =========================================================================
    # SECTION 2: SUPPORTING INDICATORS (side by side)
    # =========================================================================

    # --- MACD ---
    macd_fig = go.Figure()
    if "MACD_HIST" in chart_data.columns:
        hist_vals = chart_data["MACD_HIST"].tolist()
        hist_colors = [
            COLORS["success"] if (v is not None and v >= 0) else COLORS["coral"]
            for v in hist_vals
        ]
        macd_fig.add_trace(go.Bar(
            x=dates, y=hist_vals, name="Histogram",
            marker_color=hist_colors, opacity=0.5, showlegend=False,
        ))
    if "MACD" in chart_data.columns:
        macd_fig.add_trace(go.Scatter(
            x=dates, y=chart_data["MACD"].tolist(), name="MACD",
            line=dict(color=COLORS["teal"], width=2),
        ))
    if "MACD_SIGNAL" in chart_data.columns:
        macd_fig.add_trace(go.Scatter(
            x=dates, y=chart_data["MACD_SIGNAL"].tolist(), name="Signal",
            line=dict(color=COLORS["coral"], width=2),
        ))
    macd_fig.add_hline(y=0, line=dict(color="#9CA3AF", dash="dot", width=1))
    macd_fig.update_layout(**_chart_layout(250), showlegend=True)
    _chart_axes(macd_fig)

    # MACD verdict
    macd_val = float(chart_data["MACD"].iloc[-1]) if "MACD" in chart_data.columns else 0
    macd_sig = float(chart_data["MACD_SIGNAL"].iloc[-1]) if "MACD_SIGNAL" in chart_data.columns else 0
    if macd_val > macd_sig:
        macd_verdict, macd_vcolor = "Bullish", COLORS["success"]
        macd_explain = "MACD is above the signal line — momentum favours buyers."
    else:
        macd_verdict, macd_vcolor = "Bearish", COLORS["coral"]
        macd_explain = "MACD is below the signal line — momentum favours sellers."

    macd_card = _chart_card(
        "MACD",
        dcc.Graph(figure=macd_fig, config={"displayModeBar": False}, style={"height": "250px"}),
        macd_verdict, macd_vcolor, macd_explain,
    )

    # --- Bollinger Bands ---
    bb_fig = go.Figure()
    has_bb = all(c in chart_data.columns for c in ["BB_Upper", "BB_Mid", "BB_Lower"])

    if has_bb:
        # Shaded band
        bb_fig.add_trace(go.Scatter(
            x=dates, y=chart_data["BB_Upper"].tolist(), name="Upper Band",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ))
        bb_fig.add_trace(go.Scatter(
            x=dates, y=chart_data["BB_Lower"].tolist(), name="Lower Band",
            line=dict(width=0), fill="tonexty",
            fillcolor="rgba(0, 151, 167, 0.06)", showlegend=False, hoverinfo="skip",
        ))
        # Band lines
        bb_fig.add_trace(go.Scatter(
            x=dates, y=chart_data["BB_Upper"].tolist(), name="Upper",
            line=dict(color=COLORS["muted"], width=1, dash="dot"), mode="lines",
        ))
        bb_fig.add_trace(go.Scatter(
            x=dates, y=chart_data["BB_Mid"].tolist(), name="Mid",
            line=dict(color=COLORS["muted"], width=1), mode="lines",
        ))
        bb_fig.add_trace(go.Scatter(
            x=dates, y=chart_data["BB_Lower"].tolist(), name="Lower",
            line=dict(color=COLORS["muted"], width=1, dash="dot"), mode="lines",
        ))

    # Price on top
    bb_fig.add_trace(go.Scatter(
        x=dates, y=chart_data["Close"].tolist(), name="Price",
        line=dict(color=COLORS["heading"], width=2), mode="lines",
    ))

    bb_fig.update_layout(**_chart_layout(250), showlegend=True)
    _chart_axes(bb_fig, y_prefix="$")

    # BB verdict
    if has_bb:
        curr = float(chart_data["Close"].iloc[-1])
        upper = float(chart_data["BB_Upper"].iloc[-1])
        lower = float(chart_data["BB_Lower"].iloc[-1])
        bb_range = upper - lower if upper != lower else 1
        pos = (curr - lower) / bb_range
        if pos > 0.85:
            bb_verdict, bb_vcolor = "Near Upper Band", COLORS["warning"]
            bb_explain = "Price is near the upper Bollinger Band — potential resistance or overbought condition."
        elif pos < 0.15:
            bb_verdict, bb_vcolor = "Near Lower Band", COLORS["success"]
            bb_explain = "Price is near the lower Bollinger Band — potential support or oversold condition."
        else:
            bb_verdict, bb_vcolor = "Within Range", COLORS["muted"]
            bb_explain = "Price is within the Bollinger Bands — no extreme condition detected."
    else:
        bb_verdict, bb_vcolor = "No Data", COLORS["muted"]
        bb_explain = "Bollinger Bands data not available."

    bb_card = _chart_card(
        "BOLLINGER BANDS",
        dcc.Graph(figure=bb_fig, config={"displayModeBar": False}, style={"height": "250px"}),
        bb_verdict, bb_vcolor, bb_explain,
    )

    children.append(html.Div([
        html.Div(macd_card, style={"flex": 1, "minWidth": 0}),
        html.Div(bb_card, style={"flex": 1, "minWidth": 0}),
    ], style={"display": "flex", "gap": "12px", "alignItems": "stretch"}))

    children.append(spacer())

    # =========================================================================
    # SECTION 3: KEY LEVELS
    # =========================================================================
    current_price = float(price_data["Close"].iloc[-1])
    high_52w = float(price_data["High"].max())
    low_52w = float(price_data["Low"].min())
    price_range = high_52w - low_52w if high_52w != low_52w else 1
    range_pct = (current_price - low_52w) / price_range * 100

    sma50 = float(price_data["SMA50"].iloc[-1]) if "SMA50" in price_data.columns and pd.notna(price_data["SMA50"].iloc[-1]) else None
    sma200 = float(price_data["SMA200"].iloc[-1]) if "SMA200" in price_data.columns and pd.notna(price_data["SMA200"].iloc[-1]) else None

    def _level_tag(lbl, val, color=None):
        return html.Div([
            html.Span(lbl, style={
                "fontSize": "11px", "fontWeight": 500,
                "color": COLORS["muted"], "marginRight": "6px",
            }),
            html.Span(f"${val:.2f}", style={
                "fontSize": "12px", "fontWeight": 600,
                "color": color or COLORS["text_primary"],
            }),
        ], style={
            "display": "inline-block", "padding": "4px 12px",
            "background": "#F8FAFB", "borderRadius": "8px",
        })

    level_children = [
        label("Key Levels"),
        # 52-week range bar
        html.Div([
            html.Div([
                html.Span(f"52W Low ${low_52w:.2f}", style={
                    "fontSize": "11px", "color": COLORS["muted"],
                }),
                html.Span(f"52W High ${high_52w:.2f}", style={
                    "fontSize": "11px", "color": COLORS["muted"],
                }),
            ], style={"display": "flex", "justifyContent": "space-between", "marginBottom": "4px"}),
            html.Div(
                html.Div(style={
                    "width": f"{max(2, min(98, range_pct)):.0f}%",
                    "height": "100%",
                    "background": COLORS["teal"],
                    "borderRadius": "6px",
                    "position": "relative",
                }),
                style={
                    "background": "#F1F5F9", "borderRadius": "6px",
                    "height": "8px", "overflow": "hidden",
                },
            ),
            html.Div(f"Current: ${current_price:.2f} ({range_pct:.0f}% of range)", style={
                "fontSize": "11px", "color": COLORS["text_secondary"],
                "marginTop": "4px",
            }),
        ], style={"marginBottom": "14px"}),
        # Support / Resistance tags
        html.Div([
            _level_tag("Support (SMA50)", sma50, COLORS["success"]) if sma50 else None,
            _level_tag("Resistance (SMA200)", sma200, COLORS["coral"]) if sma200 else None,
        ], style={"display": "flex", "gap": "10px", "flexWrap": "wrap"}),
    ]

    children.append(card(level_children))
    children.append(spacer())

    # =========================================================================
    # SECTION 4: AI MODEL LENS (conditional)
    # =========================================================================
    if rl_prediction is not None:
        rl_action_map = {0: "BUY", 1: "SELL", 2: "HOLD"}
        rl_signal = paper1_details.get("rl_signal", rl_action_map.get(rl_prediction, "HOLD"))
        rl_agrees = paper1_details.get("rl_agrees")

        rec_colors = {"BUY": COLORS["success"], "SELL": COLORS["coral"], "HOLD": COLORS["warning"]}
        rl_color = rec_colors.get(rl_signal, COLORS["warning"])

        # Build RL input rows
        def _rl_row(lbl, val):
            return html.Div([
                html.Span(lbl, style={
                    "fontSize": "12px", "color": COLORS["text_secondary"],
                    "fontWeight": 450, "fontFamily": FONTS["primary"],
                }),
                html.Span(val, style={
                    "fontSize": "12px", "color": COLORS["text_primary"],
                    "fontWeight": 600, "fontFamily": FONTS["primary"],
                }),
            ], style={
                "display": "flex", "justifyContent": "space-between",
                "padding": "6px 0",
                "borderBottom": f"1px solid {COLORS['border']}",
            })

        ema_signal_val = paper1_details.get("ema_cross_signal", 0)
        atv_slope_val = paper1_details.get("atv_slope", 0)
        rsi_val = paper1_details.get("rsi", rsi_safe if 'rsi_safe' in dir() else 50)

        # Get 1d/5d returns and rel volume from price data
        ret_1d = 0
        ret_5d = 0
        rel_vol = 1.0
        if len(price_data) > 1:
            ret_1d = (float(price_data["Close"].iloc[-1]) / float(price_data["Close"].iloc[-2]) - 1) * 100
        if len(price_data) > 5:
            ret_5d = (float(price_data["Close"].iloc[-1]) / float(price_data["Close"].iloc[-6]) - 1) * 100
        if "Rel_Volume" in price_data.columns and pd.notna(price_data["Rel_Volume"].iloc[-1]):
            rel_vol = float(price_data["Rel_Volume"].iloc[-1])

        # Agreement
        rule_rec = stock_data.get("recommendation", {}).get("recommendation", "HOLD")
        agrees = rl_agrees if rl_agrees is not None else (rl_signal == rule_rec)
        agree_text = "Agrees" if agrees else "Disagrees"
        agree_color = COLORS["success"] if agrees else COLORS["warning"]

        ai_children = [
            label("AI Model Lens (PPO Agent)"),
            html.Div([
                html.Span("RL Input Features", style={
                    "fontSize": "11px", "color": COLORS["muted"],
                    "fontWeight": 600, "textTransform": "uppercase",
                    "letterSpacing": "0.04em",
                }),
            ], style={"marginBottom": "6px"}),
            _rl_row("EMA Signal", str(ema_signal_val)),
            _rl_row("ATV Slope", f"{atv_slope_val:,.0f}"),
            _rl_row("1-Day Return", f"{ret_1d:+.2f}%"),
            _rl_row("5-Day Return", f"{ret_5d:+.2f}%"),
            _rl_row("RSI", f"{rsi_val:.1f}"),
            _rl_row("Relative Volume", f"{rel_vol:.2f}x"),
            html.Div(style={"height": "12px"}),
            html.Div([
                html.Span("Action: ", style={
                    "fontSize": "12px", "color": COLORS["text_secondary"],
                    "fontWeight": 500, "marginRight": "8px",
                }),
                _verdict_badge(rl_signal, rl_color),
            ], style={"marginBottom": "8px"}),
            html.Div([
                html.Span("vs Rule-Based: ", style={
                    "fontSize": "12px", "color": COLORS["text_secondary"],
                    "fontWeight": 500, "marginRight": "8px",
                }),
                html.Span(agree_text, style={
                    "fontSize": "12px", "fontWeight": 700,
                    "color": agree_color,
                }),
            ]),
        ]

        children.append(card(ai_children))

    return html.Div(children)
