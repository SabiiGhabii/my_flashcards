"""
HuggingFace Integration for Flashcard Generation

This module provides integration with HuggingFace models for:
- Text generation and enhancement
- Content similarity detection
- Embedding-based card deduplication
- Local and API-based inference
"""

import time
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Try to import HuggingFace dependencies
try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


class InferenceMode(Enum):
    """Inference mode options"""
    LOCAL = "local"
    API = "api"
    AUTO = "auto"


@dataclass
class HuggingFaceConfig:
    """Configuration for HuggingFace integration"""
    api_token: str = ""
    text_model: str = "microsoft/DialoGPT-medium"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    inference_mode: InferenceMode = InferenceMode.LOCAL
    max_length: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    rate_limit_delay: float = 1.0
    enable_cache: bool = True


class HuggingFaceAgent:
    """HuggingFace agent for flashcard generation tasks"""
    
    def __init__(self, config: HuggingFaceConfig):
        self.config = config
        self.text_pipeline = None
        self.embedding_model = None
        self.cache = {}
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize HuggingFace models"""
        if not HAS_TRANSFORMERS:
            logger.warning("Transformers not available - HuggingFace integration disabled")
            return
        
        try:
            # Initialize text generation pipeline
            if self.config.inference_mode in [InferenceMode.LOCAL, InferenceMode.AUTO]:
                logger.info(f"Loading text model: {self.config.text_model}")
                self.text_pipeline = pipeline(
                    "text-generation",
                    model=self.config.text_model,
                    tokenizer=self.config.text_model,
                    device=0 if torch.cuda.is_available() else -1
                )
                logger.info("✓ Text generation model loaded")
            
            # Initialize embedding model
            if HAS_SENTENCE_TRANSFORMERS:
                logger.info(f"Loading embedding model: {self.config.embedding_model}")
                self.embedding_model = SentenceTransformer(self.config.embedding_model)
                logger.info("✓ Embedding model loaded")
            
        except Exception as e:
            logger.error(f"Failed to initialize HuggingFace models: {e}")
            self.text_pipeline = None
            self.embedding_model = None
    
    def enhance_card_content(self, card_content: str, context: str = "") -> str:
        """Enhance card content using HuggingFace models"""
        if not self.text_pipeline:
            return card_content
        
        try:
            # Create enhancement prompt
            prompt = self._create_enhancement_prompt(card_content, context)
            
            # Generate enhanced content
            if self.config.inference_mode == InferenceMode.LOCAL:
                enhanced = self._generate_local(prompt)
            else:
                enhanced = self._generate_api(prompt)
            
            return enhanced or card_content
            
        except Exception as e:
            logger.warning(f"Card enhancement failed: {e}")
            return card_content
    
    def _create_enhancement_prompt(self, content: str, context: str) -> str:
        """Create prompt for content enhancement"""
        prompt = f"""Improve this flashcard content to be more educational and clear:

Original: {content}
Context: {context}

Enhanced:"""
        return prompt
    
    def _generate_local(self, prompt: str) -> Optional[str]:
        """Generate text using local model"""
        if not self.text_pipeline:
            return None
        
        try:
            # Check cache
            cache_key = hash(prompt)
            if self.config.enable_cache and cache_key in self.cache:
                return self.cache[cache_key]
            
            # Generate text
            outputs = self.text_pipeline(
                prompt,
                max_length=self.config.max_length,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                do_sample=True,
                pad_token_id=self.text_pipeline.tokenizer.eos_token_id
            )
            
            if outputs and len(outputs) > 0:
                generated_text = outputs[0]['generated_text']
                # Extract only the new part
                enhanced = generated_text[len(prompt):].strip()
                
                # Cache result
                if self.config.enable_cache:
                    self.cache[cache_key] = enhanced
                
                return enhanced
            
        except Exception as e:
            logger.warning(f"Local generation failed: {e}")
        
        return None
    
    def _generate_api(self, prompt: str) -> Optional[str]:
        """Generate text using HuggingFace API"""
        if not HAS_REQUESTS or not self.config.api_token:
            return None
        
        try:
            # Check cache
            cache_key = hash(prompt)
            if self.config.enable_cache and cache_key in self.cache:
                return self.cache[cache_key]
            
            # API request
            headers = {"Authorization": f"Bearer {self.config.api_token}"}
            data = {
                "inputs": prompt,
                "parameters": {
                    "max_length": self.config.max_length,
                    "temperature": self.config.temperature,
                    "top_p": self.config.top_p
                }
            }
            
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{self.config.text_model}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get('generated_text', '')
                    enhanced = generated_text[len(prompt):].strip()
                    
                    # Cache result
                    if self.config.enable_cache:
                        self.cache[cache_key] = enhanced
                    
                    return enhanced
            
            # Rate limiting
            time.sleep(self.config.rate_limit_delay)
            
        except Exception as e:
            logger.warning(f"API generation failed: {e}")
        
        return None
    
    def detect_similar_cards(self, cards: List[Dict[str, Any]], 
                           similarity_threshold: float = 0.8) -> List[Tuple[int, int, float]]:
        """Detect similar cards using embeddings"""
        if not self.embedding_model or len(cards) < 2:
            return []
        
        try:
            # Extract text content from cards
            texts = []
            for card in cards:
                text = card.get('front', '') + ' ' + card.get('back', '') + ' ' + card.get('content', '')
                texts.append(text.strip())
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(embeddings)
            
            # Find similar pairs
            similar_pairs = []
            for i in range(len(cards)):
                for j in range(i + 1, len(cards)):
                    similarity = similarity_matrix[i][j]
                    if similarity >= similarity_threshold:
                        similar_pairs.append((i, j, similarity))
            
            # Sort by similarity (highest first)
            similar_pairs.sort(key=lambda x: x[2], reverse=True)
            
            return similar_pairs
            
        except Exception as e:
            logger.warning(f"Similarity detection failed: {e}")
            return []
    
    def generate_card_variations(self, card: Dict[str, Any], num_variations: int = 3) -> List[Dict[str, Any]]:
        """Generate variations of a card"""
        if not self.text_pipeline:
            return []
        
        variations = []
        
        try:
            original_front = card.get('front', '')
            original_back = card.get('back', '')
            
            for i in range(num_variations):
                # Create variation prompt
                prompt = f"""Create a variation of this flashcard question while keeping the same answer:

Original Question: {original_front}
Answer: {original_back}

Variation {i+1}:"""
                
                # Generate variation
                if self.config.inference_mode == InferenceMode.LOCAL:
                    variation_text = self._generate_local(prompt)
                else:
                    variation_text = self._generate_api(prompt)
                
                if variation_text:
                    variation_card = card.copy()
                    variation_card['front'] = variation_text
                    variation_card['tags'] = card.get('tags', '') + ',variation'
                    variations.append(variation_card)
            
        except Exception as e:
            logger.warning(f"Variation generation failed: {e}")
        
        return variations
    
    def extract_key_concepts(self, text: str, max_concepts: int = 10) -> List[str]:
        """Extract key concepts from text using embeddings"""
        if not self.embedding_model:
            return []
        
        try:
            # Split text into sentences
            sentences = text.split('. ')
            if len(sentences) < 2:
                return []
            
            # Generate embeddings for sentences
            embeddings = self.embedding_model.encode(sentences)
            
            # Calculate sentence importance (simplified)
            # In a more sophisticated implementation, this would use
            # techniques like TextRank or other centrality measures
            
            # For now, return the first few sentences as key concepts
            concepts = []
            for i, sentence in enumerate(sentences[:max_concepts]):
                if len(sentence.strip()) > 20:  # Filter out very short sentences
                    concepts.append(sentence.strip())
            
            return concepts
            
        except Exception as e:
            logger.warning(f"Concept extraction failed: {e}")
            return []
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "has_transformers": HAS_TRANSFORMERS,
            "has_sentence_transformers": HAS_SENTENCE_TRANSFORMERS,
            "has_requests": HAS_REQUESTS,
            "text_model_loaded": self.text_pipeline is not None,
            "embedding_model_loaded": self.embedding_model is not None,
            "inference_mode": self.config.inference_mode.value,
            "cache_size": len(self.cache),
            "cuda_available": torch.cuda.is_available() if HAS_TRANSFORMERS else False
        }


# Factory function
def create_huggingface_agent(config: Dict[str, Any]) -> Optional[HuggingFaceAgent]:
    """Create a HuggingFace agent"""
    if not HAS_TRANSFORMERS:
        logger.warning("HuggingFace integration not available - transformers not installed")
        return None
    
    try:
        hf_config = HuggingFaceConfig(
            api_token=config.get('api_token', ''),
            text_model=config.get('text_model', 'microsoft/DialoGPT-medium'),
            embedding_model=config.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2'),
            inference_mode=InferenceMode(config.get('inference_mode', 'local')),
            max_length=config.get('max_length', 512),
            temperature=config.get('temperature', 0.7),
            top_p=config.get('top_p', 0.9),
            rate_limit_delay=config.get('rate_limit_delay', 1.0),
            enable_cache=config.get('enable_cache', True)
        )
        
        return HuggingFaceAgent(hf_config)
        
    except Exception as e:
        logger.error(f"Failed to create HuggingFace agent: {e}")
        return None
