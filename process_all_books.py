#!/usr/bin/env python3
"""
Process all books in the books_to_cards folder
"""

import os
import sys
import time
import json
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.flashcard_generation import create_flashcard_generator, convert_cards_format
from app.core.card_manager import CardManager


def process_all_books():
    """Process all books in the books_to_cards folder"""
    print("Processing All Books")
    print("=" * 60)
    
    # Find all books
    books_dir = Path("../books_to_cards")
    pdf_files = list(books_dir.glob("*.pdf"))
    epub_files = list(books_dir.glob("*.epub"))
    
    all_books = []
    for pdf_file in pdf_files:
        all_books.append((pdf_file, 'pdf'))
    for epub_file in epub_files:
        all_books.append((epub_file, 'epub'))
    
    print(f"Found {len(all_books)} books to process:")
    for book_file, book_type in all_books:
        print(f"  - {book_file.name} ({book_type.upper()})")
    
    # Initialize systems
    config = {
        'use_ai': False,  # Disable AI for faster processing
        'comprehensive': True,
        'max_cards_per_section': 150,  # Increase for more cards
        'output_dir': 'exports'
    }
    
    generator = create_flashcard_generator(config)
    card_manager = CardManager()
    
    # Statistics tracking
    total_stats = {
        'books_processed': 0,
        'total_cards': 0,
        'total_time': 0,
        'book_stats': [],
        'errors': []
    }
    
    # Process each book
    for i, (book_file, book_type) in enumerate(all_books, 1):
        print(f"\n{'-' * 60}")
        print(f"Processing Book {i}/{len(all_books)}: {book_file.name}")
        print(f"Type: {book_type.upper()}")
        print(f"{'-' * 60}")
        
        start_time = time.time()
        
        try:
            # Generate cards
            print("Generating flashcards...")
            result = generator.process_content_comprehensive(str(book_file), book_type)
            
            processing_time = time.time() - start_time
            
            print(f"✓ Generated {result['total_cards']} cards in {processing_time:.1f}s")
            
            # Convert to plus_ultra format
            converted_cards = convert_cards_format(result['cards'])
            
            # Count card types
            card_type_counts = {}
            for card in converted_cards:
                card_type = card.get('card_type', 'basic')
                card_type_counts[card_type] = card_type_counts.get(card_type, 0) + 1
            
            # Create deck name
            deck_name = f"{book_file.stem} - Auto Generated"
            
            # Try to create deck
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    if attempt > 0:
                        deck_name = f"{book_file.stem} - Auto Generated {attempt + 1}"
                    deck_id = card_manager.create_deck(deck_name)
                    break
                except Exception as e:
                    if attempt < max_attempts - 1:
                        continue
                    else:
                        raise e
            
            print(f"✓ Created deck: {deck_name}")
            
            # Add cards to deck
            added_count = 0
            for card_data in converted_cards:
                try:
                    card_manager.create_card(
                        deck_id=deck_id,
                        front=card_data['front'],
                        back=card_data['back'],
                        hint=card_data.get('hint', ''),
                        tags=card_data.get('tags', ''),
                        difficulty=card_data.get('difficulty', 2)
                    )
                    added_count += 1
                except Exception as e:
                    continue
            
            print(f"✓ Added {added_count} cards to deck")
            
            # Export cards
            export_base = f"book_{i}_{book_file.stem.replace(' ', '_')}"
            export_results = generator.export_cards(result['cards'], export_base, ['json', 'csv'])
            
            print(f"✓ Exported cards:")
            for format_type, filepath in export_results.items():
                if filepath:
                    print(f"    {format_type.upper()}: {Path(filepath).name}")
            
            # Record statistics
            book_stat = {
                'book_name': book_file.name,
                'book_type': book_type,
                'cards_generated': result['total_cards'],
                'cards_added': added_count,
                'card_types': card_type_counts,
                'processing_time': processing_time,
                'deck_name': deck_name,
                'deck_id': deck_id,
                'export_files': export_results
            }
            
            total_stats['book_stats'].append(book_stat)
            total_stats['books_processed'] += 1
            total_stats['total_cards'] += added_count
            total_stats['total_time'] += processing_time
            
            print(f"✓ Book processed successfully!")
            
        except Exception as e:
            error_info = {
                'book_name': book_file.name,
                'book_type': book_type,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
            total_stats['errors'].append(error_info)
            print(f"✗ Error processing book: {e}")
            continue
    
    # Print final statistics
    print(f"\n{'=' * 60}")
    print("PROCESSING COMPLETE!")
    print(f"{'=' * 60}")
    
    print(f"Books processed: {total_stats['books_processed']}/{len(all_books)}")
    print(f"Total cards generated: {total_stats['total_cards']}")
    print(f"Total processing time: {total_stats['total_time']:.1f}s")
    print(f"Average cards per book: {total_stats['total_cards'] / max(total_stats['books_processed'], 1):.0f}")
    print(f"Average time per book: {total_stats['total_time'] / max(total_stats['books_processed'], 1):.1f}s")
    
    if total_stats['errors']:
        print(f"\nErrors encountered: {len(total_stats['errors'])}")
        for error in total_stats['errors']:
            print(f"  - {error['book_name']}: {error['error']}")
    
    print(f"\nDetailed Statistics:")
    print(f"{'-' * 60}")
    
    # Aggregate card type statistics
    all_card_types = {}
    for book_stat in total_stats['book_stats']:
        for card_type, count in book_stat['card_types'].items():
            all_card_types[card_type] = all_card_types.get(card_type, 0) + count
    
    print(f"Card Type Distribution:")
    for card_type, count in all_card_types.items():
        percentage = (count / total_stats['total_cards']) * 100 if total_stats['total_cards'] > 0 else 0
        print(f"  {card_type}: {count} cards ({percentage:.1f}%)")
    
    print(f"\nPer-Book Statistics:")
    for book_stat in total_stats['book_stats']:
        print(f"\n{book_stat['book_name']} ({book_stat['book_type'].upper()}):")
        print(f"  Cards: {book_stat['cards_added']}")
        print(f"  Time: {book_stat['processing_time']:.1f}s")
        print(f"  Deck: {book_stat['deck_name']}")
        print(f"  Types: {book_stat['card_types']}")
    
    # Save statistics to file
    stats_file = f"processing_stats_{int(time.time())}.json"
    with open(stats_file, 'w') as f:
        json.dump(total_stats, f, indent=2, default=str)
    
    print(f"\n✓ Statistics saved to: {stats_file}")
    
    return total_stats


if __name__ == "__main__":
    process_all_books()
