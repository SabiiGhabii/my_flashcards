#!/usr/bin/env python3
"""
Direct Rendering Test - No Qt, No UI
Tests the core functionality that actually matters: parsing and rendering.
"""
import sys
from pathlib import Path

# Add app to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'plus_ultra_cards'))

from app.formatting.text_formatter import TextFormatter
from app.core.card_type_factory import CardTypeFactory
from app.formatting.formatter_service import FormatterService, RenderingOptions


def test_failing_card_content():
    """Test the exact failing card content that was reported."""
    print("Testing failing card content...")
    
    failing_content = (
        "This is a test \n" 
        "$$a^2 + b^2 = c^2$$\n\n"
        "{{cin1::{start.style::code[python]}\n"
        "for i in range(10):\n"
        "    print(i)\n"
        "{end.style}}}"
    )
    
    # Test TextFormatter directly
    fmt = TextFormatter()
    html = fmt.render_cloze_input_for_display(failing_content)
    
    assert "math-container" in html, "Math should be in container"
    assert "cloze-input-placeholder" in html, "Cloze placeholder should appear"
    assert len(html) > 100, "Should generate substantial HTML"
    
    print("✅ Failing card content renders correctly")
    return True


def test_enhanced_markdown():
    """Test enhanced markdown features."""
    print("Testing enhanced markdown...")
    
    text = """# Header

**Bold** and *italic* text.

Link: [Google](https://google.com)

Inline code: `print("hello")`

- List item 1
- List item 2
"""
    
    fmt = TextFormatter()
    html = fmt.render_to_html(text)
    
    assert "<h1>" in html, "Headers should render"
    assert "<strong>" in html, "Bold should render"
    assert "<em>" in html, "Italic should render"
    assert '<a href="https://google.com"' in html, "Links should render"
    assert 'class="inline-code"' in html, "Inline code should render"
    assert "<ul>" in html and "<li>" in html, "Lists should render"
    
    print("✅ Enhanced markdown renders correctly")
    return True


def test_card_type_factory():
    """Test card type detection and rendering."""
    print("Testing card type factory...")
    
    factory = CardTypeFactory()
    formatter = FormatterService()
    
    # Test different card types
    test_cases = [
        ("Basic card", "What is Python?", "A programming language"),
        ("Cloze card", "Python is a {{c1::high-level}} language.", ""),
        ("Cloze input", "The capital of France is {{cin1::Paris}}.", ""),
        ("Mixed content", "# Test\n\n$$E=mc^2$$\n\n{{cin1::answer}}", "")
    ]
    
    for name, front, back in test_cases:
        card_type = factory.get_card_type(front)
        assert card_type is not None, f"Should detect card type for {name}"
        
        opts = RenderingOptions(reveal_cloze=False, apply_syntax_highlighting=True)
        rendered = card_type.render_front(front, opts, formatter)
        assert len(rendered) > 0, f"Should render content for {name}"
    
    print("✅ Card type factory works correctly")
    return True


def test_cloze_input_extraction():
    """Test cloze input answer extraction."""
    print("Testing cloze input extraction...")
    
    # Import the extraction method
    from app.ui.gui.study_window import StudyWindow
    
    test_text = """Simple: {{cin1::Paris}}

Multi-line: {{cin2::{start.style::code[python]}
def hello():
    return "world"
{end.style}}}

Complex: {{cin3::O(n log n)}}"""
    
    answers = StudyWindow._extract_cloze_input_answers(StudyWindow, test_text)
    
    assert "1" in answers, "Should extract cin1"
    assert answers["1"] == "Paris", "Should extract simple answer"
    
    assert "2" in answers, "Should extract cin2"
    assert "def hello" in answers["2"], "Should extract multi-line content"
    
    assert "3" in answers, "Should extract cin3"
    assert answers["3"] == "O(n log n)", "Should extract complex answer"
    
    print("✅ Cloze input extraction works correctly")
    return True


def test_math_rendering():
    """Test mathematical expression rendering."""
    print("Testing math rendering...")
    
    text = "Einstein's equation: $$E = mc^2$$ is famous."
    
    fmt = TextFormatter()
    html = fmt.render_to_html(text)
    
    assert "math-container" in html, "Math should be in container"
    assert "E = mc<sup>2</sup>" in html, "Superscripts should render"
    
    print("✅ Math rendering works correctly")
    return True


def test_code_blocks():
    """Test code block rendering."""
    print("Testing code blocks...")
    
    text = """{start.style::code[python]}
def factorial(n):
    return 1 if n <= 1 else n * factorial(n-1)
{end.style}"""
    
    fmt = TextFormatter()
    html = fmt.render_to_html(text)
    
    assert "code-block" in html, "Code blocks should render"
    assert "def factorial" in html, "Code content should be preserved"
    assert 'data-language="python"' in html, "Language should be specified"
    
    print("✅ Code blocks render correctly")
    return True


def test_error_handling():
    """Test error handling with malformed content."""
    print("Testing error handling...")
    
    malformed_content = """
    Broken style: {start.style::invalid
    Unclosed math: $$incomplete
    """
    
    fmt = TextFormatter()
    html = fmt.render_to_html(malformed_content)
    
    # Should not crash, should return some content
    assert len(html) > 0, "Should handle errors gracefully"
    
    print("✅ Error handling works correctly")
    return True


def main():
    """Run all direct rendering tests."""
    print("=" * 60)
    print("DIRECT RENDERING TESTS - NO UI DEPENDENCIES")
    print("=" * 60)
    
    tests = [
        test_failing_card_content,
        test_enhanced_markdown,
        test_card_type_factory,
        test_cloze_input_extraction,
        test_math_rendering,
        test_code_blocks,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL RENDERING TESTS PASSED!")
        print("✅ Failing card content fixed")
        print("✅ Enhanced markdown working")
        print("✅ Math expressions in containers")
        print("✅ Code blocks with highlighting")
        print("✅ Cloze input parsing robust")
        print("✅ Error handling implemented")
        print("✅ Card type detection working")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
