# =============================================================================
# TECHNICAL TAB - Simplified with 3 key charts and time period toggle
# =============================================================================

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from components import get_status_color

# Chart styling constants
CHART_FONT_COLOR = "#1A3C40"
CHART_AXIS_COLOR = "#37616A"
LEGEND_FONT_COLOR = "#1A3C40"


def find_crossovers(df):
    """Find golden cross and death cross points in the data (SMA50/200)."""
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


def find_ema_crossovers(df):
    """Find EMA20/50 golden and death cross points."""
    if "EMA20" not in df.columns or "EMA50" not in df.columns:
        return [], []

    golden = []
    death = []

    ema20 = df["EMA20"].values
    ema50 = df["EMA50"].values
    dates = df["Date"].values
    prices = df["Close"].values

    for i in range(1, len(df)):
        if pd.isna(ema20[i]) or pd.isna(ema50[i]) or pd.isna(ema20[i-1]) or pd.isna(ema50[i-1]):
            continue

        if ema20[i-1] <= ema50[i-1] and ema20[i] > ema50[i]:
            golden.append((dates[i], prices[i], ema20[i]))

        if ema20[i-1] >= ema50[i-1] and ema20[i] < ema50[i]:
            death.append((dates[i], prices[i], ema20[i]))

    return golden, death


