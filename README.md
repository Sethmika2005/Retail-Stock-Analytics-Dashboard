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

### 6. Risk Tab
- Volatility analysis
- Drawdown metrics
- Risk score calculation

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| Visualisation | Plotly |
| Data Processing | Pandas, NumPy |
| Financial Data | yfinance |
| News Data | Finnhub API |
| Stock Lists | Wikipedia (S&P 500, NASDAQ-100, DJIA) |

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/us-stock-analytics-dashboard.git
cd us-stock-analytics-dashboard
```

2. Install dependencies:
```bash
pip install streamlit pandas numpy plotly yfinance requests
```

3. Run the application:
```bash
streamlit run Test_Run2.py
```

4. Open your browser and navigate to `http://localhost:8501`

## Project Structure

```
us-stock-analytics-dashboard/
│
├── Test_Run2.py          # Main application file (~5,600 lines)
├── README.md             # Project documentation
├── .gitignore            # Git ignore file
└── requirements.txt      # Python dependencies
```

## Data Sources

| Source | Data Provided | Update Frequency |
|--------|---------------|------------------|
| yfinance | Historical prices, fundamentals | Real-time |
| Finnhub | Company news | 30-min cache |
| Wikipedia | Index constituents (S&P 500, NASDAQ-100, DJIA) | 1-hour cache |

## Key Components

### Stock Universe Construction
The application dynamically aggregates stocks from:
- S&P 500 (500 large-cap US stocks)
- NASDAQ-100 (100 largest NASDAQ companies)
- Dow Jones Industrial Average (30 blue-chip stocks)

### Sentiment Analysis
Headlines are classified using keyword-based analysis:
- **Positive**: beat, surge, growth, profit, upgrade, bullish, strong
- **Negative**: miss, drop, plunge, downgrade, bearish, weak, decline

### Market Share Visualisation
- Displays top 10 companies by market cap within the selected stock's sector
- Companies with ≤2% share grouped into "Others"
- Selected company highlighted with distinct colour

## API Configuration

The application uses Finnhub for news data. The API key is configured in the code:
```python
FINNHUB_API_KEY = "your_api_key_here"
```

Get a free API key at [finnhub.io](https://finnhub.io/) (60 calls/minute on free tier).

## Screenshots

*Dashboard screenshots to be added*

## Known Limitations

- News data requires Finnhub API key
- Some smaller stocks may have limited fundamental data
- Real-time data subject to API rate limits

## Future Enhancements

- [ ] Portfolio tracking functionality
- [ ] Watchlist feature
- [ ] Email alerts for price movements
- [ ] Enhanced ML-based sentiment analysis
- [ ] Options chain analysis
- [ ] Peer comparison tables

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Streamlit](https://streamlit.io/) for the web framework
- [yfinance](https://github.com/ranaroussi/yfinance) for financial data
- [Finnhub](https://finnhub.io/) for news API
- [Plotly](https://plotly.com/) for interactive visualisations

## Author

[Your Name]

## Contact

For questions or feedback, please open an issue on GitHub.

---
*Last updated: January 2025*
