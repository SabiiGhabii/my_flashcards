"""
API Key Management Dialog

This dialog allows users to manage API keys for various AI services
including Gemini, HuggingFace, OpenAI, and other services.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QTabWidget, QWidget, QTextEdit, QGroupBox,
    QCheckBox, QSpinBox, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt

from app.ui.font_loader import load_win95_font


class APIKeyDialog(QDialog):
    """Dialog for managing API keys and AI service configurations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Keys & AI Configuration")
        self.setModal(True)
        self.resize(600, 500)
        
        # Load existing configuration
        self.config_file = Path("config/api_keys.json")
        self.config = self.load_config()
        
        self.setup_ui()
        self.load_values()
        
        # Apply retro styling
        self.apply_retro_styling()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_gemini_tab()
        self.create_huggingface_tab()
        self.create_openai_tab()
        self.create_general_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_button = QPushButton("Test Connections")
        self.test_button.clicked.connect(self.test_connections)
        button_layout.addWidget(self.test_button)
        
        button_layout.addStretch()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def create_gemini_tab(self):
        """Create Gemini API configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # API Key section
        api_group = QGroupBox("Gemini API Configuration")
        api_layout = QFormLayout(api_group)
        
        self.gemini_api_key = QLineEdit()
        self.gemini_api_key.setEchoMode(QLineEdit.Password)
        self.gemini_api_key.setPlaceholderText("Enter your Gemini API key...")
        api_layout.addRow("API Key:", self.gemini_api_key)
        
        self.gemini_model = QComboBox()
        self.gemini_model.addItems(["gemini-pro", "gemini-pro-vision", "gemini-1.5-pro"])
        api_layout.addRow("Model:", self.gemini_model)
        
        self.gemini_temperature = QSpinBox()
        self.gemini_temperature.setRange(0, 100)
        self.gemini_temperature.setValue(70)
        self.gemini_temperature.setSuffix("%")
        api_layout.addRow("Temperature:", self.gemini_temperature)
        
        self.gemini_max_tokens = QSpinBox()
        self.gemini_max_tokens.setRange(100, 8192)
        self.gemini_max_tokens.setValue(2048)
        api_layout.addRow("Max Tokens:", self.gemini_max_tokens)
        
        layout.addWidget(api_group)
        
        # Usage section
        usage_group = QGroupBox("Usage Settings")
        usage_layout = QFormLayout(usage_group)
        
        self.gemini_enabled = QCheckBox("Enable Gemini for card generation")
        usage_layout.addRow(self.gemini_enabled)
        
        self.gemini_comprehensive = QCheckBox("Use for comprehensive processing")
        usage_layout.addRow(self.gemini_comprehensive)
        
        layout.addWidget(usage_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Gemini")
    
    def create_huggingface_tab(self):
        """Create HuggingFace configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # API Key section
        api_group = QGroupBox("HuggingFace Configuration")
        api_layout = QFormLayout(api_group)
        
        self.hf_api_key = QLineEdit()
        self.hf_api_key.setEchoMode(QLineEdit.Password)
        self.hf_api_key.setPlaceholderText("Enter your HuggingFace API token...")
        api_layout.addRow("API Token:", self.hf_api_key)
        
        layout.addWidget(api_group)
        
        # Model selection
        models_group = QGroupBox("Model Selection")
        models_layout = QFormLayout(models_group)
        
        self.hf_text_model = QComboBox()
        self.hf_text_model.setEditable(True)
        self.hf_text_model.addItems([
            "microsoft/DialoGPT-medium",
            "facebook/blenderbot-400M-distill",
            "microsoft/DialoGPT-small",
            "HuggingFaceH4/zephyr-7b-beta",
            "mistralai/Mistral-7B-Instruct-v0.1"
        ])
        models_layout.addRow("Text Generation Model:", self.hf_text_model)
        
        self.hf_embedding_model = QComboBox()
        self.hf_embedding_model.setEditable(True)
        self.hf_embedding_model.addItems([
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/all-mpnet-base-v2",
            "sentence-transformers/paraphrase-MiniLM-L6-v2"
        ])
        models_layout.addRow("Embedding Model:", self.hf_embedding_model)
        
        layout.addWidget(models_group)
        
        # Usage settings
        usage_group = QGroupBox("Usage Settings")
        usage_layout = QFormLayout(usage_group)
        
        self.hf_enabled = QCheckBox("Enable HuggingFace models")
        usage_layout.addRow(self.hf_enabled)
        
        self.hf_local_inference = QCheckBox("Use local inference (slower but free)")
        usage_layout.addRow(self.hf_local_inference)
        
        self.hf_card_enhancement = QCheckBox("Use for card content enhancement")
        usage_layout.addRow(self.hf_card_enhancement)
        
        self.hf_similarity_detection = QCheckBox("Use for duplicate detection")
        usage_layout.addRow(self.hf_similarity_detection)
        
        layout.addWidget(usage_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "HuggingFace")
    
    def create_openai_tab(self):
        """Create OpenAI configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # API Key section
        api_group = QGroupBox("OpenAI Configuration")
        api_layout = QFormLayout(api_group)
        
        self.openai_api_key = QLineEdit()
        self.openai_api_key.setEchoMode(QLineEdit.Password)
        self.openai_api_key.setPlaceholderText("Enter your OpenAI API key...")
        api_layout.addRow("API Key:", self.openai_api_key)
        
        self.openai_model = QComboBox()
        self.openai_model.addItems(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"])
        api_layout.addRow("Model:", self.openai_model)
        
        self.openai_temperature = QSpinBox()
        self.openai_temperature.setRange(0, 100)
        self.openai_temperature.setValue(70)
        self.openai_temperature.setSuffix("%")
        api_layout.addRow("Temperature:", self.openai_temperature)
        
        layout.addWidget(api_group)
        
        # Usage settings
        usage_group = QGroupBox("Usage Settings")
        usage_layout = QFormLayout(usage_group)
        
        self.openai_enabled = QCheckBox("Enable OpenAI for card generation")
        usage_layout.addRow(self.openai_enabled)
        
        layout.addWidget(usage_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "OpenAI")
    
    def create_general_tab(self):
        """Create general AI settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # General settings
        general_group = QGroupBox("General AI Settings")
        general_layout = QFormLayout(general_group)
        
        self.ai_priority = QComboBox()
        self.ai_priority.addItems(["Gemini", "HuggingFace", "OpenAI", "Local Only"])
        general_layout.addRow("Primary AI Service:", self.ai_priority)
        
        self.fallback_enabled = QCheckBox("Enable fallback to other services")
        general_layout.addRow(self.fallback_enabled)
        
        self.rate_limit_delay = QSpinBox()
        self.rate_limit_delay.setRange(0, 10)
        self.rate_limit_delay.setValue(1)
        self.rate_limit_delay.setSuffix(" seconds")
        general_layout.addRow("Rate Limit Delay:", self.rate_limit_delay)
        
        layout.addWidget(general_group)
        
        # Cache settings
        cache_group = QGroupBox("Cache Settings")
        cache_layout = QFormLayout(cache_group)
        
        self.enable_cache = QCheckBox("Enable AI response caching")
        cache_layout.addRow(self.enable_cache)
        
        self.cache_duration = QSpinBox()
        self.cache_duration.setRange(1, 30)
        self.cache_duration.setValue(7)
        self.cache_duration.setSuffix(" days")
        cache_layout.addRow("Cache Duration:", self.cache_duration)
        
        layout.addWidget(cache_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "General")
    
    def apply_retro_styling(self):
        """Apply retro Win95 styling"""
        load_win95_font()
        # Apply retro color scheme
        self.setStyleSheet("""
            QDialog {
                background-color: #c0c0c0;
                color: #000000;
            }
            QTabWidget::pane {
                border: 2px inset #c0c0c0;
                background-color: #c0c0c0;
            }
            QTabBar::tab {
                background-color: #c0c0c0;
                border: 2px outset #c0c0c0;
                padding: 4px 8px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                border: 2px inset #c0c0c0;
            }
            QGroupBox {
                border: 2px inset #c0c0c0;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #c0c0c0;
                border: 2px outset #c0c0c0;
                padding: 4px 8px;
                min-width: 60px;
            }
            QPushButton:pressed {
                border: 2px inset #c0c0c0;
            }
            QLineEdit, QComboBox, QSpinBox {
                border: 2px inset #c0c0c0;
                padding: 2px;
                background-color: white;
            }
        """)
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default configuration
        return {
            "gemini": {
                "api_key": "",
                "model": "gemini-pro",
                "temperature": 0.7,
                "max_tokens": 2048,
                "enabled": False,
                "comprehensive": False
            },
            "huggingface": {
                "api_key": "",
                "text_model": "microsoft/DialoGPT-medium",
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "enabled": False,
                "local_inference": True,
                "card_enhancement": False,
                "similarity_detection": False
            },
            "openai": {
                "api_key": "",
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "enabled": False
            },
            "general": {
                "ai_priority": "Gemini",
                "fallback_enabled": True,
                "rate_limit_delay": 1,
                "enable_cache": True,
                "cache_duration": 7
            }
        }
    
    def load_values(self):
        """Load values from configuration into UI"""
        # Gemini
        gemini = self.config.get("gemini", {})
        self.gemini_api_key.setText(gemini.get("api_key", ""))
        self.gemini_model.setCurrentText(gemini.get("model", "gemini-pro"))
        self.gemini_temperature.setValue(int(gemini.get("temperature", 0.7) * 100))
        self.gemini_max_tokens.setValue(gemini.get("max_tokens", 2048))
        self.gemini_enabled.setChecked(gemini.get("enabled", False))
        self.gemini_comprehensive.setChecked(gemini.get("comprehensive", False))
        
        # HuggingFace
        hf = self.config.get("huggingface", {})
        self.hf_api_key.setText(hf.get("api_key", ""))
        self.hf_text_model.setCurrentText(hf.get("text_model", "microsoft/DialoGPT-medium"))
        self.hf_embedding_model.setCurrentText(hf.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2"))
        self.hf_enabled.setChecked(hf.get("enabled", False))
        self.hf_local_inference.setChecked(hf.get("local_inference", True))
        self.hf_card_enhancement.setChecked(hf.get("card_enhancement", False))
        self.hf_similarity_detection.setChecked(hf.get("similarity_detection", False))
        
        # OpenAI
        openai = self.config.get("openai", {})
        self.openai_api_key.setText(openai.get("api_key", ""))
        self.openai_model.setCurrentText(openai.get("model", "gpt-3.5-turbo"))
        self.openai_temperature.setValue(int(openai.get("temperature", 0.7) * 100))
        self.openai_enabled.setChecked(openai.get("enabled", False))
        
        # General
        general = self.config.get("general", {})
        self.ai_priority.setCurrentText(general.get("ai_priority", "Gemini"))
        self.fallback_enabled.setChecked(general.get("fallback_enabled", True))
        self.rate_limit_delay.setValue(general.get("rate_limit_delay", 1))
        self.enable_cache.setChecked(general.get("enable_cache", True))
        self.cache_duration.setValue(general.get("cache_duration", 7))
    
    def save_config(self):
        """Save configuration to file"""
        # Update configuration from UI
        self.config["gemini"] = {
            "api_key": self.gemini_api_key.text(),
            "model": self.gemini_model.currentText(),
            "temperature": self.gemini_temperature.value() / 100.0,
            "max_tokens": self.gemini_max_tokens.value(),
            "enabled": self.gemini_enabled.isChecked(),
            "comprehensive": self.gemini_comprehensive.isChecked()
        }
        
        self.config["huggingface"] = {
            "api_key": self.hf_api_key.text(),
            "text_model": self.hf_text_model.currentText(),
            "embedding_model": self.hf_embedding_model.currentText(),
            "enabled": self.hf_enabled.isChecked(),
            "local_inference": self.hf_local_inference.isChecked(),
            "card_enhancement": self.hf_card_enhancement.isChecked(),
            "similarity_detection": self.hf_similarity_detection.isChecked()
        }
        
        self.config["openai"] = {
            "api_key": self.openai_api_key.text(),
            "model": self.openai_model.currentText(),
            "temperature": self.openai_temperature.value() / 100.0,
            "enabled": self.openai_enabled.isChecked()
        }
        
        self.config["general"] = {
            "ai_priority": self.ai_priority.currentText(),
            "fallback_enabled": self.fallback_enabled.isChecked(),
            "rate_limit_delay": self.rate_limit_delay.value(),
            "enable_cache": self.enable_cache.isChecked(),
            "cache_duration": self.cache_duration.value()
        }
        
        # Ensure config directory exists
        self.config_file.parent.mkdir(exist_ok=True)
        
        # Save to file
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration:\n{e}")
    
    def test_connections(self):
        """Test API connections"""
        results = []
        
        # Test Gemini
        if self.gemini_enabled.isChecked() and self.gemini_api_key.text():
            try:
                # This would test the actual Gemini connection
                results.append("✓ Gemini: Connection test would go here")
            except Exception as e:
                results.append(f"✗ Gemini: {e}")
        
        # Test HuggingFace
        if self.hf_enabled.isChecked():
            try:
                # This would test the actual HuggingFace connection
                results.append("✓ HuggingFace: Connection test would go here")
            except Exception as e:
                results.append(f"✗ HuggingFace: {e}")
        
        # Test OpenAI
        if self.openai_enabled.isChecked() and self.openai_api_key.text():
            try:
                # This would test the actual OpenAI connection
                results.append("✓ OpenAI: Connection test would go here")
            except Exception as e:
                results.append(f"✗ OpenAI: {e}")
        
        if not results:
            results.append("No services enabled for testing.")
        
        QMessageBox.information(self, "Connection Test Results", "\n".join(results))
