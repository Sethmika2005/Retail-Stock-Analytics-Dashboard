# =============================================================================
# FUNDAMENTALS TAB - "The Financial Health Story" — Charts with verdicts
# =============================================================================

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import html, dcc

from components import COLORS, FONTS, SHADOWS, LABEL_STYLE, card, label, spacer, progress_bar
from models import calculate_fundamental_score_paper2


# =============================================================================
# SHARED HELPERS
# =============================================================================

def _chart_layout(height=280):
    """Standard plotly layout matching dashboard chart style."""
    return dict(
        height=height,
        margin=dict(l=10, r=10, t=10, b=30),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
        font=dict(family=FONTS["primary"], size=11, color=COLORS["text_secondary"]),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
            font=dict(size=11, color=COLORS["text_primary"]),
        ),
    )


def _chart_axes(fig, y_prefix=""):
    """Apply standard axis styling."""
    fig.update_xaxes(
        showgrid=False, showline=True, linecolor=COLORS["border"],
        tickfont=dict(size=10, color=COLORS["muted"]),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor="#F1F5F9",
        tickfont=dict(size=10, color=COLORS["muted"]),
        tickprefix=y_prefix,
    )


def _verdict_badge(text, color):
    """Pill-shaped verdict badge."""
    return html.Span(text, style={
        "display": "inline-block",
        "padding": "3px 14px",
        "borderRadius": "20px",
        "background": color,
        "color": "white",
        "fontSize": "11px",
        "fontWeight": 700,
        "fontFamily": FONTS["primary"],
        "letterSpacing": "0.04em",
        "verticalAlign": "middle",
    })


def _chart_card(title, graph, verdict_text, verdict_color, explanation):
    """Card containing title + verdict badge, chart, and explanation."""
    return card([
        html.Div([
            html.Span(title, style={
                **LABEL_STYLE,
                "marginBottom": "0",
                "marginRight": "10px",
                "display": "inline-block",
                "verticalAlign": "middle",
            }),
            _verdict_badge(verdict_text, verdict_color),
        ], style={"marginBottom": "10px"}),
        graph,
        html.Div(explanation, style={
            "fontSize": "11px",
            "color": COLORS["muted"],
            "lineHeight": "1.4",
            "fontFamily": FONTS["primary"],
            "marginTop": "8px",
        }),
    ])


def _score_color(score):
    """Color based on score level."""
    if score >= 60:
        return COLORS["success"]
    if score >= 40:
        return COLORS["warning"]
    return COLORS["coral"]


def _find_column(df, possible_names):
    """Find first matching column name from alternatives."""
    for name in possible_names:
        if name in df.columns:
            return name
    return None


def _get_dates(df):
    """Extract year labels from DataFrame index."""
    if hasattr(df.index, "strftime"):
        return df.index.strftime("%Y").tolist()
    return [str(d)[:4] for d in df.index]


def _metric_tag(lbl, value, color):
    """Colored metric tag for the summary row."""
    return html.Div([
        html.Span(lbl, style={
            "fontSize": "11px", "fontWeight": 500,
            "color": COLORS["muted"], "marginRight": "6px",
        }),
        html.Span(value, style={
            "fontSize": "12px", "fontWeight": 600,
            "color": color,
        }),
    ], style={
        "display": "inline-block", "padding": "4px 12px",
        "background": "#F8FAFB", "borderRadius": "8px",
    })


def _metric_color(value, good_threshold, ok_threshold, higher_is_better=True):
    """Return green/amber/red based on thresholds."""
    if value is None:
        return COLORS["muted"]
    if higher_is_better:
        if value >= good_threshold:
            return COLORS["success"]
        if value >= ok_threshold:
            return COLORS["warning"]
        return COLORS["coral"]
    else:
        if value <= good_threshold:
            return COLORS["success"]
        if value <= ok_threshold:
            return COLORS["warning"]
        return COLORS["coral"]


# =============================================================================
# RENDER
# =============================================================================

