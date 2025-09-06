"""
Card Management Module
Handles CRUD operations for flashcards and deck management.
"""

import csv
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from app.core.database import Database
from app.core.config_manager import get_config
from app.core.card_service import CardService


class CardManager:
    """Manages flashcard operations and deck management."""
    
    def __init__(self, db_path: str = "data/cards.db"):
        self.db = Database(db_path)
        self._card_service = CardService(self.db)

    def close(self):
        """Close database connection."""
        self.db.close()

    def _normalize_tags(self, tags):
        """Normalize tags to a list format"""
        if not tags:
            return []

        if isinstance(tags, list):
            # Already a list, clean up any empty strings
            return [tag.strip() for tag in tags if tag and tag.strip()]

        if isinstance(tags, str):
            # Split comma-separated string into list
            if ',' in tags:
                return [tag.strip() for tag in tags.split(',') if tag and tag.strip()]
            else:
                # Single tag
                return [tags.strip()] if tags.strip() else []

        # Convert other types to string first
        return [str(tags).strip()] if str(tags).strip() else []
    
    # Deck operations
    def create_deck(self, name: str, description: str = "") -> int:
        """Create a new deck."""
        try:
            return self.db.create_deck(name, description)
        except Exception as e:
            raise Exception(f"Failed to create deck: {str(e)}")
    
    def get_deck(self, deck_id: int) -> Optional[Dict]:
        """Get deck information."""
        return self.db.get_deck(deck_id)
    
    def get_all_decks(self) -> List[Dict]:
        """Get all decks with card counts."""
        decks = self.db.get_all_decks()
        for deck in decks:
            cards = self.db.get_deck_cards(deck['id'])
            deck['card_count'] = len(cards)
            deck['due_count'] = len([c for c in cards if self._is_card_due(c)])
        return decks
    
    def update_deck(self, deck_id: int, name: str = None, description: str = None):
        """Update deck information."""
        self.db.update_deck(deck_id, name, description)
    
    def delete_deck(self, deck_id: int):
        """Delete deck and all its cards."""
        self.db.delete_deck(deck_id)
    
    # Card operations
    def create_card(self, deck_id: int, front: str, back: str, **kwargs) -> int:
        """Create a new flashcard.
        Allows cloze-only cards (front contains {{c...}} markers) where back can be empty.
        """
        is_cloze = '{{c' in front
        if not front.strip():
            raise ValueError("Front content cannot be empty")
        if not is_cloze and not back.strip():
            raise ValueError("Back content cannot be empty for non-cloze cards")

        # Normalize tags to ensure they're in list format
        if 'tags' in kwargs:
            kwargs['tags'] = self._normalize_tags(kwargs['tags'])

        card_id = self.db.create_card(deck_id, front, back, **kwargs)
        # Register with SRS via service
        self._card_service.register_card(card_id, deck_id, front)
        return card_id
    
    def get_card(self, card_id: int) -> Optional[Dict]:
        """Get card with SRS information."""
        return self.db.get_card(card_id)
    
    def get_deck_cards(self, deck_id: int) -> List[Dict]:
        """Get all cards in a deck."""
        return self.db.get_deck_cards(deck_id)
    
    def update_card(self, card_id: int, **kwargs):
        """Update card content."""
        self.db.update_card(card_id, **kwargs)
    
    def delete_card(self, card_id: int):
        """Delete a card."""
        self.db.delete_card(card_id)
    
    # CSV Import/Export
    def import_cards_from_csv(self, deck_id: int, csv_file_path: str, 
                             front_column: str = "front", back_column: str = "back") -> Tuple[int, List[str]]:
        """
        Import cards from CSV file.
        Returns (number_imported, error_messages).
        """
        imported_count = 0
        errors = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                if front_column not in reader.fieldnames:
                    raise ValueError(f"Column '{front_column}' not found in CSV")
                if back_column not in reader.fieldnames:
                    raise ValueError(f"Column '{back_column}' not found in CSV")
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    try:
                        front = row[front_column].strip()
                        back = row[back_column].strip()
                        
                        if not front or not back:
                            errors.append(f"Row {row_num}: Empty front or back content")
                            continue
                        
                        # Extract optional fields
                        kwargs = {}
                        if 'tags' in row and row['tags']:
                            kwargs['tags'] = [tag.strip() for tag in row['tags'].split(',')]
                        if 'hint' in row and row['hint']:
                            kwargs['hint'] = row['hint'].strip()
                        if 'exceptions' in row and row['exceptions']:
                            kwargs['exceptions'] = row['exceptions'].strip()
                        if 'key_terms' in row and row['key_terms']:
                            kwargs['key_terms'] = row['key_terms'].strip()
                        
                        self.create_card(deck_id, front, back, **kwargs)
                        imported_count += 1
                        
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                        
        except Exception as e:
            errors.append(f"File error: {str(e)}")
        
        return imported_count, errors
    
    def export_cards_to_csv(self, deck_id: int, csv_file_path: str) -> bool:
        """Export deck cards to CSV file."""
        try:
            cards = self.get_deck_cards(deck_id)
            
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
                if not cards:
                    return True
                
                fieldnames = ['front', 'back', 'tags', 'hint', 'exceptions', 'key_terms']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                for card in cards:
                    writer.writerow({
                        'front': card['front'],
                        'back': card['back'],
                        'tags': ','.join(card['tags']) if card['tags'] else '',
                        'hint': card['hint'] or '',
                        'exceptions': card['exceptions'] or '',
                        'key_terms': card['key_terms'] or ''
                    })
            
            return True
        except Exception:
            return False
    
    # Study-related operations
    def get_due_cards(self, deck_id: int, category: str = None) -> List[Dict]:
        """Get cards to review based on selected SRS engine."""
        config = get_config()
        engine = config.get('srs.engine', 'deeptutor')
        # Delegate to service
        return self._card_service.get_study_cards(deck_id, category)
    
    def get_cards_by_category(self, deck_id: int, category: str) -> List[Dict]:
        """Legacy helper; returns all cards of a category from DB."""
        cards = self.db.get_deck_cards(deck_id)
        return [card for card in cards if card.get('category') == category]

    def grade_card(self, card_id: int, grade: int, response_time: float = None,
                   session_id: int = None, cloze_index: int = None) -> Dict:
        """
        Grade a card (or cloze) and update DeepTutor env + srs_data compatibility fields.
        """
        card_data = self.get_card(card_id)
        if not card_data:
            raise ValueError(f"Card {card_id} not found")

        # Record outcome via service
        self._card_service.record_review_outcome(card_id, grade, cloze_index)

        # Update DB for compatibility
        self.db.update_srs_data(card_id, last_review=datetime.now(), grade=grade)

        # Record the review
        grade_mapping = {0: 'fail', 1: 'hard', 2: 'good', 3: 'easy', 4: 'very_easy', 5: 'perfect'}
        user_response = grade_mapping.get(grade, 'unknown')
        if cloze_index is not None:
            user_response = f"{user_response}:c{cloze_index}"
        self.db.add_card_review(card_id, user_response, response_time, session_id)

        return self.get_card(card_id)
    
    def mark_card_response(self, card_id: int, response: str, response_time: float = None,
                          session_id: int = None):
        """Mark card response for non-SRS study modes (like Cram)."""
        self.db.add_card_review(card_id, response, response_time, session_id)
    
    def _is_card_due(self, card: Dict) -> bool:
        """Legacy helper; due-ness is policy-driven now, but keep for UI counts."""
        if not card.get('next_review'):
            return True
        return card['next_review'] <= datetime.now()

    # Legacy methods removed - functionality moved to CardService

    # Statistics and analytics
    def get_deck_statistics(self, deck_id: int) -> Dict:
        """Get comprehensive deck statistics."""
        cards = self.get_deck_cards(deck_id)
        
        if not cards:
            return {
                'total_cards': 0,
                'due_cards': 0,
                'short_term_cards': 0,
                'long_term_cards': 0,
                'average_easiness': 0,
                'total_reviews': 0
            }
        
        due_cards = len([c for c in cards if self._is_card_due(c)])
        short_term = len([c for c in cards if c.get('category') == 'short_term'])
        long_term = len([c for c in cards if c.get('category') == 'long_term'])
        
        # Calculate average easiness for long-term cards
        long_term_cards = [c for c in cards if c.get('category') == 'long_term']
        avg_easiness = sum(c.get('easiness', 2.5) for c in long_term_cards) / len(long_term_cards) if long_term_cards else 2.5
        
        # Count total reviews
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM card_reviews cr
            JOIN cards c ON cr.card_id = c.id
            WHERE c.deck_id = ?
        """, (deck_id,))
        total_reviews = cursor.fetchone()[0]
        
        return {
            'total_cards': len(cards),
            'due_cards': due_cards,
            'short_term_cards': short_term,
            'long_term_cards': long_term,
            'average_easiness': round(avg_easiness, 2),
            'total_reviews': total_reviews
        }
    
    def get_card_history(self, card_id: int) -> List[Dict]:
        """Get review history for a card."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT user_response, response_time, reviewed_at
            FROM card_reviews
            WHERE card_id = ?
            ORDER BY reviewed_at DESC
        """, (card_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # Template system
    def create_card_template(self, name: str, front_template: str, back_template: str,
                           fields: List[str]) -> Dict:
        """Create a card template for advanced card creation."""
        template = {
            'name': name,
            'front_template': front_template,
            'back_template': back_template,
            'fields': fields,
            'created_at': datetime.now().isoformat()
        }
        return template
    
    def apply_template(self, template: Dict, field_values: Dict) -> Tuple[str, str]:
        """Apply template with field values to generate front and back content."""
        front = template['front_template']
        back = template['back_template']
        
        for field in template['fields']:
            placeholder = f"{{{field}}}"
            value = field_values.get(field, '')
            front = front.replace(placeholder, value)
            back = back.replace(placeholder, value)
        
        return front, back
    
    # Utility methods
    def search_cards(self, deck_id: int, query: str) -> List[Dict]:
        """Search cards by content."""
        cards = self.get_deck_cards(deck_id)
        query_lower = query.lower()
        
        matching_cards = []
        for card in cards:
            if (query_lower in card['front'].lower() or 
                query_lower in card['back'].lower() or
                any(query_lower in tag.lower() for tag in card['tags'])):
                matching_cards.append(card)
        
        return matching_cards
    
    def get_random_cards(self, deck_id: int, count: int) -> List[Dict]:
        """Get random cards from deck."""
        import random
        cards = self.get_deck_cards(deck_id)
        return random.sample(cards, min(count, len(cards)))
