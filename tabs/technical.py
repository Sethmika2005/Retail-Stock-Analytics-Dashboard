# =============================================================================
# TECHNICAL TAB - "The Evidence" — Charts with verdicts (Streamlit — mirrors Dash)
# =============================================================================

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import COLORS, FONTS, SHADOWS

# Shared inline styles
CARD = (
    "background:#FFFFFF;border:1px solid #E8EDF2;border-radius:14px;"
    "padding:16px 20px;"
    "box-shadow:0 1px 3px rgba(0,0,0,0.04),0 1px 2px rgba(0,0,0,0.02);"
)
LABEL = (
    "font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;font-size:11px;font-weight:600;"
    "color:#94A3B8;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0;"
)


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
        font=dict(family="Inter,-apple-system,BlinkMacSystemFont,sans-serif", size=11, color="#64748B"),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
            font=dict(size=11, color="#1E293B"),
        ),
    )


def _chart_axes(fig, y_prefix=""):
    """Apply standard axis styling."""
    fig.update_xaxes(
        showgrid=False, showline=True, linecolor="#E8EDF2",
        tickfont=dict(size=10, color="#94A3B8"),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor="#F1F5F9",
        tickfont=dict(size=10, color="#94A3B8"),
        tickprefix=y_prefix,
    )


def _verdict_badge_html(text, color):
    """Pill-shaped verdict badge as HTML."""
    return (
        f'<span style="display:inline-block;padding:3px 14px;border-radius:20px;'
        f'background:{color};color:white;font-size:11px;font-weight:700;'
        f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;'
        f'letter-spacing:0.04em;vertical-align:middle;">{text}</span>'
    )


