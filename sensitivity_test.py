"""
Sensitivity Analysis: Technical Score Weight Allocations
=========================================================
Tests different (trend, RSI, MACD) weight splits across multiple tickers
using the backtest engine. Monkey-patches calculate_technical_score at
runtime -- no production code is modified.

NOTE: RL agent is DISABLED to isolate the effect of tech score weights.
When RL is enabled it can override the composite-based recommendation,
masking any weight differences. This test measures pure rule-based
sensitivity.
"""

import sys
import os
import time
import warnings
import numpy as np
import pandas as pd
import yfinance as yf

sys.path.insert(0, os.path.dirname(__file__))
warnings.filterwarnings("ignore")

import models
from models import (
    calculate_volume_score,
    detect_market_regime,
    generate_recommendation_paper1,
)
from backtest import compute_indicators, simulate_strategy, calculate_backtest_metrics

# ---- Configuration ----
TICKERS = ["AAPL", "MSFT", "NVDA", "JPM", "JNJ"]
LOOKBACK_MONTHS = 24

WEIGHT_CONFIGS = [
    (40, 30, 30),  # Current default
    (33, 33, 34),  # Equal split
    (50, 25, 25),  # Trend-heavy
    (25, 25, 50),  # MACD-heavy
    (25, 50, 25),  # RSI-heavy
    (45, 25, 30),  # Trend+MACD bias
    (35, 35, 30),  # Trend+RSI bias
]

# Max possible raw scores for each sub-component (used for normalization)
TREND_MAX = 40
RSI_MAX = 30
MACD_MAX = 30


def make_weighted_tech_score_fn(w_trend, w_rsi, w_macd):
    """Return a patched calculate_technical_score that uses custom weights."""

    def calculate_technical_score_weighted(df):
        if df.empty or len(df) < 200:
            return 50, {}

        scores = {}
        current_price = df["Close"].iloc[-1]
        sma50 = df["SMA50"].iloc[-1] if "SMA50" in df.columns else df["Close"].rolling(50).mean().iloc[-1]
        sma200 = df["SMA200"].iloc[-1] if "SMA200" in df.columns else df["Close"].rolling(200).mean().iloc[-1]

        # Raw trend score (0-40 range)
        trend_raw = 0
        if pd.notna(sma50) and pd.notna(sma200):
            if current_price > sma50 > sma200:
                trend_raw = 40
            elif current_price > sma50 and current_price > sma200:
                trend_raw = 30
            elif current_price > sma200:
                trend_raw = 20
            elif current_price < sma50 < sma200:
                trend_raw = 0
            elif current_price < sma50 and current_price < sma200:
                trend_raw = 10
            else:
                trend_raw = 15

        # Raw RSI score (0-30 range)
        rsi = df["RSI"].iloc[-1] if "RSI" in df.columns else 50
        if pd.notna(rsi):
            if 40 <= rsi <= 60:
                rsi_raw = 25
            elif 30 <= rsi < 40:
                rsi_raw = 30
            elif 60 < rsi <= 70:
                rsi_raw = 20
            elif rsi < 30:
                rsi_raw = 25
            elif rsi > 70:
                rsi_raw = 10
            else:
                rsi_raw = 15
        else:
            rsi_raw = 15

        # Raw MACD score (0-30 range)
        macd = df["MACD"].iloc[-1] if "MACD" in df.columns else 0
        macd_signal = df["MACD_SIGNAL"].iloc[-1] if "MACD_SIGNAL" in df.columns else 0
        macd_hist = df["MACD_HIST"].iloc[-1] if "MACD_HIST" in df.columns else 0
        macd_raw = 15
        if pd.notna(macd) and pd.notna(macd_signal):
            if macd > macd_signal and macd_hist > 0:
                macd_raw = 30 if macd > 0 else 25
            elif macd < macd_signal and macd_hist < 0:
                macd_raw = 5 if macd < 0 else 10
            else:
                macd_raw = 15

        # Normalize to [0, 1] then apply weights
        trend_norm = trend_raw / TREND_MAX if TREND_MAX > 0 else 0
        rsi_norm = rsi_raw / RSI_MAX if RSI_MAX > 0 else 0
        macd_norm = macd_raw / MACD_MAX if MACD_MAX > 0 else 0

        total = trend_norm * w_trend + rsi_norm * w_rsi + macd_norm * w_macd
        total = min(100, max(0, total))

        scores["trend"] = round(trend_norm * w_trend, 1)
        scores["rsi"] = round(rsi_norm * w_rsi, 1)
        scores["macd"] = round(macd_norm * w_macd, 1)
        scores["total"] = round(total, 1)

        return round(total, 1), scores

    return calculate_technical_score_weighted


