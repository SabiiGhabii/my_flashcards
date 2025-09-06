#!/usr/bin/env python3
"""
Migration script to fix tag formatting issue

This script fixes the bug where tags were stored as strings instead of lists,
causing character-by-character comma separation in the UI.
"""

import json
import sqlite3
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import Database


def normalize_tags(tags_data):
    """Normalize tags to proper list format"""
    if not tags_data:
        return []
    
    try:
        # Try to parse as JSON first
        parsed = json.loads(tags_data)
        
        if isinstance(parsed, list):
            # Already a list, clean up any empty strings
            return [tag.strip() for tag in parsed if tag and tag.strip()]
        
        if isinstance(parsed, str):
            # It's a string that was JSON-encoded
            if ',' in parsed:
                # Split comma-separated string into list
                return [tag.strip() for tag in parsed.split(',') if tag and tag.strip()]
            else:
                # Single tag
                return [parsed.strip()] if parsed.strip() else []
        
        # Convert other types to string first
        return [str(parsed).strip()] if str(parsed).strip() else []
        
    except json.JSONDecodeError:
        # If it's not valid JSON, treat as plain string
        if isinstance(tags_data, str):
            if ',' in tags_data:
                return [tag.strip() for tag in tags_data.split(',') if tag and tag.strip()]
            else:
                return [tags_data.strip()] if tags_data.strip() else []
        
        return []


def analyze_tag_issues(db_path="data/cards.db"):
    """Analyze existing tag issues in the database"""
    print("Analyzing tag issues in database...")
    print("=" * 50)
    
    db = Database(db_path)
    
    # Get all cards
    cursor = db.conn.cursor()
    cursor.execute("SELECT id, tags FROM cards")
    cards = cursor.fetchall()
    
    issues_found = 0
    total_cards = len(cards)
    
    print(f"Total cards: {total_cards}")
    
    for card_id, tags_data in cards:
        try:
            parsed_tags = json.loads(tags_data)
            
            # Check if it's a string (the bug case)
            if isinstance(parsed_tags, str) and parsed_tags:
                print(f"Card {card_id}: Found string tags: '{parsed_tags}'")
                
                # Show what it would become
                normalized = normalize_tags(tags_data)
                print(f"  -> Would become: {normalized}")
                
                issues_found += 1
                
                if issues_found <= 5:  # Show first 5 examples
                    print()
        
        except json.JSONDecodeError:
            print(f"Card {card_id}: Invalid JSON in tags: {tags_data}")
            issues_found += 1
    
    print(f"\nSummary:")
    print(f"Cards with tag issues: {issues_found}")
    print(f"Cards without issues: {total_cards - issues_found}")
    
    db.close()
    return issues_found


def fix_tag_issues(db_path="data/cards.db", dry_run=True):
    """Fix tag formatting issues in the database"""
    print(f"{'DRY RUN: ' if dry_run else ''}Fixing tag issues in database...")
    print("=" * 50)
    
    db = Database(db_path)
    
    # Get all cards
    cursor = db.conn.cursor()
    cursor.execute("SELECT id, tags FROM cards")
    cards = cursor.fetchall()
    
    fixed_count = 0
    total_cards = len(cards)
    
    for card_id, tags_data in cards:
        try:
            parsed_tags = json.loads(tags_data)
            
            # Check if it's a string (the bug case)
            if isinstance(parsed_tags, str) and parsed_tags:
                # Normalize the tags
                normalized_tags = normalize_tags(tags_data)
                
                print(f"Card {card_id}:")
                print(f"  Before: '{parsed_tags}'")
                print(f"  After:  {normalized_tags}")
                
                if not dry_run:
                    # Update the database
                    new_tags_json = json.dumps(normalized_tags)
                    cursor.execute(
                        "UPDATE cards SET tags = ? WHERE id = ?",
                        (new_tags_json, card_id)
                    )
                
                fixed_count += 1
        
        except json.JSONDecodeError:
            print(f"Card {card_id}: Skipping invalid JSON: {tags_data}")
    
    if not dry_run:
        db.conn.commit()
        print(f"\n✓ Database updated successfully!")
    else:
        print(f"\n(DRY RUN - no changes made)")
    
    print(f"\nSummary:")
    print(f"Cards fixed: {fixed_count}")
    print(f"Total cards: {total_cards}")
    
    db.close()
    return fixed_count


def test_tag_normalization():
    """Test the tag normalization function"""
    print("Testing tag normalization function...")
    print("=" * 50)
    
    test_cases = [
        # (input, expected_output, description)
        ('["tag1", "tag2", "tag3"]', ["tag1", "tag2", "tag3"], "Normal list"),
        ('"tag1,tag2,tag3"', ["tag1", "tag2", "tag3"], "Comma-separated string (bug case)"),
        ('"single_tag"', ["single_tag"], "Single tag string"),
        ('[]', [], "Empty list"),
        ('""', [], "Empty string"),
        ('["", "tag1", "", "tag2", ""]', ["tag1", "tag2"], "List with empty strings"),
        ('"tag1, tag2 , tag3 "', ["tag1", "tag2", "tag3"], "String with spaces"),
    ]
    
    all_passed = True
    
    for i, (input_data, expected, description) in enumerate(test_cases, 1):
        try:
            result = normalize_tags(input_data)
            passed = result == expected
            
            print(f"Test {i}: {description}")
            print(f"  Input:    {input_data}")
            print(f"  Expected: {expected}")
            print(f"  Result:   {result}")
            print(f"  Status:   {'✓ PASS' if passed else '✗ FAIL'}")
            print()
            
            if not passed:
                all_passed = False
                
        except Exception as e:
            print(f"Test {i}: {description}")
            print(f"  Input:    {input_data}")
            print(f"  Error:    {e}")
            print(f"  Status:   ✗ ERROR")
            print()
            all_passed = False
    
    print(f"Overall result: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    return all_passed


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fix_tags_migration.py test     - Test tag normalization")
        print("  python fix_tags_migration.py analyze  - Analyze tag issues")
        print("  python fix_tags_migration.py dry-run  - Show what would be fixed")
        print("  python fix_tags_migration.py fix      - Actually fix the issues")
        return
    
    command = sys.argv[1].lower()
    
    if command == "test":
        test_tag_normalization()
    
    elif command == "analyze":
        analyze_tag_issues()
    
    elif command == "dry-run":
        fix_tag_issues(dry_run=True)
    
    elif command == "fix":
        print("⚠️  This will modify your database!")
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() == "yes":
            fix_tag_issues(dry_run=False)
        else:
            print("Operation cancelled.")
    
    else:
        print(f"Unknown command: {command}")
        print("Use 'test', 'analyze', 'dry-run', or 'fix'")


if __name__ == "__main__":
    main()
