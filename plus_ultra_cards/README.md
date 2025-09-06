# Plus Ultra Cards

A sophisticated flashcard application combining the best features of Anki and Quizlet with advanced spaced repetition algorithms and a nostalgic Windows 95 interface.

## Overview

Plus Ultra Cards is an advanced study application that leverages DeepTutor's reinforcement learning-based spaced repetition system alongside traditional study modes. The application features a retro Windows 95 aesthetic while providing modern functionality for effective learning and retention.

## Features

### Study Modes
- **Cram Mode**: Quizlet-style rapid learning with multiple rounds and immediate feedback
- **Ingrain Mode**: Hybrid approach combining short-term repetition with long-term spaced repetition
- **Review Mode**: Advanced spaced repetition using DeepTutor's RL-based algorithms
- **Free Recall Mode**: Memory testing without prompts using similarity scoring

### Card Types
- **Front/Back Cards**: Traditional flashcards with optional hints, exceptions, and key terms
- **Cloze Deletion Cards**: Multiple cloze deletions with easy creation UI and full integration

### Advanced Features
- **Code Formatting**: Syntax highlighting for Python, C++, Rust, R with preserved indentation
- **Template System**: Customizable card layouts including retro terminal and code-specific themes
- **DeepTutor Integration**: State-of-the-art RL-based spaced repetition algorithms
- **Statistics Tracking**: Comprehensive progress analytics and performance metrics
- **CSV Import/Export**: Bulk card management and data portability

### User Interface
- **Retro95 Theme**: Authentic Windows 95 styling with pixel-perfect recreation
- **Neobrutalist Design**: Bold borders, high-contrast colors, and geometric shadows
- **Customizable Colors**: 3-4 major colors selectable through View menu
- **Modular Architecture**: Clean separation of concerns with loose coupling

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- PySide6 >= 6.5.0 (GUI framework)
- numpy >= 1.21.0 (numerical computations)
- gymnasium >= 0.29.1 (RL environment interface)
- stable-baselines3 >= 2.2.0 (RL algorithms)
- sb3-contrib >= 2.2.0 (additional RL algorithms)
- torch >= 2.1.0 (deep learning backend)
- plotly >= 5.22.0 (statistics visualization)
- pyvis >= 0.3.2 (network visualization)

### Setup
1. Clone or download the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python main.py`

## Usage

### Getting Started
1. Launch the application with `python main.py`
2. Create your first deck using the "New Deck" button
3. Add cards manually or import from CSV
4. Select a study mode and begin learning

### CSV Import Format
Your CSV file should include these columns:
- `front` (required): Front side of the card
- `back` (required): Back side of the card
- `tags` (optional): Comma-separated tags
- `hint` (optional): Hint text
- `exceptions` (optional): Exception notes
- `key_terms` (optional): Important terms

Example:
```csv
front,back,tags,hint
"What is the capital of France?","Paris","geography,europe","Think of the Eiffel Tower"
"def fibonacci(n):","Recursive function implementation","python,algorithms","Base cases: 0 and 1"
```

### Code Formatting
Use markup syntax for enhanced code display:
```
{start.style::code[python]}
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
{end.style}
```

Supported languages: Python, C++, Rust, R, JavaScript, Java, C#, Go

## Architecture

### Core Components
- **Database Layer** (`app/core/database.py`): SQLite operations and schema management
- **Card Manager** (`app/core/card_manager.py`): Card and deck operations with DeepTutor integration
- **Study Sessions** (`app/core/study_sessions.py`): Implementation of all study modes
- **SRS Factory** (`app/srs/factory.py`): Pluggable SRS engine selection
- **DeepTutor Adapter** (`app/srs/dt_adapter.py`): RL-based spaced repetition integration

### User Interface
- **Main Window** (`app/ui/gui/main_window.py`): Primary application interface
- **Card Editor** (`app/ui/gui/card_editor.py`): Card creation and editing dialogs
- **Study Window** (`app/ui/gui/study_window.py`): Study session interfaces
- **Retro95 Theme** (`app/ui/retro95.py`): Windows 95 styling framework

### Data Management
- **Templates** (`data/card_templates.json`): Predefined card styling templates
- **Layout** (`data/deck_layout.json`): Deck grid layout configuration
- **Theme** (`data/theme_config.json`): Neobrutalist color scheme settings
- **Database** (`data/cards.db`): SQLite database for cards, decks, and SRS data

## Database Schema

### Core Tables
- **decks**: Deck metadata and configuration
- **cards**: Card content with template data
- **srs_data**: Spaced repetition scheduling information
- **study_sessions**: Session tracking and statistics
- **card_reviews**: Individual review history
- **dt_models**: DeepTutor model states and policies

### DeepTutor Integration
- **EFC/HLR/DASH Models**: Student environment implementations
- **RecurrentPPO Policy**: LSTM-based RL policy for scheduling
- **Item Mapping**: Card-to-environment item index mapping
- **State Persistence**: Environment and policy serialization

## Development

### Project Structure
```
plus_ultra_cards/
├── main.py                     # Application entry point
├── app/
│   ├── core/                   # Core business logic
│   ├── ui/                     # User interface components
│   ├── srs/                    # Spaced repetition systems
│   ├── formatting/             # Text and code formatting
│   └── docs/                   # Documentation
├── data/                       # Configuration and database
├── tests/                      # Unit tests
└── requirements.txt            # Dependencies
```

### Key Design Principles
- Modular architecture with clear separation of concerns
- Loose coupling between components
- Comprehensive error handling
- Extensible plugin architecture
- Performance optimization for large datasets

## Testing

Run tests with:
```bash
python -m pytest tests/
```

Current test coverage includes:
- DeepTutor adapter functionality
- Database operations
- Card management operations

## Contributing

1. Follow the existing code style and architecture patterns
2. Add comprehensive tests for new functionality
3. Update documentation for any API changes
4. Ensure compatibility with the retro95 theme system

## License

This project is developed as an educational tool. Please respect the original DeepTutor license and PySide6 licensing terms.

## Acknowledgments

- DeepTutor project for advanced SRS algorithms
- PySide6/Qt for the robust GUI framework
- SuperMemo for foundational SM-2 algorithm concepts
- The retro computing community for design inspiration
