# =============================================================================
# OVERVIEW TAB - Company overview and sector comparison (Dash version)
# =============================================================================

import pandas as pd
from dash import html

from components import COLORS, FONTS, metrics_strip, card, snappy


def render(stock_data, price_data, all_stocks_df, sp500_set):
    ticker = stock_data["ticker"]
    info = stock_data["info"]
    change_pct = stock_data["change_pct"]

    last_close = float(price_data["Close"].iloc[-1])
    sector = info.get("sector", "Technology")
    industry = info.get("industry", "N/A")
    is_sp500 = ticker in sp500_set

    change_color = COLORS["success"] if change_pct >= 0 else COLORS["danger"]

    # Strip 1: Price | Change | Index | Sector | Industry
    strip1 = metrics_strip([
        {"label": "Last Price", "value": f"${last_close:.2f}"},
        {"label": "Daily Change", "value": f"{change_pct:+.2f}%", "color": change_color},
        {"label": "Index", "value": "S&P 500" if is_sp500 else "Non S&P",
         "color": COLORS["success"] if is_sp500 else COLORS["text_primary"]},
        {"label": "Sector", "value": sector},
        {"label": "Industry", "value": industry},
    ])

    # Company description
    desc_children = []
    long_summary = info.get("longBusinessSummary")
    if long_summary:
        sentences = long_summary.split(". ")
        short_desc = ". ".join(sentences[:3]).strip()
        if not short_desc.endswith("."):
            short_desc += "."
        desc_children = [card(
            html.Div(short_desc, style={
                "fontFamily": FONTS["primary"], "fontSize": "13px",
                "color": "#37616A", "lineHeight": "1.55",
            }),
        )]

    # Key metrics
    pe_val = info.get("trailingPE")
    peg_val = info.get("pegRatio")
    roe_val = info.get("returnOnEquity")
    de_val = info.get("debtToEquity")

    pe_display = f"{pe_val:.1f}" if pe_val else "N/A"
    peg_display = f"{peg_val:.2f}" if peg_val else "N/A"
    roe_display = f"{roe_val * 100:.1f}%" if roe_val else "N/A"
    de_display = f"{de_val:.1f}" if de_val else "N/A"

    pe_color = COLORS["success"] if pe_val and pe_val < 25 else COLORS["warning"] if pe_val and pe_val < 35 else COLORS["danger"] if pe_val else COLORS["text_primary"]
    peg_color = COLORS["success"] if peg_val and peg_val < 1.5 else COLORS["warning"] if peg_val and peg_val < 2 else COLORS["danger"] if peg_val else COLORS["text_primary"]
    roe_color = COLORS["success"] if roe_val and roe_val > 0.15 else COLORS["warning"] if roe_val and roe_val > 0.10 else COLORS["danger"] if roe_val else COLORS["text_primary"]
    de_color = COLORS["success"] if de_val and de_val < 50 else COLORS["warning"] if de_val and de_val < 100 else COLORS["danger"] if de_val else COLORS["text_primary"]

    strip2 = metrics_strip([
        {"label": "P/E Ratio", "value": pe_display, "color": pe_color},
        {"label": "PEG Ratio", "value": peg_display, "color": peg_color},
        {"label": "ROE", "value": roe_display, "color": roe_color},
        {"label": "Debt/Equity", "value": de_display, "color": de_color},
    ])

    return html.Div([
        html.H3(f"{ticker} Overview", style={
            "fontFamily": FONTS["primary"], "fontWeight": 600,
            "color": COLORS["teal_dark"], "marginBottom": "12px",
        }),
        strip1,
        html.Div(style={"height": "8px"}),
        *desc_children,
        html.Div(style={"height": "8px"}),
        strip2,
    ])
