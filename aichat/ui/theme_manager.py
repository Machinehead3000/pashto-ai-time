"""
Theme Manager for the application.

This module provides a ThemeManager class that handles theme management,
including light/dark mode switching and custom color schemes.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from PyQt5.QtCore import QObject, pyqtSignal, QSettings, QStandardPaths
from PyQt5.QtGui import QColor, QPalette, QFont, QFontDatabase, QIcon
from PyQt5.QtWidgets import QApplication, QStyleFactory

class ThemeManager(QObject):
    """
    Manages application themes and styles.
    
    Signals:
        theme_changed: Emitted when the theme is changed.
                      Parameters:
                          str: The name of the new theme
    """
    
    theme_changed = pyqtSignal(str)
    
    # Default color schemes
    LIGHT_THEME = {
        'name': 'Light',
        'is_dark': False,
        'colors': {
            'window': '#ffffff',
            'window_text': '#000000',
            'base': '#ffffff',
            'alternate_base': '#f0f0f0',
            'tool_tip_base': '#ffffdc',
            'tool_tip_text': '#000000',
            'text': '#000000',
            'button': '#f0f0f0',
            'button_text': '#000000',
            'bright_text': '#ff0000',
            'link': '#0066cc',
            'highlight': '#4a90e2',
            'highlighted_text': '#ffffff',
            'disabled_text': '#808080',
            'disabled_button': '#e0e0e0',
            'disabled_highlight': '#a0c0e0',
            'accent': '#4a90e2',
            'accent_light': '#6ab0ff',
            'accent_dark': '#2a70c2',
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545',
            'shadow': '#40000000',
            'border': '#c0c0c0',
            'hover': '#e0e8f0',
            'pressed': '#d0d8e0',
            'link_visited': '#8e44ad',
            'titlebar': '#f0f0f0',
            'titlebar_text': '#000000',
            'selection': '#e0e8f0',
            'selection_text': '#000000',
        },
        'font': {
            'family': 'Segoe UI',
            'size': 9,
            'title_size': 11,
            'fixed_family': 'Consolas',
            'fixed_size': 10,
        },
        'sizes': {
            'border_radius': 4,
            'padding': 6,
            'margin': 8,
            'spacing': 4,
            'icon_size': 16,
        }
    }
    
    DARK_THEME = {
        'name': 'Dark',
        'is_dark': True,
        'colors': {
            'window': '#252525',
            'window_text': '#f0f0f0',
            'base': '#2d2d2d',
            'alternate_base': '#353535',
            'tool_tip_base': '#353942',
            'tool_tip_text': '#f0f0f0',
            'text': '#f0f0f0',
            'button': '#404040',
            'button_text': '#f0f0f0',
            'bright_text': '#ff6b6b',
            'link': '#4a9fea',
            'highlight': '#4a90e2',
            'highlighted_text': '#ffffff',
            'disabled_text': '#808080',
            'disabled_button': '#303030',
            'disabled_highlight': '#2a4a6a',
            'accent': '#4a90e2',
            'accent_light': '#6ab0ff',
            'accent_dark': '#2a70c2',
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545',
            'shadow': '#80000000',
            'border': '#505050',
            'hover': '#3a3a3a',
            'pressed': '#2a2a2a',
            'link_visited': '#9b59b6',
            'titlebar': '#1e1e1e',
            'titlebar_text': '#f0f0f0',
            'selection': '#3a3a3a',
            'selection_text': '#ffffff',
        },
        'font': {
            'family': 'Segoe UI',
            'size': 9,
            'title_size': 11,
            'fixed_family': 'Consolas',
            'fixed_size': 10,
        },
        'sizes': {
            'border_radius': 4,
            'padding': 6,
            'margin': 8,
            'spacing': 4,
            'icon_size': 16,
        }
    }
    
    # Built-in themes
    BUILTIN_THEMES = {
        'Light': LIGHT_THEME,
        'Dark': DARK_THEME,
        'Blue': {
            'name': 'Blue',
            'is_dark': True,
            'colors': {
                'window': '#1a2b3c',
                'window_text': '#e0e0e0',
                'base': '#223344',
                'alternate_base': '#2a3b4c',
                'tool_tip_base': '#2a3b4c',
                'tool_tip_text': '#e0e0e0',
                'text': '#e0e0e0',
                'button': '#2a4a6a',
                'button_text': '#e0e0e0',
                'highlight': '#4a90e2',
                'highlighted_text': '#ffffff',
                'accent': '#4a90e2',
            },
            'font': LIGHT_THEME['font'],
            'sizes': LIGHT_THEME['sizes']
        },
        'Solarized Dark': {
            'name': 'Solarized Dark',
            'is_dark': True,
            'colors': {
                'window': '#002b36',
                'window_text': '#839496',
                'base': '#073642',
                'alternate_base': '#0a4b5a',
                'tool_tip_base': '#073642',
                'tool_tip_text': '#839496',
                'text': '#839496',
                'button': '#0a4b5a',
                'button_text': '#839496',
                'highlight': '#268bd2',
                'highlighted_text': '#fdf6e3',
                'accent': '#268bd2',
            },
            'font': LIGHT_THEME['font'],
            'sizes': LIGHT_THEME['sizes']
        },
        'Solarized Light': {
            'name': 'Solarized Light',
            'is_dark': False,
            'colors': {
                'window': '#fdf6e3',
                'window_text': '#657b83',
                'base': '#eee8d5',
                'alternate_base': '#e5dfcc',
                'tool_tip_base': '#fdf6e3',
                'tool_tip_text': '#586e75',
                'text': '#586e75',
                'button': '#e5dfcc',
                'button_text': '#586e75',
                'highlight': '#268bd2',
                'highlighted_text': '#fdf6e3',
                'accent': '#268bd2',
            },
            'font': LIGHT_THEME['font'],
            'sizes': LIGHT_THEME['sizes']
        }
    }
    
    def __init__(self, app: QApplication):
        """
        Initialize the theme manager.
        
        Args:
            app: The QApplication instance
        """
        super().__init__()
        self.app = app
        self.settings = QSettings("PashtoAI", "ThemeSettings")
        self.current_theme = None
        self.custom_themes = {}
        self.load_themes()
    
    @property
    def theme_names(self) -> List[str]:
        """Get a list of available theme names."""
        return list(self.BUILTIN_THEMES.keys()) + list(self.custom_themes.keys())
    
    def load_themes(self):
        """Load custom themes from settings."""
        # Load custom themes
        custom_themes_data = self.settings.value("custom_themes", {})
        if isinstance(custom_themes_data, str):
            try:
                custom_themes_data = json.loads(custom_themes_data)
            except json.JSONDecodeError:
                custom_themes_data = {}
        
        self.custom_themes = {}
        for name, theme_data in custom_themes_data.items():
            if isinstance(theme_data, dict):
                self.custom_themes[name] = theme_data
        
        # Set default theme if not set
        current_theme_name = self.settings.value("current_theme", "Dark")
        self.set_theme(current_theme_name)
    
    def save_themes(self):
        """Save custom themes to settings."""
        # Convert to serializable format
        serializable_themes = {}
        for name, theme in self.custom_themes.items():
            if isinstance(theme, dict):
                serializable_themes[name] = theme
        
        self.settings.setValue("custom_themes", json.dumps(serializable_themes))
    
    def get_theme(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a theme by name.
        
        Args:
            name: Theme name
            
        Returns:
            Dict containing theme data or None if not found
        """
        # Check built-in themes
        if name in self.BUILTIN_THEMES:
            return self.BUILTIN_THEMES[name].copy()
        
        # Check custom themes
        if name in self.custom_themes:
            return self.custom_themes[name].copy()
        
        return None
    
    def add_custom_theme(self, name: str, theme_data: Dict[str, Any]) -> bool:
        """
        Add or update a custom theme.
        
        Args:
            name: Theme name
            theme_data: Theme data dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not name or not isinstance(theme_data, dict):
            return False
        
        # Ensure required fields exist
        if 'colors' not in theme_data or 'font' not in theme_data or 'sizes' not in theme_data:
            return False
        
        # Make a deep copy to avoid reference issues
        theme_data = theme_data.copy()
        theme_data['name'] = name
        
        # Add to custom themes
        self.custom_themes[name] = theme_data
        self.save_themes()
        return True
    
    def delete_custom_theme(self, name: str) -> bool:
        """
        Delete a custom theme.
        
        Args:
            name: Theme name to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        if name in self.custom_themes:
            del self.custom_themes[name]
            self.save_themes()
            
            # If the current theme was deleted, fall back to default
            if self.current_theme == name:
                self.set_theme("Dark")
                
            return True
        return False
    
    def rename_theme(self, old_name: str, new_name: str) -> bool:
        """
        Rename a custom theme.
        
        Args:
            old_name: Current theme name
            new_name: New theme name
            
        Returns:
            bool: True if renamed, False if failed
        """
        if (old_name not in self.custom_themes or 
            new_name in self.BUILTIN_THEMES or 
            new_name in self.custom_themes or 
            not new_name.strip()):
            return False
        
        # Update the theme data
        theme_data = self.custom_themes[old_name].copy()
        theme_data['name'] = new_name
        
        # Remove old and add new
        del self.custom_themes[old_name]
        self.custom_themes[new_name] = theme_data
        
        # Update current theme if needed
        if self.current_theme == old_name:
            self.current_theme = new_name
            self.settings.setValue("current_theme", new_name)
        
        self.save_themes()
        return True
    
    def set_theme(self, theme_name: str) -> bool:
        """
        Set the current theme.
        
        Args:
            theme_name: Name of the theme to set
            
        Returns:
            bool: True if theme was set, False if not found
        """
        theme = self.get_theme(theme_name)
        if not theme:
            return False
        
        self.current_theme = theme_name
        self.settings.setValue("current_theme", theme_name)
        
        # Apply the theme
        self._apply_theme(theme)
        
        # Emit signal
        self.theme_changed.emit(theme_name)
        return True
    
    def _apply_theme(self, theme: Dict[str, Any]):
        """
        Apply the given theme to the application.
        
        Args:
            theme: Theme data dictionary
        """
        # Set style
        self.app.setStyle(QStyleFactory.create("Fusion"))
        
        # Create palette
        palette = QPalette()
        colors = theme['colors']
        
        # Set colors
        palette.setColor(QPalette.Window, QColor(colors['window']))
        palette.setColor(QPalette.WindowText, QColor(colors['window_text']))
        palette.setColor(QPalette.Base, QColor(colors['base']))
        palette.setColor(QPalette.AlternateBase, QColor(colors['alternate_base']))
        palette.setColor(QPalette.ToolTipBase, QColor(colors['tool_tip_base']))
        palette.setColor(QPalette.ToolTipText, QColor(colors['tool_tip_text']))
        palette.setColor(QPalette.Text, QColor(colors['text']))
        palette.setColor(QPalette.Button, QColor(colors['button']))
        palette.setColor(QPalette.ButtonText, QColor(colors['button_text']))
        palette.setColor(QPalette.BrightText, QColor(colors['bright_text']))
        palette.setColor(QPalette.Link, QColor(colors['link']))
        palette.setColor(QPalette.Highlight, QColor(colors['highlight']))
        palette.setColor(QPalette.HighlightedText, QColor(colors['highlighted_text']))
        
        # Disabled colors
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(colors['disabled_text']))
        palette.setColor(QPalette.Disabled, QPalette.Button, QColor(colors['disabled_button']))
        palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(colors['disabled_highlight']))
        palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(colors['highlighted_text']))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(colors['disabled_text']))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(colors['disabled_text']))
        
        # Set the palette
        self.app.setPalette(palette)
        
        # Set application-wide stylesheet
        self._set_stylesheet(theme)
        
        # Set font
        font = QFont(theme['font']['family'], theme['font']['size'])
        self.app.setFont(font)
        
        # Set fixed-width font for code
        fixed_font = QFont(theme['font']['fixed_family'], theme['font']['fixed_size'])
        self.app.setFont(fixed_font, "QTextEdit, QPlainTextEdit, QLineEdit, QListWidget, QTreeView, QTableView")
    
    def _set_stylesheet(self, theme: Dict[str, Any]):
        """
        Set the application stylesheet based on the theme.
        
        Args:
            theme: Theme data dictionary
        """
        from . import styles  # Import here to avoid circular imports
        stylesheet = styles.generate_stylesheet(theme)
        self.app.setStyleSheet(stylesheet)

    def get_current_theme_data(self) -> Dict[str, Any]:
        """
        Get the current theme data.
        
        Returns:
            Dict containing the current theme data
        """
        if not self.current_theme:
            return {}
        return self.get_theme(self.current_theme) or {}
