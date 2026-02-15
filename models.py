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


# =============================================================================
# STRATEGY 2: Paper 1 — EMA Crossover + ATV Confirmation + RSI Gate + RL Agent
# =============================================================================

def calculate_volume_score(df):
    """
    Calculate volume score (0-100) based on volume trend alignment and
    relative volume strength (Paper 1: Kadia et al.).
    """
    if df.empty or "Volume" not in df.columns:
        return 0, {"score": 0, "volume_confirms_trend": False, "details": {}}

    details = {}

    # --- Volume trend alignment (0-50) ---
    price_change = 0
    if len(df) >= 10:
        price_change = df["Close"].iloc[-1] - df["Close"].iloc[-10]

    vol_slope = df["Volume_Slope"].iloc[-1] if "Volume_Slope" in df.columns and pd.notna(df["Volume_Slope"].iloc[-1]) else 0
    details["volume_slope"] = vol_slope
    details["price_direction"] = "up" if price_change > 0 else "down"

    volume_confirms = (price_change > 0 and vol_slope > 0) or (price_change < 0 and vol_slope < 0)
    details["volume_confirms_trend"] = volume_confirms

    if volume_confirms:
        alignment_score = 40 + min(10, abs(vol_slope) / 100000)
    elif vol_slope == 0:
        alignment_score = 25
    else:
        alignment_score = 10
    alignment_score = min(50, max(0, alignment_score))
    details["alignment_score"] = alignment_score

    # --- Relative volume strength (0-50) ---
    rel_vol = df["Rel_Volume"].iloc[-1] if "Rel_Volume" in df.columns and pd.notna(df["Rel_Volume"].iloc[-1]) else 1.0
    details["rel_volume"] = rel_vol

    if rel_vol >= 2.0:
        rel_score = 50
    elif rel_vol >= 1.5:
        rel_score = 40
    elif rel_vol >= 1.2:
        rel_score = 35
    elif rel_vol >= 0.8:
        rel_score = 25
    elif rel_vol >= 0.5:
        rel_score = 15
    else:
        rel_score = 5
    details["rel_volume_score"] = rel_score

    total = int(alignment_score + rel_score)
    total = min(100, max(0, total))
    details["total"] = total

    return total, {"score": total, "volume_confirms_trend": volume_confirms, "details": details}


def generate_paper1_signal(df, row_idx=-1):
    """
    Generate Paper 1 signal faithfully: EMA20/50 crossover + ATV slope confirmation + RSI gate.

    Returns:
        signal: "BUY", "SELL", or "HOLD"
        details: dict with crossover_type, atv_confirmed, rsi_gate, etc.
    """
    if df.empty or len(df) < 50:
        return "HOLD", {"reason": "insufficient_data"}

    if row_idx < 0:
        row_idx = len(df) + row_idx

    details = {}

    # 1. Check EMA Cross Signal at row_idx
    ema_cross = df["EMA_Cross_Signal"].iloc[row_idx] if "EMA_Cross_Signal" in df.columns else 0
    details["ema_cross_signal"] = int(ema_cross)

    # 2. Get ATV slope
    atv_slope = df["ATV_Slope"].iloc[row_idx] if "ATV_Slope" in df.columns and pd.notna(df["ATV_Slope"].iloc[row_idx]) else 0
    details["atv_slope"] = atv_slope

    # 3. Get RSI
    rsi = df["RSI"].iloc[row_idx] if "RSI" in df.columns and pd.notna(df["RSI"].iloc[row_idx]) else 50
    details["rsi"] = rsi

    # Determine base signal from EMA crossover
    if ema_cross == 1:
        # Golden cross detected
        details["crossover_type"] = "golden_cross"
        # Confirm with ATV slope > 0
        atv_confirmed = atv_slope > 0
        details["atv_confirmed"] = atv_confirmed
        if atv_confirmed:
            # RSI gate: block BUY if RSI > 70
            if rsi > 70:
                details["rsi_gate"] = "blocked_overbought"
                return "HOLD", details
            else:
                details["rsi_gate"] = "passed"
                return "BUY", details
        else:
            details["rsi_gate"] = "n/a"
            return "HOLD", details

    elif ema_cross == -1:
        # Death cross detected
        details["crossover_type"] = "death_cross"
        # Confirm with ATV slope < 0
        atv_confirmed = atv_slope < 0
        details["atv_confirmed"] = atv_confirmed
        if atv_confirmed:
            # RSI gate: block SELL if RSI < 30
            if rsi < 30:
                details["rsi_gate"] = "blocked_oversold"
                return "HOLD", details
            else:
                details["rsi_gate"] = "passed"
                return "SELL", details
        else:
            details["rsi_gate"] = "n/a"
            return "HOLD", details

    else:
        # No crossover event — check current EMA position for trend bias
        ema20 = df["EMA20"].iloc[row_idx] if "EMA20" in df.columns else None
        ema50 = df["EMA50"].iloc[row_idx] if "EMA50" in df.columns else None
        details["crossover_type"] = "none"
        details["atv_confirmed"] = False
        details["rsi_gate"] = "n/a"

        if ema20 is not None and ema50 is not None and pd.notna(ema20) and pd.notna(ema50):
            details["ema_trend"] = "bullish" if ema20 > ema50 else "bearish"
        else:
            details["ema_trend"] = "neutral"

        return "HOLD", details


