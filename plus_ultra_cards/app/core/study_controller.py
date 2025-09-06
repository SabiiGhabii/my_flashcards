from dataclasses import dataclass
from typing import Optional

from app.formatting.formatter_service import FormatterService, RenderingOptions
from app.core.card_type_factory import card_type_factory


@dataclass
class ViewState:
    html: str
    answer_visible: bool


class StudyController:
    """Headless controller skeleton.
    Not wired to UI yet; used to validate contracts.
    """

    def __init__(self):
        self._fmt = FormatterService()

    def render_front(self, front_text: str, inline_css: str = "") -> ViewState:
        ct = card_type_factory.get_card_type(front_text)
        options = RenderingOptions(reveal_cloze=False, apply_syntax_highlighting=True, inline_css=inline_css)
        html = ct.render_front(front_text, options, self._fmt)
        return ViewState(html=html, answer_visible=False)

    def render_answer(self, front_text: str, inline_css: str = "") -> ViewState:
        ct = card_type_factory.get_card_type(front_text)
        options = RenderingOptions(reveal_cloze=True, apply_syntax_highlighting=True, inline_css=inline_css)
        html = ct.render_back(front_text, options, self._fmt)
        return ViewState(html=html, answer_visible=True)

