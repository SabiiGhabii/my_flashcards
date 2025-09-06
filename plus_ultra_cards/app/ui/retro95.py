# study_lab_win95.py
# One-file Win95-styled PySide6 app with font loading, icons, and extra widgets.
from __future__ import annotations
import math, os, random, sys, time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtGui import (QAction, QColor, QCursor, QIcon,
                           QPainter, QPalette, QPixmap)
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDateTimeEdit, QDial, QDoubleSpinBox,
    QFileDialog, QFileSystemModel, QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLCDNumber, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMenuBar, QMessageBox, QProgressBar, QPushButton, QSlider, QSpinBox,
    QStatusBar, QStyle, QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit,
    QToolBar, QTreeView, QVBoxLayout, QWidget
)

from .font_loader import load_win95_font

# ---------------------- Win95 Palette + QSS ----------------------
WIN95 = {
    "bg":        "#C0C0C0",  # ButtonFace
    "hl":        "#FFFFFF",  # ButtonHighlight (top/left)
    "sh":        "#808080",  # ButtonShadow (bottom/right)
    "dk":        "#000000",  # ButtonDkShadow
    "text":      "#000000",
    "base":      "#FFFFFF",  # text fields
    "content_bg": "#FFFFFF",  # content background (white for markdown)
    "sel_bg":    "#000080",  # selection (Navy)
    "sel_text":  "#FFFFFF",
    "tooltip":   "#FFFFE1",  # light yellow
}

_QSS = f"""
* {{
    background: {WIN95['bg']};
    color: {WIN95['text']};
    selection-background-color: {WIN95['sel_bg']};
    selection-color: {WIN95['sel_text']};
    outline: 0;
}}
QToolTip {{
    background-color: {WIN95['tooltip']};
    color: {WIN95['text']};
    border: 1px solid {WIN95['dk']};
}}
QPushButton {{
    background: {WIN95['bg']};
    border: 2px solid {WIN95['dk']};
    border-top-color: {WIN95['hl']};
    border-left-color: {WIN95['hl']};
    border-right-color: {WIN95['sh']};
    border-bottom-color: {WIN95['sh']};
    padding: 2px 10px;
}}
QPushButton:pressed {{
    border-top-color: {WIN95['sh']};
    border-left-color: {WIN95['sh']};
    border-right-color: {WIN95['hl']};
    border-bottom-color: {WIN95['hl']};
    padding-top: 3px; padding-left: 11px; padding-right: 9px; padding-bottom: 1px;
}}
QPushButton:disabled {{ color: #7f7f7f; }}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox,
QComboBox, QListView, QTreeView, QTableView {{
    background: {WIN95['base']};
    border: 2px solid {WIN95['dk']};
    border-top-color: {WIN95['sh']};
    border-left-color: {WIN95['sh']};
    border-right-color: {WIN95['hl']};
    border-bottom-color: {WIN95['hl']};
    selection-background-color: {WIN95['sel_bg']};
    selection-color: {WIN95['sel_text']};
}}

QGroupBox {{
    border: 2px solid {WIN95['dk']};
    border-top-color: {WIN95['hl']};
    border-left-color: {WIN95['hl']};
    border-right-color: {WIN95['sh']};
    border-bottom-color: {WIN95['sh']};
    margin-top: 18px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 8px;
    top: -2px;
    padding: 2px 6px;
    background-color: {WIN95['bg']};
}}

QMenuBar {{ background: {WIN95['bg']}; }}
QMenuBar::item {{ background: transparent; padding: 4px 8px; }}
QMenuBar::item:selected {{ background: {WIN95['sel_bg']}; color: {WIN95['sel_text']}; }}
QMenu {{
    background: {WIN95['bg']};
    border: 2px solid {WIN95['dk']};
    border-top-color: {WIN95['hl']};
    border-left-color: {WIN95['hl']};
    border-right-color: {WIN95['sh']};
    border-bottom-color: {WIN95['sh']};
}}
QMenu::item:selected {{ background: {WIN95['sel_bg']}; color: {WIN95['sel_text']}; }}

QStatusBar {{ background: {WIN95['bg']}; border-top: 2px solid {WIN95['hl']}; }}

QTabWidget::pane {{
    background: {WIN95['bg']};
    border: 2px solid {WIN95['dk']};
    border-top-color: {WIN95['sh']};
    border-left-color: {WIN95['sh']};
    border-right-color: {WIN95['hl']};
    border-bottom-color: {WIN95['hl']};
}}
QTabBar::tab {{
    background: {WIN95['bg']};
    border: 2px solid {WIN95['dk']};
    border-top-color: {WIN95['hl']};
    border-left-color: {WIN95['hl']};
    border-right-color: {WIN95['sh']};
    border-bottom-color: {WIN95['sh']};
    padding: 4px 10px; margin-right: 2px;
}}
QTabBar::tab:selected {{ margin-bottom: -2px; }}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 13px; height: 13px;
    border: 2px solid {WIN95['dk']};
    border-top-color: {WIN95['hl']};
    border-left-color: {WIN95['hl']};
    border-right-color: {WIN95['sh']};
    border-bottom-color: {WIN95['sh']};
    background: {WIN95['bg']};
}}
QRadioButton::indicator:checked {{ background: {WIN95['sel_bg']}; }}
QCheckBox::indicator:checked {{ background: {WIN95['sel_bg']}; }}
"""
def vintage_icon(icon: QIcon, size: QSize, downscale: float = 0.9) -> QIcon:
    """Return a pixelated, lower-res-looking icon at 'size' by scaling down then back up."""
    pm = icon.pixmap(size)
    # (Optional) enforce 1x DPR so we actually get chunky pixels
    try: pm.setDevicePixelRatio(6)
    except Exception: pass
    small = pm.scaled(
        max(1, int(size.width() * downscale)),
        max(1, int(size.height() * downscale)),
        Qt.KeepAspectRatio,
        Qt.FastTransformation,   # nearest-neighbor
    )
    chunky = small.scaled(size, Qt.KeepAspectRatio, Qt.FastTransformation)
    return QIcon(chunky)

