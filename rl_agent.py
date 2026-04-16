# RL agent — PPO for Paper 1 signal enhancement
# ATV = Average Traded Volume (20-day slope is Paper 1's volume confirmation signal).
# State space and reward follow Kadia et al. (2025) §4.4–4.6.

import numpy as np
import pandas as pd

import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv


# 3-dim state (Kadia §4.4): [SMA crossover signal, ATV slope, price return].
# 3 actions (buy/sell/hold). Reward uses Kadia Eq. 5 (volume-scaled directional return).
class StockTradingEnv(gym.Env):
    metadata = {"render_modes": []}

    REWARD_HORIZON = 5  # days ahead for reward (deviation from Kadia's 1d — empirically better SELL-side markouts)

    def __init__(self, df, beta=0.5):
        super().__init__()
        self.df = df
        self.beta = beta  # Eq. 5 weight on volume scaling
        self.current_step = 0
        self.max_steps = len(df) - (self.REWARD_HORIZON + 1)

        self.action_space = spaces.Discrete(3)  # buy=0, sell=1, hold=2
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(3,), dtype=np.float32
        )

        self._precompute()

    # Pre-calculate state features and reward inputs as numpy arrays
    def _precompute(self):
        df = self.df
        close = df["Close"].values.astype(np.float64)

        self.sma_cross = df["SMA_Cross_Signal"].values.astype(np.float32)

        # normalise ATV slope by its std so values are roughly -1 to 1
        atv = df["ATV_Slope"].fillna(0).values.astype(np.float64)
        atv_std = np.std(atv) or 1.0
        self.atv_norm = (atv / atv_std).astype(np.float32)

        # 1-day price return (Kadia's state feature)
        self.ret_1d = np.zeros(len(df), dtype=np.float32)
        self.ret_1d[1:] = ((close[1:] - close[:-1]) / close[:-1]).astype(np.float32)

        self.close = close
        vol = df["Volume"].fillna(0).values.astype(np.float64)
        self.volume = vol
        self.vol_avg = pd.Series(vol).rolling(window=20, min_periods=1).mean().values

    def _get_obs(self):
        i = self.current_step
        return np.array([
            self.sma_cross[i], self.atv_norm[i], self.ret_1d[i],
        ], dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        return self._get_obs(), {}

    # Reward = Kadia Eq. 5 (volume-scaled directional return)
    def step(self, action):
        i = self.current_step
        n = self.REWARD_HORIZON
        price_return = (self.close[i + n] - self.close[i]) / self.close[i] if i + n < len(self.close) else 0
        v_avg = self.vol_avg[i] or 1
        vol_factor = 1 + self.beta * (self.volume[i] - v_avg) / v_avg

        # Eq. 5: buy rewarded if price rises, sell if falls; scaled by volume factor
        reward = {0: price_return, 1: -price_return, 2: 0.0}[action] * vol_factor

        self.current_step += 1
        terminated = self.current_step >= self.max_steps
        obs = self._get_obs() if not terminated else np.zeros(3, dtype=np.float32)
        return obs, float(reward), terminated, False, {}


# Train PPO on historical data. Returns model or None if too little data.
# train_split: fraction of df for training. 1.0 = all data (dashboard). 0.8 = hold out test set.
def train_ppo_agent(df, total_timesteps=100000, train_split=1.0):
    if 0 < train_split < 1:
        train_df = df.iloc[:int(len(df) * train_split)].copy()
    else:
        train_df = df.copy()
    if len(train_df) < 100:
        return None

    env = DummyVecEnv([lambda: StockTradingEnv(train_df)])
    model = PPO(
        "MlpPolicy", env,
        learning_rate=3e-4,
        n_steps=256,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        verbose=0,
    )
    model.learn(total_timesteps=total_timesteps)
    return model


# Get PPO action for latest state. Returns 0=buy, 1=sell, 2=hold, or None.
def predict_action(model, df, row_idx=-1):
    if model is None:
        return None

    if row_idx < 0:
        row_idx = len(df) + row_idx

    row = df.iloc[row_idx]
    sma_cross = float(row["SMA_Cross_Signal"])

    atv_std = df["ATV_Slope"].std()
    atv_norm = float(row["ATV_Slope"]) / atv_std if atv_std else 0.0

    ret_1d = (row["Close"] - df["Close"].iloc[row_idx - 1]) / df["Close"].iloc[row_idx - 1] if row_idx > 0 else 0.0

    obs = np.array([sma_cross, atv_norm, ret_1d], dtype=np.float32)
    action, _ = model.predict(obs, deterministic=True)
    return int(action)
