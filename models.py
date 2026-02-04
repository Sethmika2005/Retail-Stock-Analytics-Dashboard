# =============================================================================
# MODELS.PY - Scoring algorithms, sentiment analysis, and recommendation engine
# =============================================================================

import numpy as np
import pandas as pd

# =============================================================================
# SENTIMENT ANALYSIS
# =============================================================================

POSITIVE_WORDS = {
    "beat", "beats", "surge", "surges", "soar", "soars", "record",
    "growth", "profit", "upgrade", "bull", "bullish", "strong", "tops",
}

NEGATIVE_WORDS = {
    "miss", "misses", "drop", "drops", "plunge", "plunges", "cut",
    "cuts", "downgrade", "bear", "bearish", "weak", "lawsuit", "decline",
}


def classify_headline_sentiment(title):
    """Classify a headline as Positive, Negative, or Neutral based on keywords."""
    words = set(title.lower().split())
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    if pos > neg:
        return "Positive"
    if neg > pos:
        return "Negative"
    return "Neutral"


# =============================================================================
# RISK CLASSIFICATION
# =============================================================================

def classify_risk(df):
    """Classify overall risk level based on volatility and RSI."""
    returns = df["Close"].pct_change().dropna()
    if returns.empty:
        return "Unknown", "gray", []
    vol = returns.tail(60).std() * np.sqrt(252)
    rsi = df["RSI"].iloc[-1] if "RSI" in df.columns else 50
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
# MARKET REGIME DETECTION
# =============================================================================

def detect_market_regime(sp500_df, vix_df):
    """
    Detect market regime: Bull, Bear, Sideways, or High-Volatility.
    High volatility overrides other regimes.
    """
    if sp500_df.empty or vix_df.empty:
        return "Unknown", "gray", {}

    sp500_df = sp500_df.copy()
    sp500_df["SMA200"] = sp500_df["Close"].rolling(window=200).mean()
    sp500_df["SMA50"] = sp500_df["Close"].rolling(window=50).mean()

    current_price = sp500_df["Close"].iloc[-1]
    sma200 = sp500_df["SMA200"].iloc[-1]
    sma50 = sp500_df["SMA50"].iloc[-1]

    sma200_20d_ago = sp500_df["SMA200"].iloc[-20] if len(sp500_df) >= 20 else sma200
    sma200_slope = (sma200 - sma200_20d_ago) / sma200_20d_ago * 100 if sma200_20d_ago else 0

    current_vix = vix_df["Close"].iloc[-1]
    vix_ma20 = vix_df["Close"].rolling(window=20).mean().iloc[-1]

    price_vs_sma200 = (current_price - sma200) / sma200 * 100 if sma200 else 0
    sma_crossover = (sma50 - sma200) / sma200 * 100 if sma200 else 0

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

    if current_vix > 25 or current_vix > vix_ma20 * 1.3:
        return "High-Volatility", "red", metrics

    if price_vs_sma200 > 2 and sma200_slope > 0 and sma_crossover > 0:
        return "Bull", "green", metrics

    if price_vs_sma200 < -2 and sma200_slope < 0 and sma_crossover < 0:
        return "Bear", "red", metrics

    return "Sideways", "orange", metrics


# =============================================================================
# SCORING MODELS
# =============================================================================

def calculate_technical_score(df):
    """Calculate technical score (0-100) based on trend, RSI, MACD."""
    if df.empty or len(df) < 200:
        return 50, {}

    scores = {}

    current_price = df["Close"].iloc[-1]
    sma50 = df["SMA50"].iloc[-1] if "SMA50" in df.columns else df["Close"].rolling(50).mean().iloc[-1]
    sma200 = df["SMA200"].iloc[-1] if "SMA200" in df.columns else df["Close"].rolling(200).mean().iloc[-1]

    trend_score = 0
    if pd.notna(sma50) and pd.notna(sma200):
        if current_price > sma50 > sma200:
            trend_score = 40
        elif current_price > sma50 and current_price > sma200:
            trend_score = 30
        elif current_price > sma200:
            trend_score = 20
        elif current_price < sma50 < sma200:
            trend_score = 0
        elif current_price < sma50 and current_price < sma200:
            trend_score = 10
        else:
            trend_score = 15
    scores["trend"] = trend_score

    rsi = df["RSI"].iloc[-1] if "RSI" in df.columns else 50
    if pd.notna(rsi):
        if 40 <= rsi <= 60:
            rsi_score = 25
        elif 30 <= rsi < 40:
            rsi_score = 30
        elif 60 < rsi <= 70:
            rsi_score = 20
        elif rsi < 30:
            rsi_score = 25
        elif rsi > 70:
            rsi_score = 10
        else:
            rsi_score = 15
    else:
        rsi_score = 15
    scores["rsi"] = rsi_score

    macd = df["MACD"].iloc[-1] if "MACD" in df.columns else 0
    macd_signal = df["MACD_SIGNAL"].iloc[-1] if "MACD_SIGNAL" in df.columns else 0
    macd_hist = df["MACD_HIST"].iloc[-1] if "MACD_HIST" in df.columns else 0

    macd_score = 15
    if pd.notna(macd) and pd.notna(macd_signal):
        if macd > macd_signal and macd_hist > 0:
            macd_score = 30 if macd > 0 else 25
        elif macd < macd_signal and macd_hist < 0:
            macd_score = 5 if macd < 0 else 10
        else:
            macd_score = 15
    scores["macd"] = macd_score

    total = trend_score + rsi_score + macd_score
    scores["total"] = total

    return total, scores


