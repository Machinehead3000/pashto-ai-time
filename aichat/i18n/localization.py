"""
Localization manager for the application.

This module provides a LocalizationManager class that handles language
loading, string translation, and RTL (right-to-left) language support.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, List, Set, Any, Callable
from PyQt5.QtCore import QObject, QLocale, QTranslator, QCoreApplication, pyqtSignal, QDir

# Default language (English)
DEFAULT_LANGUAGE = "en"

# Supported languages with their display names and RTL status
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native": "English", "rtl": False},
    "es": {"name": "Spanish", "native": "Español", "rtl": False},
    "fr": {"name": "French", "native": "Français", "rtl": False},
    "de": {"name": "German", "native": "Deutsch", "rtl": False},
    "it": {"name": "Italian", "native": "Italiano", "rtl": False},
    "pt": {"name": "Portuguese", "native": "Português", "rtl": False},
    "ru": {"name": "Russian", "native": "Русский", "rtl": False},
    "zh": {"name": "Chinese", "native": "中文", "rtl": False},
    "ja": {"name": "Japanese", "native": "日本語", "rtl": False},
    "ko": {"name": "Korean", "native": "한국어", "rtl": False},
    "ar": {"name": "Arabic", "native": "العربية", "rtl": True},
    "fa": {"name": "Persian", "native": "فارسی", "rtl": True},
    "ps": {"name": "Pashto", "native": "پښتو", "rtl": True},
    "ur": {"name": "Urdu", "native": "اردو", "rtl": True},
}

class LocalizationManager(QObject):
    """
    Manages application localization and translations.
    
    Signals:
        language_changed: Emitted when the application language is changed.
                        Parameters:
                            str: The new language code
    """
    
    language_changed = pyqtSignal(str)
    
    def __init__(self, app: QCoreApplication, translations_dir: Optional[str] = None):
        """
        Initialize the localization manager.
        
        Args:
            app: The QApplication instance
            translations_dir: Directory containing translation files (.qm)
        """
        super().__init__()
        self.app = app
        self.translator = QTranslator()
        self.rtl = False
        self._current_language = DEFAULT_LANGUAGE
        self._translations: Dict[str, Dict[str, str]] = {}
        self._fallback_translations: Dict[str, str] = {}
        
        # Set up translations directory
        if translations_dir is None:
            # Default to translations directory next to the executable
            self.translations_dir = str(Path(__file__).parent.parent / "translations")
        else:
            self.translations_dir = translations_dir
        
        # Ensure the directory exists
        os.makedirs(self.translations_dir, exist_ok=True)
        
        # Load fallback translations (English)
        self._load_translations(DEFAULT_LANGUAGE)
        
        # Set default language
        self.set_language(DEFAULT_LANGUAGE)
    
    @property
    def current_language(self) -> str:
        """Get the current language code."""
        return self._current_language
    
    @property
    def available_languages(self) -> Dict[str, Dict[str, str]]:
        """Get a dictionary of available languages with their display names."""
        return {
            code: {"name": info["name"], "native": info["native"]}
            for code, info in SUPPORTED_LANGUAGES.items()
        }
    
    def is_rtl(self, language: Optional[str] = None) -> bool:
        """
        Check if a language is RTL (right-to-left).
        
        Args:
            language: Language code to check (defaults to current language)
            
        Returns:
            bool: True if the language is RTL
        """
        if language is None:
            language = self._current_language
        return SUPPORTED_LANGUAGES.get(language, {}).get("rtl", False)
    
    def set_language(self, language: str) -> bool:
        """
        Set the application language.
        
        Args:
            language: Language code (e.g., 'en', 'es', 'fr')
            
        Returns:
            bool: True if the language was set successfully
        """
        if language not in SUPPORTED_LANGUAGES:
            print(f"Warning: Unsupported language '{language}'. Using default.")
            language = DEFAULT_LANGUAGE
        
        # Remove any existing translator
        QCoreApplication.removeTranslator(self.translator)
        
        # Load translations for the new language if not already loaded
        if language != DEFAULT_LANGUAGE and language not in self._translations:
            if not self._load_translations(language):
                print(f"Warning: Failed to load translations for '{language}'. Using default.")
                language = DEFAULT_LANGUAGE
        
        # Set up the new translator if not using the default language
        if language != DEFAULT_LANGUAGE:
            # Try to load Qt's .qm file first
            if self.translator.load(f"aichat_{language}", self.translations_dir):
                QCoreApplication.installTranslator(self.translator)
            else:
                print(f"Warning: Failed to load Qt translations for '{language}'.")
        
        # Update RTL status
        self.rtl = self.is_rtl(language)
        
        # Update current language
        self._current_language = language
        
        # Emit signal
        self.language_changed.emit(language)
        
        return True
    
    def _load_translations(self, language: str) -> bool:
        """
        Load translations from a JSON file.
        
        Args:
            language: Language code to load
            
        Returns:
            bool: True if translations were loaded successfully
        """
        if language == DEFAULT_LANGUAGE:
            # Load default translations (English)
            self._fallback_translations = self._get_default_translations()
            return True
        
        # Try to load from file
        try:
            trans_file = Path(self.translations_dir) / f"{language}.json"
            if not trans_file.exists():
                print(f"Translation file not found: {trans_file}")
                return False
                
            with open(trans_file, 'r', encoding='utf-8') as f:
                self._translations[language] = json.load(f)
                
            return True
            
        except Exception as e:
            print(f"Error loading translations for {language}: {e}")
            return False
    
    def _get_default_translations(self) -> Dict[str, str]:
        """
        Get the default (English) translations.
        
        Returns:
            Dict[str, str]: Dictionary of translation keys to English strings
        """
        # Return a minimal set of translations for testing
        return {
            # Common UI elements
            "app.title": "Pashto AI Chat",
            "app.menu.file": "&File",
            "app.menu.edit": "&Edit",
            "app.menu.view": "&View",
            "app.menu.settings": "&Settings",
            "app.menu.help": "&Help",
            
            # Chat interface
            "chat.input_placeholder": "Type your message here...",
            "chat.send_button": "Send",
            "chat.attach_files": "Attach Files",
            "chat.clear_history": "Clear History",
            
            # Settings
            "settings.title": "Settings",
            "settings.language": "Language:",
            "settings.theme": "Theme:",
            "settings.apply": "Apply",
            "settings.cancel": "Cancel",
            "settings.ok": "OK",
            
            # Common actions
            "action.save": "Save",
            "action.cancel": "Cancel",
            "action.close": "Close",
            "action.yes": "Yes",
            "action.no": "No",
            "action.ok": "OK",
            "action.apply": "Apply",
            "action.reset": "Reset",
            "action.delete": "Delete",
            "action.edit": "Edit",
            "action.add": "Add",
            "action.remove": "Remove",
            "action.back": "Back",
            "action.next": "Next",
            "action.finish": "Finish",
            "action.cancel": "Cancel",
            "action.confirm": "Confirm",
            "action.discard": "Discard",
            "action.continue": "Continue",
            "action.retry": "Retry",
            "action.ignore": "Ignore",
            "action.details": "Details",
            "action.more_options": "More options",
            "action.learn_more": "Learn more",
            
            # Error messages
            "error.title": "Error",
            "error.generic": "An error occurred: {message}",
            "error.network": "Network error: {message}",
            "error.file_not_found": "File not found: {path}",
            "error.permission_denied": "Permission denied: {path}",
            "error.invalid_format": "Invalid format: {message}",
            "error.unsupported_operation": "Unsupported operation: {operation}",
            "error.timeout": "Operation timed out",
            "error.unknown": "An unknown error occurred",
            
            # Success messages
            "success.title": "Success",
            "success.saved": "Successfully saved",
            "success.deleted": "Successfully deleted",
            "success.updated": "Successfully updated",
            
            # Confirmation dialogs
            "confirm.title": "Confirm",
            "confirm.delete": "Are you sure you want to delete this item?",
            "confirm.unsaved_changes": "You have unsaved changes. Are you sure you want to discard them?",
            "confirm.exit": "Are you sure you want to exit?",
            "confirm.overwrite": "File already exists. Overwrite?",
            
            # Status messages
            "status.ready": "Ready",
            "status.connecting": "Connecting...",
            "status.connected": "Connected",
            "status.disconnected": "Disconnected",
            "status.saving": "Saving...",
            "status.loading": "Loading...",
            "status.processing": "Processing...",
            "status.completed": "Completed",
            "status.failed": "Failed",
            "status.cancelled": "Cancelled",
        }
    
    def tr(self, key: str, **kwargs) -> str:
        """
        Get a translated string for the given key.
        
        Args:
            key: Translation key
            **kwargs: Format arguments for the translated string
            
        Returns:
            str: Translated string with arguments formatted
        """
        # Try to get the translation for the current language
        translation = self._translations.get(self._current_language, {}).get(key)
        
        # Fall back to default language if not found
        if translation is None:
            translation = self._fallback_translations.get(key, key)
        
        # Format the string with any provided arguments
        if kwargs:
            try:
                return translation.format(**kwargs)
            except (KeyError, IndexError):
                # If formatting fails, return the unformatted string
                return translation
        
        return translation

# Global instance
_localization_manager = None

def init_localization(app: QCoreApplication, translations_dir: Optional[str] = None) -> LocalizationManager:
    """
    Initialize the global localization manager.
    
    Args:
        app: The QApplication instance
        translations_dir: Directory containing translation files
        
    Returns:
        LocalizationManager: The initialized localization manager
    """
    global _localization_manager
    if _localization_manager is None:
        _localization_manager = LocalizationManager(app, translations_dir)
    return _localization_manager

def get_localization() -> LocalizationManager:
    """
    Get the global localization manager.
    
    Returns:
        LocalizationManager: The global localization manager
        
    Raises:
        RuntimeError: If the localization manager has not been initialized
    """
    if _localization_manager is None:
        raise RuntimeError("Localization manager not initialized. Call init_localization() first.")
    return _localization_manager

def tr(key: str, **kwargs) -> str:
    """
    Get a translated string for the given key.
    
    Args:
        key: Translation key
        **kwargs: Format arguments for the translated string
        
    Returns:
        str: Translated string with arguments formatted
        
    Raises:
        RuntimeError: If the localization manager has not been initialized
    """
    return get_localization().tr(key, **kwargs)
