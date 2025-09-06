#!/usr/bin/env python3
"""
Copy EPUB file to simpler name
"""

import shutil
import os
from pathlib import Path

# Source file
source_dir = Path("../books_to_cards")
epub_files = list(source_dir.glob("*.epub"))

if epub_files:
    source_file = epub_files[0]
    dest_file = Path("neuro_symbolic_ai.epub")
    
    print(f"Copying {source_file.name} to {dest_file}")
    shutil.copy2(source_file, dest_file)
    print(f"✓ File copied successfully")
    print(f"File size: {dest_file.stat().st_size} bytes")
else:
    print("No EPUB files found")
