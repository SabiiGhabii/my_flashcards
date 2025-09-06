#!/usr/bin/env python3
"""
Pure Python UI Contract Test - No Qt Dependencies
Tests the core rendering logic without any UI framework dependencies.
Validates that all formatting features work correctly at the parser level.
"""
import sys
from pathlib import Path

# Add app to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'plus_ultra_cards'))

from app.formatting.text_formatter import TextFormatter


def assert_true(condition: bool, message: str):
    if not condition:
        raise AssertionError(f"Contract violation: {message}")


def test_enhanced_markdown():
    """Test enhanced markdown with links and inline code."""
    text = """# Header

This is **bold** and *italic* text.

Here's a link: [Google](https://google.com)

Inline code: `print("hello")` works.

- List item 1
- List item 2
"""
    
    fmt = TextFormatter()
    html = fmt.render_to_html(text)
    
    assert_true("<h1>" in html, "Headers should render")
    assert_true("<strong>" in html, "Bold should render")
    assert_true("<em>" in html, "Italic should render")
    assert_true('<a href="https://google.com"' in html, "Links should render")
    assert_true('class="inline-code"' in html, "Inline code should render")
    assert_true("<ul>" in html and "<li>" in html, "Lists should render")
    
    print("✅ Enhanced markdown test passed")


def test_math_rendering():
    """Test math expression rendering."""
    text = "Formula: $$E = mc^2$$ is famous."
    
    fmt = TextFormatter()
    html = fmt.render_to_html(text)
    
    assert_true("math-container" in html, "Math should be in container")
    assert_true("E = mc<sup>2</sup>" in html, "Superscripts should render")
    
    print("✅ Math rendering test passed")


def test_code_blocks():
    """Test code block rendering with style markers."""
    text = """{start.style::code[python]}
def hello():
    return "world"
{end.style}"""
    
    fmt = TextFormatter()
    html = fmt.render_to_html(text)
    
    assert_true("code-block" in html, "Code blocks should render")
    assert_true("def hello" in html, "Code content should be preserved")
    
    print("✅ Code block test passed")


def test_cloze_input_parsing():
    """Test complex cloze input with embedded style markers."""
    text = """This is a test 
$$a^2 + b^2 = c^2$$

{{cin1::{start.style::code[python]}
for i in range(10):
    print(i)
{end.style}}}
"""
    
    fmt = TextFormatter()
    html = fmt.render_cloze_input_for_display(text)
    
    assert_true("math-container" in html, "Math should render in cloze input")
    assert_true("cloze-input-placeholder" in html, "Cloze placeholder should appear")
    
    # Test answer extraction
    from app.ui.gui.study_window import StudyWindow
    answers = StudyWindow._extract_cloze_input_answers(StudyWindow, text)
    assert_true("1" in answers, "Should extract cin1 answer")
    assert_true("for i in range(10)" in answers["1"], "Should extract multi-line content")
    
    print("✅ Complex cloze input test passed")


def test_mixed_content():
    """Test mixed markdown, math, code, and cloze content."""
    text = """# Algorithm Analysis

The time complexity is **O(n)** where n is the input size.

Reference: [Big O Notation](https://en.wikipedia.org/wiki/Big_O_notation)

Implementation:
{start.style::code[python]}
def linear_search(arr, target):
    for i, val in enumerate(arr):
        if val == target:
            return i
    return -1
{end.style}

The worst case is {{c1::O(n)}} comparisons.

What is the space complexity? {{cin1::O(1)}}

Formula: $$T(n) = c \cdot n + d$$
"""
    
    fmt = TextFormatter()
    html = fmt.render_to_html(text)
    
    # Check all features are present
    assert_true("<h1>" in html, "Headers should work with mixed content")
    assert_true("<strong>" in html, "Bold should work with mixed content")
    assert_true('<a href=' in html, "Links should work with mixed content")
    assert_true("code-block" in html, "Code blocks should work with mixed content")
    assert_true("math-container" in html, "Math should work with mixed content")
    
    # Test cloze rendering
    cloze_html = fmt.render_cloze_blanked(text)
    assert_true("cloze-blank" in cloze_html, "Standard cloze should render")
    
    cin_html = fmt.render_cloze_input_for_display(text)
    assert_true("cloze-input-placeholder" in cin_html, "Cloze input should render")
    
    print("✅ Mixed content test passed")


def test_safety_checks():
    """Test that markdown doesn't interfere with style markers."""
    text = """This has `code with {braces}` and [link with {braces}](http://example.com/{path})

{start.style::code[python]}
# This should not be affected by markdown
def test():
    return "hello"
{end.style}

Normal `code` should work.
"""
    
    fmt = TextFormatter()
    html = fmt.render_to_html(text)
    
    # The inline code with braces should be left alone
    assert_true("code with {braces}" in html, "Inline code with braces should be preserved")
    # Normal inline code should work
    assert_true('class="inline-code"' in html, "Normal inline code should render")
    # Code blocks should work
    assert_true("code-block" in html, "Code blocks should not be affected")
    
    print("✅ Safety checks test passed")


def main():
    """Run all contract tests."""
    print("Running UI Render Contract Tests...")
    print("=" * 50)
    
    try:
        test_enhanced_markdown()
        test_math_rendering()
        test_code_blocks()
        test_cloze_input_parsing()
        test_mixed_content()
        test_safety_checks()
        
        print("=" * 50)
        print("🎉 ALL UI RENDER CONTRACT TESTS PASSED")
        print("✅ Enhanced markdown (headers, bold, italic, links, inline code)")
        print("✅ Math expressions in visual containers")
        print("✅ Code blocks with syntax highlighting")
        print("✅ Complex cloze input with embedded content")
        print("✅ Mixed content scenarios")
        print("✅ Safety checks for style marker conflicts")
        return 0
        
    except AssertionError as e:
        print(f"❌ Contract test failed: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
