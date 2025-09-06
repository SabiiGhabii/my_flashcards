"""
Mathematical Content Processing System

This module provides basic mathematical content processing for:
- LaTeX/MathJax equation parsing
- Mathematical content detection
- Formula-based flashcard generation
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


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
            
            # Common mathematical expressions
            r'[a-zA-Z]\s*=\s*[^=\n]+',  # Variable assignments
            r'[a-zA-Z]+\([^)]+\)\s*=\s*[^=\n]+',  # Function definitions
            r'\b\d+\s*[+\-*/]\s*\d+\s*=\s*\d+',  # Simple arithmetic
            r'[a-zA-Z]²|[a-zA-Z]³|[a-zA-Z]⁴',  # Superscripts
            r'√\([^)]+\)|√[a-zA-Z0-9]+',  # Square roots
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
        if any(symbol in equation for symbol in ['√', '^', '²', '³']):
            return EquationType.ALGEBRAIC
        else:
            return EquationType.GENERAL
    
    def _extract_context(self, text: str, start: int, end: int, window: int = 100) -> str:
        """Extract context around an equation"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()


class MathCardGenerator:
    """Generates mathematical flashcards"""
    
    def __init__(self, gemini_agent=None):
        self.gemini_agent = gemini_agent
        self.pattern_detector = MathPatternDetector()
    
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
        
        return cards


class MathematicalContentProcessor:
    """Main processor for mathematical content"""
    
    def __init__(self, gemini_agent=None):
        self.gemini_agent = gemini_agent
        self.card_generator = MathCardGenerator(gemini_agent)
        self.pattern_detector = MathPatternDetector()
    
    def process_mathematical_content(self, content: str, max_cards: int = 50) -> Dict[str, Any]:
        """Process mathematical content and generate comprehensive cards"""
        # Detect equations
        equations = self.pattern_detector.detect_equations(content)
        
        # Generate cards
        cards = self.card_generator.generate_math_cards(content, max_cards)
        
        return {
            "equations_found": len(equations),
            "cards_generated": len(cards),
            "cards": cards,
            "mathematical_concepts": [],
            "equation_types": list(set(eq['type'].value for eq in equations))
        }


# Factory function
def create_math_processor(gemini_agent=None) -> MathematicalContentProcessor:
    """Create a mathematical content processor"""
    return MathematicalContentProcessor(gemini_agent)
