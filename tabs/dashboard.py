# =============================================================================
# DASHBOARD TAB - At-a-Glance Executive Briefing (Streamlit — mirrors Dash)
# =============================================================================

import datetime as dt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from components import COLORS, FONTS, SHADOWS, get_status_color
from models import classify_headline_sentiment, generate_bull_bear_case

# Shared inline styles
CARD = (
    "background:#FFFFFF;border:1px solid #E8EDF2;border-radius:14px;"
    "box-shadow:0 1px 3px rgba(0,0,0,0.04),0 1px 2px rgba(0,0,0,0.02);"
)
LABEL = (
    "font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;font-size:11px;font-weight:600;"
    "color:#94A3B8;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;"
)
EXPLAIN = (
    "font-size:11px;color:#94A3B8;line-height:1.4;margin-top:8px;font-weight:400;"
    "font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;"
)
BOX = (
    "background:#FFFFFF;border:1px solid #E8EDF2;border-radius:14px;"
    "padding:18px 20px;"
    "box-shadow:0 1px 3px rgba(0,0,0,0.04),0 1px 2px rgba(0,0,0,0.02);"
)


# =============================================================================
# HELPERS (identical logic to Dash version)
# =============================================================================

def _smart_comment(price_data):
    """Generate an intelligent trend comment based on price action."""
    current = float(price_data["Close"].iloc[-1])
    dates = price_data["Date"]

    lookbacks = {"30d": 22, "60d": 44, "90d": 63, "6m": 126}
    prices = {}
    for k, n in lookbacks.items():
        if len(price_data) > n:
            prices[k] = float(price_data["Close"].iloc[-n])

    recent = price_data.tail(63)
    high_90 = float(recent["Close"].max())
    low_90 = float(recent["Close"].min())
    high_idx = recent["Close"].idxmax()
    low_idx = recent["Close"].idxmin()

    high_date = dates.iloc[high_idx] if high_idx < len(dates) else dates.iloc[-1]
    low_date = dates.iloc[low_idx] if low_idx < len(dates) else dates.iloc[-1]

    pct_from_high = ((current - high_90) / high_90) * 100
    pct_from_low = ((current - low_90) / low_90) * 100
    range_pct = ((high_90 - low_90) / low_90) * 100

    p30 = prices.get("30d", current)
    p60 = prices.get("60d", current)
    p90 = prices.get("90d", current)

    def fmt_date(d):
        if hasattr(d, "strftime"):
            return d.strftime("%b %Y")
        return str(d)[:10]

    if current < p30 < p60 and pct_from_high < -5:
        return f"Declining since {fmt_date(high_date)}, down {abs(pct_from_high):.1f}% from its recent high of ${high_90:.2f}."
    if current > p30 > p60 and pct_from_low > 5:
        return f"Trending higher since {fmt_date(low_date)}, up {pct_from_low:.1f}% from ${low_90:.2f}."
    if range_pct < 15:
        return f"Fluctuating in a range between ${low_90:.0f}\u2013${high_90:.0f} over the past 3 months."
    if current > p30 and current < p90:
        return f"Recovering from recent lows, currently at ${current:.2f}. Still below 90-day levels."
    if current < p30 and current > p90:
        return f"Short-term pullback from ${p30:.2f} (30 days ago), but still above 90-day levels."

    chg = ((current - p90) / p90) * 100 if p90 else 0
    direction = "up" if chg > 0 else "down"
    return f"Price is {direction} {abs(chg):.1f}% over the past 3 months, currently at ${current:.2f}."


