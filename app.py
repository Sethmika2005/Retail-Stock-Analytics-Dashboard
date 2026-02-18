# =============================================================================
# US Stock Analytics Dashboard - Main Application
# =============================================================================
# Run: streamlit run app.py
# =============================================================================

import datetime as dt
import os
from io import StringIO

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import from modular files
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
    classify_headline_sentiment,
)
from components import (
    get_status_color,
    get_status_bg,
    render_metric_card,
    render_badge_card,
    render_compact_card,
    format_large_number,
    format_mcap,
)
from tabs import analysis, overview, technical, fundamentals, news, backtest

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(page_title="US Stock Analytics Dashboard", layout="wide")

# =============================================================================
# CUSTOM CSS - Premium Light Theme with Source Sans Pro
# =============================================================================
st.markdown("""
<style>
/* Import Fonts */
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap');

/* Global Styles - Light Theme */
.stApp {
    background-color: #F7F5F3 !important;
    font-family: 'Source Sans Pro', Arial, sans-serif !important;
}

/* Main container styling */
.main .block-container {
    max-width: 1100px !important;
    padding: 2rem 1rem !important;
    background-color: #F7F5F3 !important;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #FBFAF9 !important;
    border-right: 1px solid #E0DEDB !important;
}
[data-testid="stSidebar"] .stMarkdown {
    font-family: 'Source Sans Pro', Arial, sans-serif !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    font-family: 'Source Sans Pro', Arial, sans-serif !important;
    font-weight: 600 !important;
    color: #37322F !important;
    font-size: 14px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: transparent !important;
    border-bottom: 1px solid #E0DEDB !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Source Sans Pro', Arial, sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #605A57 !important;
    background-color: transparent !important;
    border: none !important;
    padding: 12px 16px !important;
}
.stTabs [aria-selected="true"] {
    color: #37322F !important;
    border-bottom: 2px solid #37322F !important;
    background-color: transparent !important;
}

/* Headers */
h1 {
    font-family: 'Source Sans Pro', Arial, sans-serif !important;
    font-size: 32px !important;
    font-weight: 600 !important;
    color: #37322F !important;
}
h2, h3 {
    font-family: 'Source Sans Pro', Arial, sans-serif !important;
    font-weight: 600 !important;
    color: #37322F !important;
}

/* Body text */
p, span { color: #37322F; }
.muted { color: #605A57 !important; }

/* Streamlit metric styling */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E0DEDB;
    border-radius: 8px;
    padding: 12px;
}
[data-testid="stMetricLabel"] { color: #605A57 !important; }
[data-testid="stMetricValue"] { color: #37322F !important; }
[data-testid="stMetricDelta"] { color: #37322F !important; }

/* Caption styling */
[data-testid="stCaptionContainer"] { color: #605A57 !important; }
.stCaption, small { color: #605A57 !important; }

/* Progress bar styling */
[data-testid="stProgress"] > div > div { background-color: #E0DEDB !important; }

/* Expander text */
[data-testid="stExpander"] { color: #37322F !important; }
[data-testid="stExpander"] summary { color: #37322F !important; }

/* Toggle styling - more visible */
[data-testid="stToggle"] label { color: #37322F !important; }
[data-testid="stToggle"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E0DEDB !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
}
[data-testid="stToggle"] > div {
    background-color: #FFFFFF !important;
}

/* Button styling - light background */
.stButton > button {
    background-color: #FFFFFF !important;
    color: #37322F !important;
    border: 1px solid #E0DEDB !important;
    border-radius: 8px !important;
    font-family: 'Source Sans Pro', Arial, sans-serif !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    transition: all 200ms ease !important;
}
.stButton > button:hover {
    background-color: #F7F5F3 !important;
    border-color: #37322F !important;
}
.stButton > button:active {
    background-color: #E0DEDB !important;
}

/* Sidebar button styling */
[data-testid="stSidebar"] .stButton > button {
    background-color: #FFFFFF !important;
    color: #37322F !important;
    border: 1px solid #E0DEDB !important;
    width: 100% !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #F7F5F3 !important;
    border-color: #37322F !important;
}

/* Write/Text styling */
[data-testid="stText"] { color: #37322F !important; }

/* Markdown text */
[data-testid="stMarkdownContainer"] { color: #37322F !important; }
[data-testid="stMarkdownContainer"] p { color: #37322F !important; }
[data-testid="stMarkdownContainer"] li { color: #37322F !important; }

/* Card base style */
.metric-card {
    background: #FFFFFF;
    border: 1px solid #E0DEDB;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0px 2px 4px rgba(55, 50, 47, 0.08);
    transition: all 300ms ease-in-out;
    text-align: center;
}
.metric-card:hover {
    box-shadow: 0px 4px 12px rgba(55, 50, 47, 0.12);
    transform: translateY(-1px);
}

/* Card label */
.card-label {
    font-family: 'Source Sans Pro', Arial, sans-serif;
    font-size: 12px;
    font-weight: 500;
    color: #605A57;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 8px;
}

/* Big numbers */
.big-number {
    font-family: 'Source Sans Pro', Arial, sans-serif;
    font-size: 36px;
    font-weight: 400;
    color: #37322F;
}

/* Status colors */
.status-success { color: #10B981 !important; }
.status-warning { color: #F59E0B !important; }
.status-danger { color: #F43F5E !important; }
.status-info { color: #0EA5E9 !important; }

/* Status backgrounds */
.bg-success { background-color: rgba(16, 185, 129, 0.1) !important; }
.bg-warning { background-color: rgba(245, 158, 11, 0.1) !important; }
.bg-danger { background-color: #FFE4E6 !important; }
.bg-info { background-color: rgba(14, 165, 233, 0.1) !important; }

/* Badge/Pill style */
.badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 90px;
    font-family: 'Source Sans Pro', Arial, sans-serif;
    font-size: 13px;
    font-weight: 500;
    box-shadow: 0 0 0 4px rgba(55, 50, 47, 0.05);
}

/* Section spacing */
.section-gap { margin-top: 48px !important; }
.row-gap { margin-top: 24px !important; }

/* Expander styling - white box with thin border */
.streamlit-expanderHeader {
    font-family: 'Source Sans Pro', Arial, sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #37322F !important;
    background-color: #FFFFFF !important;
    border: 1px solid #E0DEDB !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E0DEDB !important;
    border-radius: 8px !important;
    padding: 0 !important;
}
[data-testid="stExpander"] details {
    background-color: #FFFFFF !important;
    border: 1px solid #E0DEDB !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary {
    background-color: #FFFFFF !important;
    padding: 12px 16px !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background-color: #FFFFFF !important;
    padding: 16px !important;
    border-top: 1px solid #E0DEDB !important;
}

/* DataFrame styling */
.stDataFrame {
    border: 1px solid #E0DEDB !important;
    border-radius: 8px !important;
}

/* Info/Warning boxes */
.stAlert {
    background-color: #FBFAF9 !important;
    border: 1px solid #E0DEDB !important;
    border-radius: 8px !important;
    color: #37322F !important;
}

/* Sidebar selectbox and input styling */
[data-testid="stSidebar"] [data-baseweb="select"] { background-color: #FFFFFF !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    border-color: #E0DEDB !important;
    color: #37322F !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] svg { color: #605A57 !important; }
[data-testid="stSidebar"] [data-baseweb="input"] {
    background-color: #FFFFFF !important;
    border-color: #E0DEDB !important;
}
[data-testid="stSidebar"] input {
    color: #37322F !important;
    background-color: #FFFFFF !important;
}
[data-testid="stSidebar"] label { color: #37322F !important; }
[data-testid="stSidebar"] .stCheckbox label span { color: #37322F !important; }

/* Dropdown menu styling */
[data-baseweb="popover"] { background-color: #FFFFFF !important; }
[data-baseweb="popover"] li { color: #37322F !important; }
[data-baseweb="popover"] li:hover { background-color: #F7F5F3 !important; }

/* Fix selectbox text color */
[data-baseweb="select"] span { color: #37322F !important; }
[data-baseweb="select"] div[data-testid="stMarkdownContainer"] p { color: #37322F !important; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# DATA LOADING FUNCTIONS (cached)
# =============================================================================
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")


@st.cache_data(ttl=86400)
def load_sp500_tickers():
    """Fetch S&P 500 tickers from Wikipedia."""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        response = requests.get(url, headers=HEADERS)
        tables = pd.read_html(StringIO(response.text))
        df = tables[0][["Symbol", "Security", "GICS Sector", "GICS Sub-Industry"]].copy()
        df.columns = ["ticker", "name", "sector", "industry"]
        df["ticker"] = df["ticker"].str.replace(".", "-", regex=False)
        df["is_sp500"] = True
        return df
    except Exception:
        return pd.DataFrame(columns=["ticker", "name", "sector", "industry", "is_sp500"])


@st.cache_data(ttl=86400)
def load_nasdaq100_tickers():
    """Fetch NASDAQ-100 tickers from Wikipedia."""
    try:
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        response = requests.get(url, headers=HEADERS)
        tables = pd.read_html(StringIO(response.text))

        for table in tables:
            str_cols = [str(c).lower() for c in table.columns]
            if any("ticker" in c or "symbol" in c for c in str_cols):
                ticker_col = None
                name_col = None
                for col in table.columns:
                    col_lower = str(col).lower()
                    if "ticker" in col_lower or "symbol" in col_lower:
                        ticker_col = col
                    if "company" in col_lower or "security" in col_lower:
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
    except Exception:
        return pd.DataFrame(columns=["ticker", "name", "sector", "industry", "is_sp500"])


@st.cache_data(ttl=86400)
def load_all_us_stocks():
    """Load combined list of S&P 500 and NASDAQ-100 stocks."""
    sp500 = load_sp500_tickers()
    nasdaq = load_nasdaq100_tickers()
    combined = pd.concat([sp500, nasdaq], ignore_index=True)
    combined = combined.drop_duplicates(subset=["ticker"], keep="first")
    return combined.sort_values("ticker").reset_index(drop=True)


@st.cache_data(ttl=3600)
def load_history(ticker, period="max", interval="1d"):
    """Load historical price data."""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, interval=interval, auto_adjust=False)
        if data.empty:
            st.warning(f"No data returned for {ticker}")
            return data
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        for col in required_cols:
            if col not in data.columns:
                st.error(f"Missing column {col} in data for {ticker}")
                return pd.DataFrame()
        if data["Close"].min() <= 0:
            st.warning(f"Warning: Found zero or negative Close prices for {ticker}")
        data = data.rename_axis("Date").reset_index()
        return data
    except Exception as e:
        st.error(f"Error loading data for {ticker}: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_fundamentals(ticker):
    """Load fundamental data from yfinance."""
    info = yf.Ticker(ticker).get_info()
    return info or {}


@st.cache_data(ttl=3600)
def load_industry_market_caps(tickers):
    """Fetch market caps for a list of tickers."""
    result = {}
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).get_info()
            market_cap = info.get("marketCap")
            if market_cap and market_cap > 0:
                result[ticker] = market_cap
        except Exception:
            continue
    return result


@st.cache_data(ttl=1800)
def load_finnhub_news(ticker):
    """Fetch company news from Finnhub API."""
    try:
        today = dt.date.today()
        from_date = (today - dt.timedelta(days=30)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")
        url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={from_date}&to={to_date}&token={FINNHUB_API_KEY}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []


@st.cache_data(ttl=3600)
def load_financial_statements(ticker):
    """Load historical financial statements for charts."""
    try:
        stock = yf.Ticker(ticker)
        income_stmt = stock.income_stmt
        if income_stmt is not None and not income_stmt.empty:
            income_stmt = income_stmt.T.sort_index()
        balance_sheet = stock.balance_sheet
        if balance_sheet is not None and not balance_sheet.empty:
            balance_sheet = balance_sheet.T.sort_index()
        cashflow = stock.cashflow
        if cashflow is not None and not cashflow.empty:
            cashflow = cashflow.T.sort_index()
        quarterly_income = stock.quarterly_income_stmt
        if quarterly_income is not None and not quarterly_income.empty:
            quarterly_income = quarterly_income.T.sort_index()
        quarterly_balance = stock.quarterly_balance_sheet
        if quarterly_balance is not None and not quarterly_balance.empty:
            quarterly_balance = quarterly_balance.T.sort_index()
        quarterly_cashflow = stock.quarterly_cashflow
        if quarterly_cashflow is not None and not quarterly_cashflow.empty:
            quarterly_cashflow = quarterly_cashflow.T.sort_index()
        return {
            "income_stmt": income_stmt,
            "balance_sheet": balance_sheet,
            "cashflow": cashflow,
            "quarterly_income": quarterly_income,
            "quarterly_balance": quarterly_balance,
            "quarterly_cashflow": quarterly_cashflow,
        }
    except Exception:
        return {
            "income_stmt": None, "balance_sheet": None, "cashflow": None,
            "quarterly_income": None, "quarterly_balance": None, "quarterly_cashflow": None,
        }


@st.cache_data(ttl=3600)
def load_sector_peers_metrics(tickers: tuple):
    """Load metrics for sector peers comparison."""
    rows = []
    for symbol in list(tickers):
        info = load_fundamentals(symbol)
        rows.append({
            "ticker": symbol,
            "pe": info.get("trailingPE"),
            "peg": info.get("pegRatio"),
            "roe": info.get("returnOnEquity"),
            "net_margin": info.get("profitMargins"),
            "rev_growth": info.get("revenueGrowth"),
            "de": info.get("debtToEquity"),
            "beta": info.get("beta"),
            "priceToBook": info.get("priceToBook"),
            "marketCap": info.get("marketCap"),
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def load_market_data():
    """Load S&P 500 and VIX data for market regime detection."""
    sp500 = yf.Ticker("^GSPC").history(period="2y", interval="1d", auto_adjust=False)
    vix = yf.Ticker("^VIX").history(period="2y", interval="1d", auto_adjust=False)
    return sp500, vix


def compute_indicators(df):
    """Compute technical indicators for price data."""
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

    # EMA Cross Signal: +1 golden cross, -1 death cross, 0 otherwise
    ema_cross = pd.Series(0, index=df.index)
    if len(df) > 1:
        ema20 = df["EMA20"].values
        ema50 = df["EMA50"].values
        for i in range(1, len(df)):
            if pd.notna(ema20[i]) and pd.notna(ema50[i]) and pd.notna(ema20[i-1]) and pd.notna(ema50[i-1]):
                if ema20[i-1] <= ema50[i-1] and ema20[i] > ema50[i]:
                    ema_cross.iloc[i] = 1  # Golden cross
                elif ema20[i-1] >= ema50[i-1] and ema20[i] < ema50[i]:
                    ema_cross.iloc[i] = -1  # Death cross
    df["EMA_Cross_Signal"] = ema_cross

    # Volume indicators
    if "Volume" in df.columns:
        df["Volume_SMA20"] = df["Volume"].rolling(window=20).mean()
        df["Volume_SMA50"] = df["Volume"].rolling(window=50).mean()
        df["Rel_Volume"] = df["Volume"] / df["Volume_SMA20"]
        # Volume slope: linear regression slope of Volume_SMA20 over last 10 days
        vol_sma = df["Volume_SMA20"]
        slope = vol_sma.rolling(window=10).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 10 and x.notna().all() else 0,
            raw=False,
        )
        df["Volume_Slope"] = slope

        # ATV (Average Trading Volume) indicators (Paper 1)
        df["ATV_20"] = df["Volume"].rolling(window=20).mean()
        atv_sma = df["ATV_20"]
        atv_slope = atv_sma.rolling(window=10).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 10 and x.notna().all() else 0,
            raw=False,
        )
        df["ATV_Slope"] = atv_slope

    # Monthly return (22-trading-day price change)
    df["Monthly_Return"] = df["Close"].pct_change(periods=22)

    return df


# =============================================================================
# MAIN APPLICATION
# =============================================================================
st.title("US Stock Analytics Dashboard")

# Load stock list
with st.spinner("Loading US stocks..."):
    all_stocks_df = load_all_us_stocks()
    sp500_set = set(all_stocks_df[all_stocks_df["is_sp500"]]["ticker"].tolist())

# Sidebar
with st.sidebar:
    st.header("Filters")

    # Sector filter
    sectors = ["All Sectors"] + sorted(all_stocks_df["sector"].dropna().unique().tolist())
    selected_sector = st.selectbox("Sector", sectors, index=0)

    # Apply filters
    filtered_df = all_stocks_df.copy()
    if selected_sector != "All Sectors":
        filtered_df = filtered_df[filtered_df["sector"] == selected_sector]

    st.divider()
    st.header("Stock Selection")

    if filtered_df.empty:
        st.warning("No stocks match the current filters.")
        st.stop()

    ticker_options = filtered_df["ticker"].tolist()
    ticker_labels = [f"{row['ticker']} - {row['name']}" for _, row in filtered_df.iterrows()]

    # Default to AAPL if available, otherwise first stock
    default_idx = 0
    if "AAPL" in ticker_options:
        default_idx = ticker_options.index("AAPL")

    selected_idx = st.selectbox(
        "Choose a stock",
        range(len(ticker_options)),
        format_func=lambda i: ticker_labels[i],
        index=default_idx
    )
    selected = ticker_options[selected_idx]

    # Show S&P 500 status
    stock_row = filtered_df[filtered_df["ticker"] == selected].iloc[0]
    if stock_row["is_sp500"]:
        st.caption("S&P 500 Member")
    else:
        st.caption("Not in S&P 500")

    st.divider()
    st.header("Strategy")
    selected_strategy = st.radio(
        "Scoring Strategy",
        options=["Current", "Volume+RSI", "Optimized Weights", "Combined"],
        index=0,
        help="Current = Baseline (tech+fund). Volume+RSI = Paper 1 (EMA+ATV+RSI+RL). Optimized Weights = Paper 2 (5-factor scoring). Combined = Paper 1 timing + Paper 2 quality.",
        captions=["Baseline", "Paper 1: EMA+ATV+RL", "Paper 2: Factor Weights", "Papers 1+2"],
    )

    # Risk profile selector (for Paper 2 and Combined strategies)
    risk_profile = "moderate"
    if selected_strategy in ["Optimized Weights", "Combined"]:
        risk_profile = st.selectbox(
            "Risk Profile",
            options=["conservative", "moderate", "aggressive"],
            index=1,
            format_func=lambda x: x.title(),
            help="Conservative: heavy on beta + market cap. Moderate/Aggressive: P/B, ROE, momentum weighted."
        )

    # RL Agent controls (Paper 1)
    rl_model = None
    rl_prediction = None
    if selected_strategy in ["Volume+RSI"]:
        try:
            import rl_agent
            if rl_agent.is_available():
                st.divider()
                st.header("RL Agent")
                if st.button("Retrain RL Agent", help="Retrain PPO model on current stock data (~10-30s)"):
                    st.session_state["force_retrain_rl"] = True
                st.caption("PPO agent acts as meta-decision layer on rule-based signals.")
            else:
                st.divider()
                st.warning("⚠️ RL Agent unavailable — install `stable-baselines3` and `gymnasium` for full Paper 1 analysis.")
        except ImportError:
            st.divider()
            st.warning("⚠️ RL Agent unavailable — install `stable-baselines3` and `gymnasium` for full Paper 1 analysis.")

    st.divider()
    # Clear cache button
    if st.button("Refresh Data", help="Clear cached data and reload fresh data"):
        st.cache_data.clear()
        st.rerun()

# Load data for selected stock
with st.spinner("Loading data..."):
    price_data = load_history(selected)
    info = load_fundamentals(selected)
    financials = load_financial_statements(selected)

if price_data.empty:
    st.error("No price data available for this ticker. Try another selection.")
    st.stop()

price_data = compute_indicators(price_data)

last_row = price_data.iloc[-1]
prev_row = price_data.iloc[-2] if len(price_data) > 1 else last_row
change_pct = (last_row["Close"] - prev_row["Close"]) / prev_row["Close"] * 100

sector = info.get("sector", "Technology")
industry = info.get("industry", "N/A")

# Load market data for regime detection
with st.spinner("Analyzing market conditions..."):
    sp500_market, vix_market = load_market_data()
    market_regime, regime_color, regime_metrics = detect_market_regime(sp500_market, vix_market)

    # Calculate scores
    tech_score, tech_details = calculate_technical_score(price_data)
    fund_score, fund_details = calculate_fundamental_score(info)

    # Volume score (needed for Paper 1 and Combined)
    volume_score, volume_details = calculate_volume_score(price_data)

    # RSI value for RSI gate
    rsi_value = price_data["RSI"].iloc[-1] if "RSI" in price_data.columns else 50

    # Load peer metrics for Paper 2 strategies
    peer_metrics = None
    fund_stock_sector = all_stocks_df[all_stocks_df["ticker"] == selected]["sector"].values
    if len(fund_stock_sector) > 0:
        current_sector = fund_stock_sector[0]
        sector_peers = all_stocks_df[all_stocks_df["sector"] == current_sector]["ticker"].tolist()
        sector_peers = [t for t in sector_peers if t != selected][:15]
        if sector_peers:
            peer_metrics = load_sector_peers_metrics(tuple(sector_peers + [selected]))

    # Paper 2 fundamental score (with price_data for momentum factor)
    fund_score_p2, fund_details_p2 = calculate_fundamental_score_paper2(
        info, peer_metrics=peer_metrics, risk_profile=risk_profile, price_data=price_data
    )

    # Paper 1 signal details (always init, conditionally compute)
    paper1_details = None
    if selected_strategy in ["Volume+RSI", "Combined"] and len(price_data) >= 50:
        _, paper1_details = generate_paper1_signal(price_data)

    # RL Agent (Paper 1) - always init rl_prediction here to override sidebar init
    rl_prediction = None
    if selected_strategy == "Volume+RSI":
        try:
            import rl_agent
            if rl_agent.is_available():
                force_retrain = st.session_state.pop("force_retrain_rl", False)
                with st.spinner("Loading RL agent..." if not force_retrain else "Training RL agent..."):
                    model = rl_agent.get_ppo_agent(price_data, ticker=selected, force_retrain=force_retrain)
                    if model is not None:
                        rl_prediction = rl_agent.predict_action(model, price_data)
        except ImportError:
            pass

# =============================================================================
# TABS - Render using modular tab files
# =============================================================================
analysis_tab, overview_tab, technical_tab, fundamentals_tab, news_tab, backtest_tab = st.tabs(
    ["Analysis", "Overview", "Technical", "Fundamentals", "News & Sentiment", "Backtest"]
)

with analysis_tab:
    analysis.render(
        selected=selected,
        price_data=price_data,
        info=info,
        tech_score=tech_score,
        tech_details=tech_details,
        fund_score=fund_score,
        fund_details=fund_details,
        market_regime=market_regime,
        regime_metrics=regime_metrics,
        last_row=last_row,
        selected_strategy=selected_strategy,
        volume_score=volume_score,
        volume_details=volume_details,
        rsi_value=rsi_value,
        risk_profile=risk_profile,
        fund_score_p2=fund_score_p2,
        fund_details_p2=fund_details_p2,
        paper1_details=paper1_details,
        rl_prediction=rl_prediction,
    )

with overview_tab:
    overview.render(
        selected=selected,
        price_data=price_data,
        info=info,
        all_stocks_df=all_stocks_df,
        filtered_df=filtered_df,
        sector=sector,
        industry=industry,
        last_row=last_row,
        change_pct=change_pct,
        sp500_set=sp500_set,
        load_industry_market_caps=load_industry_market_caps,
        load_sector_peers_metrics=load_sector_peers_metrics,
    )

with technical_tab:
    technical.render(
        selected=selected,
        price_data=price_data,
        info=info,
        tech_score=tech_score,
        tech_details=tech_details,
        last_row=last_row,
        selected_strategy=selected_strategy,
        volume_score=volume_score,
        volume_details=volume_details,
    )

with fundamentals_tab:
    fundamentals.render(
        selected=selected,
        info=info,
        financials=financials,
        fund_score=fund_score,
        fund_details=fund_details,
        all_stocks_df=all_stocks_df,
        filtered_df=filtered_df,
        price_data=price_data,
        load_sector_peers_metrics=load_sector_peers_metrics,
        selected_strategy=selected_strategy,
        fund_score_p2=fund_score_p2,
        fund_details_p2=fund_details_p2,
        risk_profile=risk_profile,
    )

with news_tab:
    news_items = load_finnhub_news(selected)
    news.render(news_items=news_items)

with backtest_tab:
    backtest.render(
        selected=selected,
        price_data=price_data,
        info=info,
        market_regime=market_regime,
        peer_metrics=peer_metrics,
    )

