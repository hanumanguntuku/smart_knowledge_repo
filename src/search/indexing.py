"""
Content indexing and embedding generation for the search system.

Provides functionality for generating embeddings from text content
and maintaining search indexes.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import re
import hashlib
from datetime import datetime

# Placeholder for actual embedding models
# In a real implementation, you would use sentence-transformers or OpenAI embeddings

class EmbeddingGenerator:
    """Generate embeddings for text content."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)
        self.embedding_dimension = 384  # Typical for MiniLM
        
        # In a real implementation, you would load the actual model here
        # self.model = SentenceTransformer(model_name)
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        This is a placeholder implementation that returns a simple hash-based vector.
        In production, you would use a real embedding model.
        """
        # Preprocess text
        clean_text = self._preprocess_text(text)
        
        # Placeholder: Create a simple hash-based embedding
        # In production, replace with: return self.model.encode(clean_text).tolist()
        return self._create_hash_embedding(clean_text)
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for embedding generation."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?]', '', text)
        
        # Convert to lowercase
        text = text.lower().strip()
        
        return text
    
    def _create_hash_embedding(self, text: str) -> List[float]:
        """
        Create a simple hash-based embedding as a placeholder.
        
        In production, this would be replaced with a real embedding model.
        """
        # Create a hash of the text
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Convert hash to a vector of floats
        embedding = []
        for i in range(0, len(text_hash), 2):
            # Convert hex pairs to float values between -1 and 1
            hex_val = int(text_hash[i:i+2], 16)
            float_val = (hex_val / 255.0) * 2 - 1
            embedding.append(float_val)
        
        # Pad or truncate to desired dimension
        while len(embedding) < self.embedding_dimension:
            embedding.extend(embedding[:min(len(embedding), self.embedding_dimension - len(embedding))])
        
        return embedding[:self.embedding_dimension]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model."""
        return {
            'model_name': self.model_name,
            'embedding_dimension': self.embedding_dimension,
            'model_type': 'placeholder'  # Would be 'sentence-transformer' in production
        }

