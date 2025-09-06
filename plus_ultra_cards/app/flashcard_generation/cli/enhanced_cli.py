#!/usr/bin/env python3
"""
Enhanced CLI for Flashcard Generation

This CLI provides access to the Ultimate Flashcard Generation System
from within the Plus Ultra Cards application.
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directories to path for imports
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent.parent
sys.path.insert(0, str(app_dir))

try:
    from app.flashcard_generation import (
        create_flashcard_generator,
        convert_cards_format,
        UltimateFlashcardSystem
    )
    from app.flashcard_generation.utils.export import FlashcardExporter
    HAS_GENERATION_SYSTEM = True
except ImportError as e:
    print(f"Warning: Flashcard generation system not available: {e}")
    HAS_GENERATION_SYSTEM = False


def main():
    """Main CLI entry point"""
    print("=" * 60)
    print("Plus Ultra Cards - Flashcard Generation CLI")
    print("=" * 60)
    
    if not HAS_GENERATION_SYSTEM:
        print("ERROR: Flashcard generation system not available.")
        print("Please ensure all dependencies are installed.")
        return 1
    
    parser = argparse.ArgumentParser(
        description="Generate flashcards from various sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from PDF
  python enhanced_cli.py -i document.pdf -o my_cards --source pdf
  
  # Generate from GitHub repository
  python enhanced_cli.py -i https://github.com/user/repo -o repo_cards --source github
  
  # Generate from HTML/URL
  python enhanced_cli.py -i https://example.com/docs -o web_cards --source html
  
  # Comprehensive mode with AI enhancement
  python enhanced_cli.py -i content.pdf -o cards --comprehensive --use-ai
        """
    )
    
    parser.add_argument("-i", "--input", required=True,
                       help="Input source (PDF file, GitHub URL, HTML URL)")
    parser.add_argument("-o", "--output", default="flashcards",
                       help="Output base name (default: flashcards)")
    parser.add_argument("--source", choices=['pdf', 'github', 'html', 'epub'],
                       help="Source type (auto-detected if not specified)")
    parser.add_argument("--formats", default="json,csv",
                       help="Export formats: json,csv,anki (default: json,csv)")
    parser.add_argument("--comprehensive", action="store_true",
                       help="Enable comprehensive processing")
    parser.add_argument("--use-ai", action="store_true",
                       help="Use AI for enhanced card generation")
    parser.add_argument("--max-cards", type=int, default=100,
                       help="Maximum cards per section (default: 100)")
    parser.add_argument("--output-dir", default="exports",
                       help="Output directory (default: exports)")
    
    args = parser.parse_args()
    
    # Auto-detect source type if not specified
    source_type = args.source
    if not source_type:
        if args.input.endswith('.pdf'):
            source_type = 'pdf'
        elif args.input.endswith('.epub'):
            source_type = 'epub'
        elif 'github.com' in args.input:
            source_type = 'github'
        else:
            source_type = 'html'
    
    print(f"\nProcessing {source_type} source: {args.input}")
    print(f"Output: {args.output}")
    print(f"Formats: {args.formats}")
    print(f"Comprehensive mode: {args.comprehensive}")
    print(f"AI enhancement: {args.use_ai}")
    print("-" * 60)
    
    try:
        # Create configuration
        config = {
            'use_ai': args.use_ai,
            'comprehensive': args.comprehensive,
            'max_cards_per_section': args.max_cards,
            'output_dir': args.output_dir
        }
        
        # Create flashcard generator
        print("Initializing flashcard generation system...")
        generator = create_flashcard_generator(config)
        
        # Process content
        print("Processing content...")
        result = generator.process_content_comprehensive(args.input, source_type)
        
        print(f"Generated {result['total_cards']} cards")
        
        # Export cards
        formats = args.formats.split(',')
        print(f"Exporting in formats: {', '.join(formats)}")
        
        export_results = generator.export_cards(result['cards'], args.output, formats)
        
        print("\nExport Results:")
        for format_type, filepath in export_results.items():
            if filepath:
                print(f"  {format_type.upper()}: {filepath}")
            else:
                print(f"  {format_type.upper()}: FAILED")
        
        print("\nProcessing complete!")
        return 0
        
    except Exception as e:
        print(f"\nERROR: {e}")
        return 1


def interactive_mode():
    """Interactive mode for easier use"""
    print("\n" + "=" * 60)
    print("Interactive Flashcard Generation")
    print("=" * 60)
    
    while True:
        print("\nSelect source type:")
        print("1. PDF file")
        print("2. GitHub repository")
        print("3. HTML/URL")
        print("4. EPUB file")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()

        if choice == '5':
            break
        elif choice == '1':
            source_type = 'pdf'
            source = input("Enter PDF file path: ").strip()
        elif choice == '2':
            source_type = 'github'
            source = input("Enter GitHub repository URL: ").strip()
        elif choice == '3':
            source_type = 'html'
            source = input("Enter HTML/URL: ").strip()
        elif choice == '4':
            source_type = 'epub'
            source = input("Enter EPUB file path: ").strip()
        else:
            print("Invalid choice. Please try again.")
            continue
        
        if not source:
            print("No source provided. Please try again.")
            continue
        
        output_name = input("Enter output name (default: flashcards): ").strip()
        if not output_name:
            output_name = "flashcards"
        
        comprehensive = input("Use comprehensive mode? (y/n, default: y): ").strip().lower()
        comprehensive = comprehensive != 'n'
        
        use_ai = input("Use AI enhancement? (y/n, default: y): ").strip().lower()
        use_ai = use_ai != 'n'
        
        try:
            config = {
                'use_ai': use_ai,
                'comprehensive': comprehensive,
                'max_cards_per_section': 100,
                'output_dir': 'exports'
            }
            
            print(f"\nProcessing {source_type} source...")
            generator = create_flashcard_generator(config)
            result = generator.process_content_comprehensive(source, source_type)
            
            print(f"Generated {result['total_cards']} cards")
            
            # Export in multiple formats
            export_results = generator.export_cards(result['cards'], output_name, ['json', 'csv'])
            
            print("\nExport complete:")
            for format_type, filepath in export_results.items():
                if filepath:
                    print(f"  {format_type.upper()}: {filepath}")
            
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "-" * 60)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments provided, run interactive mode
        interactive_mode()
    else:
        # Arguments provided, run CLI mode
        sys.exit(main())
