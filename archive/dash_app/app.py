# =============================================================================
# US Stock Analytics Dashboard - Dash Application
# =============================================================================
# Run: python app.py
# =============================================================================

import datetime as dt
import os
from io import StringIO

import numpy as np
import pandas as pd
import requests
import yfinance as yf
from dotenv import load_dotenv

import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
from flask_caching import Cache

from models import (
    calculate_technical_score,
    calculate_volume_score,
    detect_market_regime,
    generate_recommendation_paper1,
    generate_paper1_signal,
    classify_headline_sentiment,
)
from components import COLORS, FONTS

# Load environment variables
load_dotenv()
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")

# =============================================================================
# APP INIT
# =============================================================================
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
    ],
    title="US Stock Analytics Dashboard",
)
# Increase callback timeout (default 30s is too short for RL training)
app.config.update({"suppress_callback_exceptions": True})
server = app.server
server.config["TIMEOUT"] = 120

# Cache setup (filesystem-based, survives restarts)
cache = Cache(server, config={
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 3600,
})


# =============================================================================
# DATA LOADING (cached)
# =============================================================================

@cache.memoize(timeout=86400)
def load_sp500_tickers():
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


@cache.memoize(timeout=86400)
def load_nasdaq100_tickers():
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


@cache.memoize(timeout=86400)
def load_all_us_stocks():
    sp500 = load_sp500_tickers()
    nasdaq = load_nasdaq100_tickers()
    combined = pd.concat([sp500, nasdaq], ignore_index=True)
    combined = combined.drop_duplicates(subset=["ticker"], keep="first")
    return combined.sort_values("ticker").reset_index(drop=True)


@cache.memoize(timeout=3600)
def load_history(ticker, period="max", interval="1d"):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, interval=interval, auto_adjust=False)
        if data.empty:
            return pd.DataFrame()
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        for col in required_cols:
            if col not in data.columns:
                return pd.DataFrame()
        data = data.rename_axis("Date").reset_index()
        return data
    except Exception:
        return pd.DataFrame()


@cache.memoize(timeout=3600)
def load_fundamentals(ticker):
    info = yf.Ticker(ticker).get_info()
    return info or {}


@cache.memoize(timeout=3600)
def load_industry_market_caps(tickers_tuple):
    result = {}
    for ticker in tickers_tuple:
        try:
            info = yf.Ticker(ticker).get_info()
            market_cap = info.get("marketCap")
            if market_cap and market_cap > 0:
                result[ticker] = market_cap
        except Exception:
            continue
    return result


@cache.memoize(timeout=86400)
def load_company_logo(ticker):
    try:
        url = f"https://finnhub.io/api/v1/stock/profile2?symbol={ticker}&token={FINNHUB_API_KEY}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get("logo", "")
        return ""
    except Exception:
        return ""


@cache.memoize(timeout=1800)
def load_finnhub_news(ticker):
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


@cache.memoize(timeout=3600)
def load_financial_statements(ticker):
    try:
        stock = yf.Ticker(ticker)
        result = {}
        for key, attr in [
            ("income_stmt", "income_stmt"),
            ("balance_sheet", "balance_sheet"),
            ("cashflow", "cashflow"),
            ("quarterly_income", "quarterly_income_stmt"),
            ("quarterly_balance", "quarterly_balance_sheet"),
            ("quarterly_cashflow", "quarterly_cashflow"),
        ]:
            data = getattr(stock, attr, None)
            if data is not None and not data.empty:
                data = data.T.sort_index()
            result[key] = data
        return result
    except Exception:
        return {k: None for k in [
            "income_stmt", "balance_sheet", "cashflow",
            "quarterly_income", "quarterly_balance", "quarterly_cashflow",
        ]}


@cache.memoize(timeout=3600)
def load_sector_peers_metrics(tickers_tuple):
    rows = []
    for symbol in list(tickers_tuple):
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


@cache.memoize(timeout=3600)
def load_market_data():
    sp500 = yf.Ticker("^GSPC").history(period="2y", interval="1d", auto_adjust=False)
    vix = yf.Ticker("^VIX").history(period="2y", interval="1d", auto_adjust=False)
    return sp500, vix


# =============================================================================
# INDICATORS
# =============================================================================

