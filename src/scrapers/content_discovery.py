"""
Content discovery module for intelligent website crawling and content identification.

Provides functionality for discovering new content sources and identifying
relevant pages for scraping.
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Set, Optional
from urllib.parse import urljoin, urlparse
import re
import logging
from dataclasses import dataclass

@dataclass
class ContentSource:
    """Data class for content source information."""
    url: str
    title: str
    content_type: str  # 'profile', 'team', 'about', 'news', etc.
    priority: int = 1  # 1-5, higher is more important
    last_updated: Optional[str] = None

class ContentDiscovery:
    """Intelligent content discovery and crawling system."""
    
    def __init__(self):
        self.session = None
        self.logger = logging.getLogger(__name__)
        self.visited_urls: Set[str] = set()
        
        # Content type patterns
        self.content_patterns = {
            'profile': [
                r'/team/', r'/staff/', r'/leadership/', r'/employees/',
                r'/people/', r'/profiles/', r'/members/', r'/about/'
            ],
            'news': [
                r'/news/', r'/blog/', r'/articles/', r'/press/',
                r'/updates/', r'/announcements/'
            ],
            'services': [
                r'/services/', r'/products/', r'/solutions/',
                r'/offerings/', r'/capabilities/'
            ],
            'contact': [
                r'/contact/', r'/reach/', r'/connect/',
                r'/get-in-touch/', r'/office/'
            ]
        }

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def discover_content_sources(self, 
                                     base_url: str, 
                                     max_depth: int = 2,
                                     max_pages: int = 50) -> List[ContentSource]:
        """
        Discover content sources from a website.
        
        Args:
            base_url: Starting URL for discovery
            max_depth: Maximum crawling depth
            max_pages: Maximum number of pages to crawl
            
        Returns:
            List of discovered content sources
        """
        self.visited_urls.clear()
        content_sources = []
        
        urls_to_visit = [(base_url, 0)]  # (url, depth)
        
        while urls_to_visit and len(self.visited_urls) < max_pages:
            current_url, depth = urls_to_visit.pop(0)
            
            if current_url in self.visited_urls or depth > max_depth:
                continue
                
            self.visited_urls.add(current_url)
            
            try:
                content_source = await self._analyze_page(current_url)
                if content_source:
                    content_sources.append(content_source)
                
                # Discover new URLs if we haven't reached max depth
                if depth < max_depth:
                    new_urls = await self._extract_links(current_url, base_url)
                    for url in new_urls:
                        if url not in self.visited_urls:
                            urls_to_visit.append((url, depth + 1))
                            
            except Exception as e:
                self.logger.error(f"Error analyzing page {current_url}: {e}")
                continue
        
        return self._prioritize_sources(content_sources)

    async def _analyze_page(self, url: str) -> Optional[ContentSource]:
        """Analyze a single page to determine its content type and value."""
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    return None
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract title
                title_elem = soup.find('title')
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                # Determine content type
                content_type = self._classify_content_type(url, title, soup)
                
                # Calculate priority
                priority = self._calculate_priority(url, content_type, soup)
                
                return ContentSource(
                    url=url,
                    title=title,
                    content_type=content_type,
                    priority=priority
                )
                
        except Exception as e:
            self.logger.error(f"Error analyzing page {url}: {e}")
            return None

    def _classify_content_type(self, url: str, title: str, soup: BeautifulSoup) -> str:
        """Classify the content type of a page."""
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Check URL patterns
        for content_type, patterns in self.content_patterns.items():
            if any(re.search(pattern, url_lower) for pattern in patterns):
                return content_type
        
        # Check title patterns
        title_keywords = {
            'profile': ['team', 'staff', 'leadership', 'people', 'employees'],
            'news': ['news', 'blog', 'articles', 'press', 'updates'],
            'services': ['services', 'products', 'solutions', 'offerings'],
            'contact': ['contact', 'reach', 'connect', 'office']
        }
        
        for content_type, keywords in title_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                return content_type
        
        # Check page content
        text_content = soup.get_text().lower()
        
        # Profile page indicators
        if any(word in text_content for word in ['biography', 'experience', 'education', 'skills']):
            return 'profile'
        
        # Default classification
        return 'general'

    def _calculate_priority(self, url: str, content_type: str, soup: BeautifulSoup) -> int:
        """Calculate priority score for a content source."""
        priority = 1
        
        # Base priority by content type
        type_priorities = {
            'profile': 5,
            'team': 5,
            'news': 3,
            'services': 2,
            'contact': 4,
            'general': 1
        }
        priority = type_priorities.get(content_type, 1)
        
        # Adjust based on URL depth (fewer slashes = higher priority)
        url_depth = url.count('/') - 2  # Subtract protocol slashes
        if url_depth <= 1:
            priority += 1
        
        # Adjust based on content indicators
        text_content = soup.get_text().lower()
        
        # High-value keywords
        high_value_keywords = ['ceo', 'founder', 'director', 'manager', 'lead']
        if any(keyword in text_content for keyword in high_value_keywords):
            priority += 1
        
        # Ensure priority is within bounds
        return min(max(priority, 1), 5)

    async def _extract_links(self, url: str, base_url: str) -> List[str]:
        """Extract and normalize links from a page."""
        try:
            async with self.session.get(url, timeout=10) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                links = []
                base_domain = urlparse(base_url).netloc
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(url, href)
                    parsed_url = urlparse(absolute_url)
                    
                    # Only include links from the same domain
                    if parsed_url.netloc == base_domain:
                        # Remove fragments and query parameters for cleaner URLs
                        clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                        links.append(clean_url)
                
                return list(set(links))  # Remove duplicates
                
        except Exception as e:
            self.logger.error(f"Error extracting links from {url}: {e}")
            return []

    def _prioritize_sources(self, sources: List[ContentSource]) -> List[ContentSource]:
        """Sort content sources by priority."""
        return sorted(sources, key=lambda x: (-x.priority, x.url))

    async def find_similar_sites(self, reference_url: str) -> List[str]:
        """
        Find similar websites based on the reference URL structure.
        
        Args:
            reference_url: URL to use as reference for finding similar sites
            
        Returns:
            List of potentially similar website URLs
        """
        # This is a placeholder for more advanced functionality
        # In a real implementation, you might use search APIs or
        # domain similarity algorithms
        
        parsed_url = urlparse(reference_url)
        domain_parts = parsed_url.netloc.split('.')
        
        # Simple heuristic: look for common variations
        similar_domains = []
        
        if len(domain_parts) >= 2:
            base_name = domain_parts[-2]  # e.g., 'company' from 'company.com'
            
            # Common variations
            variations = [
                f"{base_name}.org",
                f"{base_name}.net",
                f"{base_name}.io",
                f"www.{base_name}.com",
                f"{base_name}-inc.com",
                f"{base_name}corp.com"
            ]
            
            similar_domains.extend(variations)
        
        return similar_domains

    def get_content_statistics(self, sources: List[ContentSource]) -> Dict[str, int]:
        """Get statistics about discovered content sources."""
        stats = {}
        
        # Count by content type
        type_counts = {}
        for source in sources:
            type_counts[source.content_type] = type_counts.get(source.content_type, 0) + 1
        
        stats['by_type'] = type_counts
        
        # Count by priority
        priority_counts = {}
        for source in sources:
            priority_counts[source.priority] = priority_counts.get(source.priority, 0) + 1
        
        stats['by_priority'] = priority_counts
        stats['total_sources'] = len(sources)
        
        return stats
