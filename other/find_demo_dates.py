#!/usr/bin/env python3
# Find historical dates where the rule-based signal and PPO agent both said BUY or SELL
# AND the forward markouts were strong. Purpose: cherry-pick demo dates for thesis/viva so
# the dashboard can be rewound (via As-of-Date) to a moment that shows the system working.

import argparse
import os
import sys
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import pandas as pd

from models import detect_market_regime, generate_rule_signal
import rl_agent
from testing_evaluation import (
    TEST_STOCKS, TRAIN_SPLIT, TIMESTEPS, WARMUP,
    RL_ACTION_MAP, fetch_market_data, fetch_stock, markout,
)

warnings.filterwarnings("ignore", category=FutureWarning)

HORIZONS = [1, 5, 21, 63]


def find_concordant(df, ticker, regime, model):
    records = []
    closes = df["Close"].values
    dates = df["Date"] if "Date" in df.columns else pd.Series(df.index)
    first = max(WARMUP, int(len(df) * TRAIN_SPLIT))
    last = len(df) - max(HORIZONS)

    for i in range(first, last):
        hist = df.iloc[:i + 1]
        rule_sig, _ = generate_rule_signal(hist, row_idx=-1)
        if rule_sig == "HOLD":
            continue

        rl_pred = rl_agent.predict_action(model, hist, row_idx=-1) if model else None
        rl_sig = RL_ACTION_MAP.get(int(rl_pred), "HOLD") if rl_pred is not None else "HOLD"
        if rl_sig != rule_sig:
            continue  # concordant BUY or SELL only

        entry = float(closes[i])
        marks = {h: markout(rule_sig, entry, float(closes[i + h])) for h in HORIZONS}

        # Strength = mean signed markout across horizons, + bonus if every horizon is positive
        mean_mark = sum(marks.values()) / len(marks)
        all_positive = all(m > 0 for m in marks.values())
        strength = mean_mark + (1.0 if all_positive else 0.0)

        date = dates.iloc[i]
        records.append({
            "ticker": ticker,
            "date": date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else str(date),
            "signal": rule_sig,
            "entry_price": round(entry, 2),
            **{f"markout_{h}d": round(marks[h], 3) for h in HORIZONS},
            "strength_score": round(strength, 3),
        })
    return records


def main():
    parser = argparse.ArgumentParser(description="Find rule+RL concordant demo dates.")
    parser.add_argument("--tickers", nargs="+", default=TEST_STOCKS,
                        help="Tickers to scan. Defaults to the 15 thesis test stocks.")
    parser.add_argument("--min-strength", type=float, default=0.0,
                        help="Drop rows with strength_score below this threshold.")
    args = parser.parse_args()

    print("Downloading market data (SP500 & VIX)...")
    sp, vix = fetch_market_data()
    if sp.empty or vix.empty:
        regime = "Unknown"
        print("  WARNING: market data unavailable — regime='Unknown'")
    else:
        regime = detect_market_regime(sp, vix)
        print(f"  Market regime: {regime}")

    all_records = []
    for ticker in args.tickers:
        print(f"\n[{ticker}] Downloading...")
        df = fetch_stock(ticker)
        if df is None:
            print(f"  Skipping {ticker} — insufficient data.")
            continue
        print(f"  {len(df)} bars loaded.")

        print(f"  Training PPO ({TIMESTEPS:,} steps, split={TRAIN_SPLIT})...")
        try:
            model = rl_agent.train_ppo_agent(df, total_timesteps=TIMESTEPS, train_split=TRAIN_SPLIT)
        except Exception as e:
            print(f"  [WARNING] PPO training failed: {e}")
            model = None

        print("  Scanning for concordant signals...")
        records = find_concordant(df, ticker, regime, model)
        print(f"  {len(records)} concordant BUY/SELL dates found.")
        all_records.extend(records)

    if not all_records:
        print("\nNo concordant signals found.")
        return

    out_df = pd.DataFrame(all_records)
    out_df = out_df[out_df["strength_score"] >= args.min_strength]
    out_df = out_df.sort_values("strength_score", ascending=False).reset_index(drop=True)

    out_dir = os.path.join(ROOT, "thesis_diagrams")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "demo_dates.csv")
    out_df.to_csv(out_path, index=False)

    print(f"\n{len(out_df)} rows written to {out_path}")
    print("\nTop 10 strongest demo dates:")
    print(out_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
