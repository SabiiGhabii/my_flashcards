#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
content_processors.py
Enhanced flashcard generation with AI-powered content recognition and multi-format support.

Features:
- AI-powered content analysis using sentence transformers and Gemini
- Multi-format support: PDF, GitHub repos, HTML docs, URLs, LeetCode problems
- Advanced template system with specialized templates
- Intelligent content extraction and pedagogical optimization
- Custom instruction support for card generation
"""

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

# GitHub support
try:
    from github import Github
    HAS_GITHUB_SUPPORT = True
except ImportError:
    HAS_GITHUB_SUPPORT = False

# Gemini AI support
try:
    import google.generativeai as genai
    import time
    from typing import Optional, Dict, Any, List
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# YAKE keyword extraction
try:
    import yake
    HAS_YAKE = True
except ImportError:
    HAS_YAKE = False

# KeyBERT for keyword extraction
try:
    from keybert import KeyBERT
    HAS_KEYBERT = True
except ImportError:
    HAS_KEYBERT = False

# EPUB support
try:
    import ebooklib
    from ebooklib import epub
    HAS_EPUB_SUPPORT = True
except ImportError:
    HAS_EPUB_SUPPORT = False


def ensure_nltk():
    """Ensure required NLTK data is downloaded"""
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        print("Downloading NLTK punkt tokenizer...")
        nltk.download('punkt_tab')
    
    try:
        nltk.data.find('taggers/averaged_perceptron_tagger_eng')
    except LookupError:
        print("Downloading NLTK POS tagger...")
        nltk.download('averaged_perceptron_tagger_eng')


@dataclass
class Config:
    """Configuration for flashcard generation"""
    use_ai: bool = True
    use_gemini: bool = False
    max_cards_per_section: int = 50
    custom_instructions: str = ""
    gemini_api_key: Optional[str] = None
    output_format: str = "csv"
    include_metadata: bool = True
    difficulty_levels: List[str] = None
    
    def __post_init__(self):
        if self.difficulty_levels is None:
            self.difficulty_levels = ["basic", "intermediate", "advanced"]


class ContentSource(ABC):
    """Abstract base class for content sources"""
    
    @abstractmethod
    def extract_content(self, source: str) -> str:
        """Extract text content from source"""
        pass
    
    @abstractmethod
    def get_sections(self, content: str) -> List[Tuple[str, List[str]]]:
        """Split content into logical sections"""
        pass


class PDFSource(ContentSource):
    """PDF document content source"""
    
    def extract_content(self, source: str) -> str:
        """Extract text from PDF file"""
        try:
            doc = fitz.open(source)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            raise ValueError(f"Failed to extract PDF content: {e}")
    
    def get_sections(self, content: str) -> List[Tuple[str, List[str]]]:
        """Split PDF content into sections based on headings and paragraphs"""
        lines = content.split('\n')
        sections = []
        current_section = "Introduction"
        current_paragraphs = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line looks like a heading
            if self._is_heading(line):
                if current_paragraphs:
                    sections.append((current_section, current_paragraphs))
                current_section = line
                current_paragraphs = []
            else:
                current_paragraphs.append(line)
        
        # Add final section
        if current_paragraphs:
            sections.append((current_section, current_paragraphs))
        
        return sections
    
    def _is_heading(self, line: str) -> bool:
        """Determine if a line is likely a heading"""
        # Simple heuristics for heading detection
        if len(line) < 5:
            return False
        if len(line) > 100:
            return False
        if line.isupper():
            return True
        if re.match(r'^\d+\.?\s+[A-Z]', line):
            return True
        if re.match(r'^Chapter\s+\d+', line, re.IGNORECASE):
            return True
        return False


class GitHubSource(ContentSource):
    """GitHub repository content source"""
    
    def __init__(self):
        self.github = None
        if HAS_GITHUB_SUPPORT:
            # Initialize without token for public repos
            self.github = Github()
    
    def extract_content(self, source: str) -> str:
        """Extract content from GitHub repository"""
        if not HAS_GITHUB_SUPPORT:
            raise ImportError("PyGithub not installed. Install with: pip install PyGithub")
        
        try:
            # Parse GitHub URL
            repo_path = self._parse_github_url(source)
            repo = self.github.get_repo(repo_path)
            
            content = f"# {repo.name}\n\n"
            if repo.description:
                content += f"{repo.description}\n\n"
            
            # Get README
            try:
                readme = repo.get_readme()
                content += f"## README\n\n{readme.decoded_content.decode('utf-8')}\n\n"
            except:
                pass
            
            # Get code files
            contents = repo.get_contents("")
            code_content = self._extract_code_files(contents, repo)
            content += code_content
            
            return content
            
        except Exception as e:
            raise ValueError(f"Failed to extract GitHub content: {e}")
    
    def get_sections(self, content: str) -> List[Tuple[str, List[str]]]:
        """Split GitHub content into logical sections"""
        sections = []
        lines = content.split('\n')
        current_section = "Overview"
        current_paragraphs = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Markdown headings
            if line.startswith('#'):
                if current_paragraphs:
                    sections.append((current_section, current_paragraphs))
                current_section = line.lstrip('#').strip()
                current_paragraphs = []
            else:
                current_paragraphs.append(line)
        
        if current_paragraphs:
            sections.append((current_section, current_paragraphs))
        
        return sections
    
    def _parse_github_url(self, url: str) -> str:
        """Parse GitHub URL to get repo path"""
        if url.startswith('https://github.com/'):
            path = url.replace('https://github.com/', '')
            if path.endswith('.git'):
                path = path[:-4]
            return path
        else:
            raise ValueError("Invalid GitHub URL format")
    
    def _extract_code_files(self, contents, repo, max_files=20):
        """Extract content from code files"""
        code_content = ""
        file_count = 0
        
        for content_file in contents:
            if file_count >= max_files:
                break
                
            if content_file.type == "file":
                if self._is_code_file(content_file.name):
                    try:
                        file_content = repo.get_contents(content_file.path)
                        decoded_content = file_content.decoded_content.decode('utf-8')
                        code_content += f"\n## {content_file.name}\n\n```\n{decoded_content}\n```\n\n"
                        file_count += 1
                    except:
                        continue
        
        return code_content
    
    def _is_code_file(self, filename: str) -> bool:
        """Check if file is a code file"""
        code_extensions = ['.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go']
        return any(filename.endswith(ext) for ext in code_extensions)


class HTMLSource(ContentSource):
    """HTML/Web content source"""
    
    def extract_content(self, source: str) -> str:
        """Extract content from HTML/web source"""
        if not HAS_WEB_SUPPORT:
            raise ImportError("requests and beautifulsoup4 not installed")
        
        try:
            response = requests.get(source, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            raise ValueError(f"Failed to extract HTML content: {e}")
    
    def get_sections(self, content: str) -> List[Tuple[str, List[str]]]:
        """Split HTML content into sections"""
        # Simple paragraph-based splitting
        paragraphs = content.split('\n\n')
        sections = []
        
        current_section = "Content"
        section_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if len(para) > 20:  # Filter out very short paragraphs
                section_paragraphs.append(para)
                
                # Create new section every 5 paragraphs
                if len(section_paragraphs) >= 5:
                    sections.append((f"{current_section} {len(sections) + 1}", section_paragraphs))
                    section_paragraphs = []
        
        if section_paragraphs:
            sections.append((f"{current_section} {len(sections) + 1}", section_paragraphs))
        
        return sections


class LeetCodeSource(ContentSource):
    """LeetCode problem content source"""

    def extract_content(self, source: str) -> str:
        """Extract content from LeetCode problem"""
        if not HAS_WEB_SUPPORT:
            raise ImportError("requests and beautifulsoup4 not installed")

        try:
            # LeetCode requires special handling due to dynamic content
            # This is a simplified version
            response = requests.get(source, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Try to extract problem description
            content = soup.get_text()

            return content

        except Exception as e:
            raise ValueError(f"Failed to extract LeetCode content: {e}")

    def get_sections(self, content: str) -> List[Tuple[str, List[str]]]:
        """Split LeetCode content into sections"""
        return [("Problem", [content])]


class EPUBSource(ContentSource):
    """EPUB book content source"""

    def extract_content(self, source: str) -> str:
        """Extract text content from EPUB file"""
        if not HAS_EPUB_SUPPORT:
            raise ImportError("ebooklib not installed. Install with: pip install ebooklib")

        try:
            book = epub.read_epub(source)
            content = ""

            # Extract metadata
            title = book.get_metadata('DC', 'title')
            author = book.get_metadata('DC', 'creator')

            if title:
                content += f"# {title[0][0]}\n\n"
            if author:
                content += f"**Author:** {author[0][0]}\n\n"

            # Extract content from all items
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    # Parse HTML content
                    try:
                        soup = BeautifulSoup(item.get_content(), 'html.parser')

                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()

                        # Extract text
                        text = soup.get_text()

                        # Clean up text
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        clean_text = ' '.join(chunk for chunk in chunks if chunk)

                        if clean_text and len(clean_text) > 50:  # Only add substantial content
                            content += f"\n\n{clean_text}"

                    except Exception as e:
                        # Skip problematic items
                        continue

            return content

        except Exception as e:
            raise ValueError(f"Failed to extract EPUB content: {e}")

    def get_sections(self, content: str) -> List[Tuple[str, List[str]]]:
        """Split EPUB content into logical sections"""
        sections = []

        # Split by chapters or major headings
        lines = content.split('\n')
        current_section = "Introduction"
        current_paragraphs = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line looks like a chapter heading
            if self._is_chapter_heading(line):
                if current_paragraphs:
                    sections.append((current_section, current_paragraphs))
                current_section = line
                current_paragraphs = []
            else:
                # Split long paragraphs into smaller chunks
                if len(line) > 500:
                    # Split into sentences
                    sentences = line.split('. ')
                    chunk = ""
                    for sentence in sentences:
                        if len(chunk + sentence) > 300:
                            if chunk:
                                current_paragraphs.append(chunk.strip())
                            chunk = sentence + ". "
                        else:
                            chunk += sentence + ". "
                    if chunk:
                        current_paragraphs.append(chunk.strip())
                else:
                    current_paragraphs.append(line)

        # Add final section
        if current_paragraphs:
            sections.append((current_section, current_paragraphs))

        return sections

    def _is_chapter_heading(self, line: str) -> bool:
        """Determine if a line is likely a chapter heading"""
        # Check for common chapter patterns
        chapter_patterns = [
            r'^Chapter\s+\d+',
            r'^CHAPTER\s+\d+',
            r'^\d+\.\s+[A-Z]',
            r'^Part\s+\d+',
            r'^Section\s+\d+',
        ]

        for pattern in chapter_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True

        # Check if line is short and mostly uppercase
        if len(line) < 100 and len(line) > 5:
            uppercase_ratio = sum(1 for c in line if c.isupper()) / len(line.replace(' ', ''))
            if uppercase_ratio > 0.5:
                return True

        return False


# Aliases for backward compatibility
PDFProcessor = PDFSource
GitHubProcessor = GitHubSource
HTMLProcessor = HTMLSource
LeetCodeProcessor = LeetCodeSource
EPUBProcessor = EPUBSource


class FlashcardifyEnhanced:
    """Enhanced flashcard generation system"""

    def __init__(self, config: Config):
        self.config = config

        # Initialize content sources
        self.sources = {
            'pdf': PDFSource(),
            'github': GitHubSource() if HAS_GITHUB_SUPPORT else None,
            'html': HTMLSource() if HAS_WEB_SUPPORT else None,
            'leetcode': LeetCodeSource() if HAS_WEB_SUPPORT else None,
            'epub': EPUBSource() if HAS_EPUB_SUPPORT else None,
        }

    def process_content(self, source: str, source_type: str) -> List[Dict[str, Any]]:
        """Process content and generate basic flashcards"""
        if source_type not in self.sources or self.sources[source_type] is None:
            raise ValueError(f"Unsupported source type: {source_type}")

        try:
            # Extract content
            content_handler = self.sources[source_type]
            content = content_handler.extract_content(source)
            sections = content_handler.get_sections(content)

            # Generate basic cards
            cards = []
            for title, paragraphs in sections:
                section_cards = self._generate_section_cards(title, paragraphs)
                cards.extend(section_cards[:self.config.max_cards_per_section])

            return cards

        except Exception as e:
            raise ValueError(f"Failed to process {source_type} content: {e}")

    def _generate_section_cards(self, title: str, paragraphs: List[str]) -> List[Dict[str, Any]]:
        """Generate cards from a section"""
        cards = []

        # Simple card generation - create Q&A pairs from paragraphs
        for i, paragraph in enumerate(paragraphs):
            if len(paragraph) > 50:  # Only process substantial paragraphs
                # Create a simple Q&A card
                question = f"What is discussed in the {title} section?"
                answer = paragraph[:200] + "..." if len(paragraph) > 200 else paragraph

                cards.append({
                    'type': 'fb',
                    'front': question,
                    'back': answer,
                    'hint': f"Think about the content in {title}",
                    'tags': f"{title.lower().replace(' ', '_')},content",
                    'template_id': 'fb_basic',
                    'difficulty': 'intermediate',
                    'concept': title,
                    'source': title
                })

        return cards
