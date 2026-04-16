# Models — scoring algorithms, technical indicators, and recommendation engine
# ATV = Average Traded Volume (20-day slope is Paper 1's volume confirmation signal).

import re
import numpy as np
import pandas as pd

RL_ACTION_MAP = {0: "BUY", 1: "SELL", 2: "HOLD"}

POSITIVE_WORDS = {
    "beat", "beats", "beating", "exceeded", "exceeds", "topped", "tops", "topping",
    "outperform", "outperforms", "outperformed", "outpacing",
    "record", "record-breaking", "all-time",
    "surge", "surges", "surging", "soar", "soars", "soaring",
    "rally", "rallies", "rallying", "rebound", "rebounds", "rebounding",
    "gain", "gains", "gaining", "rise", "rises", "rising", "climbs", "climbing",
    "jump", "jumps", "jumping", "spike", "spikes", "spiking",
    "growth", "growing", "grew", "expand", "expands", "expanding", "expansion",
    "boom", "booming", "breakout", "acceleration", "accelerating",
    "profit", "profits", "profitable", "profitability",
    "upgrade", "upgrades", "upgraded", "upbeat", "optimistic", "optimism",
    "bull", "bullish", "buy", "overweight",
    "strong", "strength", "strengthens", "robust", "solid", "resilient",
    "positive", "favorable", "favourable", "promising", "encouraging",
    "confident", "confidence", "momentum", "tailwind", "tailwinds",
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
    "miss", "misses", "missed", "missing", "disappoint", "disappoints", "disappointing",
    "underperform", "underperforms", "underperformed", "underperforming",
    "shortfall", "below", "worse", "worst",
    "drop", "drops", "dropping", "dropped",
    "plunge", "plunges", "plunging", "plunged",
    "fall", "falls", "falling", "fell", "tumble", "tumbles", "tumbling",
    "crash", "crashes", "crashing", "crashed", "collapse", "collapses", "collapsing",
    "sink", "sinks", "sinking", "sank", "slide", "slides", "sliding", "slid",
    "slump", "slumps", "slumping", "decline", "declines", "declining", "declined",
    "loss", "losses", "losing", "lost", "deficit",
    "selloff", "sell-off", "rout", "bloodbath", "wipeout",
    "plummets", "plummeting", "nosedive", "freefall",
    "cut", "cuts", "cutting", "slash", "slashes", "slashing",
    "downgrade", "downgrades", "downgraded", "sell", "underweight",
    "bear", "bearish", "weak", "weakness", "weakens", "weaker", "weakening",
    "negative", "unfavorable", "unfavourable", "pessimistic", "pessimism",
    "concern", "concerns", "concerned", "worried", "worries", "worry", "fear", "fears",
    "risk", "risks", "risky", "threat", "threatens", "threatening",
    "volatile", "volatility", "uncertainty", "uncertain", "turbulence",
    "headwind", "headwinds", "downturn", "recession", "recessionary",
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
    tokens = set(re.findall(r"[a-z]+(?:-[a-z]+)*", title.lower()))
    pos = len(tokens & POSITIVE_WORDS)
    neg = len(tokens & NEGATIVE_WORDS)
    if pos > neg:
        return "Positive"
    if neg > pos:
        return "Negative"
    return "Neutral"


def _safe_val(df, col_candidates, year_idx=-1):
    if df is None:
        return None
    for col in col_candidates:
        if col in df.columns:
            val = df[col].iloc[year_idx]
            if pd.notna(val):
                return float(val)
            return None
    return None


# Piotroski F-Score (0-9): 4 profitability + 3 leverage + 2 efficiency tests
def calculate_piotroski_fscore(income_stmt, balance_sheet, cashflow):
    details = {}
    score = 0

    has_two_years = (
        income_stmt is not None and len(income_stmt) >= 2 and
        balance_sheet is not None and len(balance_sheet) >= 2
    )

    net_income = _safe_val(income_stmt, ["Net Income", "NetIncome", "Net Income Common Stockholders"])
    total_assets_curr = _safe_val(balance_sheet, ["Total Assets", "TotalAssets"])
    total_assets_prev = _safe_val(balance_sheet, ["Total Assets", "TotalAssets"], -2) if has_two_years else None

    cfo = _safe_val(cashflow, [
        "Operating Cash Flow", "Cash Flow From Continuing Operating Activities",
        "Total Cash From Operating Activities", "OperatingCashFlow",
    ])

    # Profitability (tests 1-4)
    roa_current = None
    if net_income is not None and total_assets_curr is not None and total_assets_curr > 0:
        roa_current = net_income / total_assets_curr
    roa_positive = 1 if roa_current is not None and roa_current > 0 else 0
    details["roa_positive"] = {"score": roa_positive, "value": roa_current}
    score += roa_positive

    cfo_positive = 1 if cfo is not None and cfo > 0 else 0
    details["cfo_positive"] = {"score": cfo_positive, "value": cfo}
    score += cfo_positive

    roa_improving = 0
    roa_prior = None
    if has_two_years and total_assets_prev is not None and total_assets_prev > 0:
        net_income_prior = _safe_val(income_stmt, ["Net Income", "NetIncome", "Net Income Common Stockholders"], -2)
        if net_income_prior is not None:
            roa_prior = net_income_prior / total_assets_prev
            if roa_current is not None and roa_prior is not None and roa_current > roa_prior:
                roa_improving = 1
    details["roa_increasing"] = {"score": roa_improving, "value_curr": roa_current, "value_prev": roa_prior}
    score += roa_improving

    accruals_quality = 0  # CFO > net income (accrual quality)
    if cfo is not None and net_income is not None and cfo > net_income:
        accruals_quality = 1
    details["cfo_gt_net_income"] = {"score": accruals_quality, "cfo": cfo, "net_income": net_income}
    score += accruals_quality

    # Leverage / liquidity (tests 5-7)
    leverage_decreasing = 0
    long_term_debt_current = _safe_val(balance_sheet, ["Long Term Debt", "LongTermDebt", "Total Debt", "TotalDebt"])
    if has_two_years:
        long_term_debt_prior = _safe_val(balance_sheet, ["Long Term Debt", "LongTermDebt", "Total Debt", "TotalDebt"], -2)
        if long_term_debt_current is not None and long_term_debt_prior is not None and total_assets_curr and total_assets_prev:
            ratio_current = long_term_debt_current / total_assets_curr
            ratio_prior = long_term_debt_prior / total_assets_prev
            if ratio_current <= ratio_prior:
                leverage_decreasing = 1
        elif long_term_debt_current is None or long_term_debt_current == 0:
            leverage_decreasing = 1
    details["debt_decreasing"] = {"score": leverage_decreasing}
    score += leverage_decreasing

    liquidity_improving = 0
    current_assets = _safe_val(balance_sheet, ["Current Assets", "CurrentAssets", "Total Current Assets"])
    current_liabilities = _safe_val(balance_sheet, ["Current Liabilities", "CurrentLiabilities", "Total Current Liabilities"])
    if has_two_years:
        current_assets_prior = _safe_val(balance_sheet, ["Current Assets", "CurrentAssets", "Total Current Assets"], -2)
        current_liabilities_prior = _safe_val(balance_sheet, ["Current Liabilities", "CurrentLiabilities", "Total Current Liabilities"], -2)
        if current_assets and current_liabilities and current_liabilities > 0 and current_assets_prior and current_liabilities_prior and current_liabilities_prior > 0:
            current_ratio = current_assets / current_liabilities
            current_ratio_prior = current_assets_prior / current_liabilities_prior
            if current_ratio > current_ratio_prior:
                liquidity_improving = 1
    details["current_ratio_increasing"] = {"score": liquidity_improving}
    score += liquidity_improving

    no_share_dilution = 0
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
            no_share_dilution = 1
        elif shares_curr is None and shares_prev is None:
            no_share_dilution = 1
    details["no_dilution"] = {"score": no_share_dilution}
    score += no_share_dilution

    # Efficiency (tests 8-9)
    gross_margin_improving = 0
    gross_profit_current = _safe_val(income_stmt, ["Gross Profit", "GrossProfit"])
    revenue_current = _safe_val(income_stmt, ["Total Revenue", "TotalRevenue", "Revenue"])
    if has_two_years and gross_profit_current is not None and revenue_current and revenue_current > 0:
        gross_margin_current = gross_profit_current / revenue_current
        gross_profit_prior = _safe_val(income_stmt, ["Gross Profit", "GrossProfit"], -2)
        revenue_prior = _safe_val(income_stmt, ["Total Revenue", "TotalRevenue", "Revenue"], -2)
        if gross_profit_prior is not None and revenue_prior and revenue_prior > 0:
            gross_margin_prior = gross_profit_prior / revenue_prior
            if gross_margin_current > gross_margin_prior:
                gross_margin_improving = 1
    details["gross_margin_increasing"] = {"score": gross_margin_improving}
    score += gross_margin_improving

    asset_turnover_improving = 0
    if has_two_years and revenue_current is not None and total_assets_curr and total_assets_curr > 0:
        asset_turnover_current = revenue_current / total_assets_curr
        revenue_prior_val = _safe_val(income_stmt, ["Total Revenue", "TotalRevenue", "Revenue"], -2)
        if revenue_prior_val is not None and total_assets_prev and total_assets_prev > 0:
            asset_turnover_prior = revenue_prior_val / total_assets_prev
            if asset_turnover_current > asset_turnover_prior:
                asset_turnover_improving = 1
    details["asset_turnover_increasing"] = {"score": asset_turnover_improving}
    score += asset_turnover_improving

    # category totals
    details["profitability"] = roa_positive + cfo_positive + roa_improving + accruals_quality
    details["leverage_liquidity"] = leverage_decreasing + liquidity_improving + no_share_dilution
    details["efficiency"] = gross_margin_improving + asset_turnover_improving
    details["total"] = score

    return score, details


# Classify market as Bull/Bear/Sideways/High-Volatility using SMA200 slope + VIX
def detect_market_regime(sp500_df, vix_df):
    if sp500_df.empty or vix_df.empty:
        return "Unknown", "gray", {}

    sp500_df = sp500_df.copy()
    sp500_df["SMA200"] = sp500_df["Close"].rolling(window=200).mean()
    sp500_df["SMA50"] = sp500_df["Close"].rolling(window=50).mean()

    current_price = sp500_df["Close"].iloc[-1]
    sma200 = sp500_df["SMA200"].iloc[-1]
    sma50 = sp500_df["SMA50"].iloc[-1]

    sma200_20d_ago = sp500_df["SMA200"].iloc[-20]
    sma200_slope = (sma200 - sma200_20d_ago) / sma200_20d_ago * 100

    current_vix = vix_df["Close"].iloc[-1]
    vix_ma20 = vix_df["Close"].rolling(window=20).mean().iloc[-1]

    price_vs_sma200 = (current_price - sma200) / sma200 * 100
    sma_crossover = (sma50 - sma200) / sma200 * 100

    sp500_1m_return = (sp500_df["Close"].iloc[-1] / sp500_df["Close"].iloc[-22] - 1) * 100
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


# Volume score (0-100) from ATV slope alignment + relative volume strength
def calculate_volume_score(df):
    if df.empty or "Volume" not in df.columns:
        return 0, {"score": 0, "volume_confirms_trend": False, "details": {}}

    details = {}

    # ATV slope alignment score (0-50)
    # checks whether volume trend aligns with price direction
    price_change = 0
    if len(df) >= 10:
        price_change = df["Close"].iloc[-1] - df["Close"].iloc[-10]

    vol_slope = df["Volume_Slope"].iloc[-1]
    details["volume_slope"] = vol_slope
    details["price_direction"] = "up" if price_change > 0 else "down"

    # positive ATV slope = volume is increasing = institutional activity, confirms signal
    volume_confirms = vol_slope > 0
    details["volume_confirms_trend"] = volume_confirms

    if volume_confirms:
        # base 40 + bonus up to 10 based on how steep the slope is (capped with min())
        alignment_score = 40 + min(10, abs(vol_slope) / 100000)
    elif vol_slope == 0:
        alignment_score = 25
    else:
        alignment_score = 10
    details["alignment_score"] = alignment_score

    # Relative volume score (0-50)
    rel_vol = df["Rel_Volume"].iloc[-1]
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
    details["total"] = total

    return total, {"score": total, "volume_confirms_trend": volume_confirms, "details": details}


# Rule-based signal (Paper 1): SMA20/50 crossover + ATV slope confirmation + RSI gate
def generate_rule_signal(df, row_idx=-1):
    if df.empty or len(df) < 50:
        return "HOLD", {"reason": "insufficient_data"}

    # convert negative index to positive (e.g. -1 becomes last row index)
    if row_idx < 0:
        row_idx = len(df) + row_idx

    details = {}

    sma_cross = df["SMA_Cross_Signal"].iloc[row_idx]
    details["sma_cross_signal"] = int(sma_cross)

    atv_slope = df["ATV_Slope"].iloc[row_idx]
    details["atv_slope"] = atv_slope

    rsi = df["RSI"].iloc[row_idx]
    details["rsi"] = rsi

    if sma_cross == 1:  # golden cross
        details["crossover_type"] = "golden_cross"
        atv_confirmed = atv_slope > 0
        details["atv_confirmed"] = atv_confirmed
        if atv_confirmed:
            if rsi > 70:  # RSI gate: block overbought
                details["rsi_gate"] = "blocked_overbought"
                return "HOLD", details
            else:
                details["rsi_gate"] = "passed"
                return "BUY", details
        else:
            details["rsi_gate"] = "n/a"
            return "HOLD", details

    elif sma_cross == -1:  # death cross
        details["crossover_type"] = "death_cross"
        atv_confirmed = atv_slope > 0
        details["atv_confirmed"] = atv_confirmed
        if atv_confirmed:
            if rsi < 30:  # RSI gate: block oversold
                details["rsi_gate"] = "blocked_oversold"
                return "HOLD", details
            else:
                details["rsi_gate"] = "passed"
                return "SELL", details
        else:
            details["rsi_gate"] = "n/a"
            return "HOLD", details

    else:  # no crossover — report SMA trend bias
        sma20 = df["SMA20"].iloc[row_idx]
        sma50 = df["SMA50"].iloc[row_idx]
        details["crossover_type"] = "none"
        details["atv_confirmed"] = False
        details["rsi_gate"] = "n/a"
        details["sma_trend"] = "bullish" if sma20 > sma50 else "bearish"

        return "HOLD", details


# Combine rule-based signal (Paper 1) with optional RL override
def generate_hybrid_recommendation(volume_score, rsi_value,
                                    market_regime, ticker, info, time_horizon="long",
                                    price_data=None, rl_prediction=None):
    rule_signal = "HOLD"
    rule_details = {}
    if price_data is not None and not price_data.empty:
        rule_signal, rule_details = generate_rule_signal(price_data)

    recommendation = rule_signal
    confidence = 50

    rl_agrees = None
    if rl_prediction is not None:
        rl_signal = RL_ACTION_MAP.get(rl_prediction, "HOLD")
        rule_details["rl_signal"] = rl_signal
        rl_agrees = (rl_signal == recommendation)
        rule_details["rl_agrees"] = rl_agrees

        # hierarchy: if rules say HOLD (no crossover) but RL sees something, let RL take over
        if not rl_agrees and rule_details.get("crossover_type") == "none":
            recommendation = rl_signal
            rule_details["rl_override"] = True

    if rule_signal in ("BUY", "SELL"):
        if rl_agrees is True:
            confidence = 90
        elif rl_agrees is False:
            confidence = 60
        else:
            confidence = 75
    else:
        if rl_agrees is True:
            confidence = 70
        elif rl_agrees is False:
            confidence = 55
        else:
            confidence = 40
    confidence = int(confidence)

    rec_color = {"BUY": "green", "SELL": "red"}.get(recommendation, "orange")

    company_name = info.get("shortName", ticker)
    sector = info.get("sector", "N/A")
    explanation = f"**Strategy: SMA + ATV + RL (Paper 1)**\n\n"
    explanation += "**Approach:** SMA20/50 crossover with ATV slope confirmation and RSI gating.\n\n"

    crossover_type = rule_details.get("crossover_type", "none")
    if crossover_type == "golden_cross":
        explanation += "**Signal:** Golden Cross (SMA20 crossed above SMA50). "
        if rule_details.get("atv_confirmed"):
            explanation += "ATV slope confirms rising volume. "
        else:
            explanation += "ATV slope does NOT confirm — signal weakened. "
    elif crossover_type == "death_cross":
        explanation += "**Signal:** Death Cross (SMA20 crossed below SMA50). "
        if rule_details.get("atv_confirmed"):
            explanation += "ATV slope confirms rising volume (big money exiting). "
        else:
            explanation += "ATV slope does NOT confirm — low volume, signal weakened. "
    else:
        sma_trend = rule_details.get("sma_trend", "neutral")
        explanation += f"**Signal:** No crossover event detected. SMA trend: {sma_trend}. Defaulting to HOLD. "

    rsi_gate = rule_details.get("rsi_gate", "n/a")
    if rsi_gate == "blocked_overbought":
        explanation += f"\n\n**RSI Gate:** RSI at {rsi_value:.1f} (overbought) — BUY blocked."
    elif rsi_gate == "blocked_oversold":
        explanation += f"\n\n**RSI Gate:** RSI at {rsi_value:.1f} (oversold) — SELL blocked."

    if rl_prediction is not None:
        rl_signal = rule_details.get("rl_signal", "N/A")
        explanation += f"\n\n**RL Agent:** PPO predicts {rl_signal}. "
        if rl_agrees:
            explanation += "Agrees with rule-based signal (high confidence)."
        elif rule_details.get("rl_override"):
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
        "rule_details": rule_details,
    }


