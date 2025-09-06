"""
Card Type Factory Pattern Implementation
Provides a standardized interface for all card types with pluggable architecture
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from app.formatting.formatter_service import FormatterService, RenderingOptions
from app.rendering.template_system import rendering_engine, RenderingContext


@dataclass
class CardTypeMetadata:
    """Metadata for card types"""
    name: str
    description: str
    priority: int  # Higher priority types are checked first
    supports_single_sided: bool
    supports_multi_sided: bool
    supports_cloze: bool
    supports_input: bool


class CardTypeInterface(ABC):
    """Abstract interface that all card types must implement"""
    
    @abstractmethod
    def get_metadata(self) -> CardTypeMetadata:
        """Return metadata about this card type"""
        pass
    
    @abstractmethod
    def is_match(self, front_text: str, back_text: str = "") -> bool:
        """Determine if this card type matches the given content"""
        pass
    
    @abstractmethod
    def is_single_sided(self) -> bool:
        """Return True if this card type is single-sided"""
        pass
    
    @abstractmethod
    def render_front(self, text: str, options: RenderingOptions, formatter: FormatterService) -> str:
        """Render the front of the card"""
        pass
    
    @abstractmethod
    def render_back(self, text: str, options: RenderingOptions, formatter: FormatterService) -> str:
        """Render the back of the card"""
        pass
    
    @abstractmethod
    def get_study_interface_config(self) -> Dict[str, Any]:
        """Return configuration for the study interface"""
        pass
    
    @abstractmethod
    def validate_content(self, front_text: str, back_text: str = "") -> List[str]:
        """Validate card content and return list of errors"""
        pass


class BasicCardType(CardTypeInterface):
    """Standard front/back card type"""
    
    def get_metadata(self) -> CardTypeMetadata:
        return CardTypeMetadata(
            name="Basic Card",
            description="Standard front/back flashcard",
            priority=1,  # Lowest priority - fallback
            supports_single_sided=False,
            supports_multi_sided=True,
            supports_cloze=False,
            supports_input=False
        )
    
    def is_match(self, front_text: str, back_text: str = "") -> bool:
        # Basic cards match anything that doesn't match other types
        return True
    
    def is_single_sided(self) -> bool:
        return False
    
    def render_front(self, text: str, options: RenderingOptions, formatter: FormatterService) -> str:
        context = RenderingContext(
            content_type='basic',
            apply_syntax_highlighting=options.apply_syntax_highlighting,
            reveal_cloze=False,
            inline_css=options.inline_css,
            custom_options={}
        )
        return rendering_engine.render(text, context)

    def render_back(self, text: str, options: RenderingOptions, formatter: FormatterService) -> str:
        context = RenderingContext(
            content_type='basic',
            apply_syntax_highlighting=options.apply_syntax_highlighting,
            reveal_cloze=False,
            inline_css=options.inline_css,
            custom_options={}
        )
        return rendering_engine.render(text, context)
    
    def get_study_interface_config(self) -> Dict[str, Any]:
        return {
            'type': 'basic',
            'show_flip_button': True,
            'show_answer_buttons': True,
            'side_panel': None,
            'custom_buttons': []
        }
    
    def validate_content(self, front_text: str, back_text: str = "") -> List[str]:
        errors = []
        if not front_text.strip():
            errors.append("Front text cannot be empty")
        if not back_text.strip():
            errors.append("Back text cannot be empty for basic cards")
        return errors


class ClozeCardType(CardTypeInterface):
    """Standard cloze deletion card type"""
    
    def get_metadata(self) -> CardTypeMetadata:
        return CardTypeMetadata(
            name="Cloze Card",
            description="Cloze deletion flashcard",
            priority=3,  # Higher priority than basic
            supports_single_sided=True,
            supports_multi_sided=False,
            supports_cloze=True,
            supports_input=False
        )
    
    def is_match(self, front_text: str, back_text: str = "") -> bool:
        return "{{c" in front_text and "{{cin" not in front_text
    
    def is_single_sided(self) -> bool:
        return True
    
    def render_front(self, text: str, options: RenderingOptions, formatter: FormatterService) -> str:
        context = RenderingContext(
            content_type='cloze',
            apply_syntax_highlighting=options.apply_syntax_highlighting,
            reveal_cloze=False,
            inline_css=options.inline_css,
            custom_options={}
        )
        return rendering_engine.render(text, context)

    def render_back(self, text: str, options: RenderingOptions, formatter: FormatterService) -> str:
        context = RenderingContext(
            content_type='cloze',
            apply_syntax_highlighting=options.apply_syntax_highlighting,
            reveal_cloze=True,
            inline_css=options.inline_css,
            custom_options={}
        )
        return rendering_engine.render(text, context)
    
    def get_study_interface_config(self) -> Dict[str, Any]:
        return {
            'type': 'cloze',
            'show_flip_button': True,
            'show_answer_buttons': True,
            'side_panel': None,
            'custom_buttons': []
        }
    
    def validate_content(self, front_text: str, back_text: str = "") -> List[str]:
        errors = []
        if not front_text.strip():
            errors.append("Front text cannot be empty")
        if "{{c" not in front_text:
            errors.append("Cloze cards must contain cloze deletions ({{c1::text}})")
        return errors


class ClozeInputCardType(CardTypeInterface):
    """Interactive cloze input card type"""
    
    def get_metadata(self) -> CardTypeMetadata:
        return CardTypeMetadata(
            name="Cloze Input Card",
            description="Interactive cloze input flashcard",
            priority=5,  # Highest priority
            supports_single_sided=True,
            supports_multi_sided=False,
            supports_cloze=False,
            supports_input=True
        )
    
    def is_match(self, front_text: str, back_text: str = "") -> bool:
        return "{{cin" in front_text
    
    def is_single_sided(self) -> bool:
        return True
    
    def render_front(self, text: str, options: RenderingOptions, formatter: FormatterService) -> str:
        # For cloze input cards, use the robust TextFormatter pipeline that handles multi-line cin and style markers
        return formatter.render_cloze_input_for_display(text, options.apply_syntax_highlighting)

    def render_back(self, text: str, options: RenderingOptions, formatter: FormatterService) -> str:
        # For answer/reveal, show the revealed inputs via TextFormatter
        return formatter.render_cloze_input_revealed(text, options.apply_syntax_highlighting)
    
    def get_study_interface_config(self) -> Dict[str, Any]:
        return {
            'type': 'cloze_input',
            'show_flip_button': False,  # Custom button handling
            'show_answer_buttons': False,  # Custom validation
            'side_panel': 'cloze_input',
            'custom_buttons': ['check_answers'],
            'multi_attempt': True,
            'max_attempts': 3
        }
    
    def validate_content(self, front_text: str, back_text: str = "") -> List[str]:
        errors = []
        if not front_text.strip():
            errors.append("Front text cannot be empty")
        if "{{cin" not in front_text:
            errors.append("Cloze input cards must contain cloze inputs ({{cin1::answer}})")
        
        # Validate cloze input format
        import re
        pattern = r'\{\{cin(\d+)::([^}]+)\}\}'
        matches = re.findall(pattern, front_text)
        if not matches:
            errors.append("Invalid cloze input format")
        
        return errors


class CardTypeFactory:
    """Factory for managing and creating card types"""
    
    def __init__(self):
        self._card_types: List[CardTypeInterface] = []
        self._register_default_types()
    
    def _register_default_types(self):
        """Register the default card types"""
        self.register_card_type(ClozeInputCardType())
        self.register_card_type(ClozeCardType())
        self.register_card_type(BasicCardType())
    
    def register_card_type(self, card_type: CardTypeInterface):
        """Register a new card type"""
        self._card_types.append(card_type)
        # Sort by priority (highest first)
        self._card_types.sort(key=lambda ct: ct.get_metadata().priority, reverse=True)
    
    def get_card_type(self, front_text: str, back_text: str = "") -> CardTypeInterface:
        """Get the appropriate card type for the given content"""
        for card_type in self._card_types:
            if card_type.is_match(front_text, back_text):
                return card_type
        
        # Fallback to basic card
        return BasicCardType()
    
    def get_all_card_types(self) -> List[CardTypeInterface]:
        """Get all registered card types"""
        return self._card_types.copy()
    
    def get_card_type_by_name(self, name: str) -> Optional[CardTypeInterface]:
        """Get a card type by its name"""
        for card_type in self._card_types:
            if card_type.get_metadata().name == name:
                return card_type
        return None
    
    def validate_card_content(self, front_text: str, back_text: str = "") -> Dict[str, Any]:
        """Validate card content and return validation results"""
        card_type = self.get_card_type(front_text, back_text)
        errors = card_type.validate_content(front_text, back_text)
        
        return {
            'card_type': card_type.get_metadata().name,
            'is_valid': len(errors) == 0,
            'errors': errors,
            'metadata': card_type.get_metadata()
        }


# Global factory instance
card_type_factory = CardTypeFactory()
