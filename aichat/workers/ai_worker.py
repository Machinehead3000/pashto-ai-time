"""
Worker class for handling AI operations in a separate thread.
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

from aichat.services.ai_service import AIService

logger = logging.getLogger(__name__)

class AIWorker(QObject):
    """Worker for handling AI operations in a background thread."""
    
    # Signals
    response_chunk = pyqtSignal(str)  # Emitted for each chunk of the response
    response_complete = pyqtSignal(dict)  # Emitted when the full response is complete
    error_occurred = pyqtSignal(str)  # Emitted when an error occurs
    models_loaded = pyqtSignal(dict)  # Emitted when models are loaded
    
    def __init__(self, api_key: str = None):
        """Initialize the AI worker.
        
        Args:
            api_key: OpenRouter API key
        """
        super().__init__()
        self.api_key = api_key
        self.ai_service = AIService(api_key=api_key)
        self.loop = None
        self.thread = None
        self.running = False
        
        # Connect signals
        self.ai_service.response_received.connect(self._on_response_received)
        self.ai_service.response_complete.connect(self._on_response_complete)
        self.ai_service.error_occurred.connect(self._on_error_occurred)
    
    def start(self):
        """Start the worker thread."""
        if self.thread is not None:
            return
            
        self.running = True
        self.thread = QThread()
        self.moveToThread(self.thread)
        
        # Connect thread signals
        self.thread.started.connect(self._run_loop)
        self.thread.finished.connect(self._on_finished)
        
        # Start the thread
        self.thread.start()
    
    def stop(self):
        """Stop the worker thread."""
        if not self.thread or not self.running:
            return
            
        self.running = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        # Wait for the thread to finish
        self.thread.quit()
        self.thread.wait()
        self.thread = None
    
    def _run_loop(self):
        """Run the asyncio event loop."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Initialize the AI service
        self.loop.run_until_complete(self.ai_service.initialize())
        
        # Run the event loop
        self.loop.run_forever()
        
        # Cleanup when the loop exits
        self.loop.run_until_complete(self.ai_service.cleanup())
        self.loop.close()
    
    def _on_finished(self):
        """Handle thread finished signal."""
        self.running = False
    
    @pyqtSlot(str)
    def _on_response_received(self, chunk: str):
        """Handle response chunk from AI service.
        
        Args:
            chunk: A chunk of the response
        """
        self.response_chunk.emit(chunk)
    
    @pyqtSlot(dict)
    def _on_response_complete(self, response: dict):
        """Handle complete response from AI service.
        
        Args:
            response: The complete response data
        """
        self.response_complete.emit(response)
    
    @pyqtSlot(str)
    def _on_error_occurred(self, error: str):
        """Handle errors from AI service.
        
        Args:
            error: Error message
        """
        self.error_occurred.emit(error)
    
    @pyqtSlot(str, str, float, int, bool)
    def generate_response(
        self,
        messages_json: str,
        model: str = "openai/gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = True
    ):
        """Generate a response from the AI model.
        
        Args:
            messages_json: JSON string of messages
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            stream: Whether to stream the response
        """
        if not self.running or not self.loop:
            self.error_occurred.emit("Worker is not running")
            return
        
        # Schedule the coroutine in the event loop
        asyncio.run_coroutine_threadsafe(
            self._async_generate_response(messages_json, model, temperature, max_tokens, stream),
            self.loop
        )
    
    async def _async_generate_response(
        self,
        messages_json: str,
        model: str,
        temperature: float,
        max_tokens: int,
        stream: bool
    ):
        """Asynchronously generate a response."""
        try:
            # Parse messages
            messages = json.loads(messages_json)
            
            async def _process_message(self, messages: List[Dict[str, str]], model: str, **kwargs):
                """Process a message with the AI service."""
                try:
                    if not self.ai_service.api_key:
                        raise ValueError("API key is not set. Please set a valid API key.")
                        
                    if not model:
                        raise ValueError("No AI model selected. Please select a model.")
                        
                    if not messages:
                        raise ValueError("No messages to process.")
                        
                    async for chunk in self.ai_service.stream_chat_completion(
                        messages=messages,
                        model=model,
                        **kwargs
                    ):
                        if self._stop_requested:
                            self.response_complete.emit("\n\n[Generation stopped by user]")
                            return
                        self.response_chunk.emit(chunk)
                        
                    full_response = self.ai_service.get_full_response()
                    if not full_response:
                        raise ValueError("No response received from the AI service.")
                        
                    self.response_complete.emit("".join(full_response))
                    
                except Exception as e:
                    error_msg = str(e)
                    if "401" in error_msg:
                        error_msg = "Authentication failed. Please check your API key."
                    elif "404" in error_msg:
                        error_msg = "Model not found. Please select a different model."
                    elif "429" in error_msg:
                        error_msg = "Rate limit exceeded. Please wait before sending more requests."
                    elif "500" in error_msg or "502" in error_msg or "503" in error_msg or "504" in error_msg:
                        error_msg = "Server error. Please try again later."
                    elif "timeout" in str(e).lower():
                        error_msg = "Request timed out. Please check your internet connection and try again."
                        
                    self.error_occurred.emit(error_msg)
                    
            await _process_message(self, messages, model, temperature=temperature, max_tokens=max_tokens, stream=stream)
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid messages format: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
    
    @pyqtSlot()
    def load_models(self):
        """Load available models from the API."""
        if not self.running or not self.loop:
            self.error_occurred.emit("Worker is not running")
            return
        
        # Schedule the coroutine in the event loop
        asyncio.run_coroutine_threadsafe(
            self._async_load_models(),
            self.loop
        )
    
    async def _async_load_models(self):
        """Asynchronously load available models."""
        try:
            models = await self.ai_service.list_models()
            if models:
                # Format models for the UI
                formatted_models = {}
                for model in models:
                    model_id = model.get("id", "")
                    if model_id:
                        formatted_models[model_id] = {
                            "display": model.get("name", model_id),
                            "provider": model.get("pricing", {}).get("provider", {}).get("name", "Unknown"),
                            "description": model.get("description", ""),
                            "context": model.get("context_length", 0),
                            "supports_images": any(
                                m.get("mime_type", "").startswith("image/")
                                for m in model.get("capabilities", {})
                            )
                        }
                
                # Emit the models
                self.models_loaded.emit(formatted_models)
                
        except Exception as e:
            error_msg = f"Error loading models: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
    
    @pyqtSlot(str)
    def set_api_key(self, api_key: str):
        """Set the API key for the AI service.
        
        Args:
            api_key: The API key to use for authentication
        """
        self.api_key = api_key
        self.ai_service.set_api_key(api_key)
        logger.info("API key updated in worker")
