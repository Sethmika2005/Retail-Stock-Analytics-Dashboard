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
    calculate_volume_score,
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
def _flatten(raw):
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    return raw


def fetch_market_data():
    try:
        sp = _flatten(yf.download("^GSPC", period=PERIOD, progress=False)).reset_index()
        vix = _flatten(yf.download("^VIX", period=PERIOD, progress=False)).reset_index()
        return sp, vix
    except Exception:
        return pd.DataFrame(), pd.DataFrame()


def fetch_stock(ticker):
    try:
        raw = yf.download(ticker, period=PERIOD, progress=False)
        if raw.empty or len(raw) < WARMUP + max(HORIZONS) + 50:
            return None
        return compute_indicators(_flatten(raw).reset_index())
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

    vol_score, _ = calculate_volume_score(hist)
    rsi = hist["RSI"].iloc[-1] if "RSI" in hist.columns else 50
    hyb_rec = generate_hybrid_recommendation(
        volume_score=vol_score, rsi_value=rsi, market_regime=market_regime,
        ticker=ticker, info={"shortName": ticker, "sector": "N/A"},
        time_horizon="long", price_data=hist, rl_prediction=rl_pred,
    )
    hybrid_sig = hyb_rec["recommendation"]

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
        sigs = signals_at_bar(df, i, ticker, market_regime, ppo_model)
        bucket = sigs["bucket"]
        if all(sigs[s] == "HOLD" for s in STRATEGIES):
            continue
        entry = float(closes[i])
        date = dates.iloc[i]

        for strat in STRATEGIES:
            sig = sigs[strat]
            if sig == "HOLD":
                continue
            for h in HORIZONS:
                fut = float(closes[i + h])
                records.append({
                    "ticker": ticker, "date": date, "strategy": strat,
                    "signal": sig, "horizon": h,
                    "entry_price": round(entry, 2), "future_price": round(fut, 2),
                    "markout_pct": round(markout(sig, entry, fut), 4),
                    "bucket": bucket if strat == "Hybrid" else None,
                    "in_sample": False,
                })
    return records


# ── Trade simulation (Kadia metrics) ───────────────────────────────────────
def simulate_trades(df, ticker, market_regime, ppo_model):
    # Pairs BUY→SELL into round-trip trades; also tracks daily returns for Sharpe/Sortino
    closes = df["Close"].values
    test_start = max(WARMUP, int(len(df) * TRAIN_SPLIT))

    state = {s: {"in_pos": False, "entry_price": None, "entry_idx": None} for s in STRATEGIES}
    trades = {s: [] for s in STRATEGIES}
    daily_rets = {s: [] for s in STRATEGIES}

    for i in range(test_start, len(df)):
        sigs = signals_at_bar(df, i, ticker, market_regime, ppo_model)
        price = float(closes[i])
        prev = float(closes[i - 1]) if i > 0 else price

        for s in STRATEGIES:
            sig, st = sigs[s], state[s]
            daily_rets[s].append((price - prev) / prev * 100.0 if st["in_pos"] else 0.0)

            if sig == "BUY" and not st["in_pos"]:
                st.update(in_pos=True, entry_price=price, entry_idx=i)
            elif sig == "SELL" and st["in_pos"]:
                pnl = (price - st["entry_price"]) / st["entry_price"] * 100.0
                trades[s].append({
                    "ticker": ticker,
                    "entry_idx": st["entry_idx"], "exit_idx": i,
                    "entry_price": round(st["entry_price"], 2),
                    "exit_price": round(price, 2),
                    "pnl_pct": round(pnl, 4),
                    "profitable": pnl > 0,
                })
                st.update(in_pos=False, entry_price=None)

    return trades, daily_rets


def compute_metrics(trades_list, daily_rets):
    n = len(trades_list)
    if n == 0:
        return {"n_trades": 0, "accuracy": None, "avg_pnl": None,
                "sharpe": None, "sortino": None}

    profitable = sum(1 for t in trades_list if t["profitable"])
    avg_pnl = sum(t["pnl_pct"] for t in trades_list) / n
    dr = np.array(daily_rets)
    std = dr.std()
    downside = dr[dr < 0]
    down_std = np.sqrt((downside ** 2).mean()) if len(downside) > 0 else 0.0

    return {
        "n_trades": n,
        "profitable": profitable,
        "accuracy": round(profitable / n * 100.0, 2),
        "avg_pnl": round(avg_pnl, 2),
        "total_return": round(((1 + dr / 100).prod() - 1) * 100.0, 2),
        "sharpe": round(dr.mean() / std * np.sqrt(252), 2) if std > 0 else 0.0,
        "sortino": round(dr.mean() / down_std * np.sqrt(252), 2) if down_std > 0 else 0.0,
    }


