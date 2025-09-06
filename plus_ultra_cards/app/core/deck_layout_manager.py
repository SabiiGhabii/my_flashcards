"""
Deck Layout Manager
Handles persistence and management of deck box sizes and positions.
"""

import json
import os
from typing import Dict, Tuple
from pathlib import Path
from app.core.config_manager import get_config


class DeckLayoutManager:
    """Manages deck layout persistence and grid calculations."""
    
    def __init__(self, config_file: str = "data/deck_layout.json"):
        self.config_file = config_file
        self.config = get_config()
        self.layout_data = self.load_layout()
    
    def load_layout(self) -> Dict:
        """Load deck layout configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        return {
            "deck_spans": {},  # deck_id -> (row_span, col_span)
            "grid_columns": 4,
            "default_span": [1, 1]
        }
    
    def save_layout(self):
        """Save current layout configuration to file."""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.layout_data, f, indent=2)
        except Exception as e:
            print(f"Failed to save deck layout: {e}")
    
    def get_deck_span(self, deck_id: int) -> Tuple[int, int]:
        """Get the span (row_span, col_span) for a specific deck."""
        deck_spans = self.config.get("layout.deck_spans", {})
        span = deck_spans.get(str(deck_id))
        if span:
            return tuple(span)
        return tuple(self.config.get("layout.default_span", [1, 1]))
    
    def set_deck_span(self, deck_id: int, row_span: int, col_span: int):
        """Set the span for a specific deck."""
        deck_spans = self.config.get("layout.deck_spans", {})
        deck_spans[str(deck_id)] = [row_span, col_span]
        self.config.set("layout.deck_spans", deck_spans)
    
    def remove_deck(self, deck_id: int):
        """Remove deck layout data when deck is deleted."""
        deck_key = str(deck_id)
        if deck_key in self.layout_data["deck_spans"]:
            del self.layout_data["deck_spans"][deck_key]
            self.save_layout()
    
    def reset_layout(self):
        """Reset all deck spans to default."""
        self.layout_data["deck_spans"] = {}
        self.save_layout()
    
    def get_grid_columns(self) -> int:
        """Get the number of grid columns."""
        return self.config.get("layout.grid_columns", 4)
    
    def calculate_grid_positions(self, deck_ids: list) -> Dict[int, Tuple[int, int, int, int]]:
        """
        Calculate grid positions for all decks.
        Returns dict of deck_id -> (row, col, row_span, col_span)
        """
        positions = {}
        max_cols = self.get_grid_columns()
        
        # Simple left-to-right, top-to-bottom packing
        current_row = 0
        current_col = 0
        
        for deck_id in deck_ids:
            row_span, col_span = self.get_deck_span(deck_id)
            
            # Ensure we don't exceed grid width
            col_span = min(col_span, max_cols)
            
            # If current position + span exceeds grid width, move to next row
            if current_col + col_span > max_cols:
                current_row += 1
                current_col = 0
            
            positions[deck_id] = (current_row, current_col, row_span, col_span)
            
            # Move to next position
            current_col += col_span
            if current_col >= max_cols:
                current_row += 1
                current_col = 0
        
        return positions
    
    def validate_spans(self, deck_ids: list):
        """Validate and fix any invalid spans."""
        max_cols = self.get_grid_columns()
        
        for deck_id in deck_ids:
            row_span, col_span = self.get_deck_span(deck_id)
            
            # Fix invalid spans
            if row_span < 1:
                row_span = 1
            if col_span < 1:
                col_span = 1
            if col_span > max_cols:
                col_span = max_cols
            
            # Update if changed
            current_span = self.get_deck_span(deck_id)
            if current_span != (row_span, col_span):
                self.set_deck_span(deck_id, row_span, col_span)
