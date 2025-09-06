#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
flashcardify_enhanced.py
Enhanced flashcard generation with AI-powered content recognition and multi-format support.

Features:
- AI-powered content analysis using sentence transformers and Gemini
- Multi-format support: PDF, GitHub repos, HTML docs, URLs, LeetCode problems
- Advanced template system with specialized templates
- Intelligent content extraction and pedagogical optimization
- Custom instruction support for card generation

Usage:
  python flashcardify_enhanced.py -i Book.pdf -o flashcards.csv --source pdf
  python flashcardify_enhanced.py -i https://github.com/user/repo -o flashcards.csv --source github
  python flashcardify_enhanced.py -i https://leetcode.com/problems/two-sum/ -o flashcards.csv --source leetcode
  python flashcardify_enhanced.py -i https://docs.python.org/3/library/os.html -o flashcards.csv --source html
"""

import argparse
import csv
import json
import os
import random
import re
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from abc import ABC, abstractmethod

import fitz  # PyMuPDF
import nltk
from tqdm import tqdm

# AI and NLP
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

# Web support
try:
    import requests
    from bs4 import BeautifulSoup
    HAS_WEB_SUPPORT = True
except ImportError:
    HAS_WEB_SUPPORT = False

# GitHub API
try:
    import github
    HAS_GITHUB = True
except ImportError:
    HAS_GITHUB = False

# keyphrase helpers
import yake
from keybert import KeyBERT

# Optional: Gemini
try:
    import google.generativeai as genai
    import time
    from typing import Optional, Dict, Any, List
    from gemini_integration import create_gemini_agent, GeminiAgent, ContentType, MultiAgentGeminiSystem
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


# ----------------------- Configuration -----------------------

@dataclass
class Config:
    """Configuration for flashcard generation"""
    use_ai: bool = True
    use_gemini: bool = False
    max_cards_per_section: int = 50
    min_concept_length: int = 3
    max_concept_length: int = 100
    similarity_threshold: float = 0.7
    custom_instructions: str = ""
    gemini_api_key: Optional[str] = None


# ----------------------- AI-Powered Content Analyzer -----------------------

class AIContentAnalyzer:
    """AI-powered content analysis using sentence transformers and clustering"""
    
    def __init__(self, config: Config):
        self.config = config
        self.model = None
        if HAS_SENTENCE_TRANSFORMERS and config.use_ai:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                print(f"Warning: Could not load sentence transformer: {e}")
                self.model = None
    
    def extract_key_concepts(self, text: str, max_concepts: int = 20) -> List[Tuple[str, float]]:
        """Extract key concepts using AI-powered analysis"""
        if not self.model:
            return self._fallback_extraction(text, max_concepts)
        
        try:
            # Split into sentences
            sentences = nltk.sent_tokenize(text)
            if len(sentences) < 2:
                return self._fallback_extraction(text, max_concepts)
            
            # Encode sentences
            embeddings = self.model.encode(sentences)
            
            # Cluster sentences to find key topics
            n_clusters = min(max_concepts // 2, len(sentences) // 2, 10)
            if n_clusters < 2:
                return self._fallback_extraction(text, max_concepts)
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(embeddings)
            
            # Extract representative sentences from each cluster
            concepts = []
            for i in range(n_clusters):
                cluster_sentences = [sentences[j] for j in range(len(sentences)) if clusters[j] == i]
                if cluster_sentences:
                    # Find sentence closest to cluster center
                    cluster_embeddings = [embeddings[j] for j in range(len(sentences)) if clusters[j] == i]
                    center = np.mean(cluster_embeddings, axis=0)
                    similarities = cosine_similarity([center], cluster_embeddings)[0]
                    best_idx = np.argmax(similarities)
                    best_sentence = cluster_sentences[best_idx]
                    
                    # Extract key terms from the sentence
                    key_terms = self._extract_terms_from_sentence(best_sentence)
                    for term in key_terms:
                        if self.config.min_concept_length <= len(term) <= self.config.max_concept_length:
                            concepts.append((term, similarities[best_idx]))
            
            # Sort by importance and return top concepts
            concepts.sort(key=lambda x: x[1], reverse=True)
            return concepts[:max_concepts]
            
        except Exception as e:
            print(f"Warning: AI analysis failed, falling back to heuristics: {e}")
            return self._fallback_extraction(text, max_concepts)
    
    def _extract_terms_from_sentence(self, sentence: str) -> List[str]:
        """Extract key terms from a sentence"""
        # Use KeyBERT if available
        try:
            kb = KeyBERT()
            keywords = kb.extract_keywords(sentence, top_n=5, stop_words='english')
            return [kw[0] for kw in keywords]
        except:
            # Fallback to simple noun phrase extraction
            words = nltk.word_tokenize(sentence)
            pos_tags = nltk.pos_tag(words)
            terms = []
            current_term = []
            
            for word, pos in pos_tags:
                if pos.startswith('NN') or pos.startswith('JJ'):  # Nouns and adjectives
                    current_term.append(word)
                else:
                    if current_term:
                        terms.append(' '.join(current_term))
                        current_term = []
            
            if current_term:
                terms.append(' '.join(current_term))
            
            return [term for term in terms if len(term) > 2]
    
    def _fallback_extraction(self, text: str, max_concepts: int) -> List[Tuple[str, float]]:
        """Fallback extraction using YAKE and KeyBERT"""
        concepts = []
        
        # YAKE extraction
        try:
            y = yake.KeywordExtractor(lan="en", n=1, top=max_concepts)
            for kw, score in y.extract_keywords(text):
                if self.config.min_concept_length <= len(kw) <= self.config.max_concept_length:
                    concepts.append((kw.strip(), 1.0 - score))  # Convert to similarity score
        except Exception:
            pass
        
        # KeyBERT extraction
        try:
            kb = KeyBERT()
            for phrase, score in kb.extract_keywords(text, top_n=max_concepts, stop_words="english"):
                if self.config.min_concept_length <= len(phrase) <= self.config.max_concept_length:
                    concepts.append((phrase.strip(), score))
        except Exception:
            pass
        
        # Deduplicate and sort
        seen = set()
        unique_concepts = []
        for concept, score in concepts:
            if concept.lower() not in seen:
                seen.add(concept.lower())
                unique_concepts.append((concept, score))
        
        unique_concepts.sort(key=lambda x: x[1], reverse=True)
        return unique_concepts[:max_concepts]
    
    def analyze_code_complexity(self, code: str) -> Dict[str, Any]:
        """Analyze code complexity for better card generation"""
        analysis = {
            'functions': [],
            'classes': [],
            'imports': [],
            'complexity_score': 0,
            'key_concepts': []
        }
        
        lines = code.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('def '):
                analysis['functions'].append(line)
            elif line.startswith('class '):
                analysis['classes'].append(line)
            elif line.startswith(('import ', 'from ')):
                analysis['imports'].append(line)
        
        # Simple complexity scoring
        analysis['complexity_score'] = len(analysis['functions']) * 2 + len(analysis['classes']) * 3
        
        # Extract key concepts from code
        if self.model:
            try:
                # Remove code syntax for better concept extraction
                clean_text = re.sub(r'[{}()\[\];,]', ' ', code)
                clean_text = re.sub(r'\s+', ' ', clean_text)
                concepts = self.extract_key_concepts(clean_text, max_concepts=10)
                analysis['key_concepts'] = [concept for concept, _ in concepts]
            except:
                pass
        
        return analysis


# ----------------------- Content Source Handlers -----------------------

class ContentSource(ABC):
    """Abstract base class for content sources"""
    
    @abstractmethod
    def extract_content(self, source: str) -> Dict[str, Any]:
        """Extract content from the source"""
        pass
    
    @abstractmethod
    def get_sections(self, content: Dict[str, Any]) -> List[Tuple[str, List[str]]]:
        """Get sections from extracted content"""
        pass


class PDFSource(ContentSource):
    """PDF content source handler"""
    
    def extract_content(self, source: str) -> Dict[str, Any]:
        """Extract content from PDF file"""
        doc = fitz.open(source)
        blocks = self._extract_blocks(doc)
        sections = self._split_sections(blocks)
        doc.close()
        
        return {
            'type': 'pdf',
            'source': source,
            'sections': sections,
            'total_pages': len(doc)
        }
    
    def get_sections(self, content: Dict[str, Any]) -> List[Tuple[str, List[str]]]:
        """Get sections from PDF content"""
        return content['sections']
    
    def _extract_blocks(self, doc: fitz.Document) -> List[Dict]:
        """Extract text blocks from PDF"""
        blocks = []
        for pno in range(len(doc)):
            page = doc[pno]
            data = page.get_text("dict")
            for b in data.get("blocks", []):
                if b.get("type", 0) != 0:
                    continue
                
                texts = []
                sizes = []
                bold_flags = []
                
                for line in b.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text:
                            texts.append(text)
                            sizes.append(float(span.get("size", 0)))
                            flags = int(span.get("flags", 0))
                            bold_flags.append(bool(flags & 2))
                
                if texts:
                    avg_size = sum(sizes) / len(sizes) if sizes else 10
                    has_bold = any(bold_flags)
                    blocks.append({
                        'page': pno + 1,
                        'text': ''.join(texts),
                        'size_avg': avg_size,
                        'bold_any': has_bold
                    })
        
        return blocks
    
    def _split_sections(self, blocks: List[Dict]) -> List[Tuple[str, List[str]]]:
        """Split blocks into sections"""
        if not blocks:
            return []
        
        sizes = [b['size_avg'] for b in blocks]
        median_size = sorted(sizes)[len(sizes) // 2] if sizes else 10
        
        sections = []
        current_title = "Introduction"
        current_paragraphs = []
        
        for block in blocks:
            text = block['text'].strip()
            if not text:
                continue
            
            # Check if this is a heading
            is_heading = (
                block['size_avg'] >= median_size + 1.0 or
                (block['bold_any'] and len(text) <= 120) or
                bool(re.match(r"^(\d+(\.\d+)*|[Cc]hapter\s+\d+|[Ss]ection\s+\d+)", text)) or
                (text.upper() == text and len(text) <= 80)
            )
            
            if is_heading:
                if current_paragraphs:
                    sections.append((current_title, current_paragraphs))
                    current_paragraphs = []
                current_title = text
            else:
                current_paragraphs.append(text)
        
        if current_paragraphs:
            sections.append((current_title, current_paragraphs))
        
        return sections


class GitHubSource(ContentSource):
    """GitHub repository content source handler"""

    def __init__(self):
        if not HAS_GITHUB or not HAS_WEB_SUPPORT:
            raise ImportError("GitHub support requires 'PyGithub' and 'requests' packages")

    def extract_content(self, source: str) -> Dict[str, Any]:
        """Extract content from GitHub repository"""
        # Parse GitHub URL
        parsed = urllib.parse.urlparse(source)
        path_parts = parsed.path.strip('/').split('/')

        if len(path_parts) < 2:
            raise ValueError("Invalid GitHub URL format")

        owner, repo = path_parts[0], path_parts[1]

        # Use GitHub API to get repository content
        try:
            g = github.Github()  # Anonymous access
            repository = g.get_repo(f"{owner}/{repo}")

            content = {
                'type': 'github',
                'source': source,
                'owner': owner,
                'repo': repo,
                'description': repository.description or "",
                'files': [],
                'readme': ""
            }

            # Get README
            try:
                readme = repository.get_readme()
                content['readme'] = readme.decoded_content.decode('utf-8')
            except:
                pass

            # Get code files (limit to avoid rate limiting)
            files = repository.get_contents("")
            code_files = []

            for file in files[:20]:  # Limit to first 20 files
                if file.type == "file" and self._is_code_file(file.name):
                    try:
                        file_content = file.decoded_content.decode('utf-8')
                        code_files.append({
                            'name': file.name,
                            'path': file.path,
                            'content': file_content,
                            'size': file.size
                        })
                    except:
                        continue

            content['files'] = code_files
            return content

        except Exception as e:
            # Fallback to web scraping
            return self._scrape_github_repo(source)

    def get_sections(self, content: Dict[str, Any]) -> List[Tuple[str, List[str]]]:
        """Get sections from GitHub content"""
        sections = []

        # Add README as a section
        if content.get('readme'):
            sections.append(("README", [content['readme']]))

        # Add code files as sections
        for file in content.get('files', []):
            file_name = file['name']
            file_content = file['content']

            # Split large files into smaller sections
            if len(file_content) > 2000:
                chunks = self._split_code_into_chunks(file_content)
                for i, chunk in enumerate(chunks):
                    section_name = f"{file_name} (Part {i+1})"
                    sections.append((section_name, [chunk]))
            else:
                sections.append((file_name, [file_content]))

        return sections

    def _is_code_file(self, filename: str) -> bool:
        """Check if file is a code file"""
        code_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt',
            '.scala', '.clj', '.hs', '.ml', '.r', '.m', '.sh'
        }
        return any(filename.lower().endswith(ext) for ext in code_extensions)

    def _split_code_into_chunks(self, code: str, max_lines: int = 50) -> List[str]:
        """Split code into manageable chunks"""
        lines = code.split('\n')
        chunks = []
        current_chunk = []

        for line in lines:
            current_chunk.append(line)
            if len(current_chunk) >= max_lines:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []

        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def _scrape_github_repo(self, url: str) -> Dict[str, Any]:
        """Fallback web scraping for GitHub repos"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract basic info
            content = {
                'type': 'github',
                'source': url,
                'files': [],
                'readme': ""
            }

            # Try to get README content
            readme_div = soup.find('div', {'id': 'readme'})
            if readme_div:
                content['readme'] = readme_div.get_text(strip=True)

            return content

        except Exception as e:
            raise ValueError(f"Could not access GitHub repository: {e}")


