"""
Tests for the file upload widget functionality.
"""
import os
import sys
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QMimeData, QUrl
from PyQt5.QtTest import QTest

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aichat.ui.file_upload_widget import FileUploadWidget, FileProcessor

# Pytest fixtures
@pytest.fixture
def app():
    """Provide a QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

@pytest.fixture
def file_upload_widget(app):
    """Provide a FileUploadWidget instance for testing."""
    widget = FileUploadWidget()
    yield widget
    widget.close()

@pytest.fixture
def test_files():
    """Create temporary test files."""
    files = []
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        test_data = {
            'test.txt': 'This is a test text file.',
            'test.csv': 'id,name\n1,Test\n2,Example',
            'test.json': '{"key": "value"}'
        }
        
        for filename, content in test_data.items():
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write(content)
            files.append(file_path)
            
        # Yield the files and keep the temp directory alive
        yield files

# Test cases
class TestFileUploadWidget:
    """Test cases for the FileUploadWidget class."""
    
    def test_initial_state(self, file_upload_widget):
        """Test the initial state of the widget."""
        assert file_upload_widget is not None
        assert file_upload_widget.file_paths == []
        assert file_upload_widget.file_analyses == {}
        assert not file_upload_widget.file_list.isVisible()
        
    def test_add_single_file(self, file_upload_widget, test_files):
        """Test adding a single file to the widget."""
        test_file = test_files[0]  # Use the first test file
        file_upload_widget.add_files([test_file])
        
        assert len(file_upload_widget.file_paths) == 1
        assert test_file in file_upload_widget.file_paths
        assert file_upload_widget.file_list.isVisible()
        
    def test_add_multiple_files(self, file_upload_widget, test_files):
        """Test adding multiple files to the widget."""
        file_upload_widget.add_files(test_files)
        
        assert len(file_upload_widget.file_paths) == len(test_files)
        for file_path in test_files:
            assert file_path in file_upload_widget.file_paths
            
    def test_remove_file(self, file_upload_widget, test_files):
        """Test removing a file from the widget."""
        test_file = test_files[0]
        file_upload_widget.add_files([test_file])
        
        # Remove the file
        file_upload_widget.remove_file(file_upload_widget.file_list.item(0))
        
        assert len(file_upload_widget.file_paths) == 0
        assert test_file not in file_upload_widget.file_paths
        
    def test_clear_files(self, file_upload_widget, test_files):
        """Test clearing all files from the widget."""
        file_upload_widget.add_files(test_files)
        file_upload_widget.clear_files()
        
        assert len(file_upload_widget.file_paths) == 0
        assert not file_upload_widget.file_list.isVisible()
        
    def test_file_type_validation(self, file_upload_widget, test_files):
        """Test that only allowed file types can be added."""
        # Create a file with an invalid extension
        with tempfile.NamedTemporaryFile(suffix='.invalid', delete=False) as f:
            f.write(b'Test content')
            invalid_file = f.name
            
        try:
            # Try to add the invalid file
            file_upload_widget.add_files([invalid_file])
            assert len(file_upload_widget.file_paths) == 0
            
            # Add a valid file
            file_upload_widget.add_files([test_files[0]])
            assert len(file_upload_widget.file_paths) == 1
            
        finally:
            # Clean up the temporary file
            if os.path.exists(invalid_file):
                os.unlink(invalid_file)
    
    @patch('aichat.ui.file_upload_widget.FileProcessor')
    def test_file_analysis(self, mock_processor_class, file_upload_widget, test_files):
        """Test file analysis functionality."""
        # Setup mock
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        
        # Add a test file
        test_file = test_files[0]
        file_upload_widget.add_files([test_file])
        
        # Start analysis
        file_upload_widget.analyze_files()
        
        # Verify the processor was called
        mock_processor.process_files.assert_called_once_with([test_file])
        
    def test_drag_drop_events(self, file_upload_widget, test_files, qtbot):
        """Test drag and drop functionality."""
        # Create a mock drag event
        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(path) for path in test_files]
        mime_data.setUrls(urls)
        
        # Create a mock drop event
        event = MagicMock()
        event.mimeData.return_value = mime_data
        
        # Simulate drag enter event
        drag_enter_event = MagicMock()
        drag_enter_event.mimeData.return_value = mime_data
        file_upload_widget.dragEnterEvent(drag_enter_event)
        drag_enter_event.acceptProposedAction.assert_called_once()
        
        # Simulate drop event
        file_upload_widget.dropEvent(event)
        
        # Verify files were added
        assert len(file_upload_widget.file_paths) == len(test_files)
        
class TestFileProcessor:
    """Test cases for the FileProcessor class."""
    
    def test_process_files(self, qtbot):
        """Test file processing in a separate thread."""
        # Create a test file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'Test content')
            test_file = f.name
            
        try:
            # Create processor and signals
            processor = FileProcessor()
            
            # Connect to signals
            progress_values = []
            processed_files = []
            
            def on_progress(value, status):
                progress_values.append((value, status))
                
            def on_processed(file_path, result):
                processed_files.append((file_path, result))
            
            processor.progress_updated.connect(on_progress)
            processor.file_processed.connect(on_processed)
            
            # Process the file
            with qtbot.waitSignal(processor.finished, timeout=5000) as blocker:
                processor.process_files([test_file])
                
            # Verify signals were emitted
            assert len(progress_values) > 0
            assert len(processed_files) == 1
            assert processed_files[0][0] == test_file
            
        finally:
            # Clean up
            if os.path.exists(test_file):
                os.unlink(test_file)

if __name__ == "__main__":
    pytest.main([__file__])
