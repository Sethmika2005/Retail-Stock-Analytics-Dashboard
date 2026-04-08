# =============================================================================
# FUNDAMENTALS TAB - "The Financial Health Story" — Charts with verdicts
# =============================================================================

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from models import calculate_piotroski_fscore

# =============================================================================
# DESIGN TOKENS
# =============================================================================

FONT = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
BG = "#F4F7F9"
CARD_BG = "#FFFFFF"
BORDER = "#E8EDF2"
TEAL = "#0097A7"
CORAL = "#FF6B6B"
HEADING = "#0F172A"
TEXT_PRIMARY = "#1E293B"
TEXT_SECONDARY = "#64748B"
MUTED = "#94A3B8"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"
GRID_COLOR = "#F1F5F9"
SHADOW_SM = "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)"
TRACK_COLOR = "#F1F5F9"

CARD_STYLE = (
    "background:{bg};border-radius:14px;padding:20px;"
    "box-shadow:0 1px 3px rgba(0,0,0,0.04),0 1px 2px rgba(0,0,0,0.02);"
    "border:1px solid {border};margin-bottom:12px;"
).format(bg=CARD_BG, border=BORDER)

LABEL_CSS = (
    "font-size:11px;text-transform:uppercase;font-weight:600;"
    "letter-spacing:0.06em;color:{c};font-family:{f};margin:0;"
).format(c=TEXT_SECONDARY, f=FONT)


# =============================================================================
# SHARED HELPERS
# =============================================================================

def _chart_layout(height=250):
    """Standard plotly layout matching dashboard chart style."""
    return dict(
        height=height,
        margin=dict(l=10, r=10, t=10, b=30),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
        font=dict(family=FONT, size=11, color=TEXT_SECONDARY),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
            font=dict(size=11, color=TEXT_PRIMARY),
        ),
    )


def _chart_axes(fig, y_prefix=""):
    """Apply standard axis styling."""
    fig.update_xaxes(
        showgrid=False, showline=True, linecolor=BORDER,
        tickfont=dict(size=10, color=MUTED),
        type="category",
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=GRID_COLOR,
        tickfont=dict(size=10, color=MUTED),
        tickprefix=y_prefix,
    )


def _verdict_html(text, color):
    """Pill-shaped verdict badge as HTML."""
    return (
        f'<span style="display:inline-block;padding:3px 14px;border-radius:20px;'
        f'background:{color};color:white;font-size:11px;font-weight:700;'
        f"font-family:{FONT};letter-spacing:0.04em;\">{text}</span>"
    )


def _progress_bar_html(label, value, color=TEAL):
    """Progress bar matching Dash progress_bar component."""
    pct = max(0, min(100, float(value)))
    return (
        f'<div style="margin-bottom:12px;">'
        f'  <div style="display:flex;justify-content:space-between;margin-bottom:4px;">'
        f'    <span style="font-family:{FONT};font-size:12px;color:{TEXT_SECONDARY};font-weight:450;">{label}</span>'
        f'    <span style="font-weight:600;color:{TEXT_PRIMARY};font-family:{FONT};font-size:12px;">{value:.0f}</span>'
        f'  </div>'
        f'  <div style="background:{TRACK_COLOR};border-radius:6px;height:6px;overflow:hidden;">'
        f'    <div style="width:{pct}%;height:100%;background:{color};border-radius:6px;"></div>'
        f'  </div>'
        f'</div>'
    )


def _score_color(score):
    """Color based on score level."""
    if score >= 60:
        return SUCCESS
    if score >= 40:
        return WARNING
    return CORAL


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


def _metric_color(value, good_threshold, ok_threshold, higher_is_better=True):
    """Return green/amber/red based on thresholds."""
    if value is None:
        return MUTED
    if higher_is_better:
        if value >= good_threshold:
            return SUCCESS
        if value >= ok_threshold:
            return WARNING
        return CORAL
    else:
        if value <= good_threshold:
            return SUCCESS
        if value <= ok_threshold:
            return WARNING
        return CORAL


def _metric_tag_html(lbl, value, color):
    """Colored metric tag for the summary row."""
    return (
        f'<span style="display:inline-block;padding:4px 12px;background:#F8FAFB;border-radius:8px;margin-right:10px;margin-bottom:6px;">'
        f'<span style="font-size:11px;font-weight:500;color:{MUTED};margin-right:6px;font-family:{FONT};">{lbl}</span>'
        f'<span style="font-size:12px;font-weight:600;color:{color};font-family:{FONT};">{value}</span>'
        f'</span>'
    )