class HTMLSource(ContentSource):
    """HTML documentation content source handler"""

    def __init__(self):
        if not HAS_WEB_SUPPORT:
            raise ImportError("HTML support requires 'requests' and 'beautifulsoup4' packages")

    def extract_content(self, source: str) -> Dict[str, Any]:
        """Extract content from HTML documentation"""
        try:
            response = requests.get(source)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            content = {
                'type': 'html',
                'source': source,
                'title': soup.title.string if soup.title else "Documentation",
                'sections': []
            }

            # Extract sections based on headings
            sections = []
            current_section = None
            current_content = []

            for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre', 'code', 'div']):
                if element.name.startswith('h'):
                    # New section
                    if current_section and current_content:
                        sections.append((current_section, current_content))
                    current_section = element.get_text(strip=True)
                    current_content = []
                else:
                    # Content
                    text = element.get_text(strip=True)
                    if text and len(text) > 10:  # Filter out very short content
                        current_content.append(text)

            # Add final section
            if current_section and current_content:
                sections.append((current_section, current_content))

            content['sections'] = sections
            return content

        except Exception as e:
            raise ValueError(f"Could not access HTML content: {e}")

    def get_sections(self, content: Dict[str, Any]) -> List[Tuple[str, List[str]]]:
        """Get sections from HTML content"""
        return content.get('sections', [])


