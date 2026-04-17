#!/usr/bin/env python3
# Unified evaluation: Markout returns + Kadia trade metrics (accuracy, Sharpe, Sortino).
# Runs both evaluations in one pass per ticker on the out-of-sample window.
# Strategies: Rule, Rule-gated, Hybrid, RL-only.

import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import yfinance as yf

from models import (
    compute_indicators,
    detect_market_regime,
    generate_rule_signal,
    generate_hybrid_recommendation,
)
import rl_agent

warnings.filterwarnings("ignore", category=FutureWarning)

# ── Config ──────────────────────────────────────────────────────────────────
TEST_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "NVDA", "JPM", "JNJ", "XOM", "PG", "KO", "WMT",
    "INTC", "PFE", "BA", "T", "PYPL",
]
PERIOD = "5y"
HORIZONS = [1, 2, 3, 5, 10, 21]
WARMUP = 200
TRAIN_SPLIT = 0.8
TIMESTEPS = 100_000
STRATEGIES = ["Rule", "Rule-gated", "Hybrid", "RL-only"]
RL_ACTION_MAP = {0: "BUY", 1: "SELL", 2: "HOLD"}


# ── Data helpers ────────────────────────────────────────────────────────────
def flatten_columns(raw):
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    return raw


def fetch_market_data():
    try:
        sp = flatten_columns(yf.download("^GSPC", period=PERIOD, progress=False)).reset_index()
        vix = flatten_columns(yf.download("^VIX", period=PERIOD, progress=False)).reset_index()
        return sp, vix
    except Exception:
        return pd.DataFrame(), pd.DataFrame()


def fetch_stock(ticker):
    try:
        raw = yf.download(ticker, period=PERIOD, progress=False)
        if raw.empty or len(raw) < WARMUP + max(HORIZONS) + 50:
            return None
        return compute_indicators(flatten_columns(raw).reset_index())
    except Exception as e:
        print(f"  [ERROR] {ticker}: {e}")
        return None


# ── Signal generation ───────────────────────────────────────────────────────
def signals_at_bar(df, row_pos, ticker, market_regime, ppo_model):
    # Returns dict of signals per strategy + hybrid bucket label
    hist = df.iloc[:row_pos + 1]
    rule_sig, _ = generate_rule_signal(hist, row_idx=-1)

    rl_pred = rl_agent.predict_action(ppo_model, hist, row_idx=-1) if ppo_model else None
    rl_sig = RL_ACTION_MAP.get(int(rl_pred), "HOLD") if rl_pred is not None else "HOLD"

    rsi = hist["RSI"].iloc[-1] if "RSI" in hist.columns else 50
    hybrid_rec = generate_hybrid_recommendation(
        rsi_value=rsi, market_regime=market_regime,
        ticker=ticker, info={"shortName": ticker, "sector": "N/A"},
        time_horizon="long", price_data=hist, rl_prediction=rl_pred,
    )
    hybrid_sig = hybrid_rec["recommendation"]

    # Rule-gated: RL has veto power, no override power
    rule_gated = rule_sig if (rule_sig != "HOLD" and rl_sig in (rule_sig, "HOLD")) else "HOLD"

    # Bucket tells us where the hybrid signal came from
    bucket = None
    if hybrid_sig != "HOLD":
        if rule_sig == "HOLD":
            bucket = "rl_override"
        elif rl_sig == rule_sig:
            bucket = "concordant"
        else:
            bucket = "rule_led"

    return {
        "Rule": rule_sig, "Rule-gated": rule_gated,
        "Hybrid": hybrid_sig, "RL-only": rl_sig,
        "bucket": bucket,
    }


# ── Markout evaluation ─────────────────────────────────────────────────────
def markout(signal, entry, future):
    # BUY profits when price rises; SELL profits when price falls
    if signal == "BUY":
        return (future - entry) / entry * 100.0
    if signal == "SELL":
        return (entry - future) / entry * 100.0
    return None


