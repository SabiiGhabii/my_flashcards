#!/usr/bin/env python3
"""
Headless UI Smoke Test for Plus Ultra Cards
- Forces offscreen Qt platform
- Creates a deck and several sample cards
- Launches a real StudyWindow
- Verifies HTML features (markdown, math, code, cloze placeholders)
- Verifies cloze input side panel appears for cin cards
Exit code 0 on success, non-zero on failure.
"""
import os
import sys
from pathlib import Path

# Ensure repository root on path
ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / 'plus_ultra_cards'))

# Force minimal platform via argv (more reliable than offscreen on Windows)
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer, Qt
from app.core.card_manager import CardManager
from app.core.study_sessions import StudySession, StudyMode
from app.ui.gui.study_window import StudyWindow


def add_cards(cm: CardManager, deck_id: int):
    samples = []

    # 1) Failing case provided by user
    samples.append({
        'name': 'Failing Mixed Cloze Input',
        'front': (
            "This is a test \n"
            "$$a^2 + b^2 = c^2$$\n\n"
            "{{cin1::{start.style::code[python]}\n"
            "for i in range(10):\n"
            "    print(i)\n"
            "{end.style}}}"
        ),
        'back': ''
    })

    # 2) Enhanced markdown + standard cloze
    samples.append({
        'name': 'Enhanced Markdown + Cloze',
        'front': (
            "# Header\n\n**Bold** and *italic* text.\n\n"
            "Link: [Google](https://google.com)\n\n"
            "Inline code: `print('hello')`\n\n"
            "- item 1\n- item 2\n\n"
            "Python is a {{c1::high-level}} language."
        ),
        'back': ''
    })

    # 3) Code style sections + cloze input separate
    samples.append({
        'name': 'Code + Separate Cloze Input',
        'front': (
            "{start.style::code[python]}\n"
            "def add(a, b):\n    return a + b\n"
            "{end.style}\n\n"
            "Result is {{cin1::sum}}."
        ),
        'back': ''
    })

    # 4) Mixed math + cloze input
    samples.append({
        'name': 'Math + Cloze Input',
        'front': (
            "Compute energy: $$E = mc^2$$ where E is {{cin1::energy}}."
        ),
        'back': ''
    })

    ids = []
    for s in samples:
        cid = cm.create_card(deck_id, s['front'], s['back'], tags=['ui-smoke'])
        ids.append(cid)
    return ids


def assert_html(html: str, expects):
    def must(be_true: bool, msg: str):
        if not be_true:
            raise AssertionError(msg)

    # general checks
    if expects.get('markdown', False):
        must('<h1>' in html or '<h2>' in html or '<strong>' in html or '<em>' in html or '<ul>' in html, 'Markdown expected')
    if expects.get('enhanced_markdown', False):
        must('<a href=' in html and 'inline-code' in html, 'Enhanced markdown (links + inline code) expected')
    if expects.get('math', False):
        must('math-container' in html, 'Math container expected')
    if expects.get('code', False):
        must('code-block' in html or 'style-code' in html or '<pre' in html, 'Code block expected')
    if expects.get('cloze_placeholder', False):
        must('cloze-input-placeholder' in html or 'cloze-input-blank' in html, 'Cloze placeholder expected')


def main():
    app = QApplication.instance() or QApplication(["ui-smoke", "-platform", "windows"])
    cm = CardManager()

    # Create deck
    deck_name = '🧪 UI Smoke Deck'
    try:
        deck_id = cm.create_deck(deck_name)
    except Exception:
        # Find existing
        for d in cm.get_all_decks():
            if d['name'] == deck_name:
                deck_id = d['id']
                break
        else:
            raise

    add_cards(cm, deck_id)

    # Open study session
    session = StudySession(deck_id, StudyMode.CRAM, cm)
    win = StudyWindow(session, test_mode=True)
    # Ensure the window is never shown to avoid plugin issues
    win.setAttribute(Qt.WA_DontShowOnScreen, True)

    # Inspect current (first) card
    html = win.card_front.text()
    # Expect math and cloze placeholder for first failing example (no markdown h1)
    assert_html(html, {
        'math': True,
        'cloze_placeholder': True
    })

    # Verify side panel has fields
    if not win.cloze_input_fields:
        raise AssertionError('Expected cloze input fields for cin card')

    # Move to next card and verify enhanced markdown works
    session.next_card()
    win.load_current_card()
    html2 = win.card_front.text()
    assert_html(html2, {
        'markdown': True,
        'enhanced_markdown': True
    })

    # Move to third card (code + cin)
    session.next_card()
    win.load_current_card()
    html3 = win.card_front.text()
    assert_html(html3, {
        'code': True,
        'cloze_placeholder': True
    })

    # Let Qt finalize any pending events to avoid plugin stalls, then quit
    for _ in range(10):
        QCoreApplication.processEvents(QEventLoop.AllEvents, 50)
    QTimer.singleShot(50, app.quit)
    app.exec()

    # Cleanup
    cm.close()
    win.close()
    print('UI smoke test passed')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print('UI smoke test failed:', e)
        raise SystemExit(1)

