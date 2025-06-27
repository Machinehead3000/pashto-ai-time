"""
Test script for the DragDropWidget.

This script provides a simple test application to verify the drag and drop
functionality works as expected.
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTextEdit

# Add the project root to the Python path
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the DragDropWidget
try:
    from aichat.ui.drag_drop_widget import DragDropWidget
    from aichat.ui.drag_drop_widget import SUPPORTED_EXTENSIONS
    print("Imported DragDropWidget from aichat.ui.drag_drop_widget")
except ImportError as e:
    print(f"Error importing DragDropWidget: {e}")
    sys.exit(1)

class TestWindow(QMainWindow):
    """Test window for DragDropWidget."""
    
    def __init__(self):
        """Initialize the test window."""
        super().__init__()
        self.setWindowTitle("Drag & Drop Test")
        self.setMinimumSize(600, 500)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add title
        title = QLabel("Drag & Drop Test")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333;
                margin: 10px 0;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Add description
        desc = QLabel("Try dragging and dropping files onto the area below or click 'Browse Files'")
        desc.setStyleSheet("color: #666;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # Add the drag and drop widget
        self.drag_drop = DragDropWidget()
        self.drag_drop.files_dropped.connect(self.on_files_dropped)
        layout.addWidget(self.drag_drop, 1)
        
        # Add a text area to show dropped files
        self.log_label = QLabel("Dropped files will appear here:")
        layout.addWidget(self.log_label)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                background-color: #f9f9f9;
            }
        """)
        layout.addWidget(self.log_area, 1)
        
        # Add supported extensions info
        extensions = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        info = QLabel(f"Supported extensions: {extensions}")
        info.setWordWrap(True)
        info.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 11px;
                margin-top: 10px;
                padding: 10px;
                background-color: #f0f0f0;
                border-radius: 4px;
            }
        """)
        layout.addWidget(info)
    
    def on_files_dropped(self, file_paths):
        """Handle files dropped on the widget."""
        self.log_area.append("\n--- Dropped files ---")
        for path in file_paths:
            self.log_area.append(f"• {path}")

if __name__ == "__main__":
    # Set up the application
    app = QApplication(sys.argv)
    
    # Apply a clean, modern style
    app.setStyle("Fusion")
    
    # Create and show the test window
    window = TestWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())
