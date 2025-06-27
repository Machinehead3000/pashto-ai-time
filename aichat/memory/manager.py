"""
Memory manager for the Pashto AI application.

This module provides a centralized way to manage application state,
including conversation history, user preferences, and other persistent data.
"""
import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, TypeVar, Type
import logging
from datetime import datetime, timezone

from .models import (
    Conversation, Message, UserPreferences,
    MemoryError, MemoryValidationError, MessageRole, MessageType
)

# Type variable for generic class methods
T = TypeVar('T', bound='MemoryManager')

class MemoryManager:
    """
    Manages application memory including conversations and preferences.
    
    This class handles loading, saving, and managing all persistent
    application state in a thread-safe manner.
    """
    
    # Default file names
    CONVERSATIONS_FILE = 'conversations.json'
    PREFERENCES_FILE = 'preferences.json'
    BACKUP_EXT = '.bak'
    
    def __init__(self, data_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the memory manager.
        
        Args:
            data_dir: Directory to store memory files. If None, uses a default location.
        """
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Determine data directory
        if data_dir is None:
            # Use platform-appropriate default
            if os.name == 'nt':  # Windows
                app_data = os.getenv('APPDATA', os.path.expanduser('~'))
                self.data_dir = Path(app_data) / 'PashtoAI' / 'data'
            else:  # Unix-like
                self.data_dir = Path.home() / '.local' / 'share' / 'pashto-ai'
        else:
            self.data_dir = Path(data_dir)
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.conversations_file = self.data_dir / self.CONVERSATIONS_FILE
        self.preferences_file = self.data_dir / self.PREFERENCES_FILE
        
        # In-memory cache
        self._conversations: Dict[str, Conversation] = {}
        self._preferences: Optional[UserPreferences] = None
        self._current_conversation_id: Optional[str] = None
        
        # Initialize
        self._load_all()
    
    @classmethod
    def get_default(cls: Type[T]) -> T:
        """
        Get a default instance of the memory manager.
        
        Returns:
            MemoryManager: A new instance with default settings.
        """
        return cls()
    
    def _load_all(self) -> None:
        """Load all data from disk."""
        try:
            self._load_preferences()
            self._load_conversations()
        except Exception as e:
            self.logger.error(f"Failed to load data: {e}")
            # Try to recover by creating default data
            self._recover_from_error(e)
    
    def _recover_from_error(self, error: Exception) -> None:
        """Attempt to recover from an error by creating default data."""
        self.logger.warning("Attempting to recover from error by resetting data")
        
        # Backup corrupted files
        self._backup_file(self.conversations_file)
        self._backup_file(self.preferences_file)
        
        # Reset in-memory state
        self._conversations = {}
        self._preferences = UserPreferences()
        self._current_conversation_id = None
        
        # Save default data
        self._save_preferences()
        self._save_conversations()
    
    def _backup_file(self, file_path: Path) -> None:
        """Create a backup of a file if it exists."""
        if file_path.exists():
            backup_path = file_path.with_suffix(f".{int(datetime.now().timestamp())}{self.BACKUP_EXT}")
            try:
                shutil.copy2(file_path, backup_path)
                self.logger.info(f"Created backup at {backup_path}")
            except Exception as e:
                self.logger.error(f"Failed to create backup of {file_path}: {e}")
    
    def _load_preferences(self) -> None:
        """Load user preferences from disk."""
        if not self.preferences_file.exists():
            self._preferences = UserPreferences()
            self._save_preferences()
            return
        
        try:
            with open(self.preferences_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._preferences = UserPreferences.from_dict(data)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid preferences file: {e}")
            self._preferences = UserPreferences()
            self._save_preferences()
    
    def _save_preferences(self) -> None:
        """Save user preferences to disk."""
        if self._preferences is None:
            self._preferences = UserPreferences()
        
        try:
            # Create a temporary file first to ensure atomic write
            temp_file = self.preferences_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._preferences.to_dict(), f, indent=2, ensure_ascii=False)
            
            # On Windows, we need to remove the destination file first
            if os.name == 'nt' and self.preferences_file.exists():
                os.replace(temp_file, self.preferences_file)
            else:
                # On Unix-like systems, we can use rename which is atomic
                temp_file.replace(self.preferences_file)
                
        except Exception as e:
            self.logger.error(f"Failed to save preferences: {e}")
            raise MemoryError(f"Failed to save preferences: {e}") from e
    
    def _load_conversations(self) -> None:
        """Load conversations from disk."""
        if not self.conversations_file.exists():
            self._conversations = {}
            return
        
        try:
            with open(self.conversations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self._conversations = {}
            for conv_id, conv_data in data.items():
                try:
                    conv = Conversation.from_dict(conv_data)
                    self._conversations[conv_id] = conv
                except Exception as e:
                    self.logger.error(f"Failed to load conversation {conv_id}: {e}")
            
            # If we have conversations but no current one, set the most recent one
            if self._conversations and not self._current_conversation_id:
                self._current_conversation_id = max(
                    self._conversations.items(),
                    key=lambda x: x[1].updated_at
                )[0]
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid conversations file: {e}")
            self._conversations = {}
    
    def _save_conversations(self) -> None:
        """Save conversations to disk."""
        try:
            # Create a temporary file first to ensure atomic write
            temp_file = self.conversations_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                data = {
                    conv_id: conv.to_dict()
                    for conv_id, conv in self._conversations.items()
                }
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # On Windows, we need to remove the destination file first
            if os.name == 'nt' and self.conversations_file.exists():
                os.replace(temp_file, self.conversations_file)
            else:
                # On Unix-like systems, we can use rename which is atomic
                temp_file.replace(self.conversations_file)
                
        except Exception as e:
            self.logger.error(f"Failed to save conversations: {e}")
            raise MemoryError(f"Failed to save conversations: {e}") from e
    
    # Public API
    
    @property
    def preferences(self) -> UserPreferences:
        """Get the current user preferences."""
        if self._preferences is None:
            self._preferences = UserPreferences()
        return self._preferences
    
    def update_preferences(self, **updates) -> None:
        """
        Update user preferences.
        
        Args:
            **updates: Key-value pairs of preference updates.
        """
        if self._preferences is None:
            self._preferences = UserPreferences()
        
        # Update preferences
        for key, value in updates.items():
            if hasattr(self._preferences, key):
                setattr(self._preferences, key, value)
        
        # Save to disk
        self._save_preferences()
    
    def get_conversation(self, conversation_id: Optional[str] = None) -> Optional[Conversation]:
        """
        Get a conversation by ID, or the current conversation if None.
        
        Args:
            conversation_id: ID of the conversation to get, or None for current.
            
        Returns:
            The conversation, or None if not found.
        """
        if conversation_id is None:
            if not self._current_conversation_id:
                return None
            conversation_id = self._current_conversation_id
        
        return self._conversations.get(conversation_id)
    
    def get_current_conversation(self) -> Optional[Conversation]:
        """Get the current conversation, if any."""
        if not self._current_conversation_id:
            return None
        return self.get_conversation(self._current_conversation_id)
    
    def create_conversation(self, title: str = "New Conversation") -> Conversation:
        """
        Create a new conversation.
        
        Args:
            title: Title for the new conversation.
            
        Returns:
            The newly created conversation.
        """
        conv = Conversation(title=title)
        self._conversations[conv.id] = conv
        self._current_conversation_id = conv.id
        self._save_conversations()
        return conv
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: ID of the conversation to delete.
            
        Returns:
            True if the conversation was deleted, False if not found.
        """
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            
            # If we deleted the current conversation, clear it
            if self._current_conversation_id == conversation_id:
                self._current_conversation_id = None
                
            self._save_conversations()
            return True
        return False
    
    def list_conversations(self, include_archived: bool = False) -> List[Conversation]:
        """
        Get a list of all conversations.
        
        Args:
            include_archived: Whether to include archived conversations.
            
        Returns:
            List of conversations, sorted by most recently updated first.
        """
        conversations = list(self._conversations.values())
        if not include_archived:
            conversations = [c for c in conversations if not c.is_archived]
            
        return sorted(
            conversations,
            key=lambda c: c.updated_at,
            reverse=True
        )
    
    def add_message(
        self,
        role: Union[MessageRole, str],
        content: str,
        message_type: Union[MessageType, str] = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None
    ) -> Message:
        """
        Add a message to a conversation.
        
        Args:
            role: The role of the message sender.
            content: The message content.
            message_type: The type of message.
            metadata: Additional metadata for the message.
            conversation_id: ID of the conversation to add to, or None for current.
            
        Returns:
            The created message.
        """
        # Ensure we have a valid conversation
        if conversation_id is None:
            if not self._current_conversation_id:
                self.create_conversation()
            conversation_id = self._current_conversation_id
        
        # Get the conversation
        conv = self.get_conversation(conversation_id)
        if not conv:
            raise MemoryError(f"Conversation {conversation_id} not found")
        
        # Create the message
        if isinstance(role, str):
            role = MessageRole(role)
        if isinstance(message_type, str):
            message_type = MessageType(message_type)
            
        message = Message(
            role=role,
            content=content,
            message_type=message_type,
            metadata=metadata or {}
        )
        
        # Add to conversation
        conv.add_message(message)
        
        # Save changes
        self._save_conversations()
        
        return message
    
    def archive_conversation(self, conversation_id: str, archived: bool = True) -> bool:
        """
        Archive or unarchive a conversation.
        
        Args:
            conversation_id: ID of the conversation to modify.
            archived: Whether to archive (True) or unarchive (False).
            
        Returns:
            True if the conversation was found and updated, False otherwise.
        """
        conv = self.get_conversation(conversation_id)
        if conv:
            conv.is_archived = archived
            conv.updated_at = datetime.now(timezone.utc).isoformat()
            self._save_conversations()
            return True
        return False
    
    def clear_conversation(self, conversation_id: Optional[str] = None) -> bool:
        """
        Clear all messages from a conversation.
        
        Args:
            conversation_id: ID of the conversation to clear, or None for current.
            
        Returns:
            True if the conversation was found and cleared, False otherwise.
        """
        if conversation_id is None:
            if not self._current_conversation_id:
                return False
            conversation_id = self._current_conversation_id
        
        conv = self.get_conversation(conversation_id)
        if conv:
            conv.messages = []
            conv.updated_at = datetime.now(timezone.utc).isoformat()
            self._save_conversations()
            return True
        return False
    
    def search_messages(
        self,
        query: str,
        limit: int = 10,
        conversation_id: Optional[str] = None
    ) -> List[Message]:
        """
        Search for messages containing the given query.
        
        Args:
            query: The search query.
            limit: Maximum number of results to return.
            conversation_id: ID of the conversation to search in, or None for all.
            
        Returns:
            List of matching messages, most recent first.
        """
        query = query.lower()
        results = []
        
        # Determine which conversations to search
        if conversation_id:
            conv = self.get_conversation(conversation_id)
            conversations = [conv] if conv else []
        else:
            conversations = self._conversations.values()
        
        # Search messages
        for conv in conversations:
            for msg in conv.messages:
                if query in msg.content.lower():
                    results.append(msg)
        
        # Sort by timestamp, most recent first
        results.sort(key=lambda m: m.timestamp, reverse=True)
        
        return results[:limit]
