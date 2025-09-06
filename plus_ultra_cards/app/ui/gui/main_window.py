"""
Main Window for Plus Ultra Cards
Uses retro95.py framework for Win95-style interface.
"""

import os
import sys
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QAction, QIcon, QPainter, QPen, QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QGroupBox, QPushButton, QLabel, QListWidget,
    QListWidgetItem, QMessageBox, QFileDialog, QInputDialog, QDialog,
    QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QLineEdit, QFrame, QProgressDialog
)

# Import app components
from app.ui.retro95 import apply_win95_theme, RetroSeparator, RetroMarquee
from app.core.card_manager import CardManager
from app.core.study_sessions import SessionManager, StudyMode
from app.core.deck_layout_manager import DeckLayoutManager
from app.core.config_manager import get_config


class DeckWidget(QWidget):
    """Widget representing a deck on the home screen.
    Supports optional drag-resize with snap-to-grid by emitting a resize request
    that the main window resolves when laying out the grid.
    """

    def __init__(self, deck_data, main_window):
        super().__init__()
        self.deck_data = deck_data
        self.main_window = main_window
        # Ensure background styling is applied on QWidget
        self.setObjectName("deckBox")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._dragging = False
        self._drag_start_pos = None
        self.setup_ui()

        # Create four corner resize handles for continuous resizing
        self._handles = []  # list of dicts: {'w': QWidget, 'h_factor': int, 'v_factor': int}
        self._drag_handle = None
        self._drag_h_factor = 0
        self._drag_v_factor = 0
        self._init_resize_handles()
        self._reposition_handles()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Deck name
        name_label = QLabel(self.deck_data['name'])
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(name_label)

        # Deck stats
        stats_text = f"Cards: {self.deck_data['card_count']} | Due: {self.deck_data['due_count']}"
        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("color: #666666;")
        layout.addWidget(stats_label)

        # Description
        if self.deck_data.get('description'):
            desc_label = QLabel(self.deck_data['description'])
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # Action buttons
        button_layout = QHBoxLayout()

        study_btn = QPushButton("Study")
        study_btn.clicked.connect(self.show_study_options)
        button_layout.addWidget(study_btn)

        edit_btn = QPushButton("Manage Cards")
        edit_btn.clicked.connect(self.edit_deck)
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete Deck")
        delete_btn.clicked.connect(self.delete_deck)
        delete_btn.setStyleSheet("QPushButton { background-color: #FFB6C1; }")  # Light red
        button_layout.addWidget(delete_btn)

        layout.addLayout(button_layout)

        # Style the widget to be inset with white background (proper retro95 inset)
        # Use objectName selector to ensure the stylesheet applies to this QWidget
        self.setStyleSheet("""
            QWidget#deckBox {
                background-color: #FFFFFF;
                border: 2px solid;
                /* Inset look: darker on top/left, lighter on bottom/right */
                border-top-color: #808080;
                border-left-color: #808080;
                border-right-color: #FFFFFF;
                border-bottom-color: #FFFFFF;
                padding: 8px;
                margin: 6px;
            }
            QWidget#deckBox QLabel { background-color: transparent; }
        """)

    def _init_resize_handles(self):
        # Create handles with direction factors (h_factor for width, v_factor for height)
        corners = [
            { 'cursor': Qt.SizeFDiagCursor,  'h':  1, 'v':  1 },  # bottom-right
            { 'cursor': Qt.SizeBDiagCursor,  'h': -1, 'v': -1 },  # top-left
            { 'cursor': Qt.SizeBDiagCursor,  'h':  1, 'v': -1 },  # top-right
            { 'cursor': Qt.SizeFDiagCursor,  'h': -1, 'v':  1 },  # bottom-left
        ]
        for c in corners:
            w = QWidget(self)
            w.setFixedSize(16, 16)
            w.setCursor(c['cursor'])
            w.setAttribute(Qt.WA_StyledBackground, True)
            w.setStyleSheet("background: rgba(0,0,0,0);")
            w.installEventFilter(self)
            self._handles.append({ 'w': w, 'h': c['h'], 'v': c['v'] })

    def _reposition_handles(self):
        # Position: TL, TR, BL, BR
        if not self._handles:
            return
        # bottom-right
        self._handles[0]['w'].move(self.width() - 16, self.height() - 16)
        # top-left
        self._handles[1]['w'].move(0, 0)
        # top-right
        self._handles[2]['w'].move(self.width() - 16, 0)
        # bottom-left
        self._handles[3]['w'].move(0, self.height() - 16)

    def resizeEvent(self, event):
        self._reposition_handles()
        super().resizeEvent(event)

    def eventFilter(self, obj, event):
        # Handle events for any handle
        for h in self._handles:
            if obj is h['w']:
                if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                    self._dragging = True
                    self._drag_handle = h['w']
                    self._drag_h_factor = h['h']
                    self._drag_v_factor = h['v']
                    self._drag_start_pos = event.globalPosition() if hasattr(event, 'globalPosition') else event.globalPos()
                    return True
                elif event.type() == QEvent.MouseMove and self._dragging and self._drag_handle is h['w']:
                    gpos = event.globalPosition() if hasattr(event, 'globalPosition') else event.globalPos()
                    delta = gpos - self._drag_start_pos
                    # Apply factors to interpret direction from the specific corner
                    d_cols = 1 if (delta.x() * self._drag_h_factor) > 40 else (-1 if (delta.x() * self._drag_h_factor) < -40 else 0)
                    d_rows = 1 if (delta.y() * self._drag_v_factor) > 40 else (-1 if (delta.y() * self._drag_v_factor) < -40 else 0)
                    current_span = self.main_window.layout_manager.get_deck_span(self.deck_data['id'])
                    new_span = (max(1, current_span[0] + d_rows), max(1, current_span[1] + d_cols))
                    if new_span != current_span:
                        self.main_window.layout_manager.set_deck_span(self.deck_data['id'], new_span[0], new_span[1])
                        self.main_window.refresh_deck_layout()
                        # Reset threshold baseline so drag can continue to apply additional snaps
                        self._drag_start_pos = gpos
                    return True
                elif event.type() == QEvent.MouseButtonRelease and self._dragging and self._drag_handle is h['w']:
                    self._dragging = False
                    self._drag_handle = None
                    self._drag_start_pos = None
                    return True
        return super().eventFilter(obj, event)

    def show_study_options(self):
        self.main_window.show_study_options(self.deck_data['id'])

    def edit_deck(self):
        self.main_window.edit_deck(self.deck_data['id'])

    def delete_deck(self):
        """Delete this deck."""
        self.main_window.delete_deck(self.deck_data['id'])


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Initialize configuration and migrate legacy settings
        self.config = get_config()
        self.config.migrate_from_legacy_files()

        self.setWindowTitle("Plus Ultra Cards — Anki-Quizlet Hybrid")
        self.resize(1200, 800)

        # Initialize managers
        self.card_manager = CardManager()
        self.session_manager = SessionManager(self.card_manager)
        self.layout_manager = DeckLayoutManager()

        # Setup UI
        self.setup_menubar()
        self.setup_central_widget()
        self.setup_statusbar()

        # Apply retro theme
        apply_win95_theme(QApplication.instance())

        # Load initial data
        self.refresh_decks()

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_decks)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

    def setup_menubar(self):
        """Setup the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_deck_action = QAction("&New Deck", self)
        new_deck_action.triggered.connect(self.create_new_deck)
        file_menu.addAction(new_deck_action)

        import_action = QAction("&Import Cards...", self)
        import_action.triggered.connect(self.import_cards)
        file_menu.addAction(import_action)

        export_action = QAction("&Export Deck...", self)
        export_action.triggered.connect(self.export_deck)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Study menu
        study_menu = menubar.addMenu("&Study")

        cram_action = QAction("&Cram Session", self)
        cram_action.triggered.connect(lambda: self.quick_study(StudyMode.CRAM))
        study_menu.addAction(cram_action)

        review_action = QAction("&Review Session", self)
        review_action.triggered.connect(lambda: self.quick_study(StudyMode.REVIEW))
        study_menu.addAction(review_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        reset_layout_action = QAction("&Reset Deck Layout", self)
        reset_layout_action.triggered.connect(self.reset_deck_layout)
        view_menu.addAction(reset_layout_action)
        # Metrics option
        metrics_action = QAction("&Metrics", self)
        metrics_action.triggered.connect(self.show_metrics_dialog)
        view_menu.addAction(metrics_action)


        # (Removed theme submenu; keeping original View menu minimal)

        # Flashcard Generation menu
        generation_menu = menubar.addMenu("&Generate")

        import_pdf_action = QAction("Import from &PDF...", self)
        import_pdf_action.triggered.connect(lambda: self.import_from_source('pdf'))
        generation_menu.addAction(import_pdf_action)

        import_github_action = QAction("Import from &GitHub...", self)
        import_github_action.triggered.connect(lambda: self.import_from_source('github'))
        generation_menu.addAction(import_github_action)

        import_html_action = QAction("Import from &HTML/URL...", self)
        import_html_action.triggered.connect(lambda: self.import_from_source('html'))
        generation_menu.addAction(import_html_action)

        import_epub_action = QAction("Import from &EPUB...", self)
        import_epub_action.triggered.connect(lambda: self.import_from_source('epub'))
        generation_menu.addAction(import_epub_action)

        generation_menu.addSeparator()

        open_terminal_action = QAction("Open &Terminal", self)
        open_terminal_action.triggered.connect(self.open_terminal)
        generation_menu.addAction(open_terminal_action)

        generation_menu.addSeparator()

        api_keys_action = QAction("&API Keys && AI Settings...", self)
        api_keys_action.triggered.connect(self.open_api_key_dialog)
        generation_menu.addAction(api_keys_action)

        # SRS menu (before Help)
        srs_menu = menubar.addMenu("&SRS")

        # Select SRS Engine submenu
        select_engine_menu = srs_menu.addMenu("Select &SRS Engine")
        self.action_engine_deeptutor = QAction("DeepTutor RL Engine", self, checkable=True)
        self.action_engine_sm2 = QAction("Legacy SM-2 Algorithm", self, checkable=True)
        self.action_engine_future = QAction("Future Engine (placeholder)", self, checkable=True, enabled=False)
        for a in (self.action_engine_deeptutor, self.action_engine_sm2, self.action_engine_future):
            a.triggered.connect(self.on_engine_selected)
            select_engine_menu.addAction(a)

        adv_action = QAction("&Advanced SRS Settings", self)
        adv_action.triggered.connect(self.show_srs_settings_dialog)
        srs_menu.addAction(adv_action)

        self.load_engine_selection()



        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_central_widget(self):
        """Setup the central widget with tabs."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Add marquee with refined white inset styling (transparent marquee, tighter padding)
        marquee_frame = QFrame()
        marquee_frame.setObjectName("marqueeBox")
        marquee_frame.setAttribute(Qt.WA_StyledBackground, True)
        marquee_layout = QHBoxLayout(marquee_frame)
        marquee_layout.setContentsMargins(4, 4, 4, 4)
        marquee_layout.setSpacing(0)
        marquee = RetroMarquee("Welcome to Plus Ultra Cards - The Ultimate Study Companion!")
        marquee.setStyleSheet("background-color: transparent;")
        marquee_layout.addWidget(marquee)
        marquee_frame.setStyleSheet("""
            QFrame#marqueeBox {
                background-color: #FFFFFF;
                border: 2px solid;
                border-top-color: #808080;
                border-left-color: #808080;
                border-right-color: #FFFFFF;
                border-bottom-color: #FFFFFF;
                padding: 2px;
                margin: 4px;
            }
        """)
        layout.addWidget(marquee_frame)

        layout.addWidget(RetroSeparator())

        # Create tab widget
        self.tab_widget = QTabWidget()
        # Move tab labels up slightly for alignment
        self.tab_widget.setStyleSheet("QTabBar::tab { margin-top: -2px; padding: 4px 10px; }")

        # Home tab
        self.home_tab = self.create_home_tab()
        self.tab_widget.addTab(self.home_tab, "Home")

        # Statistics tab
        self.stats_tab = self.create_statistics_tab()
        self.tab_widget.addTab(self.stats_tab, "Statistics")

        layout.addWidget(self.tab_widget)

    def create_home_tab(self):
        """Create the home tab with deck management."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Quick actions group
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout(actions_group)

        new_deck_btn = QPushButton("New Deck")
        new_deck_btn.clicked.connect(self.create_new_deck)
        actions_layout.addWidget(new_deck_btn)

        import_btn = QPushButton("Import Cards")
        import_btn.clicked.connect(self.import_cards)
        actions_layout.addWidget(import_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_decks)
        actions_layout.addWidget(refresh_btn)

        actions_layout.addStretch()
        layout.addWidget(actions_group)

        layout.addWidget(RetroSeparator())

        # Decks section
        decks_label = QLabel("Your Decks")
        decks_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(decks_label)

        # Deck container (4-column grid)
        self.deck_container = QWidget()
        self.deck_layout = QGridLayout(self.deck_container)
        self.deck_layout.setHorizontalSpacing(10)
        self.deck_layout.setVerticalSpacing(10)
        layout.addWidget(self.deck_container)

        layout.addStretch()
        return widget

    def create_statistics_tab(self):
        """Create the statistics tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Overall statistics
        stats_group = QGroupBox("Overall Statistics")
        stats_layout = QGridLayout(stats_group)

        self.total_decks_label = QLabel("Total Decks: 0")
        self.total_cards_label = QLabel("Total Cards: 0")
        self.due_cards_label = QLabel("Due Cards: 0")
        self.study_streak_label = QLabel("Study Streak: 0 days")

        stats_layout.addWidget(self.total_decks_label, 0, 0)
        stats_layout.addWidget(self.total_cards_label, 0, 1)
        stats_layout.addWidget(self.due_cards_label, 1, 0)
        stats_layout.addWidget(self.study_streak_label, 1, 1)

        layout.addWidget(stats_group)

        # Recent activity
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout(activity_group)

        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels(["Date", "Deck", "Session Type", "Cards Studied"])
        self.activity_table.horizontalHeader().setStretchLastSection(True)
        activity_layout.addWidget(self.activity_table)

        layout.addWidget(activity_group)

        return widget

    def setup_statusbar(self):
        """Setup the status bar."""
        self.statusBar().showMessage("Ready")

    def refresh_decks(self):
        """Refresh the deck display."""
        # Clear existing deck widgets
        for i in reversed(range(self.deck_layout.count())):
            child = self.deck_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # Get updated deck data
        decks = self.card_manager.get_all_decks()

        self.refresh_deck_layout()

        # Update statistics
        self.update_statistics(decks)

        # Update status
        self.statusBar().showMessage(f"Loaded {len(decks)} decks")

    def refresh_deck_layout(self):
        """Refresh the deck layout using the layout manager."""
        # Clear existing widgets
        for i in reversed(range(self.deck_layout.count())):
            child = self.deck_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # Get current decks
        decks = self.card_manager.get_all_decks()
        deck_ids = [deck['id'] for deck in decks]

        # Validate spans and get positions
        self.layout_manager.validate_spans(deck_ids)
        positions = self.layout_manager.calculate_grid_positions(deck_ids)

        # Create and place deck widgets
        for deck in decks:
            deck_widget = DeckWidget(deck, self)
            deck_id = deck['id']

            if deck_id in positions:
                row, col, row_span, col_span = positions[deck_id]
                self.deck_layout.addWidget(deck_widget, row, col, row_span, col_span)

    def reset_deck_layout(self):
        """Reset all deck layouts to default 4-column grid."""
        reply = QMessageBox.question(
            self, "Reset Layout",
            "Reset all deck boxes to default sizes?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.layout_manager.reset_layout()
            self.refresh_deck_layout()
            QMessageBox.information(self, "Layout Reset", "Deck layout has been reset to default.")

    def update_statistics(self, decks):
        """Update the statistics display."""
        total_decks = len(decks)
        total_cards = sum(deck['card_count'] for deck in decks)
        due_cards = sum(deck['due_count'] for deck in decks)

        self.total_decks_label.setText(f"Total Decks: {total_decks}")
        self.total_cards_label.setText(f"Total Cards: {total_cards}")
        self.due_cards_label.setText(f"Due Cards: {due_cards}")

    def create_new_deck(self):
        """Create a new deck."""
        name, ok = QInputDialog.getText(self, "New Deck", "Enter deck name:")
        if ok and name.strip():
            description, ok = QInputDialog.getText(self, "New Deck", "Enter description (optional):")
            if ok:
                try:
                    deck_id = self.card_manager.create_deck(name.strip(), description.strip())
                    self.refresh_decks()
                    QMessageBox.information(self, "Success", f"Deck '{name}' created successfully!")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to create deck: {str(e)}")

    def import_cards(self):
        """Import cards from CSV file."""
        # First select deck
        decks = self.card_manager.get_all_decks()
        if not decks:
            QMessageBox.information(self, "No Decks", "Please create a deck first.")
            return

        deck_names = [f"{deck['name']} (ID: {deck['id']})" for deck in decks]
        deck_name, ok = QInputDialog.getItem(self, "Select Deck", "Choose deck to import to:", deck_names, 0, False)

        if ok and deck_name:
            deck_id = int(deck_name.split("ID: ")[1].split(")")[0])

            # Select CSV file
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Import CSV File", "", "CSV Files (*.csv);;All Files (*)"
            )

            if file_path:
                try:
                    imported, errors = self.card_manager.import_cards_from_csv(deck_id, file_path)

                    message = f"Successfully imported {imported} cards."
                    if errors:
                        message += f"\n\nErrors encountered:\n" + "\n".join(errors[:5])
                        if len(errors) > 5:
                            message += f"\n... and {len(errors) - 5} more errors."

                    QMessageBox.information(self, "Import Complete", message)
                    self.refresh_decks()

                except Exception as e:
                    QMessageBox.critical(self, "Import Error", f"Failed to import cards: {str(e)}")

    def export_deck(self):
        """Export deck to CSV file."""
        decks = self.card_manager.get_all_decks()
        if not decks:
            QMessageBox.information(self, "No Decks", "No decks available to export.")
            return

        deck_names = [f"{deck['name']} (ID: {deck['id']})" for deck in decks]
        deck_name, ok = QInputDialog.getItem(self, "Select Deck", "Choose deck to export:", deck_names, 0, False)

        if ok and deck_name:
            deck_id = int(deck_name.split("ID: ")[1].split(")")[0])

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export CSV File", f"deck_{deck_id}.csv", "CSV Files (*.csv);;All Files (*)"
            )

            if file_path:
                try:
                    success = self.card_manager.export_cards_to_csv(deck_id, file_path)
                    if success:
                        QMessageBox.information(self, "Export Complete", f"Deck exported to {file_path}")
                    else:
                        QMessageBox.critical(self, "Export Error", "Failed to export deck.")
                except Exception as e:
                    QMessageBox.critical(self, "Export Error", f"Failed to export deck: {str(e)}")

    def show_study_options(self, deck_id):
        """Show study mode selection for a deck."""
        from app.ui.gui.study_window import StudyOptionsDialog
        dialog = StudyOptionsDialog(deck_id, self.card_manager, self)
        if dialog.exec():
            study_mode, options = dialog.get_selection()
            self.start_study_session(deck_id, study_mode, options)

    def start_study_session(self, deck_id, study_mode, options=None):
        """Start a study session."""
        try:
            from app.ui.gui.study_window import StudyWindow
            session = self.session_manager.create_session(deck_id, study_mode)
            study_window = StudyWindow(session, self)
            study_window.exec()  # modal dialog so window layout is correct
        except Exception as e:
            QMessageBox.critical(self, "Study Error", f"Failed to start study session: {str(e)}")

    def quick_study(self, study_mode):
        """Quick study with deck selection."""
        decks = self.card_manager.get_all_decks()
        if not decks:
            QMessageBox.information(self, "No Decks", "Please create a deck first.")
            return

        deck_names = [f"{deck['name']} (ID: {deck['id']})" for deck in decks]
        deck_name, ok = QInputDialog.getItem(self, "Select Deck", "Choose deck to study:", deck_names, 0, False)

        if ok and deck_name:
            deck_id = int(deck_name.split("ID: ")[1].split(")")[0])
            self.start_study_session(deck_id, study_mode)

    def edit_deck(self, deck_id):
        """Open deck card management interface with search and bulk operations."""
        deck = self.card_manager.get_deck(deck_id)
        if not deck:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Manage Cards — {deck['name']}")
        dlg.resize(900, 650)
        v = QVBoxLayout(dlg)

        # Search/filter
        search_row = QHBoxLayout()
        search_label = QLabel("Search:")
        search_input = QLineEdit()
        search_row.addWidget(search_label)
        search_row.addWidget(search_input)
        v.addLayout(search_row)

        # Actions
        actions = QHBoxLayout()
        new_btn = QPushButton("New Card")
        new_btn.clicked.connect(lambda: self.open_card_editor(deck_id))
        refresh_btn = QPushButton("Refresh")

        # Bulk tag edit controls
        bulk_tag_label = QLabel("Bulk add tags:")
        bulk_tag_input = QLineEdit()
        bulk_apply_btn = QPushButton("Apply to Selected")

        actions.addWidget(new_btn)
        actions.addWidget(refresh_btn)
        actions.addStretch()
        actions.addWidget(bulk_tag_label)
        actions.addWidget(bulk_tag_input)
        actions.addWidget(bulk_apply_btn)
        v.addLayout(actions)

        # Card list (multi-select)
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.MultiSelection)
        v.addWidget(list_widget)

        def apply_filter():
            self.populate_card_list(deck_id, list_widget, search_input.text().strip())

        refresh_btn.clicked.connect(apply_filter)
        search_input.textChanged.connect(apply_filter)
        bulk_apply_btn.clicked.connect(lambda: self.bulk_apply_tags(deck_id, list_widget, bulk_tag_input.text()))

        apply_filter()

        # Buttons
        button_bar = QHBoxLayout()
        edit_btn = QPushButton("Edit Selected")
        edit_btn.clicked.connect(lambda: self.open_selected_card_editor(deck_id, list_widget))
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(lambda: self.delete_selected_cards(deck_id, list_widget))
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        button_bar.addWidget(edit_btn)
        button_bar.addWidget(delete_btn)
        button_bar.addStretch()
        button_bar.addWidget(close_btn)
        v.addLayout(button_bar)

        dlg.exec()

    def populate_card_list(self, deck_id, list_widget, query: str = ""):
        list_widget.clear()
        cards = self.card_manager.get_deck_cards(deck_id)
        query_l = query.lower()
        for c in cards:
            if query and (query_l not in c['front'].lower() and query_l not in c['back'].lower() and not any(query_l in t.lower() for t in c['tags'])):
                continue
            ctype = "Cloze" if "{{c" in c['front'] else "Basic"
            preview = c['front'][:80].replace('\n',' ')
            text = f"#{c['id']} — {ctype:6} — {preview}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, c['id'])
            list_widget.addItem(item)

    def bulk_apply_tags(self, deck_id, list_widget, tag_text: str):
        tags = [t.strip() for t in tag_text.split(',') if t.strip()]
        if not tags:
            return
        selected = list_widget.selectedItems()
        for item in selected:
            card_id = item.data(Qt.UserRole)
            card = self.card_manager.get_card(card_id)
            existing = card.get('tags', [])
            new_tags = sorted(set(existing + tags))
            self.card_manager.update_card(card_id, tags=new_tags)
        QMessageBox.information(self, "Tags Applied", f"Applied tags to {len(selected)} card(s).")

    def open_card_editor(self, deck_id, card=None):
        from app.ui.gui.card_editor import CardEditorDialog
        dlg = CardEditorDialog(self.card_manager, deck_id, card, self)
        if dlg.exec():
            self.refresh_decks()

    def open_selected_card_editor(self, deck_id, list_widget):
        items = list_widget.selectedItems()
        if not items:
            QMessageBox.information(self, "No Selection", "Please select a card to edit.")
            return
        # Edit the first selected card
        card_id = items[0].data(Qt.UserRole)
        card = self.card_manager.get_card(card_id)
        self.open_card_editor(deck_id, card)

    def delete_selected_cards(self, deck_id, list_widget):
        items = list_widget.selectedItems()
        if not items:
            return
        reply = QMessageBox.question(self, "Delete Cards", f"Delete {len(items)} selected card(s)?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            for item in items:
                card_id = item.data(Qt.UserRole)
                self.card_manager.delete_card(card_id)
            self.populate_card_list(deck_id, list_widget)
            self.refresh_decks()

    def delete_deck(self, deck_id):
        """Delete a deck with confirmation."""
        deck = self.card_manager.get_deck(deck_id)
        if not deck:
            return

        # Get card count for confirmation
        cards = self.card_manager.get_deck_cards(deck_id)
        card_count = len(cards)

        # Confirmation dialog
        if card_count > 0:
            message = f"Delete deck '{deck['name']}' and all {card_count} cards?\n\nThis action cannot be undone."
        else:
            message = f"Delete empty deck '{deck['name']}'?"

        reply = QMessageBox.question(
            self, "Delete Deck", message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Remove from layout manager
                self.layout_manager.remove_deck(deck_id)

                # Delete from database
                self.card_manager.delete_deck(deck_id)

                # Refresh display
                self.refresh_decks()

                QMessageBox.information(self, "Deck Deleted", f"Deck '{deck['name']}' has been deleted.")

            except Exception as e:
                QMessageBox.critical(self, "Delete Error", f"Failed to delete deck: {str(e)}")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About Plus Ultra Cards",
                         "Plus Ultra Cards v1.0\n\n"
                         "An Anki-Quizlet hybrid study application\n"
                         "with advanced spaced repetition capabilities.\n\n"
                         "Built with PySide6 and retro95.py")

    def closeEvent(self, event):
        """Handle application close."""
        self.card_manager.close()
        event.accept()

    def on_engine_selected(self):
        # Only one checked at a time
        sender = self.sender()
        for a in (self.action_engine_deeptutor, self.action_engine_sm2, self.action_engine_future):
            if a is not sender:
                a.setChecked(False)
        # Persist selection
        if sender is self.action_engine_deeptutor:
            self.card_manager.db.set_setting('srs_engine', 'deeptutor')
        elif sender is self.action_engine_sm2:
            self.card_manager.db.set_setting('srs_engine', 'sm2')
        else:
            self.card_manager.db.set_setting('srs_engine', 'future')

    def load_engine_selection(self):
        val = self.card_manager.db.get_setting('srs_engine') or 'deeptutor'
        self.action_engine_deeptutor.setChecked(val == 'deeptutor')
        self.action_engine_sm2.setChecked(val == 'sm2')
        self.action_engine_future.setChecked(val == 'future')

    def show_srs_settings_dialog(self):
        # Minimal placeholder dialog for now
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QFormLayout
        dlg = QDialog(self)
        dlg.setWindowTitle("SRS Settings")
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        env_combo = QComboBox()
        env_combo.addItems(['EFC', 'HLR', 'DASH'])
        env_combo.setCurrentText(self.card_manager.db.get_setting('dt_env') or 'EFC')
        form.addRow("Environment:", env_combo)
        reward_combo = QComboBox()
        reward_combo.addItems(['likelihood', 'log_likelihood'])
        reward_combo.setCurrentText(self.card_manager.db.get_setting('dt_reward') or 'likelihood')
        form.addRow("Reward:", reward_combo)
        layout.addLayout(form)
        btn = QPushButton("OK")
        btn.clicked.connect(dlg.accept)
        form.addRow(btn)
        dlg.exec()

    def show_metrics_dialog(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QListWidget
        from app.examples.metrics_visualizer import MetricsVisualizer
        dlg = QDialog(self)
        dlg.setWindowTitle("Metrics")
        layout = QVBoxLayout(dlg)
        decks = self.card_manager.get_all_decks()
        if not decks:
            QMessageBox.information(self, "No Decks", "Please create a deck first.")
            return
        deck_combo = QComboBox(dlg)
        id_by_idx = {}
        for i, deck in enumerate(decks):
            deck_combo.addItem(f"{deck['name']} (ID: {deck['id']})")
            id_by_idx[i] = deck['id']
        layout.addWidget(QLabel("Select deck:"))
        layout.addWidget(deck_combo)
        vis_list = QListWidget(dlg)
        items = [
            ("Per-item recall likelihood timeline", "Plot likelihood over time for a card/cloze"),
            ("Deck-level forgetting curve heatmap", "Heatmap of per-item likelihood decay"),
            ("Scheduler action distribution vs recall bands", "Distribution of items by likelihood bands"),
            ("Item mastery trajectories (cloze)", "Trajectories for clozes within a card"),
            ("Policy learning curve", "Episodic returns over training"),
            ("Delay vs recall likelihood", "Scatter with fitted decay"),
            ("Deck network graph", "Pyvis graph by content similarity"),
        ]
        for name, desc in items:
            vis_list.addItem(f"{name} — {desc}")
        layout.addWidget(vis_list)
        run_btn = QPushButton("Generate", dlg)
        layout.addWidget(run_btn)
        def run():
            deck_id = id_by_idx[deck_combo.currentIndex()]
            mv = MetricsVisualizer(self.card_manager.db)
            idx = vis_list.currentRow()
            if idx == -1:
                QMessageBox.information(self, "Select Visualization", "Please select a visualization.")
                return
            try:
                if idx == 0:
                    # Ask for card id
                    from PySide6.QtWidgets import QInputDialog
                    cid, ok = QInputDialog.getInt(self, "Card ID", "Enter card ID:")
                    if not ok:
                        return
                    fig = mv.viz_item_recall_timeline(deck_id, cid)
                    self.show_plotly_figure(fig, title="Recall Timeline")
                elif idx == 1:
                    fig = mv.viz_deck_forgetting_heatmap(deck_id)
                    self.show_plotly_figure(fig, title="Forgetting Heatmap")
                elif idx == 2:
                    fig = mv.viz_action_distribution(deck_id)
                    self.show_plotly_figure(fig, title="Action Distribution")
                elif idx == 3:
                    from PySide6.QtWidgets import QInputDialog
                    cid, ok = QInputDialog.getInt(self, "Card ID", "Enter card ID:")
                    if not ok:
                        return
                    fig = mv.viz_item_mastery_trajectories(deck_id, cid)
                    self.show_plotly_figure(fig, title="Mastery Trajectories")
                elif idx == 4:
                    fig = mv.viz_policy_learning_curve(deck_id)
                    self.show_plotly_figure(fig, title="Policy Learning Curve")
                elif idx == 5:
                    fig = mv.viz_delay_vs_likelihood(deck_id)
                    self.show_plotly_figure(fig, title="Delay vs Likelihood")
                elif idx == 6:
                    html = mv.viz_deck_network(deck_id)
                    QMessageBox.information(self, "Network Created", f"Network saved to {html}")
            except Exception as e:
                QMessageBox.critical(self, "Metrics Error", str(e))
        run_btn.clicked.connect(run)
        dlg.exec()

    def show_plotly_figure(self, fig, title="Plot"):
        # Render plotly in a temporary HTML and open QDialog with QWebEngineView if available
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        html = fig.to_html(include_plotlyjs='cdn', full_html=False)
        try:
            from PySide6.QtWebEngineWidgets import QWebEngineView
            view = QWebEngineView()
            view.setHtml(html)
            dlg = QDialog(self)
            dlg.setWindowTitle(title)
            v = QVBoxLayout(dlg)
            v.addWidget(view)
            dlg.resize(900, 600)
            dlg.exec()
        except Exception:
            # Fallback: write to temp file and notify
            import tempfile, os
            path = os.path.join(tempfile.gettempdir(), f"plot_{title.replace(' ','_')}.html")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
            QMessageBox.information(self, title, f"Saved plot to {path}")

    def import_from_source(self, source_type: str):
        """Import flashcards from various sources"""
        try:
            from app.flashcard_generation import create_flashcard_generator, convert_cards_format

            # Get source input based on type
            if source_type == 'pdf':
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Select PDF File", "", "PDF Files (*.pdf)"
                )
                if not file_path:
                    return
                source = file_path

            elif source_type == 'github':
                url, ok = QInputDialog.getText(
                    self, "GitHub Repository",
                    "Enter GitHub repository URL:"
                )
                if not ok or not url:
                    return
                source = url

            elif source_type == 'html':
                url, ok = QInputDialog.getText(
                    self, "HTML/URL Import",
                    "Enter URL to import:"
                )
                if not ok or not url:
                    return
                source = url

            elif source_type == 'epub':
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Select EPUB File", "", "EPUB Files (*.epub)"
                )
                if not file_path:
                    return
                source = file_path
            else:
                QMessageBox.warning(self, "Error", f"Unsupported source type: {source_type}")
                return

            # Get deck name
            deck_name, ok = QInputDialog.getText(
                self, "Deck Name",
                f"Enter name for new deck from {source_type}:"
            )
            if not ok or not deck_name:
                return

            # Show progress dialog
            progress = QProgressDialog("Processing content...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            try:
                # Create flashcard generator
                config = {
                    'use_ai': True,
                    'comprehensive': True,
                    'max_cards_per_section': 100
                }
                generator = create_flashcard_generator(config)

                progress.setValue(30)
                QApplication.processEvents()

                # Generate cards
                result = generator.process_content_comprehensive(source, source_type)

                progress.setValue(70)
                QApplication.processEvents()

                # Convert to plus_ultra format
                converted_cards = convert_cards_format(result['cards'])

                progress.setValue(90)
                QApplication.processEvents()

                # Create new deck
                deck_id = self.card_manager.create_deck(deck_name)

                # Add cards to deck
                for card_data in converted_cards:
                    self.card_manager.add_card(
                        deck_id=deck_id,
                        front=card_data['front'],
                        back=card_data['back'],
                        hint=card_data.get('hint', ''),
                        tags=card_data.get('tags', ''),
                        difficulty=card_data.get('difficulty', 2)
                    )

                progress.setValue(100)
                progress.close()

                # Refresh decks display
                self.refresh_decks()

                QMessageBox.information(
                    self, "Import Complete",
                    f"Successfully imported {len(converted_cards)} cards into deck '{deck_name}'"
                )

            except Exception as e:
                progress.close()
                QMessageBox.critical(self, "Import Error", f"Failed to import content:\n{str(e)}")

        except ImportError:
            QMessageBox.critical(
                self, "Import Error",
                "Flashcard generation system not available. Please check installation."
            )

    def open_terminal(self):
        """Open terminal with flashcard generation CLI"""
        import subprocess
        import sys
        import os

        try:
            # Get the path to the CLI script
            app_dir = Path(__file__).parent.parent.parent
            cli_path = app_dir / "flashcard_generation" / "cli" / "enhanced_cli.py"

            # Check if CLI exists, if not use a fallback
            if not cli_path.exists():
                # Fallback to the original CLI in the root directory
                cli_path = Path(__file__).parent.parent.parent.parent / "cli_enhanced.py"

            if not cli_path.exists():
                QMessageBox.warning(
                    self, "Terminal Error",
                    "CLI script not found. Please ensure the flashcard generation system is properly installed."
                )
                return

            # Launch terminal based on platform
            if sys.platform == "win32":
                # Windows
                subprocess.Popen(
                    f'start cmd /k "cd /d {cli_path.parent} && python {cli_path.name}"',
                    shell=True
                )
            elif sys.platform == "darwin":
                # macOS
                subprocess.Popen([
                    'open', '-a', 'Terminal',
                    f'python "{cli_path}"'
                ])
            else:
                # Linux
                subprocess.Popen([
                    'gnome-terminal', '--',
                    'python', str(cli_path)
                ])

            QMessageBox.information(
                self, "Terminal Opened",
                "Terminal window opened with flashcard generation CLI."
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Terminal Error",
                f"Failed to open terminal:\n{str(e)}"
            )

    def open_api_key_dialog(self):
        """Open API key and AI configuration dialog"""
        try:
            from app.ui.gui.api_key_dialog import APIKeyDialog

            dialog = APIKeyDialog(self)
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(
                self, "Configuration Error",
                f"Failed to open API key dialog:\n{str(e)}"
            )


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    apply_win95_theme(app, base_point_size=10)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

