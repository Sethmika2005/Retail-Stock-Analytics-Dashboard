# =============================================================================
# ANALYSIS TAB - "The Interpretation" — What to do and why (words)
# =============================================================================

import pandas as pd
from dash import html

from components import (
    COLORS, FONTS, SHADOWS, CARD_STYLE, LABEL_STYLE,
    card, label, spacer, progress_bar, signal_row,
    get_status_color,
)
from models import (
    generate_key_drivers, generate_key_risk, generate_bull_bear_case,
    generate_action_checklist, generate_view_changers,
)


# =============================================================================
# HELPERS
# =============================================================================

def _build_narrative(rec, paper1_details, rsi_value, rl_prediction):
    """Build a plain-English narrative explaining the current signal."""
    if not paper1_details:
        return html.Div(
            "Insufficient data for full signal analysis.",
            style={"fontSize": "13px", "color": COLORS["muted"], "lineHeight": "1.6"},
        )

    crossover = paper1_details.get("crossover_type", "none")
    atv_confirmed = paper1_details.get("atv_confirmed", False)
    rsi_gate = paper1_details.get("rsi_gate", "n/a")
    rl_signal = paper1_details.get("rl_signal")
    rl_agrees = paper1_details.get("rl_agrees")
    rsi_safe = rsi_value if rsi_value is not None and not pd.isna(rsi_value) else 50

    rec_colors = {"BUY": COLORS["success"], "SELL": COLORS["coral"], "HOLD": COLORS["warning"]}
    rec_color = rec_colors.get(rec, COLORS["warning"])

    parts = []

    # Recommendation
    parts.append(html.Span("We recommend ", style={"color": COLORS["text_primary"]}))
    parts.append(html.Span(rec, style={"fontWeight": 700, "color": rec_color}))

    # Crossover explanation
    if crossover == "golden_cross":
        parts.append(html.Span(" because EMA-20 crossed above EMA-50 ("))
        parts.append(html.Span("Golden Cross", style={"fontWeight": 700, "color": COLORS["success"]}))
        parts.append(html.Span(")"))
    elif crossover == "death_cross":
        parts.append(html.Span(" because EMA-20 crossed below EMA-50 ("))
        parts.append(html.Span("Death Cross", style={"fontWeight": 700, "color": COLORS["coral"]}))
        parts.append(html.Span(")"))
    else:
        ema_trend = paper1_details.get("ema_trend", "neutral")
        parts.append(html.Span(f". No crossover event detected — EMA trend is "))
        parts.append(html.Span(ema_trend, style={"fontWeight": 600}))

    # Volume confirmation
    if crossover in ("golden_cross", "death_cross"):
        if atv_confirmed:
            parts.append(html.Span(", volume confirmed with "))
            parts.append(html.Span("rising ATV slope", style={"fontWeight": 600}))
        else:
            parts.append(html.Span(", but volume "))
            parts.append(html.Span("did not confirm", style={"fontWeight": 600, "color": COLORS["warning"]}))
            parts.append(html.Span(" (ATV slope diverging)"))

    # RSI gate
    if rsi_gate == "passed":
        parts.append(html.Span(f", and RSI at {rsi_safe:.0f} "))
        parts.append(html.Span("passed", style={"fontWeight": 600, "color": COLORS["success"]}))
        parts.append(html.Span(" the overbought gate"))
    elif rsi_gate == "blocked_overbought":
        parts.append(html.Span(f". However, RSI at {rsi_safe:.0f} is "))
        parts.append(html.Span("overbought", style={"fontWeight": 600, "color": COLORS["coral"]}))
        parts.append(html.Span(" — BUY signal blocked"))
    elif rsi_gate == "blocked_oversold":
        parts.append(html.Span(f". However, RSI at {rsi_safe:.0f} is "))
        parts.append(html.Span("oversold", style={"fontWeight": 600, "color": COLORS["coral"]}))
        parts.append(html.Span(" — SELL signal blocked"))

    # AI model
    if rl_signal:
        if rl_agrees:
            parts.append(html.Span(". The "))
            parts.append(html.Span("AI model agrees", style={"fontWeight": 600, "color": COLORS["success"]}))
        else:
            parts.append(html.Span(". The AI model "))
            parts.append(html.Span("disagrees", style={"fontWeight": 600, "color": COLORS["warning"]}))
            parts.append(html.Span(f" (predicts {rl_signal})"))
    elif rl_prediction is None:
        parts.append(html.Span(". No AI model available for this stock"))

    parts.append(html.Span("."))

    return html.Div(parts, style={
        "fontSize": "13.5px", "color": COLORS["text_primary"],
        "lineHeight": "1.7", "fontFamily": FONTS["primary"],
    })


