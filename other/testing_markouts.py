#!/usr/bin/env python3
# Markout / Reversion Analysis (multi-budget version, kept for ad-hoc use)
# BUY markout = (future-entry)/entry*100, SELL = flipped so positive = correct

import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import yfinance as yf

from models import (
    calculate_volume_score,
    compute_indicators,
    detect_market_regime,
    generate_rule_signal,
    generate_hybrid_recommendation,
)

import rl_agent

warnings.filterwarnings("ignore", category=FutureWarning)

# ── Configuration ────────────────────────────────────────────────────────────
TEST_STOCKS = ["AAPL", "MSFT", "GOOGL", "JPM", "JNJ", "PG", "KO", "WMT"]
PERIOD = "5y"
HORIZONS = [1, 2, 3, 5, 10, 21]
WARMUP = 200  # need 200 bars for SMA-200 + regime indicators
TIMESTEP_BUDGETS = [100_000]


# ── Data loading ─────────────────────────────────────────────────────────────
def _flatten_columns(raw):
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    return raw


def fetch_market_data():
    try:
        sp500 = _flatten_columns(yf.download("^GSPC", period=PERIOD, progress=False)).reset_index()
        vix = _flatten_columns(yf.download("^VIX", period=PERIOD, progress=False)).reset_index()
        return sp500, vix
    except Exception:
        return pd.DataFrame(), pd.DataFrame()


def fetch_stock_data(ticker: str):
    try:
        raw = yf.download(ticker, period=PERIOD, progress=False)
        if raw.empty or len(raw) < WARMUP + max(HORIZONS) + 5:
            return None
        raw = _flatten_columns(raw).reset_index()
        return compute_indicators(raw)
    except Exception as e:
        print(f"  [ERROR] {ticker}: {e}")
        return None


# ── Signal generation at a single bar ────────────────────────────────────────
RL_ACTION_TO_SIGNAL = {0: "BUY", 1: "SELL", 2: "HOLD"}


# Return (rule_signal, hybrid_signal, rl_signal) at row_pos
def signals_at_bar(df, row_pos, ticker, market_regime, ppo_model):
    historical = df.iloc[: row_pos + 1]

    rule_signal, _ = generate_rule_signal(historical, row_idx=-1)

    rl_prediction = None
    rl_signal = "HOLD"
    if ppo_model is not None:
        rl_prediction = rl_agent.predict_action(ppo_model, historical, row_idx=-1)
        if rl_prediction is not None:
            rl_signal = RL_ACTION_TO_SIGNAL.get(int(rl_prediction), "HOLD")

    volume_score, _ = calculate_volume_score(historical)
    rsi_value = historical["RSI"].iloc[-1] if "RSI" in historical.columns else 50
    hybrid_rec = generate_hybrid_recommendation(
        volume_score=volume_score,
        rsi_value=rsi_value,
        market_regime=market_regime,
        ticker=ticker,
        info={"shortName": ticker, "sector": "N/A"},
        time_horizon="long",
        price_data=historical,
        rl_prediction=rl_prediction,
    )
    hybrid_signal = hybrid_rec["recommendation"]

    return rule_signal, hybrid_signal, rl_signal


# ── Markout evaluation ───────────────────────────────────────────────────────
def markout(signal: str, entry: float, future: float) -> float | None:
    if signal == "BUY":
        return (future - entry) / entry * 100.0
    if signal == "SELL":
        return (entry - future) / entry * 100.0
    return None


def evaluate_stock(df, ticker, market_regime, ppo_model):
    records = []
    max_h = max(HORIZONS)
    closes = df["Close"].values
    dates = df["Date"] if "Date" in df.columns else pd.Series(df.index)

    last_valid = len(df) - max_h
    for row_pos in range(WARMUP, last_valid):
        rule_sig, hybrid_sig, rl_sig = signals_at_bar(df, row_pos, ticker, market_regime, ppo_model)

        # skip bars where all three are HOLD (no data to record)
        if rule_sig == "HOLD" and hybrid_sig == "HOLD" and rl_sig == "HOLD":
            continue

        entry = closes[row_pos]
        date = dates.iloc[row_pos]

        for strategy, sig in [("Rule", rule_sig), ("Hybrid", hybrid_sig), ("RL", rl_sig)]:
            if sig == "HOLD":
                continue
            for h in HORIZONS:
                fut = closes[row_pos + h]
                mk = markout(sig, entry, fut)
                records.append({
                    "ticker": ticker,
                    "date": date,
                    "strategy": strategy,
                    "signal": sig,
                    "horizon": h,
                    "entry_price": round(float(entry), 2),
                    "future_price": round(float(fut), 2),
                    "markout_pct": round(mk, 4),
                })
    return records


# ── Reporting ────────────────────────────────────────────────────────────────
def _summarise(subset: pd.DataFrame) -> dict:
    if subset.empty:
        return {"n": 0, "avg": np.nan, "median": np.nan, "win": np.nan}
    return {
        "n": len(subset),
        "avg": subset["markout_pct"].mean(),
        "median": subset["markout_pct"].median(),
        "win": (subset["markout_pct"] > 0).mean() * 100.0,
    }


def _row(label, stats_by_h, metric):
    cells = []
    for h in HORIZONS:
        v = stats_by_h[h][metric]
        cells.append(f"{v:+7.3f}" if not np.isnan(v) else "    nan")
    return f"  {label:<12} " + " ".join(cells)


