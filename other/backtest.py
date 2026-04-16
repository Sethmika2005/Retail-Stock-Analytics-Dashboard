#!/usr/bin/env python3
# Backtesting engine with Sharpe/Sortino/accuracy metrics.
# CLI: python backtest.py AAPL --months 24

import argparse
import os
import sys
import warnings

# Add parent dir so we can import models/rl_agent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import yfinance as yf

from models import (
    calculate_volume_score,
    compute_indicators,
    detect_market_regime,
    generate_hybrid_recommendation,
    generate_rule_signal,
)

import rl_agent

warnings.filterwarnings("ignore", category=FutureWarning)


# compute_indicators is now imported from models.py

# Walk through historical data day by day, calling strategy_fn for signals.
# Returns (equity_curve, trades, signals).
def simulate_strategy(df, strategy_fn, initial_capital=10000):
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


# Calculate backtest performance metrics (Sharpe, Sortino, accuracy, drawdown).
def calculate_backtest_metrics(equity_curve, trades, risk_free_rate=0.04):
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

def _make_novel_hybrid_strategy(info, market_regime, ppo_model):
    # Novel Hybrid: EMA+ATV+RSI rules + RL agent + regime-aware fallback + confidence
    def strategy_fn(df, idx):
        historical = df.iloc[:idx + 1]
        if len(historical) < 50:
            return "HOLD"

        # Compute scores at this step
        volume_score, _ = calculate_volume_score(historical)
        rsi_value = historical["RSI"].iloc[-1] if "RSI" in historical.columns else 50

        # RL prediction
        rl_prediction = None
        if ppo_model is not None:
            rl_prediction = rl_agent.predict_action(ppo_model, historical, row_idx=-1)

        # Full recommendation with regime awareness and RL integration
        rec = generate_hybrid_recommendation(
            volume_score=volume_score,
            rsi_value=rsi_value,
            market_regime=market_regime,
            ticker="BACKTEST",
            info=info,
            time_horizon="long",
            price_data=historical,
            rl_prediction=rl_prediction,
        )
        return rec["recommendation"]
    return strategy_fn


# Return dict of strategy functions for backtesting
def get_strategy_functions(info, market_regime, backtest_df=None, ticker="UNKNOWN"):
    ppo_model = None
    if backtest_df is not None and len(backtest_df) >= 100:
        print("  Training RL agent...", end=" ", flush=True)
        ppo_model = rl_agent.train_ppo_agent(backtest_df, ticker=ticker)
        print("done." if ppo_model is not None else "failed (not enough data).")

    return {
        "Novel Hybrid (EMA+ATV+RSI+RL)": _make_novel_hybrid_strategy(info, market_regime, ppo_model),
    }


# =============================================================================
# HELPER: Load market data
# =============================================================================

# Load S&P 500 and VIX data
def load_market_data():
    sp500 = yf.Ticker("^GSPC").history(period="2y", interval="1d", auto_adjust=False)
    vix = yf.Ticker("^VIX").history(period="2y", interval="1d", auto_adjust=False)
    return sp500, vix


# Load peer metrics for percentile scoring
def load_peer_metrics(ticker):
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

# Run backtest for a single ticker (CLI mode)
def run_backtest_cli(ticker, lookback_months=24):
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

    strategies = get_strategy_functions(info, market_regime, backtest_df=backtest_df, ticker=ticker)

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