def _score_color(score):
    """Color based on score level."""
    if score >= 60:
        return COLORS["success"]
    if score >= 40:
        return COLORS["warning"]
    return COLORS["coral"]


# =============================================================================
# RENDER
# =============================================================================

def render(stock_data, price_data, cost_basis):
    ticker = stock_data["ticker"]
    info = stock_data["info"]
    tech_score = stock_data["tech_score"]
    tech_details = stock_data["tech_details"]
    volume_score = stock_data["volume_score"]
    volume_details = stock_data["volume_details"]
    rsi_value = stock_data["rsi_value"]
    market_regime = stock_data["market_regime"]
    paper1_details = stock_data.get("paper1_details") or {}
    rl_prediction = stock_data.get("rl_prediction")
    recommendation_data = stock_data["recommendation"]

    rec = recommendation_data["recommendation"]
    confidence = recommendation_data["confidence"]
    weights = recommendation_data.get("weights", {})

    _explain = {
        "fontSize": "11px", "color": COLORS["muted"],
        "lineHeight": "1.4", "fontFamily": FONTS["primary"],
    }

    children = []

    # =========================================================================
    # 1. WHY THIS SIGNAL
    # =========================================================================
    narrative = _build_narrative(rec, paper1_details if paper1_details else None,
                                 rsi_value, rl_prediction)

    children.append(card([
        label("Why This Signal"),
        narrative,
    ]))

    children.append(spacer())

    # =========================================================================
    # 2. BULL VS BEAR CASE
    # =========================================================================
    bull_case, bear_case = generate_bull_bear_case(info, tech_score, price_data, market_regime)

    def _case_items(items, color, bg_rgba):
        return [html.Div(item, style={
            "borderLeft": f"3px solid {color}",
            "borderRadius": "0 6px 6px 0",
            "background": bg_rgba,
            "padding": "8px 12px",
            "marginBottom": "6px",
            "fontSize": "12.5px",
            "color": COLORS["text_primary"],
            "lineHeight": "1.4",
            "fontFamily": FONTS["primary"],
        }) for item in items]

    bull_card = card([
        html.Div([
            html.Span("\u25cf", style={"color": COLORS["success"], "marginRight": "6px"}),
            html.Span("BULL CASE", style=LABEL_STYLE),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "10px"}),
        *_case_items(bull_case, COLORS["success"], "rgba(16, 185, 129, 0.04)"),
    ])

    bear_card = card([
        html.Div([
            html.Span("\u25cf", style={"color": COLORS["coral"], "marginRight": "6px"}),
            html.Span("BEAR CASE", style=LABEL_STYLE),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "10px"}),
        *_case_items(bear_case, COLORS["coral"], "rgba(255, 107, 107, 0.04)"),
    ])

    children.append(html.Div([
        html.Div(bull_card, style={"flex": 1, "minWidth": 0}),
        html.Div(bear_card, style={"flex": 1, "minWidth": 0}),
    ], style={"display": "flex", "gap": "12px", "alignItems": "stretch"}))

    children.append(spacer())

    # =========================================================================
    # 3. KEY DRIVERS + PRIMARY RISK
    # =========================================================================
    key_drivers = generate_key_drivers(info, tech_score, price_data, market_regime)
    key_risk = generate_key_risk(info, price_data)

    drivers_card = card([
        label("Key Drivers"),
        *[html.Div([
            html.Span("\u25cf", style={"color": COLORS["teal"], "marginRight": "8px", "fontSize": "8px"}),
            html.Span(d, style={
                "fontSize": "12.5px", "color": COLORS["text_primary"],
                "lineHeight": "1.5", "fontFamily": FONTS["primary"],
            }),
        ], style={"display": "flex", "alignItems": "baseline", "marginBottom": "8px"})
          for d in key_drivers],
    ])

    risk_card = card([
        label("Primary Risk"),
        html.Div(key_risk, style={
            "fontSize": "12.5px", "color": COLORS["text_primary"],
            "lineHeight": "1.5", "fontFamily": FONTS["primary"],
            "padding": "10px 12px",
            "background": "rgba(245, 158, 11, 0.06)",
            "borderLeft": f"3px solid {COLORS['warning']}",
            "borderRadius": "0 6px 6px 0",
        }),
    ])

    children.append(html.Div([
        html.Div(drivers_card, style={"flex": 2, "minWidth": 0}),
        html.Div(risk_card, style={"flex": 1, "minWidth": 0}),
    ], style={"display": "flex", "gap": "12px", "alignItems": "stretch"}))

    children.append(spacer())

    # =========================================================================
    # 4. SCORE BREAKDOWN
    # =========================================================================
    trend_v = tech_details.get("trend", 0)
    rsi_v = tech_details.get("rsi", 0)
    macd_v = tech_details.get("macd", 0)

    # Normalize sub-scores to percentage for bars
    trend_pct = (float(trend_v) / 40 * 100) if trend_v != "N/A" else 0
    rsi_pct = (float(rsi_v) / 30 * 100) if rsi_v != "N/A" else 0
    macd_pct = (float(macd_v) / 30 * 100) if macd_v != "N/A" else 0

    tech_card = card([
        label("Technical Score"),
        html.Div([
            html.Span(str(tech_score), style={
                "fontSize": "32px", "fontWeight": 700,
                "color": _score_color(tech_score),
                "fontFamily": FONTS["primary"],
            }),
            html.Span("/100", style={
                "fontSize": "14px", "fontWeight": 500,
                "color": COLORS["muted"], "marginLeft": "2px",
            }),
        ], style={"marginBottom": "12px"}),
        progress_bar("Overall", tech_score, _score_color(tech_score)),
        progress_bar(f"Trend ({trend_v}/40)", trend_pct, COLORS["teal"]),
        progress_bar(f"RSI ({rsi_v}/30)", rsi_pct, COLORS["teal"]),
        progress_bar(f"MACD ({macd_v}/30)", macd_pct, COLORS["teal"]),
    ])

    # Volume sub-scores
    vol_details = (volume_details or {}).get("details", {})
    align_score = vol_details.get("alignment_score", 0)
    rel_vol_score = vol_details.get("rel_volume_score", 0)
    confirms = (volume_details or {}).get("volume_confirms_trend", False)

    align_pct = (float(align_score) / 50 * 100) if align_score else 0
    rel_pct = (float(rel_vol_score) / 50 * 100) if rel_vol_score else 0

    vol_card = card([
        label("Volume Score"),
        html.Div([
            html.Span(str(volume_score), style={
                "fontSize": "32px", "fontWeight": 700,
                "color": _score_color(volume_score),
                "fontFamily": FONTS["primary"],
            }),
            html.Span("/100", style={
                "fontSize": "14px", "fontWeight": 500,
                "color": COLORS["muted"], "marginLeft": "2px",
            }),
        ], style={"marginBottom": "12px"}),
        progress_bar("Overall", volume_score, _score_color(volume_score)),
        progress_bar(f"Alignment ({align_score:.0f}/50)", align_pct, COLORS["teal"]),
        progress_bar(f"Rel Volume ({rel_vol_score:.0f}/50)", rel_pct, COLORS["teal"]),
        html.Div([
            html.Span("Confirms Trend: ", style={
                "fontSize": "12px", "color": COLORS["text_secondary"],
                "fontFamily": FONTS["primary"],
            }),
            html.Span("Yes" if confirms else "No", style={
                "fontSize": "12px", "fontWeight": 600,
                "color": COLORS["success"] if confirms else COLORS["warning"],
                "fontFamily": FONTS["primary"],
            }),
        ], style={"marginTop": "4px"}),
    ])

    children.append(html.Div([
        html.Div(tech_card, style={"flex": 1, "minWidth": 0}),
        html.Div(vol_card, style={"flex": 1, "minWidth": 0}),
    ], style={"display": "flex", "gap": "12px", "alignItems": "stretch"}))

    children.append(spacer())

    # =========================================================================
    # 5. ACTION CHECKLIST + VIEW CHANGERS
    # =========================================================================
    action_items = generate_action_checklist(rec, info, price_data)
    view_changers = generate_view_changers(rec, info, price_data)

    action_card = card([
        label("Action Checklist"),
        *[html.Div([
            html.Span("\u2713 ", style={
                "color": COLORS["teal"], "fontWeight": 700,
                "marginRight": "6px", "fontSize": "13px",
            }),
            html.Span(a, style={
                "fontSize": "12.5px", "color": COLORS["text_primary"],
                "lineHeight": "1.5", "fontFamily": FONTS["primary"],
            }),
        ], style={"marginBottom": "8px"}) for a in action_items],
    ])

    changers_card = card([
        label("What Would Change This View"),
        *[html.Div([
            html.Span("\u2192 ", style={
                "color": COLORS["coral"], "fontWeight": 700,
                "marginRight": "6px", "fontSize": "13px",
            }),
            html.Span(c, style={
                "fontSize": "12.5px", "color": COLORS["text_primary"],
                "lineHeight": "1.5", "fontFamily": FONTS["primary"],
            }),
        ], style={"marginBottom": "8px"}) for c in view_changers],
    ])

    children.append(html.Div([
        html.Div(action_card, style={"flex": 1, "minWidth": 0}),
        html.Div(changers_card, style={"flex": 1, "minWidth": 0}),
    ], style={"display": "flex", "gap": "12px", "alignItems": "stretch"}))

    # =========================================================================
    # 6. POSITION P&L (conditional)
    # =========================================================================
    if cost_basis is not None:
        children.append(spacer())
        current_price = float(price_data["Close"].iloc[-1])
        pnl_pct = (current_price - cost_basis) / cost_basis * 100
        pnl_dollar = current_price - cost_basis
        is_profit = pnl_pct >= 0
        pnl_color = COLORS["success"] if is_profit else COLORS["danger_red"]
        pnl_label = "profit" if is_profit else "loss"
        action_word = "gain" if is_profit else "lose"

        # Example P&L for 10, 50, 100 shares
        examples = []
        for qty in [10, 50, 100]:
            total_pnl = pnl_dollar * qty
            examples.append(f"{qty} shares = ${abs(total_pnl):,.2f} {pnl_label}")

        children.append(card([
            label("My Position"),
            # Main P&L line
            html.Div([
                html.Span("Avg Cost ", style={
                    "fontSize": "12px", "color": COLORS["text_secondary"],
                }),
                html.Span(f"${cost_basis:.2f}", style={
                    "fontSize": "14px", "fontWeight": 600,
                    "color": COLORS["text_primary"],
                }),
                html.Span(" → Current ", style={
                    "fontSize": "12px", "color": COLORS["text_secondary"],
                    "margin": "0 4px",
                }),
                html.Span(f"${current_price:.2f}", style={
                    "fontSize": "14px", "fontWeight": 600,
                    "color": COLORS["text_primary"],
                }),
            ], style={"marginTop": "4px"}),
            # Per-share result
            html.Div([
                html.Span(f"If you sold now, you would {action_word} approx. ", style={
                    "fontSize": "13px", "color": COLORS["text_primary"],
                    "fontFamily": FONTS["primary"],
                }),
                html.Span(f"${abs(pnl_dollar):.2f}/share", style={
                    "fontSize": "13px", "fontWeight": 700,
                    "color": pnl_color, "fontFamily": FONTS["primary"],
                }),
                html.Span(f" ({pnl_pct:+.1f}%)", style={
                    "fontSize": "13px", "fontWeight": 600,
                    "color": pnl_color, "fontFamily": FONTS["primary"],
                }),
            ], style={"marginTop": "8px"}),
            # Example quantities
            html.Div([
                html.Span(ex, style={
                    "display": "inline-block", "padding": "3px 10px",
                    "background": "#F8FAFB", "borderRadius": "8px",
                    "fontSize": "11px", "fontWeight": 500,
                    "color": pnl_color, "fontFamily": FONTS["primary"],
                }) for ex in examples
            ], style={"display": "flex", "gap": "8px", "flexWrap": "wrap", "marginTop": "8px"}),
            # Disclaimer
            html.Div(
                "Based on your entered average cost. Actual P&L depends on the number of shares held "
                "and prices at which they were acquired. Does not account for fees, taxes, or dividends.",
                style={
                    "fontSize": "10px", "color": COLORS["muted"],
                    "lineHeight": "1.4", "fontFamily": FONTS["primary"],
                    "marginTop": "10px", "fontStyle": "italic",
                },
            ),
        ], borderLeft=f"4px solid {pnl_color}"))

    return html.Div(children)
