#!/usr/bin/env python3
"""
Backtesting Engine
==================
Importable simulation engine with Sharpe/Sortino/accuracy metrics.
Also runnable as CLI: python backtest.py AAPL --months 24

Usage as module:
    from backtest import simulate_strategy, calculate_backtest_metrics
"""

import argparse
import sys
import warnings

import numpy as np
import pandas as pd
import yfinance as yf

from models import (
    calculate_technical_score,
    calculate_fundamental_score,
    calculate_volume_score,
    calculate_fundamental_score_paper2,
    detect_market_regime,
    generate_recommendation,
    generate_recommendation_paper1,
    generate_recommendation_paper2,
    generate_recommendation_combined,
    generate_paper1_signal,
)

# RL agent - graceful import
try:
    import rl_agent
    RL_AVAILABLE = rl_agent.is_available()
except (ImportError, OSError):
    RL_AVAILABLE = False

warnings.filterwarnings("ignore", category=FutureWarning)


# =============================================================================
# INDICATORS (mirrors app.py compute_indicators)
# =============================================================================

def compute_indicators(df):
    """Compute technical indicators (mirrors app.py compute_indicators)."""
    df = df.copy()
    df["SMA20"] = df["Close"].rolling(window=20).mean()
    df["SMA50"] = df["Close"].rolling(window=50).mean()
    df["SMA200"] = df["Close"].rolling(window=200).mean()
    rolling_20 = df["Close"].rolling(window=20)
    df["BB_MID"] = rolling_20.mean()
    df["BB_UPPER"] = df["BB_MID"] + 2 * rolling_20.std()
    df["BB_LOWER"] = df["BB_MID"] - 2 * rolling_20.std()

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
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
    df["ATR"] = tr.rolling(window=14).mean()

    ma60 = df["Close"].rolling(window=60).mean()
    std60 = df["Close"].rolling(window=60).std()
    df["Z_SCORE_60"] = (df["Close"] - ma60) / std60

    # EMA indicators (Paper 1)
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

    ema_cross = pd.Series(0, index=df.index)
    if len(df) > 1:
        ema20 = df["EMA20"].values
        ema50 = df["EMA50"].values
        for i in range(1, len(df)):
            if pd.notna(ema20[i]) and pd.notna(ema50[i]) and pd.notna(ema20[i-1]) and pd.notna(ema50[i-1]):
                if ema20[i-1] <= ema50[i-1] and ema20[i] > ema50[i]:
                    ema_cross.iloc[i] = 1
                elif ema20[i-1] >= ema50[i-1] and ema20[i] < ema50[i]:
                    ema_cross.iloc[i] = -1
    df["EMA_Cross_Signal"] = ema_cross

    # Volume indicators
    if "Volume" in df.columns:
        df["Volume_SMA20"] = df["Volume"].rolling(window=20).mean()
        df["Volume_SMA50"] = df["Volume"].rolling(window=50).mean()
        df["Rel_Volume"] = df["Volume"] / df["Volume_SMA20"]
        vol_sma = df["Volume_SMA20"]
        slope = vol_sma.rolling(window=10).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 10 and x.notna().all() else 0,
            raw=False,
        )
        df["Volume_Slope"] = slope

        df["ATV_20"] = df["Volume"].rolling(window=20).mean()
        atv_sma = df["ATV_20"]
        atv_slope = atv_sma.rolling(window=10).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 10 and x.notna().all() else 0,
            raw=False,
        )
        df["ATV_Slope"] = atv_slope

    # Monthly return
    df["Monthly_Return"] = df["Close"].pct_change(periods=22)

    return df


# =============================================================================
# SIMULATION ENGINE
# =============================================================================

