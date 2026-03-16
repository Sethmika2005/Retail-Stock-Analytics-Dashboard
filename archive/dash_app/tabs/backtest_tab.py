# =============================================================================
# BACKTEST TAB - Strategy backtest (Dash version)
# =============================================================================

import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc

from components import COLORS, FONTS, section_divider, snappy

CHART_LAYOUT = dict(
    font=dict(color=COLORS["text_primary"], family=FONTS["primary"], size=12),
    plot_bgcolor="white", paper_bgcolor="white", hovermode="x unified",
)
LEGEND = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
              font=dict(color=COLORS["text_primary"], size=12))

STRATEGY_COLORS = {"Novel Hybrid (EMA+ATV+RSI+RL)": "#4CAF50"}


def render_placeholder():
    """Return a lightweight placeholder — actual backtest runs on button click."""
    return html.Div([
        html.H3("Strategy Backtest", style={
            "fontFamily": FONTS["primary"], "fontWeight": 600,
            "color": COLORS["teal_dark"], "marginBottom": "4px",
        }),
        html.P("Backtesting the Novel Hybrid strategy (EMA+ATV+RSI+RL) over 2 years.",
               style={"fontSize": "12px", "color": COLORS["text_secondary"], "marginBottom": "12px"}),
        section_divider(),
        html.Div([
            html.P("Backtesting involves running strategy simulations and RL model inference.",
                   style={"color": COLORS["text_secondary"], "marginBottom": "12px"}),
            html.Button("Run Backtest", id="run-backtest-btn", n_clicks=0,
                        style={
                            "fontFamily": FONTS["primary"], "fontSize": "14px", "fontWeight": 600,
                            "padding": "10px 24px", "border": "none", "borderRadius": "6px",
                            "cursor": "pointer", "color": "white",
                            "background": COLORS["teal"],
                        }),
        ], style={"textAlign": "center", "padding": "40px 0"}),
        dcc.Loading(
            id="backtest-loading",
            type="circle",
            children=[html.Div(id="backtest-results")],
        ),
    ])


