# =============================================================================
# ANALYSIS TAB - Main stock analysis with recommendations
# =============================================================================

import streamlit as st
from components import render_badge_card, render_hero_card, render_accent_card, get_status_color
from models import (
    generate_recommendation_paper1,
    generate_key_drivers, generate_key_risk, generate_bull_bear_case,
    generate_action_checklist, generate_view_changers,
)


def render(selected, price_data, info, tech_score, tech_details,
           market_regime, regime_metrics, last_row,
           volume_score=0, volume_details=None,
           rsi_value=50,
           paper1_details=None, rl_prediction=None, cost_basis=None):
    """Render the Analysis tab content."""
    st.subheader("Market & Stock Analysis")

    # Disclaimer
    st.caption("This is a decision-support tool for educational purposes only. Not financial advice. Does not predict prices.")

    # Generate recommendation using Novel Hybrid strategy
    recommendation_data = generate_recommendation_paper1(
        tech_score, volume_score, rsi_value,
        market_regime, selected, info, time_horizon="long",
        price_data=price_data, rl_prediction=rl_prediction,
    )

    rec = recommendation_data["recommendation"]

    # ==========================================================================
    # 1. EXECUTIVE SUMMARY (Decision first)
    # ==========================================================================
    st.markdown('<div class="section-header"><h3>Executive Summary</h3></div>', unsafe_allow_html=True)

    # Main recommendation display — hero card + accent cards
    exec_col1, exec_col2 = st.columns([2, 1])

    with exec_col1:
        rec_status = {"BUY": "success", "HOLD": "warning", "SELL": "danger"}.get(rec, "neutral")
        rec_tips = {
            "BUY": "Favorable conditions for accumulation",
            "HOLD": "Mixed signals - wait for clearer direction",
            "SELL": "Concerning metrics suggest reducing exposure"
        }
        st.markdown(render_hero_card("Recommendation", rec, rec_tips.get(rec, ""), rec_status), unsafe_allow_html=True)

    with exec_col2:
        confidence = recommendation_data["confidence"]
        conf_status = "success" if confidence >= 70 else "warning" if confidence >= 50 else "danger"
        conf_label = "Strong" if confidence >= 70 else "Moderate" if confidence >= 50 else "Weak"
        conf_tip = f"Signal strength of {confidence}% measures how decisive the signals are. Currently: {conf_label}."
        st.markdown(render_accent_card("Signal Strength", f"{confidence}% — {conf_label}", conf_tip, conf_status, border_color="#FF6B6B"), unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ==========================================================================
    # 2. MARKET CONTEXT (Regime badge + explanation)
    # ==========================================================================
    st.markdown('<div class="section-header"><h3>Market Context</h3></div>', unsafe_allow_html=True)

    regime_emoji = {"Bull": "📈", "Bear": "📉", "Sideways": "➡️", "High-Volatility": "⚡"}.get(market_regime, "⚪")
    regime_status = {"Bull": "success", "Bear": "danger", "Sideways": "warning", "High-Volatility": "danger"}.get(market_regime, "neutral")
    regime_tooltips = {
        "Bull": "Bull Market: The market is trending upward with prices above key moving averages. Conditions favor growth stocks and momentum strategies.",
        "Bear": "Bear Market: The market is in a downtrend with prices below key moving averages. Defensive positioning and capital preservation are prioritized.",
        "Sideways": "Sideways Market: No clear directional trend. Range-bound trading with mixed signals suggests a balanced, cautious approach.",
        "High-Volatility": "High-Volatility Market: VIX above 25 indicates elevated fear and uncertainty. Risk management is critical regardless of trend direction."
    }
    regime_tip = regime_tooltips.get(market_regime, "Market regime could not be determined.")
    st.markdown(
        render_badge_card("Market Regime", market_regime, regime_emoji, regime_tip, regime_status),
        unsafe_allow_html=True
    )

    regime_explanations = {
        "Bull": "The market is in an uptrend with price above key moving averages and low volatility. Momentum strategies are favored.",
        "Bear": "The market is in a downtrend with price below key moving averages. Defensive positioning and risk management are critical.",
        "Sideways": "The market lacks clear direction. A balanced approach is recommended while waiting for clearer signals.",
        "High-Volatility": "Market uncertainty is elevated (VIX > 25). Risk controls should be prioritized regardless of trend direction.",
    }
    regime_text = regime_explanations.get(market_regime, "Unable to determine market regime.")
    st.markdown(f'<div style="font-family:Source Sans Pro,Arial,sans-serif;font-size:13px;color:#5A7D82;line-height:1.5;padding:6px 0;">{regime_text}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ==========================================================================
    # 3. KEY DRIVERS + PRIMARY RISK
    # ==========================================================================
    key_drivers = generate_key_drivers(info, tech_score, price_data, market_regime)
    key_risk = generate_key_risk(info, price_data)

    driver_col, risk_col = st.columns([2, 1])
    with driver_col:
        st.markdown("**Key Drivers:**")
        for i, driver in enumerate(key_drivers, 1):
            driver_icon = "📈" if any(w in driver.lower() for w in ["favorable", "strong", "bullish", "above"]) else "📉" if any(w in driver.lower() for w in ["weak", "below", "challenging"]) else "➡️"
            st.markdown(f"{driver_icon} {driver}")
    with risk_col:
        st.markdown("**Primary Risk:**")
        st.warning(f"⚠️ {key_risk}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ==========================================================================
    # 4. INVESTMENT THESIS (Bull vs Bear)
    # ==========================================================================
    st.markdown('<div class="section-header"><h3>Investment Thesis</h3></div>', unsafe_allow_html=True)

    bull_case, bear_case = generate_bull_bear_case(info, tech_score, price_data, market_regime)

    thesis_col1, thesis_col2 = st.columns(2)

    with thesis_col1:
        st.markdown("""<div style="background: rgba(0,151,167,0.05); border-left: 4px solid #0097A7; padding: 8px 12px; border-radius: 6px;">
            <strong style="color:#0097A7;">Bull Case</strong>
        </div>""", unsafe_allow_html=True)
        for point in bull_case:
            st.markdown(f"+ {point}")

    with thesis_col2:
        st.markdown("""<div style="background: rgba(255,107,107,0.05); border-left: 4px solid #FF6B6B; padding: 8px 12px; border-radius: 6px;">
            <strong style="color:#FF6B6B;">Bear Case</strong>
        </div>""", unsafe_allow_html=True)
        for point in bear_case:
            st.markdown(f"- {point}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ==========================================================================
    # 5. SIGNAL DETAILS (Collapsed, with RSI/Volume warnings inside)
    # ==========================================================================
    p1_details = recommendation_data.get("paper1_details") or paper1_details
    if p1_details:
        with st.expander("Signal Details", expanded=False):
            # RSI gate warning (plain-English)
            rsi_gate = recommendation_data.get("rsi_gate_applied", False)
            rsi_warning = recommendation_data.get("rsi_warning", "")
            if rsi_gate:
                if "overbought" in rsi_warning.lower():
                    st.warning("Caution: Stock momentum is overextended — consider waiting for a pullback before buying.")
                elif "oversold" in rsi_warning.lower():
                    st.warning("Caution: Stock momentum is deeply negative — selling pressure may be near exhaustion.")
                else:
                    st.warning(f"Momentum check: {rsi_warning}")
            vol_confirms = recommendation_data.get("volume_confirms", False)
            if vol_confirms:
                st.success("Trading volume confirms the current price trend — the move has conviction.")
            else:
                st.info("Trading volume does not confirm the current trend — the move may lack conviction.")

            d_col1, d_col2, d_col3 = st.columns(3)
            with d_col1:
                crossover = p1_details.get("crossover_type", "none")
                cross_labels = {
                    "golden_cross": ("Golden Cross", "short-term trend rising above long-term — bullish"),
                    "death_cross": ("Death Cross", "short-term trend falling below long-term — bearish"),
                    "none": ("None", "no crossover detected"),
                }
                cross_name, cross_hint = cross_labels.get(crossover, ("None", "no crossover detected"))
                cross_color = "#10B981" if crossover == "golden_cross" else "#EF4444" if crossover == "death_cross" else "#5A7D82"
                st.markdown(f"**Trend Crossover:** <span style='color:{cross_color}; font-weight:600;'>{cross_name}</span> <span style='font-size:12px;color:#5A7D82;'>({cross_hint})</span>", unsafe_allow_html=True)

            with d_col2:
                atv_conf = p1_details.get("atv_confirmed", False)
                atv_label = "Confirmed" if atv_conf else "Not Confirmed"
                atv_color = "#10B981" if atv_conf else "#F59E0B"
                atv_hint = "volume supports the signal" if atv_conf else "volume does not support the signal"
                st.markdown(f"**Volume Confirmation:** <span style='color:{atv_color}; font-weight:600;'>{atv_label}</span> <span style='font-size:12px;color:#5A7D82;'>({atv_hint})</span>", unsafe_allow_html=True)

            with d_col3:
                rsi_g = p1_details.get("rsi_gate", "n/a")
                rsi_labels = {
                    "passed": ("Passed", "#10B981"),
                    "blocked_overbought": ("Blocked (Overbought)", "#EF4444"),
                    "blocked_oversold": ("Blocked (Oversold)", "#EF4444"),
                    "n/a": ("N/A", "#5A7D82"),
                }
                rsi_label, rsi_color = rsi_labels.get(rsi_g, ("N/A", "#5A7D82"))
                st.markdown(f"**RSI Gate:** <span style='color:{rsi_color}; font-weight:600;'>{rsi_label}</span>", unsafe_allow_html=True)

            # AI model status
            rl_signal = p1_details.get("rl_signal")
            if rl_signal:
                rl_agrees = p1_details.get("rl_agrees", False)
                rl_override = p1_details.get("rl_override", False)
                rl_status_color = "#10B981" if rl_agrees else "#F59E0B"
                rl_status = "Agrees" if rl_agrees else ("Override" if rl_override else "Disagrees")
                st.markdown(f"**AI Model:** Signal: {rl_signal} — <span style='color:{rl_status_color}; font-weight:600;'>{rl_status}</span>", unsafe_allow_html=True)
            else:
                try:
                    import rl_agent
                    if rl_agent.is_available():
                        st.caption("AI Model: Available (train via sidebar)")
                    else:
                        st.caption("AI model not available. Recommendations use rule-based signals only.")
                except ImportError:
                    st.caption("AI model not available. Recommendations use rule-based signals only.")

    # ==========================================================================
    # 6. SCORE DETAILS (Collapsible)
    # ==========================================================================
    with st.expander("Score Breakdown", expanded=False):
        weights = recommendation_data["weights"]

        score_cols = st.columns(2)

        # Technical score
        with score_cols[0]:
            st.markdown("**Technical Score**")
            tech_status = "success" if tech_score >= 60 else "warning" if tech_score >= 40 else "danger"
            tech_color = get_status_color(tech_status)
            st.markdown(f"<span style='font-family: Source Sans Pro, Arial, sans-serif; font-size:28px; color:{tech_color};'>{tech_score}/100</span>", unsafe_allow_html=True)
            st.caption(f"Weight: {weights['technical']*100:.0f}%")
            st.progress(tech_score / 100)
            def _sub_assess(val, max_val):
                if val == 'N/A': return "N/A"
                ratio = float(val) / max_val
                return "Strong" if ratio >= 0.65 else "Weak" if ratio < 0.4 else "Moderate"
            trend_v = tech_details.get('trend', 'N/A')
            rsi_v = tech_details.get('rsi', 'N/A')
            macd_v = tech_details.get('macd', 'N/A')
            st.write(f"- Trend: {trend_v}/40 ({_sub_assess(trend_v, 40)})")
            st.write(f"- RSI: {rsi_v}/30 ({_sub_assess(rsi_v, 30)})")
            st.write(f"- MACD: {macd_v}/30 ({_sub_assess(macd_v, 30)})")

        # Volume score
        with score_cols[1]:
            st.markdown("**Volume Score**")
            vol_status = "success" if volume_score >= 60 else "warning" if volume_score >= 40 else "danger"
            vol_color = get_status_color(vol_status)
            st.markdown(f"<span style='font-family: Source Sans Pro, Arial, sans-serif; font-size:28px; color:{vol_color};'>{volume_score}/100</span>", unsafe_allow_html=True)
            st.caption(f"Weight: {weights.get('volume', 0)*100:.0f}%")
            st.progress(volume_score / 100)
            if volume_details and "details" in volume_details:
                d = volume_details["details"]
                align_s = d.get('alignment_score', 0)
                rel_s = d.get('rel_volume_score', 0)
                align_assess = "Strong" if align_s >= 32 else "Weak" if align_s < 20 else "Moderate"
                rel_assess = "Strong" if rel_s >= 32 else "Weak" if rel_s < 20 else "Moderate"
                st.write(f"- Alignment: {align_s:.0f}/50 ({align_assess})")
                st.write(f"- Rel Volume: {rel_s:.0f}/50 ({rel_assess})")
                confirms = volume_details.get("volume_confirms_trend", False)
                st.write(f"- Confirms Trend: {'Yes' if confirms else 'No'}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ==========================================================================
    # 7. ACTION & NEXT STEPS
    # ==========================================================================
    st.markdown('<div class="section-header"><h3>Action & Next Steps</h3></div>', unsafe_allow_html=True)

    action_col1, action_col2 = st.columns(2)

    with action_col1:
        st.markdown("**Action Checklist:**")
        action_items = generate_action_checklist(rec, info, price_data)
        for item in action_items:
            st.markdown(f"* {item}")

    with action_col2:
        st.markdown("**What Would Change This View?**")
        view_changers = generate_view_changers(rec, info, price_data)
        for changer in view_changers:
            st.markdown(f"* {changer}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ==========================================================================
    # 8. POSITION P&L (moved to bottom — personal info, doesn't interrupt analysis)
    # ==========================================================================
    if cost_basis is not None:
        current_price = last_row["Close"]
        pnl_pct = (current_price - cost_basis) / cost_basis * 100
        pnl_dollar = current_price - cost_basis
        pnl_status = "success" if pnl_pct >= 0 else "danger"
        pnl_label = "Profit" if pnl_pct >= 0 else "Loss"
        st.markdown(f"""
        <div style="background:{'rgba(16,185,129,0.08)' if pnl_pct >= 0 else 'rgba(239,68,68,0.08)'}; border-left:4px solid {'#10B981' if pnl_pct >= 0 else '#EF4444'}; padding:12px 16px; border-radius:6px; margin:8px 0;">
            <span style="font-weight:600;">My Position:</span> Bought at <b>${cost_basis:.2f}</b> → Now <b>${current_price:.2f}</b> —
            <span style="color:{'#10B981' if pnl_pct >= 0 else '#EF4444'}; font-weight:700;">{pnl_label}: {pnl_pct:+.1f}% (${pnl_dollar:+.2f}/share)</span>
        </div>
        """, unsafe_allow_html=True)
