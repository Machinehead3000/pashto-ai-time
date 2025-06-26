"""
Localization system for the Pashto AI application.

This module provides internationalization (i18n) support for the application,
allowing for easy translation of UI elements and messages.
"""
import json
import os
from pathlib import Path
from typing import Dict, Optional, Any

class Localization:
    """Handles application localization and translations."""
    
    _instance = None
    _translations: Dict[str, Dict[str, str]] = {}
    _current_language: str = 'en'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Localization, cls).__new__(cls)
            cls._instance._load_translations()
        return cls._instance
    
    def _load_translations(self):
        """Load all translation files from the locales directory."""
        locales_dir = Path(__file__).parent / 'locales'
        if not locales_dir.exists():
            os.makedirs(locales_dir, exist_ok=True)
            
            # Create default English translation if none exists
            default_translation = {
                "app_name": "Pashto AI",
                "menu_file": "File",
                "menu_edit": "Edit",
                "menu_view": "View",
                "menu_help": "Help",
                "action_new_chat": "New Chat",
                "action_open": "Open",
                "action_save": "Save",
                "action_exit": "Exit",
                "action_settings": "Settings",
                "status_ready": "Ready",
                "status_typing": "AI is typing...",
                "status_sending": "Sending...",
                "error_network": "Network error: {error}",
                "error_invalid_response": "Invalid response from server",
                "error_unknown": "An unknown error occurred",
                "button_send": "Send",
                "button_cancel": "Cancel",
                "button_ok": "OK",
                "button_yes": "Yes",
                "button_no": "No",
                "tooltip_send_message": "Send message (Ctrl+Enter)",
                "tooltip_attach_file": "Attach file",
                "tooltip_clear_chat": "Clear conversation",
                "tooltip_settings": "Application settings",
                "confirm_clear_chat": "Are you sure you want to clear the conversation?",
                "confirm_exit": "Are you sure you want to exit?",
                "error_file_too_large": "File is too large. Maximum size is {max_size}MB",
                "error_invalid_file_type": "Invalid file type. Supported types: {file_types}",
                "uploading_file": "Uploading {filename}...",
                "file_uploaded": "File uploaded: {filename}",
                "file_upload_failed": "Failed to upload file: {error}",
                "model_switched": "Switched to {model}",
                "model_not_found": "Model not found: {model}",
                "no_model_selected": "No AI model is currently selected",
                "model_not_supported": "Selected model does not support text generation",
                "generating_response": "Generating response...",
                "response_generated": "Response generated",
                "error_processing_token": "Error processing token: {error}",
                "error_completing_response": "Error completing response: {error}",
                "error_in_handler": "Critical error in error handler: {error}",
                "error_generic": "I encountered an error: {error}",
                "error_network_generic": "Network error while connecting to the AI service",
                "error_invalid_json": "Invalid response from the AI service"
            }
            
            with open(locales_dir / 'en.json', 'w', encoding='utf-8') as f:
                json.dump(default_translation, f, indent=2, ensure_ascii=False)
        
        # Load all translation files
        for file in locales_dir.glob('*.json'):
            lang = file.stem
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    self._translations[lang] = json.load(f)
            except Exception as e:
                print(f"Error loading {file}: {e}")
    
    def set_language(self, language: str):
        """Set the current language.
        
        Args:
            language: Language code (e.g., 'en', 'es', 'fr')
        """
        if language in self._translations:
            self._current_language = language
        else:
            print(f"Warning: Language '{language}' not found, falling back to 'en'")
            self._current_language = 'en'
    
    def get_language(self) -> str:
        """Get the current language code."""
        return self._current_language
    
    def tr(self, key: str, **kwargs) -> str:
        """Translate a string.
        
        Args:
            key: Translation key
            **kwargs: Format arguments
            
        Returns:
            Translated string with placeholders filled in
        """
        translation = self._translations.get(self._current_language, {})
        text = translation.get(key, key)  # Fall back to key if not found
        
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text  # Return as-is if formatting fails

# Create a singleton instance
i18n = Localization()

def tr(key: str, **kwargs) -> str:
    """Convenience function for translating strings.
    
    Args:
        key: Translation key
        **kwargs: Format arguments
        
    Returns:
        Translated string with placeholders filled in
    """
    return i18n.tr(key, **kwargs)
