# data.py - Data loading functions for stock data

import yfinance as yf
import pandas as pd
import streamlit as st


def _latest_col(df: pd.DataFrame):
    """Extract the latest column from a financial statement DataFrame."""
    if df is None or df.empty:
        return None, None
    # yfinance usually returns most recent period in the first column
    col = df.columns[0]
    # turn into a 2-col table: Item | Value (for the most recent year)
    out = df[[col]].reset_index()
    out.columns = ["Item", "Value"]
    return out, col


def _pretty_period(col):
    """Format a period column as a readable date string."""
    if col is None:
        return "N/A"
    try:
        return pd.to_datetime(str(col)).strftime("%Y-%m-%d")
    except Exception:
        return str(col)


@st.cache_data(ttl=3600)
def load_data(tkr: str) -> dict:
    """
    Load ticker data from Yahoo Finance.

    Returns a dict with:
        - name: Company name
        - hist: 5-year price history DataFrame
        - inc: Latest income statement
        - inc_period: Income statement period
        - bal: Latest balance sheet
        - bal_period: Balance sheet period
        - cf: Latest cash flow statement
        - cf_period: Cash flow period
    """
    t = yf.Ticker(tkr)

    # --- Meta / names / key metrics ---
    name = None
    metrics = {}
    try:
        info = t.get_info() or {}
        name = info.get("longName") or info.get("shortName")
        metrics = {
            "currency": info.get("currency", "USD"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "eps": info.get("trailingEps"),
            "dividend_yield": info.get("dividendYield"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "50d_avg": info.get("fiftyDayAverage"),
            "200d_avg": info.get("twoHundredDayAverage"),
            "volume": info.get("averageVolume"),
            "prev_close": info.get("previousClose"),
            "open": info.get("open"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
        }
    except Exception:
        name = None

    # --- Price history (5 years daily close, auto-adjusted) ---
    hist = t.history(period="5y", interval="1d", auto_adjust=True)
    if not hist.empty:
        hist = hist[["Close"]].copy()

    # --- Annual financial statements (latest column only) ---
    income_a = t.income_stmt
    balance_a = t.balance_sheet
    cashflow_a = t.cashflow

    inc_latest, inc_col = _latest_col(income_a)
    bal_latest, bal_col = _latest_col(balance_a)
    cf_latest, cf_col = _latest_col(cashflow_a)

    return {
        "name": name,
        "metrics": metrics,
        "hist": hist,
        "inc": inc_latest,
        "inc_period": _pretty_period(inc_col),
        "bal": bal_latest,
        "bal_period": _pretty_period(bal_col),
        "cf": cf_latest,
        "cf_period": _pretty_period(cf_col),
    }
