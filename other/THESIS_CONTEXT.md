# Thesis Context Brief — for writing Sections 5-8

## Project overview
A Streamlit-based stock analytics dashboard that provides retail investors with actionable BUY/SELL/HOLD recommendations. The core trading model combines rule-based technical analysis (from Kadia et al. 2025) with a PPO reinforcement learning agent. The dashboard also includes fundamentals, news sentiment, backtesting, and position tracking modules.

The thesis template is `6DATA007W_Final_Project_Report_Template.docx` in the project root. Marking scheme is in `6DATA007W_Final Project_Marking_Scheme.xlsx`.

## The two papers

### Paper 1 — Kadia et al. (2025) "Smart Stock Trading using an Advanced Combination of Technical Indicators with Volume Confirmation Integrated in Reinforcement Learning"
- This is the **foundation** of the trading model
- Located at `other/Smart_Stock_Trading.pdf`
- Defines: SMA crossover signals, ATV slope confirmation, RSI gate, PPO RL agent
- Reports 85% trade accuracy on Indian NSE stocks (in-sample, daily, 5y)
- Our implementation follows this paper's methodology

### Paper 2 — Mohanty (2023?) five-factor stock-picking model
- This is **NOT part of the final solution** — it was implemented only as a comparison baseline
- It's a stock-picking/portfolio model (select top 10% of stocks), NOT a BUY/SELL/HOLD signal generator
- Used only to validate that Paper 1 + RL is the right approach
- Should be mentioned briefly in Background/Literature Review, not in Model Development

## Architecture — Three-layer system

### Layer 1: Data & Indicators (`models.py:compute_indicators`)
- Downloads OHLCV data via yfinance
- Computes: SMA20, SMA50, SMA200, RSI(14), MACD, Bollinger Bands, ATV slope
- `SMA_Cross_Signal`: +1 golden cross (SMA20 > SMA50), -1 death cross, 0 otherwise
- `ATV_Slope`: 20-day linear regression slope of traded volume

### Layer 2: Rule-Based Signals (`models.py:generate_rule_signal`)
- **From Kadia (2025) directly** — not novel code
- SMA20/50 crossover detects trend reversals
- ATV slope confirmation: rising volume validates the crossover
- RSI gate: blocks BUY if RSI > 70 (overbought), blocks SELL if RSI < 30 (oversold)
- Output: BUY / SELL / HOLD with details dict

### Layer 3: RL Agent — PPO (`rl_agent.py`)
- **State space (3-dim, Kadia §4.4)**: [SMA_Cross_Signal, normalised ATV slope, 1-day price return]
- **Actions**: 0=BUY, 1=SELL, 2=HOLD
- **Reward function (Kadia Eq. 5)**: volume-scaled directional return
  ```
  price_return = (close[t+5] - close[t]) / close[t]
  vol_factor = 1 + 0.5 * (volume[t] - avg_20d_volume) / avg_20d_volume
  reward = sign(action) * price_return * vol_factor
  ```
  - BUY rewarded if price goes up, SELL rewarded if price goes down, HOLD = 0
  - Volume multiplier amplifies reward on high-volume days
- **PPO hyperparameters**: lr=3e-4, n_steps=256, batch_size=64, n_epochs=10, gamma=0.99, 100K timesteps
- **One deviation from Kadia**: REWARD_HORIZON = 5 days (Kadia uses 1 day). Empirically justified — 1-day was too noisy for SELL signals to learn anything meaningful.

### Hybrid integration (`models.py:generate_hybrid_recommendation`)
- **This is our design choice** — Kadia does not specify how rule vs RL signals should be combined
- Hierarchy: Rule signal takes priority. If Rule = HOLD (no crossover), RL can override
- If Rule and RL agree → high confidence (90%)
- If Rule active, RL disagrees → keep Rule, lower confidence (60%)
- If Rule = HOLD, RL non-HOLD → RL takes over (the "override" path)
- Confidence percentages are a UX feature, not from either paper

## What is from the paper vs what is our own work

### Directly from Kadia (adopted):
- SMA crossover signal generation logic
- ATV slope as volume confirmation
- RSI overbought/oversold gate
- PPO with 3-dim state space (§4.4)
- Volume-scaled reward function (Eq. 5)

