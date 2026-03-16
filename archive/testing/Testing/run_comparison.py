#!/usr/bin/env python3
"""
Model Comparison Test Runner
=============================
Runs all 4 models × 5 tickers, collects metrics, generates CSVs and charts.

Usage:
    python Testing/run_comparison.py
"""

import sys
import os
import time
import warnings

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import yfinance as yf

from backtest import compute_indicators, simulate_strategy, calculate_backtest_metrics, load_market_data, load_peer_metrics
from models import detect_market_regime
from strategies import get_all_strategies
from visualizations import plot_equity_curves, plot_metrics_heatmap, plot_signal_distribution

try:
    import rl_agent
    RL_AVAILABLE = rl_agent.is_available()
except (ImportError, OSError):
    RL_AVAILABLE = False

warnings.filterwarnings("ignore", category=FutureWarning)

# =============================================================================
# CONFIGURATION
# =============================================================================

TICKERS = ["AAPL", "MSFT", "JPM", "JNJ", "TSLA"]
PERIOD = "3y"
INITIAL_CAPITAL = 10000
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print("=" * 70)
    print("MODEL COMPARISON TEST FRAMEWORK")
    print("=" * 70)
    print(f"Tickers: {', '.join(TICKERS)}")
    print(f"Period:  {PERIOD}")
    print(f"Capital: ${INITIAL_CAPITAL:,}")
    print()

    # ------------------------------------------------------------------
    # 1. Load market data for regime detection (once)
    # ------------------------------------------------------------------
    print("[1/5] Loading market data (S&P 500, VIX)...")
    try:
        sp500_df, vix_df = load_market_data()
        market_regime, _, regime_metrics = detect_market_regime(sp500_df, vix_df)
        print(f"  Market regime: {market_regime}")
    except Exception as e:
        print(f"  Warning: Could not load market data ({e}), defaulting to Sideways")
        market_regime = "Sideways"
    print()

    # ------------------------------------------------------------------
    # 2. Run comparison for each ticker
    # ------------------------------------------------------------------
    all_rows = []           # per-ticker × per-model results
    all_equity = {}         # {ticker: {model: equity_curve}}
    all_signals = {}        # {model: [(date, signal), ...]} aggregated

    for t_idx, ticker in enumerate(TICKERS):
        print(f"[2/5] Processing {ticker} ({t_idx + 1}/{len(TICKERS)})")
        print("-" * 50)

        # Fetch data
        print(f"  Fetching {PERIOD} data...")
        try:
            raw = yf.Ticker(ticker).history(period=PERIOD, interval="1d", auto_adjust=False)
        except Exception as e:
            print(f"  ERROR fetching {ticker}: {e}. Skipping.")
            continue

        if raw.empty or len(raw) < 250:
            print(f"  Not enough data for {ticker} ({len(raw)} rows). Skipping.")
            continue

        raw = raw.reset_index()
        if "Date" not in raw.columns and "index" in raw.columns:
            raw = raw.rename(columns={"index": "Date"})
        # Ensure Date column exists
        if "Date" not in raw.columns:
            raw["Date"] = raw.index

        # Compute indicators
        print("  Computing indicators...")
        df = compute_indicators(raw.copy())

        # Get ticker info for Paper 2
        print("  Loading ticker info...")
        try:
            info = yf.Ticker(ticker).get_info()
        except Exception:
            info = {"shortName": ticker, "sector": "Unknown"}

        # Load peer metrics for Paper 2
        print("  Loading peer metrics...")
        peer_metrics = load_peer_metrics(ticker)

        # Train / load RL agent
        ppo_model = None
        if RL_AVAILABLE and len(df) >= 100:
            print("  Training/loading RL agent...", end=" ", flush=True)
            t0 = time.time()
            ppo_model = rl_agent.get_ppo_agent(df, ticker=ticker)
            elapsed = time.time() - t0
            status = "done" if ppo_model is not None else "failed"
            print(f"{status} ({elapsed:.1f}s)")
        else:
            print("  RL agent: skipped (unavailable or not enough data)")

        # Build strategies
        strategies = get_all_strategies(ppo_model, market_regime, info, peer_metrics)
        print(f"  Running {len(strategies)} strategies...")

        ticker_equity = {}
        for model_name, strategy_fn in strategies.items():
            print(f"    {model_name}...", end=" ", flush=True)
            t0 = time.time()

            try:
                equity_curve, trades, signals = simulate_strategy(df, strategy_fn, INITIAL_CAPITAL)
                metrics = calculate_backtest_metrics(equity_curve, trades)
                elapsed = time.time() - t0

                # Store results
                row = {"model": model_name, "ticker": ticker}
                row.update(metrics)
                all_rows.append(row)

                ticker_equity[model_name] = equity_curve

                # Aggregate signals
                if model_name not in all_signals:
                    all_signals[model_name] = []
                all_signals[model_name].extend(signals)

                print(f"done ({elapsed:.1f}s) | "
                      f"Return: {metrics['total_return']:+.1f}% | "
                      f"Sharpe: {metrics['sharpe_ratio']:.2f} | "
                      f"Trades: {metrics['trade_count']}")

            except Exception as e:
                print(f"ERROR: {e}")
                continue

        all_equity[ticker] = ticker_equity
        print()

    # ------------------------------------------------------------------
    # 3. Build DataFrames and save CSVs
    # ------------------------------------------------------------------
    print("[3/5] Saving CSV results...")

    if not all_rows:
        print("  ERROR: No results collected. Exiting.")
        return

    per_ticker_df = pd.DataFrame(all_rows)
    per_ticker_path = os.path.join(RESULTS_DIR, "per_ticker_results.csv")
    per_ticker_df.to_csv(per_ticker_path, index=False)
    print(f"  Saved: {per_ticker_path}")

    # Summary: average metrics per model
    metrics_cols = [
        "sharpe_ratio", "sortino_ratio", "total_return",
        "annual_return", "max_drawdown", "trade_count", "accuracy",
    ]
    summary_df = per_ticker_df.groupby("model")[metrics_cols].mean().reset_index()

    # Reorder
    model_order = [
        "Paper 1 Rules Only", "Paper 1 + RL (Original)",
        "Novel Hybrid (Ours)", "Paper 2 (5-Factor)"
    ]
    summary_df["_sort"] = summary_df["model"].apply(
        lambda m: model_order.index(m) if m in model_order else 99
    )
    summary_df = summary_df.sort_values("_sort").drop(columns="_sort")

    summary_path = os.path.join(RESULTS_DIR, "comparison_summary.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"  Saved: {summary_path}")
    print()

    # ------------------------------------------------------------------
    # 4. Generate visualizations
    # ------------------------------------------------------------------
    print("[4/5] Generating charts...")

    for ticker, equity_dict in all_equity.items():
        if equity_dict:
            plot_equity_curves(equity_dict, ticker)

    plot_metrics_heatmap(per_ticker_df)

    if all_signals:
        plot_signal_distribution(all_signals)
    print()

    # ------------------------------------------------------------------
    # 5. Print summary table
    # ------------------------------------------------------------------
    print("[5/5] REPORT-READY SUMMARY (averaged across all tickers)")
    print("=" * 90)

    header = f"{'Model':<28} {'Sharpe':>8} {'Sortino':>8} {'TotRet%':>9} {'AnnRet%':>9} {'MaxDD%':>8} {'Trades':>7} {'WinR%':>7}"
    print(header)
    print("-" * 90)

    for _, row in summary_df.iterrows():
        line = (
            f"{row['model']:<28} "
            f"{row['sharpe_ratio']:>8.2f} "
            f"{row['sortino_ratio']:>8.2f} "
            f"{row['total_return']:>9.2f} "
            f"{row['annual_return']:>9.2f} "
            f"{row['max_drawdown']:>8.2f} "
            f"{row['trade_count']:>7.0f} "
            f"{row['accuracy']:>7.1f}"
        )
        print(line)

    print("=" * 90)
    print()
    print(f"Full results: {RESULTS_DIR}/")
    print("  - per_ticker_results.csv (all {0} rows)".format(len(per_ticker_df)))
    print("  - comparison_summary.csv (averaged)")
    print("  - equity_curves_*.png (one per ticker)")
    print("  - metrics_heatmap.png")
    print("  - signal_distribution.png")
    print()
    print("Done.")


if __name__ == "__main__":
    main()
