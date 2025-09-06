"""
Ultimate Flashcard Generation System - Core Module

This is the comprehensive, production-ready flashcard generation system with:
- Full Gemini API integration
- Advanced cloze input cards with AST analysis
- Mathematical equations support with LaTeX/MathJax
- Performance optimization with caching and batch processing
- Advanced export system (JSON, CSV, Anki)
- Template selection interface
- Comprehensive content extraction for complete mastery
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Import all our advanced systems
try:
    from ..ai.gemini_integration import create_gemini_agent, GeminiAgent, ContentType
    from ..utils.export import export_flashcards, FlashcardExporter
    from ..advanced.cloze_system import create_cloze_system, DeletionType
    from ..advanced.math_processor import create_math_processor
    from ..utils.performance import create_optimized_processor
    from .content_processors import FlashcardifyEnhanced, Config, ensure_nltk
    HAS_ALL_MODULES = True
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    HAS_ALL_MODULES = False


class UltimateFlashcardSystem:
    """Ultimate flashcard generation system with all advanced features"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize Gemini agent if API key provided
        self.gemini_agent = None
        if config.get('use_gemini') and config.get('gemini_api_key'):
            self.gemini_agent = create_gemini_agent(config['gemini_api_key'])
            if self.gemini_agent:
                logger.info("Gemini AI integration enabled")
        
        # Initialize all subsystems
        self.cloze_system = create_cloze_system(self.gemini_agent)
        self.math_processor = create_math_processor(self.gemini_agent)
        self.performance_processor = create_optimized_processor(
            batch_size=config.get('batch_size', 1000),
            memory_threshold_mb=config.get('memory_threshold', 1000)
        )
        self.exporter = FlashcardExporter(config.get('output_dir', 'exports'))
        
        # Initialize base system
        base_config = Config(
            use_ai=config.get('use_ai', True),
            use_gemini=config.get('use_gemini', False),
            max_cards_per_section=config.get('max_cards_per_section', 100),
            custom_instructions=config.get('custom_instructions', ''),
            gemini_api_key=config.get('gemini_api_key')
        )
        self.base_system = FlashcardifyEnhanced(base_config)
    
    def process_content_comprehensive(self, source: str, source_type: str) -> Dict[str, Any]:
        """Process content comprehensively for complete mastery"""
        logger.info(f"Starting comprehensive processing of {source_type} source: {source}")
        
        # Use performance-optimized processing
        def comprehensive_processor(content_text: str) -> List[Dict[str, Any]]:
            return self._generate_comprehensive_cards(content_text, source_type)
        
        # Process with optimization
        processing_params = {
            'source_type': source_type,
            'comprehensive': self.config.get('comprehensive', False),
            'use_gemini': self.config.get('use_gemini', False)
        }
        
        # Extract content using base system
        base_cards = self.base_system.process_content(source, source_type)
        
        # If comprehensive mode, generate additional specialized cards
        if self.config.get('comprehensive', False):
            # Get the original content for additional processing
            content_handler = self.base_system.sources[source_type]
            content = content_handler.extract_content(source)
            sections = content_handler.get_sections(content)
            
            additional_cards = []
            for title, paragraphs in sections:
                content_text = "\n".join(paragraphs)
                
                # Generate mathematical cards if content contains math
                math_result = self.math_processor.process_mathematical_content(content_text)
                additional_cards.extend(math_result.get('cards', []))
                
                # Generate advanced cloze cards for code content
                if source_type == 'github' or self._contains_code(content_text):
                    code_snippets = self._extract_code_snippets(content_text)
                    for code in code_snippets:
                        cloze_cards = self.cloze_system.generate_all_cloze_types(code)
                        for card_type, cards in cloze_cards.items():
                            additional_cards.extend(cards)
                
                # Use Gemini for comprehensive card generation
                if self.gemini_agent:
                    content_type = self._determine_content_type(content_text, source_type)
                    gemini_cards = self.gemini_agent.generate_comprehensive_cards(
                        content_text, content_type, max_cards=50
                    )
                    additional_cards.extend(self._convert_gemini_cards(gemini_cards))
            
            # Combine all cards
            all_cards = base_cards + additional_cards
        else:
            all_cards = base_cards
        
        # Deduplicate and optimize
        unique_cards = self._deduplicate_cards(all_cards)
        
        logger.info(f"Generated {len(unique_cards)} unique flashcards")
        
        return {
            'cards': unique_cards,
            'total_cards': len(unique_cards),
            'source': source,
            'source_type': source_type,
            'comprehensive_mode': self.config.get('comprehensive', False),
            'processing_stats': self.performance_processor.get_system_stats()
        }
    
    def _generate_comprehensive_cards(self, content: str, source_type: str) -> List[Dict[str, Any]]:
        """Generate comprehensive cards from content"""
        cards = []
        
        # Determine content type for specialized processing
        content_type = self._determine_content_type(content, source_type)
        
        # Generate cards based on content type
        if content_type == ContentType.CODE:
            # Advanced code processing
            code_snippets = self._extract_code_snippets(content)
            for code in code_snippets:
                # Generate all types of cloze cards
                cloze_cards = self.cloze_system.generate_all_cloze_types(code)
                for card_type, type_cards in cloze_cards.items():
                    cards.extend(type_cards)
        
        elif content_type == ContentType.MATHEMATICAL:
            # Mathematical content processing
            math_result = self.math_processor.process_mathematical_content(content)
            cards.extend(math_result.get('cards', []))
        
        # Use Gemini for additional comprehensive cards
        if self.gemini_agent:
            gemini_cards = self.gemini_agent.generate_comprehensive_cards(
                content, content_type, max_cards=50
            )
            cards.extend(self._convert_gemini_cards(gemini_cards))
        
        return cards
    
    def _determine_content_type(self, content: str, source_type: str) -> ContentType:
        """Determine the type of content for specialized processing"""
        if source_type == 'github':
            return ContentType.CODE
        elif self._contains_math(content):
            return ContentType.MATHEMATICAL
        elif self._contains_code(content):
            return ContentType.CODE
        elif self._contains_procedures(content):
            return ContentType.PROCEDURAL
        else:
            return ContentType.CONCEPTUAL
    
    def _contains_code(self, content: str) -> bool:
        """Check if content contains code"""
        code_indicators = ['def ', 'class ', 'import ', 'function', 'var ', 'const ', 'let ']
        return any(indicator in content for indicator in code_indicators)
    
    def _contains_math(self, content: str) -> bool:
        """Check if content contains mathematical expressions"""
        math_indicators = ['=', '∫', '∑', '√', '²', '³', 'equation', 'formula', '$']
        return any(indicator in content for indicator in math_indicators)
    
    def _contains_procedures(self, content: str) -> bool:
        """Check if content contains procedural information"""
        procedure_indicators = ['step', 'procedure', 'algorithm', 'method', 'process']
        return any(indicator.lower() in content.lower() for indicator in procedure_indicators)
    
    def _extract_code_snippets(self, content: str) -> List[str]:
        """Extract code snippets from content"""
        import re
        
        # Look for code blocks
        code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', content, re.DOTALL)
        
        # Look for indented code
        lines = content.split('\n')
        code_snippets = []
        current_snippet = []
        
        for line in lines:
            if line.startswith('    ') or line.startswith('\t'):
                current_snippet.append(line)
            else:
                if current_snippet and len(current_snippet) > 2:
                    code_snippets.append('\n'.join(current_snippet))
                current_snippet = []
        
        if current_snippet and len(current_snippet) > 2:
            code_snippets.append('\n'.join(current_snippet))
        
        return code_blocks + code_snippets
    
    def _convert_gemini_cards(self, gemini_cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert Gemini-generated cards to standard format"""
        converted_cards = []
        
        for card in gemini_cards:
            converted_card = {
                'type': card.get('type', 'fb'),
                'front': card.get('front', ''),
                'back': card.get('back', ''),
                'content': card.get('content', ''),
                'hint': card.get('hint', ''),
                'tags': card.get('tags', ''),
                'template_id': 'gemini_generated',
                'difficulty': card.get('difficulty', 'intermediate'),
                'concept': card.get('concept', 'general')
            }
            converted_cards.append(converted_card)
        
        return converted_cards
    
    def _deduplicate_cards(self, cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate cards"""
        unique_cards = []
        seen_content = set()
        
        for card in cards:
            # Create a key based on card content
            content_key = (
                card.get("type", ""),
                (card.get("front", "") + card.get("content", "")).strip().lower()
            )
            
            if content_key not in seen_content and len(content_key[1]) >= 8:
                seen_content.add(content_key)
                unique_cards.append(card)
        
        return unique_cards
    
    def export_cards(self, cards: List[Dict[str, Any]], output_base: str, 
                    formats: List[str]) -> Dict[str, Any]:
        """Export cards in multiple formats"""
        export_results = {}
        
        for format_type in formats:
            try:
                if format_type == 'json':
                    result = self.exporter.export_to_json(cards, output_base, include_metadata=True)
                    export_results['json'] = result
                
                elif format_type == 'csv':
                    result = self.exporter.export_to_csv(cards, output_base, anki_compatible=False)
                    export_results['csv'] = result
                
                elif format_type == 'anki':
                    result = self.exporter.export_to_csv(cards, output_base, anki_compatible=True)
                    export_results['anki'] = result
                
                logger.info(f"Successfully exported in {format_type} format")
                
            except Exception as e:
                logger.error(f"Failed to export in {format_type} format: {e}")
                export_results[format_type] = None
        
        return export_results


def main():
    """Main CLI interface for the ultimate flashcard system"""
    parser = argparse.ArgumentParser(
        description="Ultimate Flashcard Generation System with AI and Advanced Features",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Comprehensive processing with Gemini
  python flashcardify_ultimate.py -i book.pdf --comprehensive --use-gemini --gemini-api-key YOUR_KEY
  
  # GitHub repository with all cloze types
  python flashcardify_ultimate.py -i https://github.com/user/repo --source github --formats json,csv,anki
  
  # Mathematical content with LaTeX support
  python flashcardify_ultimate.py -i math_textbook.pdf --comprehensive --formats json
  
  # Large document processing with optimization
  python flashcardify_ultimate.py -i large_book.pdf --comprehensive --batch-size 2000
        """
    )
    
    parser.add_argument("-i", "--input", required=True,
                       help="Input source (PDF, GitHub URL, HTML URL, etc.)")
    parser.add_argument("-o", "--output", default="ultimate_cards",
                       help="Output base name (default: ultimate_cards)")
    parser.add_argument("--source", choices=['pdf', 'github', 'html', 'leetcode'],
                       help="Source type (auto-detected if not specified)")
    parser.add_argument("--formats", default="json,csv",
                       help="Export formats: json,csv,anki (default: json,csv)")
    parser.add_argument("--comprehensive", action="store_true",
                       help="Enable comprehensive processing for complete mastery")
    parser.add_argument("--use-gemini", action="store_true",
                       help="Use Gemini AI for enhanced card generation")
    parser.add_argument("--gemini-api-key",
                       help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--max-cards-per-section", type=int, default=100,
                       help="Maximum cards per section (default: 100)")
    parser.add_argument("--batch-size", type=int, default=1000,
                       help="Batch size for large content processing (default: 1000)")
    parser.add_argument("--memory-threshold", type=int, default=1000,
                       help="Memory threshold in MB (default: 1000)")
    parser.add_argument("--custom-instructions",
                       help="Custom instructions for card generation")
    parser.add_argument("--output-dir", default="exports",
                       help="Output directory for exported files (default: exports)")
    
    args = parser.parse_args()
    
    if not HAS_ALL_MODULES:
        logger.error("Required modules are missing. Please install all dependencies.")
        sys.exit(1)
    
    # Ensure NLTK data
    ensure_nltk()
    
    # Parse formats
    formats = [f.strip() for f in args.formats.split(',')]
    
    # Auto-detect source type if not specified
    source_type = args.source
    if not source_type:
        if args.input.startswith(('http://', 'https://')):
            if 'github.com' in args.input:
                source_type = 'github'
            elif 'leetcode.com' in args.input:
                source_type = 'leetcode'
            else:
                source_type = 'html'
        else:
            source_type = 'pdf'
    
    # Create configuration
    config = {
        'use_ai': True,
        'use_gemini': args.use_gemini,
        'gemini_api_key': args.gemini_api_key or os.getenv('GEMINI_API_KEY'),
        'max_cards_per_section': args.max_cards_per_section,
        'batch_size': args.batch_size,
        'memory_threshold': args.memory_threshold,
        'custom_instructions': args.custom_instructions or '',
        'output_dir': args.output_dir,
        'comprehensive': args.comprehensive
    }
    
    try:
        # Initialize the ultimate system
        logger.info("Initializing Ultimate Flashcard Generation System...")
        system = UltimateFlashcardSystem(config)
        
        # Process content
        logger.info(f"Processing {source_type} content: {args.input}")
        result = system.process_content_comprehensive(args.input, source_type)
        
        # Export cards
        logger.info(f"Exporting {len(result['cards'])} cards in formats: {', '.join(formats)}")
        export_results = system.export_cards(result['cards'], args.output, formats)
        
        # Print summary
        print(f"\n{'='*60}")
        print("ULTIMATE FLASHCARD GENERATION COMPLETE")
        print(f"{'='*60}")
        print(f"Source: {args.input}")
        print(f"Source Type: {source_type}")
        print(f"Total Cards Generated: {result['total_cards']}")
        print(f"Comprehensive Mode: {'Yes' if config['comprehensive'] else 'No'}")
        print(f"Gemini AI: {'Yes' if config['use_gemini'] and config['gemini_api_key'] else 'No'}")
        print(f"\nExported Files:")
        for format_type, file_path in export_results.items():
            if file_path:
                print(f"  {format_type.upper()}: {file_path}")
            else:
                print(f"  {format_type.upper()}: Export failed")
        
        print(f"\n🎉 Ready for complete content mastery!")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
