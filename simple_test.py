"""
Simple test script to verify model functionality without PyTorch.
"""
import os
import sys
import logging
from pathlib import Path

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

def test_deepseek_model():
    """Test the DeepSeek model with mock data collector."""
    logger.info("\n=== Testing DeepSeek Model ===")
    
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
    try:
        response = model.generate_response("Hello, how are you?", task="default")
        logger.info(f"✅ DeepSeek response: {response[:100]}...")
        return True
    except Exception as e:
        logger.error(f"❌ DeepSeek test failed: {str(e)}")
        return False

def test_mistral_model():
    """Test the Mistral model with mock data collector."""
    logger.info("\n=== Testing Mistral Model ===")
    
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
    try:
        response = model.generate_response("Hello, how are you?", task="default")
        logger.info(f"✅ Mistral response: {response[:100]}...")
        return True
    except Exception as e:
        logger.error(f"❌ Mistral test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    deepseek_ok = test_deepseek_model()
    mistral_ok = test_mistral_model()
    
    logger.info("\n=== Test Summary ===")
    logger.info(f"DeepSeek: {'✅ PASSED' if deepseek_ok else '❌ FAILED'}")
    logger.info(f"Mistral:  {'✅ PASSED' if mistral_ok else '❌ FAILED'}")
    
    if deepseek_ok and mistral_ok:
        logger.info("\n🎉 All tests passed!")
        return 0
    else:
        logger.info("\n❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
