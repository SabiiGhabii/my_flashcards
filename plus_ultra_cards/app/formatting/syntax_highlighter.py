"""
Syntax Highlighter Module for Plus Ultra Cards
Provides syntax highlighting for multiple programming languages using Pygments.
"""

import re
import html
from typing import Dict, Optional, Set


class SyntaxHighlighter:
    """
    Lightweight syntax highlighter with fallback support.
    Uses Pygments if available, otherwise provides basic keyword highlighting.
    """
    
    def __init__(self):
        self.pygments_available = self._check_pygments()
        self.language_aliases = self._get_language_aliases()
    
    def _check_pygments(self) -> bool:
        """Check if Pygments is available for advanced syntax highlighting."""
        try:
            import pygments
            return True
        except ImportError:
            return False
    
    def _get_language_aliases(self) -> Dict[str, str]:
        """Get language aliases for normalization."""
        return {
            'c++': 'cpp',
            'c#': 'csharp',
            'js': 'javascript',
            'ts': 'typescript',
            'shell': 'bash',
            'py': 'python',
        }
    
    def normalize_language(self, language: str) -> str:
        """Normalize language name."""
        lang = language.lower().strip()
        return self.language_aliases.get(lang, lang)
    
    def highlight(self, code: str, language: str) -> str:
        """
        Highlight code with syntax highlighting.
        
        Args:
            code: Source code to highlight
            language: Programming language
            
        Returns:
            HTML string with syntax highlighting
        """
        normalized_lang = self.normalize_language(language)
        
        if self.pygments_available:
            return self._highlight_with_pygments(code, normalized_lang)
        else:
            return self._highlight_basic(code, normalized_lang)
    
    def _highlight_with_pygments(self, code: str, language: str) -> str:
        """Highlight using Pygments library."""
        try:
            from pygments import highlight
            from pygments.lexers import get_lexer_by_name
            from pygments.formatters import HtmlFormatter
            from pygments.util import ClassNotFound
            
            try:
                lexer = get_lexer_by_name(language, stripall=True)
            except ClassNotFound:
                # Fallback to text lexer
                lexer = get_lexer_by_name('text', stripall=True)
            
            formatter = HtmlFormatter(
                style='default',
                noclasses=True,  # Use inline styles
                nowrap=True,     # Don't wrap in <div class="highlight">
                linenos=False    # No line numbers
            )
            
            highlighted = highlight(code, lexer, formatter)
            return highlighted
            
        except Exception:
            # Fallback to basic highlighting
            return self._highlight_basic(code, language)
    
    def _highlight_basic(self, code: str, language: str) -> str:
        """Basic syntax highlighting using regex patterns."""
        # Escape HTML first
        escaped = html.escape(code)
        
        # Apply language-specific highlighting
        if language == 'python':
            highlighted = self._highlight_python(escaped)
        elif language in ['cpp', 'c']:
            highlighted = self._highlight_cpp(escaped)
        elif language == 'javascript':
            highlighted = self._highlight_javascript(escaped)
        elif language == 'java':
            highlighted = self._highlight_java(escaped)
        elif language == 'rust':
            highlighted = self._highlight_rust(escaped)
        elif language == 'r':
            highlighted = self._highlight_r(escaped)
        elif language in ['bash', 'shell']:
            highlighted = self._highlight_bash(escaped)
        elif language == 'sql':
            highlighted = self._highlight_sql(escaped)
        else:
            highlighted = escaped
        
        # Preserve whitespace
        highlighted = highlighted.replace('\n', '<br>')
        highlighted = re.sub(r'  +', lambda m: '&nbsp;' * len(m.group(0)), highlighted)
        highlighted = highlighted.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        
        return highlighted
    
    def _highlight_python(self, code: str) -> str:
        """Enhanced Python syntax highlighting - Notepad++ style."""
        # Comments first (green)
        code = re.sub(r'(#.*?)(?=\n|$)', r'<span style="color: #008000; font-style: italic;">\1</span>', code)

        # Strings (orange/brown like Notepad++)
        code = re.sub(r'(["\'])([^"\']*?)\1', r'<span style="color: #FF8000;">\1\2\1</span>', code)

        # Numbers (red/magenta like Notepad++)
        code = re.sub(r'\b(\d+\.?\d*)\b', r'<span style="color: #FF0080;">\1</span>', code)

        # Keywords (blue and bold like Notepad++)
        keywords = r'\b(def|class|if|elif|else|for|while|try|except|finally|with|as|import|from|return|yield|break|continue|pass|lambda|and|or|not|in|is|None|True|False|self)\b'
        code = re.sub(keywords, r'<span style="color: #0000FF; font-weight: bold;">\1</span>', code)

        # Built-in functions (purple like Notepad++)
        builtins = r'\b(print|len|range|str|int|float|list|dict|set|tuple|open|input|type|isinstance|hasattr|getattr|setattr)\b'
        code = re.sub(builtins, r'<span style="color: #8000FF; font-weight: bold;">\1</span>', code)

        return code
    
    def _highlight_cpp(self, code: str) -> str:
        """Enhanced C++ syntax highlighting - Notepad++ style."""
        # Comments first
        code = re.sub(r'(//.*?)(?=\n|$)', r'<span style="color: #008000; font-style: italic;">\1</span>', code)
        code = re.sub(r'(/\*.*?\*/)', r'<span style="color: #008000; font-style: italic;">\1</span>', code, flags=re.DOTALL)

        # Preprocessor directives (purple)
        code = re.sub(r'(#\w+)', r'<span style="color: #8000FF; font-weight: bold;">\1</span>', code)

        # Strings (orange)
        code = re.sub(r'(["\'])([^"\']*?)\1', r'<span style="color: #FF8000;">\1\2\1</span>', code)

        # Numbers (magenta)
        code = re.sub(r'\b(\d+\.?\d*)\b', r'<span style="color: #FF0080;">\1</span>', code)

        # Keywords (blue)
        keywords = r'\b(int|float|double|char|bool|void|if|else|for|while|do|switch|case|default|break|continue|return|class|struct|public|private|protected|virtual|static|const|namespace|using|include|define|ifdef|ifndef|endif)\b'
        code = re.sub(keywords, r'<span style="color: #0000FF; font-weight: bold;">\1</span>', code)

        return code
    
    def _highlight_javascript(self, code: str) -> str:
        """Enhanced JavaScript syntax highlighting - Notepad++ style."""
        # Comments first
        code = re.sub(r'(//.*?)(?=\n|$)', r'<span style="color: #008000; font-style: italic;">\1</span>', code)

        # Strings (orange)
        code = re.sub(r'(["\'])([^"\']*?)\1', r'<span style="color: #FF8000;">\1\2\1</span>', code)

        # Numbers (magenta)
        code = re.sub(r'\b(\d+\.?\d*)\b', r'<span style="color: #FF0080;">\1</span>', code)

        # Keywords (blue)
        keywords = r'\b(var|let|const|function|if|else|for|while|do|switch|case|default|break|continue|return|class|extends|import|export|from|async|await|try|catch|finally|throw|new|this|typeof|instanceof)\b'
        code = re.sub(keywords, r'<span style="color: #0000FF; font-weight: bold;">\1</span>', code)

        return code
    
    def _highlight_java(self, code: str) -> str:
        """Enhanced Java syntax highlighting - Notepad++ style."""
        # Comments first
        code = re.sub(r'(//.*?)(?=\n|$)', r'<span style="color: #008000; font-style: italic;">\1</span>', code)

        # Strings (orange)
        code = re.sub(r'(["\'])([^"\']*?)\1', r'<span style="color: #FF8000;">\1\2\1</span>', code)

        # Numbers (magenta)
        code = re.sub(r'\b(\d+\.?\d*)\b', r'<span style="color: #FF0080;">\1</span>', code)

        # Keywords (blue)
        keywords = r'\b(public|private|protected|static|final|abstract|class|interface|extends|implements|if|else|for|while|do|switch|case|default|break|continue|return|try|catch|finally|throw|throws|new|this|super|package|import|void|int|float|double|boolean|char|String)\b'
        code = re.sub(keywords, r'<span style="color: #0000FF; font-weight: bold;">\1</span>', code)

        return code

    def _highlight_rust(self, code: str) -> str:
        """Enhanced Rust syntax highlighting - Notepad++ style."""
        # Comments first
        code = re.sub(r'(//.*?)(?=\n|$)', r'<span style="color: #008000; font-style: italic;">\1</span>', code)

        # Strings (orange)
        code = re.sub(r'(["\'])([^"\']*?)\1', r'<span style="color: #FF8000;">\1\2\1</span>', code)

        # Numbers (magenta)
        code = re.sub(r'\b(\d+\.?\d*)\b', r'<span style="color: #FF0080;">\1</span>', code)

        # Keywords (blue)
        keywords = r'\b(fn|let|mut|if|else|match|for|while|loop|break|continue|return|struct|enum|impl|trait|pub|mod|use|crate|self|Self|super|const|static|unsafe|async|await|move)\b'
        code = re.sub(keywords, r'<span style="color: #0000FF; font-weight: bold;">\1</span>', code)

        return code

    def _highlight_r(self, code: str) -> str:
        """Enhanced R syntax highlighting - Notepad++ style."""
        # Comments first
        code = re.sub(r'(#.*?)(?=\n|$)', r'<span style="color: #008000; font-style: italic;">\1</span>', code)

        # Strings (orange)
        code = re.sub(r'(["\'])([^"\']*?)\1', r'<span style="color: #FF8000;">\1\2\1</span>', code)

        # Numbers (magenta)
        code = re.sub(r'\b(\d+\.?\d*)\b', r'<span style="color: #FF0080;">\1</span>', code)

        # Keywords (blue)
        keywords = r'\b(function|if|else|for|while|repeat|next|break|return|TRUE|FALSE|NULL|NA|Inf|NaN|library|require|source)\b'
        code = re.sub(keywords, r'<span style="color: #0000FF; font-weight: bold;">\1</span>', code)
        
        return code
    
    def _highlight_bash(self, code: str) -> str:
        """Enhanced Bash syntax highlighting - Notepad++ style."""
        # Comments first
        code = re.sub(r'(#.*?)(?=\n|$)', r'<span style="color: #008000; font-style: italic;">\1</span>', code)

        # Strings (orange)
        code = re.sub(r'(["\'])([^"\']*?)\1', r'<span style="color: #FF8000;">\1\2\1</span>', code)

        # Variables (purple)
        code = re.sub(r'(\$\w+|\$\{\w+\})', r'<span style="color: #8000FF;">\1</span>', code)

        # Keywords (blue)
        keywords = r'\b(if|then|else|elif|fi|for|while|do|done|case|esac|function|return|exit|break|continue|echo|printf|read|export|source|alias)\b'
        code = re.sub(keywords, r'<span style="color: #0000FF; font-weight: bold;">\1</span>', code)

        return code

    def _highlight_sql(self, code: str) -> str:
        """Enhanced SQL syntax highlighting - Notepad++ style."""
        # Comments first
        code = re.sub(r'(--.*?)(?=\n|$)', r'<span style="color: #008000; font-style: italic;">\1</span>', code)

        # Strings (orange)
        code = re.sub(r'(["\'])([^"\']*?)\1', r'<span style="color: #FF8000;">\1\2\1</span>', code)

        # Numbers (magenta)
        code = re.sub(r'\b(\d+\.?\d*)\b', r'<span style="color: #FF0080;">\1</span>', code)

        # Keywords (blue, case insensitive)
        keywords = r'\b(SELECT|FROM|WHERE|JOIN|INNER|LEFT|RIGHT|OUTER|ON|GROUP|BY|ORDER|HAVING|INSERT|INTO|VALUES|UPDATE|SET|DELETE|CREATE|TABLE|ALTER|DROP|INDEX|PRIMARY|KEY|FOREIGN|REFERENCES|NOT|NULL|UNIQUE|DEFAULT|AUTO_INCREMENT|VARCHAR|INT|INTEGER|FLOAT|DOUBLE|DECIMAL|DATE|DATETIME|TIMESTAMP|TEXT|BLOB)\b'
        code = re.sub(keywords, r'<span style="color: #0000FF; font-weight: bold;">\1</span>', code, flags=re.IGNORECASE)

        return code
