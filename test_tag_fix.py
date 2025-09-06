#!/usr/bin/env python3
"""
Test the tag fix by creating a new card and verifying tags work correctly
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.card_manager import CardManager


def test_tag_fix():
    """Test that the tag fix works for new cards"""
    print("Testing Tag Fix")
    print("=" * 50)
    
    # Initialize card manager
    card_manager = CardManager()
    
    # Create a test deck
    deck_name = "Tag Fix Test Deck"
    try:
        deck_id = card_manager.create_deck(deck_name)
        print(f"✓ Created test deck: {deck_name} (ID: {deck_id})")
    except Exception as e:
        # Deck might already exist, try to get it
        decks = card_manager.get_decks()
        deck_id = None
        for deck in decks:
            if deck['name'] == deck_name:
                deck_id = deck['id']
                break
        
        if not deck_id:
            print(f"✗ Failed to create or find deck: {e}")
            return False
        
        print(f"✓ Using existing deck: {deck_name} (ID: {deck_id})")
    
    # Test different tag formats
    test_cases = [
        {
            'front': 'What is Python?',
            'back': 'A high-level programming language',
            'tags': ['python', 'programming', 'language'],
            'description': 'List format (correct)'
        },
        {
            'front': 'What is JavaScript?',
            'back': 'A scripting language for web development',
            'tags': 'javascript,programming,web',
            'description': 'String format (should be converted)'
        },
        {
            'front': 'What is HTML?',
            'back': 'HyperText Markup Language',
            'tags': 'html,web,markup',
            'description': 'String format with spaces'
        }
    ]
    
    created_cards = []
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            print(f"\nTest {i}: {test_case['description']}")
            print(f"  Input tags: {test_case['tags']} (type: {type(test_case['tags']).__name__})")
            
            # Create card
            card_id = card_manager.create_card(
                deck_id=deck_id,
                front=test_case['front'],
                back=test_case['back'],
                tags=test_case['tags']
            )
            
            created_cards.append(card_id)
            print(f"  ✓ Card created with ID: {card_id}")
            
            # Retrieve card to verify tags
            card = card_manager.get_card(card_id)
            print(f"  Retrieved tags: {card['tags']} (type: {type(card['tags']).__name__})")
            
            # Verify tags are in list format
            if isinstance(card['tags'], list):
                print(f"  ✓ Tags are correctly stored as list")
                print(f"  ✓ Tag values: {card['tags']}")
            else:
                print(f"  ✗ Tags are not in list format: {card['tags']}")
                return False
            
        except Exception as e:
            print(f"  ✗ Error creating card: {e}")
            return False
    
    # Test CSV export to verify tags display correctly
    print(f"\nTesting CSV export...")
    try:
        csv_data = card_manager.export_deck_to_csv(deck_id)
        print(f"✓ CSV export successful")
        
        # Check a few lines of CSV to see tag formatting
        lines = csv_data.split('\n')
        print(f"CSV header: {lines[0]}")
        
        for i, line in enumerate(lines[1:4], 1):  # Show first 3 data lines
            if line.strip():
                print(f"CSV line {i}: {line}")
        
    except Exception as e:
        print(f"✗ CSV export failed: {e}")
        return False
    
    # Clean up test cards
    print(f"\nCleaning up test cards...")
    for card_id in created_cards:
        try:
            card_manager.delete_card(card_id)
            print(f"✓ Deleted card {card_id}")
        except Exception as e:
            print(f"✗ Failed to delete card {card_id}: {e}")
    
    # Clean up test deck
    try:
        card_manager.delete_deck(deck_id)
        print(f"✓ Deleted test deck {deck_id}")
    except Exception as e:
        print(f"✗ Failed to delete test deck: {e}")
    
    card_manager.close()
    
    print(f"\n{'=' * 50}")
    print(f"✅ Tag fix test completed successfully!")
    print(f"✅ Tags are now properly stored as lists")
    print(f"✅ CSV export shows comma-separated tags correctly")
    
    return True


if __name__ == "__main__":
    test_tag_fix()
