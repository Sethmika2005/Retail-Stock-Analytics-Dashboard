import datetime as dt
from io import StringIO

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st
import yfinance as yf

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
p, span {
    color: #37322F;
}

/* Muted text */
.muted {
    color: #605A57 !important;
}

/* Streamlit metric styling */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E0DEDB;
    border-radius: 8px;
    padding: 12px;
}
[data-testid="stMetricLabel"] {
    color: #605A57 !important;
}
[data-testid="stMetricValue"] {
    color: #37322F !important;
}
[data-testid="stMetricDelta"] {
    color: #37322F !important;
}

/* Caption styling */
[data-testid="stCaptionContainer"] {
    color: #605A57 !important;
}
.stCaption, small {
    color: #605A57 !important;
}

/* Progress bar styling */
[data-testid="stProgress"] > div > div {
    background-color: #E0DEDB !important;
}

/* Expander text */
[data-testid="stExpander"] {
    color: #37322F !important;
}
[data-testid="stExpander"] summary {
    color: #37322F !important;
}

/* Toggle styling */
[data-testid="stToggle"] label {
    color: #37322F !important;
}

/* Write/Text styling */
[data-testid="stText"] {
    color: #37322F !important;
}

/* Markdown text */
[data-testid="stMarkdownContainer"] {
    color: #37322F !important;
}
[data-testid="stMarkdownContainer"] p {
    color: #37322F !important;
}
[data-testid="stMarkdownContainer"] li {
    color: #37322F !important;
}

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

/* Big numbers - Source Sans Pro */
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
.section-gap {
    margin-top: 48px !important;
}
.row-gap {
    margin-top: 24px !important;
}

/* Expander styling */
.streamlit-expanderHeader {
    font-family: 'Source Sans Pro', Arial, sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #37322F !important;
    background-color: #FBFAF9 !important;
    border: 1px solid #E0DEDB !important;
    border-radius: 8px !important;
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

/* Plotly chart background */
.js-plotly-plot .plotly .bg {
    fill: #FBFAF9 !important;
}

/* Sidebar selectbox and input styling */
[data-testid="stSidebar"] [data-baseweb="select"] {
    background-color: #FFFFFF !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    border-color: #E0DEDB !important;
    color: #37322F !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] svg {
    color: #605A57 !important;
}
[data-testid="stSidebar"] [data-baseweb="input"] {
    background-color: #FFFFFF !important;
    border-color: #E0DEDB !important;
}
[data-testid="stSidebar"] input {
    color: #37322F !important;
    background-color: #FFFFFF !important;
}
[data-testid="stSidebar"] label {
    color: #37322F !important;
}
[data-testid="stSidebar"] .stCheckbox label span {
    color: #37322F !important;
}

/* Dropdown menu styling */
[data-baseweb="popover"] {
    background-color: #FFFFFF !important;
}
[data-baseweb="popover"] li {
    color: #37322F !important;
}
[data-baseweb="popover"] li:hover {
    background-color: #F7F5F3 !important;
}

/* Fix selectbox text color */
[data-baseweb="select"] span {
    color: #37322F !important;
}
[data-baseweb="select"] div[data-testid="stMarkdownContainer"] p {
    color: #37322F !important;
}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# HELPER FUNCTIONS FOR CARD STYLING
# =============================================================================
def get_status_color(status_type):
    """Get the appropriate color for a status type."""
    colors = {
        "success": "#10B981",  # Emerald - Bull/BUY/Low risk
        "warning": "#F59E0B",  # Amber - Sideways/HOLD/Medium risk
        "danger": "#F43F5E",   # Rose - Bear/SELL/High risk
        "info": "#0EA5E9",     # Sky - Info accents
        "neutral": "#37322F",  # Primary text
        "muted": "#605A57",    # Secondary text
    }
    return colors.get(status_type, colors["neutral"])


def get_status_bg(status_type):
    """Get the appropriate background color for a status type."""
    bgs = {
        "success": "rgba(16, 185, 129, 0.1)",
        "warning": "rgba(245, 158, 11, 0.1)",
        "danger": "#FFE4E6",
        "info": "rgba(14, 165, 233, 0.1)",
        "neutral": "#FFFFFF",
    }
    return bgs.get(status_type, bgs["neutral"])


def render_metric_card(label, value, tooltip="", status="neutral", size="normal"):
    """Render a styled metric card with the new design system."""
    color = get_status_color(status)
    bg = get_status_bg(status) if status != "neutral" else "#FFFFFF"

    # Font sizes based on size parameter
    if size == "large":
        value_style = "font-family: 'Source Sans Pro', Arial, sans-serif; font-size: 42px; font-weight: 400;"
    elif size == "medium":
        value_style = "font-family: 'Source Sans Pro', Arial, sans-serif; font-size: 32px; font-weight: 400;"
    else:
        value_style = "font-family: 'Source Sans Pro', Arial, sans-serif; font-size: 24px; font-weight: 400;"

    return f"""
    <div style='
        text-align: center;
        padding: 20px;
        background: {bg};
        border: 1px solid #E0DEDB;
        border-radius: 10px;
        box-shadow: 0px 2px 4px rgba(55, 50, 47, 0.08);
        cursor: help;
        transition: all 300ms ease-in-out;
    ' title='{tooltip}'>
        <div style='
            font-family: Source Sans Pro, Arial, sans-serif;
            font-size: 12px;
            font-weight: 500;
            color: #605A57;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        '>{label}</div>
        <div style='{value_style} color: {color};'>{value}</div>
    </div>
    """


def render_badge_card(label, value, icon="", tooltip="", status="neutral"):
    """Render a large badge-style card (like market regime)."""
    color = get_status_color(status)
    bg = get_status_bg(status) if status != "neutral" else "#FFFFFF"

    return f"""
    <div style='
        text-align: center;
        padding: 24px;
        background: {bg};
        border: 1px solid #E0DEDB;
        border-radius: 12px;
        box-shadow: 0px 2px 4px rgba(55, 50, 47, 0.08);
        cursor: help;
    ' title='{tooltip}'>
        <div style='font-size: 48px; margin-bottom: 8px;'>{icon}</div>
        <div style='
            font-family: Source Sans Pro, Arial, sans-serif;
            font-size: 12px;
            font-weight: 500;
            color: #605A57;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        '>{label}</div>
        <div style='
            font-family: "Source Sans Pro", Arial, sans-serif;
            font-size: 28px;
            font-weight: 400;
            color: {color};
        '>{value}</div>
    </div>
    """


def render_compact_card(label, value, tooltip="", status="neutral"):
    """Render a compact metric card for dense layouts."""
    color = get_status_color(status)

    return f"""
    <div style='
        text-align: center;
        padding: 16px;
        background: #FFFFFF;
        border: 1px solid #E0DEDB;
        border-radius: 8px;
        box-shadow: 0px 2px 4px rgba(55, 50, 47, 0.08);
        margin-bottom: 8px;
        cursor: help;
    ' title='{tooltip}'>
        <div style='
            font-family: Source Sans Pro, Arial, sans-serif;
            font-size: 11px;
            font-weight: 500;
            color: #605A57;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 6px;
        '>{label}</div>
        <div style='
            font-family: "Source Sans Pro", Arial, sans-serif;
            font-size: 22px;
            font-weight: 400;
            color: {color};
        '>{value}</div>
    </div>
    """


HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Chart styling constants
CHART_FONT_COLOR = "#4A4A4A"  # Dark grey for chart text
CHART_AXIS_COLOR = "#4A4A4A"  # Dark grey for axis labels
CHART_GRID_COLOR = "rgba(74, 74, 74, 0.15)"  # Light grey for gridlines


def get_chart_layout_defaults():
    """Return common chart layout settings with dark grey fonts."""
    return dict(
        font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif"),
        title_font=dict(color=CHART_FONT_COLOR, size=14),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            tickfont=dict(color=CHART_AXIS_COLOR),
            title=dict(font=dict(color=CHART_AXIS_COLOR)),
            gridcolor=CHART_GRID_COLOR,
            linecolor=CHART_GRID_COLOR,
        ),
        yaxis=dict(
            tickfont=dict(color=CHART_AXIS_COLOR),
            title=dict(font=dict(color=CHART_AXIS_COLOR)),
            gridcolor=CHART_GRID_COLOR,
            linecolor=CHART_GRID_COLOR,
        ),
        legend=dict(font=dict(color=CHART_FONT_COLOR)),
    )


@st.cache_data(ttl=3600)
def load_market_regime():
    """Get current market regime based on S&P 500 and VIX."""
    try:
        # Get S&P 500 data
        spy = yf.Ticker("SPY")
        spy_hist = spy.history(period="6mo")

        # Get VIX data
        vix = yf.Ticker("^VIX")
        vix_hist = vix.history(period="3mo")

        if spy_hist.empty or vix_hist.empty:
            return {"regime": "Unknown", "spy_return": 0, "vix_level": 0, "spy_trend": "Unknown"}

        # Calculate S&P 500 metrics
        spy_current = spy_hist["Close"].iloc[-1]
        spy_sma50 = spy_hist["Close"].tail(50).mean()
        spy_sma200 = spy_hist["Close"].mean()  # ~6 months
        spy_1m_return = (spy_hist["Close"].iloc[-1] / spy_hist["Close"].iloc[-22] - 1) * 100 if len(spy_hist) > 22 else 0
        spy_3m_return = (spy_hist["Close"].iloc[-1] / spy_hist["Close"].iloc[-66] - 1) * 100 if len(spy_hist) > 66 else 0

        # VIX level
        vix_current = vix_hist["Close"].iloc[-1]
        vix_avg = vix_hist["Close"].mean()

        # Determine regime
        if spy_current > spy_sma50 > spy_sma200 and vix_current < 20:
            regime = "RISK-ON"
            regime_color = "#10B981"
            regime_desc = "Markets are in a strong uptrend with low volatility. Favorable for stocks."
        elif spy_current > spy_sma50 and vix_current < 25:
            regime = "BULLISH"
            regime_color = "#10B981"
            regime_desc = "Markets trending higher with moderate volatility. Generally favorable."
        elif spy_current < spy_sma50 < spy_sma200 and vix_current > 25:
            regime = "RISK-OFF"
            regime_color = "#F43F5E"
            regime_desc = "Markets are in a downtrend with elevated volatility. Caution advised."
        elif spy_current < spy_sma50 and vix_current > 20:
            regime = "BEARISH"
            regime_color = "#F43F5E"
            regime_desc = "Markets showing weakness. Consider defensive positioning."
        elif vix_current > 30:
            regime = "HIGH VOLATILITY"
            regime_color = "#F59E0B"
            regime_desc = "Extreme fear in markets. High uncertainty - wait for clarity."
        else:
            regime = "NEUTRAL"
            regime_color = "#F59E0B"
            regime_desc = "Mixed signals. Markets are range-bound."

        spy_trend = "Uptrend" if spy_current > spy_sma50 else "Downtrend"

        return {
            "regime": regime,
            "regime_color": regime_color,
            "regime_desc": regime_desc,
            "spy_current": spy_current,
            "spy_sma50": spy_sma50,
            "spy_1m_return": spy_1m_return,
            "spy_3m_return": spy_3m_return,
            "spy_trend": spy_trend,
            "vix_current": vix_current,
            "vix_avg": vix_avg,
        }
    except Exception:
        return {"regime": "Unknown", "regime_color": "#9CA3AF", "regime_desc": "Unable to fetch market data.", "spy_current": 0, "vix_current": 0, "spy_trend": "Unknown"}


def generate_recommendation(tech_score, fund_score, risk_score, market_regime, time_horizon="long"):
    """Generate BUY/HOLD/SELL recommendation with confidence and drivers."""

    # Adjust weights based on time horizon
    if time_horizon == "short":
        tech_weight = 0.50
        fund_weight = 0.15
        risk_weight = 0.25
        regime_weight = 0.10
    else:  # long-term
        tech_weight = 0.25
        fund_weight = 0.40
        risk_weight = 0.20
        regime_weight = 0.15

    # Regime adjustment
    regime_score = 70 if market_regime in ["RISK-ON", "BULLISH"] else 50 if market_regime == "NEUTRAL" else 30

    # Combined score
    combined_score = (
        tech_score * tech_weight +
        fund_score * fund_weight +
        (100 - risk_score) * risk_weight +  # Invert risk (lower risk = better)
        regime_score * regime_weight
    )

    # Determine recommendation
    if combined_score >= 70:
        recommendation = "BUY"
        rec_color = "#10B981"
        confidence = min(95, int(50 + (combined_score - 70) * 1.5))
    elif combined_score >= 50:
        recommendation = "HOLD"
        rec_color = "#F59E0B"
        confidence = min(85, int(40 + (combined_score - 50) * 1.5))
    else:
        recommendation = "SELL"
        rec_color = "#F43F5E"
        confidence = min(90, int(50 + (50 - combined_score) * 1.5))

    return {
        "recommendation": recommendation,
        "rec_color": rec_color,
        "confidence": confidence,
        "combined_score": combined_score,
    }


def generate_key_drivers(info, tech_score, fund_score, risk_score, price_data, market_regime):
    """Generate 3 key drivers in plain English."""
    drivers = []

    # Technical driver
    if tech_score >= 65:
        if "SMA50" in price_data.columns and "SMA200" in price_data.columns:
            if price_data["SMA50"].iloc[-1] > price_data["SMA200"].iloc[-1]:
                drivers.append("Price is above key moving averages with bullish momentum")
            else:
                drivers.append("Technical indicators show improving momentum")
        else:
            drivers.append("Technical setup is favorable with strong price action")
    elif tech_score >= 40:
        drivers.append("Technical picture is mixed - no clear trend")
    else:
        drivers.append("Technical weakness with price below key support levels")

    # Fundamental driver
    pe = info.get("trailingPE")
    roe = info.get("returnOnEquity")
    growth = info.get("revenueGrowth")

    if fund_score >= 65:
        if growth and growth > 0.15:
            drivers.append(f"Strong fundamentals with {growth*100:.0f}% revenue growth")
        elif roe and roe > 0.15:
            drivers.append(f"Quality business with {roe*100:.0f}% return on equity")
        elif pe and pe < 20:
            drivers.append(f"Attractively valued at {pe:.1f}x earnings")
        else:
            drivers.append("Solid fundamentals support the investment thesis")
    elif fund_score >= 40:
        drivers.append("Fundamentals are acceptable but not compelling")
    else:
        if pe and pe > 30:
            drivers.append(f"Valuation stretched at {pe:.1f}x earnings")
        else:
            drivers.append("Fundamental concerns about profitability or growth")

    # Market/Risk driver
    if market_regime in ["RISK-ON", "BULLISH"]:
        drivers.append("Favorable market environment supports risk-taking")
    elif market_regime in ["RISK-OFF", "BEARISH"]:
        drivers.append("Challenging market backdrop adds headwinds")
    else:
        drivers.append("Market conditions are neutral - stock-specific factors matter more")

    return drivers[:3]


def generate_key_risk(info, risk_score, price_data):
    """Generate the single most important risk."""
    risks = []

    # Volatility risk
    if "ATR" in price_data.columns:
        atr_pct = (price_data["ATR"].iloc[-1] / price_data["Close"].iloc[-1]) * 100
        if atr_pct > 3:
            risks.append(f"High volatility ({atr_pct:.1f}% daily range) - position size accordingly")

    # Valuation risk
    pe = info.get("trailingPE")
    if pe and pe > 35:
        risks.append(f"Premium valuation ({pe:.0f}x P/E) leaves little margin for error")

    # Leverage risk
    de = info.get("debtToEquity")
    if de and de > 100:
        risks.append(f"High debt levels ({de:.0f} D/E) increase financial risk")

    # Drawdown risk
    if not price_data.empty:
        high = price_data["High"].max()
        current = price_data["Close"].iloc[-1]
        drawdown = (high - current) / high * 100
        if drawdown > 20:
            risks.append(f"Already {drawdown:.0f}% off highs - catching a falling knife risk")

    # Default risk
    if not risks:
        if risk_score > 60:
            risks.append("Elevated risk profile - use appropriate position sizing")
        else:
            risks.append("Standard market risk applies - diversify accordingly")

    return risks[0]


def generate_action_checklist(recommendation, info, price_data, atr_multiplier=2):
    """Generate actionable entry, sizing, and stop guidance."""
    current_price = price_data["Close"].iloc[-1] if not price_data.empty else 0
    atr = price_data["ATR"].iloc[-1] if "ATR" in price_data.columns else current_price * 0.02

    actions = []

    if recommendation == "BUY":
        # Entry idea
        if "SMA50" in price_data.columns:
            sma50 = price_data["SMA50"].iloc[-1]
            if current_price > sma50 * 1.02:
                actions.append(f"Entry: Consider buying on pullback to ${sma50:.2f} (50-day MA)")
            else:
                actions.append(f"Entry: Current price ${current_price:.2f} is near support - reasonable entry")
        else:
            actions.append(f"Entry: Current price ${current_price:.2f}")

        # Position sizing
        actions.append(f"Position: Risk 1-2% of portfolio per ATR-based stop")

        # Stop loss
        stop_price = current_price - (atr * atr_multiplier)
        actions.append(f"Stop: ${stop_price:.2f} ({atr_multiplier}x ATR = ${atr*atr_multiplier:.2f} below entry)")

    elif recommendation == "HOLD":
        actions.append("Action: Maintain existing position if owned")
        actions.append("New money: Wait for better entry or clearer signal")
        stop_price = current_price - (atr * atr_multiplier)
        actions.append(f"Trailing stop: ${stop_price:.2f} to protect gains")

    else:  # SELL
        actions.append("Action: Consider reducing or exiting position")
        actions.append("New money: Avoid until conditions improve")
        actions.append("Re-entry: Look for stabilization above 50-day MA")

    return actions


def generate_bull_bear_case(info, tech_score, fund_score, price_data, market_regime):
    """Generate bull and bear case arguments."""

    bull_case = []
    bear_case = []

    # Technical factors
    if tech_score >= 60:
        bull_case.append("Positive price momentum and trend")
    else:
        bear_case.append("Weak technical setup and momentum")

    if tech_score < 40:
        bear_case.append("Price below key moving averages")
    elif tech_score >= 70:
        bull_case.append("Strong technical breakout potential")

    # Fundamental factors
    pe = info.get("trailingPE")
    peg = info.get("pegRatio")
    roe = info.get("returnOnEquity")
    growth = info.get("revenueGrowth")
    margin = info.get("profitMargins")

    if pe and pe < 20:
        bull_case.append(f"Reasonable valuation at {pe:.1f}x earnings")
    elif pe and pe > 30:
        bear_case.append(f"Expensive valuation at {pe:.1f}x earnings")

    if peg and peg < 1.5:
        bull_case.append("Attractive price relative to growth")
    elif peg and peg > 2:
        bear_case.append("Overvalued relative to growth rate")

    if roe and roe > 0.15:
        bull_case.append(f"High quality business ({roe*100:.0f}% ROE)")
    elif roe and roe < 0.08:
        bear_case.append("Below-average returns on capital")

    if growth and growth > 0.10:
        bull_case.append(f"Strong revenue growth ({growth*100:.0f}% YoY)")
    elif growth and growth < 0:
        bear_case.append("Revenue declining year-over-year")

    if margin and margin > 0.15:
        bull_case.append("Healthy profit margins")
    elif margin and margin < 0.05:
        bear_case.append("Thin profit margins limit flexibility")

    # Market regime
    if market_regime in ["RISK-ON", "BULLISH"]:
        bull_case.append("Supportive market environment")
    elif market_regime in ["RISK-OFF", "BEARISH"]:
        bear_case.append("Challenging market headwinds")

    # Ensure we have at least some points
    if not bull_case:
        bull_case.append("Potential for mean reversion if oversold")
    if not bear_case:
        bear_case.append("Standard market and execution risks")

    return bull_case[:4], bear_case[:4]


def generate_view_changers(recommendation, info, price_data):
    """Generate what would change the current view."""
    changers = []

    current_price = price_data["Close"].iloc[-1] if not price_data.empty else 0
    sma50 = price_data["SMA50"].iloc[-1] if "SMA50" in price_data.columns else current_price
    sma200 = price_data["SMA200"].iloc[-1] if "SMA200" in price_data.columns else current_price

    if recommendation == "BUY":
        # What would turn bullish to bearish
        changers.append(f"Price breakdown below ${sma50:.2f} (50-day MA)")
        changers.append("Deterioration in revenue growth or margins")
        changers.append("Market regime shift to RISK-OFF")
        changers.append("Insider selling or earnings miss")
    elif recommendation == "SELL":
        # What would turn bearish to bullish
        changers.append(f"Price recovery above ${sma50:.2f} (50-day MA)")
        changers.append("Positive earnings surprise or guidance raise")
        changers.append("Market regime shift to RISK-ON")
        changers.append("Valuation becoming attractive on pullback")
    else:  # HOLD
        changers.append(f"Break above ${sma50*1.05:.2f} would turn bullish")
        changers.append(f"Break below ${sma50*0.95:.2f} would turn bearish")
        changers.append("Earnings catalyst could clarify direction")
        changers.append("Sector rotation or market regime change")

    return changers


@st.cache_data(ttl=86400)
def load_sp500_tickers():
    """Fetch S&P 500 tickers from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response = requests.get(url, headers=HEADERS)
    tables = pd.read_html(StringIO(response.text))
    df = tables[0][["Symbol", "Security", "GICS Sector", "GICS Sub-Industry"]].copy()
    df.columns = ["ticker", "name", "sector", "industry"]
    df["ticker"] = df["ticker"].str.replace(".", "-", regex=False)
    df["is_sp500"] = True
    return df


@st.cache_data(ttl=86400)
def load_nasdaq100_tickers():
    """Fetch NASDAQ-100 tickers from Wikipedia."""
    try:
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        response = requests.get(url, headers=HEADERS)
        tables = pd.read_html(StringIO(response.text))

        for table in tables:
            # Convert column names to strings for comparison
            str_cols = [str(c).lower() for c in table.columns]
            if any("ticker" in c or "symbol" in c for c in str_cols):
                # Find the ticker and company columns
                ticker_col = None
                name_col = None
                for col in table.columns:
                    col_lower = str(col).lower()
                    if "ticker" in col_lower or "symbol" in col_lower:
                        ticker_col = col
                    if "company" in col_lower or "security" in col_lower:
                        name_col = col

                if ticker_col is not None:
                    df = pd.DataFrame({
                        "ticker": table[ticker_col].astype(str),
                        "name": table[name_col].astype(str) if name_col else table[ticker_col].astype(str),
                        "sector": "Technology",
                        "industry": "N/A",
                    })
                    df["ticker"] = df["ticker"].str.replace(".", "-", regex=False)
                    df["is_sp500"] = False
                    return df
    except Exception:
        pass

    # Fallback: return empty DataFrame
    return pd.DataFrame(columns=["ticker", "name", "sector", "industry", "is_sp500"])


@st.cache_data(ttl=86400)
def load_nyse_additional():
    """Fetch additional stocks from Dow Jones and other sources."""
    try:
        url = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
        response = requests.get(url, headers=HEADERS)
        tables = pd.read_html(StringIO(response.text))

        stocks = []
        for table in tables:
            # Convert all column names to strings
            cols = [str(c).lower() for c in table.columns]
            if any("symbol" in c or "ticker" in c for c in cols):
                for _, row in table.iterrows():
                    ticker = None
                    name = None
                    for col in table.columns:
                        col_str = str(col).lower()
                        if "symbol" in col_str or "ticker" in col_str:
                            ticker = str(row[col]).replace(".", "-")
                        if "company" in col_str:
                            name = row[col]
                    if ticker and len(ticker) <= 5 and ticker.replace("-", "").isalpha():
                        stocks.append({
                            "ticker": ticker,
                            "name": name or ticker,
                            "sector": "Various",
                            "industry": "N/A",
                            "is_sp500": False,
                        })
                break

        return pd.DataFrame(stocks) if stocks else pd.DataFrame(
            columns=["ticker", "name", "sector", "industry", "is_sp500"]
        )
    except Exception:
        return pd.DataFrame(
            columns=["ticker", "name", "sector", "industry", "is_sp500"]
        )


@st.cache_data(ttl=86400)
def load_all_us_stocks():
    """Combine stocks from multiple sources - fully dynamic."""
    # Load from different sources (all fetched from Wikipedia)
    sp500 = load_sp500_tickers()
    nasdaq100 = load_nasdaq100_tickers()
    djia = load_nyse_additional()

    # Get set of S&P 500 tickers before combining
    sp500_set = set(sp500["ticker"].tolist())

    # Combine all dataframes
    combined = pd.concat([sp500, nasdaq100, djia], ignore_index=True)

    # Remove duplicates, keeping S&P 500 entries (they have more complete info)
    combined = combined.drop_duplicates(subset=["ticker"], keep="first")

    # Update is_sp500 flag based on S&P 500 list
    combined["is_sp500"] = combined["ticker"].isin(sp500_set)

    return combined.sort_values("ticker").reset_index(drop=True)

POSITIVE_WORDS = {
    "beat",
    "beats",
    "surge",
    "surges",
    "soar",
    "soars",
    "record",
    "growth",
    "profit",
    "upgrade",
    "bull",
    "bullish",
    "strong",
    "tops",
}
NEGATIVE_WORDS = {
    "miss",
    "misses",
    "drop",
    "drops",
    "plunge",
    "plunges",
    "cut",
    "cuts",
    "downgrade",
    "bear",
    "bearish",
    "weak",
    "lawsuit",
    "decline",
}


def classify_headline_sentiment(title):
    words = set(title.lower().split())
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    if pos > neg:
        return "Positive"
    if neg > pos:
        return "Negative"
    return "Neutral"


@st.cache_data(ttl=3600)
def load_history(ticker, period="max", interval="1d"):
    """Load historical price data. Default max for full history."""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, interval=interval, auto_adjust=False)
        if data.empty:
            st.warning(f"No data returned for {ticker}")
            return data
        # Ensure we have required columns
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        for col in required_cols:
            if col not in data.columns:
                st.error(f"Missing column {col} in data for {ticker}")
                return pd.DataFrame()
        # Verify Close prices are realistic (not zero or index-like values)
        if data["Close"].min() <= 0:
            st.warning(f"Warning: Found zero or negative Close prices for {ticker}")
        data = data.rename_axis("Date").reset_index()
        return data
    except Exception as e:
        st.error(f"Error loading data for {ticker}: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_fundamentals(ticker):
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


FINNHUB_API_KEY = "d5r1qkpr01qqqlh99vbgd5r1qkpr01qqqlh99vc0"


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

        # Get income statement (annual)
        income_stmt = stock.income_stmt
        if income_stmt is not None and not income_stmt.empty:
            income_stmt = income_stmt.T.sort_index()  # Transpose and sort by date

        # Get balance sheet (annual)
        balance_sheet = stock.balance_sheet
        if balance_sheet is not None and not balance_sheet.empty:
            balance_sheet = balance_sheet.T.sort_index()

        # Get cash flow (annual)
        cashflow = stock.cashflow
        if cashflow is not None and not cashflow.empty:
            cashflow = cashflow.T.sort_index()

        # Get quarterly data for more granular view
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
            "income_stmt": None,
            "balance_sheet": None,
            "cashflow": None,
            "quarterly_income": None,
            "quarterly_balance": None,
            "quarterly_cashflow": None,
        }


def format_large_number(value):
    """Format large numbers with B/M/K suffixes."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A"
    if abs(value) >= 1e12:
        return f"${value/1e12:.2f}T"
    if abs(value) >= 1e9:
        return f"${value/1e9:.2f}B"
    if abs(value) >= 1e6:
        return f"${value/1e6:.2f}M"
    if abs(value) >= 1e3:
        return f"${value/1e3:.2f}K"
    return f"${value:.2f}"


