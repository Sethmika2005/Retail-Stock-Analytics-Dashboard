# RL agent — PPO for Paper 1 signal enhancement
# ATV = Average Traded Volume (20-day slope is Paper 1's volume confirmation signal).
# State space and reward follow Kadia et al. (2025) §4.4–4.6.

import numpy as np
import pandas as pd

import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv


# 3-dim state: [SMA crossover signal, ATV slope, price return] - 3 actions (buy/sell/hold).
class StockTradingEnv(gym.Env):
    metadata = {"render_modes": []}

    REWARD_HORIZON = 5  # 5 days ahead for reward

    def __init__(self, df, beta=0.5):
        super().__init__()
        self.df = df
        self.beta = beta  # weight on volume scaling
        self.current_step = 0
        self.max_steps = len(df) - (self.REWARD_HORIZON + 1) # stop 6 days before the current date

        # Action Space - 3 possible actions only
        self.action_space = spaces.Discrete(3)  # buy=0, sell=1, hold=2
        
        # Observation Space = 3 floats 
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(3,), dtype=np.float32)

        self._precompute()

    def _precompute(self):
        df = self.df
        close = df["Close"].values.astype(np.float64)

        # Feature 1: SMA crossover signal (+1 golden / -1 death / 0 none)
        self.sma_cross = df["SMA_Cross_Signal"].values.astype(np.float32)

        # Feature 2: ATV slope, divided by its own std for normalisation
        atv = df["ATV_Slope"].fillna(0).values.astype(np.float64)
        atv_std = np.std(atv) or 1.0
        self.atv_norm = (atv / atv_std).astype(np.float32)

        # Feature 3: 1-day return — gives the agent a short-term momentum infromation
        self.ret_1d = np.zeros(len(df), dtype=np.float32)
        self.ret_1d[1:] = ((close[1:] - close[:-1]) / close[:-1]).astype(np.float32)

        # Cached for the reward computation — need future closes and a 20-day volume baseline
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

    # Reward
    def step(self, action):
        i = self.current_step
        n = self.REWARD_HORIZON # = 5 days
        # "Directional return": look 5 days ahead to see whether the trade would have been right
        price_return = (self.close[i + n] - self.close[i]) / self.close[i] if i + n < len(self.close) else 0
        
        # Volume factor: today's volume vs 20-day avg, tuned by beta - larger reward when participation is heavy
        v_avg = self.vol_avg[i] or 1
        vol_factor = 1 + self.beta * (self.volume[i] - v_avg) / v_avg

        #(BUY profits if price rises, SELL profits if it falls, HOLD earns nothing ) x volume factor
        reward = {0: price_return, 1: -price_return, 2: 0.0}[action] * vol_factor

        self.current_step += 1
        terminated = self.current_step >= self.max_steps
        obs = self._get_obs() if not terminated else np.zeros(3, dtype=np.float32)
        return obs, float(reward), terminated, False, {}


# Train PPO on historical data. 
def train_ppo_agent(df, total_timesteps=100000, train_split=1.0): #trained on all data(1.0) but split(0.8) when checking for accuracy
    if 0 < train_split < 1:
        train_df = df.iloc[:int(len(df) * train_split)].copy()
    else:
        train_df = df.copy()
    # Stops training if the dataset is too small
    if len(train_df) < 100:
        return None

    env = DummyVecEnv([lambda: StockTradingEnv(train_df)])
    # PPO hyperparameters (defined by Schulman)
    model = PPO(
        "MlpPolicy", env,
        learning_rate=3e-4,
        n_steps=256,          # short for daily bar granularity
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        seed=42,
        verbose=0,)
    # 100K timesteps = several hundred passes over a 10-year daily series
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