def generate_recommendation_paper1(tech_score, fund_score, volume_score, rsi_value,
                                    market_regime, ticker, info, time_horizon="long",
                                    price_data=None, rl_prediction=None):
    """
    Generate recommendation using Paper 1 approach:
    EMA crossover + ATV confirmation + RSI gate, with optional RL agent override.
    """
    # Get Paper 1 rule-based signal
    paper1_signal = "HOLD"
    paper1_details = {}
    if price_data is not None and not price_data.empty:
        paper1_signal, paper1_details = generate_paper1_signal(price_data)

    # Determine recommendation from rule-based signal
    recommendation = paper1_signal
    confidence = 50

    # If no crossover event, fall back to composite scoring
    if paper1_details.get("crossover_type") == "none":
        # Fallback composite: tech + volume weighted
        if market_regime == "Bull":
            base_weights = {"technical": 0.70, "volume": 0.30}
        elif market_regime == "Bear":
            base_weights = {"technical": 0.60, "volume": 0.40}
        elif market_regime == "High-Volatility":
            base_weights = {"technical": 0.55, "volume": 0.45}
        else:
            base_weights = {"technical": 0.65, "volume": 0.35}

        if time_horizon == "short":
            weights = {
                "technical": min(0.80, base_weights["technical"] + 0.10),
                "volume": max(0.20, base_weights["volume"] - 0.10),
            }
        else:
            weights = {
                "technical": max(0.50, base_weights["technical"] - 0.05),
                "volume": min(0.50, base_weights["volume"] + 0.05),
            }

        w_total = sum(weights.values())
        weights = {k: v / w_total for k, v in weights.items()}

        composite = (
            tech_score * weights["technical"] +
            volume_score * weights["volume"]
        )

        if composite >= 65:
            recommendation = "BUY"
        elif composite >= 45:
            recommendation = "HOLD"
        else:
            recommendation = "SELL"

        # RSI gate on fallback
        if recommendation == "BUY" and rsi_value is not None and rsi_value > 70:
            recommendation = "HOLD"
            paper1_details["rsi_gate"] = "blocked_overbought"
        elif recommendation == "SELL" and rsi_value is not None and rsi_value < 30:
            recommendation = "HOLD"
            paper1_details["rsi_gate"] = "blocked_oversold"
    else:
        # Crossover-based signal: use simpler weights for composite display
        weights = {"technical": 0.50, "volume": 0.50}
        composite = (tech_score * 0.50 + volume_score * 0.50)

    # RL agent integration
    rl_agrees = None
    if rl_prediction is not None:
        rl_action_map = {0: "BUY", 1: "SELL", 2: "HOLD"}
        rl_signal = rl_action_map.get(rl_prediction, "HOLD")
        paper1_details["rl_signal"] = rl_signal
        rl_agrees = (rl_signal == recommendation)
        paper1_details["rl_agrees"] = rl_agrees

        if not rl_agrees and paper1_details.get("crossover_type") == "none":
            # PPO overrides with lower confidence when no crossover event
            recommendation = rl_signal
            paper1_details["rl_override"] = True

    # Confidence calculation
    if paper1_details.get("crossover_type") in ("golden_cross", "death_cross"):
        if paper1_details.get("atv_confirmed"):
            confidence = 80
            if rl_agrees:
                confidence = 90
            elif rl_agrees is False:
                confidence = 65
        else:
            confidence = 45
    else:
        # Fallback composite confidence
        if composite >= 75 or composite <= 30:
            confidence = min(95, 60 + abs(composite - 50))
        elif composite >= 60 or composite <= 40:
            confidence = min(80, 50 + abs(composite - 50))
        else:
            confidence = max(30, 50 - abs(composite - 50))
    confidence = int(confidence)

    rec_color = {"BUY": "green", "SELL": "red"}.get(recommendation, "orange")

    company_name = info.get("shortName", ticker)
    sector = info.get("sector", "N/A")
    explanation = f"**Strategy: EMA + ATV + RL (Paper 1)**\n\n"
    explanation += "**Approach:** EMA20/50 crossover with ATV slope confirmation and RSI gating.\n\n"

    crossover_type = paper1_details.get("crossover_type", "none")
    if crossover_type == "golden_cross":
        explanation += "**Signal:** Golden Cross (EMA20 crossed above EMA50). "
        if paper1_details.get("atv_confirmed"):
            explanation += "ATV slope confirms rising volume. "
        else:
            explanation += "ATV slope does NOT confirm — signal weakened. "
    elif crossover_type == "death_cross":
        explanation += "**Signal:** Death Cross (EMA20 crossed below EMA50). "
        if paper1_details.get("atv_confirmed"):
            explanation += "ATV slope confirms falling volume. "
        else:
            explanation += "ATV slope does NOT confirm — signal weakened. "
    else:
        ema_trend = paper1_details.get("ema_trend", "neutral")
        explanation += f"**Signal:** No crossover event. EMA trend: {ema_trend}. Using composite fallback. "

    rsi_gate = paper1_details.get("rsi_gate", "n/a")
    if rsi_gate == "blocked_overbought":
        explanation += f"\n\n**RSI Gate:** RSI at {rsi_value:.1f} (overbought) — BUY blocked."
    elif rsi_gate == "blocked_oversold":
        explanation += f"\n\n**RSI Gate:** RSI at {rsi_value:.1f} (oversold) — SELL blocked."

    if rl_prediction is not None:
        rl_signal = paper1_details.get("rl_signal", "N/A")
        explanation += f"\n\n**RL Agent:** PPO predicts {rl_signal}. "
        if rl_agrees:
            explanation += "Agrees with rule-based signal (high confidence)."
        elif paper1_details.get("rl_override"):
            explanation += "Overrides fallback signal (lower confidence)."
        else:
            explanation += "Disagrees with rule-based signal."

    explanation += f"\n\n**Market Context:** {market_regime} regime."
    explanation += f"\n\n**Composite Score:** {composite:.0f}/100"

    return {
        "recommendation": recommendation,
        "rec_color": rec_color,
        "confidence": confidence,
        "composite_score": composite,
        "weights": weights,
        "explanation": explanation,
        "rsi_gate_applied": rsi_gate not in ("n/a", "passed"),
        "rsi_warning": f"RSI at {rsi_value:.1f}" if rsi_gate not in ("n/a", "passed") else "",
        "volume_confirms": volume_score > 50,
        "paper1_details": paper1_details,
    }


