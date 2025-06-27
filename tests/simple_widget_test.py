"""
Simple test script to verify DocumentPreviewWidget functionality.
"""
import sys
import os
import logging
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QPushButton, QMessageBox

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
sys.path.insert(0, str(Path(__file__).parent.parent))

class MockAIModel:
    """Mock AI model for testing."""
    def __init__(self):
        self.model_name = "mock-model"
        self.max_tokens = 2000
    
    def generate(self, prompt, **kwargs):
        logger.info(f"Mock AI generate called with prompt: {prompt[:200]}...")
        return "This is a test summary of the document."
    
    def chat(self, messages, **kwargs):
        logger.info(f"Mock AI chat called with messages: {messages}")
        return "This is a test answer to your question."
    
    def get_available_models(self):
        return ["mock-model"]

class TestWindow(QWidget):
    """Simple test window for DocumentPreviewWidget."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Preview Widget Test")
        self.setGeometry(100, 100, 1000, 800)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        try:
            # Create layout
            layout = QVBoxLayout(self)
            
            # Add a button to load a document
            self.load_btn = QPushButton("Load Document")
            self.load_btn.clicked.connect(self.load_document)
            layout.addWidget(self.load_btn)
            
            # Import and create the document preview widget
            from aichat.ui.document_preview_widget import DocumentPreviewWidget
            logger.info("Successfully imported DocumentPreviewWidget")
            
            self.doc_widget = DocumentPreviewWidget()
            self.doc_widget.set_model(MockAIModel())
            layout.addWidget(self.doc_widget)
            
            logger.info("DocumentPreviewWidget created and added to layout")
            
            # Add a button to test summarization
            self.summarize_btn = QPushButton("Summarize Document")
            self.summarize_btn.clicked.connect(self.test_summarize)
            layout.addWidget(self.summarize_btn)
            
            # Add a button to test Q&A
            self.qa_btn = QPushButton("Test Q&A")
            self.qa_btn.clicked.connect(self.test_qa)
            layout.addWidget(self.qa_btn)
            
            self.setLayout(layout)
            
        except ImportError as e:
            logger.error(f"Failed to import DocumentPreviewWidget: {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to import DocumentPreviewWidget: {e}")
        except Exception as e:
            logger.error(f"Error creating DocumentPreviewWidget: {e}")
            QMessageBox.critical(self, "Error", f"Error creating DocumentPreviewWidget: {e}")
    
    def load_document(self):
        """Open a file dialog to select a document to load."""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
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
    
    def test_summarize(self):
        """Test document summarization."""
        try:
            if not hasattr(self, 'doc_widget'):
                QMessageBox.warning(self, "Warning", "Document widget not initialized")
                return
                
            if not hasattr(self.doc_widget, 'generate_summary'):
                QMessageBox.warning(self, "Warning", "generate_summary method not found")
                return
                
            logger.info("Generating document summary...")
            self.doc_widget.generate_summary()
            QMessageBox.information(self, "Success", "Document summarization started!")
            
        except Exception as e:
            logger.error(f"Error during summarization: {e}")
            QMessageBox.critical(self, "Error", f"Failed to summarize document: {e}")
    
    def test_qa(self):
        """Test document Q&A."""
        try:
            if not hasattr(self, 'doc_widget'):
                QMessageBox.warning(self, "Warning", "Document widget not initialized")
                return
                
            if not hasattr(self.doc_widget, 'ask_question'):
                QMessageBox.warning(self, "Warning", "ask_question method not found")
                return
                
            # Set a test question
            question = "What is this document about?"
            if hasattr(self.doc_widget, 'qa_input'):
                self.doc_widget.qa_input.setText(question)
            
            logger.info(f"Asking question: {question}")
            self.doc_widget.ask_question()
            QMessageBox.information(self, "Success", f"Question asked: {question}")
            
        except Exception as e:
            logger.error(f"Error during Q&A: {e}")
            QMessageBox.critical(self, "Error", f"Failed to process question: {e}")

def main():
    """Main function to run the test application."""
    try:
        logger.info("Starting test application...")
        app = QApplication(sys.argv)
        
        window = TestWindow()
        window.show()
        
        logger.info("Application started successfully")
        return app.exec_()
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        QMessageBox.critical(None, "Fatal Error", f"A fatal error occurred: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