def simulate_strategy(df, strategy_fn, initial_capital=10000):
    """
    Walk through historical data day by day, calling strategy_fn for signals.

    Args:
        df: DataFrame with indicators computed
        strategy_fn: fn(df, idx) -> "BUY" | "SELL" | "HOLD"
        initial_capital: Starting capital

    Returns:
        equity_curve: list of (date, equity_value)
        trades: list of dicts with trade details
        signals: list of (date, signal) for all days
    """
    capital = initial_capital
    position = 0  # shares held
    equity_curve = []
    trades = []
    signals = []
    entry_price = 0

    # Start after enough data for indicators (200 days)
    start_idx = min(200, len(df) - 1)

    for idx in range(start_idx, len(df)):
        price = df["Close"].iloc[idx]
        date = df["Date"].iloc[idx] if "Date" in df.columns else idx

        signal = strategy_fn(df, idx)
        signals.append((date, signal))

        if signal == "BUY" and position == 0:
            # Buy with all available capital
            shares = int(capital / price) if price > 0 else 0
            if shares > 0:
                position = shares
                entry_price = price
                capital -= shares * price
                trades.append({
                    "date": date,
                    "action": "BUY",
                    "price": price,
                    "shares": shares,
                })

        elif signal == "SELL" and position > 0:
            # Sell all shares
            capital += position * price
            pnl = (price - entry_price) * position
            trades.append({
                "date": date,
                "action": "SELL",
                "price": price,
                "shares": position,
                "pnl": pnl,
                "return_pct": (price - entry_price) / entry_price * 100 if entry_price > 0 else 0,
            })
            position = 0
            entry_price = 0

        # Calculate current equity
        equity = capital + position * price
        equity_curve.append((date, equity))

    return equity_curve, trades, signals


def calculate_backtest_metrics(equity_curve, trades, risk_free_rate=0.04):
    """
    Calculate backtest performance metrics.

    Args:
        equity_curve: list of (date, value)
        trades: list of trade dicts
        risk_free_rate: annual risk-free rate (default 4%)

    Returns:
        dict with Sharpe, Sortino, total_return, trade_count, accuracy, max_drawdown
    """
    if len(equity_curve) < 2:
        return {
            "sharpe_ratio": 0, "sortino_ratio": 0, "total_return": 0,
            "trade_count": 0, "accuracy": 0, "max_drawdown": 0,
            "annual_return": 0, "win_count": 0, "loss_count": 0,
        }

    values = np.array([v for _, v in equity_curve], dtype=np.float64)

    # Daily returns
    daily_returns = np.diff(values) / values[:-1]
    daily_returns = daily_returns[np.isfinite(daily_returns)]

    if len(daily_returns) == 0:
        return {
            "sharpe_ratio": 0, "sortino_ratio": 0, "total_return": 0,
            "trade_count": 0, "accuracy": 0, "max_drawdown": 0,
            "annual_return": 0, "win_count": 0, "loss_count": 0,
        }

    # Total return
    total_return = (values[-1] - values[0]) / values[0] * 100

    # Annual return (approximate)
    n_days = len(values)
    n_years = n_days / 252
    if n_years > 0 and values[0] > 0:
        annual_return = ((values[-1] / values[0]) ** (1 / n_years) - 1) * 100
    else:
        annual_return = 0

    # Daily risk-free rate
    daily_rf = risk_free_rate / 252
    excess_returns = daily_returns - daily_rf

    # Sharpe ratio (annualized)
    mean_excess = np.mean(excess_returns)
    std_returns = np.std(excess_returns, ddof=1) if len(excess_returns) > 1 else 1
    sharpe = (mean_excess / std_returns * np.sqrt(252)) if std_returns > 0 else 0

    # Sortino ratio (annualized)
    downside = excess_returns[excess_returns < 0]
    downside_std = np.std(downside, ddof=1) if len(downside) > 1 else 1
    sortino = (mean_excess / downside_std * np.sqrt(252)) if downside_std > 0 else 0

    # Max drawdown
    peak = np.maximum.accumulate(values)
    drawdown = (values - peak) / peak
    max_drawdown = np.min(drawdown) * 100

    # Trade metrics
    sell_trades = [t for t in trades if t["action"] == "SELL"]
    trade_count = len(sell_trades)
    profitable = [t for t in sell_trades if t.get("pnl", 0) > 0]
    accuracy = len(profitable) / trade_count * 100 if trade_count > 0 else 0

    return {
        "sharpe_ratio": round(sharpe, 2),
        "sortino_ratio": round(sortino, 2),
        "total_return": round(total_return, 2),
        "annual_return": round(annual_return, 2),
        "trade_count": trade_count,
        "accuracy": round(accuracy, 1),
        "max_drawdown": round(max_drawdown, 2),
        "win_count": len(profitable),
        "loss_count": trade_count - len(profitable),
    }


# =============================================================================
# STRATEGY WRAPPER FUNCTIONS
# =============================================================================

def _make_baseline_strategy(info, market_regime):
    """Strategy 1: Baseline (tech + fund)."""
    def strategy_fn(df, idx):
        historical = df.iloc[:idx + 1]
        if len(historical) < 200:
            return "HOLD"
        tech_score, _ = calculate_technical_score(historical)
        fund_score, _ = calculate_fundamental_score(info)
        rec = generate_recommendation(tech_score, fund_score, market_regime, "BACKTEST", info)
        return rec["recommendation"]
    return strategy_fn