@st.cache_data(ttl=3600)
def load_sector_peers_metrics(tickers: tuple):
    rows = []
    for symbol in list(tickers):
        info = load_fundamentals(symbol)
        rows.append(
            {
                "ticker": symbol,
                "pe": info.get("trailingPE"),
                "peg": info.get("pegRatio"),
                "roe": info.get("returnOnEquity"),
                "net_margin": info.get("profitMargins"),
                "rev_growth": info.get("revenueGrowth"),
                "de": info.get("debtToEquity"),
            }
        )
    df = pd.DataFrame(rows)
    return df


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
    return df


def format_metric(value, suffix=""):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A"
    if isinstance(value, float):
        return f"{value:.2f}{suffix}"
    return f"{value}{suffix}"


def metric_color(value, good_high=True):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "gray"
    if good_high:
        return "green" if value >= 0 else "red"
    return "green" if value <= 0 else "red"


def classify_risk(df):
    returns = df["Close"].pct_change().dropna()
    if returns.empty:
        return "Unknown", "gray", []
    vol = returns.tail(60).std() * np.sqrt(252)
    rsi = df["RSI"].iloc[-1]
    factors = []
    if vol > 0.5:
        level = "High"
        color = "red"
        factors.append("Elevated 60d volatility")
    elif vol > 0.3:
        level = "Medium"
        color = "orange"
        factors.append("Moderate 60d volatility")
    else:
        level = "Low"
        color = "green"
        factors.append("Stable 60d volatility")

    if rsi > 70:
        factors.append("RSI above 70 (overbought)")
    elif rsi < 30:
        factors.append("RSI below 30 (oversold)")

    return level, color, factors


# =============================================================================
# MARKET REGIME & STOCK ANALYSIS FUNCTIONS
# =============================================================================

@st.cache_data(ttl=3600)
def load_market_data():
    """Load S&P 500 and VIX data for market regime detection."""
    sp500 = yf.Ticker("^GSPC").history(period="2y", interval="1d", auto_adjust=False)
    vix = yf.Ticker("^VIX").history(period="2y", interval="1d", auto_adjust=False)
    return sp500, vix


def detect_market_regime(sp500_df, vix_df):
    """
    Detect market regime: Bull, Bear, Sideways, or High-Volatility.
    High volatility overrides other regimes.
    """
    if sp500_df.empty or vix_df.empty:
        return "Unknown", "gray", {}

    # Calculate 200-day MA and its slope
    sp500_df = sp500_df.copy()
    sp500_df["SMA200"] = sp500_df["Close"].rolling(window=200).mean()
    sp500_df["SMA50"] = sp500_df["Close"].rolling(window=50).mean()

    current_price = sp500_df["Close"].iloc[-1]
    sma200 = sp500_df["SMA200"].iloc[-1]
    sma50 = sp500_df["SMA50"].iloc[-1]

    # Calculate 200-day MA slope (20-day change in SMA200)
    sma200_20d_ago = sp500_df["SMA200"].iloc[-20] if len(sp500_df) >= 20 else sma200
    sma200_slope = (sma200 - sma200_20d_ago) / sma200_20d_ago * 100 if sma200_20d_ago else 0

    # Current VIX level
    current_vix = vix_df["Close"].iloc[-1]
    vix_ma20 = vix_df["Close"].rolling(window=20).mean().iloc[-1]

    # Price relative to 200-day MA
    price_vs_sma200 = (current_price - sma200) / sma200 * 100 if sma200 else 0

    # 50-day vs 200-day MA (golden/death cross indicator)
    sma_crossover = (sma50 - sma200) / sma200 * 100 if sma200 else 0

    # Calculate S&P 500 returns for benchmarking
    sp500_1m_return = 0
    sp500_3m_return = 0
    if len(sp500_df) > 22:
        sp500_1m_return = (sp500_df["Close"].iloc[-1] / sp500_df["Close"].iloc[-22] - 1) * 100
    if len(sp500_df) > 66:
        sp500_3m_return = (sp500_df["Close"].iloc[-1] / sp500_df["Close"].iloc[-66] - 1) * 100

    metrics = {
        "sp500_price": current_price,
        "sma200": sma200,
        "sma50": sma50,
        "price_vs_sma200": price_vs_sma200,
        "sma200_slope": sma200_slope,
        "sma_crossover": sma_crossover,
        "vix": current_vix,
        "vix_ma20": vix_ma20,
        "sp500_1m_return": sp500_1m_return,
        "sp500_3m_return": sp500_3m_return,
    }

    # HIGH VOLATILITY overrides everything (VIX > 25 or significantly above its MA)
    if current_vix > 25 or current_vix > vix_ma20 * 1.3:
        return "High-Volatility", "red", metrics

    # BULL: Price above 200-day MA, positive slope, 50 > 200
    if price_vs_sma200 > 2 and sma200_slope > 0 and sma_crossover > 0:
        return "Bull", "green", metrics

    # BEAR: Price below 200-day MA, negative slope, 50 < 200
    if price_vs_sma200 < -2 and sma200_slope < 0 and sma_crossover < 0:
        return "Bear", "red", metrics

    # SIDEWAYS: Everything else
    return "Sideways", "orange", metrics


def calculate_technical_score(df):
    """
    Calculate technical score (0-100) based on trend, RSI, MACD.
    """
    if df.empty or len(df) < 200:
        return 50, {}

    scores = {}

    # 1. Trend Alignment (price vs SMAs) - 40 points max
    current_price = df["Close"].iloc[-1]
    sma50 = df["SMA50"].iloc[-1] if "SMA50" in df.columns else df["Close"].rolling(50).mean().iloc[-1]
    sma200 = df["SMA200"].iloc[-1] if "SMA200" in df.columns else df["Close"].rolling(200).mean().iloc[-1]

    trend_score = 0
    if pd.notna(sma50) and pd.notna(sma200):
        if current_price > sma50 > sma200:  # Strong uptrend
            trend_score = 40
        elif current_price > sma50 and current_price > sma200:  # Moderate uptrend
            trend_score = 30
        elif current_price > sma200:  # Weak uptrend
            trend_score = 20
        elif current_price < sma50 < sma200:  # Strong downtrend
            trend_score = 0
        elif current_price < sma50 and current_price < sma200:  # Moderate downtrend
            trend_score = 10
        else:
            trend_score = 15
    scores["trend"] = trend_score

    # 2. RSI Score - 30 points max
    rsi = df["RSI"].iloc[-1] if "RSI" in df.columns else 50
    if pd.notna(rsi):
        if 40 <= rsi <= 60:  # Neutral zone - good for entry
            rsi_score = 25
        elif 30 <= rsi < 40:  # Oversold but recovering
            rsi_score = 30
        elif 60 < rsi <= 70:  # Overbought but not extreme
            rsi_score = 20
        elif rsi < 30:  # Very oversold - potential reversal
            rsi_score = 25
        elif rsi > 70:  # Very overbought - caution
            rsi_score = 10
        else:
            rsi_score = 15
    else:
        rsi_score = 15
    scores["rsi"] = rsi_score

    # 3. MACD Score - 30 points max
    macd = df["MACD"].iloc[-1] if "MACD" in df.columns else 0
    macd_signal = df["MACD_SIGNAL"].iloc[-1] if "MACD_SIGNAL" in df.columns else 0
    macd_hist = df["MACD_HIST"].iloc[-1] if "MACD_HIST" in df.columns else 0

    macd_score = 15  # Default
    if pd.notna(macd) and pd.notna(macd_signal):
        if macd > macd_signal and macd_hist > 0:  # Bullish
            macd_score = 30 if macd > 0 else 25
        elif macd < macd_signal and macd_hist < 0:  # Bearish
            macd_score = 5 if macd < 0 else 10
        else:
            macd_score = 15
    scores["macd"] = macd_score

    total = trend_score + rsi_score + macd_score
    scores["total"] = total

    return total, scores


def calculate_fundamental_score(info):
    """
    Calculate fundamental score (0-100) based on profitability, growth, leverage, valuation.
    """
    scores = {}

    # 1. Profitability - 25 points max
    roe = info.get("returnOnEquity")
    profit_margin = info.get("profitMargins")

    prof_score = 12  # Default
    if roe is not None and profit_margin is not None:
        if roe > 0.20 and profit_margin > 0.15:
            prof_score = 25
        elif roe > 0.15 and profit_margin > 0.10:
            prof_score = 20
        elif roe > 0.10 and profit_margin > 0.05:
            prof_score = 15
        elif roe > 0 and profit_margin > 0:
            prof_score = 10
        else:
            prof_score = 5
    scores["profitability"] = prof_score

    # 2. Growth - 25 points max
    rev_growth = info.get("revenueGrowth")
    earnings_growth = info.get("earningsGrowth")

    growth_score = 12  # Default
    if rev_growth is not None:
        if rev_growth > 0.25:
            growth_score = 25
        elif rev_growth > 0.15:
            growth_score = 20
        elif rev_growth > 0.05:
            growth_score = 15
        elif rev_growth > 0:
            growth_score = 10
        else:
            growth_score = 5
    scores["growth"] = growth_score

    # 3. Leverage (lower is better) - 25 points max
    debt_equity = info.get("debtToEquity")

    leverage_score = 12  # Default
    if debt_equity is not None:
        if debt_equity < 30:
            leverage_score = 25
        elif debt_equity < 50:
            leverage_score = 20
        elif debt_equity < 100:
            leverage_score = 15
        elif debt_equity < 150:
            leverage_score = 10
        else:
            leverage_score = 5
    scores["leverage"] = leverage_score

    # 4. Valuation (P/E, PEG) - 25 points max
    pe = info.get("trailingPE")
    peg = info.get("pegRatio")

    val_score = 12  # Default
    if pe is not None and pe > 0:
        if peg is not None and peg > 0:
            if peg < 1:
                val_score = 25
            elif peg < 1.5:
                val_score = 20
            elif peg < 2:
                val_score = 15
            else:
                val_score = 10
        else:
            if pe < 15:
                val_score = 20
            elif pe < 25:
                val_score = 15
            elif pe < 35:
                val_score = 10
            else:
                val_score = 5
    scores["valuation"] = val_score

    total = prof_score + growth_score + leverage_score + val_score
    scores["total"] = total

    return total, scores


