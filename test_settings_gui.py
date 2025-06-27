"""
Simple test script for the SettingsDialog.

This script provides a simple way to test the SettingsDialog GUI manually.
"""

import sys
from PyQt5.QtWidgets import QApplication

# Add the parent directory to the path so we can import the module
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Import the dialog and its dependencies
from aichat.ui.settings_dialog import (
    SettingsDialog,
    MemoryManager,
    UserPreferences,
    ChatMessage,
    AIProfile
)


def main():
    """Run the SettingsDialog test application."""
    # Create the application
    app = QApplication(sys.argv)
    
    # Initialize memory manager with test data
    memory_manager = MemoryManager()
    memory_manager.preferences = UserPreferences()
    
    # Add some test chat history
    test_message = ChatMessage()
    test_message.role = "user"
    test_message.content = "Hello, this is a test message!"
    
    # Add a test AI profile
    test_profile = AIProfile()
    test_profile.name = "Test AI"
    test_profile.description = "A test AI profile"
    
    # Create and show the dialog
    dialog = SettingsDialog(memory_manager)
    dialog.show()
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
