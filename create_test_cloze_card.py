#!/usr/bin/env python3
"""
Create Test Cloze Input Card
Creates a comprehensive test card to verify all functionality
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent / "plus_ultra_cards"))

def create_test_card():
    """Create a comprehensive test cloze input card"""
    print("🃏 CREATING TEST CLOZE INPUT CARD")
    print("=" * 50)
    
    try:
        from app.core.card_manager import CardManager
        
        card_manager = CardManager()
        
        # Create or find test deck
        deck_name = "🧪 Cloze Input Test Deck"
        try:
            deck_id = card_manager.create_deck(deck_name)
            print(f"✅ Created new deck: {deck_name}")
        except:
            # Deck might exist
            decks = card_manager.get_all_decks()
            deck_id = next((d['id'] for d in decks if d['name'] == deck_name), None)
            if deck_id:
                print(f"✅ Using existing deck: {deck_name}")
            else:
                raise Exception("Could not create or find test deck")
        
        # Create comprehensive test card
        test_card_content = """# Programming Concepts Test

## Python Basics
Python is a {{cin1::high-level}} programming language that is {{cin2::interpreted}}.

## Code Example
```python
def fibonacci(n):
    if n <= {{cin3::1}}:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

## Mathematical Formula
The time complexity is {{cin4::O(2^n)}} for the naive recursive approach.

**Formula**: $$T(n) = T(n-1) + T(n-2) + O(1)$$

## Key Points
- Python is {{cin5::dynamically typed}}
- Functions are {{cin6::first-class objects}}
- The GIL affects {{cin7::multithreading}}

*Test your knowledge by filling in the blanks above!*
"""
        
        try:
            card_id = card_manager.create_card(
                deck_id=deck_id,
                front=test_card_content,
                back="This is a comprehensive test of cloze input functionality with code blocks, math, and markdown.",
                tags=['test', 'cloze-input', 'comprehensive'],
                hint="Think about Python's key characteristics and the fibonacci algorithm."
            )
            
            print(f"✅ Created test card: ID {card_id}")
            print(f"   Front content: {len(test_card_content)} characters")
            print(f"   Contains 7 cloze inputs")
            print(f"   Includes: markdown, code blocks, math expressions")
            
            # Verify the card
            created_card = card_manager.get_card(card_id)
            if created_card:
                print(f"✅ Card verified in database")
                
                # Test card type detection
                from app.core.card_type_factory import card_type_factory
                card_type = card_type_factory.get_card_type(created_card['front'])
                print(f"✅ Card type detected: {card_type.get_metadata().name}")
                
                # Test answer extraction
                import re
                pattern = r'\{\{cin(\d+)::([^}]+)\}\}'
                matches = re.findall(pattern, created_card['front'])
                answers = {num: answer for num, answer in matches}
                print(f"✅ Extracted answers: {answers}")
                
                print(f"\n🎯 TEST CARD READY!")
                print(f"📍 Deck: {deck_name}")
                print(f"🆔 Card ID: {card_id}")
                print(f"🎮 You can now test this card in the application")
                print(f"   1. Open Plus Ultra Cards")
                print(f"   2. Select '{deck_name}' deck")
                print(f"   3. Start a study session")
                print(f"   4. Test the cloze input functionality")
                
            else:
                print(f"❌ Card verification failed")
                return False
                
        except Exception as e:
            print(f"❌ Card creation failed: {e}")
            return False
        
        card_manager.close()
        return True
        
    except Exception as e:
        print(f"❌ CARD CREATION FAILED: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def main():
    """Create test cloze input card"""
    print("🧪 TEST CARD CREATION UTILITY")
    print("=" * 50)
    
    success = create_test_card()
    
    if success:
        print(f"\n🎊 TEST CARD CREATED SUCCESSFULLY!")
        print(f"✅ Comprehensive cloze input card ready for testing")
        print(f"✅ All features included: markdown, code, math, cloze inputs")
        print(f"✅ Ready to test in the application")
    else:
        print(f"\n💥 TEST CARD CREATION FAILED!")
        print(f"❌ Could not create test card")
    
    return success

if __name__ == "__main__":
    main()
