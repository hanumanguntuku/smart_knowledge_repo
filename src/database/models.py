"""
Database models for the Smart Knowledge Repository.

Defines SQLAlchemy models for storing profile information, knowledge entries,
and search indexes with full-text search capabilities.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()

class Profile(Base):
    """Model for storing profile information."""
    __tablename__ = 'profiles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    role = Column(String(255), index=True)
    department = Column(String(255), index=True)
    bio = Column(Text)
    contact = Column(JSON)  # Store contact info as JSON
    photo_url = Column(String(500))
    source_url = Column(String(500), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to knowledge entries
    knowledge_entries = relationship("KnowledgeEntry", back_populates="profile")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'department': self.department,
            'bio': self.bio,
            'contact': self.contact,
            'photo_url': self.photo_url,
            'source_url': self.source_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_scraper_data(cls, scraper_data) -> 'Profile':
        """Create Profile instance from scraper data."""
        return cls(
            name=scraper_data.name,
            role=scraper_data.role,
            bio=scraper_data.bio,
            contact=scraper_data.contact or {},
            photo_url=scraper_data.photo_url,
            source_url=scraper_data.url,
            department=scraper_data.department
        )

class KnowledgeEntry(Base):
    """Model for storing knowledge base entries."""
    __tablename__ = 'knowledge_entries'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), index=True)  # 'profile', 'document', 'faq', etc.
    source_url = Column(String(500))
    entry_metadata = Column(JSON)  # Additional structured data
    profile_id = Column(Integer, ForeignKey('profiles.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to profile
    profile = relationship("Profile", back_populates="knowledge_entries")
    
    # Relationship to search indexes
    search_indexes = relationship("SearchIndex", back_populates="knowledge_entry")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert knowledge entry to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'content_type': self.content_type,
            'source_url': self.source_url,
            'entry_metadata': self.entry_metadata,
            'profile_id': self.profile_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SearchIndex(Base):
    """Model for vector embeddings and search indexing."""
    __tablename__ = 'search_indexes'
    
    id = Column(Integer, primary_key=True)
    knowledge_entry_id = Column(Integer, ForeignKey('knowledge_entries.id'), nullable=False)
    embedding_vector = Column(JSON)  # Store embeddings as JSON array
    embedding_model = Column(String(100))  # Model used for embeddings
    keywords = Column(Text)  # Extracted keywords for keyword search
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to knowledge entry
    knowledge_entry = relationship("KnowledgeEntry", back_populates="search_indexes")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert search index to dictionary."""
        return {
            'id': self.id,
            'knowledge_entry_id': self.knowledge_entry_id,
            'embedding_vector': self.embedding_vector,
            'embedding_model': self.embedding_model,
            'keywords': self.keywords,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SearchQuery(Base):
    """Model for tracking search queries and analytics."""
    __tablename__ = 'search_queries'
    
    id = Column(Integer, primary_key=True)
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50))  # 'keyword', 'semantic', 'hybrid'
    results_count = Column(Integer)
    user_feedback = Column(String(20))  # 'helpful', 'not_helpful', None
    response_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert search query to dictionary."""
        return {
            'id': self.id,
            'query_text': self.query_text,
            'query_type': self.query_type,
            'results_count': self.results_count,
            'user_feedback': self.user_feedback,
            'response_time_ms': self.response_time_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class DatabaseManager:
    """Database connection and session management."""
    
    def __init__(self, database_url: str = "sqlite:///data/profiles.db"):
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()
    
    def drop_tables(self):
        """Drop all database tables (use with caution)."""
        Base.metadata.drop_all(bind=self.engine)

# Global database manager instance
db_manager = DatabaseManager()

def get_db_session():
    """Get a database session for dependency injection."""
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()
