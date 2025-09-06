"""
Flashcard Generation Library

This module provides comprehensive flashcard generation capabilities including:
- PDF document processing
- GitHub repository analysis
- HTML documentation processing
- Mathematical content extraction
- AI-powered content enhancement
- Advanced cloze input cards
- Progressive disclosure cards
- Interactive code execution cards
"""

from .core.ultimate_system import UltimateFlashcardSystem
from .core.content_processors import PDFProcessor, GitHubProcessor, HTMLProcessor, EPUBProcessor
from .advanced.cloze_system import AdvancedClozeSystem, DeletionType
from .advanced.math_processor import MathematicalContentProcessor
from .advanced.interactive_features import (
    ProgressiveDisclosureGenerator,
    InteractiveCodeGenerator,
    DiagramGenerator
)
from .utils.export import FlashcardExporter
from .utils.performance import PerformanceOptimizedProcessor

__version__ = "2.0.0"

__all__ = [
    'UltimateFlashcardSystem',
    'PDFProcessor',
    'GitHubProcessor',
    'HTMLProcessor',
    'EPUBProcessor',
    'AdvancedClozeSystem',
    'DeletionType',
    'MathematicalContentProcessor',
    'ProgressiveDisclosureGenerator',
    'InteractiveCodeGenerator',
    'DiagramGenerator',
    'FlashcardExporter',
    'PerformanceOptimizedProcessor',
    'create_flashcard_generator',
    'convert_cards_format'
]


def create_flashcard_generator(config=None):
    """Factory function for easy integration"""
    default_config = {
        'use_ai': True,
        'use_gemini': False,
        'comprehensive': True,
        'max_cards_per_section': 100,
        'output_dir': 'exports'
    }
    
    if config:
        default_config.update(config)
    
    return UltimateFlashcardSystem(default_config)


def convert_cards_format(ultimate_cards, target_format='plus_ultra'):
    """Convert Ultimate cards to target format"""
    if target_format == 'plus_ultra':
        return _convert_to_plus_ultra_format(ultimate_cards)
    else:
        raise ValueError(f"Unsupported target format: {target_format}")


def _normalize_tags(tags):
    """Normalize tags to a list format"""
    if not tags:
        return []

    if isinstance(tags, list):
        # Already a list, clean up any empty strings
        return [tag.strip() for tag in tags if tag and tag.strip()]

    if isinstance(tags, str):
        # Split comma-separated string into list
        if ',' in tags:
            return [tag.strip() for tag in tags.split(',') if tag and tag.strip()]
        else:
            # Single tag
            return [tags.strip()] if tags.strip() else []

    # Convert other types to string first
    return [str(tags).strip()] if str(tags).strip() else []


def _convert_to_plus_ultra_format(ultimate_cards):
    """Convert Ultimate cards to Plus Ultra format"""
    converted_cards = []
    
    for card in ultimate_cards:
        # Map card types
        if card['type'] == 'fb':
            # Front/back card
            converted_card = {
                'front': card['front'],
                'back': card['back'],
                'hint': card.get('hint', ''),
                'tags': _normalize_tags(card.get('tags', '')),
                'difficulty': _map_difficulty(card.get('difficulty', 'intermediate')),
                'source': card.get('source', ''),
                'card_type': 'basic'
            }
        elif card['type'] == 'cloze':
            # Standard cloze deletion card
            converted_card = {
                'front': card['content'],
                'back': '',  # Cloze cards are single-sided
                'hint': card.get('hint', ''),
                'tags': _normalize_tags(card.get('tags', '')),
                'difficulty': _map_difficulty(card.get('difficulty', 'intermediate')),
                'source': card.get('source', ''),
                'card_type': 'cloze'
            }
        elif card['type'] == 'cloze_input':
            # Cloze input card (new type)
            converted_card = {
                'front': card['content'],
                'back': '',  # Cloze input cards are single-sided
                'hint': card.get('hint', ''),
                'tags': _normalize_tags(card.get('tags', '')),
                'difficulty': _map_difficulty(card.get('difficulty', 'intermediate')),
                'source': card.get('source', ''),
                'card_type': 'cloze_input'
            }
        else:
            # Default to basic card
            converted_card = {
                'front': card.get('front', card.get('content', '')),
                'back': card.get('back', ''),
                'hint': card.get('hint', ''),
                'tags': _normalize_tags(card.get('tags', '')),
                'difficulty': _map_difficulty(card.get('difficulty', 'intermediate')),
                'source': card.get('source', ''),
                'card_type': 'basic'
            }
        
        converted_cards.append(converted_card)
    
    return converted_cards


def _map_difficulty(ultimate_difficulty):
    """Map difficulty levels"""
    mapping = {
        'basic': 1,
        'intermediate': 2,
        'advanced': 3,
        'expert': 4
    }
    return mapping.get(ultimate_difficulty, 2)
