"""
Pytest configuration and fixtures for testing.
"""
import os
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock PyTorch and related imports
MOCK_MODULES = [
    'torch', 'torch.nn', 'torch.optim', 'torch.utils', 'torch.utils.data',
    'transformers', 'transformers.modeling_utils', 'transformers.tokenization_utils',
    'transformers.trainer', 'transformers.training_args', 'accelerate', 'sentencepiece'
]

for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = MagicMock()

# Import the mock model trainer
from tests.mocks.model_trainer import mock_module as mock_model_trainer
sys.modules['aichat.learning.model_trainer'] = mock_model_trainer

# Test data
TEST_CONFIG = {
    "models": {
        "deepseek": {
            "api_key": "test_deepseek_key",
            "base_url": "https://api.deepseek.com/v1"
        },
        "mistral": {
            "api_key": "test_mistral_key",
            "base_url": "https://api.mistral.ai/v1"
        }
    }
}

@pytest.fixture
def mock_config():
    """Fixture to provide a mock config file."""
    config_path = Path("config/config.json")
    config_path.parent.mkdir(exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(TEST_CONFIG, f)
    return config_path

@pytest.fixture
def mock_env():
    """Fixture to set up mock environment variables."""
    with patch.dict(os.environ, {
        "DEEPSEEK_API_KEY": "test_deepseek_key",
        "MISTRAL_API_KEY": "test_mistral_key",
        "DATA_DIR": "test_data"
    }):
        yield

@pytest.fixture
def mock_requests():
    """Fixture to mock requests for API calls."""
    with patch('requests.Session') as mock_session:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_session.return_value.post.return_value = mock_response
        yield mock_session

@pytest.fixture
def data_collector(tmp_path):
    """Fixture to provide a data collector with a temporary directory."""
    from aichat.learning.data_collector import DataCollector
    return DataCollector(data_dir=str(tmp_path))

@pytest.fixture
def deepseek_model(data_collector):
    """Fixture to provide a DeepSeek model instance."""
    from aichat.models.deepseek import DeepSeekModel
    return DeepSeekModel(
        data_collector=data_collector,
        data_dir="test_data/deepseek",
        temperature=0.2,
        max_tokens=100
    )

@pytest.fixture
def mistral_model(data_collector):
    """Fixture to provide a Mistral model instance."""
    from aichat.models.mistral import MistralModel
    return MistralModel(
        data_collector=data_collector,
        data_dir="test_data/mistral",
        temperature=0.2,
        max_tokens=100
    )
