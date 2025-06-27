"""
Test script for the main application window.

This script provides a simple way to test the main window UI components
including the chat interface, document preview, and settings dialog.
"""

import sys
import os
from pathlib import Path

from PyQt5.QtWidgets import QApplication

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the main window class
try:
    from aichat.ui.main_window import MainWindow
except ImportError:
    # Fallback for direct execution
    from aichat.ui.main_window import MainWindow

class TestApp:
    """Test application for the main window."""
    
    def __init__(self):
        """Initialize the test application."""
        self.app = QApplication(sys.argv)
        self.main_window = MainWindow()
        self.main_window.show()
        
        # Apply some test data
        self.setup_test_data()
    
    def setup_test_data(self):
        """Set up some test data for the UI."""
        # Add a test message to the chat
        self.main_window.chat_widget.add_message(
            "Hello, this is a test message!",
            is_user=True
        )
        
        # Add a test response
        self.main_window.chat_widget.add_message(
            "Hello! I'm your AI assistant. How can I help you today?",
            is_user=False
        )
        
        # Set a test model
        if hasattr(self.main_window, 'model_combo'):
            self.main_window.model_combo.setCurrentText("Mistral-7B")
    
    def run(self):
        """Run the application."""
        return self.app.exec_()

if __name__ == "__main__":
    # Set dark theme for consistent appearance
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Apply a dark palette
    palette = app.palette()
    palette.setColor(palette.Window, QColor(53, 53, 53))
    palette.setColor(palette.WindowText, Qt.white)
    palette.setColor(palette.Base, QColor(25, 25, 25))
    palette.setColor(palette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(palette.ToolTipBase, Qt.white)
    palette.setColor(palette.ToolTipText, Qt.white)
    palette.setColor(palette.Text, Qt.white)
    palette.setColor(palette.Button, QColor(53, 53, 53))
    palette.setColor(palette.ButtonText, Qt.white)
    palette.setColor(palette.BrightText, Qt.red)
    palette.setColor(palette.Link, QColor(42, 130, 218))
    palette.setColor(palette.Highlight, QColor(42, 130, 218))
    palette.setColor(palette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    # Run the test application
    test_app = TestApp()
    sys.exit(test_app.run())
