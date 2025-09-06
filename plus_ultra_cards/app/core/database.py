"""
Database module for Plus Ultra Cards
Handles SQLite database operations for decks, cards, and study sessions.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class Database:
    def __init__(self, db_path: str = "data/cards.db"):
        """Initialize database connection and create tables if they don't exist."""
        self.db_path = db_path

        # Create data directory if it doesn't exist (only if path has a directory)
        db_dir = os.path.dirname(db_path)
        if db_dir:  # Only create directory if path contains a directory
            os.makedirs(db_dir, exist_ok=True)
        
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        self.create_tables()
    
    def create_tables(self):
        """Create all necessary tables."""
        cursor = self.conn.cursor()
        
        # Decks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Cards table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deck_id INTEGER NOT NULL,
                front TEXT NOT NULL,
                back TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                hint TEXT,
                exceptions TEXT,
                key_terms TEXT,
                template_data TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deck_id) REFERENCES decks (id) ON DELETE CASCADE
            )
        """)
        
        # Study sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deck_id INTEGER NOT NULL,
                session_type TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                total_cards INTEGER DEFAULT 0,
                correct_cards INTEGER DEFAULT 0,
                session_data TEXT DEFAULT '{}',
                FOREIGN KEY (deck_id) REFERENCES decks (id) ON DELETE CASCADE
            )
        """)
        
        # Card reviews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS card_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER NOT NULL,
                session_id INTEGER,
                response_time REAL,
                user_response TEXT NOT NULL,
                reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (card_id) REFERENCES cards (id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES study_sessions (id) ON DELETE SET NULL
            )
        """)
        
        # SRS data table (per-card)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS srs_data (
                card_id INTEGER PRIMARY KEY,
                easiness REAL DEFAULT 2.5,
                interval INTEGER DEFAULT 1,
                repetitions INTEGER DEFAULT 0,
                next_review TIMESTAMP,
                last_review TIMESTAMP,
                lapses INTEGER DEFAULT 0,
                category TEXT DEFAULT 'short_term',
                grade INTEGER DEFAULT 0,
                FOREIGN KEY (card_id) REFERENCES cards (id) ON DELETE CASCADE
            )
        """)

        # SRS data table (per-cloze blank)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS srs_cloze_data (
                card_id INTEGER NOT NULL,
                cloze_index INTEGER NOT NULL,
                easiness REAL DEFAULT 2.5,
                interval INTEGER DEFAULT 1,
                repetitions INTEGER DEFAULT 0,
                next_review TIMESTAMP,
                last_review TIMESTAMP,
                lapses INTEGER DEFAULT 0,
                grade INTEGER DEFAULT 0,
                PRIMARY KEY (card_id, cloze_index),
                FOREIGN KEY (card_id) REFERENCES cards (id) ON DELETE CASCADE
            )
        """)

        self.conn.commit()

        # DeepTutor models table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dt_models (
                deck_id INTEGER PRIMARY KEY,
                model TEXT NOT NULL,
                tutor TEXT NOT NULL,
                item_map TEXT NOT NULL,
                env_state TEXT NOT NULL,
                policy_blob BLOB,
                reward_history TEXT,
                last_trained_at TIMESTAMP,
                lib_info TEXT,
                FOREIGN KEY (deck_id) REFERENCES decks (id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

        # App settings table (for engine selection and SRS settings)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    # Deck operations
    def create_deck(self, name: str, description: str = "") -> int:
        """Create a new deck and return its ID."""
        if not name or not name.strip():
            raise ValueError("Deck name cannot be empty")

        if len(name.strip()) > 255:
            raise ValueError("Deck name too long (max 255 characters)")

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO decks (name, description) VALUES (?, ?)",
                (name.strip(), description.strip())
            )
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Failed to create deck: {str(e)}")
    
    def get_deck(self, deck_id: int) -> Optional[Dict]:
        """Get deck by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM decks WHERE id = ?", (deck_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_decks(self) -> List[Dict]:
        """Get all decks."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM decks ORDER BY updated_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def update_deck(self, deck_id: int, name: str = None, description: str = None):
        """Update deck information."""
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(deck_id)
            
            cursor = self.conn.cursor()
            cursor.execute(
                f"UPDATE decks SET {', '.join(updates)} WHERE id = ?",
                params
            )
            self.conn.commit()
    
    def delete_deck(self, deck_id: int):
        """Delete deck and all associated cards."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM decks WHERE id = ?", (deck_id,))
        self.conn.commit()
    
    # Card operations
    def create_card(self, deck_id: int, front: str, back: str, **kwargs) -> int:
        """Create a new card and return its ID.
        Allows cloze-only cards (front contains {{c...}} markers) where back may be empty.
        """
        # Validate inputs
        if not front or not front.strip():
            raise ValueError("Card front content cannot be empty")
        is_cloze = "{{c" in front
        if (not is_cloze) and (not back or not back.strip()):
            raise ValueError("Card back content cannot be empty")
        if len(front.strip()) > 5000:
            raise ValueError("Card front content too long (max 5000 characters)")
        if (not is_cloze) and len(back.strip()) > 5000:
            raise ValueError("Card back content too long (max 5000 characters)")

        # Verify deck exists
        if not self.get_deck(deck_id):
            raise ValueError(f"Deck with ID {deck_id} does not exist")

        try:
            cursor = self.conn.cursor()

            # Handle optional fields
            tags = json.dumps(kwargs.get('tags', []))
            hint = kwargs.get('hint', '')
            exceptions = kwargs.get('exceptions', '')
            key_terms = kwargs.get('key_terms', '')
            template_data = json.dumps(kwargs.get('template_data', {}))

            cursor.execute("""
                INSERT INTO cards (deck_id, front, back, tags, hint, exceptions, key_terms, template_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (deck_id, front.strip(), back.strip(), tags, hint, exceptions, key_terms, template_data))

            card_id = cursor.lastrowid

            # Initialize SRS data for the new card
            cursor.execute("""
                INSERT INTO srs_data (card_id, next_review)
                VALUES (?, ?)
            """, (card_id, datetime.now().isoformat()))

            self.conn.commit()
            return card_id
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Failed to create card: {str(e)}")
    
    def get_card(self, card_id: int) -> Optional[Dict]:
        """Get card by ID."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.*, s.easiness, s.interval, s.repetitions, s.next_review,
                   s.last_review, s.lapses, s.category, s.grade
            FROM cards c
            LEFT JOIN srs_data s ON c.id = s.card_id
            WHERE c.id = ?
        """, (card_id,))
        row = cursor.fetchone()
        if row:
            card = dict(row)
            card['tags'] = json.loads(card['tags'])
            card['template_data'] = json.loads(card['template_data'])
            # Convert datetime strings back to datetime objects
            if card.get('next_review'):
                try:
                    card['next_review'] = datetime.fromisoformat(card['next_review'])
                except (ValueError, TypeError):
                    card['next_review'] = None
            if card.get('last_review'):
                try:
                    card['last_review'] = datetime.fromisoformat(card['last_review'])
                except (ValueError, TypeError):
                    card['last_review'] = None
            return card
        return None
    
    def get_deck_cards(self, deck_id: int) -> List[Dict]:
        """Get all cards in a deck."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.*, s.easiness, s.interval, s.repetitions, s.next_review,
                   s.last_review, s.lapses, s.category, s.grade
            FROM cards c
            LEFT JOIN srs_data s ON c.id = s.card_id
            WHERE c.deck_id = ?
            ORDER BY c.created_at
        """, (deck_id,))
        cards = []
        for row in cursor.fetchall():
            card = dict(row)
            card['tags'] = json.loads(card['tags'])
            card['template_data'] = json.loads(card['template_data'])
            # Convert datetime strings back to datetime objects
            if card.get('next_review'):
                try:
                    card['next_review'] = datetime.fromisoformat(card['next_review'])
                except (ValueError, TypeError):
                    card['next_review'] = None
            if card.get('last_review'):
                try:
                    card['last_review'] = datetime.fromisoformat(card['last_review'])
                except (ValueError, TypeError):
                    card['last_review'] = None
            cards.append(card)
        return cards
    
    def update_card(self, card_id: int, **kwargs):
        """Update card information."""
        updates = []
        params = []
        
        for field in ['front', 'back', 'hint', 'exceptions', 'key_terms']:
            if field in kwargs:
                updates.append(f"{field} = ?")
                params.append(kwargs[field])
        
        if 'tags' in kwargs:
            updates.append("tags = ?")
            params.append(json.dumps(kwargs['tags']))
        
        if 'template_data' in kwargs:
            updates.append("template_data = ?")
            params.append(json.dumps(kwargs['template_data']))
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(card_id)
            
            cursor = self.conn.cursor()
            cursor.execute(
                f"UPDATE cards SET {', '.join(updates)} WHERE id = ?",
                params
            )
            self.conn.commit()
    
    def delete_card(self, card_id: int):
        """Delete card and associated SRS data."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        self.conn.commit()
    
    # SRS operations
    def update_srs_data(self, card_id: int, **kwargs):
        """Update SRS data for a card."""
        updates = []
        params = []

        for field in ['easiness', 'interval', 'repetitions', 'next_review',
                      'last_review', 'lapses', 'category', 'grade']:
            if field in kwargs:
                updates.append(f"{field} = ?")
                value = kwargs[field]
                # Convert datetime objects to ISO format strings for SQLite storage
                if field in ['next_review', 'last_review'] and isinstance(value, datetime):
                    value = value.isoformat()
                params.append(value)

        if updates:
            params.append(card_id)
            cursor = self.conn.cursor()
            cursor.execute(
                f"UPDATE srs_data SET {', '.join(updates)} WHERE card_id = ?",
                params
            )
            self.conn.commit()

    def upsert_srs_cloze(self, card_id: int, cloze_index: int, **kwargs):
        """Insert or update SRS data for a specific cloze index."""
        # Ensure exists
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO srs_cloze_data (card_id, cloze_index, next_review) VALUES (?, ?, ?)",
            (card_id, cloze_index, datetime.now())
        )

        updates = []
        params = []
        for field in ['easiness', 'interval', 'repetitions', 'next_review', 'last_review', 'lapses', 'grade']:
            if field in kwargs:
                updates.append(f"{field} = ?")
                params.append(kwargs[field])
        if updates:
            params.extend([card_id, cloze_index])
            cursor.execute(
                f"UPDATE srs_cloze_data SET {', '.join(updates)} WHERE card_id = ? AND cloze_index = ?",
                params
            )
        self.conn.commit()

    def get_srs_cloze(self, card_id: int, cloze_index: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM srs_cloze_data WHERE card_id = ? AND cloze_index = ?",
            (card_id, cloze_index)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    # -------- DeepTutor model CRUD --------
    def get_dt_model(self, deck_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM dt_models WHERE deck_id = ?", (deck_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def upsert_dt_model(self, deck_id: int, **kwargs):
        cursor = self.conn.cursor()
        existing = self.get_dt_model(deck_id)
        fields = [
            "model","tutor","item_map","env_state","policy_blob",
            "reward_history","last_trained_at","lib_info"
        ]
        if existing:
            updates = []
            params = []
            for f in fields:
                if f in kwargs:
                    updates.append(f"{f} = ?")
                    params.append(kwargs[f])
            params.append(deck_id)
            if updates:
                cursor.execute(f"UPDATE dt_models SET {', '.join(updates)} WHERE deck_id = ?", params)
        else:
            cols = ["deck_id"] + [f for f in fields if f in kwargs]
            vals = [deck_id] + [kwargs[f] for f in fields if f in kwargs]
            placeholders = ",".join(["?"] * len(vals))
            cursor.execute(f"INSERT INTO dt_models ({','.join(cols)}) VALUES ({placeholders})", vals)
        self.conn.commit()

    def update_dt_policy(self, deck_id: int, policy_blob: bytes):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE dt_models SET policy_blob = ?, last_trained_at = ? WHERE deck_id = ?",
                       (policy_blob, datetime.now(), deck_id))
        self.conn.commit()

    def get_due_cards(self, deck_id: int, category: str = None) -> List[Dict]:
        """Get cards due for review."""
        cursor = self.conn.cursor()
        query = """
            SELECT c.*, s.easiness, s.interval, s.repetitions, s.next_review,
                   s.last_review, s.lapses, s.category, s.grade
            FROM cards c
            JOIN srs_data s ON c.id = s.card_id
            WHERE c.deck_id = ? AND (s.next_review IS NULL OR s.next_review <= ?)
        """
        # Convert datetime to string for SQLite comparison
        now_str = datetime.now().isoformat()
        params = [deck_id, now_str]

        if category:
            query += " AND s.category = ?"
            params.append(category)

        query += " ORDER BY s.next_review"

        cursor.execute(query, params)
        cards = []
        for row in cursor.fetchall():
            card = dict(row)
            card['tags'] = json.loads(card['tags'])
            card['template_data'] = json.loads(card['template_data'])
            # Convert datetime strings back to datetime objects
            if card.get('next_review'):
                try:
                    card['next_review'] = datetime.fromisoformat(card['next_review'])
                except (ValueError, TypeError):
                    card['next_review'] = None
            if card.get('last_review'):
                try:
                    card['last_review'] = datetime.fromisoformat(card['last_review'])
                except (ValueError, TypeError):
                    card['last_review'] = None
            cards.append(card)
        return cards

    # -------- App Settings CRUD --------
    def set_setting(self, key: str, value: str):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO app_settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                       (key, value))
        self.conn.commit()

    def get_setting(self, key: str) -> Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None
    
    # Session operations
    def create_session(self, deck_id: int, session_type: str) -> int:
        """Create a new study session."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO study_sessions (deck_id, session_type) VALUES (?, ?)",
            (deck_id, session_type)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def update_session(self, session_id: int, **kwargs):
        """Update session data."""
        updates = []
        params = []
        
        for field in ['completed_at', 'total_cards', 'correct_cards']:
            if field in kwargs:
                updates.append(f"{field} = ?")
                params.append(kwargs[field])
        
        if 'session_data' in kwargs:
            updates.append("session_data = ?")
            params.append(json.dumps(kwargs['session_data']))
        
        if updates:
            params.append(session_id)
            cursor = self.conn.cursor()
            cursor.execute(
                f"UPDATE study_sessions SET {', '.join(updates)} WHERE id = ?",
                params
            )
            self.conn.commit()
    
    def add_card_review(self, card_id: int, user_response: str,
                       response_time: float = None, session_id: int = None):
        """Add a card review record."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO card_reviews (card_id, session_id, response_time, user_response)
            VALUES (?, ?, ?, ?)
        """, (card_id, session_id, response_time, user_response))
        self.conn.commit()

    def get_card_reviews(self, card_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM card_reviews WHERE card_id = ? ORDER BY id DESC", (card_id,))
        return [dict(r) for r in cursor.fetchall()]
