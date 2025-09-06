"""
Enhanced Text Widgets for Plus Ultra Cards
Provides text editing and display widgets with code formatting support.
"""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor, QKeySequence, QAction, QTextOption
from PySide6.QtWidgets import (
    QTextEdit, QLabel, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QToolBar, QMenu, QMessageBox
)

from app.formatting.formatter_service import FormatterService, RenderingOptions
from app.formatting.text_formatter import TextFormatter as _TF_CSS
from app.ui.font_loader import load_win95_font


class CodeAwareTextEdit(QTextEdit):
    """
    Enhanced QTextEdit that preserves indentation and supports code formatting.
    """

    # Signal emitted when content changes (for live preview)
    contentChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)  # Force plain text mode
        self.setTabStopDistance(40)    # Set tab width to 4 characters

        # Enable word wrap but preserve formatting
        self.setWordWrapMode(QTextOption.WordWrap)

        # Use monospace font for better code editing
        font = QFont("Courier New", 10)
        font.setFixedPitch(True)
        self.setFont(font)

        # Connect signals
        self.textChanged.connect(self._on_text_changed)

        # Timer for delayed content change signal (debouncing)
        self._change_timer = QTimer()
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self.contentChanged.emit)

    def _on_text_changed(self):
        """Handle text changes with debouncing."""
        self._change_timer.start(300)  # 300ms delay

    def keyPressEvent(self, event):
        """Handle key press events for better code editing."""
        if event.key() == Qt.Key_Tab:
            # Insert 4 spaces instead of tab
            cursor = self.textCursor()
            cursor.insertText("    ")
            return
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Auto-indent on new line
            cursor = self.textCursor()

            # Get current line
            cursor.select(QTextCursor.LineUnderCursor)
            current_line = cursor.selectedText()

            # Count leading whitespace
            indent = 0
            for char in current_line:
                if char == ' ':
                    indent += 1
                elif char == '\t':
                    indent += 4
                else:
                    break

            # Insert newline and matching indentation
            cursor.movePosition(QTextCursor.EndOfLine)
            cursor.insertText('\n' + ' ' * indent)
            self.setTextCursor(cursor)
            return
        elif event.key() == Qt.Key_Backspace:
            # Smart backspace for indentation
            cursor = self.textCursor()
            if cursor.hasSelection():
                super().keyPressEvent(event)
                return

            # Check if we're at the beginning of indentation
            cursor.select(QTextCursor.LineUnderCursor)
            line_text = cursor.selectedText()
            cursor.movePosition(QTextCursor.StartOfLine)
            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)

            pos_in_line = self.textCursor().positionInBlock()

            # If we're in leading whitespace, remove 4 spaces or 1 tab
            if pos_in_line > 0 and line_text[:pos_in_line].strip() == '':
                if pos_in_line >= 4 and line_text[pos_in_line-4:pos_in_line] == '    ':
                    # Remove 4 spaces
                    cursor = self.textCursor()
                    for _ in range(4):
                        cursor.deletePreviousChar()
                    return

        super().keyPressEvent(event)

    def insertFromMimeData(self, source):
        """Handle paste operations to preserve formatting."""
        if source.hasText():
            # Insert as plain text to preserve formatting
            cursor = self.textCursor()
            cursor.insertText(source.text())
        else:
            super().insertFromMimeData(source)


class FormattedTextDisplay(QLabel):
    """
    Enhanced QLabel for displaying formatted text with syntax highlighting.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextFormat(Qt.RichText)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        load_win95_font()

        self.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #ccc;
                padding: 8px;
                border-radius: 4px;
            }
        """)

        self.formatter = FormatterService()
        self._css_source = _TF_CSS()

    def setFormattedText(self, text: str, apply_syntax_highlighting: bool = True, extra_inline_css: str = ""):
        """Set text with formatting and optional syntax highlighting.
        extra_inline_css: optional inline CSS to wrap the content (e.g., template CSS)
        """
        if not text.strip():
            self.setText("")
            return

        # Add default CSS for code blocks
        css = self._css_source.get_default_code_css()
        formatted_html = self.formatter.render(
            text,
            RenderingOptions(
                reveal_cloze=False,
                apply_syntax_highlighting=apply_syntax_highlighting,
                inline_css=""
            )
        )

        # Wrap in a div with CSS and optional inline style
        style_attr = f' style="{extra_inline_css}"' if extra_inline_css else ""
        full_html = f"""
        <style>
        {css}
        </style>
        <div{style_attr}>
        {formatted_html}
        </div>
        """

        self.setText(full_html)

    def setFormattedTextWithCloze(self, text: str, show_blanks: bool = True,
                                 apply_syntax_highlighting: bool = True, extra_inline_css: str = ""):
        """Set text with cloze formatting.
        extra_inline_css: optional inline CSS to wrap the content (e.g., template CSS)
        """
        if not text.strip():
            self.setText("")
            return

        css = self._css_source.get_default_code_css()

        if show_blanks:
            formatted_html = self.formatter.render(
                text,
                RenderingOptions(
                    reveal_cloze=False,
                    apply_syntax_highlighting=apply_syntax_highlighting,
                    inline_css=""
                )
            )
        else:
            formatted_html = self.formatter.render(
                text,
                RenderingOptions(
                    reveal_cloze=True,
                    apply_syntax_highlighting=apply_syntax_highlighting,
                    inline_css=""
                )
            )

        style_attr = f' style="{extra_inline_css}"' if extra_inline_css else ""
        full_html = f"""
        <style>
        {css}
        </style>
        <div{style_attr}>
        {formatted_html}
        </div>
        """

        self.setText(full_html)