def calculate_risk_score(df):
    """
    Calculate risk score (0-100, higher = less risky/better).
    Based on rolling volatility and maximum drawdown.
    """
    if df.empty:
        return 50, {}

    scores = {}
    returns = df["Close"].pct_change().dropna()

    # 1. Rolling Volatility (annualized) - 50 points max
    vol_60d = returns.tail(60).std() * np.sqrt(252) if len(returns) >= 60 else returns.std() * np.sqrt(252)

    vol_score = 25  # Default
    if pd.notna(vol_60d):
        if vol_60d < 0.20:
            vol_score = 50
        elif vol_60d < 0.30:
            vol_score = 40
        elif vol_60d < 0.40:
            vol_score = 30
        elif vol_60d < 0.50:
            vol_score = 20
        else:
            vol_score = 10
    scores["volatility"] = vol_score
    scores["vol_60d"] = vol_60d

    # 2. Maximum Drawdown (last 252 days) - 50 points max
    prices = df["Close"].tail(252)
    rolling_max = prices.expanding().max()
    drawdown = (prices - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    dd_score = 25  # Default
    if pd.notna(max_drawdown):
        if max_drawdown > -0.10:
            dd_score = 50
        elif max_drawdown > -0.20:
            dd_score = 40
        elif max_drawdown > -0.30:
            dd_score = 30
        elif max_drawdown > -0.40:
            dd_score = 20
        else:
            dd_score = 10
    scores["drawdown"] = dd_score
    scores["max_drawdown"] = max_drawdown

    total = vol_score + dd_score
    scores["total"] = total

    return total, scores


def generate_recommendation(tech_score, fund_score, risk_score, market_regime, ticker, info, time_horizon="long"):
    """
    Generate BUY/HOLD/SELL recommendation with confidence score and explanation.
    Dynamically weight scores based on market regime and time horizon.
    """
    # Base weights adjusted by market regime
    if market_regime == "Bull":
        base_weights = {"technical": 0.45, "fundamental": 0.30, "risk": 0.25}
    elif market_regime == "Bear":
        base_weights = {"technical": 0.25, "fundamental": 0.30, "risk": 0.45}
    elif market_regime == "High-Volatility":
        base_weights = {"technical": 0.20, "fundamental": 0.30, "risk": 0.50}
    else:  # Sideways
        base_weights = {"technical": 0.35, "fundamental": 0.35, "risk": 0.30}

    # Adjust weights based on time horizon
    if time_horizon == "short":
        # Short-term: emphasize technicals more
        weights = {
            "technical": min(0.55, base_weights["technical"] + 0.10),
            "fundamental": max(0.15, base_weights["fundamental"] - 0.10),
            "risk": base_weights["risk"]
        }
    else:  # long-term
        # Long-term: emphasize fundamentals more
        weights = {
            "technical": max(0.20, base_weights["technical"] - 0.10),
            "fundamental": min(0.45, base_weights["fundamental"] + 0.10),
            "risk": base_weights["risk"]
        }

    # Calculate weighted composite score
    composite = (
        tech_score * weights["technical"] +
        fund_score * weights["fundamental"] +
        risk_score * weights["risk"]
    )

    # Determine recommendation
    if composite >= 65:
        recommendation = "BUY"
        rec_color = "green"
    elif composite >= 45:
        recommendation = "HOLD"
        rec_color = "orange"
    else:
        recommendation = "SELL"
        rec_color = "red"

    # Confidence score (how decisive the signal is)
    if composite >= 75 or composite <= 30:
        confidence = min(95, 60 + abs(composite - 50))
    elif composite >= 60 or composite <= 40:
        confidence = min(80, 50 + abs(composite - 50))
    else:
        confidence = max(30, 50 - abs(composite - 50))

    confidence = int(confidence)

    # Generate explanation
    company_name = info.get("shortName", ticker)
    sector = info.get("sector", "N/A")

    explanation = f"**Market Context:** The U.S. market is currently in a **{market_regime}** regime. "

    if market_regime == "Bull":
        explanation += "Conditions favor growth and momentum strategies. "
    elif market_regime == "Bear":
        explanation += "Defensive positioning and risk management are prioritized. "
    elif market_regime == "High-Volatility":
        explanation += "Elevated uncertainty requires cautious positioning and strong risk controls. "
    else:
        explanation += "Mixed signals suggest a balanced approach between opportunity and caution. "

    horizon_label = "Short-term (1-3 months)" if time_horizon == "short" else "Long-term (6-12 months)"
    explanation += f"\n\n**Analysis Horizon: {horizon_label}** — "
    if time_horizon == "short":
        explanation += "Technical factors weighted more heavily for near-term trading. "
    else:
        explanation += "Fundamentals weighted more heavily for position investing. "

    explanation += f"\n\n**Stock Analysis ({company_name}, {sector}):** "

    if tech_score >= 60:
        explanation += "Technical indicators show positive momentum with favorable trend alignment. "
    elif tech_score >= 40:
        explanation += "Technical indicators are neutral with mixed signals. "
    else:
        explanation += "Technical indicators suggest weakness in price momentum. "

    if fund_score >= 60:
        explanation += "Fundamentals are strong with solid profitability and reasonable valuation. "
    elif fund_score >= 40:
        explanation += "Fundamentals are adequate but not exceptional. "
    else:
        explanation += "Fundamental metrics show concerns in profitability, growth, or valuation. "

    if risk_score >= 60:
        explanation += "Risk profile is favorable with manageable volatility and drawdowns."
    elif risk_score >= 40:
        explanation += "Risk profile is moderate; position sizing should reflect this."
    else:
        explanation += "Elevated risk metrics suggest caution and smaller position sizes."

    explanation += f"\n\n**Recommendation Rationale:** "
    if recommendation == "BUY":
        explanation += f"The combination of {market_regime.lower()} market conditions and the stock's "
        explanation += f"{'strong' if composite >= 70 else 'favorable'} composite score ({composite:.0f}/100) "
        explanation += "supports accumulation at current levels."
    elif recommendation == "HOLD":
        explanation += f"Given the {market_regime.lower()} market environment and mixed signals "
        explanation += f"(composite score: {composite:.0f}/100), maintaining current positions is prudent "
        explanation += "while monitoring for clearer directional signals."
    else:
        explanation += f"The {market_regime.lower()} market backdrop combined with concerning metrics "
        explanation += f"(composite score: {composite:.0f}/100) suggests reducing exposure or avoiding new positions."

    return {
        "recommendation": recommendation,
        "rec_color": rec_color,
        "confidence": confidence,
        "composite_score": composite,
        "weights": weights,
        "explanation": explanation,
    }


st.title("US Stock Analytics Dashboard")

with st.spinner("Loading US stocks..."):
    all_stocks_df = load_all_us_stocks()
    sp500_set = set(all_stocks_df[all_stocks_df["is_sp500"]]["ticker"].tolist())

with st.sidebar:
    st.header("Filters")

    # Sector filter
    sectors = ["All Sectors"] + sorted(all_stocks_df["sector"].dropna().unique().tolist())
    selected_sector = st.selectbox("Sector", sectors, index=0)

    # S&P 500 filter
    sp500_only = st.checkbox("S&P 500 only", value=False)

    # Apply filters
    filtered_df = all_stocks_df.copy()
    if selected_sector != "All Sectors":
        filtered_df = filtered_df[filtered_df["sector"] == selected_sector]
    if sp500_only:
        filtered_df = filtered_df[filtered_df["is_sp500"]]

    st.divider()
    st.header("Stock Selection")

    if filtered_df.empty:
        st.warning("No stocks match the current filters.")
        st.stop()

    ticker_options = filtered_df["ticker"].tolist()
    ticker_labels = [f"{row['ticker']} - {row['name']}" for _, row in filtered_df.iterrows()]

    selected_idx = st.selectbox(
        "Choose a stock",
        range(len(ticker_options)),
        format_func=lambda i: ticker_labels[i],
        index=0
    )
    selected = ticker_options[selected_idx]

    # Show S&P 500 status
    stock_row = filtered_df[filtered_df["ticker"] == selected].iloc[0]
    if stock_row["is_sp500"]:
        st.caption("S&P 500 Member")
    else:
        st.caption("Not in S&P 500")

    st.divider()
    # Clear cache button
    if st.button("🔄 Refresh Data", help="Clear cached data and reload fresh data"):
        st.cache_data.clear()
        st.rerun()

with st.spinner("Loading data..."):
    price_data = load_history(selected)
    info = load_fundamentals(selected)
    financials = load_financial_statements(selected)

if price_data.empty:
    st.error("No price data available for this ticker. Try another selection.")
    st.stop()

price_data = compute_indicators(price_data)

# Debug: Show data sample to verify correct loading
with st.expander("🔍 Debug: Price Data Sample", expanded=True):
    st.write(f"**Ticker:** {selected}")
    st.write(f"**Data shape:** {price_data.shape}")
    st.write(f"**Date range:** {price_data['Date'].min()} to {price_data['Date'].max()}")
    st.write(f"**Close price range:** ${price_data['Close'].min():.2f} to ${price_data['Close'].max():.2f}")
    st.write(f"**Open price range:** ${price_data['Open'].min():.2f} to ${price_data['Open'].max():.2f}")
    st.write(f"**High price range:** ${price_data['High'].min():.2f} to ${price_data['High'].max():.2f}")
    st.write(f"**Low price range:** ${price_data['Low'].min():.2f} to ${price_data['Low'].max():.2f}")
    st.write("**Last 10 rows (OHLC):**")
    st.dataframe(price_data[["Date", "Open", "High", "Low", "Close"]].tail(10))

    # Test direct yfinance fetch
    st.write("---")
    st.write("**Direct yfinance test:**")
    try:
        test_ticker = yf.Ticker(selected)
        test_data = test_ticker.history(period="5d", interval="1d")
        st.write(f"Direct fetch for {selected} (last 5 days):")
        st.dataframe(test_data)
    except Exception as e:
        st.error(f"Direct fetch error: {e}")

last_row = price_data.iloc[-1]
prev_row = price_data.iloc[-2] if len(price_data) > 1 else last_row
change_pct = (last_row["Close"] - prev_row["Close"]) / prev_row["Close"] * 100

sector = info.get("sector", "Technology")
industry = info.get("industry", "N/A")

# Load market data for regime detection
with st.spinner("Analyzing market conditions..."):
    sp500_market, vix_market = load_market_data()
    market_regime, regime_color, regime_metrics = detect_market_regime(sp500_market, vix_market)

    # Calculate scores for recommendation
    tech_score, tech_details = calculate_technical_score(price_data)
    fund_score, fund_details = calculate_fundamental_score(info)
    risk_score, risk_details = calculate_risk_score(price_data)

analysis_tab, overview_tab, technical_tab, fundamentals_tab, news_tab, risk_tab = st.tabs(
    ["Analysis", "Overview", "Technical", "Fundamentals", "News & Sentiment", "Risk"]
)

# =============================================================================
# ANALYSIS TAB - Market Regime & Stock Recommendation
# =============================================================================
with analysis_tab:
    st.subheader("Market & Stock Analysis")

    # Disclaimer
    st.caption("This is a decision-support tool for educational purposes only. Not financial advice. Does not predict prices.")

    # --- TIME HORIZON TOGGLE ---
    horizon_col1, horizon_col2 = st.columns([3, 1])
    with horizon_col2:
        time_horizon = "short" if st.toggle("Short-term focus", value=False, help="Toggle for short-term (1-3 months) vs long-term (6-12 months) analysis. Short-term emphasizes technicals, long-term emphasizes fundamentals.") else "long"

    # Generate recommendation based on time horizon
    recommendation_data = generate_recommendation(
        tech_score, fund_score, risk_score, market_regime, selected, info, time_horizon
    )
    rec = recommendation_data["recommendation"]

    # ==========================================================================
    # 1. EXECUTIVE SUMMARY (Decision first)
    # ==========================================================================
    st.markdown("### Executive Summary")

    # Main recommendation display
    exec_col1, exec_col2, exec_col3 = st.columns([1, 1, 1])

    with exec_col1:
        rec_status = {"BUY": "success", "HOLD": "warning", "SELL": "danger"}.get(rec, "neutral")
        rec_tips = {
            "BUY": "BUY: Favorable conditions for accumulation. Technical, fundamental, and risk metrics support building a position.",
            "HOLD": "HOLD: Mixed signals - maintain positions but wait for clearer direction.",
            "SELL": "SELL: Concerning metrics suggest reducing exposure or avoiding new positions."
        }
        st.markdown(render_metric_card("Recommendation", rec, rec_tips.get(rec, ""), rec_status, "large"), unsafe_allow_html=True)

    with exec_col2:
        confidence = recommendation_data["confidence"]
        conf_status = "success" if confidence >= 70 else "warning" if confidence >= 50 else "danger"
        conf_tip = f"Confidence of {confidence}% measures signal decisiveness."
        st.markdown(render_metric_card("Confidence", f"{confidence}%", conf_tip, conf_status, "large"), unsafe_allow_html=True)

    with exec_col3:
        composite = recommendation_data["composite_score"]
        comp_status = "success" if composite >= 65 else "warning" if composite >= 45 else "danger"
        st.markdown(render_metric_card("Score", f"{composite:.0f}/100", "Weighted composite of Technical, Fundamental, and Risk scores.", comp_status, "large"), unsafe_allow_html=True)

    # Key Drivers inline
    key_drivers = generate_key_drivers(info, tech_score, fund_score, risk_score, price_data, market_regime)
    key_risk = generate_key_risk(info, risk_score, price_data)

    driver_col, risk_col = st.columns([2, 1])
    with driver_col:
        st.markdown("**Key Drivers:**")
        for i, driver in enumerate(key_drivers, 1):
            driver_icon = "📈" if any(w in driver.lower() for w in ["favorable", "strong", "bullish", "above"]) else "📉" if any(w in driver.lower() for w in ["weak", "below", "challenging"]) else "➡️"
            st.markdown(f"{driver_icon} {driver}")
    with risk_col:
        st.markdown("**Primary Risk:**")
        st.warning(f"⚠️ {key_risk}")

    st.divider()

    # ==========================================================================
    # 2. MARKET CONTEXT
    # ==========================================================================
    st.markdown("### Market Context")

    regime_col1, regime_col2 = st.columns([1, 2])

    with regime_col1:
        # Large regime indicator
        regime_emoji = {"Bull": "📈", "Bear": "📉", "Sideways": "➡️", "High-Volatility": "⚡"}.get(market_regime, "⚪")
        regime_status = {"Bull": "success", "Bear": "danger", "Sideways": "warning", "High-Volatility": "danger"}.get(market_regime, "neutral")
        regime_tooltips = {
            "Bull": "Bull Market: The market is trending upward with prices above key moving averages. Conditions favor growth stocks and momentum strategies.",
            "Bear": "Bear Market: The market is in a downtrend with prices below key moving averages. Defensive positioning and capital preservation are prioritized.",
            "Sideways": "Sideways Market: No clear directional trend. Range-bound trading with mixed signals suggests a balanced, cautious approach.",
            "High-Volatility": "High-Volatility Market: VIX above 25 indicates elevated fear and uncertainty. Risk management is critical regardless of trend direction."
        }
        regime_tip = regime_tooltips.get(market_regime, "Market regime could not be determined.")
        st.markdown(
            render_badge_card("Market Regime", market_regime, regime_emoji, regime_tip, regime_status),
            unsafe_allow_html=True
        )

    with regime_col2:
        if regime_metrics:
            metric_col1, metric_col2, metric_col3 = st.columns(3)

            # S&P 500 metrics
            sp500_val = regime_metrics.get('sp500_price', 0)
            vs_ma_val = regime_metrics.get('price_vs_sma200', 0)
            vs_ma_status = "success" if vs_ma_val > 0 else "danger"
            sp500_tip = f"S&P 500 Index at {sp500_val:,.0f}. This benchmark tracks 500 large US companies and is the primary indicator of overall US market health."
            vs_ma_tip = f"The S&P 500 is currently {abs(vs_ma_val):.1f}% {'above' if vs_ma_val > 0 else 'below'} its 200-day moving average. " + ("Trading above the 200-day MA indicates a bullish long-term trend." if vs_ma_val > 0 else "Trading below the 200-day MA indicates a bearish long-term trend.")
            with metric_col1:
                st.markdown(render_compact_card("S&P 500", f"{sp500_val:,.0f}", sp500_tip, "info"), unsafe_allow_html=True)
                st.markdown(render_compact_card("vs 200-day MA", f"{vs_ma_val:+.1f}%", vs_ma_tip, vs_ma_status), unsafe_allow_html=True)

            # MA metrics
            slope_val = regime_metrics.get('sma200_slope', 0)
            cross_val = regime_metrics.get('sma_crossover', 0)
            slope_status = "success" if slope_val > 0 else "danger"
            cross_status = "success" if cross_val > 0 else "danger"
            slope_tip = f"200-day MA Slope of {slope_val:+.2f}% measures the 20-day rate of change in the long-term trend. " + ("A positive slope confirms upward momentum." if slope_val > 0 else "A negative slope indicates deteriorating trend.")
            cross_tip = f"50/200 Cross at {cross_val:+.1f}% shows the gap between short and long-term moving averages. " + ("Positive value (Golden Cross pattern) is bullish." if cross_val > 0 else "Negative value (Death Cross pattern) is bearish.")
            with metric_col2:
                st.markdown(render_compact_card("200-MA Slope", f"{slope_val:+.2f}%", slope_tip, slope_status), unsafe_allow_html=True)
                st.markdown(render_compact_card("50/200 Cross", f"{cross_val:+.1f}%", cross_tip, cross_status), unsafe_allow_html=True)

            # VIX metrics
            vix_val = regime_metrics.get('vix', 0)
            vix_ma = regime_metrics.get('vix_ma20', 0)
            vix_status = "success" if vix_val < 20 else "warning" if vix_val < 25 else "danger"
            vix_level = "low (complacency)" if vix_val < 15 else "normal" if vix_val < 20 else "elevated" if vix_val < 25 else "high (fear)"
            vix_tip = f"VIX (Fear Index) at {vix_val:.1f} is {vix_level}. VIX measures expected 30-day volatility. Below 20 is calm, above 25 indicates significant fear in the market."
            vix_vs_ma = vix_val - vix_ma
            vix_ma_tip = f"VIX 20-day MA at {vix_ma:.1f}. Current VIX is {abs(vix_vs_ma):.1f} points {'above' if vix_vs_ma > 0 else 'below'} its average, indicating {'rising' if vix_vs_ma > 0 else 'falling'} fear levels."
            with metric_col3:
                st.markdown(render_compact_card("VIX", f"{vix_val:.1f}", vix_tip, vix_status), unsafe_allow_html=True)
                st.markdown(render_compact_card("VIX 20-MA", f"{vix_ma:.1f}", vix_ma_tip, "neutral"), unsafe_allow_html=True)

    # Regime explanation
    regime_explanations = {
        "Bull": "The market is in an uptrend with price above key moving averages and low volatility. Momentum strategies are favored.",
        "Bear": "The market is in a downtrend with price below key moving averages. Defensive positioning and risk management are critical.",
        "Sideways": "The market lacks clear direction. A balanced approach is recommended while waiting for clearer signals.",
        "High-Volatility": "Market uncertainty is elevated (VIX > 25). Risk controls should be prioritized regardless of trend direction.",
    }
    st.info(regime_explanations.get(market_regime, "Unable to determine market regime."))

    st.divider()

    # ==========================================================================
    # 3. STOCK SNAPSHOT (Benchmarking)
    # ==========================================================================
    st.markdown("### Stock Snapshot")

    # Calculate stock returns
    if len(price_data) > 22:
        stock_1m_return = (price_data["Close"].iloc[-1] / price_data["Close"].iloc[-22] - 1) * 100
    else:
        stock_1m_return = 0
    if len(price_data) > 66:
        stock_3m_return = (price_data["Close"].iloc[-1] / price_data["Close"].iloc[-66] - 1) * 100
    else:
        stock_3m_return = 0

    # Get S&P 500 returns from regime_metrics
    sp500_1m = regime_metrics.get('sp500_1m_return', 0) if regime_metrics else 0
    sp500_3m = regime_metrics.get('sp500_3m_return', 0) if regime_metrics else 0

    snap_col1, snap_col2, snap_col3, snap_col4 = st.columns(4)

    with snap_col1:
        st.markdown("**Current Price**")
        st.markdown(f"<span style='font-size:24px; color:#4A4A4A;'>${last_row['Close']:.2f}</span>", unsafe_allow_html=True)

    with snap_col2:
        st.markdown("**1-Month Return**")
        stock_status_1m = "success" if stock_1m_return > 0 else "danger"
        st.markdown(f"<span style='color:{get_status_color(stock_status_1m)};'>{selected}: {stock_1m_return:+.1f}%</span>", unsafe_allow_html=True)
        stock_vs_sp_1m = stock_1m_return - sp500_1m
        relative_status_1m = "success" if stock_vs_sp_1m > 0 else "danger"
        st.caption(f"vs S&P 500: {stock_vs_sp_1m:+.1f}%")

    with snap_col3:
        st.markdown("**3-Month Return**")
        stock_status_3m = "success" if stock_3m_return > 0 else "danger"
        st.markdown(f"<span style='color:{get_status_color(stock_status_3m)};'>{selected}: {stock_3m_return:+.1f}%</span>", unsafe_allow_html=True)
        stock_vs_sp_3m = stock_3m_return - sp500_3m
        relative_status_3m = "success" if stock_vs_sp_3m > 0 else "danger"
        st.caption(f"vs S&P 500: {stock_vs_sp_3m:+.1f}%")

    with snap_col4:
        st.markdown("**Relative Performance**")
        if stock_vs_sp_1m > 5 and stock_vs_sp_3m > 5:
            st.success("Outperforming")
        elif stock_vs_sp_1m < -5 and stock_vs_sp_3m < -5:
            st.error("Underperforming")
        else:
            st.info("In-line")

    st.divider()

    # ==========================================================================
    # 4. THESIS (Bull vs Bear)
    # ==========================================================================
    st.markdown("### Investment Thesis")

    bull_case, bear_case = generate_bull_bear_case(info, tech_score, fund_score, price_data, market_regime)

    thesis_col1, thesis_col2 = st.columns(2)

    with thesis_col1:
        st.markdown("**🐂 Bull Case**")
        for point in bull_case:
            st.markdown(f"✅ {point}")

    with thesis_col2:
        st.markdown("**🐻 Bear Case**")
        for point in bear_case:
            st.markdown(f"❌ {point}")

    st.divider()

    # ==========================================================================
    # 5. SCORE DETAILS (Collapsible)
    # ==========================================================================
    with st.expander("Score Breakdown", expanded=False):
        score_col1, score_col2, score_col3 = st.columns(3)
        weights = recommendation_data["weights"]

        with score_col1:
            st.markdown("**Technical Score**")
            tech_status = "success" if tech_score >= 60 else "warning" if tech_score >= 40 else "danger"
            tech_color = get_status_color(tech_status)
            st.markdown(f"<span style='font-family: Source Sans Pro, Arial, sans-serif; font-size:28px; color:{tech_color};'>{tech_score}/100</span>", unsafe_allow_html=True)
            st.caption(f"Weight: {weights['technical']*100:.0f}%")
            st.progress(tech_score / 100)
            st.write(f"- Trend: {tech_details.get('trend', 'N/A')}/40")
            st.write(f"- RSI: {tech_details.get('rsi', 'N/A')}/30")
            st.write(f"- MACD: {tech_details.get('macd', 'N/A')}/30")

        with score_col2:
            st.markdown("**Fundamental Score**")
            fund_status = "success" if fund_score >= 60 else "warning" if fund_score >= 40 else "danger"
            fund_color = get_status_color(fund_status)
            st.markdown(f"<span style='font-family: Source Sans Pro, Arial, sans-serif; font-size:28px; color:{fund_color};'>{fund_score}/100</span>", unsafe_allow_html=True)
            st.caption(f"Weight: {weights['fundamental']*100:.0f}%")
            st.progress(fund_score / 100)
            st.write(f"- Profitability: {fund_details.get('profitability', 'N/A')}/25")
            st.write(f"- Growth: {fund_details.get('growth', 'N/A')}/25")
            st.write(f"- Leverage: {fund_details.get('leverage', 'N/A')}/25")
            st.write(f"- Valuation: {fund_details.get('valuation', 'N/A')}/25")

        with score_col3:
            st.markdown("**Risk Score**")
            risk_status_score = "success" if risk_score >= 60 else "warning" if risk_score >= 40 else "danger"
            risk_color_score = get_status_color(risk_status_score)
            st.markdown(f"<span style='font-family: Source Sans Pro, Arial, sans-serif; font-size:28px; color:{risk_color_score};'>{risk_score}/100</span>", unsafe_allow_html=True)
            st.caption(f"Weight: {weights['risk']*100:.0f}%")
            st.progress(risk_score / 100)
            vol_60d = risk_details.get('vol_60d', 0)
            max_dd = risk_details.get('max_drawdown', 0)
            st.write(f"- Volatility: {risk_details.get('volatility', 'N/A')}/50")
            st.write(f"  - 60-day vol: {vol_60d*100:.1f}%" if vol_60d else "  - 60-day vol: N/A")
            st.write(f"- Drawdown: {risk_details.get('drawdown', 'N/A')}/50")
            st.write(f"  - Max DD: {max_dd*100:.1f}%" if max_dd else "  - Max DD: N/A")

    st.divider()

    # ==========================================================================
    # 6. ACTION & NEXT STEPS
    # ==========================================================================
    st.markdown("### Action & Next Steps")

    action_col1, action_col2 = st.columns(2)

    with action_col1:
        st.markdown("**Action Checklist:**")
        action_items = generate_action_checklist(rec, info, price_data)
        for item in action_items:
            st.markdown(f"• {item}")

    with action_col2:
        st.markdown("**What Would Change This View?**")
        view_changers = generate_view_changers(rec, info, price_data)
        for changer in view_changers:
            st.markdown(f"• {changer}")

    # Analysis Summary in expander
    with st.expander("Full Analysis Summary"):
        st.markdown(recommendation_data["explanation"])

        st.markdown(f"""
        **Weight Adjustments for {market_regime} Market:**
        - Technical: {recommendation_data['weights']['technical']*100:.0f}%
        - Fundamental: {recommendation_data['weights']['fundamental']*100:.0f}%
        - Risk: {recommendation_data['weights']['risk']*100:.0f}%
        """)

with overview_tab:
    st.subheader(f"{selected} Overview")

    # S&P 500 and Exchange badges (exchange from yfinance)
    is_sp500 = selected in sp500_set
    # Get exchange from yfinance info
    raw_exchange = info.get("exchange", "")
    if "nasdaq" in raw_exchange.lower() or "nms" in raw_exchange.lower() or "ngm" in raw_exchange.lower():
        exchange = "NASDAQ"
    elif "nyse" in raw_exchange.lower() or "nys" in raw_exchange.lower():
        exchange = "NYSE"
    else:
        exchange = raw_exchange if raw_exchange else "N/A"

    # Top row: Price, Change, Exchange, S&P 500 status
    top_col1, top_col2, top_col3, top_col4 = st.columns(4)

    change_status = "success" if change_pct >= 0 else "danger"
    price_tip = f"Last closing price of ${last_row['Close']:.2f}. This is the most recent end-of-day traded price for {selected}."
    change_tip = f"Daily change of {change_pct:+.2f}% represents the percentage move from yesterday's close. " + ("Positive movement indicates buying pressure." if change_pct >= 0 else "Negative movement indicates selling pressure.")

    with top_col1:
        st.markdown(render_metric_card("Last Price", f"${last_row['Close']:.2f}", price_tip, "neutral", "medium"), unsafe_allow_html=True)

    with top_col2:
        st.markdown(render_metric_card("Daily Change", f"{change_pct:+.2f}%", change_tip, change_status, "medium"), unsafe_allow_html=True)

    exch_tips = {
        "NASDAQ": "NASDAQ: The National Association of Securities Dealers Automated Quotations. Known for technology and growth companies. Electronic trading exchange.",
        "NYSE": "NYSE: The New York Stock Exchange. The largest stock exchange by market cap. Known for established blue-chip companies."
    }
    exch_tip = exch_tips.get(exchange, f"Stock is listed on {exchange} exchange.")

    with top_col3:
        st.markdown(render_metric_card("Exchange", exchange, exch_tip, "info", "medium"), unsafe_allow_html=True)

    sp_tip = f"{'This stock is a member of the S&P 500 index, representing one of the 500 largest US public companies by market cap.' if is_sp500 else 'This stock is NOT in the S&P 500 index. It may be a smaller company or recently listed.'}"
    sp_status = "success" if is_sp500 else "neutral"
    sp_text = "S&P 500" if is_sp500 else "Non S&P"
    with top_col4:
        st.markdown(render_metric_card("Index", sp_text, sp_tip, sp_status, "medium"), unsafe_allow_html=True)

    st.markdown("")

    # Second row: Sector & Industry
    info_col1, info_col2 = st.columns(2)
    sector_tip = f"Sector: {sector}. Sectors group companies by broad economic activity. Companies in the same sector often move together based on macroeconomic trends."
    industry_tip = f"Industry: {industry}. Industries are more specific than sectors and group companies with similar business models and competitive dynamics."
    with info_col1:
        st.markdown(render_metric_card("Sector", sector, sector_tip, "neutral", "normal"), unsafe_allow_html=True)
    with info_col2:
        st.markdown(render_metric_card("Industry", industry, industry_tip, "neutral", "normal"), unsafe_allow_html=True)

    # Sector Market Share Pie Chart
    st.markdown("### Sector Market Share")

    # Get sector from all_stocks_df for consistency
    stock_info = all_stocks_df[all_stocks_df["ticker"] == selected]
    chart_sector = stock_info["sector"].values[0] if len(stock_info) > 0 and pd.notna(stock_info["sector"].values[0]) else sector

    # Get peers from the same sector
    sector_peers = all_stocks_df[all_stocks_df["sector"] == chart_sector]["ticker"].tolist()

    # Ensure selected ticker is included
    if selected not in sector_peers:
        sector_peers.insert(0, selected)

    if len(sector_peers) > 1:
        with st.spinner("Loading sector market caps..."):
            # Get top companies by fetching market caps
            market_caps = load_industry_market_caps(tuple(sector_peers[:20]))

        if market_caps:
            # Ensure selected company is in the data
            if selected not in market_caps:
                # Fetch selected company's market cap separately
                selected_mcap = info.get("marketCap")
                if selected_mcap and selected_mcap > 0:
                    market_caps[selected] = selected_mcap

            if selected in market_caps:
                # Sort by market cap descending
                sorted_caps = sorted(market_caps.items(), key=lambda x: x[1], reverse=True)
                top_tickers = [t for t, _ in sorted_caps[:10]]
                if selected not in top_tickers:
                    top_tickers = top_tickers[:9] + [selected]
                    # Re-sort to maintain order
                    top_tickers = [t for t in [x[0] for x in sorted_caps] if t in top_tickers or t == selected][:10]

                # Filter and maintain sort order
                sorted_market_caps = [(t, market_caps[t]) for t in top_tickers if t in market_caps]
                sorted_market_caps.sort(key=lambda x: x[1], reverse=True)

                # Create ticker to company name mapping
                ticker_to_name = {}
                for ticker, _ in sorted_market_caps:
                    name_row = all_stocks_df[all_stocks_df["ticker"] == ticker]
                    if len(name_row) > 0:
                        ticker_to_name[ticker] = name_row["name"].values[0]
                    else:
                        ticker_to_name[ticker] = ticker

                # Prepare data for pie chart (sorted by market cap)
                tickers = [t for t, _ in sorted_market_caps]
                values = [v for _, v in sorted_market_caps]
                total_market_cap = sum(values)

                # Find selected company rank (before grouping)
                selected_rank = tickers.index(selected) + 1 if selected in tickers else "N/A"

                # Calculate percentages
                percentages = [(v / total_market_cap) * 100 for v in values]

                # Group companies with <= 2% into "Others" (but never group the selected company)
                grouped_tickers = []
                grouped_values = []
                grouped_percentages = []
                others_value = 0
                others_companies = []

                for t, v, pct in zip(tickers, values, percentages):
                    if pct <= 2 and t != selected:
                        others_value += v
                        others_companies.append((t, ticker_to_name.get(t, t), pct))
                    else:
                        grouped_tickers.append(t)
                        grouped_values.append(v)
                        grouped_percentages.append(pct)

                # Add "Others" group if there are any
                if others_value > 0:
                    grouped_tickers.append("Others")
                    grouped_values.append(others_value)
                    grouped_percentages.append((others_value / total_market_cap) * 100)
                    ticker_to_name["Others"] = "Others"

                # Update working variables
                tickers = grouped_tickers
                values = grouped_values
                percentages = grouped_percentages

                # Light blue-teal gradient palette (aesthetically pleasing)
                gradient_colors = [
                    "#2D8BBA",  # Deep blue
                    "#41B8D5",  # Bright teal
                    "#6CE5E8",  # Light cyan
                    "#5DADE2",  # Sky blue
                    "#85C1E9",  # Soft blue
                    "#A9CCE3",  # Pale blue
                    "#7FB3D5",  # Muted blue
                    "#AED6F1",  # Light periwinkle
                    "#3498DB",  # Bright blue
                    "#5DADE2",  # Sky blue (repeat for more)
                ]

                # Create colors - selected gets coral, Others gets gray
                colors = []
                pull_values = []
                color_idx = 0
                for ticker in tickers:
                    if ticker == selected:
                        colors.append("#FF6B6B")  # Warm coral for selected
                        pull_values.append(0.06)
                    elif ticker == "Others":
                        colors.append("#BDC3C7")  # Light gray for Others
                        pull_values.append(0)
                    else:
                        colors.append(gradient_colors[color_idx % len(gradient_colors)])
                        color_idx += 1
                        pull_values.append(0)

                # Format market cap for display
                def format_mcap(val):
                    if val >= 1e12:
                        return f"${val/1e12:.2f}T"
                    elif val >= 1e9:
                        return f"${val/1e9:.1f}B"
                    elif val >= 1e6:
                        return f"${val/1e6:.1f}M"
                    return f"${val:,.0f}"

                # Create custom hover text with company names and rank
                hover_text = []
                for i, (t, pct) in enumerate(zip(tickers, percentages)):
                    if t == "Others":
                        # Show list of companies in Others group
                        others_list = "<br>".join([f"• {name} ({tick}): {p:.1f}%" for tick, name, p in others_companies[:5]])
                        if len(others_companies) > 5:
                            others_list += f"<br>• ...and {len(others_companies) - 5} more"
                        hover_text.append(
                            f"<b>Others</b> ({len(others_companies)} companies)<br>"
                            f"Combined Market Cap: {format_mcap(others_value)}<br>"
                            f"Sector Share: {pct:.1f}%<br><br>"
                            f"{others_list}"
                        )
                    else:
                        rank = i + 1
                        mcap_fmt = format_mcap(market_caps[t])
                        hover_text.append(
                            f"<b>{ticker_to_name[t]}</b> ({t})<br>"
                            f"Rank: #{rank} in sector<br>"
                            f"Market Cap: {mcap_fmt}<br>"
                            f"Sector Share: {pct:.1f}%"
                        )

                # Text display - show percentage for larger slices, selected always shown
                text_display = []
                for t, pct in zip(tickers, percentages):
                    if t == selected:
                        text_display.append(f"<b>{t}</b><br>{pct:.1f}%")
                    elif t == "Others":
                        text_display.append(f"Others<br>{pct:.1f}%") if pct >= 5 else text_display.append("")
                    elif pct >= 8:  # Show label for slices >= 8%
                        text_display.append(f"{t}<br>{pct:.1f}%")
                    else:
                        text_display.append("")

                # Get selected company info for display
                selected_name = ticker_to_name.get(selected, selected)
                selected_pct = (market_caps[selected] / total_market_cap) * 100
                selected_mcap = format_mcap(market_caps[selected])

                fig_pie = go.Figure(data=[go.Pie(
                    labels=tickers,
                    values=values,
                    hole=0,  # Solid pie chart
                    marker=dict(
                        colors=colors,
                        line=dict(color='#ffffff', width=1.5)
                    ),
                    pull=pull_values,
                    textinfo='text',
                    text=text_display,
                    textposition='outside',
                    textfont=dict(size=11, family='Source Sans Pro', color='#2d3436'),
                    hovertext=hover_text,
                    hoverinfo='text',
                    direction='clockwise',
                    sort=False,
                    showlegend=False
                )])

                fig_pie.update_layout(
                    height=380,
                    margin=dict(t=50, b=30, l=30, r=30),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    title=dict(
                        text=f"<b>{chart_sector} Sector</b> - Top {len(tickers)} by Market Cap",
                        font=dict(size=14, color='#2d3436', family='Source Sans Pro'),
                        x=0.5,
                        xanchor='center'
                    )
                )

                st.plotly_chart(fig_pie, use_container_width=True)

                # Summary metrics below chart
                mcap_col1, mcap_col2, mcap_col3 = st.columns(3)
                with mcap_col1:
                    st.metric("Your Selection", f"#{selected_rank} in sector")
                with mcap_col2:
                    st.metric("Market Cap", selected_mcap)
                with mcap_col3:
                    st.metric("Sector Share", f"{selected_pct:.1f}%")
            else:
                st.info("Market cap data not available for this company.")
        else:
            st.info("Could not load market cap data for sector comparison.")
    else:
        st.info("Not enough companies in this sector for comparison.")

    st.markdown("### Key Metrics")

    # Key metrics with styled cards
    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)

    pe_val = info.get("trailingPE")
    peg_val = info.get("pegRatio")
    roe_val = info.get("returnOnEquity")
    de_val = info.get("debtToEquity")
    rsi_val = last_row["RSI"] if pd.notna(last_row["RSI"]) else None
    macd_val = last_row["MACD"] if pd.notna(last_row["MACD"]) else None

    # Build dynamic tooltips
    if pe_val:
        pe_assessment = "cheap (value territory)" if pe_val < 15 else "fairly valued" if pe_val < 25 else "expensive" if pe_val < 40 else "very expensive (growth premium)"
        pe_tip = f"P/E Ratio of {pe_val:.1f} means the stock trades at {pe_val:.1f}x its earnings. This is considered {pe_assessment}. Lower P/E suggests better value, but growth stocks often have higher P/E."
    else:
        pe_tip = "P/E Ratio not available. This could mean the company is not profitable or data is unavailable."

    if peg_val:
        peg_assessment = "undervalued relative to growth" if peg_val < 1 else "fairly valued for growth" if peg_val < 2 else "expensive relative to growth"
        peg_tip = f"PEG Ratio of {peg_val:.2f} adjusts P/E for expected growth. A PEG of {peg_val:.2f} is {peg_assessment}. PEG below 1 suggests the stock may be undervalued given its growth rate."
    else:
        peg_tip = "PEG Ratio not available. Requires both P/E and growth rate data."

    if roe_val:
        roe_pct = roe_val * 100
        roe_assessment = "excellent" if roe_pct > 20 else "good" if roe_pct > 15 else "moderate" if roe_pct > 10 else "weak"
        roe_tip = f"ROE of {roe_pct:.1f}% means the company generates {roe_pct:.1f} cents of profit for every dollar of shareholder equity. This is {roe_assessment}. Higher ROE indicates efficient use of capital."
    else:
        roe_tip = "Return on Equity not available."

    if de_val:
        de_assessment = "conservative (low leverage)" if de_val < 50 else "moderate leverage" if de_val < 100 else "high leverage" if de_val < 200 else "very high leverage (risky)"
        de_tip = f"Debt/Equity of {de_val:.1f} means the company has ${de_val:.1f} of debt for every $100 of equity. This is {de_assessment}. Lower ratios suggest financial stability."
    else:
        de_tip = "Debt/Equity ratio not available."

    if rsi_val:
        rsi_assessment = "overbought (potential pullback)" if rsi_val > 70 else "oversold (potential bounce)" if rsi_val < 30 else "neutral momentum"
        rsi_tip = f"RSI of {rsi_val:.1f} indicates {rsi_assessment}. RSI measures momentum on a 0-100 scale. Above 70 suggests overbought, below 30 suggests oversold."
    else:
        rsi_tip = "RSI not available due to insufficient price history."

    if macd_val:
        macd_assessment = "bullish momentum" if macd_val > 0 else "bearish momentum"
        macd_tip = f"MACD of {macd_val:.2f} shows {macd_assessment}. MACD measures the relationship between two moving averages. Positive values suggest upward momentum."
    else:
        macd_tip = "MACD not available due to insufficient price history."

    with metrics_col1:
        pe_display = f"{pe_val:.1f}" if pe_val else "N/A"
        pe_status = "success" if pe_val and pe_val < 25 else "warning" if pe_val and pe_val < 35 else "danger" if pe_val else "neutral"
        st.markdown(render_compact_card("P/E Ratio", pe_display, pe_tip, pe_status), unsafe_allow_html=True)

        peg_display = f"{peg_val:.2f}" if peg_val else "N/A"
        peg_status = "success" if peg_val and peg_val < 1.5 else "warning" if peg_val and peg_val < 2 else "danger" if peg_val else "neutral"
        st.markdown(render_compact_card("PEG Ratio", peg_display, peg_tip, peg_status), unsafe_allow_html=True)

    with metrics_col2:
        roe_display = f"{roe_val*100:.1f}%" if roe_val else "N/A"
        roe_status = "success" if roe_val and roe_val > 0.15 else "warning" if roe_val and roe_val > 0.10 else "danger" if roe_val else "neutral"
        st.markdown(render_compact_card("ROE", roe_display, roe_tip, roe_status), unsafe_allow_html=True)

        de_display = f"{de_val:.1f}" if de_val else "N/A"
        de_status = "success" if de_val and de_val < 50 else "warning" if de_val and de_val < 100 else "danger" if de_val else "neutral"
        st.markdown(render_compact_card("Debt/Equity", de_display, de_tip, de_status), unsafe_allow_html=True)

    with metrics_col3:
        rsi_display = f"{rsi_val:.1f}" if rsi_val else "N/A"
        rsi_status = "danger" if rsi_val and rsi_val > 70 else "success" if rsi_val and rsi_val < 30 else "warning" if rsi_val else "neutral"
        st.markdown(render_compact_card("RSI (14)", rsi_display, rsi_tip, rsi_status), unsafe_allow_html=True)

        macd_display = f"{macd_val:.2f}" if macd_val else "N/A"
        macd_status = "success" if macd_val and macd_val > 0 else "danger" if macd_val else "neutral"
        st.markdown(render_compact_card("MACD", macd_display, macd_tip, macd_status), unsafe_allow_html=True)

    st.markdown("### Risk & Valuation")

    risk_level, risk_color, risk_factors = classify_risk(price_data)

    risk_val_col1, risk_val_col2 = st.columns(2)

    risk_tips = {
        "Low": "Low Risk: The stock shows stable price action with controlled volatility. Suitable for conservative investors or larger position sizes.",
        "Medium": "Medium Risk: Moderate volatility detected. Standard position sizing recommended with stop-loss orders.",
        "High": "High Risk: Elevated volatility or extreme RSI readings detected. Consider smaller position sizes and wider stop-losses."
    }
    risk_tip = risk_tips.get(risk_level, "Risk assessment based on 60-day volatility and RSI extremes.")
    risk_status = {"Low": "success", "Medium": "warning", "High": "danger"}.get(risk_level, "neutral")

    with risk_val_col1:
        st.markdown(render_metric_card("Risk Level", risk_level, risk_tip, risk_status, "medium"), unsafe_allow_html=True)

    with risk_val_col2:
        stock_sector = all_stocks_df[all_stocks_df["ticker"] == selected]["sector"].values
        if len(stock_sector) > 0:
            sector_peers = all_stocks_df[all_stocks_df["sector"] == stock_sector[0]]["ticker"].tolist()[:20]
        else:
            sector_peers = filtered_df["ticker"].tolist()[:20]
        peers = load_sector_peers_metrics(tuple(sector_peers))
        peer_pe = peers["pe"].dropna().mean()

        if info.get("trailingPE") and peer_pe:
            if info.get("trailingPE") > peer_pe:
                val_text = "Above Peers"
                val_status_type = "warning"
                val_tip = f"Relative Valuation: This stock's P/E of {info.get('trailingPE'):.1f} is above the sector average of {peer_pe:.1f}. The premium may be justified by faster growth or stronger fundamentals."
            else:
                val_text = "Below Peers"
                val_status_type = "success"
                val_tip = f"Relative Valuation: This stock's P/E of {info.get('trailingPE'):.1f} is below the sector average of {peer_pe:.1f}. This may represent a value opportunity or reflect company-specific concerns."
        else:
            val_text = "N/A"
            val_status_type = "neutral"
            val_tip = "Relative valuation cannot be calculated. Either P/E is unavailable or insufficient peer data exists."

        st.markdown(render_metric_card("Relative Valuation", val_text, val_tip, val_status_type, "medium"), unsafe_allow_html=True)

