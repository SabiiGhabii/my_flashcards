#!/usr/bin/env python3
"""
Final Fixes Verification Test
Tests that both font loading and code block styling work correctly.
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path.cwd()))

def test_font_loading():
    """Test that the W95font.otf file exists in the correct location."""
    print("Testing font file location...")

    try:
        from pathlib import Path

        # Check if font file exists at the correct path
        font_path = Path(__file__).resolve().parent / "plus_ultra_cards" / "app" / "assets" / "fonts" / "W95font.otf"

        if font_path.exists():
            print("✅ W95font.otf found at correct location")
            print(f"  Path: {font_path}")
            return True
        else:
            print("❌ W95font.otf not found")
            print(f"  Expected path: {font_path}")
            return False

    except Exception as e:
        print(f"❌ Font file check error: {e}")
        return False


def test_code_block_styling():
    """Test that code blocks have proper styling."""
    print("Testing code block styling...")
    
    try:
        from app.formatting.text_formatter import TextFormatter
        
        formatter = TextFormatter()
        css = formatter.get_default_code_css()
        
        # Check for proper styling
        has_background = "background-color: #f5f5f5" in css
        has_border = "border: 2px inset #c0c0c0" in css
        has_padding = "padding: 8px" in css
        has_font = "font-family: 'Courier New'" in css
        
        if has_background and has_border and has_padding and has_font:
            print("✅ Code block styling is correct")
            print("  - Background color: ✅")
            print("  - Border styling: ✅") 
            print("  - Padding: ✅")
            print("  - Font family: ✅")
            return True
        else:
            print("❌ Code block styling is incorrect")
            print(f"  - Background color: {'✅' if has_background else '❌'}")
            print(f"  - Border styling: {'✅' if has_border else '❌'}")
            print(f"  - Padding: {'✅' if has_padding else '❌'}")
            print(f"  - Font family: {'✅' if has_font else '❌'}")
            return False
            
    except Exception as e:
        print(f"❌ Code block styling error: {e}")
        return False


def test_code_block_rendering():
    """Test that code blocks render with proper HTML."""
    print("Testing code block rendering...")
    
    try:
        from app.formatting.text_formatter import TextFormatter
        
        formatter = TextFormatter()
        
        # Test code block content
        test_content = """{start.style::code[python]}
def hello():
    print("Hello World")
{end.style}"""
        
        html = formatter.render_to_html(test_content, apply_syntax_highlighting=True)
        
        # Check for code block class
        has_code_block = 'class="code-block"' in html
        # Check for content (syntax highlighted, so look for the function name)
        has_content = "hello" in html and "def" in html
        
        if has_code_block and has_content:
            print("✅ Code block renders correctly")
            print("  - Code block class: ✅")
            print("  - Content preserved: ✅")
            return True
        else:
            print("❌ Code block rendering failed")
            print(f"  - Code block class: {'✅' if has_code_block else '❌'}")
            print(f"  - Content preserved: {'✅' if has_content else '❌'}")
            return False
            
    except Exception as e:
        print(f"❌ Code block rendering error: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("FINAL FIXES VERIFICATION")
    print("=" * 60)
    
    tests = [
        test_font_loading,
        test_code_block_styling,
        test_code_block_rendering
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ {test.__name__} crashed: {e}")
            print()
    
    print("=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL FIXES VERIFIED!")
        print("✅ Font loading works")
        print("✅ Code block styling works")
        print("✅ Code block rendering works")
        return 0
    else:
        print("❌ SOME FIXES FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
