# DeepTutor RL Integration Plan (SB3-based)

This document describes the design and implementation steps taken to replace the legacy SM-2 engine with the actual DeepTutor environments and a modern RL policy.

## Summary
- We preserve DeepTutor.py environment code (EFCEnv/HLREnv/DASHEnv), reward functions, and observation vectorization (make_rl_student_env).
- We port the policy side from rllab/TRPO+GRU to Stable-Baselines3 RecurrentPPO (LSTM policy), while keeping the DeepTutor environments unchanged.
- A new DeepTutorAdapter becomes the sole scheduling engine for long-term reviews, providing training, inference, and persistence per deck.

## Key Components
- DeepTutor.py (preserved; small import guards for rllab and notebook magics).
- dt_adapter.py
  - DTGymWrapper: wraps DeepTutor StudentEnv into a standard Gym Env (step/reset proxy to _step/_reset).
  - DeepTutorAdapter: per-deck controller. Builds env, handles item mapping, updates state from user reviews, runs SB3 policy training/inference, persists env+policy to DB, and computes approximate next_review timestamps for backward compatibility.

## Database Additions
- Table dt_models
  - deck_id (PRIMARY KEY)
  - model ('EFC'|'HLR'|'DASH')
  - tutor ('RL')
  - item_map (JSON: card_id -> item_index)
  - env_state (BLOB/JSON)
  - policy_blob (BLOB)
  - reward_history (JSON)
  - last_trained_at (TIMESTAMP)
  - lib_info (TEXT; e.g., 'sb3:RecurrentPPO')

## Integration Points
- card_manager.py
  - Replace SRSEngine with DeepTutorAdapter (one adapter per deck, lazy-init).
  - grade_card() updates DeepTutor env via adapter and persists next_review by solving DeepTutor EFC likelihood equation for a target probability threshold.
  - get_due_cards() asks adapter for next items instead of DB-only due query (adapter still writes approximate next_review to srs_data for compatibility).
- study_sessions.py (ReviewSession)
  - _initialize_cards() uses card_manager.get_due_cards() (policy-driven).

## Dependencies
- gym
- torch
- stable-baselines3 (RecurrentPPO via MlpLstmPolicy)

rllab is not required at runtime; DeepTutor’s rllab imports are guarded to avoid import-time failures.

## Cold Start & Migration
- Build item_map from current deck order. Initialize env state from existing srs_data when available (tlasts from last_review, strengths from repetitions; otherwise defaults from DeepTutor sampling).
- Cold start policy: train a small number of timesteps to initialize. Continue training periodically in the background.
- Fallback: If policy not available, adapter still computes next items via greedy on DeepTutor recall likelihoods.

## Verification
- Logging and test hooks:
  - Print the environment name and that selection path is DeepTutorAdapter, not SRSEngine.
  - Log recall likelihood vector and chosen action for several steps.
  - Expose an adapter.debug_select() method returning (obs, action, likelihoods).
- Unit tests (not yet added): item mapping stability; env state round-trip; next_review monotonic with target threshold.

## Notes
- DeepTutor notebook magics/plots are disabled at import time.
- We retain srs_data writes to avoid breaking any existing UI queries while the policy fully takes over scheduling.

