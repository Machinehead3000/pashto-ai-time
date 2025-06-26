#!/usr/bin/env python3
"""
Main entry point for the AI Chat application.
"""
import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase, QFont

from .ui.main_window import MainWindow
from .ui.cyberpunk_theme import apply_cyberpunk_theme

def setup_logging():
    """Configure application logging."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'aichat.log')),
            logging.StreamHandler()
        ]
    )

def load_fonts():
    """Load custom fonts if available."""
    try:
        # Try to load Orbitron font if available
        font_dir = os.path.join(os.path.dirname(__file__), 'resources', 'fonts')
        if os.path.exists(font_dir):
            for font_file in os.listdir(font_dir):
                if font_file.endswith(('.ttf', '.otf')):
                    font_path = os.path.join(font_dir, font_file)
                    QFontDatabase.addApplicationFont(font_path)
    except Exception as e:
        logging.warning(f"Could not load custom fonts: {e}")

def main():
    """Main application entry point."""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting AI Chat application")
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("AI Chat Pro")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")  # Use Fusion style for better cross-platform appearance
    
    # Load custom fonts
    load_fonts()
    
    # Apply cyberpunk theme
    apply_cyberpunk_theme(app)
    
    try:
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Start the application event loop
        sys.exit(app.exec_())
    except Exception as e:
        logger.exception("Unhandled exception in main:")
        sys.exit(1)

if __name__ == "__main__":
    main()
