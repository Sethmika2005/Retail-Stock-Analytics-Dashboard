#!/usr/bin/env python3
# Testing accuracy at SMA-20/50 crossover events.
# Simulates trades at golden/death cross points and reports profitable trade %.

import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# ── Configuration ────────────────────────────────────────────────────────────
TEST_STOCKS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM"]
PERIOD = "5y"          # historical data window
HOLD_DAYS = [5, 10, 20]  # evaluate outcome after N trading days


# compute_indicators is now imported from models.py


# Flatten MultiIndex columns from yfinance
def _flatten_columns(raw):
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    return raw


# ── Download & prepare data ──────────────────────────────────────────────────
# Download SP500 and VIX data for market regime detection
def fetch_market_data():
    try:
        sp500 = yf.download("^GSPC", period=PERIOD, progress=False)
        sp500 = _flatten_columns(sp500).reset_index()
        vix = yf.download("^VIX", period=PERIOD, progress=False)
        vix = _flatten_columns(vix).reset_index()
        return sp500, vix
    except Exception:
        return pd.DataFrame(), pd.DataFrame()


# Download historical data and compute indicators
def fetch_stock_data(ticker: str) -> pd.DataFrame | None:
    try:
        raw = yf.download(ticker, period=PERIOD, progress=False)
        if raw.empty or len(raw) < 200:
            return None
        raw = _flatten_columns(raw).reset_index()
        df = compute_indicators(raw)
        return df
    except Exception as e:
        print(f"  [ERROR] Failed to fetch {ticker}: {e}")
        return None


# ── Train RL model for a stock ───────────────────────────────────────────────
# Train PPO agent and return model (or None)
def train_rl_model(df: pd.DataFrame, ticker: str):
    try:
        return rl_agent.train_ppo_agent(df, total_timesteps=50_000, train_split=0.8)
    except Exception as e:
        print(f"  [WARNING] RL training failed for {ticker}: {e}")
        return None


# ── Evaluate crossover accuracy ──────────────────────────────────────────────
# Find every crossover event and measure post-trade accuracy.
# Golden crosses: price UP after N days = profitable BUY. Death crosses: price DOWN = profitable SELL.
def evaluate_crossovers(df: pd.DataFrame, ticker: str, market_regime: str, ppo_model=None):
    info = {"shortName": ticker, "sector": "N/A"}

    crossover_indices = df.index[df["SMA_Cross_Signal"] != 0].tolist()

    results = []

    for idx in crossover_indices:
        row_pos = df.index.get_loc(idx)
        cross_type = "golden_cross" if df["SMA_Cross_Signal"].iloc[row_pos] == 1 else "death_cross"
        cross_date = df["Date"].iloc[row_pos] if "Date" in df.columns else idx
        entry_price = df["Close"].iloc[row_pos]

        # ── Rule-based signal at this crossover ──────────────────────────
        historical = df.iloc[: row_pos + 1]
        rule_signal, rule_details = generate_rule_signal(historical, row_idx=-1)

        # ── Hybrid signal (rule + RL) ────────────────────────────────────
        rl_prediction = None
        if ppo_model is not None:
            rl_prediction = rl_agent.predict_action(ppo_model, historical, row_idx=-1)

        rsi_value = historical["RSI"].iloc[-1] if "RSI" in historical.columns else 50

        hybrid_rec = generate_hybrid_recommendation(
            rsi_value=rsi_value,
            market_regime=market_regime,
            ticker=ticker,
            info=info,
            time_horizon="long",
            price_data=historical,
            rl_prediction=rl_prediction,
        )
        hybrid_signal = hybrid_rec["recommendation"]
        confidence = hybrid_rec["confidence"]
        rl_agrees = hybrid_rec.get("rule_details", {}).get("rl_agrees")

        # ── Measure post-trade outcome at different horizons ─────────────
        for hold in HOLD_DAYS:
            future_pos = row_pos + hold
            if future_pos >= len(df):
                continue  # not enough future data

            exit_price = df["Close"].iloc[future_pos]
            price_change_pct = (exit_price - entry_price) / entry_price * 100

            # "Ideal" accuracy: did the crossover direction predict correctly?
            if cross_type == "golden_cross":
                crossover_correct = price_change_pct > 0  # price went up
            else:
                crossover_correct = price_change_pct < 0  # price went down

            # Rule-based accuracy: was the rule signal correct?
            if rule_signal == "BUY":
                rule_correct = price_change_pct > 0
            elif rule_signal == "SELL":
                rule_correct = price_change_pct < 0
            else:
                rule_correct = None  # HOLD - no trade taken

            # Hybrid accuracy: was the hybrid signal correct?
            if hybrid_signal == "BUY":
                hybrid_correct = price_change_pct > 0
            elif hybrid_signal == "SELL":
                hybrid_correct = price_change_pct < 0
            else:
                hybrid_correct = None  # HOLD - no trade taken

            results.append({
                "ticker": ticker,
                "date": cross_date,
                "cross_type": cross_type,
                "entry_price": round(entry_price, 2),
                "exit_price": round(exit_price, 2),
                "hold_days": hold,
                "price_change_pct": round(price_change_pct, 2),
                "crossover_correct": crossover_correct,
                "rule_signal": rule_signal,
                "rule_correct": rule_correct,
                "atv_confirmed": rule_details.get("atv_confirmed", False),
                "rsi_gate": rule_details.get("rsi_gate", "n/a"),
                "hybrid_signal": hybrid_signal,
                "hybrid_correct": hybrid_correct,
                "confidence": confidence,
                "rl_agrees": rl_agrees,
            })

    return results