class ContentIndexer:
    """Index content and maintain search indexes."""
    
    def __init__(self, embedding_generator: EmbeddingGenerator):
        self.embedding_generator = embedding_generator
        self.logger = logging.getLogger(__name__)
        self.indexed_content: Dict[int, Dict[str, Any]] = {}
    
    def index_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Index a profile for search."""
        content_id = profile_data['id']
        
        # Combine text fields for embedding
        text_content = self._combine_profile_text(profile_data)
        
        # Generate embedding
        embedding = self.embedding_generator.generate_embedding(text_content)
        
        # Extract keywords
        keywords = self._extract_keywords(text_content)
        
        # Create index entry
        index_entry = {
            'content_id': content_id,
            'content_type': 'profile',
            'title': profile_data.get('name', ''),
            'content': text_content,
            'embedding': embedding,
            'keywords': keywords,
            'metadata': {
                'role': profile_data.get('role'),
                'department': profile_data.get('department'),
                'source_url': profile_data.get('source_url')
            },
            'indexed_at': datetime.utcnow().isoformat()
        }
        
        self.indexed_content[content_id] = index_entry
        return index_entry
    
    def index_knowledge_entry(self, knowledge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Index a knowledge entry for search."""
        content_id = knowledge_data['id']
        
        # Combine title and content
        text_content = f"{knowledge_data.get('title', '')} {knowledge_data.get('content', '')}"
        
        # Generate embedding
        embedding = self.embedding_generator.generate_embedding(text_content)
        
        # Extract keywords
        keywords = self._extract_keywords(text_content)
        
        # Create index entry
        index_entry = {
            'content_id': content_id,
            'content_type': knowledge_data.get('content_type', 'knowledge'),
            'title': knowledge_data.get('title', ''),
            'content': knowledge_data.get('content', ''),
            'embedding': embedding,
            'keywords': keywords,
            'metadata': knowledge_data.get('metadata', {}),
            'indexed_at': datetime.utcnow().isoformat()
        }
        
        self.indexed_content[content_id] = index_entry
        return index_entry
    
    def batch_index(self, content_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Index multiple content items in batch."""
        indexed_entries = []
        
        for content_item in content_list:
            if content_item.get('type') == 'profile' or 'name' in content_item:
                entry = self.index_profile(content_item)
            else:
                entry = self.index_knowledge_entry(content_item)
            
            indexed_entries.append(entry)
        
        return indexed_entries
    
    def update_index(self, content_id: int, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing index entry."""
        if content_id in self.indexed_content:
            # Re-index the updated content
            if updated_data.get('type') == 'profile' or 'name' in updated_data:
                return self.index_profile(updated_data)
            else:
                return self.index_knowledge_entry(updated_data)
        return None
    
    def remove_from_index(self, content_id: int) -> bool:
        """Remove content from index."""
        if content_id in self.indexed_content:
            del self.indexed_content[content_id]
            return True
        return False
    
    def _combine_profile_text(self, profile_data: Dict[str, Any]) -> str:
        """Combine profile fields into searchable text."""
        text_parts = []
        
        # Add name (most important)
        if profile_data.get('name'):
            text_parts.append(profile_data['name'])
        
        # Add role
        if profile_data.get('role'):
            text_parts.append(profile_data['role'])
        
        # Add department
        if profile_data.get('department'):
            text_parts.append(profile_data['department'])
        
        # Add bio
        if profile_data.get('bio'):
            text_parts.append(profile_data['bio'])
        
        # Add contact information keywords
        contact = profile_data.get('contact', {})
        if isinstance(contact, dict):
            for key, value in contact.items():
                if value:
                    text_parts.append(f"{key}: {value}")
        
        return ' '.join(text_parts)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for keyword-based search."""
        if not text:
            return []
        
        # Simple keyword extraction
        # In production, you might use NLTK, spaCy, or other NLP libraries
        
        # Convert to lowercase and split
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'within',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
            'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # Filter out stop words and short words
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords[:20]  # Limit to top 20 keywords
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the content index."""
        if not self.indexed_content:
            return {
                'total_indexed': 0,
                'by_type': {},
                'avg_keywords_per_item': 0
            }
        
        # Count by content type
        type_counts = {}
        total_keywords = 0
        
        for entry in self.indexed_content.values():
            content_type = entry.get('content_type', 'unknown')
            type_counts[content_type] = type_counts.get(content_type, 0) + 1
            total_keywords += len(entry.get('keywords', []))
        
        return {
            'total_indexed': len(self.indexed_content),
            'by_type': type_counts,
            'avg_keywords_per_item': total_keywords / len(self.indexed_content) if self.indexed_content else 0,
            'embedding_dimension': self.embedding_generator.embedding_dimension
        }
    
    def export_embeddings(self) -> Dict[int, List[float]]:
        """Export all embeddings for use with vector search."""
        return {
            content_id: entry['embedding']
            for content_id, entry in self.indexed_content.items()
            if 'embedding' in entry
        }
    
    def export_content_metadata(self) -> List[Dict[str, Any]]:
        """Export content metadata for search engines."""
        content_list = []
        
        for content_id, entry in self.indexed_content.items():
            content_list.append({
                'id': content_id,
                'title': entry.get('title', ''),
                'content': entry.get('content', ''),
                'content_type': entry.get('content_type', ''),
                'keywords': entry.get('keywords', []),
                'metadata': entry.get('metadata', {})
            })
        
        return content_list

class SearchIndexManager:
    """Manage search indexes and keep them synchronized."""
    
    def __init__(self, content_indexer: ContentIndexer):
        self.content_indexer = content_indexer
        self.logger = logging.getLogger(__name__)
        self.rebuild_threshold = 100  # Rebuild index after this many changes
        self.changes_since_rebuild = 0
    
    def add_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add new content to the index."""
        if content_data.get('type') == 'profile' or 'name' in content_data:
            result = self.content_indexer.index_profile(content_data)
        else:
            result = self.content_indexer.index_knowledge_entry(content_data)
        
        self.changes_since_rebuild += 1
        self._check_rebuild_needed()
        
        return result
    
    def update_content(self, content_id: int, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing content in the index."""
        result = self.content_indexer.update_index(content_id, updated_data)
        
        if result:
            self.changes_since_rebuild += 1
            self._check_rebuild_needed()
        
        return result
    
    def remove_content(self, content_id: int) -> bool:
        """Remove content from the index."""
        result = self.content_indexer.remove_from_index(content_id)
        
        if result:
            self.changes_since_rebuild += 1
            self._check_rebuild_needed()
        
        return result
    
    def _check_rebuild_needed(self):
        """Check if index rebuild is needed."""
        if self.changes_since_rebuild >= self.rebuild_threshold:
            self.logger.info("Threshold reached, rebuilding search indexes")
            self.rebuild_indexes()
    
    def rebuild_indexes(self):
        """Rebuild all search indexes."""
        # This would trigger a rebuild of vector and keyword search indexes
        # Implementation would depend on the specific search engine used
        self.changes_since_rebuild = 0
        self.logger.info("Search indexes rebuilt")
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the search index manager."""
        stats = self.content_indexer.get_index_stats()
        stats.update({
            'changes_since_rebuild': self.changes_since_rebuild,
            'rebuild_threshold': self.rebuild_threshold
        })
        return stats
