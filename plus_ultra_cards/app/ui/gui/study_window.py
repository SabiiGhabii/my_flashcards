"""
Study Window for Plus Ultra Cards
Handles all study modes with retro95 styling.
Enhanced with code formatting and syntax highlighting support.
"""

import sys
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QKeySequence
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox, QRadioButton,
    QButtonGroup, QProgressBar, QMessageBox, QScrollArea,
    QSpinBox, QCheckBox, QComboBox, QTableWidget, QTableWidgetItem, QLineEdit
)

from app.ui.retro95 import RetroSeparator
from app.core.card_type_factory import card_type_factory
from app.core.study_sessions import StudyMode, SessionState
from app.core.config_manager import get_config
from app.ui.enhanced_text_widgets import FormattedTextDisplay
from app.core.study_controller import StudyController
from app.formatting.text_formatter import TextFormatter as _TF_CSS2
import time


class StudyOptionsDialog(QDialog):
    """Dialog for selecting study mode and options."""
    
    def __init__(self, deck_id, card_manager, parent=None):
        super().__init__(parent)
        self.deck_id = deck_id
        self.card_manager = card_manager
        self.selected_mode = None
        self.selected_options = {}
        
        self.setWindowTitle("Study Options")
        self.setModal(True)
        # Size to content to avoid geometry warnings on some displays
        self.setup_ui()
        try:
            self.adjustSize()
        except Exception:
            pass
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Deck info
        deck = self.card_manager.get_deck(self.deck_id)
        deck_label = QLabel(f"Deck: {deck['name']}")
        deck_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(deck_label)
        
        stats = self.card_manager.get_deck_statistics(self.deck_id)
        stats_label = QLabel(f"Total Cards: {stats['total_cards']} | Due: {stats['due_cards']}")
        layout.addWidget(stats_label)
        
        layout.addWidget(RetroSeparator())
        
        # Study mode selection
        mode_group = QGroupBox("Study Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_buttons = QButtonGroup(self)
        self.mode_buttons.setExclusive(True)

        # Cram mode
        cram_btn = QRadioButton("Cram - Quick learning with rounds")
        cram_btn.setAutoExclusive(True)
        cram_btn.setChecked(True)
        self.mode_buttons.addButton(cram_btn, 0)
        mode_layout.addWidget(cram_btn)

        # Ingrain mode
        ingrain_btn = QRadioButton("Ingrain - Hybrid short/long-term learning")
        ingrain_btn.setAutoExclusive(True)
        self.mode_buttons.addButton(ingrain_btn, 1)
        mode_layout.addWidget(ingrain_btn)

        # Review mode
        review_btn = QRadioButton("Review - Spaced repetition reviews")
        review_btn.setAutoExclusive(True)
        self.mode_buttons.addButton(review_btn, 2)
        mode_layout.addWidget(review_btn)

        # Free recall mode
        recall_btn = QRadioButton("Free Recall - Memory test without prompts")
        recall_btn.setAutoExclusive(True)
        self.mode_buttons.addButton(recall_btn, 3)
        mode_layout.addWidget(recall_btn)

        # Visual feedback: when selection changes, update dialog title
        self.mode_buttons.buttonClicked.connect(lambda _: self.setWindowTitle(
            f"Study Options — {self.mode_buttons.checkedButton().text().split(' - ')[0]}"))

        layout.addWidget(mode_group)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QGridLayout(options_group)
        
        # Time limit
        options_layout.addWidget(QLabel("Time Limit (minutes):"), 0, 0)
        self.time_limit_spin = QSpinBox()
        self.time_limit_spin.setRange(0, 120)
        self.time_limit_spin.setValue(0)  # 0 = no limit
        self.time_limit_spin.setSpecialValueText("No Limit")
        options_layout.addWidget(self.time_limit_spin, 0, 1)
        
        # Shuffle cards
        self.shuffle_check = QCheckBox("Shuffle Cards")
        self.shuffle_check.setChecked(True)
        options_layout.addWidget(self.shuffle_check, 1, 0, 1, 2)
        
        layout.addWidget(options_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        start_btn = QPushButton("Start Study")
        start_btn.clicked.connect(self.accept)
        button_layout.addWidget(start_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def get_selection(self):
        """Get selected study mode and options."""
        mode_map = {
            0: StudyMode.CRAM,
            1: StudyMode.INGRAIN,
            2: StudyMode.REVIEW,
            3: StudyMode.FREE_RECALL
        }
        
        selected_id = self.mode_buttons.checkedId()
        mode = mode_map.get(selected_id, StudyMode.CRAM)
        
        options = {
            'time_limit': self.time_limit_spin.value() if self.time_limit_spin.value() > 0 else None,
            'shuffle_cards': self.shuffle_check.isChecked()
        }
        
        return mode, options


class StudyWindow(QDialog):
    """Main study window for all study modes (modal dialog with proper window management)."""

    def __init__(self, session, parent=None, test_mode: bool = False):
        super().__init__(parent)
        if not test_mode:
            self.setModal(True)
        self.session = session
        self.parent_window = parent
        self.start_time = None
        self.current_card_start_time = None
        self._test_mode = test_mode

        self.setWindowTitle(f"Study Session — {session.session_type.value.title()}")

        self.setup_ui()
        try:
            self.adjustSize()
        except Exception:
            pass
        # Always use controller (feature flag removed)
        self._controller = StudyController()
        self._css_source2 = _TF_CSS2()
        self.load_current_card()

        # Timer for updating elapsed time (disabled in test mode to avoid offscreen hangs)
        if not self._test_mode:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_timer)
            self.timer.start(1000)  # Update every second
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header with session info
        header_layout = QHBoxLayout()
        
        self.session_label = QLabel(f"Mode: {self.session.session_type.value.title()}")
        self.session_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.session_label)
        
        header_layout.addStretch()
        
        self.progress_label = QLabel("0/0")
        header_layout.addWidget(self.progress_label)
        
        self.timer_label = QLabel("00:00")
        header_layout.addWidget(self.timer_label)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        layout.addWidget(RetroSeparator())
        
        # Card display area
        self.card_area = self.create_card_area()
        layout.addWidget(self.card_area)
        
        layout.addWidget(RetroSeparator())
        
        # Control buttons
        self.button_area = self.create_button_area()
        layout.addWidget(self.button_area)
        
        # Statistics area
        self.stats_area = self.create_stats_area()
        layout.addWidget(self.stats_area)
    
    def create_card_area(self):
        """Create the card display area with enhanced text formatting."""
        group = QGroupBox("Card")
        main_layout = QHBoxLayout(group)

        # Left side: Card content
        card_layout = QVBoxLayout()
        self.card_front = FormattedTextDisplay()
        self.card_front.setStyleSheet("""
            QLabel {
                background: white;
                border: 2px solid #808080;
                border-top-color: #FFFFFF;
                border-left-color: #FFFFFF;
                border-right-color: #808080;
                border-bottom-color: #808080;
                padding: 24px; /* extra padding prevents clipping */
                font-size: 16px;
                min-height: 120px;
            }
        """)
        self.card_front.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        card_layout.addWidget(self.card_front)

        # Right side: Cloze input panel (hidden by default)
        self.cloze_input_panel = self.create_cloze_input_panel()
        self.cloze_input_panel.hide()

        # Add card back to card layout
        self.card_back = FormattedTextDisplay()
        self.card_back.setStyleSheet(self.card_front.styleSheet())
        self.card_back.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.card_back.hide()
        card_layout.addWidget(self.card_back)

        # Flip button in card layout
        self.flip_button = QPushButton("Show Answer")
        self.flip_button.clicked.connect(self.flip_card)
        card_layout.addWidget(self.flip_button)

        main_layout.addLayout(card_layout, 2)  # Card takes 2/3 of space
        main_layout.addWidget(self.cloze_input_panel, 1)  # Panel takes 1/3 of space
        
        return group

    def create_cloze_input_panel(self):
        """Create the side panel for cloze input fields."""
        from app.ui.retro95 import WIN95

        panel = QGroupBox("Fill in the blanks")
        panel.setStyleSheet(f"""
            QGroupBox {{
                background: {WIN95['base']};
                border: 2px solid {WIN95['dk']};
                border-top-color: {WIN95['hl']};
                border-left-color: {WIN95['hl']};
                border-right-color: {WIN95['sh']};
                border-bottom-color: {WIN95['sh']};
                font-family: 'MS Sans Serif', sans-serif;
                font-size: 12px;
                font-weight: bold;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)

        layout = QVBoxLayout(panel)

        # Scroll area for multiple inputs
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {WIN95['dk']};
                background: {WIN95['base']};
            }}
        """)

        self.cloze_input_widget = QWidget()
        self.cloze_input_layout = QVBoxLayout(self.cloze_input_widget)
        scroll.setWidget(self.cloze_input_widget)

        layout.addWidget(scroll)

        # Check Answer button
        self.cloze_check_button = QPushButton("Check Answers")
        self.cloze_check_button.setStyleSheet(f"""
            QPushButton {{
                background: {WIN95['base']};
                border: 2px solid {WIN95['dk']};
                border-top-color: {WIN95['hl']};
                border-left-color: {WIN95['hl']};
                border-right-color: {WIN95['sh']};
                border-bottom-color: {WIN95['sh']};
                padding: 6px 12px;
                font-family: 'MS Sans Serif', sans-serif;
                font-size: 12px;
            }}
            QPushButton:pressed {{
                border-top-color: {WIN95['sh']};
                border-left-color: {WIN95['sh']};
                border-right-color: {WIN95['hl']};
                border-bottom-color: {WIN95['hl']};
            }}
        """)
        self.cloze_check_button.clicked.connect(self._handle_cloze_input_check)
        layout.addWidget(self.cloze_check_button)

        # Store input fields
        self.cloze_input_fields = {}
        self.cloze_update_buttons = {}

        return panel

    def create_button_area(self):
        """Create the control button area."""
        group = QGroupBox("Controls")
        layout = QHBoxLayout(group)
        
        if self.session.session_type == StudyMode.CRAM:
            self.correct_btn = QPushButton("✓ Correct")
            self.correct_btn.clicked.connect(lambda: self.answer_card(True))
            self.correct_btn.setEnabled(False)
            layout.addWidget(self.correct_btn)
            
            self.incorrect_btn = QPushButton("✗ Incorrect")
            self.incorrect_btn.clicked.connect(lambda: self.answer_card(False))
            self.incorrect_btn.setEnabled(False)
            layout.addWidget(self.incorrect_btn)
            
        elif self.session.session_type == StudyMode.INGRAIN:
            self.short_term_btn = QPushButton("Short Term")
            self.short_term_btn.clicked.connect(lambda: self.ingrain_response("short_term"))
            self.short_term_btn.setEnabled(False)
            layout.addWidget(self.short_term_btn)
            
            self.unknown_btn = QPushButton("Unknown")
            self.unknown_btn.clicked.connect(lambda: self.ingrain_response("unknown"))
            self.unknown_btn.setEnabled(False)
            layout.addWidget(self.unknown_btn)
            
            self.good_btn = QPushButton("Good")
            self.good_btn.clicked.connect(lambda: self.ingrain_response("good"))
            self.good_btn.setEnabled(False)
            layout.addWidget(self.good_btn)
            
            self.long_term_btn = QPushButton("Long Term")
            self.long_term_btn.clicked.connect(lambda: self.ingrain_response("long_term"))
            self.long_term_btn.setEnabled(False)
            layout.addWidget(self.long_term_btn)
            
        elif self.session.session_type == StudyMode.REVIEW:
            # SRS grading buttons (0-5)
            self.grade_buttons = []
            grade_labels = ["Fail", "Hard", "Good", "Easy", "Very Easy", "Perfect"]

            # If cloze card, show per-blank buttons
            self.cloze_indices = []
            card = self.session.get_current_card()
            if card and '{{c' in card['front']:
                import re
                self.cloze_indices = sorted(set(int(m.group(1)) for m in re.finditer(r"\{\{c(\d+)::", card['front'])))
                self.cloze_selector = QComboBox()
                for idx in self.cloze_indices:
                    self.cloze_selector.addItem(f"Blank c{idx}", idx)
                layout.addWidget(self.cloze_selector)

            for i, label in enumerate(grade_labels):
                btn = QPushButton(f"{i} - {label}")
                btn.clicked.connect(lambda checked, grade=i: self.grade_card(grade))
                btn.setEnabled(False)
                self.grade_buttons.append(btn)
                layout.addWidget(btn)

        # Common buttons
        layout.addStretch()

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_session)
        layout.addWidget(self.pause_btn)

        self.end_btn = QPushButton("End Session")
        self.end_btn.clicked.connect(self.end_session)
        layout.addWidget(self.end_btn)

        return group
    
    def create_stats_area(self):
        """Create the statistics display area."""
        group = QGroupBox("Session Statistics")
        layout = QGridLayout(group)
        
        self.cards_studied_label = QLabel("Cards Studied: 0")
        self.correct_count_label = QLabel("Correct: 0")
        self.accuracy_label = QLabel("Accuracy: 0%")
        self.avg_time_label = QLabel("Avg Time: 0s")
        
        layout.addWidget(self.cards_studied_label, 0, 0)
        layout.addWidget(self.correct_count_label, 0, 1)
        layout.addWidget(self.accuracy_label, 1, 0)
        layout.addWidget(self.avg_time_label, 1, 1)
        
        return group
    
    def load_current_card(self):
        """Load and display the current card."""
        card = self.session.get_current_card()
        if not card:
            self.show_session_complete()
            return
        
        # Update progress
        total_cards = len(self.session.cards)
        current_index = self.session.current_card_index + 1
        self.progress_label.setText(f"{current_index}/{total_cards}")
        self.progress_bar.setMaximum(total_cards)
        self.progress_bar.setValue(current_index)
        
        # Display card content with enhanced formatting and syntax highlighting
        front_text = card['front']
        back_text = card['back']
        template = card.get('template_data') or {}
        inline_css = (template.get('inline_css') or '').strip()

        # Store card info for flip logic
        self.current_card_text = front_text
        self.current_inline_css = inline_css

        # Determine card type via factory
        ct = card_type_factory.get_card_type(front_text)
        self.is_cloze_card = ct.is_single_sided() and "{{c" in front_text and "{{cin" not in front_text
        self.is_cloze_input_card = "{{cin" in front_text

        # Always use controller path (legacy removed)
        try:
            if self.is_cloze_input_card:
                # Special handling for cloze input cards with side panel
                self.card_back.hide()

                # Initialize cloze input state
                self.cloze_input_attempts = 0
                config = get_config()
                self.cloze_input_max_attempts = config.get('study', {}).get('cloze_input_attempts', 3)
                self.cloze_input_case_sensitive = config.get('study', {}).get('cloze_input_case_sensitive', False)
                self.cloze_input_answers = self._extract_cloze_input_answers(front_text)

                # Use regular display with placeholders
                vs = self._controller.render_front(front_text, inline_css=inline_css)
                css = self._css_source2.get_default_code_css()
                self.card_front.setText(f"<style>{css}</style><div>{vs.html}</div>")

                # Setup side panel
                self._setup_cloze_input_panel()
                self.cloze_input_panel.show()

                # Change button text for cloze input
                self.flip_button.setText("Show Answer")
            elif self.is_cloze_card:
                vs = self._controller.render_front(front_text, inline_css=inline_css)
                css = self._css_source2.get_default_code_css()
                self.card_back.hide()
                self.card_front.setText(f"<style>{css}</style><div>{vs.html}</div>")
                # Reset flip button
                self.flip_button.setText("Show Answer")
            else:
                vs = self._controller.render_front(front_text, inline_css=inline_css)
                css = self._css_source2.get_default_code_css()
                self.card_front.setText(f"<style>{css}</style><div>{vs.html}</div>")
                # Prepare back content as before
                self.card_back.setFormattedText(back_text, apply_syntax_highlighting=True, extra_inline_css=inline_css)
                self.card_back.hide()
                # Reset flip button
                self.flip_button.setText("Show Answer")

                # Hide cloze input panel for non-cloze input cards
                if hasattr(self, 'cloze_input_panel'):
                    self.cloze_input_panel.hide()
        except Exception as e:
            # Log and present a safe fallback instead of crashing
            from pathlib import Path as _P
            import traceback as _tb
            logs_dir = _P(__file__).resolve().parents[3] / 'plus_ultra_cards' / 'data' / 'logs'
            try:
                logs_dir.mkdir(parents=True, exist_ok=True)
                with open(logs_dir / 'study.log', 'a', encoding='utf-8') as fh:
                    fh.write("\n=== Render error ===\n")
                    fh.write(f"Card ID: {card.get('id')}\n")
                    fh.write(f"Error: {e}\n")
                    fh.write(_tb.format_exc())
                    fh.write("\nFront snippet:\n")
                    fh.write(front_text[:500])
                    fh.write("\n====================\n")
            except Exception:
                pass
            # User-facing safe message (non-blocking)
            safe_html = (
                "<div style='padding:8px;border:2px inset #808080;background:#FFFFE1;'>"
                "<b>Render error:</b> The content of this card could not be fully displayed. "
                "You can continue the session; details were logged to study.log."
                "</div>"
            )
            self.card_front.setText(safe_html)
            if hasattr(self, 'cloze_input_panel'):
                self.cloze_input_panel.hide()
            self.card_back.hide()
            self.flip_button.setText("Show Answer")

        self.flip_button.setEnabled(True)

        # Disable answer buttons until card is flipped
        self.disable_answer_buttons()

        # Start timing for this card
        self.current_card_start_time = time.time()

    def _extract_cloze_input_answers(self, text: str) -> dict:
        """Extract answers from cloze input format {{cin1::answer}}."""
        import re
        answers = {}
        # Use tolerant DOTALL pattern to capture multi-line cloze input blocks
        pattern = r'\{\{cin(\d+)::([\s\S]*?)\}\}(?!\})'
        for match in re.finditer(pattern, text, flags=re.DOTALL):
            cloze_num = match.group(1)
            answer = match.group(2).strip()
            answers[cloze_num] = answer
        return answers

    def _setup_cloze_input_panel(self):
        """Setup the cloze input panel with fields for each cloze deletion."""
        from app.ui.retro95 import WIN95

        # Clear existing fields
        for widget in self.cloze_input_fields.values():
            widget.deleteLater()
        for widget in self.cloze_update_buttons.values():
            widget.deleteLater()
        self.cloze_input_fields.clear()
        self.cloze_update_buttons.clear()

        # Clear layout
        while self.cloze_input_layout.count():
            child = self.cloze_input_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Create input fields for each cloze deletion
        for cloze_num in sorted(self.cloze_input_answers.keys(), key=int):
            # Container for this input
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(5, 5, 5, 5)

            # Label
            label = QLabel(f"C{cloze_num}: Enter response")
            label.setStyleSheet(f"""
                QLabel {{
                    font-family: 'MS Sans Serif', sans-serif;
                    font-size: 11px;
                    color: {WIN95['text']};
                    margin-bottom: 3px;
                }}
            """)
            container_layout.addWidget(label)

            # Input field
            input_field = QLineEdit()
            input_field.setStyleSheet(f"""
                QLineEdit {{
                    background: {WIN95['base']};
                    border: 2px solid {WIN95['dk']};
                    border-top-color: {WIN95['sh']};
                    border-left-color: {WIN95['sh']};
                    border-right-color: {WIN95['hl']};
                    border-bottom-color: {WIN95['hl']};
                    padding: 4px;
                    font-family: 'MS Sans Serif', sans-serif;
                    font-size: 11px;
                    selection-background-color: {WIN95['sel_bg']};
                    selection-color: {WIN95['sel_text']};
                }}
                QLineEdit:focus {{
                    border: 2px solid {WIN95['sel_bg']};
                }}
            """)
            input_field.setPlaceholderText("Type your answer...")
            container_layout.addWidget(input_field)

            # Update button
            update_btn = QPushButton("Update Display")
            update_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {WIN95['base']};
                    border: 2px solid {WIN95['dk']};
                    border-top-color: {WIN95['hl']};
                    border-left-color: {WIN95['hl']};
                    border-right-color: {WIN95['sh']};
                    border-bottom-color: {WIN95['sh']};
                    padding: 3px 8px;
                    font-family: 'MS Sans Serif', sans-serif;
                    font-size: 10px;
                }}
                QPushButton:pressed {{
                    border-top-color: {WIN95['sh']};
                    border-left-color: {WIN95['sh']};
                    border-right-color: {WIN95['hl']};
                    border-bottom-color: {WIN95['hl']};
                }}
            """)
            update_btn.clicked.connect(lambda checked, num=cloze_num: self._update_display_for_cloze(num))
            container_layout.addWidget(update_btn)

            # Store references
            self.cloze_input_fields[cloze_num] = input_field
            self.cloze_update_buttons[cloze_num] = update_btn

            # Add to layout
            self.cloze_input_layout.addWidget(container)

        # Add stretch to push everything to top
        self.cloze_input_layout.addStretch()

    def _update_display_for_cloze(self, cloze_num: str):
        """Update the card display to show user input for a specific cloze."""
        if cloze_num not in self.cloze_input_fields:
            return

        user_input = self.cloze_input_fields[cloze_num].text().strip()

        # Get current card text
        current_card = self.session.get_current_card()
        if not current_card:
            return

        front_text = current_card['front']

        # Replace the specific cloze with user input
        import re
        pattern = f'\\{{{{cin{cloze_num}::([^}}]+)\\}}}}'

        if user_input:
            # Show user input in place of placeholder
            replacement = f'<span style="background-color: #e6f3ff; border: 1px solid #0066cc; padding: 2px 4px; border-radius: 3px;">{user_input}</span>'
        else:
            # Show placeholder
            replacement = f'<span style="background-color: #f0f0f0; border: 1px dashed #999; padding: 2px 8px; text-align: center;">[ _____ ]</span>'

        updated_text = re.sub(pattern, replacement, front_text)

        # Render and display
        inline_css = self.current_inline_css or ""
        vs = self._controller.render_front(updated_text, inline_css=inline_css)
        css = self._css_source2.get_default_code_css()
        self.card_front.setText(f"<style>{css}</style><div>{vs.html}</div>")

    def _handle_cloze_input_check(self):
        """Handle checking answers for cloze input cards using side panel input."""
        # Check the answers
        self.cloze_input_attempts += 1

        # Get user inputs from side panel
        user_answers = {}
        for cloze_num, input_field in self.cloze_input_fields.items():
            user_answers[cloze_num] = input_field.text().strip()

        # Validate answers
        correct_count = 0
        total_count = len(self.cloze_input_answers)
        incorrect_cloze_numbers = []

        for cloze_num, correct_answer in self.cloze_input_answers.items():
            user_answer = user_answers.get(cloze_num, "").strip()
            correct_answer = correct_answer.strip()

            # Compare answers based on case sensitivity setting
            if self.cloze_input_case_sensitive:
                is_correct = user_answer == correct_answer
            else:
                is_correct = user_answer.lower() == correct_answer.lower()

            if is_correct:
                correct_count += 1
                # Style input field as correct
                self._style_cloze_input_field(cloze_num, True)
            else:
                # Style input field as incorrect and track for clearing
                self._style_cloze_input_field(cloze_num, False)
                incorrect_cloze_numbers.append(cloze_num)

        # Handle feedback based on correctness
        if correct_count == total_count:
            # All correct
            self._show_cloze_input_feedback("Correct! All answers are right.", "success")
            self.flip_button.setText("Show Answer")
            self.enable_answer_buttons()
        elif correct_count > 0:
            # Partially correct
            remaining_attempts = self.cloze_input_max_attempts - self.cloze_input_attempts
            if remaining_attempts > 0:
                self._show_cloze_input_feedback(
                    f"Partially correct ({correct_count}/{total_count}). {remaining_attempts} attempts remaining.",
                    "partial"
                )
                # Clear incorrect fields for retry
                for cloze_num in incorrect_cloze_numbers:
                    if cloze_num in self.cloze_input_fields:
                        self.cloze_input_fields[cloze_num].clear()
            else:
                self._show_cloze_input_feedback("Maximum attempts reached. Showing answers.", "failed")
                self._show_final_cloze_answers()
                self.flip_button.setText("Show Answer")
                self.enable_answer_buttons()
        else:
            # All incorrect
            remaining_attempts = self.cloze_input_max_attempts - self.cloze_input_attempts
            if remaining_attempts > 0:
                self._show_cloze_input_feedback(f"Incorrect. {remaining_attempts} attempts remaining.", "incorrect")
                # Clear all fields for retry
                for input_field in self.cloze_input_fields.values():
                    input_field.clear()
                # Reset styling for next attempt
                self._reset_cloze_input_styling()
            else:
                self._show_cloze_input_feedback("Maximum attempts reached. Showing answers.", "failed")
                self._show_final_cloze_answers()
                self.flip_button.setText("Show Answer")
                self.enable_answer_buttons()

    def _style_cloze_input_field(self, cloze_num: str, is_correct: bool):
        """Apply correct/incorrect styling to a cloze input field."""
        if cloze_num not in self.cloze_input_fields:
            return

        from app.ui.retro95 import WIN95
        input_field = self.cloze_input_fields[cloze_num]

        if is_correct:
            input_field.setStyleSheet(f"""
                QLineEdit {{
                    background-color: #d4edda;
                    border: 2px solid #28a745;
                    font-family: 'MS Sans Serif', sans-serif;
                    font-size: 11px;
                    padding: 4px;
                }}
            """)
        else:
            input_field.setStyleSheet(f"""
                QLineEdit {{
                    background-color: #f8d7da;
                    border: 2px solid #dc3545;
                    font-family: 'MS Sans Serif', sans-serif;
                    font-size: 11px;
                    padding: 4px;
                }}
            """)

    def _reset_cloze_input_styling(self):
        """Reset all cloze input fields to default styling."""
        from app.ui.retro95 import WIN95

        for input_field in self.cloze_input_fields.values():
            input_field.setStyleSheet(f"""
                QLineEdit {{
                    background: {WIN95['base']};
                    border: 2px solid {WIN95['dk']};
                    border-top-color: {WIN95['sh']};
                    border-left-color: {WIN95['sh']};
                    border-right-color: {WIN95['hl']};
                    border-bottom-color: {WIN95['hl']};
                    padding: 4px;
                    font-family: 'MS Sans Serif', sans-serif;
                    font-size: 11px;
                    selection-background-color: {WIN95['sel_bg']};
                    selection-color: {WIN95['sel_text']};
                }}
                QLineEdit:focus {{
                    border: 2px solid {WIN95['sel_bg']};
                }}
            """)

    def _show_final_cloze_answers(self):
        """Show the correct answers in the card display after max attempts."""
        current_card = self.session.get_current_card()
        if not current_card:
            return

        front_text = current_card['front']

        # Use FormatterService's robust revealed rendering instead of manual regex replacement
        from app.formatting.formatter_service import FormatterService
        formatter = FormatterService()
        revealed_html = formatter.render_cloze_input_revealed(
            front_text, apply_syntax_highlighting=True
        )

        # Apply CSS and display the revealed content
        css = self._css_source2.get_default_code_css()
        self.card_front.setText(f"<style>{css}</style><div>{revealed_html}</div>")

        # Disable all input fields to prevent further editing
        for field in self.cloze_input_fields.values():
            field.setEnabled(False)
            field.setStyleSheet("background-color: #f0f0f0; color: #666666;")

    def _show_cloze_input_feedback(self, message: str, feedback_type: str):
        """Show feedback for cloze input attempts."""
        # For now, we'll use a simple message box
        # In a full implementation, this would show inline feedback

        if feedback_type == "success":
            QMessageBox.information(self, "Correct!", message)
        elif feedback_type == "partial":
            QMessageBox.warning(self, "Partially Correct", message)
        elif feedback_type == "incorrect":
            QMessageBox.warning(self, "Incorrect", message)
        elif feedback_type == "failed":
            QMessageBox.critical(self, "Maximum Attempts", message)

    def _show_cloze_input_answers(self):
        """Show the correct answers for cloze input card."""
        vs = self._controller.render_answer(self.current_card_text, inline_css=self.current_inline_css)
        css = self._css_source2.get_default_code_css()
        self.card_front.setText(f"<style>{css}</style><div>{vs.html}</div>")

    def flip_card(self):
        """Flip the card to show the answer."""
        if hasattr(self, 'is_cloze_input_card') and self.is_cloze_input_card:
            # Handle cloze input card interaction
            self._handle_cloze_input_check()
        elif hasattr(self, 'is_cloze_card') and self.is_cloze_card:
            # Controller-driven toggle (legacy removed)
            if self.flip_button.text() == "Show Answer":
                vs = self._controller.render_answer(self.current_card_text, inline_css=self.current_inline_css)
                css = self._css_source2.get_default_code_css()
                self.card_front.setText(f"<style>{css}</style><div>{vs.html}</div>")
                self.flip_button.setText("Hide Answer")
                self.enable_answer_buttons()
            else:
                vs = self._controller.render_front(self.current_card_text, inline_css=self.current_inline_css)
                css = self._css_source2.get_default_code_css()
                self.card_front.setText(f"<style>{css}</style><div>{vs.html}</div>")
                self.flip_button.setText("Show Answer")
                self.disable_answer_buttons()
        else:
            # Regular front/back card: use existing logic
            if self.card_back.isVisible():
                self.card_back.hide()
                self.flip_button.setText("Show Answer")
                self.disable_answer_buttons()
            else:
                self.card_back.show()
                self.flip_button.setText("Hide Answer")
                self.enable_answer_buttons()
    
    def disable_answer_buttons(self):
        """Disable all answer buttons."""
        if hasattr(self, 'correct_btn'):
            self.correct_btn.setEnabled(False)
            self.incorrect_btn.setEnabled(False)
        elif hasattr(self, 'short_term_btn'):
            self.short_term_btn.setEnabled(False)
            self.unknown_btn.setEnabled(False)
            self.good_btn.setEnabled(False)
            self.long_term_btn.setEnabled(False)
        elif hasattr(self, 'grade_buttons'):
            for btn in self.grade_buttons:
                btn.setEnabled(False)
    
    def enable_answer_buttons(self):
        """Enable all answer buttons."""
        if hasattr(self, 'correct_btn'):
            self.correct_btn.setEnabled(True)
            self.incorrect_btn.setEnabled(True)
        elif hasattr(self, 'short_term_btn'):
            self.short_term_btn.setEnabled(True)
            self.unknown_btn.setEnabled(True)
            self.good_btn.setEnabled(True)
            self.long_term_btn.setEnabled(True)
        elif hasattr(self, 'grade_buttons'):
            for btn in self.grade_buttons:
                btn.setEnabled(True)
    
    def answer_card(self, correct):
        """Handle cram mode card answer."""
        response_time = time.time() - self.current_card_start_time if self.current_card_start_time else 0
        result = self.session.answer_card(correct, response_time)
        
        self.update_statistics()
        
        if result['status'] == 'continue':
            self.load_current_card()
        elif result['status'] == 'round_complete':
            self.show_round_complete(result)
        elif result['status'] == 'session_complete':
            self.show_session_complete(result)
    
    def ingrain_response(self, response):
        """Handle ingrain mode response."""
        response_time = time.time() - self.current_card_start_time if self.current_card_start_time else 0
        result = self.session.answer_card(response, response_time)
        
        self.update_statistics()
        
        if result['status'] == 'continue':
            self.load_current_card()
        elif result['status'] == 'phase_transition':
            self.show_phase_transition(result)
        elif result['status'] == 'session_complete':
            self.show_session_complete(result)
    
    def grade_card(self, grade):
        """Handle review mode card grading."""
        response_time = time.time() - self.current_card_start_time if self.current_card_start_time else 0

        # If cloze, let user choose which blank is being graded
        cloze_index = None
        if hasattr(self, 'cloze_selector') and self.cloze_selector.count() > 0:
            cloze_index = int(self.cloze_selector.currentData())

        result = self.session.grade_card(grade, response_time, cloze_index=cloze_index)

        self.update_statistics()

        if result['status'] == 'continue':
            self.load_current_card()
        elif result['status'] == 'session_complete':
            self.show_session_complete(result)
    
    def show_round_complete(self, result):
        """Show round completion dialog for cram mode."""
        stats = result['round_stats']
        message = (f"Round {stats['round']} Complete!\n\n"
                  f"Cards studied: {stats['total_cards']}\n"
                  f"Correct: {stats['correct']}\n"
                  f"Incorrect: {stats['incorrect']}\n"
                  f"Accuracy: {stats['accuracy']:.1f}%\n\n"
                  f"Next round will have {result['next_round_cards']} cards.")
        
        if getattr(self, '_test_mode', False):
            # In test mode, avoid modal dialogs; auto-advance to next round
            self._last_dialog_message = ("round_complete", message)
            self.session.start_next_round()
            self.load_current_card()
            return

        reply = QMessageBox.question(self, "Round Complete",
                                   message + "\n\nStart next round?",
                                   QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.session.start_next_round()
            self.load_current_card()
        else:
            self.end_session()
    
    def show_phase_transition(self, result):
        """Show phase transition for ingrain mode."""
        message = (f"Cram phase complete!\n\n"
                  f"Starting {result['new_phase']} phase with {result['cards_count']} cards.")
        
        QMessageBox.information(self, "Phase Transition", message)
        self.load_current_card()
    
    def show_session_complete(self, result=None):
        """Show session completion dialog."""
        stats = self.session.statistics
        message = (f"Session Complete!\n\n"
                  f"Total cards: {stats['total_cards']}\n"
                  f"Correct: {stats['correct_cards']}\n"
                  f"Incorrect: {stats['incorrect_cards']}\n")
        
        if stats['total_cards'] > 0:
            accuracy = (stats['correct_cards'] / stats['total_cards']) * 100
            message += f"Accuracy: {accuracy:.1f}%\n"
        
        if stats['total_time'] > 0:
            minutes = int(stats['total_time'] // 60)
            seconds = int(stats['total_time'] % 60)
            message += f"Total time: {minutes}:{seconds:02d}"
        
        if getattr(self, '_test_mode', False):
            # Avoid modal dialog in tests, record and close
            self._last_dialog_message = ("session_complete", message)
            self.close()
            return
        QMessageBox.information(self, "Session Complete", message)
        self.close()
    
    def update_statistics(self):
        """Update the statistics display."""
        stats = self.session.statistics
        
        cards_studied = stats['correct_cards'] + stats['incorrect_cards']
        self.cards_studied_label.setText(f"Cards Studied: {cards_studied}")
        self.correct_count_label.setText(f"Correct: {stats['correct_cards']}")
        
        if cards_studied > 0:
            accuracy = (stats['correct_cards'] / cards_studied) * 100
            self.accuracy_label.setText(f"Accuracy: {accuracy:.1f}%")
        
        if stats.get('total_time', 0) > 0 and cards_studied > 0:
            avg_time = stats['total_time'] / cards_studied
            self.avg_time_label.setText(f"Avg Time: {avg_time:.1f}s")
    
    def update_timer(self):
        """Update the elapsed time display."""
        if self.session.start_time:
            elapsed = time.time() - self.session.start_time.timestamp()
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
    
    def pause_session(self):
        """Pause/resume the session."""
        if self.session.state == SessionState.IN_PROGRESS:
            self.session.state = SessionState.PAUSED
            self.pause_btn.setText("Resume")
            self.timer.stop()
        else:
            self.session.state = SessionState.IN_PROGRESS
            self.pause_btn.setText("Pause")
            self.timer.start()
    
    def end_session(self):
        """End the session."""
        reply = QMessageBox.question(self, "End Session", 
                                   "Are you sure you want to end this session?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.session.end_session()
            self.close()
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key_Space or event.key() == Qt.Key_Return:
            if self.flip_button.isEnabled():
                self.flip_card()
        elif event.key() == Qt.Key_Escape:
            self.end_session()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle window close."""
        if self.session.state == SessionState.IN_PROGRESS:
            reply = QMessageBox.question(self, "Close Session", 
                                       "Session is still in progress. End session?",
                                       QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.session.end_session()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
