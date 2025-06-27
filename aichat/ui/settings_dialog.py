"""Settings dialog for the AI Chat application.

This module provides a comprehensive settings dialog that allows users to configure
various aspects of the application, including appearance, chat behavior, AI model
settings, and privacy preferences. The dialog is designed to be user-friendly and
provides immediate feedback for changes.

Typical usage example:
    memory_manager = MemoryManager()
    dialog = SettingsDialog(memory_manager)
    if dialog.exec_() == QDialog.Accepted:
        # Settings were saved
        pass
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast, TypedDict

# Import localization
from aichat.i18n import (
    init_localization,
    get_localization,
    tr,
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES
)

from PyQt5.QtCore import QSize, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QColor, QFont, QIcon, QPalette
from PyQt5.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFontComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QStyle,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from aichat.memory import MemoryManager, UserPreferences, ChatMessage, AIProfile

# Type aliases for better code readability
ColorHex = str
ThemeName = str
FontSize = int

# Configure logging
logger = logging.getLogger(__name__)

class ProfileManagerWidget(QWidget):
    """A widget for managing AI profiles."""
    def __init__(self, memory_manager: 'MemoryManager', parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.memory_manager = memory_manager
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("AI Profile Management"))
        # Add profile management UI components here


class ChatMessage:
    """Represents a chat message in the conversation."""
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create a ChatMessage from a dictionary."""
        return cls()


class AIProfile:
    """Represents an AI profile with settings and personality."""
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIProfile':
        """Create an AIProfile from a dictionary."""
        return cls()