# =============================================================================
# STRATEGY 3: Paper 2 — Percentile Scoring + Risk-Profile Weights + Interactions
# =============================================================================

# Paper 2: Risk-profile weights from Figure 12 optimization
# Conservative: heavy on beta + market_cap
# Moderate: PB 0.38, ROE 0.35, Momentum 0.23, Beta 0.04, MV 0.00
# Aggressive: same as moderate (paper shows returns-maximized weights are the same)
RISK_PROFILE_WEIGHTS_P2 = {
    "conservative": {"pb": 0.10, "roe": 0.15, "momentum": 0.10, "beta": 0.35, "market_cap": 0.30},
    "moderate":     {"pb": 0.38, "roe": 0.35, "momentum": 0.23, "beta": 0.04, "market_cap": 0.00},
    "aggressive":   {"pb": 0.38, "roe": 0.35, "momentum": 0.23, "beta": 0.04, "market_cap": 0.00},
}

# Paper 2: Interaction coefficients from Table 2 regression
INTERACTION_COEFFICIENTS = {
    # Pairwise
    ("pb", "roe"): 0.782,
    ("pb", "momentum"): 1.318,
    ("pb", "beta"): 1.387,
    ("roe", "momentum"): 1.021,
    ("roe", "beta"): 1.787,
    ("momentum", "beta"): 1.486,
    ("beta", "market_cap"): 0.922,
    # Cubic
    ("pb", "roe", "momentum"): 5.994,
    ("pb", "roe", "market_cap"): 3.615,
}


