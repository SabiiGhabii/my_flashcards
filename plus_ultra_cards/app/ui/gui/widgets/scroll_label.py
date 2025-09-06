"""
ScrollableLabel: A QLabel embedded in a QScrollArea for large content.
Scroll bars are hidden by default (overlay behavior) but scrolling works.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QScrollArea, QWidget, QVBoxLayout


class ScrollableLabel(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setFrameShape(QScrollArea.NoFrame)

        self._label = QLabel()
        self._label.setTextFormat(Qt.RichText)
        self._label.setWordWrap(True)
        self._label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)
        self.setWidget(container)

    def setText(self, html: str):
        self._label.setText(html)

    def text(self) -> str:
        return self._label.text()

    def label(self) -> QLabel:
        return self._label
