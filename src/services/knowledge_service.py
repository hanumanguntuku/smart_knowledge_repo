"""
Knowledge service for managing knowledge base operations.

Provides high-level operations for knowledge storage, retrieval,
and management with intelligent search capabilities.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import from our modules
from database.models import Profile, KnowledgeEntry, SearchQuery, db_manager
from database.repository import ProfileRepository, KnowledgeRepository, SearchQueryRepository
from search.vector_search import SemanticSearchEngine, SearchResult
from search.indexing import ContentIndexer, EmbeddingGenerator, SearchIndexManager


class KnowledgeService:
    """High-level service for knowledge management operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.db_manager = db_manager
        self.embedding_generator = EmbeddingGenerator()
        self.content_indexer = ContentIndexer(self.embedding_generator)
        self.search_engine = SemanticSearchEngine()
        self.index_manager = SearchIndexManager(self.content_indexer)
        
        # Initialize database
        self._initialize_database()
        
        # Load existing indexes
        self._load_search_indexes()
    
    def _initialize_database(self):
        """Initialize database and load existing data."""
        try:
            self.db_manager.create_tables()
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
    
    def _load_search_indexes(self):
        """Load existing search indexes from database."""
        try:
            # Load and index existing profiles and knowledge entries
            with self.db_manager.get_session() as session:
                profile_repo = ProfileRepository(session)
                knowledge_repo = KnowledgeRepository(session)
                
                # Index existing profiles
                profiles = profile_repo.get_all(limit=1000)
                for profile in profiles:
                    self.index_manager.add_content(profile.to_dict())
                
                # Index existing knowledge entries
                entries = knowledge_repo.get_all(limit=1000)
                for entry in entries:
                    self.index_manager.add_content(entry.to_dict())
                
                self.logger.info(f"Loaded {len(profiles)} profiles and {len(entries)} knowledge entries into search index")
                
        except Exception as e:
            self.logger.error(f"Error loading search indexes: {e}")
    
    def add_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new profile to the knowledge base."""
        try:
            with self.db_manager.get_session() as session:
                profile_repo = ProfileRepository(session)
                
                # Check if profile already exists
                existing_profile = None
                if profile_data.get('source_url'):
                    existing_profile = profile_repo.get_by_url(profile_data['source_url'])
                
                if existing_profile:
                    # Update existing profile
                    updated_profile = profile_repo.update(existing_profile.id, profile_data)
                    result = updated_profile.to_dict()
                    
                    # Update search index
                    self.index_manager.update_content(existing_profile.id, result)
                    
                    self.logger.info(f"Updated existing profile: {profile_data.get('name')}")
                    return result
                else:
                    # Create new profile
                    new_profile = profile_repo.create(profile_data)
                    result = new_profile.to_dict()
                    
                    # Add to search index
                    self.index_manager.add_content(result)
                    
                    self.logger.info(f"Added new profile: {profile_data.get('name')}")
                    return result
                    
        except Exception as e:
            self.logger.error(f"Error adding profile: {e}")
            raise
    
    def add_knowledge_entry(self, knowledge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new knowledge entry to the knowledge base."""
        try:
            with self.db_manager.get_session() as session:
                knowledge_repo = KnowledgeRepository(session)
                
                # Create new knowledge entry
                new_entry = knowledge_repo.create(knowledge_data)
                result = new_entry.to_dict()
                
                # Add to search index
                self.index_manager.add_content(result)
                
                self.logger.info(f"Added new knowledge entry: {knowledge_data.get('title')}")
                return result
                
        except Exception as e:
            self.logger.error(f"Error adding knowledge entry: {e}")
            raise
    
    def search_knowledge(self, 
                        query: str, 
                        search_type: str = 'hybrid',
                        content_types: Optional[List[str]] = None,
                        limit: int = 10) -> List[Dict[str, Any]]:
        """Search the knowledge base."""
        try:
            start_time = datetime.now()
            
            # Generate query embedding for semantic search
            query_embedding = None
            if search_type in ['semantic', 'hybrid']:
                query_embedding = self.embedding_generator.generate_embedding(query)
            
            # Perform search
            search_results = self.search_engine.search(
                query=query,
                query_embedding=query_embedding,
                search_type=search_type,
                top_k=limit,
                min_score=0.1
            )
            
            # Filter by content types if specified
            if content_types:
                search_results = [
                    result for result in search_results 
                    if result.content_type in content_types
                ]
            
            # Log search query for analytics
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            self._log_search_query(query, search_type, len(search_results), response_time)
            
            # Convert to dictionaries
            results = []
            for result in search_results:
                results.append({
                    'id': result.content_id,
                    'title': result.title,
                    'content': result.content,
                    'score': result.score,
                    'content_type': result.content_type,
                    'entry_metadata': result.entry_metadata
                })
            
            self.logger.info(f"Search query '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching knowledge: {e}")
            return []
    
    def get_profile_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a profile by name."""
        try:
            with self.db_manager.get_session() as session:
                profile_repo = ProfileRepository(session)
                profile = profile_repo.get_by_name(name)
                return profile.to_dict() if profile else None
                
        except Exception as e:
            self.logger.error(f"Error getting profile by name: {e}")
            return None
    
    def get_all_profiles(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all profiles with pagination."""
        try:
            with self.db_manager.get_session() as session:
                profile_repo = ProfileRepository(session)
                profiles = profile_repo.get_all(limit=limit, offset=offset)
                return [profile.to_dict() for profile in profiles]
                
        except Exception as e:
            self.logger.error(f"Error getting all profiles: {e}")
            return []
    
    def get_departments(self) -> List[str]:
        """Get list of all departments."""
        try:
            with self.db_manager.get_session() as session:
                profile_repo = ProfileRepository(session)
                return profile_repo.get_departments()
                
        except Exception as e:
            self.logger.error(f"Error getting departments: {e}")
            return []
    
    def get_roles(self) -> List[str]:
        """Get list of all roles."""
        try:
            with self.db_manager.get_session() as session:
                profile_repo = ProfileRepository(session)
                return profile_repo.get_roles()
                
        except Exception as e:
            self.logger.error(f"Error getting roles: {e}")
            return []
    
    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile from the knowledge base."""
        try:
            with self.db_manager.get_session() as session:
                profile_repo = ProfileRepository(session)
                success = profile_repo.delete(profile_id)
                
                if success:
                    # Remove from search index
                    self.index_manager.remove_content(profile_id)
                    self.logger.info(f"Deleted profile: {profile_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Error deleting profile: {e}")
            return False
    
    def rebuild_search_index(self) -> bool:
        """Rebuild the entire search index."""
        try:
            # Clear existing index
            self.index_manager.clear_index()
            
            # Reload all data
            self._load_search_indexes()
            
            self.logger.info("Search index rebuilt successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error rebuilding search index: {e}")
            return False
    
    def get_knowledge_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        try:
            with self.db_manager.get_session() as session:
                profile_repo = ProfileRepository(session)
                knowledge_repo = KnowledgeRepository(session)
                query_repo = SearchQueryRepository(session)
                
                stats = {
                    'profiles': {
                        'total': profile_repo.count(),
                    },
                    'knowledge_entries': {
                        'total': knowledge_repo.count(),
                    },
                    'search': {
                        'index_stats': self.index_manager.get_status(),
                    }
                }
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting knowledge statistics: {e}")
            return {}
    
    def _log_search_query(self, query: str, search_type: str, results_count: int, response_time_ms: float):
        """Log search query for analytics."""
        try:
            with self.db_manager.get_session() as session:
                query_repo = SearchQueryRepository(session)
                query_repo.log_query({
                    'query_text': query,
                    'query_type': search_type,
                    'results_count': results_count,
                    'response_time_ms': response_time_ms
                })
                
        except Exception as e:
            self.logger.error(f"Error logging search query: {e}")
    
    def check_scope(self, query: str) -> bool:
        """Check if a query is within the scope of the knowledge base."""
        scope_keywords = [
            'who', 'what', 'where', 'when', 'how',
            'ceo', 'cto', 'director', 'manager', 'lead', 'head',
            'team', 'staff', 'employee', 'member', 'person',
            'role', 'position', 'department', 'contact',
            'email', 'phone', 'experience', 'background',
            'bio', 'biography', 'profile'
        ]
        
        query_lower = query.lower()
        
        # Check if any scope keywords are present
        for keyword in scope_keywords:
            if keyword in query_lower:
                return True
        
        # Additional checks for organization-specific terms
        org_terms = ['company', 'organization', 'business', 'firm', 'corporation']
        if any(term in query_lower for term in org_terms):
            return True
        
        return False