with technical_tab:
    st.subheader("Technical Indicators")
    st.caption("Comprehensive technical analysis with trend, momentum, and signal indicators.")

    # =========================================================================
    # TECHNICAL SCORE OVERVIEW
    # =========================================================================
    st.markdown("### Technical Score Overview")

    tech_status = "success" if tech_score >= 65 else "warning" if tech_score >= 40 else "danger"
    tech_color = get_status_color(tech_status)

    tech_overview_col1, tech_overview_col2, tech_overview_col3 = st.columns([1, 1, 1])

    with tech_overview_col1:
        tech_score_tip = f"Technical Score of {tech_score}/100 measures price momentum and trend strength. Above 65 is bullish, below 40 is bearish."
        st.markdown(render_badge_card("Technical Score", f"{tech_score}/100", "📈", tech_score_tip, tech_status), unsafe_allow_html=True)

    with tech_overview_col2:
        # Quick summary metrics
        trend_pts = tech_details.get("trend", 0)
        rsi_pts = tech_details.get("rsi", 0)
        macd_pts = tech_details.get("macd", 0)

        trend_status = "success" if trend_pts >= 30 else "warning" if trend_pts >= 15 else "danger"
        rsi_status = "success" if rsi_pts >= 22 else "warning" if rsi_pts >= 12 else "danger"
        macd_status = "success" if macd_pts >= 22 else "warning" if macd_pts >= 12 else "danger"

        st.markdown(render_compact_card("Trend", f"{trend_pts}/40", "Measures price position relative to moving averages", trend_status), unsafe_allow_html=True)
        st.markdown(render_compact_card("RSI", f"{rsi_pts}/30", "Momentum oscillator measuring speed of price changes", rsi_status), unsafe_allow_html=True)

    with tech_overview_col3:
        st.markdown(render_compact_card("MACD", f"{macd_pts}/30", "Trend-following momentum indicator", macd_status), unsafe_allow_html=True)

        # Overall signal
        if tech_score >= 65:
            signal_text = "BULLISH"
            signal_status = "success"
        elif tech_score >= 40:
            signal_text = "NEUTRAL"
            signal_status = "warning"
        else:
            signal_text = "BEARISH"
            signal_status = "danger"
        st.markdown(render_compact_card("Signal", signal_text, "Overall technical outlook based on combined indicators", signal_status), unsafe_allow_html=True)

    st.markdown("---")

    # =========================================================================
    # 1. TREND ANALYSIS SECTION
    # =========================================================================
    st.markdown("### 1. Trend Analysis")

    current_price = price_data["Close"].iloc[-1]
    sma50 = price_data["SMA50"].iloc[-1] if "SMA50" in price_data.columns else None
    sma200 = price_data["SMA200"].iloc[-1] if "SMA200" in price_data.columns else None

    trend_col1, trend_col2 = st.columns([2, 1])

    with trend_col1:
        # Create trend chart with price line and SMAs
        trend_fig = go.Figure()

        # Use last 120 days for trend visualization
        trend_data = price_data.tail(120).copy()

        # SMA 200 first (back layer) - Orange
        if "SMA200" in trend_data.columns:
            sma200_valid = trend_data[["Date", "SMA200"]].dropna()
            if len(sma200_valid) > 0:
                trend_fig.add_trace(go.Scatter(
                    x=sma200_valid["Date"],
                    y=sma200_valid["SMA200"],
                    name="SMA 200",
                    line=dict(color="#F59E0B", width=2.5),
                    mode='lines'
                ))

        # SMA 50 (middle layer) - Blue
        if "SMA50" in trend_data.columns:
            sma50_valid = trend_data[["Date", "SMA50"]].dropna()
            if len(sma50_valid) > 0:
                trend_fig.add_trace(go.Scatter(
                    x=sma50_valid["Date"],
                    y=sma50_valid["SMA50"],
                    name="SMA 50",
                    line=dict(color="#3B82F6", width=2.5),
                    mode='lines'
                ))

        # Price line on top - Dark
        trend_fig.add_trace(go.Scatter(
            x=trend_data["Date"],
            y=trend_data["Close"],
            name="Price",
            line=dict(color="#1F2937", width=2),
            mode='lines'
        ))

        trend_fig.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=30, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=CHART_FONT_COLOR, size=11)),
            font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif"),
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode="x unified"
        )
        trend_fig.update_xaxes(
            showgrid=False,
            showline=True,
            linecolor='#E5E7EB',
            tickfont=dict(color=CHART_AXIS_COLOR, size=10)
        )
        trend_fig.update_yaxes(
            showgrid=True,
            gridcolor='#F3F4F6',
            tickfont=dict(color=CHART_AXIS_COLOR),
            tickprefix="$"
        )

        st.plotly_chart(trend_fig, use_container_width=True)

    with trend_col2:
        st.markdown("**Current Values:**")

        # Price vs SMAs table
        if sma50 and sma200:
            price_vs_sma50 = ((current_price - sma50) / sma50) * 100
            price_vs_sma200 = ((current_price - sma200) / sma200) * 100
            sma50_vs_sma200 = ((sma50 - sma200) / sma200) * 100

            st.markdown(f"**Price:** ${current_price:.2f}")
            st.markdown(f"**SMA 50:** ${sma50:.2f} ({price_vs_sma50:+.1f}%)")
            st.markdown(f"**SMA 200:** ${sma200:.2f} ({price_vs_sma200:+.1f}%)")

            st.markdown("---")
            st.markdown("**Trend Signals:**")

            # Golden Cross / Death Cross
            if sma50 > sma200:
                st.markdown("✅ **Golden Cross** - SMA50 above SMA200 (Bullish)")
            else:
                st.markdown("⚠️ **Death Cross** - SMA50 below SMA200 (Bearish)")

            # Price position
            if current_price > sma50:
                st.markdown("✅ Price above SMA50 (Short-term bullish)")
            else:
                st.markdown("⚠️ Price below SMA50 (Short-term bearish)")

            if current_price > sma200:
                st.markdown("✅ Price above SMA200 (Long-term bullish)")
            else:
                st.markdown("⚠️ Price below SMA200 (Long-term bearish)")

    with st.expander("📖 Understanding Trend Analysis"):
        st.markdown("""
        **Moving Averages (SMA)** smooth out price data to identify trends:

        - **SMA 50 (50-day):** Short-term trend indicator. Price above = bullish momentum.
        - **SMA 200 (200-day):** Long-term trend indicator. Price above = bull market.

        **Key Signals:**
        - **Golden Cross:** SMA50 crosses above SMA200 → Strong buy signal
        - **Death Cross:** SMA50 crosses below SMA200 → Strong sell signal

        **Scoring:**
        - 40 pts: Strong uptrend (Price > SMA50 > SMA200)
        - 30 pts: Moderate uptrend (Price > both SMAs)
        - 20 pts: Weak uptrend (Price > SMA200 only)
        - 10-15 pts: Downtrend or consolidation
        - 0 pts: Strong downtrend (Price < SMA50 < SMA200)
        """)

    # Daily Price Candlestick Chart with SMAs
    st.markdown("#### Daily Price Action")

    # Use last 60 days for better candlestick visibility
    daily_data = price_data.tail(60).copy()

    # Debug: Show what data the candlestick chart will use
    st.caption(f"Showing last {len(daily_data)} trading days | Close: ${daily_data['Close'].min():.2f} - ${daily_data['Close'].max():.2f} | Open: ${daily_data['Open'].iloc[-1]:.2f}, High: ${daily_data['High'].iloc[-1]:.2f}, Low: ${daily_data['Low'].iloc[-1]:.2f}, Close: ${daily_data['Close'].iloc[-1]:.2f}")

    # Create candlestick chart with explicit data conversion
    dates = daily_data["Date"].tolist()
    opens = daily_data["Open"].tolist()
    highs = daily_data["High"].tolist()
    lows = daily_data["Low"].tolist()
    closes = daily_data["Close"].tolist()

    daily_fig = go.Figure()

    # Candlestick for actual daily price
    daily_fig.add_trace(go.Candlestick(
        x=dates,
        open=opens,
        high=highs,
        low=lows,
        close=closes,
        name="OHLC",
        increasing=dict(line=dict(color='#10B981'), fillcolor='#10B981'),
        decreasing=dict(line=dict(color='#EF4444'), fillcolor='#EF4444'),
    ))

    # SMA 200 - Orange trend line
    if "SMA200" in daily_data.columns:
        sma200_vals = daily_data["SMA200"].dropna()
        sma200_dates = daily_data.loc[sma200_vals.index, "Date"]
        if len(sma200_vals) > 0:
            daily_fig.add_trace(go.Scatter(
                x=sma200_dates.tolist(),
                y=sma200_vals.tolist(),
                name="SMA 200",
                line=dict(color="#F59E0B", width=2),
                mode='lines'
            ))

    # SMA 50 - Blue trend line
    if "SMA50" in daily_data.columns:
        sma50_vals = daily_data["SMA50"].dropna()
        sma50_dates = daily_data.loc[sma50_vals.index, "Date"]
        if len(sma50_vals) > 0:
            daily_fig.add_trace(go.Scatter(
                x=sma50_dates.tolist(),
                y=sma50_vals.tolist(),
                name="SMA 50",
                line=dict(color="#3B82F6", width=2),
                mode='lines'
            ))

    daily_fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=30, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=CHART_FONT_COLOR, size=11)),
        font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif"),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode="x unified",
        xaxis_rangeslider_visible=False,
        yaxis=dict(autorange=True)
    )
    daily_fig.update_xaxes(
        showgrid=False,
        showline=True,
        linecolor='#E5E7EB',
        tickfont=dict(color=CHART_AXIS_COLOR, size=10)
    )
    daily_fig.update_yaxes(
        showgrid=True,
        gridcolor='#F3F4F6',
        tickfont=dict(color=CHART_AXIS_COLOR),
        tickprefix="$"
    )

    st.plotly_chart(daily_fig, use_container_width=True, key="daily_price_chart")

    # Daily Close Price Line Chart with SMAs and Trend Signals
    close_header_col1, close_header_col2 = st.columns([3, 1])
    with close_header_col1:
        st.markdown("#### Daily Close Price with Trend Signals")
    with close_header_col2:
        close_period = st.radio(
            "Time Period",
            ["3 Months", "1 Year", "Max"],
            horizontal=True,
            key="close_price_period",
            label_visibility="collapsed"
        )

    # Filter data based on selected time period
    if close_period == "3 Months":
        close_data = price_data.tail(63).copy()  # ~63 trading days in 3 months
    elif close_period == "1 Year":
        close_data = price_data.tail(252).copy()  # ~252 trading days in 1 year
    else:  # Max - use all available data
        close_data = price_data.copy()

    # Show date range info
    date_start = close_data["Date"].iloc[0].strftime("%b %d, %Y") if len(close_data) > 0 else "N/A"
    date_end = close_data["Date"].iloc[-1].strftime("%b %d, %Y") if len(close_data) > 0 else "N/A"
    st.caption(f"Showing {len(close_data)} trading days: {date_start} to {date_end}")

    # Convert to lists for plotting
    close_dates = close_data["Date"].tolist()
    close_prices = close_data["Close"].tolist()

    close_fig = go.Figure()

    # Daily Close Price line
    close_fig.add_trace(go.Scatter(
        x=close_dates,
        y=close_prices,
        name="Close Price",
        line=dict(color="#1F2937", width=2),
        mode='lines'
    ))

    # SMA 200 - Orange trend line
    if "SMA200" in close_data.columns:
        sma200_vals = close_data["SMA200"].dropna()
        sma200_dates = close_data.loc[sma200_vals.index, "Date"]
        if len(sma200_vals) > 0:
            close_fig.add_trace(go.Scatter(
                x=sma200_dates.tolist(),
                y=sma200_vals.tolist(),
                name="SMA 200",
                line=dict(color="#F59E0B", width=2),
                mode='lines'
            ))

    # SMA 50 - Blue trend line
    if "SMA50" in close_data.columns:
        sma50_vals = close_data["SMA50"].dropna()
        sma50_dates = close_data.loc[sma50_vals.index, "Date"]
        if len(sma50_vals) > 0:
            close_fig.add_trace(go.Scatter(
                x=sma50_dates.tolist(),
                y=sma50_vals.tolist(),
                name="SMA 50",
                line=dict(color="#3B82F6", width=2),
                mode='lines'
            ))

    # Detect Golden Cross and Death Cross signals
    if "SMA50" in close_data.columns and "SMA200" in close_data.columns:
        signal_data = close_data[["Date", "Close", "SMA50", "SMA200"]].dropna()

        golden_cross_dates = []
        golden_cross_prices = []
        death_cross_dates = []
        death_cross_prices = []

        for i in range(1, len(signal_data)):
            prev_sma50 = signal_data["SMA50"].iloc[i-1]
            prev_sma200 = signal_data["SMA200"].iloc[i-1]
            curr_sma50 = signal_data["SMA50"].iloc[i]
            curr_sma200 = signal_data["SMA200"].iloc[i]

            # Golden Cross: SMA50 crosses above SMA200
            if prev_sma50 <= prev_sma200 and curr_sma50 > curr_sma200:
                golden_cross_dates.append(signal_data["Date"].iloc[i])
                golden_cross_prices.append(signal_data["Close"].iloc[i])

            # Death Cross: SMA50 crosses below SMA200
            if prev_sma50 >= prev_sma200 and curr_sma50 < curr_sma200:
                death_cross_dates.append(signal_data["Date"].iloc[i])
                death_cross_prices.append(signal_data["Close"].iloc[i])

        # Add Golden Cross markers
        if golden_cross_dates:
            close_fig.add_trace(go.Scatter(
                x=golden_cross_dates,
                y=golden_cross_prices,
                name="Golden Cross",
                mode='markers',
                marker=dict(symbol='triangle-up', size=15, color='#10B981', line=dict(width=2, color='white')),
                hovertemplate="Golden Cross<br>%{x}<br>$%{y:.2f}<extra></extra>"
            ))

        # Add Death Cross markers
        if death_cross_dates:
            close_fig.add_trace(go.Scatter(
                x=death_cross_dates,
                y=death_cross_prices,
                name="Death Cross",
                mode='markers',
                marker=dict(symbol='triangle-down', size=15, color='#EF4444', line=dict(width=2, color='white')),
                hovertemplate="Death Cross<br>%{x}<br>$%{y:.2f}<extra></extra>"
            ))

    close_fig.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=30, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=CHART_FONT_COLOR, size=11)),
        font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif"),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode="x unified",
        yaxis=dict(autorange=True)
    )
    close_fig.update_xaxes(
        showgrid=False,
        showline=True,
        linecolor='#E5E7EB',
        tickfont=dict(color=CHART_AXIS_COLOR, size=10)
    )
    close_fig.update_yaxes(
        showgrid=True,
        gridcolor='#F3F4F6',
        tickfont=dict(color=CHART_AXIS_COLOR),
        tickprefix="$"
    )

    st.plotly_chart(close_fig, use_container_width=True, key="daily_close_chart")

    # Trend Signals Summary
    if "SMA50" in close_data.columns and "SMA200" in close_data.columns:
        latest = close_data.iloc[-1]
        latest_close = latest["Close"]
        latest_sma50 = latest["SMA50"]
        latest_sma200 = latest["SMA200"]

        # Find most recent Golden Cross and Death Cross from FULL data (max period)
        full_signal_data = price_data[["Date", "Close", "SMA50", "SMA200"]].dropna()

        most_recent_golden = None
        most_recent_death = None

        for i in range(1, len(full_signal_data)):
            prev_sma50 = full_signal_data["SMA50"].iloc[i-1]
            prev_sma200 = full_signal_data["SMA200"].iloc[i-1]
            curr_sma50 = full_signal_data["SMA50"].iloc[i]
            curr_sma200 = full_signal_data["SMA200"].iloc[i]

            # Golden Cross: SMA50 crosses above SMA200
            if prev_sma50 <= prev_sma200 and curr_sma50 > curr_sma200:
                most_recent_golden = {
                    "date": full_signal_data["Date"].iloc[i],
                    "close": full_signal_data["Close"].iloc[i],
                    "sma50": curr_sma50,
                    "sma200": curr_sma200
                }

            # Death Cross: SMA50 crosses below SMA200
            if prev_sma50 >= prev_sma200 and curr_sma50 < curr_sma200:
                most_recent_death = {
                    "date": full_signal_data["Date"].iloc[i],
                    "close": full_signal_data["Close"].iloc[i],
                    "sma50": curr_sma50,
                    "sma200": curr_sma200
                }

        signal_col1, signal_col2, signal_col3, signal_col4 = st.columns(4)

        with signal_col1:
            if latest_close > latest_sma50:
                st.markdown("✅ **Price > SMA 50**")
                st.caption("Short-term bullish")
            else:
                st.markdown("🔻 **Price < SMA 50**")
                st.caption("Short-term bearish")

        with signal_col2:
            if latest_close > latest_sma200:
                st.markdown("✅ **Price > SMA 200**")
                st.caption("Long-term bullish")
            else:
                st.markdown("🔻 **Price < SMA 200**")
                st.caption("Long-term bearish")

        with signal_col3:
            if latest_sma50 > latest_sma200:
                st.markdown("✅ **Golden Cross**")
                st.caption("SMA 50 > SMA 200")
            else:
                st.markdown("🔻 **Death Cross**")
                st.caption("SMA 50 < SMA 200")

        with signal_col4:
            # Overall trend assessment
            bullish_signals = sum([
                latest_close > latest_sma50,
                latest_close > latest_sma200,
                latest_sma50 > latest_sma200
            ])
            if bullish_signals == 3:
                st.markdown("🟢 **STRONG UPTREND**")
                st.caption("All signals bullish")
            elif bullish_signals == 2:
                st.markdown("🟡 **MODERATE UPTREND**")
                st.caption("Most signals bullish")
            elif bullish_signals == 1:
                st.markdown("🟠 **WEAK/MIXED**")
                st.caption("Mixed signals")
            else:
                st.markdown("🔴 **DOWNTREND**")
                st.caption("All signals bearish")

        # Detailed explanations with dynamic data
        with st.expander("📖 Understanding Golden Cross"):
            if most_recent_golden:
                gc_date = most_recent_golden["date"].strftime("%B %d, %Y")
                gc_close = most_recent_golden["close"]
                gc_sma50 = most_recent_golden["sma50"]
                gc_sma200 = most_recent_golden["sma200"]
                st.markdown(f"""
**Most Recent Golden Cross for {selected}:** {gc_date}

On this date:
- **Stock Price:** ${gc_close:.2f}
- **50-day Average:** ${gc_sma50:.2f}
- **200-day Average:** ${gc_sma200:.2f}

---

**What is a Golden Cross? (Simple Explanation)**

Think of it like this:
- The **200-day average** shows where the stock has been heading over the **long term** (about 10 months)
- The **50-day average** shows where the stock has been heading **recently** (about 2.5 months)

On {gc_date}, the recent trend (${gc_sma50:.2f}) rose **above** the long-term trend (${gc_sma200:.2f}).

**Why did this happen?**
- More people started buying the stock recently
- The selling pressure that was pushing the price down has weakened
- The stock's momentum shifted from negative to positive

---

**Why is this important?**

When the recent direction rises above the long-term direction, it suggests:
- 📉 Selling pressure is weakening
- 📈 Buying interest is increasing
- 🔄 The overall trend may be turning positive

---

**What does this mean for an investor?**

A Golden Cross is often seen as a **confirmation that an uptrend may be starting** - but it's not a guarantee.

**It tells you:**
- ✅ The trend is improving
- ✅ Momentum is shifting toward buyers
- ✅ It might be a good time to consider buying or holding

**It does NOT mean:**
- ❌ The price will immediately go up
- ❌ You should buy without doing more research
- ❌ The stock can't go down after this signal

---

**Bottom Line:**

Think of a Golden Cross like a green traffic light - it suggests it's okay to proceed, but you still need to watch the road. It's one positive sign among many you should look at before making investment decisions.
                """)
            else:
                st.markdown(f"""
**No Golden Cross detected in available history for {selected}**

*Here's a hypothetical example to help you understand:*

Imagine on January 15, 2025:
- **Stock Price:** $150.00
- **50-day Average:** $148.50
- **200-day Average:** $147.00

---

**What is a Golden Cross? (Simple Explanation)**

Think of it like this:
- The **200-day average** shows where the stock has been heading over the **long term** (about 10 months)
- The **50-day average** shows where the stock has been heading **recently** (about 2.5 months)

In this example, the recent trend ($148.50) rose **above** the long-term trend ($147.00).

**Why would this happen?**
- More people started buying the stock recently
- The selling pressure that was pushing the price down has weakened
- The stock's momentum shifted from negative to positive

---

**Why is this important?**

When the recent direction rises above the long-term direction, it suggests:
- 📉 Selling pressure is weakening
- 📈 Buying interest is increasing
- 🔄 The overall trend may be turning positive

---

**What does this mean for an investor?**

A Golden Cross is often seen as a **confirmation that an uptrend may be starting** - but it's not a guarantee.

**It tells you:**
- ✅ The trend is improving
- ✅ Momentum is shifting toward buyers
- ✅ It might be a good time to consider buying or holding

**It does NOT mean:**
- ❌ The price will immediately go up
- ❌ You should buy without doing more research
- ❌ The stock can't go down after this signal

---

**Bottom Line:**

Think of a Golden Cross like a green traffic light - it suggests it's okay to proceed, but you still need to watch the road.
                """)

        with st.expander("📖 Understanding Death Cross"):
            if most_recent_death:
                dc_date = most_recent_death["date"].strftime("%B %d, %Y")
                dc_close = most_recent_death["close"]
                dc_sma50 = most_recent_death["sma50"]
                dc_sma200 = most_recent_death["sma200"]
                st.markdown(f"""
**Most Recent Death Cross for {selected}:** {dc_date}

On this date:
- **Stock Price:** ${dc_close:.2f}
- **50-day Average:** ${dc_sma50:.2f}
- **200-day Average:** ${dc_sma200:.2f}

---

**What is a Death Cross? (Simple Explanation)**

Think of it like this:
- The **200-day average** shows where the stock has been heading over the **long term** (about 10 months)
- The **50-day average** shows where the stock has been heading **recently** (about 2.5 months)

On {dc_date}, the recent trend (${dc_sma50:.2f}) dropped **below** the long-term trend (${dc_sma200:.2f}).

**Why did this happen?**
- More people started selling the stock recently
- The buying interest that was pushing the price up has weakened
- The stock's momentum shifted from positive to negative

---

**Why is this important?**

When the recent direction falls below the long-term direction, it suggests:
- 📈 Buying interest is weakening
- 📉 Selling pressure is increasing
- 🔄 The overall trend may be turning negative

---

**What does this mean for an investor?**

A Death Cross is often seen as a **warning sign that a downtrend may be starting** - but it's not a guarantee.

**It tells you:**
- ⚠️ The trend is weakening
- ⚠️ Momentum is shifting toward sellers
- ⚠️ It might be time to be cautious, protect your profits, or wait before buying more

**It does NOT mean:**
- ❌ The price will immediately crash
- ❌ You must sell everything right away
- ❌ The stock can't recover after this signal

---

**Bottom Line:**

Think of a Death Cross like a yellow/red traffic light - it's a warning to slow down and be careful. It doesn't mean you'll definitely crash, but it's telling you to pay attention and maybe not speed up right now. Many investors use this signal to set "stop-loss" orders (automatic sells if the price drops further) to protect themselves.
                """)
            else:
                st.markdown(f"""
**No Death Cross detected in available history for {selected}**

*Here's a hypothetical example to help you understand:*

Imagine on March 10, 2025:
- **Stock Price:** $120.00
- **50-day Average:** $125.00
- **200-day Average:** $128.00

---

**What is a Death Cross? (Simple Explanation)**

Think of it like this:
- The **200-day average** shows where the stock has been heading over the **long term** (about 10 months)
- The **50-day average** shows where the stock has been heading **recently** (about 2.5 months)

In this example, the recent trend ($125.00) dropped **below** the long-term trend ($128.00).

**Why would this happen?**
- More people started selling the stock recently
- The buying interest that was pushing the price up has weakened
- The stock's momentum shifted from positive to negative

---

**Why is this important?**

When the recent direction falls below the long-term direction, it suggests:
- 📈 Buying interest is weakening
- 📉 Selling pressure is increasing
- 🔄 The overall trend may be turning negative

---

**What does this mean for an investor?**

A Death Cross is often seen as a **warning sign that a downtrend may be starting** - but it's not a guarantee.

**It tells you:**
- ⚠️ The trend is weakening
- ⚠️ Momentum is shifting toward sellers
- ⚠️ It might be time to be cautious, protect your profits, or wait before buying more

**It does NOT mean:**
- ❌ The price will immediately crash
- ❌ You must sell everything right away
- ❌ The stock can't recover after this signal

---

**Bottom Line:**

Think of a Death Cross like a yellow/red traffic light - it's a warning to slow down and be careful. It doesn't mean you'll definitely crash, but it's telling you to pay attention and maybe not speed up right now.
                """)

    st.markdown("---")

    # =========================================================================
    # 2. RSI ANALYSIS SECTION
    # =========================================================================
    st.markdown("### 2. RSI (Relative Strength Index)")

    rsi_val = price_data["RSI"].iloc[-1] if "RSI" in price_data.columns else 50

    rsi_col1, rsi_col2 = st.columns([2, 1])

    with rsi_col1:
        # Create RSI chart
        rsi_fig = go.Figure()

        rsi_data = price_data.tail(120)

        if "RSI" in rsi_data.columns:
            # Add shaded zones for overbought/oversold
            rsi_fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239, 68, 68, 0.1)", line_width=0)
            rsi_fig.add_hrect(y0=0, y1=30, fillcolor="rgba(34, 197, 94, 0.1)", line_width=0)

            # RSI Line - Blue
            rsi_fig.add_trace(go.Scatter(
                x=rsi_data["Date"],
                y=rsi_data["RSI"],
                name="RSI",
                line=dict(color="#3B82F6", width=2.5),
                mode='lines'
            ))

            # Overbought line
            rsi_fig.add_hline(y=70, line=dict(color="#EF4444", dash="dash", width=1.5),
                             annotation_text="70", annotation_position="right",
                             annotation_font_color="#EF4444")
            # Oversold line
            rsi_fig.add_hline(y=30, line=dict(color="#22C55E", dash="dash", width=1.5),
                             annotation_text="30", annotation_position="right",
                             annotation_font_color="#22C55E")
            # Midline
            rsi_fig.add_hline(y=50, line=dict(color="#9CA3AF", dash="dot", width=1))

        rsi_fig.update_layout(
            height=280,
            margin=dict(l=10, r=40, t=20, b=30),
            yaxis=dict(range=[0, 100]),
            font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif"),
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=False,
            hovermode="x unified"
        )
        rsi_fig.update_xaxes(
            showgrid=False,
            showline=True,
            linecolor='#E5E7EB',
            tickfont=dict(color=CHART_AXIS_COLOR, size=10)
        )
        rsi_fig.update_yaxes(
            showgrid=True,
            gridcolor='#F3F4F6',
            tickfont=dict(color=CHART_AXIS_COLOR)
        )

        st.plotly_chart(rsi_fig, use_container_width=True)

    with rsi_col2:
        st.markdown("**Current RSI:**")

        # RSI Gauge visualization
        if rsi_val > 70:
            rsi_zone = "OVERBOUGHT"
            rsi_zone_status = "danger"
            rsi_interpretation = "Stock may be overvalued. Consider taking profits or waiting for pullback."
        elif rsi_val < 30:
            rsi_zone = "OVERSOLD"
            rsi_zone_status = "success"
            rsi_interpretation = "Stock may be undervalued. Potential buying opportunity if fundamentals support."
        elif rsi_val >= 50:
            rsi_zone = "BULLISH"
            rsi_zone_status = "success"
            rsi_interpretation = "Positive momentum. Trend favors buyers."
        else:
            rsi_zone = "BEARISH"
            rsi_zone_status = "warning"
            rsi_interpretation = "Negative momentum. Trend favors sellers."

        rsi_tip = f"RSI of {rsi_val:.1f} indicates {rsi_zone.lower()} conditions."
        st.markdown(render_metric_card("RSI Value", f"{rsi_val:.1f}", rsi_tip, rsi_zone_status, "medium"), unsafe_allow_html=True)

        st.markdown(f"**Zone:** {rsi_zone}")
        st.caption(rsi_interpretation)

        # RSI trend
        if "RSI" in price_data.columns and len(price_data) > 5:
            rsi_5d_ago = price_data["RSI"].iloc[-5]
            rsi_change = rsi_val - rsi_5d_ago
            if rsi_change > 5:
                st.markdown("📈 RSI rising (+{:.1f} in 5 days)".format(rsi_change))
            elif rsi_change < -5:
                st.markdown("📉 RSI falling ({:.1f} in 5 days)".format(rsi_change))
            else:
                st.markdown("➡️ RSI stable ({:+.1f} in 5 days)".format(rsi_change))

    with st.expander("📖 Understanding RSI"):
        st.markdown("""
        **RSI (Relative Strength Index)** measures momentum on a 0-100 scale:

        **Zones:**
        - **Above 70:** Overbought - Stock may be overextended, pullback likely
        - **50-70:** Bullish momentum - Healthy uptrend
        - **30-50:** Bearish momentum - Downward pressure
        - **Below 30:** Oversold - Stock may be undervalued, bounce likely

        **Trading Signals:**
        - RSI crossing above 30 from below → Buy signal
        - RSI crossing below 70 from above → Sell signal
        - RSI divergence from price → Potential trend reversal

        **Scoring:**
        - 30 pts: Oversold (< 30) - High reversal potential
        - 25 pts: Neutral zone (40-60) - Good entry points
        - 20 pts: Mildly overbought (60-70)
        - 10 pts: Overbought (> 70) - Caution advised
        """)

    st.markdown("---")

    # =========================================================================
    # 3. MACD ANALYSIS SECTION
    # =========================================================================
    st.markdown("### 3. MACD (Moving Average Convergence Divergence)")

    macd_val = price_data["MACD"].iloc[-1] if "MACD" in price_data.columns else 0
    macd_sig = price_data["MACD_SIGNAL"].iloc[-1] if "MACD_SIGNAL" in price_data.columns else 0
    macd_hist = price_data["MACD_HIST"].iloc[-1] if "MACD_HIST" in price_data.columns else 0

    macd_col1, macd_col2 = st.columns([2, 1])

    with macd_col1:
        # Create MACD chart
        macd_fig = go.Figure()

        macd_data = price_data.tail(120)

        if "MACD_HIST" in macd_data.columns:
            # Histogram with conditional colors
            colors = ['#10B981' if val >= 0 else '#F43F5E' for val in macd_data["MACD_HIST"]]
            macd_fig.add_trace(go.Bar(
                x=macd_data["Date"],
                y=macd_data["MACD_HIST"],
                name="Histogram",
                marker_color=colors,
                opacity=0.6
            ))

        if "MACD" in macd_data.columns:
            macd_fig.add_trace(go.Scatter(
                x=macd_data["Date"],
                y=macd_data["MACD"],
                name="MACD",
                line=dict(color="#0EA5E9", width=2)
            ))

        if "MACD_SIGNAL" in macd_data.columns:
            macd_fig.add_trace(go.Scatter(
                x=macd_data["Date"],
                y=macd_data["MACD_SIGNAL"],
                name="Signal",
                line=dict(color="#F59E0B", width=2)
            ))

        # Zero line
        macd_fig.add_hline(y=0, line=dict(color="#9CA3AF", dash="dot", width=1))

        macd_fig.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=20, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=CHART_FONT_COLOR, size=11)),
            font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif"),
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode="x unified"
        )
        macd_fig.update_xaxes(
            showgrid=False,
            showline=True,
            linecolor='#E5E7EB',
            tickfont=dict(color=CHART_AXIS_COLOR, size=10)
        )
        macd_fig.update_yaxes(
            showgrid=True,
            gridcolor='#F3F4F6',
            tickfont=dict(color=CHART_AXIS_COLOR)
        )

        st.plotly_chart(macd_fig, use_container_width=True)

    with macd_col2:
        st.markdown("**Current Values:**")

        # Determine MACD signal
        if macd_val > macd_sig and macd_hist > 0:
            macd_signal = "BULLISH"
            macd_signal_status = "success"
            macd_interpretation = "MACD above signal with positive histogram. Strong upward momentum."
        elif macd_val > macd_sig:
            macd_signal = "MILDLY BULLISH"
            macd_signal_status = "success"
            macd_interpretation = "MACD above signal but histogram weak. Momentum building."
        elif macd_val < macd_sig and macd_hist < 0:
            macd_signal = "BEARISH"
            macd_signal_status = "danger"
            macd_interpretation = "MACD below signal with negative histogram. Strong downward momentum."
        elif macd_val < macd_sig:
            macd_signal = "MILDLY BEARISH"
            macd_signal_status = "warning"
            macd_interpretation = "MACD below signal. Momentum weakening."
        else:
            macd_signal = "NEUTRAL"
            macd_signal_status = "warning"
            macd_interpretation = "MACD crossing signal line. Watch for direction confirmation."

        macd_tip = f"MACD: {macd_val:.3f}, Signal: {macd_sig:.3f}, Histogram: {macd_hist:.3f}"
        st.markdown(render_metric_card("MACD Signal", macd_signal, macd_tip, macd_signal_status, "small"), unsafe_allow_html=True)

        st.markdown(f"**MACD Line:** {macd_val:.3f}")
        st.markdown(f"**Signal Line:** {macd_sig:.3f}")
        st.markdown(f"**Histogram:** {macd_hist:+.3f}")

        st.markdown("---")
        st.caption(macd_interpretation)

        # Crossover detection
        if "MACD" in price_data.columns and len(price_data) > 2:
            prev_macd = price_data["MACD"].iloc[-2]
            prev_sig = price_data["MACD_SIGNAL"].iloc[-2]
            if prev_macd <= prev_sig and macd_val > macd_sig:
                st.markdown("🚀 **Bullish Crossover** detected!")
            elif prev_macd >= prev_sig and macd_val < macd_sig:
                st.markdown("⚠️ **Bearish Crossover** detected!")

    with st.expander("📖 Understanding MACD"):
        st.markdown("""
        **MACD** shows the relationship between two moving averages:

        **Components:**
        - **MACD Line:** 12-day EMA minus 26-day EMA
        - **Signal Line:** 9-day EMA of MACD line
        - **Histogram:** Difference between MACD and Signal

        **Key Signals:**
        - **Bullish Crossover:** MACD crosses above Signal → Buy signal
        - **Bearish Crossover:** MACD crosses below Signal → Sell signal
        - **Zero Line Cross:** MACD crossing zero indicates trend change
        - **Divergence:** MACD trending opposite to price → Potential reversal

        **Histogram Interpretation:**
        - Growing green bars: Bullish momentum increasing
        - Shrinking green bars: Bullish momentum weakening
        - Growing red bars: Bearish momentum increasing
        - Shrinking red bars: Bearish momentum weakening

        **Scoring:**
        - 30 pts: Bullish crossover with positive MACD
        - 25 pts: Bullish crossover with negative MACD
        - 15 pts: Neutral/crossing
        - 5-10 pts: Bearish crossover
        """)

    st.markdown("---")

    # =========================================================================
    # 4. BOLLINGER BANDS ANALYSIS
    # =========================================================================
    st.markdown("### 4. Bollinger Bands & Volatility")

    bb_col1, bb_col2 = st.columns([2, 1])

    with bb_col1:
        bb_fig = go.Figure()

        bb_data = price_data.tail(90)

        # Price
        bb_fig.add_trace(go.Candlestick(
            x=bb_data["Date"],
            open=bb_data["Open"],
            high=bb_data["High"],
            low=bb_data["Low"],
            close=bb_data["Close"],
            name="Price",
            increasing_line_color='#10B981',
            decreasing_line_color='#F43F5E'
        ))

        # Bollinger Bands
        if "BB_UPPER" in bb_data.columns and "BB_LOWER" in bb_data.columns:
            bb_fig.add_trace(go.Scatter(
                x=bb_data["Date"],
                y=bb_data["BB_UPPER"],
                name="Upper Band",
                line=dict(color="rgba(14, 165, 233, 0.5)", width=1),
            ))
            bb_fig.add_trace(go.Scatter(
                x=bb_data["Date"],
                y=bb_data["BB_LOWER"],
                name="Lower Band",
                line=dict(color="rgba(14, 165, 233, 0.5)", width=1),
                fill='tonexty',
                fillcolor='rgba(14, 165, 233, 0.1)'
            ))

        if "SMA20" in bb_data.columns:
            bb_fig.add_trace(go.Scatter(
                x=bb_data["Date"],
                y=bb_data["SMA20"],
                name="SMA 20",
                line=dict(color="#F59E0B", width=1, dash='dot')
            ))

        bb_fig.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=20, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=CHART_FONT_COLOR, size=11)),
            font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif"),
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis_rangeslider_visible=False,
            hovermode="x unified"
        )
        bb_fig.update_xaxes(
            showgrid=False,
            showline=True,
            linecolor='#E5E7EB',
            tickfont=dict(color=CHART_AXIS_COLOR, size=10)
        )
        bb_fig.update_yaxes(
            showgrid=True,
            gridcolor='#F3F4F6',
            tickfont=dict(color=CHART_AXIS_COLOR),
            tickprefix="$"
        )

        st.plotly_chart(bb_fig, use_container_width=True)

    with bb_col2:
        st.markdown("**Band Analysis:**")

        if "BB_UPPER" in price_data.columns and "BB_LOWER" in price_data.columns:
            bb_upper = price_data["BB_UPPER"].iloc[-1]
            bb_lower = price_data["BB_LOWER"].iloc[-1]
            bb_width = bb_upper - bb_lower
            bb_pct_width = (bb_width / current_price) * 100

            # Position within bands
            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) * 100 if bb_width > 0 else 50

            if bb_position > 95:
                bb_signal = "At Upper Band"
                bb_status = "danger"
                bb_interp = "Price touching upper band - potential resistance or breakout"
            elif bb_position < 5:
                bb_signal = "At Lower Band"
                bb_status = "success"
                bb_interp = "Price touching lower band - potential support or breakdown"
            elif bb_position > 70:
                bb_signal = "Upper Zone"
                bb_status = "warning"
                bb_interp = "Price in upper zone - momentum strong but watch for reversal"
            elif bb_position < 30:
                bb_signal = "Lower Zone"
                bb_status = "info"
                bb_interp = "Price in lower zone - weakness but may find support"
            else:
                bb_signal = "Middle Zone"
                bb_status = "neutral"
                bb_interp = "Price in middle of bands - no extreme reading"

            st.markdown(render_compact_card("Band Position", f"{bb_position:.0f}%", bb_interp, bb_status), unsafe_allow_html=True)

            st.markdown(f"**Upper Band:** ${bb_upper:.2f}")
            st.markdown(f"**Lower Band:** ${bb_lower:.2f}")
            st.markdown(f"**Band Width:** {bb_pct_width:.1f}%")

            st.markdown("---")
            st.caption(bb_interp)

            # Squeeze detection
            bb_width_sma = price_data["BB_UPPER"].tail(20) - price_data["BB_LOWER"].tail(20)
            avg_width = bb_width_sma.mean()
            if bb_width < avg_width * 0.8:
                st.markdown("🔥 **Squeeze Alert:** Bands narrowing - big move may be coming!")

    with st.expander("📖 Understanding Bollinger Bands"):
        st.markdown("""
        **Bollinger Bands** measure volatility and identify overbought/oversold conditions:

        **Components:**
        - **Middle Band:** 20-day SMA
        - **Upper Band:** Middle + (2 × Standard Deviation)
        - **Lower Band:** Middle - (2 × Standard Deviation)

        **Key Signals:**
        - **Price at Upper Band:** Overbought, potential resistance
        - **Price at Lower Band:** Oversold, potential support
        - **Band Squeeze:** Narrow bands indicate low volatility, often precedes big move
        - **Band Expansion:** Wide bands indicate high volatility

        **Trading Strategies:**
        - Mean Reversion: Buy at lower band, sell at upper band (range-bound markets)
        - Breakout: Trade in direction of band break (trending markets)
        - Squeeze Play: Enter when bands expand after squeeze
        """)

    # =========================================================================
    # 5. VOLUME ANALYSIS SECTION
    # =========================================================================
    st.markdown("### 5. Volume Analysis")

    vol_col1, vol_col2 = st.columns([2, 1])

    with vol_col1:
        vol_fig = go.Figure()

        vol_data = price_data.tail(120)

        # Volume bars with color based on price change
        colors = ['#10B981' if vol_data["Close"].iloc[i] >= vol_data["Open"].iloc[i] else '#F43F5E'
                  for i in range(len(vol_data))]

        vol_fig.add_trace(go.Bar(
            x=vol_data["Date"],
            y=vol_data["Volume"],
            name="Volume",
            marker_color=colors,
            opacity=0.7
        ))

        # Add volume moving average
        vol_ma = vol_data["Volume"].rolling(window=20).mean()
        vol_fig.add_trace(go.Scatter(
            x=vol_data["Date"],
            y=vol_ma,
            name="20-Day Avg",
            line=dict(color="#F59E0B", width=2)
        ))

        vol_fig.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=20, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=CHART_FONT_COLOR, size=11)),
            font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif"),
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode="x unified"
        )
        vol_fig.update_xaxes(
            showgrid=False,
            showline=True,
            linecolor='#E5E7EB',
            tickfont=dict(color=CHART_AXIS_COLOR, size=10)
        )
        vol_fig.update_yaxes(
            showgrid=True,
            gridcolor='#F3F4F6',
            tickfont=dict(color=CHART_AXIS_COLOR)
        )

        st.plotly_chart(vol_fig, use_container_width=True)

    with vol_col2:
        st.markdown("**Volume Analysis:**")

        current_vol = price_data["Volume"].iloc[-1]
        avg_vol_20 = price_data["Volume"].tail(20).mean()
        avg_vol_50 = price_data["Volume"].tail(50).mean()

        vol_ratio = current_vol / avg_vol_20 if avg_vol_20 > 0 else 1

        if vol_ratio > 2:
            vol_signal = "VERY HIGH"
            vol_status = "danger"
            vol_interp = "Volume significantly above average - strong conviction move"
        elif vol_ratio > 1.5:
            vol_signal = "HIGH"
            vol_status = "warning"
            vol_interp = "Elevated volume indicates increased interest"
        elif vol_ratio > 0.75:
            vol_signal = "NORMAL"
            vol_status = "success"
            vol_interp = "Volume within normal range"
        else:
            vol_signal = "LOW"
            vol_status = "info"
            vol_interp = "Below average volume - lack of conviction"

        vol_tip = f"Current volume is {vol_ratio:.1f}x the 20-day average"
        st.markdown(render_metric_card("Volume Signal", vol_signal, vol_tip, vol_status, "medium"), unsafe_allow_html=True)

        st.markdown(f"**Current:** {current_vol:,.0f}")
        st.markdown(f"**20-Day Avg:** {avg_vol_20:,.0f}")
        st.markdown(f"**50-Day Avg:** {avg_vol_50:,.0f}")

        st.markdown("---")
        st.caption(vol_interp)

    with st.expander("📖 Understanding Volume"):
        st.markdown("""
        **Volume** measures the number of shares traded and confirms price moves:

        **Key Signals:**
        - **High Volume + Price Up:** Strong buying pressure, bullish confirmation
        - **High Volume + Price Down:** Strong selling pressure, bearish confirmation
        - **Low Volume + Price Move:** Weak conviction, potential reversal
        - **Volume Spike:** Often precedes or confirms breakouts

        **Volume Patterns:**
        - Increasing volume in uptrend = healthy trend
        - Decreasing volume in uptrend = weakening momentum
        - Volume climax often marks reversals
        """)

    st.markdown("---")

    # =========================================================================
    # 6. Z-SCORE & MEAN REVERSION
    # =========================================================================
    st.markdown("### 6. Z-Score & Mean Reversion")

    zscore_col1, zscore_col2 = st.columns([2, 1])

    with zscore_col1:
        zscore_fig = go.Figure()

        zscore_data = price_data.tail(120)

        if "Z_SCORE_60" in zscore_data.columns:
            # Color based on z-score level
            zscore_fig.add_trace(go.Scatter(
                x=zscore_data["Date"],
                y=zscore_data["Z_SCORE_60"],
                name="Z-Score (60)",
                line=dict(color="#8B5CF6", width=2),
                fill='tozeroy',
                fillcolor='rgba(139, 92, 246, 0.1)'
            ))

            # Reference lines
            zscore_fig.add_hline(y=2, line=dict(color="#F43F5E", dash="dash", width=1),
                                annotation_text="Overbought (+2σ)", annotation_position="right")
            zscore_fig.add_hline(y=-2, line=dict(color="#10B981", dash="dash", width=1),
                                annotation_text="Oversold (-2σ)", annotation_position="right")
            zscore_fig.add_hline(y=0, line=dict(color="#9CA3AF", dash="dot", width=1))

        zscore_fig.update_layout(
            height=280,
            margin=dict(l=10, r=40, t=20, b=30),
            yaxis=dict(range=[-4, 4]),
            font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif"),
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=False,
            hovermode="x unified"
        )
        zscore_fig.update_xaxes(
            showgrid=False,
            showline=True,
            linecolor='#E5E7EB',
            tickfont=dict(color=CHART_AXIS_COLOR, size=10)
        )
        zscore_fig.update_yaxes(
            showgrid=True,
            gridcolor='#F3F4F6',
            tickfont=dict(color=CHART_AXIS_COLOR)
        )

        st.plotly_chart(zscore_fig, use_container_width=True)

    with zscore_col2:
        st.markdown("**Mean Reversion Analysis:**")

        z_val = price_data["Z_SCORE_60"].iloc[-1] if "Z_SCORE_60" in price_data.columns else 0

        if z_val > 2:
            z_zone = "EXTREMELY OVERBOUGHT"
            z_status = "danger"
            z_interp = "Price is 2+ std devs above mean - high reversion probability"
        elif z_val > 1:
            z_zone = "OVERBOUGHT"
            z_status = "warning"
            z_interp = "Price extended above mean - watch for pullback"
        elif z_val < -2:
            z_zone = "EXTREMELY OVERSOLD"
            z_status = "success"
            z_interp = "Price is 2+ std devs below mean - high bounce probability"
        elif z_val < -1:
            z_zone = "OVERSOLD"
            z_status = "info"
            z_interp = "Price depressed below mean - potential value zone"
        else:
            z_zone = "NEUTRAL"
            z_status = "neutral"
            z_interp = "Price near 60-day mean - no extreme reading"

        z_tip = f"Z-Score of {z_val:.2f} indicates price is {abs(z_val):.2f} standard deviations {'above' if z_val > 0 else 'below'} the 60-day mean"
        st.markdown(render_metric_card("Z-Score", f"{z_val:.2f}", z_tip, z_status, "medium"), unsafe_allow_html=True)

        st.markdown(f"**Zone:** {z_zone}")
        st.caption(z_interp)

        # 60-day stats
        ma60 = price_data["Close"].rolling(window=60).mean().iloc[-1]
        std60 = price_data["Close"].rolling(window=60).std().iloc[-1]
        st.markdown("---")
        st.markdown(f"**60-Day Mean:** ${ma60:.2f}")
        st.markdown(f"**60-Day Std Dev:** ${std60:.2f}")

    with st.expander("📖 Understanding Z-Score & Mean Reversion"):
        st.markdown("""
        **Z-Score** measures how far price is from its statistical mean:

        **Interpretation:**
        - **+2 or higher:** Extremely overbought, strong reversion signal
        - **+1 to +2:** Overbought zone, momentum may be extended
        - **-1 to +1:** Normal trading range
        - **-1 to -2:** Oversold zone, potential value opportunity
        - **-2 or lower:** Extremely oversold, strong bounce potential

        **Mean Reversion Strategy:**
        - Prices tend to revert to their mean over time
        - Extreme z-scores (>2 or <-2) often precede reversals
        - Works best in range-bound markets
        - Less effective during strong trends
        """)

    st.markdown("---")

    # =========================================================================
    # 7. ATR & VOLATILITY SECTION
    # =========================================================================
    st.markdown("### 7. ATR (Average True Range)")

    atr_col1, atr_col2 = st.columns([2, 1])

    with atr_col1:
        atr_fig = go.Figure()

        atr_data = price_data.tail(120)

        if "ATR" in atr_data.columns:
            atr_fig.add_trace(go.Scatter(
                x=atr_data["Date"],
                y=atr_data["ATR"],
                name="ATR (14)",
                line=dict(color="#F59E0B", width=2),
                fill='tozeroy',
                fillcolor='rgba(245, 158, 11, 0.1)'
            ))

            # Add ATR moving average
            atr_ma = atr_data["ATR"].rolling(window=20).mean()
            atr_fig.add_trace(go.Scatter(
                x=atr_data["Date"],
                y=atr_ma,
                name="ATR 20-MA",
                line=dict(color="#0EA5E9", width=1.5, dash='dash')
            ))

        atr_fig.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=20, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=CHART_FONT_COLOR, size=11)),
            font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif"),
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode="x unified"
        )
        atr_fig.update_xaxes(
            showgrid=False,
            showline=True,
            linecolor='#E5E7EB',
            tickfont=dict(color=CHART_AXIS_COLOR, size=10)
        )
        atr_fig.update_yaxes(
            showgrid=True,
            gridcolor='#F3F4F6',
            tickfont=dict(color=CHART_AXIS_COLOR),
            tickprefix="$"
        )

        st.plotly_chart(atr_fig, use_container_width=True)

    with atr_col2:
        st.markdown("**ATR Analysis:**")

        atr_current = price_data["ATR"].iloc[-1] if "ATR" in price_data.columns else 0
        atr_ma_val = price_data["ATR"].tail(20).mean() if "ATR" in price_data.columns else 0
        atr_pct = (atr_current / current_price) * 100 if current_price > 0 else 0

        if atr_current > atr_ma_val * 1.3:
            atr_signal = "EXPANDING"
            atr_status = "danger"
            atr_interp = "Volatility increasing - expect larger moves"
        elif atr_current < atr_ma_val * 0.7:
            atr_signal = "CONTRACTING"
            atr_status = "info"
            atr_interp = "Volatility decreasing - potential breakout brewing"
        else:
            atr_signal = "STABLE"
            atr_status = "success"
            atr_interp = "Volatility within normal range"

        atr_tip = f"ATR of ${atr_current:.2f} represents typical daily range"
        st.markdown(render_metric_card("ATR Signal", atr_signal, atr_tip, atr_status, "medium"), unsafe_allow_html=True)

        st.markdown(f"**Current ATR:** ${atr_current:.2f}")
        st.markdown(f"**ATR % of Price:** {atr_pct:.2f}%")
        st.markdown(f"**20-Day ATR Avg:** ${atr_ma_val:.2f}")

        st.markdown("---")
        st.caption(atr_interp)

        # Stop-loss suggestions
        st.markdown("**Stop-Loss Guide:**")
        st.caption(f"Conservative (1x ATR): ${current_price - atr_current:.2f}")
        st.caption(f"Standard (1.5x ATR): ${current_price - (atr_current * 1.5):.2f}")
        st.caption(f"Wide (2x ATR): ${current_price - (atr_current * 2):.2f}")

    with st.expander("📖 Understanding ATR"):
        st.markdown("""
        **ATR (Average True Range)** measures volatility based on price ranges:

        **Uses:**
        - **Position Sizing:** Smaller positions when ATR is high
        - **Stop-Loss Placement:** Set stops based on ATR multiples
        - **Breakout Confirmation:** Expanding ATR confirms moves
        - **Volatility Comparison:** Compare volatility across stocks

        **ATR Patterns:**
        - **Expanding ATR:** Increasing volatility, bigger moves coming
        - **Contracting ATR:** Decreasing volatility, often precedes breakouts
        - **ATR Spike:** Often occurs at market tops/bottoms
        """)

