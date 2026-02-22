# =============================================================================
# ARCHIVED: Baseline strategy functions (removed from models.py)
# =============================================================================
# These functions were part of the original Baseline strategy (tech + fund).
# Archived for reference; no longer used in the active dashboard.
# =============================================================================

import pandas as pd


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