class LeetCodeSource(ContentSource):
    """LeetCode problem content source handler"""

    def __init__(self):
        if not HAS_WEB_SUPPORT:
            raise ImportError("LeetCode support requires 'requests' and 'beautifulsoup4' packages")

    def extract_content(self, source: str) -> Dict[str, Any]:
        """Extract content from LeetCode problem"""
        try:
            # LeetCode requires special handling due to dynamic content
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(source, headers=headers)
            response.raise_for_status()

            # Extract problem slug from URL
            problem_slug = source.split('/')[-2] if source.endswith('/') else source.split('/')[-1]

            content = {
                'type': 'leetcode',
                'source': source,
                'problem_slug': problem_slug,
                'title': "",
                'description': "",
                'examples': [],
                'constraints': "",
                'solution_approaches': []
            }

            # For now, return basic structure
            # In a full implementation, you'd use LeetCode's GraphQL API
            # or more sophisticated scraping

            content['title'] = f"LeetCode Problem: {problem_slug.replace('-', ' ').title()}"
            content['description'] = f"Problem from {source}"

            return content

        except Exception as e:
            raise ValueError(f"Could not access LeetCode problem: {e}")

    def get_sections(self, content: Dict[str, Any]) -> List[Tuple[str, List[str]]]:
        """Get sections from LeetCode content"""
        sections = []

        if content.get('title'):
            sections.append(("Problem Title", [content['title']]))

        if content.get('description'):
            sections.append(("Problem Description", [content['description']]))

        if content.get('examples'):
            sections.append(("Examples", content['examples']))

        if content.get('solution_approaches'):
            sections.append(("Solution Approaches", content['solution_approaches']))

        return sections