def _percentile_rank(value, values, higher_is_better=True):
    """Compute percentile rank (0-100) of value within values list."""
    valid = [v for v in values if v is not None and not pd.isna(v)]
    if not valid or value is None or pd.isna(value):
        return 50
    rank = sum(1 for v in valid if v <= value) / len(valid) * 100
    if not higher_is_better:
        rank = 100 - rank
    return rank


def _get_price_to_book(info, peer_metrics=None):
    """Get P/B ratio with fallback calculation."""
    pb = info.get("priceToBook")
    if pb is not None and not pd.isna(pb):
        return pb, "direct"

    # Fallback: compute from marketCap / (bookValue * sharesOutstanding)
    market_cap = info.get("marketCap")
    book_value = info.get("bookValue")
    shares = info.get("sharesOutstanding")
    if market_cap and book_value and shares and book_value * shares > 0:
        pb = market_cap / (book_value * shares)
        return pb, "computed"

    return None, "unavailable"


def calculate_fundamental_score_paper2(info, peer_metrics=None, risk_profile="moderate",
                                        price_data=None):
    """
    Calculate fundamental score using Paper 2's exact 5 factors:
    1. Small P/B ratio (ascending - lower = higher score)
    2. Large ROE (descending - higher = higher score)
    3. Large monthly return/momentum (descending - higher = higher score)
    4. Small Beta (ascending - lower = higher score)
    5. Large market cap (descending - higher = higher score)

    With interaction terms from Table 2 and risk-profile weights from Figure 12.
    """
    scores = {}
    profile_weights = RISK_PROFILE_WEIGHTS_P2.get(risk_profile, RISK_PROFILE_WEIGHTS_P2["moderate"])

    # Extract factors
    roe = info.get("returnOnEquity")
    beta = info.get("beta")
    market_cap = info.get("marketCap")

    # P/B with fallback
    pb_value, pb_source = _get_price_to_book(info)
    scores["pb_source"] = pb_source

    # Momentum: use monthly return from price_data if available, else revenueGrowth as proxy
    momentum = None
    if price_data is not None and "Monthly_Return" in price_data.columns:
        mr = price_data["Monthly_Return"].iloc[-1]
        if pd.notna(mr):
            momentum = mr
    if momentum is None:
        momentum = info.get("revenueGrowth")  # fallback proxy

    use_percentile = (peer_metrics is not None and not peer_metrics.empty and len(peer_metrics) >= 3)

    # Track which factors are available for degraded mode
    n_factors = 5
    pb_available = pb_value is not None
    if not pb_available:
        n_factors = 4
        scores["pb_unavailable"] = True

    if use_percentile:
        # Factor 1: P/B (ascending = lower is better)
        if pb_available and "priceToBook" in peer_metrics.columns:
            pb_pctile = _percentile_rank(pb_value, peer_metrics["priceToBook"].tolist(), higher_is_better=False)
        elif pb_available:
            pb_pctile = _absolute_pb(pb_value)
        else:
            pb_pctile = 50
        scores["pb_pctile"] = pb_pctile

        # Factor 2: ROE (descending = higher is better)
        roe_pctile = _percentile_rank(roe, peer_metrics["roe"].tolist(), higher_is_better=True) if roe is not None else 50
        scores["roe_pctile"] = roe_pctile

        # Factor 3: Momentum (descending = higher is better)
        if momentum is not None and "rev_growth" in peer_metrics.columns:
            momentum_pctile = _percentile_rank(momentum, peer_metrics["rev_growth"].tolist(), higher_is_better=True)
        elif momentum is not None:
            momentum_pctile = _absolute_momentum(momentum)
        else:
            momentum_pctile = 50
        scores["momentum_pctile"] = momentum_pctile

        # Factor 4: Beta (ascending = lower is better)
        beta_pctile = _percentile_rank(beta, peer_metrics["beta"].tolist(), higher_is_better=False) if beta is not None else 50
        scores["beta_pctile"] = beta_pctile

        # Factor 5: Market Cap (descending = higher is better)
        if market_cap is not None and "marketCap" in peer_metrics.columns:
            mcap_pctile = _percentile_rank(market_cap, peer_metrics["marketCap"].tolist(), higher_is_better=True)
        elif market_cap is not None:
            mcap_pctile = _absolute_mcap(market_cap)
        else:
            mcap_pctile = 50
        scores["market_cap_pctile"] = mcap_pctile
    else:
        # Absolute fallbacks
        pb_pctile = _absolute_pb(pb_value) if pb_available else 50
        scores["pb_pctile"] = pb_pctile
        roe_pctile = _absolute_roe(roe)
        scores["roe_pctile"] = roe_pctile
        momentum_pctile = _absolute_momentum(momentum)
        scores["momentum_pctile"] = momentum_pctile
        beta_pctile = _absolute_beta(beta)
        scores["beta_pctile"] = beta_pctile
        mcap_pctile = _absolute_mcap(market_cap)
        scores["market_cap_pctile"] = mcap_pctile

    # Compute weighted total
    if pb_available:
        total = (
            pb_pctile * profile_weights["pb"] +
            roe_pctile * profile_weights["roe"] +
            momentum_pctile * profile_weights["momentum"] +
            beta_pctile * profile_weights["beta"] +
            mcap_pctile * profile_weights["market_cap"]
        )
    else:
        # Redistribute P/B weight proportionally to other factors
        remaining = {k: v for k, v in profile_weights.items() if k != "pb"}
        r_total = sum(remaining.values())
        if r_total > 0:
            total = (
                roe_pctile * (remaining["roe"] / r_total) +
                momentum_pctile * (remaining["momentum"] / r_total) +
                beta_pctile * (remaining["beta"] / r_total) +
                mcap_pctile * (remaining["market_cap"] / r_total)
            )
        else:
            total = (roe_pctile + momentum_pctile + beta_pctile + mcap_pctile) / 4

    # Interaction terms (from Table 2 regression coefficients)
    interaction_bonus = 0
    if use_percentile:
        # Normalize percentiles to [0, 1]
        norm = {
            "pb": pb_pctile / 100.0,
            "roe": roe_pctile / 100.0,
            "momentum": momentum_pctile / 100.0,
            "beta": beta_pctile / 100.0,
            "market_cap": mcap_pctile / 100.0,
        }

        interaction_details = {}
        for factors, coeff in INTERACTION_COEFFICIENTS.items():
            if not pb_available and "pb" in factors:
                continue
            product = 1.0
            for f in factors:
                product *= norm[f]
            contribution = product * coeff
            interaction_bonus += contribution
            interaction_details["+".join(factors)] = round(contribution, 3)

        scores["interaction_details"] = interaction_details

    scores["interaction_bonus"] = round(interaction_bonus, 2)
    total = min(100, max(0, total + interaction_bonus))
    scores["total"] = total
    scores["risk_profile"] = risk_profile
    scores["used_percentile"] = use_percentile
    scores["n_factors"] = n_factors

    # Backward compatibility aliases
    scores["profitability_pctile"] = roe_pctile
    scores["growth_pctile"] = momentum_pctile
    scores["leverage_pctile"] = beta_pctile
    scores["valuation_pctile"] = pb_pctile

    return total, scores


