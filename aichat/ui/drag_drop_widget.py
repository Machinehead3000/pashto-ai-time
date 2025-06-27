"""
Drag and drop widget for file uploads.

This module provides a QWidget that handles file drag and drop operations,
providing visual feedback and file type validation.
"""

import os
from pathlib import Path
from typing import List, Callable, Optional, Set

from PyQt5.QtCore import Qt, QMimeData, QSize, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QPainter, QColor, QPen, QFont, QFontMetrics
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFileDialog, QPushButton, QSizePolicy,
    QMessageBox, QHBoxLayout
)

# Supported file types and their corresponding MIME types
SUPPORTED_MIME_TYPES = {
    'text/plain': ['.txt', '.md', '.csv', '.json', '.xml', '.html', '.css', '.js', '.py', '.java', '.cpp', '.h', '.c', 
                  '.hpp', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.ts', '.jsx', '.tsx', '.dart', '.sh', 
                  '.ps1', '.bat', '.cmd', '.ini', '.cfg', '.conf', '.yaml', '.yml', '.toml', '.env', '.gitignore', 
                  '.dockerignore', '.editorconfig', '.gitattributes'],
    'application/pdf': ['.pdf'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/vnd.ms-excel': ['.xls'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'application/vnd.ms-powerpoint': ['.ppt'],
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
    'image/*': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'],
    'audio/*': ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac'],
    'video/*': ['.mp4', '.webm', '.mov', '.avi', '.mkv', '.flv', '.wmv'],
    'application/zip': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
}

# Flatten the supported extensions for quick lookup
SUPPORTED_EXTENSIONS = set()
for ext_list in SUPPORTED_MIME_TYPES.values():
    SUPPORTED_EXTENSIONS.update(ext_list)

class DragDropWidget(QWidget):
    """
    A widget that handles file drag and drop operations.
    
    Signals:
        files_dropped: Emitted when files are dropped on the widget.
                      Parameters:
                          List[str]: List of file paths
    """
    
    files_dropped = pyqtSignal(list)
    
    def __init__(self, parent=None, allowed_extensions: Optional[Set[str]] = None):
        """
        Initialize the drag and drop widget.
        
        Args:
            parent: Parent widget
            allowed_extensions: Set of allowed file extensions (e.g., {'.txt', '.pdf'}).
                              If None, all supported file types are allowed.
        """
        super().__init__(parent)
        self.allowed_extensions = allowed_extensions or SUPPORTED_EXTENSIONS
        self._init_ui()
        self._setup_drag_drop()
    
    def _init_ui(self):
        """Initialize the user interface."""
        self.setAcceptDrops(True)
        self.setMinimumSize(300, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Icon
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setPixmap(self._create_drop_icon(False))
        
        # Text
        self.text_label = QLabel("Drag & drop files here")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #888;
                margin: 10px 0;
            }
        """)
        
        # Or separator
        or_label = QLabel("or")
        or_label.setAlignment(Qt.AlignCenter)
        or_label.setStyleSheet("color: #888;")
        
        # Browse button
        self.browse_button = QPushButton("Browse Files")
        self.browse_button.setMinimumWidth(150)
        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a80d2;
            }
            QPushButton:pressed {
                background-color: #2a70c2;
            }
        """)
        self.browse_button.clicked.connect(self._on_browse_clicked)
        
        # Add widgets to layout
        layout.addStretch()
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addWidget(or_label)
        layout.addWidget(self.browse_button, 0, Qt.AlignCenter)
        layout.addStretch()
    
    def _setup_drag_drop(self):
        """Set up drag and drop properties."""
        self.setAcceptDrops(True)
    
    def _create_drop_icon(self, is_dragging: bool) -> QPixmap:
        """
        Create an icon for the drag and drop area.
        
        Args:
            is_dragging: Whether the user is currently dragging files over the widget.
            
        Returns:
            QPixmap: The generated icon.
        """
        size = QSize(80, 80)
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background circle
        if is_dragging:
            painter.setBrush(QColor(230, 240, 255, 200))
            painter.setPen(QPen(QColor(100, 150, 255, 200), 2, Qt.DashLine))
        else:
            painter.setBrush(QColor(245, 245, 245))
            painter.setPen(QPen(QColor(200, 200, 200), 2, Qt.SolidLine))
        
        painter.drawEllipse(0, 0, size.width(), size.height())
        
        # Draw icon
        font = QFont("Arial", 24, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(150, 150, 150) if not is_dragging else QColor(100, 150, 255))
        
        # Draw upload icon (simple arrow up)
        painter.drawText(0, 0, size.width(), size.height(), 
                        Qt.AlignCenter, "↑")
        
        painter.end()
        return pixmap
    
    def _on_browse_clicked(self):
        """Handle browse button click."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        
        # Set name filters based on allowed extensions
        name_filters = []
        
        # Group extensions by category
        categories = {}
        for mime, exts in SUPPORTED_MIME_TYPES.items():
            # Filter extensions to only include allowed ones
            filtered_exts = [ext for ext in exts if ext in self.allowed_extensions]
            if filtered_exts:
                # Convert extensions to format: "*.ext1 *.ext2"
                extensions_str = ' '.join(f'*{ext}' for ext in filtered_exts)
                # Get category name from MIME type (e.g., 'text/plain' -> 'Text files')
                category = mime.split('/')[0].capitalize() + ' files'
                if category not in categories:
                    categories[category] = []
                categories[category].append(extensions_str)
        
        # Create name filters
        for category, ext_groups in categories.items():
            name_filters.append(f"{category} ({' '.join(ext_groups)})")
        
        name_filters.append("All files (*)")
        file_dialog.setNameFilters(name_filters)
        
        if file_dialog.exec_():
            files = file_dialog.selectedFiles()
            if files:
                self._process_files(files)
    
    def _process_files(self, file_paths: List[str]):
        """
        Process the list of file paths and emit the files_dropped signal.
        
        Args:
            file_paths: List of file paths to process
        """
        valid_files = []
        invalid_files = []
        
        for file_path in file_paths:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in self.allowed_extensions:
                valid_files.append(file_path)
            else:
                invalid_files.append(file_path)
        
        if invalid_files:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Unsupported Files")
            
            if len(invalid_files) == 1:
                msg.setText(f"The following file type is not supported:")
            else:
                msg.setText(f"The following {len(invalid_files)} file types are not supported:")
            
            # Create a list of unsupported files
            file_list = '\n'.join(f'• {os.path.basename(f)}' for f in invalid_files[:10])
            if len(invalid_files) > 10:
                file_list += f'\n...and {len(invalid_files) - 10} more'
            
            msg.setInformativeText(file_list)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        
        if valid_files:
            self.files_dropped.emit(valid_files)
    
    # Drag and drop event handlers
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            # Check if any of the dragged files have a supported extension
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext in self.allowed_extensions:
                        event.acceptProposedAction()
                        self.icon_label.setPixmap(self._create_drop_icon(True))
                        return
        
        event.ignore()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        self.icon_label.setPixmap(self._create_drop_icon(False))
        event.accept()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        self.icon_label.setPixmap(self._create_drop_icon(False))
        
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_paths.append(url.toLocalFile())
            
            if file_paths:
                self._process_files(file_paths)
                event.acceptProposedAction()
                return
        
        event.ignore()
