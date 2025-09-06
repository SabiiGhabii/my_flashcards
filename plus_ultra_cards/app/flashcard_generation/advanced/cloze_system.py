"""
Advanced Cloze Input Card System

This module implements three distinct cloze input card subtypes:
1. Partial Deletion Cards - Delete significant code components
2. Total Sequential Deletion Cards - Complete step-by-step reconstruction
3. Deterministic Deletion Cards - Delete only deterministic elements
"""

import ast
import re
import random
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import keyword
import builtins
import logging

logger = logging.getLogger(__name__)


class DeletionType(Enum):
    """Types of code deletions for cloze cards"""
    PARTIAL = "partial"
    SEQUENTIAL = "sequential"
    DETERMINISTIC = "deterministic"


@dataclass
class CodeDeletion:
    """Represents a code deletion for cloze cards"""
    text: str
    start_pos: int
    end_pos: int
    deletion_type: str
    importance: int
    explanation: str
    context: str = ""


class ASTAnalyzer:
    """AST-based code analysis for intelligent deletions"""
    
    def __init__(self):
        self.python_keywords = set(keyword.kwlist)
        self.builtin_functions = set(dir(builtins))
        self.deterministic_elements = self.python_keywords | self.builtin_functions
    
    def analyze_code_structure(self, code: str) -> Dict[str, Any]:
        """Analyze code structure using AST"""
        try:
            tree = ast.parse(code)
            analysis = {
                "functions": [],
                "classes": [],
                "variables": [],
                "imports": [],
                "function_calls": [],
                "complexity_score": 0,
                "deterministic_elements": [],
                "user_defined_elements": []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis["functions"].append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "complexity": self._calculate_function_complexity(node)
                    })
                
                elif isinstance(node, ast.ClassDef):
                    analysis["classes"].append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    })
                
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            analysis["variables"].append({
                                "name": target.id,
                                "line": node.lineno,
                                "type": self._infer_variable_type(node.value)
                            })
                
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        analysis["function_calls"].append({
                            "name": node.func.id,
                            "line": node.lineno,
                            "args": len(node.args)
                        })
            
            # Calculate overall complexity
            analysis["complexity_score"] = (
                len(analysis["functions"]) * 3 +
                len(analysis["classes"]) * 5 +
                len(analysis["function_calls"]) * 1 +
                sum(func["complexity"] for func in analysis["functions"])
            )
            
            return analysis
            
        except SyntaxError as e:
            logger.warning(f"Failed to parse code with AST: {e}")
            return self._fallback_analysis(code)
    
    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _infer_variable_type(self, value_node: ast.AST) -> str:
        """Infer variable type from assignment"""
        if isinstance(value_node, ast.Constant):
            return type(value_node.value).__name__
        elif isinstance(value_node, ast.List):
            return "list"
        elif isinstance(value_node, ast.Dict):
            return "dict"
        elif isinstance(value_node, ast.Call):
            return "function_result"
        else:
            return "unknown"
    
    def _fallback_analysis(self, code: str) -> Dict[str, Any]:
        """Fallback analysis when AST parsing fails"""
        return {
            "functions": [],
            "classes": [],
            "variables": [],
            "imports": [],
            "function_calls": [],
            "complexity_score": 1,
            "deterministic_elements": [],
            "user_defined_elements": []
        }


class PartialDeletionGenerator:
    """Generates partial deletion cloze cards"""
    
    def __init__(self, gemini_agent=None):
        self.gemini_agent = gemini_agent
        self.ast_analyzer = ASTAnalyzer()
    
    def generate_partial_deletions(self, code: str, max_deletions: int = 3) -> List[Dict[str, Any]]:
        """Generate partial deletion cloze cards"""
        analysis = self.ast_analyzer.analyze_code_structure(code)
        deletions = []
        
        # Fallback to heuristic-based deletions
        deletions.extend(self._heuristic_deletions(code, analysis, max_deletions))
        
        return deletions
    
    def _create_partial_deletion_card(self, code: str, deletion_text: str, explanation: str) -> Dict[str, Any]:
        """Create a partial deletion card"""
        # Replace the deletion with cloze input
        cloze_code = code.replace(deletion_text, f"{{{{cin1::{deletion_text}}}}}", 1)
        
        return {
            "type": "cloze_input",
            "front": "",
            "back": "",
            "content": f"~CODE[python]\n{cloze_code}\n~",
            "hint": f"Complete the missing code component. {explanation}",
            "tags": "code,partial_deletion,programming",
            "template_id": "cin_partial_deletion",
            "difficulty": "intermediate",
            "concept": "code_completion"
        }
    
    def _heuristic_deletions(self, code: str, analysis: Dict[str, Any], max_deletions: int) -> List[Dict[str, Any]]:
        """Generate deletions using heuristic analysis"""
        deletions = []
        
        # Delete important function calls
        for func_call in analysis["function_calls"][:max_deletions]:
            if func_call["name"] not in self.ast_analyzer.builtin_functions:
                deletion_text = func_call["name"]
                explanation = f"This function call is important for the code's functionality."
                deletions.append(self._create_partial_deletion_card(code, deletion_text, explanation))
        
        return deletions