def _calc_period_returns(price_data):
    """Calculate returns for standard periods."""
    current = float(price_data["Close"].iloc[-1])
    periods = []

    def _ret(n, lbl):
        if len(price_data) > n:
            past = float(price_data["Close"].iloc[-n - 1])
            pct = ((current - past) / past) * 100
            return {"label": lbl, "value": pct}
        return {"label": lbl, "value": None}

    periods.append(_ret(1, "1D"))
    periods.append(_ret(5, "5D"))
    periods.append(_ret(22, "1M"))
    periods.append(_ret(126, "6M"))

    # YTD
    if "Date" in price_data.columns:
        dates_col = price_data["Date"]
        if hasattr(dates_col.iloc[-1], "year"):
            year_start = price_data[dates_col.dt.year == dates_col.iloc[-1].year]
        else:
            year_start = pd.DataFrame()
        if len(year_start) > 0:
            ytd_start = float(year_start["Close"].iloc[0])
            periods.append({"label": "YTD", "value": ((current - ytd_start) / ytd_start) * 100})
        else:
            periods.append({"label": "YTD", "value": None})
    else:
        periods.append({"label": "YTD", "value": None})

    periods.append(_ret(252, "1Y"))
    periods.append(_ret(1260, "5Y"))
    return periods


def _fund_snippet(info):
    pe = info.get("trailingPE")
    roe = info.get("returnOnEquity")
    parts = []
    if pe is not None:
        parts.append(f"P/E {pe:.1f}")
    if roe is not None:
        parts.append(f"ROE {roe * 100:.0f}%")
    metrics = ", ".join(parts) if parts else "Limited data"
    strong = (roe is not None and roe > 0.15) or (pe is not None and pe < 20)
    weak = (roe is not None and roe < 0.08) or (pe is not None and pe > 35)
    if strong:
        return f"Fundamentals are solid ({metrics})."
    if weak:
        return f"Fundamental concerns ({metrics})."
    return f"Fundamentals are mixed ({metrics})."


def _build_chart(price_data, n_days=126):
    """Build price chart (mirrors Dash build_chart)."""
    chart_df = price_data.tail(n_days).copy()
    dates = chart_df["Date"].tolist()
    close = chart_df["Close"].tolist()

    y_min = min(close)
    y_max = max(close)
    y_padding = (y_max - y_min) * 0.08 if y_max != y_min else y_max * 0.02

    fig = go.Figure()
    # Invisible baseline for fill
    fig.add_trace(go.Scatter(
        x=dates, y=[y_min - y_padding] * len(dates),
        mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=close, mode="lines",
        line=dict(color="#0097A7", width=2),
        fill="tonexty", fillcolor="rgba(0, 151, 167, 0.05)",
        hovertemplate="$%{y:.2f}<extra></extra>",
    ))

    fig.update_layout(
        height=220, margin=dict(l=5, r=10, t=5, b=25),
        plot_bgcolor="white", paper_bgcolor="white",
        showlegend=False, hovermode="x unified",
        font=dict(family="Inter,-apple-system,BlinkMacSystemFont,sans-serif", size=11, color="#64748B"),
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor="#E8EDF2",
                     tickfont=dict(size=10, color="#94A3B8"))
    fig.update_yaxes(showgrid=True, gridcolor="#F1F5F9", tickprefix="$",
                     tickfont=dict(size=10, color="#94A3B8"),
                     range=[y_min - y_padding, y_max + y_padding])
    return fig


def _progress_bar(label_text, score, color):
    """HTML progress bar matching Dash components.progress_bar."""
    pct = max(0, min(100, score))
    return (
        f'<div style="margin-bottom:10px;">'
        f'<div style="display:flex;justify-content:space-between;'
        f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;'
        f'font-size:12px;color:#64748B;margin-bottom:3px;">'
        f'<span>{label_text}</span><span style="font-weight:600;color:#1E293B;">{pct:.0f}</span></div>'
        f'<div style="background:#F1F5F9;border-radius:4px;height:6px;overflow:hidden;">'
        f'<div style="width:{pct}%;height:100%;background:{color};border-radius:4px;"></div>'
        f'</div></div>'
    )


def _signal_row(label_text, value, color):
    """HTML signal row matching Dash components.signal_row."""
    return (
        f'<div style="display:flex;justify-content:space-between;padding:4px 0;">'
        f'<span style="font-size:12px;color:#64748B;font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">'
        f'{label_text}</span>'
        f'<span style="font-size:12px;font-weight:600;color:{color};'
        f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{value}</span></div>'
    )


# =============================================================================
# RENDER
# =============================================================================

