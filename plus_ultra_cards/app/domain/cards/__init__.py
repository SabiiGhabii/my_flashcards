"""Domain aliases for card type abstractions during migration.
Prefer importing from app.domain.cards going forward.
"""
from app.core.card_types import (
    CardType,
    CardTypeRegistry,
    BasicCard,
    ClozeCard,
)
__all__ = [
    "CardType",
    "CardTypeRegistry",
    "BasicCard",
    "ClozeCard",
]

