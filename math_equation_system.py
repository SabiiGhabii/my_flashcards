#!/usr/bin/env python3
"""
Mathematical Equations Support System

This module provides comprehensive support for:
- LaTeX/MathJax equation parsing and rendering
- Mathematical content detection and extraction
- Formula-based flashcard generation
- Mathematical concept identification
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

try:
    from sympy import sympify, latex, parse_expr, symbols
    from sympy.parsing.latex import parse_latex
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False

try:
    from gemini_integration import GeminiAgent
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class EquationType(Enum):
    """Types of mathematical equations"""
    ALGEBRAIC = "algebraic"
    CALCULUS = "calculus"
    STATISTICS = "statistics"
    GEOMETRY = "geometry"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    GENERAL = "general"


@dataclass
class MathEquation:
    """Represents a mathematical equation"""
    raw_text: str
    latex_form: str
    equation_type: EquationType
    variables: List[str]
    constants: List[str]
    description: str
    context: str = ""
    difficulty: str = "intermediate"


class MathPatternDetector:
    """Detects mathematical patterns in text"""
    
    def __init__(self):
        # Mathematical patterns for detection
        self.equation_patterns = [
            # LaTeX equations
            r'\$\$.*?\$\$',
            r'\$.*?\$',
            r'\\begin\{equation\}.*?\\end\{equation\}',
            r'\\begin\{align\}.*?\\end\{align\}',
            r'\\begin\{eqnarray\}.*?\\end\{eqnarray\}',
            
            # Common mathematical expressions
            r'[a-zA-Z]\s*=\s*[^=\n]+',  # Variable assignments
            r'[a-zA-Z]+\([^)]+\)\s*=\s*[^=\n]+',  # Function definitions
            r'\b\d+\s*[+\-*/]\s*\d+\s*=\s*\d+',  # Simple arithmetic
            r'[a-zA-Z]²|[a-zA-Z]³|[a-zA-Z]⁴',  # Superscripts
            r'√\([^)]+\)|√[a-zA-Z0-9]+',  # Square roots
            r'∫.*?dx|∫.*?dy|∫.*?dt',  # Integrals
            r'∑.*?=.*?|∏.*?=.*?',  # Summations and products
            r'lim.*?→.*?',  # Limits
            r'[a-zA-Z]+\'\s*=\s*[^=\n]+',  # Derivatives
        ]
        
        # Mathematical keywords for context
        self.math_keywords = {
            'algebra': ['equation', 'variable', 'coefficient', 'polynomial', 'quadratic'],
            'calculus': ['derivative', 'integral', 'limit', 'differential', 'gradient'],
            'statistics': ['mean', 'variance', 'probability', 'distribution', 'correlation'],
            'geometry': ['angle', 'triangle', 'circle', 'area', 'volume', 'perimeter'],
            'physics': ['force', 'energy', 'momentum', 'velocity', 'acceleration'],
            'chemistry': ['concentration', 'molarity', 'reaction', 'equilibrium']
        }
    
    def detect_equations(self, text: str) -> List[Dict[str, Any]]:
        """Detect mathematical equations in text"""
        equations = []
        
        for pattern in self.equation_patterns:
            matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                equation_text = match.group().strip()
                if len(equation_text) > 3:  # Filter out very short matches
                    equations.append({
                        'text': equation_text,
                        'start': match.start(),
                        'end': match.end(),
                        'type': self._classify_equation_type(equation_text, text),
                        'context': self._extract_context(text, match.start(), match.end())
                    })
        
        return equations
    
    def _classify_equation_type(self, equation: str, full_text: str) -> EquationType:
        """Classify the type of mathematical equation"""
        equation_lower = equation.lower()
        context_lower = full_text.lower()
        
        # Check for specific mathematical domains
        for domain, keywords in self.math_keywords.items():
            if any(keyword in equation_lower or keyword in context_lower for keyword in keywords):
                # Map domain names to valid EquationType values
                domain_mapping = {
                    'algebra': EquationType.ALGEBRAIC,
                    'calculus': EquationType.CALCULUS,
                    'statistics': EquationType.STATISTICS,
                    'geometry': EquationType.GEOMETRY,
                    'physics': EquationType.PHYSICS,
                    'chemistry': EquationType.CHEMISTRY
                }
                return domain_mapping.get(domain, EquationType.GENERAL)
        
        # Default classification based on content
        if any(symbol in equation for symbol in ['∫', 'dx', 'dy', 'dt', "'"]):
            return EquationType.CALCULUS
        elif any(symbol in equation for symbol in ['√', '^', '²', '³']):
            return EquationType.ALGEBRAIC
        elif any(symbol in equation for symbol in ['P(', 'E[', 'Var(', 'σ', 'μ']):
            return EquationType.STATISTICS
        else:
            return EquationType.GENERAL
    
    def _extract_context(self, text: str, start: int, end: int, window: int = 100) -> str:
        """Extract context around an equation"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()


