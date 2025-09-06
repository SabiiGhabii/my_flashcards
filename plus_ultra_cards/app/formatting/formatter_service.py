from dataclasses import dataclass
from typing import Optional

from .text_formatter import TextFormatter


@dataclass
class RenderingOptions:
    reveal_cloze: bool = False
    apply_syntax_highlighting: bool = False
    inline_css: str = ""


class FormatterService:
    """Facade over TextFormatter enforcing a stable API for UI/controllers.
    Keeps behavior identical to current TextFormatter usage.
    """

    def __init__(self) -> None:
        self._tf = TextFormatter()

    def render(self, text: str, options: RenderingOptions) -> str:
        """Render text handling both standard and input clozes uniformly."""
        if "{{cin" in text:
            if options.reveal_cloze:
                html = self._tf.render_cloze_input_revealed(
                    text, apply_syntax_highlighting=options.apply_syntax_highlighting
                )
            else:
                html = self._tf.render_cloze_input_blanked(
                    text, apply_syntax_highlighting=options.apply_syntax_highlighting
                )
        elif options.reveal_cloze or "{{c" in text:
            if options.reveal_cloze:
                html = self._tf.render_cloze_revealed(
                    text, apply_syntax_highlighting=options.apply_syntax_highlighting
                )
            else:
                html = self._tf.render_cloze_blanked(
                    text, apply_syntax_highlighting=options.apply_syntax_highlighting
                )
        else:
            html = self._tf.render_to_html(
                text, apply_syntax_highlighting=options.apply_syntax_highlighting
            )

        if options.inline_css:
            return f"<div style=\"{options.inline_css}\">{html}</div>"
        return html

    def render_cloze_input_for_display(self, text: str, apply_syntax_highlighting: bool = True) -> str:
        """Render cloze input text for QLabel display with placeholder spans (no interactive elements)."""
        return self._tf.render_cloze_input_for_display(text, apply_syntax_highlighting)

    def render_cloze_input_blanked(self, text: str, apply_syntax_highlighting: bool = True) -> str:
        """Render text with cloze input blanks."""
        return self._tf.render_cloze_input_blanked(text, apply_syntax_highlighting)

    def render_cloze_input_revealed(self, text: str, apply_syntax_highlighting: bool = True) -> str:
        """Render text with cloze input answers revealed."""
        return self._tf.render_cloze_input_revealed(text, apply_syntax_highlighting)

