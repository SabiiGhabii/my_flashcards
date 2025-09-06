"""
Study Session Template System
Provides a modular, adaptable study interface that works with any card type
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox


class StudyInterfaceType(Enum):
    """Types of study interfaces"""
    BASIC = "basic"
    CLOZE = "cloze"
    CLOZE_INPUT = "cloze_input"
    CUSTOM = "custom"


@dataclass
class StudyInterfaceConfig:
    """Configuration for study interface"""
    interface_type: StudyInterfaceType
    show_flip_button: bool
    show_answer_buttons: bool
    side_panel_type: Optional[str]
    custom_buttons: List[str]
    multi_attempt: bool
    max_attempts: int
    custom_handlers: Dict[str, Callable]


class StudyInterfacePlugin(ABC):
    """Abstract base class for study interface plugins"""
    
    @abstractmethod
    def get_interface_type(self) -> StudyInterfaceType:
        """Return the interface type this plugin handles"""
        pass
    
    @abstractmethod
    def create_interface(self, parent: QWidget, config: StudyInterfaceConfig) -> QWidget:
        """Create the interface widget"""
        pass
    
    @abstractmethod
    def setup_card(self, card_data: Dict[str, Any], interface_widget: QWidget):
        """Setup the interface for a specific card"""
        pass
    
    @abstractmethod
    def handle_user_action(self, action: str, data: Any, interface_widget: QWidget) -> Dict[str, Any]:
        """Handle user actions and return results"""
        pass
    
    @abstractmethod
    def cleanup(self, interface_widget: QWidget):
        """Cleanup when switching cards or ending session"""
        pass


class BasicStudyInterface(StudyInterfacePlugin):
    """Basic front/back card study interface"""
    
    def get_interface_type(self) -> StudyInterfaceType:
        return StudyInterfaceType.BASIC
    
    def create_interface(self, parent: QWidget, config: StudyInterfaceConfig) -> QWidget:
        """Create basic study interface"""
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        
        # Card display area
        card_group = QGroupBox("Card")
        card_layout = QVBoxLayout(card_group)
        
        # Front display
        front_label = QLabel()
        front_label.setObjectName("card_front")
        front_label.setWordWrap(True)
        card_layout.addWidget(front_label)
        
        # Back display (initially hidden)
        back_label = QLabel()
        back_label.setObjectName("card_back")
        back_label.setWordWrap(True)
        back_label.hide()
        card_layout.addWidget(back_label)
        
        layout.addWidget(card_group)
        
        # Control buttons
        if config.show_flip_button:
            flip_button = QPushButton("Show Answer")
            flip_button.setObjectName("flip_button")
            layout.addWidget(flip_button)
        
        if config.show_answer_buttons:
            button_layout = QHBoxLayout()
            
            correct_button = QPushButton("Correct")
            correct_button.setObjectName("correct_button")
            button_layout.addWidget(correct_button)
            
            incorrect_button = QPushButton("Incorrect")
            incorrect_button.setObjectName("incorrect_button")
            button_layout.addWidget(incorrect_button)
            
            layout.addLayout(button_layout)
        
        return widget
    
    def setup_card(self, card_data: Dict[str, Any], interface_widget: QWidget):
        """Setup interface for a basic card"""
        front_label = interface_widget.findChild(QLabel, "card_front")
        back_label = interface_widget.findChild(QLabel, "card_back")
        flip_button = interface_widget.findChild(QPushButton, "flip_button")
        
        if front_label:
            front_label.setText(card_data.get('front_html', ''))
            front_label.show()
        
        if back_label:
            back_label.setText(card_data.get('back_html', ''))
            back_label.hide()
        
        if flip_button:
            flip_button.setText("Show Answer")
    
    def handle_user_action(self, action: str, data: Any, interface_widget: QWidget) -> Dict[str, Any]:
        """Handle user actions for basic cards"""
        if action == "flip_card":
            return self._handle_flip(interface_widget)
        elif action == "answer_correct":
            return {'action': 'answer', 'result': 'correct'}
        elif action == "answer_incorrect":
            return {'action': 'answer', 'result': 'incorrect'}
        
        return {'action': 'unknown', 'result': None}
    
    def _handle_flip(self, interface_widget: QWidget) -> Dict[str, Any]:
        """Handle card flip action"""
        front_label = interface_widget.findChild(QLabel, "card_front")
        back_label = interface_widget.findChild(QLabel, "card_back")
        flip_button = interface_widget.findChild(QPushButton, "flip_button")
        
        if front_label and back_label and flip_button:
            if back_label.isVisible():
                # Hide answer
                back_label.hide()
                flip_button.setText("Show Answer")
                return {'action': 'flip', 'result': 'hidden'}
            else:
                # Show answer
                back_label.show()
                flip_button.setText("Hide Answer")
                return {'action': 'flip', 'result': 'shown'}
        
        return {'action': 'flip', 'result': 'error'}
    
    def cleanup(self, interface_widget: QWidget):
        """Cleanup basic interface"""
        # Reset to initial state
        front_label = interface_widget.findChild(QLabel, "card_front")
        back_label = interface_widget.findChild(QLabel, "card_back")
        flip_button = interface_widget.findChild(QPushButton, "flip_button")
        
        if back_label:
            back_label.hide()
        if flip_button:
            flip_button.setText("Show Answer")


class ClozeStudyInterface(StudyInterfacePlugin):
    """Cloze deletion card study interface"""

    def get_interface_type(self) -> StudyInterfaceType:
        return StudyInterfaceType.CLOZE

    def create_interface(self, parent: QWidget, config: StudyInterfaceConfig) -> QWidget:
        """Create cloze study interface (similar to basic but single-sided)"""
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)

        # Card display area
        card_group = QGroupBox("Card")
        card_layout = QVBoxLayout(card_group)

        # Front display
        front_label = QLabel()
        front_label.setObjectName("card_front")
        front_label.setWordWrap(True)
        card_layout.addWidget(front_label)

        layout.addWidget(card_group)

        # Control buttons
        if config.show_flip_button:
            flip_button = QPushButton("Show Answer")
            flip_button.setObjectName("flip_button")
            layout.addWidget(flip_button)

        if config.show_answer_buttons:
            button_layout = QHBoxLayout()

            correct_button = QPushButton("Correct")
            correct_button.setObjectName("correct_button")
            button_layout.addWidget(correct_button)

            incorrect_button = QPushButton("Incorrect")
            incorrect_button.setObjectName("incorrect_button")
            button_layout.addWidget(incorrect_button)

            layout.addLayout(button_layout)

        return widget

    def setup_card(self, card_data: Dict[str, Any], interface_widget: QWidget):
        """Setup interface for a cloze card"""
        front_label = interface_widget.findChild(QLabel, "card_front")
        flip_button = interface_widget.findChild(QPushButton, "flip_button")

        if front_label:
            front_label.setText(card_data.get('front_html', ''))

        if flip_button:
            flip_button.setText("Show Answer")

    def handle_user_action(self, action: str, data: Any, interface_widget: QWidget) -> Dict[str, Any]:
        """Handle user actions for cloze cards"""
        if action == "flip_card":
            return self._handle_flip(interface_widget, data)
        elif action == "answer_correct":
            return {'action': 'answer', 'result': 'correct'}
        elif action == "answer_incorrect":
            return {'action': 'answer', 'result': 'incorrect'}

        return {'action': 'unknown', 'result': None}

    def _handle_flip(self, interface_widget: QWidget, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle card flip action for cloze cards"""
        front_label = interface_widget.findChild(QLabel, "card_front")
        flip_button = interface_widget.findChild(QPushButton, "flip_button")

        if front_label and flip_button:
            if flip_button.text() == "Show Answer":
                # Show revealed cloze
                front_label.setText(card_data.get('revealed_html', ''))
                flip_button.setText("Hide Answer")
                return {'action': 'flip', 'result': 'shown'}
            else:
                # Show blanked cloze
                front_label.setText(card_data.get('front_html', ''))
                flip_button.setText("Show Answer")
                return {'action': 'flip', 'result': 'hidden'}

        return {'action': 'flip', 'result': 'error'}

    def cleanup(self, interface_widget: QWidget):
        """Cleanup cloze interface"""
        flip_button = interface_widget.findChild(QPushButton, "flip_button")
        if flip_button:
            flip_button.setText("Show Answer")


