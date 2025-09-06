#!/usr/bin/env python3
"""
Advanced Features Implementation

This module implements advanced features from ideas.md including:
- Progressive disclosure cards
- Interactive code execution cards
- Visual diagram completion cards
- Multi-modal content processing
- Advanced template selection interface
"""

import json
import re
import ast
import base64
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.patches import FancyBboxPatch
    import io
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


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


@dataclass
class InteractiveElement:
    """Interactive element in a card"""
    element_type: str  # code, diagram, quiz, etc.
    content: str
    metadata: Dict[str, Any]


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
        
        # Generate enhanced explanations if Gemini is available
        if self.gemini_agent:
            enhanced_levels = self._enhance_with_ai(concept, progressive_levels, context)
        else:
            enhanced_levels = progressive_levels
        
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
                for level in enhanced_levels
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
    
    def _enhance_with_ai(self, concept: str, levels: List[ProgressiveLevel], 
                        context: str) -> List[ProgressiveLevel]:
        """Enhance progressive levels with AI"""
        if not self.gemini_agent:
            return levels
        
        try:
            prompt = f"""
            Enhance these progressive disclosure levels for the concept "{concept}":
            Context: {context}
            
            Current levels:
            {chr(10).join([f"Level {l.level}: {l.content}" for l in levels])}
            
            Improve each level to be:
            1. More educationally effective
            2. Progressively more detailed
            3. Clear and memorable
            4. Appropriate for the complexity level
            
            Return the enhanced levels in the same format.
            """
            
            response = self.gemini_agent._make_request(prompt)
            if response:
                # Parse and update levels (simplified implementation)
                return levels  # Would implement full parsing in production
            
        except Exception as e:
            logger.warning(f"Failed to enhance progressive levels: {e}")
        
        return levels


