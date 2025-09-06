#!/usr/bin/env python3
"""
Comprehensive Diagnostic Test Suite for Plus Ultra Cards
Tests all critical functionality to identify broken features
"""

import sys
import traceback
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent / "plus_ultra_cards"))

def test_rendering_pipeline():
    """Test the core rendering pipeline for all content types"""
    print("\n🔧 TESTING RENDERING PIPELINE")
    print("=" * 50)
    
    try:
        from app.formatting.text_formatter import TextFormatter
        from app.formatting.formatter_service import FormatterService, RenderingOptions
        
        formatter = TextFormatter()
        service = FormatterService()
        
        test_cases = [
            {
                'name': 'Plain Text',
                'content': 'This is plain text with no markup.',
                'expected_features': ['basic_html']
            },
            {
                'name': 'Code Block',
                'content': '```python\ndef hello():\n    print("Hello World")\n```',
                'expected_features': ['code_block', 'syntax_highlighting']
            },
            {
                'name': 'Markdown',
                'content': '# Header\n\n**Bold text** and *italic text*\n\n- List item 1\n- List item 2',
                'expected_features': ['markdown', 'headers', 'formatting']
            },
            {
                'name': 'Standard Cloze',
                'content': 'Python is a {{c1::high-level}} programming language.',
                'expected_features': ['cloze_blanking', 'cloze_revealing']
            },
            {
                'name': 'Cloze Input',
                'content': 'Python is a {{cin1::high-level}} programming language.',
                'expected_features': ['cloze_input_blanking', 'cloze_input_revealing']
            },
            {
                'name': 'Math Expression',
                'content': 'The formula is $$E = mc^2$$ for energy.',
                'expected_features': ['math_rendering']
            },
            {
                'name': 'Mixed Content',
                'content': '# Code Example\n\n```python\ndef func(x):\n    return {{c1::x * 2}}\n```\n\nThe result is {{cin1::doubled}}.',
                'expected_features': ['markdown', 'code_block', 'cloze', 'cloze_input']
            },
            {
                'name': 'Code with Cloze',
                'content': '```python\ndef {{c1::factorial}}(n):\n    if n == {{c2::0}}:\n        return 1\n    return n * factorial({{c3::n-1}})\n```',
                'expected_features': ['code_block', 'cloze_in_code']
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            print(f"\nTesting: {test_case['name']}")
            print(f"Content: {test_case['content'][:50]}...")
            
            try:
                # Test basic rendering
                basic_html = formatter.render_to_html(test_case['content'])
                print(f"✅ Basic HTML rendering: OK")
                
                # Test cloze blanked
                cloze_blanked = formatter.render_cloze_blanked(test_case['content'])
                print(f"✅ Cloze blanked: OK")
                
                # Test cloze revealed
                cloze_revealed = formatter.render_cloze_revealed(test_case['content'])
                print(f"✅ Cloze revealed: OK")
                
                # Test cloze input methods
                if 'cin' in test_case['content']:
                    cloze_input_blanked = formatter.render_cloze_input_blanked(test_case['content'])
                    print(f"✅ Cloze input blanked: OK")
                    
                    cloze_input_revealed = formatter.render_cloze_input_revealed(test_case['content'])
                    print(f"✅ Cloze input revealed: OK")
                    
                    cloze_input_display = formatter.render_cloze_input_for_display(test_case['content'])
                    print(f"✅ Cloze input display: OK")
                
                # Test FormatterService
                options = RenderingOptions(reveal_cloze=False, apply_syntax_highlighting=True)
                service_result = service.render(test_case['content'], options)
                print(f"✅ FormatterService: OK")
                
                results[test_case['name']] = 'PASS'
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
                print(f"   Traceback: {traceback.format_exc()}")
                results[test_case['name']] = f'FAIL: {e}'
        
        print(f"\n📊 RENDERING PIPELINE RESULTS:")
        for name, result in results.items():
            status = "✅" if result == 'PASS' else "❌"
            print(f"{status} {name}: {result}")
        
        return all(result == 'PASS' for result in results.values())
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in rendering pipeline: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_card_types():
    """Test all card type functionality"""
    print("\n🃏 TESTING CARD TYPES")
    print("=" * 50)
    
    try:
        from app.core.card_types import CardTypeRegistry, BasicCard, ClozeCard, ClozeInputCard
        from app.formatting.formatter_service import FormatterService, RenderingOptions
        
        registry = CardTypeRegistry()
        formatter = FormatterService()
        
        test_cards = [
            {
                'name': 'Basic Card',
                'front': 'What is Python?',
                'back': 'A high-level programming language',
                'expected_type': BasicCard
            },
            {
                'name': 'Cloze Card',
                'front': 'Python is a {{c1::high-level}} programming language.',
                'back': '',
                'expected_type': ClozeCard
            },
            {
                'name': 'Cloze Input Card',
                'front': 'Python is a {{cin1::high-level}} programming language.',
                'back': '',
                'expected_type': ClozeInputCard
            },
            {
                'name': 'Mixed Cloze Card',
                'front': 'Python is {{c1::high-level}} and {{cin1::interpreted}}.',
                'back': '',
                'expected_type': ClozeInputCard  # Should prioritize cloze input
            }
        ]
        
        results = {}
        
        for test_card in test_cards:
            print(f"\nTesting: {test_card['name']}")
            print(f"Front: {test_card['front']}")
            
            try:
                # Test card type detection
                card_type = registry.get_card_type(test_card['front'])
                print(f"✅ Card type detected: {type(card_type).__name__}")
                
                # Test rendering methods
                options = RenderingOptions(reveal_cloze=False, apply_syntax_highlighting=True)
                
                front_html = card_type.render_front(test_card['front'], options, formatter)
                print(f"✅ Front rendering: OK")
                
                if hasattr(card_type, 'render_answer'):
                    answer_html = card_type.render_answer(test_card['front'], options, formatter)
                    print(f"✅ Answer rendering: OK")
                
                # Test single-sided detection
                is_single_sided = card_type.is_single_sided()
                print(f"✅ Single-sided detection: {is_single_sided}")
                
                results[test_card['name']] = 'PASS'
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
                print(f"   Traceback: {traceback.format_exc()}")
                results[test_card['name']] = f'FAIL: {e}'
        
        print(f"\n📊 CARD TYPES RESULTS:")
        for name, result in results.items():
            status = "✅" if result == 'PASS' else "❌"
            print(f"{status} {name}: {result}")
        
        return all(result == 'PASS' for result in results.values())
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in card types: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_cloze_input_system():
    """Test the cloze input system specifically"""
    print("\n🎯 TESTING CLOZE INPUT SYSTEM")
    print("=" * 50)
    
    try:
        from app.core.card_manager import CardManager
        
        card_manager = CardManager()
        
        # Create test deck
        deck_name = "🧪 Diagnostic Test Deck"
        try:
            deck_id = card_manager.create_deck(deck_name)
        except:
            # Deck might exist
            decks = card_manager.get_all_decks()
            deck_id = next((d['id'] for d in decks if d['name'] == deck_name), None)
            if not deck_id:
                raise Exception("Could not create test deck")
        
        # Test cloze input cards
        test_cards = [
            {
                'front': 'Simple test: {{cin1::answer}}',
                'back': 'Test card',
                'description': 'Single cloze input'
            },
            {
                'front': 'Multiple: {{cin1::first}} and {{cin2::second}}',
                'back': 'Test card',
                'description': 'Multiple cloze inputs'
            },
            {
                'front': 'Math: {{cin1::$$E = mc^2$$}} is Einstein\'s equation',
                'back': 'Test card',
                'description': 'Cloze input with math'
            }
        ]
        
        results = {}
        
        for i, test_card in enumerate(test_cards):
            print(f"\nTesting: {test_card['description']}")
            
            try:
                # Create card
                card_id = card_manager.create_card(
                    deck_id=deck_id,
                    front=test_card['front'],
                    back=test_card['back'],
                    tags=['diagnostic', 'test']
                )
                print(f"✅ Card created: ID {card_id}")
                
                # Retrieve card
                card = card_manager.get_card(card_id)
                print(f"✅ Card retrieved: {card['front'][:30]}...")
                
                # Test cloze input detection
                has_cloze_input = '{{cin' in card['front']
                print(f"✅ Cloze input detected: {has_cloze_input}")
                
                results[test_card['description']] = 'PASS'
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
                results[test_card['description']] = f'FAIL: {e}'
        
        card_manager.close()
        
        print(f"\n📊 CLOZE INPUT SYSTEM RESULTS:")
        for name, result in results.items():
            status = "✅" if result == 'PASS' else "❌"
            print(f"{status} {name}: {result}")
        
        return all(result == 'PASS' for result in results.values())
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in cloze input system: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def main():
    """Run comprehensive diagnostic tests"""
    print("🔍 COMPREHENSIVE DIAGNOSTIC TEST SUITE")
    print("=" * 70)
    print("Testing all critical functionality to identify broken features...")
    
    test_results = {}
    
    # Test 1: Rendering Pipeline
    test_results['Rendering Pipeline'] = test_rendering_pipeline()
    
    # Test 2: Card Types
    test_results['Card Types'] = test_card_types()
    
    # Test 3: Cloze Input System
    test_results['Cloze Input System'] = test_cloze_input_system()
    
    # Summary
    print("\n" + "=" * 70)
    print("🏁 DIAGNOSTIC TEST SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Core functionality is working")
        print("✅ Ready for architectural improvements")
    else:
        print("⚠️  CRITICAL ISSUES FOUND!")
        print("❌ Some core functionality is broken")
        print("🔧 Immediate fixes required before architectural work")
    
    return all_passed

if __name__ == "__main__":
    main()
