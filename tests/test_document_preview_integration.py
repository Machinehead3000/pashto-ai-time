"""
Integration tests for the DocumentPreviewWidget.
"""
import os
import sys
import time
import unittest
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QEventLoop
from PyQt5.QtTest import QTest

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

# Mock AI model for testing
class MockAIModel:
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

class TestDocumentPreviewIntegration(unittest.TestCase):
    """Integration tests for DocumentPreviewWidget."""
    
    @classmethod
    def setUpClass(cls):
        """Initialize the QApplication once for all tests."""
        logger.info("Setting up test class")
        try:
            cls.app = QApplication.instance()
            if cls.app is None:
                logger.info("Creating new QApplication instance")
                cls.app = QApplication(sys.argv)
            else:
                logger.info("Using existing QApplication instance")
        except Exception as e:
            logger.error(f"Failed to set up QApplication: {e}")
            raise
    
    def setUp(self):
        """Set up test environment before each test."""
        logger.info(f"\n{'='*50}\nSetting up test: {self._testMethodName}\n{'='*50}")
        
        try:
            # Create a temporary directory for test files
            self.test_dir = tempfile.mkdtemp(prefix='pashto_ai_test_')
            logger.info(f"Created temporary directory: {self.test_dir}")
            
            # Create test files
            self.create_test_files()
            
            # Import the widget after setting up the QApplication
            logger.info("Importing DocumentPreviewWidget")
            from aichat.ui.document_preview_widget import DocumentPreviewWidget
            
            # Create the widget
            logger.info("Creating DocumentPreviewWidget instance")
            self.widget = DocumentPreviewWidget()
            
            # Set up mock AI model
            logger.info("Setting up mock AI model")
            self.mock_model = MockAIModel()
            self.widget.set_model(self.mock_model)
            
            # Show the widget (not necessary for testing but helps with debugging)
            self.widget.show()
            QTest.qWait(100)  # Give the widget time to show
            
            logger.info("Test setup complete")
            
        except Exception as e:
            logger.error(f"Error in test setup: {e}\n{traceback.format_exc()}")
            raise
    
    def tearDown(self):
        """Clean up after each test."""
        try:
            if hasattr(self, 'widget') and self.widget:
                self.widget.hide()
                self.widget.deleteLater()
                self.widget = None
            
            # Clean up temporary files
            if hasattr(self, 'test_dir') and os.path.exists(self.test_dir):
                import shutil
                shutil.rmtree(self.test_dir)
                logger.info(f"Removed temporary directory: {self.test_dir}")
                
            # Process any pending events
            QApplication.processEvents()
            
        except Exception as e:
            logger.error(f"Error in tearDown: {e}")
    
    def create_test_files(self):
        """Create test files in the temporary directory."""
        # Create a simple text file
        self.text_file = os.path.join(self.test_dir, 'test.txt')
        with open(self.text_file, 'w', encoding='utf-8') as f:
            f.write("""This is a test document.
            It contains multiple lines of text.
            We'll use it to test document features.
            It has about 20 words in total.""")
        
        # Create a large text file
        self.large_file = os.path.join(self.test_dir, 'large.txt')
        with open(self.large_file, 'w', encoding='utf-8') as f:
            for _ in range(1000):
                f.write("This is a line in a large document. " * 10 + "\n")
    
    def wait_for_condition(self, condition_func, timeout=5000, interval=100):
        """Wait for a condition to be true or timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout / 1000.0:
            if condition_func():
                return True
            QTest.qWait(interval)
        return False
    
    def test_initial_state(self):
        """Test the initial state of the widget."""
        logger.info("Testing initial widget state")
        
        # Check that the widget is properly initialized
        self.assertIsNotNone(self.widget)
        self.assertTrue(hasattr(self.widget, 'tabs'))
        self.assertTrue(hasattr(self.widget, 'file_path'))
        self.assertIsNone(self.widget.file_path)
        self.assertFalse(hasattr(self.widget, 'analysis'))
        
        logger.info("Initial widget state test passed")
    
    def test_load_document(self):
        """Test loading a document into the widget."""
        logger.info("Testing document loading")
        
        # Load the document
        self.widget.load_file(self.text_file)
        
        # Process events to allow file loading
        QApplication.processEvents()
        
        # Wait for analysis to complete
        analysis_complete = self.wait_for_condition(
            lambda: hasattr(self.widget, 'analysis') and 'content' in self.widget.analysis
        )
        
        # Check if content was loaded
        self.assertTrue(analysis_complete, "Document analysis did not complete")
        self.assertEqual(self.widget.file_path, self.text_file)
        self.assertIn('content', self.widget.analysis)
        self.assertIn('This is a test document', self.widget.analysis['content'])
        
        logger.info("Document loading test passed")
    
    def test_summarize_document(self):
        """Test document summarization."""
        logger.info("Testing document summarization")
        
        # First load the document
        self.test_load_document()
        
        # Make sure summary tab is set up
        if not hasattr(self.widget, 'summary_text'):
            self.widget.setup_summary_tab()
        
        # Set summary type to 'Concise'
        if hasattr(self.widget, 'summary_type_combo'):
            self.widget.summary_type_combo.setCurrentText('Concise')
        
        # Generate summary
        self.widget.generate_summary()
        
        # Wait for summary to be generated
        summary_generated = self.wait_for_condition(
            lambda: hasattr(self.widget, 'summary_text') and 
                   bool(self.widget.summary_text.toPlainText().strip())
        )
        
        # Check if summary was generated
        self.assertTrue(summary_generated, "Summary was not generated")
        summary = self.widget.summary_text.toPlainText()
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary.strip()), 0)
        
        logger.info(f"Generated summary: {summary[:100]}...")
        logger.info("Document summarization test passed")
    
    def test_qa_functionality(self):
        """Test question answering functionality."""
        logger.info("Testing Q&A functionality")
        
        # First load the document
        self.test_load_document()
        
        # Make sure QA tab is set up
        if not hasattr(self.widget, 'qa_input'):
            self.widget.setup_qa_tab()
        
        # Ask a question
        question = "What is this document about?"
        self.widget.qa_input.setText(question)
        
        # Click the ask button
        if hasattr(self.widget, 'ask_button'):
            self.widget.ask_button.click()
        else:
            self.widget.ask_question()
        
        # Wait for answer
        answer_received = self.wait_for_condition(
            lambda: hasattr(self.widget, 'qa_history') and 
                   len(self.widget.qa_history) > 0 and
                   any(qa.get('question') == question for qa in self.widget.qa_history)
        )
        
        # Check if answer was generated
        self.assertTrue(answer_received, "No answer received")
        
        # Find the question in history
        qa_entry = next((qa for qa in self.widget.qa_history 
                        if qa.get('question') == question), None)
        
        self.assertIsNotNone(qa_entry, "Question not found in QA history")
        self.assertIn('answer', qa_entry, "No answer in QA history")
        
        answer = qa_entry['answer']
        logger.info(f"Question: {question}")
        logger.info(f"Answer: {answer[:100]}...")
        
        self.assertIsInstance(answer, str)
        self.assertGreater(len(answer.strip()), 0)
        
        logger.info("Q&A functionality test passed")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        logger.info("Tearing down test class")
        if hasattr(cls, 'app') and cls.app:
            cls.app.quit()

def run_tests():
    """Run the tests with detailed output."""
    logger.info("=" * 80)
    logger.info("DOCUMENT PREVIEW INTEGRATION TEST SUITE".center(80))
    logger.info("=" * 80)
    
    # Create test suite
    test_loader = unittest.TestLoader()
    test_suite = test_loader.loadTestsFromTestCase(TestDocumentPreviewIntegration)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY".center(80))
    logger.info("=" * 80)
    logger.info(f"\nTests run: {result.testsRun}")
    logger.info(f"Passed: {result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        logger.info("\n✅ ALL TESTS PASSED SUCCESSFULLY!")
    else:
        logger.info("\n❌ SOME TESTS FAILED!")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    import traceback
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"Fatal error: {e}\n{traceback.format_exc()}")
        sys.exit(1)
