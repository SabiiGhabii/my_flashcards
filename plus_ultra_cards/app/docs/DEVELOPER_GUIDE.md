# Plus Ultra Cards Developer Guide

## Architecture Overview

Plus Ultra Cards follows a layered architecture with clear separation of concerns:

- **Presentation Layer**: Qt views and controllers
- **Domain Layer**: Card types, study logic, business rules
- **Infrastructure Layer**: Database, SRS engines, external services
- **Formatting Layer**: Text rendering pipeline

## Key Components

### Card Type System

Card types are implemented via the `CardType` protocol:

```python
from app.domain.cards import CardType, CardTypeRegistry

class MyCardType:
    def is_match(self, front_text: str) -> bool:
        return "{{my::" in front_text
    
    def is_single_sided(self) -> bool:
        return True
    
    def render_front(self, text: str, options: RenderingOptions, fmt: FormatterService) -> str:
        return fmt.render(text, options)
    
    def render_answer(self, text: str, options: RenderingOptions, fmt: FormatterService) -> str:
        return fmt.render(text, options)

# Register your card type
registry = CardTypeRegistry()
registry._types.insert(0, MyCardType())  # Higher priority
```

### SRS Engine Integration

SRS engines implement the `SrsEngine` protocol:

```python
from app.srs.interfaces import SrsEngine

class MyEngine(SrsEngine):
    def register(self, item_ids: List[int], cloze_map: Optional[Dict[int, List[int]]] = None) -> None:
        # Register cards with your engine
        pass
    
    def next_items(self, k: int) -> List[int]:
        # Return next k items for study
        return []
    
    def record_outcome(self, item_id: int, outcome: str, metadata: Optional[Dict] = None) -> None:
        # Record study outcome
        pass
```

Add to factory in `app/srs/factory.py`:

```python
def create(db, deck_id: int) -> SrsEngine:
    cfg = get_config()
    engine = cfg.get('srs.engine', 'deeptutor').lower()
    if engine == 'myengine':
        return MyEngine(db, deck_id)
    # ... existing engines
```

### Rendering Pipeline

The rendering pipeline processes text in deterministic stages:

1. **Tokenization**: Cloze and style markup → placeholders
2. **Style Processing**: Code blocks, formatting
3. **HTML Generation**: Escape text, apply syntax highlighting
4. **Token Replacement**: Replace placeholders with final HTML
5. **Sanitization**: Clean output

Use via `FormatterService`:

```python
from app.formatting import FormatterService, RenderingOptions

fmt = FormatterService()
html = fmt.render(text, RenderingOptions(
    reveal_cloze=True,
    apply_syntax_highlighting=False,
    inline_css="color: red;"
))
```

## Testing

Run tests with:
```bash
python -m pytest tests/
```

Key test categories:
- `tests/test_formatter_service_facade.py`: Rendering pipeline
- `tests/test_card_type_registry.py`: Card type resolution
- `tests/test_srs_factory.py`: SRS engine selection
- `tests/test_card_service.py`: Business logic

## Configuration

Configuration is centralized in `app/core/config_manager.py`:

```python
from app.core.config_manager import get_config

config = get_config()
value = config.get('section.key', default_value)
config.set('section.key', new_value)
```

## Error Handling

Use typed errors from `app.core.errors`:

```python
from app.core.errors import RenderingError, StudyStateError

try:
    # risky operation
    pass
except Exception as e:
    raise RenderingError("Failed to render", card_id=123, stage="tokenization") from e
```

## Logging

Use structured logging:

```python
from app.core.logger import Logger

log = Logger("my_component")
log.info("Operation completed", card_id=123, duration_ms=45)
log.error("Operation failed", card_id=123, error=str(e))
```
