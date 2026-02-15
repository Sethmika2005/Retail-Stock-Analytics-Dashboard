# US Stock Analytics Dashboard

A comprehensive financial analysis tool built with Python and Streamlit, providing retail investors with institutional-grade stock analysis capabilities.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Overview

This dashboard aggregates financial data from multiple sources to provide real-time stock analysis, technical indicators, fundamental metrics, news sentiment analysis, and risk assessment for US equities.

## Features

### 1. Analysis Tab
- Interactive candlestick charts with volume overlay
- Multiple timeframe selection (1M, 3M, 6M, 1Y, 5Y, Max)
- Technical indicator overlays (SMA, EMA, Bollinger Bands)

### 2. Overview Tab
- Company information (Exchange, S&P 500 membership, Sector, Industry)
- Key financial metrics (P/E, PEG, ROE, Debt/Equity)
- **Sector Market Share Pie Chart** - Visual representation of company's market cap relative to sector peers
- Risk level assessment

### 3. Technical Tab
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Moving Averages (20, 50, 200-day)

### 4. Fundamentals Tab
- Income Statement analysis
- Balance Sheet metrics
- Cash Flow statements
- Historical valuation charts

### 5. News & Sentiment Tab
- Real-time news feed powered by Finnhub API
- Sentiment analysis with visual indicators
- Sentiment summary metrics (Positive/Neutral/Negative counts)


## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| Visualisation | Plotly |
| Data Processing | Pandas, NumPy |
| Financial Data | yfinance |
| News Data | Finnhub API |
| Stock Lists | Wikipedia (S&P 500, NASDAQ-100, DJIA) |


## Data Sources

| Source | Data Provided | Update Frequency |
|--------|---------------|------------------|
| yfinance | Historical prices, fundamentals | Real-time |
| Finnhub | Company news | 30-min cache |
| Wikipedia | Index constituents (S&P 500, NASDAQ-100, DJIA) | 1-hour cache |


## Acknowledgements

- [Streamlit](https://streamlit.io/) for the web framework
- [yfinance](https://github.com/ranaroussi/yfinance) for financial data
- [Finnhub](https://finnhub.io/) for news API
- [Plotly](https://plotly.com/) for interactive visualisations

## Author

Sethmika Dias


---
*Last updated: 05 February 2026*

