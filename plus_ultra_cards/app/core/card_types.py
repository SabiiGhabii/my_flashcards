from dataclasses import dataclass
from typing import Protocol

from app.formatting.formatter_service import FormatterService, RenderingOptions


class CardType(Protocol):
    def is_match(self, front_text: str) -> bool: ...
    def is_single_sided(self) -> bool: ...
    def render_front(self, text: str, options: RenderingOptions, fmt: FormatterService) -> str: ...
    def render_answer(self, text: str, options: RenderingOptions, fmt: FormatterService) -> str: ...


@dataclass
class BasicCard:
    def is_match(self, front_text: str) -> bool:
        return "{{c" not in front_text
    def is_single_sided(self) -> bool:
        return False
    def render_front(self, text: str, options: RenderingOptions, fmt: FormatterService) -> str:
        return fmt.render(text, options)
    def render_answer(self, text: str, options: RenderingOptions, fmt: FormatterService) -> str:
        return fmt.render(text, options)


@dataclass
class ClozeCard:
    def is_match(self, front_text: str) -> bool:
        return "{{c" in front_text and "{{cin" not in front_text
    def is_single_sided(self) -> bool:
        return True
    def render_front(self, text: str, options: RenderingOptions, fmt: FormatterService) -> str:
        opts = RenderingOptions(reveal_cloze=False, apply_syntax_highlighting=options.apply_syntax_highlighting, inline_css=options.inline_css)
        return fmt.render(text, opts)
    def render_answer(self, text: str, options: RenderingOptions, fmt: FormatterService) -> str:
        opts = RenderingOptions(reveal_cloze=True, apply_syntax_highlighting=options.apply_syntax_highlighting, inline_css=options.inline_css)
        return fmt.render(text, opts)


@dataclass
class ClozeInputCard:
    def is_match(self, front_text: str) -> bool:
        return "{{cin" in front_text
    def is_single_sided(self) -> bool:
        return True
    def render_front(self, text: str, options: RenderingOptions, fmt: FormatterService) -> str:
        # For cloze input cards, use display-only rendering for QLabel compatibility
        return fmt.render_cloze_input_for_display(text, options.apply_syntax_highlighting)
    def render_answer(self, text: str, options: RenderingOptions, fmt: FormatterService) -> str:
        # For answer view, show the correct answers
        return fmt.render_cloze_input_revealed(text, options.apply_syntax_highlighting)


class CardTypeRegistry:
    def __init__(self):
        self._types = [ClozeInputCard(), ClozeCard(), BasicCard()]

    def resolve(self, front_text: str) -> CardType:
        for t in self._types:
            if t.is_match(front_text):
                return t
        return BasicCard()

    def get_card_type(self, front_text: str) -> CardType:
        """Alias for resolve method for API consistency"""
        return self.resolve(front_text)