def render(selected, price_data, info, last_row, change_pct,
           tech_score, tech_details, volume_score, volume_details,
           market_regime, regime_metrics,
           recommendation_data, rsi_value,
           news_items, cost_basis, paper1_details,
           logo_url="", is_sp500=False, chart_period="6M", piotroski_score=None):

    rec = recommendation_data.get("recommendation", "HOLD")
    confidence = recommendation_data.get("confidence", 50)
    rec_colors = {"BUY": "#0097A7", "SELL": "#FF6B6B", "HOLD": "#F59E0B"}
    rec_color = rec_colors.get(rec, "#F59E0B")

    company_name = info.get("shortName", selected)
    current_price = float(price_data["Close"].iloc[-1])
    change_sign = "+" if change_pct >= 0 else ""
    change_color = "#10B981" if change_pct >= 0 else "#EF4444"
    rsi_safe = rsi_value if (rsi_value is not None and not pd.isna(rsi_value)) else 50

    logo_html = ""
    if logo_url:
        logo_html = (
            f'<img src="{logo_url}" alt="" '
            f'style="width:44px;height:44px;border-radius:12px;object-fit:contain;margin-right:14px;'
            f'border:1px solid #E8EDF2;padding:4px;background:#FFFFFF;" '
            f'onerror="this.style.display=\'none\'">'
        )

    # =====================================================================
    # 1. HEADER
    # =====================================================================
    st.html(f"""
    <div style="{CARD} padding:18px 24px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div style="display:flex;align-items:center;">
                {logo_html}
                <div>
                    <div style="font-size:20px;font-weight:600;color:#0F172A;letter-spacing:-0.02em;line-height:1.2;
                                font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{company_name}</div>
                    <span style="font-size:13px;color:#94A3B8;letter-spacing:0.05em;font-weight:500;
                                 font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{selected}</span>
                </div>
            </div>
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="text-align:right;">
                    <span style="font-size:28px;font-weight:700;color:#0F172A;letter-spacing:-0.02em;
                                 font-family:'Calibri','Segoe UI',sans-serif;">${current_price:.2f}</span>
                    <span style="font-size:14px;color:{change_color};font-weight:600;margin-left:8px;
                                 font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{change_sign}{change_pct:.2f}%</span>
                </div>
                <div style="font-size:13px;font-weight:700;color:white;background:{rec_color};
                            padding:5px 18px;border-radius:20px;
                            letter-spacing:0.04em;">{rec}</div>
            </div>
        </div>
    </div>
    """)

    st.markdown("<div style='height:3px;'></div>", unsafe_allow_html=True)

    # =====================================================================
    # 2. CHART + PERIOD RETURNS
    # =====================================================================
    _period_days = {
        "1D": 1, "5D": 5, "1M": 22, "6M": 126, "1Y": 252, "5Y": 1260, "MAX": len(price_data),
    }
    if chart_period == "YTD":
        import datetime as _dt
        _today = price_data["Date"].iloc[-1]
        _year_start = pd.Timestamp(_today.year, 1, 1) if hasattr(_today, 'year') else pd.Timestamp(_dt.date.today().year, 1, 1)
        _n_days = max(len(price_data[price_data["Date"] >= _year_start]), 1)
    else:
        _n_days = min(_period_days.get(chart_period, 126), len(price_data))
    fig = _build_chart(price_data, n_days=_n_days)
    period_returns = _calc_period_returns(price_data)
    ret_map = {p["label"]: p["value"] for p in period_returns}

    PERIOD_BUTTONS = ["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y"]
    btns_html = ""
    for p_label in PERIOD_BUTTONS:
        val = ret_map.get(p_label)
        if val is not None:
            clr = "#10B981" if val >= 0 else "#EF4444"
            val_text = f"{val:+.2f}%"
        else:
            clr = "#94A3B8"
            val_text = "\u2014"

        is_active = (p_label == chart_period)
        bg = "#E0F4F5" if is_active else "#F8FAFB"
        border = "1.5px solid #0097A7" if is_active else "1.5px solid transparent"
        lbl_clr = "#0097A7" if is_active else "#94A3B8"
        lbl_wt = "600" if is_active else "500"

        btns_html += (
            f'<div style="flex:1;text-align:center;padding:8px 4px;border-radius:10px;'
            f'background:{bg};border:{border};">'
            f'<div style="font-size:11px;color:{lbl_clr};font-weight:{lbl_wt};letter-spacing:0.02em;'
            f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{p_label}</div>'
            f'<div style="font-size:13px;color:{clr};font-weight:600;'
            f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{val_text}</div>'
            f'</div>'
        )

    # Render chart inside a card (background box trick)
    st.markdown(f"""
    <div style="background:#FFFFFF;border:1px solid #E8EDF2;border-radius:14px;
                box-shadow:0 1px 3px rgba(0,0,0,0.04),0 1px 2px rgba(0,0,0,0.02);
                min-height:380px;margin-bottom:-370px;"></div>
    """, unsafe_allow_html=True)
    _, dash_c, _ = st.columns([0.2, 9.6, 0.2])
    with dash_c:
        st.plotly_chart(fig, use_container_width=True, key="dash_price_chart",
                        config={"displayModeBar": False})
    st.markdown(f"""
        <div style="padding:4px 16px 12px 16px;display:flex;gap:6px;">{btns_html}</div>
    """, unsafe_allow_html=True)

    # =====================================================================
    # 3. SMART COMMENT
    # =====================================================================
    comment = _smart_comment(price_data)
    st.markdown(f"""
    <div style="font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;font-size:13px;
                color:#64748B;line-height:1.6;padding:6px 4px 6px 20px;">{comment}</div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:45px;'></div>", unsafe_allow_html=True)

    # =====================================================================
    # 4. COMPANY INFO
    # =====================================================================
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")

    sp500_label = "S&P 500" if is_sp500 else "Non S&P 500"
    sp500_clr = "#10B981" if is_sp500 else "#94A3B8"

    desc_text = ""
    long_summary = info.get("longBusinessSummary")
    if long_summary:
        sentences = long_summary.split(". ")
        desc_text = ". ".join(sentences[:2]).strip()
        if not desc_text.endswith("."):
            desc_text += "."

    desc_html = ""
    if desc_text:
        desc_html = (
            f'<p style="font-size:12.5px;color:#64748B;line-height:1.6;margin:0;'
            f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{desc_text}</p>'
        )

    def _info_tag(lbl, val, color=""):
        c = f"color:{color};" if color else "color:#1E293B;"
        return (
            f'<div style="padding:4px 12px;background:#F8FAFB;border-radius:8px;display:inline-block;">'
            f'<span style="font-weight:500;font-size:12px;color:#94A3B8;'
            f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{lbl}</span>'
            f' <span style="font-size:12px;font-weight:600;{c}'
            f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{val}</span></div>'
        )

    st.markdown(f"""
    <div style="{CARD} padding:16px 20px;">
        <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;">
            {_info_tag("Sector", sector)}
            {_info_tag("Industry", industry)}
            {_info_tag("Index", sp500_label, sp500_clr)}
        </div>
        {desc_html}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # =====================================================================
    # 5. SIGNAL BOXES (4 boxes in a row)
    # =====================================================================
    regime_colors = {"Bull": "#10B981", "Bear": "#EF4444", "Sideways": "#F59E0B", "High-Volatility": "#EF4444"}
    regime_clr = regime_colors.get(market_regime, "#64748B")

    regime_explanations = {
        "Bull": "Market regime reflects the overall market direction. Currently in a bull market \u2014 the broader market is trending upward, which generally supports stock prices.",
        "Bear": "Market regime reflects the overall market direction. Currently in a bear market \u2014 the broader market is trending downward, which generally puts pressure on stock prices.",
        "Sideways": "Market regime reflects the overall market direction. Currently sideways \u2014 the broader market has no clear trend, meaning prices may fluctuate without sustained direction.",
        "High-Volatility": "Market regime reflects the overall market direction. Currently experiencing high volatility \u2014 the broader market is seeing larger-than-usual price swings, increasing uncertainty.",
    }
    regime_explain = regime_explanations.get(market_regime, "Market regime reflects the overall market direction. Current conditions are being assessed.")

    # Signal explanation reflects Paper 1 logic: SMA crossover + ATV + RSI gate + RL
    if paper1_details:
        ct = paper1_details.get("crossover_type", "none")
        atv_ok = paper1_details.get("atv_confirmed", False)
        rl_override = paper1_details.get("rl_override", False)
        if rec == "BUY":
            if ct == "golden_cross" and atv_ok:
                signal_explain = "SMA-20 crossed above SMA-50 (Golden Cross) with rising volume confirmed by ATV slope. RSI gate passed. This is a rule-based signal from the SMA + ATV + RSI strategy."
            elif rl_override:
                signal_explain = "No SMA crossover detected. The RL agent (PPO) has identified a buying opportunity based on learned market patterns."
            else:
                signal_explain = "SMA crossover signal with volume and RSI confirmation pointing toward upside."
        elif rec == "SELL":
            if ct == "death_cross" and atv_ok:
                signal_explain = "SMA-20 crossed below SMA-50 (Death Cross) with rising volume confirmed by ATV slope. RSI gate passed. This is a rule-based signal from the SMA + ATV + RSI strategy."
            elif rl_override:
                signal_explain = "No SMA crossover detected. The RL agent (PPO) has identified downside risk based on learned market patterns."
            else:
                signal_explain = "SMA crossover signal with volume and RSI confirmation pointing toward downside."
        else:
            if ct == "none" and not rl_override:
                signal_explain = "No SMA-20/50 crossover event detected. The strategy holds position until a confirmed crossover with volume support appears."
            elif ct in ("golden_cross", "death_cross") and not atv_ok:
                signal_explain = "A crossover was detected but ATV slope did not confirm — volume is not supporting the move. Signal weakened to HOLD."
            else:
                signal_explain = "RSI gate or conflicting signals resulted in a HOLD. Waiting for clearer confirmation before acting."
    else:
        signal_explanations = {
            "BUY": "SMA crossover with ATV volume confirmation and RSI gate passed — pointing toward upside potential.",
            "SELL": "SMA crossover with ATV volume confirmation and RSI gate passed — pointing toward downside risk.",
            "HOLD": "No confirmed SMA crossover detected. Holding position until a clear signal emerges.",
        }
        signal_explain = signal_explanations.get(rec, "Awaiting signal confirmation.")

    conf_status_clr = "#10B981" if confidence >= 70 else "#F59E0B" if confidence >= 50 else "#EF4444"
    if confidence >= 70:
        conf_explain = "Confidence reflects signal strength: crossover type, ATV volume confirmation, and RL agent agreement. At this level, all indicators are aligned."
    elif confidence >= 50:
        conf_explain = "Confidence reflects signal strength: crossover type, ATV volume confirmation, and RL agent agreement. At this level, some indicators are not fully aligned."
    else:
        conf_explain = "Confidence reflects signal strength: crossover type, ATV volume confirmation, and RL agent agreement. At this level, the signal is weak — no crossover or volume not confirmed."

    # Key Signals data
    if paper1_details:
        cross_labels = {"golden_cross": ("Golden Cross", "#10B981"),
                        "death_cross": ("Death Cross", "#EF4444"),
                        "none": ("No Crossover", "#94A3B8")}
        cross_name, cross_clr = cross_labels.get(ct, ("No Crossover", "#94A3B8"))
        atv = "Confirmed" if paper1_details.get("atv_confirmed") else "Not Confirmed"
        atv_clr = "#10B981" if paper1_details.get("atv_confirmed") else "#F59E0B"
        rsi_g = paper1_details.get("rsi_gate", "n/a")
        rsi_gate_map = {"passed": ("Passed", "#10B981"),
                        "blocked_overbought": ("Blocked \u2014 Overbought", "#EF4444"),
                        "blocked_oversold": ("Blocked \u2014 Oversold", "#EF4444"),
                        "n/a": ("N/A", "#94A3B8")}
        rsi_lbl, rsi_clr = rsi_gate_map.get(rsi_g, ("N/A", "#94A3B8"))
        rl_sig = paper1_details.get("rl_signal")
        if rl_sig:
            ai_agrees = paper1_details.get("rl_agrees", False)
            rl_override = paper1_details.get("rl_override", False)
            if rl_override:
                ai_status = "Override"
                ai_clr = "#F59E0B"
            elif ai_agrees:
                ai_status = "Agrees"
                ai_clr = "#10B981"
            else:
                ai_status = "Disagrees"
                ai_clr = "#F59E0B"
            ai_row = _signal_row("RL Agent (PPO)", f"{rl_sig} \u2014 {ai_status}", ai_clr)
        else:
            ai_row = _signal_row("RL Agent (PPO)", "Not Active", "#94A3B8")
    else:
        cross_name, cross_clr = "N/A", "#94A3B8"
        atv, atv_clr = "N/A", "#94A3B8"
        rsi_lbl, rsi_clr = "N/A", "#94A3B8"
        ai_row = _signal_row("RL Agent (PPO)", "Not Active", "#94A3B8")

    # Use st.columns for the 4 signal boxes
    sig_cols = st.columns([1, 1, 1, 1.5])

    with sig_cols[0]:
        st.markdown(f"""
        <div style="{BOX}">
            <div style="{LABEL}">Market Regime</div>
            <div style="font-size:20px;font-weight:700;color:{regime_clr};margin-top:4px;letter-spacing:-0.01em;
                        font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{market_regime}</div>
            <div style="{EXPLAIN}">{regime_explain}</div>
        </div>
        """, unsafe_allow_html=True)

    with sig_cols[1]:
        st.markdown(f"""
        <div style="{BOX}">
            <div style="{LABEL}">Signal</div>
            <div style="font-size:28px;font-weight:700;color:{rec_color};margin-top:4px;letter-spacing:-0.02em;
                        font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{rec}</div>
            <div style="{EXPLAIN}">{signal_explain}</div>
        </div>
        """, unsafe_allow_html=True)

    with sig_cols[2]:
        st.markdown(f"""
        <div style="{BOX}">
            <div style="{LABEL}">Confidence</div>
            <div style="font-size:28px;font-weight:700;color:{conf_status_clr};margin-top:4px;letter-spacing:-0.02em;
                        font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{confidence}%</div>
            <div style="{EXPLAIN}">{conf_explain}</div>
        </div>
        """, unsafe_allow_html=True)

    with sig_cols[3]:
        st.markdown(f"""
        <div style="{BOX}">
            <div style="{LABEL}">Key Signals</div>
            <div style="line-height:1.6;font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">
                {_signal_row("SMA Crossover", cross_name, cross_clr)}
                {_signal_row("ATV Volume", atv, atv_clr)}
                {_signal_row("RSI Gate", rsi_lbl, rsi_clr)}
                {ai_row}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # =====================================================================
    # 6. HEALTH CHECK + NEWS (side by side)
    # =====================================================================
    news_col, hc_col = st.columns(2)

    with hc_col:
        rsi_zone = "Overbought" if rsi_safe > 70 else "Oversold" if rsi_safe < 30 else "Neutral"
        rsi_bar_color = "#FF6B6B" if rsi_safe > 70 or rsi_safe < 30 else "#0097A7"

        # Price vs SMA50
        current_price = float(price_data["Close"].iloc[-1])
        sma50_hc = float(price_data["SMA50"].iloc[-1]) if "SMA50" in price_data.columns and pd.notna(price_data["SMA50"].iloc[-1]) else None
        if sma50_hc is not None:
            pct_vs_sma50 = (current_price - sma50_hc) / sma50_hc * 100
            pct_sign = "+" if pct_vs_sma50 >= 0 else ""
            pct_color = "#10B981" if pct_vs_sma50 >= 0 else "#FF6B6B"
            pct_label = "above" if pct_vs_sma50 >= 0 else "below"
            sma50_row = (
                f'<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #E8EDF2;">'
                f'<span style="font-size:12px;color:#64748B;font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">Price vs SMA50</span>'
                f'<span style="font-size:12px;font-weight:700;color:{pct_color};font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">'
                f'{pct_sign}{pct_vs_sma50:.1f}% {pct_label}</span></div>'
            )
        else:
            sma50_row = ""

        # Relative Volume
        rel_vol_hc = float(price_data["Rel_Volume"].iloc[-1]) if "Rel_Volume" in price_data.columns and pd.notna(price_data["Rel_Volume"].iloc[-1]) else None
        if rel_vol_hc is not None:
            if rel_vol_hc >= 2.0:
                rv_label, rv_color = "High Activity", "#10B981"
            elif rel_vol_hc >= 0.8:
                rv_label, rv_color = "Normal Activity", "#0097A7"
            else:
                rv_label, rv_color = "Low Activity", "#F59E0B"
            rel_vol_row = (
                f'<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #E8EDF2;">'
                f'<span style="font-size:12px;color:#64748B;font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">Relative Volume</span>'
                f'<span style="font-size:12px;font-weight:700;color:{rv_color};font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">'
                f'{rel_vol_hc:.2f}x \u2014 {rv_label}</span></div>'
            )
        else:
            rel_vol_row = ""

        # Piotroski F-Score bar
        if piotroski_score is not None:
            fs_bar_val = int(piotroski_score / 9 * 100)
            fs_color = "#10B981" if piotroski_score >= 7 else "#F59E0B" if piotroski_score >= 4 else "#FF6B6B"
            fs_label = "Strong" if piotroski_score >= 7 else "Moderate" if piotroski_score >= 4 else "Weak"
            fscore_bar = _progress_bar(f"Piotroski F-Score \u2014 {piotroski_score}/9 ({fs_label})", fs_bar_val, fs_color)
        else:
            fscore_bar = ""

        bars_html = _progress_bar(f"RSI Momentum \u2014 {rsi_zone}", rsi_safe, rsi_bar_color)
        bars_html += fscore_bar

        fund_snip = _fund_snippet(info)
        bull_case, bear_case = generate_bull_bear_case(info, tech_score, price_data, market_regime)
        bull_pt = bull_case[0] if bull_case else "Potential for mean reversion"
        bear_pt = bear_case[0] if bear_case else "Standard market risk"

        st.markdown(f"""
        <div style="{CARD} padding:16px 20px;">
            <div style="{LABEL}">Health Check</div>
            {bars_html}
            {sma50_row}
            {rel_vol_row}
            <div style="font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;font-size:13px;
                        color:#64748B;line-height:1.5;margin-top:8px;">{fund_snip}</div>
            <div style="margin-top:14px;display:flex;gap:10px;">
                <div style="flex:1;border-left:3px solid #10B981;padding:6px 10px;font-size:12px;color:#1E293B;
                            line-height:1.4;border-radius:0 6px 6px 0;background:rgba(16,185,129,0.04);
                            font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{bull_pt}</div>
                <div style="flex:1;border-left:3px solid #FF6B6B;padding:6px 10px;font-size:12px;color:#1E293B;
                            line-height:1.4;border-radius:0 6px 6px 0;background:rgba(255,107,107,0.04);
                            font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{bear_pt}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with news_col:
        sentiment_colors = {"Positive": "#10B981", "Negative": "#FF6B6B", "Neutral": "#94A3B8"}
        news_html = ""
        if news_items:
            for item in news_items[:5]:
                headline = item.get("headline", "Untitled")
                url = item.get("url", "#")
                sentiment = classify_headline_sentiment(headline)
                bc = sentiment_colors.get(sentiment, "#94A3B8")
                news_html += (
                    f'<div style="border-left:3px solid {bc};padding:8px 12px;margin-bottom:6px;'
                    f'border-radius:0 8px 8px 0;background:#F8FAFB;">'
                    f'<a href="{url}" target="_blank" style="font-size:12.5px;font-weight:450;'
                    f'color:#1E293B;text-decoration:none;line-height:1.4;'
                    f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">'
                    f'{headline}</a></div>'
                )
        else:
            news_html = ('<div style="font-size:13px;color:#94A3B8;padding:8px 0;'
                         'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">No recent news available.</div>')

        st.markdown(f"""
        <div style="{CARD} padding:16px 20px;">
            <div style="{LABEL}">News & Sentiment</div>
            {news_html}
        </div>
        """, unsafe_allow_html=True)
