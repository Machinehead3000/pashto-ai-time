"""
Settings management for the application.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from PyQt5.QtCore import QSettings, QStandardPaths

logger = logging.getLogger(__name__)

class SettingsManager:
    """Manages application settings with persistence."""
    
    def __init__(self, app_name: str = "PashtoAI", org_name: str = "PashtoAI"):
        """Initialize the settings manager.
        
        Args:
            app_name: Application name
            org_name: Organization name
        """
        self.app_name = app_name
        self.org_name = org_name
        self.settings = QSettings(org_name, app_name)
        self.defaults = self._get_default_settings()
        
        # Create config directory if it doesn't exist
        self.config_dir = Path(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Migrate old settings if needed
        self._migrate_old_settings()
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings.
        
        Returns:
            Dictionary of default settings
        """
        return {
            "app": {
                "theme": "dark",
                "font_size": 12,
                "ui_scale": 1.0,
                "language": "en_US",
                "check_updates": True,
                "start_minimized": False,
                "save_window_state": True,
                "window_geometry": None,
                "window_state": None,
                "recent_files": [],
                "max_recent_files": 10,
            },
            "chat": {
                "model": "openai/gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "system_prompt": "You are a helpful AI assistant.",
                "show_timestamps": True,
                "compact_view": False,
                "auto_scroll": True,
                "typing_animation": True,
            },
            "api": {
                "api_key": "",
                "base_url": "https://openrouter.ai/api/v1",
                "timeout": 300,
                "max_retries": 3,
                "organization": "",
            },
            "models": {
                "available_models": {},
                "favorites": [],
                "last_updated": None,
            },
            "files": {
                "default_save_dir": str(Path.home() / "Documents"),
                "auto_save": True,
                "auto_save_interval": 5,  # minutes
                "backup_enabled": True,
                "backup_count": 5,
            },
            "privacy": {
                "collect_analytics": False,
                "share_usage_data": False,
                "save_chat_history": True,
                "clear_history_on_exit": False,
            },
            "shortcuts": {
                "new_chat": "Ctrl+N",
                "open_chat": "Ctrl+O",
                "save_chat": "Ctrl+S",
                "settings": "Ctrl+,",
                "exit": "Alt+F4",
                "send_message": "Ctrl+Return",
                "new_line": "Shift+Return",
                "toggle_sidebar": "Ctrl+B",
                "toggle_theme": "Ctrl+T",
            },
        }
    
    def _migrate_old_settings(self):
        """Migrate settings from old versions if needed."""
        # Check if we need to migrate from an older version
        version = self.settings.value("version")
        
        if not version:
            # This is a new installation or first run
            self.settings.setValue("version", "1.0.0")
            return
        
        # Add migration logic here when needed
        # Example:
        # if version == "1.0.0":
        #     # Migrate from 1.0.0 to 1.1.0
        #     old_value = self.settings.value("some_old_setting")
        #     if old_value is not None:
        #         self.settings.setValue("some_new_setting", old_value)
        #         self.settings.remove("some_old_setting")
        #     
        #     self.settings.setValue("version", "1.1.0")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key.
        
        Args:
            key: Setting key in dot notation (e.g., 'app.theme')
            default: Default value if key is not found
            
        Returns:
            The setting value or default if not found
        """
        # Try to get from settings first
        value = self.settings.value(key)
        
        # If not found, try to get from defaults
        if value is None:
            keys = key.split('.')
            current = self.defaults
            
            try:
                for k in keys:
                    current = current[k]
                return current
            except (KeyError, TypeError):
                return default
        
        # Convert string booleans to actual booleans
        if isinstance(value, str):
            if value.lower() == 'true':
                return True
            elif value.lower() == 'false':
                return False
            
            # Try to convert to int or float if possible
            try:
                return int(value)
            except (ValueError, TypeError):
                try:
                    return float(value)
                except (ValueError, TypeError):
                    pass
        
        return value
    
    def set(self, key: str, value: Any):
        """Set a setting value by key.
        
        Args:
            key: Setting key in dot notation (e.g., 'app.theme')
            value: Value to set
        """
        self.settings.setValue(key, value)
    
    def reset_to_defaults(self):
        """Reset all settings to their default values."""
        self.settings.clear()
    
    def save_window_state(self, window):
        """Save window geometry and state.
        
        Args:
            window: QMainWindow instance to save state from
        """
        if self.get("app.save_window_state", True):
            self.set("app.window_geometry", window.saveGeometry())
            self.set("app.window_state", window.saveState())
    
    def restore_window_state(self, window):
        """Restore window geometry and state.
        
        Args:
            window: QMainWindow instance to restore state to
        """
        if self.get("app.save_window_state", True):
            geometry = self.get("app.window_geometry")
            state = self.get("app.window_state")
            
            if geometry:
                window.restoreGeometry(geometry)
            if state:
                window.restoreState(state)
    
    def add_recent_file(self, file_path: str):
        """Add a file to the recent files list.
        
        Args:
            file_path: Path to the file to add
        """
        recent_files = self.get_recent_files()
        
        # Remove if already exists
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Add to beginning
        recent_files.insert(0, file_path)
        
        # Limit the number of recent files
        max_recent = self.get("app.max_recent_files", 10)
        recent_files = recent_files[:max_recent]
        
        self.set("app.recent_files", recent_files)
    
    def get_recent_files(self) -> list:
        """Get the list of recent files.
        
        Returns:
            List of recent file paths
        """
        return self.get("app.recent_files", [])
    
    def clear_recent_files(self):
        """Clear the list of recent files."""
        self.set("app.recent_files", [])
