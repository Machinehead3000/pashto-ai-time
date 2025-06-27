"""
Enhanced Main Window - Modern, feature-rich main window for the AI Chat application.
"""

import json
import logging
import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PyQt5.QtCore import (
    QByteArray, QEvent, QFile, QMimeData, QPoint, QSettings, QSize, Qt, QTimer,
    QUrl, pyqtSignal, pyqtSlot
)
from PyQt5.QtGui import (
    QAction, QCloseEvent, QColor, QDesktopServices, QDragEnterEvent, QDropEvent,
    QFont, QFontDatabase, QIcon, QKeySequence, QPalette, QPixmap, QTextCharFormat,
    QTextCursor, QTextDocument
)
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (
    QAction, QApplication, QComboBox, QDockWidget, QFileDialog, QHBoxLayout,
    QLabel, QMainWindow, QMenu, QMenuBar, QMessageBox, QPushButton, QSizePolicy,
    QSplitter, QStatusBar, QStyle, QStyleFactory, QTabWidget, QTextBrowser,
    QTextEdit, QToolBar, QToolButton, QVBoxLayout, QWidget
)

from ..ai import get_ai_manager
from ..ai.plugins import get_plugin_manager
from ..core.settings import settings_manager
from ..i18n.localization import tr, set_language, is_rtl_language, get_available_languages
from ..memory import MemoryManager
from ..models import BaseModel
from ..utils.resource_loader import load_icon, load_pixmap, resource_loader
from .chat_widget import ChatWidget
from .plugin_manager import PluginManagerWidget
from .settings_dialog import SettingsDialog
from .theme_manager import ThemeManager

logger = logging.getLogger(__name__)

class EnhancedMainWindow(QMainWindow):
    """Enhanced main window with modern UI and plugin support."""
    
    # Signals
    theme_changed = pyqtSignal(str)  # theme_name
    language_changed = pyqtSignal(str)  # language_code
    
    def __init__(self, memory_manager: MemoryManager = None, parent=None):
        """Initialize the enhanced main window.
        
        Args:
            memory_manager: Optional memory manager instance.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        # Initialize components
        self.memory_manager = memory_manager or MemoryManager()
        self.ai_manager = get_ai_manager()
        self.plugin_manager = get_plugin_manager()
        self.theme_manager = ThemeManager()
        
        # UI state
        self.current_theme = settings_manager.get("app.theme", "system")
        self.current_language = settings_manager.get("app.language", "en")
        self.window_state = {}
        
        # Initialize UI
        self._init_ui()
        
        # Load settings
        self._load_settings()
        
        # Connect signals
        self._connect_signals()
        
        # Set window properties
        self.setWindowTitle(tr("AI Chat"))
        self.setWindowIcon(load_icon("icons/app.png") or QIcon())
        self.resize(settings_manager.get("window/width", 1200), 
                   settings_manager.get("window/height", 800))
        
        # Apply theme
        self._apply_theme()
        
        # Show status message
        self.statusBar().showMessage(tr("Ready"), 5000)
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create main toolbar
        self._create_main_toolbar()
        
        # Create main content area
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Chat
        self.chat_widget = ChatWidget(self.memory_manager, self)
        content_splitter.addWidget(self.chat_widget)
        
        # Right panel - Plugins (initially hidden)
        self.plugins_dock = QDockWidget(tr("Plugins"), self)
        self.plugins_dock.setFeatures(
            QDockWidget.DockWidgetMovable | 
            QDockWidget.DockWidgetFloatable |
            QDockWidget.DockWidgetClosable
        )
        self.plugins_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        # Plugin tabs
        self.plugin_tabs = QTabWidget()
        self.plugin_tabs.setDocumentMode(True)
        self.plugin_tabs.setTabsClosable(True)
        self.plugin_tabs.tabCloseRequested.connect(self._on_plugin_tab_close)
        self.plugins_dock.setWidget(self.plugin_tabs)
        
        self.addDockWidget(Qt.RightDockWidgetArea, self.plugins_dock)
        self.plugins_dock.hide()
        
        # Add content to main layout
        main_layout.addWidget(content_splitter)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add status bar widgets
        self.status_label = QLabel()
        self.status_bar.addPermanentWidget(self.status_label)
        
        # Apply initial layout direction
        self._update_layout_direction()
    
    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu(tr("&File"))
        
        self.new_chat_action = QAction(load_icon("icons/new.png"), tr("&New Chat"), self)
        self.new_chat_action.setShortcut(QKeySequence.New)
        self.new_chat_action.triggered.connect(self._on_new_chat)
        file_menu.addAction(self.new_chat_action)
        
        self.open_action = QAction(load_icon("icons/open.png"), tr("&Open..."), self)
        self.open_action.setShortcut(QKeySequence.Open)
        self.open_action.triggered.connect(self._on_open_chat)
        file_menu.addAction(self.open_action)
        
        self.save_action = QAction(load_icon("icons/save.png"), tr("&Save"), self)
        self.save_action.setShortcut(QKeySequence.Save)
        self.save_action.triggered.connect(self._on_save_chat)
        file_menu.addAction(self.save_action)
        
        file_menu.addSeparator()
        
        self.export_action = QAction(load_icon("icons/export.png"), tr("&Export..."), self)
        self.export_action.triggered.connect(self._on_export_chat)
        file_menu.addAction(self.export_action)
        
        file_menu.addSeparator()
        
        self.print_action = QAction(load_icon("icons/print.png"), tr("&Print..."), self)
        self.print_action.setShortcut(QKeySequence.Print)
        self.print_action.triggered.connect(self._on_print_chat)
        file_menu.addAction(self.print_action)
        
        file_menu.addSeparator()
        
        self.settings_action = QAction(load_icon("icons/settings.png"), tr("&Settings..."), self)
        self.settings_action.triggered.connect(self._on_settings)
        file_menu.addAction(self.settings_action)
        
        file_menu.addSeparator()
        
        self.exit_action = QAction(load_icon("icons/exit.png"), tr(
