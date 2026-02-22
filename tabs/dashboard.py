# =============================================================================
# DASHBOARD TAB - At-a-Glance Executive Briefing
# =============================================================================

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from components import get_status_color
from models import classify_headline_sentiment, generate_bull_bear_case

# Shared styles
CARD = (
    "background:#FFFFFF;border:1px solid #D0E8EA;border-radius:12px;"
    "padding:22px 24px;box-shadow:0 2px 6px rgba(0,151,167,0.08);"
)
LABEL = (
    "font-family:Source Sans Pro,Arial,sans-serif;font-size:11px;font-weight:600;"
    "color:#5A7D82;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:14px;"
)
SNAPPY = (
    "font-family:Source Sans Pro,Arial,sans-serif;font-size:13px;"
    "color:#5A7D82;line-height:1.5;margin-top:10px;"
)


# ---- sparkline SVG builder ----

def _build_sparkline_svg(prices, dates=None, width=460, height=120, color="#0097A7"):
    """Build an inline SVG sparkline with Y-axis price labels and X-axis date labels."""
    if not prices or len(prices) < 2:
        return ""

    lo, hi = min(prices), max(prices)
    rng = hi - lo if hi != lo else 1
    label_font = "font-family:Source Sans Pro,Arial,sans-serif;font-size:10px;fill:#5A7D82;"

    # Layout: left margin for Y labels, bottom margin for X labels
    ml, mr, mt, mb = 48, 8, 6, 20  # margins
    cw = width - ml - mr   # chart area width
    ch = height - mt - mb   # chart area height

    n = len(prices)
    points = []
    for i, p in enumerate(prices):
        x = ml + (i / (n - 1)) * cw
        y = mt + (1 - (p - lo) / rng) * ch
        points.append(f"{x:.1f},{y:.1f}")
    polyline = " ".join(points)

    # Gradient fill
    first_y = mt + (1 - (prices[0] - lo) / rng) * ch
    fill_path = f"M{ml},{first_y:.1f} "
    fill_path += " ".join(
        f"L{ml + (i / (n - 1)) * cw:.1f},{mt + (1 - (p - lo) / rng) * ch:.1f}"
        for i, p in enumerate(prices)
    )
    fill_path += f" L{ml + cw},{mt + ch} L{ml},{mt + ch} Z"

    # Y-axis: high, mid, low labels + grid lines
    mid = (lo + hi) / 2
    y_labels_html = ""
    for val in [hi, mid, lo]:
        y_pos = mt + (1 - (val - lo) / rng) * ch
        y_labels_html += (
            f'<text x="{ml - 6}" y="{y_pos + 3:.1f}" text-anchor="end" style="{label_font}">${val:.0f}</text>'
            f'<line x1="{ml}" y1="{y_pos:.1f}" x2="{ml + cw}" y2="{y_pos:.1f}" stroke="#D0E8EA" stroke-width="0.5"/>'
        )

    # X-axis: first, middle, last date labels
    x_labels_html = ""
    if dates and len(dates) >= 2:
        x_baseline = mt + ch + 14
        indices = [0, n // 2, n - 1]
        for idx in indices:
            x_pos = ml + (idx / (n - 1)) * cw
            d = dates[idx]
            # Format date — handle both string and datetime
            if hasattr(d, 'strftime'):
                d_str = d.strftime("%b %d")
            else:
                d_str = str(d)[:6]
            anchor = "start" if idx == 0 else ("end" if idx == n - 1 else "middle")
            x_labels_html += f'<text x="{x_pos:.1f}" y="{x_baseline}" text-anchor="{anchor}" style="{label_font}">{d_str}</text>'

    return (
        f'<svg viewBox="0 0 {width} {height}" style="width:100%;height:{height}px;" xmlns="http://www.w3.org/2000/svg">'
        f'<defs><linearGradient id="sparkFill" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0.15"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0.01"/>'
        f'</linearGradient></defs>'
        f'{y_labels_html}'
        f'{x_labels_html}'
        f'<path d="{fill_path}" fill="url(#sparkFill)"/>'
        f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        f'</svg>'
    )


# ---- snappy one-liners ----

def _analysis_snippet(rec, confidence, paper1_details, selected_strategy, tech_score, rsi_value):
    if selected_strategy == "Volume+RSI" and paper1_details:
        ct = paper1_details.get("crossover_type", "none")
        if ct == "golden_cross":
            return f"Bullish EMA crossover {'confirmed' if paper1_details.get('atv_confirmed') else 'unconfirmed'} by volume — {confidence}% confidence."
        if ct == "death_cross":
            return f"Bearish EMA crossover {'confirmed' if paper1_details.get('atv_confirmed') else 'unconfirmed'} by volume — {confidence}% confidence."
    if rec == "BUY":
        return f"Technicals score {tech_score}/100 with RSI at {rsi_value:.0f} — conditions favour entry."
    if rec == "SELL":
        return f"Technicals score {tech_score}/100 with RSI at {rsi_value:.0f} — signals point to exit."
    return f"Technicals score {tech_score}/100 with RSI at {rsi_value:.0f} — no clear directional edge."


def _trend_snippet(price_data):
    """Dynamic one-liner for the trend chart."""
    current = price_data["Close"].iloc[-1]
    sma50 = price_data["SMA50"].iloc[-1] if "SMA50" in price_data.columns and pd.notna(price_data["SMA50"].iloc[-1]) else None
    sma200 = price_data["SMA200"].iloc[-1] if "SMA200" in price_data.columns and pd.notna(price_data["SMA200"].iloc[-1]) else None

    if sma50 is None or sma200 is None:
        return "Insufficient history for moving-average analysis."

    if current > sma50 > sma200:
        trend = "Strong uptrend — price above both SMA 50 and SMA 200."
    elif current > sma200 and current < sma50:
        trend = "Short-term pullback within a longer-term uptrend (below SMA 50 but above SMA 200)."
    elif current > sma200:
        trend = "Above SMA 200 but SMAs are converging — trend is uncertain."
    elif current < sma50 < sma200:
        trend = "Strong downtrend — price below both SMA 50 and SMA 200."
    elif current < sma200 and current > sma50:
        trend = "Short-term bounce within a longer-term downtrend."
    else:
        trend = "Trend is transitional — price between the moving averages."

    cross = "Golden Cross active (SMA 50 > 200)." if sma50 > sma200 else "Death Cross active (SMA 50 < 200)."
    return f"{trend} {cross}"


def _fund_snippet(fund_score_p2, info):
    pe = info.get("trailingPE")
    roe = info.get("returnOnEquity")
    parts = []
    if pe is not None:
        parts.append(f"P/E {pe:.1f}")
    if roe is not None:
        parts.append(f"ROE {roe*100:.0f}%")
    metrics = ", ".join(parts) if parts else "Limited data"
    if fund_score_p2 >= 65:
        return f"Fundamentals are solid ({metrics}). Factor score: {fund_score_p2:.0f}/100."
    if fund_score_p2 >= 40:
        return f"Fundamentals are mixed ({metrics}). Factor score: {fund_score_p2:.0f}/100."
    return f"Fundamental concerns ({metrics}). Factor score: {fund_score_p2:.0f}/100."


# ---- helpers ----

def _find_crossovers(df):
    """Find SMA50/200 golden & death crosses in df."""
    if "SMA50" not in df.columns or "SMA200" not in df.columns:
        return [], []
    golden, death = [], []
    s50, s200, dates, prices = df["SMA50"].values, df["SMA200"].values, df["Date"].values, df["Close"].values
    for i in range(1, len(df)):
        if pd.isna(s50[i]) or pd.isna(s200[i]) or pd.isna(s50[i-1]) or pd.isna(s200[i-1]):
            continue
        if s50[i-1] <= s200[i-1] and s50[i] > s200[i]:
            golden.append((dates[i], prices[i], s50[i]))
        if s50[i-1] >= s200[i-1] and s50[i] < s200[i]:
            death.append((dates[i], prices[i], s50[i]))
    return golden, death


# =============================================================================
# RENDER
# =============================================================================

def render(selected, price_data, info, last_row, change_pct,
           tech_score, tech_details, volume_score, volume_details,
           fund_score_p2, fund_details_p2,
           market_regime, regime_metrics,
           recommendation_data, rsi_value,
           selected_strategy, news_items, cost_basis, paper1_details,
           logo_url=""):

    rec = recommendation_data.get("recommendation", "HOLD")
    confidence = recommendation_data.get("confidence", 50)
    rec_colors = {"BUY": "#0097A7", "SELL": "#FF6B6B", "HOLD": "#F59E0B"}
    rec_color = rec_colors.get(rec, "#F59E0B")

    company_name = info.get("shortName", selected)
    current_price = float(price_data["Close"].iloc[-1])
    change_sign = "+" if change_pct >= 0 else ""
    change_color = get_status_color("success") if change_pct >= 0 else get_status_color("danger")
    rsi_safe = rsi_value if (rsi_value is not None and not pd.isna(rsi_value)) else 50

    logo_html = ""
    if logo_url:
        logo_html = (
            f'<img src="{logo_url}" alt="" '
            f'style="width:36px;height:36px;border-radius:8px;object-fit:contain;margin-right:10px;" '
            f'onerror="this.style.display=\'none\'">'
        )

    sentiment_colors = {"Positive": "#0097A7", "Negative": "#FF6B6B", "Neutral": "#5A7D82"}

    # =====================================================================
    # SINGLE column pair — left stacks Analysis + Trend, right stacks News + Fundamentals
    # This avoids the extra Streamlit gap between two separate st.columns() calls.
    # =====================================================================
    col_left, col_right = st.columns([3, 2])

    # --- LEFT COLUMN: Analysis card then Trend chart ---
    with col_left:
        snippet = _analysis_snippet(rec, confidence, paper1_details, selected_strategy, tech_score, rsi_safe)

        # Build SVG sparkline from last 63 days of price data
        spark_df = price_data.tail(63)
        spark_prices = spark_df["Close"].tolist()
        spark_dates = spark_df["Date"].tolist()
        svg_html = _build_sparkline_svg(spark_prices, dates=spark_dates, width=560, height=130, color="#0097A7")

        st.markdown(f"""
        <div style="{CARD}">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
                <div style="display:flex;align-items:center;">
                    {logo_html}
                    <div>
                        <div style="{LABEL} margin-bottom:2px;">Analysis</div>
                        <span style="font-family:Source Sans Pro,Arial,sans-serif;font-size:13px;color:#5A7D82;letter-spacing:0.04em;">{selected}</span>
                        <div style="font-family:Source Sans Pro,Arial,sans-serif;font-size:20px;font-weight:600;color:#1A3C40;">{company_name}</div>
                    </div>
                </div>
                <div style="text-align:right;">
                    <span style="font-family:Source Sans Pro,Arial,sans-serif;font-size:28px;font-weight:400;color:#1A3C40;">${current_price:.2f}</span>
                    <span style="font-size:14px;color:{change_color};font-weight:500;margin-left:8px;">{change_sign}{change_pct:.2f}%</span>
                    <div style="margin-top:4px;">
                        <span style="font-size:14px;font-weight:700;color:{rec_color};background:{rec_color}18;padding:3px 12px;border-radius:6px;">{rec}</span>
                    </div>
                </div>
            </div>
            <div style="margin-top:8px;">{svg_html}</div>
            <div style="{SNAPPY}">{snippet}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

        # --- Trend chart ---
        st.markdown(f'<div style="{LABEL}">Technical — Trend</div>', unsafe_allow_html=True)

        chart_1y = price_data.tail(252).copy()
        golden_crosses, death_crosses = _find_crossovers(chart_1y)

        dates_1y = chart_1y["Date"].tolist()
        close_1y = chart_1y["Close"].tolist()

        trend_fig = go.Figure()
        trend_fig.add_trace(go.Scatter(
            x=dates_1y, y=close_1y, name="Price",
            line=dict(color="#1A3C40", width=2.5), mode="lines",
        ))
        if "SMA50" in chart_1y.columns:
            trend_fig.add_trace(go.Scatter(
                x=dates_1y, y=chart_1y["SMA50"].tolist(), name="SMA 50",
                line=dict(color="#0097A7", width=2), mode="lines", connectgaps=False,
            ))
        if "SMA200" in chart_1y.columns:
            trend_fig.add_trace(go.Scatter(
                x=dates_1y, y=chart_1y["SMA200"].tolist(), name="SMA 200",
                line=dict(color="#FF6B6B", width=2), mode="lines", connectgaps=False,
            ))

        for d, p, s in golden_crosses:
            trend_fig.add_annotation(
                x=d, y=s, text="Golden Cross", showarrow=True, arrowhead=2,
                arrowwidth=2, arrowcolor="#10B981",
                font=dict(size=10, color="#10B981"), bgcolor="white",
                bordercolor="#10B981", borderwidth=1, ax=0, ay=-35,
            )
        for d, p, s in death_crosses:
            trend_fig.add_annotation(
                x=d, y=s, text="Death Cross", showarrow=True, arrowhead=2,
                arrowwidth=2, arrowcolor="#EF4444",
                font=dict(size=10, color="#EF4444"), bgcolor="white",
                bordercolor="#EF4444", borderwidth=1, ax=0, ay=35,
            )

        trend_fig.update_layout(
            height=320, margin=dict(l=10, r=10, t=10, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
                        font=dict(color="#1A3C40", size=11)),
            font=dict(color="#1A3C40", family="Source Sans Pro,Arial,sans-serif", size=12),
            plot_bgcolor="white", paper_bgcolor="white", hovermode="x unified",
        )
        trend_fig.update_xaxes(showgrid=False, showline=True, linecolor="#D0E8EA",
                               tickfont=dict(color="#37616A", size=10))
        trend_fig.update_yaxes(showgrid=True, gridcolor="#D0E8EA",
                               tickfont=dict(color="#37616A", size=10), tickprefix="$")

        st.markdown('<div style="border-radius:12px;overflow:hidden;border:1px solid #D0E8EA;box-shadow:0 2px 6px rgba(0,151,167,0.08);">', unsafe_allow_html=True)
        st.plotly_chart(trend_fig, use_container_width=True, key="dash_trend_chart")
        st.markdown('</div>', unsafe_allow_html=True)

        trend_snip = _trend_snippet(price_data)
        st.markdown(f'<div style="{SNAPPY} margin-top:-6px;">{trend_snip}</div>', unsafe_allow_html=True)

    # --- RIGHT COLUMN: News card then Fundamentals card ---
    with col_right:
        news_html = ""
        if news_items:
            for item in news_items[:5]:
                headline = item.get("headline", "Untitled")
                url = item.get("url", "#")
                sentiment = classify_headline_sentiment(headline)
                bc = sentiment_colors.get(sentiment, "#5A7D82")
                news_html += (
                    f'<div style="border-left:3px solid {bc};padding:5px 10px;margin-bottom:4px;border-radius:4px;">'
                    f'<a href="{url}" target="_blank" style="font-family:Source Sans Pro,Arial,sans-serif;'
                    f'font-size:12.5px;font-weight:500;color:#1A3C40;text-decoration:none;line-height:1.3;">'
                    f'{headline}</a></div>'
                )
        else:
            news_html = '<div style="font-size:13px;color:#5A7D82;">No recent news available.</div>'

        st.markdown(f"""
        <div style="{CARD}">
            <div style="{LABEL}">News & Sentiment</div>
            {news_html}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

        # --- Fundamentals card ---
        def _bar(label, score, color):
            pct = max(0, min(100, score))
            return (
                f'<div style="margin-bottom:10px;">'
                f'<div style="display:flex;justify-content:space-between;font-family:Source Sans Pro,Arial,sans-serif;'
                f'font-size:12px;color:#5A7D82;margin-bottom:3px;">'
                f'<span>{label}</span><span style="font-weight:600;color:#1A3C40;">{pct:.0f}</span></div>'
                f'<div style="background:#D0E8EA;border-radius:4px;height:6px;overflow:hidden;">'
                f'<div style="width:{pct}%;height:100%;background:{color};border-radius:4px;"></div>'
                f'</div></div>'
            )

        bars = _bar("Tech Score", tech_score, "#0097A7")
        if selected_strategy == "Volume+RSI":
            bars += _bar("Volume Score", volume_score, "#0097A7")
        bars += _bar("Factor Score", fund_score_p2, "#0097A7")
        bars += _bar("RSI", rsi_safe, "#FF6B6B" if rsi_safe > 70 or rsi_safe < 30 else "#0097A7")

        fund_snip = _fund_snippet(fund_score_p2, info)

        bull_case, bear_case = generate_bull_bear_case(info, tech_score, fund_score_p2, price_data, market_regime)
        bull_pt = bull_case[0] if bull_case else "Potential for mean reversion"
        bear_pt = bear_case[0] if bear_case else "Standard market risk"

        st.markdown(f"""
        <div style="{CARD}">
            <div style="{LABEL}">Fundamentals</div>
            {bars}
            <div style="{SNAPPY}">{fund_snip}</div>
            <div style="margin-top:14px;display:flex;gap:8px;">
                <div style="flex:1;border-left:3px solid #0097A7;padding:4px 8px;font-size:12px;color:#1A3C40;
                            font-family:Source Sans Pro,Arial,sans-serif;line-height:1.3;">{bull_pt}</div>
                <div style="flex:1;border-left:3px solid #FF6B6B;padding:4px 8px;font-size:12px;color:#1A3C40;
                            font-family:Source Sans Pro,Arial,sans-serif;line-height:1.3;">{bear_pt}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
