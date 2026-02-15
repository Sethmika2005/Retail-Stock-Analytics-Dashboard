# =============================================================================
# BACKTEST TAB - Strategy comparison with Sharpe, Sortino, accuracy
# =============================================================================

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Chart styling constants
CHART_FONT_COLOR = "#1F2937"
CHART_AXIS_COLOR = "#374151"
LEGEND_FONT_COLOR = "#1F2937"

STRATEGY_COLORS = {
    "Baseline": "#6B7280",
    "Paper 1: EMA+ATV+RSI": "#3B82F6",
    "Paper 2: Factor Weights": "#F59E0B",
    "Combined": "#10B981",
    "Paper 1 + RL Agent": "#8B5CF6",
}


def render(selected, price_data, info, market_regime, peer_metrics=None):
    """Render the Backtest comparison tab."""
    st.subheader("Strategy Backtest")
    st.caption("Compare all strategies (including RL agent) on historical data with risk-adjusted metrics.")

    # Import backtest engine
    from backtest import (
        simulate_strategy,
        calculate_backtest_metrics,
        get_strategy_functions,
        compute_indicators as bt_compute_indicators,
    )

    # Period selector
    period_col1, period_col2 = st.columns([3, 1])
    with period_col2:
        bt_period = st.radio(
            "Backtest Period",
            options=["1Y", "2Y", "3Y", "5Y"],
            index=1,
            horizontal=True,
            label_visibility="collapsed",
        )

    period_map = {"1Y": 252, "2Y": 504, "3Y": 756, "5Y": 1260}
    bt_days = period_map.get(bt_period, 504)

    # Run backtest button
    if st.button("Run Backtest", type="primary"):
        with st.spinner(f"Running {bt_period} backtest for {selected}..."):
            _run_and_display_backtest(
                selected, price_data, info, market_regime, peer_metrics,
                bt_days, bt_period, simulate_strategy, calculate_backtest_metrics,
                get_strategy_functions, bt_compute_indicators,
            )
    else:
        st.info(f"Click 'Run Backtest' to compare all strategies (including RL agent) over {bt_period}.")