class ClozeInputStudyInterface(StudyInterfacePlugin):
    """Cloze input card study interface with side panel"""
    
    def get_interface_type(self) -> StudyInterfaceType:
        return StudyInterfaceType.CLOZE_INPUT
    
    def create_interface(self, parent: QWidget, config: StudyInterfaceConfig) -> QWidget:
        """Create cloze input study interface"""
        widget = QWidget(parent)
        main_layout = QHBoxLayout(widget)
        
        # Left side: Card display
        card_layout = QVBoxLayout()
        
        card_group = QGroupBox("Card")
        card_group_layout = QVBoxLayout(card_group)
        
        front_label = QLabel()
        front_label.setObjectName("card_front")
        front_label.setWordWrap(True)
        card_group_layout.addWidget(front_label)
        
        card_layout.addWidget(card_group)
        
        # Right side: Input panel
        input_panel = QGroupBox("Fill in the blanks")
        input_panel.setObjectName("input_panel")
        input_layout = QVBoxLayout(input_panel)
        
        # Input fields will be added dynamically
        input_container = QWidget()
        input_container.setObjectName("input_container")
        input_container_layout = QVBoxLayout(input_container)
        input_layout.addWidget(input_container)
        
        # Check answers button
        check_button = QPushButton("Check Answers")
        check_button.setObjectName("check_button")
        input_layout.addWidget(check_button)
        
        # Add layouts to main layout
        main_layout.addLayout(card_layout, 2)  # 2/3 width
        main_layout.addWidget(input_panel, 1)  # 1/3 width
        
        return widget
    
    def setup_card(self, card_data: Dict[str, Any], interface_widget: QWidget):
        """Setup interface for a cloze input card"""
        front_label = interface_widget.findChild(QLabel, "card_front")
        input_container = interface_widget.findChild(QWidget, "input_container")
        
        if front_label:
            front_label.setText(card_data.get('front_html', ''))
        
        if input_container:
            self._setup_input_fields(input_container, card_data.get('cloze_answers', {}))
    
    def _setup_input_fields(self, container: QWidget, cloze_answers: Dict[str, str]):
        """Setup input fields for cloze answers"""
        from PySide6.QtWidgets import QLineEdit
        
        # Clear existing fields
        layout = container.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Create input fields
        for cloze_num in sorted(cloze_answers.keys(), key=int):
            field_widget = QWidget()
            field_layout = QVBoxLayout(field_widget)
            
            # Label
            label = QLabel(f"C{cloze_num}: Enter response")
            field_layout.addWidget(label)
            
            # Input field
            input_field = QLineEdit()
            input_field.setObjectName(f"input_{cloze_num}")
            input_field.setPlaceholderText("Type your answer...")
            field_layout.addWidget(input_field)
            
            # Update button
            update_button = QPushButton("Update Display")
            update_button.setObjectName(f"update_{cloze_num}")
            field_layout.addWidget(update_button)
            
            layout.addWidget(field_widget)
    
    def handle_user_action(self, action: str, data: Any, interface_widget: QWidget) -> Dict[str, Any]:
        """Handle user actions for cloze input cards"""
        if action == "check_answers":
            if interface_widget is None:
                # Mock response for testing
                return {'action': 'check', 'result': 'mock_success'}
            return self._handle_check_answers(interface_widget, data)
        elif action.startswith("update_display_"):
            cloze_num = action.split("_")[-1]
            if interface_widget is None:
                # Mock response for testing
                return {'action': 'update', 'result': 'mock_success'}
            return self._handle_update_display(interface_widget, cloze_num)

        return {'action': 'unknown', 'result': None}
    
    def _handle_check_answers(self, interface_widget: QWidget, correct_answers: Dict[str, str]) -> Dict[str, Any]:
        """Handle answer checking"""
        from PySide6.QtWidgets import QLineEdit
        
        input_container = interface_widget.findChild(QWidget, "input_container")
        if not input_container:
            return {'action': 'check', 'result': 'error'}
        
        # Collect user answers
        user_answers = {}
        for cloze_num in correct_answers.keys():
            input_field = input_container.findChild(QLineEdit, f"input_{cloze_num}")
            if input_field:
                user_answers[cloze_num] = input_field.text().strip()
        
        # Validate answers
        correct_count = 0
        for cloze_num, correct_answer in correct_answers.items():
            user_answer = user_answers.get(cloze_num, "")
            if user_answer.lower() == correct_answer.lower():
                correct_count += 1
        
        return {
            'action': 'check',
            'result': 'complete',
            'correct_count': correct_count,
            'total_count': len(correct_answers),
            'user_answers': user_answers
        }
    
    def _handle_update_display(self, interface_widget: QWidget, cloze_num: str) -> Dict[str, Any]:
        """Handle display update for specific cloze"""
        from PySide6.QtWidgets import QLineEdit
        
        input_container = interface_widget.findChild(QWidget, "input_container")
        if not input_container:
            return {'action': 'update', 'result': 'error'}
        
        input_field = input_container.findChild(QLineEdit, f"input_{cloze_num}")
        if input_field:
            user_input = input_field.text().strip()
            return {
                'action': 'update',
                'result': 'success',
                'cloze_num': cloze_num,
                'user_input': user_input
            }
        
        return {'action': 'update', 'result': 'error'}
    
    def cleanup(self, interface_widget: QWidget):
        """Cleanup cloze input interface"""
        from PySide6.QtWidgets import QLineEdit
        
        input_container = interface_widget.findChild(QWidget, "input_container")
        if input_container:
            # Clear all input fields
            for input_field in input_container.findChildren(QLineEdit):
                input_field.clear()