def print_strategy_report(df: pd.DataFrame, strategy: str, label: str = ""):
    sdf = df[df["strategy"] == strategy]
    if sdf.empty:
        print(f"\nStrategy: {strategy} {label} (no signals)")
        return

    print(f"\n{'=' * 80}")
    print(f"Strategy: {strategy} {label}".rstrip())
    print(f"{'=' * 80}")
    header = "  " + " " * 12 + " ".join(f"{h:>7d}" for h in HORIZONS) + "      N"
    print(header.replace("N", f"N  (total signals={len(sdf)//len(HORIZONS)})"))

    for sig in ["BUY", "SELL"]:
        sub = sdf[sdf["signal"] == sig]
        if sub.empty:
            print(f"\n  {sig}: (no signals)")
            continue
        stats = {h: _summarise(sub[sub["horizon"] == h]) for h in HORIZONS}
        n_signals = stats[HORIZONS[0]]["n"]
        print(f"\n  {sig} signals (n={n_signals})")
        print(_row("avg %", stats, "avg"))
        print(_row("median %", stats, "median"))
        print(_row("win rate %", stats, "win"))

    # combined (BUY + sign-adjusted SELL already in same direction)
    stats = {h: _summarise(sdf[sdf["horizon"] == h]) for h in HORIZONS}
    n_signals = stats[HORIZONS[0]]["n"]
    print(f"\n  COMBINED (BUY+SELL, sign-adjusted)  (n={n_signals})")
    print(_row("avg %", stats, "avg"))
    print(_row("median %", stats, "median"))
    print(_row("win rate %", stats, "win"))


def print_horizon_header():
    print(f"\n{' ' * 14}" + " ".join(f"{h:>7d}d" for h in HORIZONS))


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("Downloading market data (SP500 & VIX)...")
    sp500_df, vix_df = fetch_market_data()
    if sp500_df.empty or vix_df.empty:
        market_regime = "Unknown"
        print("  WARNING: market data unavailable - regime='Unknown'")
    else:
        regime_result = detect_market_regime(sp500_df, vix_df)
        market_regime = regime_result[0] if isinstance(regime_result, tuple) else regime_result
        print(f"  Market regime: {market_regime}")

    all_records = []
    stock_data = {}
    for ticker in TEST_STOCKS:
        print(f"\n[{ticker}] Downloading...")
        df = fetch_stock_data(ticker)
        if df is None:
            print(f"  Skipping {ticker} - insufficient data.")
            continue
        print(f"  {len(df)} bars loaded.")
        stock_data[ticker] = df

    for budget in TIMESTEP_BUDGETS:
        print(f"\n{'#' * 80}\n# Training budget: {budget:,} timesteps\n{'#' * 80}")
        for ticker, df in stock_data.items():
            print(f"\n[{ticker}] Training PPO ({budget:,} steps)...")
            try:
                ppo_model = rl_agent.train_ppo_agent(df, total_timesteps=budget, train_split=0.8)
            except Exception as e:
                print(f"  [WARNING] PPO training failed: {e}")
                ppo_model = None
            print(f"  Evaluating markouts...")
            records = evaluate_stock(df, ticker, market_regime, ppo_model)
            for r in records:
                r["timesteps"] = budget
            print(f"  {len(records)} records.")
            all_records.extend(records)

    if not all_records:
        print("\nNo records generated.")
        return

    results_df = pd.DataFrame(all_records)

    # Per-budget strategy reports
    for budget in TIMESTEP_BUDGETS:
        sub = results_df[results_df["timesteps"] == budget]
        for strategy in ["Rule", "Hybrid", "RL"]:
            print_strategy_report(sub, strategy, label=f"[{budget:,} steps]")

    # Side-by-side comparison
    print(f"\n{'=' * 80}\nTIMESTEP COMPARISON — COMBINED (BUY+SELL sign-adjusted)\n{'=' * 80}")
    print(f"  {'Strategy':<10} {'Budget':>10}  " + " ".join(f"{h:>7d}d" for h in HORIZONS) + "      N")
    for strategy in ["Hybrid", "RL"]:
        for budget in TIMESTEP_BUDGETS:
            sub = results_df[(results_df["strategy"] == strategy) & (results_df["timesteps"] == budget)]
            if sub.empty:
                continue
            avgs = [sub[sub["horizon"] == h]["markout_pct"].mean() for h in HORIZONS]
            n = len(sub[sub["horizon"] == HORIZONS[0]])
            cells = " ".join(f"{v:+7.3f}" if not np.isnan(v) else "    nan" for v in avgs)
            print(f"  {strategy:<10} {budget:>10,}  {cells}  {n:>6d}")

    # Signal mix per budget (BUY/SELL/HOLD skew)
    print(f"\n{'=' * 80}\nSIGNAL MIX (per budget, RL strategy, horizon=1 unique signals)\n{'=' * 80}")
    for budget in TIMESTEP_BUDGETS:
        sub = results_df[(results_df["strategy"] == "RL") & (results_df["timesteps"] == budget) & (results_df["horizon"] == 1)]
        n_buy = (sub["signal"] == "BUY").sum()
        n_sell = (sub["signal"] == "SELL").sum()
        ratio = n_buy / max(n_sell, 1)
        print(f"  {budget:>7,} steps:  BUY={n_buy:>5d}  SELL={n_sell:>5d}  ratio={ratio:.2f}")

    out_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "thesis_diagrams",
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "markout_results_budgets.csv")
    results_df.to_csv(out_path, index=False)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
