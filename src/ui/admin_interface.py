"""
Admin interface for managing the knowledge repository.

Provides administrative functions for data management, scraping,
system monitoring, and configuration.
"""

import streamlit as st
import asyncio
from typing import Dict, Any, List
from datetime import datetime
import json

class AdminInterface:
    """Streamlit-based admin interface for system management."""
    
    def __init__(self, knowledge_service, scraping_service):
        self.knowledge_service = knowledge_service
        self.scraping_service = scraping_service
    
    def render(self):
        """Render the admin interface."""
        # Check admin access (in production, implement proper authentication)
        if not self._check_admin_access():
            st.error("🔒 Admin access required")
            return
        
        st.title("⚙️ Knowledge Repository Admin")
        st.markdown("Administrative interface for system management and monitoring.")
        
        # Create tabs for different admin functions
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "🕷️ Scraping", "💾 Data", "🔍 Search", "⚙️ System"])
        
        with tab1:
            self._render_dashboard()
        
        with tab2:
            self._render_scraping_management()
        
        with tab3:
            self._render_data_management()
        
        with tab4:
            self._render_search_management()
        
        with tab5:
            self._render_system_management()
    
    def _check_admin_access(self) -> bool:
        """Check if user has admin access."""
        # In production, implement proper authentication
        # For now, use a simple password check
        
        if 'admin_authenticated' not in st.session_state:
            st.session_state.admin_authenticated = False
        
        if not st.session_state.admin_authenticated:
            admin_password = st.text_input("Admin Password", type="password")
            
            if st.button("Login"):
                if admin_password == "admin123":  # In production, use proper auth
                    st.session_state.admin_authenticated = True
                    st.success("Admin access granted")
                    st.rerun()
                else:
                    st.error("Invalid password")
            
            return False
        
        return True
    
    def _render_dashboard(self):
        """Render the admin dashboard."""
        st.header("📊 System Dashboard")
        
        # System statistics
        stats = self.knowledge_service.get_knowledge_statistics()
        scraping_stats = self.scraping_service.get_scraping_statistics()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            profile_count = stats.get('profiles', {}).get('total', 0)
            st.metric("Total Profiles", profile_count)
        
        with col2:
            knowledge_count = stats.get('knowledge_entries', {}).get('total', 0)
            st.metric("Knowledge Entries", knowledge_count)
        
        with col3:
            scraping_jobs = scraping_stats.get('total_jobs', 0)
            st.metric("Scraping Jobs", scraping_jobs)
        
        with col4:
            success_rate = scraping_stats.get('success_rate', 0)
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Recent activity
        st.subheader("📈 Recent Activity")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Recent Scraping Jobs**")
            recent_jobs = self.scraping_service.get_recent_jobs(5)
            
            if recent_jobs:
                for job in recent_jobs:
                    status_emoji = {"completed": "✅", "failed": "❌", "running": "🔄", "pending": "⏳"}.get(job['status'], "❓")
                    st.write(f"{status_emoji} {job['job_id'][:15]}... - {job['status']}")
            else:
                st.info("No recent scraping jobs")
        
        with col2:
            st.write("**System Health**")
            
            # Check database connectivity
            try:
                self.knowledge_service.get_departments()
                st.write("✅ Database: Connected")
            except:
                st.write("❌ Database: Error")
            
            # Check search index
            search_stats = stats.get('search', {}).get('index_stats', {})
            indexed_items = search_stats.get('total_indexed', 0)
            st.write(f"🔍 Search Index: {indexed_items} items")
            
            # Memory usage (placeholder)
            st.write("💾 Memory Usage: Normal")
    
    def _render_scraping_management(self):
        """Render scraping management interface."""
        st.header("🕷️ Scraping Management")
        
        # Scraping controls
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 New Scraping Job")
            
            target_url = st.text_input("Target URL", placeholder="https://example.com/team")
            job_type = st.selectbox("Job Type", ["profile", "discovery"])
            
            if st.button("🚀 Start Scraping Job"):
                if target_url:
                    job_id = self.scraping_service.create_scraping_job(target_url, job_type)
                    st.success(f"Created job: {job_id}")
                    
                    # Run the job asynchronously (in production, use proper task queue)
                    with st.spinner("Running scraping job..."):
                        try:
                            # This is a simplified approach - in production use Celery or similar
                            result = asyncio.run(self.scraping_service.run_job(job_id))
                            
                            if result['status'] == 'completed':
                                st.success(f"Job completed successfully!")
                                if job_type == 'profile':
                                    st.write(f"Scraped {result.get('profiles_scraped', 0)} profiles")
                            else:
                                st.error(f"Job failed: {result.get('error', 'Unknown error')}")
                                
                        except Exception as e:
                            st.error(f"Error running job: {e}")
                else:
                    st.error("Please enter a target URL")
        
        with col2:
            st.subheader("📊 Scraping Statistics")
            
            scraping_stats = self.scraping_service.get_scraping_statistics()
            
            st.metric("Total Jobs", scraping_stats.get('total_jobs', 0))
            st.metric("Success Rate", f"{scraping_stats.get('success_rate', 0):.1f}%")
            st.metric("Avg Processing Time", f"{scraping_stats.get('avg_processing_time_seconds', 0):.1f}s")
            
            # Job status distribution
            status_dist = scraping_stats.get('status_distribution', {})
            if status_dist:
                st.write("**Job Status Distribution:**")
                for status, count in status_dist.items():
                    st.write(f"- {status.title()}: {count}")
        
        # Job management
        st.subheader("📋 Job Management")
        
        all_jobs = self.scraping_service.get_all_jobs()
        
        if all_jobs:
            # Job filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_filter = st.selectbox("Filter by Status", ["All"] + list(set(job['status'] for job in all_jobs)))
            
            with col2:
                job_type_filter = st.selectbox("Filter by Type", ["All"] + list(set(job['job_type'] for job in all_jobs)))
            
            with col3:
                show_count = st.slider("Show Jobs", 1, min(len(all_jobs), 20), 10)
            
            # Filter jobs
            filtered_jobs = all_jobs
            if status_filter != "All":
                filtered_jobs = [job for job in filtered_jobs if job['status'] == status_filter]
            if job_type_filter != "All":
                filtered_jobs = [job for job in filtered_jobs if job['job_type'] == job_type_filter]
            
            # Display jobs
            for job in filtered_jobs[:show_count]:
                with st.expander(f"{job['job_id']} - {job['status'].upper()}"):
                    st.write(f"**URL:** {job['target_url']}")
                    st.write(f"**Type:** {job['job_type']}")
                    st.write(f"**Created:** {job['created_at']}")
                    
                    if job['status'] == 'completed':
                        st.write(f"**Results:** {job['results_count']} items")
                    elif job['status'] == 'failed':
                        st.error(f"**Error:** {job['error_message']}")
                    
                    # Job actions
                    col1, col2 = st.columns(2)
                    with col1:
                        if job['status'] == 'pending' and st.button(f"Cancel", key=f"cancel_{job['job_id']}"):
                            if self.scraping_service.cancel_job(job['job_id']):
                                st.success("Job cancelled")
                                st.rerun()
        else:
            st.info("No scraping jobs found")
    
    def _render_data_management(self):
        """Render data management interface."""
        st.header("💾 Data Management")
        
        # Data statistics
        stats = self.knowledge_service.get_knowledge_statistics()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Data Overview")
            
            profile_stats = stats.get('profiles', {})
            st.metric("Total Profiles", profile_stats.get('total', 0))
            st.metric("Departments", profile_stats.get('departments', 0))
            st.metric("Roles", profile_stats.get('roles', 0))
            
            knowledge_stats = stats.get('knowledge_entries', {})
            st.metric("Knowledge Entries", knowledge_stats.get('total', 0))
        
        with col2:
            st.subheader("🔧 Data Operations")
            
            # Data export
            if st.button("📥 Export All Data"):
                export_data = self.scraping_service.export_scraped_data()
                
                json_str = json.dumps(export_data, indent=2, default=str)
                
                st.download_button(
                    label="📥 Download Export",
                    data=json_str,
                    file_name=f"knowledge_repo_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            # Data cleanup
            if st.button("🧹 Clean Old Jobs"):
                self.scraping_service.cleanup_old_jobs(days_old=7)
                st.success("Cleaned up old scraping jobs")
            
            # Rebuild search index
            if st.button("🔄 Rebuild Search Index"):
                with st.spinner("Rebuilding search index..."):
                    try:
                        self.knowledge_service.rebuild_search_index()
                        st.success("Search index rebuilt successfully")
                    except Exception as e:
                        st.error(f"Error rebuilding index: {e}")
        
        # Profile management
        st.subheader("👥 Profile Management")
        
        # Recent profiles
        recent_profiles = self.knowledge_service.get_all_profiles(limit=10)
        
        if recent_profiles:
            selected_profile = st.selectbox(
                "Select Profile to Manage",
                options=[p['id'] for p in recent_profiles],
                format_func=lambda x: next(p['name'] for p in recent_profiles if p['id'] == x)
            )
            
            if selected_profile:
                profile = next(p for p in recent_profiles if p['id'] == selected_profile)
                
                with st.expander("Profile Details"):
                    st.json(profile)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✏️ Edit Profile"):
                        st.info("Profile editing interface would go here")
                
                with col2:
                    if st.button("🗑️ Delete Profile", type="secondary"):
                        if st.checkbox("Confirm deletion"):
                            if self.knowledge_service.delete_profile(selected_profile):
                                st.success("Profile deleted")
                                st.rerun()
                            else:
                                st.error("Failed to delete profile")
    
    def _render_search_management(self):
        """Render search management interface."""
        st.header("🔍 Search Management")
        
        # Search statistics
        stats = self.knowledge_service.get_knowledge_statistics()
        search_stats = stats.get('search', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Search Statistics")
            
            index_stats = search_stats.get('index_stats', {})
            st.metric("Indexed Items", index_stats.get('total_indexed', 0))
            st.metric("Changes Since Rebuild", index_stats.get('changes_since_rebuild', 0))
            
            query_analytics = search_stats.get('query_analytics', {})
            st.metric("Total Queries", query_analytics.get('total_queries', 0))
            avg_time = query_analytics.get('avg_response_time_ms', 0)
            st.metric("Avg Response Time", f"{avg_time:.0f}ms")
        
        with col2:
            st.subheader("🔧 Search Operations")
            
            # Test search
            test_query = st.text_input("Test Search Query")
            search_type = st.selectbox("Search Type", ["hybrid", "keyword", "semantic"])
            
            if st.button("🔍 Test Search") and test_query:
                with st.spinner("Searching..."):
                    results = self.knowledge_service.search_knowledge(
                        query=test_query,
                        search_type=search_type,
                        limit=5
                    )
                
                st.write(f"**Found {len(results)} results:**")
                for i, result in enumerate(results):
                    st.write(f"{i+1}. {result.get('title', 'Unknown')} (Score: {result.get('score', 0):.2f})")
            
            # Index management
            if st.button("🔄 Rebuild Search Index"):
                with st.spinner("Rebuilding search index..."):
                    try:
                        self.knowledge_service.rebuild_search_index()
                        st.success("Search index rebuilt")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        # Query analytics
        if query_analytics.get('total_queries', 0) > 0:
            st.subheader("📈 Query Analytics")
            
            feedback_dist = query_analytics.get('feedback_distribution', {})
            if feedback_dist:
                st.write("**User Feedback Distribution:**")
                for feedback, count in feedback_dist.items():
                    st.write(f"- {feedback or 'No feedback'}: {count}")
    
    def _render_system_management(self):
        """Render system management interface."""
        st.header("⚙️ System Management")
        
        # System configuration
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔧 Configuration")
            
            # Scraping configuration
            current_config = self.scraping_service.config
            
            rate_limit = st.number_input(
                "Rate Limit Delay (seconds)",
                min_value=0.1,
                max_value=10.0,
                value=current_config.get('rate_limit_delay', 1.0),
                step=0.1
            )
            
            max_concurrent = st.number_input(
                "Max Concurrent Jobs",
                min_value=1,
                max_value=10,
                value=current_config.get('max_concurrent_jobs', 3)
            )
            
            max_retries = st.number_input(
                "Max Retries",
                min_value=1,
                max_value=10,
                value=current_config.get('max_retries', 3)
            )
            
            if st.button("💾 Save Configuration"):
                new_config = {
                    'rate_limit_delay': rate_limit,
                    'max_concurrent_jobs': max_concurrent,
                    'max_retries': max_retries
                }
                self.scraping_service.update_config(new_config)
                st.success("Configuration saved")
        
        with col2:
            st.subheader("📊 System Health")
            
            # Database status
            try:
                stats = self.knowledge_service.get_knowledge_statistics()
                st.write("✅ Database: Connected")
                st.write(f"📊 Profiles: {stats.get('profiles', {}).get('total', 0)}")
            except Exception as e:
                st.write("❌ Database: Error")
                st.error(str(e))
            
            # Search index status
            search_stats = stats.get('search', {}).get('index_stats', {})
            indexed_count = search_stats.get('total_indexed', 0)
            st.write(f"🔍 Search Index: {indexed_count} items")
            
            # System actions
            st.subheader("🔄 System Actions")
            
            if st.button("🧹 System Cleanup"):
                with st.spinner("Running system cleanup..."):
                    # Cleanup old jobs
                    self.scraping_service.cleanup_old_jobs(days_old=7)
                    st.success("System cleanup completed")
            
            if st.button("📊 Generate Report"):
                # Generate system report
                report = {
                    'timestamp': datetime.now().isoformat(),
                    'statistics': stats,
                    'scraping_stats': self.scraping_service.get_scraping_statistics(),
                    'system_config': current_config
                }
                
                report_json = json.dumps(report, indent=2, default=str)
                
                st.download_button(
                    label="📥 Download Report",
                    data=report_json,
                    file_name=f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        # Logs viewer (placeholder)
        st.subheader("📝 System Logs")
        
        log_level = st.selectbox("Log Level", ["INFO", "WARNING", "ERROR"])
        
        if st.button("📄 View Recent Logs"):
            # This would show actual logs in a production system
            st.text_area(
                "Recent Logs",
                value=f"[{datetime.now()}] {log_level}: Sample log entry\\n"
                      f"[{datetime.now()}] INFO: System is running normally\\n"
                      f"[{datetime.now()}] INFO: Search index is up to date",
                height=200
            )
