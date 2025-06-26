"""
Tests for the Mistral model implementation.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

def test_mistral_initialization(mistral_model):
    """Test that the Mistral model initializes correctly."""
    assert mistral_model is not None
    assert hasattr(mistral_model, 'model_id')
    assert hasattr(mistral_model, 'data_collector')
    assert hasattr(mistral_model, 'config')

@patch('aichat.models.mistral.requests.Session')
def test_generate_response(mock_session, mistral_model):
    """Test generating a response from the Mistral model."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test response from Mistral"}}]
    }
    mock_session.return_value.post.return_value = mock_response
    
    # Test the method
    response = mistral_model.generate_response("Hello, how are you?")
    
    # Verify the response
    assert response == "Test response from Mistral"
    
    # Verify the API call was made correctly
    mock_session.return_value.post.assert_called_once()
    args, kwargs = mock_session.return_value.post.call_args
    assert 'https://api.mistral.ai/v1/chat/completions' in args[0]
    assert 'Authorization' in kwargs['headers']
    assert 'application/json' in kwargs['headers']['Content-Type']
    assert kwargs['json']['messages'][0]['content'] == "Hello, how are you?"

def test_generate_response_with_conversation_history(mistral_model):
    """Test generating a response with conversation history."""
    conversation_history = [
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"}
    ]
    
    with patch.object(mistral_model, '_call_model') as mock_call:
        mock_call.return_value = "I'm doing well, thank you!"
        
        response = mistral_model.generate_response(
            "What about you?",
            conversation_history=conversation_history
        )
        
        assert response == "I'm doing well, thank you!"
        
        # Verify the conversation history was included in the API call
        args, kwargs = mock_call.call_args
        messages = args[0]
        assert len(messages) == 4  # System + 3 history messages + new message
        assert messages[0]['role'] == 'system'
        assert messages[1]['content'] == "Hello!"
        assert messages[2]['content'] == "Hi there!"

def test_handle_error_response(mistral_model):
    """Test handling of error responses from the API."""
    with patch('aichat.models.mistral.requests.Session') as mock_session:
        # Setup error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid request"}
        mock_session.return_value.post.return_value = mock_response
        
        # Test error handling
        with pytest.raises(Exception) as exc_info:
            mistral_model.generate_response("Test message")
        
        assert "API request failed" in str(exc_info.value)

def test_data_collection(mistral_model, data_collector, tmp_path):
    """Test that data collection works correctly."""
    with patch.object(mistral_model, '_call_model') as mock_call:
        mock_call.return_value = "Test response"
        
        # Generate a response to trigger data collection
        response = mistral_model.generate_response("Test message")
        
        # Verify the response
        assert response == "Test response"
        
        # Verify data was collected
        interactions = data_collector.interactions
        assert len(interactions) > 0
        
        # Check the last interaction
        last_interaction = interactions[-1]
        assert last_interaction['input'] == "Test message"
        assert last_interaction['output'] == "Test response"
        assert last_interaction['model'] == mistral_model.model_id

def test_system_prompt_handling(mistral_model):
    """Test that system prompts are handled correctly."""
    with patch.object(mistral_model, '_call_model') as mock_call:
        mock_call.return_value = "Response with custom system prompt"
        
        # Test with a custom system prompt
        response = mistral_model.generate_response(
            "Test message",
            system_prompt="You are a helpful assistant."
        )
        
        # Verify the system prompt was included in the API call
        args, kwargs = mock_call.call_args
        messages = args[0]
        assert messages[0]['role'] == 'system'
        assert "helpful assistant" in messages[0]['content']

def test_temperature_and_max_tokens(mistral_model):
    """Test that temperature and max_tokens parameters are passed correctly."""
    with patch.object(mistral_model, '_call_model') as mock_call:
        mock_call.return_value = "Response with custom parameters"
        
        # Test with custom parameters
        mistral_model.temperature = 0.8
        mistral_model.max_tokens = 200
        
        mistral_model.generate_response("Test message")
        
        # Verify the parameters were included in the API call
        args, kwargs = mock_call.call_args
        call_kwargs = args[1] if len(args) > 1 else {}
        
        assert call_kwargs.get('temperature') == 0.8
        assert call_kwargs.get('max_tokens') == 200

def test_streaming_response(mistral_model):
    """Test streaming response functionality."""
    # Mock the streaming response
    mock_response = MagicMock()
    mock_response.iter_lines.return_value = [
        b'data: {"choices": [{"delta": {"content": "Stream"}}]}',
        b'data: {"choices": [{"delta": {"content": "ing "}}]}',
        b'data: {"choices": [{"delta": {"content": "response"}}]}',
        b'data: [DONE]'
    ]
    
    with patch('aichat.models.mistral.requests.Session') as mock_session:
        mock_session.return_value.post.return_value = mock_response
        
        # Test streaming
        responses = list(mistral_model.generate_response("Test message", stream=True))
        
        # Verify the streaming response
        assert len(responses) == 3
        assert responses[0] == "Stream"
        assert responses[1] == "ing "
        assert responses[2] == "response"
