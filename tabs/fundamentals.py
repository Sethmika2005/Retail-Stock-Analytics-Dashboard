# =============================================================================
# FUNDAMENTALS TAB - Simplified with 4 key charts
# =============================================================================

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from components import format_large_number

# Chart styling constants
CHART_FONT_COLOR = "#1A3C40"
CHART_AXIS_COLOR = "#37616A"
LEGEND_FONT_COLOR = "#1A3C40"


def render(selected, info, financials, all_stocks_df, filtered_df,
           price_data, load_sector_peers_metrics,
           selected_strategy="Volume+RSI", fund_score_p2=50, fund_details_p2=None, risk_profile="moderate"):
    """Render the Fundamentals tab content."""
    st.subheader("Fundamentals")

    # =========================================================================
    # FUNDAMENTAL SCORE BREAKDOWN
    # =========================================================================
    # Show percentile-based score when Paper 2 or Combined strategy is active
    if fund_details_p2:
        display_score = fund_score_p2
        f_status = "success" if display_score >= 65 else "warning" if display_score >= 40 else "danger"
        f_color = {"success": "#10B981", "warning": "#FF6B6B", "danger": "#FF6B6B"}.get(f_status, "#5A7D82")

        score_col1, score_col2 = st.columns([1, 3])

        with score_col1:
            st.markdown(f"""
            <div style="background: white; border: 1px solid #D0E8EA; border-radius: 8px; padding: 16px; text-align: center;">
                <div style="font-size: 12px; color: #5A7D82; margin-bottom: 4px;">Fundamental Score (Percentile)</div>
                <div style="font-size: 36px; font-weight: 700; color: {f_color};">{display_score:.0f}</div>
                <div style="font-size: 12px; color: #5A7D82;">/100 | {risk_profile.title()}</div>
            </div>
            """, unsafe_allow_html=True)

        with score_col2:
            st.markdown("**5-Factor Score Breakdown** (vs sector peers)")

            # Factor 1: P/B Ratio
            pb_pctile = fund_details_p2.get("pb_pctile", 50)
            pb_val = info.get("priceToBook")
            pb_detail = f"P/B: {pb_val:.2f}" if pb_val else ""
            if fund_details_p2.get("pb_unavailable"):
                st.markdown(f"P/B Ratio: **N/A** (unavailable — using 4-factor model)")
            else:
                st.markdown(f"P/B Ratio: **{pb_pctile:.0f}/100** percentile {(' - ' + pb_detail) if pb_detail else ''}")
                st.progress(min(1.0, pb_pctile / 100))

            # Factor 2: ROE
            roe_pctile = fund_details_p2.get("roe_pctile", fund_details_p2.get("profitability_pctile", 50))
            roe_val = info.get("returnOnEquity")
            roe_detail = f"ROE: {roe_val*100:.1f}%" if roe_val else ""
            st.markdown(f"ROE: **{roe_pctile:.0f}/100** percentile {(' - ' + roe_detail) if roe_detail else ''}")
            st.progress(min(1.0, roe_pctile / 100))

            # Factor 3: Momentum
            momentum_pctile = fund_details_p2.get("momentum_pctile", fund_details_p2.get("growth_pctile", 50))
            monthly_ret = None
            if price_data is not None and "Monthly_Return" in price_data.columns:
                mr = price_data["Monthly_Return"].iloc[-1]
                if pd.notna(mr):
                    monthly_ret = mr
            mom_detail = f"Monthly Return: {monthly_ret*100:.1f}%" if monthly_ret is not None else ""
            if not mom_detail:
                rev_growth = info.get("revenueGrowth")
                mom_detail = f"Rev Growth: {rev_growth*100:.1f}%" if rev_growth else ""
            st.markdown(f"Momentum: **{momentum_pctile:.0f}/100** percentile {(' - ' + mom_detail) if mom_detail else ''}")
            st.progress(min(1.0, momentum_pctile / 100))

            # Factor 4: Beta
            beta_pctile = fund_details_p2.get("beta_pctile", fund_details_p2.get("leverage_pctile", 50))
            beta_val = info.get("beta")
            beta_detail = f"Beta: {beta_val:.2f}" if beta_val else ""
            st.markdown(f"Beta: **{beta_pctile:.0f}/100** percentile {(' - ' + beta_detail) if beta_detail else ''}")
            st.progress(min(1.0, beta_pctile / 100))

            # Factor 5: Market Cap
            mcap_pctile = fund_details_p2.get("market_cap_pctile", 50)
            mcap_val = info.get("marketCap")
            mcap_detail = ""
            if mcap_val:
                if mcap_val >= 1e12:
                    mcap_detail = f"MCap: ${mcap_val/1e12:.2f}T"
                elif mcap_val >= 1e9:
                    mcap_detail = f"MCap: ${mcap_val/1e9:.1f}B"
                else:
                    mcap_detail = f"MCap: ${mcap_val/1e6:.0f}M"
            st.markdown(f"Market Cap: **{mcap_pctile:.0f}/100** percentile {(' - ' + mcap_detail) if mcap_detail else ''}")
            st.progress(min(1.0, mcap_pctile / 100))

            bonus = fund_details_p2.get("interaction_bonus", 0)
            if bonus > 0:
                st.markdown(f"**Interaction Bonus: +{bonus} pts**")
                interaction_details = fund_details_p2.get("interaction_details", {})
                if interaction_details:
                    top_interactions = sorted(interaction_details.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
                    for name, val in top_interactions:
                        st.caption(f"{name}: {val:+.3f}")

            n_factors = fund_details_p2.get("n_factors", 5)
            if fund_details_p2.get("used_percentile"):
                st.caption(f"Scores based on {n_factors}-factor percentile ranking vs sector peers")
            else:
                st.caption(f"Scores based on {n_factors}-factor absolute thresholds (insufficient peer data)")

    st.markdown("---")

    # =========================================================================
    # PEER COMPARISON TOGGLE
    # =========================================================================
    show_peer_comparison = st.toggle(
        "Compare with Industry Peers",
        value=False,
        help="Show industry averages on charts and comparison table"
    )

    # Load peer data
    fund_stock_sector = all_stocks_df[all_stocks_df["ticker"] == selected]["sector"].values
    if len(fund_stock_sector) > 0:
        current_sector = fund_stock_sector[0]
        fund_sector_peers = all_stocks_df[all_stocks_df["sector"] == current_sector]["ticker"].tolist()
        fund_sector_peers = [t for t in fund_sector_peers if t != selected][:15]
    else:
        current_sector = "Unknown"
        fund_sector_peers = filtered_df["ticker"].tolist()[:15]

    peers_data = load_sector_peers_metrics(tuple(fund_sector_peers + [selected]))
    peer_means = peers_data[peers_data["ticker"] != selected].drop(columns=["ticker"]).mean()

    if show_peer_comparison:
        st.caption(f"Comparing {selected} with {len(fund_sector_peers)} peers in **{current_sector}** sector")

    # Get financial data
    income_stmt = financials.get("income_stmt")
    balance_sheet = financials.get("balance_sheet")
    quarterly_income = financials.get("quarterly_income")
    quarterly_balance = financials.get("quarterly_balance")

    st.markdown("---")

    # =========================================================================
    # 1. PROFITABILITY CHART (Net Income columns + ROE line)
    # =========================================================================
    st.markdown("### Profitability")

    prof_toggle_col1, prof_toggle_col2 = st.columns([3, 1])
    with prof_toggle_col2:
        prof_period = st.radio("Period", ["Annual", "Quarterly"], horizontal=True, key="prof_period", label_visibility="collapsed")

    # Select data source
    if prof_period == "Quarterly" and quarterly_income is not None and not quarterly_income.empty:
        prof_data = quarterly_income.copy()
        prof_dates = _get_quarterly_dates(prof_data)
    elif income_stmt is not None and not income_stmt.empty:
        prof_data = income_stmt.copy()
        prof_dates = _get_annual_dates(prof_data)
    else:
        prof_data = None
        prof_dates = []

    if prof_data is not None and len(prof_dates) > 0:
        # Find net income column
        ni_col = _find_column(prof_data, ["Net Income", "NetIncome", "Net Income Common Stockholders"])

        if ni_col:
            prof_fig = make_subplots(specs=[[{"secondary_y": True}]])

            ni_values = (prof_data[ni_col] / 1e9).tolist()

            # Net Income bars
            prof_fig.add_trace(
                go.Bar(x=prof_dates, y=ni_values, name="Net Income ($B)", marker_color="#0097A7"),
                secondary_y=False
            )

            # ROE line (current ROE as horizontal line since we don't have historical)
            roe_val = info.get("returnOnEquity")
            if roe_val:
                roe_pct = roe_val * 100
                prof_fig.add_trace(
                    go.Scatter(
                        x=prof_dates, y=[roe_pct] * len(prof_dates),
                        name=f"ROE ({roe_pct:.1f}%)", mode='lines',
                        line=dict(color="#FF6B6B", width=2, dash='dash')
                    ),
                    secondary_y=True
                )

                # Industry average ROE if comparison enabled
                if show_peer_comparison and peer_means.get("roe"):
                    peer_roe = peer_means.get("roe") * 100
                    prof_fig.add_trace(
                        go.Scatter(
                            x=prof_dates, y=[peer_roe] * len(prof_dates),
                            name=f"Industry ROE ({peer_roe:.1f}%)", mode='lines',
                            line=dict(color="#80A4AA", width=2, dash='dot')
                        ),
                        secondary_y=True
                    )

            prof_fig.update_layout(
                height=350, margin=dict(l=10, r=60, t=10, b=40),
                font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif", size=12),
                plot_bgcolor='white', paper_bgcolor='white',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color=LEGEND_FONT_COLOR, size=12)),
                hovermode="x unified", bargap=0.3
            )
            prof_fig.update_xaxes(showgrid=False, tickfont=dict(color=CHART_AXIS_COLOR, size=11))
            prof_fig.update_yaxes(title_text="Net Income ($B)", ticksuffix=" B", secondary_y=False, showgrid=True, gridcolor='#D0E8EA', tickfont=dict(color=CHART_AXIS_COLOR, size=11), title_font=dict(color=CHART_AXIS_COLOR, size=12), rangemode="tozero")
            prof_fig.update_yaxes(title_text="ROE %", ticksuffix="%", secondary_y=True, showgrid=False, tickfont=dict(color=CHART_AXIS_COLOR, size=11), title_font=dict(color=CHART_AXIS_COLOR, size=12))

            st.plotly_chart(prof_fig, use_container_width=True, config={'scrollZoom': True})
    else:
        st.info("Profitability data not available.")

    st.markdown("---")

    # =========================================================================
    # 2. GROWTH CHART (Revenue columns)
    # =========================================================================
    st.markdown("### Growth")

    growth_toggle_col1, growth_toggle_col2 = st.columns([3, 1])
    with growth_toggle_col2:
        growth_period = st.radio("Period", ["Annual", "Quarterly"], horizontal=True, key="growth_period", label_visibility="collapsed")

    # Select data source
    if growth_period == "Quarterly" and quarterly_income is not None and not quarterly_income.empty:
        growth_data = quarterly_income.copy()
        growth_dates = _get_quarterly_dates(growth_data)
    elif income_stmt is not None and not income_stmt.empty:
        growth_data = income_stmt.copy()
        growth_dates = _get_annual_dates(growth_data)
    else:
        growth_data = None
        growth_dates = []

    if growth_data is not None and len(growth_dates) > 0:
        rev_col = _find_column(growth_data, ["Total Revenue", "TotalRevenue", "Revenue"])

        if rev_col:
            growth_fig = make_subplots(specs=[[{"secondary_y": True}]])

            rev_values = (growth_data[rev_col] / 1e9).tolist()

            # Revenue bars
            growth_fig.add_trace(
                go.Bar(x=growth_dates, y=rev_values, name="Revenue ($B)", marker_color="#0097A7"),
                secondary_y=False
            )

            # Calculate period-over-period growth rate
            raw_rev = growth_data[rev_col].tolist()
            growth_rates = [None]  # First period has no prior period
            for i in range(1, len(raw_rev)):
                if raw_rev[i-1] and raw_rev[i-1] != 0:
                    rate = ((raw_rev[i] - raw_rev[i-1]) / abs(raw_rev[i-1])) * 100
                    growth_rates.append(rate)
                else:
                    growth_rates.append(None)

            # Add growth rate line
            growth_fig.add_trace(
                go.Scatter(
                    x=growth_dates, y=growth_rates,
                    name="Growth Rate %", mode='lines+markers',
                    line=dict(color="#FF6B6B", width=2),
                    marker=dict(size=6, color="#FF6B6B"),
                    connectgaps=True
                ),
                secondary_y=True
            )

            # Industry average revenue growth line when peer comparison is enabled
            if show_peer_comparison and peer_means.get("rev_growth"):
                peer_rev_growth = peer_means.get("rev_growth") * 100
                growth_fig.add_trace(
                    go.Scatter(
                        x=growth_dates, y=[peer_rev_growth] * len(growth_dates),
                        name=f"Industry Avg ({peer_rev_growth:.1f}%)", mode='lines',
                        line=dict(color="#80A4AA", width=2, dash='dot')
                    ),
                    secondary_y=True
                )

            growth_fig.update_layout(
                height=350, margin=dict(l=10, r=60, t=10, b=40),
                font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif", size=12),
                plot_bgcolor='white', paper_bgcolor='white',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color=LEGEND_FONT_COLOR, size=12)),
                hovermode="x unified", bargap=0.3
            )
            growth_fig.update_xaxes(showgrid=False, tickfont=dict(color=CHART_AXIS_COLOR, size=11))
            growth_fig.update_yaxes(title_text="Revenue ($B)", ticksuffix=" B", secondary_y=False, showgrid=True, gridcolor='#D0E8EA', tickfont=dict(color=CHART_AXIS_COLOR, size=11), title_font=dict(color=CHART_AXIS_COLOR, size=12), rangemode="tozero")
            growth_fig.update_yaxes(title_text="Growth %", ticksuffix="%", secondary_y=True, showgrid=False, tickfont=dict(color=CHART_AXIS_COLOR, size=11), title_font=dict(color=CHART_AXIS_COLOR, size=12))

            st.plotly_chart(growth_fig, use_container_width=True)

            # Show growth rate
            rev_growth = info.get("revenueGrowth")
            if rev_growth:
                growth_col1, growth_col2 = st.columns(2)
                with growth_col1:
                    st.metric("Revenue Growth (YoY)", f"{rev_growth*100:.1f}%")
                if show_peer_comparison and peer_means.get("rev_growth"):
                    with growth_col2:
                        st.metric("Industry Average", f"{peer_means.get('rev_growth')*100:.1f}%")
    else:
        st.info("Revenue data not available.")

    st.markdown("---")

    # =========================================================================
    # 3. LEVERAGE CHART (Debt & Equity columns + D/E ratio line)
    # =========================================================================
    st.markdown("### Leverage")

    lev_toggle_col1, lev_toggle_col2 = st.columns([3, 1])
    with lev_toggle_col2:
        lev_period = st.radio("Period", ["Annual", "Quarterly"], horizontal=True, key="lev_period", label_visibility="collapsed")

    # Select data source
    if lev_period == "Quarterly" and quarterly_balance is not None and not quarterly_balance.empty:
        lev_data = quarterly_balance.copy()
        lev_dates = _get_quarterly_dates(lev_data)
    elif balance_sheet is not None and not balance_sheet.empty:
        lev_data = balance_sheet.copy()
        lev_dates = _get_annual_dates(lev_data)
    else:
        lev_data = None
        lev_dates = []

    if lev_data is not None and len(lev_dates) > 0:
        debt_col = _find_column(lev_data, ["Total Debt", "TotalDebt", "Long Term Debt", "LongTermDebt"])
        equity_col = _find_column(lev_data, ["Total Equity Gross Minority Interest", "Stockholders Equity", "StockholdersEquity", "Total Stockholders Equity", "Total Equity"])

        if debt_col or equity_col:
            lev_fig = make_subplots(specs=[[{"secondary_y": True}]])

            if debt_col:
                debt_values = (lev_data[debt_col] / 1e9).tolist()
                lev_fig.add_trace(
                    go.Bar(x=lev_dates, y=debt_values, name="Debt ($B)", marker_color="#FF6B6B", width=0.35, offset=-0.2),
                    secondary_y=False
                )

            if equity_col:
                equity_values = (lev_data[equity_col] / 1e9).tolist()
                lev_fig.add_trace(
                    go.Bar(x=lev_dates, y=equity_values, name="Equity ($B)", marker_color="#0097A7", width=0.35, offset=0.2),
                    secondary_y=False
                )

            # D/E ratio line
            de_val = info.get("debtToEquity")
            if de_val:
                lev_fig.add_trace(
                    go.Scatter(
                        x=lev_dates, y=[de_val] * len(lev_dates),
                        name=f"D/E Ratio ({de_val:.1f})", mode='lines',
                        line=dict(color="#FF6B6B", width=2, dash='dash')
                    ),
                    secondary_y=True
                )

                if show_peer_comparison and peer_means.get("de"):
                    peer_de = peer_means.get("de")
                    lev_fig.add_trace(
                        go.Scatter(
                            x=lev_dates, y=[peer_de] * len(lev_dates),
                            name=f"Industry D/E ({peer_de:.1f})", mode='lines',
                            line=dict(color="#80A4AA", width=2, dash='dot')
                        ),
                        secondary_y=True
                    )

            lev_fig.update_layout(
                height=350, margin=dict(l=10, r=60, t=10, b=40),
                font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif", size=12),
                plot_bgcolor='white', paper_bgcolor='white', barmode='group',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color=LEGEND_FONT_COLOR, size=12)),
                hovermode="x unified", bargap=0.3
            )
            lev_fig.update_xaxes(showgrid=False, tickfont=dict(color=CHART_AXIS_COLOR, size=11))
            lev_fig.update_yaxes(title_text="Amount ($B)", ticksuffix=" B", secondary_y=False, showgrid=True, gridcolor='#D0E8EA', tickfont=dict(color=CHART_AXIS_COLOR, size=11), title_font=dict(color=CHART_AXIS_COLOR, size=12), rangemode="tozero")
            lev_fig.update_yaxes(title_text="D/E Ratio", secondary_y=True, showgrid=False, tickfont=dict(color=CHART_AXIS_COLOR, size=11), title_font=dict(color=CHART_AXIS_COLOR, size=12))

            st.plotly_chart(lev_fig, use_container_width=True)
    else:
        st.info("Balance sheet data not available.")

    st.markdown("---")

    # =========================================================================
    # 4. VALUATION CHART (P/E ratio line over time)
    # =========================================================================
    st.markdown("### Valuation")

    val_toggle_col1, val_toggle_col2 = st.columns([3, 1])
    with val_toggle_col2:
        val_period = st.radio("Period", ["1Y", "2Y", "Max"], horizontal=True, key="val_period", label_visibility="collapsed")

    eps = info.get("trailingEps")
    if eps and eps > 0 and not price_data.empty:
        # Filter price data by period
        if val_period == "1Y":
            val_price_data = price_data.tail(252)
        elif val_period == "2Y":
            val_price_data = price_data.tail(504)
        else:
            val_price_data = price_data

        val_fig = go.Figure()

        hist_pe = val_price_data["Close"] / eps
        val_dates = val_price_data["Date"].tolist()
        pe_values = hist_pe.tolist()

        val_fig.add_trace(
            go.Scatter(
                x=val_dates, y=pe_values,
                name="P/E Ratio", mode='lines',
                line=dict(color="#0097A7", width=2),
                fill='tozeroy', fillcolor='rgba(0, 151, 167, 0.1)'
            )
        )

        # Average P/E line
        avg_pe = hist_pe.mean()
        val_fig.add_hline(
            y=avg_pe, line=dict(color="#FF6B6B", dash="dash", width=1.5),
            annotation_text=f"Avg: {avg_pe:.1f}", annotation_position="right"
        )

        # Industry P/E if comparison enabled
        if show_peer_comparison and peer_means.get("pe"):
            peer_pe = peer_means.get("pe")
            val_fig.add_hline(
                y=peer_pe, line=dict(color="#80A4AA", dash="dot", width=1.5),
                annotation_text=f"Industry: {peer_pe:.1f}", annotation_position="left"
            )

        val_fig.update_layout(
            height=350, margin=dict(l=10, r=10, t=10, b=40),
            font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif", size=12),
            plot_bgcolor='white', paper_bgcolor='white',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color=LEGEND_FONT_COLOR, size=12)),
            hovermode="x unified", showlegend=False
        )
        val_fig.update_xaxes(showgrid=False, tickfont=dict(color=CHART_AXIS_COLOR, size=11))
        val_fig.update_yaxes(title_text="P/E Ratio", showgrid=True, gridcolor='#D0E8EA', tickfont=dict(color=CHART_AXIS_COLOR, size=11), title_font=dict(color=CHART_AXIS_COLOR, size=12))

        st.plotly_chart(val_fig, use_container_width=True)

        # Stats
        current_pe = price_data["Close"].iloc[-1] / eps
        val_col1, val_col2, val_col3 = st.columns(3)
        with val_col1:
            st.metric("Current P/E", f"{current_pe:.1f}")
        with val_col2:
            st.metric("Average P/E", f"{avg_pe:.1f}")
        with val_col3:
            if show_peer_comparison and peer_means.get("pe"):
                st.metric("Industry P/E", f"{peer_means.get('pe'):.1f}")
    else:
        st.info("P/E data not available (requires positive EPS).")

    # =========================================================================
    # COMPARISON TABLE (shown when peer comparison is enabled)
    # =========================================================================
    if show_peer_comparison:
        st.markdown("---")
        st.markdown("### Comparison Summary")

        # Get company values
        company_pe = info.get("trailingPE")
        company_peg = info.get("pegRatio")
        company_roe = info.get("returnOnEquity")
        company_margin = info.get("profitMargins")
        company_growth = info.get("revenueGrowth")
        company_de = info.get("debtToEquity")

        # Build comparison data
        comparison_data = []

        # P/E Ratio (lower is better, unless negative)
        if company_pe and peer_means.get("pe"):
            favorable = "Favorable" if company_pe < peer_means.get("pe") else "Unfavorable"
            comparison_data.append({
                "Metric": "P/E Ratio",
                "Company": f"{company_pe:.1f}",
                "Industry": f"{peer_means.get('pe'):.1f}",
                "Assessment": favorable
            })

        # PEG Ratio (lower is better)
        if company_peg and peer_means.get("peg"):
            favorable = "Favorable" if company_peg < peer_means.get("peg") else "Unfavorable"
            comparison_data.append({
                "Metric": "PEG Ratio",
                "Company": f"{company_peg:.2f}",
                "Industry": f"{peer_means.get('peg'):.2f}",
                "Assessment": favorable
            })

        # ROE (higher is better)
        if company_roe and peer_means.get("roe"):
            favorable = "Favorable" if company_roe > peer_means.get("roe") else "Unfavorable"
            comparison_data.append({
                "Metric": "ROE",
                "Company": f"{company_roe*100:.1f}%",
                "Industry": f"{peer_means.get('roe')*100:.1f}%",
                "Assessment": favorable
            })

        # Net Margin (higher is better)
        if company_margin and peer_means.get("net_margin"):
            favorable = "Favorable" if company_margin > peer_means.get("net_margin") else "Unfavorable"
            comparison_data.append({
                "Metric": "Net Margin",
                "Company": f"{company_margin*100:.1f}%",
                "Industry": f"{peer_means.get('net_margin')*100:.1f}%",
                "Assessment": favorable
            })

        # Revenue Growth (higher is better)
        if company_growth and peer_means.get("rev_growth"):
            favorable = "Favorable" if company_growth > peer_means.get("rev_growth") else "Unfavorable"
            comparison_data.append({
                "Metric": "Revenue Growth",
                "Company": f"{company_growth*100:.1f}%",
                "Industry": f"{peer_means.get('rev_growth')*100:.1f}%",
                "Assessment": favorable
            })

        # Debt/Equity (lower is generally better)
        if company_de and peer_means.get("de"):
            favorable = "Favorable" if company_de < peer_means.get("de") else "Unfavorable"
            comparison_data.append({
                "Metric": "Debt/Equity",
                "Company": f"{company_de:.1f}",
                "Industry": f"{peer_means.get('de'):.1f}",
                "Assessment": favorable
            })

        if comparison_data:
            df = pd.DataFrame(comparison_data)

            # Style the dataframe
            def highlight_assessment(val):
                if val == "Favorable":
                    return 'background-color: rgba(16, 185, 129, 0.2); color: #059669;'
                elif val == "Unfavorable":
                    return 'background-color: rgba(239, 68, 68, 0.2); color: #DC2626;'
                return ''

            styled_df = df.style.applymap(highlight_assessment, subset=['Assessment'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

            # Summary
            favorable_count = sum(1 for item in comparison_data if item["Assessment"] == "Favorable")
            total_count = len(comparison_data)
            st.caption(f"{selected} is favorable on {favorable_count} of {total_count} metrics compared to industry peers.")
        else:
            st.info("Insufficient data for comparison table.")


def _find_column(df, possible_names):
    """Find first matching column from list of possible names."""
    for name in possible_names:
        if name in df.columns:
            return name
    return None


def _get_annual_dates(df):
    """Get formatted annual dates from dataframe index."""
    if hasattr(df.index, 'strftime'):
        return df.index.strftime('%Y').tolist()
    return [str(d)[:4] for d in df.index]


def _get_quarterly_dates(df):
    """Get formatted quarterly dates from dataframe index."""
    dates = []
    for d in df.index:
        if hasattr(d, 'quarter'):
            dates.append(f"Q{d.quarter} '{str(d.year)[2:]}")
        else:
            dates.append(str(d)[:7])
    return dates
