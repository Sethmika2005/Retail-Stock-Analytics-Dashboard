# Fundamentals tab — financial health charts with verdicts

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from models import calculate_piotroski_fscore
from styles import (
    FONT, TEAL, CORAL, SUCCESS, WARNING, MUTED, TEXT, TEXT_SEC, BORDER, CARD_BG, SIDEBAR_BG,
    SHADOW, GRID,
    badge_html, chart_layout, chart_axes, chart_card_bg, chart_card_header,
    explanation_html, progress_bar, metric_tag, metric_color,
)

CARD_STYLE = (
    f"background:{CARD_BG};border-radius:14px;padding:20px;"
    f"box-shadow:{SHADOW};border:1px solid {BORDER};margin-bottom:12px;"
)
LABEL_CSS = (
    f"font-size:11px;text-transform:uppercase;font-weight:600;"
    f"letter-spacing:0.06em;color:{TEXT_SEC};font-family:{FONT};margin:0;"
)


def _find_column(df, names):
    for n in names:
        if n in df.columns: return n
    return None


def _get_dates(df):
    # extract year labels from the dataframe index for chart x-axis
    # hasattr check because index might be DatetimeIndex or plain strings
    if hasattr(df.index, "strftime"):
        return df.index.strftime("%Y").tolist()
    return [str(d)[:4] for d in df.index]


def _fmt(val, suffix="", mult=1, decimals=1):
    if val is None: return "N/A"
    return f"{val * mult:.{decimals}f}{suffix}"


def _label(text):
    return f'<span style="{LABEL_CSS};display:inline-block;vertical-align:middle;margin-right:10px;">{text}</span>'


CARD_OPEN = f'<div style="{CARD_STYLE}">'
CARD_CLOSE = '</div>'


def _not_available(title, msg):
    st.markdown(f'{CARD_OPEN}{_label(title)}'
                f'<div style="font-size:12px;color:{MUTED};font-family:{FONT};">{msg}</div>'
                f'{CARD_CLOSE}', unsafe_allow_html=True)


