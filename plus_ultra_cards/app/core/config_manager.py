"""
Centralized Configuration Manager for Plus Ultra Cards
Replaces scattered JSON configuration files with a unified system.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime


class ConfigManager:
    """Centralized configuration management system."""
    
    def __init__(self, config_file: str = "data/config.json"):
        self.config_file = config_file
        self.config_data = {}
        self._default_config = self._get_default_config()
        self.load_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            # Application settings
            "app": {
                "name": "Plus Ultra Cards",
                "version": "1.0.0",
                "organization": "Plus Ultra Cards",
                "auto_save": True,
                "auto_backup": True,
                "backup_interval_days": 7,
                "session_timeout_minutes": 60
            },
            
            # Theme and UI settings
            "theme": {
                "current_theme": "neobrutalist",
                "retro95_enabled": True,
                "font_size": 10,
                "neobrutalist_colors": {
                    "primary": "#FF0000",
                    "secondary": "#0000FF", 
                    "accent": "#00FFFF",
                    "background": "#FFFFFF"
                },
                "card_flip_animation": True,
                "show_statistics": True
            },
            
            # SRS Engine settings
            "srs": {
                "engine": "deeptutor",  # "deeptutor" or "sm2"
                "deeptutor_model": "EFC",  # "EFC", "HLR", or "DASH"
                "deeptutor_reward_func": "log_likelihood",
                "training_timesteps": 1000,
                "training_frequency": 10,  # train every N reviews
                "sm2_initial_interval": 1,
                "sm2_initial_easiness": 2.5
            },
            
            # Study settings
            "study": {
                "default_mode": "cram",
                "daily_goal": 20,
                "study_reminders": True,
                "sound_enabled": False,
                "show_hints": True,
                "auto_advance": False,
                "review_batch_size": 20
            },
            
            # Deck layout settings
            "layout": {
                "grid_columns": 4,
                "default_span": [1, 1],
                "deck_spans": {}  # deck_id -> [row_span, col_span]
            },
            
            # Card templates
            "templates": {
                "default_template": "Basic",
                "custom_templates": {},
                "code_highlighting": True,
                "preserve_formatting": True
            },
            
            # Import/Export settings
            "import_export": {
                "csv_delimiter": ",",
                "csv_encoding": "utf-8",
                "export_include_stats": True,
                "backup_before_import": True
            },
            
            # Database settings
            "database": {
                "path": "data/cards.db",
                "backup_path": "data/backups",
                "vacuum_frequency_days": 30,
                "max_backup_count": 10
            },
            
            # Advanced settings
            "advanced": {
                "debug_mode": False,
                "log_level": "INFO",
                "performance_monitoring": False,
                "experimental_features": False
            }
        }
    
    def load_config(self):
        """Load configuration from file, merging with defaults."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config_data = self._merge_configs(self._default_config, loaded_config)
            else:
                self.config_data = self._default_config.copy()
                self.save_config()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to load config file: {e}")
            self.config_data = self._default_config.copy()
            self.save_config()
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Add metadata
            config_with_meta = self.config_data.copy()
            config_with_meta["_metadata"] = {
                "last_updated": datetime.now().isoformat(),
                "config_version": "1.0"
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_with_meta, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded config with defaults."""
        result = default.copy()
        
        for key, value in loaded.items():
            if key.startswith('_'):  # Skip metadata
                continue
                
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        Example: get("theme.neobrutalist_colors.primary")
        """
        keys = key_path.split('.')
        current = self.config_data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any, save: bool = True):
        """
        Set configuration value using dot notation.
        Example: set("theme.font_size", 12)
        """
        keys = key_path.split('.')
        current = self.config_data
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the value
        current[keys[-1]] = value
        
        if save:
            self.save_config()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self.config_data.get(section, {})
    
    def update_section(self, section: str, updates: Dict[str, Any], save: bool = True):
        """Update multiple values in a configuration section."""
        if section not in self.config_data:
            self.config_data[section] = {}
        
        self.config_data[section].update(updates)
        
        if save:
            self.save_config()
    
    def reset_to_defaults(self, section: Optional[str] = None):
        """Reset configuration to defaults (optionally just one section)."""
        if section:
            if section in self._default_config:
                self.config_data[section] = self._default_config[section].copy()
        else:
            self.config_data = self._default_config.copy()
        
        self.save_config()
    
    def migrate_from_legacy_files(self):
        """Migrate settings from legacy configuration files."""
        migrations_performed = []
        
        # Migrate theme_config.json
        theme_file = "data/theme_config.json"
        if os.path.exists(theme_file):
            try:
                with open(theme_file, 'r') as f:
                    theme_data = json.load(f)
                
                if "current_theme" in theme_data:
                    self.set("theme.current_theme", theme_data["current_theme"], save=False)
                
                if "neobrutalist_colors" in theme_data:
                    self.set("theme.neobrutalist_colors", theme_data["neobrutalist_colors"], save=False)
                
                migrations_performed.append("theme_config.json")
            except Exception as e:
                print(f"Warning: Failed to migrate theme_config.json: {e}")
        
        # Migrate deck_layout.json
        layout_file = "data/deck_layout.json"
        if os.path.exists(layout_file):
            try:
                with open(layout_file, 'r') as f:
                    layout_data = json.load(f)
                
                if "grid_columns" in layout_data:
                    self.set("layout.grid_columns", layout_data["grid_columns"], save=False)
                
                if "default_span" in layout_data:
                    self.set("layout.default_span", layout_data["default_span"], save=False)
                
                if "deck_spans" in layout_data:
                    self.set("layout.deck_spans", layout_data["deck_spans"], save=False)
                
                migrations_performed.append("deck_layout.json")
            except Exception as e:
                print(f"Warning: Failed to migrate deck_layout.json: {e}")
        
        # Migrate card_templates.json
        templates_file = "data/card_templates.json"
        if os.path.exists(templates_file):
            try:
                with open(templates_file, 'r') as f:
                    templates_data = json.load(f)
                
                # Store custom templates (non-preset ones)
                custom_templates = {
                    name: template for name, template in templates_data.items()
                    if not template.get('is_preset', False)
                }
                
                if custom_templates:
                    self.set("templates.custom_templates", custom_templates, save=False)
                
                migrations_performed.append("card_templates.json")
            except Exception as e:
                print(f"Warning: Failed to migrate card_templates.json: {e}")
        
        if migrations_performed:
            self.save_config()
            print(f"Migrated settings from: {', '.join(migrations_performed)}")
        
        return migrations_performed


# Global configuration instance
_config_instance = None

def get_config() -> ConfigManager:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance

def reset_config():
    """Reset the global configuration instance (useful for testing)."""
    global _config_instance
    _config_instance = None