class CodeFormattingToolbar(QToolBar):
    """
    Toolbar with code formatting tools.
    """

    # Signals
    insertStyleMarkup = Signal(str, str)  # style_type, language
    insertCloze = Signal(int)             # cloze_index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setup_actions()

    def setup_actions(self):
        """Setup toolbar actions."""
        # Code block insertion
        code_menu = QMenu("Insert Code Block")

        languages = [
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
        ]

        for display_name, lang_code in languages:
            action = QAction(display_name, self)
            action.triggered.connect(lambda checked, lang=lang_code: self._insert_code_block(lang))
            code_menu.addAction(action)

        # Use a ToolButton with popup menu that inserts on click
        code_button = QPushButton("Code Block ▾")
        code_button.setMenu(code_menu)
        code_button.setToolTip("Insert a code block at the cursor")
        self.addWidget(code_button)

        self.addSeparator()

        # Cloze deletion buttons removed - functionality moved to card editor dialog level

    def _insert_code_block(self, language: str):
        """Insert code block markup."""
        if language:
            self.insertStyleMarkup.emit("code", language)
        else:
            self.insertStyleMarkup.emit("code", "")


class CodeEditorWidget(QWidget):
    """
    Complete code editor widget with toolbar and preview.
    """

    # Signal emitted when content changes
    contentChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Text editor only - toolbar functionality moved to card editor dialog level
        self.editor = CodeAwareTextEdit()
        self.editor.setPlaceholderText(
            "Enter your content here. Use the buttons above to insert code blocks and cloze deletions.\n\n"
            "Example:\n"
            "{start.style::code[python]}\n"
            "def hello():\n"
            "    print({{c1::\"Hello, World!\"}})\n"
            "{end.style}"
        )
        layout.addWidget(self.editor)

    def connect_signals(self):
        """Connect widget signals."""
        # Only connect editor signals - toolbar functionality moved to card editor dialog level
        self.editor.contentChanged.connect(self.contentChanged.emit)

    def _insert_style_markup(self, style_type: str, language: str):
        """Insert style markup at cursor position."""
        # Ensure the inner editor has focus and we use its current cursor
        if not self.editor.hasFocus():
            self.editor.setFocus()
        cursor = self.editor.textCursor()

        if language:
            start_markup = f"{{start.style::{style_type}[{language}]}}\n"
        else:
            start_markup = f"{{start.style::{style_type}}}\n"

        end_markup = f"\n{{end.style}}"

        if cursor.hasSelection():
            # Wrap selection
            selected_text = cursor.selectedText()
            cursor.insertText(start_markup + selected_text + end_markup)
            self.editor.setTextCursor(cursor)
        else:
            # Insert template
            cursor.insertText(start_markup + "// Your code here" + end_markup)

            # Position cursor inside the block (just before the end markup)
            move_count = len(end_markup) + len("// Your code here")
            cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.MoveAnchor, move_count)
            self.editor.setTextCursor(cursor)

        # Make sure user can see the inserted text and preview updates
        self.editor.ensureCursorVisible()
        self.contentChanged.emit()

    def _insert_cloze(self, index: int):
        """Insert cloze deletion markup."""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor.insertText(f"{{{{c{index}::{selected_text}}}}}")
        else:
            cursor.insertText(f"{{{{c{index}::text}}}}")
            # Select "text" for easy replacement
            cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.MoveAnchor, 2)
            cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor, 4)
            self.editor.setTextCursor(cursor)

    # _emit_dynamic_cloze method removed - functionality moved to card editor dialog level

    def toPlainText(self) -> str:
        """Get the plain text content."""
        return self.editor.toPlainText()

    def setPlainText(self, text: str):
        """Set the plain text content."""
        self.editor.setPlainText(text)

    def clear(self):
        """Clear the editor content."""
        self.editor.clear()
