# RL agent — PPO for Paper 1 signal enhancement

import numpy as np
import pandas as pd

import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv


class StockTradingEnv(gym.Env):
    """Custom Gymnasium environment for the PPO agent.
    6-dimensional state space, 3 actions (buy/sell/hold). Reward per Paper 1 Eq. 5."""
    metadata = {"render_modes": []}

    REWARD_HORIZON = 5  # days ahead for reward computation (was 1)

    def __init__(self, df, beta=0.5):
        super().__init__()
        self.df = df
        self.beta = beta  # controls how much volume influences the reward
        self.current_step = 0
        self.max_steps = len(df) - (self.REWARD_HORIZON + 1)  # need N future steps for reward

        self.action_space = spaces.Discrete(3)  # buy=0, sell=1, hold=2
        # Box = continuous values, shape=(6,) = 6 numbers the agent sees each step
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(6,), dtype=np.float32
        )

        self._precompute()

    def _precompute(self):
        """Pre-calculate all features as numpy arrays for fast access during training.
        This avoids recalculating from the dataframe every step."""
        df = self.df
        close = df["Close"].values.astype(np.float64)

        self.sma_cross = df["SMA_Cross_Signal"].values.astype(np.float32)

        # normalise ATV slope by dividing by its std deviation so values are roughly -1 to 1
        # "or 1.0" prevents division by zero if all slopes are identical
        atv = df["ATV_Slope"].fillna(0).values.astype(np.float64)  # missing slope → 0 = flat volume trend (neutral)
        atv_std = np.std(atv) or 1.0
        self.atv_norm = (atv / atv_std).astype(np.float32)

        # 1-day return: array slicing trick — close[1:] vs close[:-1] gives each day vs previous
        self.ret_1d = np.zeros(len(df), dtype=np.float32)
        self.ret_1d[1:] = ((close[1:] - close[:-1]) / close[:-1]).astype(np.float32)

        # same idea but 5-day lookback
        self.ret_5d = np.zeros(len(df), dtype=np.float32)
        if len(df) > 5:
            self.ret_5d[5:] = ((close[5:] - close[:-5]) / close[:-5]).astype(np.float32)

        # RSI normalised from 0-100 range to -1 to +1 range (better for neural networks)
        rsi = df["RSI"].fillna(50).values.astype(np.float64)  # missing RSI → 50 = neutral (neither overbought nor oversold)
        self.rsi_norm = ((rsi - 50) / 50).astype(np.float32)

        # clip extreme volume values to prevent outliers from dominating
        rv = df["Rel_Volume"].fillna(1.0).values.astype(np.float64)  # missing rel volume → 1.0 = exactly average
        self.rel_vol = np.clip(rv, 0, 5).astype(np.float32)

        self.close = close
        vol = df["Volume"].fillna(0).values.astype(np.float64)  # missing volume → 0 (safe default; rolling avg handles it below)
        self.volume = vol
        # min_periods=1 so we get averages from day 1 instead of NaN for the first 19 days
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
        """Execute one trading step. Returns (observation, reward, terminated, truncated, info).
        Reward = price return * volume factor (Paper 1 Eq. 5)."""
        i = self.current_step
        n = self.REWARD_HORIZON
        price_return = (self.close[i + n] - self.close[i]) / self.close[i] if i + n < len(self.close) else 0
        # volume factor: trades on high-volume days are rewarded/penalised more
        v_avg = self.vol_avg[i] or 1
        vol_factor = 1 + self.beta * (self.volume[i] - v_avg) / v_avg

        # buy gets positive reward if price goes up, sell gets positive reward if price goes down
        reward = {0: price_return, 1: -price_return, 2: 0.0}[action] * vol_factor

        self.current_step += 1
        terminated = self.current_step >= self.max_steps
        obs = self._get_obs() if not terminated else np.zeros(6, dtype=np.float32)
        return obs, float(reward), terminated, False, {}


def train_ppo_agent(df, total_timesteps=100000):
    """Train PPO on historical data. Returns model or None if too little data."""
    # use first 80% of data for training (last 20% is unseen, used for prediction)
    train_df = df.iloc[:int(len(df) * 0.8)].copy()
    if len(train_df) < 100:
        return None

    # DummyVecEnv wraps our env in a list — stable-baselines3 requires vectorised envs
    # even when using just one environment
    env = DummyVecEnv([lambda: StockTradingEnv(train_df)])
    # MlpPolicy = Multi-Layer Perceptron (standard neural network)
    model = PPO(
        "MlpPolicy", env,
        learning_rate=3e-4,  # how fast the model updates its weights
        n_steps=256,         # steps collected before each policy update
        batch_size=64,       # samples per training mini-batch
        n_epochs=10,         # passes over collected data per update
        gamma=0.99,          # discount factor — how much future rewards matter
        verbose=0,           # suppress training logs
    )
    model.learn(total_timesteps=total_timesteps)
    return model


def predict_action(model, df, row_idx=-1):
    """Get PPO action for latest state. Returns 0=buy, 1=sell, 2=hold, or None."""
    if model is None:
        return None

    # convert negative index (e.g. -1 = last row) to positive
    if row_idx < 0:
        row_idx = len(df) + row_idx

    # build the same 6-feature observation vector the model was trained on
    row = df.iloc[row_idx]
    sma_cross = float(row["SMA_Cross_Signal"])

    # normalise ATV slope the same way as in training
    atv_std = df["ATV_Slope"].std()
    atv_norm = float(row["ATV_Slope"]) / atv_std if atv_std else 0.0

    ret_1d = (row["Close"] - df["Close"].iloc[row_idx - 1]) / df["Close"].iloc[row_idx - 1] if row_idx > 0 else 0.0
    ret_5d = (row["Close"] - df["Close"].iloc[row_idx - 5]) / df["Close"].iloc[row_idx - 5] if row_idx >= 5 else 0.0

    rsi_norm = (float(row["RSI"]) - 50) / 50
    rel_vol = min(float(row["Rel_Volume"]), 5.0)

    obs = np.array([sma_cross, atv_norm, ret_1d, ret_5d, rsi_norm, rel_vol], dtype=np.float32)
    # deterministic=True means pick the best action, not random exploration
    action, _ = model.predict(obs, deterministic=True)
    return int(action)