def _fmt(val, suffix="", mult=1, decimals=1):
    if val is None:
        return "N/A"
    return f"{val * mult:.{decimals}f}{suffix}"


def _card_open():
    return f'<div style="{CARD_STYLE}">'


def _card_close():
    return '</div>'


def _label_html(text):
    return f'<span style="{LABEL_CSS};display:inline-block;vertical-align:middle;margin-right:10px;">{text}</span>'


def _explanation_html(text):
    return (
        f'<div style="font-size:11px;color:{MUTED};line-height:1.4;'
        f'font-family:{FONT};padding:0px 16px 12px 16px;margin-top:-12px;">{text}</div>'
    )


def _chart_card_bg(height=350):
    """Render a white rounded background box that content will sit on top of."""
    return (
        f'<div style="background:#FFFFFF;border:1px solid {BORDER};border-radius:14px;'
        f'box-shadow:{SHADOW_SM};min-height:{height}px;margin-bottom:-{height - 10}px;"></div>'
    )


def _chart_card_header_html(title, verdict_text, verdict_color):
    """Header HTML for chart card (title + verdict badge)."""
    return (
        f'<div style="padding:8px 16px 4px 16px;">'
        f'{_label_html(title)}'
        f'{_verdict_html(verdict_text, verdict_color)}'
        f'</div>'
    )


def _chart_card_start(title, verdict_text, verdict_color):
    """Open a chart card with label + verdict badge header."""
    return (
        f'{_card_open()}'
        f'<div style="margin-bottom:10px;">'
        f'{_label_html(title)}'
        f'{_verdict_html(verdict_text, verdict_color)}'
        f'</div>'
    )


def _chart_card_end(explanation):
    """Close chart card with explanation text."""
    return f'{_explanation_html(explanation)}{_card_close()}'


def _not_available_card(title, message):
    """Render a card showing data not available."""
    st.markdown(
        f'{_card_open()}'
        f'{_label_html(title)}'
        f'<div style="font-size:12px;color:{MUTED};font-family:{FONT};">{message}</div>'
        f'{_card_close()}',
        unsafe_allow_html=True,
    )


# =============================================================================
# RENDER
# =============================================================================

