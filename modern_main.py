#!/usr/bin/env python3
"""
Modern entry point for the Pashto AI application with enhanced UI.
"""
import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pashto_ai.log')
    ]
)

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from aichat.ui.modern_main_window import ModernMainWindow

def main():
    """Main entry point for the application."""
    # Create application
    app = QApplication(sys.argv)
    
    # Set application information
    app.setApplicationName("Pashto AI")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PashtoAI")
    
    # Set window icon if available
    icon_path = os.path.join(project_root, "resources", "icons", "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show main window
    window = ModernMainWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