def evaluate_markouts(df, ticker, market_regime, ppo_model):
    records = []
    closes = df["Close"].values
    dates = df["Date"] if "Date" in df.columns else pd.Series(df.index)
    first = max(WARMUP, int(len(df) * TRAIN_SPLIT))
    last = len(df) - max(HORIZONS)

    for i in range(first, last):
        signals = signals_at_bar(df, i, ticker, market_regime, ppo_model)
        bucket = signals["bucket"]
        if all(signals[strategy] == "HOLD" for strategy in STRATEGIES):
            continue
        entry = float(closes[i])
        date = dates.iloc[i]

        for strategy in STRATEGIES:
            signal = signals[strategy]
            if signal == "HOLD":
                continue
            for horizon in HORIZONS:
                future_price = float(closes[i + horizon])
                records.append({
                    "ticker": ticker, "date": date, "strategy": strategy,
                    "signal": signal, "horizon": horizon,
                    "entry_price": round(entry, 2), "future_price": round(future_price, 2),
                    "markout_pct": round(markout(signal, entry, future_price), 4),
                    "bucket": bucket if strategy == "Hybrid" else None,
                    "in_sample": False,
                })
    return records


# ── Trade simulation (Kadia metrics) ───────────────────────────────────────
def simulate_trades(df, ticker, market_regime, ppo_model):
    # Pairs BUY→SELL into round-trip trades; also tracks daily returns for Sharpe/Sortino
    closes = df["Close"].values
    test_start = max(WARMUP, int(len(df) * TRAIN_SPLIT))

    position = {strategy: {"in_position": False, "entry_price": None, "entry_idx": None} for strategy in STRATEGIES}
    trades = {strategy: [] for strategy in STRATEGIES}
    daily_returns = {strategy: [] for strategy in STRATEGIES}

    for i in range(test_start, len(df)):
        signals = signals_at_bar(df, i, ticker, market_regime, ppo_model)
        price = float(closes[i])
        prev_price = float(closes[i - 1]) if i > 0 else price

        for strategy in STRATEGIES:
            signal = signals[strategy]
            pos = position[strategy]
            daily_returns[strategy].append(
                (price - prev_price) / prev_price * 100.0 if pos["in_position"] else 0.0
            )

            if signal == "BUY" and not pos["in_position"]:
                pos.update(in_position=True, entry_price=price, entry_idx=i)
            elif signal == "SELL" and pos["in_position"]:
                pnl = (price - pos["entry_price"]) / pos["entry_price"] * 100.0
                trades[strategy].append({
                    "ticker": ticker,
                    "entry_idx": pos["entry_idx"], "exit_idx": i,
                    "entry_price": round(pos["entry_price"], 2),
                    "exit_price": round(price, 2),
                    "pnl_pct": round(pnl, 4),
                    "profitable": pnl > 0,
                })
                pos.update(in_position=False, entry_price=None)

    return trades, daily_returns


def compute_metrics(trades_list, daily_returns):
    n = len(trades_list)
    if n == 0:
        return {"n_trades": 0, "accuracy": None, "avg_pnl": None,
                "sharpe": None, "sortino": None}

    profitable = sum(1 for trade in trades_list if trade["profitable"])
    avg_pnl = sum(trade["pnl_pct"] for trade in trades_list) / n
    returns = np.array(daily_returns)
    std_dev = returns.std()
    downside = returns[returns < 0]
    downside_std = np.sqrt((downside ** 2).mean()) if len(downside) > 0 else 0.0

    return {
        "n_trades": n,
        "profitable": profitable,
        "accuracy": round(profitable / n * 100.0, 2),
        "avg_pnl": round(avg_pnl, 2),
        "total_return": round(((1 + returns / 100).prod() - 1) * 100.0, 2),
        "sharpe": round(returns.mean() / std_dev * np.sqrt(252), 2) if std_dev > 0 else 0.0,
        "sortino": round(returns.mean() / downside_std * np.sqrt(252), 2) if downside_std > 0 else 0.0,
    }


# ── Reporting helpers ───────────────────────────────────────────────────────
def get_stats(filtered):
    if filtered.empty:
        return None
    return {
        "n": len(filtered),
        "avg": filtered["markout_pct"].mean(),
        "median": filtered["markout_pct"].median(),
        "win": (filtered["markout_pct"] > 0).mean() * 100.0,
    }


def format_number(value, width=7, precision=3):
    if value is not None and not np.isnan(value):
        return f"{value:+{width}.{precision}f}"
    return " " * (width - 3) + "nan"


