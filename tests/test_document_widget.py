import os
import sys
import unittest
import tempfile
import shutil
import logging
import traceback
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QEventLoop

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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the AI model
class MockAIModel:
    def generate(self, prompt, **kwargs):
        return "This is a test summary of the document."
    
    def chat(self, messages, **kwargs):
        return "This is a test answer to your question."

class TestDocumentWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialize the QApplication once for all tests"""
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
        """Set up test environment before each test"""
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
            self.widget.set_model(MockAIModel())
            
            logger.info("Test setup complete")
            
        except Exception as e:
            logger.error(f"Error in test setup: {e}\n{traceback.format_exc()}")
            raise
    
    def tearDown(self):
        """Clean up after each test"""
        self.widget.close()
        self.widget.deleteLater()
        shutil.rmtree(self.test_dir)
    
    def create_test_files(self):
        """Create test files in the temporary directory"""
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
    
    def test_load_document(self):
        """Test loading a document"""
        logger.info("Starting test_load_document")
        
        try:
            logger.info(f"Loading document: {self.text_file}")
            self.widget.load_file(self.text_file)
            
            # Process events to allow file loading
            logger.info("Processing Qt events")
            QApplication.processEvents()
            
            # Check if content is loaded
            logger.info("Checking if content was loaded")
            self.assertTrue(hasattr(self.widget, 'analysis'), 
                          "Widget has no 'analysis' attribute after loading document")
            self.assertIn('content', self.widget.analysis, 
                        "Analysis result has no 'content' key")
            self.assertIn('This is a test document', self.widget.analysis['content'],
                        "Expected content not found in document")
            
            logger.info("Document loaded and verified successfully")
            
        except Exception as e:
            logger.error(f"Test failed: {e}\n{traceback.format_exc()}")
            raise
    
    def test_summarize_document(self):
        """Test document summarization"""
        logger.info("Starting test_summarize_document")
        
        try:
            # Load the document
            logger.info(f"Loading document: {self.text_file}")
            self.widget.load_file(self.text_file)
            
            # Setup summary tab if not already set up
            if not hasattr(self.widget, 'summary_text'):
                logger.info("Setting up summary tab")
                self.widget.setup_summary_tab()
            
            # Set summary type
            if hasattr(self.widget, 'summary_type_combo'):
                logger.info("Setting summary type to 'Concise'")
                self.widget.summary_type_combo.setCurrentText('Concise')
            
            # Generate summary
            logger.info("Generating summary")
            self.widget.generate_summary()
            
            # Process events and wait for summary
            logger.info("Waiting for summary generation to complete")
            max_attempts = 10
            summary_generated = False
            
            for i in range(max_attempts):
                QApplication.processEvents()
                if hasattr(self.widget, 'summary_text') and self.widget.summary_text.toPlainText().strip():
                    summary_generated = True
                    logger.info("Summary generated successfully")
                    break
                logger.info(f"Waiting for summary... (attempt {i+1}/{max_attempts})")
                QTimer.singleShot(500, QApplication.quit)
                QApplication.exec_()
            
            # Check if summary was generated
            self.assertTrue(summary_generated, "Summary was not generated in time")
            self.assertTrue(hasattr(self.widget, 'summary_text'), "Summary text widget not found")
            
            # Get and verify summary content
            summary = self.widget.summary_text.toPlainText()
            logger.info(f"Generated summary: {summary[:100]}...")
            self.assertIn('test', summary.lower(), "Expected 'test' in summary")
            
            logger.info("Document summarization test completed successfully")
            
        except Exception as e:
            logger.error(f"Test failed: {e}\n{traceback.format_exc()}")
            raise
    
    def test_qa_document(self):
        """Test document Q&A functionality"""
        logger.info("Starting test_qa_document")
        
        try:
            # Load the document
            logger.info(f"Loading document: {self.text_file}")
            self.widget.load_file(self.text_file)
            
            # Setup Q&A tab if not already set up
            if not hasattr(self.widget, 'qa_history_widget'):
                logger.info("Setting up Q&A tab")
                if hasattr(self.widget, 'setup_qa_tab'):
                    self.widget.setup_qa_tab()
                else:
                    self.skipTest("setup_qa_tab method not found in widget")
            
            # Test asking a question
            question = "What is this document about?"
            logger.info(f"Asking question: {question}")
            
            if not hasattr(self.widget, 'qa_input'):
                self.fail("qa_input widget not found")
                
            self.widget.qa_input.setText(question)
            
            if not hasattr(self.widget, 'ask_question'):
                self.fail("ask_question method not found")
                
            self.widget.ask_question()
            
            # Process events and wait for answer
            logger.info("Waiting for answer...")
            max_attempts = 10
            answer_received = False
            
            for i in range(max_attempts):
                QApplication.processEvents()
                if (hasattr(self.widget, 'qa_history') and 
                    len(self.widget.qa_history) > 0 and 
                    any(qa.get('question') == question for qa in self.widget.qa_history)):
                    answer_received = True
                    logger.info("Answer received")
                    break
                logger.info(f"Waiting for answer... (attempt {i+1}/{max_attempts})")
                QTimer.singleShot(500, QApplication.quit)
                QApplication.exec_()
            
            # Check if answer was generated
            self.assertTrue(answer_received, "No answer received in time")
            self.assertTrue(hasattr(self.widget, 'qa_history'), "QA history not found")
            self.assertGreater(len(self.widget.qa_history), 0, "QA history is empty")
            
            # Find the question in history
            found = False
            for qa in self.widget.qa_history:
                if qa.get('question') == question:
                    found = True
                    self.assertIn('answer', qa, "No answer in QA history")
                    answer = qa['answer']
                    logger.info(f"Question: {question}")
                    logger.info(f"Answer: {answer[:100]}...")
                    self.assertIsInstance(answer, str, "Answer is not a string")
                    self.assertGreater(len(answer.strip()), 0, "Empty answer")
                    break
                    
            self.assertTrue(found, f"Question '{question}' not found in QA history")
            
            logger.info("Document Q&A test completed successfully")
            
        except Exception as e:
            logger.error(f"Test failed: {e}\n{traceback.format_exc()}")
            raise
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        # Delete the QApplication instance
        if cls.app:
            cls.app.quit()

def run_tests():
    """Run the tests with detailed output"""
    logger.info("=" * 80)
    logger.info("STARTING DOCUMENT WIDGET TEST SUITE".center(80))
    logger.info("=" * 80)
    
    # Create test suite
    test_loader = unittest.TestLoader()
    test_suite = test_loader.loadTestsFromTestCase(TestDocumentWidget)
    
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

if __name__ == '__main__':
    logger.info("Starting document widget tests...")
    success = run_tests()
    sys.exit(0 if success else 1)