def compute_indicators(df):
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

    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

    ema_cross = pd.Series(0, index=df.index)
    if len(df) > 1:
        ema20 = df["EMA20"].values
        ema50 = df["EMA50"].values
        for i in range(1, len(df)):
            if pd.notna(ema20[i]) and pd.notna(ema50[i]) and pd.notna(ema20[i - 1]) and pd.notna(ema50[i - 1]):
                if ema20[i - 1] <= ema50[i - 1] and ema20[i] > ema50[i]:
                    ema_cross.iloc[i] = 1
                elif ema20[i - 1] >= ema50[i - 1] and ema20[i] < ema50[i]:
                    ema_cross.iloc[i] = -1
    df["EMA_Cross_Signal"] = ema_cross

    if "Volume" in df.columns:
        df["Volume_SMA20"] = df["Volume"].rolling(window=20).mean()
        df["Volume_SMA50"] = df["Volume"].rolling(window=50).mean()
        df["Rel_Volume"] = df["Volume"] / df["Volume_SMA20"]
        vol_sma = df["Volume_SMA20"]
        slope = vol_sma.rolling(window=10).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 10 and x.notna().all() else 0,
            raw=False,
        )
        df["Volume_Slope"] = slope
        df["ATV_20"] = df["Volume"].rolling(window=20).mean()
        atv_sma = df["ATV_20"]
        atv_slope = atv_sma.rolling(window=10).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 10 and x.notna().all() else 0,
            raw=False,
        )
        df["ATV_Slope"] = atv_slope

    df["Monthly_Return"] = df["Close"].pct_change(periods=22)
    return df


# =============================================================================
# LAYOUT
# =============================================================================

# Load stock list at startup
all_stocks_df = load_all_us_stocks()
if all_stocks_df.empty or "ticker" not in all_stocks_df.columns:
    # Fallback: minimal stock list if Wikipedia fetch fails
    all_stocks_df = pd.DataFrame({
        "ticker": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"],
        "name": ["Apple", "Microsoft", "Alphabet", "Amazon", "Meta", "NVIDIA", "Tesla"],
        "sector": ["Technology"] * 7,
        "industry": ["Technology"] * 7,
        "is_sp500": [True] * 7,
    })
sp500_set = set(all_stocks_df[all_stocks_df["is_sp500"]]["ticker"].tolist())

# Pre-build dropdown options so they're available immediately (no callback needed on load)
_initial_stock_options = [
    {"label": f"{row['ticker']} - {row['name']}", "value": row["ticker"]}
    for _, row in all_stocks_df.iterrows()
]

# Build the sidebar
_sidebar_label = {
    "fontSize": "11px", "fontWeight": 600, "textTransform": "uppercase",
    "letterSpacing": "0.06em", "color": COLORS["muted"], "marginBottom": "10px",
}

sidebar = html.Div(
    [
        html.Div("Stock Selection", style=_sidebar_label),
        dcc.Dropdown(
            id="stock-dropdown",
            options=_initial_stock_options,
            value="AAPL",
            clearable=False,
            style={"marginBottom": "20px"},
        ),

        html.Div(style={"height": "1px", "background": COLORS["border"], "margin": "0 0 20px 0"}),

        html.Div("My Position", style=_sidebar_label),
        dbc.Checklist(
            id="owns-stock-toggle",
            options=[{"label": " I own this stock", "value": "owns"}],
            value=[],
            switch=True,
            style={"marginBottom": "10px"},
        ),
        html.Div([
            dbc.Input(
                id="cost-basis-input",
                type="number",
                min=0.01,
                step=0.01,
                value=100.0,
                placeholder="Avg cost per share ($)",
            ),
            html.Div("Average Price", style={
                "fontStyle": "italic", "fontSize": "11px",
                "color": COLORS["muted"], "marginTop": "5px",
            }),
        ],
            id="cost-basis-container",
            style={"display": "none"},
        ),

        html.Div(style={"height": "1px", "background": COLORS["border"], "margin": "20px 0"}),
        dbc.Button("Refresh Data", id="refresh-btn", color="light", className="w-100"),
    ],
    style={
        "backgroundColor": COLORS["sidebar"],
        "padding": "24px 20px",
        "height": "100vh",
        "overflowY": "auto",
        "borderRight": f"1px solid {COLORS['border']}",
        "minWidth": "240px",
        "maxWidth": "260px",
    },
)

