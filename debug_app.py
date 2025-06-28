import sys
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QFont
        from main import FreeAIChatApp
        
        logger.info("Starting Pashto AI application...")
        
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        font = QFont("Segoe UI", 10)
        app.setFont(font)
        
        logger.info("Creating main window...")
        window = FreeAIChatApp()
        window.show()
        
        logger.info("Entering application event loop")
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.exception("Fatal error in application:")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
