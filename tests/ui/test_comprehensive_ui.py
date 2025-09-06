"""
Comprehensive UI Tests for Plus Ultra Cards
Tests complete study workflow, rendering features, and edge cases.
"""
import os
import sys
from pathlib import Path
import pytest

# Ensure offscreen Qt for headless test
os.environ.setdefault("QT_QPA_PLATFORM", "minimal")

# Add app to path
sys.path.insert(0, str(Path(__file__).parents[2] / "plus_ultra_cards"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer, Qt

from app.core.card_manager import CardManager
from app.core.study_sessions import StudySession, StudyMode
from app.ui.gui.study_window import StudyWindow


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for the test module."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(["test", "-platform", "minimal"])
    yield app
    # Cleanup handled by pytest teardown


@pytest.fixture
def card_manager():
    """Create a fresh card manager for each test."""
    cm = CardManager()
    yield cm
    cm.close()


@pytest.fixture
def test_deck(card_manager):
    """Create a test deck with sample cards."""
    deck_id = card_manager.create_deck("Test Deck")
    
    # Add various card types
    cards = [
        {
            'front': '# Markdown Test\n\n**Bold** and *italic* text.\n\nLink: [Google](https://google.com)\n\nInline code: `print("hello")`',
            'back': 'Markdown features test',
            'tags': ['markdown']
        },
        {
            'front': 'Math formula: $$E = mc^2$$ is Einstein\'s equation.',
            'back': 'Energy-mass equivalence',
            'tags': ['math']
        },
        {
            'front': '{start.style::code[python]}\ndef factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)\n{end.style}\n\nWhat is the time complexity?',
            'back': 'O(n) time, O(n) space',
            'tags': ['code']
        },
        {
            'front': 'Standard cloze: Python is a {{c1::high-level}} programming language.',
            'back': '',
            'tags': ['cloze']
        },
        {
            'front': 'Cloze input: The capital of France is {{cin1::Paris}}.',
            'back': '',
            'tags': ['cloze-input']
        },
        {
            'front': '''Complex mixed content:
# Algorithm Analysis

Time complexity: **O(n log n)**

Reference: [Sorting Algorithms](https://en.wikipedia.org/wiki/Sorting_algorithm)

Implementation:
{start.style::code[python]}
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)
{end.style}

Best case: {{c1::O(n log n)}}
Space complexity: {{cin1::O(n)}}

Formula: $$T(n) = 2T(n/2) + O(n)$$''',
            'back': 'Comprehensive algorithm card',
            'tags': ['mixed', 'complex']
        }
    ]
    
    card_ids = []
    for card in cards:
        card_id = card_manager.create_card(deck_id, card['front'], card['back'], tags=card['tags'])
        card_ids.append(card_id)
    
    return deck_id, card_ids


def pump_events(app, cycles=10):
    """Pump Qt event loop to ensure UI updates."""
    for _ in range(cycles):
        QCoreApplication.processEvents(QEventLoop.AllEvents, 50)


class TestMarkdownRendering:
    """Test markdown rendering features."""
    
    def test_markdown_features(self, qapp, test_deck, card_manager):
        """Test that markdown renders correctly in study window."""
        deck_id, card_ids = test_deck
        session = StudySession(deck_id, StudyMode.CRAM, card_manager)
        
        # Navigate to markdown card (first one)
        session.current_card_index = 0
        
        win = StudyWindow(session, test_mode=True)
        win.setAttribute(Qt.WA_DontShowOnScreen, True)
        pump_events(qapp)
        
        html = win.card_front.text()
        
        # Check markdown features
        assert "<h1>" in html, "Headers should render"
        assert "<strong>" in html, "Bold should render"
        assert "<em>" in html, "Italic should render"
        assert '<a href="https://google.com"' in html, "Links should render"
        assert 'class="inline-code"' in html, "Inline code should render"
        
        win.close()


class TestMathRendering:
    """Test mathematical expression rendering."""
    
    def test_math_containers(self, qapp, test_deck, card_manager):
        """Test that math expressions appear in visual containers."""
        deck_id, card_ids = test_deck
        session = StudySession(deck_id, StudyMode.CRAM, card_manager)
        
        # Navigate to math card
        session.current_card_index = 1
        
        win = StudyWindow(session, test_mode=True)
        win.setAttribute(Qt.WA_DontShowOnScreen, True)
        pump_events(qapp)
        
        html = win.card_front.text()
        
        assert "math-container" in html, "Math should be in visual container"
        assert "E = mc<sup>2</sup>" in html, "Superscripts should render"
        
        win.close()


class TestCodeBlocks:
    """Test code block rendering."""
    
    def test_code_highlighting(self, qapp, test_deck, card_manager):
        """Test that code blocks render with proper styling."""
        deck_id, card_ids = test_deck
        session = StudySession(deck_id, StudyMode.CRAM, card_manager)
        
        # Navigate to code card
        session.current_card_index = 2
        
        win = StudyWindow(session, test_mode=True)
        win.setAttribute(Qt.WA_DontShowOnScreen, True)
        pump_events(qapp)
        
        html = win.card_front.text()
        
        assert "code-block" in html, "Code blocks should render"
        assert "def factorial" in html, "Code content should be preserved"
        assert 'data-language="python"' in html, "Language should be specified"
        
        win.close()


class TestClozeCards:
    """Test cloze deletion and input functionality."""
    
    def test_standard_cloze(self, qapp, test_deck, card_manager):
        """Test standard cloze deletion cards."""
        deck_id, card_ids = test_deck
        session = StudySession(deck_id, StudyMode.CRAM, card_manager)
        
        # Navigate to standard cloze card
        session.current_card_index = 3
        
        win = StudyWindow(session, test_mode=True)
        win.setAttribute(Qt.WA_DontShowOnScreen, True)
        pump_events(qapp)
        
        html = win.card_front.text()
        
        assert "cloze-blank" in html, "Cloze blanks should appear"
        assert "high-level" not in html, "Answer should be hidden"
        
        win.close()
    
    def test_cloze_input_side_panel(self, qapp, test_deck, card_manager):
        """Test cloze input cards create side panel fields."""
        deck_id, card_ids = test_deck
        session = StudySession(deck_id, StudyMode.CRAM, card_manager)
        
        # Navigate to cloze input card
        session.current_card_index = 4
        
        win = StudyWindow(session, test_mode=True)
        win.setAttribute(Qt.WA_DontShowOnScreen, True)
        pump_events(qapp)
        
        html = win.card_front.text()
        
        assert "cloze-input-placeholder" in html, "Cloze input placeholder should appear"
        assert len(win.cloze_input_fields) >= 1, "Side panel input fields should be created"
        assert "1" in win.cloze_input_fields, "Input field for cin1 should exist"
        
        # Test input field functionality
        input_field = win.cloze_input_fields["1"]
        input_field.setText("Paris")
        assert input_field.text() == "Paris", "Input field should accept text"
        
        win.close()


class TestMixedContent:
    """Test complex cards with mixed content types."""
    
    def test_complex_mixed_card(self, qapp, test_deck, card_manager):
        """Test card with markdown, math, code, and cloze content."""
        deck_id, card_ids = test_deck
        session = StudySession(deck_id, StudyMode.CRAM, card_manager)
        
        # Navigate to complex mixed card
        session.current_card_index = 5
        
        win = StudyWindow(session, test_mode=True)
        win.setAttribute(Qt.WA_DontShowOnScreen, True)
        pump_events(qapp)
        
        html = win.card_front.text()
        
        # Check all features are present
        assert "<h1>" in html, "Headers should work with mixed content"
        assert "<strong>" in html, "Bold should work with mixed content"
        assert '<a href=' in html, "Links should work with mixed content"
        assert "code-block" in html, "Code blocks should work with mixed content"
        assert "math-container" in html, "Math should work with mixed content"
        assert "cloze-blank" in html, "Standard cloze should work with mixed content"
        assert "cloze-input-placeholder" in html, "Cloze input should work with mixed content"
        
        # Check side panel for cloze input
        assert len(win.cloze_input_fields) >= 1, "Mixed content should create input fields"
        
        win.close()


class TestStudyWorkflow:
    """Test complete study session workflow."""
    
    def test_card_navigation(self, qapp, test_deck, card_manager):
        """Test navigating through cards in a study session."""
        deck_id, card_ids = test_deck
        session = StudySession(deck_id, StudyMode.CRAM, card_manager)
        
        win = StudyWindow(session, test_mode=True)
        win.setAttribute(Qt.WA_DontShowOnScreen, True)
        pump_events(qapp)
        
        # Test initial state
        assert session.current_card_index == 0, "Should start at first card"
        
        # Navigate through cards
        for i in range(min(3, len(card_ids))):
            session.current_card_index = i
            win.load_current_card()
            pump_events(qapp)
            
            html = win.card_front.text()
            assert len(html) > 0, f"Card {i} should have content"
        
        win.close()
    
    def test_error_handling(self, qapp, card_manager):
        """Test that malformed content doesn't crash the session."""
        deck_id = card_manager.create_deck("Error Test Deck")
        
        # Add a card with potentially problematic content
        malformed_content = """
        Broken style: {start.style::invalid
        Unclosed math: $$incomplete
        Nested cloze: {{c1::{{c2::nested}}}}
        """
        
        card_manager.create_card(deck_id, malformed_content, "")
        
        session = StudySession(deck_id, StudyMode.CRAM, card_manager)
        win = StudyWindow(session, test_mode=True)
        win.setAttribute(Qt.WA_DontShowOnScreen, True)
        pump_events(qapp)
        
        # Should not crash, should show error handling
        html = win.card_front.text()
        assert len(html) > 0, "Should show some content even with errors"
        
        win.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
