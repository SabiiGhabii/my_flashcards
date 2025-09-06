#!/usr/bin/env python3
"""
Check existing decks
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.card_manager import CardManager


def check_decks():
    """Check existing decks"""
    try:
        card_manager = CardManager()
        decks = card_manager.get_all_decks()
        
        print("Existing Decks:")
        print("=" * 50)
        
        for deck in decks:
            print(f"ID: {deck['id']}, Name: {deck['name']}")
            
        # Look for Fluent Python decks
        fluent_decks = [d for d in decks if 'fluent' in d['name'].lower() or 'python' in d['name'].lower()]
        
        if fluent_decks:
            print(f"\nFound {len(fluent_decks)} Fluent Python related decks:")
            for deck in fluent_decks:
                print(f"  ID: {deck['id']}, Name: {deck['name']}")
                
                # Delete the deck
                try:
                    card_manager.delete_deck(deck['id'])
                    print(f"  Deleted deck: {deck['name']}")
                except Exception as e:
                    print(f"  Failed to delete deck {deck['name']}: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    check_decks()