with fundamentals_tab:
    st.subheader("Fundamentals")
    st.caption("Metrics pulled from yfinance. Values are reported if available.")

    # =========================================================================
    # PEER COMPARISON TOGGLE
    # =========================================================================
    show_peer_comparison = st.toggle("Compare with Industry Peers", value=False, help="Toggle to compare this company's metrics with industry peers")

    # Load peer data
    fund_stock_sector = all_stocks_df[all_stocks_df["ticker"] == selected]["sector"].values
    if len(fund_stock_sector) > 0:
        current_sector = fund_stock_sector[0]
        fund_sector_peers = all_stocks_df[all_stocks_df["sector"] == current_sector]["ticker"].tolist()
        fund_sector_peers = [t for t in fund_sector_peers if t != selected][:15]  # Exclude current stock, limit to 15
    else:
        current_sector = "Unknown"
        fund_sector_peers = filtered_df["ticker"].tolist()[:15]

    peers_data = load_sector_peers_metrics(tuple(fund_sector_peers + [selected]))
    peer_means = peers_data[peers_data["ticker"] != selected].drop(columns=["ticker"]).mean()

    if show_peer_comparison:
        # =====================================================================
        # PEER COMPARISON VIEW
        # =====================================================================
        st.markdown(f"### Industry Peer Comparison")
        st.caption(f"Comparing {selected} with {len(fund_sector_peers)} peers in the **{current_sector}** sector")

        st.markdown("---")

        # Get current company values
        fund_pe = info.get("trailingPE")
        fund_peg = info.get("pegRatio")
        fund_roe = info.get("returnOnEquity")
        fund_margin = info.get("profitMargins")
        fund_growth = info.get("revenueGrowth")
        fund_de = info.get("debtToEquity")

        # Valuation Comparison Chart
        st.markdown("#### Valuation Comparison")
        val_compare_col1, val_compare_col2 = st.columns(2)

        with val_compare_col1:
            # P/E Comparison
            pe_fig = go.Figure()
            pe_fig.add_trace(go.Bar(
                x=[selected, "Peer Average"],
                y=[fund_pe if fund_pe else 0, peer_means.get("pe", 0) if peer_means.get("pe") else 0],
                marker_color=["#0EA5E9", "#9CA3AF"],
                text=[f"{fund_pe:.1f}" if fund_pe else "N/A", f"{peer_means.get('pe', 0):.1f}" if peer_means.get("pe") else "N/A"],
                textposition='outside'
            ))
            pe_fig.update_layout(
                title="P/E Ratio",
                height=300,
                margin=dict(l=0, r=0, t=40, b=0),
                font=dict(color=CHART_FONT_COLOR),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )
            pe_fig.update_xaxes(tickfont=dict(color=CHART_AXIS_COLOR))
            pe_fig.update_yaxes(tickfont=dict(color=CHART_AXIS_COLOR), gridcolor=CHART_GRID_COLOR)
            st.plotly_chart(pe_fig, use_container_width=True)

        with val_compare_col2:
            # PEG Comparison
            peg_fig = go.Figure()
            peg_fig.add_trace(go.Bar(
                x=[selected, "Peer Average"],
                y=[fund_peg if fund_peg else 0, peer_means.get("peg", 0) if peer_means.get("peg") else 0],
                marker_color=["#0EA5E9", "#9CA3AF"],
                text=[f"{fund_peg:.2f}" if fund_peg else "N/A", f"{peer_means.get('peg', 0):.2f}" if peer_means.get("peg") else "N/A"],
                textposition='outside'
            ))
            peg_fig.update_layout(
                title="PEG Ratio",
                height=300,
                margin=dict(l=0, r=0, t=40, b=0),
                font=dict(color=CHART_FONT_COLOR),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )
            peg_fig.update_xaxes(tickfont=dict(color=CHART_AXIS_COLOR))
            peg_fig.update_yaxes(tickfont=dict(color=CHART_AXIS_COLOR), gridcolor=CHART_GRID_COLOR)
            st.plotly_chart(peg_fig, use_container_width=True)

        st.markdown("---")

        # Profitability Comparison Chart
        st.markdown("#### Profitability Comparison")
        prof_compare_col1, prof_compare_col2 = st.columns(2)

        with prof_compare_col1:
            # ROE Comparison
            roe_fig = go.Figure()
            roe_fig.add_trace(go.Bar(
                x=[selected, "Peer Average"],
                y=[(fund_roe * 100) if fund_roe else 0, (peer_means.get("roe", 0) * 100) if peer_means.get("roe") else 0],
                marker_color=["#10B981", "#9CA3AF"],
                text=[f"{fund_roe*100:.1f}%" if fund_roe else "N/A", f"{peer_means.get('roe', 0)*100:.1f}%" if peer_means.get("roe") else "N/A"],
                textposition='outside'
            ))
            roe_fig.update_layout(
                title="Return on Equity (ROE)",
                height=300,
                margin=dict(l=0, r=0, t=40, b=0),
                font=dict(color=CHART_FONT_COLOR),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                yaxis_title="%"
            )
            roe_fig.update_xaxes(tickfont=dict(color=CHART_AXIS_COLOR))
            roe_fig.update_yaxes(tickfont=dict(color=CHART_AXIS_COLOR), gridcolor=CHART_GRID_COLOR)
            st.plotly_chart(roe_fig, use_container_width=True)

        with prof_compare_col2:
            # Net Margin Comparison
            margin_fig = go.Figure()
            margin_fig.add_trace(go.Bar(
                x=[selected, "Peer Average"],
                y=[(fund_margin * 100) if fund_margin else 0, (peer_means.get("net_margin", 0) * 100) if peer_means.get("net_margin") else 0],
                marker_color=["#10B981", "#9CA3AF"],
                text=[f"{fund_margin*100:.1f}%" if fund_margin else "N/A", f"{peer_means.get('net_margin', 0)*100:.1f}%" if peer_means.get("net_margin") else "N/A"],
                textposition='outside'
            ))
            margin_fig.update_layout(
                title="Net Profit Margin",
                height=300,
                margin=dict(l=0, r=0, t=40, b=0),
                font=dict(color=CHART_FONT_COLOR),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                yaxis_title="%"
            )
            margin_fig.update_xaxes(tickfont=dict(color=CHART_AXIS_COLOR))
            margin_fig.update_yaxes(tickfont=dict(color=CHART_AXIS_COLOR), gridcolor=CHART_GRID_COLOR)
            st.plotly_chart(margin_fig, use_container_width=True)

        st.markdown("---")

        # Growth & Leverage Comparison
        st.markdown("#### Growth & Leverage Comparison")
        gl_compare_col1, gl_compare_col2 = st.columns(2)

        with gl_compare_col1:
            # Revenue Growth Comparison
            growth_fig = go.Figure()
            growth_fig.add_trace(go.Bar(
                x=[selected, "Peer Average"],
                y=[(fund_growth * 100) if fund_growth else 0, (peer_means.get("rev_growth", 0) * 100) if peer_means.get("rev_growth") else 0],
                marker_color=["#8B5CF6", "#9CA3AF"],
                text=[f"{fund_growth*100:.1f}%" if fund_growth else "N/A", f"{peer_means.get('rev_growth', 0)*100:.1f}%" if peer_means.get("rev_growth") else "N/A"],
                textposition='outside'
            ))
            growth_fig.update_layout(
                title="Revenue Growth (YoY)",
                height=300,
                margin=dict(l=0, r=0, t=40, b=0),
                font=dict(color=CHART_FONT_COLOR),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                yaxis_title="%"
            )
            growth_fig.update_xaxes(tickfont=dict(color=CHART_AXIS_COLOR))
            growth_fig.update_yaxes(tickfont=dict(color=CHART_AXIS_COLOR), gridcolor=CHART_GRID_COLOR)
            st.plotly_chart(growth_fig, use_container_width=True)

        with gl_compare_col2:
            # Debt/Equity Comparison
            de_fig = go.Figure()
            de_fig.add_trace(go.Bar(
                x=[selected, "Peer Average"],
                y=[fund_de if fund_de else 0, peer_means.get("de", 0) if peer_means.get("de") else 0],
                marker_color=["#F43F5E", "#9CA3AF"],
                text=[f"{fund_de:.1f}" if fund_de else "N/A", f"{peer_means.get('de', 0):.1f}" if peer_means.get("de") else "N/A"],
                textposition='outside'
            ))
            de_fig.update_layout(
                title="Debt to Equity Ratio",
                height=300,
                margin=dict(l=0, r=0, t=40, b=0),
                font=dict(color=CHART_FONT_COLOR),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )
            de_fig.update_xaxes(tickfont=dict(color=CHART_AXIS_COLOR))
            de_fig.update_yaxes(tickfont=dict(color=CHART_AXIS_COLOR), gridcolor=CHART_GRID_COLOR)
            st.plotly_chart(de_fig, use_container_width=True)

        st.markdown("---")

        # Full Peer Comparison Table
        st.markdown("#### Detailed Peer Comparison")
        compare_df = pd.DataFrame({
            "Metric": ["P/E Ratio", "PEG Ratio", "ROE (%)", "Net Margin (%)", "Revenue Growth (%)", "Debt/Equity"],
            selected: [
                f"{fund_pe:.1f}" if fund_pe else "N/A",
                f"{fund_peg:.2f}" if fund_peg else "N/A",
                f"{fund_roe*100:.1f}" if fund_roe else "N/A",
                f"{fund_margin*100:.1f}" if fund_margin else "N/A",
                f"{fund_growth*100:.1f}" if fund_growth else "N/A",
                f"{fund_de:.1f}" if fund_de else "N/A"
            ],
            "Peer Average": [
                f"{peer_means.get('pe', 0):.1f}" if peer_means.get("pe") else "N/A",
                f"{peer_means.get('peg', 0):.2f}" if peer_means.get("peg") else "N/A",
                f"{peer_means.get('roe', 0)*100:.1f}" if peer_means.get("roe") else "N/A",
                f"{peer_means.get('net_margin', 0)*100:.1f}" if peer_means.get("net_margin") else "N/A",
                f"{peer_means.get('rev_growth', 0)*100:.1f}" if peer_means.get("rev_growth") else "N/A",
                f"{peer_means.get('de', 0):.1f}" if peer_means.get("de") else "N/A"
            ],
            "vs Peers": [
                "Better" if fund_pe and peer_means.get("pe") and fund_pe < peer_means.get("pe") else "Worse" if fund_pe and peer_means.get("pe") else "-",
                "Better" if fund_peg and peer_means.get("peg") and fund_peg < peer_means.get("peg") else "Worse" if fund_peg and peer_means.get("peg") else "-",
                "Better" if fund_roe and peer_means.get("roe") and fund_roe > peer_means.get("roe") else "Worse" if fund_roe and peer_means.get("roe") else "-",
                "Better" if fund_margin and peer_means.get("net_margin") and fund_margin > peer_means.get("net_margin") else "Worse" if fund_margin and peer_means.get("net_margin") else "-",
                "Better" if fund_growth and peer_means.get("rev_growth") and fund_growth > peer_means.get("rev_growth") else "Worse" if fund_growth and peer_means.get("rev_growth") else "-",
                "Better" if fund_de and peer_means.get("de") and fund_de < peer_means.get("de") else "Worse" if fund_de and peer_means.get("de") else "-"
            ]
        })
        st.dataframe(compare_df, use_container_width=True, hide_index=True)
        st.caption(f"Comparing with {len(fund_sector_peers)} companies in {current_sector} sector")

    else:
        # =====================================================================
        # COMPANY VIEW (Default)
        # =====================================================================

        # =========================================================================
        # FUNDAMENTAL SCORE BREAKDOWN
        # =========================================================================
        st.markdown("### Fundamental Score")

    fund_status = "success" if fund_score >= 65 else "warning" if fund_score >= 40 else "danger"

    fund_score_col1, fund_score_col2 = st.columns([1, 2])

    with fund_score_col1:
        fund_score_tip = f"Fundamental Score of {fund_score}/100 measures company quality based on profitability, growth, leverage, and valuation. Above 65 is strong, below 40 is weak."
        st.markdown(render_badge_card("Fundamental Score", f"{fund_score}/100", "📊", fund_score_tip, fund_status), unsafe_allow_html=True)

    with fund_score_col2:
        st.markdown("**Score Breakdown:**")

        # Profitability Score (25 max)
        prof_pts = fund_details.get("profitability", 0)
        prof_pct = prof_pts / 25 * 100
        roe_val = info.get("returnOnEquity")
        margin_val = info.get("profitMargins")
        st.markdown(f"**Profitability** ({prof_pts}/25 pts)")
        st.progress(prof_pct / 100)
        if roe_val and margin_val:
            st.caption(f"ROE: {roe_val*100:.1f}% | Net Margin: {margin_val*100:.1f}%")
        elif roe_val:
            st.caption(f"ROE: {roe_val*100:.1f}%")
        elif margin_val:
            st.caption(f"Net Margin: {margin_val*100:.1f}%")

        # Growth Score (25 max)
        growth_pts = fund_details.get("growth", 0)
        growth_pct = growth_pts / 25 * 100
        rev_growth_val = info.get("revenueGrowth")
        st.markdown(f"**Growth** ({growth_pts}/25 pts)")
        st.progress(growth_pct / 100)
        if rev_growth_val:
            growth_assess = "Exceptional" if rev_growth_val > 0.25 else "Strong" if rev_growth_val > 0.15 else "Moderate" if rev_growth_val > 0.05 else "Slow" if rev_growth_val > 0 else "Declining"
            st.caption(f"Revenue Growth: {rev_growth_val*100:.1f}% ({growth_assess})")

        # Leverage Score (25 max)
        lev_pts = fund_details.get("leverage", 0)
        lev_pct = lev_pts / 25 * 100
        de_val = info.get("debtToEquity")
        st.markdown(f"**Leverage** ({lev_pts}/25 pts)")
        st.progress(lev_pct / 100)
        if de_val:
            lev_assess = "Very Conservative" if de_val < 30 else "Conservative" if de_val < 50 else "Moderate" if de_val < 100 else "Aggressive" if de_val < 150 else "High Risk"
            st.caption(f"Debt/Equity: {de_val:.1f} ({lev_assess})")

        # Valuation Score (25 max)
        val_pts = fund_details.get("valuation", 0)
        val_pct = val_pts / 25 * 100
        pe_val = info.get("trailingPE")
        peg_val = info.get("pegRatio")
        st.markdown(f"**Valuation** ({val_pts}/25 pts)")
        st.progress(val_pct / 100)
        if peg_val:
            val_assess = "Undervalued" if peg_val < 1 else "Fair Value" if peg_val < 1.5 else "Slightly Overvalued" if peg_val < 2 else "Overvalued"
            st.caption(f"PEG: {peg_val:.2f} ({val_assess})")
        elif pe_val:
            val_assess = "Attractive" if pe_val < 15 else "Reasonable" if pe_val < 25 else "Premium" if pe_val < 35 else "Expensive"
            st.caption(f"P/E: {pe_val:.1f} ({val_assess})")

    st.markdown("---")

    # Styled metric cards
    fund_pe = info.get("trailingPE")
    fund_peg = info.get("pegRatio")
    fund_roe = info.get("returnOnEquity")
    fund_margin = info.get("profitMargins")
    fund_growth = info.get("revenueGrowth")
    fund_de = info.get("debtToEquity")

    st.markdown("### Valuation Metrics")
    val_col1, val_col2, val_col3 = st.columns(3)

    # Build tooltips for Fundamentals tab
    if fund_pe:
        fund_pe_assess = "attractive valuation" if fund_pe < 15 else "reasonable valuation" if fund_pe < 25 else "premium valuation" if fund_pe < 40 else "very high valuation"
        fund_pe_tip = f"P/E of {fund_pe:.1f} indicates {fund_pe_assess}. You pay ${fund_pe:.1f} for every $1 of annual earnings. Lower is typically better for value investors."
    else:
        fund_pe_tip = "P/E Ratio unavailable. The company may not be profitable or data is missing."

    if fund_peg:
        fund_peg_assess = "undervalued vs growth" if fund_peg < 1 else "fair value vs growth" if fund_peg < 1.5 else "slightly overvalued" if fund_peg < 2 else "overvalued vs growth"
        fund_peg_tip = f"PEG of {fund_peg:.2f} suggests the stock is {fund_peg_assess}. PEG divides P/E by growth rate. Under 1.0 is often considered attractive."
    else:
        fund_peg_tip = "PEG Ratio unavailable. Requires earnings growth forecast data."

    if fund_de:
        fund_de_assess = "very conservative" if fund_de < 30 else "conservative" if fund_de < 50 else "moderate" if fund_de < 100 else "aggressive" if fund_de < 200 else "highly leveraged"
        fund_de_tip = f"Debt/Equity of {fund_de:.1f} is {fund_de_assess}. For every $100 in equity, the company has ${fund_de:.1f} in debt. Higher values mean more financial risk."
    else:
        fund_de_tip = "Debt/Equity unavailable."

    with val_col1:
        pe_disp = f"{fund_pe:.1f}" if fund_pe else "N/A"
        pe_status = "success" if fund_pe and fund_pe < 20 else "warning" if fund_pe and fund_pe < 30 else "danger" if fund_pe else "neutral"
        st.markdown(render_metric_card("P/E Ratio", pe_disp, fund_pe_tip, pe_status, "medium"), unsafe_allow_html=True)

    with val_col2:
        peg_disp = f"{fund_peg:.2f}" if fund_peg else "N/A"
        peg_status = "success" if fund_peg and fund_peg < 1 else "warning" if fund_peg and fund_peg < 2 else "danger" if fund_peg else "neutral"
        st.markdown(render_metric_card("PEG Ratio", peg_disp, fund_peg_tip, peg_status, "medium"), unsafe_allow_html=True)

    with val_col3:
        de_disp = f"{fund_de:.1f}" if fund_de else "N/A"
        de_status = "success" if fund_de and fund_de < 50 else "warning" if fund_de and fund_de < 100 else "danger" if fund_de else "neutral"
        st.markdown(render_metric_card("Debt/Equity", de_disp, fund_de_tip, de_status, "medium"), unsafe_allow_html=True)

    st.markdown("### Profitability & Growth")
    prof_col1, prof_col2, prof_col3 = st.columns(3)

    # Build tooltips for profitability metrics
    if fund_roe:
        roe_pct_val = fund_roe * 100
        fund_roe_assess = "exceptional" if roe_pct_val > 25 else "excellent" if roe_pct_val > 20 else "good" if roe_pct_val > 15 else "adequate" if roe_pct_val > 10 else "below average"
        fund_roe_tip = f"ROE of {roe_pct_val:.1f}% is {fund_roe_assess}. This means for every $100 of shareholder equity, the company generates ${roe_pct_val:.1f} in profit. Higher ROE indicates efficient capital use."
    else:
        fund_roe_tip = "Return on Equity unavailable."

    if fund_margin:
        margin_pct = fund_margin * 100
        fund_margin_assess = "excellent" if margin_pct > 20 else "strong" if margin_pct > 15 else "healthy" if margin_pct > 10 else "thin" if margin_pct > 5 else "very thin"
        fund_margin_tip = f"Net Margin of {margin_pct:.1f}% is {fund_margin_assess}. The company keeps ${margin_pct:.1f} as profit from every $100 in revenue after all expenses. Higher margins mean better pricing power."
    else:
        fund_margin_tip = "Net Profit Margin unavailable."

    if fund_growth:
        growth_pct = fund_growth * 100
        fund_growth_assess = "exceptional growth" if growth_pct > 25 else "strong growth" if growth_pct > 15 else "moderate growth" if growth_pct > 5 else "slow growth" if growth_pct > 0 else "declining revenue"
        fund_growth_tip = f"Revenue Growth of {growth_pct:.1f}% indicates {fund_growth_assess}. Year-over-year revenue {'increased' if growth_pct > 0 else 'decreased'} by {abs(growth_pct):.1f}%. Sustained growth drives long-term value."
    else:
        fund_growth_tip = "Revenue Growth data unavailable."

    with prof_col1:
        roe_disp = f"{fund_roe*100:.1f}%" if fund_roe else "N/A"
        roe_status = "success" if fund_roe and fund_roe > 0.15 else "warning" if fund_roe and fund_roe > 0.08 else "danger" if fund_roe else "neutral"
        st.markdown(render_metric_card("ROE", roe_disp, fund_roe_tip, roe_status, "medium"), unsafe_allow_html=True)

    with prof_col2:
        margin_disp = f"{fund_margin*100:.1f}%" if fund_margin else "N/A"
        margin_status = "success" if fund_margin and fund_margin > 0.15 else "warning" if fund_margin and fund_margin > 0.05 else "danger" if fund_margin else "neutral"
        st.markdown(render_metric_card("Net Margin", margin_disp, fund_margin_tip, margin_status, "medium"), unsafe_allow_html=True)

    with prof_col3:
        growth_disp = f"{fund_growth*100:.1f}%" if fund_growth else "N/A"
        growth_status = "success" if fund_growth and fund_growth > 0.15 else "warning" if fund_growth and fund_growth > 0 else "danger" if fund_growth else "neutral"
        st.markdown(render_metric_card("Revenue Growth", growth_disp, fund_growth_tip, growth_status, "medium"), unsafe_allow_html=True)

    st.markdown("---")

    # =========================================================================
    # HISTORICAL FINANCIAL CHARTS
    # =========================================================================
    st.markdown("### Historical Financials")
    st.caption("Annual and quarterly financial data from company filings.")

    income_stmt = financials.get("income_stmt")
    balance_sheet = financials.get("balance_sheet")
    cashflow = financials.get("cashflow")
    quarterly_income = financials.get("quarterly_income")
    quarterly_balance = financials.get("quarterly_balance")

    # -------------------------------------------------------------------------
    # 1. REVENUE & PROFIT PERFORMANCE (Vertical Bar + Line Chart)
    # -------------------------------------------------------------------------
    rev_header_col1, rev_header_col2 = st.columns([3, 1])
    with rev_header_col1:
        st.markdown("#### Revenue & Profit Performance")
    with rev_header_col2:
        rev_view_mode = st.radio("", ["Annual", "Quarterly"], horizontal=True, key="rev_view_mode", label_visibility="collapsed")

    if income_stmt is not None and not income_stmt.empty:
        # Try different column names for revenue
        revenue_col = None
        for col_name in ["Total Revenue", "TotalRevenue", "Revenue"]:
            if col_name in income_stmt.columns:
                revenue_col = col_name
                break

        net_income_col = None
        for col_name in ["Net Income", "NetIncome", "Net Income Common Stockholders"]:
            if col_name in income_stmt.columns:
                net_income_col = col_name
                break

        gross_profit_col = None
        for col_name in ["Gross Profit", "GrossProfit"]:
            if col_name in income_stmt.columns:
                gross_profit_col = col_name
                break

        operating_income_col = None
        for col_name in ["Operating Income", "OperatingIncome", "EBIT"]:
            if col_name in income_stmt.columns:
                operating_income_col = col_name
                break

        # Choose data source based on view mode
        if rev_view_mode == "Quarterly" and quarterly_income is not None and not quarterly_income.empty:
            data_source = quarterly_income
            # Format as Q1 '24, Q2 '24, etc.
            dates = []
            for d in data_source.index:
                if hasattr(d, 'quarter'):
                    dates.append(f"Q{d.quarter} '{str(d.year)[2:]}")
                else:
                    dates.append(str(d)[:7])
        else:
            data_source = income_stmt
            dates = data_source.index.strftime('%Y') if hasattr(data_source.index, 'strftime') else [str(d)[:4] for d in data_source.index]

        # Find columns in data source
        rev_col_ds = None
        for col_name in ["Total Revenue", "TotalRevenue", "Revenue"]:
            if col_name in data_source.columns:
                rev_col_ds = col_name
                break

        ni_col_ds = None
        for col_name in ["Net Income", "NetIncome", "Net Income Common Stockholders"]:
            if col_name in data_source.columns:
                ni_col_ds = col_name
                break

        # Revenue Performance Chart (Bar + Line with dual Y-axis)
        if rev_col_ds:
            rev_perf_fig = make_subplots(specs=[[{"secondary_y": True}]])

            revenue_values = data_source[rev_col_ds] / 1e9

            # Calculate profit margin if net income available
            if ni_col_ds:
                net_income_values = data_source[ni_col_ds] / 1e9
                profit_margins = [(ni / rev * 100) if rev != 0 else 0 for ni, rev in zip(data_source[ni_col_ds], data_source[rev_col_ds])]

            # Revenue bars (primary y-axis) - Blue
            rev_perf_fig.add_trace(
                go.Bar(
                    x=list(dates),
                    y=revenue_values.tolist(),
                    name="Revenue",
                    marker_color="#3B82F6",
                    width=0.35,
                    offset=-0.2,
                ),
                secondary_y=False
            )

            # Net Income bars (primary y-axis) - Cyan/Teal
            if ni_col_ds:
                rev_perf_fig.add_trace(
                    go.Bar(
                        x=list(dates),
                        y=net_income_values.tolist(),
                        name="Net Income",
                        marker_color="#22D3D8",
                        width=0.35,
                        offset=0.2,
                    ),
                    secondary_y=False
                )

                # Profit Margin line (secondary y-axis) - Orange
                rev_perf_fig.add_trace(
                    go.Scatter(
                        x=list(dates),
                        y=profit_margins,
                        name="Net Margin %",
                        mode='lines+markers',
                        line=dict(color="#F59E0B", width=2.5),
                        marker=dict(size=8, color="#F59E0B", symbol='circle', line=dict(width=2, color='white')),
                    ),
                    secondary_y=True
                )

            rev_perf_fig.update_layout(
                height=380,
                margin=dict(l=10, r=10, t=20, b=40),
                font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif"),
                plot_bgcolor='white',
                paper_bgcolor='white',
                barmode='group',
                bargap=0.3,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(color=CHART_FONT_COLOR, size=11)
                ),
                hovermode="x unified"
            )

            rev_perf_fig.update_xaxes(
                tickfont=dict(color=CHART_AXIS_COLOR, size=11),
                showgrid=False,
                showline=True,
                linecolor='#E5E7EB'
            )
            rev_perf_fig.update_yaxes(
                tickfont=dict(color=CHART_AXIS_COLOR),
                gridcolor='#F3F4F6',
                showline=False,
                ticksuffix=" B",
                secondary_y=False
            )
            rev_perf_fig.update_yaxes(
                tickfont=dict(color="#F59E0B"),
                showgrid=False,
                ticksuffix="%",
                secondary_y=True
            )

            st.plotly_chart(rev_perf_fig, use_container_width=True)

            # Dynamic Interpretation for Revenue & Profit
            if len(income_stmt) >= 2:
                latest_rev = income_stmt[revenue_col].iloc[-1]
                prev_rev = income_stmt[revenue_col].iloc[-2]
                rev_growth = ((latest_rev - prev_rev) / abs(prev_rev) * 100) if prev_rev else 0

                if net_income_col:
                    latest_ni = income_stmt[net_income_col].iloc[-1]
                    prev_ni = income_stmt[net_income_col].iloc[-2] if len(income_stmt) > 1 else 0
                    ni_growth = ((latest_ni - prev_ni) / abs(prev_ni) * 100) if prev_ni else 0
                    margin = (latest_ni / latest_rev * 100) if latest_rev else 0

                    # Build interpretation
                    rev_trend = "growing" if rev_growth > 5 else "declining" if rev_growth < -5 else "stable"
                    ni_trend = "improving" if ni_growth > 5 else "deteriorating" if ni_growth < -5 else "stable"
                    margin_quality = "excellent" if margin > 20 else "healthy" if margin > 10 else "thin" if margin > 0 else "negative"

                    interpretation = f"**Interpretation:** Revenue is {rev_trend} at {rev_growth:+.1f}% YoY, reaching {format_large_number(latest_rev)}. "
                    interpretation += f"Net income is {ni_trend} ({ni_growth:+.1f}% YoY) with a {margin_quality} profit margin of {margin:.1f}%. "

                    if rev_growth > 10 and ni_growth > 10:
                        interpretation += "The company demonstrates strong top and bottom-line growth, indicating healthy business expansion."
                        st.success(interpretation)
                    elif rev_growth > 0 and ni_growth < 0:
                        interpretation += "Revenue growth without profit growth suggests margin compression - watch for rising costs or pricing pressure."
                        st.warning(interpretation)
                    elif rev_growth < 0 and ni_growth < 0:
                        interpretation += "Both revenue and profits are declining, which may indicate business challenges or market headwinds."
                        st.error(interpretation)
                    else:
                        interpretation += "Performance is mixed - monitor future quarters for trend confirmation."
                        st.info(interpretation)

        st.markdown("---")

        # -------------------------------------------------------------------------
        # 2. GROSS & OPERATING PROFIT (Vertical Bar + Margin Line)
        # -------------------------------------------------------------------------
        profit_header_col1, profit_header_col2 = st.columns([3, 1])
        with profit_header_col1:
            st.markdown("#### Profitability Breakdown")
        with profit_header_col2:
            profit_view_mode = st.radio("", ["Annual", "Quarterly"], horizontal=True, key="profit_view_mode", label_visibility="collapsed")

        if gross_profit_col or operating_income_col:
            # Choose data source based on view mode
            if profit_view_mode == "Quarterly" and quarterly_income is not None and not quarterly_income.empty:
                profit_data = quarterly_income
                profit_dates = []
                for d in profit_data.index:
                    if hasattr(d, 'quarter'):
                        profit_dates.append(f"Q{d.quarter} '{str(d.year)[2:]}")
                    else:
                        profit_dates.append(str(d)[:7])
            else:
                profit_data = income_stmt
                profit_dates = profit_data.index.strftime('%Y') if hasattr(profit_data.index, 'strftime') else [str(d)[:4] for d in profit_data.index]

            # Find columns in data source
            gp_col_ds = None
            for col_name in ["Gross Profit", "GrossProfit"]:
                if col_name in profit_data.columns:
                    gp_col_ds = col_name
                    break

            op_col_ds = None
            for col_name in ["Operating Income", "OperatingIncome", "EBIT"]:
                if col_name in profit_data.columns:
                    op_col_ds = col_name
                    break

            rev_col_profit = None
            for col_name in ["Total Revenue", "TotalRevenue", "Revenue"]:
                if col_name in profit_data.columns:
                    rev_col_profit = col_name
                    break

            profit_fig = make_subplots(specs=[[{"secondary_y": True}]])

            # Gross Profit bars - Blue
            if gp_col_ds:
                gp_values = profit_data[gp_col_ds] / 1e9
                gp_margins = [(gp / rev * 100) if rev != 0 else 0 for gp, rev in zip(profit_data[gp_col_ds], profit_data[rev_col_profit])] if rev_col_profit else []

                profit_fig.add_trace(
                    go.Bar(
                        x=list(profit_dates),
                        y=gp_values.tolist(),
                        name="Gross Profit",
                        marker_color="#3B82F6",
                        width=0.35,
                        offset=-0.2,
                    ),
                    secondary_y=False
                )

            # Operating Income bars - Cyan
            if op_col_ds:
                op_values = profit_data[op_col_ds] / 1e9
                op_margins = [(op / rev * 100) if rev != 0 else 0 for op, rev in zip(profit_data[op_col_ds], profit_data[rev_col_profit])] if rev_col_profit else []

                profit_fig.add_trace(
                    go.Bar(
                        x=list(profit_dates),
                        y=op_values.tolist(),
                        name="Operating Income",
                        marker_color="#22D3D8",
                        width=0.35,
                        offset=0.2,
                    ),
                    secondary_y=False
                )

            # Gross Margin line - Orange
            if gp_col_ds and rev_col_profit and gp_margins:
                profit_fig.add_trace(
                    go.Scatter(
                        x=list(profit_dates),
                        y=gp_margins,
                        name="Gross Margin %",
                        mode='lines+markers',
                        line=dict(color="#F59E0B", width=2.5),
                        marker=dict(size=8, color="#F59E0B", symbol='circle', line=dict(width=2, color='white')),
                    ),
                    secondary_y=True
                )

            profit_fig.update_layout(
                height=380,
                margin=dict(l=10, r=10, t=20, b=40),
                font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif"),
                plot_bgcolor='white',
                paper_bgcolor='white',
                barmode='group',
                bargap=0.3,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(color=CHART_FONT_COLOR, size=11)
                ),
                hovermode="x unified"
            )

            profit_fig.update_xaxes(
                tickfont=dict(color=CHART_AXIS_COLOR, size=11),
                showgrid=False,
                showline=True,
                linecolor='#E5E7EB'
            )
            profit_fig.update_yaxes(
                tickfont=dict(color=CHART_AXIS_COLOR),
                gridcolor='#F3F4F6',
                showline=False,
                ticksuffix=" B",
                secondary_y=False
            )
            profit_fig.update_yaxes(
                tickfont=dict(color="#F59E0B"),
                showgrid=False,
                ticksuffix="%",
                secondary_y=True
            )

            st.plotly_chart(profit_fig, use_container_width=True)

            # Stats row
            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)

            with stats_col1:
                if gross_profit_col and len(income_stmt) > 0:
                    latest_gp = income_stmt[gross_profit_col].iloc[-1]
                    st.metric("Gross Profit", format_large_number(latest_gp))

            with stats_col2:
                if gross_profit_col and revenue_col and len(income_stmt) > 0:
                    gp_margin = (latest_gp / income_stmt[revenue_col].iloc[-1] * 100) if income_stmt[revenue_col].iloc[-1] else 0
                    st.metric("Gross Margin", f"{gp_margin:.1f}%")

            with stats_col3:
                if operating_income_col and len(income_stmt) > 0:
                    latest_op = income_stmt[operating_income_col].iloc[-1]
                    st.metric("Operating Income", format_large_number(latest_op))

            with stats_col4:
                if operating_income_col and revenue_col and len(income_stmt) > 0:
                    op_margin = (latest_op / income_stmt[revenue_col].iloc[-1] * 100) if income_stmt[revenue_col].iloc[-1] else 0
                    st.metric("Operating Margin", f"{op_margin:.1f}%")

            # Dynamic Interpretation for Profitability
            if gross_profit_col and operating_income_col and revenue_col and len(income_stmt) >= 2:
                latest_rev = income_stmt[revenue_col].iloc[-1]
                prev_rev = income_stmt[revenue_col].iloc[-2]

                latest_gp_margin = (income_stmt[gross_profit_col].iloc[-1] / latest_rev * 100) if latest_rev else 0
                prev_gp_margin = (income_stmt[gross_profit_col].iloc[-2] / prev_rev * 100) if prev_rev else 0

                latest_op_margin = (income_stmt[operating_income_col].iloc[-1] / latest_rev * 100) if latest_rev else 0
                prev_op_margin = (income_stmt[operating_income_col].iloc[-2] / prev_rev * 100) if prev_rev else 0

                gp_change = latest_gp_margin - prev_gp_margin
                op_change = latest_op_margin - prev_op_margin

                gp_quality = "strong" if latest_gp_margin > 40 else "healthy" if latest_gp_margin > 25 else "moderate" if latest_gp_margin > 15 else "low"
                op_quality = "excellent" if latest_op_margin > 20 else "good" if latest_op_margin > 12 else "average" if latest_op_margin > 5 else "weak"

                interp = f"**Interpretation:** Gross margin is {gp_quality} at {latest_gp_margin:.1f}% ({gp_change:+.1f}pp YoY), "
                interp += f"while operating margin is {op_quality} at {latest_op_margin:.1f}% ({op_change:+.1f}pp YoY). "

                if gp_change > 0 and op_change > 0:
                    interp += "Both margins are expanding, showing improved pricing power and operational efficiency."
                    st.success(interp)
                elif gp_change < 0 and op_change < 0:
                    interp += "Margin compression across the board suggests cost pressures or competitive pricing challenges."
                    st.warning(interp)
                elif gp_change > 0 and op_change < 0:
                    interp += "Gross margin expansion but operating margin decline indicates rising SG&A or R&D costs."
                    st.info(interp)
                else:
                    interp += "Mixed margin trends - review cost structure for insights."
                    st.info(interp)

    else:
        st.info("Income statement data not available for this stock.")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 2. PROFIT MARGINS OVER TIME
    # -------------------------------------------------------------------------
    st.markdown("#### Profit Margins History")

    if income_stmt is not None and not income_stmt.empty:
        margin_col1, margin_col2 = st.columns([2, 1])

        with margin_col1:
            margin_fig = go.Figure()

            dates = income_stmt.index.strftime('%Y') if hasattr(income_stmt.index, 'strftime') else [str(d)[:4] for d in income_stmt.index]

            # Calculate margins
            if revenue_col:
                revenues = income_stmt[revenue_col].values

                if gross_profit_col:
                    gp_margins = [(income_stmt[gross_profit_col].iloc[i] / revenues[i] * 100) if revenues[i] else 0 for i in range(len(revenues))]
                    margin_fig.add_trace(go.Scatter(
                        x=dates,
                        y=gp_margins,
                        name="Gross Margin",
                        line=dict(color="#10B981", width=2),
                        mode='lines+markers'
                    ))

                if operating_income_col:
                    op_margins = [(income_stmt[operating_income_col].iloc[i] / revenues[i] * 100) if revenues[i] else 0 for i in range(len(revenues))]
                    margin_fig.add_trace(go.Scatter(
                        x=dates,
                        y=op_margins,
                        name="Operating Margin",
                        line=dict(color="#F59E0B", width=2),
                        mode='lines+markers'
                    ))

                if net_income_col:
                    ni_margins = [(income_stmt[net_income_col].iloc[i] / revenues[i] * 100) if revenues[i] else 0 for i in range(len(revenues))]
                    margin_fig.add_trace(go.Scatter(
                        x=dates,
                        y=ni_margins,
                        name="Net Margin",
                        line=dict(color="#8B5CF6", width=2),
                        mode='lines+markers'
                    ))

            margin_fig.update_layout(
                title="Profit Margins Over Time",
                height=300,
                margin=dict(l=0, r=0, t=40, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=CHART_FONT_COLOR)),
                xaxis_title="Fiscal Year",
                yaxis_title="Margin (%)",
                font=dict(color=CHART_FONT_COLOR),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            margin_fig.update_xaxes(showgrid=True, gridcolor=CHART_GRID_COLOR, tickfont=dict(color=CHART_AXIS_COLOR))
            margin_fig.update_yaxes(showgrid=True, gridcolor=CHART_GRID_COLOR, tickfont=dict(color=CHART_AXIS_COLOR))

            st.plotly_chart(margin_fig, use_container_width=True)

        with margin_col2:
            st.markdown("**Margin Analysis:**")

            if revenue_col and gross_profit_col and len(income_stmt) > 0:
                latest_gp_margin = income_stmt[gross_profit_col].iloc[-1] / income_stmt[revenue_col].iloc[-1] * 100 if income_stmt[revenue_col].iloc[-1] else 0
                gp_status = "success" if latest_gp_margin > 40 else "warning" if latest_gp_margin > 20 else "danger"
                st.markdown(render_compact_card("Gross Margin", f"{latest_gp_margin:.1f}%", "Gross profit as % of revenue", gp_status), unsafe_allow_html=True)

            if revenue_col and operating_income_col and len(income_stmt) > 0:
                latest_op_margin = income_stmt[operating_income_col].iloc[-1] / income_stmt[revenue_col].iloc[-1] * 100 if income_stmt[revenue_col].iloc[-1] else 0
                op_status = "success" if latest_op_margin > 20 else "warning" if latest_op_margin > 10 else "danger"
                st.markdown(render_compact_card("Operating Margin", f"{latest_op_margin:.1f}%", "Operating income as % of revenue", op_status), unsafe_allow_html=True)

            if revenue_col and net_income_col and len(income_stmt) > 0:
                latest_ni_margin = income_stmt[net_income_col].iloc[-1] / income_stmt[revenue_col].iloc[-1] * 100 if income_stmt[revenue_col].iloc[-1] else 0
                ni_status = "success" if latest_ni_margin > 15 else "warning" if latest_ni_margin > 5 else "danger"
                st.markdown(render_compact_card("Net Margin", f"{latest_ni_margin:.1f}%", "Net income as % of revenue", ni_status), unsafe_allow_html=True)

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 3. BALANCE SHEET - ASSETS, LIABILITIES, EQUITY
    # -------------------------------------------------------------------------
    bs_header_col1, bs_header_col2 = st.columns([3, 1])
    with bs_header_col1:
        st.markdown("#### Balance Sheet Overview")
    with bs_header_col2:
        bs_view_mode = st.radio("", ["Annual", "Quarterly"], horizontal=True, key="bs_view_mode", label_visibility="collapsed")

    if balance_sheet is not None and not balance_sheet.empty:
        # Choose data source based on view mode
        if bs_view_mode == "Quarterly" and quarterly_balance is not None and not quarterly_balance.empty:
            bs_data = quarterly_balance
            bs_dates = []
            for d in bs_data.index:
                if hasattr(d, 'quarter'):
                    bs_dates.append(f"Q{d.quarter} '{str(d.year)[2:]}")
                else:
                    bs_dates.append(str(d)[:7])
        else:
            bs_data = balance_sheet
            bs_dates = bs_data.index.strftime('%Y') if hasattr(bs_data.index, 'strftime') else [str(d)[:4] for d in bs_data.index]

        bs_col1, bs_col2 = st.columns([2, 1])

        with bs_col1:
            # Try different column names
            total_assets_col = None
            for col_name in ["Total Assets", "TotalAssets"]:
                if col_name in bs_data.columns:
                    total_assets_col = col_name
                    break

            total_liabilities_col = None
            for col_name in ["Total Liabilities Net Minority Interest", "Total Liab", "TotalLiabilitiesNetMinorityInterest", "Total Liabilities"]:
                if col_name in bs_data.columns:
                    total_liabilities_col = col_name
                    break

            total_equity_col = None
            for col_name in ["Total Equity Gross Minority Interest", "Stockholders Equity", "StockholdersEquity", "Total Stockholders Equity", "Total Equity"]:
                if col_name in bs_data.columns:
                    total_equity_col = col_name
                    break

            # Calculate debt ratio for line overlay
            debt_ratios = []
            if total_assets_col and total_liabilities_col:
                for i in range(len(bs_data)):
                    assets = bs_data[total_assets_col].iloc[i]
                    liab = bs_data[total_liabilities_col].iloc[i]
                    debt_ratios.append((liab / assets * 100) if assets else 0)

            bs_fig = make_subplots(specs=[[{"secondary_y": True}]])

            if total_assets_col:
                bs_fig.add_trace(go.Bar(
                    x=list(bs_dates),
                    y=(bs_data[total_assets_col] / 1e9).tolist(),
                    name="Total Assets",
                    marker_color="#3B82F6",
                    width=0.25,
                    offset=-0.28,
                ), secondary_y=False)

            if total_liabilities_col:
                bs_fig.add_trace(go.Bar(
                    x=list(bs_dates),
                    y=(bs_data[total_liabilities_col] / 1e9).tolist(),
                    name="Liabilities",
                    marker_color="#F43F5E",
                    width=0.25,
                    offset=0,
                ), secondary_y=False)

            if total_equity_col:
                bs_fig.add_trace(go.Bar(
                    x=list(bs_dates),
                    y=(bs_data[total_equity_col] / 1e9).tolist(),
                    name="Equity",
                    marker_color="#22D3D8",
                    width=0.25,
                    offset=0.28,
                ), secondary_y=False)

            # Debt Ratio line - Orange
            if debt_ratios:
                bs_fig.add_trace(go.Scatter(
                    x=list(bs_dates),
                    y=debt_ratios,
                    name="Debt Ratio %",
                    mode='lines+markers',
                    line=dict(color="#F59E0B", width=2.5),
                    marker=dict(size=8, color="#F59E0B", symbol='circle', line=dict(width=2, color='white')),
                ), secondary_y=True)

            bs_fig.update_layout(
                height=380,
                margin=dict(l=10, r=10, t=20, b=40),
                font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif"),
                plot_bgcolor='white',
                paper_bgcolor='white',
                barmode='group',
                bargap=0.3,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(color=CHART_FONT_COLOR, size=11)
                ),
                hovermode="x unified"
            )

            bs_fig.update_xaxes(
                tickfont=dict(color=CHART_AXIS_COLOR, size=11),
                showgrid=False,
                showline=True,
                linecolor='#E5E7EB'
            )
            bs_fig.update_yaxes(
                tickfont=dict(color=CHART_AXIS_COLOR),
                gridcolor='#F3F4F6',
                showline=False,
                ticksuffix=" B",
                secondary_y=False
            )
            bs_fig.update_yaxes(
                tickfont=dict(color="#F59E0B"),
                showgrid=False,
                ticksuffix="%",
                secondary_y=True
            )

            st.plotly_chart(bs_fig, use_container_width=True)

        with bs_col2:
            st.markdown("**Latest Balance Sheet:**")

            if total_assets_col and len(balance_sheet) > 0:
                latest_assets = balance_sheet[total_assets_col].iloc[-1]
                st.markdown(f"**Total Assets:** {format_large_number(latest_assets)}")

            if total_liabilities_col and len(balance_sheet) > 0:
                latest_liab = balance_sheet[total_liabilities_col].iloc[-1]
                st.markdown(f"**Total Liabilities:** {format_large_number(latest_liab)}")

            if total_equity_col and len(balance_sheet) > 0:
                latest_equity = balance_sheet[total_equity_col].iloc[-1]
                st.markdown(f"**Equity:** {format_large_number(latest_equity)}")

            st.markdown("---")

            # Calculate key ratios
            if total_assets_col and total_liabilities_col and len(balance_sheet) > 0:
                debt_ratio = balance_sheet[total_liabilities_col].iloc[-1] / balance_sheet[total_assets_col].iloc[-1] * 100 if balance_sheet[total_assets_col].iloc[-1] else 0
                dr_status = "success" if debt_ratio < 50 else "warning" if debt_ratio < 70 else "danger"
                st.markdown(render_compact_card("Debt Ratio", f"{debt_ratio:.1f}%", "Liabilities / Assets", dr_status), unsafe_allow_html=True)

        # Dynamic Interpretation for Balance Sheet
        if total_assets_col and total_liabilities_col and total_equity_col and len(balance_sheet) >= 2:
            latest_assets = balance_sheet[total_assets_col].iloc[-1]
            prev_assets = balance_sheet[total_assets_col].iloc[-2]
            assets_growth = ((latest_assets - prev_assets) / abs(prev_assets) * 100) if prev_assets else 0

            latest_equity = balance_sheet[total_equity_col].iloc[-1]
            prev_equity = balance_sheet[total_equity_col].iloc[-2]
            equity_growth = ((latest_equity - prev_equity) / abs(prev_equity) * 100) if prev_equity else 0

            debt_ratio = balance_sheet[total_liabilities_col].iloc[-1] / latest_assets * 100 if latest_assets else 0
            leverage_level = "conservative" if debt_ratio < 40 else "moderate" if debt_ratio < 60 else "aggressive" if debt_ratio < 80 else "highly leveraged"

            interp = f"**Interpretation:** Total assets {format_large_number(latest_assets)} ({assets_growth:+.1f}% YoY) with a {leverage_level} debt ratio of {debt_ratio:.1f}%. "
            interp += f"Shareholder equity {'grew' if equity_growth > 0 else 'declined'} by {abs(equity_growth):.1f}% to {format_large_number(latest_equity)}. "

            if debt_ratio < 50 and equity_growth > 0:
                interp += "Strong balance sheet with healthy equity growth and manageable debt levels."
                st.success(interp)
            elif debt_ratio > 70:
                interp += "High leverage increases financial risk - monitor debt servicing capacity."
                st.warning(interp)
            elif equity_growth < -10:
                interp += "Declining equity may indicate losses or significant shareholder distributions."
                st.warning(interp)
            else:
                interp += "Balance sheet structure is reasonable for most operating conditions."
                st.info(interp)

    else:
        st.info("Balance sheet data not available for this stock.")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 4. DEBT & CASH POSITION
    # -------------------------------------------------------------------------
    debt_header_col1, debt_header_col2 = st.columns([3, 1])
    with debt_header_col1:
        st.markdown("#### Debt & Cash Position")
    with debt_header_col2:
        debt_view_mode = st.radio("", ["Annual", "Quarterly"], horizontal=True, key="debt_view_mode", label_visibility="collapsed")

    if balance_sheet is not None and not balance_sheet.empty:
        # Choose data source based on view mode
        if debt_view_mode == "Quarterly" and quarterly_balance is not None and not quarterly_balance.empty:
            debt_data = quarterly_balance
            debt_dates = []
            for d in debt_data.index:
                if hasattr(d, 'quarter'):
                    debt_dates.append(f"Q{d.quarter} '{str(d.year)[2:]}")
                else:
                    debt_dates.append(str(d)[:7])
        else:
            debt_data = balance_sheet
            debt_dates = debt_data.index.strftime('%Y') if hasattr(debt_data.index, 'strftime') else [str(d)[:4] for d in debt_data.index]

        debt_col1, debt_col2 = st.columns([2, 1])

        with debt_col1:
            # Try different column names for debt and cash
            total_debt_col = None
            for col_name in ["Total Debt", "TotalDebt", "Long Term Debt", "LongTermDebt"]:
                if col_name in debt_data.columns:
                    total_debt_col = col_name
                    break

            cash_col = None
            for col_name in ["Cash And Cash Equivalents", "CashAndCashEquivalents", "Cash", "Cash And Short Term Investments"]:
                if col_name in debt_data.columns:
                    cash_col = col_name
                    break

            current_assets_col = None
            for col_name in ["Current Assets", "CurrentAssets", "Total Current Assets"]:
                if col_name in debt_data.columns:
                    current_assets_col = col_name
                    break

            current_liab_col = None
            for col_name in ["Current Liabilities", "CurrentLiabilities", "Total Current Liabilities"]:
                if col_name in debt_data.columns:
                    current_liab_col = col_name
                    break

            # Calculate net debt for line overlay
            net_debt_values = []
            if total_debt_col and cash_col:
                for i in range(len(debt_data)):
                    debt_val = debt_data[total_debt_col].iloc[i] if total_debt_col in debt_data.columns else 0
                    cash_val = debt_data[cash_col].iloc[i] if cash_col in debt_data.columns else 0
                    net_debt_values.append((debt_val - cash_val) / 1e9)

            debt_fig = make_subplots(specs=[[{"secondary_y": True}]])

            if total_debt_col:
                debt_fig.add_trace(go.Bar(
                    x=list(debt_dates),
                    y=(debt_data[total_debt_col] / 1e9).tolist(),
                    name="Total Debt",
                    marker_color="#3B82F6",
                    width=0.35,
                    offset=-0.2,
                ), secondary_y=False)

            if cash_col:
                debt_fig.add_trace(go.Bar(
                    x=list(debt_dates),
                    y=(debt_data[cash_col] / 1e9).tolist(),
                    name="Cash",
                    marker_color="#22D3D8",
                    width=0.35,
                    offset=0.2,
                ), secondary_y=False)

            # Net Debt line - Orange
            if net_debt_values:
                debt_fig.add_trace(go.Scatter(
                    x=list(debt_dates),
                    y=net_debt_values,
                    name="Net Debt",
                    mode='lines+markers',
                    line=dict(color="#F59E0B", width=2.5),
                    marker=dict(size=8, color="#F59E0B", symbol='circle', line=dict(width=2, color='white')),
                ), secondary_y=False)

            debt_fig.update_layout(
                height=380,
                margin=dict(l=10, r=10, t=20, b=40),
                font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif"),
                plot_bgcolor='white',
                paper_bgcolor='white',
                barmode='group',
                bargap=0.3,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(color=CHART_FONT_COLOR, size=11)
                ),
                hovermode="x unified"
            )

            debt_fig.update_xaxes(
                tickfont=dict(color=CHART_AXIS_COLOR, size=11),
                showgrid=False,
                showline=True,
                linecolor='#E5E7EB'
            )
            debt_fig.update_yaxes(
                tickfont=dict(color=CHART_AXIS_COLOR),
                gridcolor='#F3F4F6',
                showline=False,
                ticksuffix=" B",
                secondary_y=False
            )

            st.plotly_chart(debt_fig, use_container_width=True)

        with debt_col2:
            st.markdown("**Financial Health:**")

            if total_debt_col and len(balance_sheet) > 0:
                latest_debt = balance_sheet[total_debt_col].iloc[-1]
                st.markdown(f"**Total Debt:** {format_large_number(latest_debt)}")

            if cash_col and len(balance_sheet) > 0:
                latest_cash = balance_sheet[cash_col].iloc[-1]
                st.markdown(f"**Cash:** {format_large_number(latest_cash)}")

            if total_debt_col and cash_col and len(balance_sheet) > 0:
                net_debt_val = balance_sheet[total_debt_col].iloc[-1] - balance_sheet[cash_col].iloc[-1]
                nd_status = "success" if net_debt_val < 0 else "warning" if net_debt_val < balance_sheet[cash_col].iloc[-1] else "danger"
                st.markdown(render_compact_card("Net Debt", format_large_number(net_debt_val), "Debt minus Cash", nd_status), unsafe_allow_html=True)

            st.markdown("---")

            # Current Ratio
            if current_assets_col and current_liab_col and len(balance_sheet) > 0:
                current_ratio = balance_sheet[current_assets_col].iloc[-1] / balance_sheet[current_liab_col].iloc[-1] if balance_sheet[current_liab_col].iloc[-1] else 0
                cr_status = "success" if current_ratio > 1.5 else "warning" if current_ratio > 1 else "danger"
                st.markdown(render_compact_card("Current Ratio", f"{current_ratio:.2f}", "Current Assets / Current Liabilities", cr_status), unsafe_allow_html=True)

        # Dynamic Interpretation for Debt & Cash
        if total_debt_col and cash_col and len(balance_sheet) >= 2:
            latest_debt = balance_sheet[total_debt_col].iloc[-1]
            latest_cash = balance_sheet[cash_col].iloc[-1]
            net_debt = latest_debt - latest_cash

            prev_debt = balance_sheet[total_debt_col].iloc[-2]
            prev_cash = balance_sheet[cash_col].iloc[-2]
            prev_net_debt = prev_debt - prev_cash

            debt_change = ((latest_debt - prev_debt) / abs(prev_debt) * 100) if prev_debt else 0
            cash_change = ((latest_cash - prev_cash) / abs(prev_cash) * 100) if prev_cash else 0

            liquidity = "net cash position" if net_debt < 0 else "moderate net debt" if net_debt < latest_cash else "significant net debt"

            interp = f"**Interpretation:** The company has a {liquidity} of {format_large_number(abs(net_debt))}. "
            interp += f"Debt {'increased' if debt_change > 0 else 'decreased'} {abs(debt_change):.1f}% while cash {'grew' if cash_change > 0 else 'declined'} {abs(cash_change):.1f}% YoY. "

            if net_debt < 0:
                interp += "Net cash position provides financial flexibility and a cushion against economic downturns."
                st.success(interp)
            elif cash_change > 0 and debt_change < 0:
                interp += "Improving financial health with deleveraging and cash accumulation."
                st.success(interp)
            elif debt_change > 20:
                interp += "Significant debt increase - evaluate if it's funding growth or covering operational shortfalls."
                st.warning(interp)
            elif cash_change < -20:
                interp += "Sharp cash decline warrants attention - check for large investments, acquisitions, or operational challenges."
                st.warning(interp)
            else:
                interp += "Liquidity position is stable and manageable."
                st.info(interp)

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 5. CASH FLOW ANALYSIS
    # -------------------------------------------------------------------------
    cf_header_col1, cf_header_col2 = st.columns([3, 1])
    with cf_header_col1:
        st.markdown("#### Cash Flow Analysis")
    with cf_header_col2:
        cf_view_mode = st.radio("", ["Annual", "Quarterly"], horizontal=True, key="cf_view_mode", label_visibility="collapsed")

    # Get quarterly cashflow data
    quarterly_cashflow = financials.get("quarterly_cashflow") if financials else None

    if cashflow is not None and not cashflow.empty:
        # Choose data source based on view mode
        if cf_view_mode == "Quarterly" and quarterly_cashflow is not None and not quarterly_cashflow.empty:
            cf_data = quarterly_cashflow
            cf_dates = []
            for d in cf_data.index:
                if hasattr(d, 'quarter'):
                    cf_dates.append(f"Q{d.quarter} '{str(d.year)[2:]}")
                else:
                    cf_dates.append(str(d)[:7])
        else:
            cf_data = cashflow
            cf_dates = cf_data.index.strftime('%Y') if hasattr(cf_data.index, 'strftime') else [str(d)[:4] for d in cf_data.index]

        cf_col1, cf_col2 = st.columns([2, 1])

        with cf_col1:
            # Try different column names
            operating_cf_col = None
            for col_name in ["Operating Cash Flow", "OperatingCashFlow", "Cash Flow From Continuing Operating Activities", "Total Cash From Operating Activities"]:
                if col_name in cf_data.columns:
                    operating_cf_col = col_name
                    break

            investing_cf_col = None
            for col_name in ["Investing Cash Flow", "InvestingCashFlow", "Cash Flow From Continuing Investing Activities", "Total Cashflows From Investing Activities"]:
                if col_name in cf_data.columns:
                    investing_cf_col = col_name
                    break

            capex_col = None
            for col_name in ["Capital Expenditure", "CapitalExpenditure", "Capital Expenditures"]:
                if col_name in cf_data.columns:
                    capex_col = col_name
                    break

            # Calculate FCF for line overlay
            fcf_values = []
            if operating_cf_col and capex_col:
                for i in range(len(cf_data)):
                    ocf = cf_data[operating_cf_col].iloc[i] if operating_cf_col in cf_data.columns else 0
                    capex = cf_data[capex_col].iloc[i] if capex_col in cf_data.columns else 0
                    fcf_values.append((ocf + capex) / 1e9)

            cf_fig = make_subplots(specs=[[{"secondary_y": True}]])

            if operating_cf_col:
                cf_fig.add_trace(go.Bar(
                    x=list(cf_dates),
                    y=(cf_data[operating_cf_col] / 1e9).tolist(),
                    name="Operating CF",
                    marker_color="#3B82F6",
                    width=0.35,
                    offset=-0.2,
                ), secondary_y=False)

            if investing_cf_col:
                cf_fig.add_trace(go.Bar(
                    x=list(cf_dates),
                    y=(cf_data[investing_cf_col] / 1e9).tolist(),
                    name="Investing CF",
                    marker_color="#22D3D8",
                    width=0.35,
                    offset=0.2,
                ), secondary_y=False)

            # Free Cash Flow line - Orange
            if fcf_values:
                cf_fig.add_trace(go.Scatter(
                    x=list(cf_dates),
                    y=fcf_values,
                    name="Free Cash Flow",
                    mode='lines+markers',
                    line=dict(color="#F59E0B", width=2.5),
                    marker=dict(size=8, color="#F59E0B", symbol='circle', line=dict(width=2, color='white')),
                ), secondary_y=False)

            cf_fig.add_hline(y=0, line=dict(color="#9CA3AF", dash="dot", width=1))

            cf_fig.update_layout(
                height=380,
                margin=dict(l=10, r=10, t=20, b=40),
                font=dict(color=CHART_FONT_COLOR, family="Source Sans Pro, Arial, sans-serif"),
                plot_bgcolor='white',
                paper_bgcolor='white',
                barmode='group',
                bargap=0.3,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(color=CHART_FONT_COLOR, size=11)
                ),
                hovermode="x unified"
            )

            cf_fig.update_xaxes(
                tickfont=dict(color=CHART_AXIS_COLOR, size=11),
                showgrid=False,
                showline=True,
                linecolor='#E5E7EB'
            )
            cf_fig.update_yaxes(
                tickfont=dict(color=CHART_AXIS_COLOR),
                gridcolor='#F3F4F6',
                showline=False,
                ticksuffix=" B",
                secondary_y=False
            )

            st.plotly_chart(cf_fig, use_container_width=True)

        with cf_col2:
            st.markdown("**Latest Cash Flows:**")

            if operating_cf_col and len(cashflow) > 0:
                latest_ocf = cashflow[operating_cf_col].iloc[-1]
                ocf_status = "success" if latest_ocf > 0 else "danger"
                st.markdown(f"**Operating CF:** {format_large_number(latest_ocf)}")

            if capex_col and len(cashflow) > 0:
                latest_capex = cashflow[capex_col].iloc[-1]
                st.markdown(f"**CapEx:** {format_large_number(latest_capex)}")

            if operating_cf_col and capex_col and len(cashflow) > 0:
                fcf_val = cashflow[operating_cf_col].iloc[-1] + cashflow[capex_col].iloc[-1]
                fcf_status = "success" if fcf_val > 0 else "danger"
                st.markdown(render_compact_card("Free Cash Flow", format_large_number(fcf_val), "Operating CF + CapEx", fcf_status), unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("**Cash Flow Quality:**")

            # FCF Margin
            if operating_cf_col and capex_col and income_stmt is not None and revenue_col and len(cashflow) > 0:
                fcf_val = cashflow[operating_cf_col].iloc[-1] + cashflow[capex_col].iloc[-1]
                latest_rev = income_stmt[revenue_col].iloc[-1] if len(income_stmt) > 0 else 0
                if latest_rev:
                    fcf_margin = fcf_val / latest_rev * 100
                    fcf_m_status = "success" if fcf_margin > 15 else "warning" if fcf_margin > 5 else "danger"
                    st.markdown(render_compact_card("FCF Margin", f"{fcf_margin:.1f}%", "Free Cash Flow / Revenue", fcf_m_status), unsafe_allow_html=True)

        # Dynamic Interpretation for Cash Flow
        if operating_cf_col and capex_col and len(cashflow) >= 2:
            latest_ocf = cashflow[operating_cf_col].iloc[-1]
            prev_ocf = cashflow[operating_cf_col].iloc[-2]
            ocf_growth = ((latest_ocf - prev_ocf) / abs(prev_ocf) * 100) if prev_ocf else 0

            fcf_val = latest_ocf + cashflow[capex_col].iloc[-1]
            prev_fcf = prev_ocf + cashflow[capex_col].iloc[-2]
            fcf_growth = ((fcf_val - prev_fcf) / abs(prev_fcf) * 100) if prev_fcf else 0

            cash_quality = "strong" if latest_ocf > 0 and fcf_val > 0 else "mixed" if latest_ocf > 0 else "weak"

            interp = f"**Interpretation:** Operating cash flow of {format_large_number(latest_ocf)} ({ocf_growth:+.1f}% YoY) indicates {cash_quality} cash generation. "
            interp += f"Free cash flow is {format_large_number(fcf_val)} ({fcf_growth:+.1f}% YoY). "

            if latest_ocf > 0 and fcf_val > 0:
                if fcf_growth > 10:
                    interp += "Growing free cash flow demonstrates improving cash conversion and supports dividends, buybacks, or reinvestment."
                    st.success(interp)
                else:
                    interp += "Positive cash flows support ongoing operations and shareholder returns."
                    st.success(interp)
            elif latest_ocf > 0 and fcf_val < 0:
                interp += "Negative FCF despite positive operating CF suggests heavy capital investment - check if it's growth-related."
                st.warning(interp)
            elif latest_ocf < 0:
                interp += "Negative operating cash flow is a red flag - the core business is consuming rather than generating cash."
                st.error(interp)
            else:
                interp += "Cash flow trends require monitoring for sustainability."
                st.info(interp)

    else:
        st.info("Cash flow data not available for this stock.")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 6. VALUATION MULTIPLES HISTORY
    # -------------------------------------------------------------------------
    st.markdown("#### Valuation History")
    st.caption("Historical P/E and other valuation metrics based on price history.")

    # Calculate historical P/E using price data and latest earnings
    eps = info.get("trailingEps")
    if eps and eps > 0 and not price_data.empty:
        val_hist_col1, val_hist_col2 = st.columns([2, 1])

        with val_hist_col1:
            val_hist_fig = go.Figure()

            # Use last 2 years of price data
            hist_data = price_data.tail(504)  # ~2 years of trading days

            # Calculate historical P/E (simplified - using current EPS)
            hist_pe = hist_data["Close"] / eps

            val_hist_fig.add_trace(go.Scatter(
                x=hist_data["Date"],
                y=hist_pe,
                name="P/E Ratio",
                line=dict(color="#0EA5E9", width=2),
                fill='tozeroy',
                fillcolor='rgba(14, 165, 233, 0.1)'
            ))

            # Add reference lines
            avg_pe = hist_pe.mean()
            val_hist_fig.add_hline(y=avg_pe, line=dict(color="#F59E0B", dash="dash", width=1),
                                  annotation_text=f"Avg: {avg_pe:.1f}", annotation_position="right")

            val_hist_fig.update_layout(
                title="Historical P/E Ratio (2 Years)",
                height=300,
                margin=dict(l=0, r=0, t=40, b=0),
                xaxis_title="",
                yaxis_title="P/E Ratio",
                font=dict(color=CHART_FONT_COLOR),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )
            val_hist_fig.update_xaxes(showgrid=True, gridcolor=CHART_GRID_COLOR, tickfont=dict(color=CHART_AXIS_COLOR))
            val_hist_fig.update_yaxes(showgrid=True, gridcolor=CHART_GRID_COLOR, tickfont=dict(color=CHART_AXIS_COLOR))

            st.plotly_chart(val_hist_fig, use_container_width=True)

        with val_hist_col2:
            st.markdown("**Valuation Stats:**")

            current_pe = price_data["Close"].iloc[-1] / eps
            min_pe = hist_pe.min()
            max_pe = hist_pe.max()
            avg_pe = hist_pe.mean()

            # Current vs average
            pe_vs_avg = (current_pe - avg_pe) / avg_pe * 100
            pe_status = "success" if pe_vs_avg < -10 else "warning" if pe_vs_avg < 10 else "danger"

            st.markdown(render_compact_card("Current P/E", f"{current_pe:.1f}", f"vs Avg: {pe_vs_avg:+.1f}%", pe_status), unsafe_allow_html=True)

            st.markdown(f"**2Y Average:** {avg_pe:.1f}")
            st.markdown(f"**2Y Low:** {min_pe:.1f}")
            st.markdown(f"**2Y High:** {max_pe:.1f}")

            # Percentile
            percentile = (hist_pe <= current_pe).sum() / len(hist_pe) * 100
            pct_status = "success" if percentile < 30 else "warning" if percentile < 70 else "danger"
            st.markdown("---")
            st.markdown(render_compact_card("Percentile", f"{percentile:.0f}%", "Current P/E rank in 2Y history", pct_status), unsafe_allow_html=True)

        # Dynamic Interpretation for Valuation
        valuation_level = "undervalued" if percentile < 25 else "fairly valued" if percentile < 75 else "overvalued"
        pe_quality = "attractive" if current_pe < 15 else "reasonable" if current_pe < 25 else "premium" if current_pe < 40 else "expensive"

        interp = f"**Interpretation:** At a P/E of {current_pe:.1f}x, the stock appears {valuation_level} relative to its 2-year history (sitting at the {percentile:.0f}th percentile). "
        interp += f"The current valuation is {pe_quality} in absolute terms. "

        if percentile < 25 and current_pe < 20:
            interp += "This may represent a buying opportunity if fundamentals remain intact and there's no structural reason for the discount."
            st.success(interp)
        elif percentile > 75 and current_pe > 30:
            interp += "Elevated valuation suggests high growth expectations are priced in - any disappointment could lead to multiple compression."
            st.warning(interp)
        elif percentile > 90:
            interp += "Near historical highs - exercise caution unless strong catalysts justify the premium."
            st.warning(interp)
        elif percentile < 10:
            interp += "Near historical lows - investigate whether this reflects temporary pessimism or fundamental deterioration."
            st.info(interp)
        else:
            interp += "Valuation is within normal historical range, suggesting fair pricing based on recent patterns."
            st.info(interp)

    else:
        st.info("Insufficient data to calculate historical valuation metrics.")

    with st.expander("📖 Understanding Financial Statements"):
        st.markdown("""
        **Income Statement** shows profitability over time:
        - **Revenue:** Total sales/income generated
        - **Gross Profit:** Revenue minus cost of goods sold
        - **Operating Income:** Profit from core operations
        - **Net Income:** Bottom-line profit after all expenses

        **Balance Sheet** shows financial position at a point in time:
        - **Assets:** What the company owns (cash, inventory, property)
        - **Liabilities:** What the company owes (debt, payables)
        - **Equity:** Net worth (Assets - Liabilities)

        **Cash Flow Statement** shows actual cash movements:
        - **Operating CF:** Cash from core business operations
        - **Investing CF:** Cash used for investments (usually negative)
        - **Financing CF:** Cash from debt/equity transactions
        - **Free Cash Flow:** Operating CF - Capital Expenditures

        **Key Ratios:**
        - **Debt Ratio:** Liabilities/Assets (lower is safer)
        - **Current Ratio:** Current Assets/Current Liabilities (>1.5 is healthy)
        - **FCF Margin:** Free Cash Flow/Revenue (higher is better)
        """)

with news_tab:
    st.subheader("Recent News")
    st.caption("Latest headlines from Finnhub. Read articles to form your own opinion on sentiment.")

    news_items = load_finnhub_news(selected)
    if not news_items:
        st.info("No recent news available for this ticker.")
    else:
        # Count sentiment
        sentiments = {"Positive": 0, "Negative": 0, "Neutral": 0}
        for item in news_items[:15]:
            sentiment = classify_headline_sentiment(item.get("headline", ""))
            sentiments[sentiment] += 1

        # Display sentiment summary
        total = sum(sentiments.values())
        if total > 0:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Positive", sentiments["Positive"], delta=None)
            with col2:
                st.metric("Neutral", sentiments["Neutral"], delta=None)
            with col3:
                st.metric("Negative", sentiments["Negative"], delta=None)
            st.markdown("---")

        # Display news items
        for item in news_items[:15]:
            headline = item.get("headline", "Untitled")
            source = item.get("source", "Unknown")
            url = item.get("url", "#")
            timestamp = item.get("datetime")
            summary = item.get("summary", "")

            when = dt.datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M") if timestamp else "N/A"
            sentiment = classify_headline_sentiment(headline)
            sentiment_icon = {"Positive": "🟢", "Negative": "🔴", "Neutral": "⚪"}.get(sentiment, "⚪")

            st.markdown(f"{sentiment_icon} **[{headline}]({url})**")
            if summary:
                st.caption(summary[:200] + "..." if len(summary) > 200 else summary)
            st.caption(f"{source} · {when}")
            st.markdown("---")

with risk_tab:
    st.subheader("Risk Outlook")
    st.caption("Risk assessment based on volatility, drawdown, and technical indicators.")

    # =========================================================================
    # RISK SCORE BREAKDOWN
    # =========================================================================
    st.markdown("### Risk Score")

    risk_score_status = "success" if risk_score >= 60 else "warning" if risk_score >= 40 else "danger"

    risk_score_col1, risk_score_col2 = st.columns([1, 2])

    with risk_score_col1:
        risk_score_tip = f"Risk Score of {risk_score}/100 measures investment safety. Higher scores mean lower risk. Above 60 is low risk, below 40 is high risk."
        st.markdown(render_badge_card("Risk Score", f"{risk_score}/100", "🛡️", risk_score_tip, risk_score_status), unsafe_allow_html=True)

    with risk_score_col2:
        st.markdown("**Score Breakdown:**")

        # Volatility Score (50 max)
        vol_pts = risk_details.get("volatility", 0)
        vol_pct_score = vol_pts / 50 * 100
        vol_60d_val = risk_details.get("vol_60d", 0)
        st.markdown(f"**Volatility** ({vol_pts}/50 pts)")
        st.progress(vol_pct_score / 100)
        if vol_60d_val:
            vol_annualized = vol_60d_val * 100
            if vol_annualized < 20:
                vol_assess = "Very Low - Stable price action, suitable for conservative investors"
            elif vol_annualized < 30:
                vol_assess = "Low - Below average volatility, manageable swings"
            elif vol_annualized < 40:
                vol_assess = "Moderate - Average volatility, standard risk management"
            elif vol_annualized < 50:
                vol_assess = "High - Above average swings, consider position sizing"
            else:
                vol_assess = "Very High - Significant price swings, use caution"
            st.caption(f"60-Day Volatility: {vol_annualized:.1f}% annualized ({vol_assess})")

        # Drawdown Score (50 max)
        dd_pts = risk_details.get("drawdown", 0)
        dd_pct_score = dd_pts / 50 * 100
        max_dd_val = risk_details.get("max_drawdown", 0)
        st.markdown(f"**Drawdown** ({dd_pts}/50 pts)")
        st.progress(dd_pct_score / 100)
        if max_dd_val:
            dd_percent = abs(max_dd_val * 100)
            if dd_percent < 10:
                dd_assess = "Minimal - Very limited downside over past year"
            elif dd_percent < 20:
                dd_assess = "Moderate - Normal correction territory"
            elif dd_percent < 30:
                dd_assess = "Significant - Notable pullback from highs"
            elif dd_percent < 40:
                dd_assess = "Severe - Major decline experienced"
            else:
                dd_assess = "Extreme - Deep drawdown, high risk"
            st.caption(f"Max Drawdown (1Y): -{dd_percent:.1f}% ({dd_assess})")

    st.markdown("---")

    risk_level, risk_color, risk_factors = classify_risk(price_data)

    # Calculate additional risk metrics
    returns = price_data["Close"].pct_change().dropna()
    vol_30d = returns.tail(30).std() * np.sqrt(252) if len(returns) >= 30 else 0
    vol_60d = returns.tail(60).std() * np.sqrt(252) if len(returns) >= 60 else 0

    prices = price_data["Close"].tail(252)
    rolling_max = prices.expanding().max()
    drawdown = (prices - rolling_max) / rolling_max
    max_dd = drawdown.min()
    current_dd = drawdown.iloc[-1]

    # Risk level card
    st.markdown("### Overall Risk Assessment")

    risk_main_col1, risk_main_col2 = st.columns([1, 2])

    risk_tab_tips = {
        "Low": "Low Risk: Volatility is under 30% annualized with no extreme RSI readings. The stock exhibits stable, predictable price movements suitable for conservative portfolios.",
        "Medium": "Medium Risk: Moderate volatility (30-50% annualized) detected. Price swings are noticeable but manageable. Standard risk management practices recommended.",
        "High": "High Risk: Elevated volatility (over 50% annualized) or extreme technical readings. Expect large price swings. Consider smaller positions and strict stop-losses."
    }
    risk_tab_tip = risk_tab_tips.get(risk_level, "Risk level determined by 60-day volatility and RSI extremes.")

    with risk_main_col1:
        risk_emoji = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}.get(risk_level, "⚪")
        risk_tab_status = {"Low": "success", "Medium": "warning", "High": "danger"}.get(risk_level, "neutral")
        st.markdown(render_badge_card("Risk Level", f"{risk_level} Risk", risk_emoji, risk_tab_tip, risk_tab_status), unsafe_allow_html=True)

    with risk_main_col2:
        st.markdown("**Contributing Factors:**")
        for factor in risk_factors:
            st.markdown(f"- {factor}")

    st.markdown("### Volatility Metrics")
    vol_col1, vol_col2, vol_col3 = st.columns(3)

    # Build volatility tooltips
    vol30_pct = vol_30d * 100
    vol30_assess = "very low" if vol30_pct < 15 else "low" if vol30_pct < 25 else "moderate" if vol30_pct < 40 else "high" if vol30_pct < 60 else "very high"
    vol30_tip = f"30-Day Volatility of {vol30_pct:.1f}% (annualized) is {vol30_assess}. This short-term measure shows recent price fluctuations. The S&P 500 typically has 15-20% volatility."

    vol60_pct = vol_60d * 100
    vol60_assess = "very low" if vol60_pct < 15 else "low" if vol60_pct < 25 else "moderate" if vol60_pct < 40 else "high" if vol60_pct < 60 else "very high"
    vol60_tip = f"60-Day Volatility of {vol60_pct:.1f}% (annualized) is {vol60_assess}. This medium-term measure smooths out short-term noise and gives a better sense of typical price swings."

    with vol_col1:
        vol30_status = "success" if vol_30d < 0.25 else "warning" if vol_30d < 0.40 else "danger"
        st.markdown(render_metric_card("30-Day Volatility", f"{vol_30d*100:.1f}%", vol30_tip, vol30_status, "medium"), unsafe_allow_html=True)

    with vol_col2:
        vol60_status = "success" if vol_60d < 0.25 else "warning" if vol_60d < 0.40 else "danger"
        st.markdown(render_metric_card("60-Day Volatility", f"{vol_60d*100:.1f}%", vol60_tip, vol60_status, "medium"), unsafe_allow_html=True)

    with vol_col3:
        atr_val = price_data["ATR"].iloc[-1] if "ATR" in price_data.columns else 0
        atr_pct = (atr_val / price_data["Close"].iloc[-1]) * 100 if atr_val else 0
        atr_status = "success" if atr_pct < 2 else "warning" if atr_pct < 4 else "danger"
        atr_assess = "tight" if atr_pct < 2 else "normal" if atr_pct < 3 else "wide" if atr_pct < 5 else "very wide"
        atr_tip = f"ATR of {atr_pct:.2f}% of price is {atr_assess}. Average True Range measures daily price movement. At ${last_row['Close']:.2f}, expect daily moves of about ${atr_val:.2f}. Useful for setting stop-losses."
        st.markdown(render_metric_card("ATR (% of Price)", f"{atr_pct:.2f}%", atr_tip, atr_status, "medium"), unsafe_allow_html=True)

    st.markdown("### Drawdown Analysis")
    dd_col1, dd_col2 = st.columns(2)

    # Build drawdown tooltips
    max_dd_pct = abs(max_dd * 100)
    max_dd_assess = "minimal" if max_dd_pct < 10 else "moderate" if max_dd_pct < 20 else "significant" if max_dd_pct < 30 else "severe" if max_dd_pct < 50 else "extreme"
    max_dd_tip = f"Max Drawdown of -{max_dd_pct:.1f}% is {max_dd_assess}. This is the largest peak-to-trough decline in the past year. It shows the worst-case loss if you bought at the high."

    curr_dd_pct = abs(current_dd * 100)
    if curr_dd_pct < 1:
        curr_dd_assess = "at or near highs"
    elif curr_dd_pct < 10:
        curr_dd_assess = "minor pullback from highs"
    elif curr_dd_pct < 20:
        curr_dd_assess = "in correction territory"
    else:
        curr_dd_assess = "significantly below recent highs"
    curr_dd_tip = f"Current Drawdown of -{curr_dd_pct:.1f}% means the stock is {curr_dd_assess}. This shows how far below the 52-week high the current price sits."

    with dd_col1:
        max_dd_status = "success" if max_dd > -0.15 else "warning" if max_dd > -0.30 else "danger"
        st.markdown(render_metric_card("Max Drawdown (1Y)", f"{max_dd*100:.1f}%", max_dd_tip, max_dd_status, "medium"), unsafe_allow_html=True)

    with dd_col2:
        curr_dd_status = "success" if current_dd > -0.10 else "warning" if current_dd > -0.20 else "danger"
        st.markdown(render_metric_card("Current Drawdown", f"{current_dd*100:.1f}%", curr_dd_tip, curr_dd_status, "medium"), unsafe_allow_html=True)
