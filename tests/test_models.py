"""
Tests for AI model implementations.
"""
import os
import sys
import json
import logging
import unittest
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aichat.models import DeepSeekModel, MistralModel
from aichat.learning.data_collector import DataCollector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")
os.makedirs(TEST_DATA_DIR, exist_ok=True)

class BaseModelTest(unittest.TestCase):
    """Base test class for model tests."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before any tests in this class run."""
        cls.data_collector = DataCollector(data_dir=os.path.join(TEST_DATA_DIR, "test_sessions"))
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_messages = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you! How can I help you today?"},
            {"role": "user", "content": "What's the weather like today?"}
        ]
    
    def assert_valid_response(self, response: str) -> None:
        """Assert that a response is valid."""
        self.assertIsInstance(response, str)
        self.assertGreater(len(response.strip()), 0)
        self.assertNotIn("Error:", response)


class TestDeepSeekModel(BaseModelTest):
    """Tests for the DeepSeek model."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        super().setUp()
        self.model = DeepSeekModel(
            data_collector=self.data_collector,
            data_dir=os.path.join(TEST_DATA_DIR, "deepseek"),
            temperature=0.2,  # Use lower temperature for more deterministic responses
            max_tokens=100
        )
    
    def test_generate_response(self):
        """Test generating a response."""
        response = self.model.generate_response(
            "What is the capital of France?",
            task="default"
        )
        self.assert_valid_response(response)
        logger.info(f"DeepSeek response: {response[:100]}...")
    
    def test_conversation_history(self):
        """Test generating a response with conversation history."""
        response = self.model.generate_response(
            "What was the first thing I asked?",
            conversation_history=self.test_messages,
            task="default"
        )
        self.assert_valid_response(response)
        logger.info(f"DeepSeek conversation history response: {response[:100]}...")
    
    def test_system_prompt(self):
        """Test generating a response with a system prompt."""
        response = self.model.generate_response(
            "What is 2+2?",
            task="analytical"
        )
        self.assert_valid_response(response)
        logger.info(f"DeepSeek system prompt response: {response[:100]}...")


class TestMistralModel(BaseModelTest):
    """Tests for the Mistral model."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        super().setUp()
        self.model = MistralModel(
            data_collector=self.data_collector,
            data_dir=os.path.join(TEST_DATA_DIR, "mistral"),
            temperature=0.2,  # Use lower temperature for more deterministic responses
            max_tokens=100
        )
    
    def test_generate_response(self):
        """Test generating a response."""
        response = self.model.generate_response(
            "What is the capital of France?",
            task="default"
        )
        self.assert_valid_response(response)
        logger.info(f"Mistral response: {response[:100]}...")
    
    def test_conversation_history(self):
        """Test generating a response with conversation history."""
        response = self.model.generate_response(
            "What was the first thing I asked?",
            conversation_history=self.test_messages,
            task="default"
        )
        self.assert_valid_response(response)
        logger.info(f"Mistral conversation history response: {response[:100]}...")
    
    def test_system_prompt(self):
        """Test generating a response with a system prompt."""
        response = self.model.generate_response(
            "What is 2+2?",
            task="analytical"
        )
        self.assert_valid_response(response)
        logger.info(f"Mistral system prompt response: {response[:100]}...")


if __name__ == "__main__":
    unittest.main()
