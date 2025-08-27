"""
Repository pattern implementation for database operations.

Provides clean interfaces for data access operations including
CRUD operations, search, and analytics.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from .models import Profile, KnowledgeEntry, SearchIndex, SearchQuery
import logging

class BaseRepository:
    """Base repository with common operations."""
    
    def __init__(self, session: Session):
        self.session = session
        self.logger = logging.getLogger(self.__class__.__name__)

class ProfileRepository(BaseRepository):
    """Repository for Profile operations."""
    
    def create(self, profile_data: Dict[str, Any]) -> Profile:
        """Create a new profile."""
        profile = Profile(**profile_data)
        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)
        return profile
    
    def get_by_id(self, profile_id: int) -> Optional[Profile]:
        """Get profile by ID."""
        return self.session.query(Profile).filter(Profile.id == profile_id).first()
    
    def get_by_name(self, name: str) -> Optional[Profile]:
        """Get profile by name."""
        return self.session.query(Profile).filter(Profile.name.ilike(f"%{name}%")).first()
    
    def get_by_url(self, url: str) -> Optional[Profile]:
        """Get profile by source URL."""
        return self.session.query(Profile).filter(Profile.source_url == url).first()
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Profile]:
        """Get all profiles with pagination."""
        return self.session.query(Profile).offset(offset).limit(limit).all()
    
    def search_by_role(self, role: str) -> List[Profile]:
        """Search profiles by role."""
        return self.session.query(Profile).filter(
            Profile.role.ilike(f"%{role}%")
        ).all()
    
    def search_by_department(self, department: str) -> List[Profile]:
        """Search profiles by department."""
        return self.session.query(Profile).filter(
            Profile.department.ilike(f"%{department}%")
        ).all()
    
    def search_by_keyword(self, keyword: str) -> List[Profile]:
        """Search profiles by keyword in name, role, or bio."""
        keyword_filter = f"%{keyword}%"
        return self.session.query(Profile).filter(
            or_(
                Profile.name.ilike(keyword_filter),
                Profile.role.ilike(keyword_filter),
                Profile.bio.ilike(keyword_filter)
            )
        ).all()
    
    def update(self, profile_id: int, update_data: Dict[str, Any]) -> Optional[Profile]:
        """Update a profile."""
        profile = self.get_by_id(profile_id)
        if profile:
            for key, value in update_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            self.session.commit()
            self.session.refresh(profile)
        return profile
    
    def delete(self, profile_id: int) -> bool:
        """Delete a profile."""
        profile = self.get_by_id(profile_id)
        if profile:
            self.session.delete(profile)
            self.session.commit()
            return True
        return False
    
    def get_departments(self) -> List[str]:
        """Get list of unique departments."""
        result = self.session.query(Profile.department).distinct().all()
        return [dept[0] for dept in result if dept[0]]
    
    def get_roles(self) -> List[str]:
        """Get list of unique roles."""
        result = self.session.query(Profile.role).distinct().all()
        return [role[0] for role in result if role[0]]
    
    def count(self) -> int:
        """Get total count of profiles."""
        return self.session.query(Profile).count()

class KnowledgeRepository(BaseRepository):
    """Repository for KnowledgeEntry operations."""
    
    def create(self, knowledge_data: Dict[str, Any]) -> KnowledgeEntry:
        """Create a new knowledge entry."""
        entry = KnowledgeEntry(**knowledge_data)
        self.session.add(entry)
        self.session.commit()
        self.session.refresh(entry)
        return entry
    
    def get_by_id(self, entry_id: int) -> Optional[KnowledgeEntry]:
        """Get knowledge entry by ID."""
        return self.session.query(KnowledgeEntry).filter(
            KnowledgeEntry.id == entry_id
        ).first()
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[KnowledgeEntry]:
        """Get all knowledge entries with pagination."""
        return self.session.query(KnowledgeEntry).offset(offset).limit(limit).all()
    
    def get_by_type(self, content_type: str) -> List[KnowledgeEntry]:
        """Get knowledge entries by content type."""
        return self.session.query(KnowledgeEntry).filter(
            KnowledgeEntry.content_type == content_type
        ).all()
    
    def get_by_profile(self, profile_id: int) -> List[KnowledgeEntry]:
        """Get knowledge entries for a specific profile."""
        return self.session.query(KnowledgeEntry).filter(
            KnowledgeEntry.profile_id == profile_id
        ).all()
    
    def search_by_keyword(self, keyword: str) -> List[KnowledgeEntry]:
        """Search knowledge entries by keyword."""
        keyword_filter = f"%{keyword}%"
        return self.session.query(KnowledgeEntry).filter(
            or_(
                KnowledgeEntry.title.ilike(keyword_filter),
                KnowledgeEntry.content.ilike(keyword_filter)
            )
        ).all()
    
    def full_text_search(self, query: str) -> List[KnowledgeEntry]:
        """Perform full-text search on knowledge entries."""
        # This is a simplified implementation
        # In production, you'd use proper FTS5 with SQLite or other full-text search
        keywords = query.split()
        conditions = []
        
        for keyword in keywords:
            keyword_filter = f"%{keyword}%"
            conditions.append(
                or_(
                    KnowledgeEntry.title.ilike(keyword_filter),
                    KnowledgeEntry.content.ilike(keyword_filter)
                )
            )
        
        if conditions:
            return self.session.query(KnowledgeEntry).filter(and_(*conditions)).all()
        return []
    
    def update(self, entry_id: int, update_data: Dict[str, Any]) -> Optional[KnowledgeEntry]:
        """Update a knowledge entry."""
        entry = self.get_by_id(entry_id)
        if entry:
            for key, value in update_data.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
            self.session.commit()
            self.session.refresh(entry)
        return entry
    
    def delete(self, entry_id: int) -> bool:
        """Delete a knowledge entry."""
        entry = self.get_by_id(entry_id)
        if entry:
            self.session.delete(entry)
            self.session.commit()
            return True
        return False
    
    def get_content_types(self) -> List[str]:
        """Get list of unique content types."""
        result = self.session.query(KnowledgeEntry.content_type).distinct().all()
        return [ct[0] for ct in result if ct[0]]
    
    def count(self) -> int:
        """Get total count of knowledge entries."""
        return self.session.query(KnowledgeEntry).count()

class SearchIndexRepository(BaseRepository):
    """Repository for SearchIndex operations."""
    
    def create(self, index_data: Dict[str, Any]) -> SearchIndex:
        """Create a new search index."""
        index = SearchIndex(**index_data)
        self.session.add(index)
        self.session.commit()
        self.session.refresh(index)
        return index
    
    def get_by_knowledge_entry(self, entry_id: int) -> Optional[SearchIndex]:
        """Get search index for a knowledge entry."""
        return self.session.query(SearchIndex).filter(
            SearchIndex.knowledge_entry_id == entry_id
        ).first()
    
    def update_embedding(self, entry_id: int, embedding: List[float], model: str) -> Optional[SearchIndex]:
        """Update or create embedding for a knowledge entry."""
        index = self.get_by_knowledge_entry(entry_id)
        
        if index:
            index.embedding_vector = embedding
            index.embedding_model = model
        else:
            index = SearchIndex(
                knowledge_entry_id=entry_id,
                embedding_vector=embedding,
                embedding_model=model
            )
            self.session.add(index)
        
        self.session.commit()
        self.session.refresh(index)
        return index
    
    def get_all_embeddings(self) -> List[SearchIndex]:
        """Get all search indexes with embeddings."""
        return self.session.query(SearchIndex).filter(
            SearchIndex.embedding_vector.isnot(None)
        ).all()
    
    def delete_by_knowledge_entry(self, entry_id: int) -> bool:
        """Delete search index for a knowledge entry."""
        index = self.get_by_knowledge_entry(entry_id)
        if index:
            self.session.delete(index)
            self.session.commit()
            return True
        return False

class SearchQueryRepository(BaseRepository):
    """Repository for SearchQuery analytics."""
    
    def log_query(self, query_data: Dict[str, Any]) -> SearchQuery:
        """Log a search query for analytics."""
        query = SearchQuery(**query_data)
        self.session.add(query)
        self.session.commit()
        self.session.refresh(query)
        return query
    
    def get_popular_queries(self, limit: int = 10) -> List[tuple]:
        """Get most popular search queries."""
        return self.session.query(
            SearchQuery.query_text, 
            func.count(SearchQuery.id).label('count')
        ).group_by(SearchQuery.query_text).order_by(
            func.count(SearchQuery.id).desc()
        ).limit(limit).all()
    
    def get_query_analytics(self) -> Dict[str, Any]:
        """Get search query analytics."""
        total_queries = self.session.query(SearchQuery).count()
        avg_response_time = self.session.query(
            func.avg(SearchQuery.response_time_ms)
        ).scalar() or 0
        
        feedback_stats = self.session.query(
            SearchQuery.user_feedback,
            func.count(SearchQuery.id)
        ).group_by(SearchQuery.user_feedback).all()
        
        return {
            'total_queries': total_queries,
            'avg_response_time_ms': float(avg_response_time),
            'feedback_distribution': dict(feedback_stats)
        }
