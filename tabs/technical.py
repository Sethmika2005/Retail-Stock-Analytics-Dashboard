# Technical tab — charts with verdicts for SMA, Volume, RSI, MACD, Bollinger

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from models import RL_ACTION_MAP
from styles import (
    CARD, LABEL, FONT, TEAL, CORAL, SUCCESS, WARNING, DANGER, MUTED, TEXT, BORDER,
    badge_html, chart_layout, chart_axes, chart_card_bg, chart_card_header, explanation_html,
)


# Find SMA20/SMA50 crossover points
def _find_sma_crossovers(df):
    if "SMA20" not in df.columns or "SMA50" not in df.columns:
        return [], []
    golden, death = [], []
    s20, s50 = df["SMA20"].values, df["SMA50"].values
    dates, prices = df["Date"].values, df["Close"].values
    for i in range(1, len(df)):
        if pd.isna(s20[i]) or pd.isna(s50[i]) or pd.isna(s20[i-1]) or pd.isna(s50[i-1]):
            continue  # SMAs need 20/50 days of history — skip crossover detection until enough data exists
        if s20[i-1] <= s50[i-1] and s20[i] > s50[i]:
            golden.append((dates[i], prices[i]))
        if s20[i-1] >= s50[i-1] and s20[i] < s50[i]:
            death.append((dates[i], prices[i]))
    return golden, death


