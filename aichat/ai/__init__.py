"""
AI Core Module - Advanced AI capabilities for the Pashto AI application.

This module provides the core AI functionality including language understanding,
context management, and advanced processing capabilities.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class AIContext:
    """Represents the context for AI processing."""
    user_id: str
    session_id: str
    conversation_history: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    system_instructions: str
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIContext':
        """Create context from dictionary."""
        return cls(**data)

class AIManager:
    """Manages AI capabilities and processing."""
    
    def __init__(self, memory_manager=None):
        """Initialize the AI manager.
        
        Args:
            memory_manager: Optional memory manager for persistent storage.
        """
        self.memory_manager = memory_manager
        self.contexts: Dict[str, AIContext] = {}
        self.plugins = {}
        
    def create_context(self, user_id: str, session_id: str, **kwargs) -> AIContext:
        """Create a new AI context.
        
        Args:
            user_id: Unique user identifier.
            session_id: Unique session identifier.
            **kwargs: Additional context parameters.
            
        Returns:
            AIContext: The created context.
        """
        context = AIContext(
            user_id=user_id,
            session_id=session_id,
            conversation_history=[],
            user_preferences={},
            system_instructions="",
            **kwargs
        )
        self.contexts[session_id] = context
        return context
    
    def get_context(self, session_id: str) -> Optional[AIContext]:
        """Get context by session ID."""
        return self.contexts.get(session_id)
    
    def update_context(self, session_id: str, **updates) -> bool:
        """Update context attributes.
        
        Args:
            session_id: Session ID to update.
            **updates: Key-value pairs to update in the context.
            
        Returns:
            bool: True if update was successful, False otherwise.
        """
        if session_id not in self.contexts:
            return False
            
        context = self.contexts[session_id]
        for key, value in updates.items():
            if hasattr(context, key):
                setattr(context, key, value)
        return True
    
    def process_input(self, session_id: str, user_input: str, **kwargs) -> Dict[str, Any]:
        """Process user input and generate response.
        
        Args:
            session_id: Session ID for context.
            user_input: User input text.
            **kwargs: Additional processing parameters.
            
        Returns:
            Dict containing response and metadata.
        """
        context = self.get_context(session_id)
        if not context:
            return {
                'success': False,
                'error': 'Session not found',
                'response': 'Session expired. Please start a new conversation.'
            }
            
        # Update conversation history
        context.conversation_history.append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # TODO: Implement actual AI processing
        response = {
            'success': True,
            'response': f"Processed: {user_input}",
            'metadata': {
                'model': 'pashto-ai-v1',
                'tokens_used': len(user_input.split()),
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        # Update conversation history with AI response
        context.conversation_history.append({
            'role': 'assistant',
            'content': response['response'],
            'timestamp': response['metadata']['timestamp']
        })
        
        return response
    
    def register_plugin(self, name: str, plugin: Any) -> bool:
        """Register an AI plugin.
        
        Args:
            name: Plugin name.
            plugin: Plugin instance.
            
        Returns:
            bool: True if registration was successful.
        """
        if not hasattr(plugin, 'process') or not callable(plugin.process):
            logger.warning(f"Plugin {name} is missing required 'process' method")
            return False
            
        self.plugins[name] = plugin
        logger.info(f"Registered plugin: {name}")
        return True
    
    def get_plugin(self, name: str) -> Optional[Any]:
        """Get a registered plugin by name."""
        return self.plugins.get(name)

# Singleton instance
ai_manager = AIManager()

def get_ai_manager() -> AIManager:
    """Get the global AI manager instance."""
    return ai_manager
