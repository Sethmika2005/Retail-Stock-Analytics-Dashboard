#!/usr/bin/env python3
"""
Testing Accuracy at Crossover Events
=====================================
Measures the actual accuracy (profitable trade %) of the rule-based and
hybrid (rule + RL) models specifically at SMA-20/50 crossover points.

For each stock:
  1. Downloads historical data & computes indicators.
  2. Finds every golden cross and death cross event.
  3. Simulates the trade triggered by each crossover and tracks the outcome.
  4. Reports per-stock and aggregate accuracy at crossover events only.

Usage:
    python testing_accuracy.py
"""

import warnings
import numpy as np
import pandas as pd
import yfinance as yf

from models import (
    calculate_technical_score,
    calculate_volume_score,
    detect_market_regime,
    generate_paper1_signal,
    generate_recommendation_paper1,
)

try:
    import rl_agent
    RL_AVAILABLE = rl_agent.is_available()
except (ImportError, OSError):
    RL_AVAILABLE = False

warnings.filterwarnings("ignore", category=FutureWarning)

# ── Configuration ────────────────────────────────────────────────────────────
TEST_STOCKS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM"]
PERIOD = "5y"          # historical data window
HOLD_DAYS = [5, 10, 20]  # evaluate outcome after N trading days


# ── Indicator computation (mirrors backtest.py / app.py) ─────────────────────
def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()

    rolling_20 = df["Close"].rolling(20)
    df["BB_MID"] = rolling_20.mean()
    df["BB_UPPER"] = df["BB_MID"] + 2 * rolling_20.std()
    df["BB_LOWER"] = df["BB_MID"] - 2 * rolling_20.std()

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_SIGNAL"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_HIST"] = df["MACD"] - df["MACD_SIGNAL"]

    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14).mean()

    ma60 = df["Close"].rolling(60).mean()
    std60 = df["Close"].rolling(60).std()
    df["Z_SCORE_60"] = (df["Close"] - ma60) / std60

    # SMA indicators (Paper 1 — Kadia et al. use SMA crossover)
    df["SMA20"] = df["Close"].rolling(window=20).mean()
    df["SMA50"] = df["Close"].rolling(window=50).mean()

    sma_cross = pd.Series(0, index=df.index)
    if len(df) > 1:
        sma20 = df["SMA20"].values
        sma50 = df["SMA50"].values
        for i in range(1, len(df)):
            if (pd.notna(sma20[i]) and pd.notna(sma50[i])
                    and pd.notna(sma20[i - 1]) and pd.notna(sma50[i - 1])):
                if sma20[i - 1] <= sma50[i - 1] and sma20[i] > sma50[i]:
                    sma_cross.iloc[i] = 1   # golden cross
                elif sma20[i - 1] >= sma50[i - 1] and sma20[i] < sma50[i]:
                    sma_cross.iloc[i] = -1  # death cross
    df["SMA_Cross_Signal"] = sma_cross

    if "Volume" in df.columns:
        df["Volume_SMA20"] = df["Volume"].rolling(20).mean()
        df["Volume_SMA50"] = df["Volume"].rolling(50).mean()
        df["Rel_Volume"] = df["Volume"] / df["Volume_SMA20"]
        vol_sma = df["Volume_SMA20"]
        slope = vol_sma.rolling(10).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0]
            if len(x) == 10 and x.notna().all() else 0,
            raw=False,
        )
        df["Volume_Slope"] = slope
        df["ATV_20"] = df["Volume"].rolling(20).mean()
        atv_sma = df["ATV_20"]
        atv_slope = atv_sma.rolling(10).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0]
            if len(x) == 10 and x.notna().all() else 0,
            raw=False,
        )
        df["ATV_Slope"] = atv_slope

    df["Monthly_Return"] = df["Close"].pct_change(periods=22)
    return df


def _flatten_columns(raw):
    """Flatten MultiIndex columns from yfinance."""
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    return raw


