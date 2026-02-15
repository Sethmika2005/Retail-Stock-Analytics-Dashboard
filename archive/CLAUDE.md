# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Streamlit web application that displays stock price charts and financial statements (income statement, balance sheet, cash flow) for any ticker using Yahoo Finance data.

## Commands

```bash
# Install dependencies
pip install streamlit yfinance pandas

# Run the application
streamlit run index.py
```

## Architecture

Single-file Streamlit app (`index.py`) with:
- `load_data(tkr)` - Cached function (1hr TTL) that fetches ticker info, 5-year price history, and latest annual financial statements via yfinance
- `format_commas(df)` - Formats numeric values with thousand separators for display
- UI renders a price chart and three-column layout for financial statements, each with CSV download buttons

Data flow: User enters ticker → `load_data()` queries yfinance API → Results cached and rendered in Streamlit widgets