# Non-crossover days where RL triggers an override (rule=HOLD → RL=BUY/SELL)
def evaluate_overrides(df: pd.DataFrame, ticker: str, market_regime: str, ppo_model):
    if ppo_model is None:
        return []
    info = {"shortName": ticker, "sector": "N/A"}
    results = []
    max_hold = max(HOLD_DAYS)

    non_cross = df.index[df["SMA_Cross_Signal"] == 0].tolist()
    for idx in non_cross:
        row_pos = df.index.get_loc(idx)
        if row_pos < 200 or row_pos + max_hold >= len(df):
            continue

        historical = df.iloc[: row_pos + 1]
        rl_prediction = rl_agent.predict_action(ppo_model, historical, row_idx=-1)
        if rl_prediction is None or rl_prediction == 2:  # HOLD => no override
            continue

        rsi_value = historical["RSI"].iloc[-1] if "RSI" in historical.columns else 50
        hybrid_rec = generate_hybrid_recommendation(
            rsi_value=rsi_value,
            market_regime=market_regime,
            ticker=ticker,
            info=info,
            time_horizon="long",
            price_data=historical,
            rl_prediction=rl_prediction,
        )
        hybrid_signal = hybrid_rec["recommendation"]
        if hybrid_signal == "HOLD":
            continue

        entry_price = df["Close"].iloc[row_pos]
        date = df["Date"].iloc[row_pos] if "Date" in df.columns else idx
        for hold in HOLD_DAYS:
            future_pos = row_pos + hold
            if future_pos >= len(df):
                continue
            exit_price = df["Close"].iloc[future_pos]
            pct = (exit_price - entry_price) / entry_price * 100
            correct = (pct > 0) if hybrid_signal == "BUY" else (pct < 0)
            results.append({
                "ticker": ticker,
                "date": date,
                "hold_days": hold,
                "hybrid_signal": hybrid_signal,
                "confidence": hybrid_rec["confidence"],
                "price_change_pct": round(pct, 2),
                "correct": correct,
            })
    return results


# Buy-and-hold total return from day 200 (indicators warmed) to last day
def compute_buy_hold(df: pd.DataFrame) -> dict:
    if len(df) < 210:
        return {"start_price": None, "end_price": None, "total_return_pct": None, "days": 0}
    start_price = df["Close"].iloc[200]
    end_price = df["Close"].iloc[-1]
    total_return = (end_price - start_price) / start_price * 100
    return {
        "start_price": round(start_price, 2),
        "end_price": round(end_price, 2),
        "total_return_pct": round(total_return, 2),
        "days": len(df) - 200,
    }


