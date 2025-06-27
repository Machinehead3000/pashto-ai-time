import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QMessageBox

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.abspath('.'))

# Mock AI model
class MockAIModel:
    def generate(self, prompt, **kwargs):
        logger.info(f"AI generate called with prompt: {prompt[:100]}...")
        return "This is a test summary of the document."
    
    def chat(self, messages, **kwargs):
        logger.info(f"AI chat called with messages: {messages}")
        return "This is a test answer to your question."

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Preview Widget Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add a button to load a document
        self.load_btn = QPushButton("Load Document")
        self.load_btn.clicked.connect(self.load_document)
        layout.addWidget(self.load_btn)
        
        # Import and create the document preview widget
        try:
            from aichat.ui.document_preview_widget import DocumentPreviewWidget
            logger.info("Successfully imported DocumentPreviewWidget")
            
            self.doc_widget = DocumentPreviewWidget()
            self.doc_widget.set_model(MockAIModel())
            layout.addWidget(self.doc_widget)
            
            logger.info("DocumentPreviewWidget created and added to layout")
            
        except ImportError as e:
            logger.error(f"Failed to import DocumentPreviewWidget: {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to import DocumentPreviewWidget: {e}")
        except Exception as e:
            logger.error(f"Error creating DocumentPreviewWidget: {e}")
            QMessageBox.critical(self, "Error", f"Error creating DocumentPreviewWidget: {e}")
    
    def load_document(self):
        """Open a file dialog to select a document to load"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Open Document",
                "",
                "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf);;Word Documents (*.docx)"
            )
            
            if file_path:
                logger.info(f"Loading document: {file_path}")
                if hasattr(self, 'doc_widget') and hasattr(self.doc_widget, 'load_file'):
                    self.doc_widget.load_file(file_path)
                    logger.info("Document loaded successfully")
                    QMessageBox.information(self, "Success", "Document loaded successfully!")
                else:
                    logger.error("Document widget or load_file method not found")
                    QMessageBox.critical(self, "Error", "Document widget not properly initialized")
            else:
                logger.info("No file selected")
                
        except Exception as e:
            logger.error(f"Error loading document: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load document: {e}")

if __name__ == "__main__":
    try:
        logger.info("Starting application...")
        app = QApplication(sys.argv)
        
        window = TestWindow()
        window.show()
        
        logger.info("Application started successfully")
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        QMessageBox.critical(None, "Fatal Error", f"A fatal error occurred: {e}")
        sys.exit(1)