class LaTeXProcessor:
    """Processes LaTeX equations"""
    
    def __init__(self):
        self.latex_commands = {
            'frac': r'\\frac\{([^}]+)\}\{([^}]+)\}',
            'sqrt': r'\\sqrt\{([^}]+)\}',
            'sum': r'\\sum_\{([^}]+)\}\^\{([^}]+)\}',
            'int': r'\\int_\{([^}]+)\}\^\{([^}]+)\}',
            'lim': r'\\lim_\{([^}]+)\}',
            'partial': r'\\frac\{\\partial ([^}]+)\}\{\\partial ([^}]+)\}'
        }
    
    def parse_latex(self, latex_str: str) -> Dict[str, Any]:
        """Parse LaTeX equation and extract components"""
        if not HAS_SYMPY:
            return self._basic_latex_parse(latex_str)
        
        try:
            # Clean LaTeX string
            cleaned = self._clean_latex(latex_str)
            
            # Try to parse with SymPy
            expr = parse_latex(cleaned)
            
            return {
                'expression': str(expr),
                'latex': latex(expr),
                'variables': [str(var) for var in expr.free_symbols],
                'is_equation': '=' in cleaned,
                'complexity': self._calculate_complexity(str(expr))
            }
        
        except Exception as e:
            logger.warning(f"Failed to parse LaTeX with SymPy: {e}")
            return self._basic_latex_parse(latex_str)
    
    def _clean_latex(self, latex_str: str) -> str:
        """Clean LaTeX string for parsing"""
        # Remove LaTeX delimiters
        cleaned = re.sub(r'\$+', '', latex_str)
        cleaned = re.sub(r'\\begin\{.*?\}|\\end\{.*?\}', '', cleaned)
        
        # Handle common LaTeX commands
        for cmd, pattern in self.latex_commands.items():
            if cmd == 'frac':
                cleaned = re.sub(pattern, r'(\1)/(\2)', cleaned)
            elif cmd == 'sqrt':
                cleaned = re.sub(pattern, r'sqrt(\1)', cleaned)
        
        return cleaned.strip()
    
    def _basic_latex_parse(self, latex_str: str) -> Dict[str, Any]:
        """Basic LaTeX parsing without SymPy"""
        variables = re.findall(r'[a-zA-Z](?![a-zA-Z])', latex_str)
        
        return {
            'expression': latex_str,
            'latex': latex_str,
            'variables': list(set(variables)),
            'is_equation': '=' in latex_str,
            'complexity': len(variables) + latex_str.count('\\')
        }
    
    def _calculate_complexity(self, expression: str) -> int:
        """Calculate mathematical complexity score"""
        complexity = 0
        
        # Count operations
        complexity += expression.count('+') + expression.count('-')
        complexity += expression.count('*') * 2 + expression.count('/') * 2
        complexity += expression.count('**') * 3
        complexity += expression.count('sqrt') * 2
        complexity += expression.count('log') * 3
        complexity += expression.count('sin') + expression.count('cos') + expression.count('tan')
        
        return complexity


