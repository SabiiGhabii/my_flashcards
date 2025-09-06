"""
Export System for Flashcards

This module provides comprehensive export functionality for:
- JSON format with metadata
- CSV format with Anki compatibility
- Bulk export operations
- Format conversion utilities
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class FlashcardExporter:
    """Advanced flashcard export system"""
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_to_json(self, cards: List[Dict[str, Any]], output_base: str,
                      include_metadata: bool = True) -> str:
        """Export cards to JSON format"""
        try:
            timestamp = datetime.now().isoformat()
            
            export_data = {
                "metadata": {
                    "export_timestamp": timestamp,
                    "total_cards": len(cards),
                    "export_format": "json",
                    "version": "2.0.0"
                } if include_metadata else {},
                "cards": cards
            }
            
            filename = f"{output_base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(cards)} cards to JSON: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            raise
    
    def export_to_csv(self, cards: List[Dict[str, Any]], output_base: str,
                     anki_compatible: bool = False) -> str:
        """Export cards to CSV format"""
        try:
            if anki_compatible:
                return self._export_anki_csv(cards, output_base)
            else:
                return self._export_standard_csv(cards, output_base)
                
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            raise
    
    def _export_standard_csv(self, cards: List[Dict[str, Any]], output_base: str) -> str:
        """Export to standard CSV format"""
        filename = f"{output_base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = self.output_dir / filename
        
        # Define CSV headers
        headers = [
            'type', 'front', 'back', 'content', 'hint', 'tags', 
            'template_id', 'difficulty', 'concept', 'source'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for card in cards:
                # Ensure all required fields exist
                row = {header: card.get(header, '') for header in headers}
                writer.writerow(row)
        
        logger.info(f"Exported {len(cards)} cards to CSV: {filepath}")
        return str(filepath)
    
    def _export_anki_csv(self, cards: List[Dict[str, Any]], output_base: str) -> str:
        """Export to Anki-compatible CSV format"""
        # Group cards by type for separate files
        card_groups = {}
        for card in cards:
            card_type = card.get('type', 'basic')
            if card_type not in card_groups:
                card_groups[card_type] = []
            card_groups[card_type].append(card)
        
        exported_files = []
        
        for card_type, type_cards in card_groups.items():
            filename = f"{output_base}_{card_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = self.output_dir / filename
            
            if card_type == 'fb':
                # Front/Back cards
                headers = ['Front', 'Back', 'Tags']
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    
                    for card in type_cards:
                        writer.writerow([
                            card.get('front', ''),
                            card.get('back', ''),
                            card.get('tags', '')
                        ])
            
            elif card_type in ['cloze', 'cloze_input']:
                # Cloze cards
                headers = ['Text', 'Tags']
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    
                    for card in type_cards:
                        writer.writerow([
                            card.get('content', ''),
                            card.get('tags', '')
                        ])
            
            exported_files.append(str(filepath))
            logger.info(f"Exported {len(type_cards)} {card_type} cards to: {filepath}")
        
        return exported_files[0] if len(exported_files) == 1 else str(exported_files)
    
    def export_bulk(self, cards: List[Dict[str, Any]], output_base: str,
                   formats: List[str]) -> Dict[str, str]:
        """Export cards in multiple formats"""
        results = {}
        
        for format_type in formats:
            try:
                if format_type == 'json':
                    results['json'] = self.export_to_json(cards, output_base)
                elif format_type == 'csv':
                    results['csv'] = self.export_to_csv(cards, output_base, anki_compatible=False)
                elif format_type == 'anki':
                    results['anki'] = self.export_to_csv(cards, output_base, anki_compatible=True)
                else:
                    logger.warning(f"Unsupported export format: {format_type}")
                    
            except Exception as e:
                logger.error(f"Failed to export in {format_type} format: {e}")
                results[format_type] = None
        
        return results


def export_flashcards(cards: List[Dict[str, Any]], output_path: str,
                     format_type: str = "csv", **kwargs) -> str:
    """Convenience function for exporting flashcards"""
    exporter = FlashcardExporter()
    
    if format_type == "json":
        return exporter.export_to_json(cards, output_path, **kwargs)
    elif format_type == "csv":
        return exporter.export_to_csv(cards, output_path, **kwargs)
    else:
        raise ValueError(f"Unsupported format: {format_type}")


def convert_cards_format(cards: List[Dict[str, Any]], 
                        source_format: str, target_format: str) -> List[Dict[str, Any]]:
    """Convert cards between different formats"""
    if source_format == target_format:
        return cards
    
    # Add format conversion logic here if needed
    return cards
