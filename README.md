# Retail Stock Analytics Dashboard

A Streamlit dashboard that produces Buy / Sell / Hold recommendations for US stocks by combining a rule-based strategy with a PPO reinforcement-learning agent. Built as a final-year project for retail investors who want a clearer picture than raw charts provide.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## What it does

Pick a stock, and the dashboard shows:

- A Buy / Sell / Hold call, with a confidence score and a written explanation of why
- The current market regime (Bull / Bear / Sideways / High-Volatility)
- Technical charts and indicators
- Company fundamentals, Piotroski F-Score, and peer comparison
- Recent news with headline sentiment

The recommendation comes from two sources: a rule strategy based on SMA crossovers, volume confirmation and RSI; and a PPO agent trained on the same stock's history. The rule is primary — the RL agent acts as a second opinion and can override when the rule defaults to HOLD.

## How the recommendation is built

**Rule-based signal** (`models.py`):
- SMA-20 / SMA-50 crossover triggers a candidate Buy (golden cross) or Sell (death cross)
- ATV slope (linear regression through the last 10 days of 20-day average volume) must be positive to confirm
- RSI gate blocks Buys when RSI > 70 and Sells when RSI < 30
- Otherwise the signal is HOLD

**RL agent** (`rl_agent.py`):
- PPO from stable-baselines3, trained per ticker on that ticker's full history
- 3-dimensional state: SMA crossover signal, normalised ATV slope, 1-day return
- 3 actions: Buy / Sell / Hold
- Reward: 5-day forward price return, scaled by a volume factor (heavier reward when the trade happens on high-volume days)
- 100,000 training timesteps by default

**Hybrid layer**:
- Confidence starts at 50
- Rule fires + RL agrees → 90
- Rule fires alone → 75
- Rule fires, RL disagrees → 60
- Both say HOLD → 70
- RL overrides a HOLD (no crossover event) → 55
- Pure HOLD with no RL → 40

**Market regime** is tagged using the S&P 500 and VIX: SMA-200 slope, SMA-50/200 crossover, and VIX level vs. its 20-day average.

## Tabs

- **Overview** — recommendation, confidence, written reasoning, regime, price chart with SMA overlays, key stats, position tracker (enter your cost basis to see P&L)
- **Technical** — candlestick chart with volume, RSI, MACD, Bollinger Bands, and the rule trace alongside the RL agent's current prediction
- **Fundamentals** — income statement, balance sheet, cash flow (annual + quarterly), Piotroski F-Score, sector peer comparison
- **Recent News** — Finnhub news feed with keyword-based sentiment labels (positive / neutral / negative)

## Project structure

```
app.py                  Streamlit entry point
models.py               Indicators, rule logic, hybrid layer, regime detection, F-Score
rl_agent.py             PPO training and inference (stable-baselines3 + Gymnasium)
styles.py               CSS and disclaimers
tabs/                   Per-tab render functions
EDA.ipynb               Exploratory data analysis
evaluation_results/     Main hybrid-strategy evaluation (markouts, agreement matrix, Kadia P&L)
accuracy_check/         Crossover-event accuracy test
thesis_diagrams/        Figures and tables for the thesis
archive/                Older prototypes and one-off scripts
other/                  Reference material and additional testing scripts
```

## Tech stack

| Component | Used for |
|-----------|----------|
| Streamlit | Web UI |
| Plotly | Charts |
| Pandas, NumPy | Data processing |
| stable-baselines3, Gymnasium | PPO agent |
| yfinance | Prices and fundamentals |
| Finnhub | Company news |
| Wikipedia | S&P 500 and NASDAQ-100 constituents |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env     # then paste your Finnhub API key
streamlit run app.py
```

A free Finnhub key (https://finnhub.io/register) covers the news and company-logo endpoints. yfinance needs no key.

## Data sources and caveats

- **yfinance** is an unofficial wrapper around Yahoo Finance. It has no SLA and Yahoo's terms do not permit redistribution of its data, so the project is fine for a thesis or personal use but is not suitable for a production deployment. A licensed vendor (Polygon, Finnhub, Alpaca, Tiingo) would be needed for that.
- Prices from Yahoo are delayed by 15 minutes.
- The first load for any ticker trains a PPO agent from scratch, which takes a minute or so. The trained model is then cached for the session.

## Disclaimer

This tool is for research and educational use only. It is not investment advice. Signals are automated outputs of academic models and past performance does not guarantee future results.

## Acknowledgements

- Streamlit, Plotly, stable-baselines3, yfinance, Finnhub

## Author

Sethmika Dias

---

*Last updated: 19 April 2026*
