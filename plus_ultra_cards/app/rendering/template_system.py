"""
Modular Rendering Template System
Provides pluggable rendering components for different content types
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class RenderingPriority(Enum):
    """Priority levels for rendering processors"""
    HIGHEST = 100
    HIGH = 75
    MEDIUM = 50
    LOW = 25
    LOWEST = 10


@dataclass
class RenderingContext:
    """Context information for rendering"""
    content_type: str
    apply_syntax_highlighting: bool
    reveal_cloze: bool
    inline_css: str
    custom_options: Dict[str, Any]


class RenderingProcessor(ABC):
    """Abstract base class for rendering processors"""
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this processor"""
        pass
    
    @abstractmethod
    def get_priority(self) -> RenderingPriority:
        """Return the priority of this processor"""
        pass
    
    @abstractmethod
    def can_process(self, text: str, context: RenderingContext) -> bool:
        """Return True if this processor can handle the given text"""
        pass
    
    @abstractmethod
    def process(self, text: str, context: RenderingContext) -> str:
        """Process the text and return the rendered result"""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """Return list of processor names this depends on"""
        pass


class MathExpressionProcessor(RenderingProcessor):
    """Processor for mathematical expressions"""
    
    def get_name(self) -> str:
        return "math_expression"
    
    def get_priority(self) -> RenderingPriority:
        return RenderingPriority.HIGH
    
    def can_process(self, text: str, context: RenderingContext) -> bool:
        return "$$" in text
    
    def process(self, text: str, context: RenderingContext) -> str:
        """Process mathematical expressions"""
        import re
        
        # Pattern to match $$...$$
        math_pattern = r'\$\$(.*?)\$\$'
        
        def replace_math(match):
            math_content = match.group(1)
            return f'<span class="math-container" data-math="{math_content}">$${math_content}$$</span>'
        
        return re.sub(math_pattern, replace_math, text, flags=re.DOTALL)
    
    def get_dependencies(self) -> List[str]:
        return []


class CodeBlockProcessor(RenderingProcessor):
    """Processor for code blocks with syntax highlighting"""
    
    def get_name(self) -> str:
        return "code_block"
    
    def get_priority(self) -> RenderingPriority:
        return RenderingPriority.HIGH
    
    def can_process(self, text: str, context: RenderingContext) -> bool:
        return "```" in text
    
    def process(self, text: str, context: RenderingContext) -> str:
        """Process code blocks with syntax highlighting"""
        import re
        
        # Pattern to match ```language\ncode\n```
        code_pattern = r'```(\w+)?\n(.*?)\n```'
        
        def replace_code(match):
            language = match.group(1) or 'text'
            code_content = match.group(2)
            
            if context.apply_syntax_highlighting:
                # Apply syntax highlighting
                highlighted_code = self._apply_syntax_highlighting(code_content, language)
                return f'<div class="code-block" data-language="{language}">{highlighted_code}</div>'
            else:
                return f'<div class="code-block" data-language="{language}"><pre><code>{code_content}</code></pre></div>'
        
        return re.sub(code_pattern, replace_code, text, flags=re.DOTALL)
    
    def _apply_syntax_highlighting(self, code: str, language: str) -> str:
        """Apply syntax highlighting to code"""
        try:
            from pygments import highlight
            from pygments.lexers import get_lexer_by_name
            from pygments.formatters import HtmlFormatter
            
            lexer = get_lexer_by_name(language, stripall=True)
            formatter = HtmlFormatter(nowrap=True, classprefix='hl-')
            return highlight(code, lexer, formatter)
        except:
            # Fallback if pygments is not available
            return f'<pre><code>{code}</code></pre>'
    
    def get_dependencies(self) -> List[str]:
        return []


class MarkdownProcessor(RenderingProcessor):
    """Processor for markdown content"""
    
    def get_name(self) -> str:
        return "markdown"
    
    def get_priority(self) -> RenderingPriority:
        return RenderingPriority.MEDIUM
    
    def can_process(self, text: str, context: RenderingContext) -> bool:
        # Check for common markdown patterns
        markdown_patterns = ['#', '**', '*', '- ', '1. ', '[', '](']
        return any(pattern in text for pattern in markdown_patterns)
    
    def process(self, text: str, context: RenderingContext) -> str:
        """Process markdown content"""
        import re
        
        # Simple markdown processing (can be extended)
        # Headers
        text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        
        # Bold and italic
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        
        # Lists
        text = re.sub(r'^- (.*?)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        text = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', text, flags=re.DOTALL)
        
        return text
    
    def get_dependencies(self) -> List[str]:
        return ["code_block"]  # Process after code blocks to avoid conflicts