# ----------------------- Enhanced Card Generator -----------------------

class EnhancedCardGenerator:
    """Enhanced flashcard generator with AI-powered content analysis"""

    def __init__(self, config: Config, templates: Dict[str, List[dict]]):
        self.config = config
        self.templates = templates
        self.analyzer = AIContentAnalyzer(config)

        # Initialize Gemini if available
        self.gemini_model = None
        if config.use_gemini and HAS_GEMINI and config.gemini_api_key:
            try:
                genai.configure(api_key=config.gemini_api_key)
                self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
            except Exception as e:
                print(f"Warning: Could not initialize Gemini: {e}")

    def generate_cards_from_section(self, title: str, paragraphs: List[str], source_type: str = 'pdf') -> List[Dict[str, str]]:
        """Generate flashcards from a section with AI-powered analysis"""
        cards = []
        joined_text = "\n".join(paragraphs)

        # AI-powered concept extraction
        key_concepts = self.analyzer.extract_key_concepts(joined_text, max_concepts=30)

        # Generate different types of cards based on content type
        if source_type == 'github':
            cards.extend(self._generate_code_cards(title, paragraphs, key_concepts))
        elif source_type == 'leetcode':
            cards.extend(self._generate_leetcode_cards(title, paragraphs, key_concepts))
        elif source_type == 'html':
            cards.extend(self._generate_documentation_cards(title, paragraphs, key_concepts))
        else:  # PDF and general content
            cards.extend(self._generate_general_cards(title, paragraphs, key_concepts))

        # Apply custom instructions if provided
        if self.config.custom_instructions:
            cards = self._apply_custom_instructions(cards, self.config.custom_instructions)

        return cards[:self.config.max_cards_per_section]

    def _generate_code_cards(self, title: str, paragraphs: List[str], key_concepts: List[Tuple[str, float]]) -> List[Dict[str, str]]:
        """Generate cards specifically for code content"""
        cards = []

        for paragraph in paragraphs:
            if self._is_code_content(paragraph):
                # Analyze code complexity
                analysis = self.analyzer.analyze_code_complexity(paragraph)

                # Generate cloze input cards for functions
                for func in analysis['functions']:
                    cards.append(self._create_code_completion_card(func, title))

                # Generate explanation cards for complex code
                if analysis['complexity_score'] > 5:
                    cards.append(self._create_code_explanation_card(paragraph, title, analysis))

                # Generate API usage cards
                if analysis['imports']:
                    for import_stmt in analysis['imports']:
                        cards.append(self._create_api_usage_card(import_stmt, title))

        return cards

    def _generate_leetcode_cards(self, title: str, paragraphs: List[str], key_concepts: List[Tuple[str, float]]) -> List[Dict[str, str]]:
        """Generate cards specifically for LeetCode problems"""
        cards = []

        # Algorithm explanation cards
        for concept, score in key_concepts[:10]:
            if any(algo in concept.lower() for algo in ['sort', 'search', 'tree', 'graph', 'dynamic', 'greedy']):
                cards.append(self._create_algorithm_explanation_card(concept, title))

        # Time/space complexity cards
        for paragraph in paragraphs:
            if 'complexity' in paragraph.lower():
                cards.append(self._create_complexity_card(paragraph, title))

        return cards

    def _generate_documentation_cards(self, title: str, paragraphs: List[str], key_concepts: List[Tuple[str, float]]) -> List[Dict[str, str]]:
        """Generate cards for documentation content"""
        cards = []

        # API documentation cards
        for paragraph in paragraphs:
            if self._is_api_documentation(paragraph):
                cards.append(self._create_api_documentation_card(paragraph, title))

        # Concept definition cards
        for concept, score in key_concepts[:15]:
            definition = self._extract_definition_for_concept(concept, paragraphs)
            if definition:
                cards.append(self._create_concept_definition_card(concept, definition, title))

        return cards

    def _generate_general_cards(self, title: str, paragraphs: List[str], key_concepts: List[Tuple[str, float]]) -> List[Dict[str, str]]:
        """Generate general-purpose cards"""
        cards = []

        # Concept cards
        for concept, score in key_concepts[:20]:
            definition = self._extract_definition_for_concept(concept, paragraphs)
            if definition:
                cards.append(self._create_concept_definition_card(concept, definition, title))

        # Extract equations and create math cards
        equations = self._extract_equations(paragraphs)
        for name, equation in equations:
            cards.append(self._create_equation_card(name, equation, title))

        return cards

    def _create_code_completion_card(self, code: str, title: str) -> Dict[str, str]:
        """Create a cloze input card for code completion"""
        # Find a good token to hide
        tokens = re.findall(r'[A-Za-z_][A-Za-z0-9_]*', code)
        if tokens:
            token_to_hide = random.choice(tokens[:3])  # Hide one of the first few tokens
            code_with_cloze = code.replace(token_to_hide, f"{{{{cin1::{token_to_hide}}}}}", 1)
        else:
            code_with_cloze = f"{{{{cin1::{code}}}}}"

        return {
            "type": "cloze_input",
            "front": "",
            "back": "",
            "content": f"~CODE[python]\n{code_with_cloze}\n~",
            "hint": "Complete the missing code. Pay attention to syntax and naming conventions.",
            "tags": f"{title.lower().replace(' ', '_')},code,completion",
            "template_id": "cin_code_completion_enhanced"
        }

    def _create_code_explanation_card(self, code: str, title: str, analysis: Dict) -> Dict[str, str]:
        """Create a card explaining what code does"""
        # Generate explanation using Gemini if available
        explanation = "This code performs a specific function."
        if self.gemini_model:
            try:
                prompt = f"Explain what this code does in 1-2 sentences:\n\n{code}"
                response = self.gemini_model.generate_content(prompt)
                if hasattr(response, 'text'):
                    explanation = response.text.strip()
            except:
                pass

        return {
            "type": "fb",
            "front": f"What does this code do?\n\n~CODE[python]\n{code}\n~",
            "back": explanation,
            "content": "",
            "hint": "Think about the main purpose and key operations.",
            "tags": f"{title.lower().replace(' ', '_')},code,explanation",
            "template_id": "fb_code_explanation_enhanced"
        }

    def _create_api_usage_card(self, import_stmt: str, title: str) -> Dict[str, str]:
        """Create a card for API usage"""
        return {
            "type": "cloze",
            "front": "",
            "back": "",
            "content": f"{{{{c1::{import_stmt}}}}} is used to access specific functionality.",
            "hint": "What import statement provides this functionality?",
            "tags": f"{title.lower().replace(' ', '_')},api,import",
            "template_id": "cloze_api_usage_enhanced"
        }

    def _create_algorithm_explanation_card(self, concept: str, title: str) -> Dict[str, str]:
        """Create a card explaining an algorithm concept"""
        return {
            "type": "fb",
            "front": f"Explain the {concept} algorithm approach.",
            "back": f"The {concept} algorithm...",  # Would be enhanced with AI
            "content": "",
            "hint": "Think about time complexity, space complexity, and key steps.",
            "tags": f"{title.lower().replace(' ', '_')},algorithm,{concept.lower().replace(' ', '_')}",
            "template_id": "fb_algorithm_explanation"
        }

    def _create_complexity_card(self, paragraph: str, title: str) -> Dict[str, str]:
        """Create a card about time/space complexity"""
        # Extract complexity information
        complexity_match = re.search(r'O\([^)]+\)', paragraph)
        complexity = complexity_match.group(0) if complexity_match else "O(?)"

        return {
            "type": "cloze",
            "front": "",
            "back": "",
            "content": f"The time complexity of this algorithm is {{{{c1::{complexity}}}}}.",
            "hint": "Consider the number of operations relative to input size.",
            "tags": f"{title.lower().replace(' ', '_')},complexity,algorithm",
            "template_id": "cloze_complexity"
        }

    def _create_api_documentation_card(self, paragraph: str, title: str) -> Dict[str, str]:
        """Create a card for API documentation"""
        # Extract function/method names
        func_match = re.search(r'(\w+)\s*\([^)]*\)', paragraph)
        func_name = func_match.group(1) if func_match else "function"

        return {
            "type": "fb",
            "front": f"What does the {func_name} function do?",
            "back": paragraph[:200] + "..." if len(paragraph) > 200 else paragraph,
            "content": "",
            "hint": "Consider the function's purpose and parameters.",
            "tags": f"{title.lower().replace(' ', '_')},api,documentation",
            "template_id": "fb_api_documentation"
        }

    def _create_concept_definition_card(self, concept: str, definition: str, title: str) -> Dict[str, str]:
        """Create a concept definition card"""
        return {
            "type": "fb",
            "front": f"What is {concept}?",
            "back": definition,
            "content": "",
            "hint": "Think about the core meaning and key characteristics.",
            "tags": f"{title.lower().replace(' ', '_')},concept,{concept.lower().replace(' ', '_')}",
            "template_id": "fb_concept_enhanced"
        }

    def _create_equation_card(self, name: str, equation: str, title: str) -> Dict[str, str]:
        """Create an equation card"""
        return {
            "type": "cloze",
            "front": "",
            "back": "",
            "content": f"{name}: {{{{c1::{equation}}}}}",
            "hint": "Recall the mathematical formula.",
            "tags": f"{title.lower().replace(' ', '_')},equation,math",
            "template_id": "cloze_equation_enhanced"
        }

    # Helper methods
    def _is_code_content(self, text: str) -> bool:
        """Check if text contains code"""
        code_indicators = ['def ', 'class ', 'import ', 'from ', 'if __name__', 'return ', 'print(']
        return any(indicator in text for indicator in code_indicators)

    def _is_api_documentation(self, text: str) -> bool:
        """Check if text is API documentation"""
        api_indicators = ['function', 'method', 'parameter', 'returns', 'example:', 'usage:']
        return any(indicator in text.lower() for indicator in api_indicators)

    def _extract_definition_for_concept(self, concept: str, paragraphs: List[str]) -> Optional[str]:
        """Extract definition for a concept from paragraphs"""
        for paragraph in paragraphs:
            if concept.lower() in paragraph.lower():
                # Simple heuristic: look for sentences that define the concept
                sentences = nltk.sent_tokenize(paragraph)
                for sentence in sentences:
                    if concept.lower() in sentence.lower() and any(word in sentence.lower() for word in ['is', 'are', 'means', 'refers to']):
                        return sentence.strip()
        return None

    def _extract_equations(self, paragraphs: List[str]) -> List[Tuple[str, str]]:
        """Extract mathematical equations from text"""
        equations = []
        math_pattern = re.compile(r'[=+\-*/^()0-9a-zA-Z\s]+[=][=+\-*/^()0-9a-zA-Z\s]+')

        for paragraph in paragraphs:
            matches = math_pattern.findall(paragraph)
            for match in matches:
                if len(match) > 5 and len(match) < 100:  # Reasonable equation length
                    equations.append(("Equation", match.strip()))

        return equations

    def _apply_custom_instructions(self, cards: List[Dict[str, str]], instructions: str) -> List[Dict[str, str]]:
        """Apply custom instructions to modify card generation"""
        # This would use AI to modify cards based on custom instructions
        # For now, just return cards as-is
        return cards


