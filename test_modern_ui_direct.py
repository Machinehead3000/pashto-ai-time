#!/usr/bin/env python3
"""
Direct test script for the modern UI of the Pashto AI application.
"""
import sys
import logging
from PyQt5.QtWidgets import QApplication

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pashto_ai_debug.log")
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for testing the modern UI."""
    try:
        logger.info("Starting Pashto AI Modern UI...")
        
        # Create application
        app = QApplication(sys.argv)
        
        # Import here to catch import errors
        from aichat.ui.modern_main_window import ModernMainWindow
        
        # Create and show main window
        logger.info("Creating main window...")
        window = ModernMainWindow()
        window.show()
        
        logger.info("Application started successfully")
        
        # Run the application
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.exception("Fatal error in application:")
        print(f"Fatal error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
