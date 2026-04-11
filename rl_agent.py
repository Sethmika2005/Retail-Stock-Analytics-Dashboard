# RL agent — PPO for Paper 1 signal enhancement

import numpy as np
import pandas as pd

import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv


class StockTradingEnv(gym.Env):
    """6D state, 3 actions (buy/sell/hold). Reward per Paper 1 Eq. 5."""
    metadata = {"render_modes": []}

    def __init__(self, df, beta=0.5):
        super().__init__()
        self.df = df
        self.beta = beta
        self.current_step = 0
        self.max_steps = len(df) - 2  # need ≥1 future step for reward

        self.action_space = spaces.Discrete(3)  # buy=0, sell=1, hold=2
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(6,), dtype=np.float32
        )

        self._precompute()

    def _precompute(self):
        df = self.df
        close = df["Close"].values.astype(np.float64)

        self.sma_cross = df["SMA_Cross_Signal"].values.astype(np.float32)

        atv = df["ATV_Slope"].fillna(0).values.astype(np.float64)
        atv_std = np.std(atv) or 1.0
        self.atv_norm = (atv / atv_std).astype(np.float32)

        self.ret_1d = np.zeros(len(df), dtype=np.float32)
        self.ret_1d[1:] = ((close[1:] - close[:-1]) / close[:-1]).astype(np.float32)

        self.ret_5d = np.zeros(len(df), dtype=np.float32)
        if len(df) > 5:
            self.ret_5d[5:] = ((close[5:] - close[:-5]) / close[:-5]).astype(np.float32)

        rsi = df["RSI"].fillna(50).values.astype(np.float64)
        self.rsi_norm = ((rsi - 50) / 50).astype(np.float32)

        rv = df["Rel_Volume"].fillna(1.0).values.astype(np.float64)
        self.rel_vol = np.clip(rv, 0, 5).astype(np.float32)

        self.close = close
        vol = df["Volume"].fillna(0).values.astype(np.float64)
        self.volume = vol
        self.vol_avg = pd.Series(vol).rolling(window=20, min_periods=1).mean().values

    def _get_obs(self):
        i = self.current_step
        return np.array([
            self.sma_cross[i], self.atv_norm[i],
            self.ret_1d[i], self.ret_5d[i],
            self.rsi_norm[i], self.rel_vol[i],
        ], dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        return self._get_obs(), {}

    def step(self, action):
        i = self.current_step
        price_return = (self.close[i + 1] - self.close[i]) / self.close[i] if i + 1 < len(self.close) else 0
        v_avg = self.vol_avg[i] or 1
        vol_factor = 1 + self.beta * (self.volume[i] - v_avg) / v_avg

        if action == 0:      # buy
            reward = price_return * vol_factor
        elif action == 1:    # sell
            reward = -price_return * vol_factor
        else:                # hold
            reward = 0.0

        self.current_step += 1
        terminated = self.current_step >= self.max_steps
        obs = self._get_obs() if not terminated else np.zeros(6, dtype=np.float32)
        return obs, float(reward), terminated, False, {}


def train_ppo_agent(df, ticker="UNKNOWN", total_timesteps=50000):
    """Train PPO on historical data. Returns model or None if too little data."""
    train_df = df.iloc[:int(len(df) * 0.8)].copy()
    if len(train_df) < 100:
        return None

    env = DummyVecEnv([lambda: StockTradingEnv(train_df)])
    model = PPO(
        "MlpPolicy", env,
        learning_rate=3e-4, n_steps=256, batch_size=64,
        n_epochs=10, gamma=0.99, verbose=0,
    )
    model.learn(total_timesteps=total_timesteps)
    return model


def predict_action(model, df, row_idx=-1):
    """Get PPO action for latest state. Returns 0=buy, 1=sell, 2=hold, or None."""
    if model is None:
        return None

    if row_idx < 0:
        row_idx = len(df) + row_idx

    row = df.iloc[row_idx]
    sma_cross = float(row["SMA_Cross_Signal"])

    atv_std = df["ATV_Slope"].std()
    atv_norm = float(row["ATV_Slope"]) / atv_std if atv_std else 0.0

    ret_1d = (row["Close"] - df["Close"].iloc[row_idx - 1]) / df["Close"].iloc[row_idx - 1] if row_idx > 0 else 0.0
    ret_5d = (row["Close"] - df["Close"].iloc[row_idx - 5]) / df["Close"].iloc[row_idx - 5] if row_idx >= 5 else 0.0

    rsi_norm = (float(row["RSI"]) - 50) / 50
    rel_vol = min(float(row["Rel_Volume"]), 5.0)

    obs = np.array([sma_cross, atv_norm, ret_1d, ret_5d, rsi_norm, rel_vol], dtype=np.float32)
    action, _ = model.predict(obs, deterministic=True)
    return int(action)
