"""
Study Sessions Module
Implements all study modes: Cram, Ingrain, Reviews, and Free Recall.
"""

import random
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum
from app.core.card_manager import CardManager


class StudyMode(Enum):
    CRAM = "cram"
    INGRAIN = "ingrain"
    REVIEW = "review"
    FREE_RECALL = "free_recall"


class SessionState(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"


class StudySession:
    """Base class for all study sessions."""
    
    def __init__(self, deck_id: int, session_type: StudyMode, card_manager: CardManager):
        self.deck_id = deck_id
        self.session_type = session_type
        self.card_manager = card_manager
        self.session_id = None
        self.state = SessionState.NOT_STARTED
        self.start_time = None
        self.end_time = None
        self.current_card_index = 0
        self.cards = []
        self.statistics = {
            'total_cards': 0,
            'correct_cards': 0,
            'incorrect_cards': 0,
            'total_time': 0,
            'average_response_time': 0,
            'rounds_completed': 0
        }
    
    def start_session(self):
        """Start the study session."""
        try:
            # Verify deck exists
            deck = self.card_manager.get_deck(self.deck_id)
            if not deck:
                raise ValueError(f"Deck with ID {self.deck_id} does not exist")

            self.session_id = self.card_manager.db.create_session(self.deck_id, self.session_type.value)
            self.state = SessionState.IN_PROGRESS
            self.start_time = datetime.now()
            self._initialize_cards()

            if not self.cards:
                raise ValueError("No cards available for study session")

        except Exception as e:
            self.state = SessionState.ERROR
            raise Exception(f"Failed to start study session: {str(e)}")
    
    def end_session(self):
        """End the study session."""
        self.state = SessionState.COMPLETED
        self.end_time = datetime.now()
        
        if self.start_time and self.end_time:
            self.statistics['total_time'] = (self.end_time - self.start_time).total_seconds()
        
        # Update session in database
        self.card_manager.db.update_session(
            self.session_id,
            completed_at=self.end_time,
            total_cards=self.statistics['total_cards'],
            correct_cards=self.statistics['correct_cards'],
            session_data=self.statistics
        )
    
    def _initialize_cards(self):
        """Initialize cards for the session. Override in subclasses."""
        raise NotImplementedError
    
    def get_current_card(self) -> Optional[Dict]:
        """Get the current card to study."""
        if 0 <= self.current_card_index < len(self.cards):
            return self.cards[self.current_card_index]
        return None
    
    def has_more_cards(self) -> bool:
        """Check if there are more cards to study."""
        return self.current_card_index < len(self.cards)


class CramSession(StudySession):
    """Cram study mode - Quizlet-style learning with rounds."""
    
    def __init__(self, deck_id: int, card_manager: CardManager):
        super().__init__(deck_id, StudyMode.CRAM, card_manager)
        self.current_round = 1
        self.incorrect_cards = []
        self.round_statistics = []
    
    def _initialize_cards(self):
        """Initialize cards for cramming."""
        all_cards = self.card_manager.get_deck_cards(self.deck_id)
        self.cards = random.sample(all_cards, len(all_cards))  # Shuffle cards
        self.statistics['total_cards'] = len(self.cards)
    
    def answer_card(self, correct: bool, response_time: float = None) -> Dict:
        """
        Answer the current card.
        Returns information about the response and next action.
        """
        current_card = self.get_current_card()
        if not current_card:
            return {'error': 'No current card'}
        
        # Record the response
        response = 'correct' if correct else 'incorrect'
        self.card_manager.mark_card_response(
            current_card['id'], response, response_time, self.session_id
        )
        
        # Update statistics
        if correct:
            self.statistics['correct_cards'] += 1
        else:
            self.statistics['incorrect_cards'] += 1
            self.incorrect_cards.append(current_card)
        
        # Move to next card
        self.current_card_index += 1
        
        # Check if round is complete
        if not self.has_more_cards():
            return self._complete_round()
        
        return {
            'status': 'continue',
            'next_card': self.get_current_card(),
            'progress': f"{self.current_card_index}/{len(self.cards)}"
        }
    
    def _complete_round(self) -> Dict:
        """Complete the current round and prepare for next."""
        round_stats = {
            'round': self.current_round,
            'total_cards': len(self.cards),
            'correct': self.statistics['correct_cards'],
            'incorrect': len(self.incorrect_cards),
            'accuracy': (self.statistics['correct_cards'] / len(self.cards)) * 100 if self.cards else 0
        }
        self.round_statistics.append(round_stats)
        
        if not self.incorrect_cards:
            # All cards learned - session complete
            self.end_session()
            return {
                'status': 'session_complete',
                'round_stats': round_stats,
                'session_stats': self.statistics,
                'all_rounds': self.round_statistics
            }
        else:
            # Prepare next round with incorrect cards
            return {
                'status': 'round_complete',
                'round_stats': round_stats,
                'next_round_cards': len(self.incorrect_cards)
            }
    
    def start_next_round(self):
        """Start the next round with incorrect cards."""
        self.current_round += 1
        self.cards = random.sample(self.incorrect_cards, len(self.incorrect_cards))
        self.incorrect_cards = []
        self.current_card_index = 0
        
        # Reset round-specific statistics
        round_correct = self.statistics['correct_cards']
        self.statistics['correct_cards'] = 0
        self.statistics['incorrect_cards'] = 0


class IngrainSession(StudySession):
    """Ingrain study mode - hybrid short-term/long-term learning."""
    
    def __init__(self, deck_id: int, card_manager: CardManager):
        super().__init__(deck_id, StudyMode.INGRAIN, card_manager)
        self.phase = "cram"  # "cram" or "review"
        self.card_responses = {}  # Track responses for each card
        self.consecutive_responses = {}  # Track consecutive correct/incorrect
    
    def _initialize_cards(self):
        """Initialize cards for ingrain session."""
        # Start with short-term cards for cram phase
        short_term_cards = self.card_manager.get_cards_by_category(self.deck_id, "short_term")
        if short_term_cards:
            self.cards = random.sample(short_term_cards, len(short_term_cards))
            self.phase = "cram"
        else:
            # No short-term cards, go directly to review phase
            self.cards = self.card_manager.get_due_cards(self.deck_id, "long_term")
            self.phase = "review"
        
        self.statistics['total_cards'] = len(self.cards)
    
    def answer_card(self, response: str, response_time: float = None) -> Dict:
        """
        Answer card with ingrain-specific responses.
        response: 'short_term', 'unknown', 'good', 'long_term', 'forgot'
        """
        current_card = self.get_current_card()
        if not current_card:
            return {'error': 'No current card'}
        
        card_id = current_card['id']
        
        # Initialize tracking for this card if needed
        if card_id not in self.card_responses:
            self.card_responses[card_id] = []
            self.consecutive_responses[card_id] = {'unknown': 0, 'good': 0, 'views': 0}
        
        # Record response
        self.card_responses[card_id].append(response)
        self.consecutive_responses[card_id]['views'] += 1
        
        # Update consecutive counters
        if response == 'unknown':
            self.consecutive_responses[card_id]['unknown'] += 1
            self.consecutive_responses[card_id]['good'] = 0  # Reset good counter
        elif response == 'good':
            self.consecutive_responses[card_id]['good'] += 1
            self.consecutive_responses[card_id]['unknown'] = 0  # Reset unknown counter
        else:
            # Reset counters for direct categorization
            self.consecutive_responses[card_id]['unknown'] = 0
            self.consecutive_responses[card_id]['good'] = 0
        
        # Determine card categorization
        new_category = self._determine_card_category(card_id, response)
        
        # Update card category in database
        if new_category:
            self.card_manager.db.update_srs_data(card_id, category=new_category)
        
        # Record the response
        self.card_manager.mark_card_response(card_id, response, response_time, self.session_id)
        
        # Move to next card
        self.current_card_index += 1
        
        if not self.has_more_cards():
            return self._complete_phase()
        
        return {
            'status': 'continue',
            'next_card': self.get_current_card(),
            'progress': f"{self.current_card_index}/{len(self.cards)}",
            'phase': self.phase
        }
    
    def _determine_card_category(self, card_id: int, response: str) -> Optional[str]:
        """Determine if card should move between categories."""
        consecutive = self.consecutive_responses[card_id]
        
        # Direct categorization
        if response == 'short_term':
            return 'short_term'
        elif response == 'long_term':
            return 'long_term'
        
        # Rule-based categorization
        if consecutive['unknown'] >= 3:
            return 'short_term'
        elif consecutive['good'] >= 2:
            return 'long_term'
        elif consecutive['views'] >= 5:
            # Force categorization after 5 views
            if consecutive['good'] > consecutive['unknown']:
                return 'long_term'
            else:
                return 'short_term'
        
        return None  # No category change
    
    def _complete_phase(self) -> Dict:
        """Complete current phase and transition if needed."""
        if self.phase == "cram":
            # Check if we need to do review phase
            long_term_due = self.card_manager.get_due_cards(self.deck_id, "long_term")
            if long_term_due:
                self.phase = "review"
                self.cards = long_term_due
                self.current_card_index = 0
                return {
                    'status': 'phase_transition',
                    'new_phase': 'review',
                    'cards_count': len(self.cards)
                }
            else:
                # No review needed, session complete
                self.end_session()
                return {'status': 'session_complete', 'session_stats': self.statistics}
        else:
            # Review phase complete
            self.end_session()
            return {'status': 'session_complete', 'session_stats': self.statistics}


class ReviewSession(StudySession):
    """Review study mode - pure SRS reviews."""
    
    def __init__(self, deck_id: int, card_manager: CardManager):
        super().__init__(deck_id, StudyMode.REVIEW, card_manager)
    
    def _initialize_cards(self):
        """Initialize cards for review (DeepTutor policy-driven selection)."""
        self.cards = self.card_manager.get_due_cards(self.deck_id)
        self.statistics['total_cards'] = len(self.cards)

    def grade_card(self, grade: int, response_time: float = None, cloze_index: int = None) -> Dict:
        """Grade card using DeepTutor policy (0-5 scale). Supports per-cloze grading for logging only."""
        # Validate inputs
        if grade < 0 or grade > 5:
            return {'error': 'Grade must be between 0 and 5'}

        if response_time is not None and response_time < 0:
            return {'error': 'Response time cannot be negative'}

        current_card = self.get_current_card()
        if not current_card:
            return {'error': 'No current card'}

        try:
            # Grade the card using SRS (pass cloze_index if provided)
            updated_card = self.card_manager.grade_card(
                current_card['id'], grade, response_time, self.session_id, cloze_index=cloze_index
            )

            # Update statistics
            if grade >= 2:  # Consider grade 2+ as correct
                self.statistics['correct_cards'] += 1
            else:
                self.statistics['incorrect_cards'] += 1

            # Move to next card
            self.current_card_index += 1
        except Exception as e:
            return {'error': f'Failed to grade card: {str(e)}'}

        if not self.has_more_cards():
            self.end_session()
            return {'status': 'session_complete', 'session_stats': self.statistics}

        return {
            'status': 'continue',
            'next_card': self.get_current_card(),
            'updated_card_info': updated_card,
            'progress': f"{self.current_card_index}/{len(self.cards)}"
        }


class FreeRecallSession(StudySession):
    """Free Recall study mode - memory test without prompts."""
    
    def __init__(self, deck_id: int, card_manager: CardManager, source_session_type: str = "all"):
        super().__init__(deck_id, StudyMode.FREE_RECALL, card_manager)
        self.source_session_type = source_session_type  # "cram", "review", "all"
        self.user_responses = []
        self.similarity_scores = []
        self.recall_complete = False
    
    def _initialize_cards(self):
        """Initialize cards based on source session type."""
        if self.source_session_type == "all":
            self.cards = self.card_manager.get_deck_cards(self.deck_id)
        else:
            # For now, use all cards. In a full implementation, 
            # this would filter based on last session of specified type
            self.cards = self.card_manager.get_deck_cards(self.deck_id)
        
        self.statistics['total_cards'] = len(self.cards)
    
    def submit_recall_responses(self, responses: List[Dict]) -> Dict:
        """
        Submit user's free recall responses.
        responses: List of {'front': str, 'back': str} dictionaries
        """
        self.user_responses = responses
        self.recall_complete = True
        
        # Calculate similarity scores (simplified version)
        self.similarity_scores = self._calculate_similarity_scores()
        
        # Generate results
        results = []
        for i, card in enumerate(self.cards):
            user_response = responses[i] if i < len(responses) else {'front': '', 'back': ''}
            similarity = self.similarity_scores[i] if i < len(self.similarity_scores) else 0.0
            
            results.append({
                'card_id': card['id'],
                'actual_front': card['front'],
                'actual_back': card['back'],
                'user_front': user_response['front'],
                'user_back': user_response['back'],
                'similarity_score': similarity,
                'recalled': similarity > 0.5  # Threshold for "recalled"
            })
        
        # Update statistics
        recalled_count = sum(1 for r in results if r['recalled'])
        self.statistics['correct_cards'] = recalled_count
        self.statistics['incorrect_cards'] = len(results) - recalled_count
        
        return {
            'status': 'recall_complete',
            'results': results,
            'statistics': self.statistics,
            'missed_cards': [r for r in results if not r['recalled']]
        }
    
    def _calculate_similarity_scores(self) -> List[float]:
        """Calculate similarity scores between user responses and actual cards."""
        # Simplified similarity calculation
        # In a full implementation, this would use sentence transformers or similar
        scores = []
        
        for i, card in enumerate(self.cards):
            if i >= len(self.user_responses):
                scores.append(0.0)
                continue
            
            user_resp = self.user_responses[i]
            
            # Simple word overlap similarity
            front_similarity = self._word_overlap_similarity(
                card['front'].lower(), user_resp['front'].lower()
            )
            back_similarity = self._word_overlap_similarity(
                card['back'].lower(), user_resp['back'].lower()
            )
            
            # Average of front and back similarity
            avg_similarity = (front_similarity + back_similarity) / 2
            scores.append(avg_similarity)
        
        return scores
    
    def _word_overlap_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity based on word overlap."""
        if not text1.strip() or not text2.strip():
            return 0.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0


class SessionManager:
    """Manages study sessions and provides session factory."""
    
    def __init__(self, card_manager: CardManager):
        self.card_manager = card_manager
        self.active_sessions = {}
    
    def create_session(self, deck_id: int, session_type: StudyMode, **kwargs) -> StudySession:
        """Create a new study session."""
        if session_type == StudyMode.CRAM:
            session = CramSession(deck_id, self.card_manager)
        elif session_type == StudyMode.INGRAIN:
            session = IngrainSession(deck_id, self.card_manager)
        elif session_type == StudyMode.REVIEW:
            session = ReviewSession(deck_id, self.card_manager)
        elif session_type == StudyMode.FREE_RECALL:
            source_type = kwargs.get('source_session_type', 'all')
            session = FreeRecallSession(deck_id, self.card_manager, source_type)
        else:
            raise ValueError(f"Unknown session type: {session_type}")
        
        session.start_session()
        self.active_sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: int) -> Optional[StudySession]:
        """Get an active session by ID."""
        return self.active_sessions.get(session_id)
    
    def end_session(self, session_id: int):
        """End and remove a session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.end_session()
            del self.active_sessions[session_id]
