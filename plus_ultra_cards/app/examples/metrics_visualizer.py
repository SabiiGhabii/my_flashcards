"""
Interactive Metrics Visualization for DeepTutor Adapter
- Plotly-based statistical visualizations
- Pyvis-based network/graph visualization
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

import numpy as np

try:
    import plotly.graph_objects as go
    import plotly.express as px
except Exception as e:  # pragma: no cover
    go = None
    px = None
    _PLOTLY_ERR = e
else:
    _PLOTLY_ERR = None

try:
    from pyvis.network import Network
except Exception as e:  # pragma: no cover
    Network = None
    _PYVIS_ERR = e
else:
    _PYVIS_ERR = None

from dt_adapter import DeepTutorAdapter
from database import Database


@dataclass
class VizInput:
    deck_id: int
    card_ids: List[int]
    card_data: Dict[int, Dict]


class MetricsVisualizer:
    def __init__(self, db: Database):
        self.db = db

    def _get_adapter(self, deck_id: int) -> Optional[DeepTutorAdapter]:
        # Lightweight adapter just to read env state
        try:
            return DeepTutorAdapter(self.db, deck_id)
        except Exception:
            return None

    def _ensure_plotly(self):
        if _PLOTLY_ERR is not None:
            raise RuntimeError(f"Plotly not available: {_PLOTLY_ERR}")

    def _ensure_pyvis(self):
        if _PYVIS_ERR is not None:
            raise RuntimeError(f"Pyvis not available: {_PYVIS_ERR}")

    def get_viz_input(self, deck_id: int) -> VizInput:
        cards = self.db.get_deck_cards(deck_id)
        ids = [c['id'] for c in cards]
        mapping = {c['id']: c for c in cards}
        return VizInput(deck_id=deck_id, card_ids=ids, card_data=mapping)

    # 1) Per-item recall likelihood timeline
    def viz_item_recall_timeline(self, deck_id: int, card_id: int, cloze_index: Optional[int] = None):
        self._ensure_plotly()
        adapter = self._get_adapter(deck_id)
        if not adapter or not adapter.env:
            return go.Figure().add_annotation(text="No DeepTutor environment available", showarrow=False)
        # Create synthetic timeline using current env now and EFC-like equation
        # For demonstration: likelihood over next 30 days
        liks = []
        xs = []
        now_ts = int(getattr(adapter.env, 'now', 0) or datetime.now().timestamp())
        for d in range(0, 31):
            t = now_ts + d * 86400
            dt = datetime.fromtimestamp(t)
            xs.append(dt)
            key = f"card:{card_id}:cloze:{cloze_index}" if cloze_index is not None else f"card:{card_id}"
            idx = adapter._key_to_index(key)  # type: ignore
            if idx is None:
                liks.append(np.nan)
                continue
            try:
                if hasattr(adapter.env, 'item_decay_rates'):
                    # EFC approximation
                    strength = float(adapter.env.strengths[idx])
                    rate = float(adapter.env.item_decay_rates[idx])
                    delay = (t - int(adapter.env.now))
                    liks.append(np.exp(-rate * delay / max(1e-6, strength)))
                else:
                    # Generic fallback: monotonic decay proxy
                    delay = (t - int(adapter.env.now))
                    liks.append(np.exp(-delay / (5*86400)))
            except Exception:
                liks.append(np.nan)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=xs, y=liks, mode='lines', name='Recall Likelihood'))
        fig.update_layout(title=f'Recall Likelihood Timeline (card {card_id}{" cloze " + str(cloze_index) if cloze_index else ""})', xaxis_title='Date', yaxis_title='Likelihood', yaxis=dict(range=[0,1]))
        return fig

    # 2) Deck-level forgetting curve heatmap
    def viz_deck_forgetting_heatmap(self, deck_id: int):
        self._ensure_plotly()
        adapter = self._get_adapter(deck_id)
        if not adapter or not adapter.env:
            return go.Figure().add_annotation(text="No DeepTutor environment available", showarrow=False)
        n = len(adapter.rev_item_map)
        horizon = 10
        mat = np.zeros((n, horizon))
        for i in range(n):
            for d in range(horizon):
                try:
                    if hasattr(adapter.env, 'item_decay_rates'):
                        strength = float(adapter.env.strengths[i])
                        rate = float(adapter.env.item_decay_rates[i])
                        delay = (d+1) * 86400
                        mat[i, d] = np.exp(-rate * delay / max(1e-6, strength))
                    else:
                        mat[i, d] = np.exp(-(d+1)/5)
                except Exception:
                    mat[i, d] = np.nan
        fig = px.imshow(mat, color_continuous_scale='Viridis', labels=dict(x='Days Ahead', y='Item Index', color='Likelihood'))
        fig.update_layout(title='Deck-level Forgetting Curve Heatmap (likelihood)')
        return fig

    # 3) Scheduler action distribution vs recall bands
    def viz_action_distribution(self, deck_id: int):
        self._ensure_plotly()
        adapter = self._get_adapter(deck_id)
        if not adapter or not adapter.env:
            return go.Figure().add_annotation(text="No DeepTutor environment available", showarrow=False)
        lik = adapter.env._recall_likelihoods()
        bins = [0.0, 0.3, 0.6, 1.0]
        labels = ['<0.3', '0.3-0.6', '>0.6']
        counts = [int(((lik >= bins[i]) & (lik < bins[i+1])).sum()) for i in range(3)]
        fig = go.Figure(go.Bar(x=labels, y=counts, text=counts, textposition='auto'))
        fig.update_layout(title='Action Distribution vs Recall Bands (proxy)', xaxis_title='Recall Likelihood Band', yaxis_title='Count of Candidates')
        return fig

    # 4) Item mastery trajectories with cloze splitting
    def viz_item_mastery_trajectories(self, deck_id: int, card_id: int):
        self._ensure_plotly()
        adapter = self._get_adapter(deck_id)
        if not adapter or not adapter.env:
            return go.Figure().add_annotation(text="No DeepTutor environment available", showarrow=False)
        fig = go.Figure()
        # Find all cloze indices registered for this card
        clozes = sorted({int(k.split(':')[3]) for k in adapter.item_map if k.startswith(f"card:{card_id}:cloze:")})
        if not clozes:
            clozes = [None]
        for cidx in clozes:
            f = self.viz_item_recall_timeline(deck_id, card_id, cidx)
            if f.data:
                fig.add_trace(f.data[0])
        fig.update_layout(title=f'Item Mastery Trajectories (card {card_id})', xaxis_title='Date', yaxis_title='Likelihood', yaxis=dict(range=[0,1]))
        return fig

    # 5) Policy learning curve and stability bands (requires rew_chkpts; we synthesize from DB last_trained_at)
    def viz_policy_learning_curve(self, deck_id: int):
        self._ensure_plotly()
        row = self.db.get_dt_model(deck_id)
        if not row:
            return go.Figure().add_annotation(text="No DT model available", showarrow=False)
        # Placeholder: we don’t log episodic returns yet; use timestamps as x and synthetic returns
        ts = row.get('last_trained_at')
        if not ts:
            return go.Figure().add_annotation(text="No training history available", showarrow=False)
        xs = [datetime.fromisoformat(ts)]
        ys = [1.0]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=xs, y=ys, mode='lines+markers', name='Return'))
        fig.update_layout(title='Policy Learning Curve (placeholder)', xaxis_title='Time', yaxis_title='Return')
        return fig

    # 6) Delay vs recall likelihood scatter and fit
    def viz_delay_vs_likelihood(self, deck_id: int):
        self._ensure_plotly()
        adapter = self._get_adapter(deck_id)
        if not adapter or not adapter.env:
            return go.Figure().add_annotation(text="No DeepTutor environment available", showarrow=False)
        # Build scatter from current state: approximate delays as (now - tlasts)
        try:
            delays = (adapter.env.now - adapter.env.tlasts).astype(float)
            lik = adapter.env._recall_likelihoods()
        except Exception:
            return go.Figure().add_annotation(text="Insufficient data for delay vs likelihood", showarrow=False)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=delays, y=lik, mode='markers', name='Items'))
        # Fit simple 1/x curve in logspace: y ~ exp(-k * x / s)
        if hasattr(adapter.env, 'item_decay_rates'):
            k = float(np.nanmean(adapter.env.item_decay_rates / np.maximum(1e-6, adapter.env.strengths)))
            xline = np.linspace(0, np.nanmax(delays)+1, 50)
            yline = np.exp(-k * xline)
            fig.add_trace(go.Scatter(x=xline, y=yline, mode='lines', name='Fit'))
        fig.update_layout(title='Delay vs Recall Likelihood', xaxis_title='Delay (sec)', yaxis_title='Likelihood')
        return fig

    # 7) Pyvis network visualization (content similarity default)
    def viz_deck_network(self, deck_id: int, metric: str = 'content_similarity', output_html: Optional[str] = None):
        self._ensure_pyvis()
        vi = self.get_viz_input(deck_id)
        net = Network(height='700px', width='100%', bgcolor='#ffffff', font_color='black', notebook=False, directed=False)
        # Simple content similarity: cosine over bag-of-words TF vectors
        from collections import Counter
        import math
        def tokenize(text: str) -> List[str]:
            import re
            return re.findall(r"[A-Za-z0-9]+", text.lower())
        tf = {}
        for cid in vi.card_ids:
            c = vi.card_data[cid]
            tokens = tokenize((c.get('front') or '') + ' ' + (c.get('back') or ''))
            tf[cid] = Counter(tokens)
        # Build vocabulary
        vocab = {}
        for counter in tf.values():
            for w in counter:
                if w not in vocab:
                    vocab[w] = len(vocab)
        def vec(counter: Counter) -> np.ndarray:
            v = np.zeros(len(vocab), dtype=float)
            for w, cnt in counter.items():
                v[vocab[w]] = cnt
            return v
        vecs = {cid: vec(tf[cid]) for cid in vi.card_ids}
        def cosine(a: np.ndarray, b: np.ndarray) -> float:
            na = np.linalg.norm(a); nb = np.linalg.norm(b)
            if na == 0 or nb == 0: return 0.0
            return float(np.dot(a,b)/(na*nb))
        # Add nodes
        for cid in vi.card_ids:
            c = vi.card_data[cid]
            title = f"<b>{c.get('front','')}</b><br/>{c.get('back','')}"
            net.add_node(int(cid), label=str(cid), title=title)
        # Add edges for pairs above threshold
        ids = vi.card_ids
        for i in range(len(ids)):
            for j in range(i+1, len(ids)):
                s = cosine(vecs[ids[i]], vecs[ids[j]])
                if s >= 0.5:
                    net.add_edge(int(ids[i]), int(ids[j]), value=s)
        # Node size by review count
        for cid in vi.card_ids:
            reviews = self.db.get_card_reviews(cid)
            net.get_node(int(cid))["size"] = max(10, 10 + (len(reviews) if reviews else 0))
        if output_html is None:
            output_html = f"deck_{deck_id}_network.html"
        net.show(output_html)
        return output_html