# Compute all technical indicators for price data
def compute_indicators(df):
    # .copy() so we don't accidentally modify the original cached dataframe
    df = df.copy()

    # Moving averages
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()

    # Bollinger Bands — middle band is SMA20, upper/lower are +/- 2 standard deviations
    r20 = df["Close"].rolling(20)
    df["BB_MID"] = r20.mean()
    df["BB_UPPER"] = df["BB_MID"] + 2 * r20.std()
    df["BB_LOWER"] = df["BB_MID"] - 2 * r20.std()

    # RSI (14-period)
    # .diff() gets day-to-day price change, .where() zeros out the losses/gains respectively
    delta = df["Close"].diff()
    avg_gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    avg_loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    # standard RSI formula: 100 - (100 / (1 + RS)) where RS = avg gain / avg loss
    df["RSI"] = 100 - (100 / (1 + avg_gain / avg_loss))

    # MACD — ewm() calculates exponential weighted moving average (reacts faster to recent prices)
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_SIGNAL"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_HIST"] = df["MACD"] - df["MACD_SIGNAL"]

    # ATR (Average True Range) — measures volatility
    # True Range = max of these three values (accounts for overnight gaps)
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()  # .shift() gets previous day's close
    low_close = (df["Low"] - df["Close"].shift()).abs()
    # stack all three into columns, take the max of each row, then average over 14 days
    df["ATR"] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(14).mean()

    # Z-score — how many std deviations the price is from its 60-day mean
    ma60 = df["Close"].rolling(60).mean()
    df["Z_SCORE_60"] = (df["Close"] - ma60) / df["Close"].rolling(60).std()

    # SMA crossover signal (vectorised instead of looping):
    # above=1 when SMA20 > SMA50, diff() catches the moment it flips: +1 = golden cross, -1 = death cross
    above = (df["SMA20"] > df["SMA50"]).astype(int)
    cross = above.diff()
    df["SMA_Cross_Signal"] = cross.fillna(0).astype(int)  # NaN on day 1 (no prior day to diff) → 0 = no signal

    # Volume indicators
    if "Volume" in df.columns:
        df["Volume_SMA20"] = df["Volume"].rolling(20).mean()
        df["Volume_SMA50"] = df["Volume"].rolling(50).mean()
        # relative volume: today's volume vs 20-day average (>1 = above average)
        df["Rel_Volume"] = df["Volume"] / df["Volume_SMA20"]

        # ATV slope: fit a straight line (linear regression) through last 10 days of volume
        # np.polyfit returns [slope, intercept] — we grab [0] for just the slope
        vol_sma = df["Volume_SMA20"]
        df["Volume_Slope"] = vol_sma.rolling(10).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if x.notna().all() else 0,
            raw=False)

        df["ATV_20"] = df["Volume"].rolling(20).mean()
        df["ATV_Slope"] = df["ATV_20"].rolling(10).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if x.notna().all() else 0,
            raw=False)

    # ~22 trading days in a month
    df["Monthly_Return"] = df["Close"].pct_change(periods=22)
    return df

