# =============================================================================
# RL_AGENT.PY - PPO Reinforcement Learning Agent for Paper 1
# =============================================================================
# Gymnasium environment + PPO training pipeline with model caching.
# Gracefully degrades if stable-baselines3 is not installed.
# =============================================================================

import os
import hashlib
import numpy as np
import pandas as pd

# Graceful import guard
RL_AVAILABLE = False
try:
    import gymnasium as gym
    from gymnasium import spaces
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv
    RL_AVAILABLE = True
except (ImportError, OSError):
    pass

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models_cache")


# =============================================================================
# GYMNASIUM ENVIRONMENT
# =============================================================================

if RL_AVAILABLE:
    class StockTradingEnv(gym.Env):
        """
        Gymnasium environment for Paper 1 PPO agent.

        State: [ema_cross_signal, atv_slope_normalized, 1d_return, 5d_return, rsi_normalized, rel_volume]
        Actions: Discrete(3) -> buy(0), sell(1), hold(2)
        Reward: Rt = (Pt+1 - Pt)/Pt * (1 + beta * (Vt - V_avg)/V_avg)  (paper's Eq. 5)
        """
        metadata = {"render_modes": []}

        def __init__(self, df, beta=0.5):
            super().__init__()
            self.df = df.reset_index(drop=True)
            self.beta = beta
            self.current_step = 0
            self.max_steps = len(df) - 2  # Need at least 1 future step for reward

            self.action_space = spaces.Discrete(3)  # buy=0, sell=1, hold=2
            # 6-dimensional continuous observation
            self.observation_space = spaces.Box(
                low=-np.inf, high=np.inf, shape=(6,), dtype=np.float32
            )

            # Precompute features
            self._precompute()

        def _precompute(self):
            """Precompute normalized features for all timesteps."""
            df = self.df

            # EMA cross signal (already -1, 0, 1)
            self.ema_cross = df["EMA_Cross_Signal"].values.astype(np.float32) if "EMA_Cross_Signal" in df.columns else np.zeros(len(df), dtype=np.float32)

            # ATV slope normalized (z-score)
            if "ATV_Slope" in df.columns:
                atv = df["ATV_Slope"].fillna(0).values.astype(np.float64)
                atv_std = np.std(atv) if np.std(atv) > 0 else 1.0
                self.atv_norm = (atv / atv_std).astype(np.float32)
            else:
                self.atv_norm = np.zeros(len(df), dtype=np.float32)

            # 1-day return
            close = df["Close"].values.astype(np.float64)
            self.ret_1d = np.zeros(len(df), dtype=np.float32)
            self.ret_1d[1:] = ((close[1:] - close[:-1]) / np.where(close[:-1] != 0, close[:-1], 1)).astype(np.float32)

            # 5-day return
            self.ret_5d = np.zeros(len(df), dtype=np.float32)
            if len(df) > 5:
                self.ret_5d[5:] = ((close[5:] - close[:-5]) / np.where(close[:-5] != 0, close[:-5], 1)).astype(np.float32)

            # RSI normalized to [-1, 1]
            if "RSI" in df.columns:
                rsi = df["RSI"].fillna(50).values.astype(np.float64)
                self.rsi_norm = ((rsi - 50) / 50).astype(np.float32)
            else:
                self.rsi_norm = np.zeros(len(df), dtype=np.float32)

            # Relative volume (capped)
            if "Rel_Volume" in df.columns:
                rv = df["Rel_Volume"].fillna(1.0).values.astype(np.float64)
                self.rel_vol = np.clip(rv, 0, 5).astype(np.float32)
            else:
                self.rel_vol = np.ones(len(df), dtype=np.float32)

            # For reward computation
            self.close = close
            if "Volume" in df.columns:
                vol = df["Volume"].fillna(0).values.astype(np.float64)
                self.volume = vol
                self.vol_avg = pd.Series(vol).rolling(window=20, min_periods=1).mean().values
            else:
                self.volume = np.ones(len(df), dtype=np.float64)
                self.vol_avg = np.ones(len(df), dtype=np.float64)

        def _get_obs(self):
            i = self.current_step
            return np.array([
                self.ema_cross[i],
                self.atv_norm[i],
                self.ret_1d[i],
                self.ret_5d[i],
                self.rsi_norm[i],
                self.rel_vol[i],
            ], dtype=np.float32)

        def reset(self, seed=None, options=None):
            super().reset(seed=seed)
            self.current_step = 0
            return self._get_obs(), {}

        def step(self, action):
            i = self.current_step

            # Price return for reward
            if i + 1 < len(self.close):
                price_return = (self.close[i + 1] - self.close[i]) / self.close[i] if self.close[i] != 0 else 0
            else:
                price_return = 0

            # Volume factor for reward (paper's Eq. 5)
            v_avg = self.vol_avg[i] if self.vol_avg[i] > 0 else 1
            vol_factor = 1 + self.beta * (self.volume[i] - v_avg) / v_avg

            # Reward based on action
            if action == 0:  # buy
                reward = price_return * vol_factor
            elif action == 1:  # sell
                reward = -price_return * vol_factor
            else:  # hold
                reward = 0.0

            self.current_step += 1
            terminated = self.current_step >= self.max_steps
            truncated = False

            obs = self._get_obs() if not terminated else np.zeros(6, dtype=np.float32)

            return obs, float(reward), terminated, truncated, {}