# ----------------------- Main Application -----------------------

class FlashcardifyEnhanced:
    """Main application class for enhanced flashcard generation"""

    def __init__(self, config: Config):
        self.config = config
        self.templates = self._load_templates()
        self.generator = EnhancedCardGenerator(config, self.templates)

        # Initialize content sources
        self.sources = {
            'pdf': PDFSource(),
            'github': GitHubSource() if HAS_GITHUB and HAS_WEB_SUPPORT else None,
            'html': HTMLSource() if HAS_WEB_SUPPORT else None,
            'leetcode': LeetCodeSource() if HAS_WEB_SUPPORT else None,
        }

    def _load_templates(self) -> Dict[str, List[dict]]:
        """Load template files"""
        template_dir = Path("templates")
        templates = {"fb": [], "cloze": [], "cloze_input": []}

        template_files = {
            "fb": template_dir / "fb_templates.json",
            "cloze": template_dir / "cloze_templates.json",
            "cloze_input": template_dir / "cloze_input_templates.json"
        }

        for template_type, file_path in template_files.items():
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        templates[template_type] = json.load(f)
                except Exception as e:
                    print(f"Warning: Could not load {template_type} templates: {e}")
            else:
                print(f"Warning: Template file not found: {file_path}")

        return templates

    def process_content(self, source: str, source_type: str) -> List[Dict[str, str]]:
        """Process content from various sources and generate flashcards"""
        # Validate source type
        if source_type not in self.sources or self.sources[source_type] is None:
            raise ValueError(f"Unsupported source type: {source_type}")

        # Extract content
        print(f"Extracting content from {source_type} source...")
        content_handler = self.sources[source_type]
        content = content_handler.extract_content(source)
        sections = content_handler.get_sections(content)

        # Generate flashcards
        all_cards = []
        print(f"Generating flashcards from {len(sections)} sections...")

        for title, paragraphs in tqdm(sections, desc="Processing sections"):
            if not paragraphs:
                continue

            cards = self.generator.generate_cards_from_section(title, paragraphs, source_type)
            all_cards.extend(cards)

        # Deduplicate cards
        unique_cards = self._deduplicate_cards(all_cards)

        print(f"Generated {len(unique_cards)} unique flashcards")
        return unique_cards

    def _deduplicate_cards(self, cards: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Remove duplicate cards based on content similarity"""
        if not cards:
            return []

        unique_cards = []
        seen_content = set()

        for card in cards:
            # Create a key based on card content
            content_key = (
                card.get("type", ""),
                (card.get("front", "") + card.get("content", "")).strip().lower()
            )

            if content_key not in seen_content and len(content_key[1]) >= 8:
                seen_content.add(content_key)
                unique_cards.append(card)

        return unique_cards

    def save_cards(self, cards: List[Dict[str, str]], output_path: str):
        """Save flashcards to CSV file"""
        if not cards:
            print("No cards to save.")
            return

        fieldnames = ["type", "front", "back", "content", "hint", "tags", "template_id"]

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for card in cards:
                # Ensure all required fields are present
                row = {field: card.get(field, "") for field in fieldnames}
                writer.writerow(row)

        print(f"Saved {len(cards)} flashcards to {output_path}")


def ensure_nltk():
    """Ensure NLTK data is available"""
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        print("Downloading NLTK data...")
        nltk.download("punkt_tab", quiet=True)

    try:
        nltk.data.find("taggers/averaged_perceptron_tagger_eng")
    except LookupError:
        print("Downloading NLTK POS tagger...")
        nltk.download("averaged_perceptron_tagger_eng", quiet=True)


def detect_source_type(source: str) -> str:
    """Auto-detect source type from input"""
    if source.startswith(('http://', 'https://')):
        if 'github.com' in source:
            return 'github'
        elif 'leetcode.com' in source:
            return 'leetcode'
        else:
            return 'html'
    elif source.endswith('.pdf'):
        return 'pdf'
    else:
        # Default to PDF for local files
        return 'pdf'


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Enhanced flashcard generation with AI-powered content recognition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python flashcardify_enhanced.py -i book.pdf -o cards.csv
  python flashcardify_enhanced.py -i https://github.com/user/repo -o cards.csv --source github
  python flashcardify_enhanced.py -i https://leetcode.com/problems/two-sum/ -o cards.csv --source leetcode
  python flashcardify_enhanced.py -i https://docs.python.org/3/library/os.html -o cards.csv --source html
        """
    )

    parser.add_argument("-i", "--input", required=True,
                       help="Input source (PDF file, GitHub URL, LeetCode URL, or HTML URL)")
    parser.add_argument("-o", "--output", default="flashcards.csv",
                       help="Output CSV file (default: flashcards.csv)")
    parser.add_argument("--source", choices=['pdf', 'github', 'html', 'leetcode'],
                       help="Source type (auto-detected if not specified)")
    parser.add_argument("--use-ai", action="store_true", default=True,
                       help="Use AI-powered content analysis (default: True)")
    parser.add_argument("--use-gemini", action="store_true",
                       help="Use Gemini for enhanced card generation")
    parser.add_argument("--gemini-api-key",
                       help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--max-cards", type=int, default=50,
                       help="Maximum cards per section (default: 50)")
    parser.add_argument("--custom-instructions",
                       help="Custom instructions for card generation")

    args = parser.parse_args()

    # Ensure NLTK data is available
    ensure_nltk()

    # Auto-detect source type if not specified
    source_type = args.source or detect_source_type(args.input)

    # Create configuration
    config = Config(
        use_ai=args.use_ai,
        use_gemini=args.use_gemini,
        max_cards_per_section=args.max_cards,
        custom_instructions=args.custom_instructions or "",
        gemini_api_key=args.gemini_api_key or os.getenv("GEMINI_API_KEY")
    )

    try:
        # Initialize application
        app = FlashcardifyEnhanced(config)

        # Process content and generate cards
        cards = app.process_content(args.input, source_type)

        # Save cards
        app.save_cards(cards, args.output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
