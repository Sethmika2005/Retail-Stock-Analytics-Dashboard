# =============================================================================
# MODELS.PY - Scoring algorithms, sentiment analysis, and recommendation engine
# =============================================================================

import numpy as np
import pandas as pd

# =============================================================================
# SENTIMENT ANALYSIS
# =============================================================================

POSITIVE_WORDS = {
    # Earnings & performance
    "beat", "beats", "beating", "exceeded", "exceeds", "topped", "tops", "topping",
    "outperform", "outperforms", "outperformed", "outpacing",
    "record", "record-breaking", "all-time",
    # Growth & gains
    "surge", "surges", "surging", "soar", "soars", "soaring",
    "rally", "rallies", "rallying", "rebound", "rebounds", "rebounding",
    "gain", "gains", "gaining", "rise", "rises", "rising", "climbs", "climbing",
    "jump", "jumps", "jumping", "spike", "spikes", "spiking",
    "growth", "growing", "grew", "expand", "expands", "expanding", "expansion",
    "boom", "booming", "breakout", "acceleration", "accelerating",
    # Positive sentiment
    "profit", "profits", "profitable", "profitability",
    "upgrade", "upgrades", "upgraded", "upbeat", "optimistic", "optimism",
    "bull", "bullish", "buy", "overweight", "outperform",
    "strong", "strength", "strengthens", "robust", "solid", "resilient",
    "positive", "favorable", "favourable", "promising", "encouraging",
    "confident", "confidence", "momentum", "tailwind", "tailwinds",
    # Business events
    "innovation", "innovative", "breakthrough", "launch", "launches", "launched",
    "partnership", "acquisition", "deal", "wins", "win", "winning", "won",
    "approval", "approved", "approves", "dividend", "buyback", "repurchase",
    "recovery", "recovering", "recovered", "turnaround",
    "revenue", "sales", "demand", "orders",
    "milestone", "achievement", "success", "successful",
    "raises", "raised", "hikes", "hiking", "boost", "boosts", "boosting",
    "exceeding", "impressive", "stellar", "blockbuster", "blowout",
    "highest", "peak", "upside", "upward",
}

NEGATIVE_WORDS = {
    # Earnings & performance
    "miss", "misses", "missed", "missing", "disappoint", "disappoints", "disappointing",
    "underperform", "underperforms", "underperformed", "underperforming",
    "shortfall", "below", "worse", "worst",
    # Declines & losses
    "drop", "drops", "dropping", "dropped",
    "plunge", "plunges", "plunging", "plunged",
    "fall", "falls", "falling", "fell", "tumble", "tumbles", "tumbling",
    "crash", "crashes", "crashing", "crashed", "collapse", "collapses", "collapsing",
    "sink", "sinks", "sinking", "sank", "slide", "slides", "sliding", "slid",
    "slump", "slumps", "slumping", "decline", "declines", "declining", "declined",
    "loss", "losses", "losing", "lost", "deficit",
    "selloff", "sell-off", "rout", "bloodbath", "wipeout",
    "plummets", "plummeting", "nosedive", "freefall",
    # Negative sentiment
    "cut", "cuts", "cutting", "slash", "slashes", "slashing",
    "downgrade", "downgrades", "downgraded", "sell", "underweight",
    "bear", "bearish", "weak", "weakness", "weakens", "weaker", "weakening",
    "negative", "unfavorable", "unfavourable", "pessimistic", "pessimism",
    "concern", "concerns", "concerned", "worried", "worries", "worry", "fear", "fears",
    "risk", "risks", "risky", "threat", "threatens", "threatening",
    "volatile", "volatility", "uncertainty", "uncertain", "turbulence",
    "headwind", "headwinds", "downturn", "recession", "recessionary",
    # Business events
    "lawsuit", "lawsuits", "sued", "sues", "litigation", "probe", "investigation",
    "fraud", "scandal", "violation", "penalty", "penalties", "fine", "fined", "fines",
    "layoff", "layoffs", "restructuring", "job-cuts", "downsizing",
    "bankruptcy", "insolvent", "default", "defaults", "defaulted",
    "recall", "recalls", "recalled", "warning", "warns", "warned",
    "shutdown", "halt", "halts", "halted", "suspend", "suspends", "suspended",
    "delay", "delays", "delayed", "setback", "obstacle",
    "debt", "leverage", "overvalued", "bubble", "inflated",
    "downside", "downward", "lowest", "bottom", "gutted",
    "failure", "fails", "failed", "struggling", "struggle",
}


