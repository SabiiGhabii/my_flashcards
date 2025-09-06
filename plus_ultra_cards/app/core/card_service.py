"""CardService: business logic for card operations with SRS integration."""

from typing import List, Dict, Optional
from datetime import datetime

from app.core.database import Database
from app.srs.factory import SrsFactory
from app.srs.interfaces import SrsEngine


class CardService:
    """Encapsulates card business logic and SRS engine coordination."""
    
    def __init__(self, db: Database):
        self.db = db
        self._engines: Dict[int, SrsEngine] = {}
    
    def _get_engine(self, deck_id: int) -> SrsEngine:
        """Get or create SRS engine for deck via factory."""
        if deck_id not in self._engines:
            self._engines[deck_id] = SrsFactory.create(self.db, deck_id)
        return self._engines[deck_id]
    
    def register_card(self, card_id: int, deck_id: int, front_text: str) -> None:
        """Register a single card with the SRS engine."""
        engine = self._get_engine(deck_id)
        cloze_indices = self._extract_cloze_indices(front_text)
        cloze_map = {card_id: cloze_indices} if cloze_indices else None
        engine.register([card_id], cloze_map=cloze_map)
        # Set next_review for immediate availability
        self.db.update_srs_data(card_id, next_review=datetime.now())
    
    def get_study_cards(self, deck_id: int, category: str = 'all') -> List[Dict]:
        """Get cards for study via SRS engine selection."""
        from app.core.config_manager import get_config
        config = get_config()
        engine_type = (config.get('srs.engine', 'deeptutor') or 'deeptutor').lower()
        
        cards = self.db.get_deck_cards(deck_id)
        if engine_type == 'sm2':
            # Legacy ordering by next_review
            return self.db.get_due_cards(deck_id, category)
        
        # DeepTutor or other engine
        engine = self._get_engine(deck_id)
        # Build cloze map for registrations
        cloze_map: Dict[int, List[int]] = {}
        for c in cards:
            inds = self._extract_cloze_indices(c.get('front', '') or '')
            if inds:
                cloze_map[c['id']] = inds
        engine.register([c['id'] for c in cards], cloze_map=cloze_map)
        selected_ids = engine.next_items(k=len(cards))
        id_to_card = {c['id']: c for c in cards}
        return [id_to_card[i] for i in selected_ids if i in id_to_card]
    
    def record_review_outcome(self, card_id: int, grade: int, cloze_index: Optional[int] = None) -> None:
        """Record review outcome with SRS engine."""
        card_data = self.db.get_card(card_id)
        if not card_data:
            raise ValueError(f"Card {card_id} not found")
        
        deck_id = card_data['deck_id']
        engine = self._get_engine(deck_id)
        metadata = {"grade": grade, "timestamp": datetime.now()}
        if cloze_index is not None:
            metadata["cloze_index"] = cloze_index
        engine.record_outcome(card_id, "reviewed", metadata)
    
    @staticmethod
    def _extract_cloze_indices(front_text: str) -> List[int]:
        """Extract cloze indices from front text."""
        import re
        pattern = r'\{\{c(\d+)::'
        matches = re.findall(pattern, front_text)
        return [int(m) for m in matches]