# ── Reporting ────────────────────────────────────────────────────────────────
# Print a summary report from all crossover results
def print_report(all_results: list[dict]):
    if not all_results:
        print("\nNo crossover events found.")
        return

    df = pd.DataFrame(all_results)

    print("\n" + "=" * 80)
    print("CROSSOVER ACCURACY REPORT")
    print("=" * 80)

    # ── Per-stock summary ────────────────────────────────────────────────
    for ticker in df["ticker"].unique():
        tdf = df[df["ticker"] == ticker]
        n_golden = len(tdf[(tdf["cross_type"] == "golden_cross") & (tdf["hold_days"] == HOLD_DAYS[0])])
        n_death = len(tdf[(tdf["cross_type"] == "death_cross") & (tdf["hold_days"] == HOLD_DAYS[0])])
        print(f"\n{'-' * 60}")
        print(f"  {ticker}  --  {n_golden} golden crosses, {n_death} death crosses")
        print(f"{'-' * 60}")

        for hold in HOLD_DAYS:
            subset = tdf[tdf["hold_days"] == hold]
            if subset.empty:
                continue

            n = len(subset)
            cross_acc = subset["crossover_correct"].sum() / n * 100

            # Rule-based: only count trades where a signal was given (not HOLD)
            rule_traded = subset[subset["rule_correct"].notna()]
            rule_acc = (rule_traded["rule_correct"].sum() / len(rule_traded) * 100) if len(rule_traded) > 0 else float("nan")
            rule_trade_rate = len(rule_traded) / n * 100

            # Hybrid
            hybrid_traded = subset[subset["hybrid_correct"].notna()]
            hybrid_acc = (hybrid_traded["hybrid_correct"].sum() / len(hybrid_traded) * 100) if len(hybrid_traded) > 0 else float("nan")
            hybrid_trade_rate = len(hybrid_traded) / n * 100

            print(f"\n  Hold period: {hold} days  ({n} crossover events)")
            print(f"    Raw crossover accuracy:    {cross_acc:5.1f}%")
            print(f"    Rule-based accuracy:       {rule_acc:5.1f}%  (traded {rule_trade_rate:.0f}% of crossovers)")
            print(f"    Hybrid (rule+RL) accuracy: {hybrid_acc:5.1f}%  (traded {hybrid_trade_rate:.0f}% of crossovers)")

    # ── Aggregate summary ────────────────────────────────────────────────
    print(f"\n{'=' * 80}")
    print("AGGREGATE ACROSS ALL STOCKS")
    print(f"{'=' * 80}")

    for hold in HOLD_DAYS:
        subset = df[df["hold_days"] == hold]
        if subset.empty:
            continue

        n = len(subset)
        cross_acc = subset["crossover_correct"].sum() / n * 100

        rule_traded = subset[subset["rule_correct"].notna()]
        rule_acc = (rule_traded["rule_correct"].sum() / len(rule_traded) * 100) if len(rule_traded) > 0 else float("nan")

        hybrid_traded = subset[subset["hybrid_correct"].notna()]
        hybrid_acc = (hybrid_traded["hybrid_correct"].sum() / len(hybrid_traded) * 100) if len(hybrid_traded) > 0 else float("nan")

        print(f"\n  Hold period: {hold} days  ({n} crossover events)")
        print(f"    Raw crossover accuracy:    {cross_acc:5.1f}%")
        print(f"    Rule-based accuracy:       {rule_acc:5.1f}%")
        print(f"    Hybrid (rule+RL) accuracy: {hybrid_acc:5.1f}%")

    # ── Breakdown by crossover type ──────────────────────────────────────
    print(f"\n{'=' * 80}")
    print("BREAKDOWN BY CROSSOVER TYPE (20-day hold)")
    print(f"{'=' * 80}")

    hold_20 = df[df["hold_days"] == 20]
    if not hold_20.empty:
        for ct in ["golden_cross", "death_cross"]:
            subset = hold_20[hold_20["cross_type"] == ct]
            if subset.empty:
                continue
            n = len(subset)
            cross_acc = subset["crossover_correct"].sum() / n * 100
            avg_return = subset["price_change_pct"].mean()

            rule_traded = subset[subset["rule_correct"].notna()]
            rule_acc = (rule_traded["rule_correct"].sum() / len(rule_traded) * 100) if len(rule_traded) > 0 else float("nan")

            hybrid_traded = subset[subset["hybrid_correct"].notna()]
            hybrid_acc = (hybrid_traded["hybrid_correct"].sum() / len(hybrid_traded) * 100) if len(hybrid_traded) > 0 else float("nan")

            label = "Golden Cross (BUY)" if ct == "golden_cross" else "Death Cross (SELL)"
            print(f"\n  {label}  ({n} events)")
            print(f"    Raw accuracy:       {cross_acc:5.1f}%   avg return: {avg_return:+.2f}%")
            print(f"    Rule-based accuracy: {rule_acc:5.1f}%")
            print(f"    Hybrid accuracy:     {hybrid_acc:5.1f}%")

    # ── ATV confirmation impact ──────────────────────────────────────────
    print(f"\n{'=' * 80}")
    print("IMPACT OF ATV CONFIRMATION (20-day hold)")
    print(f"{'=' * 80}")

    if not hold_20.empty:
        atv_yes = hold_20[hold_20["atv_confirmed"] == True]
        atv_no = hold_20[hold_20["atv_confirmed"] == False]

        if not atv_yes.empty:
            acc = atv_yes["crossover_correct"].sum() / len(atv_yes) * 100
            avg_ret = atv_yes["price_change_pct"].mean()
            print(f"\n  ATV confirmed:      {acc:5.1f}% accuracy  ({len(atv_yes)} events)  avg return: {avg_ret:+.2f}%")
        if not atv_no.empty:
            acc = atv_no["crossover_correct"].sum() / len(atv_no) * 100
            avg_ret = atv_no["price_change_pct"].mean()
            print(f"  ATV not confirmed:  {acc:5.1f}% accuracy  ({len(atv_no)} events)  avg return: {avg_ret:+.2f}%")

    # ── RL agreement impact ──────────────────────────────────────────────
    print(f"\n{'=' * 80}")
    print("IMPACT OF RL AGREEMENT (20-day hold)")
    print(f"{'=' * 80}")

    if not hold_20.empty:
        rl_yes = hold_20[hold_20["rl_agrees"] == True]
        rl_no = hold_20[hold_20["rl_agrees"] == False]

        if not rl_yes.empty:
            acc = rl_yes["crossover_correct"].sum() / len(rl_yes) * 100
            avg_ret = rl_yes["price_change_pct"].mean()
            print(f"\n  RL agrees:      {acc:5.1f}% accuracy  ({len(rl_yes)} events)  avg return: {avg_ret:+.2f}%")
        if not rl_no.empty:
            acc = rl_no["crossover_correct"].sum() / len(rl_no) * 100
            avg_ret = rl_no["price_change_pct"].mean()
            print(f"  RL disagrees:   {acc:5.1f}% accuracy  ({len(rl_no)} events)  avg return: {avg_ret:+.2f}%")
        if rl_yes.empty and rl_no.empty:
            print("\n  No RL data available.")

    # ── Confidence tier breakdown ────────────────────────────────────────
    print(f"\n{'=' * 80}")
    print("IMPACT OF CONFIDENCE TIER (20-day hold, hybrid signal only)")
    print(f"{'=' * 80}")

    tiers = [
        (">= 80", lambda c: c >= 80),
        ("70-79", lambda c: 70 <= c < 80),
        ("55-69", lambda c: 55 <= c < 70),
        ("< 55", lambda c: c < 55),
    ]

    if not hold_20.empty:
        traded = hold_20[hold_20["hybrid_correct"].notna()]
        for label, predicate in tiers:
            subset = traded[traded["confidence"].apply(predicate)]
            if subset.empty:
                print(f"\n  Confidence {label}: (no events)")
                continue
            acc = subset["hybrid_correct"].sum() / len(subset) * 100
            avg_ret = subset["price_change_pct"].mean()
            print(f"\n  Confidence {label}: {acc:5.1f}% accuracy  "
                  f"({len(subset)} trades)  avg return: {avg_ret:+.2f}%")

    print(f"\n{'=' * 80}")
    print("Done.")


