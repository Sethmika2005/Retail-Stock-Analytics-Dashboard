# US Stock Analytics Dashboard — Main Application
# Run: streamlit run app.py

import datetime as dt
import os
from io import StringIO  # needed to wrap HTML text so pd.read_html can parse it

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf
from dotenv import load_dotenv

# pull API keys and config from .env file into environment variables
load_dotenv()

from models import (
    calculate_volume_score,
    compute_indicators,
    detect_market_regime,
    generate_hybrid_recommendation,
    generate_rule_signal,
    calculate_piotroski_fscore,
)
from styles import inject_css, render_disclaimer_footer, render_disclaimer_sidebar
from tabs import dashboard, technical, fundamentals, news

st.set_page_config(page_title="US Stock Analytics Dashboard", layout="wide")
inject_css()


def _sort(df):
    # yfinance returns financials with years as columns — .T flips them to rows,
    # then sort_index puts them in chronological order
    return df.T.sort_index() if df is not None and not df.empty else None


# -- Data loading (cached) --

# Wikipedia blocks requests without a browser-like User-Agent header
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")


# @st.cache_data caches the result for ttl seconds (86400 = 24 hours)
# so we don't re-scrape Wikipedia on every page refresh
@st.cache_data(ttl=86400)
def load_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    resp = requests.get(url, headers=HEADERS)
    # StringIO wraps the HTML string so pandas can read it like a file
    tables = pd.read_html(StringIO(resp.text))
    df = tables[0][["Symbol", "Security", "GICS Sector", "GICS Sub-Industry"]].copy()
    df.columns = ["ticker", "name", "sector", "industry"]
    # yfinance uses dashes instead of dots in tickers (e.g. BRK-B not BRK.B)
    df["ticker"] = df["ticker"].str.replace(".", "-", regex=False)
    df["is_sp500"] = True
    return df


@st.cache_data(ttl=86400)
def load_nasdaq100_tickers():
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    resp = requests.get(url, headers=HEADERS)
    tables = pd.read_html(StringIO(resp.text))
    # Wikipedia has multiple tables on the page — we need to find the one
    # with ticker/symbol columns by checking each table's column names
    for table in tables:
        str_cols = [str(c).lower() for c in table.columns]
        # skip tables that don't have a ticker or symbol column
        if not any("ticker" in c or "symbol" in c for c in str_cols):
            continue
        ticker_col, name_col = None, None
        for col in table.columns:
            cl = str(col).lower()
            if "ticker" in cl or "symbol" in cl:
                ticker_col = col
            if "company" in cl or "security" in cl:
                name_col = col
        if ticker_col:
            df = pd.DataFrame()
            df["ticker"] = table[ticker_col].astype(str).str.replace(".", "-", regex=False)
            df["name"] = table[name_col] if name_col else df["ticker"]
            df["sector"] = "Technology"
            df["industry"] = "Technology"
            df["is_sp500"] = False
            return df
    return pd.DataFrame(columns=["ticker", "name", "sector", "industry", "is_sp500"])


@st.cache_data(ttl=86400)
def load_all_us_stocks():
    sp500 = load_sp500_tickers()
    nasdaq = load_nasdaq100_tickers()
    # stack both lists and remove any stocks that appear in both (keep S&P 500 version)
    combined = pd.concat([sp500, nasdaq], ignore_index=True)
    combined = combined.drop_duplicates(subset=["ticker"], keep="first")
    return combined.sort_values("ticker").reset_index(drop=True)


@st.cache_data(ttl=3600)
def load_history(ticker, period="max", interval="1d"):
    stock = yf.Ticker(ticker)
    # auto_adjust=False keeps raw OHLC prices (not adjusted for splits/dividends)
    data = stock.history(period=period, interval=interval, auto_adjust=False)
    if data.empty:
        st.warning(f"No data returned for {ticker}")
        return data
    return data.rename_axis("Date").reset_index()


@st.cache_data(ttl=3600)
def load_fundamentals(ticker):
    return yf.Ticker(ticker).get_info() or {}


@st.cache_data(ttl=86400)
def load_company_logo(ticker):
    url = f"https://finnhub.io/api/v1/stock/profile2?symbol={ticker}&token={FINNHUB_API_KEY}"
    resp = requests.get(url, timeout=10)
    return resp.json().get("logo", "") if resp.status_code == 200 else ""


