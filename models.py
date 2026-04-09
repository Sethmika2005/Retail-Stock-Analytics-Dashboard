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
# RECOMMENDATION ENGINE
# =============================================================================


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


def generate_bull_bear_case(info, price_data, market_regime):
    """Generate bull and bear case arguments."""
    bull_case = []
    bear_case = []

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