def render(selected, info, financials, all_stocks_df, price_data, load_sector_peers_metrics, load_peer_fscores=None):
    income_stmt = financials.get("income_stmt")
    balance_sheet = financials.get("balance_sheet")

    # Drop rows where key financial columns are missing (avoids empty years on x-axis)
    if income_stmt is not None and not income_stmt.empty:
        key_cols = [c for c in income_stmt.columns if any(k in c for k in
                    ["Net Income", "NetIncome", "Total Revenue", "TotalRevenue", "Revenue"])]
        if key_cols:
            income_stmt = income_stmt.dropna(subset=key_cols, how="all")
        else:
            income_stmt = income_stmt.dropna(how="all")
    if balance_sheet is not None and not balance_sheet.empty:
        key_bs_cols = [c for c in balance_sheet.columns if any(k in c for k in
                       ["Total Debt", "TotalDebt", "Total Assets", "TotalAssets",
                        "Stockholders Equity", "StockholdersEquity"])]
        if key_bs_cols:
            balance_sheet = balance_sheet.dropna(subset=key_bs_cols, how="all")
        else:
            balance_sheet = balance_sheet.dropna(how="all")

    # =========================================================================
    # SECTION 1: PIOTROSKI F-SCORE (Piotroski, 2000)
    # =========================================================================
    cashflow = financials.get("cashflow")
    try:
        fscore, fscore_details = calculate_piotroski_fscore(income_stmt, balance_sheet, cashflow)
    except Exception:
        fscore, fscore_details = None, {}

    if fscore is not None:
        if fscore >= 7:
            fund_verdict, fund_vcolor = "Strong", SUCCESS
        elif fscore >= 4:
            fund_verdict, fund_vcolor = "Fair", WARNING
        else:
            fund_verdict, fund_vcolor = "Weak", CORAL

        score_html = _card_open()
        score_html += (
            f'<div style="margin-bottom:12px;">'
            f'{_label_html("PIOTROSKI F-SCORE")}'
            f'{_verdict_html(fund_verdict, fund_vcolor)}'
            f'</div>'
        )
        score_html += (
            f'<div style="margin-bottom:12px;">'
            f'<span style="font-size:32px;font-weight:700;color:{_score_color(fscore / 9 * 100)};font-family:{FONT};">'
            f'{fscore}</span>'
            f'<span style="font-size:14px;font-weight:500;color:{MUTED};margin-left:2px;font-family:{FONT};">/9</span>'
            f'</div>'
        )

        # Category progress bars (out of max per category)
        prof = fscore_details.get("profitability", 0)
        lev = fscore_details.get("leverage_liquidity", 0)
        eff = fscore_details.get("efficiency", 0)

        score_html += _progress_bar_html("Profitability", prof / 4 * 100, TEAL)
        score_html += _progress_bar_html("Leverage & Liquidity", lev / 3 * 100, TEAL)
        score_html += _progress_bar_html("Efficiency", eff / 2 * 100, TEAL)

        # Individual test results
        def _test_badge(detail_key, label):
            d = fscore_details.get(detail_key, {})
            passed = d.get("score", 0) == 1
            bg = "rgba(16,185,129,0.1)" if passed else "rgba(255,107,107,0.1)"
            color = SUCCESS if passed else CORAL
            dot = "●"
            return (
                f'<span style="display:inline-flex;align-items:center;gap:4px;'
                f'padding:3px 8px;border-radius:6px;background:{bg};'
                f'font-size:11px;font-weight:500;color:{color};font-family:{FONT};">'
                f'{dot} {label}</span>'
            )

        tests_html = (
            f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;">'
            f'{_test_badge("roa_positive", "ROA Positive")}'
            f'{_test_badge("cfo_positive", "Cash Flow Positive")}'
            f'{_test_badge("roa_increasing", "ROA Increasing")}'
            f'{_test_badge("cfo_gt_net_income", "CFO > Net Income")}'
            f'{_test_badge("debt_decreasing", "Debt Decreasing")}'
            f'{_test_badge("current_ratio_increasing", "Current Ratio Up")}'
            f'{_test_badge("no_dilution", "No Dilution")}'
            f'{_test_badge("gross_margin_increasing", "Gross Margin Up")}'
            f'{_test_badge("asset_turnover_increasing", "Asset Turnover Up")}'
            f'</div>'
        )
        score_html += tests_html

        score_html += _card_close()
        st.markdown(score_html, unsafe_allow_html=True)
    else:
        _not_available_card("PIOTROSKI F-SCORE", "Financial statement data not available for this stock.")

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    # =========================================================================
    # SECTION 2: PROFITABILITY + REVENUE GROWTH (side by side)
    # =========================================================================
    prof_dates = _get_dates(income_stmt) if income_stmt is not None and not income_stmt.empty else []

    col_prof, col_growth = st.columns(2)

    # --- Profitability ---
    with col_prof:
        if income_stmt is not None and len(prof_dates) > 0:
            ni_col = _find_column(income_stmt, ["Net Income", "NetIncome", "Net Income Common Stockholders"])
            if ni_col:
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                ni_values = (income_stmt[ni_col] / 1e9).tolist()
                fig.add_trace(go.Bar(
                    x=prof_dates, y=ni_values, name="Net Income ($B)",
                    marker_color=TEAL,
                ), secondary_y=False)

                roe_val = info.get("returnOnEquity")
                if roe_val is not None:
                    roe_pct = roe_val * 100
                    fig.add_trace(go.Scatter(
                        x=prof_dates, y=[roe_pct] * len(prof_dates),
                        name=f"ROE ({roe_pct:.1f}%)", mode="lines",
                        line=dict(color=CORAL, width=2, dash="dash"),
                    ), secondary_y=True)

                # Verdict
                latest_ni = ni_values[-1] if ni_values else 0
                growing = len(ni_values) >= 2 and ni_values[-1] > ni_values[0]
                if latest_ni > 0 and growing:
                    prof_verdict, prof_color = "Profitable & Growing", SUCCESS
                    prof_explain = f"Net income has grown over the period shown, reaching ${ni_values[-1]:.1f}B."
                elif latest_ni > 0:
                    prof_verdict, prof_color = "Profitable but Declining", WARNING
                    prof_explain = f"The company is profitable at ${ni_values[-1]:.1f}B but income has declined over time."
                else:
                    prof_verdict, prof_color = "Unprofitable", CORAL
                    prof_explain = f"Net income is negative at ${ni_values[-1]:.1f}B — the company is currently unprofitable."

                if roe_val is not None:
                    assess = "strong" if roe_val > 0.15 else "moderate" if roe_val > 0.10 else "weak"
                    prof_explain += f" ROE of {roe_val * 100:.1f}% is {assess}."

                fig.update_layout(**_chart_layout(250), showlegend=True, bargap=0.3)
                _chart_axes(fig, y_prefix="$")
                fig.update_yaxes(ticksuffix=" B", secondary_y=False, rangemode="tozero")
                fig.update_yaxes(ticksuffix="%", secondary_y=True, showgrid=False)

                st.markdown(_chart_card_bg(350), unsafe_allow_html=True)
                st.markdown(_chart_card_header_html("PROFITABILITY", prof_verdict, prof_color), unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.markdown(_explanation_html(prof_explain), unsafe_allow_html=True)
            else:
                _not_available_card("PROFITABILITY", "Net income data not available.")
        else:
            _not_available_card("PROFITABILITY", "Profitability data not available.")

    # --- Revenue Growth ---
    with col_growth:
        if income_stmt is not None and len(prof_dates) > 0:
            rev_col = _find_column(income_stmt, ["Total Revenue", "TotalRevenue", "Revenue"])
            if rev_col:
                fig = go.Figure()
                rev_values = (income_stmt[rev_col] / 1e9).tolist()
                fig.add_trace(go.Bar(
                    x=prof_dates, y=rev_values, name="Revenue ($B)",
                    marker_color=TEAL,
                ))

                # Verdict
                rev_growth = info.get("revenueGrowth")
                if rev_growth is not None:
                    rg_pct = rev_growth * 100
                    if rev_growth > 0.15:
                        growth_verdict, growth_color = "Strong Growth", SUCCESS
                        growth_explain = f"Revenue is growing at {rg_pct:.1f}% year-over-year — well above market average."
                    elif rev_growth > 0.05:
                        growth_verdict, growth_color = "Moderate Growth", TEAL
                        growth_explain = f"Revenue is growing at {rg_pct:.1f}% year-over-year — a steady pace."
                    elif rev_growth > 0:
                        growth_verdict, growth_color = "Slow Growth", WARNING
                        growth_explain = f"Revenue is growing at just {rg_pct:.1f}% year-over-year — below average."
                    else:
                        growth_verdict, growth_color = "Declining", CORAL
                        growth_explain = f"Revenue is declining at {rg_pct:.1f}% year-over-year."
                else:
                    growth_verdict, growth_color = "No Data", MUTED
                    growth_explain = "Revenue growth rate not available from source."

                fig.update_layout(**_chart_layout(250), showlegend=True, bargap=0.3)
                _chart_axes(fig, y_prefix="$")
                fig.update_yaxes(ticksuffix=" B", rangemode="tozero")

                st.markdown(_chart_card_bg(350), unsafe_allow_html=True)
                st.markdown(_chart_card_header_html("REVENUE GROWTH", growth_verdict, growth_color), unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.markdown(_explanation_html(growth_explain), unsafe_allow_html=True)
            else:
                _not_available_card("REVENUE GROWTH", "Revenue data not available.")
        else:
            _not_available_card("REVENUE GROWTH", "Revenue data not available.")

    st.markdown('<div style="height:30px;"></div>', unsafe_allow_html=True)

    # =========================================================================
    # SECTION 3: LEVERAGE + VALUATION (side by side)
    # =========================================================================
    lev_dates = _get_dates(balance_sheet) if balance_sheet is not None and not balance_sheet.empty else []

    col_lev, col_val = st.columns(2)

    # --- Leverage ---
    with col_lev:
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
                        name="Debt ($B)", marker_color=CORAL, width=0.35, offset=-0.2,
                    ), secondary_y=False)
                if equity_col:
                    fig.add_trace(go.Bar(
                        x=lev_dates, y=(balance_sheet[equity_col] / 1e9).tolist(),
                        name="Equity ($B)", marker_color=TEAL, width=0.35, offset=0.2,
                    ), secondary_y=False)

                de_val = info.get("debtToEquity")
                if de_val is not None:
                    fig.add_trace(go.Scatter(
                        x=lev_dates, y=[de_val] * len(lev_dates),
                        name=f"D/E ({de_val:.1f})", mode="lines",
                        line=dict(color=CORAL, width=2, dash="dash"),
                    ), secondary_y=True)

                # Verdict
                if de_val is not None:
                    if de_val < 50:
                        lev_verdict, lev_color = "Conservative", SUCCESS
                        lev_explain = f"Debt-to-Equity of {de_val:.0f} is low — the company relies more on equity than debt financing."
                    elif de_val < 100:
                        lev_verdict, lev_color = "Moderate", WARNING
                        lev_explain = f"Debt-to-Equity of {de_val:.0f} is moderate — a balanced mix of debt and equity financing."
                    else:
                        lev_verdict, lev_color = "High Leverage", CORAL
                        lev_explain = f"Debt-to-Equity of {de_val:.0f} is high — the company carries significant debt relative to equity."
                else:
                    lev_verdict, lev_color = "No Data", MUTED
                    lev_explain = "Debt-to-Equity ratio not available."

                fig.update_layout(**_chart_layout(250), showlegend=True, barmode="group", bargap=0.3)
                _chart_axes(fig, y_prefix="$")
                fig.update_yaxes(ticksuffix=" B", secondary_y=False, rangemode="tozero")
                fig.update_yaxes(secondary_y=True, showgrid=False)

                st.markdown(_chart_card_bg(350), unsafe_allow_html=True)
                st.markdown(_chart_card_header_html("LEVERAGE", lev_verdict, lev_color), unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.markdown(_explanation_html(lev_explain), unsafe_allow_html=True)
            else:
                _not_available_card("LEVERAGE", "Balance sheet data not available.")
        else:
            _not_available_card("LEVERAGE", "Balance sheet data not available.")

    # --- Valuation (P/E History) ---
    with col_val:
        eps = info.get("trailingEps")
        if eps is not None and eps > 0 and not price_data.empty:
            val_data = price_data.tail(504).copy()
            hist_pe = val_data["Close"] / eps
            val_dates = val_data["Date"].tolist()

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=val_dates, y=hist_pe.tolist(), name="P/E Ratio", mode="lines",
                line=dict(color=TEAL, width=2),
                fill="tozeroy", fillcolor="rgba(0,151,167,0.08)",
            ))
            avg_pe = float(hist_pe.mean())
            fig.add_hline(
                y=avg_pe, line=dict(color=CORAL, dash="dash", width=1.5),
                annotation_text=f"Avg: {avg_pe:.1f}", annotation_position="right",
            )

            current_pe = float(price_data["Close"].iloc[-1]) / eps

            # Verdict
            if current_pe < avg_pe * 0.8:
                val_verdict, val_color = "Undervalued", SUCCESS
                val_explain = f"Current P/E of {current_pe:.1f} is well below the {avg_pe:.1f} average — the stock may be undervalued relative to its history."
            elif current_pe > avg_pe * 1.2:
                val_verdict, val_color = "Premium", CORAL
                val_explain = f"Current P/E of {current_pe:.1f} is above the {avg_pe:.1f} average — the stock is trading at a premium to its historical valuation."
            else:
                val_verdict, val_color = "Fair Value", TEAL
                val_explain = f"Current P/E of {current_pe:.1f} is close to the {avg_pe:.1f} average — the stock appears fairly valued."

            fig.update_layout(**_chart_layout(250), showlegend=False)
            _chart_axes(fig)
            fig.update_xaxes(type=None)

            st.markdown(_chart_card_bg(350), unsafe_allow_html=True)
            st.markdown(_chart_card_header_html("VALUATION (P/E HISTORY)", val_verdict, val_color), unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown(_explanation_html(val_explain), unsafe_allow_html=True)
        else:
            _not_available_card("VALUATION", "P/E data not available (requires positive trailing EPS).")

    st.markdown('<div style="height:30px;"></div>', unsafe_allow_html=True)

    # =========================================================================
    # SECTION 4: KEY METRICS SUMMARY
    # =========================================================================
    pe = info.get("trailingPE")
    peg = info.get("pegRatio")
    pb = info.get("priceToBook")
    roe = info.get("returnOnEquity")
    profit_margin = info.get("profitMargins")
    rev_growth_val = info.get("revenueGrowth")
    beta = info.get("beta")

    # Row 1: P/E, PEG, P/B
    pe_color = _metric_color(pe, 20, 30, higher_is_better=False) if pe else MUTED
    peg_color = _metric_color(peg, 1.0, 2.0, higher_is_better=False) if peg else MUTED
    pb_color = _metric_color(pb, 3.0, 5.0, higher_is_better=False) if pb else MUTED

    row1 = ""
    row1 += _metric_tag_html("P/E", _fmt(pe, "", 1, 1), pe_color)
    row1 += _metric_tag_html("PEG", _fmt(peg, "", 1, 2), peg_color)
    row1 += _metric_tag_html("P/B", _fmt(pb, "", 1, 2), pb_color)

    # Row 2: ROE, Profit Margin, Rev Growth, Beta
    roe_color = _metric_color(roe, 0.15, 0.10) if roe else MUTED
    pm_color = _metric_color(profit_margin, 0.15, 0.05) if profit_margin else MUTED
    rg_color = _metric_color(rev_growth_val, 0.15, 0.05) if rev_growth_val else MUTED
    beta_color = _metric_color(beta, 1.0, 1.5, higher_is_better=False) if beta else MUTED

    row2 = ""
    row2 += _metric_tag_html("ROE", _fmt(roe, "%", 100, 1), roe_color)
    row2 += _metric_tag_html("Profit Margin", _fmt(profit_margin, "%", 100, 1), pm_color)
    row2 += _metric_tag_html("Rev Growth", _fmt(rev_growth_val, "%", 100, 1), rg_color)
    row2 += _metric_tag_html("Beta", _fmt(beta, "", 1, 2), beta_color)

    metrics_html = (
        f'{_card_open()}'
        f'<div style="{LABEL_CSS};margin-bottom:10px;">KEY METRICS</div>'
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px;">{row1}</div>'
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;">{row2}</div>'
        f'{_card_close()}'
    )
    st.markdown(metrics_html, unsafe_allow_html=True)

    # =========================================================================
    # SECTION 5: SECTOR PEER COMPARISON
    # =========================================================================
    st.markdown('<div style="height:30px;"></div>', unsafe_allow_html=True)

    # Resolve sector
    stock_sector = info.get("sector", "")
    if not stock_sector:
        sector_match = all_stocks_df[all_stocks_df["ticker"] == selected]
        if not sector_match.empty:
            stock_sector = sector_match.iloc[0]["sector"]

    if not stock_sector:
        st.caption("Sector information not available for this stock.")
    else:
        # Get same-sector peers (max 8, excluding selected)
        sector_peers = all_stocks_df[
            (all_stocks_df["sector"] == stock_sector) & (all_stocks_df["ticker"] != selected)
        ]["ticker"].tolist()[:8]

        if len(sector_peers) < 3:
            st.caption(f"Not enough sector peers for comparison (found {len(sector_peers)} in {stock_sector}).")
        else:
            with st.spinner("Loading peer data..."):
                peers_df = load_sector_peers_metrics(tuple(sector_peers))
                # Load peer F-Scores
                peer_fscores_df = None
                if load_peer_fscores is not None:
                    try:
                        peer_fscores_df = load_peer_fscores(tuple(sector_peers))
                    except Exception:
                        peer_fscores_df = None

            # Selected stock's values
            stock_pe = info.get("trailingPE")
            stock_roe = info.get("returnOnEquity")
            stock_margin = info.get("profitMargins")
            stock_rev_growth = info.get("revenueGrowth")
            stock_de = info.get("debtToEquity")

            # Sector medians
            median_pe = peers_df["pe"].dropna().median()
            median_roe = peers_df["roe"].dropna().median()
            median_margin = peers_df["net_margin"].dropna().median()
            median_rev_growth = peers_df["rev_growth"].dropna().median()
            median_de = peers_df["de"].dropna().median()

            # F-Score peer median
            stock_fscore_val = fscore  # from Section 1
            median_fscore = None
            median_prof = None
            median_lev = None
            median_eff = None
            if peer_fscores_df is not None and not peer_fscores_df.empty:
                _fs = peer_fscores_df["fscore"].dropna()
                median_fscore = float(_fs.median()) if len(_fs) > 0 else None
                _pr = peer_fscores_df["profitability"].dropna()
                median_prof = float(_pr.median()) if len(_pr) > 0 else None
                _lv = peer_fscores_df["leverage"].dropna()
                median_lev = float(_lv.median()) if len(_lv) > 0 else None
                _ef = peer_fscores_df["efficiency"].dropna()
                median_eff = float(_ef.median()) if len(_ef) > 0 else None

            # Compare: count how many metrics the stock beats
            comparisons = []
            metrics_compare = [
                ("P/E Ratio", stock_pe, median_pe, False),       # lower is better
                ("ROE", stock_roe, median_roe, True),            # higher is better
                ("Net Margin", stock_margin, median_margin, True),
                ("Rev Growth", stock_rev_growth, median_rev_growth, True),
                ("Debt/Equity", stock_de, median_de, False),     # lower is better
                ("F-Score", stock_fscore_val, median_fscore, True),  # higher is better
            ]

            wins = 0
            for label, stock_val, peer_val, higher_better in metrics_compare:
                if stock_val is not None and peer_val is not None and not pd.isna(peer_val):
                    if higher_better:
                        better = stock_val >= peer_val
                    else:
                        better = stock_val <= peer_val
                    if better:
                        wins += 1
                    comparisons.append((label, stock_val, peer_val, higher_better, better))
                else:
                    comparisons.append((label, stock_val, peer_val, higher_better, None))

            # Verdict
            if wins >= 5:
                peer_verdict, peer_vcolor = "Above Peers", SUCCESS
            elif wins >= 3:
                peer_verdict, peer_vcolor = "In Line", TEAL
            else:
                peer_verdict, peer_vcolor = "Below Peers", CORAL

            # Format helpers
            def _peer_fmt(val, is_pct=False, is_score=False):
                if val is None or (isinstance(val, float) and pd.isna(val)):
                    return "\u2014"
                if is_score:
                    return f"{val:.0f}/9"
                if is_pct:
                    return f"{val * 100:.1f}%"
                return f"{val:.1f}"

            # Build comparison card HTML
            header_cells = ""
            stock_cells = ""
            peer_cells = ""
            diff_cells = ""

            for label, stock_val, peer_val, higher_better, is_better in comparisons:
                is_pct = label in ("ROE", "Net Margin", "Rev Growth")
                is_score = label == "F-Score"

                # Color the stock value based on comparison
                if is_better is True:
                    val_color = SUCCESS
                elif is_better is False:
                    val_color = CORAL
                else:
                    val_color = MUTED

                header_cells += (
                    f'<div style="flex:1;text-align:center;">'
                    f'<div style="font-size:11px;font-weight:600;color:{MUTED};'
                    f'text-transform:uppercase;letter-spacing:0.04em;'
                    f'font-family:{FONT};">{label}</div></div>'
                )
                stock_cells += (
                    f'<div style="flex:1;text-align:center;">'
                    f'<div style="font-size:15px;font-weight:600;color:{val_color};'
                    f'font-family:{FONT};">{_peer_fmt(stock_val, is_pct, is_score)}</div></div>'
                )
                peer_cells += (
                    f'<div style="flex:1;text-align:center;">'
                    f'<div style="font-size:15px;font-weight:500;color:{TEXT_SECONDARY};'
                    f'font-family:{FONT};">{_peer_fmt(peer_val, is_pct, is_score)}</div></div>'
                )

                # Difference row
                if stock_val is not None and peer_val is not None and not pd.isna(stock_val) and not pd.isna(peer_val):
                    diff = stock_val - peer_val
                    if is_score:
                        diff_txt = f"{'+' if diff >= 0 else ''}{diff:.0f}"
                    elif is_pct:
                        diff_txt = f"{'+' if diff >= 0 else ''}{diff * 100:.1f}pp"
                    elif peer_val != 0:
                        diff_pct = (diff / abs(peer_val)) * 100
                        diff_txt = f"{'+' if diff_pct >= 0 else ''}{diff_pct:.0f}%"
                    else:
                        diff_txt = f"{'+' if diff >= 0 else ''}{diff:.1f}"
                    diff_color = SUCCESS if is_better else CORAL if is_better is False else MUTED
                else:
                    diff_txt = "\u2014"
                    diff_color = MUTED

                diff_cells += (
                    f'<div style="flex:1;text-align:center;">'
                    f'<div style="font-size:12px;font-weight:600;color:{diff_color};'
                    f'font-family:{FONT};">{diff_txt}</div></div>'
                )

            # F-Score category breakdown HTML
            fscore_breakdown_html = ""
            if (stock_fscore_val is not None and fscore_details
                    and median_prof is not None):
                stock_prof = fscore_details.get("profitability", 0)
                stock_lev = fscore_details.get("leverage_liquidity", 0)
                stock_eff = fscore_details.get("efficiency", 0)

                categories = [
                    ("Profitability", stock_prof, 4, median_prof),
                    ("Leverage", stock_lev, 3, median_lev),
                    ("Efficiency", stock_eff, 2, median_eff),
                ]

                cat_cells = ""
                for cat_name, s_val, max_val, p_med in categories:
                    s_better = s_val >= p_med if p_med is not None else None
                    s_color = SUCCESS if s_better else CORAL if s_better is False else MUTED
                    p_color = TEXT_SECONDARY
                    cat_cells += (
                        f'<div style="flex:1;text-align:center;">'
                        f'<div style="font-size:10px;font-weight:600;color:{MUTED};'
                        f'text-transform:uppercase;letter-spacing:0.04em;'
                        f'font-family:{FONT};margin-bottom:4px;">{cat_name}</div>'
                        f'<div style="font-family:{FONT};">'
                        f'<span style="font-size:14px;font-weight:600;color:{s_color};">'
                        f'{s_val}/{max_val}</span>'
                        f'<span style="font-size:11px;color:{MUTED};margin:0 4px;">vs</span>'
                        f'<span style="font-size:14px;font-weight:500;color:{p_color};">'
                        f'{p_med:.0f}/{max_val}</span>'
                        f'</div></div>'
                    )

                fscore_breakdown_html = (
                    f'<div style="border-top:1px solid {BORDER};padding-top:12px;margin-top:4px;">'
                    f'<div style="font-size:10px;font-weight:600;color:{MUTED};'
                    f'text-transform:uppercase;letter-spacing:0.06em;'
                    f'font-family:{FONT};margin-bottom:8px;">F-Score Breakdown vs Peers</div>'
                    f'<div style="display:flex;gap:4px;">{cat_cells}</div>'
                    f'</div>'
                )

            peer_card_html = f"""
            <div style="background:#FFFFFF;border:1px solid {BORDER};border-radius:14px;
                        box-shadow:{SHADOW_SM};padding:20px;">
                <div style="margin-bottom:14px;">
                    <span style="{LABEL_CSS};display:inline-block;vertical-align:middle;
                                 margin-right:10px;">SECTOR PEER COMPARISON</span>
                    <span style="display:inline-block;padding:3px 14px;border-radius:20px;
                                 background:{peer_vcolor};color:white;font-size:11px;font-weight:700;
                                 font-family:{FONT};letter-spacing:0.04em;
                                 vertical-align:middle;">{peer_verdict}</span>
                </div>
                <div style="display:flex;gap:4px;margin-bottom:6px;margin-left:55px;">{header_cells}</div>
                <div style="display:flex;gap:4px;align-items:center;margin-bottom:10px;">
                    <div style="width:50px;flex-shrink:0;font-size:11px;font-weight:600;color:{TEAL};
                                font-family:{FONT};">{selected}</div>
                    <div style="display:flex;gap:4px;flex:1;">{stock_cells}</div>
                </div>
                <div style="display:flex;gap:4px;align-items:center;margin-bottom:10px;">
                    <div style="width:50px;flex-shrink:0;font-size:11px;font-weight:600;color:{MUTED};
                                font-family:{FONT};">Peers (Avg)</div>
                    <div style="display:flex;gap:4px;flex:1;">{peer_cells}</div>
                </div>
                <div style="display:flex;gap:4px;align-items:center;margin-bottom:12px;
                            border-top:1px solid {BORDER};padding-top:8px;">
                    <div style="width:50px;flex-shrink:0;font-size:11px;font-weight:600;color:{MUTED};
                                font-family:{FONT};">Diff</div>
                    <div style="display:flex;gap:4px;flex:1;">{diff_cells}</div>
                </div>
                {fscore_breakdown_html}
                <div style="font-size:11px;color:{MUTED};line-height:1.4;font-family:{FONT};margin-top:12px;">
                    Compared against {len(sector_peers)} peers in {stock_sector}.
                    {selected} scores above sector median on {wins} of {len(comparisons)} key metrics.
                </div>
            </div>
            """
            st.markdown(peer_card_html, unsafe_allow_html=True)