def _absolute_pb(pb):
    """Absolute P/B score (lower is better)."""
    if pb is None or pd.isna(pb):
        return 50
    if pb < 1:
        return 95
    elif pb < 2:
        return 75
    elif pb < 3:
        return 55
    elif pb < 5:
        return 35
    else:
        return 15


def _absolute_roe(roe):
    """Absolute ROE score (higher is better)."""
    if roe is None or pd.isna(roe):
        return 50
    if roe > 0.25:
        return 95
    elif roe > 0.15:
        return 75
    elif roe > 0.10:
        return 55
    elif roe > 0:
        return 35
    else:
        return 15


def _absolute_momentum(momentum):
    """Absolute momentum score (higher is better)."""
    if momentum is None or pd.isna(momentum):
        return 50
    if momentum > 0.20:
        return 95
    elif momentum > 0.10:
        return 75
    elif momentum > 0.02:
        return 55
    elif momentum > 0:
        return 40
    elif momentum > -0.10:
        return 25
    else:
        return 10


def _absolute_beta(beta):
    """Absolute beta score (lower is better for stability)."""
    if beta is None or pd.isna(beta):
        return 50
    if beta < 0.5:
        return 95
    elif beta < 0.8:
        return 75
    elif beta < 1.0:
        return 60
    elif beta < 1.2:
        return 45
    elif beta < 1.5:
        return 30
    else:
        return 15


