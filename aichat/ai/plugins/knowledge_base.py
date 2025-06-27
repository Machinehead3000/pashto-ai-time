"""
Knowledge Base Plugin - Provides persistent storage and retrieval of information.
"""

from typing import Dict, Any, List, Optional, Union
import logging
import json
import os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from ..plugins import AIPlugin

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeEntry:
    """Represents a single piece of knowledge in the knowledge base."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeEntry':
        """Create entry from dictionary."""
        return cls(**data)

class KnowledgeBasePlugin(AIPlugin):
    """Plugin for managing a knowledge base."""
    
    def __init__(self, storage_path: str = None):
        """Initialize the knowledge base plugin.
        
        Args:
            storage_path: Path to store the knowledge base. If None, uses in-memory only.
        """
        super().__init__(
            name="knowledge_base",
            description="Manages a persistent knowledge base",
            version="1.0.0"
        )
        self.storage_path = storage_path
        self.entries: Dict[str, KnowledgeEntry] = {}
        self._load_knowledge_base()
    
    def _get_storage_path(self) -> Optional[Path]:
        """Get the storage path for the knowledge base."""
        if not self.storage_path:
            return None
            
        path = Path(self.storage_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    
    def _load_knowledge_base(self) -> None:
        """Load knowledge base from storage."""
        path = self._get_storage_path()
        if not path or not path.exists():
            return
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.entries = {
                entry_id: KnowledgeEntry.from_dict(entry_data)
                for entry_id, entry_data in data.get('entries', {}).items()
            }
            logger.info(f"Loaded {len(self.entries)} entries from knowledge base")
            
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}", exc_info=True)
    
    def _save_knowledge_base(self) -> bool:
        """Save knowledge base to storage.
        
        Returns:
            bool: True if save was successful.
        """
        if not self.storage_path:
            return False
            
        try:
            path = self._get_storage_path()
            if not path:
                return False
                
            data = {
                'entries': {
                    entry_id: entry.to_dict()
                    for entry_id, entry in self.entries.items()
                },
                'metadata': {
                    'version': '1.0',
                    'last_updated': datetime.utcnow().isoformat(),
                    'entry_count': len(self.entries)
                }
            }
            
            # Write to temporary file first, then rename (atomic write)
            temp_path = path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # On Windows, we need to remove the destination file first
            if path.exists():
                path.unlink()
                
            temp_path.rename(path)
            return True
            
        except Exception as e:
            logger.error(f"Failed to save knowledge base: {e}", exc_info=True)
            return False
    
    def add_entry(
        self,
        content: str,
        entry_id: str = None,
        tags: List[str] = None,
        **metadata
    ) -> KnowledgeEntry:
        """Add a new entry to the knowledge base.
        
        Args:
            content: The content of the entry.
            entry_id: Optional custom ID for the entry. Auto-generated if not provided.
            tags: List of tags for the entry.
            **metadata: Additional metadata for the entry.
            
        Returns:
            The created or updated KnowledgeEntry.
        """
        if not content:
            raise ValueError("Content cannot be empty")
            
        if not entry_id:
            # Generate a simple ID based on content hash and timestamp
            import hashlib
            import time
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
            entry_id = f"kb_{content_hash}_{int(time.time())}"
        
        entry = KnowledgeEntry(
            id=entry_id,
            content=content,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.entries[entry_id] = entry
        self._save_knowledge_base()
        return entry
    
    def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get an entry by ID."""
        return self.entries.get(entry_id)
    
    def search_entries(
        self,
        query: str = None,
        tags: List[str] = None,
        limit: int = 10,
        **filters
    ) -> List[KnowledgeEntry]:
        """Search for entries matching the given criteria.
        
        Args:
            query: Text to search for in entry content.
            tags: List of tags to filter by.
            limit: Maximum number of results to return.
            **filters: Additional field filters (e.g., metadata fields).
            
        Returns:
            List of matching KnowledgeEntry objects, ordered by most recent first.
        """
        results = []
        
        for entry in self.entries.values():
            # Filter by query
            if query and query.lower() not in entry.content.lower():
                continue
                
            # Filter by tags
            if tags and not any(tag in entry.tags for tag in tags):
                continue
                
            # Filter by metadata fields
            if filters and not all(
                str(entry.metadata.get(k, '')).lower() == str(v).lower()
                for k, v in filters.items()
            ):
                continue
                
            results.append(entry)
        
        # Sort by most recently updated
        results.sort(key=lambda x: x.updated_at, reverse=True)
        
        return results[:limit]
    
    def update_entry(
        self,
        entry_id: str,
        content: str = None,
        tags: List[str] = None,
        **updates
    ) -> Optional[KnowledgeEntry]:
        """Update an existing entry.
        
        Args:
            entry_id: ID of the entry to update.
            content: New content for the entry.
            tags: New tags for the entry.
            **updates: Additional fields to update.
            
        Returns:
            The updated KnowledgeEntry, or None if not found.
        """
        if entry_id not in self.entries:
            return None
            
        entry = self.entries[entry_id]
        
        if content is not None:
            entry.content = content
            
        if tags is not None:
            entry.tags = tags
            
        # Update metadata
        if 'metadata' in updates:
            entry.metadata.update(updates.pop('metadata'))
            
        # Update any other fields
        for key, value in updates.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
        
        # Update timestamp
        entry.updated_at = datetime.utcnow().isoformat()
        
        self._save_knowledge_base()
        return entry
    
    def delete_entry(self, entry_id: str) -> bool:
        """Delete an entry from the knowledge base.
        
        Args:
            entry_id: ID of the entry to delete.
            
        Returns:
            bool: True if the entry was deleted, False otherwise.
        """
        if entry_id in self.entries:
            del self.entries[entry_id]
            self._save_knowledge_base()
            return True
        return False
    
    def process(self, context: Any, input_data: Any, **kwargs) -> Any:
        """Process input with knowledge base capabilities.
        
        Args:
            context: The current AI context.
            input_data: Input data to process.
            **kwargs: Additional parameters including 'action', 'entry_id', 'tags', etc.
            
        Returns:
            Processed output with knowledge base interaction results.
        """
        if not self.enabled or not input_data or not isinstance(input_data, str):
            return input_data
            
        action = kwargs.get('action', 'search')
        
        try:
            if action == 'add':
                # Add new entry
                entry = self.add_entry(
                    content=input_data,
                    tags=kwargs.get('tags'),
                    **kwargs.get('metadata', {})
                )
                return f"Added knowledge base entry with ID: {entry.id}"
                
            elif action == 'get':
                # Get entry by ID
                entry_id = kwargs.get('entry_id')
                if not entry_id:
                    return "Error: entry_id is required for 'get' action"
                    
                entry = self.get_entry(entry_id)
                if not entry:
                    return f"No entry found with ID: {entry_id}"
                    
                return f"Entry {entry_id}:\n{entry.content}"
                
            elif action == 'search':
                # Search entries
                results = self.search_entries(
                    query=input_data if input_data.strip() else None,
                    tags=kwargs.get('tags'),
                    limit=int(kwargs.get('limit', 5)),
                    **kwargs.get('filters', {})
                )
                
                if not results:
                    return "No matching entries found in the knowledge base."
                    
                response = ["Matching knowledge base entries:"]
                for i, entry in enumerate(results, 1):
                    preview = entry.content[:100] + ('...' if len(entry.content) > 100 else '')
                    response.append(f"{i}. [{entry.id}] {preview}")
                    if entry.tags:
                        response.append(f"   Tags: {', '.join(entry.tags)}")
                    response.append("")
                
                return "\n".join(response)
                
            elif action == 'delete':
                # Delete entry
                entry_id = kwargs.get('entry_id')
                if not entry_id:
                    return "Error: entry_id is required for 'delete' action"
                    
                if self.delete_entry(entry_id):
                    return f"Deleted entry with ID: {entry_id}"
                return f"No entry found with ID: {entry_id}"
                
            else:
                return f"Unknown action: {action}"
                
        except Exception as e:
            logger.error(f"Knowledge base error: {e}", exc_info=True)
            return f"Error processing knowledge base request: {str(e)}"

# Register the plugin
from ..plugins import get_plugin_manager

def register() -> bool:
    """Register the knowledge base plugin."""
    # Default storage path: ~/.aichat/knowledge_base.json
    storage_path = os.path.expanduser('~/.aichat/knowledge_base.json')
    return get_plugin_manager().register_plugin(KnowledgeBasePlugin(storage_path))

# Auto-register the plugin when imported
register()
