"""Base class for AI model implementations with advanced features."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, Union
from pathlib import Path
import logging
from ..models.user_preferences import UserPreferences
from .model_configs import get_model_config, format_prompt, get_system_prompt

logger = logging.getLogger(__name__)

class BaseAIModel(ABC):
    """Abstract base class for AI model implementations with advanced features."""
    
    def __init__(self, model_name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the AI model.
        
        Args:
            model_name: Name of the model (e.g., 'deepseek-r1', 'mistral-7b')
            config: Optional configuration overrides for the model
        """
        self.model_name = model_name.lower()
        
        # Load base configuration for this model
        self.config = get_model_config(self.model_name)
        
        # Apply any provided config overrides
        if config:
            self.config.update(config)
        
        # Initialize user preferences and personality
        self.user_prefs = UserPreferences()
        self.personality = {}
        self._load_personality()
        
        # Set capabilities from config
        self.supports_streaming = self.config.get('supports_streaming', False)
        self.supports_image = self.config.get('supports_image', False)
        self.supports_voice = self.config.get('supports_voice', False)
        self.supports_code = self.config.get('supports_code', False)
        self.context_window = self.config.get('context_window', 2048)
    
    def _load_personality(self) -> None:
        """Load model personality settings."""
        self.personality = self.user_prefs.get_personality(self.model_name)
        if not self.personality:
            self.personality = {
                'style': 'helpful and professional',
                'tone': 'friendly',
                'expertise_level': 'advanced',
                'explanation_style': self.user_prefs.get_explanation_style(),
                'language_style': 'natural and conversational',
                'emotional_intelligence': 'high',
                'memory_retention': 'persistent'
            }
    
    def set_personality(self, traits: Dict[str, Any]) -> None:
        """Set model personality traits."""
        self.personality.update(traits)
        self.user_prefs.set_personality(self.model_name, self.personality)
    
    def _format_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format messages with personality and user preferences.
        
        Note: This method is deprecated in favor of _prepare_messages.
        Kept for backward compatibility.
        """
        user_name = self.user_prefs.get_user_name()
        style = self.personality.get('style', 'helpful')
        expertise = self.personality.get('expertise_level', 'advanced')
        tone = self.personality.get('tone', 'friendly')
        language_style = self.personality.get('language_style', 'natural')
        
        system_prompt = f"You are a {style} AI assistant with {expertise} expertise. "
        if user_name:
            system_prompt += f"You are talking to {user_name}. "
        system_prompt += f"Maintain a {tone} tone and {language_style} communication style."
        
        # Add memory context if available
        memory_context = self._get_memory_context()
        if memory_context:
            system_prompt += f"\n\nPrevious context: {memory_context}"
        
        formatted_messages = [{"role": "system", "content": system_prompt}]
        formatted_messages.extend(messages)
        return formatted_messages
    
    def _get_memory_context(self) -> Optional[str]:
        """Get relevant memory context for the current conversation."""
        if self.personality.get('memory_retention', 'none') == 'persistent':
            # Implement memory retrieval logic here
            return None
        return None
    
    @abstractmethod
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        on_token: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> str:
        """Generate a response from the model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            on_token: Optional callback function that's called with each token
            **kwargs: Additional model-specific parameters
            
        Returns:
            The full generated response as a string
        """
        formatted_messages = self._format_prompt(messages)
        # Implement in subclass
        pass
    
    @property
    @abstractmethod
    def model_id(self) -> str:
        """Return the model's unique identifier."""
        pass
    
    def get_available_parameters(self) -> Dict[str, Any]:
        """Get available configuration parameters for this model.
        
        Returns:
            Dictionary of parameter names and their default values
        """
        return {
            'temperature': 0.7,
            'max_tokens': 2048,
            'top_p': 1.0,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0,
            'stop_sequences': [],
            'supports_image': self.supports_image,
            'supports_voice': self.supports_voice,
            'supports_code': self.supports_code
        }
    
    def update_parameters(self, **kwargs) -> None:
        """Update model parameters.
        
        Args:
            **kwargs: Key-value pairs of parameters to update
        """
        self.config.update(kwargs)
    
    def create_custom_personality(self, name: str, traits: Dict[str, Any]) -> None:
        """Create a custom personality profile for the model.
        
        Args:
            name: Name of the custom personality
            traits: Dictionary of personality traits
        """
        self.user_prefs.create_custom_personality(name, traits)
    
    def load_custom_personality(self, name: str) -> bool:
        """Load a custom personality profile.
        
        Args:
            name: Name of the custom personality to load
            
        Returns:
            True if personality was loaded successfully, False otherwise
        """
        custom_personalities = self.user_prefs.get_custom_personalities()
        if f"custom_{name}" in custom_personalities:
            self.set_personality(custom_personalities[f"custom_{name}"])
            return True
        return False
