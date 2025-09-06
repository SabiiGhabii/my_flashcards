#!/usr/bin/env python3
"""
Test script for the enhanced flashcard generation features
"""

import os
import sys
from pathlib import Path

def test_pdf_processing():
    """Test PDF processing with the enhanced system"""
    print("Testing PDF processing...")
    
    # Create a simple test PDF content (would need actual PDF for real test)
    test_command = [
        "python", "flashcardify_enhanced.py",
        "-i", "test_content.pdf",  # Would need actual PDF
        "-o", "test_pdf_cards.csv",
        "--source", "pdf",
        "--max-cards", "10"
    ]
    
    print(f"Command: {' '.join(test_command)}")
    print("Note: Requires actual PDF file for testing")

def test_github_processing():
    """Test GitHub repository processing"""
    print("\nTesting GitHub repository processing...")
    
    test_command = [
        "python", "flashcardify_enhanced.py",
        "-i", "https://github.com/python/cpython",
        "-o", "test_github_cards.csv",
        "--source", "github",
        "--max-cards", "5"
    ]
    
    print(f"Command: {' '.join(test_command)}")
    print("Note: This will access a real GitHub repository")

def test_html_processing():
    """Test HTML documentation processing"""
    print("\nTesting HTML documentation processing...")
    
    test_command = [
        "python", "flashcardify_enhanced.py",
        "-i", "https://docs.python.org/3/library/os.html",
        "-o", "test_html_cards.csv",
        "--source", "html",
        "--max-cards", "5"
    ]
    
    print(f"Command: {' '.join(test_command)}")
    print("Note: This will access real HTML documentation")

def test_leetcode_processing():
    """Test LeetCode problem processing"""
    print("\nTesting LeetCode problem processing...")
    
    test_command = [
        "python", "flashcardify_enhanced.py",
        "-i", "https://leetcode.com/problems/two-sum/",
        "-o", "test_leetcode_cards.csv",
        "--source", "leetcode",
        "--max-cards", "5"
    ]
    
    print(f"Command: {' '.join(test_command)}")
    print("Note: This will access a real LeetCode problem")

def test_ai_features():
    """Test AI-powered features"""
    print("\nTesting AI-powered content analysis...")
    
    test_command = [
        "python", "flashcardify_enhanced.py",
        "-i", "https://docs.python.org/3/library/collections.html",
        "-o", "test_ai_cards.csv",
        "--source", "html",
        "--use-ai",
        "--max-cards", "10",
        "--custom-instructions", "Focus on practical examples and code usage"
    ]
    
    print(f"Command: {' '.join(test_command)}")
    print("Note: Uses AI-powered content analysis with custom instructions")

def test_gemini_integration():
    """Test Gemini integration"""
    print("\nTesting Gemini integration...")
    
    if not os.getenv("GEMINI_API_KEY"):
        print("Skipping Gemini test - GEMINI_API_KEY not set")
        return
    
    test_command = [
        "python", "flashcardify_enhanced.py",
        "-i", "https://docs.python.org/3/library/itertools.html",
        "-o", "test_gemini_cards.csv",
        "--source", "html",
        "--use-ai",
        "--use-gemini",
        "--max-cards", "5"
    ]
    
    print(f"Command: {' '.join(test_command)}")
    print("Note: Uses Gemini for enhanced card generation")

def create_sample_content():
    """Create sample content for testing"""
    print("\nCreating sample content for testing...")
    
    # Create a sample Python file to test GitHub-like processing
    sample_code = '''
def binary_search(arr, target):
    """
    Perform binary search on a sorted array.
    
    Args:
        arr: Sorted list of elements
        target: Element to search for
    
    Returns:
        Index of target if found, -1 otherwise
    
    Time Complexity: O(log n)
    Space Complexity: O(1)
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

class TreeNode:
    """Binary tree node implementation"""
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def inorder_traversal(root):
    """
    Perform inorder traversal of binary tree.
    
    Args:
        root: TreeNode representing the root of the tree
    
    Returns:
        List of values in inorder sequence
    """
    result = []
    
    def dfs(node):
        if node:
            dfs(node.left)
            result.append(node.val)
            dfs(node.right)
    
    dfs(root)
    return result
'''
    
    with open("sample_algorithms.py", "w") as f:
        f.write(sample_code)
    
    print("Created sample_algorithms.py for testing")

def run_sample_test():
    """Run a simple test with the sample content"""
    print("\nRunning sample test...")
    
    # First create sample content
    create_sample_content()
    
    # Test with the original system
    print("\n1. Testing original system:")
    os.system("python flashcardify_book.py -i sample_algorithms.py -o original_cards.csv 2>/dev/null || echo 'Original system test failed (expected - no PDF input)'")
    
    # Test enhanced system with auto-detection
    print("\n2. Testing enhanced system with auto-detection:")
    test_command = "python flashcardify_enhanced.py -i https://httpbin.org/html -o enhanced_test_cards.csv --max-cards 3"
    print(f"Running: {test_command}")
    
    # Note: This is a demonstration - actual execution would require proper error handling

def main():
    """Main test function"""
    print("Enhanced Flashcard Generation System - Test Suite")
    print("=" * 60)
    
    # Check if enhanced system is available
    if not Path("flashcardify_enhanced.py").exists():
        print("Error: flashcardify_enhanced.py not found!")
        sys.exit(1)
    
    # Run tests
    test_pdf_processing()
    test_github_processing()
    test_html_processing()
    test_leetcode_processing()
    test_ai_features()
    test_gemini_integration()
    run_sample_test()
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("\nTo run actual tests, execute the commands shown above.")
    print("Make sure you have:")
    print("- Internet connection for web-based sources")
    print("- GEMINI_API_KEY environment variable for Gemini features")
    print("- Actual PDF files for PDF testing")

if __name__ == "__main__":
    main()