class ClozeProcessor(RenderingProcessor):
    """Processor for cloze deletions"""
    
    def get_name(self) -> str:
        return "cloze"
    
    def get_priority(self) -> RenderingPriority:
        return RenderingPriority.MEDIUM
    
    def can_process(self, text: str, context: RenderingContext) -> bool:
        return "{{c" in text
    
    def process(self, text: str, context: RenderingContext) -> str:
        """Process cloze deletions"""
        import re
        
        # Pattern to match {{c1::text}}
        cloze_pattern = r'\{\{c(\d+)::([^}]+)\}\}'
        
        def replace_cloze(match):
            cloze_num = match.group(1)
            cloze_text = match.group(2)
            
            if context.reveal_cloze:
                return f'<span class="cloze-revealed" data-cloze="{cloze_num}">{cloze_text}</span>'
            else:
                return f'<span class="cloze-blank" data-cloze="{cloze_num}">[...]</span>'
        
        return re.sub(cloze_pattern, replace_cloze, text)
    
    def get_dependencies(self) -> List[str]:
        return []  # Process cloze before code blocks to handle cloze in code


class ClozeInputProcessor(RenderingProcessor):
    """Processor for cloze input fields"""
    
    def get_name(self) -> str:
        return "cloze_input"
    
    def get_priority(self) -> RenderingPriority:
        return RenderingPriority.MEDIUM
    
    def can_process(self, text: str, context: RenderingContext) -> bool:
        return "{{cin" in text
    
    def process(self, text: str, context: RenderingContext) -> str:
        """Process cloze input fields"""
        import re
        
        # Pattern to match {{cin1::answer}}
        cloze_input_pattern = r'\{\{cin(\d+)::([^}]+)\}\}'
        
        def replace_cloze_input(match):
            cloze_num = match.group(1)
            answer = match.group(2)
            
            if context.custom_options.get('reveal_answers', False):
                return f'<span class="cloze-input-revealed" data-cloze="{cloze_num}">{answer}</span>'
            else:
                return f'<span class="cloze-input-placeholder" data-cloze="{cloze_num}">[ _____ ]</span>'
        
        return re.sub(cloze_input_pattern, replace_cloze_input, text)
    
    def get_dependencies(self) -> List[str]:
        return []  # Process cloze input before code blocks to handle cloze in code


class WhitespaceProcessor(RenderingProcessor):
    """Processor for preserving whitespace"""
    
    def get_name(self) -> str:
        return "whitespace"
    
    def get_priority(self) -> RenderingPriority:
        return RenderingPriority.LOWEST
    
    def can_process(self, text: str, context: RenderingContext) -> bool:
        return True  # Always applicable
    
    def process(self, text: str, context: RenderingContext) -> str:
        """Preserve whitespace and convert to HTML"""
        # Convert newlines to <br> tags
        text = text.replace('\n', '<br>')
        
        # Convert multiple spaces to &nbsp;
        import re
        text = re.sub(r'  +', lambda m: '&nbsp;' * len(m.group()), text)
        
        return text
    
    def get_dependencies(self) -> List[str]:
        return ["code_block", "math_expression", "markdown", "cloze", "cloze_input"]


class RenderingTemplateEngine:
    """Main rendering engine that coordinates all processors"""
    
    def __init__(self):
        self._processors: List[RenderingProcessor] = []
        self._register_default_processors()
    
    def _register_default_processors(self):
        """Register default rendering processors"""
        self.register_processor(MathExpressionProcessor())
        self.register_processor(CodeBlockProcessor())
        self.register_processor(MarkdownProcessor())
        self.register_processor(ClozeProcessor())
        self.register_processor(ClozeInputProcessor())
        self.register_processor(WhitespaceProcessor())
    
    def register_processor(self, processor: RenderingProcessor):
        """Register a new rendering processor"""
        self._processors.append(processor)
        self._sort_processors()
    
    def _sort_processors(self):
        """Sort processors by priority and dependencies"""
        # Simple topological sort based on dependencies
        sorted_processors = []
        remaining_processors = self._processors.copy()
        
        while remaining_processors:
            # Find processors with no unmet dependencies
            ready_processors = []
            for processor in remaining_processors:
                dependencies = processor.get_dependencies()
                if all(dep in [p.get_name() for p in sorted_processors] for dep in dependencies):
                    ready_processors.append(processor)
            
            if not ready_processors:
                # Circular dependency or missing dependency - add remaining by priority
                ready_processors = sorted(remaining_processors, key=lambda p: p.get_priority().value, reverse=True)[:1]
            
            # Sort ready processors by priority
            ready_processors.sort(key=lambda p: p.get_priority().value, reverse=True)
            
            # Add to sorted list and remove from remaining
            for processor in ready_processors:
                sorted_processors.append(processor)
                remaining_processors.remove(processor)
        
        self._processors = sorted_processors
    
    def render(self, text: str, context: RenderingContext) -> str:
        """Render text using all applicable processors"""
        result = text
        
        for processor in self._processors:
            if processor.can_process(result, context):
                try:
                    result = processor.process(result, context)
                except Exception as e:
                    # Log error but continue processing
                    print(f"Warning: Processor {processor.get_name()} failed: {e}")
        
        return result
    
    def get_processors(self) -> List[RenderingProcessor]:
        """Get all registered processors"""
        return self._processors.copy()


# Global rendering engine instance
rendering_engine = RenderingTemplateEngine()


# Create __init__.py file marker
__all__ = ['RenderingTemplateEngine', 'RenderingProcessor', 'RenderingContext', 'rendering_engine']