def render(stock_data, price_data):
    """Render backtest results (called when Run Backtest is clicked)."""
    ticker = stock_data["ticker"]
    info = stock_data["info"]
    market_regime = stock_data["market_regime"]

    children = []

    # Run backtest
    try:
        from backtest_engine import (
            simulate_strategy,
            calculate_backtest_metrics,
            get_strategy_functions,
            compute_indicators as bt_compute_indicators,
        )
    except ImportError:
        children.append(html.P("Backtest engine not available.",
                                style={"color": COLORS["danger"]}))
        return html.Div(children)

    bt_days = 504  # 2Y
    if "EMA_Cross_Signal" not in price_data.columns:
        bt_df = bt_compute_indicators(price_data)
    else:
        bt_df = price_data.copy()

    total_needed = bt_days + 200
    if len(bt_df) < total_needed:
        bt_df_slice = bt_df.copy()
    else:
        bt_df_slice = bt_df.tail(total_needed).copy()
    bt_df_slice = bt_df_slice.reset_index(drop=True)

    strategies = get_strategy_functions(info, market_regime, backtest_df=bt_df_slice, ticker=ticker)

    all_results = {}
    for name, fn in strategies.items():
        equity_curve, trades, signals = simulate_strategy(bt_df_slice, fn)
        metrics = calculate_backtest_metrics(equity_curve, trades)
        all_results[name] = {"equity_curve": equity_curve, "trades": trades,
                              "signals": signals, "metrics": metrics}

    strategy_names = list(strategies.keys())

    # 1. METRICS TABLE
    children.append(html.H4("Performance", style={"fontFamily": FONTS["primary"], "color": COLORS["teal_dark"]}))

    for name in strategy_names:
        m = all_results[name]["metrics"]
        children.append(html.Div([
            html.Strong(name, style={"display": "block", "marginBottom": "8px"}),
            html.Div([
                _metric_box("Total Return", f"{m['total_return']:.2f}%"),
                _metric_box("Annual Return", f"{m['annual_return']:.2f}%"),
                _metric_box("Risk-Adj Return", f"{m['sharpe_ratio']:.2f}"),
                _metric_box("Downside Risk", f"{m['sortino_ratio']:.2f}"),
                _metric_box("Max Drawdown", f"{m['max_drawdown']:.2f}%"),
                _metric_box("Trades", str(m["trade_count"])),
                _metric_box("Accuracy", f"{m['accuracy']:.1f}%"),
                _metric_box("Win/Loss", f"{m['win_count']}/{m['loss_count']}"),
            ], style={"display": "flex", "gap": "8px", "flexWrap": "wrap"}),
        ], style={"marginBottom": "16px"}))

    children.append(section_divider())

    # 2. EQUITY CURVE
    children.append(html.H4("Equity Curve", style={"fontFamily": FONTS["primary"], "color": COLORS["teal_dark"]}))

    eq_fig = go.Figure()
    for name in strategy_names:
        curve = all_results[name]["equity_curve"]
        if not curve:
            continue
        eq_fig.add_trace(go.Scatter(
            x=[d for d, _ in curve], y=[v for _, v in curve], name=name, mode="lines",
            line=dict(color=STRATEGY_COLORS.get(name, COLORS["text_secondary"]), width=2),
        ))
    eq_fig.update_layout(height=400, margin=dict(l=10, r=10, t=40, b=40), legend=LEGEND, **CHART_LAYOUT)
    eq_fig.update_xaxes(showgrid=False, showline=True, linecolor=COLORS["border"])
    eq_fig.update_yaxes(showgrid=True, gridcolor=COLORS["border"], tickprefix="$")
    children.append(dcc.Graph(figure=eq_fig, config={"displayModeBar": False}))

    for name in strategy_names:
        curve = all_results[name]["equity_curve"]
        if curve and len(curve) >= 2 and curve[0][1] > 0:
            hypothetical = 10000 * (curve[-1][1] / curve[0][1])
            children.append(snappy(
                f"$10,000 invested using {name} would now be worth ${hypothetical:,.0f}."
            ))

    children.append(section_divider())

    # 3. SIGNAL TIMELINE
    children.append(html.H4("Signal Timeline", style={"fontFamily": FONTS["primary"], "color": COLORS["teal_dark"]}))

    for name in strategy_names:
        signals = all_results[name]["signals"]
        trades = all_results[name]["trades"]
        if not signals:
            continue

        sig_fig = go.Figure()
        sig_dates = [d for d, _ in signals]
        sig_prices = []
        for d, _ in signals:
            mask = bt_df_slice["Date"] == d if "Date" in bt_df_slice.columns else None
            if mask is not None and mask.any():
                sig_prices.append(float(bt_df_slice.loc[mask, "Close"].iloc[0]))
            else:
                sig_prices.append(None)
        if all(p is None for p in sig_prices):
            start_offset = len(bt_df_slice) - len(signals)
            sig_prices = bt_df_slice["Close"].iloc[start_offset:].tolist()

        sig_fig.add_trace(go.Scatter(x=sig_dates, y=sig_prices, name="Price",
                                      line=dict(color=COLORS["text_primary"], width=1.5), mode="lines"))
        buy_trades = [t for t in trades if t["action"] == "BUY"]
        if buy_trades:
            sig_fig.add_trace(go.Scatter(
                x=[t["date"] for t in buy_trades], y=[t["price"] for t in buy_trades],
                name="BUY", mode="markers",
                marker=dict(symbol="triangle-up", size=12, color=COLORS["success"],
                            line=dict(width=1, color="white")),
            ))
        sell_trades = [t for t in trades if t["action"] == "SELL"]
        if sell_trades:
            sig_fig.add_trace(go.Scatter(
                x=[t["date"] for t in sell_trades], y=[t["price"] for t in sell_trades],
                name="SELL", mode="markers",
                marker=dict(symbol="triangle-down", size=12, color=COLORS["danger_red"],
                            line=dict(width=1, color="white")),
            ))

        sig_fig.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=30), legend=LEGEND, **CHART_LAYOUT)
        sig_fig.update_xaxes(showgrid=False, showline=True, linecolor=COLORS["border"])
        sig_fig.update_yaxes(showgrid=True, gridcolor=COLORS["border"], tickprefix="$")
        children.append(dcc.Graph(figure=sig_fig, config={"displayModeBar": False}))

    return html.Div(children)


def _metric_box(label_text, value):
    return html.Div([
        html.Div(label_text, style={
            "fontFamily": FONTS["primary"], "fontSize": "11px", "fontWeight": 500,
            "color": COLORS["text_secondary"], "textTransform": "uppercase",
            "letterSpacing": "0.04em", "marginBottom": "2px",
        }),
        html.Div(value, style={
            "fontFamily": FONTS["primary"], "fontSize": "16px", "fontWeight": 600,
            "color": COLORS["text_primary"],
        }),
    ], style={
        "background": COLORS["card"], "border": f"1px solid {COLORS['border']}",
        "borderRadius": "6px", "padding": "8px 12px", "textAlign": "center",
        "minWidth": "100px",
    })
