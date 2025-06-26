"""
Cross-platform compatibility tests for the AI Chat application.
"""
import os
import sys
import unittest
import platform
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the application
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import QApplication at the module level
try:
    from PyQt5.QtWidgets import QApplication
    # Skip GUI tests on non-Windows platforms if GUI is not available
    SKIP_GUI = False
    if platform.system() != 'Windows':
        try:
            app = QApplication.instance() or QApplication(sys.argv)
        except Exception as e:
            logger.warning(f"Failed to initialize QApplication: {e}")
            SKIP_GUI = True
except ImportError:
    SKIP_GUI = True

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Skip decorator for GUI tests
skip_if_no_gui = unittest.skipIf(SKIP_GUI, "GUI tests skipped on this platform")

class CrossPlatformTests(unittest.TestCase):
    """Test cases for cross-platform compatibility."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        if not SKIP_GUI:
            cls.app = QApplication.instance() or QApplication(sys.argv)
    
    @skip_if_no_gui
    def test_gui_initialization(self):
        """Test that the GUI initializes correctly on this platform."""
        from aichat.ui.main_window import MainWindow
        window = MainWindow()
        try:
            window.show()
            self.assertTrue(window.isVisible())
        finally:
            window.close()
    
    def test_path_handling(self):
        """Test that path handling works correctly on this platform."""
        from aichat.ui.main_window import MainWindow
        
        # Test path joining
        test_path = os.path.join("path", "to", "file.txt")
        if platform.system() == 'Windows':
            self.assertIn('\\', test_path)
        else:
            self.assertIn('/', test_path)
    
    @skip_if_no_gui
    def test_theme_application(self):
        """Test that themes are applied correctly on this platform."""
        from aichat.ui.main_window import MainWindow
        from aichat.ui.cyberpunk_theme import apply_cyberpunk_theme
        
        window = MainWindow()
        try:
            # Apply theme and verify no errors
            apply_cyberpunk_theme(self.app)
            window.show()
        finally:
            window.close()
    
    def test_file_operations(self):
        """Test basic file operations on this platform."""
        test_file = Path("test_file.txt")
        try:
            # Test file creation
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("Test content")
            
            # Test file reading
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertEqual(content, "Test content")
                
        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()
    
    @skip_if_no_gui
    def test_locale_handling(self):
        """Test that locale handling works correctly."""
        from aichat.localization import i18n, tr
        
        # Test that we can load translations
        test_string = tr("Settings")
        self.assertIsInstance(test_string, str)
        self.assertGreater(len(test_string), 0)

if __name__ == "__main__":
    unittest.main()
