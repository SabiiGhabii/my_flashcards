"""
Plus Ultra Cards - Main Application Entry Point
An Anki-Quizlet hybrid study application with advanced spaced repetition.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMessageBox
from app.ui.gui.main_window import MainWindow
from app.ui.retro95 import apply_win95_theme


def check_dependencies():
    """Check if all required dependencies are available."""
    missing_deps = []

    # Core GUI framework
    try:
        import PySide6
    except ImportError:
        missing_deps.append("PySide6")

    # Database support (usually built-in)
    try:
        import sqlite3
    except ImportError:
        missing_deps.append("sqlite3")

    # NumPy for numerical operations
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")

    # DeepTutor dependencies
    try:
        import gymnasium
    except ImportError:
        missing_deps.append("gymnasium")

    try:
        import stable_baselines3
    except ImportError:
        missing_deps.append("stable-baselines3")

    try:
        import torch
    except ImportError:
        missing_deps.append("torch")

    if missing_deps:
        print("Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install missing dependencies using:")
        print("pip install -r requirements.txt")
        return False, missing_deps

    return True, []


def create_data_directory():
    """Create the data directory and required subdirectories if they don't exist."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Create subdirectories for organization
    (data_dir / "backups").mkdir(exist_ok=True)

    print(f"Data directory ready: {data_dir.absolute()}")
    return data_dir


def main():
    """Main application entry point."""
    # Check dependencies
    deps_ok, missing = check_dependencies()
    if not deps_ok:
        print(f"Missing required dependencies: {', '.join(missing)}")
        print("Please install them using: pip install PySide6")
        return 1
    
    # Create data directory
    try:
        create_data_directory()
    except Exception as e:
        print(f"Failed to create data directory: {e}")
        return 1
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Plus Ultra Cards")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Plus Ultra Cards")
    
    # Apply retro95 theme
    try:
        apply_win95_theme(app, base_point_size=10)
    except Exception as e:
        print(f"Warning: Failed to apply retro95 theme: {e}")
    
    # Create and show main window
    try:
        window = MainWindow()
        window.show()
        
        # Run application
        return app.exec()
        
    except Exception as e:
        QMessageBox.critical(None, "Application Error", 
                           f"Failed to start application:\n{str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
