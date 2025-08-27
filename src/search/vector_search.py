"""
Vector search implementation for semantic similarity and intelligent retrieval.

Provides functionality for vector-based search using embeddings and
cosine similarity for finding relevant content.
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import json
import logging
from dataclasses import dataclass
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import os

@dataclass
class SearchResult:
    """Data class for search results."""
    content_id: int
    title: str
    content: str
    score: float
    content_type: str
    metadata: Dict[str, Any] = None

class VectorSearch:
    """Vector-based search engine using embeddings."""
    
    def __init__(self, embedding_dimension: int = 384):
        self.embedding_dimension = embedding_dimension
        self.logger = logging.getLogger(__name__)
        self.embeddings: Dict[int, np.ndarray] = {}
        self.content_metadata: Dict[int, Dict[str, Any]] = {}
        
    def add_embedding(self, content_id: int, embedding: List[float], metadata: Dict[str, Any]):
        """Add an embedding vector for content."""
        if len(embedding) != self.embedding_dimension:
            raise ValueError(f"Embedding dimension mismatch. Expected {self.embedding_dimension}, got {len(embedding)}")
        
        self.embeddings[content_id] = np.array(embedding)
        self.content_metadata[content_id] = metadata
        
    def search(self, query_embedding: List[float], top_k: int = 10, min_score: float = 0.1) -> List[SearchResult]:
        """Search for similar content using vector similarity."""
        if not self.embeddings:
            return []
        
        query_vector = np.array(query_embedding).reshape(1, -1)
        
        results = []
        for content_id, embedding in self.embeddings.items():
            # Calculate cosine similarity
            similarity = cosine_similarity(query_vector, embedding.reshape(1, -1))[0][0]
            
            if similarity >= min_score:
                metadata = self.content_metadata.get(content_id, {})
                result = SearchResult(
                    content_id=content_id,
                    title=metadata.get('title', ''),
                    content=metadata.get('content', ''),
                    score=float(similarity),
                    content_type=metadata.get('content_type', ''),
                    metadata=metadata
                )
                results.append(result)
        
        # Sort by score (descending) and return top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def remove_embedding(self, content_id: int):
        """Remove an embedding."""
        if content_id in self.embeddings:
            del self.embeddings[content_id]
        if content_id in self.content_metadata:
            del self.content_metadata[content_id]
    
    def save_index(self, filepath: str):
        """Save the vector index to disk."""
        index_data = {
            'embeddings': {k: v.tolist() for k, v in self.embeddings.items()},
            'metadata': self.content_metadata,
            'dimension': self.embedding_dimension
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(index_data, f)
    
    def load_index(self, filepath: str):
        """Load the vector index from disk."""
        try:
            with open(filepath, 'r') as f:
                index_data = json.load(f)
            
            self.embedding_dimension = index_data['dimension']
            self.embeddings = {
                int(k): np.array(v) for k, v in index_data['embeddings'].items()
            }
            self.content_metadata = {
                int(k): v for k, v in index_data['metadata'].items()
            }
            
            self.logger.info(f"Loaded {len(self.embeddings)} embeddings from {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error loading index from {filepath}: {e}")
            raise

class KeywordSearch:
    """Traditional keyword-based search using TF-IDF."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = None
        self.content_metadata: Dict[int, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
    
    def build_index(self, documents: List[Dict[str, Any]]):
        """Build TF-IDF index from documents."""
        texts = []
        self.content_metadata = {}
        
        for doc in documents:
            content_id = doc['id']
            text = f"{doc.get('title', '')} {doc.get('content', '')}"
            texts.append(text)
            self.content_metadata[content_id] = doc
        
        if texts:
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
            self.logger.info(f"Built TF-IDF index for {len(texts)} documents")
    
    def search(self, query: str, top_k: int = 10, min_score: float = 0.1) -> List[SearchResult]:
        """Search using keyword matching."""
        if self.tfidf_matrix is None:
            return []
        
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        results = []
        for idx, score in enumerate(similarities):
            if score >= min_score:
                # Get content_id from metadata index
                content_ids = list(self.content_metadata.keys())
                if idx < len(content_ids):
                    content_id = content_ids[idx]
                    metadata = self.content_metadata[content_id]
                    
                    result = SearchResult(
                        content_id=content_id,
                        title=metadata.get('title', ''),
                        content=metadata.get('content', ''),
                        score=float(score),
                        content_type=metadata.get('content_type', ''),
                        metadata=metadata
                    )
                    results.append(result)
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def save_index(self, filepath: str):
        """Save the keyword index to disk."""
        index_data = {
            'vectorizer': self.vectorizer,
            'tfidf_matrix': self.tfidf_matrix,
            'metadata': self.content_metadata
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(index_data, f)
    
    def load_index(self, filepath: str):
        """Load the keyword index from disk."""
        try:
            with open(filepath, 'rb') as f:
                index_data = pickle.load(f)
            
            self.vectorizer = index_data['vectorizer']
            self.tfidf_matrix = index_data['tfidf_matrix']
            self.content_metadata = index_data['metadata']
            
            self.logger.info(f"Loaded keyword index from {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error loading keyword index from {filepath}: {e}")
            raise

class SemanticSearchEngine:
    """Combined semantic and keyword search engine."""
    
    def __init__(self, embedding_dimension: int = 384):
        self.vector_search = VectorSearch(embedding_dimension)
        self.keyword_search = KeywordSearch()
        self.logger = logging.getLogger(__name__)
    
    def index_content(self, content_list: List[Dict[str, Any]], embeddings: Dict[int, List[float]]):
        """Index content for both vector and keyword search."""
        # Build keyword index
        self.keyword_search.build_index(content_list)
        
        # Add vector embeddings
        for content in content_list:
            content_id = content['id']
            if content_id in embeddings:
                self.vector_search.add_embedding(
                    content_id, 
                    embeddings[content_id], 
                    content
                )
    
    def search(self, 
               query: str, 
               query_embedding: Optional[List[float]] = None,
               search_type: str = 'hybrid',
               top_k: int = 10,
               min_score: float = 0.1) -> List[SearchResult]:
        """
        Perform search using different strategies.
        
        Args:
            query: Text query
            query_embedding: Vector embedding of query (optional)
            search_type: 'vector', 'keyword', or 'hybrid'
            top_k: Number of results to return
            min_score: Minimum similarity score
        """
        if search_type == 'vector' and query_embedding:
            return self.vector_search.search(query_embedding, top_k, min_score)
        
        elif search_type == 'keyword':
            return self.keyword_search.search(query, top_k, min_score)
        
        elif search_type == 'hybrid':
            # Combine vector and keyword search results
            vector_results = []
            keyword_results = []
            
            if query_embedding:
                vector_results = self.vector_search.search(query_embedding, top_k * 2, min_score)
            
            keyword_results = self.keyword_search.search(query, top_k * 2, min_score)
            
            # Merge and re-rank results
            return self._merge_results(vector_results, keyword_results, top_k)
        
        else:
            # Default to keyword search
            return self.keyword_search.search(query, top_k, min_score)
    
    def _merge_results(self, 
                      vector_results: List[SearchResult], 
                      keyword_results: List[SearchResult], 
                      top_k: int) -> List[SearchResult]:
        """Merge and re-rank vector and keyword search results."""
        # Create a dictionary to combine scores for the same content
        combined_scores = {}
        
        # Weight vector search results
        for result in vector_results:
            combined_scores[result.content_id] = {
                'result': result,
                'vector_score': result.score,
                'keyword_score': 0.0
            }
        
        # Add keyword search results
        for result in keyword_results:
            if result.content_id in combined_scores:
                combined_scores[result.content_id]['keyword_score'] = result.score
            else:
                combined_scores[result.content_id] = {
                    'result': result,
                    'vector_score': 0.0,
                    'keyword_score': result.score
                }
        
        # Calculate combined scores (weighted average)
        vector_weight = 0.6
        keyword_weight = 0.4
        
        final_results = []
        for content_id, scores in combined_scores.items():
            combined_score = (
                scores['vector_score'] * vector_weight + 
                scores['keyword_score'] * keyword_weight
            )
            
            result = scores['result']
            result.score = combined_score
            final_results.append(result)
        
        # Sort by combined score and return top_k
        final_results.sort(key=lambda x: x.score, reverse=True)
        return final_results[:top_k]
    
    def save_indexes(self, base_path: str):
        """Save both search indexes."""
        vector_path = os.path.join(base_path, 'vector_index.json')
        keyword_path = os.path.join(base_path, 'keyword_index.pkl')
        
        self.vector_search.save_index(vector_path)
        self.keyword_search.save_index(keyword_path)
    
    def load_indexes(self, base_path: str):
        """Load both search indexes."""
        vector_path = os.path.join(base_path, 'vector_index.json')
        keyword_path = os.path.join(base_path, 'keyword_index.pkl')
        
        if os.path.exists(vector_path):
            self.vector_search.load_index(vector_path)
        
        if os.path.exists(keyword_path):
            self.keyword_search.load_index(keyword_path)
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get statistics about the search indexes."""
        return {
            'vector_embeddings': len(self.vector_search.embeddings),
            'keyword_documents': len(self.keyword_search.content_metadata),
            'embedding_dimension': self.vector_search.embedding_dimension
        }
