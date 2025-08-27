"""
Web scraping module for the Smart Knowledge Repository.

This module provides functionality for scraping profile pages and discovering content
from various websites with intelligent extraction capabilities.
"""

from .profile_scraper import ProfileScraper
from .content_discovery import ContentDiscovery

__all__ = ['ProfileScraper', 'ContentDiscovery']