def calculate_fundamental_score(info):
    """Calculate fundamental score (0-100) based on profitability, growth, leverage, valuation."""
    scores = {}

    roe = info.get("returnOnEquity")
    profit_margin = info.get("profitMargins")

    prof_score = 12
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

    rev_growth = info.get("revenueGrowth")

    growth_score = 12
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

    debt_equity = info.get("debtToEquity")

    leverage_score = 12
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

    pe = info.get("trailingPE")
    peg = info.get("pegRatio")

    val_score = 12
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
    """Calculate risk score (0-100, higher = less risky/better)."""
    if df.empty:
        return 50, {}

    scores = {}
    returns = df["Close"].pct_change().dropna()

    vol_60d = returns.tail(60).std() * np.sqrt(252) if len(returns) >= 60 else returns.std() * np.sqrt(252)

    vol_score = 25
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

    prices = df["Close"].tail(252)
    rolling_max = prices.expanding().max()
    drawdown = (prices - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    dd_score = 25
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


# =============================================================================
# RECOMMENDATION ENGINE
# =============================================================================

def generate_recommendation(tech_score, fund_score, market_regime, ticker, info, time_horizon="long"):
    """
    Generate BUY/HOLD/SELL recommendation with confidence score and explanation.
    Dynamically weight scores based on market regime and time horizon.
    """
    # Base weights adjusted by market regime
    if market_regime == "Bull":
        base_weights = {"technical": 0.60, "fundamental": 0.40}
    elif market_regime == "Bear":
        base_weights = {"technical": 0.35, "fundamental": 0.65}
    elif market_regime == "High-Volatility":
        base_weights = {"technical": 0.40, "fundamental": 0.60}
    else:  # Sideways
        base_weights = {"technical": 0.50, "fundamental": 0.50}

    # Adjust weights based on time horizon
    if time_horizon == "short":
        weights = {
            "technical": min(0.70, base_weights["technical"] + 0.10),
            "fundamental": max(0.30, base_weights["fundamental"] - 0.10),
        }
    else:  # long-term
        weights = {
            "technical": max(0.30, base_weights["technical"] - 0.10),
            "fundamental": min(0.70, base_weights["fundamental"] + 0.10),
        }

    # Calculate weighted composite score
    composite = (
        tech_score * weights["technical"] +
        fund_score * weights["fundamental"]
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

    # Confidence score
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
        explanation += "Fundamentals are strong with solid profitability and reasonable valuation."
    elif fund_score >= 40:
        explanation += "Fundamentals are adequate but not exceptional."
    else:
        explanation += "Fundamental metrics show concerns in profitability, growth, or valuation."

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


def generate_key_drivers(info, tech_score, fund_score, price_data, market_regime):
    """Generate 3 key drivers in plain English."""
    drivers = []

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

    if market_regime in ["Bull"]:
        drivers.append("Favorable market environment supports risk-taking")
    elif market_regime in ["Bear", "High-Volatility"]:
        drivers.append("Challenging market backdrop adds headwinds")
    else:
        drivers.append("Market conditions are neutral - stock-specific factors matter more")

    return drivers[:3]


def generate_key_risk(info, price_data):
    """Generate the single most important risk."""
    risks = []

    if "ATR" in price_data.columns:
        atr_pct = (price_data["ATR"].iloc[-1] / price_data["Close"].iloc[-1]) * 100
        if atr_pct > 3:
            risks.append(f"High volatility ({atr_pct:.1f}% daily range) - position size accordingly")

    pe = info.get("trailingPE")
    if pe and pe > 35:
        risks.append(f"Premium valuation ({pe:.0f}x P/E) leaves little margin for error")

    de = info.get("debtToEquity")
    if de and de > 100:
        risks.append(f"High debt levels ({de:.0f} D/E) increase financial risk")

    if not price_data.empty:
        high = price_data["High"].max()
        current = price_data["Close"].iloc[-1]
        drawdown = (high - current) / high * 100
        if drawdown > 20:
            risks.append(f"Already {drawdown:.0f}% off highs - catching a falling knife risk")

    if not risks:
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
    if market_regime in ["Bull", "RISK-ON", "BULLISH"]:
        bull_case.append("Supportive market environment")
    elif market_regime in ["Bear", "RISK-OFF", "BEARISH"]:
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
        changers.append("Market regime shift to Bear/High-Volatility")
        changers.append("Insider selling or earnings miss")
    elif recommendation == "SELL":
        # What would turn bearish to bullish
        changers.append(f"Price recovery above ${sma50:.2f} (50-day MA)")
        changers.append("Positive earnings surprise or guidance raise")
        changers.append("Market regime shift to Bull")
        changers.append("Valuation becoming attractive on pullback")
    else:  # HOLD
        changers.append(f"Break above ${sma50*1.05:.2f} would turn bullish")
        changers.append(f"Break below ${sma50*0.95:.2f} would turn bearish")
        changers.append("Earnings catalyst could clarify direction")
        changers.append("Sector rotation or market regime change")

    return changers
