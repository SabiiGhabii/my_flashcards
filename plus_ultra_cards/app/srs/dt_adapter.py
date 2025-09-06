"""
DeepTutorAdapter: Bridges DeepTutor.py student environments to the app using a modern RL library (SB3).
- Preserves DeepTutor env/reward/observation vectorization via make_rl_student_env
- Uses Stable-Baselines3 RecurrentPPO (LSTM policy) for training/inference
- Persists env state and policy per deck via database methods
- Supports per-cloze mapping: "card:{id}:cloze:{n}" are distinct items
"""
from __future__ import annotations

import io
import json
import math
import pickle
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np

from app.srs.DeepTutor import EFCEnv, HLREnv, DASHEnv, make_rl_student_env, StudentEnv

# SB3 (recurrent PPO via sb3-contrib)
try:
    from sb3_contrib import RecurrentPPO
    # Avoid importing policy classes directly for version portability
    from stable_baselines3.common.vec_env import DummyVecEnv
    from stable_baselines3.common.utils import set_random_seed
    try:
        import gym
    except Exception:
        import gymnasium as gym
    import stable_baselines3 as _sb3
    import sb3_contrib as _sb3c
except Exception as _e:  # pragma: no cover
    RecurrentPPO = None  # type: ignore
    gym = None  # type: ignore
    _SB3_IMPORT_ERR = _e
else:
    _SB3_IMPORT_ERR = None

DAY = 24 * 60 * 60


if gym is not None:
    class DTGymWrapper(gym.Env):
        """Wraps a DeepTutor StudentEnv to standard Gym step/reset for SB3 training."""
        metadata = {"render_modes": []}

        def __init__(self, base_env: StudentEnv):
            super().__init__()
            self.env = base_env
            self.action_space = self.env.action_space
            self.observation_space = self.env.observation_space

        def reset(self, *, seed: Optional[int] = None, options: Optional[dict] = None):
            obs = self.env._reset()
            return obs, {}

        def step(self, action):
            obs, rew, done, info = self.env._step(int(action))
            truncated = False
            return obs, float(rew), bool(done), bool(truncated), info
else:
    DTGymWrapper = None  # type: ignore


