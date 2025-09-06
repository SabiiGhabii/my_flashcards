"""
Text Formatter Module for Plus Ultra Cards
Handles style markup parsing, whitespace preservation, and syntax highlighting integration.
"""

import re
import html
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class StyleSection:
    """Represents a styled section of text."""
    start_pos: int
    end_pos: int
    style_type: str
    language: Optional[str] = None
    content: str = ""


class TextFormatter:
    """
    Handles parsing and rendering of styled text with support for:
    - Style markup: {start.style::code[python]} ... {end.style}
    - Whitespace preservation
    - Syntax highlighting integration
    - Cloze deletion compatibility
    """
    
    # Supported programming languages for syntax highlighting
    SUPPORTED_LANGUAGES = {
        # Priority languages
        'python', 'cpp', 'c++', 'rust', 'r',
        # Additional languages
        'javascript', 'js', 'java', 'bash', 'shell', 'html', 'css', 'sql',
        'c', 'csharp', 'c#', 'powershell', 'go', 'clojure', 'ocaml', 'typescript', 'ts'
    }
    
    # Style markup patterns (legacy; tolerant patterns compiled in parse_markup)
    STYLE_START_PATTERN = r'\{start\.style::(\w+)(?:\[([^\]]+)\])?\}'
    STYLE_END_PATTERN = r'\{end\.style\}'
    # Choose closing '}}' that is not followed by another '}' to avoid overlap with
    # style marker braces like '{end.style}' right before the cloze terminator.
    CLOZE_PATTERN = r'\{\{c(\d+)::([\s\S]*?)\}\}(?!\})'
    # Cloze input pattern for interactive completion cards
    CLOZE_INPUT_PATTERN = r'\{\{cin(\d+)::([\s\S]*?)\}\}(?!\})'
    
    def __init__(self):
        self.style_sections: List[StyleSection] = []

    def parse_markup(self, text: str) -> Tuple[str, List[StyleSection]]:
        """
        Parse style markup and return clean text with style section metadata.
        - Case-insensitive for markers
        - Allows optional whitespace around tokens
        - Robust for multiple sections
        """
        self.style_sections = []

        # Tolerant patterns (case-insensitive; optional spaces)
        start_re = re.compile(r"\{\s*start\s*\.\s*style\s*::\s*([A-Za-z0-9_]+)(?:\s*\[\s*([^\]]+?)\s*\])?\s*\}", re.IGNORECASE)
        end_re = re.compile(r"\{\s*end\s*\.\s*style\s*\}", re.IGNORECASE)

        out_parts: List[str] = []
        sections: List[StyleSection] = []
        pos = 0
        out_len = 0  # length of output built so far (for section positions)

        while True:
            m = start_re.search(text, pos)
            if not m:
                break
            # Text before section
            before = text[pos:m.start()]
            if before:
                out_parts.append(before)
                out_len += len(before)

            # Find end after this start
            m_end = end_re.search(text, m.end())
            if not m_end:
                # No end marker: treat rest as normal text
                remainder = text[m.start():]
                out_parts.append(remainder)
                out_len += len(remainder)
                pos = len(text)
                break

            style_type = m.group(1) or ""
            language = (m.group(2) or None)
            content = text[m.end():m_end.start()]

            # Record section with positions relative to output (clean text)
            sec = StyleSection(
                start_pos=out_len,
                end_pos=out_len + len(content),
                style_type=style_type.lower(),
                language=(language.lower() if language else None),
                content=content,
            )
            sections.append(sec)

            # Append content (without markers) to output
            out_parts.append(content)
            out_len += len(content)

            pos = m_end.end()

        # Append trailing text
        if pos < len(text):
            tail = text[pos:]
            out_parts.append(tail)

        clean_text = ''.join(out_parts)
        self.style_sections = sections
        return clean_text, sections
    
    def preserve_whitespace(self, text: str) -> str:
        """
        Convert text to HTML with preserved whitespace and newlines.
        """
        # Escape HTML characters
        escaped = html.escape(text)
        
        # Convert newlines to <br> tags
        escaped = escaped.replace('\n', '<br>')
        
        # Convert multiple spaces to &nbsp; to preserve indentation
        escaped = re.sub(r'  +', lambda m: '&nbsp;' * len(m.group(0)), escaped)
        
        # Convert tabs to 4 spaces
        escaped = escaped.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        
        return escaped
    
    def render_to_html(self, text: str, apply_syntax_highlighting: bool = True) -> str:
        """
        Render text with style markup to HTML.
        Also applies basic markdown for non-code segments (headers, bold, italic, lists).
        """
        try:
            # First, extract mathematical expressions and replace with tokens
            text_with_math_tokens, math_token_map = self._process_mathematical_expressions(text)

            clean_text, sections = self.parse_markup(text_with_math_tokens)

            def _apply_basic_markdown(t: str) -> str:
                # Enhanced markdown subset with links and inline code
                import re
                # Headers
                t = re.sub(r'^###\s+(.*?)$', r'<h3>\1</h3>', t, flags=re.MULTILINE)
                t = re.sub(r'^##\s+(.*?)$', r'<h2>\1</h2>', t, flags=re.MULTILINE)
                t = re.sub(r'^#\s+(.*?)$', r'<h1>\1</h1>', t, flags=re.MULTILINE)

                # Links [text](url) - avoid conflicts with style markers by checking for :: and {}
                def safe_link_replace(match):
                    link_text, url = match.groups()
                    # Skip if this looks like it's inside a style marker or cloze
                    full_match = match.group(0)
                    if '::' in full_match or '{' in link_text or '}' in link_text:
                        return full_match  # leave unchanged
                    return f'<a href="{url}" target="_blank">{link_text}</a>'
                t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', safe_link_replace, t)

                # Inline code `code` - avoid conflicts with style sections
                def safe_code_replace(match):
                    code_content = match.group(1)
                    # Skip if this looks like it's part of a larger code block or style marker
                    if '{' in code_content or '}' in code_content or '::' in code_content:
                        return match.group(0)  # leave unchanged
                    return f'<code class="inline-code">{code_content}</code>'
                t = re.sub(r'`([^`]+)`', safe_code_replace, t)

                # Bold and italic
                t = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', t)
                t = re.sub(r'\*(.*?)\*', r'<em>\1</em>', t)

                # Simple list handling
                t = re.sub(r'^(?:-\s+)(.*)$', r'<ul><li>\1</li></ul>', t, flags=re.MULTILINE)
                return t

            if not sections:
                # No style sections, just markdown + whitespace
                md = _apply_basic_markdown(clean_text)
                html_result = self.preserve_whitespace(md)
            else:
                # Process sections
                html_parts = []
                last_pos = 0

                for section in sections:
                    # Add text before this section (apply markdown)
                    if section.start_pos > last_pos:
                        before_text = clean_text[last_pos:section.start_pos]
                        before_text = _apply_basic_markdown(before_text)
                        html_parts.append(self.preserve_whitespace(before_text))

                    # Render the styled section
                    section_html = self._render_section(section, apply_syntax_highlighting)
                    html_parts.append(section_html)

                    last_pos = section.end_pos

                # Add remaining text
                if last_pos < len(clean_text):
                    remaining_text = clean_text[last_pos:]
                    remaining_text = _apply_basic_markdown(remaining_text)
                    html_parts.append(self.preserve_whitespace(remaining_text))

                html_result = ''.join(html_parts)

            # Replace math tokens with their HTML
            for token in sorted(math_token_map.keys(), key=len, reverse=True):
                html_result = html_result.replace(token, math_token_map[token])

            return html_result
        except Exception as e:
            # Robust error handling: never crash rendering
            import html as html_escape
            safe = html_escape.escape(text[:500])  # Escape and truncate for safety
            return f'<div class="render-error">[Render error: {str(e)[:100]}]<br><pre>{safe}</pre></div>'

    def _process_mathematical_expressions(self, text: str) -> str:
        """Process mathematical expressions enclosed in $$ delimiters using token approach."""
        import re

        # Pattern to match $$....$$ expressions
        math_pattern = r'\$\$(.*?)\$\$'

        # Find all math expressions and replace with tokens
        matches = list(re.finditer(math_pattern, text, flags=re.DOTALL))
        if not matches:
            return text, {}

        token_map = {}
        text_with_tokens = text

        # Process matches in reverse order to maintain positions
        for i, match in enumerate(reversed(matches)):
            math_content = match.group(1).strip()
            if not math_content:
                continue

            # Create unique token
            token = f"__MATH_TOKEN_{i}_{len(token_map)}__"

            # Create math HTML
            math_id = f"math_{hash(math_content) % 10000}"
            math_html = f'''<div class="math-container" id="{math_id}">
                <div class="math-content">{self._render_latex_to_html(math_content)}</div>
            </div>'''

            token_map[token] = math_html

            # Replace in text with token
            text_with_tokens = text_with_tokens[:match.start()] + token + text_with_tokens[match.end():]

        return text_with_tokens, token_map

    def _render_latex_to_html(self, latex_content: str) -> str:
        """Convert LaTeX mathematical expression to HTML."""
        import re

        # For now, we'll use a simple approach that handles basic LaTeX
        # In a full implementation, this would use MathJax or KaTeX

        # Basic LaTeX to HTML conversions
        html_content = latex_content

        # Superscripts: x^2 -> x<sup>2</sup>
        html_content = re.sub(r'([a-zA-Z0-9\)])\^(\{[^}]+\}|[a-zA-Z0-9])',
                             r'\1<sup>\2</sup>', html_content)
        html_content = re.sub(r'<sup>\{([^}]+)\}</sup>', r'<sup>\1</sup>', html_content)

        # Subscripts: x_2 -> x<sub>2</sub>
        html_content = re.sub(r'([a-zA-Z0-9\)])_(\{[^}]+\}|[a-zA-Z0-9])',
                             r'\1<sub>\2</sub>', html_content)
        html_content = re.sub(r'<sub>\{([^}]+)\}</sub>', r'<sub>\1</sub>', html_content)

        # Fractions: \frac{a}{b} -> <span class="fraction">...</span>
        html_content = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}',
                             r'<span class="fraction"><span class="numerator">\1</span><span class="denominator">\2</span></span>',
                             html_content)

        # Square root: \sqrt{x} -> √(x)
        html_content = re.sub(r'\\sqrt\{([^}]+)\}', r'√(\1)', html_content)

        # Greek letters
        greek_letters = {
            r'\\alpha': 'α', r'\\beta': 'β', r'\\gamma': 'γ', r'\\delta': 'δ',
            r'\\epsilon': 'ε', r'\\theta': 'θ', r'\\lambda': 'λ', r'\\mu': 'μ',
            r'\\pi': 'π', r'\\sigma': 'σ', r'\\tau': 'τ', r'\\phi': 'φ',
            r'\\omega': 'ω', r'\\Omega': 'Ω', r'\\Delta': 'Δ', r'\\Gamma': 'Γ'
        }

        for latex_symbol, unicode_symbol in greek_letters.items():
            html_content = html_content.replace(latex_symbol, unicode_symbol)

        # Mathematical operators
        operators = {
            r'\\cdot': '·', r'\\times': '×', r'\\div': '÷',
            r'\\pm': '±', r'\\mp': '∓', r'\\leq': '≤', r'\\geq': '≥',
            r'\\neq': '≠', r'\\approx': '≈', r'\\equiv': '≡',
            r'\\sum': '∑', r'\\prod': '∏', r'\\int': '∫',
            r'\\infty': '∞', r'\\partial': '∂'
        }

        for latex_op, unicode_op in operators.items():
            html_content = html_content.replace(latex_op, unicode_op)

        return html_content

    def _render_section(self, section: StyleSection, apply_syntax_highlighting: bool) -> str:
        """Render a single style section to HTML."""
        content = section.content
        
        if section.style_type == 'code':
            return self._render_code_section(content, section.language, apply_syntax_highlighting)
        else:
            # Unknown style type, render as plain text with preserved whitespace
            return f'<div class="style-{section.style_type}">{self.preserve_whitespace(content)}</div>'
    
    def _render_code_section(self, content: str, language: Optional[str], 
                           apply_syntax_highlighting: bool) -> str:
        """Render a code section with optional syntax highlighting."""
        if apply_syntax_highlighting and language and language.lower() in self.SUPPORTED_LANGUAGES:
            try:
                from app.formatting.syntax_highlighter import SyntaxHighlighter
                highlighter = SyntaxHighlighter()
                highlighted = highlighter.highlight(content, language)
                return f'<div class="code-block" data-language="{language}">{highlighted}</div>'
            except ImportError:
                # Fallback if syntax highlighter not available
                pass
        
        # Fallback: render as plain code block with preserved formatting
        escaped_content = self.preserve_whitespace(content)
        lang_attr = f' data-language="{language}"' if language else ''
        return f'<pre class="code-block"{lang_attr}><code>{escaped_content}</code></pre>'
    
    def _render_with_cloze_placeholders(
        self,
        text: str,
        reveal: bool,
        apply_syntax_highlighting: bool,
        use_input_fields: bool = False,
    ) -> str:
        """Common pipeline to handle cloze before escaping and style parsing.
        - Replaces each cloze with a unique placeholder token (plain text)
        - Builds a map from token -> final HTML (blank span/input or revealed+rendered HTML)
        - Renders the remainder via render_to_html (which escapes text)
        - Finally replaces tokens with their HTML (post-escape), preventing raw HTML from being escaped
        """
        token_map: Dict[str, str] = {}
        token_counter = 0

        def repl_standard(m: re.Match) -> str:
            nonlocal token_counter
            token_counter += 1
            token = f"__CLOZE_TOKEN_{token_counter}__"
            inner = m.group(2)
            if reveal:
                # Render inner content to HTML so style markup like code blocks works
                # For cloze reveal, we do not need syntax highlighting; keep code clean
                inner_html = self.render_to_html(inner, apply_syntax_highlighting=False)
                # If the inner is a code block, show only the rendered code block (no green cloze span)
                if re.match(r'\s*(?:<div class="code-block"[\s\S]*</div>|<pre class="code-block"[\s\S]*</pre>)\s*$', inner_html):
                    token_map[token] = inner_html
                else:
                    token_map[token] = f'<span class="cloze-revealed">{inner_html}</span>'
            else:
                token_map[token] = '<span class="cloze-blank">[ … ]</span>'
            return token

        def repl_input(m: re.Match) -> str:
            nonlocal token_counter
            token_counter += 1
            token = f"__CLOZE_INPUT_TOKEN_{token_counter}__"
            cloze_num = m.group(1)
            inner = m.group(2)
            if reveal:
                # For cloze input, show the answer with different styling
                inner_html = self.render_to_html(inner, apply_syntax_highlighting=False)
                token_map[token] = (
                    f'<span class="cloze-input-revealed" data-cloze="{cloze_num}">{inner_html}</span>'
                )
            else:
                if use_input_fields:
                    token_map[token] = (
                        f'<input type="text" class="cloze-input-field" '
                        f'data-cloze="{cloze_num}" data-answer="{inner}" '
                        f'placeholder="Type answer..." />'
                    )
                else:
                    # For cloze input without interactive fields, show a blank span
                    token_map[token] = '<span class="cloze-input-blank">[ _____ ]</span>'
            return token

        # Replace standard clozes with tokens (DOTALL for multiline)
        text_with_tokens = re.sub(self.CLOZE_PATTERN, repl_standard, text, flags=re.DOTALL)

        # Replace cloze input with tokens (DOTALL for multiline)
        text_with_tokens = re.sub(self.CLOZE_INPUT_PATTERN, repl_input, text_with_tokens, flags=re.DOTALL)

        # Render the rest normally (this will escape the tokens literally)
        html_out = self.render_to_html(text_with_tokens, apply_syntax_highlighting)

        # Swap tokens for their HTML (post-escape, to avoid raw tags showing).
        # Replace from longest token to shortest to avoid accidental partial matches.
        for token in sorted(token_map.keys(), key=len, reverse=True):
            html_out = html_out.replace(token, token_map[token])
        return html_out

    def render_cloze_blanked(self, text: str, apply_syntax_highlighting: bool = True) -> str:
        """Render text with cloze deletions blanked out (for study mode front side)."""
        return self._render_with_cloze_placeholders(text, reveal=False, apply_syntax_highlighting=apply_syntax_highlighting)

    def render_cloze_revealed(self, text: str, apply_syntax_highlighting: bool = True) -> str:
        """Render text with cloze deletions revealed and highlighted (answer side)."""
        return self._render_with_cloze_placeholders(text, reveal=True, apply_syntax_highlighting=apply_syntax_highlighting)

    def render_cloze_input_blanked(self, text: str, apply_syntax_highlighting: bool = True) -> str:
        """Render text with cloze input fields for user interaction."""
        return self._render_with_cloze_placeholders(
            text,
            reveal=False,
            apply_syntax_highlighting=apply_syntax_highlighting,
            use_input_fields=True,
        )

    def render_cloze_input_revealed(self, text: str, apply_syntax_highlighting: bool = True) -> str:
        """Render text with cloze input answers revealed."""
        return self._render_with_cloze_placeholders(
            text,
            reveal=True,
            apply_syntax_highlighting=apply_syntax_highlighting,
            use_input_fields=True,
        )

    def render_cloze_input_for_display(self, text: str, apply_syntax_highlighting: bool = True) -> str:
        """Render cloze input text for QLabel display with placeholder spans (no interactive elements)."""
        import re

        # Pattern to match {{cin1::answer}} format for display-only placeholders
        cloze_input_pattern = self.CLOZE_INPUT_PATTERN

        # Find all cloze input matches
        matches = list(re.finditer(cloze_input_pattern, text, flags=re.DOTALL))
        if not matches:
            # No cloze input patterns, render normally
            return self.render_to_html(text, apply_syntax_highlighting)

        # Create placeholders and build token map
        token_map = {}
        text_with_tokens = text

        # Process matches in reverse order to maintain positions
        for match in reversed(matches):
            cloze_num = match.group(1)
            answer = match.group(2)

            # Create unique token
            token = f"__CLOZE_DISPLAY_TOKEN_{cloze_num}_{len(token_map)}__"

            # Create placeholder span for overlay positioning
            placeholder_id = f"cloze_placeholder_{cloze_num}"
            html_replacement = f'<span id="{placeholder_id}" class="cloze-input-placeholder" style="background-color: #f0f0f0; border: 1px dashed #999; padding: 2px 8px; margin: 0 2px; display: inline-block; min-width: 100px; text-align: center;">[ _____ ]</span>'

            token_map[token] = html_replacement

            # Replace in text with token
            text_with_tokens = text_with_tokens[:match.start()] + token + text_with_tokens[match.end():]

        # Render the text with tokens (this will escape HTML but preserve our tokens)
        html_out = self.render_to_html(text_with_tokens, apply_syntax_highlighting)

        # Replace tokens with their HTML (post-escape)
        for token in sorted(token_map.keys(), key=len, reverse=True):
            html_out = html_out.replace(token, token_map[token])

        return html_out

    def get_default_code_css(self) -> str:
        """Get default CSS for code blocks."""
        return """
        .code-block {
            font-family: 'Courier New', 'Consolas', monospace;
            font-size: 12px;
            background-color: #f5f5f5;
            border: 2px inset #c0c0c0;
            padding: 8px;
            margin: 8px 0;
            overflow-x: auto;
            white-space: pre;
            line-height: 1.4;
            border-radius: 0; /* Win95 style - no rounded corners */
            box-shadow: inset 1px 1px 0 #ffffff, inset -1px -1px 0 #808080;
        }
        
        .code-block code {
            background: none;
            padding: 0;
            border: none;
            font-family: inherit;
        }
        
        .cloze-blank {
            background-color: #ffeb3b;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
        }

        .cloze-revealed {
            background-color: #4caf50;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
        }

        .cloze-input-blank {
            background-color: #e3f2fd;
            border: 2px dashed #2196f3;
            padding: 2px 8px;
            border-radius: 3px;
            font-weight: bold;
            color: #1976d2;
        }

        .cloze-input-revealed {
            background-color: #2196f3;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
            border: 2px solid #1976d2;
        }

        .cloze-input-field {
            background-color: white;
            border: 2px inset #c0c0c0;
            padding: 4px 8px;
            font-family: inherit;
            font-size: inherit;
            min-width: 100px;
            margin: 0 2px;
        }

        .cloze-input-field:focus {
            border: 2px inset #0000ff;
            outline: none;
        }

        .cloze-input-field.correct {
            background-color: #d4edda;
            border-color: #28a745;
        }

        .cloze-input-field.incorrect {
            background-color: #f8d7da;
            border-color: #dc3545;
        }

        .style-code {
            font-family: 'Courier New', 'Consolas', monospace;
        }

        /* Syntax highlighting classes */
        .keyword { color: #0000ff; font-weight: bold; }
        .string { color: #008000; }
        .number { color: #800080; }
        .comment { color: #808080; font-style: italic; }

        /* Mathematical expression styling */
        .math-container {
            background-color: #f5f5f5;
            border: 2px inset #c0c0c0;
            margin: 8px 0;
            padding: 12px;
            border-radius: 0; /* Win95 style - no rounded corners */
            box-shadow: inset 1px 1px 0 #ffffff, inset -1px -1px 0 #808080;
        }

        .math-content {
            font-family: 'Times New Roman', serif;
            font-size: 16px;
            text-align: center;
            line-height: 1.6;
            color: #000000;
        }

        .math-content .fraction {
            display: inline-block;
            vertical-align: middle;
            text-align: center;
        }

        .math-content .numerator {
            display: block;
            border-bottom: 1px solid #000;
            padding-bottom: 2px;
        }

        .math-content .denominator {
            display: block;
            padding-top: 2px;
        }

        .math-content sup {
            font-size: 0.8em;
            vertical-align: super;
        }

        .math-content sub {
            font-size: 0.8em;
            vertical-align: sub;
        }

        /* Inline code styling */
        .inline-code {
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            padding: 1px 4px;
            border-radius: 2px;
            font-family: 'Courier New', 'Consolas', monospace;
            font-size: 0.9em;
        }

        /* Link styling */
        a {
            color: #0000EE;
            text-decoration: underline;
        }

        a:visited {
            color: #551A8B;
        }

        /* Ensure white background for all content */
        body, div, p, h1, h2, h3, h4, h5, h6, ul, ol, li {
            background-color: #ffffff !important;
        }
        """
