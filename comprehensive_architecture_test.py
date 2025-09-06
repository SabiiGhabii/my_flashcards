#!/usr/bin/env python3
"""
Comprehensive Architecture Test Suite
Tests the new modular template-based architecture
"""

import sys
import traceback
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent / "plus_ultra_cards"))

def test_card_type_factory():
    """Test the new card type factory system"""
    print("\n🏭 TESTING CARD TYPE FACTORY")
    print("=" * 50)
    
    try:
        from app.core.card_type_factory import CardTypeFactory, CardTypeInterface
        
        factory = CardTypeFactory()
        
        test_cases = [
            {
                'name': 'Basic Card',
                'front': 'What is Python?',
                'back': 'A programming language',
                'expected_type': 'Basic Card'
            },
            {
                'name': 'Cloze Card',
                'front': 'Python is a {{c1::high-level}} language.',
                'back': '',
                'expected_type': 'Cloze Card'
            },
            {
                'name': 'Cloze Input Card',
                'front': 'Python is a {{cin1::high-level}} language.',
                'back': '',
                'expected_type': 'Cloze Input Card'
            },
            {
                'name': 'Mixed Content (should prioritize cloze input)',
                'front': 'Python is {{c1::high-level}} and {{cin1::interpreted}}.',
                'back': '',
                'expected_type': 'Cloze Input Card'
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            print(f"\nTesting: {test_case['name']}")
            
            try:
                # Test card type detection
                card_type = factory.get_card_type(test_case['front'], test_case['back'])
                detected_type = card_type.get_metadata().name
                
                print(f"✅ Detected type: {detected_type}")
                
                if detected_type == test_case['expected_type']:
                    print(f"✅ Correct type detection")
                    
                    # Test validation
                    validation = factory.validate_card_content(test_case['front'], test_case['back'])
                    print(f"✅ Validation: {'Valid' if validation['is_valid'] else 'Invalid'}")
                    
                    # Test interface config
                    config = card_type.get_study_interface_config()
                    print(f"✅ Interface config: {config['type']}")
                    
                    results[test_case['name']] = 'PASS'
                else:
                    print(f"❌ Expected {test_case['expected_type']}, got {detected_type}")
                    results[test_case['name']] = f'FAIL: Wrong type'
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
                results[test_case['name']] = f'FAIL: {e}'
        
        print(f"\n📊 CARD TYPE FACTORY RESULTS:")
        for name, result in results.items():
            status = "✅" if result == 'PASS' else "❌"
            print(f"{status} {name}: {result}")
        
        return all(result == 'PASS' for result in results.values())
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_rendering_template_system():
    """Test the new rendering template system"""
    print("\n🎨 TESTING RENDERING TEMPLATE SYSTEM")
    print("=" * 50)
    
    try:
        from app.rendering.template_system import RenderingTemplateEngine, RenderingContext
        
        engine = RenderingTemplateEngine()
        
        test_cases = [
            {
                'name': 'Math Expression',
                'content': 'The formula is $$E = mc^2$$ for energy.',
                'context': RenderingContext(
                    content_type='text',
                    apply_syntax_highlighting=True,
                    reveal_cloze=False,
                    inline_css='',
                    custom_options={}
                ),
                'expected_features': ['math-container']
            },
            {
                'name': 'Code Block',
                'content': '```python\ndef hello():\n    print("Hello")\n```',
                'context': RenderingContext(
                    content_type='text',
                    apply_syntax_highlighting=True,
                    reveal_cloze=False,
                    inline_css='',
                    custom_options={}
                ),
                'expected_features': ['code-block']
            },
            {
                'name': 'Cloze Deletion',
                'content': 'Python is a {{c1::high-level}} language.',
                'context': RenderingContext(
                    content_type='text',
                    apply_syntax_highlighting=True,
                    reveal_cloze=False,
                    inline_css='',
                    custom_options={}
                ),
                'expected_features': ['cloze-blank']
            },
            {
                'name': 'Cloze Input',
                'content': 'Python is a {{cin1::high-level}} language.',
                'context': RenderingContext(
                    content_type='text',
                    apply_syntax_highlighting=True,
                    reveal_cloze=False,
                    inline_css='',
                    custom_options={}
                ),
                'expected_features': ['cloze-input-placeholder']
            },
            {
                'name': 'Mixed Content',
                'content': '# Code Example\n\n```python\ndef func():\n    return 42\n```\n\nResult: {{cin1::42}} and {{c1::value}}',
                'context': RenderingContext(
                    content_type='text',
                    apply_syntax_highlighting=True,
                    reveal_cloze=False,
                    inline_css='',
                    custom_options={}
                ),
                'expected_features': ['h1', 'code-block', 'cloze-blank', 'cloze-input-placeholder']
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            print(f"\nTesting: {test_case['name']}")
            print(f"Content: {test_case['content'][:50]}...")
            
            try:
                # Render content
                rendered = engine.render(test_case['content'], test_case['context'])
                print(f"✅ Rendering completed")

                # Debug: Print rendered content for mixed content test
                if test_case['name'] == 'Mixed Content':
                    print(f"DEBUG: Rendered content: {rendered}")

                # Check for expected features
                missing_features = []
                for feature in test_case['expected_features']:
                    if feature not in rendered:
                        missing_features.append(feature)

                if not missing_features:
                    print(f"✅ All expected features present: {test_case['expected_features']}")
                    results[test_case['name']] = 'PASS'
                else:
                    print(f"❌ Missing features: {missing_features}")
                    results[test_case['name']] = f'FAIL: Missing {missing_features}'
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
                results[test_case['name']] = f'FAIL: {e}'
        
        print(f"\n📊 RENDERING TEMPLATE SYSTEM RESULTS:")
        for name, result in results.items():
            status = "✅" if result == 'PASS' else "❌"
            print(f"{status} {name}: {result}")
        
        return all(result == 'PASS' for result in results.values())
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_study_template_system():
    """Test the study template system (logic only, no UI)"""
    print("\n📚 TESTING STUDY TEMPLATE SYSTEM")
    print("=" * 50)
    
    try:
        from app.ui.study_template import StudyTemplateManager, StudyInterfaceType, StudyInterfaceConfig
        
        manager = StudyTemplateManager()
        
        test_cases = [
            {
                'name': 'Basic Interface',
                'interface_type': StudyInterfaceType.BASIC,
                'config': StudyInterfaceConfig(
                    interface_type=StudyInterfaceType.BASIC,
                    show_flip_button=True,
                    show_answer_buttons=True,
                    side_panel_type=None,
                    custom_buttons=[],
                    multi_attempt=False,
                    max_attempts=1,
                    custom_handlers={}
                )
            },
            {
                'name': 'Cloze Input Interface',
                'interface_type': StudyInterfaceType.CLOZE_INPUT,
                'config': StudyInterfaceConfig(
                    interface_type=StudyInterfaceType.CLOZE_INPUT,
                    show_flip_button=False,
                    show_answer_buttons=False,
                    side_panel_type='cloze_input',
                    custom_buttons=['check_answers'],
                    multi_attempt=True,
                    max_attempts=3,
                    custom_handlers={}
                )
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            print(f"\nTesting: {test_case['name']}")
            
            try:
                # Test plugin availability
                plugin = manager.get_plugin(test_case['interface_type'])
                if plugin:
                    print(f"✅ Plugin available: {plugin.get_interface_type().value}")
                    
                    # Test plugin methods (without creating actual widgets)
                    interface_type = plugin.get_interface_type()
                    print(f"✅ Interface type: {interface_type.value}")
                    
                    # Test action handling (mock)
                    if test_case['interface_type'] == StudyInterfaceType.CLOZE_INPUT:
                        # Mock cloze input action
                        mock_result = plugin.handle_user_action("check_answers", {'1': 'test'}, None)
                        print(f"✅ Action handling: {mock_result.get('action', 'unknown')}")
                    
                    results[test_case['name']] = 'PASS'
                else:
                    print(f"❌ Plugin not available")
                    results[test_case['name']] = 'FAIL: No plugin'
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
                results[test_case['name']] = f'FAIL: {e}'
        
        print(f"\n📊 STUDY TEMPLATE SYSTEM RESULTS:")
        for name, result in results.items():
            status = "✅" if result == 'PASS' else "❌"
            print(f"{status} {name}: {result}")
        
        return all(result == 'PASS' for result in results.values())
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_integration():
    """Test integration between all architectural components"""
    print("\n🔗 TESTING ARCHITECTURAL INTEGRATION")
    print("=" * 50)
    
    try:
        from app.core.card_type_factory import CardTypeFactory
        from app.rendering.template_system import RenderingTemplateEngine, RenderingContext
        from app.ui.study_template import StudyTemplateManager, StudyInterfaceType
        
        # Create instances
        card_factory = CardTypeFactory()
        rendering_engine = RenderingTemplateEngine()
        study_manager = StudyTemplateManager()
        
        # Test integration scenario
        test_card = {
            'front': 'The formula $$E = mc^2$$ has {{cin1::energy}} and {{c1::mass}}.',
            'back': 'Physics equation'
        }
        
        print(f"Testing integration with: {test_card['front'][:50]}...")
        
        # Step 1: Detect card type
        card_type = card_factory.get_card_type(test_card['front'], test_card['back'])
        print(f"✅ Card type detected: {card_type.get_metadata().name}")
        
        # Step 2: Get study interface config
        interface_config = card_type.get_study_interface_config()
        print(f"✅ Interface config: {interface_config['type']}")
        
        # Step 3: Test rendering
        context = RenderingContext(
            content_type='text',
            apply_syntax_highlighting=True,
            reveal_cloze=False,
            inline_css='',
            custom_options={}
        )
        rendered = rendering_engine.render(test_card['front'], context)
        print(f"✅ Rendering completed: {len(rendered)} characters")
        
        # Step 4: Check if study interface plugin exists
        interface_type = StudyInterfaceType(interface_config['type'])
        plugin = study_manager.get_plugin(interface_type)
        if plugin:
            print(f"✅ Study interface plugin available: {plugin.get_interface_type().value}")
        else:
            print(f"❌ No study interface plugin for: {interface_type}")
            return False
        
        # Step 5: Validate content
        validation = card_factory.validate_card_content(test_card['front'], test_card['back'])
        print(f"✅ Content validation: {'Valid' if validation['is_valid'] else 'Invalid'}")
        
        print(f"✅ Full integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ INTEGRATION ERROR: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def main():
    """Run comprehensive architecture tests"""
    print("🏗️  COMPREHENSIVE ARCHITECTURE TEST SUITE")
    print("=" * 70)
    print("Testing the new modular template-based architecture...")
    
    test_results = {}
    
    # Test 1: Card Type Factory
    test_results['Card Type Factory'] = test_card_type_factory()
    
    # Test 2: Rendering Template System
    test_results['Rendering Template System'] = test_rendering_template_system()
    
    # Test 3: Study Template System
    test_results['Study Template System'] = test_study_template_system()
    
    # Test 4: Integration
    test_results['Architectural Integration'] = test_integration()
    
    # Summary
    print("\n" + "=" * 70)
    print("🏁 ARCHITECTURE TEST SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ALL ARCHITECTURE TESTS PASSED!")
        print("✅ Modular template-based architecture is working")
        print("✅ Card Type Factory Pattern implemented")
        print("✅ Rendering Template System operational")
        print("✅ Study Session Template system functional")
        print("✅ All components integrate successfully")
        print("🚀 Ready for production deployment!")
    else:
        print("⚠️  ARCHITECTURE ISSUES FOUND!")
        print("❌ Some architectural components are broken")
        print("🔧 Fixes required before deployment")
    
    return all_passed

if __name__ == "__main__":
    main()
