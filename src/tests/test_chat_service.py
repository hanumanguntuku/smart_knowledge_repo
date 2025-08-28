import unittest
from unittest.mock import MagicMock
from datetime import datetime
from src.services.chat_service import ChatService, ChatSession, ChatMessage

class MockKnowledgeService:
    def __init__(self):
        self.check_scope = MagicMock(return_value=True)
        self.get_profile_by_name = MagicMock(return_value={'name': 'Alice', 'role': 'CEO', 'department': 'Leadership', 'bio': 'CEO bio', 'contact': {'email': 'alice@example.com'}})
        self.get_profiles_by_role = MagicMock(return_value=[{'name': 'Alice', 'role': 'CEO'}])
        self.get_departments = MagicMock(return_value=['Leadership', 'Engineering'])
        self.search_knowledge = MagicMock(return_value=[{'content_type': 'profile', 'name': 'Alice', 'role': 'CEO', 'title': 'Alice', 'score': 0.99}])

class TestChatService(unittest.TestCase):
    def setUp(self):
        self.knowledge_service = MockKnowledgeService()
        self.chat_service = ChatService(self.knowledge_service)

    def test_create_session(self):
        session = self.chat_service.create_session('test1')
        self.assertIsInstance(session, ChatSession)
        self.assertEqual(session.session_id, 'test1')
        self.assertEqual(len(session.messages), 1)  # Welcome message

    def test_get_session(self):
        self.chat_service.create_session('test2')
        session = self.chat_service.get_session('test2')
        self.assertIsNotNone(session)
        self.assertEqual(session.session_id, 'test2')

    def test_process_message_in_scope(self):
        response = self.chat_service.process_message('test3', 'Who is Alice?')
        self.assertIn('message', response)
        self.assertTrue(response['in_scope'])
        self.assertEqual(response['type'], 'person_found')

    def test_process_message_out_of_scope(self):
        self.knowledge_service.check_scope.return_value = False
        response = self.chat_service.process_message('test4', 'What is the weather?')
        self.assertIn('message', response)
        self.assertFalse(response['in_scope'])
        self.assertEqual(response['type'], 'out_of_scope')

    def test_get_session_history(self):
        self.chat_service.create_session('test5')
        history = self.chat_service.get_session_history('test5')
        self.assertIn('messages', history)
        self.assertEqual(history['session_id'], 'test5')

    def test_clear_session(self):
        self.chat_service.create_session('test6')
        result = self.chat_service.clear_session('test6')
        self.assertTrue(result)
        self.assertIsNone(self.chat_service.get_session('test6'))

    def test_get_active_sessions(self):
        self.chat_service.create_session('test7')
        self.chat_service.create_session('test8')
        sessions = self.chat_service.get_active_sessions()
        self.assertIn('test7', sessions)
        self.assertIn('test8', sessions)

    def test_provide_feedback(self):
        self.chat_service.create_session('test9')
        self.chat_service.process_message('test9', 'Who is Alice?')
        result = self.chat_service.provide_feedback('test9', 1, 'helpful')
        self.assertTrue(result)

    def test_handle_general_search_no_results(self):
        self.knowledge_service.search_knowledge.return_value = []
        response = self.chat_service.process_message('test10', 'Nonexistent query')
        self.assertEqual(response['type'], 'no_results')

if __name__ == '__main__':
    unittest.main()