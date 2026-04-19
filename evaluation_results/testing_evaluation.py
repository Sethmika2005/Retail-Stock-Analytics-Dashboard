#!/usr/bin/env python3
# Evaluate the Hybrid strategy against forward markouts (90%-concordant signals
# only), the Rule-vs-RL agreement matrix (all bars), and Kadia-style portfolio
# metrics (all Hybrid signals). Trains PPO on full history per ticker, evaluates
# from 2023 onwards.

import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import yfinance as yf

from models import compute_indicators, generate_rule_signal
import rl_agent

warnings.filterwarnings("ignore", category=FutureWarning)

#TEST_STOCKS = ["APP"]
TEST_STOCKS = ["AAPL", "APP", "GOOGL", "BAX", "JPM", "CVNA", "DASH", "ISRG", "AMZN", "TSLA"]
PERIOD = "max"
SIGNAL_START = pd.Timestamp("2023-01-01")
HORIZONS = [1, 2, 3, 5, 10, 21]
TIMESTEPS = 100_000
RL_ACTION_MAP = {0: "BUY", 1: "SELL", 2: "HOLD"}
ACTIONS = ["BUY", "SELL", "HOLD"]
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def fetch(ticker):
    raw = yf.download(ticker, period=PERIOD, progress=False, auto_adjust=False)
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    return compute_indicators(raw.reset_index())


def evaluate(ticker, df, model):
    closes = df["Close"].values
    dates = pd.to_datetime(df["Date"])
    start = dates.searchsorted(SIGNAL_START)
    signals, pairs, trades, daily = [], [], [], []
    position = None

    for i in range(start, len(df)):
        hist = df.iloc[:i + 1]
        rule_sig, rule_details = generate_rule_signal(hist, row_idx=-1) or ("HOLD", {})
        rl_sig = RL_ACTION_MAP.get(rl_agent.predict_action(model, hist, row_idx=-1), "HOLD")
        pairs.append((rule_sig, rl_sig))

        # Hybrid = rule, with RL-override when rule has no crossover event (matches models.py:412)
        hybrid = rule_sig
        if rule_sig == "HOLD" and rl_sig != "HOLD" and rule_details.get("crossover_type") == "none":
            hybrid = rl_sig

        price = float(closes[i])
        prev = float(closes[i - 1]) if i > 0 else price
        daily.append((price - prev) / prev * 100.0 if position is not None else 0.0)

        if hybrid == "BUY" and position is None:
            position = price
        elif hybrid == "SELL" and position is not None:
            trades.append((price - position) / position * 100.0)
            position = None

        if rule_sig != "HOLD" and rl_sig == rule_sig:
            row = {"ticker": ticker, "date": dates.iloc[i].date(),
                   "signal": rule_sig, "close": round(price, 2)}
            for h in HORIZONS:
                if i + h < len(df):
                    future = float(closes[i + h])
                    mk = (future - price) / price * 100.0 if rule_sig == "BUY" else (price - future) / price * 100.0
                    row[f"markout_{h}d"] = round(mk, 4)
                else:
                    row[f"markout_{h}d"] = np.nan
            signals.append(row)

    return signals, pairs, trades, daily


def markout_summary(df):
    if df.empty:
        return pd.DataFrame()
    out = [_markout_row(ticker, group) for ticker, group in df.groupby("ticker")]
    out.append(_markout_row("ALL", df))
    return pd.DataFrame(out)


def _markout_row(label, group):
    row = {"ticker": label, "n_signals": len(group)}
    for h in HORIZONS:
        col = group[f"markout_{h}d"].dropna()
        row[f"avg_markout_{h}d"] = round(col.mean(), 3) if len(col) else np.nan
        row[f"win_rate_{h}d"] = round((col > 0).mean() * 100.0, 2) if len(col) else np.nan
    return row


def agreement_matrix(pairs):
    mat = pd.DataFrame(0, index=ACTIONS, columns=ACTIONS, dtype=int)
    mat.index.name = "rule\\rl"
    for rule_sig, rl_sig in pairs:
        mat.loc[rule_sig, rl_sig] += 1
    return mat


def kadia(trades, daily):
    n = len(trades)
    returns = np.array(daily) if daily else np.array([0.0])
    std = returns.std()
    downside = returns[returns < 0]
    dstd = np.sqrt((downside ** 2).mean()) if len(downside) else 0.0
    wins = sum(1 for t in trades if t > 0)
    return {
        "n_trades": n,
        "accuracy_pct": round(wins / n * 100.0, 2) if n else np.nan,
        "avg_pnl_pct": round(sum(trades) / n, 3) if n else np.nan,
        "total_return_pct": round(((1 + returns / 100.0).prod() - 1) * 100.0, 2),
        "sharpe": round(returns.mean() / std * np.sqrt(252), 2) if std > 0 else 0.0,
        "sortino": round(returns.mean() / dstd * np.sqrt(252), 2) if dstd > 0 else 0.0,
    }


def main():
    all_signals, all_pairs, all_trades, all_daily = [], [], [], []
    kadia_rows = []

    for ticker in TEST_STOCKS:
        df = fetch(ticker)
        model = rl_agent.train_ppo_agent(df, total_timesteps=TIMESTEPS)
        signals, pairs, trades, daily = evaluate(ticker, df, model)
        all_signals.extend(signals)
        all_pairs.extend(pairs)
        all_trades.extend(trades)
        all_daily.extend(daily)
        kadia_rows.append({"ticker": ticker, **kadia(trades, daily)})

    kadia_rows.append({"ticker": "ALL", **kadia(all_trades, all_daily)})

    signals_df = pd.DataFrame(all_signals)
    summary_df = markout_summary(signals_df)
    matrix_df = agreement_matrix(all_pairs)
    kadia_df = pd.DataFrame(kadia_rows)

    signals_df.to_csv(os.path.join(OUT_DIR, "signals.csv"), index=False)
    summary_df.to_csv(os.path.join(OUT_DIR, "summary.csv"), index=False)
    matrix_df.to_csv(os.path.join(OUT_DIR, "agreement_matrix.csv"))
    kadia_df.to_csv(os.path.join(OUT_DIR, "kadia.csv"), index=False)

    print("\nMarkout summary (90%-concordant signals):")
    print(summary_df.to_string(index=False))
    print("\nRule vs RL agreement matrix (all bars since 2023):")
    print(matrix_df.to_string())
    print("\nKadia metrics (Hybrid strategy):")
    print(kadia_df.to_string(index=False))


if __name__ == "__main__":
    main()
