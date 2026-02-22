# =============================================================================
# ARCHIVED: Combined strategy function (removed from models.py)
# =============================================================================
# This function was part of the Combined strategy (Paper 1 timing + Paper 2 quality).
# Archived for reference; no longer used in the active dashboard.
# =============================================================================

import numpy as np
import pandas as pd

from models import generate_paper1_signal


def generate_recommendation_combined(tech_score, fund_score_paper2, volume_score, rsi_value,
                                      market_regime, ticker, info,
                                      risk_profile="moderate", time_horizon="long",
                                      price_data=None):
    """
    Combined strategy: Paper 1 timing (EMA crossover) + Paper 2 quality (factor score).
    - Paper 1 BUY + Paper 2 high score -> strong BUY
    - Paper 1 BUY + Paper 2 low score -> HOLD
    - Paper 1 SELL + Paper 2 low score -> strong SELL
    - Paper 1 SELL + Paper 2 high score -> HOLD
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
        # Active crossover event -- use timing + quality logic
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
        # No crossover -- fall back to weighted composite
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