class InteractiveCodeGenerator:
    """Generates interactive code execution cards"""
    
    def __init__(self, gemini_agent=None):
        self.gemini_agent = gemini_agent
    
    def create_interactive_card(self, code: str, test_cases: List[Tuple], 
                              explanation: str = "", language: str = "python") -> Dict[str, Any]:
        """Create an interactive code execution card"""
        
        # Analyze code structure
        code_analysis = self._analyze_code_structure(code, language)
        
        # Generate test cases if not provided
        if not test_cases and self.gemini_agent:
            test_cases = self._generate_test_cases(code, language)
        
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
    
    def _generate_test_cases(self, code: str, language: str) -> List[Tuple]:
        """Generate test cases using AI"""
        if not self.gemini_agent:
            return []
        
        try:
            prompt = f"""
            Generate appropriate test cases for this {language} code:
            
            {code}
            
            Provide 3-5 test cases with inputs and expected outputs.
            Format as: input -> expected_output
            """
            
            response = self.gemini_agent._make_request(prompt)
            if response:
                # Parse test cases from response (simplified)
                return [(1, 1), (5, 5), (10, 55)]  # Example fallback
            
        except Exception as e:
            logger.warning(f"Failed to generate test cases: {e}")
        
        return []


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
        if not HAS_MATPLOTLIB:
            return {"svg": "<svg>Neural Network Diagram (matplotlib required)</svg>", "components": []}
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Draw basic network structure
        layers = metadata.get("layers", [3, 4, 2])
        layer_positions = []
        
        for i, layer_size in enumerate(layers):
            x = i * 3
            y_positions = [(j - layer_size/2) * 1.5 for j in range(layer_size)]
            layer_positions.append([(x, y) for y in y_positions])
            
            # Draw neurons
            for y in y_positions:
                if f"layer_{i}_neuron" not in missing_components:
                    circle = plt.Circle((x, y), 0.3, color='lightblue', ec='black')
                    ax.add_patch(circle)
                else:
                    # Missing component placeholder
                    circle = plt.Circle((x, y), 0.3, color='lightgray', ec='red', linestyle='--')
                    ax.add_patch(circle)
        
        # Draw connections
        for i in range(len(layers) - 1):
            for pos1 in layer_positions[i]:
                for pos2 in layer_positions[i + 1]:
                    if "connections" not in missing_components:
                        ax.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]], 'k-', alpha=0.3)
        
        ax.set_xlim(-1, len(layers) * 3)
        ax.set_ylim(-max(layers), max(layers))
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('Neural Network Architecture')
        
        # Convert to SVG
        svg_buffer = io.StringIO()
        plt.savefig(svg_buffer, format='svg')
        svg_content = svg_buffer.getvalue()
        plt.close()
        
        return {
            "svg": svg_content,
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


class MultiModalProcessor:
    """Processes multi-modal content (video, audio, images)"""
    
    def __init__(self, gemini_agent=None):
        self.gemini_agent = gemini_agent
    
    def process_video_content(self, video_url: str, extract_frames: bool = True,
                            transcribe_audio: bool = True) -> List[Dict[str, Any]]:
        """Process video content into flashcards"""
        cards = []
        
        # Placeholder implementation - would use actual video processing libraries
        video_metadata = {
            "url": video_url,
            "duration": "unknown",
            "format": "unknown"
        }
        
        if extract_frames:
            # Extract key frames
            key_frames = self._extract_key_frames(video_url)
            for frame in key_frames:
                cards.append(self._create_frame_card(frame, video_metadata))
        
        if transcribe_audio:
            # Transcribe audio
            transcript = self._transcribe_audio(video_url)
            if transcript:
                cards.extend(self._create_transcript_cards(transcript, video_metadata))
        
        return cards
    
    def _extract_key_frames(self, video_url: str) -> List[Dict[str, Any]]:
        """Extract key frames from video"""
        # Placeholder - would use OpenCV or similar
        return [
            {"timestamp": "00:01:30", "description": "Introduction slide"},
            {"timestamp": "00:05:45", "description": "Main concept diagram"},
            {"timestamp": "00:10:20", "description": "Code example"}
        ]
    
    def _transcribe_audio(self, video_url: str) -> str:
        """Transcribe audio from video"""
        # Placeholder - would use speech recognition API
        return "This is a placeholder transcript of the video content."
    
    def _create_frame_card(self, frame: Dict[str, Any], 
                          video_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create flashcard from video frame"""
        return {
            "type": "video_frame",
            "timestamp": frame["timestamp"],
            "description": frame["description"],
            "video_metadata": video_metadata,
            "front": f"What is shown at {frame['timestamp']}?",
            "back": frame["description"],
            "hint": "Think about the visual content at this timestamp",
            "tags": "video,frame,visual",
            "template_id": "video_frame",
            "difficulty": "intermediate"
        }
    
    def _create_transcript_cards(self, transcript: str, 
                               video_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create flashcards from transcript"""
        # Simple sentence splitting - would use more sophisticated NLP
        sentences = transcript.split('. ')
        cards = []
        
        for i, sentence in enumerate(sentences):
            if len(sentence.strip()) > 20:  # Filter short sentences
                cards.append({
                    "type": "transcript",
                    "sentence_index": i,
                    "video_metadata": video_metadata,
                    "front": "Complete this statement from the video:",
                    "back": sentence.strip(),
                    "content": f"{{{{c1::{sentence.strip()}}}}}",
                    "hint": "Recall the spoken content from the video",
                    "tags": "video,transcript,audio",
                    "template_id": "transcript_cloze",
                    "difficulty": "intermediate"
                })
        
        return cards


class AdvancedTemplateSelector:
    """Advanced template selection interface"""
    
    def __init__(self):
        self.template_categories = {
            "primary": ["front_back", "cloze", "cloze_input"],
            "secondary": {
                "front_back": ["definition", "explanation", "application", "comparison"],
                "cloze": ["concept", "formula", "code", "process"],
                "cloze_input": ["partial", "sequential", "deterministic"]
            },
            "granular": {
                "definition": ["basic", "detailed", "contextual"],
                "explanation": ["step_by_step", "conceptual", "practical"],
                "code": ["syntax", "logic", "algorithm", "debugging"]
            }
        }
    
    def interactive_selection(self) -> Dict[str, Any]:
        """Interactive template selection interface"""
        if not HAS_RICH:
            return self._fallback_selection()
        
        console = Console()
        
        console.print("\n[bold blue]Advanced Template Selection[/bold blue]\n")
        
        # Primary level selection
        primary_table = Table(title="Primary Card Types")
        primary_table.add_column("Option", style="cyan")
        primary_table.add_column("Description", style="green")
        
        primary_table.add_row("1", "Front/Back - Traditional question/answer cards")
        primary_table.add_row("2", "Cloze - Fill-in-the-blank cards")
        primary_table.add_row("3", "Cloze Input - Active completion cards")
        primary_table.add_row("4", "All Types - Generate all card types")
        
        console.print(primary_table)
        
        # This would be interactive in a full implementation
        selection = {
            "primary_type": "all",
            "secondary_types": ["definition", "concept", "partial"],
            "granular_options": ["detailed", "step_by_step", "algorithm"],
            "custom_filters": {
                "difficulty": ["intermediate", "advanced"],
                "content_type": ["code", "concept"],
                "learning_objective": ["understanding", "application"]
            }
        }
        
        return selection
    
    def _fallback_selection(self) -> Dict[str, Any]:
        """Fallback selection without rich interface"""
        return {
            "primary_type": "all",
            "secondary_types": ["definition", "concept", "partial"],
            "granular_options": ["detailed", "step_by_step", "algorithm"]
        }
    
    def apply_selection(self, cards: List[Dict[str, Any]], 
                       selection: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply template selection to filter cards"""
        filtered_cards = []
        
        for card in cards:
            if self._matches_selection(card, selection):
                filtered_cards.append(card)
        
        return filtered_cards
    
    def _matches_selection(self, card: Dict[str, Any], 
                          selection: Dict[str, Any]) -> bool:
        """Check if card matches selection criteria"""
        # Primary type check
        if selection["primary_type"] != "all":
            if card.get("type") != selection["primary_type"]:
                return False
        
        # Secondary type check
        template_id = card.get("template_id", "")
        if selection.get("secondary_types"):
            if not any(sec_type in template_id for sec_type in selection["secondary_types"]):
                return False
        
        # Custom filters
        custom_filters = selection.get("custom_filters", {})
        
        if "difficulty" in custom_filters:
            if card.get("difficulty") not in custom_filters["difficulty"]:
                return False
        
        if "content_type" in custom_filters:
            tags = card.get("tags", "").lower()
            if not any(content_type in tags for content_type in custom_filters["content_type"]):
                return False
        
        return True


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


def process_video_content(video_url: str, **kwargs) -> List[Dict[str, Any]]:
    """Factory function for video content processing"""
    processor = MultiModalProcessor()
    return processor.process_video_content(video_url, **kwargs)