# Tab definitions
TAB_NAMES = ["dashboard", "analysis", "technical", "fundamentals", "news"]
TAB_LABELS = ["Dashboard", "Analysis", "Technical", "Fundamentals", "Recent News"]

_tab_btn_base = {
    "fontFamily": FONTS["primary"], "fontSize": "13px", "fontWeight": 500,
    "padding": "10px 18px", "border": "none", "cursor": "pointer",
    "background": "transparent", "color": COLORS["muted"],
    "borderBottom": "2px solid transparent", "borderRadius": "0",
    "transition": "all 0.15s ease", "letterSpacing": "0.01em",
}
_tab_btn_active = {
    **_tab_btn_base,
    "color": COLORS["teal"], "fontWeight": 600,
    "borderBottom": f"2px solid {COLORS['teal']}",
}

# Build tab bar as buttons (switching handled by clientside callback — instant)
tab_bar = html.Div(
    [
        html.Button(
            lbl, id=f"tab-btn-{name}",
            n_clicks=0,
            style=_tab_btn_active if name == "dashboard" else _tab_btn_base,
        )
        for name, lbl in zip(TAB_NAMES, TAB_LABELS)
    ],
    style={
        "display": "flex", "gap": "2px", "borderBottom": f"1px solid {COLORS['border']}",
        "marginBottom": "20px",
    },
)

# All tab content divs (rendered together, visibility toggled client-side)
tab_panels = html.Div([
    html.Div(id=f"tab-panel-{name}",
             style={"display": "block" if name == "dashboard" else "none"})
    for name in TAB_NAMES
])

# Main content area
main_content = html.Div(
    [
        html.H1("US Stock Analytics Dashboard",
                 style={"fontFamily": FONTS["primary"], "fontSize": "24px", "fontWeight": 700,
                         "color": COLORS["heading"], "marginBottom": "20px",
                         "letterSpacing": "-0.03em"}),
        dcc.Store(id="active-tab-store", data="dashboard"),
        tab_bar,
        dcc.Loading(
            id="loading-data",
            type="circle",
            color=COLORS["teal"],
            children=[tab_panels],
        ),
    ],
    style={
        "backgroundColor": COLORS["background"],
        "padding": "28px 36px",
        "minHeight": "100vh",
        "flex": "1",
        "overflowY": "auto",
    },
)

# Root layout
app.layout = html.Div(
    [
        dcc.Store(id="cost-basis-store"),
        html.Div(
            [sidebar, main_content],
            style={"display": "flex", "fontFamily": FONTS["primary"]},
        ),
    ],
    style={"backgroundColor": COLORS["background"]},
)


# =============================================================================
# JSON SERIALIZATION HELPER
# =============================================================================

