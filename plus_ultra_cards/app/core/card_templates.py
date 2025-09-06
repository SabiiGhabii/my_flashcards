"""
Card Template System
Provides retro-styled preset templates and custom template management.
"""

import json
import os
from typing import Dict, List
from pathlib import Path


class CardTemplateManager:
    """Manages card templates with retro95 styling presets."""
    
    def __init__(self, templates_file: str = "data/card_templates.json"):
        self.templates_file = templates_file
        self.templates = self.load_templates()
    
    def load_templates(self) -> Dict:
        """Load templates from file, creating defaults if needed."""
        try:
            if os.path.exists(self.templates_file):
                with open(self.templates_file, 'r') as f:
                    templates = json.load(f)
                    # Ensure we have default templates
                    self.ensure_default_templates(templates)
                    return templates
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        # Create default templates
        return self.create_default_templates()
    
    def save_templates(self):
        """Save templates to file."""
        try:
            os.makedirs(os.path.dirname(self.templates_file), exist_ok=True)
            with open(self.templates_file, 'w') as f:
                json.dump(self.templates, f, indent=2)
        except Exception as e:
            print(f"Failed to save templates: {e}")
    
    def create_default_templates(self) -> Dict:
        """Create the default template - only Basic template with proper MS Sans Serif font."""
        # Load the MS Sans Serif font explicitly to ensure it's available
        self._ensure_ms_sans_serif_loaded()

        templates = {
            "Basic": {
                "name": "Basic",
                "description": "Default card template with MS Sans Serif font",
                "rich": True,
                "css": "font-family: 'W95font', 'Microsoft Sans Serif', sans-serif; font-size: 14px; line-height: 1.4; padding: 8px;",
                "is_preset": True,
                "is_default": True
            }
        }
        
        self.templates = templates
        self.save_templates()
        return templates

    def _ensure_ms_sans_serif_loaded(self):
        """Ensure MS Sans Serif font is loaded from the .otf file."""
        try:
            from PySide6.QtGui import QFontDatabase, QFont
            from pathlib import Path

            # Path to the MS Sans Serif font file
            font_path = Path(__file__).resolve().parents[1] / "assets" / "fonts" / "W95font.otf"

            if font_path.exists():
                fid = QFontDatabase.addApplicationFont(str(font_path))
                if fid != -1:
                    families = QFontDatabase.applicationFontFamilies(fid)
                    if families:
                        loaded_family = families[0]
                        # Set up font substitutions to ensure MS Sans Serif resolves correctly
                        QFont.insertSubstitution("MS Sans Serif", loaded_family)
                        QFont.insertSubstitution("Microsoft Sans Serif", loaded_family)
                        # Also set up the reverse mapping
                        QFont.insertSubstitution("W95font", loaded_family)
                        print(f"MS Sans Serif font loaded successfully: {loaded_family}")
                        return True

            print("Warning: MS Sans Serif font file not found, using system fallback")
            return False

        except Exception as e:
            print(f"Error loading MS Sans Serif font: {e}")
            return False
    
    def ensure_default_templates(self, templates: Dict):
        """Ensure default templates exist in the loaded templates."""
        defaults = self.create_default_templates()
        
        for template_name, template_data in defaults.items():
            if template_name not in templates:
                templates[template_name] = template_data
        
        # Save if we added any defaults
        if len(templates) != len(self.templates):
            self.templates = templates
            self.save_templates()
    
    def get_template_names(self) -> List[str]:
        """Get list of all template names."""
        return list(self.templates.keys())
    
    def get_preset_names(self) -> List[str]:
        """Get list of preset template names."""
        return [name for name, data in self.templates.items() if data.get('is_preset', False)]
    
    def get_custom_names(self) -> List[str]:
        """Get list of custom template names."""
        return [name for name, data in self.templates.items() if not data.get('is_preset', False)]
    
    def get_template(self, name: str) -> Dict:
        """Get template data by name."""
        return self.templates.get(name, {})
    
    def create_template(self, name: str, description: str, css: str, rich: bool = True) -> bool:
        """Create a new custom template."""
        if name in self.templates:
            return False  # Template already exists
        
        self.templates[name] = {
            "name": name,
            "description": description,
            "rich": rich,
            "css": css,
            "is_preset": False
        }
        
        self.save_templates()
        return True
    
    def update_template(self, name: str, description: str = None, css: str = None, rich: bool = None) -> bool:
        """Update an existing custom template."""
        if name not in self.templates:
            return False
        
        template = self.templates[name]
        
        # Don't allow editing preset templates
        if template.get('is_preset', False):
            return False
        
        if description is not None:
            template['description'] = description
        if css is not None:
            template['css'] = css
        if rich is not None:
            template['rich'] = rich
        
        self.save_templates()
        return True
    
    def delete_template(self, name: str) -> bool:
        """Delete a custom template."""
        if name not in self.templates:
            return False
        
        template = self.templates[name]
        
        # Don't allow deleting preset templates
        if template.get('is_preset', False):
            return False
        
        del self.templates[name]
        self.save_templates()
        return True
    
    def apply_template_to_card_data(self, template_name: str) -> Dict:
        """Get template data formatted for card template_data field."""
        template = self.get_template(template_name)
        if not template:
            return {}
        
        return {
            'rich': template.get('rich', True),
            'inline_css': template.get('css', ''),
            'template_name': template_name
        }
    
    def get_template_preview_html(self, template_name: str, sample_text: str = "Sample card content") -> str:
        """Generate preview HTML for a template."""
        template = self.get_template(template_name)
        if not template:
            return sample_text
        
        if template.get('rich', True):
            css = template.get('css', '')
            return f'<div style="{css}">{sample_text}</div>'
        else:
            return sample_text
