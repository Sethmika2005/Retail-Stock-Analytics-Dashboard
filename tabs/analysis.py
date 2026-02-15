# =============================================================================
# ANALYSIS TAB - Main stock analysis with recommendations
# =============================================================================

import streamlit as st
from components import render_metric_card, render_badge_card, render_compact_card, get_status_color
from models import generate_recommendation, generate_key_drivers, generate_key_risk, generate_bull_bear_case, generate_action_checklist, generate_view_changers


def render(selected, price_data, info, tech_score, tech_details, fund_score, fund_details,
           market_regime, regime_metrics, last_row):
    """Render the Analysis tab content."""
    st.subheader("Market & Stock Analysis")

    # Disclaimer
    st.caption("This is a decision-support tool for educational purposes only. Not financial advice. Does not predict prices.")

    # --- TIME HORIZON TOGGLE ---
    horizon_col1, horizon_col2 = st.columns([3, 1])
    with horizon_col2:
        time_horizon = "short" if st.toggle("Short-term focus", value=False, help="Toggle for short-term (1-3 months) vs long-term (6-12 months) analysis. Short-term emphasizes technicals, long-term emphasizes fundamentals.") else "long"

    # Generate recommendation based on time horizon
    recommendation_data = generate_recommendation(
        tech_score, fund_score, market_regime, selected, info, time_horizon
    )
    rec = recommendation_data["recommendation"]

    # ==========================================================================
    # 1. EXECUTIVE SUMMARY (Decision first)
    # ==========================================================================
    st.markdown("### Executive Summary")

    # Main recommendation display
    exec_col1, exec_col2, exec_col3 = st.columns([1, 1, 1])

    with exec_col1:
        rec_status = {"BUY": "success", "HOLD": "warning", "SELL": "danger"}.get(rec, "neutral")
        rec_tips = {
            "BUY": "BUY: Favorable conditions for accumulation. Technical and fundamental metrics support building a position.",
            "HOLD": "HOLD: Mixed signals - maintain positions but wait for clearer direction.",
            "SELL": "SELL: Concerning metrics suggest reducing exposure or avoiding new positions."
        }
        st.markdown(render_metric_card("Recommendation", rec, rec_tips.get(rec, ""), rec_status, "large"), unsafe_allow_html=True)

    with exec_col2:
        confidence = recommendation_data["confidence"]
        conf_status = "success" if confidence >= 70 else "warning" if confidence >= 50 else "danger"
        conf_tip = f"Confidence of {confidence}% measures signal decisiveness."
        st.markdown(render_metric_card("Confidence", f"{confidence}%", conf_tip, conf_status, "large"), unsafe_allow_html=True)

    with exec_col3:
        composite = recommendation_data["composite_score"]
        comp_status = "success" if composite >= 65 else "warning" if composite >= 45 else "danger"
        st.markdown(render_metric_card("Score", f"{composite:.0f}/100", "Weighted composite of Technical and Fundamental scores.", comp_status, "large"), unsafe_allow_html=True)

    # Key Drivers inline
    key_drivers = generate_key_drivers(info, tech_score, fund_score, price_data, market_regime)
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

    st.divider()

    # ==========================================================================
    # 2. MARKET CONTEXT
    # ==========================================================================
    st.markdown("### Market Context")

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

    st.divider()

    # ==========================================================================
    # 3. STOCK SNAPSHOT (Benchmarking)
    # ==========================================================================
    st.markdown("### Stock Snapshot")

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
        st.markdown(f"<span style='font-size:24px; color:#4A4A4A;'>${last_row['Close']:.2f}</span>", unsafe_allow_html=True)

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

    st.divider()

    # ==========================================================================
    # 4. THESIS (Bull vs Bear)
    # ==========================================================================
    st.markdown("### Investment Thesis")

    bull_case, bear_case = generate_bull_bear_case(info, tech_score, fund_score, price_data, market_regime)

    thesis_col1, thesis_col2 = st.columns(2)

    with thesis_col1:
        st.markdown("**Bull Case**")
        for point in bull_case:
            st.markdown(f"+ {point}")

    with thesis_col2:
        st.markdown("**Bear Case**")
        for point in bear_case:
            st.markdown(f"- {point}")

    st.divider()

    # ==========================================================================
    # 5. SCORE DETAILS (Collapsible)
    # ==========================================================================
    with st.expander("Score Breakdown", expanded=False):
        score_col1, score_col2 = st.columns(2)
        weights = recommendation_data["weights"]

        with score_col1:
            st.markdown("**Technical Score**")
            tech_status = "success" if tech_score >= 60 else "warning" if tech_score >= 40 else "danger"
            tech_color = get_status_color(tech_status)
            st.markdown(f"<span style='font-family: Source Sans Pro, Arial, sans-serif; font-size:28px; color:{tech_color};'>{tech_score}/100</span>", unsafe_allow_html=True)
            st.caption(f"Weight: {weights['technical']*100:.0f}%")
            st.progress(tech_score / 100)
            st.write(f"- Trend: {tech_details.get('trend', 'N/A')}/40")
            st.write(f"- RSI: {tech_details.get('rsi', 'N/A')}/30")
            st.write(f"- MACD: {tech_details.get('macd', 'N/A')}/30")

        with score_col2:
            st.markdown("**Fundamental Score**")
            fund_status = "success" if fund_score >= 60 else "warning" if fund_score >= 40 else "danger"
            fund_color = get_status_color(fund_status)
            st.markdown(f"<span style='font-family: Source Sans Pro, Arial, sans-serif; font-size:28px; color:{fund_color};'>{fund_score}/100</span>", unsafe_allow_html=True)
            st.caption(f"Weight: {weights['fundamental']*100:.0f}%")
            st.progress(fund_score / 100)
            st.write(f"- Profitability: {fund_details.get('profitability', 'N/A')}/25")
            st.write(f"- Growth: {fund_details.get('growth', 'N/A')}/25")
            st.write(f"- Leverage: {fund_details.get('leverage', 'N/A')}/25")
            st.write(f"- Valuation: {fund_details.get('valuation', 'N/A')}/25")

    st.divider()

    # ==========================================================================
    # 6. ACTION & NEXT STEPS
    # ==========================================================================
    st.markdown("### Action & Next Steps")

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

        st.markdown(f"""
        **Weight Adjustments for {market_regime} Market:**
        - Technical: {recommendation_data['weights']['technical']*100:.0f}%
        - Fundamental: {recommendation_data['weights']['fundamental']*100:.0f}%
        """)