def render(selected, price_data, info, last_row,
           volume_score=0, volume_details=None,
           rule_details=None, rl_prediction=None, rsi_value=None):

    rule_details = rule_details or {}
    rsi_safe = rsi_value if rsi_value is not None and not pd.isna(rsi_value) else 50  # default to neutral RSI if missing so UI doesn't break
    # tail(252) = last 252 trading days (~1 year of data) for the charts
    chart_data = price_data.tail(252).copy()
    dates = chart_data["Date"].tolist()

    # -- SMA Crossover chart --
    sma_fig = go.Figure()
    sma_fig.add_trace(go.Scatter(x=dates, y=chart_data["Close"].tolist(), name="Price",
                                  line=dict(color="#0F172A", width=2), mode="lines"))
    if "SMA20" in chart_data.columns:
        sma_fig.add_trace(go.Scatter(x=dates, y=chart_data["SMA20"].tolist(), name="SMA-20",
                                      line=dict(color=TEAL, width=1.5), mode="lines"))
    if "SMA50" in chart_data.columns:
        sma_fig.add_trace(go.Scatter(x=dates, y=chart_data["SMA50"].tolist(), name="SMA-50",
                                      line=dict(color=CORAL, width=1.5), mode="lines"))

    for d, p in _find_sma_crossovers(chart_data)[0]:
        sma_fig.add_annotation(x=pd.Timestamp(d), y=float(p), text="\u2191 Golden", showarrow=True,
                               arrowhead=2, arrowwidth=2, arrowcolor=SUCCESS,
                               font=dict(size=9, color=SUCCESS), bgcolor="white",
                               bordercolor=SUCCESS, borderwidth=1, ax=0, ay=-30)
    for d, p in _find_sma_crossovers(chart_data)[1]:
        sma_fig.add_annotation(x=pd.Timestamp(d), y=float(p), text="\u2193 Death", showarrow=True,
                               arrowhead=2, arrowwidth=2, arrowcolor=DANGER,
                               font=dict(size=9, color=DANGER), bgcolor="white",
                               bordercolor=DANGER, borderwidth=1, ax=0, ay=30)

    ct = rule_details.get("crossover_type", "none")
    if ct == "golden_cross":
        sma_verdict, sma_color = "Golden Cross", SUCCESS
        sma_explain = "SMA tracks the average closing price. SMA-20 crossed above SMA-50, indicating upward momentum."
    elif ct == "death_cross":
        sma_verdict, sma_color = "Death Cross", DANGER
        sma_explain = "SMA tracks the average closing price. SMA-20 crossed below SMA-50, indicating downward momentum."
    else:
        sma_verdict, sma_color = "No Crossover", MUTED
        trend = rule_details.get("sma_trend", "neutral")
        sma_explain = f"No crossover between SMA-20 and SMA-50. Current trend bias is {trend}."

    sma_fig.update_layout(**chart_layout(280), showlegend=True)
    chart_axes(sma_fig, y_prefix="$")

    st.markdown(chart_card_bg(380), unsafe_allow_html=True)
    st.markdown(chart_card_header("SMA CROSSOVER", sma_verdict, sma_color), unsafe_allow_html=True)
    _, c, _ = st.columns([0.2, 9.6, 0.2])
    with c:
        st.plotly_chart(sma_fig, use_container_width=True, key="tech_sma_chart", config={"displayModeBar": False})
    st.markdown(explanation_html(sma_explain), unsafe_allow_html=True)
    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

    # -- Volume Confirmation chart --
    vol_fig = go.Figure()
    if "Volume" in chart_data.columns:
        close_vals = chart_data["Close"].values
        # np.roll shifts the array by 1 so each day lines up with its previous day
        # then set first element manually (no "previous" day for day 0)
        prev_close = np.roll(close_vals, 1); prev_close[0] = close_vals[0]
        # green bars for up days, red for down — zip pairs each day with its previous
        vol_colors = ["rgba(16,185,129,0.5)" if c >= p else "rgba(255,107,107,0.5)"
                      for c, p in zip(close_vals, prev_close)]
        vol_fig.add_trace(go.Bar(x=dates, y=chart_data["Volume"].tolist(), name="Volume",
                                  marker_color=vol_colors, showlegend=False))
    if "Volume_SMA20" in chart_data.columns:
        vol_fig.add_trace(go.Scatter(x=dates, y=chart_data["Volume_SMA20"].tolist(), name="Volume SMA-20",
                                      line=dict(color=TEAL, width=2), mode="lines"))

    atv_confirmed = rule_details.get("atv_confirmed", False)
    if ct in ("golden_cross", "death_cross"):
        if atv_confirmed:
            vol_verdict, vol_color = "Volume Confirms", SUCCESS
            vol_explain = "Rising volume alongside the trend suggests strong conviction behind the move."
        else:
            vol_verdict, vol_color = "Volume Diverging", WARNING
            vol_explain = "Volume is not rising with the trend, suggesting weaker conviction."
    else:
        vol_verdict, vol_color = "No Signal", MUTED
        vol_explain = "No active trend signal to confirm — volume shown for reference."

    vol_fig.update_layout(**chart_layout(280), showlegend=True)
    chart_axes(vol_fig)

    st.markdown(chart_card_bg(380), unsafe_allow_html=True)
    st.markdown(chart_card_header("VOLUME CONFIRMATION", vol_verdict, vol_color), unsafe_allow_html=True)
    _, c, _ = st.columns([0.2, 9.6, 0.2])
    with c:
        st.plotly_chart(vol_fig, use_container_width=True, key="tech_vol_chart", config={"displayModeBar": False})
    st.markdown(explanation_html(vol_explain), unsafe_allow_html=True)
    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

    # -- RSI Gate chart --
    rsi_fig = go.Figure()
    rsi_fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239,68,68,0.06)", line_width=0)
    rsi_fig.add_hrect(y0=0, y1=30, fillcolor="rgba(16,185,129,0.06)", line_width=0)
    if "RSI" in chart_data.columns:
        rsi_fig.add_trace(go.Scatter(x=dates, y=chart_data["RSI"].tolist(), name="RSI",
                                      line=dict(color=TEAL, width=2), mode="lines", showlegend=False))
    rsi_fig.add_hline(y=70, line=dict(color=DANGER, dash="dash", width=1))
    rsi_fig.add_hline(y=30, line=dict(color=SUCCESS, dash="dash", width=1))
    rsi_fig.add_hline(y=50, line=dict(color="#9CA3AF", dash="dot", width=1))

    if "RSI" in chart_data.columns and len(dates) > 0:
        rsi_fig.add_trace(go.Scatter(
            x=[dates[-1]], y=[rsi_safe], mode="markers+text",
            marker=dict(size=8, color=TEAL, line=dict(width=2, color="white")),
            text=[f"{rsi_safe:.0f}"], textposition="top center",
            textfont=dict(size=10, color=TEAL, family=FONT), showlegend=False))

    rsi_gate = rule_details.get("rsi_gate", "n/a")
    if rsi_gate == "passed":
        rsi_verdict, rsi_vcolor = "Gate Passed", SUCCESS
        rsi_explain = f"RSI at {rsi_safe:.0f} is within normal range (30\u201370) — not overbought or oversold."
    elif rsi_gate == "blocked_overbought":
        rsi_verdict, rsi_vcolor = "Blocked \u2014 Overbought", DANGER
        rsi_explain = f"RSI at {rsi_safe:.0f} is above 70 — stock has risen rapidly, may pull back."
    elif rsi_gate == "blocked_oversold":
        rsi_verdict, rsi_vcolor = "Blocked \u2014 Oversold", DANGER
        rsi_explain = f"RSI at {rsi_safe:.0f} is below 30 — stock has fallen sharply, may recover."
    else:
        rsi_verdict, rsi_vcolor = "No Gate Applied", MUTED
        rsi_explain = f"RSI at {rsi_safe:.0f}, no active signal to evaluate against."

    rsi_fig.update_layout(**chart_layout(280), showlegend=False)
    rsi_fig.update_yaxes(range=[0, 100], showgrid=True, gridcolor="#F1F5F9",
                          tickfont=dict(size=10, color=MUTED))
    rsi_fig.update_xaxes(showgrid=False, showline=True, linecolor=BORDER,
                          tickfont=dict(size=10, color=MUTED))

    st.markdown(chart_card_bg(380), unsafe_allow_html=True)
    st.markdown(chart_card_header("RSI GATE", rsi_verdict, rsi_vcolor), unsafe_allow_html=True)
    _, c, _ = st.columns([0.2, 9.6, 0.2])
    with c:
        st.plotly_chart(rsi_fig, use_container_width=True, key="tech_rsi_chart", config={"displayModeBar": False})
    st.markdown(explanation_html(rsi_explain), unsafe_allow_html=True)
    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

    # -- MACD + Bollinger side by side --
    macd_fig = go.Figure()
    if "MACD_HIST" in chart_data.columns:
        hist_vals = chart_data["MACD_HIST"].tolist()
        macd_fig.add_trace(go.Bar(x=dates, y=hist_vals, name="Histogram",
                                   marker_color=[SUCCESS if v and v >= 0 else CORAL for v in hist_vals],
                                   opacity=0.5, showlegend=False))
    if "MACD" in chart_data.columns:
        macd_fig.add_trace(go.Scatter(x=dates, y=chart_data["MACD"].tolist(), name="MACD",
                                       line=dict(color=TEAL, width=2)))
    if "MACD_SIGNAL" in chart_data.columns:
        macd_fig.add_trace(go.Scatter(x=dates, y=chart_data["MACD_SIGNAL"].tolist(), name="Signal",
                                       line=dict(color=CORAL, width=2)))
    macd_fig.add_hline(y=0, line=dict(color="#9CA3AF", dash="dot", width=1))

    macd_val = float(chart_data["MACD"].iloc[-1]) if "MACD" in chart_data.columns else 0
    macd_sig = float(chart_data["MACD_SIGNAL"].iloc[-1]) if "MACD_SIGNAL" in chart_data.columns else 0
    if macd_val > macd_sig:
        macd_verdict, macd_vcolor = "Bullish", SUCCESS
        macd_explain = "MACD is above its signal line — upward momentum building."
    else:
        macd_verdict, macd_vcolor = "Bearish", CORAL
        macd_explain = "MACD is below its signal line — downward momentum building."

    macd_fig.update_layout(**chart_layout(250), showlegend=True)
    chart_axes(macd_fig)

    # Bollinger Bands
    bb_fig = go.Figure()
    bb_cols = {}
    # column names vary depending on how indicators were computed — check both formats
    for key, names in [("upper", ["BB_Upper", "BB_UPPER"]), ("mid", ["BB_Mid", "BB_MID"]),
                        ("lower", ["BB_Lower", "BB_LOWER"])]:
        for n in names:
            if n in chart_data.columns:
                bb_cols[key] = n; break

    has_bb = len(bb_cols) == 3
    if has_bb:
        # two invisible traces (width=0) with fill="tonexty" creates the shaded band between them
        bb_fig.add_trace(go.Scatter(x=dates, y=chart_data[bb_cols["upper"]].tolist(),
                                     line=dict(width=0), showlegend=False, hoverinfo="skip"))
        bb_fig.add_trace(go.Scatter(x=dates, y=chart_data[bb_cols["lower"]].tolist(),
                                     line=dict(width=0), fill="tonexty",
                                     fillcolor="rgba(0,151,167,0.06)", showlegend=False, hoverinfo="skip"))
        for key, name, dash in [("upper", "Upper", "dot"), ("mid", "Mid", None), ("lower", "Lower", "dot")]:
            bb_fig.add_trace(go.Scatter(x=dates, y=chart_data[bb_cols[key]].tolist(), name=name,
                                         line=dict(color=MUTED, width=1, dash=dash), mode="lines"))

    bb_fig.add_trace(go.Scatter(x=dates, y=chart_data["Close"].tolist(), name="Price",
                                 line=dict(color="#0F172A", width=2), mode="lines"))

    if has_bb:
        curr = float(chart_data["Close"].iloc[-1])
        upper = float(chart_data[bb_cols["upper"]].iloc[-1])
        lower = float(chart_data[bb_cols["lower"]].iloc[-1])
        bb_range = upper - lower if upper != lower else 1
        # pos = where price sits within the band (0 = at lower, 1 = at upper)
        pos = (curr - lower) / bb_range
        if pos > 0.85:
            bb_verdict, bb_vcolor = "Near Upper Band", WARNING
            bb_explain = "Price near upper band — may be stretched above typical range."
        elif pos < 0.15:
            bb_verdict, bb_vcolor = "Near Lower Band", SUCCESS
            bb_explain = "Price near lower band — may be compressed below typical range."
        else:
            bb_verdict, bb_vcolor = "Within Range", MUTED
            bb_explain = "Price within Bollinger Bands — normal trading conditions."
    else:
        bb_verdict, bb_vcolor = "No Data", MUTED
        bb_explain = "Bollinger Bands data not available."

    bb_fig.update_layout(**chart_layout(250), showlegend=True)
    chart_axes(bb_fig, y_prefix="$")

    macd_col, bb_col = st.columns(2)
    with macd_col:
        st.markdown(chart_card_bg(350), unsafe_allow_html=True)
        st.markdown(chart_card_header("MACD", macd_verdict, macd_vcolor), unsafe_allow_html=True)
        st.plotly_chart(macd_fig, use_container_width=True, key="tech_macd_chart", config={"displayModeBar": False})
        st.markdown(explanation_html(macd_explain), unsafe_allow_html=True)
    with bb_col:
        st.markdown(chart_card_bg(350), unsafe_allow_html=True)
        st.markdown(chart_card_header("BOLLINGER BANDS", bb_verdict, bb_vcolor), unsafe_allow_html=True)
        st.plotly_chart(bb_fig, use_container_width=True, key="tech_bb_chart", config={"displayModeBar": False})
        st.markdown(explanation_html(bb_explain), unsafe_allow_html=True)

    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

    # -- AI Model Lens --
    if rl_prediction is not None:
        rl_signal = rule_details.get("rl_signal", RL_ACTION_MAP.get(rl_prediction, "HOLD"))
        rl_agrees = rule_details.get("rl_agrees")

        rec_colors = {"BUY": SUCCESS, "SELL": CORAL, "HOLD": WARNING}
        rl_color = rec_colors.get(rl_signal, WARNING)

        sma_signal_val = rule_details.get("sma_cross_signal", 0)
        atv_slope_val = rule_details.get("atv_slope", 0)
        rsi_val = rule_details.get("rsi", rsi_safe)

        ret_1d = ret_5d = 0
        rel_vol = 1.0
        if len(price_data) > 1:
            ret_1d = (float(price_data["Close"].iloc[-1]) / float(price_data["Close"].iloc[-2]) - 1) * 100
        if len(price_data) > 5:
            ret_5d = (float(price_data["Close"].iloc[-1]) / float(price_data["Close"].iloc[-6]) - 1) * 100
        if "Rel_Volume" in price_data.columns and pd.notna(price_data["Rel_Volume"].iloc[-1]):
            rel_vol = float(price_data["Rel_Volume"].iloc[-1])

        from models import generate_hybrid_recommendation
        rule_rec_data = generate_hybrid_recommendation(
            volume_score, rsi_safe, "Bull", selected, info,
            time_horizon="long", price_data=price_data, rl_prediction=rl_prediction)
        rule_rec = rule_rec_data.get("recommendation", "HOLD")
        agrees = rl_agrees if rl_agrees is not None else (rl_signal == rule_rec)
        agree_text = "Agrees" if agrees else "Disagrees"
        agree_color = SUCCESS if agrees else WARNING

        def _row(lbl, val):
            return (f'<div style="display:flex;justify-content:space-between;padding:6px 0;'
                    f'border-bottom:1px solid {BORDER};">'
                    f'<span style="font-size:12px;color:{MUTED};font-weight:450;font-family:{FONT};">{lbl}</span>'
                    f'<span style="font-size:12px;color:{TEXT};font-weight:600;font-family:{FONT};">{val}</span></div>')

        def _sma_tag(label, val):
            if val is None:
                return ""
            return (f'<div style="display:inline-block;padding:4px 12px;background:#F8FAFB;border-radius:8px;">'
                    f'<span style="font-size:11px;font-weight:500;color:{MUTED};margin-right:6px;'
                    f'font-family:{FONT};">{label}</span>'
                    f'<span style="font-size:12px;font-weight:600;color:{TEAL};font-family:{FONT};">${val:.2f}</span></div>')

        sma20_v = float(price_data["SMA20"].iloc[-1]) if "SMA20" in price_data.columns and pd.notna(price_data["SMA20"].iloc[-1]) else None
        sma50_v = float(price_data["SMA50"].iloc[-1]) if "SMA50" in price_data.columns and pd.notna(price_data["SMA50"].iloc[-1]) else None

        st.markdown(f"""
        <div style="{CARD} padding:16px 20px;">
            <div style="{LABEL} margin-bottom:10px;">What the AI Model Sees</div>
            {_row("SMA Signal", str(sma_signal_val))}
            {_row("ATV Slope", f"{atv_slope_val:,.0f}")}
            {_row("1-Day Return", f"{ret_1d:+.2f}%")}
            {_row("5-Day Return", f"{ret_5d:+.2f}%")}
            {_row("RSI", f"{rsi_val:.1f}")}
            {_row("Relative Volume", f"{rel_vol:.2f}x")}
            <div style="height:12px;"></div>
            <div style="margin-bottom:8px;">
                <span style="font-size:12px;color:{MUTED};font-weight:500;margin-right:8px;font-family:{FONT};">Action: </span>
                {badge_html(rl_signal, rl_color)}
            </div>
            <div style="margin-bottom:14px;">
                <span style="font-size:12px;color:{MUTED};font-weight:500;margin-right:8px;font-family:{FONT};">vs Rule-Based: </span>
                <span style="font-size:12px;font-weight:700;color:{agree_color};font-family:{FONT};">{agree_text}</span>
            </div>
            <div style="display:flex;gap:10px;flex-wrap:wrap;">
                {_sma_tag("SMA 20", sma20_v)}
                {_sma_tag("SMA 50", sma50_v)}
            </div>
        </div>
        """, unsafe_allow_html=True)
