"""
Performance testing for the AI Chat application.
"""
import os
import sys
import time
import logging
import unittest
from pathlib import Path
from typing import List, Dict, Any

# Add the parent directory to the path so we can import the application
sys.path.insert(0, str(Path(__file__).parent.parent))

from aichat.ui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceTests(unittest.TestCase):
    """Performance test cases for the AI Chat application."""
    
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
        
    def test_large_file_upload(self):
        """Test uploading a large file to the chat."""
        # Create a large file (5MB)
        test_file = Path("test_large_file.txt")
        with open(test_file, "w") as f:
            f.write("A" * 5 * 1024 * 1024)  # 5MB file
            
        try:
            # Simulate file upload
            start_time = time.time()
            self.window.chat_widget.handle_file_upload([str(test_file.absolute())])
            elapsed = time.time() - start_time
            
            logger.info(f"File upload took {elapsed:.2f} seconds")
            self.assertLess(elapsed, 10.0, "File upload took too long")
            
        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()
    
    def test_long_conversation(self):
        """Test performance with a long conversation."""
        messages = [
            ("user", f"Test message {i}") 
            for i in range(50)  # 100 messages (50 user, 50 assistant)
        ]
        
        start_time = time.time()
        
        # Add messages to the chat
        for role, text in messages:
            self.window.chat_widget.add_message(role, text)
            
        elapsed = time.time() - start_time
        logger.info(f"Added {len(messages)} messages in {elapsed:.2f} seconds")
        self.assertLess(elapsed, 5.0, "Adding messages took too long")
        
        # Test scrolling performance
        start_time = time.time()
        self.window.chat_widget.scroll_to_bottom()
        scroll_time = time.time() - start_time
        logger.info(f"Scrolling took {scroll_time:.4f} seconds")
        self.assertLess(scroll_time, 1.0, "Scrolling took too long")

if __name__ == "__main__":
    unittest.main()
