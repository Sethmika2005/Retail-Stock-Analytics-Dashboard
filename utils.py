# utils.py - Utility functions for formatting and display

import pandas as pd


def format_large_number(value, currency: str = "") -> str:
    """Format large numbers with B/M/K suffixes."""
    if value is None:
        return "N/A"
    try:
        v = float(value)
        prefix = f"{currency} " if currency else ""
        if v >= 1_000_000_000_000:
            return f"{prefix}{v / 1_000_000_000_000:.2f}T"
        elif v >= 1_000_000_000:
            return f"{prefix}{v / 1_000_000_000:.2f}B"
        elif v >= 1_000_000:
            return f"{prefix}{v / 1_000_000:.2f}M"
        elif v >= 1_000:
            return f"{prefix}{v / 1_000:.2f}K"
        else:
            return f"{prefix}{v:,.2f}"
    except (ValueError, TypeError):
        return "N/A"


def format_percent(value) -> str:
    """Format a decimal as percentage."""
    if value is None:
        return "N/A"
    try:
        return f"{float(value) * 100:.2f}%"
    except (ValueError, TypeError):
        return "N/A"


def format_price(value, currency: str = "") -> str:
    """Format a price value with currency."""
    if value is None:
        return "N/A"
    try:
        prefix = f"{currency} " if currency else ""
        return f"{prefix}{float(value):,.2f}"
    except (ValueError, TypeError):
        return "N/A"


def format_ratio(value) -> str:
    """Format a ratio value."""
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return "N/A"


def format_commas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Format numeric values in a DataFrame with thousand separators.

    Expects a DataFrame with a 'Value' column containing numeric data.
    """
    if df is None or df.empty:
        return df
    out = df.copy()

    def fmt(x):
        try:
            if pd.isna(x):
                return ""
            return f"{float(x):,.0f}"
        except Exception:
            return x

    if "Value" in out.columns:
        out["Value"] = out["Value"].apply(fmt)
    return out