class MathCardGenerator:
    """Generates mathematical flashcards"""
    
    def __init__(self, gemini_agent: Optional[GeminiAgent] = None):
        self.gemini_agent = gemini_agent
        self.pattern_detector = MathPatternDetector()
        self.latex_processor = LaTeXProcessor()
    
    def generate_math_cards(self, text: str, max_cards: int = 20) -> List[Dict[str, Any]]:
        """Generate mathematical flashcards from text"""
        equations = self.pattern_detector.detect_equations(text)
        cards = []
        
        for equation_data in equations[:max_cards]:
            equation = MathEquation(
                raw_text=equation_data['text'],
                latex_form=self._convert_to_latex(equation_data['text']),
                equation_type=equation_data['type'],
                variables=self._extract_variables(equation_data['text']),
                constants=self._extract_constants(equation_data['text']),
                description=self._generate_description(equation_data),
                context=equation_data['context']
            )
            
            # Generate different types of cards for each equation
            cards.extend(self._generate_equation_cards(equation))
        
        return cards
    
    def _convert_to_latex(self, equation_text: str) -> str:
        """Convert equation text to LaTeX format"""
        if equation_text.startswith('$') or equation_text.startswith('\\'):
            return equation_text
        
        # Basic conversion for simple equations
        latex_eq = equation_text
        
        # Convert superscripts
        latex_eq = re.sub(r'([a-zA-Z0-9])²', r'\1^2', latex_eq)
        latex_eq = re.sub(r'([a-zA-Z0-9])³', r'\1^3', latex_eq)
        
        # Convert square roots
        latex_eq = re.sub(r'√\(([^)]+)\)', r'\\sqrt{\1}', latex_eq)
        latex_eq = re.sub(r'√([a-zA-Z0-9]+)', r'\\sqrt{\1}', latex_eq)
        
        return f"${latex_eq}$"
    
    def _extract_variables(self, equation: str) -> List[str]:
        """Extract variables from equation"""
        # Find single letters that are likely variables
        variables = re.findall(r'\b[a-zA-Z]\b', equation)
        return list(set(variables))
    
    def _extract_constants(self, equation: str) -> List[str]:
        """Extract constants from equation"""
        # Find numbers and common mathematical constants
        constants = re.findall(r'\b\d+\.?\d*\b', equation)
        math_constants = ['π', 'e', 'φ', '∞']
        for const in math_constants:
            if const in equation:
                constants.append(const)
        return list(set(constants))
    
    def _generate_description(self, equation_data: Dict[str, Any]) -> str:
        """Generate description for equation"""
        if self.gemini_agent:
            try:
                prompt = f"Provide a brief educational description for this mathematical equation: {equation_data['text']}"
                description = self.gemini_agent._make_request(prompt)
                if description:
                    return description
            except Exception as e:
                logger.warning(f"Failed to generate description with Gemini: {e}")
        
        # Fallback description
        eq_type = equation_data['type'].value
        return f"A {eq_type} equation involving mathematical relationships."
    
    def _generate_equation_cards(self, equation: MathEquation) -> List[Dict[str, Any]]:
        """Generate multiple card types for an equation"""
        cards = []
        
        # 1. Definition card
        cards.append({
            "type": "fb",
            "front": f"What does this equation represent?\n\n{equation.latex_form}",
            "back": equation.description,
            "content": "",
            "hint": f"Consider the {equation.equation_type.value} context and variables involved.",
            "tags": f"math,equation,{equation.equation_type.value},definition",
            "template_id": "fb_equation_definition",
            "difficulty": equation.difficulty,
            "concept": f"{equation.equation_type.value}_equation"
        })
        
        # 2. Variable identification card
        if equation.variables:
            variables_str = ", ".join(equation.variables)
            cards.append({
                "type": "cloze",
                "front": "",
                "back": "",
                "content": f"In the equation {equation.latex_form}, the variables are {{{{c1::{variables_str}}}}}.",
                "hint": "Identify the unknown quantities that can vary.",
                "tags": f"math,variables,{equation.equation_type.value}",
                "template_id": "cloze_equation_variables",
                "difficulty": "basic",
                "concept": "variable_identification"
            })
        
        # 3. Equation completion card
        if '=' in equation.raw_text:
            # Create cloze input for part of the equation
            parts = equation.raw_text.split('=')
            if len(parts) == 2:
                left_part, right_part = parts[0].strip(), parts[1].strip()
                cards.append({
                    "type": "cloze_input",
                    "front": "",
                    "back": "",
                    "content": f"Complete the equation: {left_part} = {{{{cin1::{right_part}}}}}",
                    "hint": "Solve for the right side of the equation.",
                    "tags": f"math,equation_completion,{equation.equation_type.value}",
                    "template_id": "cin_equation_completion",
                    "difficulty": "intermediate",
                    "concept": "equation_solving"
                })
        
        # 4. Application card
        if equation.context:
            cards.append({
                "type": "fb",
                "front": f"How is this equation used?\n\n{equation.latex_form}",
                "back": f"Context: {equation.context}",
                "content": "",
                "hint": "Think about practical applications and real-world usage.",
                "tags": f"math,application,{equation.equation_type.value}",
                "template_id": "fb_equation_application",
                "difficulty": "advanced",
                "concept": "mathematical_application"
            })
        
        return cards


class MathematicalContentProcessor:
    """Main processor for mathematical content"""
    
    def __init__(self, gemini_agent: Optional[GeminiAgent] = None):
        self.gemini_agent = gemini_agent
        self.card_generator = MathCardGenerator(gemini_agent)
        self.pattern_detector = MathPatternDetector()
    
    def process_mathematical_content(self, content: str, max_cards: int = 50) -> Dict[str, Any]:
        """Process mathematical content and generate comprehensive cards"""
        # Detect equations
        equations = self.pattern_detector.detect_equations(content)
        
        # Generate cards
        cards = self.card_generator.generate_math_cards(content, max_cards)
        
        # Extract mathematical concepts using Gemini if available
        concepts = []
        if self.gemini_agent:
            concepts = self.gemini_agent.extract_mathematical_concepts(content)
        
        return {
            "equations_found": len(equations),
            "cards_generated": len(cards),
            "cards": cards,
            "mathematical_concepts": concepts,
            "equation_types": list(set(eq['type'].value for eq in equations))
        }


# Factory function
def create_math_processor(gemini_agent: Optional[GeminiAgent] = None) -> MathematicalContentProcessor:
    """Create a mathematical content processor"""
    return MathematicalContentProcessor(gemini_agent)
