"""
Mistral model implementation with enhanced configuration and streaming support.
"""
import json
import logging
import requests
from typing import List, Dict, Any, Optional, Callable, Iterator, Union
from pathlib import Path

from ..learning.data_collector import DataCollector
from .base import BaseAIModel

logger = logging.getLogger(__name__)

class MistralModel(BaseAIModel):
    """Implementation of the Mistral AI model with learning capabilities."""
    
    def __init__(
        self, 
        data_collector: Optional[DataCollector] = None, 
        data_dir: Union[str, Path] = None,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """Initialize the Mistral model with data collection.
        
        Args:
            data_collector: Optional DataCollector instance. If None, a new one will be created.
            data_dir: Directory to store training data (only used if data_collector is None)
            api_key: Optional API key for Mistral API
            **kwargs: Additional configuration overrides
        """
        # Initialize with Mistral-specific config
        config = {
            'url': "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
            'api_key': api_key or "hf_community",
            'supports_streaming': False,  # Community endpoint doesn't support streaming
            **kwargs
        }
        
        super().__init__("mistral-7b", config)
        
        # Initialize data collector
        self.data_collector = data_collector or DataCollector(data_dir or "training_data")
        self.current_session_id: Optional[str] = None
        self._response_handler: Optional[Callable] = None
        
        # Set up API headers
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.config.get('api_key'):
            self.headers['Authorization'] = f"Bearer {self.config['api_key']}"
        
        # Start a new conversation by default
        self.start_new_conversation()
    
    @property
    def model_id(self) -> str:
        return "mistral-7b-instruct-v0.2"
    
    def _call_model(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Call the Mistral API to generate a response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters for the API call
            
        Returns:
            The generated response text
        """
        # Format messages for Mistral's instruction format
        prompt = self._format_messages(messages)
        
        # Prepare the request payload
        payload = {
            'inputs': prompt,
            'parameters': {
                'temperature': self.config.get('temperature', 0.7),
                'max_new_tokens': self.config.get('max_tokens', 2048),
                'top_p': self.config.get('top_p', 0.9),
                'return_full_text': False,
                **{k: v for k, v in kwargs.items() if k != 'messages'}
            }
        }
        
        try:
            # Make the API request
            response = requests.post(
                self.config['url'],
                headers=self.headers,
                json=payload,
                timeout=60  # 60 seconds timeout
            )
            response.raise_for_status()
            
            # Extract and return the response text
            result = response.json()
            if isinstance(result, list) and len(result) > 0 and 'generated_text' in result[0]:
                return result[0]['generated_text'].strip()
            return ""
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for the Mistral instruction format."""
        formatted = []
        for msg in messages:
            role = "User" if msg["role"] == "user" else "AI"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted) + "\nAI:"
    
    def generate_response(
        self,
        message: str,
        **kwargs
    ) -> str:
        """Generate a response to the given message with conversation history.
        
        Args:
            message: The user's message
            **kwargs: Additional parameters for the generation
                - conversation_history: List of previous messages in the conversation
                - stream: If True, returns a generator that yields response chunks
                - task: The type of task (default, code, creative, analytical)
                
        Returns:
            The AI's response as a string (streaming not supported for Mistral community endpoint)
        """
        # Get conversation history if provided
        conversation_history = kwargs.pop('conversation_history', None)
        
        # Prepare messages with proper formatting
        messages = self._prepare_messages(
            message=message,
            task=kwargs.get('task', 'default'),
            conversation_history=conversation_history
        )
        
        # Handle streaming (not supported by community endpoint)
        if kwargs.get('stream', False):
            logger.warning("Streaming not supported for Mistral community endpoint")
            
        # Process user input for data collection
        user_input = self._process_user_input(messages)
        
        try:
            # Call the model
            response = self._call_model(messages, **kwargs)
            
            # Log the interaction
            if user_input and self.data_collector:
                interaction_data = {
                    "model_id": self.model_id,
                    "model_params": {
                        "temperature": self.config.get('temperature'),
                        "max_tokens": self.config.get('max_tokens')
                    },
                    **kwargs
                }
                self.data_collector.add_interaction(
                    user_input=user_input,
                    model_response=response,
                    **interaction_data
                )
            
            # Notify response handler if set
            if self._response_handler:
                self._response_handler(response, is_user=False)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            error_msg = f"Error: {str(e)}"
            
            # Log the error
            if user_input and self.data_collector:
                self.data_collector.add_interaction(
                    user_input=user_input,
                    model_response=error_msg,
                    model_id=self.model_id,
                    error=str(e),
                    **kwargs
                )
            
            # Notify response handler if set
            if self._response_handler:
                self._response_handler(error_msg, is_user=False)
            
            return error_msg
    
    def start_new_conversation(self, system_prompt: str = "") -> None:
        """Start a new conversation session for data collection."""
        self.current_session_id = self.data_collector.start_new_conversation(
            model_id=self.model_id,
            system_prompt=system_prompt
        )
    
    def save_conversation(
        self,
        rating: Optional[int] = None,
        comments: Optional[str] = None,
        **feedback_kwargs
    ) -> Optional[str]:
        """Save the current conversation with optional feedback."""
        if not self.current_session_id:
            logger.warning("No active conversation to save")
            return None
            
        return self.data_collector.save_session(
            session_id=self.current_session_id,
            rating=rating,
            comments=comments,
            **feedback_kwargs
        )
    
    def set_data_collector(self, data_collector: DataCollector) -> None:
        """Set the data collector for this model."""
        self.data_collector = data_collector
    
    def set_response_handler(self, handler: Callable) -> None:
        """Set the response handler for this model."""
        self._response_handler = handler
    
    def _process_user_input(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Extract and process user input from messages."""
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                return msg.get('content', '').strip()
        return None
    
    def _prepare_messages(
        self,
        message: str,
        task: str = 'default',
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """Prepare messages for the model with proper formatting."""
        messages = []
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add the current message
        messages.append({'role': 'user', 'content': message})
        
        return messages
