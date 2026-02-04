# =============================================================================
# TECHNICAL TAB - Simplified with 3 key charts and time period toggle
# =============================================================================

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from components import get_status_color

# Chart styling constants
CHART_FONT_COLOR = "#1F2937"
CHART_AXIS_COLOR = "#374151"
LEGEND_FONT_COLOR = "#1F2937"


def find_crossovers(df):
    """Find golden cross and death cross points in the data."""
    if "SMA50" not in df.columns or "SMA200" not in df.columns:
        return [], []

    golden_crosses = []
    death_crosses = []

    sma50 = df["SMA50"].values
    sma200 = df["SMA200"].values
    dates = df["Date"].values
    prices = df["Close"].values

    for i in range(1, len(df)):
        if pd.isna(sma50[i]) or pd.isna(sma200[i]) or pd.isna(sma50[i-1]) or pd.isna(sma200[i-1]):
            continue

        # Golden Cross: SMA50 crosses above SMA200
        if sma50[i-1] <= sma200[i-1] and sma50[i] > sma200[i]:
            golden_crosses.append((dates[i], prices[i], sma50[i]))

        # Death Cross: SMA50 crosses below SMA200
        if sma50[i-1] >= sma200[i-1] and sma50[i] < sma200[i]:
            death_crosses.append((dates[i], prices[i], sma50[i]))

    return golden_crosses, death_crosses


