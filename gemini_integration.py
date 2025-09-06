#!/usr/bin/env python3
"""
Advanced Gemini API Integration for Enhanced Flashcard Generation

This module provides comprehensive Gemini AI integration for:
- Enhanced card generation and explanation improvement
- Intelligent content analysis and concept extraction
- Code analysis and explanation generation
- Mathematical equation processing
- Multi-agent content processing
"""

import json
import time
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Content types for specialized processing"""
    CODE = "code"
    MATHEMATICAL = "mathematical"
    CONCEPTUAL = "conceptual"
    PROCEDURAL = "procedural"
    FACTUAL = "factual"


@dataclass
class GeminiConfig:
    """Configuration for Gemini API integration"""
    api_key: str
    model_name: str = "gemini-1.5-flash"
    temperature: float = 0.7
    max_tokens: int = 2048
    rate_limit_delay: float = 1.0
    max_retries: int = 3
    timeout: int = 30


class GeminiRateLimiter:
    """Rate limiter for Gemini API calls"""
    
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.last_call = 0.0
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_call
        
        if time_since_last < self.delay:
            sleep_time = self.delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_call = time.time()


class GeminiAgent:
    """Advanced Gemini AI agent for content processing"""
    
    def __init__(self, config: GeminiConfig):
        if not HAS_GEMINI:
            raise ImportError("google-generativeai package is required for Gemini integration")
        
        self.config = config
        self.rate_limiter = GeminiRateLimiter(config.rate_limit_delay)
        
        # Configure Gemini
        genai.configure(api_key=config.api_key)
        self.model = genai.GenerativeModel(config.model_name)
        
        # Generation config
        self.generation_config = genai.types.GenerationConfig(
            temperature=config.temperature,
            max_output_tokens=config.max_tokens,
        )
    
    def _make_request(self, prompt: str, system_instruction: str = None) -> Optional[str]:
        """Make a request to Gemini with error handling and retries"""
        self.rate_limiter.wait_if_needed()
        
        for attempt in range(self.config.max_retries):
            try:
                if system_instruction:
                    full_prompt = f"System: {system_instruction}\n\nUser: {prompt}"
                else:
                    full_prompt = prompt
                
                response = self.model.generate_content(
                    full_prompt,
                    generation_config=self.generation_config
                )
                
                if hasattr(response, 'text') and response.text:
                    return response.text.strip()
                else:
                    logger.warning(f"Empty response from Gemini on attempt {attempt + 1}")
                    
            except Exception as e:
                logger.warning(f"Gemini API error on attempt {attempt + 1}: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                
        logger.error("Failed to get response from Gemini after all retries")
        return None
    
    def enhance_card_explanation(self, concept: str, definition: str, context: str = "") -> str:
        """Enhance card explanations using Gemini"""
        system_instruction = """You are an expert educational content creator. Your task is to improve flashcard explanations to be more clear, comprehensive, and pedagogically effective. Focus on:
1. Clarity and precision
2. Educational value
3. Memorable explanations
4. Practical examples when appropriate
5. Proper difficulty level"""
        
        prompt = f"""
Improve this flashcard explanation:

Concept: {concept}
Current Definition: {definition}
Context: {context}

Provide an enhanced explanation that is:
- Clear and concise
- Educationally valuable
- Easy to understand and remember
- Includes a practical example if relevant

Enhanced explanation:"""
        
        response = self._make_request(prompt, system_instruction)
        return response if response else definition
    
    def analyze_code_complexity(self, code: str) -> Dict[str, Any]:
        """Analyze code complexity and generate educational insights"""
        system_instruction = """You are a programming education expert. Analyze code for educational flashcard generation. Focus on:
1. Key concepts demonstrated
2. Difficulty level
3. Important components to highlight
4. Common mistakes to avoid
5. Learning objectives"""
        
        prompt = f"""
Analyze this code for educational flashcard generation:

```
{code}
```

Provide analysis in JSON format with these fields:
- "key_concepts": List of main programming concepts
- "difficulty_level": "beginner", "intermediate", or "advanced"
- "important_components": List of code parts to highlight
- "learning_objectives": What students should learn
- "common_mistakes": Potential pitfalls
- "explanation": Brief explanation of what the code does

JSON response:"""
        
        response = self._make_request(prompt, system_instruction)
        if response:
            try:
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from Gemini code analysis")
        
        # Fallback response
        return {
            "key_concepts": ["programming"],
            "difficulty_level": "intermediate",
            "important_components": [],
            "learning_objectives": ["understand code functionality"],
            "common_mistakes": [],
            "explanation": "Code performs specific functionality"
        }
    
    def generate_code_explanation(self, code: str, context: str = "") -> str:
        """Generate clear explanations for code snippets"""
        system_instruction = """You are a programming instructor. Explain code clearly and concisely for educational flashcards. Focus on:
1. What the code does (main purpose)
2. How it works (key steps)
3. Why it's written this way
4. Educational insights"""
        
        prompt = f"""
Explain this code for a flashcard:

```
{code}
```

Context: {context}

Provide a clear, educational explanation in 2-3 sentences that covers:
- What the code does
- Key programming concepts involved
- Any important details for learning

Explanation:"""
        
        response = self._make_request(prompt, system_instruction)
        return response if response else "This code performs a specific programming task."
    
    def identify_key_deletions(self, code: str) -> List[Dict[str, Any]]:
        """Identify pedagogically important parts of code to delete for cloze cards"""
        system_instruction = """You are an expert in programming education. Identify the most pedagogically valuable parts of code to remove for cloze deletion flashcards. Focus on:
1. Key function calls
2. Important variable assignments
3. Critical logic components
4. Language-specific syntax
5. Algorithm-specific elements"""
        
        prompt = f"""