def _make_paper1_strategy(info, market_regime):
    """Strategy 2: Paper 1 — EMA + ATV + RSI gate."""
    def strategy_fn(df, idx):
        historical = df.iloc[:idx + 1]
        if len(historical) < 50:
            return "HOLD"
        signal, _ = generate_paper1_signal(historical, row_idx=-1)
        return signal
    return strategy_fn


def _make_paper2_strategy(info, market_regime, peer_metrics=None):
    """Strategy 3: Paper 2 — Factor scoring."""
    def strategy_fn(df, idx):
        historical = df.iloc[:idx + 1]
        if len(historical) < 200:
            return "HOLD"
        tech_score, _ = calculate_technical_score(historical)
        fund_score_p2, _ = calculate_fundamental_score_paper2(
            info, peer_metrics=peer_metrics, risk_profile="moderate", price_data=historical
        )
        rec = generate_recommendation_paper2(
            tech_score, fund_score_p2, market_regime, "BACKTEST", info
        )
        return rec["recommendation"]
    return strategy_fn


def _make_combined_strategy(info, market_regime, peer_metrics=None):
    """Strategy 4: Combined — Paper 1 timing + Paper 2 quality."""
    def strategy_fn(df, idx):
        historical = df.iloc[:idx + 1]
        if len(historical) < 200:
            return "HOLD"
        tech_score, _ = calculate_technical_score(historical)
        volume_score, _ = calculate_volume_score(historical)
        rsi_val = historical["RSI"].iloc[-1] if "RSI" in historical.columns and pd.notna(historical["RSI"].iloc[-1]) else 50
        fund_score_p2, _ = calculate_fundamental_score_paper2(
            info, peer_metrics=peer_metrics, risk_profile="moderate", price_data=historical
        )
        rec = generate_recommendation_combined(
            tech_score, fund_score_p2, volume_score, rsi_val,
            market_regime, "BACKTEST", info, price_data=historical
        )
        return rec["recommendation"]
    return strategy_fn


def _make_paper1_rl_strategy(info, market_regime, ppo_model):
    """Strategy 5: Paper 1 + RL Agent — rule-based signal confirmed/overridden by PPO."""
    def strategy_fn(df, idx):
        historical = df.iloc[:idx + 1]
        if len(historical) < 50:
            return "HOLD"

        # Get rule-based signal
        rule_signal, _ = generate_paper1_signal(historical, row_idx=-1)

        # Get RL agent prediction
        rl_action = rl_agent.predict_action(ppo_model, historical, row_idx=-1)
        # rl_action: 0=buy, 1=sell, 2=hold
        rl_signal_map = {0: "BUY", 1: "SELL", 2: "HOLD"}
        rl_signal = rl_signal_map.get(rl_action, "HOLD")

        # If both agree, act with confidence
        if rule_signal == rl_signal:
            return rule_signal

        # If rule says HOLD but RL says BUY/SELL, trust RL
        if rule_signal == "HOLD" and rl_signal in ("BUY", "SELL"):
            return rl_signal

        # If rule says BUY/SELL but RL disagrees, trust RL (it learned from data)
        if rule_signal != "HOLD" and rl_signal != rule_signal:
            return rl_signal

        return "HOLD"
    return strategy_fn


def get_strategy_functions(info, market_regime, peer_metrics=None, backtest_df=None, ticker="UNKNOWN"):
    """Return dict of all strategy functions (includes RL if available)."""
    strategies = {
        "Baseline": _make_baseline_strategy(info, market_regime),
        "Paper 1: EMA+ATV+RSI": _make_paper1_strategy(info, market_regime),
        "Paper 2: Factor Weights": _make_paper2_strategy(info, market_regime, peer_metrics),
        "Combined": _make_combined_strategy(info, market_regime, peer_metrics),
    }

    # Add RL-enhanced strategy if available
    if RL_AVAILABLE and backtest_df is not None and len(backtest_df) >= 100:
        print("  Training RL agent...", end=" ", flush=True)
        ppo_model = rl_agent.get_ppo_agent(backtest_df, ticker=ticker)
        if ppo_model is not None:
            strategies["Paper 1 + RL Agent"] = _make_paper1_rl_strategy(info, market_regime, ppo_model)
            print("done.")
        else:
            print("failed (not enough data).")
    elif not RL_AVAILABLE:
        print("  RL agent: skipped (stable-baselines3 not installed)")

    return strategies


# =============================================================================
# HELPER: Load market data
# =============================================================================

