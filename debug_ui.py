#!/usr/bin/env python3
"""
Debug script for the Pashto AI Modern UI.
"""
import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Configure logging to both console and file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug.log', mode='w', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def show_error(title, message):
    """Show an error message dialog."""
    app = QApplication.instance() or QApplication(sys.argv)
    QMessageBox.critical(None, title, message)
    if not app:
        sys.exit(1)

def main():
    """Main entry point for debugging the modern UI."""
    try:
        logger.info("Starting Pashto AI Modern UI in debug mode...")
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("Pashto AI Chat - Debug")
        
        # Import UI components
        try:
            logger.info("Importing UI components...")
            from aichat.ui.modern_main_window import ModernMainWindow
            logger.info("UI components imported successfully")
        except ImportError as e:
            logger.exception("Failed to import UI components:")
            show_error("Import Error", f"Failed to import UI components: {str(e)}")
            return 1
        
        try:
            # Create and show main window
            logger.info("Creating main window...")
            window = ModernMainWindow()
            window.show()
            logger.info("Main window created and shown")
            
            # Run the application
            logger.info("Starting application event loop")
            return app.exec_()
            
        except Exception as e:
            logger.exception("Error in application:")
            show_error("Application Error", f"An error occurred: {str(e)}")
            return 1
            
    except Exception as e:
        logger.exception("Fatal error:")
        show_error("Fatal Error", f"A fatal error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
