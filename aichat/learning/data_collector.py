"""
Data collection module for gathering training data from user interactions.

This module provides functionality to collect, store, and manage conversation data
for the purpose of training and improving AI models. It includes features for:
- Structured conversation tracking
- User feedback collection
- Data persistence
- Conversation metadata management
"""

import json
import os
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, TypedDict, TypeVar, Generic, Type
from dataclasses import dataclass, asdict, field
from enum import Enum, auto
import hashlib

# Type variable for generic message content
T = TypeVar('T')

# Configure module-level logger
logger = logging.getLogger(__name__)

class MessageRole(str, Enum):
    """Defines the possible roles for messages in a conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"


class Message(TypedDict, total=False):
    """Represents a single message in a conversation with typed fields.
    
    Attributes:
        role: The role of the message sender (user, assistant, system, function)
        content: The text content of the message
        timestamp: ISO 8601 formatted timestamp of when the message was created
        metadata: Additional metadata about the message
        name: Optional name of the sender (for function calls)
        function_call: Optional function call information
    """
    role: MessageRole
    content: str
    timestamp: str
    metadata: Dict[str, Any]
    name: Optional[str]
    function_call: Optional[Dict[str, Any]]


class Feedback(TypedDict, total=False):
    """Structured feedback for a conversation.
    
    Attributes:
        rating: Numeric rating from 1-5 (inclusive)
        comments: Optional free-form text feedback
        tags: List of string tags for categorization
        metadata: Additional structured feedback data
    """
    rating: int  # 1-5 scale
    comments: str
    tags: List[str]
    metadata: Dict[str, Any]


@dataclass
class Conversation:
    """Manages a conversation session with messages and metadata.
    
    A conversation represents a single interaction session with a user,
    containing all messages exchanged and any associated metadata.
    """
    session_id: str = field(default_factory=lambda: f"sess_{uuid.uuid4().hex}")
    messages: List[Message] = field(default_factory=list)
    start_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    end_time: Optional[str] = None
    feedback: Optional[Feedback] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"

    def add_message(
        self, 
        role: Union[MessageRole, str], 
        content: str, 
        **metadata: Any
    ) -> Message:
        """Add a message to the conversation.
        
        Args:
            role: Role of the message sender
            content: Text content of the message
            **metadata: Additional metadata to attach to the message
            
        Returns:
            The created message dictionary
            
        Raises:
            ValueError: If role is invalid or content is empty
        """
        if not content.strip():
            raise ValueError("Message content cannot be empty")
            
        if isinstance(role, str):
            try:
                role = MessageRole(role.lower())
            except ValueError as e:
                raise ValueError(
                    f"Invalid role: {role}. Must be one of {[r.value for r in MessageRole]}"
                ) from e

        message: Message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        self.messages.append(message)
        return message
    
    def add_feedback(
        self, 
        rating: int, 
        comments: str = "", 
        tags: Optional[List[str]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Add feedback for the conversation.
        
        Args:
            rating: User rating from 1-5 (inclusive)
            comments: Optional feedback comments
            tags: List of tags for categorization
            **kwargs: Additional feedback metadata
            
        Returns:
            The complete feedback dictionary
            
        Raises:
            ValueError: If rating is outside 1-5 range
        """
        rating = int(rating)
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")
            
        self.feedback = {
            "rating": rating,
            "comments": str(comments),
            "tags": list(tags or []),
            "metadata": kwargs or {}
        }
        return self.feedback
    
    def finalize(self) -> None:
        """Mark the conversation as complete with current timestamp."""
        self.end_time = datetime.utcnow().isoformat()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to a serializable dictionary."""
        return {
            "version": self.version,
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "messages": [
                {k: v.value if isinstance(v, MessageRole) else v 
                 for k, v in msg.items() if v is not None}
                for msg in self.messages
            ],
            "feedback": self.feedback,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create a Conversation from a dictionary."""
        conv = cls(
            session_id=data.get('session_id', f"sess_{uuid.uuid4().hex}"),
            start_time=data.get('start_time', datetime.utcnow().isoformat()),
            end_time=data.get('end_time'),
            metadata=data.get('metadata', {})
        )
        
        # Add messages
        for msg in data.get('messages', []):
            conv.add_message(
                role=msg['role'],
                content=msg['content'],
                **msg.get('metadata', {})
            )
        
        # Add feedback if present
        if 'feedback' in data:
            conv.feedback = data['feedback']
            
        return conv


