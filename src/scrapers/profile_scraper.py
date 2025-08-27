"""
Profile scraper for extracting structured information from profile pages.

Handles automatic profile page discovery, multi-template content extraction,
contact information parsing, and duplicate detection.
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import re
import logging

@dataclass
class ProfileData:
    """Data class for storing extracted profile information."""
    name: str
    role: Optional[str] = None
    bio: Optional[str] = None
    contact: Optional[Dict[str, str]] = None
    photo_url: Optional[str] = None
    url: str = ""
    department: Optional[str] = None

class ProfileScraper:
    """Intelligent web scraper for profile extraction."""
    
    def __init__(self):
        self.session = None
        self.logger = logging.getLogger(__name__)
        
        # Common selectors for different website layouts
        self.selectors = {
            'name': [
                'h1', 'h2', '.name', '.profile-name', '[data-name]',
                '.employee-name', '.person-name', '.staff-name'
            ],
            'role': [
                '.title', '.position', '.role', '.job-title',
                '.employee-title', '.designation', '[data-role]'
            ],
            'bio': [
                '.bio', '.biography', '.description', '.about',
                '.profile-description', '.employee-bio', 'p'
            ],
            'photo': [
                '.photo img', '.profile-image img', '.headshot img',
                '.employee-photo img', '.avatar img', 'img'
            ],
            'contact': [
                '.email', '.phone', '.contact', '[href^="mailto:"]',
                '[href^="tel:"]', '.social-links a'
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

    async def discover_profiles(self, base_url: str) -> List[str]:
        """
        Intelligent page discovery for profile pages.
        
        Args:
            base_url: Base URL to search for profile pages
            
        Returns:
            List of discovered profile URLs
        """
        try:
            async with self.session.get(base_url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                profile_urls = []
                
                # Look for common profile page patterns
                profile_patterns = [
                    r'/team/', r'/staff/', r'/leadership/', r'/employees/',
                    r'/people/', r'/about/', r'/profiles/', r'/members/'
                ]
                
                # Find all links
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link['href']
                    # Check if link matches profile patterns
                    if any(re.search(pattern, href, re.IGNORECASE) for pattern in profile_patterns):
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            href = base_url.rstrip('/') + href
                        elif not href.startswith('http'):
                            continue
                        
                        profile_urls.append(href)
                
                # Remove duplicates and return
                return list(set(profile_urls))
                
        except Exception as e:
            self.logger.error(f"Error discovering profiles from {base_url}: {e}")
            return []

    async def extract_profile(self, url: str) -> Optional[ProfileData]:
        """
        Extract structured profile information from a URL.
        
        Args:
            url: URL of the profile page to extract
            
        Returns:
            ProfileData object or None if extraction fails
        """
        try:
            async with self.session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract name
                name = self._extract_by_selectors(soup, self.selectors['name'])
                if not name:
                    return None
                
                # Extract other fields
                role = self._extract_by_selectors(soup, self.selectors['role'])
                bio = self._extract_by_selectors(soup, self.selectors['bio'])
                photo_url = self._extract_photo(soup, url)
                contact = self._extract_contact(soup)
                
                return ProfileData(
                    name=name,
                    role=role,
                    bio=bio,
                    contact=contact,
                    photo_url=photo_url,
                    url=url
                )
                
        except Exception as e:
            self.logger.error(f"Error extracting profile from {url}: {e}")
            return None

    def _extract_by_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract text using multiple CSS selectors."""
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 2:  # Avoid empty or too short text
                    return text
        return None

    def _extract_photo(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract profile photo URL."""
        for selector in self.selectors['photo']:
            img_elements = soup.select(selector)
            for img in img_elements:
                src = img.get('src') or img.get('data-src')
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith('/'):
                        src = base_url.split('/')[0] + '//' + base_url.split('//')[1].split('/')[0] + src
                    elif not src.startswith('http'):
                        continue
                    return src
        return None

    def _extract_contact(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract contact information."""
        contact = {}
        
        # Extract email
        email_links = soup.find_all('a', href=re.compile(r'^mailto:'))
        if email_links:
            contact['email'] = email_links[0]['href'].replace('mailto:', '')
        
        # Extract phone
        phone_links = soup.find_all('a', href=re.compile(r'^tel:'))
        if phone_links:
            contact['phone'] = phone_links[0]['href'].replace('tel:', '')
        
        # Extract social links
        social_patterns = {
            'linkedin': r'linkedin\.com',
            'twitter': r'twitter\.com|x\.com',
            'github': r'github\.com'
        }
        
        for platform, pattern in social_patterns.items():
            social_links = soup.find_all('a', href=re.compile(pattern, re.IGNORECASE))
            if social_links:
                contact[platform] = social_links[0]['href']
        
        return contact

    async def scrape_multiple_profiles(self, urls: List[str]) -> List[ProfileData]:
        """
        Scrape multiple profile URLs concurrently.
        
        Args:
            urls: List of profile URLs to scrape
            
        Returns:
            List of ProfileData objects
        """
        tasks = [self.extract_profile(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        profiles = []
        for result in results:
            if isinstance(result, ProfileData):
                profiles.append(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Error in concurrent scraping: {result}")
        
        return profiles