def print_markout_tables(df):
    # Table A: headline markouts per strategy
    print(f"\n{'=' * 96}")
    print("TABLE A — Headline markouts per strategy (out-of-sample)")
    print(f"{'=' * 96}")
    print(f"  {'strategy':<12} {'h':>3}  {'n':>6} {'n_eff':>6}   {'avg%':>7}  {'med%':>7}  {'win%':>6}")
    for strategy in STRATEGIES:
        for horizon in HORIZONS:
            stats = get_stats(df[(df["strategy"] == strategy) & (df["horizon"] == horizon)])
            if stats is None:
                print(f"  {strategy:<12} {horizon:>3d}  {'—':>6}")
                continue
            marker = " *" if horizon == 5 else ""  # PPO reward horizon
            print(f"  {strategy:<12} {horizon:>3d}  {stats['n']:>6d} {int(stats['n']/horizon):>6d}   "
                  f"{format_number(stats['avg'])}  {format_number(stats['median'])}  {stats['win']:>5.1f}{marker}")
    print("  (* 5d = PPO reward horizon, in-distribution)")

    # Table B: hybrid override buckets
    print(f"\n{'=' * 96}")
    print("TABLE B — Hybrid override decomposition  (answers: is RL-override worth it?)")
    print(f"{'=' * 96}")
    hybrid_rows = df[df["strategy"] == "Hybrid"]
    print(f"  {'bucket':<12} {'h':>3}  {'n':>6}   {'avg%':>7}  {'win%':>6}")
    for bucket in ["concordant", "rule_led", "rl_override"]:
        for horizon in HORIZONS:
            stats = get_stats(hybrid_rows[(hybrid_rows["bucket"] == bucket) & (hybrid_rows["horizon"] == horizon)])
            if stats is None:
                print(f"  {bucket:<12} {horizon:>3d}  {'—':>6}")
                continue
            print(f"  {bucket:<12} {horizon:>3d}  {stats['n']:>6d}   {format_number(stats['avg'])}  {stats['win']:>5.1f}")
        print()

    # Table C: per-ticker 5d sanity check
    print(f"\n{'=' * 96}")
    print("TABLE C — Per-ticker 5d sanity check")
    print(f"{'=' * 96}")
    print(f"  {'ticker':<8} " + " ".join(f"{strategy:>14}" for strategy in STRATEGIES))
    for ticker in sorted(df["ticker"].unique()):
        cells = []
        for strategy in STRATEGIES:
            stats = get_stats(df[(df["ticker"] == ticker) & (df["strategy"] == strategy) & (df["horizon"] == 5)])
            cells.append(f"{stats['avg']:+6.2f}% n={stats['n']:>3d}" if stats else "           —  ")
        print(f"  {ticker:<8} " + " ".join(f"{cell:>14}" for cell in cells))

    # Consistency check
    hybrid_first = hybrid_rows[hybrid_rows["horizon"] == HORIZONS[0]]
    by_bucket = hybrid_first["bucket"].value_counts().to_dict()
    status = "OK" if sum(by_bucket.values()) == len(hybrid_first) else "MISMATCH"
    print(f"\n[consistency] Hybrid non-HOLD bars at h={HORIZONS[0]}: "
          f"total={len(hybrid_first)}, buckets={by_bucket}, sum={sum(by_bucket.values())}  [{status}]")


