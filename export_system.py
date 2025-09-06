#!/usr/bin/env python3
"""
Advanced Export System for Flashcard Generation

This module provides comprehensive export functionality for:
- JSON and CSV format export
- Anki compatibility
- Bulk export support
- Tag management and organization
- Performance optimization for large datasets
"""

import json
import csv
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class FlashcardData:
    """Structured flashcard data"""
    type: str  # "fb", "cloze", "cloze_input"
    front: str = ""
    back: str = ""
    content: str = ""
    hint: str = ""
    tags: str = ""
    template_id: str = ""
    difficulty: str = "intermediate"
    concept: str = ""
    source: str = ""
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class FlashcardExporter:
    """Advanced flashcard export system"""
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Anki field mappings
        self.anki_field_mapping = {
            "fb": ["Front", "Back", "Hint", "Tags", "Source"],
            "cloze": ["Text", "Hint", "Tags", "Source"],
            "cloze_input": ["Text", "Hint", "Tags", "Source"]
        }
    
    def export_to_json(self, cards: List[Dict[str, Any]], filename: str, 
                      include_metadata: bool = True) -> str:
        """Export flashcards to JSON format with metadata"""
        output_path = self.output_dir / f"{filename}.json"
        
        # Convert to structured format
        structured_cards = []
        for card in cards:
            flashcard = FlashcardData(**card)
            structured_cards.append(asdict(flashcard))
        
        export_data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "total_cards": len(structured_cards),
                "card_types": self._get_card_type_counts(structured_cards),
                "tags": self._extract_all_tags(structured_cards),
                "difficulty_distribution": self._get_difficulty_distribution(structured_cards)
            } if include_metadata else {},
            "cards": structured_cards
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(structured_cards)} cards to {output_path}")
        return str(output_path)
    
    def export_to_csv(self, cards: List[Dict[str, Any]], filename: str,
                     anki_compatible: bool = True) -> str:
        """Export flashcards to CSV format with Anki compatibility"""
        output_path = self.output_dir / f"{filename}.csv"
        
        if anki_compatible:
            return self._export_anki_csv(cards, output_path)
        else:
            return self._export_standard_csv(cards, output_path)
    
    def _export_standard_csv(self, cards: List[Dict[str, Any]], output_path: Path) -> str:
        """Export to standard CSV format"""
        if not cards:
            logger.warning("No cards to export")
            return str(output_path)
        
        # Define field order
        fieldnames = [
            "type", "front", "back", "content", "hint", "tags", 
            "template_id", "difficulty", "concept", "source", "created_at"
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for card in cards:
                # Ensure all fields are present
                row = {}
                for field in fieldnames:
                    row[field] = card.get(field, "")
                
                # Add metadata if missing
                if not row["created_at"]:
                    row["created_at"] = datetime.now().isoformat()
                
                writer.writerow(row)
        
        logger.info(f"Exported {len(cards)} cards to {output_path}")
        return str(output_path)
    
    def _export_anki_csv(self, cards: List[Dict[str, Any]], output_path: Path) -> str:
        """Export to Anki-compatible CSV format"""
        if not cards:
            logger.warning("No cards to export")
            return str(output_path)
        
        # Group cards by type for separate files
        cards_by_type = {}
        for card in cards:
            card_type = card.get("type", "fb")
            if card_type not in cards_by_type:
                cards_by_type[card_type] = []
            cards_by_type[card_type].append(card)
        
        exported_files = []
        
        for card_type, type_cards in cards_by_type.items():
            type_output_path = output_path.parent / f"{output_path.stem}_{card_type}.csv"
            
            with open(type_output_path, 'w', newline='', encoding='utf-8') as csvfile:
                if card_type == "fb":
                    # Front/Back cards
                    fieldnames = ["Front", "Back", "Hint", "Tags", "Source"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for card in type_cards:
                        writer.writerow({
                            "Front": card.get("front", ""),
                            "Back": card.get("back", ""),
                            "Hint": card.get("hint", ""),
                            "Tags": card.get("tags", ""),
                            "Source": card.get("source", "")
                        })
                
                elif card_type in ["cloze", "cloze_input"]:
                    # Cloze cards
                    fieldnames = ["Text", "Hint", "Tags", "Source"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for card in type_cards:
                        writer.writerow({
                            "Text": card.get("content", ""),
                            "Hint": card.get("hint", ""),
                            "Tags": card.get("tags", ""),
                            "Source": card.get("source", "")
                        })
            
            exported_files.append(str(type_output_path))
            logger.info(f"Exported {len(type_cards)} {card_type} cards to {type_output_path}")
        
        return ", ".join(exported_files)
    
    def export_bulk(self, cards: List[Dict[str, Any]], base_filename: str,
                   formats: List[str] = None, chunk_size: int = 1000) -> Dict[str, List[str]]:
        """Export large datasets in chunks with multiple formats"""
        if formats is None:
            formats = ["json", "csv", "anki"]
        
        exported_files = {format_type: [] for format_type in formats}
        
        # Process in chunks for memory efficiency
        total_chunks = (len(cards) + chunk_size - 1) // chunk_size
        
        for chunk_idx in range(total_chunks):
            start_idx = chunk_idx * chunk_size
            end_idx = min(start_idx + chunk_size, len(cards))
            chunk_cards = cards[start_idx:end_idx]
            
            chunk_filename = f"{base_filename}_chunk_{chunk_idx + 1:03d}"
            
            for format_type in formats:
                try:
                    if format_type == "json":
                        file_path = self.export_to_json(chunk_cards, chunk_filename)
                        exported_files["json"].append(file_path)
                    
                    elif format_type == "csv":
                        file_path = self.export_to_csv(chunk_cards, chunk_filename, anki_compatible=False)
                        exported_files["csv"].append(file_path)
                    
                    elif format_type == "anki":
                        file_paths = self.export_to_csv(chunk_cards, chunk_filename, anki_compatible=True)
                        exported_files["anki"].extend(file_paths.split(", "))
                
                except Exception as e:
                    logger.error(f"Failed to export chunk {chunk_idx + 1} in {format_type} format: {e}")
        
        # Create summary file
        self._create_export_summary(exported_files, base_filename, len(cards))
        
        return exported_files
    
    def _create_export_summary(self, exported_files: Dict[str, List[str]], 
                              base_filename: str, total_cards: int):
        """Create a summary of exported files"""
        summary_path = self.output_dir / f"{base_filename}_export_summary.json"
        
        summary = {
            "export_date": datetime.now().isoformat(),
            "total_cards": total_cards,
            "exported_files": exported_files,
            "file_counts": {format_type: len(files) for format_type, files in exported_files.items()}
        }
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created export summary: {summary_path}")
    
    def _get_card_type_counts(self, cards: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get count of each card type"""
        counts = {}
        for card in cards:
            card_type = card.get("type", "unknown")
            counts[card_type] = counts.get(card_type, 0) + 1
        return counts
    
    def _extract_all_tags(self, cards: List[Dict[str, Any]]) -> List[str]:
        """Extract all unique tags from cards"""
        all_tags = set()
        for card in cards:
            tags = card.get("tags", "")
            if tags:
                tag_list = [tag.strip() for tag in tags.split(",")]
                all_tags.update(tag_list)
        return sorted(list(all_tags))
    
    def _get_difficulty_distribution(self, cards: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of difficulty levels"""
        distribution = {}
        for card in cards:
            difficulty = card.get("difficulty", "intermediate")
            distribution[difficulty] = distribution.get(difficulty, 0) + 1
        return distribution


class TagManager:
    """Advanced tag management system"""
    
    def __init__(self):
        self.tag_hierarchy = {}
        self.tag_synonyms = {}
    
    def normalize_tags(self, tags: str) -> str:
        """Normalize and clean tags"""
        if not tags:
            return ""
        
        tag_list = [tag.strip().lower() for tag in tags.split(",")]
        
        # Remove duplicates and empty tags
        normalized_tags = []
        seen = set()
        
        for tag in tag_list:
            if tag and tag not in seen:
                # Apply synonyms
                normalized_tag = self.tag_synonyms.get(tag, tag)
                normalized_tags.append(normalized_tag)
                seen.add(tag)
        
        return ",".join(normalized_tags)
    
    def add_tag_hierarchy(self, parent: str, children: List[str]):
        """Add hierarchical tag relationships"""
        self.tag_hierarchy[parent] = children
    
    def add_tag_synonyms(self, synonyms: Dict[str, str]):
        """Add tag synonyms for normalization"""
        self.tag_synonyms.update(synonyms)
    
    def expand_tags(self, tags: str) -> str:
        """Expand tags with hierarchical relationships"""
        if not tags:
            return ""
        
        tag_list = [tag.strip() for tag in tags.split(",")]
        expanded_tags = set(tag_list)
        
        # Add parent tags
        for tag in tag_list:
            for parent, children in self.tag_hierarchy.items():
                if tag in children:
                    expanded_tags.add(parent)
        
        return ",".join(sorted(expanded_tags))


# Factory functions
def create_exporter(output_dir: str = "exports") -> FlashcardExporter:
    """Create a flashcard exporter"""
    return FlashcardExporter(output_dir)


def export_flashcards(cards: List[Dict[str, Any]], filename: str, 
                     formats: List[str] = None, output_dir: str = "exports") -> Dict[str, Any]:
    """Convenience function to export flashcards in multiple formats"""
    exporter = create_exporter(output_dir)
    
    if formats is None:
        formats = ["json", "csv", "anki"]
    
    results = {}
    
    for format_type in formats:
        try:
            if format_type == "json":
                results["json"] = exporter.export_to_json(cards, filename)
            elif format_type == "csv":
                results["csv"] = exporter.export_to_csv(cards, filename, anki_compatible=False)
            elif format_type == "anki":
                results["anki"] = exporter.export_to_csv(cards, filename, anki_compatible=True)
        except Exception as e:
            logger.error(f"Failed to export in {format_type} format: {e}")
            results[format_type] = None
    
    return results