# ── Main ─────────────────────────────────────────────────────────────────────
def print_override_report(override_results):
    if not override_results:
        print("\nNo RL override events.")
        return
    odf = pd.DataFrame(override_results)
    print(f"\n{'=' * 80}")
    print("RL OVERRIDE EVENTS (non-crossover days, RL drives the decision)")
    print(f"{'=' * 80}")
    for hold in HOLD_DAYS:
        s = odf[odf["hold_days"] == hold]
        if s.empty:
            continue
        acc = s["correct"].sum() / len(s) * 100
        avg_ret = s["price_change_pct"].mean()
        n_buy = (s["hybrid_signal"] == "BUY").sum()
        n_sell = (s["hybrid_signal"] == "SELL").sum()
        print(f"\n  {hold}-day hold: {acc:5.1f}% accuracy  avg return: {avg_ret:+.2f}%  "
              f"(n={len(s)}  BUY={n_buy}  SELL={n_sell})")


def print_benchmark_report(benchmarks):
    if not benchmarks:
        return
    print(f"\n{'=' * 80}")
    print("BUY-AND-HOLD BENCHMARK (from day 200 to end)")
    print(f"{'=' * 80}")
    total = 0.0
    for ticker, b in benchmarks.items():
        if b["total_return_pct"] is None:
            continue
        total += b["total_return_pct"]
        print(f"  {ticker:6s}  {b['total_return_pct']:+7.2f}%   "
              f"({b['days']} days, ${b['start_price']} → ${b['end_price']})")
    print(f"\n  Equal-weight avg:  {total / len(benchmarks):+.2f}%")


