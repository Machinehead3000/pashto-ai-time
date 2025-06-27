import os
import sys
import json
import unittest
import time
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QEventLoop

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import traceback
from aichat.ui.document_preview_widget import DocumentPreviewWidget
from aichat.models.base import BaseModel
from aichat.utils.file_utils import FileAnalyzer

# Mock AI model for testing
class MockAIModel(BaseModel):    
    def generate(self, prompt, **kwargs):
        if "summary" in prompt.lower():
            return "This is a test summary of the document content."
        elif "?" in prompt:
            return "This is a test answer to your question about the document."
        return "Test response"
    
    def chat(self, messages, **kwargs):
        return "Test chat response"

class TestDocumentFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialize the QApplication once for all tests"""
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
    
    def setUp(self):
        """Set up test environment before each test"""
        self.model = MockAIModel()
        self.widget = DocumentPreviewWidget()
        self.widget.set_model(self.model)
        
        # Create a test directory
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_docs')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create test documents
        self.create_test_documents()
    
    def tearDown(self):
        """Clean up after each test"""
        self.widget.deleteLater()
        self.widget = None
    
    def create_test_documents(self):
        """Create test documents for testing"""
        # Simple text document
        with open(os.path.join(self.test_dir, 'test.txt'), 'w', encoding='utf-8') as f:
            f.write("""This is a test document.
            It contains multiple lines of text.
            We'll use it to test document features.
            It has about 20 words in total.""")
        
        # JSON document
        with open(os.path.join(self.test_dir, 'test.json'), 'w', encoding='utf-8') as f:
            json.dump({
                "title": "Test Document",
                "content": "This is a test JSON document.",
                "items": [1, 2, 3, 4, 5]
            }, f)
        
        # Large text document (will be truncated)
        with open(os.path.join(self.test_dir, 'large.txt'), 'w', encoding='utf-8') as f:
            f.write("Large document content.\n" * 1000)
    
    def test_load_text_document(self):
        """Test loading a text document"""
        print("\n=== Testing text document loading ===")
        test_file = os.path.join(self.test_dir, 'test.txt')
        print(f"Loading test file: {test_file}")
        
        try:
            # Load the file
            self.widget.load_file(test_file)
            
            # Process events to allow file loading
            QApplication.processEvents()
            
            # Check if content is loaded
            self.assertTrue(hasattr(self.widget, 'analysis'), "Analysis attribute not found")
            self.assertIn('content', self.widget.analysis, "Content not found in analysis")
            self.assertIn('This is a test document', self.widget.analysis['content'], 
                        "Expected content not found in document")
            
            # Check metadata
            self.assertIn('file_path', self.widget.analysis, "File path not in analysis")
            self.assertEqual(self.widget.analysis['file_path'], test_file, 
                          f"Expected file path {test_file}, got {self.widget.analysis.get('file_path')}")
            self.assertIn('file_size', self.widget.analysis, "File size not in analysis")
            self.assertGreater(self.widget.analysis['file_size'], 0, "File size should be greater than 0")
            
            # Check if content is displayed in the UI
            if hasattr(self.widget, 'content_text'):
                content = self.widget.content_text.toPlainText()
                self.assertIn('This is a test document', content, 
                            "Content not displayed in the UI")
            
            print("✓ Text document loaded successfully")
        except Exception as e:
            self.fail(f"Failed to load text document: {str(e)}\n{traceback.format_exc()}")
    
    def test_summarize_document(self):
        """Test document summarization"""
        print("\n=== Testing document summarization ===")
        test_file = os.path.join(self.test_dir, 'test.txt')
        print(f"Loading test file: {test_file}")
        
        try:
            # Load the document
            self.widget.load_file(test_file)
            
            # Make sure summary tab is set up
            if not hasattr(self.widget, 'summary_text'):
                self.widget.setup_summary_tab()
            
            # Test different summary types
            for summary_type in ['Concise', 'Detailed', 'Key Points']:
                print(f"Testing {summary_type} summary...")
                
                # Set summary type
                if hasattr(self.widget, 'summary_type_combo'):
                    self.widget.summary_type_combo.setCurrentText(summary_type)
                
                # Generate summary
                if hasattr(self.widget, 'generate_summary'):
                    self.widget.generate_summary()
                else:
                    self.skipTest("generate_summary method not found in widget")
                
                # Process events and wait for summary
                QApplication.processEvents()
                time.sleep(1)  # Give it time to process
                
                # Check if summary was generated
                if not hasattr(self.widget, 'summary_text'):
                    self.fail("Summary text widget not found")
                
                # Wait for summary to be generated
                max_attempts = 10
                for _ in range(max_attempts):
                    summary = self.widget.summary_text.toPlainText().strip().lower()
                    if summary and 'test' in summary:
                        break
                    QApplication.processEvents()
                    time.sleep(0.5)
                else:
                    self.fail(f"Summary not generated after {max_attempts} attempts")
                
                # Verify summary content
                self.assertIn('test', summary, 
                            f"Expected 'test' in {summary_type} summary, got: {summary}")
                
                print(f"  ✓ {summary_type} summary generated successfully")
                
        except Exception as e:
            self.fail(f"Failed to generate document summary: {str(e)}\n{traceback.format_exc()}")
    
    def test_qa_document(self):
        """Test document Q&A"""
        print("\n=== Testing document Q&A ===")
        test_file = os.path.join(self.test_dir, 'test.txt')
        print(f"Loading test file: {test_file}")
        
        try:
            # Load the document
            self.widget.load_file(test_file)
            
            # Set up Q&A tab if not already set up
            if not hasattr(self.widget, 'qa_history_widget'):
                if hasattr(self.widget, 'setup_qa_tab'):
                    self.widget.setup_qa_tab()
                else:
                    self.skipTest("setup_qa_tab method not found in widget")
            
            # Test questions
            test_questions = [
                "What is this document about?",
                "How many words does it contain?",
                "What is the main topic?"
            ]
            
            for question in test_questions:
                print(f"Asking question: {question}")
                
                # Set the question
                if hasattr(self.widget, 'qa_input'):
                    self.widget.qa_input.setText(question)
                else:
                    self.fail("qa_input widget not found")
                
                # Ask the question
                if hasattr(self.widget, 'ask_question'):
                    self.widget.ask_question()
                else:
                    self.fail("ask_question method not found")
                
                # Process events and wait for response
                QApplication.processEvents()
                
                # Wait for answer with timeout
                max_attempts = 10
                answer_found = False
                
                for _ in range(max_attempts):
                    if (hasattr(self.widget, 'qa_history') and 
                        len(self.widget.qa_history) > 0 and 
                        any(qa['question'] == question for qa in self.widget.qa_history)):
                        answer_found = True
                        break
                    QApplication.processEvents()
                    time.sleep(0.5)
                
                if not answer_found:
                    self.fail(f"No answer received for question: {question}")
                
                # Find the question in history
                found = False
                for qa in self.widget.qa_history:
                    if qa.get('question') == question:
                        found = True
                        self.assertIn('answer', qa, "No answer found in Q&A history")
                        self.assertIsInstance(qa['answer'], str, "Answer is not a string")
                        self.assertGreater(len(qa['answer'].strip()), 0, "Empty answer in Q&A history")
                        print(f"  ✓ Got answer: {qa['answer'][:50]}...")
                        break
                        
                self.assertTrue(found, f"Question '{question}' not found in Q&A history")
            
            # Test conversation history
            self.assertEqual(len(self.widget.qa_history), len(test_questions), 
                           f"Expected {len(test_questions)} Q&A pairs in history, got {len(self.widget.qa_history)}")
            
            print("✓ All Q&A tests passed")
            
        except Exception as e:
            self.fail(f"Failed to test document Q&A: {str(e)}\n{traceback.format_exc()}")
    
    def test_large_document_handling(self):
        """Test handling of large documents"""
        print("\n=== Testing large document handling ===")
        test_file = os.path.join(self.test_dir, 'large.txt')
        print(f"Loading large test file: {test_file}")
        
        try:
            # Create a large test file if it doesn't exist
            if not os.path.exists(test_file):
                with open(test_file, 'w', encoding='utf-8') as f:
                    # Generate a large text file (about 1MB)
                    for _ in range(10000):
                        f.write("This is a test line in a large document. " * 10 + "\n")
            
            # Get file size
            file_size = os.path.getsize(test_file)
            print(f"File size: {file_size} bytes")
            
            # Load the file
            self.widget.load_file(test_file)
            QApplication.processEvents()
            
            # Check if content was loaded and truncated
            self.assertTrue(hasattr(self.widget, 'analysis'), "Analysis attribute not found")
            self.assertIn('content', self.widget.analysis, "Content not found in analysis")
            
            # Check if content was truncated to a reasonable size
            content_length = len(self.widget.analysis['content'])
            print(f"Loaded content length: {content_length} characters")
            
            # Define reasonable limits (adjust based on your application's requirements)
            max_expected_size = 100000  # 100KB should be more than enough for analysis
            min_expected_size = 1000    # At least 1KB of content should be loaded
            
            self.assertLess(content_length, max_expected_size, 
                          f"Document content too large ({content_length} > {max_expected_size})")
            self.assertGreater(content_length, min_expected_size, 
                           f"Document content too small ({content_length} < {min_expected_size})")
            
            # Verify the content is properly truncated (not cut in the middle of a word/sentence)
            if content_length > 0:
                last_char = self.widget.analysis['content'][-1]
                self.assertIn(last_char, ['.', '!', '?', '\n'], 
                             f"Document content ends with '{last_char}', expected sentence terminator")
            
            print("✓ Large document handling test passed")
            
        except Exception as e:
            self.fail(f"Failed to test large document handling: {str(e)}\n{traceback.format_exc()}")
    
    def test_error_handling(self):
        """Test error handling for invalid files and edge cases"""
        print("\n=== Testing error handling ===")
        
        try:
            # Test non-existent file
            print("Testing non-existent file...")
            with self.assertRaises(FileNotFoundError):
                self.widget.load_file("nonexistent.txt")
            print("  ✓ Correctly handled non-existent file")
            
            # Test invalid file type
            print("Testing invalid file type...")
            invalid_file = os.path.join(self.test_dir, 'invalid.xyz')
            with open(invalid_file, 'w') as f:
                f.write("test")
            
            with self.assertRaises(ValueError):
                self.widget.load_file(invalid_file)
            print("  ✓ Correctly handled invalid file type")
            
            # Test empty file
            print("Testing empty file...")
            empty_file = os.path.join(self.test_dir, 'empty.txt')
            with open(empty_file, 'w') as f:
                pass
                
            with self.assertRaises(ValueError):
                self.widget.load_file(empty_file)
            print("  ✓ Correctly handled empty file")
            
            # Test summarization with no document loaded
            print("Testing summarization with no document...")
            original_analysis = getattr(self.widget, 'analysis', None)
            self.widget.analysis = None
            
            # Mock the warning message box
            with patch.object(QMessageBox, 'warning') as mock_warning:
                if hasattr(self.widget, 'generate_summary'):
                    self.widget.generate_summary()
                    mock_warning.assert_called_once()
                    print("  ✓ Correctly handled summarization with no document")
                else:
                    self.skipTest("generate_summary method not found in widget")
            
            # Restore original analysis
            self.widget.analysis = original_analysis
            
            # Test Q&A with no document loaded
            print("Testing Q&A with no document...")
            self.widget.analysis = None
            
            # Mock the warning message box
            with patch.object(QMessageBox, 'warning') as mock_warning:
                if hasattr(self.widget, 'ask_question'):
                    self.widget.ask_question()
                    mock_warning.assert_called_once()
                    print("  ✓ Correctly handled Q&A with no document")
                else:
                    self.skipTest("ask_question method not found in widget")
            
            # Test with corrupted file
            print("Testing corrupted file...")
            corrupted_file = os.path.join(self.test_dir, 'corrupted.pdf')
            with open(corrupted_file, 'wb') as f:
                f.write(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')  # Invalid PDF header
                
            with self.assertRaises((ValueError, RuntimeError)):
                self.widget.load_file(corrupted_file)
            print("  ✓ Correctly handled corrupted file")
            
        except Exception as e:
            self.fail(f"Error handling test failed: {str(e)}\n{traceback.format_exc()}")
        finally:
            # Clean up test files
            for filename in ['invalid.xyz', 'empty.txt', 'corrupted.pdf']:
                file_path = os.path.join(self.test_dir, filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        # Remove test directory
        import shutil
        test_dir = os.path.join(os.path.dirname(__file__), 'test_docs')
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        
        # Delete the QApplication instance
        if cls.app:
            cls.app.quit()

class ColorTextTestResult(unittest.TextTestResult):
    """Custom test result class with colored output"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dots = False
    
    def startTest(self, test):
        super().startTest(test)
        test_id = test.id().split('.')[-1]
        print(f"\n\n{'-'*70}\nRunning test: {test_id}\n{'-'*70}")
    
    def addSuccess(self, test):
        super().addSuccess(test)
        print("\n✅ Test passed")
    
    def addError(self, test, err):
        super().addError(test, err)
        print(f"\n❌ Test error: {err[1]}")
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        print(f"\n❌ Test failed: {err[1]}")
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        print(f"\n⚠️  Test skipped: {reason}")

