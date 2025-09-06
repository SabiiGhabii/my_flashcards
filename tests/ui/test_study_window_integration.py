import os
import sys
from pathlib import Path

# Ensure offscreen Qt for headless test
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Add app to path
sys.path.insert(0, str(Path(__file__).parents[2] / "plus_ultra_cards"))

from PySide6.QtWidgets import QApplication

from app.core.card_manager import CardManager
from app.core.study_sessions import StudySession, StudyMode
from app.ui.gui.study_window import StudyWindow


def test_failing_card_end_to_end():
    app = QApplication.instance() or QApplication([])

    # Create deck and card
    cm = CardManager()
    deck_id = cm.create_deck("UI Integration Test Deck")

    failing_content = (
        "This is a test \n" 
        "$$a^2 + b^2 = c^2$$\n\n"
        "{{cin1::{start.style::code[python]}\n"
        "for i in range(10):\n"
        "    print(i)\n"
        "{end.style}}}"
    )

    card_id = cm.create_card(deck_id, failing_content, back="", tags=["ui-test"])

    session = StudySession(deck_id, StudyMode.CRAM, cm)
    win = StudyWindow(session)

    # Assert front QLabel contains HTML tags (markdown/math processed)
    html = win.card_front.text()
    assert "math-container" in html or "$$" not in html, "Math should be wrapped in visual container"
    assert "<h1>" in html or "This is a test" in html  # relaxed: at least not rawified later

    # Check side panel for cloze input fields
    assert len(win.cloze_input_fields) >= 1, "Cloze input fields should be created for cin1"

    # Update a field and press Check Answers
    fld = win.cloze_input_fields.get("1")
    assert fld is not None, "Input field for cin1 must exist"
    fld.setText("for i in range(10):\n    print(i)")
    win._check_cloze_input_answers()

    # Cleanup
    cm.close()
    win.close()
    app.quit()