def classify_headline_sentiment(title):
    """Classify a headline as Positive, Negative, or Neutral based on keywords."""
    # Clean and tokenize — strip punctuation from each word
    import re
    tokens = set(re.findall(r"[a-z]+(?:-[a-z]+)*", title.lower()))
    pos = len(tokens & POSITIVE_WORDS)
    neg = len(tokens & NEGATIVE_WORDS)
    if pos > neg:
        return "Positive"
    if neg > pos:
        return "Negative"
    return "Neutral"


# =============================================================================
# PIOTROSKI F-SCORE (Piotroski, 2000)
# =============================================================================

def _find_col(df, candidates):
    """Find first matching column name from a list of candidates."""
    if df is None or df.empty:
        return None
    for name in candidates:
        if name in df.columns:
            return name
    return None


def _safe_val(df, col_candidates, year_idx=-1):
    """Safely extract a value from a DataFrame given column candidates and year index."""
    if df is None or df.empty:
        return None
    col = _find_col(df, col_candidates)
    if col is None:
        return None
    try:
        val = df[col].iloc[year_idx]
        if pd.notna(val):
            return float(val)
    except (IndexError, TypeError):
        pass
    return None


def calculate_piotroski_fscore(income_stmt, balance_sheet, cashflow):
    """
    Calculate the Piotroski F-Score (0-9) based on 9 binary financial health tests.

    Reference: Piotroski, J. D. (2000). "Value Investing: The Use of Historical
    Financial Statement Information to Separate Winners from Losers."
    Journal of Accounting Research, 38, 1-41.

    Categories:
      Profitability (4 points): ROA > 0, CFO > 0, ROA increasing, CFO > Net Income
      Leverage/Liquidity (3 points): Debt ratio decreasing, Current ratio increasing, No dilution
      Efficiency (2 points): Gross margin increasing, Asset turnover increasing

    Args:
        income_stmt: Annual income statement DataFrame (rows = years, ascending)
        balance_sheet: Annual balance sheet DataFrame (rows = years, ascending)
        cashflow: Annual cash flow statement DataFrame (rows = years, ascending)

    Returns:
        (total_score, details_dict) where details_dict has per-test results
    """
    details = {}
    score = 0

    # Need at least 2 years for year-over-year comparisons
    has_two_years = (
        income_stmt is not None and len(income_stmt) >= 2 and
        balance_sheet is not None and len(balance_sheet) >= 2
    )

    # --- Current year values ---
    net_income = _safe_val(income_stmt, ["Net Income", "NetIncome", "Net Income Common Stockholders"])
    total_assets_curr = _safe_val(balance_sheet, ["Total Assets", "TotalAssets"])
    total_assets_prev = _safe_val(balance_sheet, ["Total Assets", "TotalAssets"], -2) if has_two_years else None

    cfo = _safe_val(cashflow, [
        "Operating Cash Flow", "Cash Flow From Continuing Operating Activities",
        "Total Cash From Operating Activities", "OperatingCashFlow",
    ]) if cashflow is not None and not cashflow.empty else None

    # --- PROFITABILITY (4 tests) ---

    # Test 1: ROA > 0 (Net Income / Total Assets > 0)
    roa_curr = None
    if net_income is not None and total_assets_curr is not None and total_assets_curr > 0:
        roa_curr = net_income / total_assets_curr
    test1 = 1 if roa_curr is not None and roa_curr > 0 else 0
    details["roa_positive"] = {"score": test1, "value": roa_curr}
    score += test1

    # Test 2: Operating Cash Flow > 0
    test2 = 1 if cfo is not None and cfo > 0 else 0
    details["cfo_positive"] = {"score": test2, "value": cfo}
    score += test2

    # Test 3: ROA increasing (ROA this year > ROA last year)
    test3 = 0
    roa_prev = None
    if has_two_years and total_assets_prev is not None and total_assets_prev > 0:
        ni_prev = _safe_val(income_stmt, ["Net Income", "NetIncome", "Net Income Common Stockholders"], -2)
        if ni_prev is not None:
            roa_prev = ni_prev / total_assets_prev
            if roa_curr is not None and roa_prev is not None and roa_curr > roa_prev:
                test3 = 1
    details["roa_increasing"] = {"score": test3, "value_curr": roa_curr, "value_prev": roa_prev}
    score += test3

    # Test 4: Cash Flow > Net Income (accruals quality)
    test4 = 0
    if cfo is not None and net_income is not None and cfo > net_income:
        test4 = 1
    details["cfo_gt_net_income"] = {"score": test4, "cfo": cfo, "net_income": net_income}
    score += test4

    # --- LEVERAGE / LIQUIDITY (3 tests) ---

    # Test 5: Long-term debt ratio decreasing
    test5 = 0
    lt_debt_curr = _safe_val(balance_sheet, ["Long Term Debt", "LongTermDebt", "Total Debt", "TotalDebt"])
    if has_two_years:
        lt_debt_prev = _safe_val(balance_sheet, ["Long Term Debt", "LongTermDebt", "Total Debt", "TotalDebt"], -2)
        if lt_debt_curr is not None and lt_debt_prev is not None and total_assets_curr and total_assets_prev:
            ratio_curr = lt_debt_curr / total_assets_curr
            ratio_prev = lt_debt_prev / total_assets_prev
            if ratio_curr <= ratio_prev:
                test5 = 1
        elif lt_debt_curr is None or lt_debt_curr == 0:
            test5 = 1  # No debt is good
    details["debt_decreasing"] = {"score": test5}
    score += test5

    # Test 6: Current ratio increasing
    test6 = 0
    ca_curr = _safe_val(balance_sheet, ["Current Assets", "CurrentAssets", "Total Current Assets"])
    cl_curr = _safe_val(balance_sheet, ["Current Liabilities", "CurrentLiabilities", "Total Current Liabilities"])
    if has_two_years:
        ca_prev = _safe_val(balance_sheet, ["Current Assets", "CurrentAssets", "Total Current Assets"], -2)
        cl_prev = _safe_val(balance_sheet, ["Current Liabilities", "CurrentLiabilities", "Total Current Liabilities"], -2)
        if ca_curr and cl_curr and cl_curr > 0 and ca_prev and cl_prev and cl_prev > 0:
            cr_curr = ca_curr / cl_curr
            cr_prev = ca_prev / cl_prev
            if cr_curr > cr_prev:
                test6 = 1
    details["current_ratio_increasing"] = {"score": test6}
    score += test6

    # Test 7: No new shares issued (dilution check)
    test7 = 0
    shares_curr = _safe_val(income_stmt, [
        "Diluted Average Shares", "Basic Average Shares",
        "Shares Issued", "ShareIssued", "Ordinary Shares Number",
    ])
    if has_two_years:
        shares_prev = _safe_val(income_stmt, [
            "Diluted Average Shares", "Basic Average Shares",
            "Shares Issued", "ShareIssued", "Ordinary Shares Number",
        ], -2)
        if shares_curr is not None and shares_prev is not None and shares_curr <= shares_prev:
            test7 = 1
        elif shares_curr is None and shares_prev is None:
            test7 = 1  # Can't determine, give benefit of doubt
    details["no_dilution"] = {"score": test7}
    score += test7

    # --- EFFICIENCY (2 tests) ---

    # Test 8: Gross margin increasing
    test8 = 0
    gp_curr = _safe_val(income_stmt, ["Gross Profit", "GrossProfit"])
    rev_curr = _safe_val(income_stmt, ["Total Revenue", "TotalRevenue", "Revenue"])
    if has_two_years and gp_curr is not None and rev_curr and rev_curr > 0:
        gm_curr = gp_curr / rev_curr
        gp_prev = _safe_val(income_stmt, ["Gross Profit", "GrossProfit"], -2)
        rev_prev = _safe_val(income_stmt, ["Total Revenue", "TotalRevenue", "Revenue"], -2)
        if gp_prev is not None and rev_prev and rev_prev > 0:
            gm_prev = gp_prev / rev_prev
            if gm_curr > gm_prev:
                test8 = 1
    details["gross_margin_increasing"] = {"score": test8}
    score += test8

    # Test 9: Asset turnover increasing
    test9 = 0
    if has_two_years and rev_curr is not None and total_assets_curr and total_assets_curr > 0:
        at_curr = rev_curr / total_assets_curr
        rev_prev_val = _safe_val(income_stmt, ["Total Revenue", "TotalRevenue", "Revenue"], -2)
        if rev_prev_val is not None and total_assets_prev and total_assets_prev > 0:
            at_prev = rev_prev_val / total_assets_prev
            if at_curr > at_prev:
                test9 = 1
    details["asset_turnover_increasing"] = {"score": test9}
    score += test9

    # Summary by category
    details["profitability"] = test1 + test2 + test3 + test4
    details["leverage_liquidity"] = test5 + test6 + test7
    details["efficiency"] = test8 + test9
    details["total"] = score

    return score, details


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

    # Paper 1: ATV slope > 0 confirms signals regardless of price direction
    # (positive slope = big money active, entering or exiting)
    # ATV slope <= 0 = big money has no interest, signal unreliable
    volume_confirms = vol_slope > 0
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
    Generate Paper 1 signal faithfully: SMA20/50 crossover + ATV slope confirmation + RSI gate.

    Returns:
        signal: "BUY", "SELL", or "HOLD"
        details: dict with crossover_type, atv_confirmed, rsi_gate, etc.
    """
    if df.empty or len(df) < 50:
        return "HOLD", {"reason": "insufficient_data"}

    if row_idx < 0:
        row_idx = len(df) + row_idx

    details = {}

    # 1. Check SMA Cross Signal at row_idx
    sma_cross = df["SMA_Cross_Signal"].iloc[row_idx] if "SMA_Cross_Signal" in df.columns else 0
    details["sma_cross_signal"] = int(sma_cross)

    # 2. Get ATV slope
    atv_slope = df["ATV_Slope"].iloc[row_idx] if "ATV_Slope" in df.columns and pd.notna(df["ATV_Slope"].iloc[row_idx]) else 0
    details["atv_slope"] = atv_slope

    # 3. Get RSI
    rsi = df["RSI"].iloc[row_idx] if "RSI" in df.columns and pd.notna(df["RSI"].iloc[row_idx]) else 50
    details["rsi"] = rsi

    # Determine base signal from SMA crossover
    if sma_cross == 1:
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

    elif sma_cross == -1:
        # Death cross detected
        details["crossover_type"] = "death_cross"
        # Confirm with ATV slope > 0 (rising volume = big money exiting, confirms sell)
        atv_confirmed = atv_slope > 0
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
        # No crossover event — check current SMA position for trend bias
        sma20 = df["SMA20"].iloc[row_idx] if "SMA20" in df.columns else None
        sma50 = df["SMA50"].iloc[row_idx] if "SMA50" in df.columns else None
        details["crossover_type"] = "none"
        details["atv_confirmed"] = False
        details["rsi_gate"] = "n/a"

        if sma20 is not None and sma50 is not None and pd.notna(sma20) and pd.notna(sma50):
            details["sma_trend"] = "bullish" if sma20 > sma50 else "bearish"
        else:
            details["sma_trend"] = "neutral"

        return "HOLD", details


def generate_recommendation_paper1(volume_score, rsi_value,
                                    market_regime, ticker, info, time_horizon="long",
                                    price_data=None, rl_prediction=None):
    """
    Generate recommendation using Paper 1 approach (Kadia et al., 2025):
    SMA20/50 crossover + ATV confirmation + RSI gate, with optional RL agent override.
    No crossover = HOLD (pure Paper 1). RL can override when no crossover is active.
    """
    # Get Paper 1 rule-based signal
    paper1_signal = "HOLD"
    paper1_details = {}
    if price_data is not None and not price_data.empty:
        paper1_signal, paper1_details = generate_paper1_signal(price_data)

    # Determine recommendation from rule-based signal
    recommendation = paper1_signal
    confidence = 50

    # RL agent integration
    rl_agrees = None
    if rl_prediction is not None:
        rl_action_map = {0: "BUY", 1: "SELL", 2: "HOLD"}
        rl_signal = rl_action_map.get(rl_prediction, "HOLD")
        paper1_details["rl_signal"] = rl_signal
        rl_agrees = (rl_signal == recommendation)
        paper1_details["rl_agrees"] = rl_agrees

        if not rl_agrees and paper1_details.get("crossover_type") == "none":
            # PPO overrides HOLD when no crossover event
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
        # No crossover: base confidence is low (HOLD or RL override)
        if paper1_details.get("rl_override"):
            confidence = 55
            if rl_agrees:
                confidence = 65
        else:
            confidence = 40
    confidence = int(confidence)

    rec_color = {"BUY": "green", "SELL": "red"}.get(recommendation, "orange")

    company_name = info.get("shortName", ticker)
    sector = info.get("sector", "N/A")
    explanation = f"**Strategy: SMA + ATV + RL (Paper 1)**\n\n"
    explanation += "**Approach:** SMA20/50 crossover with ATV slope confirmation and RSI gating.\n\n"

    crossover_type = paper1_details.get("crossover_type", "none")
    if crossover_type == "golden_cross":
        explanation += "**Signal:** Golden Cross (SMA20 crossed above SMA50). "
        if paper1_details.get("atv_confirmed"):
            explanation += "ATV slope confirms rising volume. "
        else:
            explanation += "ATV slope does NOT confirm — signal weakened. "
    elif crossover_type == "death_cross":
        explanation += "**Signal:** Death Cross (SMA20 crossed below SMA50). "
        if paper1_details.get("atv_confirmed"):
            explanation += "ATV slope confirms rising volume (big money exiting). "
        else:
            explanation += "ATV slope does NOT confirm — low volume, signal weakened. "
    else:
        sma_trend = paper1_details.get("sma_trend", "neutral")
        explanation += f"**Signal:** No crossover event detected. SMA trend: {sma_trend}. Defaulting to HOLD. "

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
            explanation += "Overrides HOLD — RL sees an opportunity the rules don't."
        else:
            explanation += "Disagrees with rule-based signal."

    explanation += f"\n\n**Market Context:** {market_regime} regime."

    return {
        "recommendation": recommendation,
        "rec_color": rec_color,
        "confidence": confidence,
        "explanation": explanation,
        "rsi_gate_applied": rsi_gate not in ("n/a", "passed"),
        "rsi_warning": f"RSI at {rsi_value:.1f}" if rsi_gate not in ("n/a", "passed") else "",
        "volume_confirms": volume_score > 50,
        "paper1_details": paper1_details,
    }