Analyze this code and identify the most important parts to remove for educational cloze deletion cards:

```
{code}
```

For each deletion, provide:
- "text": The exact text to remove
- "type": Type of deletion (function_call, variable, keyword, etc.)
- "importance": Educational importance (1-10)
- "explanation": Why this deletion is pedagogically valuable

Provide response in JSON format with "deletions" array:"""
        
        response = self._make_request(prompt, system_instruction)
        if response:
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    return data.get("deletions", [])
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from Gemini deletion analysis")
        
        return []
    
    def generate_sequential_explanation(self, code: str, task_description: str = "") -> Dict[str, Any]:
        """Generate detailed explanation for sequential code reconstruction"""
        system_instruction = """You are a programming instructor creating step-by-step code reconstruction exercises. Provide:
1. Clear task description
2. Detailed explanation of what the code accomplishes
3. Legend of non-deterministic elements
4. Step-by-step breakdown for sequential reconstruction"""
        
        prompt = f"""
Create a sequential code reconstruction exercise for this code:

```
{code}
```

Task Description: {task_description}

Provide response in JSON format with:
- "task": Clear description of what to accomplish
- "explanation": Detailed explanation of the code's purpose
- "legend": Object with non-deterministic elements (variable names, file paths, etc.)
- "steps": Array of steps with "description" and "code_pattern"
- "notes": Any important notes or constraints

JSON response:"""
        
        response = self._make_request(prompt, system_instruction)
        if response:
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from Gemini sequential analysis")
        
        # Fallback response
        return {
            "task": "Complete the code implementation",
            "explanation": "This code performs a specific task",
            "legend": {},
            "steps": [],
            "notes": []
        }
    
    def extract_mathematical_concepts(self, text: str) -> List[Dict[str, Any]]:
        """Extract and analyze mathematical concepts from text"""
        system_instruction = """You are a mathematics education expert. Extract mathematical concepts, equations, and formulas from text for flashcard generation. Focus on:
1. Mathematical definitions
2. Formulas and equations
3. Theorems and proofs
4. Mathematical relationships
5. Problem-solving techniques"""
        
        prompt = f"""
Extract mathematical concepts from this text for flashcard generation:

{text}

Identify:
- Mathematical definitions
- Equations and formulas
- Theorems or principles
- Key relationships
- Problem-solving techniques

Provide response in JSON format with "concepts" array containing:
- "type": "definition", "equation", "theorem", etc.
- "concept": The mathematical concept name
- "content": The mathematical content
- "explanation": Educational explanation
- "difficulty": "basic", "intermediate", "advanced"

JSON response:"""
        
        response = self._make_request(prompt, system_instruction)
        if response:
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    return data.get("concepts", [])
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from Gemini math analysis")
        
        return []
    
    def generate_comprehensive_cards(self, content: str, content_type: ContentType, max_cards: int = 50) -> List[Dict[str, Any]]:
        """Generate comprehensive flashcards from content"""
        system_instruction = f"""You are an expert educational content creator specializing in {content_type.value} content. Generate comprehensive flashcards that cover ALL important information. Focus on:
1. Complete coverage of key concepts
2. Progressive difficulty levels
3. Multiple card types (definition, application, analysis)
4. Pedagogically sound design
5. Spaced repetition optimization"""
        
        prompt = f"""
Generate comprehensive flashcards from this {content_type.value} content:

{content}

Create up to {max_cards} flashcards covering ALL important information. For each card, provide:
- "type": "front_back", "cloze", or "cloze_input"
- "front": Front of card (for front_back type)
- "back": Back of card (for front_back type)
- "content": Content with cloze deletions (for cloze types)
- "hint": Helpful hint
- "tags": Relevant tags
- "difficulty": "basic", "intermediate", "advanced"
- "concept": Main concept being tested

Provide response in JSON format with "cards" array:"""
        
        response = self._make_request(prompt, system_instruction)
        if response:
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    return data.get("cards", [])
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from Gemini card generation")
        
        return []


class MultiAgentGeminiSystem:
    """Multi-agent system using multiple Gemini agents for specialized processing"""
    
    def __init__(self, config: GeminiConfig):
        self.config = config
        self.agents = {
            ContentType.CODE: GeminiAgent(config),
            ContentType.MATHEMATICAL: GeminiAgent(config),
            ContentType.CONCEPTUAL: GeminiAgent(config),
            ContentType.PROCEDURAL: GeminiAgent(config),
            ContentType.FACTUAL: GeminiAgent(config)
        }
    
    def process_content(self, content: str, content_type: ContentType) -> Dict[str, Any]:
        """Process content using specialized agent"""
        agent = self.agents.get(content_type, self.agents[ContentType.CONCEPTUAL])
        
        if content_type == ContentType.CODE:
            return {
                "analysis": agent.analyze_code_complexity(content),
                "explanation": agent.generate_code_explanation(content),
                "deletions": agent.identify_key_deletions(content)
            }
        elif content_type == ContentType.MATHEMATICAL:
            return {
                "concepts": agent.extract_mathematical_concepts(content)
            }
        else:
            return {
                "cards": agent.generate_comprehensive_cards(content, content_type)
            }


# Factory function for easy integration
def create_gemini_agent(api_key: str, **kwargs) -> Optional[GeminiAgent]:
    """Create a Gemini agent with the given configuration"""
    if not HAS_GEMINI:
        logger.error("google-generativeai package is required for Gemini integration")
        return None
    
    if not api_key:
        logger.error("Gemini API key is required")
        return None
    
    config = GeminiConfig(api_key=api_key, **kwargs)
    try:
        return GeminiAgent(config)
    except Exception as e:
        logger.error(f"Failed to create Gemini agent: {e}")
        return None
