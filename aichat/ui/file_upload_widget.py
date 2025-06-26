"""
File upload widget with drag and drop support and file analysis capabilities.
"""
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QHBoxLayout, QListWidget, QListWidgetItem, QAbstractItemView,
    QProgressBar, QSizePolicy, QMenu, QAction, QToolTip
)
import os
import json
from typing import Dict, List, Optional, Set, Union

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QListWidget, QListWidgetItem, QAbstractItemView, QProgressBar, 
    QSizePolicy, QMenu, QAction, QDialog, QTextEdit, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QMimeData, QSize, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QIcon, QPixmap, QFont, QColor

from ..utils.file_analyzer import FileAnalyzer


class FileProcessor(QObject):
    """Worker class for processing files in a separate thread."""
    progress_updated = pyqtSignal(int, str)  # progress_percent, status
    file_processed = pyqtSignal(str, dict)   # file_path, analysis_result
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)         # error_message
    
    def __init__(self):
        super().__init__()
        self._is_running = False
        self._current_file = None
    
    def process_files(self, file_paths):
        """Process a list of files asynchronously."""
        if self._is_running:
            return
            
        self._is_running = True
        total_files = len(file_paths)
        
        try:
            for i, file_path in enumerate(file_paths, 1):
                if not self._is_running:
                    break
                    
                self._current_file = file_path
                progress = int((i / total_files) * 100)
                self.progress_updated.emit(progress, f"Analyzing {os.path.basename(file_path)}...")
                
                try:
                    # Analyze the file
                    analysis = FileAnalyzer.analyze_file(file_path)
                    self.file_processed.emit(file_path, analysis)
                except Exception as e:
                    self.error_occurred.emit(f"Error analyzing {os.path.basename(file_path)}: {str(e)}")
                
                # Small delay to prevent UI freezing
                QThread.msleep(100)
                
        except Exception as e:
            self.error_occurred.emit(f"Processing error: {str(e)}")
        finally:
            self._is_running = False
            self._current_file = None
            self.finished.emit()
    
    def stop_processing(self):
        """Stop the current processing operation."""
        self._is_running = False