@st.cache_data(ttl=1800)
def load_finnhub_news(ticker):
    today = dt.date.today()
    from_date = (today - dt.timedelta(days=30)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={from_date}&to={to_date}&token={FINNHUB_API_KEY}"
    resp = requests.get(url, timeout=10)
    return resp.json() if resp.status_code == 200 else []


@st.cache_data(ttl=3600)
def load_financial_statements(ticker):
    stock = yf.Ticker(ticker)
    return {
        "income_stmt": _sort(stock.income_stmt),
        "balance_sheet": _sort(stock.balance_sheet),
        "cashflow": _sort(stock.cashflow),
        "quarterly_income": _sort(stock.quarterly_income_stmt),
        "quarterly_balance": _sort(stock.quarterly_balance_sheet),
        "quarterly_cashflow": _sort(stock.quarterly_cashflow),
    }


@st.cache_data(ttl=3600)
def load_sector_peers_metrics(tickers: tuple):
    rows = []
    for sym in tickers:
        info = load_fundamentals(sym)
        rows.append({
            "ticker": sym,
            "pe": info.get("trailingPE"), "peg": info.get("pegRatio"),
            "roe": info.get("returnOnEquity"), "net_margin": info.get("profitMargins"),
            "rev_growth": info.get("revenueGrowth"), "de": info.get("debtToEquity"),
            "beta": info.get("beta"), "priceToBook": info.get("priceToBook"),
            "marketCap": info.get("marketCap"),
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def load_peer_fscores(tickers: tuple):
    rows = []
    for sym in tickers:
        stock = yf.Ticker(sym)
        inc, bs, cf = _sort(stock.income_stmt), _sort(stock.balance_sheet), _sort(stock.cashflow)
        score, details = calculate_piotroski_fscore(inc, bs, cf)
        rows.append({
            "ticker": sym, "fscore": score,
            "profitability": details.get("profitability"),
            "leverage": details.get("leverage_liquidity"),
            "efficiency": details.get("efficiency"),
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def load_market_data():
    sp500 = yf.Ticker("^GSPC").history(period="2y", interval="1d", auto_adjust=False)
    vix = yf.Ticker("^VIX").history(period="2y", interval="1d", auto_adjust=False)
    return sp500, vix


# -- Main app --

_disclaimer_tip = (
    "DISCLAIMER: For educational purposes only. Not investment advice. "
    "The creator is not a registered investment advisor (RIA), broker-dealer, or financial planner. "
    "BUY/SELL/HOLD signals are automated outputs of academic research models, not personalized advice. "
    "Investing involves risk of loss. Past performance does not guarantee future results. "
    "Data from third parties (Yahoo Finance, Finnhub); accuracy not guaranteed. "
    "Do your own research and consult a licensed financial advisor before investing."
)
st.markdown(
    f'<h1 style="display:inline;">US Stock Analytics Dashboard</h1>'
    f'<span title="{_disclaimer_tip}" style="font-size:18px;color:#64748B;cursor:help;margin-left:8px;vertical-align:super;">&#9432;</span>',
    unsafe_allow_html=True,
)

with st.spinner("Loading US stocks..."):
    all_stocks_df = load_all_us_stocks()
    if all_stocks_df.empty:
        st.error("Failed to load stock list. Please refresh the page.")
        st.stop()
    # convert to a set for O(1) lookup speed when checking if a ticker is in S&P 500
    sp500_set = set(all_stocks_df[all_stocks_df["is_sp500"]]["ticker"].tolist())

# Sidebar
with st.sidebar:
    st.markdown(
        '<div style="font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;'
        'font-size:18px;font-weight:700;color:#0F172A;letter-spacing:-0.02em;'
        'margin-bottom:16px;padding-top:4px;">Dashboard Controls</div>',
        unsafe_allow_html=True,
    )

    ticker_options = all_stocks_df["ticker"].tolist()
    # build "AAPL - Apple Inc." labels for the dropdown
    ticker_labels = [f"{r['ticker']} - {r['name']}" for _, r in all_stocks_df.iterrows()]
    default_idx = ticker_options.index("MSFT") if "MSFT" in ticker_options else 0

    # format_func tells Streamlit to display the label instead of the raw index number
    selected_idx = st.selectbox("Stock", range(len(ticker_options)),
                                format_func=lambda i: ticker_labels[i], index=default_idx)
    selected = ticker_options[selected_idx]

    period_options = ["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y", "MAX"]
    chart_period = st.selectbox("Chart Period", period_options, index=period_options.index("6M"))

    st.divider()

    owns_stock = st.toggle("I own this stock", value=False)
    cost_basis = st.number_input("Avg cost per share ($)", min_value=0.01, value=100.0, step=0.01) if owns_stock else None

    st.divider()
    st.caption(f"*Last updated: {dt.datetime.now().strftime('%I:%M %p')}*")
    if st.button("Refresh Data", help="Clear cached data and reload fresh data"):
        st.cache_data.clear()
        st.rerun()

render_disclaimer_sidebar()

# Load data
with st.spinner("Loading data..."):
    try:
        price_data = load_history(selected)
    except Exception as e:
        st.error(f"Rate limited by Yahoo Finance. Please wait a moment and refresh. ({type(e).__name__})")
        st.stop()
    info = load_fundamentals(selected)
    financials = load_financial_statements(selected)

fs = financials
piotroski_score, _ = calculate_piotroski_fscore(
    fs.get("income_stmt"), fs.get("balance_sheet"), fs.get("cashflow"))

if price_data.empty:
    st.error("No price data available for this ticker. Try another selection or wait a moment if rate limited.")
    st.stop()

price_data = compute_indicators(price_data)

# iloc[-1] gets the last row, iloc[-2] gets second-to-last — used for daily % change
last_row = price_data.iloc[-1]
prev_row = price_data.iloc[-2] if len(price_data) > 1 else last_row
change_pct = (last_row["Close"] - prev_row["Close"]) / prev_row["Close"] * 100

# Market analysis
with st.spinner("Analyzing market conditions..."):
    sp500_market, vix_market = load_market_data()
    market_regime, regime_color, regime_metrics = detect_market_regime(sp500_market, vix_market)
    volume_score, volume_details = calculate_volume_score(price_data)
    rsi_value = price_data["RSI"].iloc[-1] if "RSI" in price_data.columns else 50

    rule_details = None
    if len(price_data) >= 50:
        _, rule_details = generate_rule_signal(price_data)

    # RL agent
    import rl_agent
    rl_prediction = None
    with st.spinner("Loading RL agent..."):
        model = rl_agent.train_ppo_agent(price_data)
        if model is not None:
            rl_prediction = rl_agent.predict_action(model, price_data)

# Shared data
company_logo_url = load_company_logo(selected)
dashboard_recommendation = generate_hybrid_recommendation(
    volume_score, rsi_value, market_regime, selected, info,
    time_horizon="long", price_data=price_data, rl_prediction=rl_prediction,
)
news_items = load_finnhub_news(selected)

# Tabs
dashboard_tab, technical_tab, fundamentals_tab, news_tab = st.tabs(
    ["Dashboard", "Technical", "Fundamentals", "Recent News"])

with dashboard_tab:
    dashboard.render(
        selected=selected, price_data=price_data, info=info,
        last_row=last_row, change_pct=change_pct,
        volume_score=volume_score, volume_details=volume_details,
        market_regime=market_regime, regime_metrics=regime_metrics,
        recommendation_data=dashboard_recommendation, rsi_value=rsi_value,
        news_items=news_items, cost_basis=cost_basis,
        rule_details=dashboard_recommendation.get("rule_details", rule_details),
        logo_url=company_logo_url, is_sp500=selected in sp500_set,
        chart_period=chart_period, piotroski_score=piotroski_score,
    )

with technical_tab:
    technical.render(
        selected=selected, price_data=price_data, info=info,
        last_row=last_row, volume_score=volume_score, volume_details=volume_details,
        rule_details=dashboard_recommendation.get("rule_details", rule_details),
        rl_prediction=rl_prediction, rsi_value=rsi_value,
    )

with fundamentals_tab:
    fundamentals.render(
        selected=selected, info=info, financials=financials,
        all_stocks_df=all_stocks_df, price_data=price_data,
        load_sector_peers_metrics=load_sector_peers_metrics,
        load_peer_fscores=load_peer_fscores,
    )

with news_tab:
    news.render(news_items=news_items)

render_disclaimer_footer()
