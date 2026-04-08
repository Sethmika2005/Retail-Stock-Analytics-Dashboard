# =============================================================================
# ANALYSIS TAB - "The Interpretation" — What to do and why (Streamlit — mirrors Dash)
# =============================================================================

import pandas as pd
import streamlit as st

from components import COLORS, FONTS, SHADOWS, get_status_color
from models import (
    generate_recommendation_paper1,
    generate_bull_bear_case,
    generate_action_checklist, generate_view_changers,
)

# Shared inline styles
CARD = (
    "background:#FFFFFF;border:1px solid #E8EDF2;border-radius:14px;"
    "padding:16px 20px;"
    "box-shadow:0 1px 3px rgba(0,0,0,0.04),0 1px 2px rgba(0,0,0,0.02);"
)
LABEL = (
    "font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;font-size:11px;font-weight:600;"
    "color:#94A3B8;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;"
)


# =============================================================================
# HELPERS
# =============================================================================

def _build_narrative_html(rec, paper1_details, rsi_value, rl_prediction):
    """Build a plain-English narrative explaining the current signal (HTML version)."""
    if not paper1_details:
        return ('<span style="font-size:13px;color:#94A3B8;line-height:1.6;">'
                'Insufficient data for full signal analysis.</span>')

    crossover = paper1_details.get("crossover_type", "none")
    atv_confirmed = paper1_details.get("atv_confirmed", False)
    rsi_gate = paper1_details.get("rsi_gate", "n/a")
    rl_signal = paper1_details.get("rl_signal")
    rl_agrees = paper1_details.get("rl_agrees")
    rsi_safe = rsi_value if rsi_value is not None and not pd.isna(rsi_value) else 50

    rec_colors = {"BUY": "#10B981", "SELL": "#FF6B6B", "HOLD": "#F59E0B"}
    rec_color = rec_colors.get(rec, "#F59E0B")

    parts = []

    # Recommendation
    parts.append('<span style="color:#1E293B;">We recommend </span>')
    parts.append(f'<span style="font-weight:700;color:{rec_color};">{rec}</span>')

    # Crossover explanation
    if crossover == "golden_cross":
        parts.append('<span> because SMA-20 crossed above SMA-50 (</span>')
        parts.append('<span style="font-weight:700;color:#10B981;">Golden Cross</span>')
        parts.append('<span>)</span>')
    elif crossover == "death_cross":
        parts.append('<span> because SMA-20 crossed below SMA-50 (</span>')
        parts.append('<span style="font-weight:700;color:#FF6B6B;">Death Cross</span>')
        parts.append('<span>)</span>')
    else:
        sma_trend = paper1_details.get("sma_trend", "neutral")
        parts.append(f'<span>. No crossover event detected \u2014 SMA trend is </span>')
        parts.append(f'<span style="font-weight:600;">{sma_trend}</span>')

    # Volume confirmation
    if crossover in ("golden_cross", "death_cross"):
        if atv_confirmed:
            parts.append('<span>, volume confirmed with </span>')
            parts.append('<span style="font-weight:600;">rising ATV slope</span>')
        else:
            parts.append('<span>, but volume </span>')
            parts.append('<span style="font-weight:600;color:#F59E0B;">did not confirm</span>')
            parts.append('<span> (ATV slope diverging)</span>')

    # RSI gate
    if rsi_gate == "passed":
        parts.append(f'<span>, and RSI at {rsi_safe:.0f} </span>')
        parts.append('<span style="font-weight:600;color:#10B981;">passed</span>')
        parts.append('<span> the overbought gate</span>')
    elif rsi_gate == "blocked_overbought":
        parts.append(f'<span>. However, RSI at {rsi_safe:.0f} is </span>')
        parts.append('<span style="font-weight:600;color:#FF6B6B;">overbought</span>')
        parts.append('<span> \u2014 BUY signal blocked</span>')
    elif rsi_gate == "blocked_oversold":
        parts.append(f'<span>. However, RSI at {rsi_safe:.0f} is </span>')
        parts.append('<span style="font-weight:600;color:#FF6B6B;">oversold</span>')
        parts.append('<span> \u2014 SELL signal blocked</span>')

    # AI model
    if rl_signal:
        if rl_agrees:
            parts.append('<span>. The </span>')
            parts.append('<span style="font-weight:600;color:#10B981;">AI model agrees</span>')
        else:
            parts.append('<span>. The AI model </span>')
            parts.append(f'<span style="font-weight:600;color:#F59E0B;">disagrees</span>')
            parts.append(f'<span> (predicts {rl_signal})</span>')
    elif rl_prediction is None:
        parts.append('<span>. No AI model available for this stock</span>')

    parts.append('<span>.</span>')

    return "".join(parts)



# =============================================================================
# RENDER
# =============================================================================