def make_strategy(info, market_regime):
    """Build strategy function WITHOUT RL to isolate tech score weight impact."""
    def strategy_fn(df, idx):
        historical = df.iloc[:idx + 1]
        if len(historical) < 50:
            return "HOLD"

        tech_score, _ = models.calculate_technical_score(historical)
        volume_score, _ = calculate_volume_score(historical)
        rsi_value = historical["RSI"].iloc[-1] if "RSI" in historical.columns else 50

        rec = generate_recommendation_paper1(
            tech_score=tech_score,
            volume_score=volume_score,
            rsi_value=rsi_value,
            market_regime=market_regime,
            ticker="BACKTEST",
            info=info,
            time_horizon="long",
            price_data=historical,
            rl_prediction=None,  # NO RL -- isolate tech weight effect
        )
        return rec["recommendation"]
    return strategy_fn


def main():
    print("=" * 80)
    print("  SENSITIVITY ANALYSIS: Technical Score Weight Allocations")
    print("=" * 80)
    print(f"  Tickers:  {', '.join(TICKERS)}")
    print(f"  Lookback: {LOOKBACK_MONTHS} months")
    print(f"  Configs:  {len(WEIGHT_CONFIGS)} weight splits")
    print(f"  RL Agent: DISABLED (isolating tech score weights)")
    print("=" * 80)

    # Load market data once
    print("\nLoading market data...", flush=True)
    sp500 = yf.Ticker("^GSPC").history(period="2y", interval="1d", auto_adjust=False)
    time.sleep(2)
    vix = yf.Ticker("^VIX").history(period="2y", interval="1d", auto_adjust=False)
    market_regime, _, _ = detect_market_regime(sp500, vix)
    print(f"  Market regime: {market_regime}")

    # Pre-load all ticker data with delays to avoid rate limiting
    print("\nLoading ticker data...", flush=True)
    ticker_data = {}
    for ticker in TICKERS:
        time.sleep(3)  # Avoid yfinance rate limiting
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="max", interval="1d", auto_adjust=False)
            if df.empty or len(df) < 500:
                print(f"  {ticker}: SKIPPED (insufficient data: {len(df)} days)")
                continue
            df = df.rename_axis("Date").reset_index()
            time.sleep(2)
            info = stock.get_info() or {}
            df = compute_indicators(df)

            # Slice to lookback period
            total_days = len(df)
            start_idx = max(200, total_days - LOOKBACK_MONTHS * 22)
            backtest_df = df.iloc[start_idx:].copy().reset_index(drop=True)
            if "Date" not in backtest_df.columns and "Date" in df.columns:
                backtest_df["Date"] = df["Date"].iloc[start_idx:].values

            ticker_data[ticker] = {
                "df": backtest_df,
                "info": info,
            }
            print(f"  {ticker}: {len(backtest_df)} days loaded", flush=True)
        except Exception as e:
            print(f"  {ticker}: FAILED ({e})")
            continue

    if len(ticker_data) < 2:
        print("\nERROR: Need at least 2 tickers for meaningful analysis. Exiting.")
        return

    # Store the original function
    original_calc_tech = models.calculate_technical_score

    # Run sensitivity analysis
    all_results = []
    total_runs = len(WEIGHT_CONFIGS) * len(ticker_data)

    print(f"\nRunning {total_runs} backtests (no RL, pure rule-based)...\n", flush=True)

    for w_trend, w_rsi, w_macd in WEIGHT_CONFIGS:
        config_label = f"({w_trend},{w_rsi},{w_macd})"
        print(f"  Config {config_label}:", end=" ", flush=True)

        # Monkey-patch the scoring function
        models.calculate_technical_score = make_weighted_tech_score_fn(w_trend, w_rsi, w_macd)

        for ticker, data in ticker_data.items():
            strategy = make_strategy(data["info"], market_regime)
            equity_curve, trades, signals = simulate_strategy(data["df"], strategy)
            metrics = calculate_backtest_metrics(equity_curve, trades)

            all_results.append({
                "config": config_label,
                "w_trend": w_trend,
                "w_rsi": w_rsi,
                "w_macd": w_macd,
                "ticker": ticker,
                **metrics,
            })
            print(f"{ticker}[OK]", end=" ", flush=True)

        print(flush=True)

    # Restore original function
    models.calculate_technical_score = original_calc_tech

    # Build results DataFrame
    df_results = pd.DataFrame(all_results)

    # ---- Per-Ticker Detail Table ----
    print("\n" + "=" * 100)
    print("  DETAILED RESULTS BY TICKER")
    print("=" * 100)

    for config in df_results["config"].unique():
        subset = df_results[df_results["config"] == config]
        print(f"\n  Config: {config}")
        print(f"  {'Ticker':<8} {'Sharpe':>8} {'Sortino':>8} {'Return%':>9} {'MaxDD%':>9} {'WinRate%':>9} {'Trades':>7}")
        print(f"  {'-'*8} {'-'*8} {'-'*8} {'-'*9} {'-'*9} {'-'*9} {'-'*7}")
        for _, row in subset.iterrows():
            print(f"  {row['ticker']:<8} {row['sharpe_ratio']:>8.2f} {row['sortino_ratio']:>8.2f} "
                  f"{row['total_return']:>9.2f} {row['max_drawdown']:>9.2f} "
                  f"{row['accuracy']:>9.1f} {row['trade_count']:>7d}")

    # ---- Summary Table (sorted by avg Sharpe) ----
    summary = df_results.groupby("config").agg(
        avg_sharpe=("sharpe_ratio", "mean"),
        avg_sortino=("sortino_ratio", "mean"),
        avg_return=("total_return", "mean"),
        avg_maxdd=("max_drawdown", "mean"),
        avg_winrate=("accuracy", "mean"),
        total_trades=("trade_count", "sum"),
    ).round(3)

    # Keep weight columns for sorting
    config_weights = df_results.drop_duplicates("config")[["config", "w_trend", "w_rsi", "w_macd"]].set_index("config")
    summary = summary.join(config_weights)
    summary = summary.sort_values("avg_sharpe", ascending=False)

    print("\n\n" + "=" * 100)
    print("  SUMMARY TABLE -- Sorted by Average Sharpe Ratio (best first)")
    print("=" * 100)
    print(f"\n  {'Config':<16} {'Avg Sharpe':>11} {'Avg Sortino':>12} {'Avg Return%':>12} "
          f"{'Avg MaxDD%':>11} {'Avg WinRate%':>13} {'Trades':>7}")
    print(f"  {'-'*16} {'-'*11} {'-'*12} {'-'*12} {'-'*11} {'-'*13} {'-'*7}")

    for config, row in summary.iterrows():
        marker = " <-- CURRENT" if config == "(40,30,30)" else ""
        print(f"  {config:<16} {row['avg_sharpe']:>11.3f} {row['avg_sortino']:>12.3f} "
              f"{row['avg_return']:>12.2f} {row['avg_maxdd']:>11.2f} "
              f"{row['avg_winrate']:>13.1f} {row['total_trades']:>7.0f}{marker}")

    # ---- Verdict ----
    best_config = summary.index[0]
    best_sharpe = summary.iloc[0]["avg_sharpe"]
    current = summary.loc["(40,30,30)"] if "(40,30,30)" in summary.index else None

    print("\n\n" + "=" * 100)
    print("  VERDICT")
    print("=" * 100)
    print(f"\n  Best configuration:   {best_config}  (Avg Sharpe: {best_sharpe:.3f})")

    if current is not None:
        current_sharpe = current["avg_sharpe"]
        current_rank = list(summary.index).index("(40,30,30)") + 1
        delta = best_sharpe - current_sharpe
        print(f"  Current (40,30,30):   Avg Sharpe: {current_sharpe:.3f}  (Rank: {current_rank}/{len(summary)})")
        print(f"  Delta:                {delta:+.3f} Sharpe points")

        if current_rank == 1:
            print(f"\n  [PASS] The current (40,30,30) split IS the best performing configuration.")
        elif abs(delta) < 0.05:
            print(f"\n  [TIED] The difference is marginal (<0.05 Sharpe). Current (40,30,30) is statistically comparable.")
        else:
            print(f"\n  [CHANGE] Configuration {best_config} outperforms the current (40,30,30) by {delta:.3f} Sharpe points.")
            print(f"    Consider switching to {best_config} for better risk-adjusted returns.")

    # ---- Also show which configs differ from current ----
    unique_results = df_results.groupby("config")["sharpe_ratio"].apply(list).to_dict()
    current_results = unique_results.get("(40,30,30)", [])
    n_different = 0
    for cfg, vals in unique_results.items():
        if cfg != "(40,30,30)" and vals != current_results:
            n_different += 1

    print(f"\n  Configs with different outcomes vs current: {n_different}/{len(WEIGHT_CONFIGS)-1}")
    if n_different == 0:
        print("  NOTE: All configs produced identical trade signals. This means the")
        print("        composite score changes from weight adjustments did not cross")
        print("        the BUY(>=65) / HOLD(45-65) / SELL(<45) thresholds differently.")
        print("        The current weights are robust to perturbation in this regime.")

    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