def _chart_card_bg(height=380):
    """Render a white rounded background box that content will sit on top of."""
    return f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid #E8EDF2;
        border-radius: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02);
        min-height: {height}px;
        margin-bottom: -{height - 10}px;
    "></div>
    """


def _chart_card_header(title, verdict_text, verdict_color):
    """HTML for chart card title + verdict badge."""
    return f"""
    <div style="padding:8px 16px 4px 16px;">
        <span style="{LABEL} font-size:14px;margin-right:10px;display:inline-block;vertical-align:middle;">{title}</span>
        {_verdict_badge_html(verdict_text, verdict_color)}
    </div>
    """


def _chart_card_explanation(text):
    """HTML for chart card explanation text."""
    return f"""
    <div style="font-size:11px;color:#94A3B8;line-height:1.4;
                font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;
                padding:0px 16px 12px 16px;margin-top:-12px;">
        {text}
    </div>
    """


def _find_ema_crossovers(df):
    """Find EMA20/EMA50 crossover points (Paper 1)."""
    if "EMA20" not in df.columns or "EMA50" not in df.columns:
        return [], []
    golden, death = [], []
    e20 = df["EMA20"].values
    e50 = df["EMA50"].values
    dates = df["Date"].values
    prices = df["Close"].values
    for i in range(1, len(df)):
        if pd.isna(e20[i]) or pd.isna(e50[i]) or pd.isna(e20[i - 1]) or pd.isna(e50[i - 1]):
            continue
        if e20[i - 1] <= e50[i - 1] and e20[i] > e50[i]:
            golden.append((dates[i], prices[i]))
        if e20[i - 1] >= e50[i - 1] and e20[i] < e50[i]:
            death.append((dates[i], prices[i]))
    return golden, death


# =============================================================================
# RENDER
# =============================================================================

def render(selected, price_data, info, tech_score, tech_details, last_row,
           volume_score=0, volume_details=None,
           paper1_details=None, rl_prediction=None, rsi_value=None):
    """Render the Technical tab — mirrors Dash technical tab exactly."""

    paper1_details = paper1_details or {}
    rsi_safe = rsi_value if rsi_value is not None and not pd.isna(rsi_value) else 50

    # Use 1Y of data for charts
    chart_data = price_data.tail(252).copy()
    dates = chart_data["Date"].tolist()

    # =========================================================================
    # SECTION 1: DECISION PIPELINE (3 stacked chart cards)
    # =========================================================================

    # --- Chart 1: EMA Crossover ---
    ema_fig = go.Figure()
    ema_fig.add_trace(go.Scatter(
        x=dates, y=chart_data["Close"].tolist(), name="Price",
        line=dict(color="#0F172A", width=2), mode="lines",
    ))
    if "EMA20" in chart_data.columns:
        ema_fig.add_trace(go.Scatter(
            x=dates, y=chart_data["EMA20"].tolist(), name="EMA-20",
            line=dict(color="#0097A7", width=1.5), mode="lines",
        ))
    if "EMA50" in chart_data.columns:
        ema_fig.add_trace(go.Scatter(
            x=dates, y=chart_data["EMA50"].tolist(), name="EMA-50",
            line=dict(color="#FF6B6B", width=1.5), mode="lines",
        ))

    golden_pts, death_pts = _find_ema_crossovers(chart_data)
    for d, p in golden_pts:
        ema_fig.add_annotation(
            x=d, y=float(p), text="\u2191 Golden", showarrow=True,
            arrowhead=2, arrowwidth=2, arrowcolor="#10B981",
            font=dict(size=9, color="#10B981"), bgcolor="white",
            bordercolor="#10B981", borderwidth=1, ax=0, ay=-30,
        )
    for d, p in death_pts:
        ema_fig.add_annotation(
            x=d, y=float(p), text="\u2193 Death", showarrow=True,
            arrowhead=2, arrowwidth=2, arrowcolor="#EF4444",
            font=dict(size=9, color="#EF4444"), bgcolor="white",
            bordercolor="#EF4444", borderwidth=1, ax=0, ay=30,
        )

    # Verdict
    ct = paper1_details.get("crossover_type", "none")
    if ct == "golden_cross":
        ema_verdict, ema_color = "Golden Cross", "#10B981"
        ema_explain = "EMA-20 has crossed above EMA-50 \u2014 short-term momentum is turning bullish. This is the primary buy trigger in the Paper 1 strategy."
    elif ct == "death_cross":
        ema_verdict, ema_color = "Death Cross", "#EF4444"
        ema_explain = "EMA-20 has crossed below EMA-50 \u2014 short-term momentum is turning bearish. This is the primary sell trigger in the Paper 1 strategy."
    else:
        ema_verdict, ema_color = "No Crossover", "#94A3B8"
        trend = paper1_details.get("ema_trend", "neutral")
        ema_explain = f"No EMA crossover event detected. Current EMA trend bias: {trend}. The system falls back to composite scoring."

    ema_fig.update_layout(**_chart_layout(280), showlegend=True)
    _chart_axes(ema_fig, y_prefix="$")

    st.markdown(_chart_card_bg(380), unsafe_allow_html=True)
    st.markdown(_chart_card_header("EMA CROSSOVER", ema_verdict, ema_color), unsafe_allow_html=True)
    _, ema_c, _ = st.columns([0.2, 9.6, 0.2])
    with ema_c:
        st.plotly_chart(ema_fig, use_container_width=True, key="tech_ema_chart",
                        config={"displayModeBar": False})
    st.markdown(_chart_card_explanation(ema_explain), unsafe_allow_html=True)

    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

    # --- Chart 2: Volume Confirmation ---
    vol_fig = go.Figure()
    if "Volume" in chart_data.columns:
        close_vals = chart_data["Close"].values
        prev_close = np.roll(close_vals, 1)
        prev_close[0] = close_vals[0]
        vol_colors = [
            "rgba(16, 185, 129, 0.5)" if c >= p else "rgba(255, 107, 107, 0.5)"
            for c, p in zip(close_vals, prev_close)
        ]
        vol_fig.add_trace(go.Bar(
            x=dates, y=chart_data["Volume"].tolist(), name="Volume",
            marker_color=vol_colors, showlegend=False,
        ))
    if "Volume_SMA20" in chart_data.columns:
        vol_fig.add_trace(go.Scatter(
            x=dates, y=chart_data["Volume_SMA20"].tolist(), name="Volume SMA-20",
            line=dict(color="#0097A7", width=2), mode="lines",
        ))

    atv_confirmed = paper1_details.get("atv_confirmed", False)
    if ct in ("golden_cross", "death_cross"):
        if atv_confirmed:
            vol_verdict, vol_color = "Volume Confirms", "#10B981"
            vol_explain = "ATV slope is rising in the direction of the crossover \u2014 volume is confirming the trend signal."
        else:
            vol_verdict, vol_color = "Volume Diverging", "#F59E0B"
            vol_explain = "ATV slope does not confirm the crossover \u2014 volume divergence weakens the signal."
    else:
        vol_verdict, vol_color = "No Signal", "#94A3B8"
        vol_explain = "No crossover to confirm. Volume is shown for context."

    vol_fig.update_layout(**_chart_layout(280), showlegend=True)
    _chart_axes(vol_fig)

    st.markdown(_chart_card_bg(380), unsafe_allow_html=True)
    st.markdown(_chart_card_header("VOLUME CONFIRMATION", vol_verdict, vol_color), unsafe_allow_html=True)
    _, vol_c, _ = st.columns([0.2, 9.6, 0.2])
    with vol_c:
        st.plotly_chart(vol_fig, use_container_width=True, key="tech_vol_chart",
                        config={"displayModeBar": False})
    st.markdown(_chart_card_explanation(vol_explain), unsafe_allow_html=True)

    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

    # --- Chart 3: RSI Gate ---
    rsi_fig = go.Figure()
    rsi_fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239, 68, 68, 0.06)", line_width=0)
    rsi_fig.add_hrect(y0=0, y1=30, fillcolor="rgba(16, 185, 129, 0.06)", line_width=0)

    if "RSI" in chart_data.columns:
        rsi_fig.add_trace(go.Scatter(
            x=dates, y=chart_data["RSI"].tolist(), name="RSI",
            line=dict(color="#0097A7", width=2), mode="lines", showlegend=False,
        ))

    rsi_fig.add_hline(y=70, line=dict(color="#EF4444", dash="dash", width=1))
    rsi_fig.add_hline(y=30, line=dict(color="#10B981", dash="dash", width=1))
    rsi_fig.add_hline(y=50, line=dict(color="#9CA3AF", dash="dot", width=1))

    # Current RSI marker
    if "RSI" in chart_data.columns and len(dates) > 0:
        rsi_fig.add_trace(go.Scatter(
            x=[dates[-1]], y=[rsi_safe], mode="markers+text",
            marker=dict(size=8, color="#0097A7", line=dict(width=2, color="white")),
            text=[f"{rsi_safe:.0f}"], textposition="top center",
            textfont=dict(size=10, color="#0097A7", family="Inter,-apple-system,BlinkMacSystemFont,sans-serif"),
            showlegend=False,
        ))

    rsi_gate = paper1_details.get("rsi_gate", "n/a")
    if rsi_gate == "passed":
        rsi_verdict, rsi_vcolor = "Gate Passed", "#10B981"
        rsi_explain = f"RSI at {rsi_safe:.0f} is within acceptable range. The signal is not blocked."
    elif rsi_gate == "blocked_overbought":
        rsi_verdict, rsi_vcolor = "Blocked \u2014 Overbought", "#EF4444"
        rsi_explain = f"RSI at {rsi_safe:.0f} exceeds 70 (overbought). Buy signal is blocked to prevent chasing."
    elif rsi_gate == "blocked_oversold":
        rsi_verdict, rsi_vcolor = "Blocked \u2014 Oversold", "#EF4444"
        rsi_explain = f"RSI at {rsi_safe:.0f} is below 30 (oversold). Sell signal is blocked to prevent panic selling."
    else:
        rsi_verdict, rsi_vcolor = "No Gate Applied", "#94A3B8"
        rsi_explain = f"RSI at {rsi_safe:.0f}. No crossover-based signal to gate."

    rsi_fig.update_layout(**_chart_layout(280), showlegend=False)
    rsi_fig.update_yaxes(range=[0, 100], showgrid=True, gridcolor="#F1F5F9",
                          tickfont=dict(size=10, color="#94A3B8"))
    rsi_fig.update_xaxes(showgrid=False, showline=True, linecolor="#E8EDF2",
                          tickfont=dict(size=10, color="#94A3B8"))

    st.markdown(_chart_card_bg(380), unsafe_allow_html=True)
    st.markdown(_chart_card_header("RSI GATE", rsi_verdict, rsi_vcolor), unsafe_allow_html=True)
    _, rsi_c, _ = st.columns([0.2, 9.6, 0.2])
    with rsi_c:
        st.plotly_chart(rsi_fig, use_container_width=True, key="tech_rsi_chart",
                        config={"displayModeBar": False})
    st.markdown(_chart_card_explanation(rsi_explain), unsafe_allow_html=True)

    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # SECTION 2: SUPPORTING INDICATORS (MACD + Bollinger Bands side by side)
    # =========================================================================

    # --- MACD ---
    macd_fig = go.Figure()
    if "MACD_HIST" in chart_data.columns:
        hist_vals = chart_data["MACD_HIST"].tolist()
        hist_colors = [
            "#10B981" if (v is not None and v >= 0) else "#FF6B6B"
            for v in hist_vals
        ]
        macd_fig.add_trace(go.Bar(
            x=dates, y=hist_vals, name="Histogram",
            marker_color=hist_colors, opacity=0.5, showlegend=False,
        ))
    if "MACD" in chart_data.columns:
        macd_fig.add_trace(go.Scatter(
            x=dates, y=chart_data["MACD"].tolist(), name="MACD",
            line=dict(color="#0097A7", width=2),
        ))
    if "MACD_SIGNAL" in chart_data.columns:
        macd_fig.add_trace(go.Scatter(
            x=dates, y=chart_data["MACD_SIGNAL"].tolist(), name="Signal",
            line=dict(color="#FF6B6B", width=2),
        ))
    macd_fig.add_hline(y=0, line=dict(color="#9CA3AF", dash="dot", width=1))

    macd_val = float(chart_data["MACD"].iloc[-1]) if "MACD" in chart_data.columns else 0
    macd_sig = float(chart_data["MACD_SIGNAL"].iloc[-1]) if "MACD_SIGNAL" in chart_data.columns else 0
    if macd_val > macd_sig:
        macd_verdict, macd_vcolor = "Bullish", "#10B981"
        macd_explain = "MACD is above the signal line \u2014 momentum favours buyers."
    else:
        macd_verdict, macd_vcolor = "Bearish", "#FF6B6B"
        macd_explain = "MACD is below the signal line \u2014 momentum favours sellers."

    macd_fig.update_layout(**_chart_layout(250), showlegend=True)
    _chart_axes(macd_fig)

    # --- Bollinger Bands ---
    bb_fig = go.Figure()
    # Check column names (Streamlit compute_indicators uses BB_UPPER/BB_MID/BB_LOWER)
    bb_cols = {"upper": None, "mid": None, "lower": None}
    for u in ["BB_Upper", "BB_UPPER"]:
        if u in chart_data.columns:
            bb_cols["upper"] = u
    for m in ["BB_Mid", "BB_MID"]:
        if m in chart_data.columns:
            bb_cols["mid"] = m
    for l in ["BB_Lower", "BB_LOWER"]:
        if l in chart_data.columns:
            bb_cols["lower"] = l

    has_bb = all(bb_cols[k] is not None for k in ("upper", "mid", "lower"))

    if has_bb:
        upper_col = bb_cols["upper"]
        mid_col = bb_cols["mid"]
        lower_col = bb_cols["lower"]
        # Shaded band
        bb_fig.add_trace(go.Scatter(
            x=dates, y=chart_data[upper_col].tolist(), name="Upper Band",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ))
        bb_fig.add_trace(go.Scatter(
            x=dates, y=chart_data[lower_col].tolist(), name="Lower Band",
            line=dict(width=0), fill="tonexty",
            fillcolor="rgba(0, 151, 167, 0.06)", showlegend=False, hoverinfo="skip",
        ))
        # Band lines
        bb_fig.add_trace(go.Scatter(
            x=dates, y=chart_data[upper_col].tolist(), name="Upper",
            line=dict(color="#94A3B8", width=1, dash="dot"), mode="lines",
        ))
        bb_fig.add_trace(go.Scatter(
            x=dates, y=chart_data[mid_col].tolist(), name="Mid",
            line=dict(color="#94A3B8", width=1), mode="lines",
        ))
        bb_fig.add_trace(go.Scatter(
            x=dates, y=chart_data[lower_col].tolist(), name="Lower",
            line=dict(color="#94A3B8", width=1, dash="dot"), mode="lines",
        ))

    # Price on top
    bb_fig.add_trace(go.Scatter(
        x=dates, y=chart_data["Close"].tolist(), name="Price",
        line=dict(color="#0F172A", width=2), mode="lines",
    ))

    # BB verdict
    if has_bb:
        curr = float(chart_data["Close"].iloc[-1])
        upper = float(chart_data[bb_cols["upper"]].iloc[-1])
        lower = float(chart_data[bb_cols["lower"]].iloc[-1])
        bb_range = upper - lower if upper != lower else 1
        pos = (curr - lower) / bb_range
        if pos > 0.85:
            bb_verdict, bb_vcolor = "Near Upper Band", "#F59E0B"
            bb_explain = "Price is near the upper Bollinger Band \u2014 potential resistance or overbought condition."
        elif pos < 0.15:
            bb_verdict, bb_vcolor = "Near Lower Band", "#10B981"
            bb_explain = "Price is near the lower Bollinger Band \u2014 potential support or oversold condition."
        else:
            bb_verdict, bb_vcolor = "Within Range", "#94A3B8"
            bb_explain = "Price is within the Bollinger Bands \u2014 no extreme condition detected."
    else:
        bb_verdict, bb_vcolor = "No Data", "#94A3B8"
        bb_explain = "Bollinger Bands data not available."

    bb_fig.update_layout(**_chart_layout(250), showlegend=True)
    _chart_axes(bb_fig, y_prefix="$")

    # Render MACD + BB side by side
    macd_col, bb_col = st.columns(2)

    with macd_col:
        st.markdown(_chart_card_bg(350), unsafe_allow_html=True)
        st.markdown(_chart_card_header("MACD", macd_verdict, macd_vcolor), unsafe_allow_html=True)
        st.plotly_chart(macd_fig, use_container_width=True, key="tech_macd_chart",
                        config={"displayModeBar": False})
        st.markdown(_chart_card_explanation(macd_explain), unsafe_allow_html=True)

    with bb_col:
        st.markdown(_chart_card_bg(350), unsafe_allow_html=True)
        st.markdown(_chart_card_header("BOLLINGER BANDS", bb_verdict, bb_vcolor), unsafe_allow_html=True)
        st.plotly_chart(bb_fig, use_container_width=True, key="tech_bb_chart",
                        config={"displayModeBar": False})
        st.markdown(_chart_card_explanation(bb_explain), unsafe_allow_html=True)

    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # SECTION 3: KEY LEVELS
    # =========================================================================
    current_price = float(price_data["Close"].iloc[-1])
    high_52w = float(price_data["High"].max())
    low_52w = float(price_data["Low"].min())
    price_range = high_52w - low_52w if high_52w != low_52w else 1
    range_pct = (current_price - low_52w) / price_range * 100

    sma50 = float(price_data["SMA50"].iloc[-1]) if "SMA50" in price_data.columns and pd.notna(price_data["SMA50"].iloc[-1]) else None
    sma200 = float(price_data["SMA200"].iloc[-1]) if "SMA200" in price_data.columns and pd.notna(price_data["SMA200"].iloc[-1]) else None

    support_tag = ""
    if sma50 is not None:
        support_tag = (
            f'<div style="display:inline-block;padding:4px 12px;background:#F8FAFB;border-radius:8px;">'
            f'<span style="font-size:11px;font-weight:500;color:#94A3B8;margin-right:6px;'
            f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">Support (SMA50)</span>'
            f'<span style="font-size:12px;font-weight:600;color:#10B981;'
            f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">${sma50:.2f}</span></div>'
        )
    resistance_tag = ""
    if sma200 is not None:
        resistance_tag = (
            f'<div style="display:inline-block;padding:4px 12px;background:#F8FAFB;border-radius:8px;">'
            f'<span style="font-size:11px;font-weight:500;color:#94A3B8;margin-right:6px;'
            f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">Resistance (SMA200)</span>'
            f'<span style="font-size:12px;font-weight:600;color:#FF6B6B;'
            f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">${sma200:.2f}</span></div>'
        )

    bar_width = max(2, min(98, range_pct))

    st.markdown(f"""
    <div style="{CARD}">
        <div style="{LABEL} margin-bottom:10px;">Key Levels</div>
        <div style="margin-bottom:14px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="font-size:11px;color:#94A3B8;font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">
                    52W Low ${low_52w:.2f}</span>
                <span style="font-size:11px;color:#94A3B8;font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">
                    52W High ${high_52w:.2f}</span>
            </div>
            <div style="background:#F1F5F9;border-radius:6px;height:8px;overflow:hidden;">
                <div style="width:{bar_width:.0f}%;height:100%;background:#0097A7;border-radius:6px;position:relative;"></div>
            </div>
            <div style="font-size:11px;color:#64748B;margin-top:4px;
                        font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">
                Current: ${current_price:.2f} ({range_pct:.0f}% of range)</div>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
            {support_tag}
            {resistance_tag}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # SECTION 4: AI MODEL LENS (conditional)
    # =========================================================================
    if rl_prediction is not None:
        rl_action_map = {0: "BUY", 1: "SELL", 2: "HOLD"}
        rl_signal = paper1_details.get("rl_signal", rl_action_map.get(rl_prediction, "HOLD"))
        rl_agrees = paper1_details.get("rl_agrees")

        rec_colors = {"BUY": "#10B981", "SELL": "#FF6B6B", "HOLD": "#F59E0B"}
        rl_color = rec_colors.get(rl_signal, "#F59E0B")

        ema_signal_val = paper1_details.get("ema_cross_signal", 0)
        atv_slope_val = paper1_details.get("atv_slope", 0)
        rsi_val = paper1_details.get("rsi", rsi_safe)

        # Get 1d/5d returns and rel volume from price data
        ret_1d = 0
        ret_5d = 0
        rel_vol = 1.0
        if len(price_data) > 1:
            ret_1d = (float(price_data["Close"].iloc[-1]) / float(price_data["Close"].iloc[-2]) - 1) * 100
        if len(price_data) > 5:
            ret_5d = (float(price_data["Close"].iloc[-1]) / float(price_data["Close"].iloc[-6]) - 1) * 100
        if "Rel_Volume" in price_data.columns and pd.notna(price_data["Rel_Volume"].iloc[-1]):
            rel_vol = float(price_data["Rel_Volume"].iloc[-1])

        # Agreement
        from models import generate_recommendation_paper1
        rule_rec_data = generate_recommendation_paper1(
            tech_score, volume_score, rsi_safe,
            "Bull", selected, info, time_horizon="long",
            price_data=price_data, rl_prediction=rl_prediction,
        )
        rule_rec = rule_rec_data.get("recommendation", "HOLD")
        agrees = rl_agrees if rl_agrees is not None else (rl_signal == rule_rec)
        agree_text = "Agrees" if agrees else "Disagrees"
        agree_color = "#10B981" if agrees else "#F59E0B"

        def _rl_row(lbl, val):
            return (
                f'<div style="display:flex;justify-content:space-between;padding:6px 0;'
                f'border-bottom:1px solid #E8EDF2;">'
                f'<span style="font-size:12px;color:#64748B;font-weight:450;'
                f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{lbl}</span>'
                f'<span style="font-size:12px;color:#1E293B;font-weight:600;'
                f'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{val}</span></div>'
            )

        st.markdown(f"""
        <div style="{CARD}">
            <div style="{LABEL} margin-bottom:10px;">AI Model Lens (PPO Agent)</div>
            <div style="font-size:11px;color:#94A3B8;font-weight:600;text-transform:uppercase;
                        letter-spacing:0.04em;margin-bottom:6px;
                        font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">RL Input Features</div>
            {_rl_row("EMA Signal", str(ema_signal_val))}
            {_rl_row("ATV Slope", f"{atv_slope_val:,.0f}")}
            {_rl_row("1-Day Return", f"{ret_1d:+.2f}%")}
            {_rl_row("5-Day Return", f"{ret_5d:+.2f}%")}
            {_rl_row("RSI", f"{rsi_val:.1f}")}
            {_rl_row("Relative Volume", f"{rel_vol:.2f}x")}
            <div style="height:12px;"></div>
            <div style="margin-bottom:8px;">
                <span style="font-size:12px;color:#64748B;font-weight:500;margin-right:8px;
                             font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">Action: </span>
                {_verdict_badge_html(rl_signal, rl_color)}
            </div>
            <div>
                <span style="font-size:12px;color:#64748B;font-weight:500;margin-right:8px;
                             font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">vs Rule-Based: </span>
                <span style="font-size:12px;font-weight:700;color:{agree_color};
                             font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;">{agree_text}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
