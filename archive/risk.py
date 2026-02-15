# =============================================================================
# RISK TAB - Risk assessment and volatility analysis
# =============================================================================

import numpy as np
import streamlit as st
from models import classify_risk
from components import render_badge_card, render_metric_card


def render(price_data, risk_score, risk_details, last_row):
    """Render the Risk Assessment tab content."""
    st.subheader("Risk Outlook")
    st.caption("Risk assessment based on volatility, drawdown, and technical indicators.")

    # =========================================================================
    # RISK SCORE BREAKDOWN
    # =========================================================================
    st.markdown("### Risk Score")

    risk_score_status = "success" if risk_score >= 60 else "warning" if risk_score >= 40 else "danger"

    risk_score_col1, risk_score_col2 = st.columns([1, 2])

    with risk_score_col1:
        risk_score_tip = f"Risk Score of {risk_score}/100 measures investment safety. Higher scores mean lower risk. Above 60 is low risk, below 40 is high risk."
        st.markdown(render_badge_card("Risk Score", f"{risk_score}/100", "🛡️", risk_score_tip, risk_score_status), unsafe_allow_html=True)

    with risk_score_col2:
        st.markdown("**Score Breakdown:**")

        # Volatility Score (50 max)
        vol_pts = risk_details.get("volatility", 0)
        vol_pct_score = vol_pts / 50 * 100
        vol_60d_val = risk_details.get("vol_60d", 0)
        st.markdown(f"**Volatility** ({vol_pts}/50 pts)")
        st.progress(vol_pct_score / 100)
        if vol_60d_val:
            vol_annualized = vol_60d_val * 100
            if vol_annualized < 20:
                vol_assess = "Very Low - Stable price action, suitable for conservative investors"
            elif vol_annualized < 30:
                vol_assess = "Low - Below average volatility, manageable swings"
            elif vol_annualized < 40:
                vol_assess = "Moderate - Average volatility, standard risk management"
            elif vol_annualized < 50:
                vol_assess = "High - Above average swings, consider position sizing"
            else:
                vol_assess = "Very High - Significant price swings, use caution"
            st.caption(f"60-Day Volatility: {vol_annualized:.1f}% annualized ({vol_assess})")

        # Drawdown Score (50 max)
        dd_pts = risk_details.get("drawdown", 0)
        dd_pct_score = dd_pts / 50 * 100
        max_dd_val = risk_details.get("max_drawdown", 0)
        st.markdown(f"**Drawdown** ({dd_pts}/50 pts)")
        st.progress(dd_pct_score / 100)
        if max_dd_val:
            dd_percent = abs(max_dd_val * 100)
            if dd_percent < 10:
                dd_assess = "Minimal - Very limited downside over past year"
            elif dd_percent < 20:
                dd_assess = "Moderate - Normal correction territory"
            elif dd_percent < 30:
                dd_assess = "Significant - Notable pullback from highs"
            elif dd_percent < 40:
                dd_assess = "Severe - Major decline experienced"
            else:
                dd_assess = "Extreme - Deep drawdown, high risk"
            st.caption(f"Max Drawdown (1Y): -{dd_percent:.1f}% ({dd_assess})")

    st.markdown("---")

    risk_level, risk_color, risk_factors = classify_risk(price_data)

    # Calculate additional risk metrics
    returns = price_data["Close"].pct_change().dropna()
    vol_30d = returns.tail(30).std() * np.sqrt(252) if len(returns) >= 30 else 0
    vol_60d = returns.tail(60).std() * np.sqrt(252) if len(returns) >= 60 else 0

    prices = price_data["Close"].tail(252)
    rolling_max = prices.expanding().max()
    drawdown = (prices - rolling_max) / rolling_max
    max_dd = drawdown.min()
    current_dd = drawdown.iloc[-1]

    # Risk level card
    st.markdown("### Overall Risk Assessment")

    risk_main_col1, risk_main_col2 = st.columns([1, 2])

    risk_tab_tips = {
        "Low": "Low Risk: Volatility is under 30% annualized with no extreme RSI readings.",
        "Medium": "Medium Risk: Moderate volatility (30-50% annualized) detected.",
        "High": "High Risk: Elevated volatility (over 50% annualized) or extreme technical readings."
    }
    risk_tab_tip = risk_tab_tips.get(risk_level, "Risk level determined by 60-day volatility and RSI extremes.")

    with risk_main_col1:
        risk_emoji = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}.get(risk_level, "⚪")
        risk_tab_status = {"Low": "success", "Medium": "warning", "High": "danger"}.get(risk_level, "neutral")
        st.markdown(render_badge_card("Risk Level", f"{risk_level} Risk", risk_emoji, risk_tab_tip, risk_tab_status), unsafe_allow_html=True)

    with risk_main_col2:
        st.markdown("**Contributing Factors:**")
        for factor in risk_factors:
            st.markdown(f"- {factor}")

    st.markdown("### Volatility Metrics")
    vol_col1, vol_col2, vol_col3 = st.columns(3)

    with vol_col1:
        vol30_status = "success" if vol_30d < 0.25 else "warning" if vol_30d < 0.40 else "danger"
        vol30_tip = f"30-Day Volatility of {vol_30d*100:.1f}% (annualized)"
        st.markdown(render_metric_card("30-Day Volatility", f"{vol_30d*100:.1f}%", vol30_tip, vol30_status, "medium"), unsafe_allow_html=True)

    with vol_col2:
        vol60_status = "success" if vol_60d < 0.25 else "warning" if vol_60d < 0.40 else "danger"
        vol60_tip = f"60-Day Volatility of {vol_60d*100:.1f}% (annualized)"
        st.markdown(render_metric_card("60-Day Volatility", f"{vol_60d*100:.1f}%", vol60_tip, vol60_status, "medium"), unsafe_allow_html=True)

    with vol_col3:
        atr_val = price_data["ATR"].iloc[-1] if "ATR" in price_data.columns else 0
        atr_pct = (atr_val / price_data["Close"].iloc[-1]) * 100 if atr_val else 0
        atr_status = "success" if atr_pct < 2 else "warning" if atr_pct < 4 else "danger"
        atr_tip = f"ATR of {atr_pct:.2f}% of price"
        st.markdown(render_metric_card("ATR (% of Price)", f"{atr_pct:.2f}%", atr_tip, atr_status, "medium"), unsafe_allow_html=True)

    st.markdown("### Drawdown Analysis")
    dd_col1, dd_col2 = st.columns(2)

    with dd_col1:
        max_dd_status = "success" if max_dd > -0.15 else "warning" if max_dd > -0.30 else "danger"
        max_dd_tip = f"Max Drawdown of {max_dd*100:.1f}% over past year"
        st.markdown(render_metric_card("Max Drawdown (1Y)", f"{max_dd*100:.1f}%", max_dd_tip, max_dd_status, "medium"), unsafe_allow_html=True)

    with dd_col2:
        curr_dd_status = "success" if current_dd > -0.10 else "warning" if current_dd > -0.20 else "danger"
        curr_dd_tip = f"Current Drawdown of {current_dd*100:.1f}%"
        st.markdown(render_metric_card("Current Drawdown", f"{current_dd*100:.1f}%", curr_dd_tip, curr_dd_status, "medium"), unsafe_allow_html=True)