def apply_win95_theme(app: QApplication):
    """Apply Win95-style palette and styling."""
    # Palette (Fusion for consistent cross-platform look)
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(WIN95["bg"]))
    pal.setColor(QPalette.WindowText, QColor(WIN95["text"]))
    pal.setColor(QPalette.Base, QColor(WIN95["base"]))
    pal.setColor(QPalette.AlternateBase, QColor(WIN95["bg"]))
    pal.setColor(QPalette.ToolTipBase, QColor(WIN95["tooltip"]))
    pal.setColor(QPalette.ToolTipText, QColor(WIN95["text"]))
    pal.setColor(QPalette.Text, QColor(WIN95["text"]))
    pal.setColor(QPalette.Button, QColor(WIN95["bg"]))
    pal.setColor(QPalette.ButtonText, QColor(WIN95["text"]))
    pal.setColor(QPalette.Highlight, QColor(WIN95["sel_bg"]))
    pal.setColor(QPalette.HighlightedText, QColor(WIN95["sel_text"]))
    app.setPalette(pal)

    app.setStyleSheet(_QSS)

# Convenience retro widgets
class RetroSeparator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

# ---------------------- Fun custom widgets ----------------------
class RetroMarquee(QLabel):
    """Scrolling marquee label (1995 called)."""
    def __init__(self, text="Welcome to Study Lab", speed=40, parent=None):
        super().__init__(text, parent)
        self._speed = speed  # px/step
        self._x = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)
        self.setFixedHeight(20)
        self.setStyleSheet("background-color: transparent;")

    def _tick(self):
        self._x -= self._speed * 0.05
        if self._x < -self.fontMetrics().horizontalAdvance(self.text()):
            self._x = self.width()
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.TextAntialiasing, False)
        p.drawText(QPoint(int(self._x), int(self.height() - 5)), self.text())

