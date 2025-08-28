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
        
        # Site-specific selectors for better accuracy
        self.site_selectors = {
            'amzur.com': {
                'name': ['h1', 'h4 a', '.wp-block-heading'],
                'role': ['.role-title', 'h1 + p', 'h4 + p', '.job-title'],
                'bio': ['.entry-content p', '.profile-content p', 'main p'],
                'photo': ['img[src*="leadership"]', '.wp-image', 'img'],
                'contact': ['a[href^="mailto:"]', 'a[href^="tel:"]', 'a[href*="linkedin"]'],
                'profile_links': ['a[href*="/leadership/"]']
            }
        }
        
        # Common selectors for different website layouts (fallback)
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
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with self.session.get(base_url, headers=headers) as response:
                if response.status != 200:
                    self.logger.error(f"HTTP {response.status} for {base_url}")
                    return []
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                profile_urls = []
                
                # Site-specific discovery for Amzur.com
                if 'amzur.com' in base_url:
                    profile_urls = await self._discover_amzur_profiles(soup, base_url)
                else:
                    # Generic discovery for other sites
                    profile_urls = await self._discover_generic_profiles(soup, base_url)
                
                # Remove duplicates and return
                unique_urls = list(set(profile_urls))
                self.logger.info(f"Discovered {len(unique_urls)} profile URLs from {base_url}")
                return unique_urls
                
        except Exception as e:
            self.logger.error(f"Error discovering profiles from {base_url}: {e}")
            return []
    
    async def _discover_amzur_profiles(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Discover profiles specifically from Amzur.com leadership page."""
        profile_urls = []
        
        # Look for leadership profile links
        leadership_links = soup.find_all('a', href=re.compile(r'/leadership/[^/]+/?$'))
        
        for link in leadership_links:
            href = link.get('href')
            if href and href != '/leadership/' and '/leadership-team' not in href:
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    full_url = 'https://amzur.com' + href
                else:
                    full_url = href
                profile_urls.append(full_url)
        
        return profile_urls
    
    async def _discover_generic_profiles(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Generic profile discovery for other websites."""
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
        
        return profile_urls

    async def extract_profile(self, url: str) -> Optional[ProfileData]:
        """
        Extract structured profile information from a URL.
        
        Args:
            url: URL of the profile page to extract
            
        Returns:
            ProfileData object or None if extraction fails
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    self.logger.error(f"HTTP {response.status} for {url}")
                    return None
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Use site-specific extraction if available
                if 'amzur.com' in url:
                    return await self._extract_amzur_profile(soup, url)
                else:
                    return await self._extract_generic_profile(soup, url)
                
        except Exception as e:
            self.logger.error(f"Error extracting profile from {url}: {e}")
            return None
    
    async def _extract_amzur_profile(self, soup: BeautifulSoup, url: str) -> Optional[ProfileData]:
        """Extract profile specifically from Amzur.com profile pages."""
        try:
            # Extract name from h1 or breadcrumb
            name = None
            name_element = soup.find('h1')
            if name_element:
                name = name_element.get_text(strip=True)
            
            # Extract role from the subtitle or breadcrumb
            role = None
            
            # Look for role in various locations
            # Method 1: Look for role after the name in breadcrumb
            breadcrumb = soup.find(string=re.compile(r'President|CEO|Director|Head|Chief|Manager'))
            if breadcrumb:
                role = breadcrumb.strip()
            
            # Method 2: Look for role in meta description or nearby text
            if not role:
                role_element = soup.find('p', string=re.compile(r'President|CEO|Director|Head|Chief|Manager'))
                if role_element:
                    role_text = role_element.get_text(strip=True)
                    # Extract just the role part
                    role_match = re.search(r'(President[^.]*|CEO[^.]*|Director[^.]*|Head[^.]*|Chief[^.]*|Manager[^.]*)', role_text)
                    if role_match:
                        role = role_match.group(1).strip()
            
            # Extract bio from main content
            bio = None
            # Look for bio in entry content
            bio_element = soup.find('div', class_='entry-content')
            if bio_element:
                # Get all paragraphs and combine them
                paragraphs = bio_element.find_all('p')
                bio_parts = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:  # Avoid short fragments
                        bio_parts.append(text)
                if bio_parts:
                    bio = ' '.join(bio_parts)
            
            # Extract photo URL
            photo_url = None
            # Look for profile image
            img_elements = soup.find_all('img')
            for img in img_elements:
                src = img.get('src') or img.get('data-src')
                if src and ('leadership' in src.lower() or 'profile' in src.lower() or img.get('alt', '').lower() == name.lower() if name else False):
                    if src.startswith('/'):
                        photo_url = 'https://amzur.com' + src
                    else:
                        photo_url = src
                    break
            
            # Extract contact information
            contact = {}
            
            # Look for LinkedIn
            linkedin_link = soup.find('a', href=re.compile(r'linkedin\.com'))
            if linkedin_link:
                contact['linkedin'] = linkedin_link['href']
            
            # Look for email (if available)
            email_link = soup.find('a', href=re.compile(r'^mailto:'))
            if email_link:
                contact['email'] = email_link['href'].replace('mailto:', '')
            
            # Extract department from role
            department = None
            if role:
                if any(word in role.lower() for word in ['ceo', 'president', 'chief']):
                    department = 'Executive Leadership'
                elif 'director' in role.lower():
                    department = 'Directors'
                elif 'head' in role.lower():
                    department = 'Department Heads'
                else:
                    department = 'Leadership Team'
            
            if not name:
                self.logger.warning(f"Could not extract name from {url}")
                return None
            
            return ProfileData(
                name=name,
                role=role,
                bio=bio,
                contact=contact if contact else None,
                photo_url=photo_url,
                url=url,
                department=department
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting Amzur profile from {url}: {e}")
            return None
    
    async def _extract_generic_profile(self, soup: BeautifulSoup, url: str) -> Optional[ProfileData]:
        """Extract profile using generic patterns."""
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

    async def scrape_amzur_leadership_team(self) -> List[ProfileData]:
        """
        Scrape Amzur.com leadership team page and extract profile information.
        
        Returns:
            List of ProfileData objects with basic information
        """
        leadership_url = "https://amzur.com/leadership-team/"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with self.session.get(leadership_url, headers=headers) as response:
                if response.status != 200:
                    self.logger.error(f"HTTP {response.status} for {leadership_url}")
                    return []
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                profiles = []
                
                # Find all leadership profile links and basic info from the main page
                leadership_links = soup.find_all('a', href=re.compile(r'/leadership/[^/]+/?$'))
                
                for link in leadership_links:
                    try:
                        href = link.get('href')
                        if not href or href == '/leadership/' or '/leadership-team' in href:
                            continue
                        
                        # Convert relative URL to absolute
                        if href.startswith('/'):
                            profile_url = 'https://amzur.com' + href
                        else:
                            profile_url = href
                        
                        # Extract basic info from the link and surrounding context
                        name = link.get_text(strip=True)
                        
                        # Try to find role by looking at surrounding text
                        role = None
                        parent = link.parent
                        if parent:
                            # Look for role in next siblings or parent text
                            next_elem = link.find_next_sibling(text=True)
                            if next_elem:
                                role_text = next_elem.strip()
                                if role_text and len(role_text) > 3:
                                    role = role_text
                            
                            # If not found, look in parent's text content
                            if not role:
                                parent_text = parent.get_text(strip=True)
                                # Extract role that comes after name
                                if name in parent_text:
                                    role_part = parent_text.split(name)[-1].strip()
                                    if role_part and len(role_part) > 3:
                                        role = role_part
                        
                        if name:
                            # Determine department based on role
                            department = None
                            if role:
                                if any(word in role.lower() for word in ['ceo', 'president', 'chief']):
                                    department = 'Executive Leadership'
                                elif 'director' in role.lower():
                                    department = 'Directors'
                                elif 'head' in role.lower():
                                    department = 'Department Heads'
                                else:
                                    department = 'Leadership Team'
                            
                            profile_data = ProfileData(
                                name=name,
                                role=role,
                                bio=None,  # Will be filled when extracting individual pages
                                contact=None,
                                photo_url=None,
                                url=profile_url,
                                department=department
                            )
                            profiles.append(profile_data)
                            
                    except Exception as e:
                        self.logger.error(f"Error processing leadership link: {e}")
                        continue
                
                self.logger.info(f"Extracted {len(profiles)} leadership profiles from main page")
                return profiles
                
        except Exception as e:
            self.logger.error(f"Error scraping Amzur leadership team: {e}")
            return []
    
    async def enhance_profiles_with_details(self, basic_profiles: List[ProfileData]) -> List[ProfileData]:
        """
        Enhance basic profile data by scraping individual profile pages.
        
        Args:
            basic_profiles: List of ProfileData with basic info
            
        Returns:
            List of ProfileData with enhanced details
        """
        enhanced_profiles = []
        
        for profile in basic_profiles:
            try:
                # Extract detailed information from individual profile page
                detailed_profile = await self.extract_profile(profile.url)
                
                if detailed_profile:
                    # Merge basic info with detailed info
                    enhanced_profile = ProfileData(
                        name=detailed_profile.name or profile.name,
                        role=detailed_profile.role or profile.role,
                        bio=detailed_profile.bio,
                        contact=detailed_profile.contact,
                        photo_url=detailed_profile.photo_url,
                        url=profile.url,
                        department=detailed_profile.department or profile.department
                    )
                    enhanced_profiles.append(enhanced_profile)
                else:
                    # Keep basic profile if detailed extraction fails
                    enhanced_profiles.append(profile)
                
                # Add delay to be respectful to the server
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error enhancing profile {profile.name}: {e}")
                enhanced_profiles.append(profile)  # Keep basic profile
        
        return enhanced_profiles
