"""
Chat interface using Streamlit for conversational AI interactions.

Provides a user-friendly chat interface with message history,
context awareness, and scope-limited responses.
"""

import streamlit as st
from typing import Dict, Any, List
import uuid
from datetime import datetime

class ChatInterface:
    """Streamlit-based chat interface."""
    
    def __init__(self, chat_service):
        self.chat_service = chat_service
        
        # Initialize session state
        if 'chat_session_id' not in st.session_state:
            st.session_state.chat_session_id = str(uuid.uuid4())
        
        if 'messages' not in st.session_state:
            st.session_state.messages = []
            # Get initial welcome message
            session = self.chat_service.get_session(st.session_state.chat_session_id)
            if not session:
                session = self.chat_service.create_session(st.session_state.chat_session_id)
            
            # Add welcome message to session state
            if session.messages:
                welcome_msg = session.messages[0]
                st.session_state.messages.append({
                    'role': welcome_msg.role,
                    'content': welcome_msg.content,
                    'timestamp': welcome_msg.timestamp.isoformat()
                })
    
    def render(self):
        """Render the chat interface."""
        st.title("🤖 Knowledge Assistant")
        st.markdown("Ask me about our team members, roles, departments, and organizational structure.")
        
        # Sidebar with session info and options
        self._render_sidebar()
        
        # Chat container
        chat_container = st.container()
        
        with chat_container:
            # Display chat messages
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    
                    # Show timestamp for assistant messages
                    if message["role"] == "assistant":
                        timestamp = datetime.fromisoformat(message["timestamp"]).strftime("%H:%M:%S")
                        st.caption(f"Responded at {timestamp}")
        
        # Chat input
        self._render_chat_input()
        
        # Quick action buttons
        self._render_quick_actions()
    
    def _render_sidebar(self):
        """Render the sidebar with session info and controls."""
        with st.sidebar:
            st.header("Chat Session")
            
            # Session info
            st.text(f"Session ID: {st.session_state.chat_session_id[:8]}...")
            st.text(f"Messages: {len(st.session_state.messages)}")
            
            # Clear chat button
            if st.button("🗑️ Clear Chat", help="Start a new conversation"):
                self._clear_chat()
            
            # Export chat button
            if st.button("📥 Export Chat", help="Download chat history"):
                self._export_chat()
            
            st.divider()
            
            # Chat statistics
            self._render_chat_stats()
            
            st.divider()
            
            # Help section
            self._render_help_section()
    
    def _render_chat_input(self):
        """Render the chat input area."""
        # Chat input
        user_input = st.chat_input("Ask me about team members, roles, or departments...")
        
        if user_input:
            # Add user message to chat
            user_message = {
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now().isoformat()
            }
            st.session_state.messages.append(user_message)
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(user_input)
            
            # Get response from chat service
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = self.chat_service.process_message(
                        st.session_state.chat_session_id,
                        user_input
                    )
                
                # Display response
                st.markdown(response['message'])
                
                # Show response metadata
                if response.get('search_results'):
                    with st.expander(f"📊 Found {len(response['search_results'])} relevant results"):
                        for i, result in enumerate(response['search_results'][:3]):
                            st.write(f"**{i+1}. {result.get('title', 'Unknown')}**")
                            st.write(f"Type: {result.get('content_type', 'Unknown')}")
                            st.write(f"Relevance: {result.get('score', 0):.2f}")
                            if i < len(response['search_results']) - 1:
                                st.divider()
                
                # Show scope indicator
                if not response.get('in_scope'):
                    st.warning("⚠️ This question is outside my knowledge area. I can help with questions about our team and organization.")
                
                # Feedback buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👍 Helpful", key=f"helpful_{len(st.session_state.messages)}"):
                        self._provide_feedback(len(st.session_state.messages), "helpful")
                with col2:
                    if st.button("👎 Not Helpful", key=f"not_helpful_{len(st.session_state.messages)}"):
                        self._provide_feedback(len(st.session_state.messages), "not_helpful")
            
            # Add assistant response to session state
            assistant_message = {
                'role': 'assistant',
                'content': response['message'],
                'timestamp': response['timestamp'],
                'metadata': {
                    'type': response['type'],
                    'in_scope': response['in_scope'],
                    'results_count': len(response.get('search_results', []))
                }
            }
            st.session_state.messages.append(assistant_message)
            
            # Rerun to update the interface
            st.rerun()
    
    def _render_quick_actions(self):
        """Render quick action buttons."""
        st.subheader("Quick Questions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👑 Who is the CEO?"):
                self._ask_question("Who is the CEO?")
        
        with col2:
            if st.button("👥 Show me the team"):
                self._ask_question("Show me all team members")
        
        with col3:
            if st.button("🏢 List departments"):
                self._ask_question("What departments do we have?")
        
        # Additional quick actions
        col4, col5, col6 = st.columns(3)
        
        with col4:
            if st.button("💼 Engineering team"):
                self._ask_question("Who is in the engineering team?")
        
        with col5:
            if st.button("📊 Leadership team"):
                self._ask_question("Show me the leadership team")
        
        with col6:
            if st.button("📞 Contact info"):
                self._ask_question("How can I contact the team?")
    
    def _render_chat_stats(self):
        """Render chat statistics in the sidebar."""
        st.subheader("Chat Stats")
        
        user_messages = len([msg for msg in st.session_state.messages if msg['role'] == 'user'])
        assistant_messages = len([msg for msg in st.session_state.messages if msg['role'] == 'assistant'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Your messages", user_messages)
        with col2:
            st.metric("AI responses", assistant_messages)
        
        # Calculate in-scope vs out-of-scope messages
        in_scope = 0
        out_of_scope = 0
        
        for msg in st.session_state.messages:
            if msg['role'] == 'assistant' and 'metadata' in msg:
                if msg['metadata'].get('in_scope', True):
                    in_scope += 1
                else:
                    out_of_scope += 1
        
        if in_scope + out_of_scope > 0:
            scope_percentage = (in_scope / (in_scope + out_of_scope)) * 100
            st.metric("In-scope queries", f"{scope_percentage:.0f}%")
    
    def _render_help_section(self):
        """Render help information."""
        st.subheader("💡 Tips")
        
        help_text = """
        **What I can help with:**
        - Finding team members by name
        - Looking up roles and positions
        - Exploring departments
        - Getting contact information
        - Learning about backgrounds
        
        **Example questions:**
        - "Who is the CTO?"
        - "Show me people in marketing"
        - "Tell me about John Smith"
        - "What is Sarah's email?"
        """
        
        st.markdown(help_text)
    
    def _ask_question(self, question: str):
        """Programmatically ask a question."""
        # Add the question as if the user typed it
        st.session_state.chat_input = question
        st.rerun()
    
    def _provide_feedback(self, message_index: int, feedback: str):
        """Provide feedback on a response."""
        success = self.chat_service.provide_feedback(
            st.session_state.chat_session_id,
            message_index,
            feedback
        )
        
        if success:
            st.success(f"Thank you for your feedback! ({feedback})")
        else:
            st.error("Failed to record feedback")
    
    def _clear_chat(self):
        """Clear the current chat session."""
        # Clear session state
        st.session_state.messages = []
        
        # Create new session
        st.session_state.chat_session_id = str(uuid.uuid4())
        session = self.chat_service.create_session(st.session_state.chat_session_id)
        
        # Add welcome message
        if session.messages:
            welcome_msg = session.messages[0]
            st.session_state.messages.append({
                'role': welcome_msg.role,
                'content': welcome_msg.content,
                'timestamp': welcome_msg.timestamp.isoformat()
            })
        
        st.success("Chat cleared! Starting fresh conversation.")
        st.rerun()
    
    def _export_chat(self):
        """Export chat history."""
        session_history = self.chat_service.get_session_history(st.session_state.chat_session_id)
        
        if session_history:
            import json
            
            # Prepare export data
            export_data = {
                'session_id': session_history['session_id'],
                'created_at': session_history['created_at'],
                'messages': session_history['messages'],
                'export_timestamp': datetime.now().isoformat()
            }
            
            # Convert to JSON
            json_str = json.dumps(export_data, indent=2)
            
            # Provide download
            st.download_button(
                label="📥 Download Chat History",
                data=json_str,
                file_name=f"chat_history_{st.session_state.chat_session_id[:8]}.json",
                mime="application/json"
            )
        else:
            st.error("No chat history found")
    
    def render_chat_analytics(self):
        """Render chat analytics (for admin use)."""
        st.subheader("📊 Chat Analytics")
        
        # Get active sessions
        active_sessions = self.chat_service.get_active_sessions()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Active Sessions", len(active_sessions))
        with col2:
            st.metric("Current Session Messages", len(st.session_state.messages))
        
        # Session details
        if st.checkbox("Show Session Details"):
            for session_id in active_sessions[:5]:  # Show top 5
                session_data = self.chat_service.get_session_history(session_id)
                if session_data:
                    with st.expander(f"Session {session_id[:8]}..."):
                        st.write(f"**Created:** {session_data['created_at']}")
                        st.write(f"**Messages:** {len(session_data['messages'])}")
                        
                        if st.button(f"Clear Session {session_id[:8]}", key=f"clear_{session_id}"):
                            self.chat_service.clear_session(session_id)
                            st.success(f"Cleared session {session_id[:8]}")
                            st.rerun()
