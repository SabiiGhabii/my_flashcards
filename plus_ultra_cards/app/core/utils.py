"""
Utilities Module for Plus Ultra Cards
Contains helper functions for NLP, import/export, and other utilities.
"""

import re
import csv
import json
import math
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta


class TextSimilarity:
    """Simple text similarity calculator for Free Recall mode."""
    
    @staticmethod
    def word_overlap_similarity(text1: str, text2: str) -> float:
        """Calculate similarity based on word overlap (Jaccard similarity)."""
        if not text1.strip() or not text2.strip():
            return 0.0
        
        # Normalize text
        words1 = set(TextSimilarity._normalize_text(text1).split())
        words2 = set(TextSimilarity._normalize_text(text2).split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def cosine_similarity(text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts."""
        if not text1.strip() or not text2.strip():
            return 0.0
        
        # Create word frequency vectors
        words1 = TextSimilarity._normalize_text(text1).split()
        words2 = TextSimilarity._normalize_text(text2).split()
        
        # Get all unique words
        all_words = set(words1 + words2)
        
        # Create frequency vectors
        vec1 = [words1.count(word) for word in all_words]
        vec2 = [words2.count(word) for word in all_words]
        
        # Calculate cosine similarity
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    @staticmethod
    def levenshtein_similarity(text1: str, text2: str) -> float:
        """Calculate similarity based on Levenshtein distance."""
        if not text1.strip() or not text2.strip():
            return 0.0
        
        text1 = TextSimilarity._normalize_text(text1)
        text2 = TextSimilarity._normalize_text(text2)
        
        distance = TextSimilarity._levenshtein_distance(text1, text2)
        max_len = max(len(text1), len(text2))
        
        if max_len == 0:
            return 1.0
        
        return 1.0 - (distance / max_len)
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for comparison."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return TextSimilarity._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def combined_similarity(text1: str, text2: str) -> float:
        """Calculate combined similarity score using multiple methods."""
        word_sim = TextSimilarity.word_overlap_similarity(text1, text2)
        cosine_sim = TextSimilarity.cosine_similarity(text1, text2)
        levenshtein_sim = TextSimilarity.levenshtein_similarity(text1, text2)
        
        # Weighted average (word overlap gets more weight)
        return (word_sim * 0.5 + cosine_sim * 0.3 + levenshtein_sim * 0.2)


class CSVHandler:
    """Handles CSV import/export operations."""
    
    @staticmethod
    def validate_csv_file(file_path: str) -> Tuple[bool, str, List[str]]:
        """
        Validate CSV file and return column information.
        Returns (is_valid, error_message, column_names).
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Try to detect delimiter
                sample = file.read(1024)
                file.seek(0)
                
                sniffer = csv.Sniffer()
                try:
                    delimiter = sniffer.sniff(sample).delimiter
                except:
                    delimiter = ','
                
                reader = csv.DictReader(file, delimiter=delimiter)
                column_names = reader.fieldnames or []
                
                if not column_names:
                    return False, "No columns found in CSV file", []
                
                # Check if we have at least front and back columns
                has_front = any('front' in col.lower() for col in column_names)
                has_back = any('back' in col.lower() for col in column_names)
                
                if not (has_front and has_back):
                    return False, "CSV must contain 'front' and 'back' columns", column_names
                
                return True, "", column_names
                
        except Exception as e:
            return False, f"Error reading CSV file: {str(e)}", []
    
    @staticmethod
    def preview_csv_data(file_path: str, max_rows: int = 5) -> List[Dict]:
        """Preview first few rows of CSV data."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                preview_data = []
                
                for i, row in enumerate(reader):
                    if i >= max_rows:
                        break
                    preview_data.append(dict(row))
                
                return preview_data
                
        except Exception:
            return []


class StatisticsCalculator:
    """Calculates various statistics for study sessions and decks."""
    
    @staticmethod
    def calculate_retention_rate(correct: int, total: int) -> float:
        """Calculate retention rate as percentage."""
        if total == 0:
            return 0.0
        return (correct / total) * 100
    
    @staticmethod
    def calculate_study_streak(review_dates: List[datetime]) -> int:
        """Calculate current study streak in days."""
        if not review_dates:
            return 0
        
        # Sort dates in descending order
        sorted_dates = sorted(review_dates, reverse=True)
        
        # Check if studied today or yesterday
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        if sorted_dates[0].date() not in [today, yesterday]:
            return 0
        
        # Count consecutive days
        streak = 1
        current_date = sorted_dates[0].date()
        
        for i in range(1, len(sorted_dates)):
            expected_date = current_date - timedelta(days=1)
            actual_date = sorted_dates[i].date()
            
            if actual_date == expected_date:
                streak += 1
                current_date = actual_date
            else:
                break
        
        return streak
    
    @staticmethod
    def calculate_difficulty_distribution(cards: List[Dict]) -> Dict[str, int]:
        """Calculate distribution of cards by difficulty/category."""
        distribution = {
            'new': 0,
            'learning': 0,
            'review': 0,
            'difficult': 0
        }
        
        for card in cards:
            repetitions = card.get('repetitions', 0)
            lapses = card.get('lapses', 0)
            
            if repetitions == 0:
                distribution['new'] += 1
            elif repetitions < 3:
                distribution['learning'] += 1
            elif lapses > 2:
                distribution['difficult'] += 1
            else:
                distribution['review'] += 1
        
        return distribution
    
    @staticmethod
    def calculate_average_ease(cards: List[Dict]) -> float:
        """Calculate average easiness factor for cards."""
        ease_values = [card.get('easiness', 2.5) for card in cards if card.get('easiness')]
        
        if not ease_values:
            return 2.5
        
        return sum(ease_values) / len(ease_values)
    
    @staticmethod
    def predict_workload(cards: List[Dict], days_ahead: int = 7) -> List[int]:
        """Predict daily review workload for the next N days."""
        workload = [0] * days_ahead
        today = datetime.now().date()
        
        for card in cards:
            next_review = card.get('next_review')
            if not next_review:
                continue
            
            if isinstance(next_review, str):
                next_review = datetime.fromisoformat(next_review).date()
            elif isinstance(next_review, datetime):
                next_review = next_review.date()
            
            days_from_today = (next_review - today).days
            
            if 0 <= days_from_today < days_ahead:
                workload[days_from_today] += 1
        
        return workload


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.default_config = {
            "theme": "retro95",
            "font_size": 10,
            "auto_save": True,
            "backup_enabled": True,
            "backup_interval_days": 7,
            "study_reminders": True,
            "default_study_mode": "cram",
            "show_statistics": True,
            "card_flip_animation": True,
            "sound_enabled": False,
            "daily_goal": 20,
            "session_timeout_minutes": 60
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
        except (FileNotFoundError, json.JSONDecodeError):
            return self.default_config.copy()
    
    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """Set configuration value."""
        self.config[key] = value
        self.save_config()
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self.config = self.default_config.copy()
        self.save_config()


class BackupManager:
    """Manages database backups."""
    
    def __init__(self, db_path: str = "data/cards.db", backup_dir: str = "data/backups"):
        self.db_path = db_path
        self.backup_dir = backup_dir
        
        # Create backup directory
        from pathlib import Path
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
    
    def create_backup(self) -> str:
        """Create a backup of the database."""
        import shutil
        from pathlib import Path
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"cards_backup_{timestamp}.db"
        backup_path = Path(self.backup_dir) / backup_filename
        
        try:
            shutil.copy2(self.db_path, backup_path)
            return str(backup_path)
        except Exception as e:
            raise Exception(f"Failed to create backup: {e}")
    
    def list_backups(self) -> List[Tuple[str, datetime]]:
        """List all available backups."""
        from pathlib import Path
        
        backup_files = []
        backup_path = Path(self.backup_dir)
        
        if backup_path.exists():
            for file in backup_path.glob("cards_backup_*.db"):
                try:
                    # Extract timestamp from filename
                    timestamp_str = file.stem.split("_", 2)[2]
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    backup_files.append((str(file), timestamp))
                except (ValueError, IndexError):
                    continue
        
        # Sort by timestamp (newest first)
        backup_files.sort(key=lambda x: x[1], reverse=True)
        return backup_files
    
    def restore_backup(self, backup_path: str):
        """Restore database from backup."""
        import shutil
        
        try:
            shutil.copy2(backup_path, self.db_path)
        except Exception as e:
            raise Exception(f"Failed to restore backup: {e}")
    
    def cleanup_old_backups(self, keep_count: int = 10):
        """Remove old backups, keeping only the most recent ones."""
        backups = self.list_backups()
        
        if len(backups) > keep_count:
            for backup_path, _ in backups[keep_count:]:
                try:
                    from pathlib import Path
                    Path(backup_path).unlink()
                except Exception:
                    continue


def format_time_duration(seconds: float) -> str:
    """Format time duration in a human-readable format."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_date_relative(date: datetime) -> str:
    """Format date in a relative format (e.g., 'Today', 'Yesterday', '3 days ago')."""
    now = datetime.now()
    diff = now.date() - date.date()
    
    if diff.days == 0:
        return "Today"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days} days ago"
    elif diff.days < 30:
        weeks = diff.days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    else:
        return date.strftime("%Y-%m-%d")


def validate_card_content(front: str, back: str) -> Tuple[bool, str]:
    """Validate card content and return (is_valid, error_message).
    Allows cloze-only cards where front contains {{c...}} markers and back can be empty.
    """
    if not front.strip():
        return False, "Front content cannot be empty"

    is_cloze = '{{c' in front
    if not is_cloze and not back.strip():
        return False, "Back content cannot be empty for non-cloze cards"

    if len(front) > 5000:
        return False, "Front content is too long (max 5000 characters)"

    if not is_cloze and len(back) > 5000:
        return False, "Back content is too long (max 5000 characters)"

    return True, ""


def extract_key_terms(text: str) -> List[str]:
    """Extract potential key terms from text."""
    # Simple key term extraction based on capitalization and length
    words = re.findall(r'\b[A-Z][a-z]+\b|\b[a-z]{4,}\b', text)
    
    # Filter out common words
    common_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
        'those', 'what', 'which', 'who', 'when', 'where', 'why', 'how'
    }
    
    key_terms = [word for word in words if word.lower() not in common_words]
    
    # Remove duplicates and return
    return list(set(key_terms))