def render(selected, price_data, info, tech_score, tech_details, last_row,
           selected_strategy="Volume+RSI", volume_score=0, volume_details=None):
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
        line=dict(color="#1A3C40", width=2.5),
        mode='lines'
    ))

    # Add SMA 50 if available
    if "SMA50" in chart_data.columns:
        sma50_data = chart_data["SMA50"].tolist()
        trend_fig.add_trace(go.Scatter(
            x=dates,
            y=sma50_data,
            name="SMA 50",
            line=dict(color="#0097A7", width=2, dash='solid'),
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
            line=dict(color="#FF6B6B", width=2, dash='solid'),
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
        linecolor='#D0E8EA',
        tickfont=dict(color=CHART_AXIS_COLOR, size=11)
    )
    trend_fig.update_yaxes(
        showgrid=True,
        gridcolor='#D0E8EA',
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
            line=dict(color="#0097A7", width=2),
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
    rsi_fig.update_xaxes(showgrid=False, showline=True, linecolor='#D0E8EA', tickfont=dict(color=CHART_AXIS_COLOR, size=11))
    rsi_fig.update_yaxes(showgrid=True, gridcolor='#D0E8EA', tickfont=dict(color=CHART_AXIS_COLOR, size=11))

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
            line=dict(color="#0097A7", width=2)
        ))

    if "MACD_SIGNAL" in chart_data.columns:
        signal_values = chart_data["MACD_SIGNAL"].tolist()
        macd_fig.add_trace(go.Scatter(
            x=macd_dates,
            y=signal_values,
            name="Signal",
            line=dict(color="#FF6B6B", width=2)
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
    macd_fig.update_xaxes(showgrid=False, showline=True, linecolor='#D0E8EA', tickfont=dict(color=CHART_AXIS_COLOR, size=11))
    macd_fig.update_yaxes(showgrid=True, gridcolor='#D0E8EA', tickfont=dict(color=CHART_AXIS_COLOR, size=11))

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

    # =========================================================================
    # 4. VOLUME CHART (shown when Volume+RSI or Combined strategy is active)
    # =========================================================================
    if selected_strategy == "Volume+RSI":
        st.markdown("---")
        st.markdown("### Volume Analysis")

        vol_fig = go.Figure()

        if "Volume" in chart_data.columns:
            vol_dates = chart_data["Date"].tolist()
            vol_values = chart_data["Volume"].tolist()

            # Color bars by price direction
            close_vals = chart_data["Close"].values
            prev_close = np.roll(close_vals, 1)
            prev_close[0] = close_vals[0]
            vol_colors = ['#10B981' if c >= p else '#F43F5E' for c, p in zip(close_vals, prev_close)]

            vol_fig.add_trace(go.Bar(
                x=vol_dates,
                y=vol_values,
                name="Volume",
                marker_color=vol_colors,
                opacity=0.6,
            ))

            # Volume SMA 20
            if "Volume_SMA20" in chart_data.columns:
                vol_fig.add_trace(go.Scatter(
                    x=vol_dates,
                    y=chart_data["Volume_SMA20"].tolist(),
                    name="Vol SMA 20",
                    line=dict(color="#0097A7", width=2),
                    mode='lines',
                ))

            # Volume SMA 50
            if "Volume_SMA50" in chart_data.columns:
                vol_fig.add_trace(go.Scatter(
                    x=vol_dates,
                    y=chart_data["Volume_SMA50"].tolist(),
                    name="Vol SMA 50",
                    line=dict(color="#FF6B6B", width=2),
                    mode='lines',
                ))

        vol_fig.update_layout(
            height=300,
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
            hovermode="x unified",
        )
        vol_fig.update_xaxes(showgrid=False, showline=True, linecolor='#D0E8EA', tickfont=dict(color=CHART_AXIS_COLOR, size=11))
        vol_fig.update_yaxes(showgrid=True, gridcolor='#D0E8EA', tickfont=dict(color=CHART_AXIS_COLOR, size=11))

        st.plotly_chart(vol_fig, use_container_width=True)

        # Volume metrics row
        vol_col1, vol_col2, vol_col3 = st.columns(3)
        with vol_col1:
            st.metric("Volume Score", f"{volume_score}/100")
        with vol_col2:
            rel_vol = price_data["Rel_Volume"].iloc[-1] if "Rel_Volume" in price_data.columns and pd.notna(price_data["Rel_Volume"].iloc[-1]) else 1.0
            st.metric("Relative Volume", f"{rel_vol:.2f}x")
        with vol_col3:
            confirms = volume_details.get("volume_confirms_trend", False) if volume_details else False
            st.markdown("**Trend Confirmation**")
            if confirms:
                st.markdown("<span style='color:#10B981; font-weight:600;'>Confirmed</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span style='color:#F59E0B; font-weight:600;'>Not Confirmed</span>", unsafe_allow_html=True)

        with st.expander("Understanding Volume Analysis"):
            st.markdown("""
Volume analysis confirms price movements by measuring participation:

**Key Concepts:**
- **Rising price + rising volume:** Strong bullish confirmation
- **Rising price + falling volume:** Weak rally, potential reversal
- **Falling price + rising volume:** Strong selling pressure
- **Falling price + falling volume:** Weak selloff, potential bottom

**Volume SMAs:**
- **SMA 20:** Short-term average volume (blue)
- **SMA 50:** Medium-term average volume (yellow)
- Volume above SMA 20 = above-average participation
            """)

    # =========================================================================
    # 5. EMA CROSSOVER CHART (shown when Paper 1 or Combined strategy active)
    # =========================================================================
    if selected_strategy == "Volume+RSI":
        st.markdown("---")
        st.markdown("### EMA Crossover (Paper 1)")

        ema_golden, ema_death = find_ema_crossovers(chart_data)

        ema_fig = go.Figure()

        # Price line
        ema_fig.add_trace(go.Scatter(
            x=dates,
            y=close_prices,
            name="Price",
            line=dict(color="#1A3C40", width=2.5),
            mode='lines'
        ))

        # EMA 20
        if "EMA20" in chart_data.columns:
            ema_fig.add_trace(go.Scatter(
                x=dates,
                y=chart_data["EMA20"].tolist(),
                name="EMA 20",
                line=dict(color="#0097A7", width=2),
                mode='lines',
                connectgaps=False
            ))

        # EMA 50
        if "EMA50" in chart_data.columns:
            ema_fig.add_trace(go.Scatter(
                x=dates,
                y=chart_data["EMA50"].tolist(),
                name="EMA 50",
                line=dict(color="#FF6B6B", width=2),
                mode='lines',
                connectgaps=False
            ))

        # Golden Cross markers
        for date_val, price_val, ema_val in ema_golden:
            ema_fig.add_annotation(
                x=date_val, y=ema_val,
                text="EMA Golden",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2,
                arrowcolor="#10B981",
                font=dict(size=10, color="#10B981"),
                bgcolor="white", bordercolor="#10B981", borderwidth=1,
                ax=0, ay=-40
            )

        # Death Cross markers
        for date_val, price_val, ema_val in ema_death:
            ema_fig.add_annotation(
                x=date_val, y=ema_val,
                text="EMA Death",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2,
                arrowcolor="#EF4444",
                font=dict(size=10, color="#EF4444"),
                bgcolor="white", bordercolor="#EF4444", borderwidth=1,
                ax=0, ay=40
            )

        ema_fig.update_layout(
            height=400,
            margin=dict(l=10, r=10, t=40, b=40),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
                font=dict(color=LEGEND_FONT_COLOR, size=12)
            ),
            font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif", size=12),
            plot_bgcolor='white', paper_bgcolor='white',
            hovermode="x unified"
        )
        ema_fig.update_xaxes(showgrid=False, showline=True, linecolor='#D0E8EA', tickfont=dict(color=CHART_AXIS_COLOR, size=11))
        ema_fig.update_yaxes(showgrid=True, gridcolor='#D0E8EA', tickfont=dict(color=CHART_AXIS_COLOR, size=11), tickprefix="$")

        st.plotly_chart(ema_fig, use_container_width=True)

        # EMA key values
        ema20_val = price_data["EMA20"].iloc[-1] if "EMA20" in price_data.columns else None
        ema50_val = price_data["EMA50"].iloc[-1] if "EMA50" in price_data.columns else None

        if ema20_val and ema50_val:
            is_ema_golden = ema20_val > ema50_val
            ema_status = "EMA Golden Cross" if is_ema_golden else "EMA Death Cross"
            ema_s_color = "#10B981" if is_ema_golden else "#EF4444"

            ec1, ec2, ec3, ec4 = st.columns(4)
            with ec1:
                st.metric("Price", f"${current_price:.2f}")
            with ec2:
                st.metric("EMA 20", f"${ema20_val:.2f}")
            with ec3:
                st.metric("EMA 50", f"${ema50_val:.2f}")
            with ec4:
                st.markdown("**EMA Status**")
                st.markdown(f"<span style='color:{ema_s_color}; font-weight:600;'>{ema_status}</span>", unsafe_allow_html=True)

        # =====================================================================
        # 6. ATV SLOPE SUBPLOT
        # =====================================================================
        st.markdown("---")
        st.markdown("### ATV Slope")

        if "ATV_Slope" in chart_data.columns:
            atv_fig = go.Figure()

            atv_dates = chart_data["Date"].tolist()
            atv_values = chart_data["ATV_Slope"].tolist()

            # Color by positive/negative
            atv_colors = ['#10B981' if (v is not None and not pd.isna(v) and v >= 0) else '#F43F5E' for v in atv_values]

            atv_fig.add_trace(go.Bar(
                x=atv_dates,
                y=atv_values,
                name="ATV Slope",
                marker_color=atv_colors,
                opacity=0.7,
            ))

            atv_fig.add_hline(y=0, line=dict(color="#9CA3AF", dash="dot", width=1))

            atv_fig.update_layout(
                height=250,
                margin=dict(l=10, r=10, t=10, b=30),
                font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif", size=12),
                plot_bgcolor='white', paper_bgcolor='white',
                showlegend=False,
                hovermode="x unified",
            )
            atv_fig.update_xaxes(showgrid=False, showline=True, linecolor='#D0E8EA', tickfont=dict(color=CHART_AXIS_COLOR, size=11))
            atv_fig.update_yaxes(showgrid=True, gridcolor='#D0E8EA', tickfont=dict(color=CHART_AXIS_COLOR, size=11))

            st.plotly_chart(atv_fig, use_container_width=True)

            atv_current = price_data["ATV_Slope"].iloc[-1] if pd.notna(price_data["ATV_Slope"].iloc[-1]) else 0
            atv_direction = "Rising" if atv_current > 0 else "Falling" if atv_current < 0 else "Flat"
            atv_d_color = "#10B981" if atv_current > 0 else "#EF4444" if atv_current < 0 else "#6B7280"

            ac1, ac2 = st.columns(2)
            with ac1:
                st.metric("ATV Slope", f"{atv_current:,.0f}")
            with ac2:
                st.markdown("**Volume Trend**")
                st.markdown(f"<span style='color:{atv_d_color}; font-weight:600;'>{atv_direction}</span>", unsafe_allow_html=True)

            with st.expander("Understanding ATV Slope"):
                st.markdown("""
ATV (Average Trading Volume) Slope measures the direction of volume momentum:

- **Positive slope:** Volume is increasing — confirms price moves
- **Negative slope:** Volume is decreasing — warns of weakening moves
- Used with EMA crossovers to confirm signal strength (Paper 1)
                """)
