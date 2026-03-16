# =============================================================================
# OVERVIEW TAB - Company overview and sector comparison
# =============================================================================

import pandas as pd
import streamlit as st
from components import render_metrics_strip


def render(selected, price_data, info, all_stocks_df, filtered_df, sector, industry,
           last_row, change_pct, sp500_set,
           load_sector_peers_metrics):
    """Render the Overview tab content."""
    st.subheader(f"{selected} Overview")

    # S&P 500 badge
    is_sp500 = selected in sp500_set

    change_color = "#10B981" if change_pct >= 0 else "#F43F5E"
    price_tip = f"Last closing price of ${last_row['Close']:.2f}."
    change_tip = f"Daily change of {change_pct:+.2f}%."
    sp_tip = "S&P 500 member" if is_sp500 else "Not in S&P 500"
    sp_text = "S&P 500" if is_sp500 else "Non S&P"
    sector_tip = f"Sector: {sector}"
    industry_tip = f"Industry: {industry}"

    # Strip 1: Price | Change | Index | Sector | Industry
    st.markdown(render_metrics_strip([
        {"label": "Last Price", "value": f"${last_row['Close']:.2f}", "tooltip": price_tip},
        {"label": "Daily Change", "value": f"{change_pct:+.2f}%", "color": change_color, "tooltip": change_tip},
        {"label": "Index", "value": sp_text, "color": "#10B981" if is_sp500 else "#1A3C40", "tooltip": sp_tip},
        {"label": "Sector", "value": sector, "tooltip": sector_tip},
        {"label": "Industry", "value": industry, "tooltip": industry_tip},
    ]), unsafe_allow_html=True)

    # Company description
    long_summary = info.get("longBusinessSummary")
    if long_summary:
        sentences = long_summary.split(". ")
        short_desc = ". ".join(sentences[:3]).strip()
        if not short_desc.endswith("."):
            short_desc += "."
        st.markdown(f"""
        <div style="background:#FFFFFF;border:1px solid #D0E8EA;border-radius:6px;padding:10px 14px;">
            <div style="font-family:Source Sans Pro,Arial,sans-serif;font-size:13px;color:#37616A;line-height:1.55;">
                {short_desc}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Key metrics + relative valuation
    pe_val = info.get("trailingPE")
    peg_val = info.get("pegRatio")
    roe_val = info.get("returnOnEquity")
    de_val = info.get("debtToEquity")

    pe_display = f"{pe_val:.1f}" if pe_val else "N/A"
    peg_display = f"{peg_val:.2f}" if peg_val else "N/A"
    roe_display = f"{roe_val*100:.1f}%" if roe_val else "N/A"
    de_display = f"{de_val:.1f}" if de_val else "N/A"

    pe_color = "#10B981" if pe_val and pe_val < 25 else "#F59E0B" if pe_val and pe_val < 35 else "#F43F5E" if pe_val else "#1A3C40"
    peg_color = "#10B981" if peg_val and peg_val < 1.5 else "#F59E0B" if peg_val and peg_val < 2 else "#F43F5E" if peg_val else "#1A3C40"
    roe_color = "#10B981" if roe_val and roe_val > 0.15 else "#F59E0B" if roe_val and roe_val > 0.10 else "#F43F5E" if roe_val else "#1A3C40"
    de_color = "#10B981" if de_val and de_val < 50 else "#F59E0B" if de_val and de_val < 100 else "#F43F5E" if de_val else "#1A3C40"

    # Relative valuation
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
            val_color = "#F59E0B"
        else:
            val_text = "Below Peers"
            val_color = "#10B981"
    else:
        val_text = "N/A"
        val_color = "#1A3C40"

    # Strip 2: P/E | PEG | ROE | D/E | Rel. Valuation
    st.markdown(render_metrics_strip([
        {"label": "P/E Ratio", "value": pe_display, "color": pe_color},
        {"label": "PEG Ratio", "value": peg_display, "color": peg_color},
        {"label": "ROE", "value": roe_display, "color": roe_color},
        {"label": "Debt/Equity", "value": de_display, "color": de_color},
        {"label": "Rel. Valuation", "value": val_text, "color": val_color},
    ]), unsafe_allow_html=True)
