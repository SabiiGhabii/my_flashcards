"""
Spaced Repetition System (SRS) Engine
Based on DeepTutor's SuperMnemoTutor implementation with SM-2 algorithm.
Extended to support per-cloze grading ({{cN::...}} in front text).
"""

import re
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Constants
HOUR = 60 * 60
DAY = 24 * HOUR

class SRSCard:
    def __init__(self, card_id: int):
        self.card_id = card_id
        self.grade = 0
        self.next_rep = 0
        self.last_rep = 0
        self.easiness = 2.5
        self.acq_reps = 0
        self.acq_reps_since_lapse = 0
        self.ret_reps = 0
        self.ret_reps_since_lapse = 0
        self.lapses = 0
        self.category = "short_term"

class SRSEngine:
    def __init__(self, fail_grade: int = 0, pass_grade: int = 2):
        self.fail_grade = fail_grade
        self.pass_grade = pass_grade
        self.cards: Dict[int, SRSCard] = {}
        self.current_time = datetime.now()

    @staticmethod
    def extract_cloze_indices(front_text: str) -> List[int]:
        return sorted(set(int(m.group(1)) for m in re.finditer(r"\{\{c(\d+)::", front_text)))

    @staticmethod
    def blank_cloze(front_text: str) -> str:
        return re.sub(r"\{\{c\d+::(.*?)\}\}", "[ ... ]", front_text)
    
    def add_card(self, card_id: int) -> SRSCard:
        """Add a new card to the SRS system."""
        if card_id not in self.cards:
            self.cards[card_id] = SRSCard(card_id)
        return self.cards[card_id]
    
    def get_card(self, card_id: int) -> Optional[SRSCard]:
        """Get a card from the SRS system."""
        return self.cards.get(card_id)
    
    def update_time(self, current_time: datetime = None):
        """Update the current time for the SRS system."""
        self.current_time = current_time or datetime.now()
    
    def calculate_initial_interval(self, grade: int) -> int:
        """
        Calculate initial interval for a card based on its first grade.
        Returns interval in seconds.
        """
        intervals = {
            0: 0,           # Fail - review immediately
            1: 0,           # Hard - review immediately  
            2: 1 * DAY,     # Good - 1 day
            3: 3 * DAY,     # Easy - 3 days
            4: 4 * DAY,     # Very easy - 4 days
            5: 7 * DAY      # Perfect - 7 days
        }
        return intervals.get(grade, 1 * DAY)
    
    def calculate_interval_noise(self, interval: int) -> int:
        """Add randomness to intervals to avoid clustering."""
        if interval == 0:
            return 0
        elif interval <= 10 * DAY:
            return random.choice([0, DAY])
        elif interval <= 60 * DAY:
            return int(random.uniform(-3 * DAY, 3 * DAY))
        else:
            return int(random.uniform(-0.05 * interval, 0.05 * interval))
    
    def true_scheduled_interval(self, card: SRSCard) -> int:
        """Calculate the true scheduled interval for a card."""
        interval = card.next_rep - card.last_rep
        if card.grade < 2:
            return interval
        return int(interval + HOUR)
    
    def grade_card(self, card_id: int, grade: int, timestamp: datetime = None) -> int:
        """
        Grade a card and update its scheduling parameters.
        Returns the new interval in seconds.
        """
        if timestamp is None:
            timestamp = self.current_time
        
        card = self.get_card(card_id)
        if not card:
            card = self.add_card(card_id)
        
        # Convert datetime to timestamp for calculations
        now_timestamp = int(timestamp.timestamp())
        
        # Determine timing (early, on time, late)
        if now_timestamp - DAY >= card.next_rep:
            timing = "LATE"
        elif now_timestamp < card.next_rep:
            timing = "EARLY"
        else:
            timing = "ON TIME"
        
        # Calculate intervals
        scheduled_interval = self.true_scheduled_interval(card)
        
        if card.grade == -1:  # Unseen card
            actual_interval = 0
        else:
            actual_interval = now_timestamp - card.last_rep
        
        # Grade-based scheduling logic
        if card.grade == -1:
            # First time seeing this card
            card.easiness = 2.5
            card.acq_reps = 1
            card.acq_reps_since_lapse = 1
            new_interval = self.calculate_initial_interval(grade)
            
        elif card.grade in [0, 1] and grade in [0, 1]:
            # In acquisition phase, staying there
            card.acq_reps += 1
            card.acq_reps_since_lapse += 1
            new_interval = 0  # Review immediately
            
        elif card.grade in [0, 1] and grade in [2, 3, 4, 5]:
            # Moving from acquisition to retention phase
            card.acq_reps += 1
            card.acq_reps_since_lapse += 1
            
            if grade == 2:
                new_interval = DAY
            elif grade == 3:
                new_interval = random.choice([1, 1, 2]) * DAY
            elif grade == 4:
                new_interval = random.choice([1, 2, 2]) * DAY
            elif grade == 5:
                new_interval = 2 * DAY
                
        elif card.grade in [2, 3, 4, 5] and grade in [0, 1]:
            # Dropping from retention to acquisition phase (lapse)
            card.ret_reps += 1
            card.lapses += 1
            card.acq_reps_since_lapse = 0
            card.ret_reps_since_lapse = 0
            new_interval = 0  # Review immediately
            
        elif card.grade in [2, 3, 4, 5] and grade in [2, 3, 4, 5]:
            # Staying in retention phase
            card.ret_reps += 1
            card.ret_reps_since_lapse += 1
            
            # Update easiness based on grade (only if not learning ahead)
            if timing in ["LATE", "ON TIME"]:
                if grade == 2:
                    card.easiness -= 0.16
                elif grade == 3:
                    card.easiness -= 0.14
                elif grade == 5:
                    card.easiness += 0.10
                
                # Ensure easiness doesn't go below 1.3
                if card.easiness < 1.3:
                    card.easiness = 1.3
            
            # Calculate new interval
            if card.ret_reps_since_lapse == 1:
                new_interval = 6 * DAY
            else:
                if grade in [2, 3]:
                    if timing in ["ON TIME", "EARLY"]:
                        new_interval = int(actual_interval * card.easiness)
                    else:
                        # Late review - don't increase interval too much
                        new_interval = scheduled_interval
                elif grade == 4:
                    new_interval = int(actual_interval * card.easiness)
                elif grade == 5:
                    if timing == "EARLY":
                        # Learning ahead - use scheduled interval
                        new_interval = scheduled_interval
                    else:
                        new_interval = int(actual_interval * card.easiness)
                
                # Ensure minimum interval of 1 day
                if new_interval < DAY:
                    new_interval = DAY
        
        # Add randomness to interval
        new_interval += self.calculate_interval_noise(new_interval)
        new_interval = max(0, new_interval)  # Ensure non-negative
        
        # Update card properties
        card.grade = grade
        card.last_rep = now_timestamp
        
        if grade >= 2:
            card.next_rep = card.last_rep + new_interval
            card.category = "long_term"
        else:
            card.next_rep = card.last_rep
            card.category = "short_term"
        
        return new_interval
    
    def get_due_cards(self, card_ids: List[int], category: str = None) -> List[int]:
        """Get cards that are due for review."""
        now_timestamp = int(self.current_time.timestamp())
        due_cards = []
        
        for card_id in card_ids:
            card = self.get_card(card_id)
            if not card:
                continue
                
            # Check if card is due
            if card.next_rep <= now_timestamp:
                # Filter by category if specified
                if category is None or card.category == category:
                    due_cards.append(card_id)
        
        # Sort by next_rep (most overdue first)
        due_cards.sort(key=lambda cid: self.cards[cid].next_rep)
        return due_cards
    
    def get_card_info(self, card_id: int) -> Dict:
        """Get detailed information about a card."""
        card = self.get_card(card_id)
        if not card:
            return {}
        
        next_review = datetime.fromtimestamp(card.next_rep) if card.next_rep > 0 else None
        last_review = datetime.fromtimestamp(card.last_rep) if card.last_rep > 0 else None
        
        return {
            'card_id': card.card_id,
            'grade': card.grade,
            'easiness': card.easiness,
            'interval_days': (card.next_rep - card.last_rep) // DAY if card.next_rep > card.last_rep else 0,
            'next_review': next_review,
            'last_review': last_review,
            'repetitions': card.acq_reps + card.ret_reps,
            'lapses': card.lapses,
            'category': card.category
        }
    
    def load_card_data(self, card_data: Dict):
        """Load card data from database."""
        card_id = card_data['card_id']
        card = self.add_card(card_id)
        
        card.grade = card_data.get('grade', 0)
        card.easiness = card_data.get('easiness', 2.5)
        card.lapses = card_data.get('lapses', 0)
        card.category = card_data.get('category', 'short_term')
        
        # Convert datetime to timestamp if needed
        if 'next_review' in card_data and card_data['next_review']:
            if isinstance(card_data['next_review'], datetime):
                card.next_rep = int(card_data['next_review'].timestamp())
            else:
                card.next_rep = card_data['next_review']
        
        if 'last_review' in card_data and card_data['last_review']:
            if isinstance(card_data['last_review'], datetime):
                card.last_rep = int(card_data['last_review'].timestamp())
            else:
                card.last_rep = card_data['last_review']
    
    def export_card_data(self, card_id: int) -> Dict:
        """Export card data for database storage."""
        card = self.get_card(card_id)
        if not card:
            return {}
        
        return {
            'easiness': card.easiness,
            'interval': (card.next_rep - card.last_rep) // DAY if card.next_rep > card.last_rep else 0,
            'repetitions': card.acq_reps + card.ret_reps,
            'next_review': datetime.fromtimestamp(card.next_rep) if card.next_rep > 0 else None,
            'last_review': datetime.fromtimestamp(card.last_rep) if card.last_rep > 0 else None,
            'lapses': card.lapses,
            'category': card.category,
            'grade': card.grade
        }