class DoodlePad(QWidget):
    """Tiny mouse-draw canvas like MSPaint."""
    def __init__(self):
        super().__init__()
        self.setMinimumSize(320, 200)
        self._pix = QPixmap(self.size())
        self._pix.fill(Qt.white)
        self._last = None

    def resizeEvent(self, e):
        new = QPixmap(self.size())
        new.fill(Qt.white)
        p = QPainter(new)
        p.drawPixmap(0, 0, self._pix)
        p.end()
        self._pix = new

    def mousePressEvent(self, e):
        if e.buttons() & Qt.LeftButton:
            self._last = e.position().toPoint()

    def mouseMoveEvent(self, e):
        if self._last is None: return
        p = QPainter(self._pix)
        p.setRenderHint(QPainter.Antialiasing, False)
        p.setPen(Qt.black)
        p.drawLine(self._last, e.position().toPoint())
        p.end()
        self._last = e.position().toPoint()
        self.update()

    def mouseReleaseEvent(self, e):
        self._last = None

    def paintEvent(self, e):
        p = QPainter(self)
        p.drawPixmap(0, 0, self._pix)

    def clear(self):
        self._pix.fill(Qt.white); self.update()

# ---------------------- Main Window ----------------------
class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Study Lab — Win95 (All-in-One)")
        self.resize(1024, 700)

        # Toolbar with classic icons
        self._make_toolbar()

        # Menubar
        self._make_menubar()

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._home_tab(), "Home")
        tabs.addTab(self._forms_tab(), "Forms")
        tabs.addTab(self._table_tab(), "Table")
        tabs.addTab(self._fun_tab(), "Fun")
        tabs.addTab(self._files_tab(), "Files")

        self.setCentralWidget(tabs)

        # Status bar
        sb = QStatusBar()
        sb.showMessage("Ready")
        self.setStatusBar(sb)

        # little timer to animate the progress bar on the fun tab
        self._spin_timer = QTimer(self)
        self._spin_timer.timeout.connect(self._tick_fun)
        self._spin_timer.start(80)
        self._spin_phase = 0

    # ---------- UI builders ----------
    def _make_toolbar(self):
        tb = QToolBar("Main"); tb.setMovable(False)
        icon_size = QSize(24, 24)            # or 20x20 if you want smaller
        tb.setIconSize(icon_size)

        mk = self.style().standardIcon
        actions = [
            ("New",     mk(QStyle.SP_FileIcon),                self._action_new),
            ("Open",    mk(QStyle.SP_DialogOpenButton),        self._action_open),
            ("Save",    mk(QStyle.SP_DialogSaveButton),        self._action_save),
            ("Compute", mk(QStyle.SP_MediaPlay),               self._action_compute),
            ("Mystery", mk(QStyle.SP_MessageBoxQuestion),      self._action_mystery),
        ]
        for name, base_icon, slot in actions:
            vint = vintage_icon(base_icon, icon_size, downscale=0.75)
            act = QAction(vint, name, self); act.triggered.connect(slot)
            tb.addAction(act)
        tb.addSeparator()
        self.addToolBar(tb)

    def _make_menubar(self):
        mb = QMenuBar(self)
        file_menu = mb.addMenu("&File")
        file_menu.addAction("New", self._action_new)
        file_menu.addAction("Open…", self._action_open)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        help_menu = mb.addMenu("&Help")
        help_menu.addAction("About", self._action_about)
        self.setMenuBar(mb)

    # ---------- Tabs ----------
    def _home_tab(self) -> QWidget:
        w = QWidget(); v = QVBoxLayout(w)
        v.addWidget(RetroMarquee("Welcome to the most serious retro laboratory of learning."))
        v.addWidget(RetroSeparator())

        # Quick Actions group
        g = QGroupBox("Quick Actions"); gl = QHBoxLayout(g)
        for label, slot in [("Compute", self._action_compute),
                            ("Run Drill", self._action_run_drill),
                            ("Review Queue…", self._action_review)]:
            b = QPushButton(label); b.clicked.connect(slot); gl.addWidget(b)
        gl.addStretch(1)
        v.addWidget(g)

        v.addWidget(RetroSeparator())
        notes = QTextEdit()
        notes.setPlainText("Notes go here.\nMake Win95 great again.")
        v.addWidget(notes)
        return w

    def _forms_tab(self) -> QWidget:
        w = QWidget(); grid = QGridLayout(w)
        grid.setHorizontalSpacing(10); grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Expression:"), 0, 0)
        expr = QLineEdit(placeholderText="f(x)"); grid.addWidget(expr, 0, 1, 1, 2)
        grid.addWidget(QPushButton("Differentiate"), 0, 3)

        grid.addWidget(QLabel("Method:"), 1, 0)
        combo = QComboBox(); combo.addItems(["Cholesky", "QR", "CG", "SVD"])
        grid.addWidget(combo, 1, 1)

        cb = QCheckBox("Interleave topics"); grid.addWidget(cb, 2, 0, 1, 2)
        rb_e = QCheckBox("Easy"); rb_h = QCheckBox("Hard")
        grid.addWidget(rb_e, 3, 0); grid.addWidget(rb_h, 3, 1)

        grid.addWidget(QLabel("Start time:"), 4, 0)
        grid.addWidget(QDateTimeEdit(), 4, 1)

        # Sliders/dials
        grid.addWidget(QLabel("Difficulty:"), 5, 0)
        diff = QSlider(Qt.Horizontal); diff.setRange(0, 100); diff.setValue(50)
        grid.addWidget(diff, 5, 1, 1, 2)

        grid.addWidget(QLabel("Iterations:"), 6, 0)
        grid.addWidget(QSpinBox(), 6, 1)
        grid.addWidget(QDoubleSpinBox(), 6, 2)

        grid.addWidget(QPushButton("Run"), 7, 3)
        return w

    def _table_tab(self) -> QWidget:
        w = QWidget(); v = QVBoxLayout(w)
        tbl = QTableWidget(8, 4)
        tbl.setHorizontalHeaderLabels(["Item", "Next Due", "Stability", "Ease"])
        for r in range(tbl.rowCount()):
            tbl.setItem(r, 0, QTableWidgetItem(f"Card {r+1}"))
            tbl.setItem(r, 1, QTableWidgetItem(f"{random.randint(1,6)} days"))
            tbl.setItem(r, 2, QTableWidgetItem(f"{random.random():.2f}"))
            tbl.setItem(r, 3, QTableWidgetItem(f"{0.3 + random.random()*0.6:.2f}"))
        v.addWidget(tbl)
        return w

    def _fun_tab(self) -> QWidget:
        w = QWidget(); v = QVBoxLayout(w)

        # Icon zoo
        zoo = QListWidget()
        zoo.setViewMode(QListWidget.IconMode)
        zoo.setIconSize(QSize(32,32))
        zoo.setResizeMode(QListWidget.Adjust)
        zoo.setSpacing(8)
        def add_icon(name, sp):
            base = self.style().standardIcon(sp)
            size = zoo.iconSize() or QSize(32, 32)
            vint = vintage_icon(base, size, downscale=0.75)
            zoo.addItem(QListWidgetItem(vint, name))
        add_icon("Computer", QStyle.SP_ComputerIcon)
        add_icon("Folder", QStyle.SP_DirIcon)
        add_icon("File", QStyle.SP_FileIcon)
        add_icon("Info", QStyle.SP_MessageBoxInformation)
        add_icon("Warning", QStyle.SP_MessageBoxWarning)
        add_icon("Critical", QStyle.SP_MessageBoxCritical)
        add_icon("Help", QStyle.SP_MessageBoxQuestion)
        add_icon("Play", QStyle.SP_MediaPlay)
        add_icon("Stop", QStyle.SP_MediaStop)

        # Doodle pad with controls
        pad = DoodlePad()
        btns = QHBoxLayout()
        clear = QPushButton("Clear Canvas"); clear.clicked.connect(pad.clear)
        surprise = QPushButton("Surprise…"); surprise.clicked.connect(self._action_mystery)
        btns.addWidget(clear); btns.addWidget(surprise); btns.addStretch(1)

        # Retro progress + LCD
        g = QGroupBox("Gauges"); gl = QHBoxLayout(g)
        self._prog = QProgressBar(); self._prog.setRange(0, 100)
        self._lcd = QLCDNumber(); self._lcd.setDigitCount(5)
        dial = QDial(); dial.setRange(0, 100); dial.valueChanged.connect(self._prog.setValue)
        gl.addWidget(QLabel("Progress:")); gl.addWidget(self._prog)
        gl.addWidget(QLabel("Dial→")); gl.addWidget(dial)
        gl.addWidget(QLabel("LCD:")); gl.addWidget(self._lcd)

        v.addWidget(QLabel("Icon Zoo")); v.addWidget(zoo, 1)
        v.addWidget(RetroSeparator())
        v.addWidget(QLabel("Doodle Pad")); v.addLayout(btns); v.addWidget(pad, 2)
        v.addWidget(RetroSeparator())
        v.addWidget(g)
        return w

    def _files_tab(self) -> QWidget:
        w = QWidget(); v = QVBoxLayout(w)
        g = QGroupBox("File Explorer"); gl = QHBoxLayout(g)
        model = QFileSystemModel(); model.setRootPath(str(Path.cwd()))
        tree = QTreeView(); tree.setModel(model)
        tree.setRootIndex(model.index(str(Path.cwd())))
        tree.setColumnWidth(0, 260)
        open_btn = QPushButton("Open Selected…")
        def open_selected():
            idx = tree.currentIndex()
            if not idx.isValid(): return
            path = model.filePath(idx)
            QMessageBox.information(self, "Open", f"Would open:\n{path}")
        open_btn.clicked.connect(open_selected)
        gl.addWidget(tree, 1); gl.addWidget(open_btn)
        v.addWidget(g)
        return w

    # ---------- Actions ----------
    def _action_new(self):
        QMessageBox.information(self, "New", "New project (pretend) created.")

    def _action_open(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open…", str(Path.cwd()))
        if fname:
            self.statusBar().showMessage(f"Opened: {fname}", 3000)

    def _action_save(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save As…", str(Path.cwd() / "untitled.txt"))
        if fname:
            with open(fname, "w", encoding="utf-8") as f: f.write("Hello from 1995.\n")
            self.statusBar().showMessage(f"Saved: {fname}", 3000)

    def _action_compute(self):
        QMessageBox.information(self, "Compute", "Pretend we differentiated something very important.")

    def _action_run_drill(self):
        QMessageBox.information(self, "Drill", "5-minute reflex drill: GO!")

    def _action_review(self):
        QMessageBox.information(self, "SRS", "Opening your review queue… (in a future tab)")

    def _action_about(self):
        QMessageBox.information(self, "About", "Study Lab — Win95 Edition\nAll the vibes, none of the bugs.")

    def _action_mystery(self):
        msgs = ["Beep boop", "Y2K compatible!", "Insert floppy disk 2", "It’s not a bug, it’s a feature"]
        icons = [QMessageBox.Information, QMessageBox.Warning, QMessageBox.Critical, QMessageBox.Question]
        m = QMessageBox(self)
        m.setIcon(random.choice(icons))
        m.setText(random.choice(msgs))
        m.setWindowTitle("Mystery Box")
        m.exec()

    def _tick_fun(self):
        self._spin_phase = (self._spin_phase + 1) % 100
        self._prog.setValue((self._prog.value() + 1) % 101)
        self._lcd.display(self._prog.value() * math.pi)

# ---------------------- Main ----------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    load_win95_font(app, base_point_size=11)
    apply_win95_theme(app)
    Main().show()
    sys.exit(app.exec())
