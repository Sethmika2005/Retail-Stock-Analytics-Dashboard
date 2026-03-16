"""
Strategy Definitions for Model Comparison
==========================================
Four strategy wrappers, each with signature (df, idx) → "BUY" | "SELL" | "HOLD",
compatible with backtest.simulate_strategy().
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    generate_paper1_signal,
    generate_recommendation_paper1,
    generate_recommendation_paper2,
    calculate_technical_score,
    calculate_volume_score,
    calculate_fundamental_score_paper2,
)

try:
    import rl_agent
    RL_AVAILABLE = rl_agent.is_available()
except (ImportError, OSError):
    RL_AVAILABLE = False


# =============================================================================
# Strategy 1: Paper 1 Rules Only (EMA + ATV + RSI gate, no RL)
# =============================================================================

def make_rules_only_strategy():
    """Pure rule-based: EMA crossover + ATV slope + RSI gate. No RL."""
    def strategy_fn(df, idx):
        historical = df.iloc[:idx + 1]
        if len(historical) < 50:
            return "HOLD"
        signal, _ = generate_paper1_signal(historical, row_idx=-1)
        return signal
    return strategy_fn


# =============================================================================
# Strategy 2: Paper 1 + RL (Original Paper — RL overrides on disagreement)
# =============================================================================

def make_paper1_rl_strategy(ppo_model):
    """Paper 1 rules + PPO agent with simple override logic (RL wins on disagreement)."""
    def strategy_fn(df, idx):
        historical = df.iloc[:idx + 1]
        if len(historical) < 50:
            return "HOLD"

        # Rule-based signal
        rule_signal, _ = generate_paper1_signal(historical, row_idx=-1)

        # RL prediction
        rl_action = rl_agent.predict_action(ppo_model, historical, row_idx=-1)
        rl_signal_map = {0: "BUY", 1: "SELL", 2: "HOLD"}
        rl_signal = rl_signal_map.get(rl_action, "HOLD")

        # Hybrid logic: RL overrides whenever it disagrees
        if rule_signal == rl_signal:
            return rule_signal
        if rule_signal == "HOLD" and rl_signal in ("BUY", "SELL"):
            return rl_signal
        if rule_signal != "HOLD" and rl_signal != rule_signal:
            return rl_signal
        return "HOLD"
    return strategy_fn


# =============================================================================
# Strategy 3: Novel Hybrid (Ours) — Rules + RL + regime-aware + confidence
# =============================================================================

def make_novel_hybrid_strategy(ppo_model, market_regime, info):
    """
    Full dashboard logic: per-step tech_score, volume_score, RSI,
    plus RL prediction and market regime, passed to generate_recommendation_paper1().
    """
    def strategy_fn(df, idx):
        historical = df.iloc[:idx + 1]
        if len(historical) < 50:
            return "HOLD"

        # Compute scores at this step
        tech_score, _ = calculate_technical_score(historical)
        volume_score, _ = calculate_volume_score(historical)
        rsi_value = historical["RSI"].iloc[-1] if "RSI" in historical.columns else 50

        # RL prediction
        rl_prediction = None
        if ppo_model is not None:
            rl_prediction = rl_agent.predict_action(ppo_model, historical, row_idx=-1)

        # Full recommendation with regime awareness and RL integration
        rec = generate_recommendation_paper1(
            tech_score=tech_score,
            fund_score=50,          # neutral — backtest doesn't use fundamentals
            volume_score=volume_score,
            rsi_value=rsi_value,
            market_regime=market_regime,
            ticker="BACKTEST",
            info=info,
            time_horizon="long",
            price_data=historical,
            rl_prediction=rl_prediction,
        )
        return rec["recommendation"]
    return strategy_fn


# =============================================================================
# Strategy 4: Paper 2 — 5-Factor Percentile Scoring
# =============================================================================

def make_paper2_strategy(info, market_regime, peer_metrics=None):
    """Paper 2: percentile-based factor scoring with risk-profile weights."""
    def strategy_fn(df, idx):
        historical = df.iloc[:idx + 1]
        if len(historical) < 200:
            return "HOLD"
        tech_score, _ = calculate_technical_score(historical)
        fund_score, _ = calculate_fundamental_score_paper2(
            info, peer_metrics=peer_metrics, risk_profile="moderate", price_data=historical
        )
        rec = generate_recommendation_paper2(
            tech_score, fund_score, market_regime, "BACKTEST", info
        )
        return rec["recommendation"]
    return strategy_fn


# =============================================================================
# Registry: returns all 4 strategies as a dict
# =============================================================================

def get_all_strategies(ppo_model, market_regime, info, peer_metrics=None):
    """
    Build and return all 4 strategies.

    Returns:
        dict of {name: strategy_fn}
    """
    strategies = {
        "Paper 1 Rules Only": make_rules_only_strategy(),
        "Paper 1 + RL (Original)": make_paper1_rl_strategy(ppo_model) if ppo_model else None,
        "Novel Hybrid (Ours)": make_novel_hybrid_strategy(ppo_model, market_regime, info),
        "Paper 2 (5-Factor)": make_paper2_strategy(info, market_regime, peer_metrics),
    }
    # Remove None entries (e.g., if RL unavailable)
    return {k: v for k, v in strategies.items() if v is not None}
