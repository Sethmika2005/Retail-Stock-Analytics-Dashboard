# Symposium Presentation Plan

## Context
Preparing a 6-slide, 10-minute presentation for the Research Council at Westminster symposium.
Audience: Not domain experts but academically knowledgeable. Needs story-like flow, accessible language.

## Key Decisions Made
- **Paper 2 (5-factor model) is NOT part of the final solution** — it exists only as a comparison baseline to validate Paper 1 + RL approach
- **No conclusion slide** — Slide 6 focuses on Proposed Solution & Impact instead
- **Core narrative gap to market**: Retail investors don't lack data, they lack interpretation. Existing tools show raw charts and metrics that require deep financial knowledge to act on. Our tool bridges this by providing actionable, explained recommendations.
- **The RL agent is positioned as a "decision amplifier"** — it augments rule-based signals, not replaces them. Transparency is key.

## Slide Structure (6 slides, ~10 mins)
1. **Title** (~30s) — Project title + name/affiliation
2. **The Retail Investor's Blind Spot** (~2 min) — Problem domain. Opens with storytelling hook (imagine you want to invest...). Key stat: 150M+ retail investors. Core message: "The gap isn't data — it's interpretation." Visual: institutional vs retail comparison infographic.
3. **From Academic Signals to Actionable Intelligence** (~2 min) — Literature review. Three indicators as cards (EMA Crossover, Volume Confirmation, RSI Safety Gate). Research gap: rules are rigid, can't adapt. Key insight: "Don't replace rules with a black box — amplify them."
4. **Three-Layer Intelligence System** (~2.5 min) — Methodology. Pipeline infographic: Layer 1 (Data & Indicators) → Layer 2 (Rule-Based Signals) → Layer 3 (RL Agent PPO) → Output (Buy/Sell/Hold with confidence). Hybrid agree/disagree logic explained.
5. **The Solution — Dashboard** (~2 min) — 6 modules in icon grid (Analysis, Technical, Fundamentals, News, Backtesting, Position Tracking). Four differentiators: Interprets not just displays, Transparent AI, Market-aware, Zero cost.
6. **Proposed Solution & Impact** (~1 min) — Two columns: What We Propose (unified platform, hybrid rules+AI, transparent reasoning, auto-adapting) + The Impact (bridges knowledge gap, research to practice, transparent AI, empirically validated, zero cost). Closing banner: "Institutional-grade intelligence, accessible to everyone."

## Speaker Notes Approach
- Slide 2 opens with relatable story: "Imagine you've saved some money and want to invest..."
- Use analogies for non-expert audience (e.g., "EMA crossover is like checking if the tide is coming in or going out")
- Slide 5: screenshots speak louder than bullets — show, don't tell
- Validation note: a separate 5-factor model (Paper 2) was implemented as comparison baseline

## Technical Details for Reference
- **Paper 1 Strategy**: EMA-20/50 crossover + ATV slope confirmation + RSI gate (blocks buy >70, sell <30)
- **RL Agent**: PPO, 6-dim state space (EMA signal, ATV slope, 1d/5d returns, RSI, rel volume), 3 actions (Buy/Sell/Hold), volume-adjusted reward, 50K timesteps training
- **Market Regime Detection**: Bull/Bear/Sideways/High-Volatility based on SMA-200 slope, SMA-50/200 crossover, VIX
- **Backtesting**: Sharpe ratio, Sortino ratio, Max Drawdown, trade accuracy
- **Tech Stack**: Streamlit, Plotly, yfinance, Finnhub, stable-baselines3, Gymnasium