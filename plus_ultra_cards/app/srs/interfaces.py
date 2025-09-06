from typing import List, Protocol, Any, Dict, Optional, runtime_checkable

@runtime_checkable
class SrsEngine(Protocol):
    """Protocol for spaced repetition engines.
    Concrete implementations: DeepTutorAdapter, SM2Engine, etc.
    """

    def register(self, item_ids: List[int], cloze_map: Optional[Dict[int, List[int]]] = None) -> None:
        ...

    def next_items(self, k: int) -> List[int]:
        ...

    def record_outcome(self, item_id: int, outcome: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        ...

