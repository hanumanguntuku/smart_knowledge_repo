"""
Chat service for handling conversational AI interactions.

Provides scope-aware chat functionality with context management
and intelligent response generation.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re

class ChatMessage:
    """Represents a chat message."""
    
    def __init__(self, content: str, role: str = "user", timestamp: Optional[datetime] = None):
        self.content = content
        self.role = role  # "user", "assistant", "system"
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'role': self.role,
            'timestamp': self.timestamp.isoformat()
        }

class ChatSession:
    """Manages a chat session with message history."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[ChatMessage] = []
        self.context: Dict[str, Any] = {}
        self.created_at = datetime.now()
    
    def add_message(self, message: ChatMessage):
        """Add a message to the session."""
        self.messages.append(message)
    
    def get_recent_messages(self, count: int = 10) -> List[ChatMessage]:
        """Get recent messages from the session."""
        return self.messages[-count:]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'messages': [msg.to_dict() for msg in self.messages],
            'context': self.context,
            'created_at': self.created_at.isoformat()
        }

class ChatService:
    """Service for handling chat interactions with scope-aware responses."""
    
    def __init__(self, knowledge_service):
        self.knowledge_service = knowledge_service
        self.logger = logging.getLogger(__name__)
        self.sessions: Dict[str, ChatSession] = {}
        
        # Response templates
        self.response_templates = {
            'out_of_scope': [
                "I'm sorry, but I can only help with questions about our team members and organization. "
                "Could you ask me something about our staff, leadership, or company profiles?",
                
                "I don't have information about that topic. I can help you find information about "
                "our team members, their roles, contact details, and backgrounds. What would you like to know?",
                
                "That's outside my area of expertise. I specialize in providing information about "
                "our organization's people and structure. How can I help you with that?"
            ],
            'no_results': [
                "I couldn't find any information matching your query. Could you try rephrasing your question "
                "or ask about a specific person or role?",
                
                "I don't have that information in my knowledge base. You might want to try searching for "
                "someone by name, role, or department.",
                
                "No matching results found. Try asking about specific team members, departments, or roles."
            ],
            'greeting': [
                "Hello! I'm here to help you find information about our team members and organization. "
                "You can ask me about people's roles, contact information, backgrounds, or departments.",
                
                "Hi there! I can help you learn about our team. You can ask me questions like 'Who is the CEO?' "
                "or 'Show me people in the engineering department.'",
                
                "Welcome! I'm your knowledge assistant. I can provide information about our staff, "
                "leadership team, and organizational structure. What would you like to know?"
            ]
        }
    
    def create_session(self, session_id: str) -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(session_id)
        self.sessions[session_id] = session
        
        # Add welcome message
        welcome_msg = ChatMessage(
            content=self._get_random_template('greeting'),
            role="assistant"
        )
        session.add_message(welcome_msg)
        
        self.logger.info(f"Created new chat session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get an existing chat session."""
        return self.sessions.get(session_id)
    
    def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Process a user message and generate a response.
        
        Args:
            session_id: Chat session ID
            user_message: User's message
            
        Returns:
            Dictionary containing response and metadata
        """
        # Get or create session
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)
        
        # Add user message to session
        user_msg = ChatMessage(content=user_message, role="user")
        session.add_message(user_msg)
        
        try:
            # Check if query is within scope
            if not self.knowledge_service.check_scope(user_message):
                response_content = self._get_random_template('out_of_scope')
                response_type = "out_of_scope"
                search_results = []
            else:
                # Process the query
                response_content, response_type, search_results = self._process_knowledge_query(user_message)
            
            # Create assistant response
            assistant_msg = ChatMessage(content=response_content, role="assistant")
            session.add_message(assistant_msg)
            
            response = {
                'message': response_content,
                'type': response_type,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'search_results': search_results,
                'in_scope': response_type != 'out_of_scope'
            }
            
            self.logger.info(f"Processed message in session {session_id}: {response_type}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            error_response = ChatMessage(
                content="I'm sorry, I encountered an error while processing your request. Please try again.",
                role="assistant"
            )
            session.add_message(error_response)
            
            return {
                'message': error_response.content,
                'type': 'error',
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'search_results': [],
                'in_scope': False
            }
    
    def _process_knowledge_query(self, query: str) -> Tuple[str, str, List[Dict[str, Any]]]:
        """Process a knowledge query and generate response."""
        # Determine query type and search strategy
        query_type = self._classify_query(query)
        
        if query_type == 'person_lookup':
            return self._handle_person_lookup(query)
        elif query_type == 'role_lookup':
            return self._handle_role_lookup(query)
        elif query_type == 'department_lookup':
            return self._handle_department_lookup(query)
        elif query_type == 'general_search':
            return self._handle_general_search(query)
        else:
            return self._handle_general_search(query)
    
    def _classify_query(self, query: str) -> str:
        """Classify the type of query to determine search strategy."""
        query_lower = query.lower()
        
        # Person lookup patterns
        person_patterns = [
            r'who is (\w+)',
            r'find (\w+)',
            r'tell me about (\w+)',
            r'(\w+)\'s (contact|email|phone)',
        ]
        
        for pattern in person_patterns:
            if re.search(pattern, query_lower):
                return 'person_lookup'
        
        # Role lookup patterns
        role_patterns = [
            r'who is the (ceo|cto|cfo|director|manager)',
            r'(ceo|cto|cfo|director|manager)',
            r'head of (\w+)',
            r'lead (\w+)',
        ]
        
        for pattern in role_patterns:
            if re.search(pattern, query_lower):
                return 'role_lookup'
        
        # Department lookup patterns
        department_patterns = [
            r'(engineering|marketing|sales|hr|finance|operations) team',
            r'people in (\w+)',
            r'(\w+) department',
        ]
        
        for pattern in department_patterns:
            if re.search(pattern, query_lower):
                return 'department_lookup'
        
        return 'general_search'
    
    def _handle_person_lookup(self, query: str) -> Tuple[str, str, List[Dict[str, Any]]]:
        """Handle queries looking for specific people."""
        # Extract person name from query
        name_match = re.search(r'(?:who is|find|about)\s+(\w+(?:\s+\w+)?)', query.lower())
        if name_match:
            name = name_match.group(1)
            profile = self.knowledge_service.get_profile_by_name(name)
            
            if profile:
                response = self._format_profile_response(profile)
                return response, 'person_found', [profile]
        
        # Fallback to general search
        return self._handle_general_search(query)
    
    def _handle_role_lookup(self, query: str) -> Tuple[str, str, List[Dict[str, Any]]]:
        """Handle queries looking for people by role."""
        # Extract role from query
        role_patterns = [
            r'who is the (\w+)',
            r'(ceo|cto|cfo|director|manager)',
            r'head of (\w+)',
        ]
        
        role = None
        for pattern in role_patterns:
            match = re.search(pattern, query.lower())
            if match:
                role = match.group(1)
                break
        
        if role:
            profiles = self.knowledge_service.get_profiles_by_role(role)
            if profiles:
                if len(profiles) == 1:
                    response = self._format_profile_response(profiles[0])
                    return response, 'role_found', profiles
                else:
                    response = self._format_multiple_profiles_response(profiles, f"people with role '{role}'")
                    return response, 'multiple_found', profiles
        
        # Fallback to general search
        return self._handle_general_search(query)
    
    def _handle_department_lookup(self, query: str) -> Tuple[str, str, List[Dict[str, Any]]]:
        """Handle queries looking for people by department."""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated department extraction
        departments = self.knowledge_service.get_departments()
        
        query_lower = query.lower()
        for dept in departments:
            if dept.lower() in query_lower:
                # Search for profiles in this department
                results = self.knowledge_service.search_knowledge(
                    query=dept,
                    content_types=['profile'],
                    limit=10
                )
                
                if results:
                    response = self._format_multiple_profiles_response(results, f"people in {dept}")
                    return response, 'department_found', results
        
        # Fallback to general search
        return self._handle_general_search(query)
    
    def _handle_general_search(self, query: str) -> Tuple[str, str, List[Dict[str, Any]]]:
        """Handle general search queries."""
        results = self.knowledge_service.search_knowledge(
            query=query,
            search_type='hybrid',
            limit=5
        )
        
        if results:
            if len(results) == 1 and results[0]['content_type'] == 'profile':
                response = self._format_profile_response(results[0])
                return response, 'search_found', results
            else:
                response = self._format_search_results_response(results, query)
                return response, 'search_results', results
        else:
            response = self._get_random_template('no_results')
            return response, 'no_results', []
    
    def _format_profile_response(self, profile: Dict[str, Any]) -> str:
        """Format a response for a single profile."""
        name = profile.get('name', 'Unknown')
        role = profile.get('role', '')
        department = profile.get('department', '')
        bio = profile.get('bio', '')
        contact = profile.get('contact', {})
        
        response_parts = [f"**{name}**"]
        
        if role:
            response_parts.append(f"*Role:* {role}")
        
        if department:
            response_parts.append(f"*Department:* {department}")
        
        if bio:
            # Truncate bio if too long
            bio_text = bio[:200] + "..." if len(bio) > 200 else bio
            response_parts.append(f"*About:* {bio_text}")
        
        if contact:
            contact_info = []
            if contact.get('email'):
                contact_info.append(f"Email: {contact['email']}")
            if contact.get('phone'):
                contact_info.append(f"Phone: {contact['phone']}")
            
            if contact_info:
                response_parts.append(f"*Contact:* {', '.join(contact_info)}")
        
        return "\\n\\n".join(response_parts)
    
    def _format_multiple_profiles_response(self, profiles: List[Dict[str, Any]], description: str) -> str:
        """Format a response for multiple profiles."""
        response_parts = [f"I found {len(profiles)} {description}:"]
        
        for profile in profiles[:5]:  # Limit to 5 profiles
            name = profile.get('name', 'Unknown')
            role = profile.get('role', '')
            
            if role:
                response_parts.append(f"• **{name}** - {role}")
            else:
                response_parts.append(f"• **{name}**")
        
        if len(profiles) > 5:
            response_parts.append(f"... and {len(profiles) - 5} more")
        
        response_parts.append("\\nWould you like more details about any specific person?")
        
        return "\\n".join(response_parts)
    
    def _format_search_results_response(self, results: List[Dict[str, Any]], query: str) -> str:
        """Format a response for general search results."""
        response_parts = [f"I found {len(results)} results for '{query}':"]
        
        for result in results[:3]:  # Limit to 3 results
            title = result.get('title', 'Unknown')
            content_type = result.get('content_type', '')
            score = result.get('score', 0)
            
            response_parts.append(f"• **{title}** ({content_type}) - Relevance: {score:.2f}")
        
        if len(results) > 3:
            response_parts.append(f"... and {len(results) - 3} more results")
        
        return "\\n".join(response_parts)
    
    def _get_random_template(self, template_type: str) -> str:
        """Get a random response template."""
        import random
        templates = self.response_templates.get(template_type, ["I'm not sure how to help with that."])
        return random.choice(templates)
    
    def get_session_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the full history of a chat session."""
        session = self.get_session(session_id)
        return session.to_dict() if session else None
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a chat session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"Cleared chat session: {session_id}")
            return True
        return False
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        return list(self.sessions.keys())
    
    def provide_feedback(self, session_id: str, message_index: int, feedback: str) -> bool:
        """
        Provide feedback on a chat response.
        
        Args:
            session_id: Chat session ID
            message_index: Index of the message to provide feedback on
            feedback: 'helpful' or 'not_helpful'
        """
        try:
            session = self.get_session(session_id)
            if session and 0 <= message_index < len(session.messages):
                # Log feedback for analytics
                # In a real implementation, you'd store this in the database
                self.logger.info(f"Received feedback '{feedback}' for session {session_id}, message {message_index}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error providing feedback: {e}")
            return False
