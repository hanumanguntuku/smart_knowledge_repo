"""
Database module for the Smart Knowledge Repository.

Provides data models, repository patterns, and migration support for
managing profile and knowledge data.
"""

from .models import Profile, KnowledgeEntry, SearchIndex
from .repository import ProfileRepository, KnowledgeRepository
from .migrations import DatabaseMigrations

__all__ = [
    'Profile', 'KnowledgeEntry', 'SearchIndex',
    'ProfileRepository', 'KnowledgeRepository', 
    'DatabaseMigrations'
]
