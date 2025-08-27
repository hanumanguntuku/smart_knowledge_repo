"""
Browse interface for exploring the knowledge repository.

Provides structured browsing of profiles, departments, and
knowledge entries with filtering and search capabilities.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional

class BrowseInterface:
    """Streamlit-based interface for browsing knowledge repository."""
    
    def __init__(self, knowledge_service):
        self.knowledge_service = knowledge_service
    
    def render(self):
        """Render the browse interface."""
        st.title("📚 Knowledge Repository Browser")
        st.markdown("Explore our team profiles, departments, and organizational knowledge.")
        
        # Create tabs for different browsing modes
        tab1, tab2, tab3, tab4 = st.tabs(["👥 People", "🏢 Departments", "🔍 Search", "📊 Statistics"])
        
        with tab1:
            self._render_people_browser()
        
        with tab2:
            self._render_department_browser()
        
        with tab3:
            self._render_search_interface()
        
        with tab4:
            self._render_statistics()
    
    def _render_people_browser(self):
        """Render the people browsing interface."""
        st.header("👥 Team Members")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Department filter
            departments = self.knowledge_service.get_departments()
            selected_dept = st.selectbox(
                "Filter by Department",
                ["All"] + departments,
                key="people_dept_filter"
            )
        
        with col2:
            # Role filter
            roles = self.knowledge_service.get_roles()
            selected_role = st.selectbox(
                "Filter by Role",
                ["All"] + roles,
                key="people_role_filter"
            )
        
        with col3:
            # Sort options
            sort_by = st.selectbox(
                "Sort by",
                ["Name", "Role", "Department"],
                key="people_sort"
            )
        
        # Get profiles based on filters
        profiles = self._get_filtered_profiles(selected_dept, selected_role)
        
        if not profiles:
            st.info("No team members found matching the current filters.")
            return
        
        # Display count
        st.write(f"**Found {len(profiles)} team members**")
        
        # Sort profiles
        profiles = self._sort_profiles(profiles, sort_by)
        
        # Display profiles
        self._display_profiles_grid(profiles)
    
    def _render_department_browser(self):
        """Render the department browsing interface."""
        st.header("🏢 Departments")
        
        departments = self.knowledge_service.get_departments()
        
        if not departments:
            st.info("No departments found in the knowledge base.")
            return
        
        # Department selection
        selected_dept = st.selectbox("Select a department to explore:", departments)
        
        if selected_dept:
            # Get department statistics
            dept_profiles = []
            all_profiles = self.knowledge_service.get_all_profiles(limit=1000)
            
            for profile in all_profiles:
                if profile.get('department') == selected_dept:
                    dept_profiles.append(profile)
            
            # Display department info
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Team Members", len(dept_profiles))
            
            with col2:
                # Count unique roles in department
                roles = set(profile.get('role', '') for profile in dept_profiles if profile.get('role'))
                st.metric("Unique Roles", len(roles))
            
            # Display department members
            if dept_profiles:
                st.subheader(f"Members of {selected_dept}")
                self._display_profiles_list(dept_profiles)
            else:
                st.info(f"No team members found in {selected_dept} department.")
    
    def _render_search_interface(self):
        """Render the search interface."""
        st.header("🔍 Advanced Search")
        
        # Search configuration
        col1, col2 = st.columns(2)
        
        with col1:
            search_query = st.text_input(
                "Search Query",
                placeholder="Enter your search terms...",
                key="browse_search_query"
            )
        
        with col2:
            search_type = st.selectbox(
                "Search Type",
                ["Hybrid", "Keyword", "Semantic"],
                key="browse_search_type"
            )
        
        # Content type filters
        content_types = st.multiselect(
            "Content Types",
            ["profile", "knowledge", "document"],
            default=["profile"],
            key="browse_content_types"
        )
        
        # Number of results
        max_results = st.slider("Maximum Results", 1, 50, 10, key="browse_max_results")
        
        # Search button
        if st.button("🔍 Search", key="browse_search_btn") and search_query:
            with st.spinner("Searching..."):
                results = self.knowledge_service.search_knowledge(
                    query=search_query,
                    search_type=search_type.lower(),
                    content_types=content_types,
                    limit=max_results
                )
            
            if results:
                st.success(f"Found {len(results)} results")
                self._display_search_results(results)
            else:
                st.info("No results found for your search query.")
    
    def _render_statistics(self):
        """Render knowledge repository statistics."""
        st.header("📊 Repository Statistics")
        
        # Get statistics
        stats = self.knowledge_service.get_knowledge_statistics()
        
        if not stats:
            st.error("Unable to load statistics.")
            return
        
        # Profile statistics
        st.subheader("👥 Profile Statistics")
        
        profile_stats = stats.get('profiles', {})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Profiles", profile_stats.get('total', 0))
        with col2:
            st.metric("Departments", profile_stats.get('departments', 0))
        with col3:
            st.metric("Unique Roles", profile_stats.get('roles', 0))
        
        # Department distribution
        if profile_stats.get('total', 0) > 0:
            st.subheader("🏢 Department Distribution")
            
            # Get all profiles and count by department
            all_profiles = self.knowledge_service.get_all_profiles(limit=1000)
            dept_counts = {}
            
            for profile in all_profiles:
                dept = profile.get('department', 'Unknown')
                dept_counts[dept] = dept_counts.get(dept, 0) + 1
            
            if dept_counts:
                # Create bar chart
                dept_df = pd.DataFrame(
                    list(dept_counts.items()),
                    columns=['Department', 'Count']
                )
                st.bar_chart(dept_df.set_index('Department'))
        
        # Knowledge entries statistics
        if 'knowledge_entries' in stats:
            st.subheader("📚 Knowledge Entries")
            
            knowledge_stats = stats['knowledge_entries']
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Entries", knowledge_stats.get('total', 0))
            
            with col2:
                content_types = knowledge_stats.get('types', [])
                st.metric("Content Types", len(content_types))
        
        # Search statistics
        if 'search' in stats:
            st.subheader("🔍 Search Statistics")
            
            search_stats = stats['search']
            index_stats = search_stats.get('index_stats', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Indexed Items", index_stats.get('total_indexed', 0))
            
            with col2:
                st.metric("Search Changes", index_stats.get('changes_since_rebuild', 0))
            
            # Query analytics
            if 'query_analytics' in search_stats:
                query_analytics = search_stats['query_analytics']
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Queries", query_analytics.get('total_queries', 0))
                
                with col2:
                    avg_time = query_analytics.get('avg_response_time_ms', 0)
                    st.metric("Avg Response Time", f"{avg_time:.0f}ms")
                
                with col3:
                    feedback_dist = query_analytics.get('feedback_distribution', {})
                    helpful = feedback_dist.get('helpful', 0)
                    total_feedback = sum(feedback_dist.values())
                    if total_feedback > 0:
                        satisfaction = (helpful / total_feedback) * 100
                        st.metric("User Satisfaction", f"{satisfaction:.0f}%")
    
    def _get_filtered_profiles(self, department: str, role: str) -> List[Dict[str, Any]]:
        """Get profiles based on filters."""
        all_profiles = self.knowledge_service.get_all_profiles(limit=1000)
        
        filtered_profiles = []
        
        for profile in all_profiles:
            # Department filter
            if department != "All" and profile.get('department') != department:
                continue
            
            # Role filter
            if role != "All" and profile.get('role') != role:
                continue
            
            filtered_profiles.append(profile)
        
        return filtered_profiles
    
    def _sort_profiles(self, profiles: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
        """Sort profiles by the specified field."""
        if sort_by == "Name":
            return sorted(profiles, key=lambda x: x.get('name', '').lower())
        elif sort_by == "Role":
            return sorted(profiles, key=lambda x: x.get('role', '').lower())
        elif sort_by == "Department":
            return sorted(profiles, key=lambda x: x.get('department', '').lower())
        else:
            return profiles
    
    def _display_profiles_grid(self, profiles: List[Dict[str, Any]]):
        """Display profiles in a grid layout."""
        # Display in columns of 2
        for i in range(0, len(profiles), 2):
            col1, col2 = st.columns(2)
            
            with col1:
                if i < len(profiles):
                    self._display_profile_card(profiles[i])
            
            with col2:
                if i + 1 < len(profiles):
                    self._display_profile_card(profiles[i + 1])
    
    def _display_profiles_list(self, profiles: List[Dict[str, Any]]):
        """Display profiles in a list format."""
        for profile in profiles:
            with st.expander(f"👤 {profile.get('name', 'Unknown')}"):
                self._display_profile_details(profile)
    
    def _display_profile_card(self, profile: Dict[str, Any]):
        """Display a single profile card."""
        with st.container():
            st.subheader(f"👤 {profile.get('name', 'Unknown')}")
            
            if profile.get('role'):
                st.write(f"**Role:** {profile['role']}")
            
            if profile.get('department'):
                st.write(f"**Department:** {profile['department']}")
            
            if profile.get('bio'):
                bio_text = profile['bio'][:100] + "..." if len(profile['bio']) > 100 else profile['bio']
                st.write(f"**Bio:** {bio_text}")
            
            # Contact information
            contact = profile.get('contact', {})
            if contact:
                contact_info = []
                if contact.get('email'):
                    contact_info.append(f"📧 {contact['email']}")
                if contact.get('phone'):
                    contact_info.append(f"📞 {contact['phone']}")
                
                if contact_info:
                    st.write("**Contact:** " + " | ".join(contact_info))
            
            # View details button
            if st.button(f"View Details", key=f"details_{profile.get('id', 'unknown')}"):
                st.session_state[f"show_profile_{profile.get('id')}"] = True
            
            st.divider()
    
    def _display_profile_details(self, profile: Dict[str, Any]):
        """Display detailed profile information."""
        # Basic info
        if profile.get('role'):
            st.write(f"**Role:** {profile['role']}")
        
        if profile.get('department'):
            st.write(f"**Department:** {profile['department']}")
        
        # Bio
        if profile.get('bio'):
            st.write(f"**Biography:**")
            st.write(profile['bio'])
        
        # Contact information
        contact = profile.get('contact', {})
        if contact:
            st.write("**Contact Information:**")
            
            if contact.get('email'):
                st.write(f"📧 Email: {contact['email']}")
            
            if contact.get('phone'):
                st.write(f"📞 Phone: {contact['phone']}")
            
            # Social links
            social_links = []
            for platform in ['linkedin', 'twitter', 'github']:
                if contact.get(platform):
                    social_links.append(f"[{platform.title()}]({contact[platform]})")
            
            if social_links:
                st.write("🔗 Social: " + " | ".join(social_links))
        
        # Source URL
        if profile.get('source_url'):
            st.write(f"**Source:** [Original Profile]({profile['source_url']})")
        
        # Metadata
        if profile.get('created_at'):
            st.caption(f"Added to repository: {profile['created_at']}")
    
    def _display_search_results(self, results: List[Dict[str, Any]]):
        """Display search results."""
        for i, result in enumerate(results):
            with st.expander(f"{i+1}. {result.get('title', 'Unknown')} (Score: {result.get('score', 0):.2f})"):
                
                st.write(f"**Type:** {result.get('content_type', 'Unknown')}")
                
                if result.get('content'):
                    content_preview = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
                    st.write(f"**Content Preview:**")
                    st.write(content_preview)
                
                # Metadata
                metadata = result.get('metadata', {})
                if metadata:
                    st.write("**Additional Info:**")
                    for key, value in metadata.items():
                        if value:
                            st.write(f"- {key.title()}: {value}")
    
    def render_profile_detail_modal(self, profile_id: int):
        """Render a detailed view modal for a profile."""
        # This would be implemented if Streamlit supports modal dialogs
        # For now, we'll use the expander approach in the main interface
        pass
