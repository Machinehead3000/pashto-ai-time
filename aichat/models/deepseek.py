"""
DeepSeek model implementation with learning capabilities.
"""
import json
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Union, Iterator

from ..learning.data_collector import DataCollector
from .base import BaseAIModel

logger = logging.getLogger(__name__)

class DeepSeekModel(BaseAIModel):
    """Implementation of the DeepSeek AI model with learning capabilities."""
    
    def __init__(
        self, 
        data_collector: Optional[DataCollector] = None, 
        data_dir: Union[str, Path] = None,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """Initialize the DeepSeek model with data collection.
        
        Args:
            data_collector: Optional DataCollector instance. If None, a new one will be created.
            data_dir: Directory to store training data (only used if data_collector is None)
            api_key: Optional API key for DeepSeek API
            **kwargs: Additional configuration overrides
        """
        # Initialize with DeepSeek-specific config
        config = {
            'url': "https://api.deepseek.com/v1/chat/completions",
            'api_key': api_key,
            'model': 'deepseek-r1',
            'supports_streaming': True,
            'supports_image': False,
            'supports_voice': False,
            'supports_code': True,
            'context_window': 4096,
            **kwargs
        }
        
        super().__init__("deepseek-r1", config)
        
        # Initialize data collector
        self.data_collector = data_collector or DataCollector(data_dir or "training_data")
        self.current_session_id: Optional[str] = None
        self._response_handler: Optional[Callable] = None
        self.system_prompt = ""
        self.temperature = 0.7
        self.max_tokens = 2000
        
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
        """Return the model's unique identifier."""
        return "deepseek-r1"
        
    def _call_model(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Call the DeepSeek API to generate a response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters for the API call
                - temperature: Optional float between 0 and 1
                - max_tokens: Optional integer for max tokens to generate
                - top_p: Optional float for nucleus sampling
                - n: Optional integer for number of completions
                - stop: Optional string or list of strings to stop generation
                - presence_penalty: Optional float for presence penalty
                - frequency_penalty: Optional float for frequency penalty
            
        Returns:
            The generated response text
        """
        try:
            # Prepare the request payload with default values
            payload = {
                'model': self.config.get('model', 'deepseek-r1'),
                'messages': messages,
                'stream': False,
            }
            
            # Add optional parameters if provided
            optional_params = [
                'temperature', 'max_tokens', 'top_p', 'n', 'stop',
                'presence_penalty', 'frequency_penalty'
            ]
            for param in optional_params:
                if param in kwargs:
                    payload[param] = kwargs[param]
            
            # Log the API request for debugging
            logger.debug(f"Making API request to {self.config['url']} with payload: {json.dumps(payload, indent=2)}")
            
            # Make the API request
            response = requests.post(
                self.config['url'],
                headers=self.headers,
                json=payload,
                timeout=kwargs.get('timeout', 60)
            )
            
            # Log the response status and headers for debugging
            logger.debug(f"API response status: {response.status_code}")
            logger.debug(f"API response headers: {dict(response.headers)}")
            
            # Check for errors
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            
            # Log the full response for debugging
            logger.debug(f"API response data: {json.dumps(response_data, indent=2)}")
            
            # Extract the response text
            if 'choices' in response_data and len(response_data['choices']) > 0:
                return response_data['choices'][0]['message']['content']
            else:
                error_msg = "No choices in API response"
                logger.error(f"{error_msg}. Response: {response_data}")
                raise ValueError(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Error making request to DeepSeek API: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f" (Details: {error_detail})"
                except:
                    error_msg += f" (Status: {e.response.status_code} - {e.response.text})"
            logger.error(error_msg)
            raise Exception(f"Failed to generate response: {error_msg}")
        except json.JSONDecodeError as e:
            error_msg = f"Error decoding API response: {str(e)}"
            logger.error(f"{error_msg}. Response text: {getattr(response, 'text', 'No response text')}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error processing DeepSeek API response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)
    
    def stream_response(self, messages: List[Dict[str, str]], on_token: Callable[[str], None], **kwargs) -> str:
        """Stream the model's response token by token.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            on_token: Callback function that gets called with each token
            **kwargs: Additional parameters for the API call
            
        Yields:
            Response chunks as they are received
            
        Returns:
            The full generated response
        """
        if not self.supports_streaming:
            raise NotImplementedError("Streaming not supported by this model")
            
        # Prepare the streaming request payload
        payload = {
            'model': self.model_id,
            'messages': messages,
            'temperature': self.config.get('temperature', 0.7),
            'max_tokens': self.config.get('max_tokens', 2048),
            'stream': True,
            **{k: v for k, v in kwargs.items() if k not in ['stream', 'messages']}
        }
        
        full_response = ""
        try:
            with requests.post(
                self.config['url'],
                headers={**self.headers, 'Accept': 'text/event-stream'},
                json=payload,
                stream=True,
                timeout=60
            ) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            chunk = line[6:].strip()
                            if chunk == '[DONE]':
                                break
                                
                            try:
                                data = json.loads(chunk)
                                if 'choices' in data and data['choices']:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        token = delta['content']
                                        if on_token:
                                            on_token(token)
                                        full_response += token
                            except json.JSONDecodeError:
                                continue
                                
        except requests.exceptions.RequestException as e:
            logger.error(f"Streaming request failed: {e}")
            raise Exception(f"Failed to stream response: {str(e)}")
            
        return full_response
        
    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format messages for the DeepSeek API."""
        return [
            {"role": msg["role"], "content": str(msg["content"])}
            for msg in messages
        ]
        
    def _process_user_input(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Extract and process user input from messages."""
        # Last user message is the most recent input
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                return str(msg.get('content', ''))
        return None
        
    def start_new_conversation(self, system_prompt: str = "") -> None:
        """Start a new conversation session."""
        if system_prompt:
            self.system_prompt = system_prompt
        if hasattr(self, 'data_collector'):
            self.current_session_id = self.data_collector.start_new_conversation(
                system_prompt=system_prompt
            )
            logger.info(f"Started new conversation session: {self.current_session_id}")
            
    def generate_response(
        self,
        messages: Union[str, List[Dict[str, str]]],
        on_token: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> str:
        """Generate a response from the model.
        
        Args:
            messages: Either a string or list of message dictionaries
            on_token: Optional callback for streaming responses
            **kwargs: Additional parameters for the API call
                - system_prompt: Optional system prompt to use for this request
                - temperature: Optional float between 0 and 1
                - max_tokens: Optional integer for max tokens to generate
                - conversation_history: Optional list of previous messages
            
        Returns:
            The generated response text
        """
        try:
            # Get system prompt from kwargs or use instance default
            system_prompt = kwargs.pop('system_prompt', self.system_prompt)
            
            # Normalize messages to list format
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]
            
            # Add conversation history if provided
            conversation_history = kwargs.pop('conversation_history', [])
            if conversation_history:
                messages = conversation_history + messages
            
            # Add system prompt if provided and not already in messages
            if system_prompt and (not messages or messages[0].get('role') != 'system'):
                messages = [{"role": "system", "content": system_prompt}] + messages
            
            # Extract model parameters from kwargs
            model_params = {
                'temperature': kwargs.pop('temperature', self.temperature),
                'max_tokens': kwargs.pop('max_tokens', self.max_tokens),
            }
            
            # Format messages for the API
            formatted_messages = self._format_messages(messages)
            
            # Log the interaction if data collector is available
            user_input = self._process_user_input(messages)
            
            # Call the model with combined parameters
            call_kwargs = {**model_params, **kwargs}
            
            if on_token:
                # For streaming responses
                return self.stream_response(
                    messages=formatted_messages,
                    on_token=on_token,
                    **call_kwargs
                )
            else:
                # For non-streaming responses
                response = self._call_model(
                    messages=formatted_messages,
                    **call_kwargs
                )
                
                # Log the interaction if data collector is available
                if user_input and hasattr(self.data_collector, 'log_interaction'):
                    try:
                        self.data_collector.log_interaction(
                            input=user_input,
                            output=response,
                            model=self.model_id,
                            **kwargs
                        )
                    except Exception as e:
                        logger.error(f"Failed to log interaction: {str(e)}")
                
                return response
                
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Log the error if data collector is available
            if hasattr(self.data_collector, 'log_error'):
                try:
                    self.data_collector.log_error(
                        error=error_msg,
                        **kwargs
                    )
                except Exception as e:
                    logger.error(f"Failed to log error: {str(e)}")
            
            raise Exception(error_msg)
        
    def _call_model(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Call the DeepSeek API to generate a response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters for the API call
            
        Returns:
            The generated response text
        """
        # Prepare the request payload
        payload = {
            'model': self.model_id,
            'messages': messages,
            'temperature': self.config.get('temperature', 0.7),
            'max_tokens': self.config.get('max_tokens', 2048),
            'top_p': self.config.get('top_p', 0.9),
            'frequency_penalty': self.config.get('frequency_penalty', 0.0),
            'presence_penalty': self.config.get('presence_penalty', 0.6),
            'stream': False,
            **{k: v for k, v in kwargs.items() if k not in ['stream', 'messages']}
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
            if not isinstance(result, dict):
                logger.error(f"Unexpected API response format: {result}")
                return ""
                
            if 'error' in result:
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                logger.error(f"API error: {error_msg}")
                return f"Error: {error_msg}"
                
            if 'choices' not in result or not result['choices']:
                logger.error(f"No choices in API response: {result}")
                return ""
                
            choice = result['choices'][0]
            if 'message' not in choice or 'content' not in choice['message']:
                logger.error(f"Unexpected choice format: {choice}")
                return ""
                
            return str(choice['message']['content'])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    def start_new_conversation(self, system_prompt: str = "") -> None:
        """Start a new conversation session for data collection.
        
        Args:
            system_prompt: Optional system prompt for the conversation
        """
        if system_prompt:
            self.system_prompt = system_prompt
        self.current_session_id = self.data_collector.start_new_conversation(
            system_prompt=system_prompt
        )
        logger.info(f"Started new conversation session: {self.current_session_id}")
    
    def save_conversation(
        self,
        rating: Optional[int] = None,
        comments: Optional[str] = None,
        **feedback_kwargs
    ) -> Optional[Path]:
        """Save the current conversation with optional feedback.
        
        Args:
            rating: User rating (1-5)
            comments: Optional feedback comments
            **feedback_kwargs: Additional feedback metadata
            
        Returns:
            Path to the saved conversation file, or None if save failed
        """
        if not self.current_session_id:
            logger.warning("No active conversation to save")
            return None
            
        return self.data_collector.save_conversation(rating, comments, **feedback_kwargs)
    
    def _handle_streaming_response(
        self,
        response,
        on_token: Optional[Callable[[str], None]],
        user_input: Optional[str] = None
    ) -> str:
        """Handle a streaming response from the API.
        
        Args:
            response: The streaming HTTP response
            on_token: Callback function for each token
            user_input: The user's input that prompted this response
            
        Returns:
            The full generated response
        """
        full_response = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith("data:"):
                    if "[DONE]" in line_str:
                        break
                    try:
                        data = json.loads(line_str[5:].strip())
                        token = data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                        if token and on_token:
                            on_token(token)
                        full_response += token
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding streaming response: {e}")
                        continue
        return full_response
    
    def set_data_collector(self, data_collector: DataCollector) -> None:
        """Set the data collector for this model.
        
        Args:
            data_collector: DataCollector instance to use for data collection
        """
        self.data_collector = data_collector
        # Start a new conversation with the new data collector
        self.start_new_conversation(self.system_prompt)
    
    def set_response_handler(self, handler: Callable) -> None:
        """Set the response handler for this model.
        
        Args:
            handler: Callable that handles the model's responses
        """
        self._response_handler = handler
    
    def _process_user_input(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Extract and process user input from messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            The user's input text, or None if not found
        """
        # Last user message is the most recent input
        for msg in reversed(messages):
            if msg.get('role') == 'user' and 'content' in msg:
                return str(msg['content'])
        return None

    def _handle_streaming_response(
        self,
        response,
        on_token: Optional[Callable[[str], None]],
        user_input: Optional[str] = None
    ) -> str:
        """Handle a streaming response from the API.
        
        Args:
            response: The streaming HTTP response
            on_token: Callback function for each token
            user_input: The user's input that prompted this response
            
        Returns:
            The full generated response
        """
        full_response = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith("data:"):
                    if "[DONE]" in line_str:
                        break
                    try:
                        data = json.loads(line_str[5:].strip())
                        token = data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                        if token and on_token:
                            on_token(token)
                        full_response += token
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding streaming response: {e}")
                        continue
        return full_response
        
    def set_data_collector(self, data_collector: DataCollector) -> None:
        """Set the data collector for this model.
        
        Args:
            data_collector: DataCollector instance to use for data collection
        """
        self.data_collector = data_collector
        # Start a new conversation with the new data collector
        self.start_new_conversation(self.system_prompt)
    
    def set_response_handler(self, handler: Callable) -> None:
        """Set the response handler for this model.
        
        Args:
            handler: Callable that handles the model's responses
        """
        self._response_handler = handler