def _absolute_mcap(market_cap):
    """Absolute market cap score (higher is better)."""
    if market_cap is None or pd.isna(market_cap):
        return 50
    if market_cap > 200e9:
        return 95
    elif market_cap > 50e9:
        return 75
    elif market_cap > 10e9:
        return 55
    elif market_cap > 2e9:
        return 35
    else:
        return 15


# Keep legacy absolute fallbacks for backward compat
def _absolute_profitability(roe, profit_margin):
    """Absolute profitability score (0-100) fallback."""
    if roe is not None and profit_margin is not None:
        if roe > 0.20 and profit_margin > 0.15:
            return 100
        elif roe > 0.15 and profit_margin > 0.10:
            return 80
        elif roe > 0.10 and profit_margin > 0.05:
            return 60
        elif roe > 0 and profit_margin > 0:
            return 40
        else:
            return 20
    return 50


def _absolute_growth(rev_growth):
    """Absolute growth score (0-100) fallback."""
    if rev_growth is not None:
        if rev_growth > 0.25:
            return 100
        elif rev_growth > 0.15:
            return 80
        elif rev_growth > 0.05:
            return 60
        elif rev_growth > 0:
            return 40
        else:
            return 20
    return 50


def _absolute_leverage(debt_equity):
    """Absolute leverage score (0-100) fallback."""
    if debt_equity is not None:
        if debt_equity < 30:
            return 100
        elif debt_equity < 50:
            return 80
        elif debt_equity < 100:
            return 60
        elif debt_equity < 150:
            return 40
        else:
            return 20
    return 50


def _absolute_valuation(pe, peg):
    """Absolute valuation score (0-100) fallback."""
    if pe is not None and pe > 0:
        if peg is not None and peg > 0:
            if peg < 1:
                return 100
            elif peg < 1.5:
                return 80
            elif peg < 2:
                return 60
            else:
                return 40
        else:
            if pe < 15:
                return 80
            elif pe < 25:
                return 60
            elif pe < 35:
                return 40
            else:
                return 20
    return 50


