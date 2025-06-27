"""
Tests for the memory management system.
"""
import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from aichat.memory.manager import MemoryManager
from aichat.memory.models import (
    Conversation, Message, UserPreferences,
    MessageRole, MessageType, MemoryError
)

class TestMemoryManager(unittest.TestCase):
    """Test cases for the MemoryManager class."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test data
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_memory_"))
        self.manager = MemoryManager(data_dir=self.test_dir)
    
    def tearDown(self):
        """Clean up after each test."""
        # Remove the temporary directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test that the manager initializes correctly."""
        # Test default data directory
        default_manager = MemoryManager()
        self.assertTrue(hasattr(default_manager, 'data_dir'))
        
        # Test custom data directory
        self.assertEqual(self.manager.data_dir, self.test_dir)
        
        # Test that preferences are initialized
        self.assertIsInstance(self.manager.preferences, UserPreferences)
    
    def test_preferences_loading_and_saving(self):
        """Test loading and saving preferences."""
        # Change a preference
        self.manager.update_preferences(theme="light", font_size=14)
        
        # Create a new manager that should load the saved preferences
        new_manager = MemoryManager(data_dir=self.test_dir)
        
        # Verify preferences were saved and loaded correctly
        self.assertEqual(new_manager.preferences.theme, "light")
        self.assertEqual(new_manager.preferences.font_size, 14)
    
    def test_conversation_management(self):
        """Test creating, retrieving, and deleting conversations."""
        # Create a new conversation
        conv = self.manager.create_conversation("Test Conversation")
        self.assertIsNotNone(conv)
        self.assertEqual(conv.title, "Test Conversation")
        
        # Get the conversation
        retrieved = self.manager.get_conversation(conv.id)
        self.assertEqual(conv.id, retrieved.id)
        
        # List conversations
        conversations = self.manager.list_conversations()
        self.assertEqual(len(conversations), 1)
        self.assertEqual(conversations[0].id, conv.id)
        
        # Delete the conversation
        self.assertTrue(self.manager.delete_conversation(conv.id))
        self.assertEqual(len(self.manager.list_conversations()), 0)
    
    def test_message_management(self):
        """Test adding and retrieving messages."""
        # Create a conversation
        conv = self.manager.create_conversation("Test Messages")
        
        # Add a message
        message = self.manager.add_message(
            role=MessageRole.USER,
            content="Hello, world!",
            message_type=MessageType.TEXT,
            conversation_id=conv.id
        )
        
        # Verify the message was added
        conv = self.manager.get_conversation(conv.id)
        self.assertEqual(len(conv.messages), 1)
        self.assertEqual(conv.messages[0].content, "Hello, world!")
        
        # Test searching messages
        results = self.manager.search_messages("world")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, message.id)
    
    def test_archiving(self):
        """Test archiving and unarchiving conversations."""
        # Create a conversation
        conv = self.manager.create_conversation("Test Archiving")
        
        # Archive the conversation
        self.manager.archive_conversation(conv.id, True)
        
        # Verify it's archived
        conv = self.manager.get_conversation(conv.id)
        self.assertTrue(conv.is_archived)
        
        # Verify it's excluded from default listing
        self.assertEqual(len(self.manager.list_conversations(include_archived=False)), 0)
        self.assertEqual(len(self.manager.list_conversations(include_archived=True)), 1)
        
        # Unarchive
        self.manager.archive_conversation(conv.id, False)
        self.assertEqual(len(self.manager.list_conversations()), 1)
    
    def test_error_handling(self):
        """Test error conditions and recovery."""
        # Test getting non-existent conversation
        self.assertIsNone(self.manager.get_conversation("nonexistent"))
        
        # Test deleting non-existent conversation
        self.assertFalse(self.manager.delete_conversation("nonexistent"))
        
        # Test adding message to non-existent conversation
        with self.assertRaises(MemoryError):
            self.manager.add_message(
                role=MessageRole.USER,
                content="Test",
                conversation_id="nonexistent"
            )
    
    @patch('aichat.memory.manager.MemoryManager._save_conversations')
    @patch('aichat.memory.manager.MemoryManager._save_preferences')
    def test_atomic_save_handling(self, mock_save_prefs, mock_save_conv):
        """Test that save operations are atomic."""
        # Trigger saves
        self.manager.update_preferences(theme="dark")
        self.manager.create_conversation("Test")
        
        # Verify the save methods were called
        mock_save_prefs.assert_called_once()
        mock_save_conv.assert_called_once()
    
    def test_conversation_ordering(self):
        """Test that conversations are ordered by last update time."""
        # Create conversations with different timestamps
        conv1 = self.manager.create_conversation("First")
        conv1.updated_at = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        
        conv2 = self.manager.create_conversation("Second")
        conv2.updated_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        
        conv3 = self.manager.create_conversation("Third")
        
        # Save the conversations
        self.manager._save_conversations()
        
        # Test the order
        conversations = self.manager.list_conversations()
        self.assertEqual(len(conversations), 3)
        self.assertEqual(conversations[0].title, "Third")  # Most recent
        self.assertEqual(conversations[1].title, "Second")
        self.assertEqual(conversations[2].title, "First")   # Oldest


class TestModels(unittest.TestCase):
    """Test cases for model classes."""
    
    def test_message_serialization(self):
        """Test serialization and deserialization of Message objects."""
        msg = Message(
            role=MessageRole.USER,
            content="Hello, world!",
            message_type=MessageType.TEXT,
            metadata={"test": 123}
        )
        
        # Convert to dict and back
        data = msg.to_dict()
        new_msg = Message.from_dict(data)
        
        self.assertEqual(msg.role, new_msg.role)
        self.assertEqual(msg.content, new_msg.content)
        self.assertEqual(msg.message_type, new_msg.message_type)
        self.assertEqual(msg.metadata, new_msg.metadata)
    
    def test_conversation_serialization(self):
        """Test serialization and deserialization of Conversation objects."""
        conv = Conversation(
            id="test123",
            title="Test Conversation",
            messages=[
                Message(role=MessageRole.USER, content="Hi"),
                Message(role=MessageRole.ASSISTANT, content="Hello!")
            ]
        )
        
        # Convert to dict and back
        data = conv.to_dict()
        new_conv = Conversation.from_dict(data)
        
        self.assertEqual(conv.id, new_conv.id)
        self.assertEqual(conv.title, new_conv.title)
        self.assertEqual(len(conv.messages), len(new_conv.messages))
        self.assertEqual(conv.messages[0].content, new_conv.messages[0].content)
    
    def test_user_preferences_serialization(self):
        """Test serialization and deserialization of UserPreferences."""
        prefs = UserPreferences(
            theme="dark",
            font_size=14,
            font_family="Arial",
            language="en-US",
            custom_styles={"button": "color: blue;"}
        )
        
        # Convert to dict and back
        data = prefs.to_dict()
        new_prefs = UserPreferences.from_dict(data)
        
        self.assertEqual(prefs.theme, new_prefs.theme)
        self.assertEqual(prefs.font_size, new_prefs.font_size)
        self.assertEqual(prefs.font_family, new_prefs.font_family)
        self.assertEqual(prefs.language, new_prefs.language)
        self.assertEqual(prefs.custom_styles, new_prefs.custom_styles)


if __name__ == "__main__":
    unittest.main()
