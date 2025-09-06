#!/usr/bin/env python3
"""
Test EPUB functionality
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def test_epub_support():
    """Test EPUB support"""
    print("Testing EPUB Support")
    print("=" * 50)
    
    try:
        # Test ebooklib import
        import ebooklib
        from ebooklib import epub
        print("✓ ebooklib imported successfully")
        
        # Test our EPUB processor
        from app.flashcard_generation.core.content_processors import EPUBSource, HAS_EPUB_SUPPORT
        print(f"✓ EPUBSource imported, HAS_EPUB_SUPPORT: {HAS_EPUB_SUPPORT}")
        
        # Test with actual EPUB file
        epub_file = "../books_to_cards/Neuro-Symbolic AI _ Design Transparent and Trustworthy -- Alexiei Dingli , David Farrugia -- 1, 2023 -- Packt Publishing Pvt Ltd -- 9781804616956 -- a261259aa4a6cfb633e894ecd89f1bf1 -- Anna's Archive (1).epub"
        
        if Path(epub_file).exists():
            print(f"✓ EPUB file exists: {Path(epub_file).name}")
            
            # Test content extraction
            epub_source = EPUBSource()
            content = epub_source.extract_content(epub_file)
            print(f"✓ Content extracted: {len(content)} characters")
            print(f"First 200 chars: {content[:200]}...")
            
            # Test section splitting
            sections = epub_source.get_sections(content)
            print(f"✓ Sections extracted: {len(sections)} sections")
            
            for i, (title, paragraphs) in enumerate(sections[:3]):
                print(f"  Section {i+1}: {title} ({len(paragraphs)} paragraphs)")
        else:
            print(f"✗ EPUB file not found: {epub_file}")
        
        # Test FlashcardifyEnhanced with EPUB
        from app.flashcard_generation.core.content_processors import FlashcardifyEnhanced, Config
        
        config = Config(use_ai=False, max_cards_per_section=5)
        enhanced = FlashcardifyEnhanced(config)
        
        print(f"✓ FlashcardifyEnhanced created")
        print(f"Available sources: {list(enhanced.sources.keys())}")
        print(f"EPUB source available: {'epub' in enhanced.sources and enhanced.sources['epub'] is not None}")
        
        if Path(epub_file).exists() and enhanced.sources.get('epub'):
            print("Testing card generation...")
            cards = enhanced.process_content(epub_file, 'epub')
            print(f"✓ Generated {len(cards)} cards")
            
            if cards:
                print("Sample card:")
                print(f"  Type: {cards[0].get('type')}")
                print(f"  Front: {cards[0].get('front', '')[:100]}...")
                print(f"  Back: {cards[0].get('back', '')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_epub_support()
