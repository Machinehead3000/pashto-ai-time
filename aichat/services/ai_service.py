"""
AI Service for handling interactions with AI models.
"""
import json
import logging
from typing import Dict, List, Optional, AsyncGenerator, Union
import aiohttp
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

logger = logging.getLogger(__name__)

class AIService(QObject):
    """Service for handling AI model interactions."""
    
    # Signals
    response_received = pyqtSignal(str)  # Emitted when a new token is received
    response_complete = pyqtSignal(dict)  # Emitted when the full response is complete
    error_occurred = pyqtSignal(str)  # Emitted when an error occurs
    
    def __init__(self, api_key: str = None, base_url: str = "https://openrouter.ai/api/v1"):
        """Initialize the AI service.
        
        Args:
            api_key: OpenRouter API key
            base_url: Base URL for the OpenRouter API
        """
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        self.current_request = None
        
    async def initialize(self):
        """Initialize the AI service session."""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str = "openai/gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Generate a response from the AI model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            stream: Whether to stream the response
            
        Yields:
            Response chunks as they are received
            
        Raises:
            Exception: If the API request fails
        """
        if not self.api_key:
            error_msg = "API key is not set"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return
        
        if not self.session:
            await self.initialize()
        
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://pashto-ai.app",
            "X-Title": "Pashto AI"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        try:
            async with self.session.post(
                url, 
                headers=headers, 
                json=payload,
                timeout=aiohttp.ClientTimeout(total=300)  # 5 minute timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    error_msg = f"API request failed with status {response.status}: {error_text}"
                    logger.error(error_msg)
                    self.error_occurred.emit(error_msg)
                    return
                
                if stream:
                    buffer = ""
                    async for line in response.content:
                        if line.startswith(b'data: '):
                            line = line[6:].strip()
                            if line == b'[DONE]':
                                break
                                
                            try:
                                data = json.loads(line)
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content = delta['content']
                                        buffer += content
                                        yield content
                                        
                                        # Emit the response so far
                                        self.response_received.emit(buffer)
                            except json.JSONDecodeError as e:
                                logger.error(f"Error parsing response: {e}")
                                continue
                    
                    # Emit the complete response
                    self.response_complete.emit({
                        "content": buffer,
                        "model": model,
                        "tokens_used": len(buffer.split())  # Rough estimate
                    })
                else:
                    data = await response.json()
                    if 'choices' in data and len(data['choices']) > 0:
                        content = data['choices'][0]['message']['content']
                        self.response_received.emit(content)
                        self.response_complete.emit({
                            "content": content,
                            "model": model,
                            "tokens_used": data.get('usage', {}).get('total_tokens', 0)
                        })
                        
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
            raise
    
    @pyqtSlot(str, str, float, int, bool)
    def generate_response_async(
        self, 
        messages_json: str, 
        model: str = "openai/gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = True
    ):
        """Qt slot for async response generation.
        
        Args:
            messages_json: JSON string of messages
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            stream: Whether to stream the response
        """
        import asyncio
        import json
        
        try:
            messages = json.loads(messages_json)
            
            async def run():
                try:
                    async for chunk in self.generate_response(
                        messages, model, temperature, max_tokens, stream
                    ):
                        pass  # Signals are emitted within generate_response
                except Exception as e:
                    logger.error(f"Error in async response generation: {e}", exc_info=True)
            
            asyncio.create_task(run())
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid messages format: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        except Exception as e:
            error_msg = f"Failed to start response generation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
    
    async def list_models(self) -> List[Dict[str, any]]:
        """List available models from the API.
        
        Returns:
            List of available models with their details
            
        Raises:
            Exception: If the API request fails
        """
        if not self.api_key:
            error_msg = "API key is not set"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return []
        
        if not self.session:
            await self.initialize()
        
        url = f"{self.base_url}/models"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.get(
                url, 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    error_msg = f"Failed to fetch models: {response.status} - {error_text}"
                    logger.error(error_msg)
                    self.error_occurred.emit(error_msg)
                    return []
                
                data = await response.json()
                return data.get("data", [])
                
        except Exception as e:
            error_msg = f"Error listing models: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
            return []
    
    def set_api_key(self, api_key: str):
        """Set the API key for the service.
        
        Args:
            api_key: The API key to use for authentication
        """
        self.api_key = api_key
        logger.info("API key updated")
    
    def is_authenticated(self) -> bool:
        """Check if the service has an API key.
        
        Returns:
            bool: True if an API key is set, False otherwise
        """
        return bool(self.api_key)
