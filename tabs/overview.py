# =============================================================================
# OVERVIEW TAB - Company overview and sector comparison
# =============================================================================

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from components import render_metric_card, render_compact_card, format_mcap


def render(selected, price_data, info, all_stocks_df, filtered_df, sector, industry,
           last_row, change_pct, sp500_set,
           load_industry_market_caps, load_sector_peers_metrics):
    """Render the Overview tab content."""
    st.subheader(f"{selected} Overview")

    # S&P 500 and Exchange badges (exchange from yfinance)
    is_sp500 = selected in sp500_set
    # Get exchange from yfinance info
    raw_exchange = info.get("exchange", "")
    if "nasdaq" in raw_exchange.lower() or "nms" in raw_exchange.lower() or "ngm" in raw_exchange.lower():
        exchange = "NASDAQ"
    elif "nyse" in raw_exchange.lower() or "nys" in raw_exchange.lower():
        exchange = "NYSE"
    else:
        exchange = raw_exchange if raw_exchange else "N/A"

    # Top row: Price, Change, Exchange, S&P 500 status
    top_col1, top_col2, top_col3, top_col4 = st.columns(4)

    change_status = "success" if change_pct >= 0 else "danger"
    price_tip = f"Last closing price of ${last_row['Close']:.2f}. This is the most recent end-of-day traded price for {selected}."
    change_tip = f"Daily change of {change_pct:+.2f}% represents the percentage move from yesterday's close. " + ("Positive movement indicates buying pressure." if change_pct >= 0 else "Negative movement indicates selling pressure.")

    with top_col1:
        st.markdown(render_metric_card("Last Price", f"${last_row['Close']:.2f}", price_tip, "neutral", "medium"), unsafe_allow_html=True)

    with top_col2:
        st.markdown(render_metric_card("Daily Change", f"{change_pct:+.2f}%", change_tip, change_status, "medium"), unsafe_allow_html=True)

    exch_tips = {
        "NASDAQ": "NASDAQ: The National Association of Securities Dealers Automated Quotations. Known for technology and growth companies. Electronic trading exchange.",
        "NYSE": "NYSE: The New York Stock Exchange. The largest stock exchange by market cap. Known for established blue-chip companies."
    }
    exch_tip = exch_tips.get(exchange, f"Stock is listed on {exchange} exchange.")

    with top_col3:
        st.markdown(render_metric_card("Exchange", exchange, exch_tip, "info", "medium"), unsafe_allow_html=True)

    sp_tip = f"{'This stock is a member of the S&P 500 index, representing one of the 500 largest US public companies by market cap.' if is_sp500 else 'This stock is NOT in the S&P 500 index. It may be a smaller company or recently listed.'}"
    sp_status = "success" if is_sp500 else "neutral"
    sp_text = "S&P 500" if is_sp500 else "Non S&P"
    with top_col4:
        st.markdown(render_metric_card("Index", sp_text, sp_tip, sp_status, "medium"), unsafe_allow_html=True)

    st.markdown("")

    # Second row: Sector & Industry
    info_col1, info_col2 = st.columns(2)
    sector_tip = f"Sector: {sector}. Sectors group companies by broad economic activity. Companies in the same sector often move together based on macroeconomic trends."
    industry_tip = f"Industry: {industry}. Industries are more specific than sectors and group companies with similar business models and competitive dynamics."
    with info_col1:
        st.markdown(render_metric_card("Sector", sector, sector_tip, "neutral", "normal"), unsafe_allow_html=True)
    with info_col2:
        st.markdown(render_metric_card("Industry", industry, industry_tip, "neutral", "normal"), unsafe_allow_html=True)

    # Sector Market Share Pie Chart
    st.markdown("### Sector Market Share")

    # Get sector from all_stocks_df for consistency
    stock_info = all_stocks_df[all_stocks_df["ticker"] == selected]
    chart_sector = stock_info["sector"].values[0] if len(stock_info) > 0 and pd.notna(stock_info["sector"].values[0]) else sector

    # Get peers from the same sector
    sector_peers = all_stocks_df[all_stocks_df["sector"] == chart_sector]["ticker"].tolist()

    # Ensure selected ticker is included
    if selected not in sector_peers:
        sector_peers.insert(0, selected)

    if len(sector_peers) > 1:
        with st.spinner("Loading sector market caps..."):
            # Get top companies by fetching market caps
            market_caps = load_industry_market_caps(tuple(sector_peers[:20]))

        if market_caps:
            # Ensure selected company is in the data
            if selected not in market_caps:
                # Fetch selected company's market cap separately
                selected_mcap = info.get("marketCap")
                if selected_mcap and selected_mcap > 0:
                    market_caps[selected] = selected_mcap

            if selected in market_caps:
                # Sort by market cap descending
                sorted_caps = sorted(market_caps.items(), key=lambda x: x[1], reverse=True)
                top_tickers = [t for t, _ in sorted_caps[:10]]
                if selected not in top_tickers:
                    top_tickers = top_tickers[:9] + [selected]
                    # Re-sort to maintain order
                    top_tickers = [t for t in [x[0] for x in sorted_caps] if t in top_tickers or t == selected][:10]

                # Filter and maintain sort order
                sorted_market_caps = [(t, market_caps[t]) for t in top_tickers if t in market_caps]
                sorted_market_caps.sort(key=lambda x: x[1], reverse=True)

                # Create ticker to company name mapping
                ticker_to_name = {}
                for ticker, _ in sorted_market_caps:
                    name_row = all_stocks_df[all_stocks_df["ticker"] == ticker]
                    if len(name_row) > 0:
                        ticker_to_name[ticker] = name_row["name"].values[0]
                    else:
                        ticker_to_name[ticker] = ticker

                # Prepare data for pie chart (sorted by market cap)
                tickers = [t for t, _ in sorted_market_caps]
                values = [v for _, v in sorted_market_caps]
                total_market_cap = sum(values)

                # Find selected company rank (before grouping)
                selected_rank = tickers.index(selected) + 1 if selected in tickers else "N/A"

                # Calculate percentages
                percentages = [(v / total_market_cap) * 100 for v in values]

                # Group companies with <= 2% into "Others" (but never group the selected company)
                grouped_tickers = []
                grouped_values = []
                grouped_percentages = []
                others_value = 0
                others_companies = []

                for t, v, pct in zip(tickers, values, percentages):
                    if pct <= 2 and t != selected:
                        others_value += v
                        others_companies.append((t, ticker_to_name.get(t, t), pct))
                    else:
                        grouped_tickers.append(t)
                        grouped_values.append(v)
                        grouped_percentages.append(pct)

                # Add "Others" group if there are any
                if others_value > 0:
                    grouped_tickers.append("Others")
                    grouped_values.append(others_value)
                    grouped_percentages.append((others_value / total_market_cap) * 100)
                    ticker_to_name["Others"] = "Others"

                # Update working variables
                tickers = grouped_tickers
                values = grouped_values
                percentages = grouped_percentages

                # Light blue-teal gradient palette (aesthetically pleasing)
                gradient_colors = [
                    "#2D8BBA",  # Deep blue
                    "#41B8D5",  # Bright teal
                    "#6CE5E8",  # Light cyan
                    "#5DADE2",  # Sky blue
                    "#85C1E9",  # Soft blue
                    "#A9CCE3",  # Pale blue
                    "#7FB3D5",  # Muted blue
                    "#AED6F1",  # Light periwinkle
                    "#3498DB",  # Bright blue
                    "#5DADE2",  # Sky blue (repeat for more)
                ]

                # Create colors - selected gets coral, Others gets gray
                colors = []
                pull_values = []
                color_idx = 0
                for ticker in tickers:
                    if ticker == selected:
                        colors.append("#FF6B6B")  # Warm coral for selected
                        pull_values.append(0.06)
                    elif ticker == "Others":
                        colors.append("#BDC3C7")  # Light gray for Others
                        pull_values.append(0)
                    else:
                        colors.append(gradient_colors[color_idx % len(gradient_colors)])
                        color_idx += 1
                        pull_values.append(0)

                # Create custom hover text with company names and rank
                hover_text = []
                for i, (t, pct) in enumerate(zip(tickers, percentages)):
                    if t == "Others":
                        # Show list of companies in Others group
                        others_list = "<br>".join([f"* {name} ({tick}): {p:.1f}%" for tick, name, p in others_companies[:5]])
                        if len(others_companies) > 5:
                            others_list += f"<br>* ...and {len(others_companies) - 5} more"
                        hover_text.append(
                            f"<b>Others</b> ({len(others_companies)} companies)<br>"
                            f"Combined Market Cap: {format_mcap(others_value)}<br>"
                            f"Sector Share: {pct:.1f}%<br><br>"
                            f"{others_list}"
                        )
                    else:
                        rank = i + 1
                        mcap_fmt = format_mcap(market_caps[t])
                        hover_text.append(
                            f"<b>{ticker_to_name[t]}</b> ({t})<br>"
                            f"Rank: #{rank} in sector<br>"
                            f"Market Cap: {mcap_fmt}<br>"
                            f"Sector Share: {pct:.1f}%"
                        )

                # Text display - show percentage for larger slices, selected always shown
                text_display = []
                for t, pct in zip(tickers, percentages):
                    if t == selected:
                        text_display.append(f"<b>{t}</b><br>{pct:.1f}%")
                    elif t == "Others":
                        text_display.append(f"Others<br>{pct:.1f}%") if pct >= 5 else text_display.append("")
                    elif pct >= 8:  # Show label for slices >= 8%
                        text_display.append(f"{t}<br>{pct:.1f}%")
                    else:
                        text_display.append("")

                # Get selected company info for display
                selected_name = ticker_to_name.get(selected, selected)
                selected_pct = (market_caps[selected] / total_market_cap) * 100
                selected_mcap = format_mcap(market_caps[selected])

                fig_pie = go.Figure(data=[go.Pie(
                    labels=tickers,
                    values=values,
                    hole=0,  # Solid pie chart
                    marker=dict(
                        colors=colors,
                        line=dict(color='#ffffff', width=1.5)
                    ),
                    pull=pull_values,
                    textinfo='text',
                    text=text_display,
                    textposition='outside',
                    textfont=dict(size=11, family='Source Sans Pro', color='#2d3436'),
                    hovertext=hover_text,
                    hoverinfo='text',
                    direction='clockwise',
                    sort=False,
                    showlegend=False
                )])

                fig_pie.update_layout(
                    height=380,
                    margin=dict(t=50, b=30, l=30, r=30),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    title=dict(
                        text=f"<b>{chart_sector} Sector</b> - Top {len(tickers)} by Market Cap",
                        font=dict(size=14, color='#2d3436', family='Source Sans Pro'),
                        x=0.5,
                        xanchor='center'
                    )
                )

                st.plotly_chart(fig_pie, use_container_width=True)

                # Summary metrics below chart
                mcap_col1, mcap_col2, mcap_col3 = st.columns(3)
                with mcap_col1:
                    st.metric("Your Selection", f"#{selected_rank} in sector")
                with mcap_col2:
                    st.metric("Market Cap", selected_mcap)
                with mcap_col3:
                    st.metric("Sector Share", f"{selected_pct:.1f}%")
            else:
                st.info("Market cap data not available for this company.")
        else:
            st.info("Could not load market cap data for sector comparison.")
    else:
        st.info("Not enough companies in this sector for comparison.")

    st.markdown("### Key Metrics")

    # Key metrics with styled cards
    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)

    pe_val = info.get("trailingPE")
    peg_val = info.get("pegRatio")
    roe_val = info.get("returnOnEquity")
    de_val = info.get("debtToEquity")
    rsi_val = last_row["RSI"] if pd.notna(last_row["RSI"]) else None
    macd_val = last_row["MACD"] if pd.notna(last_row["MACD"]) else None

    # Build dynamic tooltips
    if pe_val:
        pe_assessment = "cheap (value territory)" if pe_val < 15 else "fairly valued" if pe_val < 25 else "expensive" if pe_val < 40 else "very expensive (growth premium)"
        pe_tip = f"P/E Ratio of {pe_val:.1f} means the stock trades at {pe_val:.1f}x its earnings. This is considered {pe_assessment}. Lower P/E suggests better value, but growth stocks often have higher P/E."
    else:
        pe_tip = "P/E Ratio not available. This could mean the company is not profitable or data is unavailable."

    if peg_val:
        peg_assessment = "undervalued relative to growth" if peg_val < 1 else "fairly valued for growth" if peg_val < 2 else "expensive relative to growth"
        peg_tip = f"PEG Ratio of {peg_val:.2f} adjusts P/E for expected growth. A PEG of {peg_val:.2f} is {peg_assessment}. PEG below 1 suggests the stock may be undervalued given its growth rate."
    else:
        peg_tip = "PEG Ratio not available. Requires both P/E and growth rate data."

    if roe_val:
        roe_pct = roe_val * 100
        roe_assessment = "excellent" if roe_pct > 20 else "good" if roe_pct > 15 else "moderate" if roe_pct > 10 else "weak"
        roe_tip = f"ROE of {roe_pct:.1f}% means the company generates {roe_pct:.1f} cents of profit for every dollar of shareholder equity. This is {roe_assessment}. Higher ROE indicates efficient use of capital."
    else:
        roe_tip = "Return on Equity not available."

    if de_val:
        de_assessment = "conservative (low leverage)" if de_val < 50 else "moderate leverage" if de_val < 100 else "high leverage" if de_val < 200 else "very high leverage (risky)"
        de_tip = f"Debt/Equity of {de_val:.1f} means the company has ${de_val:.1f} of debt for every $100 of equity. This is {de_assessment}. Lower ratios suggest financial stability."
    else:
        de_tip = "Debt/Equity ratio not available."

    if rsi_val:
        rsi_assessment = "overbought (potential pullback)" if rsi_val > 70 else "oversold (potential bounce)" if rsi_val < 30 else "neutral momentum"
        rsi_tip = f"RSI of {rsi_val:.1f} indicates {rsi_assessment}. RSI measures momentum on a 0-100 scale. Above 70 suggests overbought, below 30 suggests oversold."
    else:
        rsi_tip = "RSI not available due to insufficient price history."

    if macd_val:
        macd_assessment = "bullish momentum" if macd_val > 0 else "bearish momentum"
        macd_tip = f"MACD of {macd_val:.2f} shows {macd_assessment}. MACD measures the relationship between two moving averages. Positive values suggest upward momentum."
    else:
        macd_tip = "MACD not available due to insufficient price history."

    with metrics_col1:
        pe_display = f"{pe_val:.1f}" if pe_val else "N/A"
        pe_status = "success" if pe_val and pe_val < 25 else "warning" if pe_val and pe_val < 35 else "danger" if pe_val else "neutral"
        st.markdown(render_compact_card("P/E Ratio", pe_display, pe_tip, pe_status), unsafe_allow_html=True)

        peg_display = f"{peg_val:.2f}" if peg_val else "N/A"
        peg_status = "success" if peg_val and peg_val < 1.5 else "warning" if peg_val and peg_val < 2 else "danger" if peg_val else "neutral"
        st.markdown(render_compact_card("PEG Ratio", peg_display, peg_tip, peg_status), unsafe_allow_html=True)

    with metrics_col2:
        roe_display = f"{roe_val*100:.1f}%" if roe_val else "N/A"
        roe_status = "success" if roe_val and roe_val > 0.15 else "warning" if roe_val and roe_val > 0.10 else "danger" if roe_val else "neutral"
        st.markdown(render_compact_card("ROE", roe_display, roe_tip, roe_status), unsafe_allow_html=True)

        de_display = f"{de_val:.1f}" if de_val else "N/A"
        de_status = "success" if de_val and de_val < 50 else "warning" if de_val and de_val < 100 else "danger" if de_val else "neutral"
        st.markdown(render_compact_card("Debt/Equity", de_display, de_tip, de_status), unsafe_allow_html=True)

    with metrics_col3:
        rsi_display = f"{rsi_val:.1f}" if rsi_val else "N/A"
        rsi_status = "danger" if rsi_val and rsi_val > 70 else "success" if rsi_val and rsi_val < 30 else "warning" if rsi_val else "neutral"
        st.markdown(render_compact_card("RSI (14)", rsi_display, rsi_tip, rsi_status), unsafe_allow_html=True)

        macd_display = f"{macd_val:.2f}" if macd_val else "N/A"
        macd_status = "success" if macd_val and macd_val > 0 else "danger" if macd_val else "neutral"
        st.markdown(render_compact_card("MACD", macd_display, macd_tip, macd_status), unsafe_allow_html=True)

    st.markdown("### Relative Valuation")

    stock_sector = all_stocks_df[all_stocks_df["ticker"] == selected]["sector"].values
    if len(stock_sector) > 0:
        val_sector_peers = all_stocks_df[all_stocks_df["sector"] == stock_sector[0]]["ticker"].tolist()[:20]
    else:
        val_sector_peers = filtered_df["ticker"].tolist()[:20]
    peers = load_sector_peers_metrics(tuple(val_sector_peers))
    peer_pe = peers["pe"].dropna().mean()

    if info.get("trailingPE") and peer_pe:
        if info.get("trailingPE") > peer_pe:
            val_text = "Above Peers"
            val_status_type = "warning"
            val_tip = f"Relative Valuation: This stock's P/E of {info.get('trailingPE'):.1f} is above the sector average of {peer_pe:.1f}. The premium may be justified by faster growth or stronger fundamentals."
        else:
            val_text = "Below Peers"
            val_status_type = "success"
            val_tip = f"Relative Valuation: This stock's P/E of {info.get('trailingPE'):.1f} is below the sector average of {peer_pe:.1f}. This may represent a value opportunity or reflect company-specific concerns."
    else:
        val_text = "N/A"
        val_status_type = "neutral"
        val_tip = "Relative valuation cannot be calculated. Either P/E is unavailable or insufficient peer data exists."

    st.markdown(render_metric_card("Relative Valuation", val_text, val_tip, val_status_type, "medium"), unsafe_allow_html=True)