def render(selected, price_data, info, tech_score, tech_details,
           market_regime, regime_metrics, last_row,
           volume_score=0, volume_details=None,
           rsi_value=50,
           paper1_details=None, rl_prediction=None, cost_basis=None):
    """Render the Analysis tab content — mirrors Dash analysis tab exactly."""

    # Generate recommendation
    recommendation_data = generate_recommendation_paper1(
        tech_score, volume_score, rsi_value,
        market_regime, selected, info, time_horizon="long",
        price_data=price_data, rl_prediction=rl_prediction,
    )

    rec = recommendation_data["recommendation"]
    confidence = recommendation_data["confidence"]
    weights = recommendation_data.get("weights", {})

    p1 = paper1_details or {}

    # =========================================================================
    # 1. WHY THIS SIGNAL
    # =========================================================================
    narrative_html = _build_narrative_html(rec, p1 if p1 else None, rsi_value, rl_prediction)

    st.markdown(f"""
    <div style="{CARD}">
        <div style="{LABEL}">Why This Signal</div>
        <div style="font-size:13.5px;color:#1E293B;line-height:1.7;
                    font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">
            {narrative_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # 2. BULL VS BEAR CASE
    # =========================================================================
    bull_case, bear_case = generate_bull_bear_case(info, tech_score, price_data, market_regime)

    def _case_items_html(items, color, bg_rgba):
        html = ""
        for item in items:
            html += (
                f'<div style="border-left:3px solid {color};border-radius:0 6px 6px 0;'
                f'background:{bg_rgba};padding:8px 12px;margin-bottom:6px;font-size:12.5px;'
                f'color:#1E293B;line-height:1.4;font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">'
                f'{item}</div>'
            )
        return html

    bull_col, bear_col = st.columns(2)

    with bull_col:
        st.markdown(f"""
        <div style="{CARD}">
            <div style="display:flex;align-items:center;margin-bottom:10px;">
                <span style="color:#10B981;margin-right:6px;">\u25cf</span>
                <span style="{LABEL} margin-bottom:0;">BULL CASE</span>
            </div>
            {_case_items_html(bull_case, "#10B981", "rgba(16,185,129,0.04)")}
        </div>
        """, unsafe_allow_html=True)

    with bear_col:
        st.markdown(f"""
        <div style="{CARD}">
            <div style="display:flex;align-items:center;margin-bottom:10px;">
                <span style="color:#FF6B6B;margin-right:6px;">\u25cf</span>
                <span style="{LABEL} margin-bottom:0;">BEAR CASE</span>
            </div>
            {_case_items_html(bear_case, "#FF6B6B", "rgba(255,107,107,0.04)")}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # 3. ACTION CHECKLIST + VIEW CHANGERS
    # =========================================================================
    action_items = generate_action_checklist(rec, info, price_data)
    view_changers = generate_view_changers(rec, info, price_data)

    action_html = ""
    for a in action_items:
        action_html += (
            f'<div style="margin-bottom:8px;">'
            f'<span style="color:#0097A7;font-weight:700;margin-right:6px;font-size:13px;">\u2713</span>'
            f'<span style="font-size:12.5px;color:#1E293B;line-height:1.5;'
            f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{a}</span></div>'
        )

    changers_html = ""
    for c in view_changers:
        changers_html += (
            f'<div style="margin-bottom:8px;">'
            f'<span style="color:#FF6B6B;font-weight:700;margin-right:6px;font-size:13px;">\u2192</span>'
            f'<span style="font-size:12.5px;color:#1E293B;line-height:1.5;'
            f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{c}</span></div>'
        )

    act_col, chg_col = st.columns(2)

    with act_col:
        st.markdown(f"""
        <div style="{CARD}">
            <div style="{LABEL}">Action Checklist</div>
            {action_html}
        </div>
        """, unsafe_allow_html=True)

    with chg_col:
        st.markdown(f"""
        <div style="{CARD}">
            <div style="{LABEL}">What Would Change This View</div>
            {changers_html}
        </div>
        """, unsafe_allow_html=True)

    # =========================================================================
    # 4. POSITION P&L (conditional)
    # =========================================================================
    if cost_basis is not None:
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        current_price = float(price_data["Close"].iloc[-1])
        pnl_pct = (current_price - cost_basis) / cost_basis * 100
        pnl_dollar = current_price - cost_basis
        is_profit = pnl_pct >= 0
        pnl_color = "#10B981" if is_profit else "#EF4444"
        pnl_label = "profit" if is_profit else "loss"
        action_word = "gain" if is_profit else "lose"

        examples_html = ""
        for qty in [10, 50, 100]:
            total_pnl = pnl_dollar * qty
            examples_html += (
                f'<span style="display:inline-block;padding:3px 10px;background:#F8FAFB;'
                f'border-radius:8px;font-size:11px;font-weight:500;color:{pnl_color};'
                f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">'
                f'{qty} shares = ${abs(total_pnl):,.2f} {pnl_label}</span>'
            )

        st.markdown(f"""
        <div style="{CARD} border-left:4px solid {pnl_color};">
            <div style="{LABEL}">My Position</div>
            <div style="margin-top:4px;">
                <span style="font-size:12px;color:#64748B;">Avg Cost </span>
                <span style="font-size:14px;font-weight:600;color:#1E293B;">${cost_basis:.2f}</span>
                <span style="font-size:12px;color:#64748B;margin:0 4px;"> \u2192 Current </span>
                <span style="font-size:14px;font-weight:600;color:#1E293B;">${current_price:.2f}</span>
            </div>
            <div style="margin-top:8px;">
                <span style="font-size:13px;color:#1E293B;font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">
                    If you sold now, you would {action_word} approx. </span>
                <span style="font-size:13px;font-weight:700;color:{pnl_color};
                             font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">${abs(pnl_dollar):.2f}/share</span>
                <span style="font-size:13px;font-weight:600;color:{pnl_color};
                             font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;"> ({pnl_pct:+.1f}%)</span>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;">{examples_html}</div>
            <div style="font-size:10px;color:#94A3B8;line-height:1.4;
                        font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;
                        margin-top:10px;font-style:italic;">
                Based on your entered average cost. Actual P&amp;L depends on the number of shares held
                and prices at which they were acquired. Does not account for fees, taxes, or dividends.
            </div>
        </div>
        """, unsafe_allow_html=True)