def load_market_data():
    """Load S&P 500 and VIX data."""
    sp500 = yf.Ticker("^GSPC").history(period="2y", interval="1d", auto_adjust=False)
    vix = yf.Ticker("^VIX").history(period="2y", interval="1d", auto_adjust=False)
    return sp500, vix


def load_peer_metrics(ticker):
    """Load peer metrics for percentile scoring."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.get_info()
        sector = info.get("sector", "")
        if not sector:
            return None

        sp500_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(sp500_url)
        sp500_df = tables[0]
        sp500_df.columns = [c.replace(" ", "_") for c in sp500_df.columns]

        sector_col = None
        for c in sp500_df.columns:
            if "sector" in c.lower():
                sector_col = c
                break
        if not sector_col:
            return None

        peers = sp500_df[sp500_df[sector_col] == sector]["Symbol"].tolist()
        peers = [p.replace(".", "-") for p in peers if p.replace(".", "-") != ticker][:10]

        if len(peers) < 3:
            return None

        rows = []
        for p in peers + [ticker]:
            try:
                p_info = yf.Ticker(p).get_info()
                rows.append({
                    "ticker": p,
                    "pe": p_info.get("trailingPE"),
                    "peg": p_info.get("pegRatio"),
                    "roe": p_info.get("returnOnEquity"),
                    "net_margin": p_info.get("profitMargins"),
                    "rev_growth": p_info.get("revenueGrowth"),
                    "de": p_info.get("debtToEquity"),
                    "beta": p_info.get("beta"),
                    "priceToBook": p_info.get("priceToBook"),
                    "marketCap": p_info.get("marketCap"),
                })
            except Exception:
                continue

        if len(rows) < 3:
            return None

        return pd.DataFrame(rows)
    except Exception:
        return None


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def run_backtest_cli(ticker, lookback_months=24):
    """Run backtest for a single ticker (CLI mode)."""
    print(f"\n{'='*70}")
    print(f"  BACKTESTING: {ticker}")
    print(f"{'='*70}")

    stock = yf.Ticker(ticker)
    df = stock.history(period="max", interval="1d", auto_adjust=False)
    if df.empty or len(df) < 500:
        print(f"  ERROR: Insufficient data for {ticker} ({len(df)} days). Need 500+.")
        return None

    df = df.rename_axis("Date").reset_index()
    info = stock.get_info()

    print("Loading market data...")
    sp500, vix = load_market_data()
    market_regime, _, _ = detect_market_regime(sp500, vix)

    print("Loading peer metrics...")
    peer_metrics = load_peer_metrics(ticker)

    df = compute_indicators(df)

    # Use last N months
    total_days = len(df)
    start_idx = max(200, total_days - lookback_months * 22)
    backtest_df = df.iloc[start_idx:].copy().reset_index(drop=True)
    # Re-add Date column if lost
    if "Date" not in backtest_df.columns and "Date" in df.columns:
        backtest_df["Date"] = df["Date"].iloc[start_idx:].values

    strategies = get_strategy_functions(info, market_regime, peer_metrics, backtest_df=backtest_df, ticker=ticker)

    print(f"  Period: {backtest_df['Date'].iloc[0]} to {backtest_df['Date'].iloc[-1]}")
    print(f"  Days: {len(backtest_df)}")

    for name, fn in strategies.items():
        equity_curve, trades, signals = simulate_strategy(backtest_df, fn)
        metrics = calculate_backtest_metrics(equity_curve, trades)

        print(f"\n--- {name} ---")
        print(f"  Total Return: {metrics['total_return']:.2f}%")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"  Sortino Ratio: {metrics['sortino_ratio']:.2f}")
        print(f"  Max Drawdown: {metrics['max_drawdown']:.2f}%")
        print(f"  Trades: {metrics['trade_count']} (Win: {metrics['win_count']}, Loss: {metrics['loss_count']})")
        print(f"  Accuracy: {metrics['accuracy']:.1f}%")

    return True


def main():
    parser = argparse.ArgumentParser(description="Backtest scoring strategies on historical stock data")
    parser.add_argument("tickers", nargs="+", help="Ticker symbols to backtest (e.g., AAPL MSFT)")
    parser.add_argument("--months", type=int, default=24, help="Months of lookback (default: 24)")
    args = parser.parse_args()

    for ticker in args.tickers:
        ticker = ticker.upper()
        run_backtest_cli(ticker, lookback_months=args.months)

    print(f"\nBacktest complete.")


if __name__ == "__main__":
    main()
