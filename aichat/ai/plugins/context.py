"""
Context Plugin - Manages conversation context and memory.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
from ..plugins import AIPlugin

logger = logging.getLogger(__name__)

class ContextPlugin(AIPlugin):
    """Plugin for managing conversation context and memory."""
    
    def __init__(self, max_history: int = 50, ttl_hours: int = 24):
        """Initialize the context plugin.
        
        Args:
            max_history: Maximum number of messages to keep in history.
            ttl_hours: Time-to-live for context in hours.
        """
        super().__init__(
            name="context",
            description="Manages conversation context and memory",
            version="1.0.0"
        )
        self.max_history = max_history
        self.ttl = timedelta(hours=ttl_hours)
        self.contexts: Dict[str, Dict] = {}
    
    def _cleanup_old_contexts(self):
        """Remove expired contexts."""
        now = datetime.utcnow()
        expired = [
            session_id for session_id, ctx in self.contexts.items()
            if now - datetime.fromisoformat(ctx.get('last_accessed', now.isoformat())) > self.ttl
        ]
        
        for session_id in expired:
            del self.contexts[session_id]
            logger.debug(f"Cleaned up expired context for session: {session_id}")
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get or create context for a session.
        
        Args:
            session_id: Unique session identifier.
            
        Returns:
            Dict containing the session context.
        """
        self._cleanup_old_contexts()
        
        if session_id not in self.contexts:
            self.contexts[session_id] = {
                'created_at': datetime.utcnow().isoformat(),
                'last_accessed': datetime.utcnow().isoformat(),
                'history': [],
                'metadata': {}
            }
        else:
            self.contexts[session_id]['last_accessed'] = datetime.utcnow().isoformat()
            
        return self.contexts[session_id]
    
    def update_context(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update context for a session.
        
        Args:
            session_id: Session identifier.
            updates: Dictionary of updates to apply.
            
        Returns:
            bool: True if update was successful.
        """
        if session_id not in self.contexts:
            return False
            
        ctx = self.get_context(session_id)
        ctx.update(updates)
        ctx['last_accessed'] = datetime.utcnow().isoformat()
        return True
    
    def add_to_history(self, session_id: str, role: str, content: str, **metadata) -> bool:
        """Add a message to the conversation history.
        
        Args:
            session_id: Session identifier.
            role: Role of the message sender ('user', 'assistant', 'system').
            content: Message content.
            **metadata: Additional metadata for the message.
            
        Returns:
            bool: True if the message was added successfully.
        """
        ctx = self.get_context(session_id)
        
        message = {
            'timestamp': datetime.utcnow().isoformat(),
            'role': role,
            'content': content,
            'metadata': metadata or {}
        }
        
        ctx['history'].append(message)
        
        # Trim history if needed
        if len(ctx['history']) > self.max_history:
            ctx['history'] = ctx['history'][-self.max_history:]
            
        return True
    
    def get_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a session.
        
        Args:
            session_id: Session identifier.
            limit: Maximum number of recent messages to return.
            
        Returns:
            List of message dictionaries, most recent last.
        """
        ctx = self.get_context(session_id)
        return ctx['history'][-limit:] if ctx else []
    
    def clear_history(self, session_id: str) -> bool:
        """Clear conversation history for a session.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            bool: True if history was cleared.
        """
        if session_id in self.contexts:
            self.contexts[session_id]['history'] = []
            return True
        return False
    
    def process(self, context: Any, input_data: Any, **kwargs) -> Any:
        """Process input with context management.
        
        Args:
            context: The current AI context.
            input_data: Input data to process.
            **kwargs: Additional parameters including 'session_id' and 'role'.
            
        Returns:
            Processed output with context.
        """
        if not self.enabled or not input_data or not isinstance(input_data, str):
            return input_data
            
        session_id = kwargs.get('session_id', 'default')
        role = kwargs.get('role', 'user')
        
        # Add to history
        self.add_to_history(
            session_id=session_id,
            role=role,
            content=input_data,
            **{k: v for k, v in kwargs.items() if k not in ('session_id', 'role')}
        )
        
        # Get recent context
        history = self.get_history(session_id, limit=5)
        
        # Format context for the AI
        context_parts = []
        for msg in history:
            prefix = 'User' if msg['role'] == 'user' else 'AI'
            context_parts.append(f"{prefix}: {msg['content']}")
        
        context_str = "\n".join(context_parts)
        
        # Return input with context
        if context_parts:
            return f"Context:\n{context_str}\n\n{input_data}"
        return input_data

# Register the plugin
from ..plugins import get_plugin_manager

def register() -> bool:
    """Register the context plugin."""
    return get_plugin_manager().register_plugin(ContextPlugin())

# Auto-register the plugin when imported
register()