def render(selected, info, financials, all_stocks_df, price_data,
           load_sector_peers_metrics, load_peer_fscores=None):

    income_stmt = financials.get("income_stmt")
    balance_sheet = financials.get("balance_sheet")

    # Drop years where all key financial columns are NaN — these are incomplete rows
    # that would cause misleading gaps in the charts
    if income_stmt is not None and not income_stmt.empty:
        # list comprehension: find columns whose names match any of our target names
        key = [c for c in income_stmt.columns if any(k in c for k in
               ["Net Income", "NetIncome", "Total Revenue", "TotalRevenue", "Revenue"])]
        income_stmt = income_stmt.dropna(subset=key, how="all") if key else income_stmt.dropna(how="all")  # drop rows where all key financial columns are empty
    if balance_sheet is not None and not balance_sheet.empty:
        key = [c for c in balance_sheet.columns if any(k in c for k in
               ["Total Debt", "TotalDebt", "Total Assets", "TotalAssets",
                "Stockholders Equity", "StockholdersEquity"])]
        balance_sheet = balance_sheet.dropna(subset=key, how="all") if key else balance_sheet.dropna(how="all")  # same idea for balance sheet — drop empty rows

    # -- Piotroski F-Score --
    cashflow = financials.get("cashflow")
    fscore, fscore_details = calculate_piotroski_fscore(income_stmt, balance_sheet, cashflow)

    if fscore is not None:
        if fscore >= 7: fund_verdict, fund_vcolor = "Strong", SUCCESS
        elif fscore >= 4: fund_verdict, fund_vcolor = "Fair", WARNING
        else: fund_verdict, fund_vcolor = "Weak", CORAL

        html = CARD_OPEN
        html += f'<div style="margin-bottom:12px;">{_label("PIOTROSKI F-SCORE")}{badge_html(fund_verdict, fund_vcolor)}</div>'
        html += (f'<div style="margin-bottom:12px;">'
                 f'<span style="font-size:32px;font-weight:700;color:{metric_color(fscore / 9 * 100, 60, 40)};font-family:{FONT};">{fscore}</span>'
                 f'<span style="font-size:14px;font-weight:500;color:{MUTED};margin-left:2px;font-family:{FONT};">/9</span></div>')

        prof = fscore_details.get("profitability", 0)
        lev = fscore_details.get("leverage_liquidity", 0)
        eff = fscore_details.get("efficiency", 0)
        html += progress_bar("Profitability", prof / 4 * 100, TEAL)
        html += progress_bar("Leverage & Liquidity", lev / 3 * 100, TEAL)
        html += progress_bar("Efficiency", eff / 2 * 100, TEAL)

        def _test(key, label):
            d = fscore_details.get(key, {})
            passed = d.get("score", 0) == 1
            bg = "rgba(16,185,129,0.1)" if passed else "rgba(255,107,107,0.1)"
            color = SUCCESS if passed else CORAL
            return (f'<span style="display:inline-flex;align-items:center;gap:4px;'
                    f'padding:3px 8px;border-radius:6px;background:{bg};'
                    f'font-size:11px;font-weight:500;color:{color};font-family:{FONT};">● {label}</span>')

        html += (f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;">'
                 f'{_test("roa_positive", "ROA Positive")}'
                 f'{_test("cfo_positive", "Cash Flow Positive")}'
                 f'{_test("roa_increasing", "ROA Increasing")}'
                 f'{_test("cfo_gt_net_income", "CFO > Net Income")}'
                 f'{_test("debt_decreasing", "Debt Decreasing")}'
                 f'{_test("current_ratio_increasing", "Current Ratio Up")}'
                 f'{_test("no_dilution", "No Dilution")}'
                 f'{_test("gross_margin_increasing", "Gross Margin Up")}'
                 f'{_test("asset_turnover_increasing", "Asset Turnover Up")}'
                 f'</div>')
        html += CARD_CLOSE
        st.markdown(html, unsafe_allow_html=True)
    else:
        _not_available("PIOTROSKI F-SCORE", "Financial statement data not available.")

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    # -- Profitability + Revenue Growth side by side --
    prof_dates = _get_dates(income_stmt) if income_stmt is not None and not income_stmt.empty else []
    col_prof, col_growth = st.columns(2)

    with col_prof:
        if prof_dates:
            ni_col = _find_column(income_stmt, ["Net Income", "NetIncome", "Net Income Common Stockholders"])
            if ni_col:
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                # divide by 1 billion for readability on chart ($B)
                ni_vals = (income_stmt[ni_col] / 1e9).tolist()
                fig.add_trace(go.Bar(x=prof_dates, y=ni_vals, name="Net Income ($B)",
                                      marker_color=TEAL), secondary_y=False)
                roe_val = info.get("returnOnEquity")
                if roe_val is not None:
                    fig.add_trace(go.Scatter(x=prof_dates, y=[roe_val * 100] * len(prof_dates),
                                              name=f"ROE ({roe_val * 100:.1f}%)", mode="lines",
                                              line=dict(color=CORAL, width=2, dash="dash")), secondary_y=True)

                latest = ni_vals[-1] if ni_vals else 0
                growing = len(ni_vals) >= 2 and ni_vals[-1] > ni_vals[0]
                if latest > 0 and growing:
                    v, vc = "Profitable & Growing", SUCCESS
                    ex = f"Net income has grown, reaching ${ni_vals[-1]:.1f}B."
                elif latest > 0:
                    v, vc = "Profitable but Declining", WARNING
                    ex = f"Profitable at ${ni_vals[-1]:.1f}B but income declining."
                else:
                    v, vc = "Unprofitable", CORAL
                    ex = f"Net income negative at ${ni_vals[-1]:.1f}B."
                if roe_val is not None:
                    assess = "strong" if roe_val > 0.15 else "moderate" if roe_val > 0.10 else "weak"
                    ex += f" ROE of {roe_val * 100:.1f}% is {assess}."

                fig.update_layout(**chart_layout(250), showlegend=True, bargap=0.3)
                chart_axes(fig, y_prefix="$", x_category=True)
                fig.update_yaxes(ticksuffix=" B", secondary_y=False, rangemode="tozero")
                fig.update_yaxes(ticksuffix="%", secondary_y=True, showgrid=False)

                st.markdown(chart_card_bg(350), unsafe_allow_html=True)
                st.markdown(chart_card_header("PROFITABILITY", v, vc), unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.markdown(explanation_html(ex), unsafe_allow_html=True)
            else:
                _not_available("PROFITABILITY", "Net income data not available.")
        else:
            _not_available("PROFITABILITY", "Profitability data not available.")

    with col_growth:
        if income_stmt is not None and prof_dates:
            rev_col = _find_column(income_stmt, ["Total Revenue", "TotalRevenue", "Revenue"])
            if rev_col:
                fig = go.Figure()
                rev_vals = (income_stmt[rev_col] / 1e9).tolist()
                fig.add_trace(go.Bar(x=prof_dates, y=rev_vals, name="Revenue ($B)", marker_color=TEAL))

                rev_growth = info.get("revenueGrowth")
                if rev_growth is not None:
                    rev_growth_pct = rev_growth * 100
                    if rev_growth > 0.15: verdict, verdict_color, explanation = "Strong Growth", SUCCESS, f"Revenue growing at {rev_growth_pct:.1f}% YoY."
                    elif rev_growth > 0.05: verdict, verdict_color, explanation = "Moderate Growth", TEAL, f"Revenue growing at {rev_growth_pct:.1f}% YoY."
                    elif rev_growth > 0: verdict, verdict_color, explanation = "Slow Growth", WARNING, f"Revenue growing at {rev_growth_pct:.1f}% YoY."
                    else: verdict, verdict_color, explanation = "Declining", CORAL, f"Revenue declining at {rev_growth_pct:.1f}% YoY."
                else:
                    verdict, verdict_color, explanation = "No Data", MUTED, "Revenue growth rate not available."

                fig.update_layout(**chart_layout(250), showlegend=True, bargap=0.3)
                chart_axes(fig, y_prefix="$", x_category=True)
                fig.update_yaxes(ticksuffix=" B", rangemode="tozero")

                st.markdown(chart_card_bg(350), unsafe_allow_html=True)
                st.markdown(chart_card_header("REVENUE GROWTH", verdict, verdict_color), unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.markdown(explanation_html(explanation), unsafe_allow_html=True)
            else:
                _not_available("REVENUE GROWTH", "Revenue data not available.")
        else:
            _not_available("REVENUE GROWTH", "Revenue data not available.")

    st.markdown('<div style="height:30px;"></div>', unsafe_allow_html=True)

    # -- Leverage + Valuation side by side --
    lev_dates = _get_dates(balance_sheet) if balance_sheet is not None and not balance_sheet.empty else []
    col_lev, col_val = st.columns(2)

    with col_lev:
        if balance_sheet is not None and lev_dates:
            debt_col = _find_column(balance_sheet, ["Total Debt", "TotalDebt", "Long Term Debt", "LongTermDebt"])
            equity_col = _find_column(balance_sheet, [
                "Total Equity Gross Minority Interest", "Stockholders Equity",
                "StockholdersEquity", "Total Stockholders Equity", "Total Equity"])

            if debt_col or equity_col:
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                if debt_col:
                    fig.add_trace(go.Bar(x=lev_dates, y=(balance_sheet[debt_col] / 1e9).tolist(),
                                          name="Debt ($B)", marker_color=CORAL, width=0.35, offset=-0.2), secondary_y=False)
                if equity_col:
                    fig.add_trace(go.Bar(x=lev_dates, y=(balance_sheet[equity_col] / 1e9).tolist(),
                                          name="Equity ($B)", marker_color=TEAL, width=0.35, offset=0.2), secondary_y=False)

                debt_to_equity = info.get("debtToEquity")
                if debt_to_equity is not None:
                    fig.add_trace(go.Scatter(x=lev_dates, y=[debt_to_equity] * len(lev_dates),
                                              name=f"D/E ({debt_to_equity:.1f})", mode="lines",
                                              line=dict(color=CORAL, width=2, dash="dash")), secondary_y=True)

                if debt_to_equity is not None:
                    if debt_to_equity < 50: verdict, verdict_color, explanation = "Conservative", SUCCESS, f"D/E of {debt_to_equity:.0f} is low."
                    elif debt_to_equity < 100: verdict, verdict_color, explanation = "Moderate", WARNING, f"D/E of {debt_to_equity:.0f} is moderate."
                    else: verdict, verdict_color, explanation = "High Leverage", CORAL, f"D/E of {debt_to_equity:.0f} is high."
                else:
                    verdict, verdict_color, explanation = "No Data", MUTED, "D/E ratio not available."

                fig.update_layout(**chart_layout(250), showlegend=True, barmode="group", bargap=0.3)
                chart_axes(fig, y_prefix="$", x_category=True)
                fig.update_yaxes(ticksuffix=" B", secondary_y=False, rangemode="tozero")
                fig.update_yaxes(secondary_y=True, showgrid=False)

                st.markdown(chart_card_bg(350), unsafe_allow_html=True)
                st.markdown(chart_card_header("LEVERAGE", verdict, verdict_color), unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.markdown(explanation_html(explanation), unsafe_allow_html=True)
            else:
                _not_available("LEVERAGE", "Balance sheet data not available.")
        else:
            _not_available("LEVERAGE", "Balance sheet data not available.")

    with col_val:
        eps = info.get("trailingEps")
        if eps is not None and eps > 0 and not price_data.empty:
            # tail(504) = ~2 years of trading days for P/E history
            val_data = price_data.tail(504).copy()
            # P/E = price / earnings per share
            hist_pe = val_data["Close"] / eps

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=val_data["Date"].tolist(), y=hist_pe.tolist(), name="P/E Ratio",
                                      mode="lines", line=dict(color=TEAL, width=2),
                                      fill="tozeroy", fillcolor="rgba(0,151,167,0.08)"))
            avg_pe = float(hist_pe.mean())
            fig.add_hline(y=avg_pe, line=dict(color=CORAL, dash="dash", width=1.5),
                          annotation_text=f"Avg: {avg_pe:.1f}", annotation_position="right")

            current_pe = float(price_data["Close"].iloc[-1]) / eps
            if current_pe < avg_pe * 0.8:
                v, vc = "Undervalued", SUCCESS
                ex = f"P/E of {current_pe:.1f} well below avg {avg_pe:.1f}."
            elif current_pe > avg_pe * 1.2:
                v, vc = "Premium", CORAL
                ex = f"P/E of {current_pe:.1f} above avg {avg_pe:.1f}."
            else:
                v, vc = "Fair Value", TEAL
                ex = f"P/E of {current_pe:.1f} close to avg {avg_pe:.1f}."

            fig.update_layout(**chart_layout(250), showlegend=False)
            chart_axes(fig)
            fig.update_xaxes(type=None)

            st.markdown(chart_card_bg(350), unsafe_allow_html=True)
            st.markdown(chart_card_header("VALUATION (P/E HISTORY)", v, vc), unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown(explanation_html(ex), unsafe_allow_html=True)
        else:
            _not_available("VALUATION", "P/E data not available (requires positive trailing EPS).")

    st.markdown('<div style="height:30px;"></div>', unsafe_allow_html=True)

    # -- Key Metrics Summary --
    pe = info.get("trailingPE"); peg = info.get("pegRatio"); pb = info.get("priceToBook")
    roe = info.get("returnOnEquity"); pm = info.get("profitMargins")
    rg = info.get("revenueGrowth"); beta = info.get("beta")

    row1 = (metric_tag("P/E", _fmt(pe), metric_color(pe, 20, 30, False) if pe else MUTED)
            + metric_tag("PEG", _fmt(peg, "", 1, 2), metric_color(peg, 1.0, 2.0, False) if peg else MUTED)
            + metric_tag("P/B", _fmt(pb, "", 1, 2), metric_color(pb, 3.0, 5.0, False) if pb else MUTED))
    row2 = (metric_tag("ROE", _fmt(roe, "%", 100), metric_color(roe, 0.15, 0.10) if roe else MUTED)
            + metric_tag("Profit Margin", _fmt(pm, "%", 100), metric_color(pm, 0.15, 0.05) if pm else MUTED)
            + metric_tag("Rev Growth", _fmt(rg, "%", 100), metric_color(rg, 0.15, 0.05) if rg else MUTED)
            + metric_tag("Beta", _fmt(beta, "", 1, 2), metric_color(beta, 1.0, 1.5, False) if beta else MUTED))

    st.markdown(
        f'{CARD_OPEN}<div style="{LABEL_CSS};margin-bottom:10px;">KEY METRICS</div>'
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px;">{row1}</div>'
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;">{row2}</div>{CARD_CLOSE}',
        unsafe_allow_html=True)

    # -- Sector Peer Comparison --
    st.markdown('<div style="height:30px;"></div>', unsafe_allow_html=True)

    stock_sector = info.get("sector", "")
    if not stock_sector:
        match = all_stocks_df[all_stocks_df["ticker"] == selected]
        if not match.empty: stock_sector = match.iloc[0]["sector"]

    if not stock_sector:
        st.caption("Sector information not available.")
        return

    sector_peers = all_stocks_df[
        (all_stocks_df["sector"] == stock_sector) & (all_stocks_df["ticker"] != selected)
    ]["ticker"].tolist()[:8]

    if len(sector_peers) < 3:
        st.caption(f"Not enough sector peers ({len(sector_peers)} in {stock_sector}).")
        return

    with st.spinner("Loading peer data..."):
        peers_df = load_sector_peers_metrics(tuple(sector_peers))
        peer_fscores_df = None
        if load_peer_fscores:
            peer_fscores_df = load_peer_fscores(tuple(sector_peers))

    stock_pe = info.get("trailingPE"); stock_roe = info.get("returnOnEquity")
    stock_margin = info.get("profitMargins"); stock_rg = info.get("revenueGrowth")
    stock_de = info.get("debtToEquity")

    # median is more robust than mean for financial metrics (resistant to outliers)
    peer_median_pe = peers_df["pe"].dropna().median()          # ignore peers with missing P/E
    peer_median_roe = peers_df["roe"].dropna().median()        # ignore peers with missing ROE
    peer_median_margin = peers_df["net_margin"].dropna().median()  # ignore peers with missing net margin
    peer_median_rg = peers_df["rev_growth"].dropna().median()  # ignore peers with missing revenue growth
    peer_median_de = peers_df["de"].dropna().median()          # ignore peers with missing debt/equity

    stock_fs = fscore
    peer_median_fs = peer_median_prof = peer_median_lev = peer_median_eff = None
    if peer_fscores_df is not None and not peer_fscores_df.empty:
        def _med(col):
            vals = peer_fscores_df[col].dropna()  # strip out peers with no F-score before computing median
            return float(vals.median()) if len(vals) > 0 else None
        peer_median_fs, peer_median_prof, peer_median_lev, peer_median_eff = _med("fscore"), _med("profitability"), _med("leverage"), _med("efficiency")

    comparisons = []
    metrics_cmp = [
        ("P/E Ratio", stock_pe, peer_median_pe, False), ("ROE", stock_roe, peer_median_roe, True),
        ("Net Margin", stock_margin, peer_median_margin, True), ("Rev Growth", stock_rg, peer_median_rg, True),
        ("Debt/Equity", stock_de, peer_median_de, False), ("F-Score", stock_fs, peer_median_fs, True)]

    # count how many metrics the stock beats its peers on
    wins = 0
    for label, stock_val, peer_median, higher_is_better in metrics_cmp:
        if stock_val is not None and peer_median is not None and not pd.isna(peer_median):  # only count the metric if both stock & peer value exist
            # for ROE, higher wins; for P/E, lower wins
            better = (stock_val >= peer_median) if higher_is_better else (stock_val <= peer_median)
            if better: wins += 1
            comparisons.append((label, stock_val, peer_median, higher_is_better, better))
        else:
            comparisons.append((label, stock_val, peer_median, higher_is_better, None))

    if wins >= 5: peer_verdict_text, peer_verdict_color = "Above Peers", SUCCESS
    elif wins >= 3: peer_verdict_text, peer_verdict_color = "In Line", TEAL
    else: peer_verdict_text, peer_verdict_color = "Below Peers", CORAL

    def _pfmt(val, is_pct=False, is_score=False):
        if val is None: return "\u2014"  # show em-dash "—" for missing values
        if is_score: return f"{val:.0f}/9"
        if is_pct: return f"{val * 100:.1f}%"
        return f"{val:.1f}"

    header_cells = stock_cells = peer_cells = diff_cells = ""
    for label, stock_val, peer_median, higher_is_better, better in comparisons:
        is_pct = label in ("ROE", "Net Margin", "Rev Growth")
        is_score = label == "F-Score"
        cell_color = SUCCESS if better else CORAL if better is False else MUTED

        header_cells += (f'<div style="flex:1;text-align:center;"><div style="font-size:11px;font-weight:600;'
                         f'color:{MUTED};text-transform:uppercase;letter-spacing:0.04em;font-family:{FONT};">{label}</div></div>')
        stock_cells += (f'<div style="flex:1;text-align:center;"><div style="font-size:15px;font-weight:600;'
                        f'color:{cell_color};font-family:{FONT};">{_pfmt(stock_val, is_pct, is_score)}</div></div>')
        peer_cells += (f'<div style="flex:1;text-align:center;"><div style="font-size:15px;font-weight:500;'
                       f'color:{TEXT_SEC};font-family:{FONT};">{_pfmt(peer_median, is_pct, is_score)}</div></div>')

        if stock_val is not None and peer_median is not None and not pd.isna(stock_val) and not pd.isna(peer_median):  # only compute diff if both values are valid
            diff = stock_val - peer_median
            if is_score: diff_text = f"{'+' if diff >= 0 else ''}{int(round(diff))}"
            elif is_pct: diff_text = f"{'+' if diff >= 0 else ''}{diff * 100:.1f}pp"
            elif peer_median != 0: diff_text = f"{'+' if diff / abs(peer_median) * 100 >= 0 else ''}{diff / abs(peer_median) * 100:.0f}%"
            else: diff_text = f"{'+' if diff >= 0 else ''}{diff:.1f}"
            diff_color = SUCCESS if better else CORAL if better is False else MUTED
        else:
            diff_text, diff_color = "\u2014", MUTED

        diff_cells += (f'<div style="flex:1;text-align:center;"><div style="font-size:12px;font-weight:600;'
                       f'color:{diff_color};font-family:{FONT};">{diff_text}</div></div>')

    # F-Score breakdown vs peers
    fscore_bk = ""
    if stock_fs is not None and fscore_details and peer_median_prof is not None:
        score_profit = fscore_details.get("profitability", 0)
        score_leverage = fscore_details.get("leverage_liquidity", 0)
        score_efficiency = fscore_details.get("efficiency", 0)
        cats = ""
        for category_name, stock_val, max_score, peer_median_score in [
            ("Profitability", score_profit, 4, peer_median_prof),
            ("Leverage", score_leverage, 3, peer_median_lev),
            ("Efficiency", score_efficiency, 2, peer_median_eff),
        ]:
            score_beats_peer = stock_val >= peer_median_score if peer_median_score is not None else None
            score_color = SUCCESS if score_beats_peer else CORAL if score_beats_peer is False else MUTED
            cats += (f'<div style="flex:1;text-align:center;">'
                     f'<div style="font-size:10px;font-weight:600;color:{MUTED};text-transform:uppercase;'
                     f'letter-spacing:0.04em;font-family:{FONT};margin-bottom:4px;">{category_name}</div>'
                     f'<div style="font-family:{FONT};">'
                     f'<span style="font-size:14px;font-weight:600;color:{score_color};">{stock_val}/{max_score}</span>'
                     f'<span style="font-size:11px;color:{MUTED};margin:0 4px;">vs</span>'
                     f'<span style="font-size:14px;font-weight:500;color:{TEXT_SEC};">{peer_median_score:.0f}/{max_score}</span>'
                     f'</div></div>')
        fscore_bk = (f'<div style="border-top:1px solid {BORDER};padding-top:12px;margin-top:4px;">'
                     f'<div style="font-size:10px;font-weight:600;color:{MUTED};text-transform:uppercase;'
                     f'letter-spacing:0.06em;font-family:{FONT};margin-bottom:8px;">F-Score Breakdown vs Peers</div>'
                     f'<div style="display:flex;gap:4px;">{cats}</div></div>')

    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:14px;
                box-shadow:{SHADOW};padding:20px;">
        <div style="margin-bottom:14px;">
            <span style="{LABEL_CSS};display:inline-block;vertical-align:middle;margin-right:10px;">SECTOR PEER COMPARISON</span>
            {badge_html(peer_verdict_text, peer_verdict_color)}
        </div>
        <div style="display:flex;gap:4px;margin-bottom:6px;margin-left:55px;">{header_cells}</div>
        <div style="display:flex;gap:4px;align-items:center;margin-bottom:10px;">
            <div style="width:50px;flex-shrink:0;font-size:11px;font-weight:600;color:{TEAL};font-family:{FONT};">{selected}</div>
            <div style="display:flex;gap:4px;flex:1;">{stock_cells}</div>
        </div>
        <div style="display:flex;gap:4px;align-items:center;margin-bottom:10px;">
            <div style="width:50px;flex-shrink:0;font-size:11px;font-weight:600;color:{MUTED};font-family:{FONT};">Peers (Avg)</div>
            <div style="display:flex;gap:4px;flex:1;">{peer_cells}</div>
        </div>
        <div style="display:flex;gap:4px;align-items:center;margin-bottom:12px;
                    border-top:1px solid {BORDER};padding-top:8px;">
            <div style="width:50px;flex-shrink:0;font-size:11px;font-weight:600;color:{MUTED};font-family:{FONT};">Diff</div>
            <div style="display:flex;gap:4px;flex:1;">{diff_cells}</div>
        </div>
        {fscore_bk}
        <div style="font-size:11px;color:{MUTED};line-height:1.4;font-family:{FONT};margin-top:12px;">
            Compared against {len(sector_peers)} peers in {stock_sector}.
            {selected} scores above sector median on {wins} of {len(comparisons)} key metrics.
        </div>
    </div>
    """, unsafe_allow_html=True)
