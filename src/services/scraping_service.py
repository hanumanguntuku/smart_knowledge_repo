"""
Scraping service for coordinating web scraping operations.

Provides high-level orchestration of scraping tasks with
scheduling, error handling, and data processing.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import yaml
import os

# Import from our modules
from scrapers.profile_scraper import ProfileScraper
from scrapers.content_discovery import ContentDiscovery

class ScrapingJob:
    """Represents a scraping job with metadata."""
    
    def __init__(self, job_id: str, target_url: str, job_type: str = "profile"):
        self.job_id = job_id
        self.target_url = target_url
        self.job_type = job_type
        self.status = "pending"  # pending, running, completed, failed
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.results: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'job_id': self.job_id,
            'target_url': self.target_url,
            'job_type': self.job_type,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'results_count': len(self.results),
            'metadata': self.metadata
        }

class ScrapingService:
    """High-level service for coordinating scraping operations."""
    
    def __init__(self, knowledge_service):
        self.knowledge_service = knowledge_service
        self.logger = logging.getLogger(__name__)
        self.jobs: Dict[str, ScrapingJob] = {}
        self.config = self._load_config()
        
        # Rate limiting
        self.rate_limit_delay = self.config.get('rate_limit_delay', 1.0)  # seconds
        self.max_concurrent_jobs = self.config.get('max_concurrent_jobs', 3)
        
        # Retry settings
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 5.0)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load scraping configuration from YAML file."""
        config_path = "config/scraping_targets.yaml"
        default_config = {
            'rate_limit_delay': 1.0,
            'max_concurrent_jobs': 3,
            'max_retries': 3,
            'retry_delay': 5.0,
            'targets': []
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    return {**default_config, **config}
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
        
        return default_config
    
    def create_scraping_job(self, target_url: str, job_type: str = "profile") -> str:
        """Create a new scraping job."""
        job_id = f"{job_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.jobs)}"
        job = ScrapingJob(job_id, target_url, job_type)
        self.jobs[job_id] = job
        
        self.logger.info(f"Created scraping job: {job_id} for {target_url}")
        return job_id
    
    async def run_profile_scraping_job(self, job_id: str) -> Dict[str, Any]:
        """Run a profile scraping job."""
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        job.status = "running"
        job.started_at = datetime.now()
        
        try:
            async with ProfileScraper() as scraper:
                # Discover profile URLs
                self.logger.info(f"Discovering profiles from {job.target_url}")
                profile_urls = await scraper.discover_profiles(job.target_url)
                
                if not profile_urls:
                    self.logger.warning(f"No profile URLs found at {job.target_url}")
                    profile_urls = [job.target_url]  # Try the URL itself
                
                job.metadata['discovered_urls'] = len(profile_urls)
                
                # Scrape profiles with rate limiting
                scraped_profiles = []
                for i, url in enumerate(profile_urls):
                    try:
                        # Rate limiting
                        if i > 0:
                            await asyncio.sleep(self.rate_limit_delay)
                        
                        profile_data = await scraper.extract_profile(url)
                        if profile_data:
                            # Convert to dictionary and add to knowledge base
                            profile_dict = {
                                'name': profile_data.name,
                                'role': profile_data.role,
                                'bio': profile_data.bio,
                                'contact': profile_data.contact or {},
                                'photo_url': profile_data.photo_url,
                                'source_url': profile_data.url,
                                'department': profile_data.department
                            }
                            
                            # Add to knowledge base
                            saved_profile = self.knowledge_service.add_profile(profile_dict)
                            scraped_profiles.append(saved_profile)
                            
                            self.logger.info(f"Scraped and saved profile: {profile_data.name}")
                        
                    except Exception as e:
                        self.logger.error(f"Error scraping profile from {url}: {e}")
                        continue
                
                job.results = scraped_profiles
                job.status = "completed"
                job.completed_at = datetime.now()
                
                self.logger.info(f"Completed scraping job {job_id}: {len(scraped_profiles)} profiles")
                
                return {
                    'job_id': job_id,
                    'status': 'completed',
                    'profiles_scraped': len(scraped_profiles),
                    'profiles': scraped_profiles
                }
                
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now()
            
            self.logger.error(f"Scraping job {job_id} failed: {e}")
            
            return {
                'job_id': job_id,
                'status': 'failed',
                'error': str(e)
            }
    
    async def run_content_discovery_job(self, job_id: str) -> Dict[str, Any]:
        """Run a content discovery job."""
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        job.status = "running"
        job.started_at = datetime.now()
        
        try:
            async with ContentDiscovery() as discovery:
                # Discover content sources
                self.logger.info(f"Discovering content from {job.target_url}")
                content_sources = await discovery.discover_content_sources(
                    job.target_url,
                    max_depth=2,
                    max_pages=50
                )
                
                # Filter for high-priority sources
                profile_sources = [
                    source for source in content_sources 
                    if source.content_type in ['profile', 'team'] and source.priority >= 3
                ]
                
                job.metadata['total_sources'] = len(content_sources)
                job.metadata['profile_sources'] = len(profile_sources)
                
                # Create scraping jobs for profile sources
                profile_jobs = []
                for source in profile_sources[:10]:  # Limit to top 10
                    profile_job_id = self.create_scraping_job(source.url, "profile")
                    profile_jobs.append(profile_job_id)
                
                job.results = [source.__dict__ for source in content_sources]
                job.status = "completed"
                job.completed_at = datetime.now()
                
                self.logger.info(f"Completed discovery job {job_id}: {len(content_sources)} sources found")
                
                return {
                    'job_id': job_id,
                    'status': 'completed',
                    'sources_found': len(content_sources),
                    'profile_sources': len(profile_sources),
                    'created_profile_jobs': profile_jobs,
                    'sources': content_sources
                }
                
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now()
            
            self.logger.error(f"Discovery job {job_id} failed: {e}")
            
            return {
                'job_id': job_id,
                'status': 'failed',
                'error': str(e)
            }
    
    async def run_job(self, job_id: str) -> Dict[str, Any]:
        """Run a scraping job based on its type."""
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        if job.job_type == "profile":
            return await self.run_profile_scraping_job(job_id)
        elif job.job_type == "discovery":
            return await self.run_content_discovery_job(job_id)
        else:
            raise ValueError(f"Unknown job type: {job.job_type}")
    
    async def run_batch_scraping(self, target_urls: List[str]) -> List[Dict[str, Any]]:
        """Run scraping for multiple URLs concurrently."""
        # Create jobs for all URLs
        job_ids = []
        for url in target_urls:
            job_id = self.create_scraping_job(url, "profile")
            job_ids.append(job_id)
        
        # Run jobs with concurrency limit
        semaphore = asyncio.Semaphore(self.max_concurrent_jobs)
        
        async def run_limited_job(job_id):
            async with semaphore:
                return await self.run_job(job_id)
        
        # Execute all jobs
        results = await asyncio.gather(
            *[run_limited_job(job_id) for job_id in job_ids],
            return_exceptions=True
        )
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'job_id': job_ids[i],
                    'status': 'failed',
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def scrape_amzur_leadership(self) -> Dict[str, Any]:
        """
        Specialized method to scrape Amzur.com leadership team.
        
        Returns:
            Dictionary with scraping results and metadata
        """
        job_id = self.create_scraping_job("https://amzur.com/leadership-team/", "amzur_leadership")
        job = self.jobs[job_id]
        
        job.status = "running"
        job.started_at = datetime.now()
        
        try:
            async with ProfileScraper() as scraper:
                # Step 1: Get basic profiles from leadership page
                self.logger.info("Extracting basic profiles from Amzur leadership page...")
                basic_profiles = await scraper.scrape_amzur_leadership_team()
                
                if not basic_profiles:
                    job.status = "failed"
                    job.error_message = "No profiles found on leadership page"
                    return self.get_job_status(job_id)
                
                job.metadata['basic_profiles_found'] = len(basic_profiles)
                self.logger.info(f"Found {len(basic_profiles)} basic profiles")
                
                # Step 2: Enhance profiles with detailed information
                self.logger.info("Enhancing profiles with detailed information...")
                enhanced_profiles = await scraper.enhance_profiles_with_details(basic_profiles)
                
                job.metadata['enhanced_profiles'] = len(enhanced_profiles)
                
                # Step 3: Save to knowledge base
                saved_profiles = []
                for profile_data in enhanced_profiles:
                    try:
                        # Convert to dictionary format for knowledge service
                        profile_dict = {
                            'name': profile_data.name,
                            'role': profile_data.role,
                            'bio': profile_data.bio,
                            'contact': profile_data.contact or {},
                            'photo_url': profile_data.photo_url,
                            'source_url': profile_data.url,
                            'department': profile_data.department or 'Leadership'
                        }
                        
                        # Add to knowledge base
                        saved_profile = self.knowledge_service.add_profile(profile_dict)
                        saved_profiles.append(saved_profile)
                        
                        self.logger.info(f"Saved profile: {profile_data.name}")
                        
                        # Rate limiting between saves
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        self.logger.error(f"Error saving profile {profile_data.name}: {e}")
                        continue
                
                job.results = saved_profiles
                job.status = "completed"
                job.completed_at = datetime.now()
                job.metadata['profiles_saved'] = len(saved_profiles)
                
                self.logger.info(f"Successfully scraped and saved {len(saved_profiles)} Amzur leadership profiles")
                
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now()
            self.logger.error(f"Error in Amzur leadership scraping: {e}")
        
        return self.get_job_status(job_id)
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a scraping job."""
        job = self.jobs.get(job_id)
        return job.to_dict() if job else None
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get status of all scraping jobs."""
        return [job.to_dict() for job in self.jobs.values()]
    
    def get_recent_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent scraping jobs."""
        sorted_jobs = sorted(
            self.jobs.values(),
            key=lambda x: x.created_at,
            reverse=True
        )
        return [job.to_dict() for job in sorted_jobs[:limit]]
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a scraping job (if it's still pending)."""
        job = self.jobs.get(job_id)
        if job and job.status == "pending":
            job.status = "cancelled"
            job.completed_at = datetime.now()
            self.logger.info(f"Cancelled job: {job_id}")
            return True
        return False
    
    def cleanup_old_jobs(self, days_old: int = 7):
        """Clean up jobs older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        jobs_to_remove = []
        for job_id, job in self.jobs.items():
            if job.created_at < cutoff_date and job.status in ["completed", "failed", "cancelled"]:
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
        
        self.logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
    
    def get_scraping_statistics(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        total_jobs = len(self.jobs)
        status_counts = {}
        
        for job in self.jobs.values():
            status_counts[job.status] = status_counts.get(job.status, 0) + 1
        
        # Calculate success rate
        completed = status_counts.get('completed', 0)
        failed = status_counts.get('failed', 0)
        total_finished = completed + failed
        success_rate = (completed / total_finished * 100) if total_finished > 0 else 0
        
        # Calculate average processing time for completed jobs
        processing_times = []
        for job in self.jobs.values():
            if job.status == 'completed' and job.started_at and job.completed_at:
                duration = (job.completed_at - job.started_at).total_seconds()
                processing_times.append(duration)
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            'total_jobs': total_jobs,
            'status_distribution': status_counts,
            'success_rate': success_rate,
            'avg_processing_time_seconds': avg_processing_time,
            'rate_limit_delay': self.rate_limit_delay,
            'max_concurrent_jobs': self.max_concurrent_jobs
        }
    
    def schedule_recurring_scraping(self, target_url: str, interval_hours: int = 24):
        """
        Schedule recurring scraping for a target URL.
        
        This is a placeholder for more advanced scheduling functionality.
        In a production system, you might use Celery, APScheduler, or similar.
        """
        self.logger.info(f"Scheduled recurring scraping for {target_url} every {interval_hours} hours")
        # Implementation would depend on the chosen scheduling system
        
    def update_config(self, new_config: Dict[str, Any]):
        """Update scraping configuration."""
        self.config.update(new_config)
        
        # Update instance variables
        self.rate_limit_delay = self.config.get('rate_limit_delay', 1.0)
        self.max_concurrent_jobs = self.config.get('max_concurrent_jobs', 3)
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 5.0)
        
        self.logger.info("Updated scraping configuration")
    
    def export_scraped_data(self, output_format: str = "json") -> Dict[str, Any]:
        """Export all scraped data."""
        all_profiles = []
        
        for job in self.jobs.values():
            if job.status == "completed" and job.results:
                all_profiles.extend(job.results)
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_profiles': len(all_profiles),
            'profiles': all_profiles,
            'jobs_summary': self.get_scraping_statistics()
        }
        
        return export_data
