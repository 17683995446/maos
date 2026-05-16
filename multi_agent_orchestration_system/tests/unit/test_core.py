"""
Unit Tests - Core Module Tests
===============================

Tests for core abstractions and base classes.
"""

import unittest
from datetime import datetime

from multi_agent_orchestration_system.core_abstractions import (
    BaseAgent,
    AgentOperationalStatus,
    AgentMessageType,
    AgentMessage,
    AgentCapabilities
)


class TestAgentCapabilities(unittest.TestCase):
    """Test agent capabilities functionality"""
    
    def test_capability_checking(self):
        """Test capability has and has_all methods"""
        capabilities = AgentCapabilities(
            capability_list=['data_cleaning', 'analysis', 'reporting']
        )
        
        self.assertTrue(capabilities.has_capability('data_cleaning'))
        self.assertFalse(capabilities.has_capability('unknown_capability'))
        self.assertTrue(capabilities.has_all_capabilities(['data_cleaning', 'analysis']))
        self.assertFalse(capabilities.has_all_capabilities(['data_cleaning', 'unknown']))


class TestAgentMessage(unittest.TestCase):
    """Test agent message functionality"""
    
    def test_message_creation(self):
        """Test basic message creation"""
        message = AgentMessage(
            sender_agent_name='agent_1',
            receiver_agent_names=['agent_2'],
            message_type=AgentMessageType.TASK_REQUEST,
            payload=None
        )
        
        self.assertEqual(message.sender_agent_name, 'agent_1')
        self.assertEqual(message.receiver_agent_names, ['agent_2'])
        self.assertEqual(message.message_type, AgentMessageType.TASK_REQUEST)
        self.assertIsNotNone(message.message_id)
    
    def test_message_serialization(self):
        """Test message to dict conversion"""
        message = AgentMessage(
            sender_agent_name='sender',
            receiver_agent_names=['receiver'],
            message_type=AgentMessageType.TASK_RESPONSE
        )
        
        message_dict = message.to_dict()
        self.assertIsInstance(message_dict, dict)
        self.assertEqual(message_dict['sender_agent_name'], 'sender')
        self.assertEqual(message_dict['message_type'], 'task_response')


class TestBaseAgent(unittest.TestCase):
    """Test base agent functionality"""
    
    def test_agent_creation_with_valid_name(self):
        """Test agent creation with valid name"""
        agent = BaseAgent(
            agent_name='test_agent',
            capability_list=['test_capability']
        )
        
        self.assertEqual(agent.agent_name, 'test_agent')
        self.assertEqual(agent.agent_status, AgentOperationalStatus.IDLE)
        self.assertIn('test_capability', agent.get_agent_capabilities().capability_list)
    
    def test_agent_creation_with_empty_name_fails(self):
        """Test agent creation with empty name raises error"""
        with self.assertRaises(ValueError):
            BaseAgent(agent_name='')
    
    def test_agent_status_update(self):
        """Test agent status transitions"""
        agent = BaseAgent(agent_name='test_agent')
        
        agent.update_agent_status(AgentOperationalStatus.BUSY)
        self.assertEqual(agent.agent_status, AgentOperationalStatus.BUSY)
        
        agent.update_agent_status(AgentOperationalStatus.IDLE)
        self.assertEqual(agent.agent_status, AgentOperationalStatus.IDLE)
    
    def test_agent_capability_checking(self):
        """Test agent capability methods"""
        agent = BaseAgent(
            agent_name='test_agent',
            capability_list=['capability_1', 'capability_2']
        )
        
        self.assertTrue(agent.get_agent_capabilities().has_capability('capability_1'))
        self.assertFalse(agent.get_agent_capabilities().has_capability('unknown'))


if __name__ == '__main__':
    unittest.main()