class SequentialDeletionGenerator:
    """Generates total sequential deletion cloze cards"""
    
    def __init__(self, gemini_agent=None):
        self.gemini_agent = gemini_agent
        self.ast_analyzer = ASTAnalyzer()
    
    def generate_sequential_deletion(self, code: str, task_description: str = "") -> Dict[str, Any]:
        """Generate a sequential deletion card"""
        return self._create_heuristic_sequential_card(code, task_description)
    
    def _create_heuristic_sequential_card(self, code: str, task_description: str) -> Dict[str, Any]:
        """Create sequential card using heuristic analysis"""
        lines = code.split('\n')
        sequential_content = []
        
        for i, line in enumerate(lines, 1):
            if line.strip():
                sequential_content.append(f"{{{{cin{i}::{line}}}}}")
            else:
                sequential_content.append("")
        
        task = task_description or "Complete the code implementation step by step"
        
        content = f"""Task: {task}

~CODE[python]
{chr(10).join(sequential_content)}
~"""
        
        return {
            "type": "cloze_input",
            "front": "",
            "back": "",
            "content": content,
            "hint": "Complete each line of code in sequence.",
            "tags": "code,sequential_deletion,programming",
            "template_id": "cin_sequential_deletion",
            "difficulty": "advanced",
            "concept": "code_reconstruction"
        }


class DeterministicDeletionGenerator:
    """Generates deterministic deletion cloze cards"""
    
    def __init__(self):
        self.ast_analyzer = ASTAnalyzer()
        
        # Define deterministic elements to delete
        self.deterministic_patterns = [
            r'\bdef\b', r'\bclass\b', r'\bif\b', r'\belse\b', r'\belif\b',
            r'\bfor\b', r'\bwhile\b', r'\btry\b', r'\bexcept\b', r'\bfinally\b',
            r'\bwith\b', r'\breturn\b', r'\byield\b', r'\bimport\b', r'\bfrom\b',
            r'\band\b', r'\bor\b', r'\bnot\b', r'\bin\b', r'\bis\b',
            r'==', r'!=', r'<=', r'>=', r'<', r'>', r'\+', r'-', r'\*', r'/',
            r'=', r'\(', r'\)', r'\[', r'\]', r'\{', r'\}', r':', r';', r','
        ]
    
    def generate_deterministic_deletions(self, code: str, max_deletions: int = 5) -> List[Dict[str, Any]]:
        """Generate deterministic deletion cloze cards"""
        deletions = []
        
        # Find deterministic elements to delete
        deterministic_elements = set()
        
        for pattern in self.deterministic_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                element = match.group()
                if element not in deterministic_elements:
                    deterministic_elements.add(element)
                    if len(deletions) < max_deletions:
                        deletions.append(self._create_deterministic_deletion_card(code, element))
        
        return deletions
    
    def _create_deterministic_deletion_card(self, code: str, deletion_element: str) -> Dict[str, Any]:
        """Create a deterministic deletion card"""
        # Replace the deterministic element with cloze input
        cloze_code = code.replace(deletion_element, f"{{{{cin1::{deletion_element}}}}}", 1)
        
        return {
            "type": "cloze_input",
            "front": "",
            "back": "",
            "content": f"~CODE[python]\n{cloze_code}\n~",
            "hint": f"Complete the missing syntax element. Focus on Python language syntax.",
            "tags": "code,deterministic_deletion,syntax,programming",
            "template_id": "cin_deterministic_deletion",
            "difficulty": "basic",
            "concept": "syntax_knowledge"
        }


class AdvancedClozeSystem:
    """Main system for generating advanced cloze input cards"""
    
    def __init__(self, gemini_agent=None):
        self.gemini_agent = gemini_agent
        self.partial_generator = PartialDeletionGenerator(gemini_agent)
        self.sequential_generator = SequentialDeletionGenerator(gemini_agent)
        self.deterministic_generator = DeterministicDeletionGenerator()
    
    def generate_all_cloze_types(self, code: str, task_description: str = "") -> Dict[str, List[Dict[str, Any]]]:
        """Generate all types of cloze input cards"""
        return {
            "partial": self.partial_generator.generate_partial_deletions(code),
            "sequential": [self.sequential_generator.generate_sequential_deletion(code, task_description)],
            "deterministic": self.deterministic_generator.generate_deterministic_deletions(code)
        }
    
    def generate_by_type(self, code: str, deletion_type: DeletionType, 
                        task_description: str = "") -> List[Dict[str, Any]]:
        """Generate cloze cards of a specific type"""
        if deletion_type == DeletionType.PARTIAL:
            return self.partial_generator.generate_partial_deletions(code)
        elif deletion_type == DeletionType.SEQUENTIAL:
            return [self.sequential_generator.generate_sequential_deletion(code, task_description)]
        elif deletion_type == DeletionType.DETERMINISTIC:
            return self.deterministic_generator.generate_deterministic_deletions(code)
        else:
            return []


# Factory function
def create_cloze_system(gemini_agent=None) -> AdvancedClozeSystem:
    """Create an advanced cloze system"""
    return AdvancedClozeSystem(gemini_agent)
