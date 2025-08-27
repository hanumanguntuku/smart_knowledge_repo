"""
Main application entry point for the Smart Knowledge Repository.

This file sets up and runs the Streamlit application with all
UI components and services integrated.
"""

import streamlit as st
import sys
import os
import logging
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import services
from src.services.knowledge_service import KnowledgeService
from src.services.chat_service import ChatService
from src.services.scraping_service import ScrapingService

# Import UI components
from src.ui.chat_interface import ChatInterface
from src.ui.browse_interface import BrowseInterface
from src.ui.admin_interface import AdminInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@st.cache_resource
def initialize_services():
    """Initialize all services (cached for performance)."""
    try:
        # Initialize knowledge service (this will set up database)
        knowledge_service = KnowledgeService()
        
        # Initialize chat service
        chat_service = ChatService(knowledge_service)
        
        # Initialize scraping service
        scraping_service = ScrapingService(knowledge_service)
        
        return knowledge_service, chat_service, scraping_service
    
    except Exception as e:
        st.error(f"Failed to initialize services: {e}")
        st.stop()

def main():
    """Main application function."""
    
    # Page configuration
    st.set_page_config(
        page_title="Smart Knowledge Repository",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
    
    .metric-container {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🧠 Smart Knowledge Repository</h1>
        <p>Intelligent knowledge management with AI-powered search and chat</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize services
    with st.spinner("Initializing system..."):
        knowledge_service, chat_service, scraping_service = initialize_services()
    
    # Sidebar with system status
    with st.sidebar:
        st.header("📊 System Status")
        
        # System health check
        try:
            stats = knowledge_service.get_knowledge_statistics()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Profiles", stats.get('profiles', {}).get('total', 0))
            with col2:
                st.metric("Departments", stats.get('profiles', {}).get('departments', 0))
            
            st.success("🟢 System Online")
            
        except Exception as e:
            st.error("🔴 System Error")
            st.error(str(e))
        
        st.divider()
        
        # Navigation info
        st.info("""
        **Navigation:**
        - 💬 **Chat**: Ask questions about team members
        - 📚 **Browse**: Explore profiles and departments  
        - ⚙️ **Admin**: System management (admin only)
        """)
        
        st.divider()
        
        # Quick stats
        st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        
        if st.button("🔄 Refresh"):
            st.cache_resource.clear()
            st.rerun()
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "📚 Browse", "⚙️ Admin"])
    
    with tab1:
        chat_interface = ChatInterface(chat_service)
        chat_interface.render()
    
    with tab2:
        browse_interface = BrowseInterface(knowledge_service)
        browse_interface.render()
    
    with tab3:
        admin_interface = AdminInterface(knowledge_service, scraping_service)
        admin_interface.render()
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📋 Project 3: Smart Knowledge Repository**")
    
    with col2:
        st.markdown("Built with Streamlit, SQLAlchemy, and AI")
    
    with col3:
        st.markdown(f"**Version 1.0** | {datetime.now().strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    main()
