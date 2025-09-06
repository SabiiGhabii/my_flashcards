from typing import List, Optional, Dict

from app.core.config_manager import get_config
from app.srs.interfaces import SrsEngine
from app.srs.dt_adapter import DeepTutorAdapter
from app.srs.sm2_engine import SRSEngine as SM2Engine


class DeepTutorSrsAdapter(SrsEngine):
    """Adapter to make DeepTutorAdapter conform to SrsEngine protocol."""
    def __init__(self, db, deck_id: int, model: str = 'EFC', reward_func: str = 'log_likelihood'):
        self.adapter = DeepTutorAdapter(db, deck_id=deck_id, model=model, reward_func=reward_func)
    def register(self, item_ids: List[int], cloze_map: Optional[Dict[int, List[int]]] = None) -> None:
        self.adapter.register_cards(item_ids, cloze_map=cloze_map)
    def next_items(self, k: int) -> List[int]:
        return self.adapter.next_items(k=k)
    def record_outcome(self, item_id: int, outcome: str, metadata: Optional[Dict] = None) -> None:
        grade = metadata.get("grade", 2) if metadata else 2
        cloze_index = metadata.get("cloze_index") if metadata else None
        from datetime import datetime
        self.adapter.update_after_review(item_id, grade, datetime.now(), cloze_index=cloze_index)

class SM2Adapter(SrsEngine):
    def __init__(self, db):
        self.engine = SM2Engine()
        self.db = db
    def register(self, item_ids: List[int], cloze_map: Optional[Dict[int, List[int]]] = None) -> None:
        for cid in item_ids:
            self.engine.add_card(cid)
    def next_items(self, k: int) -> List[int]:
        cards = list(self.engine.cards.keys())
        return cards[:k]
    def record_outcome(self, item_id: int, outcome: str, metadata: Optional[Dict] = None) -> None:
        grade = metadata.get("grade", 2) if metadata else 2
        self.engine.grade_card(item_id, grade)


class SrsFactory:
    @staticmethod
    def create(db, deck_id: int) -> SrsEngine:
        cfg = get_config()
        engine = (cfg.get('srs.engine', 'deeptutor') or 'deeptutor').lower()
        if engine == 'sm2':
            return SM2Adapter(db)
        # Default: DeepTutor
        # Model and reward come from config
        model = cfg.get('srs.deeptutor_model', 'EFC')
        reward = cfg.get('srs.deeptutor_reward_func', 'log_likelihood')
        return DeepTutorSrsAdapter(db, deck_id=deck_id, model=model, reward_func=reward)