def _run_and_display_backtest(
    selected, price_data, info, market_regime, peer_metrics,
    bt_days, bt_period, simulate_strategy, calculate_backtest_metrics,
    get_strategy_functions, bt_compute_indicators,
):
    """Execute backtest and display results."""

    # Prepare data: ensure indicators are computed
    if "EMA_Cross_Signal" not in price_data.columns:
        bt_df = bt_compute_indicators(price_data)
    else:
        bt_df = price_data.copy()

    # Slice to backtest period (need extra 200 days for warmup)
    total_needed = bt_days + 200
    if len(bt_df) < total_needed:
        bt_df_slice = bt_df.copy()
    else:
        bt_df_slice = bt_df.tail(total_needed).copy()
    bt_df_slice = bt_df_slice.reset_index(drop=True)

    # Get strategy functions (includes RL agent if available)
    strategies = get_strategy_functions(
        info, market_regime, peer_metrics,
        backtest_df=bt_df_slice, ticker=selected,
    )

    # Run each strategy
    all_results = {}
    progress = st.progress(0)
    strategy_names = list(strategies.keys())

    for i, (name, fn) in enumerate(strategies.items()):
        equity_curve, trades, signals = simulate_strategy(bt_df_slice, fn)
        metrics = calculate_backtest_metrics(equity_curve, trades)
        all_results[name] = {
            "equity_curve": equity_curve,
            "trades": trades,
            "signals": signals,
            "metrics": metrics,
        }
        progress.progress((i + 1) / len(strategies))

    progress.empty()

    # =========================================================================
    # 1. COMPARISON TABLE
    # =========================================================================
    st.markdown("### Performance Comparison")

    table_rows = []
    for name in strategy_names:
        m = all_results[name]["metrics"]
        table_rows.append({
            "Strategy": name,
            "Total Return %": m["total_return"],
            "Annual Return %": m["annual_return"],
            "Sharpe Ratio": m["sharpe_ratio"],
            "Sortino Ratio": m["sortino_ratio"],
            "Max Drawdown %": m["max_drawdown"],
            "Trades": m["trade_count"],
            "Accuracy %": m["accuracy"],
            "Wins": m["win_count"],
            "Losses": m["loss_count"],
        })

    table_df = pd.DataFrame(table_rows)

    # Highlight best values
    def highlight_best(s):
        styles = [""] * len(s)
        if s.name in ["Total Return %", "Annual Return %", "Sharpe Ratio", "Sortino Ratio", "Accuracy %"]:
            best_idx = s.idxmax()
            styles[best_idx] = "background-color: rgba(16, 185, 129, 0.2); font-weight: bold;"
        elif s.name == "Max Drawdown %":
            best_idx = s.idxmax()  # Least negative = best
            styles[best_idx] = "background-color: rgba(16, 185, 129, 0.2); font-weight: bold;"
        return styles

    numeric_cols = ["Total Return %", "Annual Return %", "Sharpe Ratio", "Sortino Ratio",
                    "Max Drawdown %", "Accuracy %"]
    styled_table = table_df.style.apply(highlight_best, subset=numeric_cols)
    st.dataframe(styled_table, use_container_width=True, hide_index=True)

    st.markdown("---")

    # =========================================================================
    # 2. EQUITY CURVES
    # =========================================================================
    st.markdown("### Equity Curves")

    eq_fig = go.Figure()

    for name in strategy_names:
        curve = all_results[name]["equity_curve"]
        if not curve:
            continue
        dates = [d for d, _ in curve]
        values = [v for _, v in curve]

        eq_fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            name=name,
            line=dict(
                color=STRATEGY_COLORS.get(name, "#6B7280"),
                width=2,
            ),
            mode="lines",
        ))

    eq_fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=40, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(color=LEGEND_FONT_COLOR, size=12),
        ),
        font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif", size=12),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
    )
    eq_fig.update_xaxes(
        showgrid=False, showline=True, linecolor="#E5E7EB",
        tickfont=dict(color=CHART_AXIS_COLOR, size=11),
    )
    eq_fig.update_yaxes(
        showgrid=True, gridcolor="#E5E7EB",
        tickfont=dict(color=CHART_AXIS_COLOR, size=11),
        tickprefix="$",
    )

    st.plotly_chart(eq_fig, use_container_width=True)

    st.markdown("---")

    # =========================================================================
    # 3. SIGNAL TIMELINE (for selected strategy)
    # =========================================================================
    st.markdown("### Signal Timeline")

    selected_strat = st.selectbox(
        "Strategy to inspect",
        options=strategy_names,
        index=0,
        key="bt_signal_strat",
    )

    signals = all_results[selected_strat]["signals"]
    trades = all_results[selected_strat]["trades"]

    if signals:
        sig_fig = go.Figure()

        # Price line
        sig_dates = [d for d, _ in signals]
        # Get prices for those dates
        sig_prices = []
        for d, _ in signals:
            mask = bt_df_slice["Date"] == d if "Date" in bt_df_slice.columns else None
            if mask is not None and mask.any():
                sig_prices.append(bt_df_slice.loc[mask, "Close"].iloc[0])
            else:
                sig_prices.append(None)

        # If Date matching didn't work, use position-based pricing
        if all(p is None for p in sig_prices):
            start_offset = len(bt_df_slice) - len(signals)
            sig_prices = bt_df_slice["Close"].iloc[start_offset:].tolist()

        sig_fig.add_trace(go.Scatter(
            x=sig_dates,
            y=sig_prices,
            name="Price",
            line=dict(color="#000000", width=1.5),
            mode="lines",
        ))

        # Buy markers
        buy_trades = [t for t in trades if t["action"] == "BUY"]
        if buy_trades:
            sig_fig.add_trace(go.Scatter(
                x=[t["date"] for t in buy_trades],
                y=[t["price"] for t in buy_trades],
                name="BUY",
                mode="markers",
                marker=dict(symbol="triangle-up", size=12, color="#10B981", line=dict(width=1, color="white")),
            ))

        # Sell markers
        sell_trades = [t for t in trades if t["action"] == "SELL"]
        if sell_trades:
            sig_fig.add_trace(go.Scatter(
                x=[t["date"] for t in sell_trades],
                y=[t["price"] for t in sell_trades],
                name="SELL",
                mode="markers",
                marker=dict(symbol="triangle-down", size=12, color="#EF4444", line=dict(width=1, color="white")),
            ))

        sig_fig.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=10, b=30),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(color=LEGEND_FONT_COLOR, size=12),
            ),
            font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif", size=12),
            plot_bgcolor="white",
            paper_bgcolor="white",
            hovermode="x unified",
        )
        sig_fig.update_xaxes(
            showgrid=False, showline=True, linecolor="#E5E7EB",
            tickfont=dict(color=CHART_AXIS_COLOR, size=11),
        )
        sig_fig.update_yaxes(
            showgrid=True, gridcolor="#E5E7EB",
            tickfont=dict(color=CHART_AXIS_COLOR, size=11),
            tickprefix="$",
        )

        st.plotly_chart(sig_fig, use_container_width=True)

        # Trade summary
        m = all_results[selected_strat]["metrics"]
        t_col1, t_col2, t_col3, t_col4 = st.columns(4)
        with t_col1:
            st.metric("Total Trades", m["trade_count"])
        with t_col2:
            st.metric("Win / Loss", f"{m['win_count']} / {m['loss_count']}")
        with t_col3:
            st.metric("Accuracy", f"{m['accuracy']:.1f}%")
        with t_col4:
            st.metric("Sharpe", f"{m['sharpe_ratio']:.2f}")
