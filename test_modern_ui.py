#!/usr/bin/env python3
"""
Test script for the modern UI of the Pashto AI application.
"""
import sys
import os
import logging
import traceback
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging before importing any application modules
logging.basicConfig(
    level=logging.DEBUG,  # Use DEBUG level for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pashto_ai_test.log")
    ]
)

logger = logging.getLogger(__name__)

def check_imports():
    """Check if all required imports are available."""
    try:
        logger.info("Checking imports...")
        from PyQt5.QtWidgets import QApplication
        logger.info("PyQt5 is available")
        return True
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Please install the required dependencies with: pip install -r requirements_light.txt")
        return False

def main():
    """Run the modern UI with enhanced error handling."""
    try:
        logger.info("Starting Pashto AI Modern UI test...")
        
        # Check imports first
        if not check_imports():
            return 1
            
        logger.info("Creating QApplication...")
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QApplication
        
        # Enable high DPI scaling
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        # Enable debug output
        os.environ["QT_DEBUG_PLUGINS"] = "1"
        
        # Create application
        app = QApplication(sys.argv)
        logger.info("QApplication created successfully")
        
        # Import and create main window
        logger.info("Importing ModernMainWindow...")
        from aichat.ui.modern_main_window import ModernMainWindow
        
        logger.info("Creating main window...")
        window = ModernMainWindow()
        window.show()
        logger.info("Main window shown")
        
        # Run the application
        logger.info("Starting application event loop...")
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
