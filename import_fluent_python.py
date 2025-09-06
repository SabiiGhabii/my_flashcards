#!/usr/bin/env python3
"""
Import Fluent Python cards into plus_ultra_cards application
"""

import json
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.card_manager import CardManager
from app.flashcard_generation import convert_cards_format


def import_fluent_python_cards():
    """Import Fluent Python cards from JSON export"""
    print("Importing Fluent Python Cards")
    print("=" * 50)
    
    try:
        # Load the JSON export
        json_file = "exports/fluent_python_test_20250903_203104.json"
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cards = data['cards']
        print(f"Loaded {len(cards)} cards from {json_file}")
        
        # Convert to plus_ultra format
        converted_cards = convert_cards_format(cards)
        print(f"Converted {len(converted_cards)} cards to plus_ultra format")
        
        # Initialize card manager
        card_manager = CardManager()
        
        # Create deck with unique name
        import time
        import random
        deck_name = f"Fluent Python - Complete Book {random.randint(1000, 9999)}"

        # Try to create deck, if it fails, try with different name
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                deck_id = card_manager.create_deck(deck_name)
                break
            except Exception as e:
                if attempt < max_attempts - 1:
                    deck_name = f"Fluent Python - Complete Book {random.randint(1000, 9999)}"
                    continue
                else:
                    raise e
        print(f"Created deck: {deck_name} (ID: {deck_id})")
        
        # Count card types
        card_type_counts = {}
        
        # Add cards to deck
        added_count = 0
        for i, card_data in enumerate(converted_cards):
            try:
                card_type = card_data.get('card_type', 'basic')
                card_type_counts[card_type] = card_type_counts.get(card_type, 0) + 1
                
                card_id = card_manager.create_card(
                    deck_id=deck_id,
                    front=card_data['front'],
                    back=card_data['back'],
                    hint=card_data.get('hint', ''),
                    tags=card_data.get('tags', ''),
                    difficulty=card_data.get('difficulty', 2)
                )
                added_count += 1
                
                if (i + 1) % 100 == 0:
                    print(f"Added {i + 1} cards...")
                    
            except Exception as e:
                print(f"Error adding card {i + 1}: {e}")
                continue
        
        print(f"\nImport Complete!")
        print(f"Successfully added {added_count} cards to deck '{deck_name}'")
        print(f"\nCard Type Distribution:")
        for card_type, count in card_type_counts.items():
            print(f"  {card_type}: {count} cards")
        
        # Verify deck
        deck_cards = card_manager.get_deck_cards(deck_id)
        print(f"\nVerification: Deck contains {len(deck_cards)} cards")
        
        # Test card type detection
        from app.core.card_types import CardTypeRegistry
        registry = CardTypeRegistry()
        
        type_detection_counts = {}
        for card in deck_cards[:100]:  # Test first 100 cards
            card_type = registry.resolve(card['front'])
            type_name = card_type.__class__.__name__
            type_detection_counts[type_name] = type_detection_counts.get(type_name, 0) + 1
        
        print(f"\nCard Type Detection (first 100 cards):")
        for type_name, count in type_detection_counts.items():
            print(f"  {type_name}: {count} cards")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = import_fluent_python_cards()
    sys.exit(0 if success else 1)
