"""
Service layer for the Smart Knowledge Repository.

Provides business logic and orchestration for knowledge management,
chat interactions, and scraping operations.
"""

from .knowledge_service import KnowledgeService
from .chat_service import ChatService
from .scraping_service import ScrapingService

__all__ = ['KnowledgeService', 'ChatService', 'ScrapingService']