# ── Reporting helpers ───────────────────────────────────────────────────────
def _stats(sub):
    if sub.empty:
        return None
    return {
        "n": len(sub),
        "avg": sub["markout_pct"].mean(),
        "median": sub["markout_pct"].median(),
        "win": (sub["markout_pct"] > 0).mean() * 100.0,
    }


def _fmt(v, w=7, p=3):
    return f"{v:+{w}.{p}f}" if v is not None and not np.isnan(v) else " " * (w - 3) + "nan"


def print_markout_tables(df):
    # Table A: headline markouts per strategy
    print(f"\n{'=' * 96}")
    print("TABLE A — Headline markouts per strategy (out-of-sample)")
    print(f"{'=' * 96}")
    print(f"  {'strategy':<12} {'h':>3}  {'n':>6} {'n_eff':>6}   {'avg%':>7}  {'med%':>7}  {'win%':>6}")
    for strat in STRATEGIES:
        for h in HORIZONS:
            s = _stats(df[(df["strategy"] == strat) & (df["horizon"] == h)])
            if s is None:
                print(f"  {strat:<12} {h:>3d}  {'—':>6}")
                continue
            marker = " *" if h == 5 else ""  # PPO reward horizon
            print(f"  {strat:<12} {h:>3d}  {s['n']:>6d} {int(s['n']/h):>6d}   "
                  f"{_fmt(s['avg'])}  {_fmt(s['median'])}  {s['win']:>5.1f}{marker}")
    print("  (* 5d = PPO reward horizon, in-distribution)")

    # Table B: hybrid override buckets
    print(f"\n{'=' * 96}")
    print("TABLE B — Hybrid override decomposition  (answers: is RL-override worth it?)")
    print(f"{'=' * 96}")
    hyb = df[df["strategy"] == "Hybrid"]
    print(f"  {'bucket':<12} {'h':>3}  {'n':>6}   {'avg%':>7}  {'win%':>6}")
    for bucket in ["concordant", "rule_led", "rl_override"]:
        for h in HORIZONS:
            s = _stats(hyb[(hyb["bucket"] == bucket) & (hyb["horizon"] == h)])
            if s is None:
                print(f"  {bucket:<12} {h:>3d}  {'—':>6}")
                continue
            print(f"  {bucket:<12} {h:>3d}  {s['n']:>6d}   {_fmt(s['avg'])}  {s['win']:>5.1f}")
        print()

    # Table C: per-ticker 5d sanity check
    print(f"\n{'=' * 96}")
    print("TABLE C — Per-ticker 5d sanity check")
    print(f"{'=' * 96}")
    print(f"  {'ticker':<8} " + " ".join(f"{s:>14}" for s in STRATEGIES))
    for ticker in sorted(df["ticker"].unique()):
        cells = []
        for strat in STRATEGIES:
            s = _stats(df[(df["ticker"] == ticker) & (df["strategy"] == strat) & (df["horizon"] == 5)])
            cells.append(f"{s['avg']:+6.2f}% n={s['n']:>3d}" if s else "           —  ")
        print(f"  {ticker:<8} " + " ".join(f"{c:>14}" for c in cells))

    # Consistency check
    hyb1 = hyb[hyb["horizon"] == HORIZONS[0]]
    by_bucket = hyb1["bucket"].value_counts().to_dict()
    status = "OK" if sum(by_bucket.values()) == len(hyb1) else "MISMATCH"
    print(f"\n[consistency] Hybrid non-HOLD bars at h={HORIZONS[0]}: "
          f"total={len(hyb1)}, buckets={by_bucket}, sum={sum(by_bucket.values())}  [{status}]")


