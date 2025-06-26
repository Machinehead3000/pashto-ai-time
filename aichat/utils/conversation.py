"""
Conversation management for saving and loading chat sessions.
"""
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manages saving and loading conversation history."""
    
    def __init__(self, save_dir: str = "conversations"):
        """Initialize the conversation manager.
        
        Args:
            save_dir: Directory to store conversation files
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
    
    def get_conversation_path(self, conversation_id: str) -> Path:
        """Get the full path for a conversation file."""
        return self.save_dir / f"{conversation_id}.json"
    
    def save_conversation(
        self, 
        messages: List[Dict[str, Any]], 
        conversation_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> str:
        """Save a conversation to disk.
        
        Args:
            messages: List of message dictionaries
            conversation_id: Optional ID for the conversation (generated if None)
            title: Optional title for the conversation
            
        Returns:
            str: The conversation ID
        """
        if conversation_id is None:
            conversation_id = f"conv_{int(datetime.now().timestamp())}"
        
        if title is None:
            # Generate a title from the first user message
            user_messages = [m for m in messages if m.get('role') == 'user']
            title = user_messages[0]['content'][:50] + ('...' if len(user_messages[0]['content']) > 50 else '') if user_messages else 'New Chat'
        
        data = {
            'id': conversation_id,
            'title': title,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'messages': messages
        }
        
        file_path = self.get_conversation_path(conversation_id)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved conversation to {file_path}")
            return conversation_id
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            raise
    
    def load_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Load a conversation from disk.
        
        Args:
            conversation_id: ID of the conversation to load
            
        Returns:
            Dict containing conversation data
        """
        file_path = self.get_conversation_path(conversation_id)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading conversation {conversation_id}: {e}")
            raise
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all saved conversations.
        
        Returns:
            List of conversation metadata dictionaries
        """
        conversations = []
        for file_path in self.save_dir.glob('*.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    conversations.append({
                        'id': data.get('id', file_path.stem),
                        'title': data.get('title', 'Untitled'),
                        'created_at': data.get('created_at'),
                        'updated_at': data.get('updated_at'),
                        'message_count': len(data.get('messages', [])),
                        'path': str(file_path)
                    })
            except Exception as e:
                logger.error(f"Error reading conversation file {file_path}: {e}")
        
        # Sort by last updated (newest first)
        return sorted(
            conversations,
            key=lambda x: x.get('updated_at', ''),
            reverse=True
        )
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation.
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        file_path = self.get_conversation_path(conversation_id)
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted conversation {conversation_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            return False
