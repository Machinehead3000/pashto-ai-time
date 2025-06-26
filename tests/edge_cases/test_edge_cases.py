"""
Edge case tests for the AI Chat application.
"""
import os
import sys
import unittest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the application
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from aichat.ui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QEvent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EdgeCaseTests(unittest.TestCase):
    """Test cases for edge cases in the AI Chat application."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        cls.app = QApplication.instance() or QApplication(sys.argv)
        
    def setUp(self):
        """Set up each test case."""
        self.window = MainWindow()
        self.window.show()
        
    def tearDown(self):
        """Clean up after each test case."""
        self.window.close()
    
    def test_special_characters(self):
        """Test handling of special characters in messages."""
        test_cases = [
            "Hello, world!",
            "مرحبا بالعالم!",  # Arabic
            "こんにちは世界",  # Japanese
            "Привет, мир!",  # Russian
            "!@#$%^&*()_+{}|:<>?[];',./\"",  # Special chars
            " " * 1000,  # Whitespace
            "\n\n\n",  # Newlines
            "\x00\x01\x02\x03\x04\x05",  # Control characters
        ]
        
        for message in test_cases:
            with self.subTest(message=message):
                try:
                    self.window.chat_widget.add_message("user", message)
                    self.window.chat_widget.add_message("assistant", f"Echo: {message}")
                except Exception as e:
                    self.fail(f"Failed to handle message: {message!r} - {str(e)}")
    
    def test_long_messages(self):
        """Test handling of very long messages."""
        # Test with 10KB message
        long_message = "A" * (10 * 1024)
        try:
            self.window.chat_widget.add_message("user", long_message)
            self.window.chat_widget.add_message("assistant", "Received long message")
        except Exception as e:
            self.fail(f"Failed to handle long message: {str(e)}")
    
    @patch('aichat.ui.main_window.QMessageBox.critical')
    def test_network_failure(self, mock_critical):
        """Test handling of network failures."""
        # Mock the model to simulate a network error
        original_model = self.window.models[self.window.current_model]
        mock_model = MagicMock()
        mock_model.generate_response.side_effect = Exception("Network error")
        self.window.models[self.window.current_model] = mock_model
        
        # Try to send a message
        self.window.send_message("Test message")
        
        # Verify error handling
        self.assertTrue(mock_critical.called)
        
        # Restore original model
        self.window.models[self.window.current_model] = original_model
    
    def test_low_disk_space(self):
        """Test behavior with low disk space."""
        # Mock os.statvfs to simulate low disk space
        with patch('os.statvfs') as mock_statvfs:
            # Set free blocks to a very low number
            mock_statvfs.return_value.f_bavail = 1
            mock_statvfs.return_value.f_frsize = 4096
            
            # Try to save a file
            with patch('aichat.ui.main_window.QFileDialog.getSaveFileName', 
                     return_value=("test_chat.json", None)):
                with patch('builtins.open', create=True) as mock_open:
                    mock_file = MagicMock()
                    mock_file.__enter__.return_value = mock_file
                    mock_open.return_value = mock_file
                    
                    self.window.save_chat()
                    
                    # Verify the file was attempted to be written
                    mock_file.write.assert_called()

if __name__ == "__main__":
    unittest.main()