def print_kadia_results(all_metrics, per_ticker):
    print(f"\n{'=' * 100}")
    print("KADIA-ALIGNED METRICS — Per strategy (pooled across all tickers, OOS only)")
    print(f"{'=' * 100}")
    print(f"  {'Strategy':<12} {'Trades':>7} {'Profitable':>11} {'Accuracy%':>10} "
          f"{'AvgP&L%':>8} {'TotalRet%':>10} {'Sharpe':>7} {'Sortino':>8}")
    print(f"  {'-'*12} {'-'*7} {'-'*11} {'-'*10} {'-'*8} {'-'*10} {'-'*7} {'-'*8}")
    for s in STRATEGIES:
        m = all_metrics[s]
        if m["n_trades"] == 0:
            print(f"  {s:<12} {'0':>7} {'—':>11} {'—':>10} {'—':>8} {'—':>10} {'—':>7} {'—':>8}")
            continue
        print(f"  {s:<12} {m['n_trades']:>7d} {m['profitable']:>11d} {m['accuracy']:>9.2f}% "
              f"{m['avg_pnl']:>+7.2f}% {m['total_return']:>+9.2f}% {m['sharpe']:>7.2f} {m['sortino']:>8.2f}")

    print(f"\n{'=' * 100}")
    print("PER-TICKER BREAKDOWN (Hybrid strategy)")
    print(f"{'=' * 100}")
    print(f"  {'Ticker':<8} {'Trades':>7} {'Accuracy%':>10} {'AvgP&L%':>8} "
          f"{'TotalRet%':>10} {'Sharpe':>7} {'Sortino':>8}")
    print(f"  {'-'*8} {'-'*7} {'-'*10} {'-'*8} {'-'*10} {'-'*7} {'-'*8}")
    for ticker, tm in per_ticker.items():
        hm = tm["Hybrid"]
        if hm["n_trades"] == 0:
            print(f"  {ticker:<8} {'0':>7} {'—':>10} {'—':>8} {'—':>10} {'—':>7} {'—':>8}")
            continue
        print(f"  {ticker:<8} {hm['n_trades']:>7d} {hm['accuracy']:>9.2f}% "
              f"{hm['avg_pnl']:>+7.2f}% {hm['total_return']:>+9.2f}% "
              f"{hm['sharpe']:>7.2f} {hm['sortino']:>8.2f}")


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    print("Downloading market data (SP500 & VIX)...")
    sp, vix = fetch_market_data()
    if sp.empty or vix.empty:
        regime = "Unknown"
        print("  WARNING: market data unavailable — regime='Unknown'")
    else:
        r = detect_market_regime(sp, vix)
        regime = r[0] if isinstance(r, tuple) else r
        print(f"  Market regime: {regime}")

    stock_data = {}
    for t in TEST_STOCKS:
        print(f"\n[{t}] Downloading...")
        df = fetch_stock(t)
        if df is None:
            print(f"  Skipping {t} — insufficient data.")
            continue
        print(f"  {len(df)} bars loaded.")
        stock_data[t] = df

    all_markout_records = []
    pooled_trades = {s: [] for s in STRATEGIES}
    pooled_daily = {s: [] for s in STRATEGIES}
    per_ticker_metrics = {}

    for ticker, df in stock_data.items():
        print(f"\n[{ticker}] Training PPO ({TIMESTEPS:,} steps, split={TRAIN_SPLIT})...")
        try:
            model = rl_agent.train_ppo_agent(df, total_timesteps=TIMESTEPS, train_split=TRAIN_SPLIT)
        except Exception as e:
            print(f"  [WARNING] PPO training failed: {e}")
            model = None

        # Both evaluations use the same model
        print(f"  Running markout evaluation...")
        recs = evaluate_markouts(df, ticker, regime, model)
        print(f"  {len(recs)} markout records.")
        all_markout_records.extend(recs)

        print(f"  Running trade simulation...")
        trades, daily_rets = simulate_trades(df, ticker, regime, model)
        ticker_metrics = {}
        for s in STRATEGIES:
            pooled_trades[s].extend(trades[s])
            pooled_daily[s].extend(daily_rets[s])
            ticker_metrics[s] = compute_metrics(trades[s], daily_rets[s])
            n = len(trades[s])
            acc = ticker_metrics[s]["accuracy"]
            print(f"    {s:<12}  {n:>3d} trades  "
                  f"{'acc=' + f'{acc:.1f}%' if acc is not None else 'no trades'}")
        per_ticker_metrics[ticker] = ticker_metrics

    # Print all results
    if all_markout_records:
        markout_df = pd.DataFrame(all_markout_records)
        print_markout_tables(markout_df)

    pooled_metrics = {s: compute_metrics(pooled_trades[s], pooled_daily[s]) for s in STRATEGIES}
    print_kadia_results(pooled_metrics, per_ticker_metrics)

    # Save CSVs
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "thesis_diagrams")
    os.makedirs(out_dir, exist_ok=True)

    if all_markout_records:
        markout_df.to_csv(os.path.join(out_dir, "markout_results_oos.csv"), index=False)
        print(f"\nMarkout CSV written to {os.path.join(out_dir, 'markout_results_oos.csv')}")

    kadia_rows = []
    for ticker, tm in per_ticker_metrics.items():
        for s in STRATEGIES:
            kadia_rows.append({"ticker": ticker, "strategy": s, **tm[s]})
    pd.DataFrame(kadia_rows).to_csv(os.path.join(out_dir, "kadia_metrics.csv"), index=False)
    print(f"Kadia CSV written to {os.path.join(out_dir, 'kadia_metrics.csv')}")


if __name__ == "__main__":
    main()