def generate_recommendation_paper2(tech_score, fund_score, market_regime, ticker, info,
                                    risk_profile="moderate", time_horizon="long"):
    """
    Generate recommendation using Paper 2 approach:
    risk-profile-aware weighting between technicals and fundamentals.
    """
    if risk_profile == "conservative":
        base_tech, base_fund = 0.35, 0.65
    elif risk_profile == "aggressive":
        base_tech, base_fund = 0.60, 0.40
    else:
        base_tech, base_fund = 0.50, 0.50

    if market_regime == "Bull":
        base_tech += 0.05
        base_fund -= 0.05
    elif market_regime == "Bear":
        base_tech -= 0.10
        base_fund += 0.10
    elif market_regime == "High-Volatility":
        base_tech -= 0.05
        base_fund += 0.05

    if time_horizon == "short":
        base_tech += 0.10
        base_fund -= 0.10
    else:
        base_tech -= 0.05
        base_fund += 0.05

    base_tech = max(0.20, min(0.75, base_tech))
    base_fund = max(0.25, min(0.80, base_fund))
    w_total = base_tech + base_fund
    weights = {"technical": base_tech / w_total, "fundamental": base_fund / w_total}

    composite = tech_score * weights["technical"] + fund_score * weights["fundamental"]

    if composite >= 65:
        recommendation = "BUY"
        rec_color = "green"
    elif composite >= 45:
        recommendation = "HOLD"
        rec_color = "orange"
    else:
        recommendation = "SELL"
        rec_color = "red"

    if composite >= 75 or composite <= 30:
        confidence = min(95, 60 + abs(composite - 50))
    elif composite >= 60 or composite <= 40:
        confidence = min(80, 50 + abs(composite - 50))
    else:
        confidence = max(30, 50 - abs(composite - 50))
    confidence = int(confidence)

    company_name = info.get("shortName", ticker)
    sector = info.get("sector", "N/A")
    explanation = f"**Strategy: Optimized Weights (Paper 2)**\n\n"
    explanation += f"**Risk Profile:** {risk_profile.title()}\n\n"
    explanation += f"**Market Context:** {market_regime} regime. "
    explanation += f"\n\n**Stock Analysis ({company_name}, {sector}):** "
    explanation += f"Technical: {tech_score}/100, Fundamental (percentile): {fund_score:.0f}/100. "
    explanation += f"\n\n**Composite Score:** {composite:.0f}/100"

    return {
        "recommendation": recommendation,
        "rec_color": rec_color,
        "confidence": confidence,
        "composite_score": composite,
        "weights": weights,
        "explanation": explanation,
    }


# =============================================================================
# STRATEGY 4: Combined — Best of Both Papers
# =============================================================================

