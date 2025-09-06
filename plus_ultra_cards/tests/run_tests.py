#!/usr/bin/env python3
"""
Test runner for Plus Ultra Cards test suite.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_tests():
    """Run the complete test suite."""
    print("Plus Ultra Cards - Test Suite Runner")
    print("=" * 50)
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("ERROR: pytest is not installed.")
        print("Please install it with: pip install pytest")
        return 1
    
    # Test files to run
    test_files = [
        "tests/test_database.py",
        "tests/test_config_manager.py", 
        "tests/test_card_manager.py",
        "tests/test_dt_adapter.py"
    ]
    
    # Check which test files exist
    existing_tests = []
    for test_file in test_files:
        if os.path.exists(test_file):
            existing_tests.append(test_file)
        else:
            print(f"Warning: {test_file} not found, skipping...")
    
    if not existing_tests:
        print("ERROR: No test files found!")
        return 1
    
    print(f"Running {len(existing_tests)} test files...")
    print()
    
    # Run tests with pytest
    try:
        # Run with verbose output and coverage if available
        cmd = [
            sys.executable, "-m", "pytest",
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            "--strict-markers",  # Strict marker checking
        ]
        
        # Add coverage if available
        try:
            import coverage
            cmd.extend([
                "--cov=app",  # Coverage for app directory
                "--cov-report=term-missing",  # Show missing lines
                "--cov-report=html:htmlcov",  # HTML coverage report
            ])
            print("Running with coverage analysis...")
        except ImportError:
            print("Running without coverage (install pytest-cov for coverage analysis)")
        
        # Add test files
        cmd.extend(existing_tests)
        
        # Run the tests
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
        
    except Exception as e:
        print(f"ERROR running tests: {e}")
        return 1


def run_specific_test(test_name):
    """Run a specific test file or test function."""
    print(f"Running specific test: {test_name}")
    print("=" * 50)
    
    try:
        cmd = [
            sys.executable, "-m", "pytest",
            "-v",
            "--tb=short",
            test_name
        ]
        
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
        
    except Exception as e:
        print(f"ERROR running test: {e}")
        return 1


def check_dependencies():
    """Check if all required dependencies for testing are available."""
    print("Checking test dependencies...")
    
    required_packages = [
        "pytest",
        "PySide6",
        "numpy", 
        "gymnasium",
        "stable_baselines3",
        "torch"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("\nAll dependencies available!")
    return True


def main():
    """Main test runner entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--check-deps":
            return 0 if check_dependencies() else 1
        elif sys.argv[1] == "--help":
            print("Plus Ultra Cards Test Runner")
            print("\nUsage:")
            print("  python tests/run_tests.py                 # Run all tests")
            print("  python tests/run_tests.py --check-deps    # Check dependencies")
            print("  python tests/run_tests.py <test_name>     # Run specific test")
            print("\nExamples:")
            print("  python tests/run_tests.py tests/test_database.py")
            print("  python tests/run_tests.py tests/test_card_manager.py::TestCardManager::test_create_card_success")
            return 0
        else:
            # Run specific test
            return run_specific_test(sys.argv[1])
    else:
        # Run all tests
        return run_tests()


if __name__ == "__main__":
    sys.exit(main())
