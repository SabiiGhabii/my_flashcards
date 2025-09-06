"""
Card Editor Dialog
Supports creating and editing Basic (Front/Back) and Cloze cards.
Adds a live preview for cloze rendering and template system.
Enhanced with code formatting and syntax highlighting support.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QGroupBox, QMessageBox, QListWidget,
    QListWidgetItem, QCheckBox, QSplitter, QInputDialog, QTabWidget, QScrollArea, QWidget, QMenu
)

from app.ui.retro95 import RetroSeparator
from app.core.utils import validate_card_content
from app.core.card_templates import CardTemplateManager
from app.ui.enhanced_text_widgets import CodeEditorWidget, FormattedTextDisplay, CodeAwareTextEdit
from app.ui.gui.widgets.scroll_label import ScrollableLabel

import re

class CardEditorDialog(QDialog):
    """Dialog for creating/editing cards with type selection."""

    def __init__(self, card_manager, deck_id, card=None, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.card_manager = card_manager
        self.deck_id = deck_id
        self.card = card  # existing card dict or None
        self.template_manager = CardTemplateManager()
        self.setWindowTitle("Card Editor")
        self.resize(900, 700)

        # Ensure Win95 font is loaded + substitution for legacy names in dialogs
        try:
            from PySide6.QtGui import QFontDatabase, QFont
            from pathlib import Path
            otf_path = Path(__file__).resolve().parents[2] / "assets" / "fonts" / "W95font.otf"
            if otf_path.exists():
                fid = QFontDatabase.addApplicationFont(str(otf_path))
                if fid != -1:
                    fams = QFontDatabase.applicationFontFamilies(fid)
                    if fams:
                        fam = fams[0]
                        self.setFont(QFont(fam, 9))
                        # Substitutions so CSS requests resolve
                        QFont.insertSubstitution("MS Sans Serif", fam)
                        QFont.insertSubstitution("Microsoft Sans Serif", fam)
                        QFont.insertSubstitution("Fixedsys", "Courier New")
        except Exception:
            pass

        self.setup_ui()
        if card:
            self.populate_from_card(card)

    def setup_ui(self):
        # Root layout wraps a scroll area to allow access to all controls on smaller screens
        root_layout = QVBoxLayout(self)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Container widget inside the scroll area
        container = QWidget()
        layout = QVBoxLayout(container)

        # Card type selector
        type_group = QGroupBox("Card Type")
        type_layout = QHBoxLayout(type_group)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Front/Back", "Cloze Deletion"])
        self.type_combo.currentIndexChanged.connect(self.update_type_visibility)
        type_layout.addWidget(QLabel("Type:"))
        type_layout.addWidget(self.type_combo)
        layout.addWidget(type_group)

        layout.addWidget(RetroSeparator())

        # Front/Back editors with enhanced text support
        self.basic_group = QGroupBox("Front / Back")
        basic_layout = QGridLayout(self.basic_group)

        # Front editor with code support
        basic_layout.addWidget(QLabel("Front:"), 0, 0)
        self.front_edit = CodeEditorWidget()
        basic_layout.addWidget(self.front_edit, 1, 0)

        # Back editor with code support
        basic_layout.addWidget(QLabel("Back:"), 2, 0)
        self.back_edit = CodeEditorWidget()
        basic_layout.addWidget(self.back_edit, 3, 0)

        layout.addWidget(self.basic_group)

        # Cloze editor with enhanced features
        self.cloze_group = QGroupBox("Cloze Content")
        cloze_layout = QVBoxLayout(self.cloze_group)

        # Enhanced cloze editor with code support
        cloze_layout.addWidget(QLabel("Use {{c1::...}} syntax and code blocks. Use the buttons above for quick insertion."))

        # Functional buttons should appear ABOVE the input box
        toolbar = QHBoxLayout()
        self.add_c1_btn = QPushButton("Add {{c1}}")
        self.add_c1_btn.clicked.connect(lambda: self.wrap_selection_with_cloze(1))
        self.add_c2_btn = QPushButton("Add {{c2}}")
        self.add_c2_btn.clicked.connect(lambda: self.wrap_selection_with_cloze(2))
        self.add_c3_btn = QPushButton("Add {{c3}}")
        self.add_c3_btn.clicked.connect(lambda: self.wrap_selection_with_cloze(3))
        self.add_c4_btn = QPushButton("Add {{c4}}")
        self.add_c4_btn.clicked.connect(lambda: self.wrap_selection_with_cloze(4))
        self.add_c5_btn = QPushButton("Add {{c5}}")
        self.add_c5_btn.clicked.connect(lambda: self.wrap_selection_with_cloze(5))
        toolbar.addWidget(self.add_c1_btn)
        toolbar.addWidget(self.add_c2_btn)
        toolbar.addWidget(self.add_c3_btn)
        toolbar.addWidget(self.add_c4_btn)
        toolbar.addWidget(self.add_c5_btn)

        # Global Code Block button (acts on cloze editor to match cloze buttons UX)
        self.code_block_btn = QPushButton("Code Block ▾")
        self.code_block_menu = self._build_code_block_menu()
        self.code_block_btn.setMenu(self.code_block_menu)
        toolbar.addWidget(self.code_block_btn)

        toolbar.addStretch()
        cloze_layout.addLayout(toolbar)

        # Now add the editor below the buttons
        self.cloze_edit = CodeEditorWidget()
        cloze_layout.addWidget(self.cloze_edit)

        # Live preview area with enhanced formatting
        preview_group = QGroupBox("Live Preview")
        prev_layout = QVBoxLayout(preview_group)
        # Wrap preview in scrollable container
        self.preview_label = FormattedTextDisplay()
        scroll_preview = QScrollArea()
        scroll_preview.setWidgetResizable(True)
        scroll_preview.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_preview.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_preview.setFrameShape(QScrollArea.NoFrame)
        scroll_preview.setWidget(self.preview_label)
        prev_layout.addWidget(scroll_preview)
        cloze_layout.addWidget(preview_group)
        layout.addWidget(self.cloze_group)

        # Update preview as user types
        # Updated to use CodeEditorWidget's signal
        self.cloze_edit.contentChanged.connect(self.update_preview)

        # Styling section (simplified - Basic template only)
        template_group = QGroupBox("Card Styling")
        template_layout = QGridLayout(template_group)

        # Info label
        info_label = QLabel("Using Basic template with W95font. Code highlighting is automatic.")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        template_layout.addWidget(info_label, 0, 0, 1, 2)

        # Rich text option (always enabled for Basic template)
        self.rich_check = QCheckBox("Render as Rich Text (HTML)")
        self.rich_check.setChecked(True)  # Default to enabled
        self.rich_check.setEnabled(False)  # Disabled since we always use rich text
        template_layout.addWidget(self.rich_check, 1, 0, 1, 2)

        # Custom CSS (optional override)
        template_layout.addWidget(QLabel("Custom CSS (optional):"), 2, 0)
        self.style_edit = QTextEdit()
        self.style_edit.setMaximumHeight(80)
        self.style_edit.setPlaceholderText("Optional custom CSS to override default styling...")
        template_layout.addWidget(self.style_edit, 3, 0, 1, 2)

        layout.addWidget(template_group)

        # Tags and hint
        meta_group = QGroupBox("Metadata")
        meta_layout = QGridLayout(meta_group)
        self.tags_input = QLineEdit()
        self.hint_input = QLineEdit()
        meta_layout.addWidget(QLabel("Tags (comma-separated):"), 0, 0)
        meta_layout.addWidget(self.tags_input, 0, 1)
        meta_layout.addWidget(QLabel("Hint (optional):"), 1, 0)
        meta_layout.addWidget(self.hint_input, 1, 1)
        layout.addWidget(meta_group)

        layout.addWidget(RetroSeparator())

        # Buttons
        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_card)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_card)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(delete_btn)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        # Finalize scroll area
        scroll.setWidget(container)
        root_layout.addWidget(scroll)

        self.update_type_visibility()
        self.update_preview()

        # Connect signals for live preview updates
        self.cloze_edit.contentChanged.connect(self.update_preview)
        self.rich_check.toggled.connect(self.update_preview)
        self.style_edit.textChanged.connect(self.update_preview)

    def get_default_template_css(self):
        """Get the default Basic template CSS."""
        basic_template = self.template_manager.get_template("Basic")
        if basic_template:
            return basic_template.get('css', '')
        return "font-family: 'W95font', 'Microsoft Sans Serif', sans-serif; font-size: 14px; line-height: 1.4; padding: 8px;"

    def update_preview(self):
        text = self.cloze_edit.toPlainText()

        # Use Basic template CSS with optional custom CSS override
        inline_css = self.style_edit.toPlainText().strip()
        if not inline_css:
            inline_css = self.get_default_template_css()

        # Use the enhanced formatter for preview with cloze blanking
        # Code highlighting is automatic - no need for special template
        self.preview_label.setFormattedTextWithCloze(text, show_blanks=True, apply_syntax_highlighting=True, extra_inline_css=inline_css)

    def update_type_visibility(self):
        is_cloze = self.type_combo.currentIndex() == 1
        self.basic_group.setVisible(not is_cloze)
        self.cloze_group.setVisible(is_cloze)
        if is_cloze:
            self.setWindowTitle("Card Editor — Cloze Deletion")
        else:
            self.setWindowTitle("Card Editor — Front/Back")

    def wrap_selection_with_cloze(self, idx: int):
        # Get the editor from the CodeEditorWidget
        editor = self.cloze_edit.editor
        cursor = editor.textCursor()
        selected = cursor.selectedText()
        if not selected:
            cursor.insertText(f"{{{{c{idx}::text}}}}")
        else:
            cursor.insertText(f"{{{{c{idx}::{selected}}}}}")
        editor.setTextCursor(cursor)
        self.update_preview()

    def populate_from_card(self, card):
        content = card.get('front', '')
        if '{{c' in content:
            self.type_combo.setCurrentIndex(1)
            self.cloze_edit.setPlainText(content)
        else:
            self.type_combo.setCurrentIndex(0)
            self.front_edit.setPlainText(card.get('front', ''))
            self.back_edit.setPlainText(card.get('back', ''))

        if card.get('tags'):
            self.tags_input.setText(','.join(card['tags']))
        if card.get('hint'):
            self.hint_input.setText(card['hint'])

        # Load template data (always use Basic template)
        template_data = card.get('template_data', {})
        self.rich_check.setChecked(template_data.get('rich', True))  # Default to True
        self.style_edit.setPlainText(template_data.get('inline_css', ''))

        # No need to set template since we only have Basic template
        self.update_preview()

    def save_card(self):
        is_cloze = self.type_combo.currentIndex() == 1
        if is_cloze:
            front = self.cloze_edit.toPlainText()
            back = ""
        else:
            front = self.front_edit.toPlainText()
            back = self.back_edit.toPlainText()

        ok, err = validate_card_content(front, back if not is_cloze else "x")
        if not ok:
            QMessageBox.warning(self, "Validation Error", err)
            return

        tags = [t.strip() for t in self.tags_input.text().split(',') if t.strip()]
        template_data = {
            'rich': self.rich_check.isChecked(),
            'inline_css': self.style_edit.toPlainText().strip(),
            'template_name': 'Basic'  # Always use Basic template
        }
        kwargs = { 'tags': tags, 'hint': self.hint_input.text().strip(), 'template_data': template_data }

        if self.card:
            self.card_manager.update_card(self.card['id'], front=front, back=back, **kwargs)
        else:
            self.card_manager.create_card(self.deck_id, front, back, **kwargs)

        self.accept()

    def delete_card(self):
        if not self.card:
            self.reject()
            return
        reply = QMessageBox.question(self, "Delete Card", "Delete this card?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.card_manager.delete_card(self.card['id'])
            self.accept()

    def _build_code_block_menu(self):
        """Build the code block menu for the global button."""
        menu = QMenu(self)
        for label, lang in [
            ("Python", "python"),
            ("C++", "cpp"),
            ("Rust", "rust"),
            ("R", "r"),
            ("JavaScript", "javascript"),
            ("Java", "java"),
            ("Bash", "bash"),
            ("SQL", "sql"),
            ("HTML", "html"),
            ("CSS", "css"),
            ("Generic", "")
        ]:
            act = menu.addAction(label)
            act.triggered.connect(lambda checked, l=lang: self._insert_code_block_global(l))
        return menu

    def _insert_code_block_global(self, language: str):
        """Insert code block into the cloze editor (mirrors cloze button UX)."""
        editor = self.cloze_edit.editor
        if not editor.hasFocus():
            editor.setFocus()
        cursor = editor.textCursor()
        start = f"{{start.style::code[{language}]}}\n" if language else "{start.style::code}\n"
        end = "\n{end.style}"
        cursor.insertText(start + "// Your code here" + end)
        # Move cursor inside the block
        cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.MoveAnchor, len(end) + len("// Your code here"))
        editor.setTextCursor(cursor)
        editor.ensureCursorVisible()
        self.update_preview()

