"""
Publication-Quality Visualizations
===================================
Matplotlib charts for model comparison report.
All outputs saved as high-DPI PNGs to Testing/results/.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

# Consistent styling
COLORS = {
    "Paper 1 Rules Only": "#2196F3",       # blue
    "Paper 1 + RL (Original)": "#FF9800",  # orange
    "Novel Hybrid (Ours)": "#4CAF50",      # green
    "Paper 2 (5-Factor)": "#9C27B0",       # purple
}
DEFAULT_COLOR_LIST = ["#2196F3", "#FF9800", "#4CAF50", "#9C27B0"]

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "legend.fontsize": 9,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.grid": True,
    "grid.alpha": 0.3,
})


def plot_equity_curves(results, ticker):
    """
    Plot equity curves for all models on a single chart.

    Args:
        results: dict of {model_name: equity_curve} where equity_curve is list of (date, value)
        ticker: str, used in title and filename
    """
    fig, ax = plt.subplots(figsize=(10, 5.5))

    for i, (model_name, equity_curve) in enumerate(results.items()):
        if not equity_curve:
            continue
        dates = [e[0] for e in equity_curve]
        values = [e[1] for e in equity_curve]
        color = COLORS.get(model_name, DEFAULT_COLOR_LIST[i % len(DEFAULT_COLOR_LIST)])
        ax.plot(dates, values, label=model_name, color=color, linewidth=1.5)

    ax.set_title(f"Equity Curves — {ticker}", fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value ($)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.legend(loc="upper left", framealpha=0.9)

    # Rotate date labels
    fig.autofmt_xdate(rotation=30)

    path = os.path.join(RESULTS_DIR, f"equity_curves_{ticker}.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


def plot_metrics_heatmap(summary_df):
    """
    Heatmap: models (rows) × metrics (columns), averaged across tickers.

    Args:
        summary_df: DataFrame with columns [model, ticker, sharpe_ratio, sortino_ratio,
                     total_return, annual_return, max_drawdown, trade_count, accuracy]
    """
    metrics_cols = [
        "sharpe_ratio", "sortino_ratio", "total_return",
        "annual_return", "max_drawdown", "trade_count", "accuracy",
    ]
    display_labels = [
        "Sharpe", "Sortino", "Total Ret %",
        "Annual Ret %", "Max DD %", "Trades", "Win Rate %",
    ]

    # Average across tickers per model
    avg = summary_df.groupby("model")[metrics_cols].mean()

    # Reorder to match our model order
    model_order = [m for m in [
        "Paper 1 Rules Only", "Paper 1 + RL (Original)",
        "Novel Hybrid (Ours)", "Paper 2 (5-Factor)"
    ] if m in avg.index]
    avg = avg.loc[model_order]

    fig, ax = plt.subplots(figsize=(10, 3.5))

    data = avg.values
    im = ax.imshow(data, aspect="auto", cmap="RdYlGn")

    ax.set_xticks(range(len(display_labels)))
    ax.set_xticklabels(display_labels, rotation=35, ha="right")
    ax.set_yticks(range(len(model_order)))
    ax.set_yticklabels(model_order)

    # Annotate cells
    for i in range(len(model_order)):
        for j in range(len(metrics_cols)):
            val = data[i, j]
            fmt = f"{val:.1f}" if abs(val) < 1000 else f"{val:.0f}"
            text_color = "white" if abs(val - np.nanmean(data[:, j])) > np.nanstd(data[:, j]) else "black"
            ax.text(j, i, fmt, ha="center", va="center", fontsize=9, color=text_color)

    ax.set_title("Average Performance Metrics Across All Tickers", fontweight="bold", pad=12)
    fig.colorbar(im, ax=ax, shrink=0.8)

    path = os.path.join(RESULTS_DIR, "metrics_heatmap.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


def plot_signal_distribution(all_signals):
    """
    Grouped bar chart: BUY/SELL/HOLD counts per model.

    Args:
        all_signals: dict of {model_name: list of (date, signal)} across all tickers
    """
    signal_types = ["BUY", "SELL", "HOLD"]
    model_names = list(all_signals.keys())

    counts = {}
    for model, signals in all_signals.items():
        c = {"BUY": 0, "SELL": 0, "HOLD": 0}
        for _, sig in signals:
            if sig in c:
                c[sig] += 1
        counts[model] = c

    x = np.arange(len(model_names))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 5))
    signal_colors = {"BUY": "#4CAF50", "SELL": "#F44336", "HOLD": "#FF9800"}

    for i, sig in enumerate(signal_types):
        vals = [counts[m][sig] for m in model_names]
        bars = ax.bar(x + i * width, vals, width, label=sig, color=signal_colors[sig])
        # Add value labels on bars
        for bar, val in zip(bars, vals):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                        str(val), ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x + width)
    ax.set_xticklabels(model_names, rotation=15, ha="right")
    ax.set_ylabel("Signal Count")
    ax.set_title("Signal Distribution Across All Tickers", fontweight="bold")
    ax.legend()

    path = os.path.join(RESULTS_DIR, "signal_distribution.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")