def render(stock_data, price_data, all_stocks_df, financials=None):
    ticker = stock_data["ticker"]
    info = stock_data["info"]

    # Use pre-loaded financials if provided, otherwise load inline
    if financials is None:
        import yfinance as yf
        try:
            stock = yf.Ticker(ticker)
            financials = {}
            for key, attr in [("income_stmt", "income_stmt"), ("balance_sheet", "balance_sheet"),
                              ("cashflow", "cashflow"), ("quarterly_income", "quarterly_income_stmt"),
                              ("quarterly_balance", "quarterly_balance_sheet"), ("quarterly_cashflow", "quarterly_cashflow")]:
                data = getattr(stock, attr, None)
                if data is not None and not data.empty:
                    data = data.T.sort_index()
                financials[key] = data
        except Exception:
            financials = {k: None for k in ["income_stmt", "balance_sheet", "cashflow",
                                             "quarterly_income", "quarterly_balance", "quarterly_cashflow"]}

    income_stmt = financials.get("income_stmt")
    balance_sheet = financials.get("balance_sheet")

    children = []

    # =========================================================================
    # SECTION 1: FUNDAMENTAL SCORE (Paper 2)
    # =========================================================================
    try:
        fund_score, fund_details = calculate_fundamental_score_paper2(info, price_data=price_data)
    except Exception:
        fund_score, fund_details = None, {}

    if fund_score is not None:
        # Verdict
        if fund_score >= 65:
            fund_verdict, fund_vcolor = "Strong", COLORS["success"]
        elif fund_score >= 45:
            fund_verdict, fund_vcolor = "Fair", COLORS["warning"]
        else:
            fund_verdict, fund_vcolor = "Weak", COLORS["coral"]

        score_children = [
            html.Div([
                html.Span("FUNDAMENTAL SCORE", style={
                    **LABEL_STYLE,
                    "marginBottom": "0",
                    "marginRight": "10px",
                    "display": "inline-block",
                    "verticalAlign": "middle",
                }),
                _verdict_badge(fund_verdict, fund_vcolor),
            ], style={"marginBottom": "12px"}),
            html.Div([
                html.Span(f"{fund_score:.0f}", style={
                    "fontSize": "32px", "fontWeight": 700,
                    "color": _score_color(fund_score),
                    "fontFamily": FONTS["primary"],
                }),
                html.Span("/100", style={
                    "fontSize": "14px", "fontWeight": 500,
                    "color": COLORS["muted"], "marginLeft": "2px",
                }),
            ], style={"marginBottom": "12px"}),
        ]

        # Progress bars for 5 factors
        pb_pctile = fund_details.get("pb_pctile", 50)
        roe_pctile = fund_details.get("roe_pctile", 50)
        momentum_pctile = fund_details.get("momentum_pctile", fund_details.get("growth_pctile", 50))
        beta_pctile = fund_details.get("beta_pctile", fund_details.get("leverage_pctile", 50))
        mcap_pctile = fund_details.get("market_cap_pctile", 50)

        score_children.append(progress_bar("P/B Percentile", pb_pctile, COLORS["teal"]))
        score_children.append(progress_bar("ROE Percentile", roe_pctile, COLORS["teal"]))
        score_children.append(progress_bar("Momentum Percentile", momentum_pctile, COLORS["teal"]))
        score_children.append(progress_bar("Beta Percentile", beta_pctile, COLORS["teal"]))
        score_children.append(progress_bar("Market Cap Percentile", mcap_pctile, COLORS["teal"]))

        # Interaction bonus note
        interaction_bonus = fund_details.get("interaction_bonus", 0)
        if interaction_bonus != 0:
            score_children.append(html.Div(
                f"Interaction bonus: {interaction_bonus:+.1f} pts",
                style={
                    "fontSize": "11px", "color": COLORS["muted"],
                    "fontFamily": FONTS["primary"], "marginTop": "4px",
                },
            ))

        children.append(card(score_children))
        children.append(spacer())
    else:
        children.append(card([
            label("Fundamental Score"),
            html.Div("Fundamental score not available for this stock.", style={
                "fontSize": "12px", "color": COLORS["muted"],
                "fontFamily": FONTS["primary"],
            }),
        ]))
        children.append(spacer())

    # =========================================================================
    # SECTION 2 & 3: PROFITABILITY + REVENUE GROWTH (side by side)
    # =========================================================================
    prof_dates = _get_dates(income_stmt) if income_stmt is not None and not income_stmt.empty else []

    # --- Profitability ---
    if income_stmt is not None and len(prof_dates) > 0:
        ni_col = _find_column(income_stmt, ["Net Income", "NetIncome", "Net Income Common Stockholders"])
        if ni_col:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            ni_values = (income_stmt[ni_col] / 1e9).tolist()
            fig.add_trace(go.Bar(
                x=prof_dates, y=ni_values, name="Net Income ($B)",
                marker_color=COLORS["teal"],
            ), secondary_y=False)

            roe_val = info.get("returnOnEquity")
            if roe_val is not None:
                roe_pct = roe_val * 100
                fig.add_trace(go.Scatter(
                    x=prof_dates, y=[roe_pct] * len(prof_dates),
                    name=f"ROE ({roe_pct:.1f}%)", mode="lines",
                    line=dict(color=COLORS["coral"], width=2, dash="dash"),
                ), secondary_y=True)

            fig.update_layout(**_chart_layout(250), showlegend=True, bargap=0.3)
            _chart_axes(fig, y_prefix="$")
            fig.update_yaxes(ticksuffix=" B", secondary_y=False, rangemode="tozero")
            fig.update_yaxes(ticksuffix="%", secondary_y=True, showgrid=False)

            # Verdict
            latest_ni = ni_values[-1] if ni_values else 0
            growing = len(ni_values) >= 2 and ni_values[-1] > ni_values[0]
            if latest_ni > 0 and growing:
                prof_verdict, prof_color = "Profitable & Growing", COLORS["success"]
                prof_explain = f"Net income has grown over the period shown, reaching ${ni_values[-1]:.1f}B."
            elif latest_ni > 0:
                prof_verdict, prof_color = "Profitable but Declining", COLORS["warning"]
                prof_explain = f"The company is profitable at ${ni_values[-1]:.1f}B but income has declined over time."
            else:
                prof_verdict, prof_color = "Unprofitable", COLORS["coral"]
                prof_explain = f"Net income is negative at ${ni_values[-1]:.1f}B — the company is currently unprofitable."

            if roe_val is not None:
                assess = "strong" if roe_val > 0.15 else "moderate" if roe_val > 0.10 else "weak"
                prof_explain += f" ROE of {roe_val * 100:.1f}% is {assess}."

            prof_card = _chart_card(
                "PROFITABILITY",
                dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "250px"}),
                prof_verdict, prof_color, prof_explain,
            )
        else:
            prof_card = card([
                label("Profitability"),
                html.Div("Net income data not available.", style={
                    "fontSize": "12px", "color": COLORS["muted"],
                }),
            ])
    else:
        prof_card = card([
            label("Profitability"),
            html.Div("Profitability data not available.", style={
                "fontSize": "12px", "color": COLORS["muted"],
            }),
        ])

    # --- Revenue Growth ---
    if income_stmt is not None and len(prof_dates) > 0:
        rev_col = _find_column(income_stmt, ["Total Revenue", "TotalRevenue", "Revenue"])
        if rev_col:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            rev_values = (income_stmt[rev_col] / 1e9).tolist()
            fig.add_trace(go.Bar(
                x=prof_dates, y=rev_values, name="Revenue ($B)",
                marker_color=COLORS["teal"],
            ), secondary_y=False)

            raw_rev = income_stmt[rev_col].tolist()
            growth_rates = [None]
            for i in range(1, len(raw_rev)):
                if raw_rev[i - 1] and raw_rev[i - 1] != 0:
                    growth_rates.append(((raw_rev[i] - raw_rev[i - 1]) / abs(raw_rev[i - 1])) * 100)
                else:
                    growth_rates.append(None)

            fig.add_trace(go.Scatter(
                x=prof_dates, y=growth_rates, name="YoY Growth %",
                mode="lines+markers", line=dict(color=COLORS["coral"], width=2),
                marker=dict(size=6, color=COLORS["coral"]), connectgaps=True,
            ), secondary_y=True)

            fig.update_layout(**_chart_layout(250), showlegend=True, bargap=0.3)
            _chart_axes(fig, y_prefix="$")
            fig.update_yaxes(ticksuffix=" B", secondary_y=False, rangemode="tozero")
            fig.update_yaxes(ticksuffix="%", secondary_y=True, showgrid=False)

            # Verdict
            rev_growth = info.get("revenueGrowth")
            if rev_growth is not None:
                rg_pct = rev_growth * 100
                if rev_growth > 0.15:
                    growth_verdict, growth_color = "Strong Growth", COLORS["success"]
                    growth_explain = f"Revenue is growing at {rg_pct:.1f}% year-over-year — well above market average."
                elif rev_growth > 0.05:
                    growth_verdict, growth_color = "Moderate Growth", COLORS["teal"]
                    growth_explain = f"Revenue is growing at {rg_pct:.1f}% year-over-year — a steady pace."
                elif rev_growth > 0:
                    growth_verdict, growth_color = "Slow Growth", COLORS["warning"]
                    growth_explain = f"Revenue is growing at just {rg_pct:.1f}% year-over-year — below average."
                else:
                    growth_verdict, growth_color = "Declining", COLORS["coral"]
                    growth_explain = f"Revenue is declining at {rg_pct:.1f}% year-over-year."
            else:
                growth_verdict, growth_color = "No Data", COLORS["muted"]
                growth_explain = "Revenue growth rate not available from source."

            growth_card = _chart_card(
                "REVENUE GROWTH",
                dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "250px"}),
                growth_verdict, growth_color, growth_explain,
            )
        else:
            growth_card = card([
                label("Revenue Growth"),
                html.Div("Revenue data not available.", style={
                    "fontSize": "12px", "color": COLORS["muted"],
                }),
            ])
    else:
        growth_card = card([
            label("Revenue Growth"),
            html.Div("Revenue data not available.", style={
                "fontSize": "12px", "color": COLORS["muted"],
            }),
        ])

    children.append(html.Div([
        html.Div(prof_card, style={"flex": 1, "minWidth": 0}),
        html.Div(growth_card, style={"flex": 1, "minWidth": 0}),
    ], style={"display": "flex", "gap": "12px", "alignItems": "stretch"}))

    children.append(spacer())

    # =========================================================================
    # SECTION 4 & 5: LEVERAGE + VALUATION (side by side)
    # =========================================================================

    # --- Leverage ---
    lev_dates = _get_dates(balance_sheet) if balance_sheet is not None and not balance_sheet.empty else []

    if balance_sheet is not None and len(lev_dates) > 0:
        debt_col = _find_column(balance_sheet, ["Total Debt", "TotalDebt", "Long Term Debt", "LongTermDebt"])
        equity_col = _find_column(balance_sheet, [
            "Total Equity Gross Minority Interest", "Stockholders Equity",
            "StockholdersEquity", "Total Stockholders Equity", "Total Equity",
        ])

        if debt_col or equity_col:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            if debt_col:
                fig.add_trace(go.Bar(
                    x=lev_dates, y=(balance_sheet[debt_col] / 1e9).tolist(),
                    name="Debt ($B)", marker_color=COLORS["coral"], width=0.35, offset=-0.2,
                ), secondary_y=False)
            if equity_col:
                fig.add_trace(go.Bar(
                    x=lev_dates, y=(balance_sheet[equity_col] / 1e9).tolist(),
                    name="Equity ($B)", marker_color=COLORS["teal"], width=0.35, offset=0.2,
                ), secondary_y=False)

            de_val = info.get("debtToEquity")
            if de_val is not None:
                fig.add_trace(go.Scatter(
                    x=lev_dates, y=[de_val] * len(lev_dates),
                    name=f"D/E ({de_val:.1f})", mode="lines",
                    line=dict(color=COLORS["coral"], width=2, dash="dash"),
                ), secondary_y=True)

            fig.update_layout(**_chart_layout(250), showlegend=True, barmode="group", bargap=0.3)
            _chart_axes(fig, y_prefix="$")
            fig.update_yaxes(ticksuffix=" B", secondary_y=False, rangemode="tozero")
            fig.update_yaxes(secondary_y=True, showgrid=False)

            # Verdict
            if de_val is not None:
                if de_val < 50:
                    lev_verdict, lev_color = "Conservative", COLORS["success"]
                    lev_explain = f"Debt-to-Equity of {de_val:.0f} is low — the company relies more on equity than debt financing."
                elif de_val < 100:
                    lev_verdict, lev_color = "Moderate", COLORS["warning"]
                    lev_explain = f"Debt-to-Equity of {de_val:.0f} is moderate — a balanced mix of debt and equity financing."
                else:
                    lev_verdict, lev_color = "High Leverage", COLORS["coral"]
                    lev_explain = f"Debt-to-Equity of {de_val:.0f} is high — the company carries significant debt relative to equity."
            else:
                lev_verdict, lev_color = "No Data", COLORS["muted"]
                lev_explain = "Debt-to-Equity ratio not available."

            lev_card = _chart_card(
                "LEVERAGE",
                dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "250px"}),
                lev_verdict, lev_color, lev_explain,
            )
        else:
            lev_card = card([
                label("Leverage"),
                html.Div("Balance sheet data not available.", style={
                    "fontSize": "12px", "color": COLORS["muted"],
                }),
            ])
    else:
        lev_card = card([
            label("Leverage"),
            html.Div("Balance sheet data not available.", style={
                "fontSize": "12px", "color": COLORS["muted"],
            }),
        ])

    # --- Valuation (P/E History) ---
    eps = info.get("trailingEps")
    if eps is not None and eps > 0 and not price_data.empty:
        val_data = price_data.tail(504).copy()
        hist_pe = val_data["Close"] / eps
        val_dates = val_data["Date"].tolist()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=val_dates, y=hist_pe.tolist(), name="P/E Ratio", mode="lines",
            line=dict(color=COLORS["teal"], width=2),
            fill="tozeroy", fillcolor="rgba(0,151,167,0.08)",
        ))
        avg_pe = float(hist_pe.mean())
        fig.add_hline(
            y=avg_pe, line=dict(color=COLORS["coral"], dash="dash", width=1.5),
            annotation_text=f"Avg: {avg_pe:.1f}", annotation_position="right",
        )

        fig.update_layout(**_chart_layout(250), showlegend=False)
        _chart_axes(fig)

        current_pe = float(price_data["Close"].iloc[-1]) / eps

        # Verdict
        if current_pe < avg_pe * 0.8:
            val_verdict, val_color = "Undervalued", COLORS["success"]
            val_explain = f"Current P/E of {current_pe:.1f} is well below the {avg_pe:.1f} average — the stock may be undervalued relative to its history."
        elif current_pe > avg_pe * 1.2:
            val_verdict, val_color = "Premium", COLORS["coral"]
            val_explain = f"Current P/E of {current_pe:.1f} is above the {avg_pe:.1f} average — the stock is trading at a premium to its historical valuation."
        else:
            val_verdict, val_color = "Fair Value", COLORS["teal"]
            val_explain = f"Current P/E of {current_pe:.1f} is close to the {avg_pe:.1f} average — the stock appears fairly valued."

        val_card = _chart_card(
            "VALUATION (P/E HISTORY)",
            dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "250px"}),
            val_verdict, val_color, val_explain,
        )
    else:
        val_card = card([
            label("Valuation"),
            html.Div("P/E data not available (requires positive trailing EPS).", style={
                "fontSize": "12px", "color": COLORS["muted"],
            }),
        ])

    children.append(html.Div([
        html.Div(lev_card, style={"flex": 1, "minWidth": 0}),
        html.Div(val_card, style={"flex": 1, "minWidth": 0}),
    ], style={"display": "flex", "gap": "12px", "alignItems": "stretch"}))

    children.append(spacer())

    # =========================================================================
    # SECTION 6: KEY METRICS SUMMARY
    # =========================================================================
    pe = info.get("trailingPE")
    peg = info.get("pegRatio")
    pb = info.get("priceToBook")
    roe = info.get("returnOnEquity")
    profit_margin = info.get("profitMargins")
    rev_growth = info.get("revenueGrowth")
    beta = info.get("beta")

    def _fmt(val, suffix="", mult=1, decimals=1):
        if val is None:
            return "N/A"
        return f"{val * mult:.{decimals}f}{suffix}"

    row1 = []
    # P/E
    pe_color = _metric_color(pe, 20, 30, higher_is_better=False) if pe else COLORS["muted"]
    row1.append(_metric_tag("P/E", _fmt(pe, "", 1, 1), pe_color))
    # PEG
    peg_color = _metric_color(peg, 1.0, 2.0, higher_is_better=False) if peg else COLORS["muted"]
    row1.append(_metric_tag("PEG", _fmt(peg, "", 1, 2), peg_color))
    # P/B
    pb_color = _metric_color(pb, 3.0, 5.0, higher_is_better=False) if pb else COLORS["muted"]
    row1.append(_metric_tag("P/B", _fmt(pb, "", 1, 2), pb_color))

    row2 = []
    # ROE
    roe_color = _metric_color(roe, 0.15, 0.10) if roe else COLORS["muted"]
    row2.append(_metric_tag("ROE", _fmt(roe, "%", 100, 1), roe_color))
    # Profit Margin
    pm_color = _metric_color(profit_margin, 0.15, 0.05) if profit_margin else COLORS["muted"]
    row2.append(_metric_tag("Profit Margin", _fmt(profit_margin, "%", 100, 1), pm_color))
    # Revenue Growth
    rg_color = _metric_color(rev_growth, 0.15, 0.05) if rev_growth else COLORS["muted"]
    row2.append(_metric_tag("Rev Growth", _fmt(rev_growth, "%", 100, 1), rg_color))
    # Beta
    beta_color = _metric_color(beta, 1.0, 1.5, higher_is_better=False) if beta else COLORS["muted"]
    row2.append(_metric_tag("Beta", _fmt(beta, "", 1, 2), beta_color))

    children.append(card([
        label("Key Metrics"),
        html.Div(row1, style={
            "display": "flex", "gap": "10px", "flexWrap": "wrap", "marginBottom": "8px",
        }),
        html.Div(row2, style={
            "display": "flex", "gap": "10px", "flexWrap": "wrap",
        }),
    ]))

    return html.Div(children)