### Our design choices (novel/adapted):
- **Hybrid override logic**: how Rule and RL signals are combined (Kadia doesn't specify)
- **Reward horizon = 5 days** instead of Kadia's 1 day (empirically justified)
- **Confidence percentage**: UX feature for the dashboard
- **Market regime detection**: Bull/Bear/Sideways/High-Volatility via SMA-200 slope + VIX
- **Dashboard itself**: Streamlit app with 6 tabs (Analysis, Technical, Fundamentals, News, Backtesting, Position Tracking)
- **Evaluation methodology**: markout analysis + Kadia-aligned metrics with train/test split
- **Piotroski F-Score** in fundamentals tab (Piotroski 2000, UX only, not part of trading model)

## Evaluation methodology

### Why train/test split is needed for RL
The RL agent is trained on historical data — during training, PPO sees the future returns for each bar and optimises toward them. Evaluating on those same bars measures memorisation, not generalisation. Analogy: "The RL agent is a student who took an open-book exam. Testing on the same bars is asking the student to recite the answer key."

Rule-based signals DON'T have this problem — no fitting, nothing memorised. But since we report them together, we evaluate all strategies on the held-out tail (last 20%) for apples-to-apples comparison.

### Markout analysis (`testing_markouts.py`)
- For each bar in the OOS window, generate signals from 4 strategies: Rule, Rule-gated, Hybrid, RL-only
- For each non-HOLD signal, compute % price move at horizons [1, 2, 3, 5, 10, 21] days
- BUY markout = (future - entry) / entry × 100 (positive = price went up, BUY correct)
- SELL markout = (entry - future) / entry × 100 (sign-flipped, positive = price went down, SELL correct)
- Report: n, avg%, median%, win% per (strategy, horizon)
- Hybrid rows bucketed into: concordant (Rule==RL), rule_led (Rule active, RL disagrees), rl_override (Rule=HOLD, RL takes over)
- Note: 5d horizon is "in-distribution" for PPO (matches reward horizon); 1d and 21d are off-objective

### Kadia-aligned metrics (`testing_kadia_metrics.py`)
- Simulates actual trades: BUY opens position, SELL closes it
- Computes: Trade Accuracy (profitable / total × 100), Avg P&L %, Sharpe Ratio, Sortino Ratio
- These are the same four metrics Kadia reports in Tables 2-4

### Test stocks
15 tickers across bull-leaning and bear/choppy:
- Bull: AAPL, MSFT, GOOGL, NVDA, JPM, JNJ, XOM, PG, KO, WMT
- Bear/choppy: INTC, PFE, BA, T, PYPL (added to stress-test BUY bias)

## Key results (OOS, 15 tickers, before alpha removal)

### Markouts (Hybrid):
| Horizon | Avg Return | Win Rate |
|---------|-----------|----------|
| 1d | +0.092% | 52.9% |
| 5d | +0.371% | 54.9% |
| 21d | +1.715% | 56.5% |

### Kadia metrics (Hybrid):
| Metric | Our result (OOS) | Kadia (in-sample) |
|--------|-----------------|-------------------|
| Trade Accuracy | 65.33% | 85.00% |
| Sharpe Ratio | 1.08 | 2.27 |
| Sortino Ratio | 0.95 | 2.52 |

### Key findings:
- Hybrid ≈ RL-only (99% of Hybrid signals are rl_override — Rule rarely fires in the OOS window)
- Rule signals are too rare OOS (only 23 across 15 tickers) to evaluate statistically
- RL BUY-bias causes losses on declining stocks (PFE: -0.73%, PYPL: -0.76%)
- Overall positive markouts, 53-57% win rates, but market drift partially explains this
- Our OOS numbers are lower than Kadia's in-sample numbers — expected and honest

### Why our numbers differ from Kadia:
1. Kadia evaluates in-sample (no train/test split) — our numbers are OOS only
2. Kadia uses Indian NSE large-caps in a bull market — we use mixed US portfolio including declining stocks
3. Only 75 completed trades (BUY→SELL pairs) due to RL BUY bias (opens positions, rarely closes them)

## Dashboard tech stack
- **Streamlit** — Python web framework
- **Plotly** — interactive charts
- **yfinance** — market data
- **Finnhub** — news headlines
- **stable-baselines3** — PPO implementation
- **Gymnasium** — RL environment interface

## Key files to reference
- `rl_agent.py` — PPO environment, training, inference (the RL agent)
- `models.py` — indicators, rule signals, hybrid recommendation, market regime
- `testing_markouts.py` — markout evaluation script
- `testing_kadia_metrics.py` — Kadia-aligned metrics (accuracy, Sharpe, Sortino)
- `app.py` — main Streamlit entry point
- `tabs/` — dashboard tab implementations
- `styles.py` — UI styling helpers
- `other/Smart_Stock_Trading.pdf` — Kadia et al. (2025) paper

## Section guidance from template

### Section 5 — Tools (500 words)
Tools used and why. Justify Streamlit, yfinance, stable-baselines3, etc.

### Section 6 — Model Development (2500 words)
The big one. Per marking rubric (70-79 = "Technically strong and well-justified solution. Comprehensive model development and validation."):
- Present code extracts with explanation
- Clearly indicate: novel code vs adopted/adapted from Kadia
- Explain the three-layer architecture
- Discuss testing: markout methodology + Kadia metrics
- Critical evaluation of the solution

### Section 7 — Results, Analysis, Discussion (1500-2000 words)
- Present markout tables and Kadia metrics
- Compare with Kadia's reported numbers
- Discuss BUY bias, declining stock performance
- Per-ticker breakdown
- Honest assessment of what the numbers mean

### Section 8 — Conclusions & Reflections (1000 words)
- What worked, what didn't
- Limitations (BUY bias, in-sample caveat on dashboard, Rule rarely fires)
- Further work (regime-aware training, HOLD penalty, walk-forward evaluation)
- Skills gained, reflections on process

## Important caveats to flag honestly in the thesis
1. The dashboard itself uses train_split=1.0 (trains on ALL data) — so live predictions are not OOS-validated in real-time
2. Rule signals fire rarely — the "hybrid" is effectively just the RL agent most of the time
3. RL BUY bias — PPO over-buys, particularly harmful on declining stocks
4. Confidence percentages are UX, not from either paper
5. No transaction costs in evaluation
6. Test stocks are hand-picked, not a random sample
7. Results will vary across runs (PPO training is stochastic)
