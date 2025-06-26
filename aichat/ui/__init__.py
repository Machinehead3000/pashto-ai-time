"""
UI components for the AI Chat application.

This package contains all the user interface components for the AI Chat application,
including the main window, chat widget, settings dialog, and other UI elements.
"""

from typing import List

from .main_window import MainWindow
from .chat_widget import ChatWidget
from .settings_dialog import SettingsDialog
from .conversation_dialog import ConversationDialog
from .feedback_dialog import FeedbackDialog, FeedbackButton

# Define public API
__all__: List[str] = [
    'MainWindow',
    'ChatWidget',
    'SettingsDialog',
    'ConversationDialog',
    'FeedbackDialog',
    'FeedbackButton',
]

# Package version
__version__ = '0.1.0'

# Initialize package-level logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
