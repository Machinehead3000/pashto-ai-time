"""Tests for the SettingsDialog class."""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from PyQt5.QtWidgets import QApplication, QMessageBox

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the dialog and its dependencies
from aichat.ui.settings_dialog import (
    SettingsDialog, 
    MemoryManager, 
    UserPreferences, 
    ChatMessage, 
    AIProfile,
    ColorButton
)


class TestSettingsDialog(unittest.TestCase):
    """Test cases for the SettingsDialog class."""

    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def setUp(self):
        """Set up each test case."""
        self.memory_manager = MagicMock(spec=MemoryManager)
        self.memory_manager.preferences = UserPreferences()
        self.dialog = SettingsDialog(self.memory_manager)

    def test_initialization(self):
        """Test that the dialog initializes correctly."""
        self.assertIsNotNone(self.dialog)
        self.assertEqual(self.dialog.windowTitle(), "Settings")

    def test_theme_change(self):
        """Test changing the theme."""
        # Mock the theme application
        with patch.object(self.dialog, 'apply_theme') as mock_apply_theme:
            self.dialog.on_theme_changed("dark")
            mock_apply_theme.assert_called_once_with("dark")

    def test_export_import_data(self):
        """Test exporting and importing data."""
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Test export
            with patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName', 
                      return_value=(temp_path, '')):
                self.dialog.export_data()
                
                # Verify the file was created
                self.assertTrue(os.path.exists(temp_path))
                
                # Test import
                with patch('PyQt5.QtWidgets.QMessageBox.question', 
                          return_value=QMessageBox.Yes):
                    with patch('PyQt5.QtWidgets.QFileDialog.getOpenFileName', 
                              return_value=(temp_path, '')):
                        self.dialog.import_data()
                        
                        # Verify the memory manager was called
                        self.memory_manager.update_preferences.assert_called()
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_reset_to_defaults(self):
        """Test resetting settings to default values."""
        with patch('PyQt5.QtWidgets.QMessageBox.question', 
                  return_value=QMessageBox.Yes):
            self.dialog.reset_to_defaults()
            # Verify the preferences were reset
            self.memory_manager.update_preferences.assert_called_once()

    def test_clear_chat_history(self):
        """Test clearing chat history."""
        with patch('PyQt5.QtWidgets.QMessageBox.question', 
                  return_value=QMessageBox.Yes):
            self.dialog.clear_chat_history()
            # Verify the chat history was cleared
            self.memory_manager.clear_chat_history.assert_called_once()

    def test_save_settings(self):
        """Test saving settings."""
        self.dialog.save_settings()
        # Verify preferences were updated
        self.memory_manager.update_preferences.assert_called_once()


if __name__ == '__main__':
    unittest.main()