def _make_json_safe(obj):
    """Recursively convert numpy/pandas types to native Python for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_json_safe(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return _make_json_safe(obj.tolist())
    if isinstance(obj, pd.Timestamp):
        return str(obj)
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    return obj


# =============================================================================
# CALLBACKS - Sidebar
# =============================================================================





@callback(
    Output("cost-basis-container", "style"),
    Input("owns-stock-toggle", "value"),
)
def show_cost_basis(owns):
    if "owns" in owns:
        return {"display": "block", "marginTop": "8px"}
    return {"display": "none"}


@callback(
    Output("cost-basis-store", "data"),
    Input("owns-stock-toggle", "value"),
    Input("cost-basis-input", "value"),
    prevent_initial_call=True,
)
def store_cost_basis(owns, cost_value):
    if "owns" in owns and cost_value is not None:
        return cost_value
    return None


# =============================================================================
# CALLBACKS - Tab Switching (clientside — instant, no server round-trip)
# =============================================================================

# Clientside callback: toggle panel visibility + button styles
app.clientside_callback(
    """
    function() {
        const tabs = %s;
        const ctx = dash_clientside.callback_context;
        if (!ctx.triggered.length) return Array(tabs.length * 2).fill(dash_clientside.no_update);

        const clickedId = ctx.triggered[0].prop_id.split('.')[0];
        const activeTab = clickedId.replace('tab-btn-', '');

        const panelStyles = [];
        const btnStyles = [];
        const baseBtn = %s;
        const activeBtn = %s;

        for (const t of tabs) {
            panelStyles.push(t === activeTab ? {display: 'block'} : {display: 'none'});
            btnStyles.push(t === activeTab ? activeBtn : baseBtn);
        }
        return [...panelStyles, ...btnStyles];
    }
    """ % (
        str(TAB_NAMES),
        str({k: v for k, v in _tab_btn_base.items()}),
        str({k: v for k, v in _tab_btn_active.items()}),
    ),
    # Outputs: panel styles, then button styles
    [Output(f"tab-panel-{t}", "style") for t in TAB_NAMES] +
    [Output(f"tab-btn-{t}", "style") for t in TAB_NAMES],
    # Inputs: all tab button clicks
    [Input(f"tab-btn-{t}", "n_clicks") for t in TAB_NAMES],
)


# =============================================================================
# CALLBACKS - Data Loading (renders ALL tabs at once on stock change)
# =============================================================================

@callback(
    [Output(f"tab-panel-{t}", "children") for t in TAB_NAMES],
    Input("stock-dropdown", "value"),
    Input("refresh-btn", "n_clicks"),
    State("cost-basis-store", "data"),
    prevent_initial_call=False,
)
def load_and_render_all(ticker, _refresh_clicks, cost_basis):
    if not ticker:
        empty = html.Div("Select a stock to begin.",
                          style={"padding": "40px", "color": COLORS["text_secondary"]})
        return [empty] * len(TAB_NAMES)

    # Clear cache on refresh
    if dash.ctx.triggered_id == "refresh-btn":
        cache.clear()

    # --- Load all data (server-side, no JSON serialization) ---
    price_data = load_history(ticker)
    if price_data.empty:
        err = html.Div([html.H3("Error"), html.P(f"No price data for {ticker}")],
                        style={"padding": "40px", "color": COLORS["danger"]})
        return [err] * len(TAB_NAMES)

    price_data = compute_indicators(price_data)
    info = load_fundamentals(ticker)

    last_row = price_data.iloc[-1]
    prev_row = price_data.iloc[-2] if len(price_data) > 1 else last_row
    change_pct = float((last_row["Close"] - prev_row["Close"]) / prev_row["Close"] * 100)

    sp500_market, vix_market = load_market_data()
    market_regime, _, regime_metrics = detect_market_regime(sp500_market, vix_market)

    tech_score, tech_details = calculate_technical_score(price_data)
    volume_score, volume_details = calculate_volume_score(price_data)
    rsi_value = float(price_data["RSI"].iloc[-1]) if "RSI" in price_data.columns else 50.0

    paper1_details = None
    if len(price_data) >= 50:
        _, paper1_details = generate_paper1_signal(price_data)

    # RL prediction — trains on first load per stock, cached after that
    rl_prediction = None
    try:
        import rl_agent
        print(f"[RL] is_available: {rl_agent.is_available()}")
        if rl_agent.is_available():
            model = rl_agent.get_ppo_agent(price_data, ticker=ticker)
            print(f"[RL] model: {model}")
            if model is not None:
                rl_prediction = int(rl_agent.predict_action(model, price_data))
                print(f"[RL] prediction: {rl_prediction}")
    except Exception as e:
        print(f"[RL] ERROR: {e}")
    print(f"[RL] final rl_prediction: {rl_prediction}")

    recommendation_data = generate_recommendation_paper1(
        tech_score, volume_score, rsi_value,
        market_regime, ticker, info, time_horizon="long",
        price_data=price_data, rl_prediction=rl_prediction,
    )

    news_items = load_finnhub_news(ticker)
    logo_url = load_company_logo(ticker)

    # Use paper1_details from recommendation (includes rl_signal)
    enriched_paper1 = recommendation_data.get("paper1_details", paper1_details)

    # Build shared stock_data dict (stays server-side, never serialized)
    stock_data = {
        "ticker": ticker,
        "info": info,
        "change_pct": round(change_pct, 4),
        "market_regime": market_regime,
        "regime_metrics": regime_metrics,
        "tech_score": int(tech_score),
        "tech_details": tech_details,
        "volume_score": int(volume_score),
        "volume_details": volume_details,
        "rsi_value": round(rsi_value, 2),
        "paper1_details": enriched_paper1,
        "rl_prediction": rl_prediction,
        "recommendation": recommendation_data,
        "news_items": news_items[:20],
        "logo_url": logo_url,
        "is_sp500": ticker in sp500_set,
    }

    # --- Render all tabs ---
    from tabs.dashboard import render as render_dashboard
    from tabs.analysis import render as render_analysis
    from tabs.news import render as render_news
    from tabs.technical import render as render_technical
    from tabs.fundamentals import render as render_fundamentals

    return [
        render_dashboard(stock_data, price_data, cost_basis),
        render_analysis(stock_data, price_data, cost_basis),
        render_technical(stock_data, price_data),
        render_fundamentals(stock_data, price_data, all_stocks_df),
        render_news(stock_data),
    ]


# =============================================================================
# CALLBACKS - Dashboard Chart Period Switching
# =============================================================================

PERIOD_BUTTONS = ["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y"]

# Period config: (yfinance period, yfinance interval, tail days from daily data)
_PERIOD_CONFIG = {
    "1D": ("2d", "60m", None),
    "5D": ("5d", "60m", None),
    "1M": (None, None, 22),
    "6M": (None, None, 126),
    "YTD": (None, None, "ytd"),
    "1Y": (None, None, 252),
    "5Y": (None, None, 1260),
}


@callback(
    Output("dashboard-price-chart", "figure"),
    *[Output(f"period-btn-{p}", "style") for p in PERIOD_BUTTONS],
    *[Input(f"period-btn-{p}", "n_clicks") for p in PERIOD_BUTTONS],
    Input("stock-dropdown", "value"),
    prevent_initial_call=False,
)
def update_chart_period(*args):
    n_clicks_list = args[:len(PERIOD_BUTTONS)]
    ticker = args[len(PERIOD_BUTTONS)]

    if not ticker:
        empty_fig = go.Figure()
        empty_fig.update_layout(height=220, margin=dict(l=5, r=10, t=5, b=25))
        base_style = {"flex": 1, "textAlign": "center", "padding": "8px 4px",
                      "borderRadius": "10px", "background": "#F8FAFB",
                      "border": "none", "cursor": "pointer"}
        return [empty_fig] + [base_style] * len(PERIOD_BUTTONS)

    # Determine which period was clicked
    triggered = dash.ctx.triggered_id
    if triggered and triggered.startswith("period-btn-"):
        active_period = triggered.replace("period-btn-", "")
    else:
        active_period = "6M"  # default

    # Fetch data based on period
    yf_period, yf_interval, tail_days = _PERIOD_CONFIG[active_period]

    from tabs.dashboard import build_chart

    if yf_period is not None:
        # Intraday data
        try:
            stock = yf.Ticker(ticker)
            intraday = stock.history(period=yf_period, interval=yf_interval, auto_adjust=False)
            if intraday.empty:
                raise ValueError("No intraday data")
            intraday = intraday.rename_axis("Date").reset_index()
            fig = build_chart(intraday)
        except Exception:
            # Fallback to daily
            daily = load_history(ticker)
            if not daily.empty:
                fig = build_chart(daily.tail(5))
            else:
                fig = go.Figure()
                fig.update_layout(height=220)
    else:
        # Daily data
        daily = load_history(ticker)
        if not daily.empty:
            if tail_days == "ytd":
                if "Date" in daily.columns and hasattr(daily["Date"].iloc[-1], "year"):
                    current_year = daily["Date"].iloc[-1].year
                    chart_df = daily[daily["Date"].dt.year == current_year]
                else:
                    chart_df = daily.tail(252)
            else:
                chart_df = daily.tail(tail_days)
            fig = build_chart(chart_df)
        else:
            fig = go.Figure()
            fig.update_layout(height=220)

    # Build button styles
    btn_styles = []
    for p in PERIOD_BUTTONS:
        is_active = (p == active_period)
        btn_styles.append({
            "flex": 1, "textAlign": "center", "padding": "8px 4px",
            "borderRadius": "10px", "cursor": "pointer",
            "background": "#E0F4F5" if is_active else "#F8FAFB",
            "border": f"1.5px solid {COLORS['teal']}" if is_active else "1.5px solid transparent",
        })

    return [fig] + btn_styles


# =============================================================================
# RUN
# =============================================================================
if __name__ == "__main__":
    app.run(debug=True, port=8050)
