# =============================================================================
# ANALYSIS TAB - Main stock analysis with recommendations
# =============================================================================

import streamlit as st
from components import render_metric_card, render_badge_card, render_compact_card, render_hero_card, render_accent_card, get_status_color
from models import (
    generate_recommendation_paper1,
    generate_recommendation_paper2,
    generate_key_drivers, generate_key_risk, generate_bull_bear_case,
    generate_action_checklist, generate_view_changers,
)


def render(selected, price_data, info, tech_score, tech_details,
           market_regime, regime_metrics, last_row,
           selected_strategy="Volume+RSI", volume_score=0, volume_details=None,
           rsi_value=50, risk_profile="moderate", fund_score_p2=50, fund_details_p2=None,
           paper1_details=None, rl_prediction=None, cost_basis=None):
    """Render the Analysis tab content."""
    st.subheader("Market & Stock Analysis")

    # Disclaimer
    st.caption("This is a decision-support tool for educational purposes only. Not financial advice. Does not predict prices.")

    # --- TIME HORIZON TOGGLE ---
    horizon_col1, horizon_col2 = st.columns([3, 1])
    with horizon_col2:
        time_horizon = "short" if st.toggle("Short-term focus", value=False, help="Toggle for short-term (1-3 months) vs long-term (6-12 months) analysis. Short-term emphasizes technicals, long-term emphasizes fundamentals.") else "long"

    # Generate recommendation based on selected strategy
    if selected_strategy == "Volume+RSI":
        recommendation_data = generate_recommendation_paper1(
            tech_score, fund_score_p2, volume_score, rsi_value,
            market_regime, selected, info, time_horizon,
            price_data=price_data, rl_prediction=rl_prediction,
        )
    else:  # Optimized Weights (Paper 2)
        recommendation_data = generate_recommendation_paper2(
            tech_score, fund_score_p2, market_regime, selected, info,
            risk_profile, time_horizon
        )

    rec = recommendation_data["recommendation"]

    # ==========================================================================
    # STRATEGY INDICATOR
    # ==========================================================================
    strategy_labels = {
        "Volume+RSI": "Paper 1: EMA + ATV + RSI + RL",
        "Optimized Weights": "Paper 2: 5-Factor Scoring",
    }
    st.caption(f"Active Strategy: **{strategy_labels.get(selected_strategy, selected_strategy)}**")

    # ==========================================================================
    # 1. EXECUTIVE SUMMARY (Decision first)
    # ==========================================================================
    st.markdown('<div class="section-header"><h3>Executive Summary</h3></div>', unsafe_allow_html=True)

    # Main recommendation display — hero card + accent cards
    exec_col1, exec_col2, exec_col3 = st.columns([2, 1, 1])

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
        conf_tip = f"Confidence of {confidence}% measures signal decisiveness."
        st.markdown(render_accent_card("Confidence", f"{confidence}%", conf_tip, conf_status, border_color="#FF6B6B"), unsafe_allow_html=True)

    with exec_col3:
        composite = recommendation_data["composite_score"]
        comp_status = "success" if composite >= 65 else "warning" if composite >= 45 else "danger"
        st.markdown(render_accent_card("Score", f"{composite:.0f}/100", "Weighted composite score.", comp_status, border_color="#0097A7"), unsafe_allow_html=True)

    # Position P&L (if user owns the stock)
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

    # RSI gate warning (for Paper 1 strategy)
    if selected_strategy == "Volume+RSI":
        rsi_gate = recommendation_data.get("rsi_gate_applied", False)
        rsi_warning = recommendation_data.get("rsi_warning", "")
        if rsi_gate:
            st.warning(f"RSI Gate: {rsi_warning}")
        vol_confirms = recommendation_data.get("volume_confirms", False)
        if vol_confirms:
            st.success("Volume confirms current price trend")
        else:
            st.info("Volume does not confirm current price trend")

    # Paper 1 signal details
    p1_details = recommendation_data.get("paper1_details") or paper1_details
    if p1_details and selected_strategy == "Volume+RSI":
        with st.expander("Paper 1 Signal Details", expanded=True):
            d_col1, d_col2, d_col3 = st.columns(3)
            with d_col1:
                crossover = p1_details.get("crossover_type", "none")
                cross_label = crossover.replace("_", " ").title()
                cross_color = "#10B981" if crossover == "golden_cross" else "#EF4444" if crossover == "death_cross" else "#5A7D82"
                st.markdown(f"**EMA Crossover:** <span style='color:{cross_color}; font-weight:600;'>{cross_label}</span>", unsafe_allow_html=True)

            with d_col2:
                atv_conf = p1_details.get("atv_confirmed", False)
                atv_label = "Confirmed" if atv_conf else "Not Confirmed"
                atv_color = "#10B981" if atv_conf else "#F59E0B"
                st.markdown(f"**ATV Confirmation:** <span style='color:{atv_color}; font-weight:600;'>{atv_label}</span>", unsafe_allow_html=True)

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

            # RL agent status
            rl_signal = p1_details.get("rl_signal")
            if rl_signal:
                rl_agrees = p1_details.get("rl_agrees", False)
                rl_override = p1_details.get("rl_override", False)
                rl_status_color = "#10B981" if rl_agrees else "#F59E0B"
                rl_status = "Agrees" if rl_agrees else ("Override" if rl_override else "Disagrees")
                st.markdown(f"**RL Agent (PPO):** Signal: {rl_signal} — <span style='color:{rl_status_color}; font-weight:600;'>{rl_status}</span>", unsafe_allow_html=True)
            elif selected_strategy == "Volume+RSI":
                try:
                    import rl_agent
                    if rl_agent.is_available():
                        st.caption("RL Agent: Available (train via sidebar)")
                    else:
                        st.warning("RL Agent: Unavailable — install `stable-baselines3` and `gymnasium`. Recommendations are based on rule-based signals only.")
                except ImportError:
                    st.warning("RL Agent: Unavailable — install `stable-baselines3` and `gymnasium`. Recommendations are based on rule-based signals only.")

    # Key Drivers inline
    key_drivers = generate_key_drivers(info, tech_score, fund_score_p2, price_data, market_regime)
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
    # 2. MARKET CONTEXT
    # ==========================================================================
    st.markdown('<div class="section-header"><h3>Market Context</h3></div>', unsafe_allow_html=True)

    regime_col1, regime_col2 = st.columns([1, 2])

    with regime_col1:
        # Large regime indicator
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

    with regime_col2:
        if regime_metrics:
            metric_col1, metric_col2, metric_col3 = st.columns(3)

            # S&P 500 metrics
            sp500_val = regime_metrics.get('sp500_price', 0)
            vs_ma_val = regime_metrics.get('price_vs_sma200', 0)
            vs_ma_status = "success" if vs_ma_val > 0 else "danger"
            sp500_tip = f"S&P 500 Index at {sp500_val:,.0f}. This benchmark tracks 500 large US companies and is the primary indicator of overall US market health."
            vs_ma_tip = f"The S&P 500 is currently {abs(vs_ma_val):.1f}% {'above' if vs_ma_val > 0 else 'below'} its 200-day moving average. " + ("Trading above the 200-day MA indicates a bullish long-term trend." if vs_ma_val > 0 else "Trading below the 200-day MA indicates a bearish long-term trend.")
            with metric_col1:
                st.markdown(render_compact_card("S&P 500", f"{sp500_val:,.0f}", sp500_tip, "info"), unsafe_allow_html=True)
                st.markdown(render_compact_card("vs 200-day MA", f"{vs_ma_val:+.1f}%", vs_ma_tip, vs_ma_status), unsafe_allow_html=True)

            # MA metrics
            slope_val = regime_metrics.get('sma200_slope', 0)
            cross_val = regime_metrics.get('sma_crossover', 0)
            slope_status = "success" if slope_val > 0 else "danger"
            cross_status = "success" if cross_val > 0 else "danger"
            slope_tip = f"200-day MA Slope of {slope_val:+.2f}% measures the 20-day rate of change in the long-term trend. " + ("A positive slope confirms upward momentum." if slope_val > 0 else "A negative slope indicates deteriorating trend.")
            cross_tip = f"50/200 Cross at {cross_val:+.1f}% shows the gap between short and long-term moving averages. " + ("Positive value (Golden Cross pattern) is bullish." if cross_val > 0 else "Negative value (Death Cross pattern) is bearish.")
            with metric_col2:
                st.markdown(render_compact_card("200-MA Slope", f"{slope_val:+.2f}%", slope_tip, slope_status), unsafe_allow_html=True)
                st.markdown(render_compact_card("50/200 Cross", f"{cross_val:+.1f}%", cross_tip, cross_status), unsafe_allow_html=True)

            # VIX metrics
            vix_val = regime_metrics.get('vix', 0)
            vix_ma = regime_metrics.get('vix_ma20', 0)
            vix_status = "success" if vix_val < 20 else "warning" if vix_val < 25 else "danger"
            vix_level = "low (complacency)" if vix_val < 15 else "normal" if vix_val < 20 else "elevated" if vix_val < 25 else "high (fear)"
            vix_tip = f"VIX (Fear Index) at {vix_val:.1f} is {vix_level}. VIX measures expected 30-day volatility. Below 20 is calm, above 25 indicates significant fear in the market."
            vix_vs_ma = vix_val - vix_ma
            vix_ma_tip = f"VIX 20-day MA at {vix_ma:.1f}. Current VIX is {abs(vix_vs_ma):.1f} points {'above' if vix_vs_ma > 0 else 'below'} its average, indicating {'rising' if vix_vs_ma > 0 else 'falling'} fear levels."
            with metric_col3:
                st.markdown(render_compact_card("VIX", f"{vix_val:.1f}", vix_tip, vix_status), unsafe_allow_html=True)
                st.markdown(render_compact_card("VIX 20-MA", f"{vix_ma:.1f}", vix_ma_tip, "neutral"), unsafe_allow_html=True)

    # Regime explanation
    regime_explanations = {
        "Bull": "The market is in an uptrend with price above key moving averages and low volatility. Momentum strategies are favored.",
        "Bear": "The market is in a downtrend with price below key moving averages. Defensive positioning and risk management are critical.",
        "Sideways": "The market lacks clear direction. A balanced approach is recommended while waiting for clearer signals.",
        "High-Volatility": "Market uncertainty is elevated (VIX > 25). Risk controls should be prioritized regardless of trend direction.",
    }
    st.info(regime_explanations.get(market_regime, "Unable to determine market regime."))

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ==========================================================================
    # 3. STOCK SNAPSHOT (Benchmarking)
    # ==========================================================================
    st.markdown('<div class="section-header"><h3>Stock Snapshot</h3></div>', unsafe_allow_html=True)

    # Calculate stock returns
    if len(price_data) > 22:
        stock_1m_return = (price_data["Close"].iloc[-1] / price_data["Close"].iloc[-22] - 1) * 100
    else:
        stock_1m_return = 0
    if len(price_data) > 66:
        stock_3m_return = (price_data["Close"].iloc[-1] / price_data["Close"].iloc[-66] - 1) * 100
    else:
        stock_3m_return = 0

    # Get S&P 500 returns from regime_metrics
    sp500_1m = regime_metrics.get('sp500_1m_return', 0) if regime_metrics else 0
    sp500_3m = regime_metrics.get('sp500_3m_return', 0) if regime_metrics else 0

    snap_col1, snap_col2, snap_col3, snap_col4 = st.columns(4)

    with snap_col1:
        st.markdown("**Current Price**")
        st.markdown(f"<span style='font-size:24px; color:#1A3C40;'>${last_row['Close']:.2f}</span>", unsafe_allow_html=True)

    with snap_col2:
        st.markdown("**1-Month Return**")
        stock_status_1m = "success" if stock_1m_return > 0 else "danger"
        st.markdown(f"<span style='color:{get_status_color(stock_status_1m)};'>{selected}: {stock_1m_return:+.1f}%</span>", unsafe_allow_html=True)
        stock_vs_sp_1m = stock_1m_return - sp500_1m
        st.caption(f"vs S&P 500: {stock_vs_sp_1m:+.1f}%")

    with snap_col3:
        st.markdown("**3-Month Return**")
        stock_status_3m = "success" if stock_3m_return > 0 else "danger"
        st.markdown(f"<span style='color:{get_status_color(stock_status_3m)};'>{selected}: {stock_3m_return:+.1f}%</span>", unsafe_allow_html=True)
        stock_vs_sp_3m = stock_3m_return - sp500_3m
        st.caption(f"vs S&P 500: {stock_vs_sp_3m:+.1f}%")

    with snap_col4:
        st.markdown("**Relative Performance**")
        if stock_vs_sp_1m > 5 and stock_vs_sp_3m > 5:
            st.success("Outperforming")
        elif stock_vs_sp_1m < -5 and stock_vs_sp_3m < -5:
            st.error("Underperforming")
        else:
            st.info("In-line")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ==========================================================================
    # 4. THESIS (Bull vs Bear)
    # ==========================================================================
    st.markdown('<div class="section-header"><h3>Investment Thesis</h3></div>', unsafe_allow_html=True)

    bull_case, bear_case = generate_bull_bear_case(info, tech_score, fund_score_p2, price_data, market_regime)

    thesis_col1, thesis_col2 = st.columns(2)

    with thesis_col1:
        st.markdown("""<div style="background: rgba(0,151,167,0.05); border-left: 4px solid #0097A7; padding: 16px; border-radius: 6px;">
            <strong style="color:#0097A7;">Bull Case</strong>
        </div>""", unsafe_allow_html=True)
        for point in bull_case:
            st.markdown(f"+ {point}")

    with thesis_col2:
        st.markdown("""<div style="background: rgba(255,107,107,0.05); border-left: 4px solid #FF6B6B; padding: 16px; border-radius: 6px;">
            <strong style="color:#FF6B6B;">Bear Case</strong>
        </div>""", unsafe_allow_html=True)
        for point in bear_case:
            st.markdown(f"- {point}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ==========================================================================
    # 5. SCORE DETAILS (Collapsible)
    # ==========================================================================
    with st.expander("Score Breakdown", expanded=False):
        weights = recommendation_data["weights"]
        has_volume = "volume" in weights
        has_fundamental = "fundamental" in weights

        # Determine columns based on strategy
        if has_volume and has_fundamental:
            score_cols = st.columns(3)
        elif has_volume or has_fundamental:
            score_cols = st.columns(2)
        else:
            score_cols = [st.columns(1)[0]]

        col_idx = 0

        # Technical score (always shown)
        with score_cols[col_idx]:
            st.markdown("**Technical Score**")
            tech_status = "success" if tech_score >= 60 else "warning" if tech_score >= 40 else "danger"
            tech_color = get_status_color(tech_status)
            st.markdown(f"<span style='font-family: Source Sans Pro, Arial, sans-serif; font-size:28px; color:{tech_color};'>{tech_score}/100</span>", unsafe_allow_html=True)
            st.caption(f"Weight: {weights['technical']*100:.0f}%")
            st.progress(tech_score / 100)
            st.write(f"- Trend: {tech_details.get('trend', 'N/A')}/40")
            st.write(f"- RSI: {tech_details.get('rsi', 'N/A')}/30")
            st.write(f"- MACD: {tech_details.get('macd', 'N/A')}/30")
        col_idx += 1

        # Fundamental score (shown for Paper 2)
        if has_fundamental:
            with score_cols[col_idx]:
                display_fund = fund_score_p2
                st.markdown("**Factor Score (Paper 2)**")
                fund_status = "success" if display_fund >= 60 else "warning" if display_fund >= 40 else "danger"
                fund_color = get_status_color(fund_status)
                st.markdown(f"<span style='font-family: Source Sans Pro, Arial, sans-serif; font-size:28px; color:{fund_color};'>{display_fund:.0f}/100</span>", unsafe_allow_html=True)
                st.caption(f"Weight: {weights['fundamental']*100:.0f}% | Profile: {risk_profile.title()}")
                st.progress(min(1.0, display_fund / 100))
                if fund_details_p2:
                    st.write(f"- P/B Ratio: {fund_details_p2.get('pb_pctile', fund_details_p2.get('valuation_pctile', 'N/A')):.0f}/100")
                    st.write(f"- ROE: {fund_details_p2.get('roe_pctile', fund_details_p2.get('profitability_pctile', 'N/A')):.0f}/100")
                    st.write(f"- Momentum: {fund_details_p2.get('momentum_pctile', fund_details_p2.get('growth_pctile', 'N/A')):.0f}/100")
                    st.write(f"- Beta: {fund_details_p2.get('beta_pctile', fund_details_p2.get('leverage_pctile', 'N/A')):.0f}/100")
                    st.write(f"- Market Cap: {fund_details_p2.get('market_cap_pctile', 50):.0f}/100")
                    bonus = fund_details_p2.get('interaction_bonus', 0)
                    if bonus > 0:
                        st.write(f"- Interaction Bonus: +{bonus} pts")
                    if fund_details_p2.get('pb_unavailable'):
                        st.caption("P/B unavailable — using 4-factor model")
            col_idx += 1

        # Volume score (shown for Volume+RSI)
        if has_volume:
            with score_cols[col_idx]:
                st.markdown("**Volume Score**")
                vol_status = "success" if volume_score >= 60 else "warning" if volume_score >= 40 else "danger"
                vol_color = get_status_color(vol_status)
                st.markdown(f"<span style='font-family: Source Sans Pro, Arial, sans-serif; font-size:28px; color:{vol_color};'>{volume_score}/100</span>", unsafe_allow_html=True)
                st.caption(f"Weight: {weights.get('volume', 0)*100:.0f}%")
                st.progress(volume_score / 100)
                if volume_details and "details" in volume_details:
                    d = volume_details["details"]
                    st.write(f"- Alignment: {d.get('alignment_score', 'N/A'):.0f}/50")
                    st.write(f"- Rel Volume: {d.get('rel_volume_score', 'N/A'):.0f}/50")
                    confirms = volume_details.get("volume_confirms_trend", False)
                    st.write(f"- Confirms Trend: {'Yes' if confirms else 'No'}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ==========================================================================
    # 6. ACTION & NEXT STEPS
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

    # Analysis Summary in expander
    with st.expander("Full Analysis Summary"):
        st.markdown(recommendation_data["explanation"])

        weight_lines = "\n".join(
            f"        - {k.title()}: {v*100:.0f}%"
            for k, v in recommendation_data['weights'].items()
        )
        st.markdown(f"""
        **Weight Adjustments for {market_regime} Market:**
{weight_lines}
        """)