def render(selected, price_data, info, tech_score, tech_details, last_row):
    """Render the Technical Indicators tab content."""
    st.subheader("Technical Analysis")

    # =========================================================================
    # TIME PERIOD TOGGLE
    # =========================================================================
    period_col1, period_col2 = st.columns([3, 1])

    with period_col2:
        time_period = st.radio(
            "Time Period",
            options=["3M", "1Y", "Max"],
            horizontal=True,
            index=1,
            label_visibility="collapsed"
        )

    # Filter data based on selected time period
    if time_period == "3M":
        chart_data = price_data.tail(63).copy()
        period_label = "3 Months"
    elif time_period == "1Y":
        chart_data = price_data.tail(252).copy()
        period_label = "1 Year"
    else:
        chart_data = price_data.copy()
        period_label = "All Time"

    st.caption(f"Showing {period_label} ({len(chart_data)} days)")

    # Get current values
    current_price = price_data["Close"].iloc[-1]
    sma50 = price_data["SMA50"].iloc[-1] if "SMA50" in price_data.columns else None
    sma200 = price_data["SMA200"].iloc[-1] if "SMA200" in price_data.columns else None

    st.markdown("---")

    # =========================================================================
    # 1. TREND CHART
    # =========================================================================
    st.markdown("### Trend")

    # Find crossovers in the chart data
    golden_crosses, death_crosses = find_crossovers(chart_data)

    # Create trend chart
    trend_fig = go.Figure()

    # Get x and y data
    dates = chart_data["Date"].tolist()
    close_prices = chart_data["Close"].tolist()

    # Add Price line (most important - add last so it's on top)
    trend_fig.add_trace(go.Scatter(
        x=dates,
        y=close_prices,
        name="Price",
        line=dict(color="#000000", width=2.5),
        mode='lines'
    ))

    # Add SMA 50 if available
    if "SMA50" in chart_data.columns:
        sma50_data = chart_data["SMA50"].tolist()
        trend_fig.add_trace(go.Scatter(
            x=dates,
            y=sma50_data,
            name="SMA 50",
            line=dict(color="#3B82F6", width=2, dash='solid'),
            mode='lines',
            connectgaps=False
        ))

    # Add SMA 200 if available
    if "SMA200" in chart_data.columns:
        sma200_data = chart_data["SMA200"].tolist()
        trend_fig.add_trace(go.Scatter(
            x=dates,
            y=sma200_data,
            name="SMA 200",
            line=dict(color="#F59E0B", width=2, dash='solid'),
            mode='lines',
            connectgaps=False
        ))

    # Add Golden Cross markers
    for date, price, sma_val in golden_crosses:
        trend_fig.add_annotation(
            x=date, y=sma_val,
            text="Golden Cross",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#10B981",
            font=dict(size=10, color="#10B981"),
            bgcolor="white",
            bordercolor="#10B981",
            borderwidth=1,
            ax=0, ay=-40
        )

    # Add Death Cross markers
    for date, price, sma_val in death_crosses:
        trend_fig.add_annotation(
            x=date, y=sma_val,
            text="Death Cross",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#EF4444",
            font=dict(size=10, color="#EF4444"),
            bgcolor="white",
            bordercolor="#EF4444",
            borderwidth=1,
            ax=0, ay=40
        )

    trend_fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=40, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(color=LEGEND_FONT_COLOR, size=12)
        ),
        font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif", size=12),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode="x unified"
    )
    trend_fig.update_xaxes(
        showgrid=False,
        showline=True,
        linecolor='#E5E7EB',
        tickfont=dict(color=CHART_AXIS_COLOR, size=11)
    )
    trend_fig.update_yaxes(
        showgrid=True,
        gridcolor='#E5E7EB',
        tickfont=dict(color=CHART_AXIS_COLOR, size=11),
        tickprefix="$"
    )

    st.plotly_chart(trend_fig, use_container_width=True)

    # Key values row
    if sma50 and sma200:
        is_golden = sma50 > sma200
        cross_status = "Golden Cross" if is_golden else "Death Cross"
        cross_color = "#10B981" if is_golden else "#EF4444"

        val_col1, val_col2, val_col3, val_col4 = st.columns(4)
        with val_col1:
            st.metric("Price", f"${current_price:.2f}")
        with val_col2:
            st.metric("SMA 50", f"${sma50:.2f}")
        with val_col3:
            st.metric("SMA 200", f"${sma200:.2f}")
        with val_col4:
            st.markdown("**Status**")
            st.markdown(f"<span style='color:{cross_color}; font-weight:600;'>{cross_status}</span>", unsafe_allow_html=True)

    # Hidden explanation
    with st.expander("Understanding Trend Analysis"):
        if sma50 and sma200:
            price_vs_sma50 = ((current_price - sma50) / sma50) * 100
            price_vs_sma200 = ((current_price - sma200) / sma200) * 100

            if sma50 > sma200:
                cross_desc = "**Golden Cross Active:** SMA 50 is above SMA 200, indicating a bullish long-term trend."
            else:
                cross_desc = "**Death Cross Active:** SMA 50 is below SMA 200, indicating a bearish long-term trend."

            if current_price > sma50 > sma200:
                trend_desc = "Price is above both moving averages in a strong uptrend configuration."
            elif current_price > sma50 and current_price > sma200:
                trend_desc = "Price is above both SMAs with bullish momentum."
            elif current_price > sma200:
                trend_desc = "Price is above SMA 200 but below SMA 50 - short-term weakness in longer-term uptrend."
            elif current_price < sma50 < sma200:
                trend_desc = "Price is below both moving averages in a strong downtrend configuration."
            else:
                trend_desc = "Price is in a transitional phase between the moving averages."

            st.markdown(f"""
{cross_desc}

{trend_desc}

**Current Position:**
- Price vs SMA 50: {price_vs_sma50:+.1f}%
- Price vs SMA 200: {price_vs_sma200:+.1f}%

**Key Signals:**
- **Golden Cross:** SMA 50 crosses above SMA 200 - Strong buy signal
- **Death Cross:** SMA 50 crosses below SMA 200 - Strong sell signal
            """)

    st.markdown("---")

    # =========================================================================
    # 2. RSI CHART
    # =========================================================================
    st.markdown("### RSI")

    rsi_val = price_data["RSI"].iloc[-1] if "RSI" in price_data.columns else 50

    # Create RSI chart
    rsi_fig = go.Figure()

    if "RSI" in chart_data.columns:
        rsi_fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239, 68, 68, 0.08)", line_width=0)
        rsi_fig.add_hrect(y0=0, y1=30, fillcolor="rgba(34, 197, 94, 0.08)", line_width=0)

        rsi_dates = chart_data["Date"].tolist()
        rsi_values = chart_data["RSI"].tolist()

        rsi_fig.add_trace(go.Scatter(
            x=rsi_dates,
            y=rsi_values,
            name="RSI",
            line=dict(color="#8B5CF6", width=2),
            mode='lines'
        ))

        rsi_fig.add_hline(y=70, line=dict(color="#EF4444", dash="dash", width=1))
        rsi_fig.add_hline(y=30, line=dict(color="#22C55E", dash="dash", width=1))
        rsi_fig.add_hline(y=50, line=dict(color="#9CA3AF", dash="dot", width=1))

    rsi_fig.update_layout(
        height=250,
        margin=dict(l=10, r=10, t=10, b=30),
        yaxis=dict(range=[0, 100]),
        font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif", size=12),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False,
        hovermode="x unified"
    )
    rsi_fig.update_xaxes(showgrid=False, showline=True, linecolor='#E5E7EB', tickfont=dict(color=CHART_AXIS_COLOR, size=11))
    rsi_fig.update_yaxes(showgrid=True, gridcolor='#E5E7EB', tickfont=dict(color=CHART_AXIS_COLOR, size=11))

    st.plotly_chart(rsi_fig, use_container_width=True)

    # Key values row
    if rsi_val > 70:
        rsi_zone = "Overbought"
        rsi_color = "#EF4444"
    elif rsi_val < 30:
        rsi_zone = "Oversold"
        rsi_color = "#22C55E"
    elif rsi_val >= 50:
        rsi_zone = "Bullish"
        rsi_color = "#10B981"
    else:
        rsi_zone = "Bearish"
        rsi_color = "#F59E0B"

    rsi_col1, rsi_col2 = st.columns(2)
    with rsi_col1:
        st.metric("RSI (14)", f"{rsi_val:.1f}")
    with rsi_col2:
        st.markdown("**Zone**")
        st.markdown(f"<span style='color:{rsi_color}; font-weight:600;'>{rsi_zone}</span>", unsafe_allow_html=True)

    with st.expander("Understanding RSI"):
        if rsi_val > 70:
            rsi_interpretation = f"RSI at {rsi_val:.1f} is above 70, indicating the stock may be overbought. Recent gains may be overextended and a pullback could occur."
        elif rsi_val < 30:
            rsi_interpretation = f"RSI at {rsi_val:.1f} is below 30, indicating the stock may be oversold. Selling pressure may be exhausted and a bounce could occur."
        elif rsi_val >= 50:
            rsi_interpretation = f"RSI at {rsi_val:.1f} shows bullish momentum. Buyers are in control."
        else:
            rsi_interpretation = f"RSI at {rsi_val:.1f} shows bearish momentum. Sellers are in control."

        st.markdown(f"""
{rsi_interpretation}

**RSI Zones:**
- **Above 70:** Overbought - potential pullback
- **50-70:** Bullish momentum
- **30-50:** Bearish momentum
- **Below 30:** Oversold - potential bounce
        """)

    st.markdown("---")

    # =========================================================================
    # 3. MACD CHART
    # =========================================================================
    st.markdown("### MACD")

    macd_val = price_data["MACD"].iloc[-1] if "MACD" in price_data.columns else 0
    macd_sig = price_data["MACD_SIGNAL"].iloc[-1] if "MACD_SIGNAL" in price_data.columns else 0
    macd_hist = price_data["MACD_HIST"].iloc[-1] if "MACD_HIST" in price_data.columns else 0

    # Create MACD chart
    macd_fig = go.Figure()

    macd_dates = chart_data["Date"].tolist()

    if "MACD_HIST" in chart_data.columns:
        hist_values = chart_data["MACD_HIST"].tolist()
        colors = ['#10B981' if (v is not None and v >= 0) else '#F43F5E' for v in hist_values]
        macd_fig.add_trace(go.Bar(
            x=macd_dates,
            y=hist_values,
            name="Histogram",
            marker_color=colors,
            opacity=0.6
        ))

    if "MACD" in chart_data.columns:
        macd_values = chart_data["MACD"].tolist()
        macd_fig.add_trace(go.Scatter(
            x=macd_dates,
            y=macd_values,
            name="MACD",
            line=dict(color="#0EA5E9", width=2)
        ))

    if "MACD_SIGNAL" in chart_data.columns:
        signal_values = chart_data["MACD_SIGNAL"].tolist()
        macd_fig.add_trace(go.Scatter(
            x=macd_dates,
            y=signal_values,
            name="Signal",
            line=dict(color="#F59E0B", width=2)
        ))

    macd_fig.add_hline(y=0, line=dict(color="#9CA3AF", dash="dot", width=1))

    macd_fig.update_layout(
        height=250,
        margin=dict(l=10, r=10, t=10, b=30),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(color=LEGEND_FONT_COLOR, size=12)
        ),
        font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif", size=12),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode="x unified"
    )
    macd_fig.update_xaxes(showgrid=False, showline=True, linecolor='#E5E7EB', tickfont=dict(color=CHART_AXIS_COLOR, size=11))
    macd_fig.update_yaxes(showgrid=True, gridcolor='#E5E7EB', tickfont=dict(color=CHART_AXIS_COLOR, size=11))

    st.plotly_chart(macd_fig, use_container_width=True)

    # Key values row
    if macd_val > macd_sig:
        macd_signal = "Bullish"
        macd_color = "#10B981"
    else:
        macd_signal = "Bearish"
        macd_color = "#EF4444"

    macd_col1, macd_col2, macd_col3, macd_col4 = st.columns(4)
    with macd_col1:
        st.metric("MACD", f"{macd_val:.3f}")
    with macd_col2:
        st.metric("Signal", f"{macd_sig:.3f}")
    with macd_col3:
        st.metric("Histogram", f"{macd_hist:+.3f}")
    with macd_col4:
        st.markdown("**Signal**")
        st.markdown(f"<span style='color:{macd_color}; font-weight:600;'>{macd_signal}</span>", unsafe_allow_html=True)

    with st.expander("Understanding MACD"):
        if macd_val > macd_sig and macd_hist > 0:
            macd_interpretation = "MACD is above Signal with positive histogram - strong bullish momentum."
        elif macd_val > macd_sig:
            macd_interpretation = "MACD is above Signal - bullish momentum present."
        elif macd_val < macd_sig and macd_hist < 0:
            macd_interpretation = "MACD is below Signal with negative histogram - strong bearish momentum."
        else:
            macd_interpretation = "MACD is below Signal - bearish pressure present."

        # Check for crossover
        crossover_text = ""
        if "MACD" in price_data.columns and len(price_data) > 2:
            prev_macd = price_data["MACD"].iloc[-2]
            prev_sig = price_data["MACD_SIGNAL"].iloc[-2]
            if prev_macd <= prev_sig and macd_val > macd_sig:
                crossover_text = "\n\n**Bullish Crossover just occurred!** MACD crossed above Signal - buy signal."
            elif prev_macd >= prev_sig and macd_val < macd_sig:
                crossover_text = "\n\n**Bearish Crossover just occurred!** MACD crossed below Signal - sell signal."

        st.markdown(f"""
{macd_interpretation}{crossover_text}

**MACD Components:**
- **MACD Line:** 12-day EMA minus 26-day EMA
- **Signal Line:** 9-day EMA of MACD
- **Histogram:** MACD minus Signal (momentum strength)

**Key Signals:**
- **Bullish Crossover:** MACD crosses above Signal
- **Bearish Crossover:** MACD crosses below Signal
        """)