# =============================================================================
# TRAINING PIPELINE
# =============================================================================

def _get_cache_key(ticker, data_len):
    """Generate a cache key based on ticker and data length."""
    raw = f"{ticker}_{data_len}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def train_ppo_agent(df, ticker="UNKNOWN", total_timesteps=50000):
    """
    Train a PPO agent on historical data.

    Args:
        df: DataFrame with computed indicators (EMA_Cross_Signal, ATV_Slope, RSI, etc.)
        ticker: Ticker symbol for caching
        total_timesteps: Training duration

    Returns:
        model: Trained PPO model, or None if RL not available
    """
    if not RL_AVAILABLE:
        return None

    # 80/10/10 split
    n = len(df)
    train_end = int(n * 0.8)
    val_end = int(n * 0.9)

    train_df = df.iloc[:train_end].copy()
    # val_df = df.iloc[train_end:val_end].copy()  # reserved for validation
    # test_df = df.iloc[val_end:].copy()  # reserved for testing

    if len(train_df) < 100:
        return None

    env = DummyVecEnv([lambda: StockTradingEnv(train_df)])

    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=256,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        verbose=0,
    )

    model.learn(total_timesteps=total_timesteps)

    return model


def get_ppo_agent(df, ticker="UNKNOWN", force_retrain=False):
    """
    Get a PPO agent, using cache if available.

    Returns:
        model: PPO model or None
    """
    if not RL_AVAILABLE:
        return None

    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_key = _get_cache_key(ticker, len(df))
    cache_path = os.path.join(CACHE_DIR, f"ppo_{cache_key}")

    # Try loading from cache
    if not force_retrain and os.path.exists(cache_path + ".zip"):
        try:
            model = PPO.load(cache_path)
            return model
        except Exception:
            pass

    # Train new model
    model = train_ppo_agent(df, ticker)
    if model is not None:
        try:
            model.save(cache_path)
        except Exception:
            pass

    return model


def predict_action(model, df, row_idx=-1):
    """
    Get PPO agent's action prediction for a given state.

    Returns:
        action: 0=buy, 1=sell, 2=hold, or None if model unavailable
    """
    if model is None or not RL_AVAILABLE:
        return None

    if row_idx < 0:
        row_idx = len(df) + row_idx

    # Build observation
    row = df.iloc[row_idx]

    ema_cross = float(row.get("EMA_Cross_Signal", 0) or 0)

    atv_slope = float(row.get("ATV_Slope", 0) or 0)
    if "ATV_Slope" in df.columns:
        atv_std = df["ATV_Slope"].std()
        if atv_std and atv_std > 0:
            atv_norm = atv_slope / atv_std
        else:
            atv_norm = 0.0
    else:
        atv_norm = 0.0

    # 1-day return
    if row_idx > 0:
        prev_close = df["Close"].iloc[row_idx - 1]
        ret_1d = (row["Close"] - prev_close) / prev_close if prev_close != 0 else 0
    else:
        ret_1d = 0.0

    # 5-day return
    if row_idx >= 5:
        close_5d_ago = df["Close"].iloc[row_idx - 5]
        ret_5d = (row["Close"] - close_5d_ago) / close_5d_ago if close_5d_ago != 0 else 0
    else:
        ret_5d = 0.0

    rsi = float(row.get("RSI", 50) or 50)
    rsi_norm = (rsi - 50) / 50

    rel_vol = float(row.get("Rel_Volume", 1.0) or 1.0)
    rel_vol = min(rel_vol, 5.0)

    obs = np.array([ema_cross, atv_norm, ret_1d, ret_5d, rsi_norm, rel_vol], dtype=np.float32)

    try:
        action, _ = model.predict(obs, deterministic=True)
        return int(action)
    except Exception:
        return None


def is_available():
    """Check if RL dependencies are installed."""
    return RL_AVAILABLE