class FileUploadWidget(QWidget):
    """
    A widget for uploading files with drag and drop support.
    """
    # Signal emitted when files are added
    files_added = pyqtSignal(list)  # List of file paths
    
    # Signal emitted when a file is removed
    file_removed = pyqtSignal(str)  # Path of removed file
    
    # Signal emitted when files are processed
    files_processed = pyqtSignal(dict)  # Dict with file paths and their content/analysis
    
    def __init__(self, parent=None, allowed_extensions: Optional[List[str]] = None):
        """
        Initialize the file upload widget with analysis capabilities.
        
        Args:
            parent: Parent widget
            allowed_extensions: List of allowed file extensions (e.g., ['.txt', '.pdf', '.csv'])
        """
        super().__init__(parent)
        self.allowed_extensions = allowed_extensions or [
            '.txt', '.pdf', '.csv', '.xlsx', '.xls', '.docx', '.doc', 
            '.jpg', '.jpeg', '.png', '.py', '.ipynb', '.json', '.md',
            '.pptx', '.ppt', '.odt', '.rtf', '.tsv', '.log'
        ]
        self.file_paths = []
        self.file_analyses = {}
        self.max_file_size = 50 * 1024 * 1024  # 50MB default max
        self.setAcceptDrops(True)
        self.setup_ui()
        
        # Setup file icons
        self.file_icons = {
            'pdf': ':/icons/pdf_icon.png',
            'document': ':/icons/word_icon.png',
            'spreadsheet': ':/icons/excel_icon.png',
            'image': ':/icons/image_icon.png',
            'code': ':/icons/code_icon.png',
            'text': ':/icons/text_icon.png',
            'archive': ':/icons/archive_icon.png',
            'default': ':/icons/file_icon.png'
        }
    
    def setup_ui(self):
        """Initialize the user interface with enhanced styling and feedback."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Drop area
        self.drop_area = QLabel("Drag & drop files here or click to browse")
        self.drop_area.setAlignment(Qt.AlignCenter)
        self.drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #4a4a6a;
                border-radius: 8px;
                padding: 20px;
                color: #8a8aa3;
                background-color: #1a1a2e;
                font-size: 14px;
                font-weight: 500;
                margin: 5px;
            }
            QLabel:hover {
                border-color: #6e44ff;
                background-color: #25253a;
                color: #b8b8d1;
            }
            QLabel[active="true"] {
                border-color: #6e44ff;
                background-color: #2a2a40;
                border-style: solid;
                border-width: 3px;
            }
        """)
        self.drop_area.setMinimumHeight(150)
        self.drop_area.setProperty("active", False)
        self.drop_area.installEventFilter(self)
        
        # Progress bar for file processing
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #2a2a4a;
                border-radius: 4px;
                background: #1a1a2e;
                text-align: center;
                height: 8px;
            }
            QProgressBar::chunk {
                background: #6e44ff;
                border-radius: 4px;
            }
        """)
        
        # File list with enhanced styling
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a2e;
                border: 1px solid #2a2a4a;
                border-radius: 4px;
                padding: 2px;
                color: #e0e0ff;
                font-size: 12px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 5px;
                border-bottom: 1px solid #2a2a4a;
                margin: 2px 0;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #2a2a4a;
            }
            QListWidget::item:selected {
                background-color: #3a3a5a;
                color: #ffffff;
                border: 1px solid #6e44ff;
            }
            QListWidget::item:selected:!active {
                background-color: #3a3a5a;
            }
        """)
        self.file_list.setVisible(False)
        self.file_list.setIconSize(QSize(24, 24))
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)
        self.file_list.itemDoubleClicked.connect(self.show_file_analysis)
        
        # Buttons with consistent styling
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Browse button
        self.browse_btn = QPushButton("Browse Files")
        self.browse_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_DirOpenIcon')))
        self.browse_btn.clicked.connect(self.browse_files)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a4a;
                color: #e0e0ff;
                border: 1px solid #3a3a5a;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3a3a5a;
                border-color: #6e44ff;
            }
            QPushButton:pressed {
                background-color: #4a4a6a;
            }
            QPushButton:disabled {
                background-color: #1a1a2e;
                color: #5a5a7a;
                border-color: #2a2a4a;
            }
        """)
        
        # Remove button
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_TrashIcon')))
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a1a1a;
                color: #ffb3b3;
                border: 1px solid #5a2a2a;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #5a2a2a;
                border-color: #ff4d4d;
            }
            QPushButton:pressed {
                background-color: #6a3a3a;
            }
            QPushButton:disabled {
                background-color: #2a1a1a;
                color: #7a5a5a;
                border-color: #3a2a2a;
            }
        """)
        self.remove_btn.clicked.connect(self.remove_selected_files)
        self.remove_btn.setEnabled(False)
        
        # Clear button
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_DialogResetButton')))
        self.clear_btn.clicked.connect(self.clear_files)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a4a;
                color: #e0e0ff;
                border: 1px solid #3a3a5a;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3a3a5a;
                border-color: #6e44ff;
            }
            QPushButton:pressed {
                background-color: #4a4a6a;
            }
            QPushButton:disabled {
                background-color: #1a1a2e;
                color: #5a5a7a;
                border-color: #2a2a4a;
            }
        """)
        
        # Analyze button
        self.analyze_btn = QPushButton("Analyze Files")
        self.analyze_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_FileDialogDetailedView')))
        self.analyze_btn.clicked.connect(self.analyze_files)
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a4a2a;
                color: #b3ffcc;
                border: 1px solid #2a5a3a;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2a5a3a;
                border-color: #4cff88;
            }
            QPushButton:pressed {
                background-color: #3a6a4a;
            }
            QPushButton:disabled {
                background-color: #1a2a1a;
                color: #5a7a5a;
                border-color: #2a3a2a;
            }
        """)
        
        # Add buttons to layout
        button_layout.addWidget(self.browse_btn)
        button_layout.addWidget(self.remove_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.analyze_btn)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #8a8aa3; font-size: 11px;")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Add widgets to layout
        layout.addWidget(self.drop_area)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.file_list)
        layout.addLayout(button_layout)
        layout.addWidget(self.status_label)
        
        # Update button states
        self.update_button_states()
        
        # Setup file processing worker
        self.worker_thread = QThread()
        self.worker = FileProcessor()
        self.worker.moveToThread(self.worker_thread)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.file_processed.connect(self.on_file_processed)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error_occurred.connect(self.on_processing_error)
        self.worker_thread.start()
        
        # Connect signals
        self.file_list.itemSelectionChanged.connect(self.update_button_states)
        
        # Connect signals
        self.file_list.itemSelectionChanged.connect(self.update_remove_button)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        if not event.mimeData().hasUrls():
            return
            
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path and self.is_file_allowed(file_path):
                files.append(file_path)
        
        if files:
            self.add_files(files)
    
    def browse_files(self):
        """Open file dialog to select files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            "",
            "All Supported Files ({});;All Files (*)".format(" ".join([f"*{ext}" for ext in self.allowed_extensions]))
        )
        
        if files:
            self.add_files(files)
    
    def add_files(self, file_paths: List[str]):
        """
        Add files to the upload list.
        
        Args:
            file_paths: List of file paths to add
        """
        new_files = []
        for file_path in file_paths:
            if file_path not in self.file_paths and self.is_file_allowed(file_path):
                self.file_paths.append(file_path)
                new_files.append(file_path)
                
                # Add to list widget
                item = QListWidgetItem(file_path)
                item.setData(Qt.UserRole, file_path)
                self.file_list.addItem(item)
        
        if new_files:
            self.file_list.setVisible(True)
            
        if hasattr(self, 'files_added'):
            self.files_added.emit(new_files)
            
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"Added {len(new_files)} file(s)")
            
        self.update_button_states()
    
    def is_file_allowed(self, file_path: str) -> bool:
        """
        Check if a file is allowed based on its extension.
        
        Args:
            file_path: Path of the file to check
        
        Returns:
            bool: True if the file is allowed, False otherwise
        """
        return any(file_path.lower().endswith(ext) for ext in self.allowed_extensions)
    
    def get_files(self) -> List[str]:
        """
        Get the list of selected files.
        
        Returns:
            List of file paths
        """
        return self.file_paths.copy()
    
    def clear(self):
        """Clear all files from the upload widget."""
        self.file_paths.clear()
        self.file_list.clear()
        self.file_list.setVisible(False)
    
    def analyze_files(self):
        """Start analysis of the selected files."""
        if hasattr(self, 'worker') and hasattr(self.worker, '_is_running') and self.worker._is_running:
            self.status_label.setText("Processing in progress...")
            return
            
        selected_items = self.file_list.selectedItems()
        file_paths = [item.data(Qt.UserRole) for item in selected_items] if selected_items else self.file_paths
        
        if not file_paths:
            self.status_label.setText("No files to analyze")
            return
            
        self.start_analysis(file_paths)
    
    def start_analysis(self, file_paths):
        """Start the file analysis process."""
        if not file_paths:
            return
            
        # Reset UI
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Starting analysis...")
        self.status_label.setVisible(True)
        
        # Disable UI elements during processing
        self.setEnabled(False)
        
        # Start the worker thread if not already running
        if not hasattr(self, 'worker_thread') or not self.worker_thread.isRunning():
            self.worker_thread = QThread()
            self.worker = FileProcessor()
            self.worker.moveToThread(self.worker_thread)
            
            # Connect signals
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.file_processed.connect(self.on_file_processed)
            self.worker.finished.connect(self.on_processing_finished)
            self.worker.error_occurred.connect(self.on_processing_error)
            
            # Start the thread
            self.worker_thread.start()
        
        # Start processing files
        self.worker.process_files(file_paths)
    
    @pyqtSlot(int, str)
    def update_progress(self, progress, status):
        """Update the progress bar and status."""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
    
    @pyqtSlot(str, dict)
    def on_file_processed(self, file_path, analysis):
        """Handle a completed file analysis."""
        self.file_analyses[file_path] = analysis
        
        # Update the file list item
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.data(Qt.UserRole) == file_path:
                # Update item with analysis status
                file_name = os.path.basename(file_path)
                if 'error' in analysis:
                    item.setText(f"{file_name} (Error: {analysis['error']})")
                    item.setForeground(QColor('#ff6b6b'))
                else:
                    item_type = analysis.get('type', 'unknown').upper()
                    item.setText(f"{file_name} ({item_type})")
                    item.setForeground(QColor('#a0e0a0'))
                break
    
    @pyqtSlot()
    def on_processing_finished(self):
        """Handle completion of file processing."""
        self.progress_bar.setValue(100)
        self.status_label.setText(f"Analysis complete. Processed {len(self.file_analyses)} files.")
        self.setEnabled(True)
        self.update_button_states()
        
        # Emit signal with all analysis results
        if self.file_analyses:
            self.files_processed.emit(self.file_analyses)
    
    @pyqtSlot(str)
    def on_processing_error(self, error_message):
        """Handle errors during processing."""
        self.status_label.setText(f"Error: {error_message}")
        self.status_label.setStyleSheet("color: #ff6b6b;")
        self.setEnabled(True)
        self.update_button_states()
    
    def show_context_menu(self, position):
        """Show context menu for file actions."""
        item = self.file_list.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        
        # View details action
        view_action = QAction("View Details", self)
        view_action.triggered.connect(lambda: self.show_file_analysis(item))
        menu.addAction(view_action)
        
        # Remove action
        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(lambda: self.remove_file(item))
        menu.addAction(remove_action)
        
        # Show context menu
        menu.exec_(self.file_list.viewport().mapToGlobal(position))
    
    def show_file_analysis(self, item):
        """Show detailed analysis of a file."""
        file_path = item.data(Qt.UserRole)
        analysis = self.file_analyses.get(file_path, {})
        
        # Create and show a dialog with analysis details
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Analysis: {os.path.basename(file_path)}")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Show analysis details
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a2e;
                color: #e0e0ff;
                border: 1px solid #2a2a4a;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Monospace';
            }
        """)
        
        # Format analysis as JSON
        import json
        formatted_analysis = json.dumps(analysis, indent=2, default=str)
        text_edit.setPlainText(formatted_analysis)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        
        layout.addWidget(QLabel(f"<b>Analysis for {os.path.basename(file_path)}</b>"))
        layout.addWidget(text_edit, 1)
        layout.addWidget(button_box)
        
        dialog.exec_()
    
    def remove_file(self, item):
        """Remove a file from the list."""
        file_path = item.data(Qt.UserRole)
        if file_path in self.file_paths:
            self.file_paths.remove(file_path)
        if file_path in self.file_analyses:
            del self.file_analyses[file_path]
            
        self.file_list.takeItem(self.file_list.row(item))
        self.file_removed.emit(file_path)
        
        if not self.file_paths:
            self.file_list.setVisible(False)
        
        self.update_button_states()
    
    def remove_selected_files(self):
        """Remove selected files from the list."""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
            
        for item in selected_items:
            self.remove_file(item)
    
    def clear_files(self):
        """Clear all files from the list."""
        if hasattr(self, 'worker') and hasattr(self.worker, '_is_running') and self.worker._is_running:
            self.worker.stop_processing()
            
        self.file_paths.clear()
        self.file_analyses.clear()
        self.file_list.clear()
        self.file_list.setVisible(False)
        self.status_label.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.update_button_states()
    
    def closeEvent(self, event):
        """Clean up resources when the widget is closed."""
        if hasattr(self, 'worker_thread') and self.worker_thread.isRunning():
            if hasattr(self, 'worker') and hasattr(self.worker, 'stop_processing'):
                self.worker.stop_processing()
            self.worker_thread.quit()
            self.worker_thread.wait()
        event.accept()
