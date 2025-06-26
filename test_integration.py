"""
Integration tests for the Pashto AI application.
This script tests the core functionality without requiring PyTorch.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Mock DataCollector for testing
class MockDataCollector:
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or "test_data"
        self.interactions = []
        self.sessions = {}
        
    def add_interaction(self, **kwargs):
        self.interactions.append(kwargs)
        return True
    
    def start_new_session(self, model_id: str, system_prompt: str = "") -> str:
        session_id = f"test_session_{len(self.sessions) + 1}"
        self.sessions[session_id] = {
            "model_id": model_id,
            "system_prompt": system_prompt,
            "interactions": []
        }
        return session_id
    
    def save_session(self, session_id: str, **kwargs) -> str:
        if session_id in self.sessions:
            self.sessions[session_id].update(kwargs)
            return f"saved_{session_id}"
        return ""

def test_deepseek_model():
    """Test the DeepSeek model with mock data collector."""
    logger.info("Testing DeepSeek model...")
    
    # Import inside function to avoid import errors if deepseek.py has issues
    from aichat.models.deepseek import DeepSeekModel
    
    # Initialize with mock data collector
    data_collector = MockDataCollector()
    model = DeepSeekModel(
        data_collector=data_collector,
        data_dir="test_data/deepseek",
        temperature=0.2,
        max_tokens=50
    )
    
    # Test basic response generation
    response = model.generate_response("Hello, how are you?", task="default")
    logger.info(f"DeepSeek response: {response}")
    
    # Test conversation history
    response = model.generate_response(
        "What was my previous question?",
        conversation_history=[
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"}
        ]
    )
    logger.info(f"DeepSeek conversation response: {response}")
    
    # Verify data collection
    assert len(data_collector.interactions) > 0, "No interactions were recorded"
    logger.info("✓ DeepSeek model tests passed")

def test_mistral_model():
    """Test the Mistral model with mock data collector."""
    logger.info("\nTesting Mistral model...")
    
    # Import inside function to avoid import errors if mistral.py has issues
    from aichat.models.mistral import MistralModel
    
    # Initialize with mock data collector
    data_collector = MockDataCollector()
    model = MistralModel(
        data_collector=data_collector,
        data_dir="test_data/mistral",
        temperature=0.2,
        max_tokens=50
    )
    
    # Test basic response generation
    response = model.generate_response("Hello, how are you?", task="default")
    logger.info(f"Mistral response: {response}")
    
    # Test conversation history
    response = model.generate_response(
        "What was my previous question?",
        conversation_history=[
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"}
        ]
    )
    logger.info(f"Mistral conversation response: {response}")
    
    # Verify data collection
    assert len(data_collector.interactions) > 0, "No interactions were recorded"
    logger.info("✓ Mistral model tests passed")

def main():
    """Run all integration tests."""
    try:
        test_deepseek_model()
        test_mistral_model()
        logger.info("\n✅ All integration tests passed!")
    except Exception as e:
        logger.error(f"\n❌ Test failed: {str(e)}", exc_info=True)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