class DataCollector:
    """Manages collection, storage, and retrieval of conversation data.
    
    This class provides thread-safe methods for managing conversation data
    with persistence to disk and support for various storage backends.
    """
    
    def __init__(self, data_dir: Union[str, Path] = "training_data") -> None:
        """Initialize the data collector.
        
        Args:
            data_dir: Base directory for storing conversation data.
                     Will be created if it doesn't exist.
        """
        self.data_dir = Path(data_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.current_conversation: Optional[Conversation] = None
        self._lock = None  # Would be a threading.Lock in a threaded environment
        
        self._setup_logging()
        self._setup_storage()
    
    def _setup_logging(self) -> None:
        """Configure logging for the data collector."""
        log_file = self.data_dir / "data_collector.log"
        
        # Only add file handler if not already configured
        if not logger.handlers:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(file_handler)
            logger.setLevel(logging.INFO)
    
    def _setup_storage(self) -> None:
        """Initialize storage directories and resources."""
        # Create necessary subdirectories
        self.conversations_dir = self.data_dir / 'conversations'
        self.conversations_dir.mkdir(exist_ok=True)
        
        # Initialize thread lock for thread safety
        try:
            from threading import Lock
            self._lock = Lock()
        except ImportError:
            logger.warning("Threading not available, running in single-threaded mode")
            self._lock = None
    
    def _acquire_lock(self) -> bool:
        """Acquire the thread lock if available.
        
        Returns:
            bool: True if lock was acquired, False otherwise
        """
        if self._lock is None:
            return True
        return self._lock.acquire(blocking=True, timeout=5.0)
    
    def _release_lock(self) -> None:
        """Release the thread lock if it's held."""
        if self._lock is not None and self._lock.locked():
            self._lock.release()
    
    def _save_conversation(self, conversation: Conversation) -> Path:
        """Save a conversation to disk.
        
        Args:
            conversation: The conversation to save
            
        Returns:
            Path: Path to the saved conversation file
            
        Raises:
            IOError: If the conversation cannot be saved
        """
        if not conversation.messages:
            raise ValueError("Cannot save an empty conversation")
            
        try:
            # Ensure the conversation is finalized
            if not conversation.end_time:
                conversation.finalize()
                
            # Create filename with timestamp and session ID
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"conv_{timestamp}_{conversation.session_id}.json"
            filepath = self.conversations_dir / filename
            
            # Save with atomic write
            temp_file = filepath.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(conversation.to_dict(), f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_file.replace(filepath)
            logger.info(f"Saved conversation to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save conversation: {str(e)}")
            raise IOError(f"Failed to save conversation: {str(e)}") from e
    
    def _load_conversation(self, filepath: Union[str, Path]) -> Conversation:
        """Load a conversation from disk.
        
        Args:
            filepath: Path to the conversation file
            
        Returns:
            Conversation: The loaded conversation
            
        Raises:
            IOError: If the conversation cannot be loaded
            ValueError: If the conversation data is invalid
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                raise ValueError("Invalid conversation format: expected a dictionary")
                
            return Conversation.from_dict(data)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in conversation file: {str(e)}") from e
        except Exception as e:
            logger.error(f"Failed to load conversation from {filepath}: {str(e)}")
            raise IOError(f"Failed to load conversation: {str(e)}") from e
    
    def start_new_conversation(self, system_prompt: str = "", **metadata) -> str:
        """Start a new conversation session.
        
        Args:
            system_prompt: Optional system message to start the conversation
            **metadata: Additional metadata to attach to the conversation
            
        Returns:
            str: The session ID of the new conversation
            
        Raises:
            RuntimeError: If a conversation is already active and not saved
        """
        # Finalize and save the current conversation if it exists and has messages
        if self.current_conversation and self.current_conversation.messages:
            if not self.current_conversation.end_time:
                self.current_conversation.finalize()
            try:
                self._save_conversation(self.current_conversation)
            except Exception as e:
                logger.warning(f"Failed to save previous conversation: {e}")
        
        # Create a new conversation
        self.current_conversation = Conversation(metadata=metadata)
        if system_prompt:
            self.current_conversation.add_message("system", system_prompt)
            
        logger.info(f"Started new conversation: {self.current_conversation.session_id}")
        return self.current_conversation.session_id
    
    def add_message(self, role: Union[MessageRole, str], content: str, **metadata) -> Message:
        """Add a message to the current conversation.
        
        Args:
            role: Role of the message sender
            content: Text content of the message
            **metadata: Additional metadata to attach to the message
            
        Returns:
            Message: The created message
            
        Raises:
            RuntimeError: If no active conversation exists
        """
        if not self.current_conversation:
            raise RuntimeError("No active conversation. Call start_new_conversation() first.")
            
        message = self.current_conversation.add_message(role, content, **metadata)
        logger.debug(f"Added message to conversation {self.current_conversation.session_id}")
        return message
    
    def add_feedback(
        self,
        rating: int,
        comments: str = "",
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Add feedback to the current conversation.
        
        Args:
            rating: User rating from 1-5 (inclusive)
            comments: Optional feedback comments
            tags: List of tags for categorization
            **kwargs: Additional feedback metadata
            
        Returns:
            Dict[str, Any]: The complete feedback data
            
        Raises:
            RuntimeError: If no active conversation exists
        """
        if not self.current_conversation:
            raise RuntimeError("No active conversation. Call start_new_conversation() first.")
            
        feedback = self.current_conversation.add_feedback(rating, comments, tags, **kwargs)
        logger.info(f"Added feedback to conversation {self.current_conversation.session_id}")
        return feedback
    
    def finalize_conversation(self, save: bool = True) -> Optional[Path]:
        """Finalize the current conversation.
        
        Args:
            save: Whether to save the conversation to disk
            
        Returns:
            Optional[Path]: Path to the saved conversation file if saved, None otherwise
            
        Raises:
            RuntimeError: If no active conversation exists
        """
        if not self.current_conversation:
            raise RuntimeError("No active conversation to finalize")
            
        self.current_conversation.finalize()
        
        if save and self.current_conversation.messages:
            try:
                filepath = self._save_conversation(self.current_conversation)
                self.current_conversation = None
                return filepath
            except Exception as e:
                logger.error(f"Failed to save conversation: {e}")
                raise
        
        self.current_conversation = None
        return None
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get a list of recent conversations with their metadata.
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List[Dict[str, Any]]: List of conversation metadata dictionaries
        """
        try:
            # Get all conversation files, sorted by modification time (newest first)
            conv_files = sorted(
                self.conversations_dir.glob("conv_*.json"),
                key=os.path.getmtime,
                reverse=True
            )
            
            conversations = []
            for filepath in conv_files[:limit]:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        conversations.append({
                            'session_id': data.get('session_id'),
                            'start_time': data.get('start_time'),
                            'end_time': data.get('end_time'),
                            'message_count': len(data.get('messages', [])),
                            'has_feedback': bool(data.get('feedback')),
                            'filepath': str(filepath)
                        })
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Error reading conversation file {filepath}: {e}")
            
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")
            return []
    
    def load_conversation(self, session_id: str) -> Optional[Conversation]:
        """Load a conversation by session ID.
        
        Args:
            session_id: The session ID of the conversation to load
            
        Returns:
            Optional[Conversation]: The loaded conversation, or None if not found
        """
        try:
            # First check if it's the current conversation
            if self.current_conversation and self.current_conversation.session_id == session_id:
                return self.current_conversation
                
            # Search for the conversation file
            for filepath in self.conversations_dir.glob(f"*{session_id}*.json"):
                try:
                    conversation = self._load_conversation(filepath)
                    if conversation.session_id == session_id:
                        self.current_conversation = conversation
                        return conversation
                except Exception as e:
                    logger.warning(f"Error loading conversation from {filepath}: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading conversation {session_id}: {e}")
    def add_interaction(
        self,
        user_input: str,
        assistant_response: str,
        user_metadata: Optional[Dict[str, Any]] = None,
        assistant_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Message]:
        """Add a user-assistant interaction to the current conversation.
        
        Args:
            user_input: The user's input text
            assistant_response: The assistant's response text
            user_metadata: Optional metadata for the user message
            assistant_metadata: Optional metadata for the assistant message
            
        Returns:
            List[Message]: The added message objects [user_message, assistant_message]
            
        Raises:
            ValueError: If either input or response is empty
        """
        if not user_input.strip():
            raise ValueError("User input cannot be empty")
        if not assistant_response.strip():
            raise ValueError("Assistant response cannot be empty")
            
        if not self.current_conversation:
            self.start_new_conversation()
        
        # Add user message
        user_message = self.add_message(
            MessageRole.USER,
            user_input,
            **(user_metadata or {})
        )
        
        # Add assistant message with timing information
        start_time = datetime.utcnow()
        assistant_message = self.add_message(
            MessageRole.ASSISTANT,
            assistant_response,
            **(assistant_metadata or {})
        )
        
        # Add timing metadata to assistant message
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        assistant_message['metadata'].update({
            'processing_time_seconds': processing_time,
            'response_length': len(assistant_response)
        })
        
        logger.debug(
            f"Added interaction to conversation {self.current_conversation.session_id} "
            f"({processing_time:.2f}s, {len(assistant_response)} chars)"
        )
        
        return [user_message, assistant_message]
    
    def export_conversation(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Export a conversation as a dictionary.
        
        Args:
            session_id: The session ID of the conversation to export. 
                      If None, exports the current conversation.
                      
        Returns:
            Dict[str, Any]: The exported conversation data
            
        Raises:
            ValueError: If no conversation is found with the given session_id
        """
        if session_id is None:
            if not self.current_conversation:
                raise ValueError("No active conversation to export")
            return self.current_conversation.to_dict()
        
        # Try to load the conversation if it's not the current one
        if not self.current_conversation or self.current_conversation.session_id != session_id:
            conversation = self.load_conversation(session_id)
            if not conversation:
                raise ValueError(f"No conversation found with ID: {session_id}")
            return conversation.to_dict()
            
        return self.current_conversation.to_dict()
    
    def import_conversation(self, data: Dict[str, Any]) -> str:
        """Import a conversation from a dictionary.
        
        Args:
            data: The conversation data to import
            
        Returns:
            str: The session ID of the imported conversation
            
        Raises:
            ValueError: If the conversation data is invalid
        """
        try:
            conversation = Conversation.from_dict(data)
            
            # If there's no active conversation, make this the active one
            if not self.current_conversation:
                self.current_conversation = conversation
            else:
                # Otherwise, save it to disk
                self._save_conversation(conversation)
                
            return conversation.session_id
            
        except Exception as e:
            logger.error(f"Failed to import conversation: {e}")
            raise ValueError(f"Invalid conversation data: {e}") from e
    
    def delete_conversation(self, session_id: str) -> bool:
        """Delete a conversation by session ID.
        
        Args:
            session_id: The session ID of the conversation to delete
            
        Returns:
            bool: True if the conversation was deleted, False otherwise
        """
        try:
            # If it's the current conversation, clear the reference
            if self.current_conversation and self.current_conversation.session_id == session_id:
                self.current_conversation = None
            
            # Find and delete the conversation file
            for filepath in self.conversations_dir.glob(f"*{session_id}*.json"):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('session_id') == session_id:
                            filepath.unlink()
                            logger.info(f"Deleted conversation file: {filepath}")
                            return True
                except (json.JSONDecodeError, KeyError):
                    continue
            
            logger.warning(f"No conversation found with ID: {session_id}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete conversation {session_id}: {e}")
            return False
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get statistics about stored conversations.
        
        Returns:
            Dict[str, Any]: Statistics about the conversations
        """
        stats = {
            'total_conversations': 0,
            'total_messages': 0,
            'total_feedback': 0,
            'avg_messages_per_conversation': 0.0,
            'conversations_by_role': {},
            'recent_conversations': []
        }
        
        try:
            conversations = self.get_conversation_history(limit=1000)  # Get all conversations
            if not conversations:
                return stats
                
            total_messages = 0
            total_feedback = 0
            role_counts = {}
            
            for conv in conversations:
                stats['total_conversations'] += 1
                total_messages += conv.get('message_count', 0)
                
                if conv.get('has_feedback'):
                    total_feedback += 1
                
                # Count messages by role
                try:
                    with open(conv['filepath'], 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for msg in data.get('messages', []):
                            role = msg.get('role', 'unknown')
                            role_counts[role] = role_counts.get(role, 0) + 1
                except (IOError, json.JSONDecodeError):
                    continue
            
            # Update stats
            stats['total_messages'] = total_messages
            stats['total_feedback'] = total_feedback
            stats['avg_messages_per_conversation'] = (
                total_messages / len(conversations) if conversations else 0.0
            )
            stats['conversations_by_role'] = role_counts
            stats['recent_conversations'] = conversations[:10]  # Last 10 conversations
            
        except Exception as e:
            logger.error(f"Error calculating conversation stats: {e}")
        
        return stats
    
    def save_conversation(
        self,
        rating: Optional[int] = None,
        comments: Optional[str] = None,
        **feedback_kwargs
    ) -> Optional[Path]:
        """Save the current conversation to disk.
        
        Args:
            rating: Optional user rating (1-5)
            comments: Optional user comments
            **feedback_kwargs: Additional feedback metadata
            
        Returns:
            Optional[Path]: Path to the saved conversation file, or None if save failed
        """
        if not self.current_conversation or not self.current_conversation.messages:
            logger.warning("No active conversation or empty conversation to save")
            return None
        
        # Add feedback if provided
        if rating is not None:
            self.current_conversation.add_feedback(rating, comments or "", **feedback_kwargs)
        
        # Finalize the conversation
        self.current_conversation.finalize()
        
        # Prepare filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"conv_{timestamp}_{self.current_conversation.session_id}.json"
        filepath = self.data_dir / filename
        
        try:
            # Convert to dict and save as JSON
            conv_dict = asdict(self.current_conversation)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conv_dict, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved conversation to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}", exc_info=True)
            return None
        
        finally:
            # Reset current conversation
            self.current_conversation = None
    
    def load_conversation(self, filepath: Union[str, Path]) -> Optional[Conversation]:
        """Load a conversation from a file.
        
        Args:
            filepath: Path to the conversation file
            
        Returns:
            Optional[Conversation]: Loaded conversation, or None if loading failed
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create new conversation and populate it
            conv = Conversation()
            for key, value in data.items():
                if hasattr(conv, key):
                    setattr(conv, key, value)
            
            logger.info(f"Loaded conversation from {filepath}")
            return conv
            
        except Exception as e:
            logger.error(f"Error loading conversation from {filepath}: {e}", exc_info=True)
            return None
    
    def list_conversations(self) -> List[Path]:
        """List all saved conversation files.
        
        Returns:
            List[Path]: List of paths to conversation files, sorted by modification time (newest first)
        """
        files = sorted(
            self.data_dir.glob("conv_*.json"),
            key=os.path.getmtime,
            reverse=True
        )
        return files


# Example usage
if __name__ == "__main__":
    # Initialize data collector
    collector = DataCollector()
    
    # Start a new conversation
    collector.start_new_conversation("You are a helpful AI assistant.")
    
    # Add some interactions
    collector.add_interaction("Hello!", "Hi there! How can I help you today?")
    collector.add_interaction("What's the weather like?", "I'm sorry, I don't have access to real-time weather data.")
    
    # Save the conversation with feedback
    collector.save_conversation(
        rating=4,
        comments="Helpful but limited by data access"
    )
