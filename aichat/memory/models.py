"""
Data models for the memory management system.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import json
import uuid

class MessageRole(str, Enum):
    """Roles for chat messages."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class MessageType(str, Enum):
    """Types of messages."""
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    DOCUMENT = "document"
    ACTION = "action"

@dataclass
class Message:
    """A single message in a conversation."""
    role: MessageRole
    content: str
    message_type: MessageType = MessageType.TEXT
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        data = asdict(self)
        data['role'] = self.role.value
        data['message_type'] = self.message_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create a message from a dictionary."""
        if isinstance(data.get('role'), str):
            data['role'] = MessageRole(data['role'])
        if isinstance(data.get('message_type'), str):
            data['message_type'] = MessageType(data['message_type'])
        return cls(**data)

@dataclass
class Conversation:
    """A conversation between the user and the assistant."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "New Conversation"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_archived: bool = False
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow().isoformat()
    
    def get_messages(self) -> List[Message]:
        """Get all messages in the conversation."""
        return self.messages
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the conversation to a dictionary."""
        data = asdict(self)
        data['messages'] = [msg.to_dict() for msg in self.messages]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create a conversation from a dictionary."""
        messages_data = data.pop('messages', [])
        conv = cls(**data)
        conv.messages = [Message.from_dict(msg) for msg in messages_data]
        return conv

@dataclass
class UserPreferences:
    """User preferences for the application."""
    theme: str = "dark"
    font_size: int = 12
    font_family: str = "Arial, sans-serif"
    language: str = "en-US"
    auto_save: bool = True
    auto_save_interval: int = 60  # seconds
    max_history_items: int = 100
    enable_analytics: bool = False
    enable_error_reporting: bool = True
    custom_styles: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert preferences to a dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """Create preferences from a dictionary."""
        return cls(**data)

class MemoryError(Exception):
    """Base exception for memory-related errors."""
    pass

class MemoryValidationError(MemoryError):
    """Raised when memory data validation fails."""
    pass