class DeepTutorAdapter:
    """
    Per-deck controller.
    Responsibilities:
    - Maintain item_map between app card ids (and clozes) and DeepTutor item indices
    - Hold DeepTutor env (EFC/HLR/DASH) with make_rl_student_env vectorization
    - Train and run SB3 RecurrentPPO (LSTM policy)
    - Persist env state and policy parameters via Database CRUD methods
    - Compute approximate next_review timestamps to backfill srs_data
    """

    def __init__(self, database, deck_id: int, model: str = "EFC", reward_func: str = "log_likelihood"):
        if _SB3_IMPORT_ERR is not None:
            raise RuntimeError(f"Stable-Baselines3 not available: {_SB3_IMPORT_ERR}")
        self.db = database
        self.deck_id = deck_id
        self.model_name = model
        self.reward_func = reward_func
        self.item_map: Dict[str, int] = {}
        self.rev_item_map: List[str] = []
        self.env: Optional[StudentEnv] = None
        self.sb3_model: Optional[RecurrentPPO] = None
        self.last_obs = None
        self.lib_info = f"sb3c:RecurrentPPO:{getattr(_sb3c, '__version__', 'unknown')}|sb3:{getattr(_sb3, '__version__', 'unknown')}"
        self._load_or_initialize()

    # ---------- Public API ----------
    def register_cards(self, card_ids: List[int], cloze_map: Optional[Dict[int, List[int]]] = None):
        """Ensure all card ids (and clozes) exist in the mapping. New ones appended at end.
        cloze_map: {card_id: [cloze_indices]} for cloze cards.
        """
        for cid in card_ids:
            added = False
            # register clozes first, if any
            has_clozes = bool(cloze_map and cid in cloze_map and cloze_map[cid])
            if has_clozes:
                for cidx in sorted(set(cloze_map[cid])):
                    key = f"card:{cid}:cloze:{cidx}"
                    if key not in self.item_map:
                        self.item_map[key] = len(self.rev_item_map)
                        self.rev_item_map.append(key)
                        added = True
            # Register base card only if there are no clozes
            if not has_clozes:
                base_key = f"card:{cid}"
                if base_key not in self.item_map:
                    self.item_map[base_key] = len(self.rev_item_map)
                    self.rev_item_map.append(base_key)
                    added = True
        self._maybe_resize_env()
        self._persist_model_state()
        # Ensure env capacity >= number of mapped items
        if self.env is not None and hasattr(self.env, 'n_items') and self.env.n_items < len(self.rev_item_map):
            self._maybe_resize_env()

    def next_items(self, k: int = 50) -> List[int]:
        """Return next k card_ids chosen by the current policy. Does not mutate state."""
        if self.env is None:
            return []
        selected: List[int] = []
        # Use policy to sample actions from current last_obs; if not trained, fall back to greedy likelihood
        if self.sb3_model is None:
            # Greedy on 1 - likelihood (prioritize the lowest recall likelihood)
            lik = self.env._recall_likelihoods()
            order = list(np.argsort(lik))  # ascending recall probability
            for idx in order:
                key = self.rev_item_map[idx]
                if key.startswith("card:"):
                    # map cloze keys to base card id
                    parts = key.split(":")
                    cid = int(parts[1])
                    if cid not in selected:
                        selected.append(cid)
                        if len(selected) >= k:
                            break
            return selected

        obs = self._ensure_obs()
        seen_cards = set()
        for _ in range(min(k * 4, len(self.rev_item_map))):
            action, _ = self.sb3_model.predict(obs, deterministic=True)
            idx = int(action)
            if 0 <= idx < len(self.rev_item_map):
                key = self.rev_item_map[idx]
                if key.startswith("card:"):
                    parts = key.split(":")
                    cid = int(parts[1])
                    if cid not in seen_cards:
                        selected.append(cid)
                        seen_cards.add(cid)
                        if len(selected) >= k:
                            break
            # small noise on outcome bit
            obs = obs.copy()
            if obs.shape[-1] >= 1:
                obs[-1] = 1 - obs[-1]
        if not selected:
            # fallback greedy
            lik = self.env._recall_likelihoods()
            order = list(np.argsort(lik))
            for idx in order:
                key = self.rev_item_map[idx]
                if key.startswith("card:"):
                    parts = key.split(":")
                    cid = int(parts[1])
                    if cid not in selected:
                        selected.append(cid)
                        if len(selected) >= k:
                            break
        return selected

    def update_after_review(self, card_id: int, grade: int, timestamp: Optional[datetime] = None, cloze_index: Optional[int] = None):
        """Update env given user's grade on the card or a specific cloze.
        grade >= 2 -> outcome=1 else 0.
        """
        if self.env is None:
            return
        ts = int((timestamp or datetime.now()).timestamp())
        key = f"card:{card_id}:cloze:{cloze_index}" if cloze_index is not None else f"card:{card_id}"
        item = self._key_to_index(key)
        if item is None:
            # unseen: register this card/cloze
            cloze_map = {card_id: [cloze_index]} if cloze_index is not None else None
            self.register_cards([card_id], cloze_map=cloze_map)
            item = self._key_to_index(key)
        # Ensure env capacity matches mapping
        self._maybe_resize_env()
        outcome = 1 if grade >= 2 else 0
        delay = max(1, ts - int(getattr(self.env, "now", 0)))
        # update env bookkeeping
        self.env.curr_item = item
        self.env.curr_outcome = outcome
        self.env.curr_delay = delay
        self.env.now = ts
        if getattr(self.env, "curr_step", None) is None:
            self.env.curr_step = 0
        self.env._update_model(item, outcome, ts, delay)
        self.env.curr_step += 1
        # refresh observation snapshot
        try:
            self.last_obs = make_rl_student_env(self.env)._obs()
        except Exception:
            self.last_obs = None
        self._persist_model_state()

    def train_policy(self, total_timesteps: int = 4000, seed: int = 0):
        """Train RecurrentPPO on a DTGymWrapper around a copy of the env."""
        if self.env is None:
            return
        set_random_seed(seed)
        # Build a fresh training env with same parameters/state
        env_copy = pickle.loads(pickle.dumps(self.env))
        rl_env = make_rl_student_env(env_copy)
        gym_env = DTGymWrapper(rl_env)
        vec = DummyVecEnv([lambda: gym_env])
        # Recurrent PPO with default policy (let library choose suitable recurrent policy)
        self.sb3_model = RecurrentPPO('MlpLstmPolicy', vec, verbose=0)
        self.sb3_model.learn(total_timesteps=total_timesteps)
        self._persist_policy()

    def compute_next_review_time(self, card_id: int, target_lik: float = 0.5, cloze_index: Optional[int] = None) -> datetime:
        """Approximate next review time by solving DeepTutor EFC likelihood for delay.
        Supports per-cloze by using the cloze-specific item index when available.
        """
        now_ts = int(getattr(self.env, "now", int(time.time())))
        key = f"card:{card_id}:cloze:{cloze_index}" if cloze_index is not None else f"card:{card_id}"
        idx = self._key_to_index(key)
        if idx is None:
            return datetime.fromtimestamp(now_ts)
        strength = 1.0
        rate = 0.1
        if isinstance(self.env, EFCEnv):
            strength = float(self.env.strengths[idx])
            rate = float(self.env.item_decay_rates[idx])
        elif isinstance(self.env, HLREnv):
            try:
                s = float(np.exp(np.dot(self.env.loglinear_coeffs, self.env.loglinear_feats[idx])))
                strength = max(1.0, s)
            except Exception:
                strength = 1.0
            rate = 0.1
        else:
            strength = 1.0
            rate = 0.1
        delay = max(1.0, -math.log(max(1e-6, target_lik)) * strength / max(1e-6, rate))
        return datetime.fromtimestamp(now_ts + int(delay))

    # ---------- Internals ----------
    def _load_or_initialize(self):
        row = self.db.get_dt_model(self.deck_id)
        if row:
            try:
                self.model_name = row.get("model", self.model_name)
                self.item_map = json.loads(row.get("item_map", "{}"))
                self.rev_item_map = [None] * (max(self.item_map.values()) + 1 if self.item_map else 0)
                for k, v in self.item_map.items():
                    if v >= len(self.rev_item_map):
                        self.rev_item_map.extend([None] * (v - len(self.rev_item_map) + 1))
                    self.rev_item_map[v] = k
                env_state = json.loads(row.get("env_state", "{}"))
                self._restore_env(env_state)
                policy_blob = row.get("policy_blob")
                if policy_blob:
                    self._load_policy_from_bytes(policy_blob)
            except Exception:
                self._init_fresh_env(n_items=1)
        else:
            self._init_fresh_env(n_items=1)
        if self.env is not None:
            # Ensure minimal observation fields exist on base env
            if getattr(self.env, 'curr_delay', None) is None:
                self.env.curr_delay = 0
            if getattr(self.env, 'curr_outcome', None) is None:
                self.env.curr_outcome = 1
            if getattr(self.env, 'curr_item', None) is None:
                self.env.curr_item = 0
            if getattr(self.env, 'curr_step', None) is None:
                self.env.curr_step = 0
            try:
                self.last_obs = make_rl_student_env(self.env)._obs()
            except Exception:
                self.last_obs = None

    def _init_fresh_env(self, n_items: int):
        if self.model_name.upper() == "HLR":
            env = HLREnv(n_items=n_items, reward_func=self.reward_func)
        elif self.model_name.upper() == "DASH":
            env = DASHEnv(n_items=n_items, reward_func=self.reward_func)
        else:
            env = EFCEnv(n_items=n_items, reward_func=self.reward_func)
        # Do NOT clear mappings here; they determine target size elsewhere
        self.env = env

    def _maybe_resize_env(self):
        # Expand env arrays if new items were registered
        target_n = max(1, len(self.rev_item_map))
        if self.env is None:
            self._init_fresh_env(n_items=target_n)
            return
        current_n = int(getattr(self.env, 'n_items', target_n))
        if current_n >= target_n:
            return
        # Preserve current state
        old_state = self._env_state()
        old_n = int(old_state.get('n_items', current_n))
        # Init new env with target_n
        self._init_fresh_env(n_items=target_n)
        e = self.env
        # Initialize arrays up to target_n if needed
        if isinstance(e, EFCEnv):
            e.tlasts[:old_n] = np.array(old_state.get('tlasts', [0]*old_n))[:old_n]
            e.strengths[:old_n] = np.array(old_state.get('strengths', [1]*old_n))[:old_n]
            e.item_decay_rates[:old_n] = np.array(old_state.get('item_decay_rates', [0.1]*old_n))[:old_n]
            e.now = int(old_state.get('now', getattr(e, 'now', 0)))
            e.curr_step = int(old_state.get('curr_step', 0))
        elif isinstance(e, HLREnv):
            e.tlasts[:old_n] = np.array(old_state.get('tlasts', [0]*old_n))[:old_n]
            e.loglinear_feats[:old_n, :] = np.array(old_state.get('loglinear_feats', np.zeros_like(e.loglinear_feats)))[:old_n, :]
            e.loglinear_coeffs[:] = np.array(old_state.get('loglinear_coeffs', e.loglinear_coeffs))
            e.now = int(old_state.get('now', getattr(e, 'now', 0)))
            e.curr_step = int(old_state.get('curr_step', 0))
        elif isinstance(e, DASHEnv):
            e.tlasts[:old_n] = np.array(old_state.get('tlasts', [0]*old_n))[:old_n]
            e.n_correct[:old_n] = np.array(old_state.get('n_correct', [0]*old_n))[:old_n]
            e.n_attempts[:old_n] = np.array(old_state.get('n_attempts', [0]*old_n))[:old_n]
            e.window_cw[:old_n] = np.array(old_state.get('window_cw', [0]*old_n))[:old_n]
            e.window_nw[:old_n] = np.array(old_state.get('window_nw', [0]*old_n))[:old_n]
            e.item_decay_exps[:old_n] = np.array(old_state.get('item_decay_exps', [1]*old_n))[:old_n]
            e.student_decay_exp = float(old_state.get('student_decay_exp', getattr(e, 'student_decay_exp', 0.0)))
            e.delay_coef = float(old_state.get('delay_coef', getattr(e, 'delay_coef', 1.0)))
            e.now = int(old_state.get('now', getattr(e, 'now', 0)))
            e.curr_step = int(old_state.get('curr_step', 0))
        # Minimal obs fields
        if getattr(e, 'curr_delay', None) is None:
            e.curr_delay = 0
        if getattr(e, 'curr_outcome', None) is None:
            e.curr_outcome = 1
        if getattr(e, 'curr_item', None) is None:
            e.curr_item = 0
        if getattr(e, 'curr_step', None) is None:
            e.curr_step = 0
        # Note: do not wrap with make_rl_student_env here; keep base env for adapter bookkeeping
        try:
            self.last_obs = make_rl_student_env(self.env)._obs()
        except Exception:
            self.last_obs = None

    def _restore_env(self, state: Dict):
        model = state.get("model", self.model_name)
        n_items = int(state.get("n_items", 1))
        self.model_name = model
        self._init_fresh_env(n_items=n_items)
        if isinstance(self.env, EFCEnv):
            for field in ["tlasts", "strengths", "item_decay_rates", "now", "curr_step"]:
                if field in state:
                    setattr(self.env, field, np.array(state[field]) if isinstance(state[field], list) else state[field])
        elif isinstance(self.env, HLREnv):
            for field in ["tlasts", "loglinear_feats", "loglinear_coeffs", "now", "curr_step"]:
                if field in state:
                    val = state[field]
                    if isinstance(val, list):
                        val = np.array(val)
                    setattr(self.env, field, val)
        elif isinstance(self.env, DASHEnv):
            for field in ["tlasts", "n_correct", "n_attempts", "window_cw", "window_nw", "item_decay_exps", "student_decay_exp", "delay_coef", "now", "curr_step"]:
                if field in state:
                    val = state[field]
                    if isinstance(val, list):
                        val = np.array(val)
                    setattr(self.env, field, val)

    def _env_state(self) -> Dict:
        state = {"model": self.model_name, "n_items": int(self.env.n_items if self.env else 0)}
        e = self.env
        if isinstance(e, EFCEnv):
            state.update({
                "tlasts": e.tlasts.tolist(),
                "strengths": e.strengths.tolist(),
                "item_decay_rates": e.item_decay_rates.tolist(),
                "now": int(e.now),
                "curr_step": int(e.curr_step or 0),
            })
        elif isinstance(e, HLREnv):
            state.update({
                "tlasts": e.tlasts.tolist(),
                "loglinear_feats": e.loglinear_feats.tolist(),
                "loglinear_coeffs": e.loglinear_coeffs.tolist(),
                "now": int(e.now),
                "curr_step": int(e.curr_step or 0),
            })
        elif isinstance(e, DASHEnv):
            state.update({
                "tlasts": e.tlasts.tolist(),
                "n_correct": e.n_correct.tolist(),
                "n_attempts": e.n_attempts.tolist(),
                "window_cw": e.window_cw.tolist(),
                "window_nw": e.window_nw.tolist(),
                "item_decay_exps": e.item_decay_exps.tolist(),
                "student_decay_exp": float(e.student_decay_exp),
                "delay_coef": float(e.delay_coef),
                "now": int(e.now),
                "curr_step": int(e.curr_step or 0),
            })
        return state

    def _persist_model_state(self):
        model_row = {
            "model": self.model_name,
            "tutor": "RL",
            "item_map": json.dumps(self.item_map),
            "env_state": json.dumps(self._env_state()),
            "policy_blob": self._policy_bytes() if self.sb3_model else None,
            "reward_history": json.dumps([]),
            "lib_info": self.lib_info,
        }
        self.db.upsert_dt_model(self.deck_id, **model_row)

    def _persist_policy(self):
        self.db.update_dt_policy(self.deck_id, self._policy_bytes())

    def _policy_bytes(self) -> bytes:
        if self.sb3_model is None:
            return b""
        # Save only parameter dict for robustness
        params = self.sb3_model.get_parameters()
        meta = {
            "lib_info": self.lib_info,
            "policy_class": "RecurrentPPO",
        }
        payload = {"params": params, "meta": meta}
        return pickle.dumps(payload)

    def _load_policy_from_bytes(self, data: bytes):
        if not data:
            return
        payload = pickle.loads(data)
        meta = payload.get("meta", {})
        params = payload.get("params", {})
        # Basic compatibility check
        if "sb3c:RecurrentPPO" not in meta.get("lib_info", ""):
            return
        # Recreate a minimal model if absent
        if self.sb3_model is None and DTGymWrapper is not None:
            dummy_env = DummyVecEnv([lambda: DTGymWrapper(self.env)])
            self.sb3_model = RecurrentPPO('MlpLstmPolicy', dummy_env, verbose=0)
        if self.sb3_model is not None and params:
            self.sb3_model.set_parameters(params)

    def _ensure_obs(self):
        if self.last_obs is None:
            self.last_obs = self.env._obs()
        return self.last_obs

    def _key_to_index(self, key: str) -> Optional[int]:
        if key in self.item_map:
            return int(self.item_map[key])
        return None