def main():
    all_results = []
    override_results = []
    benchmarks = {}

    # Fetch market data once for regime detection
    print("Downloading market data (SP500 & VIX)...")
    sp500_df, vix_df = fetch_market_data()
    if sp500_df.empty or vix_df.empty:
        print("  WARNING: Could not fetch market data - defaulting to 'Unknown' regime.")
        market_regime = "Unknown"
    else:
        market_regime = detect_market_regime(sp500_df, vix_df)
        print(f"  Current market regime: {market_regime}")

    for ticker in TEST_STOCKS:
        print(f"\n[{ticker}] Downloading data...")
        df = fetch_stock_data(ticker)
        if df is None:
            print(f"  Skipping {ticker} - insufficient data.")
            continue

        print(f"  {len(df)} trading days loaded.")

        # Train RL model
        print(f"  Training PPO agent...")
        ppo_model = train_rl_model(df, ticker)
        print(f"  PPO model ready." if ppo_model else f"  PPO model unavailable - rule-based only.")

        # Evaluate crossovers
        print(f"  Evaluating crossover events...")
        results = evaluate_crossovers(df, ticker, market_regime, ppo_model)
        n_events = len([r for r in results if r["hold_days"] == HOLD_DAYS[0]])
        print(f"  Found {n_events} crossover events.")
        all_results.extend(results)

        # Evaluate RL-override events (non-crossover days)
        print(f"  Scanning non-crossover days for RL overrides...")
        overrides = evaluate_overrides(df, ticker, market_regime, ppo_model)
        n_ov = len([r for r in overrides if r["hold_days"] == HOLD_DAYS[0]])
        print(f"  Found {n_ov} RL-override decisions.")
        override_results.extend(overrides)

        # Buy-and-hold benchmark
        benchmarks[ticker] = compute_buy_hold(df)

    print_report(all_results)
    print_override_report(override_results)
    print_benchmark_report(benchmarks)

    # ── Export per-event results for thesis reference ───────────────────
    out_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "thesis_diagrams",
    )
    os.makedirs(out_dir, exist_ok=True)
    if all_results:
        p = os.path.join(out_dir, "accuracy_results.csv")
        pd.DataFrame(all_results).to_csv(p, index=False)
        print(f"\nCrossover results      → {p}")
    if override_results:
        p = os.path.join(out_dir, "override_results.csv")
        pd.DataFrame(override_results).to_csv(p, index=False)
        print(f"RL override results    → {p}")
    if benchmarks:
        rows = [{"ticker": t, **b} for t, b in benchmarks.items()]
        p = os.path.join(out_dir, "buy_hold_benchmark.csv")
        pd.DataFrame(rows).to_csv(p, index=False)
        print(f"Buy-and-hold benchmark → {p}")


if __name__ == "__main__":
    main()