def print_kadia_results(all_metrics, per_ticker):
    print(f"\n{'=' * 100}")
    print("KADIA-ALIGNED METRICS — Per strategy (pooled across all tickers, OOS only)")
    print(f"{'=' * 100}")
    print(f"  {'Strategy':<12} {'Trades':>7} {'Profitable':>11} {'Accuracy%':>10} "
          f"{'AvgP&L%':>8} {'TotalRet%':>10} {'Sharpe':>7} {'Sortino':>8}")
    print(f"  {'-'*12} {'-'*7} {'-'*11} {'-'*10} {'-'*8} {'-'*10} {'-'*7} {'-'*8}")
    for strategy in STRATEGIES:
        metrics = all_metrics[strategy]
        if metrics["n_trades"] == 0:
            print(f"  {strategy:<12} {'0':>7} {'—':>11} {'—':>10} {'—':>8} {'—':>10} {'—':>7} {'—':>8}")
            continue
        print(f"  {strategy:<12} {metrics['n_trades']:>7d} {metrics['profitable']:>11d} {metrics['accuracy']:>9.2f}% "
              f"{metrics['avg_pnl']:>+7.2f}% {metrics['total_return']:>+9.2f}% "
              f"{metrics['sharpe']:>7.2f} {metrics['sortino']:>8.2f}")

    print(f"\n{'=' * 100}")
    print("PER-TICKER BREAKDOWN (Hybrid strategy)")
    print(f"{'=' * 100}")
    print(f"  {'Ticker':<8} {'Trades':>7} {'Accuracy%':>10} {'AvgP&L%':>8} "
          f"{'TotalRet%':>10} {'Sharpe':>7} {'Sortino':>8}")
    print(f"  {'-'*8} {'-'*7} {'-'*10} {'-'*8} {'-'*10} {'-'*7} {'-'*8}")
    for ticker, ticker_results in per_ticker.items():
        hybrid_metrics = ticker_results["Hybrid"]
        if hybrid_metrics["n_trades"] == 0:
            print(f"  {ticker:<8} {'0':>7} {'—':>10} {'—':>8} {'—':>10} {'—':>7} {'—':>8}")
            continue
        print(f"  {ticker:<8} {hybrid_metrics['n_trades']:>7d} {hybrid_metrics['accuracy']:>9.2f}% "
              f"{hybrid_metrics['avg_pnl']:>+7.2f}% {hybrid_metrics['total_return']:>+9.2f}% "
              f"{hybrid_metrics['sharpe']:>7.2f} {hybrid_metrics['sortino']:>8.2f}")


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    print("Downloading market data (SP500 & VIX)...")
    sp, vix = fetch_market_data()
    if sp.empty or vix.empty:
        regime = "Unknown"
        print("  WARNING: market data unavailable — regime='Unknown'")
    else:
        regime = detect_market_regime(sp, vix)
        print(f"  Market regime: {regime}")

    stock_data = {}
    for ticker in TEST_STOCKS:
        print(f"\n[{ticker}] Downloading...")
        df = fetch_stock(ticker)
        if df is None:
            print(f"  Skipping {ticker} — insufficient data.")
            continue
        print(f"  {len(df)} bars loaded.")
        stock_data[ticker] = df

    all_markout_records = []
    pooled_trades = {strategy: [] for strategy in STRATEGIES}
    pooled_daily = {strategy: [] for strategy in STRATEGIES}
    per_ticker_metrics = {}

    for ticker, df in stock_data.items():
        print(f"\n[{ticker}] Training PPO ({TIMESTEPS:,} steps, split={TRAIN_SPLIT})...")
        try:
            model = rl_agent.train_ppo_agent(df, total_timesteps=TIMESTEPS, train_split=TRAIN_SPLIT)
        except Exception as e:
            print(f"  [WARNING] PPO training failed: {e}")
            model = None

        # Both evaluations use the same trained model
        print(f"  Running markout evaluation...")
        markout_records = evaluate_markouts(df, ticker, regime, model)
        print(f"  {len(markout_records)} markout records.")
        all_markout_records.extend(markout_records)

        print(f"  Running trade simulation...")
        trades, daily_returns = simulate_trades(df, ticker, regime, model)
        ticker_metrics = {}
        for strategy in STRATEGIES:
            pooled_trades[strategy].extend(trades[strategy])
            pooled_daily[strategy].extend(daily_returns[strategy])
            ticker_metrics[strategy] = compute_metrics(trades[strategy], daily_returns[strategy])
            n = len(trades[strategy])
            acc = ticker_metrics[strategy]["accuracy"]
            print(f"    {strategy:<12}  {n:>3d} trades  "
                  f"{'acc=' + f'{acc:.1f}%' if acc is not None else 'no trades'}")
        per_ticker_metrics[ticker] = ticker_metrics

    # Print all results
    if all_markout_records:
        markout_df = pd.DataFrame(all_markout_records)
        print_markout_tables(markout_df)

    pooled_metrics = {strategy: compute_metrics(pooled_trades[strategy], pooled_daily[strategy]) for strategy in STRATEGIES}
    print_kadia_results(pooled_metrics, per_ticker_metrics)

    # Save CSVs
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "thesis_diagrams")
    os.makedirs(out_dir, exist_ok=True)

    if all_markout_records:
        markout_df.to_csv(os.path.join(out_dir, "markout_results_oos.csv"), index=False)
        print(f"\nMarkout CSV written to {os.path.join(out_dir, 'markout_results_oos.csv')}")

    kadia_rows = []
    for ticker, ticker_results in per_ticker_metrics.items():
        for strategy in STRATEGIES:
            kadia_rows.append({"ticker": ticker, "strategy": strategy, **ticker_results[strategy]})
    pd.DataFrame(kadia_rows).to_csv(os.path.join(out_dir, "kadia_metrics.csv"), index=False)
    print(f"Kadia CSV written to {os.path.join(out_dir, 'kadia_metrics.csv')}")


if __name__ == "__main__":
    main()