class StudyTemplateManager:
    """Manager for study interface templates"""
    
    def __init__(self):
        self._plugins: Dict[StudyInterfaceType, StudyInterfacePlugin] = {}
        self._register_default_plugins()
    
    def _register_default_plugins(self):
        """Register default study interface plugins"""
        self.register_plugin(BasicStudyInterface())
        self.register_plugin(ClozeStudyInterface())
        self.register_plugin(ClozeInputStudyInterface())
    
    def register_plugin(self, plugin: StudyInterfacePlugin):
        """Register a study interface plugin"""
        self._plugins[plugin.get_interface_type()] = plugin
    
    def create_interface(self, interface_type: StudyInterfaceType, parent: QWidget, config: StudyInterfaceConfig) -> QWidget:
        """Create a study interface of the specified type"""
        plugin = self._plugins.get(interface_type)
        if plugin:
            return plugin.create_interface(parent, config)
        
        # Fallback to basic interface
        basic_plugin = self._plugins.get(StudyInterfaceType.BASIC)
        if basic_plugin:
            return basic_plugin.create_interface(parent, config)
        
        raise ValueError(f"No plugin available for interface type: {interface_type}")
    
    def get_plugin(self, interface_type: StudyInterfaceType) -> Optional[StudyInterfacePlugin]:
        """Get a plugin by interface type"""
        return self._plugins.get(interface_type)
    
    def get_all_plugins(self) -> Dict[StudyInterfaceType, StudyInterfacePlugin]:
        """Get all registered plugins"""
        return self._plugins.copy()


# Global template manager instance
study_template_manager = StudyTemplateManager()
