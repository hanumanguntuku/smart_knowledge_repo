"""
User interface module for the Smart Knowledge Repository.

Provides Streamlit-based interfaces for chat, browsing, and administration.
"""

from .chat_interface import ChatInterface
from .browse_interface import BrowseInterface
from .admin_interface import AdminInterface

__all__ = ['ChatInterface', 'BrowseInterface', 'AdminInterface']
