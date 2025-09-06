"""
Interactive Features Implementation

This module implements advanced features including:
- Progressive disclosure cards
- Interactive code execution cards
- Visual diagram completion cards
"""

import json
import re
import ast
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CardComplexity(Enum):
    """Card complexity levels"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class ProgressiveLevel:
    """Represents a level in progressive disclosure"""
    level: int
    content: str
    reveal_trigger: str
    complexity: CardComplexity


class ProgressiveDisclosureGenerator:
    """Generates progressive disclosure cards for complex concepts"""
    
    def __init__(self, gemini_agent=None):
        self.gemini_agent = gemini_agent
    
    def create_progressive_card(self, concept: str, levels: List[str], 
                              context: str = "") -> Dict[str, Any]:
        """Create a progressive disclosure card"""
        
        progressive_levels = []
        for i, level_content in enumerate(levels):
            progressive_levels.append(ProgressiveLevel(
                level=i + 1,
                content=level_content,
                reveal_trigger=f"click_level_{i + 1}",
                complexity=self._determine_complexity(level_content, i)
            ))
        
        return {
            "type": "progressive_disclosure",
            "concept": concept,
            "context": context,
            "levels": [
                {
                    "level": level.level,
                    "content": level.content,
                    "complexity": level.complexity.value,
                    "reveal_trigger": level.reveal_trigger
                }
                for level in progressive_levels
            ],
            "front": f"What is {concept}? (Click to reveal progressive details)",
            "back": "",  # Progressive content replaces traditional back
            "hint": "Click through each level for increasing detail",
            "tags": f"progressive,concept,{concept.lower().replace(' ', '_')}",
            "template_id": "progressive_disclosure",
            "difficulty": "intermediate",
            "interactive": True
        }
    
    def _determine_complexity(self, content: str, level: int) -> CardComplexity:
        """Determine complexity based on content and level"""
        if level == 0:
            return CardComplexity.BASIC
        elif level == 1:
            return CardComplexity.INTERMEDIATE
        elif level == 2:
            return CardComplexity.ADVANCED
        else:
            return CardComplexity.EXPERT


class InteractiveCodeGenerator:
    """Generates interactive code execution cards"""
    
    def __init__(self, gemini_agent=None):
        self.gemini_agent = gemini_agent
    
    def create_interactive_card(self, code: str, test_cases: List[Tuple], 
                              explanation: str = "", language: str = "python") -> Dict[str, Any]:
        """Create an interactive code execution card"""
        
        # Analyze code structure
        code_analysis = self._analyze_code_structure(code, language)
        
        # Create interactive elements
        interactive_elements = [
            {
                "type": "code_editor",
                "content": code,
                "language": language,
                "editable": True,
                "runnable": True
            },
            {
                "type": "test_runner",
                "test_cases": [{"input": tc[0], "expected": tc[1]} for tc in test_cases],
                "auto_run": False
            },
            {
                "type": "output_display",
                "content": "",
                "real_time": True
            }
        ]
        
        return {
            "type": "interactive_code",
            "language": language,
            "code": code,
            "explanation": explanation,
            "test_cases": test_cases,
            "interactive_elements": interactive_elements,
            "code_analysis": code_analysis,
            "front": f"Complete and test this {language} code:",
            "back": explanation,
            "hint": "Modify the code and run tests to verify correctness",
            "tags": f"interactive,code,{language},execution",
            "template_id": "interactive_code_execution",
            "difficulty": "advanced",
            "interactive": True
        }
    
    def _analyze_code_structure(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code structure for educational insights"""
        analysis = {
            "functions": [],
            "classes": [],
            "complexity": 1,
            "concepts": [],
            "language": language
        }
        
        if language == "python":
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        analysis["functions"].append(node.name)
                    elif isinstance(node, ast.ClassDef):
                        analysis["classes"].append(node.name)
                
                analysis["complexity"] = len(analysis["functions"]) + len(analysis["classes"])
                
            except SyntaxError:
                pass
        
        return analysis


class DiagramGenerator:
    """Generates visual diagram completion cards"""
    
    def __init__(self):
        self.diagram_types = {
            "neural_network": self._create_neural_network_diagram,
            "system_architecture": self._create_system_diagram,
            "algorithm_flow": self._create_algorithm_diagram,
            "data_structure": self._create_data_structure_diagram
        }
    
    def create_diagram_card(self, diagram_type: str, missing_components: List[str],
                          description: str = "", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a visual diagram completion card"""
        
        if diagram_type not in self.diagram_types:
            raise ValueError(f"Unsupported diagram type: {diagram_type}")
        
        # Generate diagram
        diagram_data = self.diagram_types[diagram_type](missing_components, metadata or {})
        
        return {
            "type": "diagram_completion",
            "diagram_type": diagram_type,
            "description": description,
            "missing_components": missing_components,
            "diagram_data": diagram_data,
            "interactive_elements": [
                {
                    "type": "svg_canvas",
                    "content": diagram_data.get("svg", ""),
                    "editable_areas": missing_components
                },
                {
                    "type": "component_palette",
                    "available_components": diagram_data.get("components", []),
                    "drag_drop": True
                }
            ],
            "front": f"Complete the {diagram_type.replace('_', ' ')} diagram",
            "back": description,
            "hint": "Drag components from the palette to complete the diagram",
            "tags": f"diagram,visual,{diagram_type},completion",
            "template_id": "diagram_completion",
            "difficulty": "intermediate",
            "interactive": True
        }
    
    def _create_neural_network_diagram(self, missing_components: List[str], 
                                     metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create neural network diagram"""
        return {
            "svg": "<svg>Neural Network Diagram</svg>",
            "components": ["activation_function", "weights", "bias", "neurons"],
            "metadata": metadata
        }
    
    def _create_system_diagram(self, missing_components: List[str], 
                             metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create system architecture diagram"""
        return {
            "svg": "<svg>System Architecture Diagram</svg>",
            "components": ["database", "api", "frontend", "backend"],
            "metadata": metadata
        }
    
    def _create_algorithm_diagram(self, missing_components: List[str], 
                                metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create algorithm flow diagram"""
        return {
            "svg": "<svg>Algorithm Flow Diagram</svg>",
            "components": ["decision", "process", "input", "output"],
            "metadata": metadata
        }
    
    def _create_data_structure_diagram(self, missing_components: List[str], 
                                     metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create data structure diagram"""
        return {
            "svg": "<svg>Data Structure Diagram</svg>",
            "components": ["nodes", "edges", "pointers", "values"],
            "metadata": metadata
        }


# Factory functions for easy integration
def create_progressive_card(concept: str, levels: List[str], **kwargs) -> Dict[str, Any]:
    """Factory function for progressive disclosure cards"""
    generator = ProgressiveDisclosureGenerator()
    return generator.create_progressive_card(concept, levels, **kwargs)


def create_interactive_code_card(code: str, test_cases: List[Tuple], 
                               explanation: str = "", **kwargs) -> Dict[str, Any]:
    """Factory function for interactive code cards"""
    generator = InteractiveCodeGenerator()
    return generator.create_interactive_card(code, test_cases, explanation, **kwargs)


def create_diagram_card(diagram_type: str, missing_components: List[str], **kwargs) -> Dict[str, Any]:
    """Factory function for diagram completion cards"""
    generator = DiagramGenerator()
    return generator.create_diagram_card(diagram_type, missing_components, **kwargs)
