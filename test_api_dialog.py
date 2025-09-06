#!/usr/bin/env python3
"""
Test API Key Dialog
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from app.ui.gui.api_key_dialog import APIKeyDialog


def test_api_dialog():
    """Test the API key dialog"""
    app = QApplication(sys.argv)
    
    dialog = APIKeyDialog()
    dialog.show()
    
    return app.exec()


if __name__ == "__main__":
    test_api_dialog()