def run_tests():
    """Run the tests and print a detailed summary"""
    print("\n" + "=" * 80)
    print("STARTING DOCUMENT FEATURES TEST SUITE".center(80))
    print("=" * 80)
    
    # Create test suite
    test_loader = unittest.TestLoader()
    test_suite = test_loader.loadTestsFromTestCase(TestDocumentFeatures)
    
    # Create a custom test runner with our result class
    test_runner = unittest.TextTestRunner(
        resultclass=ColorTextTestResult,
        verbosity=2,
        descriptions=True,
        failfast=False,
        buffer=False
    )
    
    # Run tests
    print("\n" + "-" * 80)
    print("RUNNING TESTS".center(80))
    print("-" * 80)
    start_time = time.time()
    result = test_runner.run(test_suite)
    end_time = time.time()
    
    # Calculate test duration
    duration = end_time - start_time
    
    # Print detailed summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY".center(80))
    print("=" * 80)
    
    # Print test statistics
    print(f"\n{'Total Tests:':<20} {result.testsRun}")
    print(f"{'Passed:':<20} {result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)}")
    print(f"{'Failed:':<20} {len(result.failures)}")
    print(f"{'Errors:':<20} {len(result.errors)}")
    print(f"{'Skipped:':<20} {len(result.skipped)}")
    print(f"{'Duration:':<20} {duration:.2f} seconds")
    
    # Print detailed failure/error information
    if result.failures:
        print("\n" + "FAILURES".center(80, '-'))
        for i, (test, traceback_text) in enumerate(result.failures, 1):
            print(f"\n{i}. {test.id()}")
            print("-" * 80)
            print(traceback_text)
    
    if result.errors:
        print("\n" + "ERRORS".center(80, '-'))
        for i, (test, traceback_text) in enumerate(result.errors, 1):
            print(f"\n{i}. {test.id()}")
            print("-" * 80)
            print(traceback_text)
    
    if result.skipped:
        print("\n" + "SKIPPED TESTS".center(80, '-'))
        for i, (test, reason) in enumerate(result.skipped, 1):
            print(f"{i}. {test.id()}: {reason}")
    
    # Print final result
    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED SUCCESSFULLY!".center(80))
    else:
        print("❌ SOME TESTS FAILED!".center(80))
    print("=" * 80)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    run_tests()
