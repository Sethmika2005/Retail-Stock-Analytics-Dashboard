# utils.py - Utility functions for formatting and display

import pandas as pd


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