class UserPreferences:
    """Stores user preferences for the application."""
    def to_dict(self) -> Dict[str, Any]:
        """Convert preferences to a dictionary."""
        return {}
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load preferences from a dictionary."""
        pass


class MemoryManager:
    """Manages persistent storage for the application."""
    def __init__(self) -> None:
        self.preferences = UserPreferences()
    
    def transaction(self) -> 'MemoryManager':
        """Context manager for database transactions."""
        return self
    
    def clear_chat_history(self) -> None:
        """Clear all chat history."""
        pass
    
    def add_chat_message(self, message: ChatMessage) -> None:
        """Add a message to chat history."""
        pass
    
    def clear_ai_profiles(self) -> None:
        """Clear all AI profiles."""
        pass
    
    def add_ai_profile(self, profile: AIProfile) -> None:
        """Add an AI profile."""
        pass
    
    def update_preferences(self, preferences: UserPreferences) -> None:
        """Update user preferences."""
        pass

ThemeName = str  # Name of the theme (e.g., "dark", "light")
FontSize = int  # Font size in points

class ColorButton(QPushButton):
    """A button that shows a color and allows picking a new one.
    
    This widget provides a button that displays a color swatch and opens a color
    picker dialog when clicked. The selected color can be retrieved using the
    color() method or by connecting to the color_changed signal.
    
    Attributes:
        color_changed: Signal emitted when the color changes.
                      Parameter: The new color in hex format (str).
    """
    
    color_changed = pyqtSignal(str)  # Emits the new color in hex format
    
    def __init__(self, color: ColorHex = "#000000", parent: Optional[QWidget] = None) -> None:
        """Initialize the color button.
        
        Args:
            color: Initial color in hex format (e.g., "#RRGGBB").
            parent: Parent widget.
        """
        super().__init__(parent)
        self._color: ColorHex = color
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self) -> None:
        """Initialize the user interface components."""
        self.setFixedSize(32, 24)
        self._update_style()
    
    def _connect_signals(self) -> None:
        """Connect signals to slots."""
        self.clicked.connect(self._on_clicked)
    
    def _update_style(self) -> None:
        """Update the button's style based on the current color."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                border: 1px solid #444;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 2px solid #00f0ff;
                margin: -1px;
            }}
            QPushButton:pressed {{
                margin: 1px -1px -1px 1px;
            }}
        """)
    
    def color(self) -> ColorHex:
        """Get the current color.
        
        Returns:
            The current color in hex format (e.g., "#RRGGBB").
        """
        return self._color
    
    def set_color(self, color: ColorHex) -> None:
        """Set the current color.
        
        Args:
            color: New color in hex format (e.g., "#RRGGBB").
            
        Raises:
            ValueError: If the color format is invalid.
        """
        if not self._is_valid_hex_color(color):
            raise ValueError(f"Invalid color format: {color}. Expected format: #RRGGBB or #AARRGGBB")
            
        if color != self._color:
            self._color = color
            self._update_style()
            self.color_changed.emit(color)
    
    @staticmethod
    def _is_valid_hex_color(color: str) -> bool:
        """Check if a string is a valid hex color.
        
        Args:
            color: Color string to validate.
            
        Returns:
            True if the string is a valid hex color, False otherwise.
        """
        import re
        return bool(re.match(r'^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$', color))
    
    @pyqtSlot()
    def _on_clicked(self) -> None:
        """Handle button click by showing a color picker dialog."""
        self.pick_color()
    
    def pick_color(self) -> None:
        """Open a color picker dialog to select a new color.
        
        If the user selects a valid color, the color will be updated and the
        color_changed signal will be emitted.
        """
        color = QColorDialog.getColor(QColor(self._color), self, "Pick a color")
        if color.isValid():
            self.set_color(color.name())

class SettingsDialog(QDialog):
    """A comprehensive settings dialog for the AI Chat application.
    
    This dialog provides a tabbed interface for configuring all aspects of the
    application, including appearance, chat behavior, AI model settings, and
    privacy preferences. It integrates with the MemoryManager for persistent
    storage of user preferences.
    
    Signals:
        settings_updated: Emitted when settings are saved.
            Parameters:
                dict: A dictionary containing all settings.
        preferences_updated: Emitted when preferences are updated.
            Parameters:
                UserPreferences: The updated preferences object.
        theme_changed: Emitted when the theme is changed.
            Parameters:
                str: The name of the new theme.
        font_changed: Emitted when font settings are changed.
            Parameters:
                str: The font family name.
                int: The font size in points.
    """
    
    # Signal definitions with type hints
    settings_updated = pyqtSignal(dict)  # type: ignore[arg-type]
    preferences_updated = pyqtSignal(UserPreferences)  # type: ignore[arg-type]
    theme_changed = pyqtSignal(str)  # type: ignore[arg-type]
    font_changed = pyqtSignal(str, int)  # type: ignore[arg-type]
    
    # Default settings
    DEFAULT_THEME: ThemeName = "dark"
    DEFAULT_FONT_FAMILY: str = "Segoe UI"
    DEFAULT_FONT_SIZE: FontSize = 10
    MIN_WINDOW_WIDTH: int = 800
    MIN_WINDOW_HEIGHT: int = 600
    
    def __init__(self, memory_manager: MemoryManager, parent: Optional[QWidget] = None) -> None:
        """Initialize the settings dialog.
        
        Args:
            memory_manager: An instance of MemoryManager for persisting settings.
            parent: The parent widget of this dialog.
            
        Raises:
            TypeError: If memory_manager is not an instance of MemoryManager.
            RuntimeError: If there's an error initializing the UI.
        """
        super().__init__(parent)
        
        # Validate input parameters
        if not isinstance(memory_manager, MemoryManager):
            raise TypeError(
                f"memory_manager must be an instance of MemoryManager, "
                f"got {type(memory_manager).__name__} instead"
            )
        
        self.memory_manager = memory_manager
        
        try:
            # Load current preferences
            self.preferences = memory_manager.preferences
            
            # Initialize UI components
            self._init_ui()
            
            # Load current settings into the UI
            self.load_settings()
            
            # Apply the current theme
            self.apply_theme(self.preferences.theme)
            
            # Connect signals after UI is initialized
            self._connect_signals()
            
        except Exception as e:
            logger.exception("Failed to initialize settings dialog")
            raise RuntimeError(
                "Failed to initialize settings dialog. See logs for details."
            ) from e
    
    def _init_ui(self) -> None:
        """Initialize the user interface components."""
        self.setWindowTitle("Settings")
        self.setMinimumSize(self.MIN_WINDOW_WIDTH, self.MIN_WINDOW_HEIGHT)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Add tabs
        self.tab_widget.addTab(self._create_appearance_tab(), "Appearance")
        self.tab_widget.addTab(self._create_chat_tab(), "Chat")
        self.tab_widget.addTab(self._create_ai_tab(), "AI")
        self.tab_widget.addTab(self._create_privacy_tab(), "Privacy")
        self.tab_widget.addTab(self._create_profiles_tab(), "Profiles")
        
        # Add tabs to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Add dialog buttons
        self._add_dialog_buttons(main_layout)
    
    def _connect_signals(self) -> None:
        """Connect signals to slots."""
        # Connect theme changes
        theme_combo = self.findChild(QComboBox, "theme_combo")
        if theme_combo:
            theme_combo.currentTextChanged.connect(self.on_theme_changed)
        
        # Connect font changes
        font_family_combo = self.findChild(QComboBox, "font_family_combo")
        font_size_spin = self.findChild(QSpinBox, "font_size_spin")
        
        if font_family_combo:
            font_family_combo.currentFontChanged.connect(self._on_font_changed)
        if font_size_spin:
            font_size_spin.valueChanged.connect(self._on_font_changed)
    
    def _add_dialog_buttons(self, layout: QVBoxLayout) -> None:
        """Add dialog buttons to the layout.
        
        Args:
            layout: The layout to add buttons to.
        """
        button_box = QHBoxLayout()
        button_box.setSpacing(10)
        
        # Reset to Defaults button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setToolTip("Reset all settings to their default values")
        reset_btn.clicked.connect(self.reset_to_defaults)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        
        # Save button
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.save_settings)
        
        # Add buttons to layout
        button_box.addWidget(reset_btn)
        button_box.addStretch(1)
        button_box.addWidget(close_btn)
        button_box.addWidget(save_btn)
        
        layout.addLayout(button_box)
    
    def _create_appearance_tab(self) -> QWidget:
        """Create the appearance settings tab.
        
        Returns:
            QWidget: The configured appearance tab widget.
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Language settings
        lang_group = QGroupBox(tr("settings.language_group", default="Language & Region"))
        lang_layout = QFormLayout(lang_group)
        
        # Language selection
        self.language_combo = QComboBox()
        
        # Add available languages to the combo box
        for code, info in SUPPORTED_LANGUAGES.items():
            self.language_combo.addItem(f"{info['name']} ({info['native']})", code)
        
        # Set current language
        current_lang = get_localization().current_language
        current_index = self.language_combo.findData(current_lang)
        if current_index >= 0:
            self.language_combo.setCurrentIndex(current_index)
        
        lang_layout.addRow(tr("settings.language", default="Language:"), self.language_combo)
        
        # RTL layout checkbox (only show for RTL languages)
        self.rtl_checkbox = QCheckBox(tr("settings.enable_rtl", default="Enable right-to-left layout"))
        self.rtl_checkbox.setChecked(get_localization().is_rtl())
        self.rtl_checkbox.setVisible(get_localization().is_rtl())
        lang_layout.addRow("", self.rtl_checkbox)
        
        layout.addWidget(lang_group)
        
        # Theme settings
        theme_group = QGroupBox(tr("settings.theme_group", default="Theme"))
        theme_layout = QFormLayout(theme_group)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            tr("theme.dark", default="Dark"),
            tr("theme.light", default="Light"),
            tr("theme.system", default="System")
        ])
        theme_layout.addRow(tr("settings.color_theme", default="Color theme:"), self.theme_combo)
        
        # Accent color
        self.accent_color_btn = ColorButton("#0078d7")  # Default blue
        theme_layout.addRow(tr("settings.accent_color", default="Accent color:"), self.accent_color_btn)
        
        layout.addWidget(theme_group)
        
        # Font settings
        font_group = QGroupBox("Font")
        font_layout = QFormLayout()
        
        # Font family selection
        self.font_family_combo = QFontComboBox()
        font_layout.addRow("Font family:", self.font_family_combo)
        
        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(10)
        font_layout.addRow("Font size:", self.font_size_spin)
        
        # Font preview
        self.font_preview = QLabel("The quick brown fox jumps over the lazy dog")
        self.font_preview.setAlignment(Qt.AlignCenter)
        self.font_preview.setFrameStyle(QLabel.Panel | QLabel.Sunken)
        self.font_preview.setMargin(10)
        font_layout.addRow(self.font_preview)
        
        font_group.setLayout(font_layout)
        
        # Add groups to layout
        layout.addWidget(font_group)
        layout.addStretch(1)
        
        return tab
    
    def _create_chat_tab(self) -> QWidget:
        """Create the chat settings tab.
        
        Returns:
            QWidget: The configured chat settings tab widget.
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Display settings
        display_group = QGroupBox("Display")
        display_layout = QVBoxLayout()
        
        # Chat display options
        self.show_timestamps_cb = QCheckBox("Show timestamps")
        self.show_typing_cb = QCheckBox("Show typing indicators")
        self.markdown_rendering_cb = QCheckBox("Enable markdown rendering")
        self.link_preview_cb = QCheckBox("Show link previews")
        self.emoji_picker_cb = QCheckBox("Show emoji picker")
        
        display_layout.addWidget(self.show_timestamps_cb)
        display_layout.addWidget(self.show_typing_cb)
        display_layout.addWidget(self.markdown_rendering_cb)
        display_layout.addWidget(self.link_preview_cb)
        display_layout.addWidget(self.emoji_picker_cb)
        
        display_group.setLayout(display_layout)
        
        # Message history
        history_group = QGroupBox("Message History")
        history_layout = QFormLayout()
        
        self.history_limit_spin = QSpinBox()
        self.history_limit_spin.setRange(10, 1000)
        self.history_limit_spin.setSuffix(" messages")
        
        self.auto_clear_cb = QCheckBox("Clear history on exit")
        history_layout.addRow("History limit:", self.history_limit_spin)
        history_layout.addRow("", self.auto_clear_cb)
        
        clear_history_btn = QPushButton("Clear History Now")
        clear_history_btn.clicked.connect(self.clear_chat_history)
        history_layout.addRow("", clear_history_btn)
        
        history_group.setLayout(history_layout)
        
        # Add all groups to the main layout
        layout.addWidget(display_group)
        layout.addWidget(history_group)
        layout.addStretch(1)
        
        return tab
    
    def _create_ai_tab(self) -> QWidget:
        """Create the AI settings tab.
        
        Returns:
            QWidget: The configured AI settings tab widget.
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Model settings
        model_group = QGroupBox("AI Model")
        model_layout = QFormLayout()
        
        # Model selection
        self.model_combo = QComboBox()
        self.model_combo.addItems(["GPT-4", "GPT-3.5 Turbo", "Claude 2", "Claude Instant"])
        model_layout.addRow("Model:", self.model_combo)
        
        # Temperature
        self.temperature_slider = QSlider(Qt.Horizontal)
        self.temperature_slider.setRange(0, 200)  # 0.0 to 2.0 in 0.01 increments
        self.temperature_slider.setValue(70)  # Default to 0.7
        model_layout.addRow("Creativity:", self.temperature_slider)
        
        # Max tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 8000)
        self.max_tokens_spin.setValue(2048)
        model_layout.addRow("Max tokens:", self.max_tokens_spin)
        
        # Context window
        self.context_window_cb = QCheckBox("Use extended context window")
        model_layout.addRow("", self.context_window_cb)
        
        model_group.setLayout(model_layout)
        
        # Memory settings
        memory_group = QGroupBox("Memory")
        memory_layout = QVBoxLayout()
        
        self.memory_enabled_cb = QCheckBox("Enable conversation memory")
        self.memory_summary_cb = QCheckBox("Generate conversation summaries")
        
        memory_layout.addWidget(self.memory_enabled_cb)
        memory_layout.addWidget(self.memory_summary_cb)
        memory_layout.addStretch(1)
        
        memory_group.setLayout(memory_layout)
        
        # Add all groups to the main layout
        layout.addWidget(model_group)
        layout.addWidget(memory_group)
        layout.addStretch(1)
        
        return tab
    
    def _create_privacy_tab(self) -> QWidget:
        """Create the privacy settings tab.
        
        Returns:
            QWidget: The configured privacy settings tab widget.
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Data collection
        data_group = QGroupBox("Data Collection")
        data_layout = QVBoxLayout()
        
        self.analytics_cb = QCheckBox("Send anonymous usage statistics")
        self.crash_reports_cb = QCheckBox("Automatically send crash reports")
        self.typing_analytics_cb = QCheckBox("Help improve suggestions by sending typing data")
        
        data_layout.addWidget(self.analytics_cb)
        data_layout.addWidget(self.crash_reports_cb)
        data_layout.addWidget(self.typing_analytics_cb)
        data_layout.addStretch(1)
        
        data_group.setLayout(data_layout)
        
        # Data management
        manage_group = QGroupBox("Data Management")
        manage_layout = QVBoxLayout()
        
        export_btn = QPushButton("Export All Data...")
        export_btn.clicked.connect(self.export_data)
        
        import_btn = QPushButton("Import Data...")
        import_btn.clicked.connect(self.import_data)
        
        manage_layout.addWidget(export_btn)
        manage_layout.addWidget(import_btn)
        manage_layout.addStretch(1)
        
        manage_group.setLayout(manage_layout)
        
        # Add all groups to the main layout
        layout.addWidget(data_group)
        layout.addWidget(manage_group)
        layout.addStretch(1)
        
        return tab
    
    def _create_profiles_tab(self) -> QWidget:
        """Create the AI profiles management tab.
        
        Returns:
            QWidget: The configured profiles tab widget.
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Add the profile manager widget
        self.profile_manager = ProfileManagerWidget(self.memory_manager)
        layout.addWidget(self.profile_manager)
        
        return tab
    
    def clear_chat_history(self) -> None:
        """Clear all chat history after confirmation."""
        try:
            reply = QMessageBox.question(
                self,
                "Confirm Clear History",
                "Are you sure you want to clear all chat history?\n\n"
                "This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.memory_manager.clear_chat_history()
                QMessageBox.information(
                    self,
                    "History Cleared",
                    "Chat history has been cleared successfully.",
                    QMessageBox.Ok
                )
                logger.info("Chat history cleared")
                
        except Exception as e:
            logger.error(f"Failed to clear chat history: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Clear History Error",
                f"Failed to clear chat history: {e}",
                QMessageBox.Ok
            )
    
    def export_data(self) -> None:
        """Export application data to a file."""
        try:
            # Get save file path
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Application Data",
                os.path.expanduser("~/aichat_export.json"),
                "JSON Files (*.json);;All Files (*)"
            )
            
            if not file_path:
                return  # User cancelled
                
            # Add .json extension if not present
            if not file_path.lower().endswith('.json'):
                file_path += '.json'
            
            # Prepare data for export
            export_data = {
                'version': 1,
                'preferences': self.preferences.to_dict(),
                'chat_history': [msg.to_dict() for msg in self.memory_manager.get_chat_history()],
                'ai_profiles': [profile.to_dict() for profile in self.memory_manager.get_ai_profiles()],
                'exported_at': datetime.now().isoformat(),
            }
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Application data has been exported to:\n{file_path}",
                QMessageBox.Ok
            )
            logger.info(f"Application data exported to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export data: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export data: {e}",
                QMessageBox.Ok
            )
    
    def import_data(self) -> None:
        """Import application data from a file."""
        try:
            # Get file path
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Application Data",
                os.path.expanduser("~"),
                "JSON Files (*.json);;All Files (*)"
            )
            
            if not file_path or not os.path.exists(file_path):
                return  # User cancelled or file doesn't exist
            
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate import data
            if not isinstance(import_data, dict) or 'version' not in import_data:
                raise ValueError("Invalid import file format")
            
            # Ask for confirmation
            reply = QMessageBox.question(
                self,
                "Confirm Import",
                "This will overwrite your current settings and data.\n"
                "Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Import data within a transaction
            with self.memory_manager.transaction():
                # Import preferences
                if 'preferences' in import_data:
                    self.preferences.from_dict(import_data['preferences'])
                    self.memory_manager.update_preferences(self.preferences)
                
                # Import chat history
                if 'chat_history' in import_data:
                    self.memory_manager.clear_chat_history()
                    for msg_data in import_data['chat_history']:
                        message = ChatMessage.from_dict(msg_data)
                        self.memory_manager.add_chat_message(message)
                
                # Import AI profiles
                if 'ai_profiles' in import_data:
                    self.memory_manager.clear_ai_profiles()
                    for profile_data in import_data['ai_profiles']:
                        profile = AIProfile.from_dict(profile_data)
                        self.memory_manager.add_ai_profile(profile)
            
            # Reload settings in UI after transaction completes
            self.load_settings()
            
            # Show success message
            QMessageBox.information(
                self,
                "Import Successful",
                "Application data has been imported successfully.",
                QMessageBox.Ok
            )
            logger.info(f"Application data imported from {file_path}")
            
            # Emit signals to update the rest of the application
            self.settings_updated.emit(self._get_all_settings())
            self.preferences_updated.emit(self.preferences)
            self.theme_changed.emit(self.preferences.theme)
            
        except Exception as e:
            logger.error(f"Failed to import data: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import data: {e}",
                QMessageBox.Ok
            )
    
    def init_ui(self):
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabPosition(QTabWidget.West)
        main_layout.addWidget(self.tab_widget)
        
        # Add tabs
        self.appearance_tab = self.create_appearance_tab()
        self.chat_tab = self.create_chat_tab()
        self.ai_tab = self.create_ai_tab()
        self.privacy_tab = self.create_privacy_tab()
        self.profiles_tab = self.create_profiles_tab()
        
        self.tab_widget.addTab(self.appearance_tab, self.style().standardIcon(QStyle.SP_DesktopIcon), "Appearance")
        self.tab_widget.addTab(self.chat_tab, self.style().standardIcon(QStyle.SP_MessageBoxInformation), "Chat")
        self.tab_widget.addTab(self.ai_tab, self.style().standardIcon(QStyle.SP_ComputerIcon), "AI")
        self.tab_widget.addTab(self.privacy_tab, self.style().standardIcon(QStyle.SP_MessageBoxShield), "Privacy")
        self.tab_widget.addTab(self.profiles_tab, self.style().standardIcon(QStyle.SP_FileDialogDetailedView), "Profiles")
        
        # Buttons
        button_box = QHBoxLayout()
        button_box.addStretch()
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.save_settings)
        
        button_box.addWidget(self.reset_btn)
        button_box.addStretch()
        button_box.addWidget(self.cancel_btn)
        button_box.addWidget(self.save_btn)
        
        main_layout.addLayout(button_box)
        
        # Apply theme
        self.update_theme_preview()
        
        # Connect signals
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        self.font_family_combo.currentFontChanged.connect(self.update_font_preview)
        self.font_size_spin.valueChanged.connect(self.update_font_preview)
        
        # Load current settings
        self.load_settings()
    
    def create_appearance_tab(self) -> QWidget:
        """Create the appearance settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Language settings
        lang_group = QGroupBox(tr("settings.language_group", default="Language & Region"))
        lang_layout = QFormLayout(lang_group)
        
        # Language selection
        self.language_combo = QComboBox()
        
        # Add available languages to the combo box
        for code, info in SUPPORTED_LANGUAGES.items():
            self.language_combo.addItem(f"{info['name']} ({info['native']})", code)
        
        # Set current language
        current_lang = get_localization().current_language
        current_index = self.language_combo.findData(current_lang)
        if current_index >= 0:
            self.language_combo.setCurrentIndex(current_index)
        
        lang_layout.addRow(tr("settings.language", default="Language:"), self.language_combo)
        
        # RTL layout checkbox (only show for RTL languages)
        self.rtl_checkbox = QCheckBox(tr("settings.enable_rtl", default="Enable right-to-left layout"))
        self.rtl_checkbox.setChecked(get_localization().is_rtl())
        self.rtl_checkbox.setVisible(get_localization().is_rtl())
        lang_layout.addRow("", self.rtl_checkbox)
        
        layout.addWidget(lang_group)
        
        # Theme settings
        theme_group = QGroupBox(tr("settings.theme_group", default="Theme"))
        theme_layout = QFormLayout(theme_group)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            tr("theme.dark", default="Dark"),
            tr("theme.light", default="Light"),
            tr("theme.system", default="System")
        ])
        theme_layout.addRow(tr("settings.color_theme", default="Color theme:"), self.theme_combo)
        
        # Accent color
        self.accent_color_btn = ColorButton("#0078d7")  # Default blue
        theme_layout.addRow(tr("settings.accent_color", default="Accent color:"), self.accent_color_btn)
        
        layout.addWidget(theme_group)
        
        # Font settings
        font_group = QGroupBox("Font")
        font_layout = QFormLayout()
        
        self.font_family_combo = QFontComboBox()
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 32)
        self.font_size_spin.setValue(12)
        
        self.font_preview = QLabel("The quick brown fox jumps over the lazy dog")
        self.font_preview.setAlignment(Qt.AlignCenter)
        self.font_preview.setFrameStyle(QLabel.Panel | QLabel.Sunken)
        self.font_preview.setMargin(10)
        
        font_layout.addRow("Font Family:", self.font_family_combo)
        font_layout.addRow("Font Size:", self.font_size_spin)
        font_layout.addRow(self.font_preview)
        
        font_group.setLayout(font_layout)
        
        # Add groups to layout
        layout.addWidget(font_group)
        layout.addStretch()
        
        return tab
    
    def create_chat_tab(self) -> QWidget:
        """Create the chat settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Display options
        display_group = QGroupBox("Display Options")
        display_layout = QVBoxLayout()
        display_group.setLayout(display_layout)
        
        self.show_timestamps_cb = QCheckBox("Show timestamps")
        self.show_typing_cb = QCheckBox("Show typing indicator")
        self.markdown_rendering_cb = QCheckBox("Enable Markdown rendering")
        self.link_preview_cb = QCheckBox("Show link previews")
        self.emoji_picker_cb = QCheckBox("Show emoji picker")
        
        display_layout.addWidget(self.show_timestamps_cb)
        display_layout.addWidget(self.show_typing_cb)
        display_layout.addWidget(self.markdown_rendering_cb)
        display_layout.addWidget(self.link_preview_cb)
        display_layout.addWidget(self.emoji_picker_cb)
        
        # Message history
        history_group = QGroupBox("Message History")
        history_layout = QFormLayout()
        history_group.setLayout(history_layout)
        
        self.history_limit_spin = QSpinBox()
        self.history_limit_spin.setRange(10, 1000)
        self.history_limit_spin.setSuffix(" messages")
        
        self.auto_clear_cb = QCheckBox("Clear history on exit")
        history_layout.addRow("Maximum messages to keep:", self.history_limit_spin)
        history_layout.addRow(self.auto_clear_cb)
        
        # Add groups to layout
        layout.addWidget(display_group)
        layout.addWidget(history_group)
        layout.addStretch()
        
        return tab
    
    def create_ai_tab(self) -> QWidget:
        """Create the AI settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Model settings
        model_group = QGroupBox("AI Model")
        model_layout = QFormLayout()
        model_group.setLayout(model_layout)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["GPT-4", "GPT-3.5", "Claude 2", "Llama 2"])
        
        self.temperature_slider = QSlider(Qt.Horizontal)
        self.temperature_slider.setRange(0, 100)
        self.temperature_slider.setValue(70)  # Default to 0.7
        
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 8000)
        self.max_tokens_spin.setValue(2048)
        
        model_layout.addRow("Model:", self.model_combo)
        model_layout.addRow("Temperature (creativity):", self.temperature_slider)
        model_layout.addRow("Max tokens per response:", self.max_tokens_spin)
        
        # Context settings
        context_group = QGroupBox("Context & Memory")
        context_layout = QVBoxLayout()
        context_group.setLayout(context_layout)
        
        self.context_window_cb = QCheckBox("Enable context window")
        self.memory_enabled_cb = QCheckBox("Enable conversation memory")
        self.memory_summary_cb = QCheckBox("Generate conversation summaries")
        
        context_layout.addWidget(self.context_window_cb)
        context_layout.addWidget(self.memory_enabled_cb)
        context_layout.addWidget(self.memory_summary_cb)
        
        # Add groups to layout
        layout.addWidget(model_group)
        layout.addWidget(context_group)
        layout.addStretch()
        
        return tab
    
    def create_privacy_tab(self) -> QWidget:
        """Create the privacy settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Data collection
        data_group = QGroupBox("Data Collection")
        data_layout = QVBoxLayout()
        data_group.setLayout(data_layout)
        
        self.analytics_cb = QCheckBox("Send anonymous usage statistics")
        self.crash_reports_cb = QCheckBox("Automatically send crash reports")
        self.typing_analytics_cb = QCheckBox("Help improve typing suggestions")
        
        data_layout.addWidget(self.analytics_cb)
        data_layout.addWidget(self.crash_reports_cb)
        data_layout.addWidget(self.typing_analytics_cb)
        
        # Data management
        manage_group = QGroupBox("Data Management")
        manage_layout = QVBoxLayout()
        manage_group.setLayout(manage_layout)
        
        self.clear_history_btn = QPushButton("Clear Chat History")
        self.clear_history_btn.clicked.connect(self.clear_chat_history)
        
        self.export_data_btn = QPushButton("Export All Data...")
        self.export_data_btn.clicked.connect(self.export_data)
        
        self.import_data_btn = QPushButton("Import Data...")
        self.import_data_btn.clicked.connect(self.import_data)
        
        manage_layout.addWidget(self.clear_history_btn)
        manage_layout.addWidget(self.export_data_btn)
        manage_layout.addWidget(self.import_data_btn)
        
        # Add groups to layout
        layout.addWidget(data_group)
        layout.addWidget(manage_group)
        layout.addStretch()
        
        return tab
    
    def create_profiles_tab(self) -> QWidget:
        """Create the AI profiles management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create profile manager widget
        from ..profiles.manager import ProfileManager
        profile_manager = ProfileManager()
        self.profile_widget = ProfileManagerWidget(profile_manager)
        
        layout.addWidget(self.profile_widget)
        
        return tab
        
    # Settings management methods
    
    def load_settings(self) -> None:
        """Load current settings into the UI."""
        # Load language settings
        current_lang = self.preferences.get("language", DEFAULT_LANGUAGE)
        current_index = self.language_combo.findData(current_lang)
        if current_index >= 0:
            self.language_combo.setCurrentIndex(current_index)
            
        # Load RTL setting if available
        if "rtl_layout" in self.preferences:
            self.rtl_checkbox.setChecked(self.preferences["rtl_layout"])
            
        # Load theme
        theme = self.preferences.get("theme", "dark").capitalize()
        theme_text = tr(f"theme.{theme.lower()}", default=theme)
        index = self.theme_combo.findText(theme_text, Qt.MatchFixedString)
        if index < 0 and self.theme_combo.count() > 0:
            index = 0  # Default to first theme if not found
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
            
        # Load accent color if available
        if "accent_color" in self.preferences:
            self.accent_color_btn.set_color(self.preferences["accent_color"])
            
        # Load font settings
        if "font_family" in self.preferences:
            self.font_family_combo.setCurrentFont(QFont(self.preferences["font_family"]))
        if "font_size" in self.preferences:
            self.font_size_spin.setValue(self.preferences["font_size"])
        
        # Chat settings
        self.show_timestamps_cb.setChecked(self.preferences.get('show_timestamps', True))
        self.show_typing_cb.setChecked(self.preferences.get('show_typing_indicator', True))
        self.markdown_rendering_cb.setChecked(self.preferences.get('markdown_rendering', True))
        self.link_preview_cb.setChecked(self.preferences.get('link_preview', True))
        self.emoji_picker_cb.setChecked(self.preferences.get('emoji_picker', True))
        self.history_limit_spin.setValue(self.preferences.get('history_limit', 100))
        self.auto_clear_cb.setChecked(self.preferences.get('auto_clear_history', False))
        
        # AI settings
        self.model_combo.setCurrentText(self.preferences.get('ai_model', 'GPT-4'))
        self.temperature_slider.setValue(int(self.preferences.get('temperature', 0.7) * 100))
        self.max_tokens_spin.setValue(self.preferences.get('max_tokens', 2048))
        self.context_window_cb.setChecked(self.preferences.get('context_window', True))
        self.memory_enabled_cb.setChecked(self.preferences.get('memory_enabled', True))
        self.memory_summary_cb.setChecked(self.preferences.get('memory_summaries', True))
        
        # Privacy settings
        self.analytics_cb.setChecked(self.preferences.get('analytics_enabled', False))
        self.crash_reports_cb.setChecked(self.preferences.get('crash_reports', True))
        self.typing_analytics_cb.setChecked(self.preferences.get('typing_analytics', False))
    
    def save_settings(self) -> Dict[str, Any]:
        """Save settings from UI to preferences.
        
        Returns:
            Dict[str, Any]: Dictionary of all settings.
        """
        settings = {}
        
        # Language settings
        lang_index = self.language_combo.currentIndex()
        if lang_index >= 0:
            lang_code = self.language_combo.currentData()
            settings["language"] = lang_code
            
            # Update RTL setting based on selected language
            is_rtl = SUPPORTED_LANGUAGES.get(lang_code, {}).get("rtl", False)
            settings["rtl_layout"] = is_rtl and self.rtl_checkbox.isChecked()
        
        # Theme settings
        theme_text = self.theme_combo.currentText()
        # Map translated theme names back to internal values
        theme_map = {
            tr("theme.dark", default="Dark"): "dark",
            tr("theme.light", default="Light"): "light",
            tr("theme.system", default="System"): "system"
        }
        settings["theme"] = theme_map.get(theme_text, "dark")
        settings["accent_color"] = self.accent_color_btn.color()
        
        # Font settings
        settings["font_family"] = self.font_family_combo.currentFont().family()
        settings["font_size"] = self.font_size_spin.value()
        
        # Chat settings
        settings["show_timestamps"] = self.show_timestamps_cb.isChecked()
        settings["show_typing_indicator"] = self.show_typing_cb.isChecked()
        settings["markdown_rendering"] = self.markdown_rendering_cb.isChecked()
        settings["link_preview"] = self.link_preview_cb.isChecked()
        settings["emoji_picker"] = self.emoji_picker_cb.isChecked()
        settings["history_limit"] = self.history_limit_spin.value()
        settings["auto_clear_history"] = self.auto_clear_cb.isChecked()
        
        # AI settings
        settings["ai_model"] = self.model_combo.currentText()
        settings["temperature"] = self.temperature_slider.value() / 100.0
        settings["max_tokens"] = self.max_tokens_spin.value()
        settings["context_window"] = self.context_window_cb.isChecked()
        settings["memory_enabled"] = self.memory_enabled_cb.isChecked()
        settings["memory_summaries"] = self.memory_summary_cb.isChecked()
        
        # Privacy settings
        settings["analytics_enabled"] = self.analytics_cb.isChecked()
        settings["crash_reports"] = self.crash_reports_cb.isChecked()
        settings["typing_analytics"] = self.typing_analytics_cb.isChecked()
        
        # Save to memory manager
        self.memory_manager.update_preferences(settings)
        
        # Emit signals
        self.settings_updated.emit(settings)
        self.preferences_updated.emit(self.preferences)
        
        return settings
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        reply = QMessageBox.question(
            self, 
            'Reset Settings',
            'Are you sure you want to reset all settings to their default values?\n\nThis cannot be undone.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset to default preferences
            self.preferences = UserPreferences()
            self.load_settings()
            
            # Apply changes immediately
            self.theme_changed.emit(self.preferences.theme)
            self.font_changed.emit(self.preferences.font_family, self.preferences.font_size)
    
    # Theme and appearance methods
    
    def on_language_changed(self, index: int) -> None:
        """Handle language change.
        
        Args:
            index: Index of the selected language in the combo box.
        """
        if index >= 0:
            lang_code = self.language_combo.currentData()
            # Update RTL checkbox visibility based on selected language
            is_rtl = SUPPORTED_LANGUAGES.get(lang_code, {}).get("rtl", False)
            self.rtl_checkbox.setVisible(is_rtl)
            
            # If switching to an RTL language, enable RTL by default
            if is_rtl and not self.preferences.get("rtl_layout", False):
                self.rtl_checkbox.setChecked(True)
    
    def on_rtl_toggled(self, checked: bool) -> None:
        """Handle RTL layout toggle.
        
        Args:
            checked: Whether RTL layout is enabled.
        """
        self.preferences["rtl_layout"] = checked
        # Emit signal to update the UI direction
        QApplication.instance().setLayoutDirection(
            Qt.RightToLeft if checked else Qt.LeftToRight
        )
    
    def on_theme_changed(self, theme_name: str) -> None:
        """Handle theme change.
        
        Args:
            theme_name: Display name of the selected theme.
        """
        # Map the translated theme name back to internal theme name
        theme_map = {
            tr("theme.dark", default="Dark"): "dark",
            tr("theme.light", default="Light"): "light",
            tr("theme.system", default="System"): "system"
        }
        theme = theme_map.get(theme_name, "dark")
        self.preferences["theme"] = theme
        self.theme_changed.emit(theme)
        self.apply_theme(theme)
        
        # Apply theme-specific styles
        if theme == "dark":
            self.setStyleSheet("""
                QDialog { background-color: #1e1e2e; color: #cdd6f4; }
                QLabel { color: #cdd6f4; }
                QGroupBox::title { color: #89b4fa; }
                #theme_preview {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e1e2e, stop:1 #181825);
                    border: 1px solid #313244;
                    border-radius: 6px;
                }
            """)
        elif theme == "light":
            self.setStyleSheet("""
                QDialog { background-color: #f5f5f5; color: #333333; }
                QLabel { color: #333333; }
                QGroupBox::title { color: #1e66f5; }
                #theme_preview { 
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f5f5f5, stop:1 #e6e6e6);
                    border: 1px solid #d4d4d4;
                    border-radius: 6px;
                }
            """)
        # Add more themes as needed
        
        # Update the preview
        self.update_theme_preview()
    
    def update_theme_preview(self) -> None:
        """Update the theme preview based on current settings."""
        theme_name = self.theme_combo.currentText()
        preview = self.findChild(QLabel, "theme_preview")
        if preview:
            if theme_name == "dark":
                preview.setText("Dark Theme Preview\nSleek and easy on the eyes")
            elif theme_name == "light":
                preview.setText("Light Theme Preview\nClean and professional")
            # Add more previews for other themes
    
    def update_font_preview(self) -> None:
        """Update the font preview with current font settings."""
        font = self.font_family_combo.currentFont()
        font.setPointSize(self.font_size_spin.value())
        self.font_preview.setFont(font)
    
    # Data management methods
    
    def clear_chat_history(self) -> None:
        """Clear all chat history."""
        reply = QMessageBox.question(
            self, 
            'Clear Chat History',
            'Are you sure you want to delete all chat history?\n\nThis action cannot be undone.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Clear all conversations
                for conv in self.memory_manager.list_conversations():
                    self.memory_manager.delete_conversation(conv.id)
                
                QMessageBox.information(
                    self,
                    'Success',
                    'All chat history has been cleared.',
                    QMessageBox.Ok
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    'Error',
                    f'Failed to clear chat history: {str(e)}',
                    QMessageBox.Ok
                )
    
    def export_data(self) -> None:
        """Export application data to a file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Export Data',
            os.path.expanduser('~/aichat_export.json'),
            'JSON Files (*.json);;All Files (*)'
        )
        
        if file_path:
            try:
                # Prepare data for export
                export_data = {
                    'preferences': self.memory_manager.preferences.__dict__,
                    'conversations': [
                        conv.to_dict() 
                        for conv in self.memory_manager.list_conversations(include_archived=True)
                    ]
                }
                
                # Save to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2)
                
                QMessageBox.information(
                    self,
                    'Export Complete',
                    f'Successfully exported data to:\n{file_path}',
                    QMessageBox.Ok
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    'Export Failed',
                    f'Failed to export data: {str(e)}',
                    QMessageBox.Ok
                )
    
    def import_data(self) -> None:
        """Import application data from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Import Data',
            os.path.expanduser('~'),
            'JSON Files (*.json);;All Files (*)'
        )
        
        if file_path:
            try:
                # Ask for confirmation
                reply = QMessageBox.question(
                    self,
                    'Confirm Import',
                    'This will overwrite your current settings and conversations. Continue?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Load data from file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        import_data = json.load(f)
                    
                    # Import preferences
                    if 'preferences' in import_data:
                        for key, value in import_data['preferences'].items():
                            if hasattr(self.memory_manager.preferences, key):
                                setattr(self.memory_manager.preferences, key, value)
                    
                    # Import conversations
                    if 'conversations' in import_data:
                        for conv_data in import_data['conversations']:
                            try:
                                # Skip if conversation with same ID already exists
                                if not self.memory_manager.get_conversation(conv_data['id']):
                                    conv = Conversation.from_dict(conv_data)
                                    self.memory_manager._conversations[conv.id] = conv
                            except Exception as e:
                                print(f"Failed to import conversation: {e}")
                    
                    # Save changes
                    self.memory_manager._save_preferences()
                    self.memory_manager._save_conversations()
                    
                    # Reload settings
                    self.load_settings()
                    
                    QMessageBox.information(
                        self,
                        'Import Complete',
                        'Successfully imported data.',
                        QMessageBox.Ok
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    'Import Failed',
                    f'Failed to import data: {str(e)}',
                    QMessageBox.Ok
                )


# For testing the dialog
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from ..memory.manager import MemoryManager
    
    app = QApplication(sys.argv)
    
    # Create memory manager with test data
    memory_manager = MemoryManager()
    
    # Create and show the dialog
    dialog = SettingsDialog(memory_manager)
    dialog.show()
    
    sys.exit(app.exec_())
        # Appearance Group
        appearance_group = QGroupBox("APPEARANCE")
        appearance_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #00f0ff;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
        """)
        
        appearance_layout = QFormLayout()
        appearance_layout.setContentsMargins(15, 15, 15, 15)
        appearance_layout.setSpacing(10)
        
        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["cyberpunk", "dark", "light"])
        self.theme_combo.setCurrentText(self.settings["theme"])
        self.theme_combo.setStyleSheet("""
            QComboBox {
                background: #0a0a12;
                color: #e0e0ff;
                border: 1px solid #00f0ff;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 150px;
            }
            QComboBox:hover {
                border: 1px solid #ff00ff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
        """)
        appearance_layout.addRow("Theme:", self.theme_combo)
        
        # Font Size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(self.settings["font_size"])
        self.font_size_spin.setStyleSheet("""
            QSpinBox {
                background: #0a0a12;
                color: #e0e0ff;
                border: 1px solid #00f0ff;
                border-radius: 4px;
                padding: 5px;
                min-width: 60px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                border: none;
            }
        """)
        appearance_layout.addRow("Font Size:", self.font_size_spin)
        
        appearance_group.setLayout(appearance_layout)
        
        # AI Settings Group
        ai_group = QGroupBox("AI SETTINGS")
        ai_group.setStyleSheet(appearance_group.styleSheet())
        
        ai_layout = QFormLayout()
        ai_layout.setContentsMargins(15, 15, 15, 15)
        ai_layout.setSpacing(10)
        
        # Max Tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 4096)
        self.max_tokens_spin.setValue(self.settings["max_tokens"])
        self.max_tokens_spin.setStyleSheet(self.font_size_spin.styleSheet())
        ai_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        # Temperature
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.1, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(self.settings["temperature"])
        self.temp_spin.setStyleSheet(self.font_size_spin.styleSheet())
        ai_layout.addRow("Temperature:", self.temp_spin)
        
        # Top P
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.1, 1.0)
        self.top_p_spin.setSingleStep(0.1)
        self.top_p_spin.setValue(self.settings["top_p"])
        self.top_p_spin.setStyleSheet(self.font_size_spin.styleSheet())
        ai_layout.addRow("Top P:", self.top_p_spin)
        
        ai_group.setLayout(ai_layout)
        
        # Chat Settings Group
        chat_group = QGroupBox("CHAT SETTINGS")
        chat_group.setStyleSheet(appearance_group.styleSheet())
        
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(15, 15, 15, 15)
        chat_layout.setSpacing(10)
        
        # Stream Responses
        self.stream_check = QCheckBox("Stream responses")
        self.stream_check.setChecked(self.settings["stream_responses"])
        chat_layout.addWidget(self.stream_check)
        
        # Show Timestamps
        self.timestamps_check = QCheckBox("Show message timestamps")
        self.timestamps_check.setChecked(self.settings["show_timestamps"])
        chat_layout.addWidget(self.timestamps_check)
        
        # Show Typing Indicator
        self.typing_check = QCheckBox("Show typing indicator")
        self.typing_check.setChecked(self.settings["show_typing_indicator"])
        chat_layout.addWidget(self.typing_check)
        
        chat_group.setLayout(chat_layout)
        
        # Add groups to form
        form_layout.addWidget(appearance_group)
        form_layout.addWidget(ai_group)
        form_layout.addWidget(chat_group)
        form_layout.addStretch()
        
        # Set scroll widget
        scroll.setWidget(container)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Reset Button
        self.reset_btn = QPushButton("DEFAULT")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #00f0ff;
                border: 1px solid #00f0ff;
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: rgba(0, 240, 255, 0.1);
                border: 1px solid #ff00ff;
                color: #ff00ff;
            }
            QPushButton:pressed {
                background: rgba(255, 0, 255, 0.2);
            }
        """)
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        
        # Cancel Button
        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ff5555;
                border: 1px solid #ff5555;
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: rgba(255, 85, 85, 0.1);
                border: 1px solid #ff9999;
                color: #ff9999;
            }
            QPushButton:pressed {
                background: rgba(255, 85, 85, 0.2);
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        # Save Button
        self.save_btn = QPushButton("SAVE CHANGES")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                          stop:0 #ff00ff, stop:1 #00f0ff);
                color: #0a0a12;
                border: none;
                border-radius: 4px;
                padding: 8px 25px;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 1px;
                min-width: 150px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #ff69b4, stop:1 #00c8d7);
                box-shadow: 0 0 15px rgba(0, 240, 255, 0.5);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #cc00cc, stop:1 #008c99);
            }
        """)
        self.save_btn.clicked.connect(self.accept)
        
        # Add buttons to layout
        buttons_layout.addWidget(self.reset_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.save_btn)
        
        # Add widgets to main layout
        main_layout.addWidget(scroll)
        main_layout.addLayout(buttons_layout)
        
        # Set main layout
        self.setLayout(main_layout)
        
        # Apply cyberpunk style to checkboxes
        checkbox_style = """
            QCheckBox {
                color: #e0e0ff;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #00f0ff;
                border-radius: 3px;
                background: #0a0a12;
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                          stop:0 #ff00ff, stop:1 #00f0ff);
                border: 1px solid #00f0ff;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #ff00ff;
            }
        """
        
        for checkbox in [self.stream_check, self.timestamps_check, self.typing_check]:
            checkbox.setStyleSheet(checkbox_style)
    
    def get_settings(self) -> Dict[str, Any]:
        """Get the current settings from the UI."""
        return {
            "theme": self.theme_combo.currentText(),
            "font_size": self.font_size_spin.value(),
            "max_tokens": self.max_tokens_spin.value(),
            "temperature": self.temp_spin.value(),
            "top_p": self.top_p_spin.value(),
            "stream_responses": self.stream_check.isChecked(),
            "show_timestamps": self.timestamps_check.isChecked(),
            "show_typing_indicator": self.typing_check.isChecked(),
        }
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        self.theme_combo.setCurrentText(self.default_settings["theme"])
        self.font_size_spin.setValue(self.default_settings["font_size"])
        self.max_tokens_spin.setValue(self.default_settings["max_tokens"])
        self.temp_spin.setValue(self.default_settings["temperature"])
        self.top_p_spin.setValue(self.default_settings["top_p"])
        self.stream_check.setChecked(self.default_settings["stream_responses"])
        self.timestamps_check.setChecked(self.default_settings["show_timestamps"])
        self.typing_check.setChecked(self.default_settings["show_typing_indicator"])
    
    def accept(self):
        """Handle dialog accept (Save button)."""
        self.settings = self.get_settings()
        self.settings_updated.emit(self.settings)
        super().accept()