# ── Download & prepare data ──────────────────────────────────────────────────
def fetch_market_data():
    """Download SP500 and VIX data for market regime detection."""
    try:
        sp500 = yf.download("^GSPC", period=PERIOD, progress=False)
        sp500 = _flatten_columns(sp500).reset_index()
        vix = yf.download("^VIX", period=PERIOD, progress=False)
        vix = _flatten_columns(vix).reset_index()
        return sp500, vix
    except Exception:
        return pd.DataFrame(), pd.DataFrame()


def fetch_stock_data(ticker: str) -> pd.DataFrame | None:
    """Download historical data and compute indicators."""
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
def train_rl_model(df: pd.DataFrame, ticker: str):
    """Train PPO agent and return model (or None)."""
    if not RL_AVAILABLE:
        return None
    try:
        model = rl_agent.train_ppo_agent(df, ticker=ticker, total_timesteps=50_000)
        return model
    except Exception as e:
        print(f"  [WARNING] RL training failed for {ticker}: {e}")
        return None


# ── Evaluate crossover accuracy ──────────────────────────────────────────────
def evaluate_crossovers(df: pd.DataFrame, ticker: str, market_regime: str, ppo_model=None):
    """
    Find every crossover event and measure post-trade accuracy.

    For golden crosses: checks if price went UP after N days (profitable BUY).
    For death crosses:  checks if price went DOWN after N days (profitable SELL).

    Also records what the rule-based and hybrid models actually signalled,
    so we can see if their gating (ATV / RSI) improved accuracy.
    """
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
        rule_signal, rule_details = generate_paper1_signal(historical, row_idx=-1)

        # ── Hybrid signal (rule + RL) ────────────────────────────────────
        rl_prediction = None
        if ppo_model is not None:
            rl_prediction = rl_agent.predict_action(ppo_model, historical, row_idx=-1)

        tech_score, _ = calculate_technical_score(historical)
        volume_score, _ = calculate_volume_score(historical)
        rsi_value = historical["RSI"].iloc[-1] if "RSI" in historical.columns else 50

        hybrid_rec = generate_recommendation_paper1(
            tech_score=tech_score,
            volume_score=volume_score,
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
        rl_agrees = hybrid_rec.get("paper1_details", {}).get("rl_agrees")

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


# ── Reporting ────────────────────────────────────────────────────────────────
def print_report(all_results: list[dict]):
    """Print a summary report from all crossover results."""
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

    print(f"\n{'=' * 80}")
    print("Done.")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    all_results = []

    # Fetch market data once for regime detection
    print("Downloading market data (SP500 & VIX)...")
    sp500_df, vix_df = fetch_market_data()
    if sp500_df.empty or vix_df.empty:
        print("  WARNING: Could not fetch market data - defaulting to 'Unknown' regime.")
        market_regime = "Unknown"
    else:
        regime_result = detect_market_regime(sp500_df, vix_df)
        market_regime = regime_result[0] if isinstance(regime_result, tuple) else regime_result
        print(f"  Current market regime: {market_regime}")

    for ticker in TEST_STOCKS:
        print(f"\n[{ticker}] Downloading data...")
        df = fetch_stock_data(ticker)
        if df is None:
            print(f"  Skipping {ticker} - insufficient data.")
            continue

        print(f"  {len(df)} trading days loaded.")

        # Train RL model
        ppo_model = None
        if RL_AVAILABLE:
            print(f"  Training PPO agent...")
            ppo_model = train_rl_model(df, ticker)
            if ppo_model:
                print(f"  PPO model ready.")
            else:
                print(f"  PPO model unavailable - rule-based only.")

        # Evaluate crossovers
        print(f"  Evaluating crossover events...")
        results = evaluate_crossovers(df, ticker, market_regime, ppo_model)
        n_events = len([r for r in results if r["hold_days"] == HOLD_DAYS[0]])
        print(f"  Found {n_events} crossover events.")
        all_results.extend(results)

    print_report(all_results)


if __name__ == "__main__":
    main()