def generate_recommendation_combined(tech_score, fund_score_paper2, volume_score, rsi_value,
                                      market_regime, ticker, info,
                                      risk_profile="moderate", time_horizon="long",
                                      price_data=None):
    """
    Combined strategy: Paper 1 timing (EMA crossover) + Paper 2 quality (factor score).
    - Paper 1 BUY + Paper 2 high score → strong BUY
    - Paper 1 BUY + Paper 2 low score → HOLD
    - Paper 1 SELL + Paper 2 low score → strong SELL
    - Paper 1 SELL + Paper 2 high score → HOLD
    """
    # Get Paper 1 timing signal
    p1_signal = "HOLD"
    p1_details = {}
    if price_data is not None and not price_data.empty:
        p1_signal, p1_details = generate_paper1_signal(price_data)

    # Determine Paper 2 quality tier
    p2_high = fund_score_paper2 >= 60
    p2_low = fund_score_paper2 < 40

    # Combined logic
    if p1_details.get("crossover_type") in ("golden_cross", "death_cross"):
        # Active crossover event — use timing + quality logic
        if p1_signal == "BUY" and p2_high:
            recommendation = "BUY"
            confidence = 85
        elif p1_signal == "BUY" and p2_low:
            recommendation = "HOLD"
            confidence = 50
        elif p1_signal == "BUY":
            recommendation = "BUY"
            confidence = 65
        elif p1_signal == "SELL" and p2_low:
            recommendation = "SELL"
            confidence = 85
        elif p1_signal == "SELL" and p2_high:
            recommendation = "HOLD"
            confidence = 50
        elif p1_signal == "SELL":
            recommendation = "SELL"
            confidence = 65
        else:
            recommendation = "HOLD"
            confidence = 45
    else:
        # No crossover — fall back to weighted composite
        if risk_profile == "conservative":
            base_weights = {"technical": 0.30, "fundamental": 0.55, "volume": 0.15}
        elif risk_profile == "aggressive":
            base_weights = {"technical": 0.50, "fundamental": 0.30, "volume": 0.20}
        else:
            base_weights = {"technical": 0.40, "fundamental": 0.40, "volume": 0.20}

        if market_regime == "Bull":
            base_weights["technical"] += 0.05
            base_weights["fundamental"] -= 0.05
        elif market_regime == "Bear":
            base_weights["technical"] -= 0.10
            base_weights["fundamental"] += 0.10
        elif market_regime == "High-Volatility":
            base_weights["technical"] -= 0.05
            base_weights["fundamental"] += 0.05

        if time_horizon == "short":
            base_weights["technical"] += 0.10
            base_weights["fundamental"] -= 0.10
        else:
            base_weights["technical"] -= 0.05
            base_weights["fundamental"] += 0.05

        w_total = sum(base_weights.values())
        weights = {k: max(0.05, v / w_total) for k, v in base_weights.items()}
        w_total = sum(weights.values())
        weights = {k: v / w_total for k, v in weights.items()}

        composite = (
            tech_score * weights["technical"] +
            fund_score_paper2 * weights["fundamental"] +
            volume_score * weights["volume"]
        )

        if composite >= 65:
            recommendation = "BUY"
        elif composite >= 45:
            recommendation = "HOLD"
        else:
            recommendation = "SELL"

        if composite >= 75 or composite <= 30:
            confidence = min(95, 60 + abs(composite - 50))
        elif composite >= 60 or composite <= 40:
            confidence = min(80, 50 + abs(composite - 50))
        else:
            confidence = max(30, 50 - abs(composite - 50))

    # RSI gate
    rsi_gate_applied = False
    rsi_warning = ""
    if recommendation == "BUY" and rsi_value is not None and rsi_value > 70:
        recommendation = "HOLD"
        rsi_gate_applied = True
        rsi_warning = f"RSI at {rsi_value:.1f} (overbought) - BUY downgraded to HOLD"
    elif recommendation == "SELL" and rsi_value is not None and rsi_value < 30:
        recommendation = "HOLD"
        rsi_gate_applied = True
        rsi_warning = f"RSI at {rsi_value:.1f} (oversold) - SELL downgraded to HOLD"

    confidence = int(confidence)
    if rsi_gate_applied:
        confidence = max(30, confidence - 15)

    rec_color = {"BUY": "green", "SELL": "red"}.get(recommendation, "orange")

    # Compute composite for display
    weights = {"technical": 0.35, "fundamental": 0.40, "volume": 0.25}
    composite = (
        tech_score * weights["technical"] +
        fund_score_paper2 * weights["fundamental"] +
        volume_score * weights["volume"]
    )

    company_name = info.get("shortName", ticker)
    sector = info.get("sector", "N/A")
    explanation = f"**Strategy: Combined (Papers 1 + 2)**\n\n"
    explanation += f"**Risk Profile:** {risk_profile.title()}\n\n"

    crossover_type = p1_details.get("crossover_type", "none")
    if crossover_type != "none":
        explanation += f"**Paper 1 Timing:** {crossover_type.replace('_', ' ').title()} detected. Signal: {p1_signal}. "
        if p1_details.get("atv_confirmed"):
            explanation += "ATV confirmed. "
    else:
        explanation += "**Paper 1 Timing:** No crossover event. Using composite fallback. "

    explanation += f"\n\n**Paper 2 Quality:** Factor score {fund_score_paper2:.0f}/100. "
    explanation += f"{'High quality' if p2_high else 'Low quality' if p2_low else 'Medium quality'}. "

    explanation += f"\n\n**Market Context:** {market_regime} regime. "
    explanation += f"\n\n**Stock Analysis ({company_name}, {sector}):** "
    explanation += f"Technical: {tech_score}/100, Fundamental: {fund_score_paper2:.0f}/100, Volume: {volume_score}/100. "
    if rsi_gate_applied:
        explanation += f"\n\n**RSI Gate Applied:** {rsi_warning}"
    explanation += f"\n\n**Composite Score:** {composite:.0f}/100"

    return {
        "recommendation": recommendation,
        "rec_color": rec_color,
        "confidence": confidence,
        "composite_score": composite,
        "weights": weights,
        "explanation": explanation,
        "rsi_gate_applied": rsi_gate_applied,
        "rsi_warning": rsi_warning,
        "volume_confirms": volume_score > 50,
        "paper1_details": p1_details,
        "paper1_signal": p1_signal,
    }

