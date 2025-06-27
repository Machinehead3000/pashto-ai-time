"""
Document preview and analysis widget for displaying and interacting with document files.
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QTextEdit, 
                            QTableWidget, QTableWidgetItem, QLabel, QPushButton,
                            QHBoxLayout, QFileDialog, QMessageBox, QHeaderView,
                            QComboBox, QProgressBar, QSplitter, QSizePolicy, QApplication,
                            QLineEdit, QScrollArea, QFrame, QToolButton)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QTextCursor, QFont, QIcon, QTextCharFormat, QTextDocument, QSyntaxHighlighter, QTextFormat

from aichat.utils.file_analyzer import FileAnalyzer
from aichat.models.base import BaseAIModel
from aichat.models.deepseek import DeepSeekModel
from aichat.models.mistral import MistralModel


class DocumentHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for document content."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(Qt.yellow)
        self.highlight_format.setForeground(Qt.black)
        
    def highlightBlock(self, text):
        # This is a placeholder for future highlighting functionality
        pass


class DocumentWorker(QThread):
    """Base worker class for document processing tasks."""
    finished = pyqtSignal(dict)  # result dict with 'type', 'content', 'error' keys
    progress = pyqtSignal(int)   # progress percentage
    
    def __init__(self, model: BaseAIModel, content: str, **kwargs):
        super().__init__()
        self.model = model
        self.content = content
        self.kwargs = kwargs
        self._is_running = True
    
    def stop(self):
        """Stop the worker process."""
        self._is_running = False
        self.quit()
        self.wait(1000)


class SummarizationWorker(DocumentWorker):
    """Worker thread for document summarization."""
    
    def run(self):
        """Run the summarization task."""
        try:
            self.progress.emit(10)
            summary_type = self.kwargs.get('summary_type', 'concise')
            
            # Truncate content if too long (keep first 6000 tokens ~ 24000 chars)
            max_length = 24000
            if len(self.content) > max_length:
                self.content = self.content[:max_length] + "\n\n[Document truncated for summarization]"
            
            self.progress.emit(30)
            
            # Prepare the prompt based on summary type
            if summary_type == 'concise':
                prompt = f"Please provide a concise summary of the following document in 3-5 sentences. Focus on the main points and key information.\n\nDocument:\n{self.content}"
            elif summary_type == 'detailed':
                prompt = f"Please provide a detailed summary of the following document in 2-3 paragraphs. Include key points, supporting details, and any important context.\n\nDocument:\n{self.content}"
            else:  # 'key_points'
                prompt = f"Please provide key points from the following document as a bulleted list. Include 5-8 main points.\n\nDocument:\n{self.content}"
            
            self.progress.emit(50)
            
            # Generate summary
            response = self.model.generate(prompt, max_tokens=1000, temperature=0.7)
            
            self.progress.emit(90)
            
            if response and response.strip():
                self.finished.emit({
                    'type': 'summary',
                    'content': response.strip(),
                    'error': ''
                })
            else:
                self.finished.emit({
                    'type': 'summary',
                    'content': '',
                    'error': 'Failed to generate summary: Empty response from model'
                })
                
        except Exception as e:
            self.finished.emit({
                'type': 'summary',
                'content': '',
                'error': f'Error during summarization: {str(e)}'
            })
        finally:
            self.progress.emit(100)


class QAWorker(DocumentWorker):
    """Worker thread for document question answering."""
    
    def run(self):
        """Run the Q&A task."""
        try:
            self.progress.emit(10)
            question = self.kwargs.get('question', '')
            history = self.kwargs.get('history', [])
            
            if not question.strip():
                self.finished.emit({
                    'type': 'qa',
                    'content': '',
                    'error': 'No question provided',
                    'question': question
                })
                return
            
            # Prepare context from document content
            max_context_length = 16000  # ~4000 tokens
            context = self.content
            if len(context) > max_context_length:
                context = context[:max_context_length] + "\n\n[Document truncated for context]"
            
            self.progress.emit(30)
            
            # Prepare conversation history
            history_text = ""
            for h in history[-3:]:  # Keep last 3 exchanges for context
                history_text += f"Q: {h['question']}\nA: {h['answer']}\n\n"
            
            # Prepare the prompt
            prompt = (
                "You are a helpful assistant that answers questions about a document. "
                "Use the following document content to answer the question. "
                "If the answer cannot be found in the document, say so.\n\n"
                f"Document content:\n{context}\n\n"
                f"Previous conversation:\n{history_text}\n"
                f"Question: {question}\n"
                "Answer:"
            )
            
            self.progress.emit(60)
            
            # Generate answer
            response = self.model.generate(
                prompt,
                max_tokens=1000,
                temperature=0.3,  # Lower temperature for more focused answers
                stop=["\nQ:", "\n\nQ:"]  # Stop if model starts a new question
            )
            
            self.progress.emit(90)
            
            if response and response.strip():
                self.finished.emit({
                    'type': 'qa',
                    'content': response.strip(),
                    'error': '',
                    'question': question
                })
            else:
                self.finished.emit({
                    'type': 'qa',
                    'content': '',
                    'error': 'Failed to generate answer: Empty response from model',
                    'question': question
                })
                
        except Exception as e:
            self.finished.emit({
                'type': 'qa',
                'content': '',
                'error': f'Error during question answering: {str(e)}',
                'question': question if 'question' in locals() else ''
            })
        finally:
            self.progress.emit(100)


class DocumentPreviewWidget(QWidget):
    """Widget for previewing and analyzing document files."""
    
    # Signal emitted when document analysis is complete
    analysis_complete = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize the document preview widget."""
        super().__init__(parent)
        self.file_path = None
        self.analysis = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setMinimumSize(600, 500)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # File info bar
        self.file_info_label = QLabel("No document loaded")
        self.file_info_label.setStyleSheet("""
            QLabel {
                padding: 5px;
                background-color: #2a2a4a;
                border-radius: 3px;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(self.file_info_label)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Content tab
        self.content_tab = QWidget()
        self.content_layout = QVBoxLayout(self.content_tab)
        
        # Metadata tab
        self.metadata_tab = QWidget()
        self.metadata_layout = QVBoxLayout(self.metadata_tab)
        
        # Summarization tab
        self.summary_tab = QWidget()
        self.summary_layout = QVBoxLayout(self.summary_tab)
        
        # Add tabs to the tab widget
        self.tab_widget.addTab(self.content_tab, "Content")
        self.tab_widget.addTab(self.metadata_tab, "Metadata")
        self.tab_widget.addTab(self.summary_tab, "Summary")
        
        # Set up the content tab
        self.setup_content_tab()
        
        # Set up the metadata tab
        self.setup_metadata_tab()
        
        # Set up the summary tab
        self.setup_summary_tab()
        
        # Add tab widget to main layout
        layout.addWidget(self.tab_widget)
        
        # Initialize models and workers
        self.model = None
        self.worker = None
        self.qa_history = []  # Store Q&A history for context
        
        # Set up connections
        self.setup_connections()
    
    def setup_connections(self):
        """Set up signal connections."""
        # Connect document loaded signal
        if hasattr(self, 'document_loaded'):
            self.document_loaded.connect(self.on_document_loaded)
    
    def setup_content_tab(self):
        """Set up the content tab with appropriate viewer."""
        # Clear any existing widgets
        for i in reversed(range(self.content_layout.count())): 
            self.content_layout.itemAt(i).widget().setParent(None)
        
        # Add content viewer (text or table)
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_highlighter = DocumentHighlighter(self.content_text.document())
        
        # Add table for structured data
        self.content_table = QTableWidget()
        self.content_table.setAlternatingRowColors(True)
        self.content_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Add to layout
        self.content_layout.addWidget(self.content_text)
        self.content_layout.addWidget(self.content_table)
        
        # Initially hide the table
        self.content_table.hide()
    
    def setup_metadata_tab(self):
        """Set up the metadata tab."""
        # Clear any existing widgets
        for i in reversed(range(self.metadata_layout.count())): 
            self.metadata_layout.itemAt(i).widget().setParent(None)
        
        # Create metadata table
        self.metadata_table = QTableWidget()
        self.metadata_table.setColumnCount(2)
        self.metadata_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.metadata_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.metadata_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.metadata_table.verticalHeader().setVisible(False)
        self.metadata_table.setAlternatingRowColors(True)
        self.metadata_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.metadata_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Add to layout
        self.metadata_layout.addWidget(self.metadata_table)
    
    def setup_summary_tab(self):
        """Set up the summarization tab."""
        # Clear any existing widgets
        for i in reversed(range(self.summary_layout.count())): 
            self.summary_layout.itemAt(i).widget().setParent(None)
        
        # Summary type selection
        self.summary_type_layout = QHBoxLayout()
        self.summary_type_label = QLabel("Summary Type:")
        self.summary_type_combo = QComboBox()
        self.summary_type_combo.addItems(["Concise", "Detailed", "Key Points"])
        self.summary_type_combo.setCurrentIndex(0)
        self.summary_type_layout.addWidget(self.summary_type_label)
        self.summary_type_layout.addWidget(self.summary_type_combo)
        self.summary_type_layout.addStretch()
        
        # Generate button
        self.generate_btn = QPushButton("Generate Summary")
        self.generate_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self.generate_btn.clicked.connect(self.generate_summary)
        self.summary_type_layout.addWidget(self.generate_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Ready")
        self.progress_bar.hide()
        
        # Summary display
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setPlaceholderText("Click 'Generate Summary' to create a summary of the document.")
        
        # Add to layout
        self.summary_layout.addLayout(self.summary_type_layout)
        self.summary_layout.addWidget(self.progress_bar)
        self.summary_layout.addWidget(self.summary_text)
        self.tab_widget = QTabWidget()
        
        # Preview tab
        self.preview_tab = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_tab)
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_layout.addWidget(self.preview_text)
        self.tab_widget.addTab(self.preview_tab, "Preview")
        
        # Metadata tab
        self.metadata_tab = QWidget()
        self.metadata_layout = QVBoxLayout(self.metadata_tab)
        self.metadata_table = QTableWidget()
        self.metadata_table.setColumnCount(2)
        self.metadata_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.metadata_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.metadata_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.metadata_layout.addWidget(self.metadata_table)
        self.tab_widget.addTab(self.metadata_tab, "Metadata")
        
        # Content tab (for structured data like CSV/Excel)
        self.content_tab = QWidget()
        self.content_layout = QVBoxLayout(self.content_tab)
        self.content_table = QTableWidget()
        self.content_layout.addWidget(self.content_table)
        self.tab_widget.addTab(self.content_tab, "Content")
        
        # Add tabs to main layout
        layout.addWidget(self.tab_widget)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        self.summarize_btn = QPushButton("Summarize")
        self.summarize_btn.setToolTip("Generate a summary of the document")
        self.summarize_btn.clicked.connect(self.on_summarize)
        self.summarize_btn.setEnabled(False)
        
        self.qa_btn = QPushButton("Q&A")
        self.qa_btn.setToolTip("Ask questions about the document")
        self.qa_btn.clicked.connect(self.on_qa)
        self.qa_btn.setEnabled(False)
        
        btn_layout.addWidget(self.summarize_btn)
        btn_layout.addWidget(self.qa_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
    
    def load_file(self, file_path: str):
        """Load and analyze a document file."""
        self.file_path = file_path
        path = Path(file_path)
        
        if not path.exists():
            QMessageBox.warning(self, "File Not Found", f"File not found: {file_path}")
            return
        
        # Update file info
        self.file_info_label.setText(f"File: {path.name} ({path.suffix.upper()[1:] if path.suffix else 'Unknown'}, {self.format_file_size(path.stat().st_size)})")
        
        # Show loading state
        self.preview_text.setPlainText("Analyzing document...")
        
        # Analyze file in a separate thread
        from PyQt5.QtCore import QThread, pyqtSignal, QObject
        
        class FileAnalyzerWorker(QObject):
            finished = pyqtSignal(dict)
            
            def __init__(self, file_path):
                super().__init__()
                self.file_path = file_path
            
            def run(self):
                try:
                    analysis = FileAnalyzer.analyze_file(self.file_path)
                    self.finished.emit(analysis)
                except Exception as e:
                    self.finished.emit({"error": str(e)})
        
        self.worker = FileAnalyzerWorker(file_path)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.on_analysis_complete)
        self.thread.started.connect(self.worker.run)
        self.thread.start()
    
    def on_analysis_complete(self, analysis: Dict[str, Any]):
        """Handle completion of document analysis."""
        self.analysis = analysis
        
        # Update UI with analysis results
        if "error" in analysis:
            self.preview_text.setPlainText(f"Error analyzing document: {analysis['error']}")
            return
        
        # Update preview tab
        if "content" in analysis and analysis["content"] is not None:
            if isinstance(analysis["content"], str):
                self.preview_text.setPlainText(analysis["content"][:10000] + ("..." if len(analysis["content"]) > 10000 else ""))
            elif isinstance(analysis["content"], dict) and "data" in analysis["content"]:
                self.preview_text.setPlainText("Use the 'Content' tab to view structured data.")
        
        # Update metadata tab
        self.update_metadata_tab()
        
        # Update content tab for structured data
        if analysis.get("type") in ["csv", "excel"] and "content" in analysis and isinstance(analysis["content"], dict):
            self.update_content_tab(analysis["content"])
        
        # Enable action buttons
        self.summarize_btn.setEnabled(True)
        self.qa_btn.setEnabled(True)
        
        # Emit signal that analysis is complete
        self.analysis_complete.emit(analysis)
    
    def update_metadata_tab(self):
        """Update the metadata tab with file information."""
        if not self.analysis:
            return
        
        # Create metadata items
        metadata = []
        
        # Basic file info
        path = Path(self.file_path)
        metadata.extend([
            ("File Name", path.name),
            ("File Path", str(path.absolute())),
            ("File Size", self.format_file_size(path.stat().st_size)),
            ("File Type", self.analysis.get("type", "Unknown").upper()),
            ("Last Modified", self.format_timestamp(path.stat().st_mtime)),
        ])
        
        # Add analysis-specific metadata
        if "page_count" in self.analysis:
            metadata.append(("Pages", str(self.analysis["page_count"])))
        if "paragraph_count" in self.analysis:
            metadata.append(("Paragraphs", str(self.analysis["paragraph_count"])))
        if "word_count" in self.analysis:
            metadata.append(("Words", str(self.analysis["word_count"])))
        if "char_count" in self.analysis:
            metadata.append(("Characters", str(self.analysis["char_count"])))
        if "row_count" in self.analysis:
            metadata.append(("Rows", str(self.analysis["row_count"])))
        if "column_count" in self.analysis:
            metadata.append(("Columns", str(self.analysis["column_count"])))
        
        # Update table
        self.metadata_table.setRowCount(len(metadata))
        for i, (key, value) in enumerate(metadata):
            key_item = QTableWidgetItem(key)
            value_item = QTableWidgetItem(str(value))
            self.metadata_table.setItem(i, 0, key_item)
            self.metadata_table.setItem(i, 1, value_item)
    
    def update_content_tab(self, content: Dict[str, Any]):
        """Update the content tab with structured data."""
        if not content or not isinstance(content, dict):
            return
        
        if "data" in content and content["data"] and len(content["data"]) > 0:
            # For tabular data (CSV, Excel)
            headers = content.get("headers", [])
            data = content["data"]
            
            self.content_table.setColumnCount(len(headers) if headers else len(data[0]) if data else 0)
            self.content_table.setRowCount(len(data))
            
            # Set headers if available
            if headers:
                self.content_table.setHorizontalHeaderLabels(headers)
            
            # Populate table
            for i, row in enumerate(data):
                for j, cell in enumerate(row):
                    item = QTableWidgetItem(str(cell) if cell is not None else "")
                    self.content_table.setItem(i, j, item)
            
            # Resize columns to fit content
            self.content_table.resizeColumnsToContents()
    
    def set_model(self, model: BaseAIModel):
        """Set the AI model to use for summarization and Q&A."""
        self.model = model
        # Update UI to reflect model availability
        if hasattr(self, 'generate_btn'):
            self.generate_btn.setEnabled(model is not None)
        if hasattr(self, 'qa_input'):
            self.qa_input.setPlaceholderText("Ask a question about the document..." if model else "No AI model available")
            self.qa_input.setEnabled(model is not None)
            self.ask_btn.setEnabled(model is not None)
    
    def generate_summary(self):
        """Generate a summary of the current document."""
        if not self.model:
            QMessageBox.warning(self, "No Model", "No AI model available for summarization.")
            return
            
        if not self.analysis or not self.analysis.get('content'):
            QMessageBox.warning(self, "No Content", "No document content available to summarize.")
            return
        
        # Get document content
        content = self.analysis.get('content', '')
        if not content.strip():
            QMessageBox.warning(self, "Empty Content", "The document appears to be empty.")
            return
        
        # Get summary type
        summary_type = self.summary_type_combo.currentText().lower().replace(' ', '_')
        
        # Update UI
        self.generate_btn.setEnabled(False)
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Generating summary...")
        QApplication.processEvents()
        
        # Start summarization in a separate thread
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            
        self.worker = SummarizationWorker(
            model=self.model,
            content=content,
            summary_type=summary_type
        )
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.progress.connect(self.on_worker_progress)
        self.worker.start()
    
    def on_document_loaded(self):
        """Handle when a new document is loaded."""
        # Clear Q&A history when a new document is loaded
        self.qa_history = []
        if hasattr(self, 'qa_history_widget'):
            self.clear_qa_history()
    
    @pyqtSlot(int)
    def on_worker_progress(self, value: int):
        """Update progress bar during worker operations."""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(value)
    
    @pyqtSlot(dict)
    def on_worker_finished(self, result: dict):
        """Handle completion of worker tasks."""
        task_type = result.get('type', '')
        
        if task_type == 'summary':
            self.handle_summary_result(result)
        elif task_type == 'qa':
            self.handle_qa_result(result)
    
    def handle_summary_result(self, result: dict):
        """Handle completion of summarization."""
        if hasattr(self, 'generate_btn'):
            self.generate_btn.setEnabled(True)
        
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(100)
            
            if result.get('error'):
                self.progress_bar.setFormat("Error")
                QMessageBox.critical(self, "Summarization Error", 
                                   f"Failed to generate summary: {result['error']}")
            else:
                self.progress_bar.setFormat("Complete")
                if hasattr(self, 'summary_text'):
                    self.summary_text.setPlainText(result.get('content', ''))
            
            # Hide progress bar after a short delay
            QTimer.singleShot(2000, lambda: self.progress_bar.hide())
    
    def handle_qa_result(self, result: dict):
        """Handle completion of Q&A."""
        if hasattr(self, 'ask_btn'):
            self.ask_btn.setEnabled(True)
        
        if hasattr(self, 'qa_progress'):
            self.qa_progress.setValue(100)
            
            if result.get('error'):
                self.qa_progress.setFormat("Error")
                self.add_message_to_qa("assistant", f"Error: {result['error']}")
            else:
                self.qa_progress.setFormat("Complete")
                answer = result.get('content', 'No answer generated.')
                self.add_message_to_qa("assistant", answer)
                
                # Add to history
                self.qa_history.append({
                    'question': result.get('question', ''),
                    'answer': answer
                })
            
            # Hide progress bar after a short delay
            QTimer.singleShot(2000, lambda: self.qa_progress.hide())
    
    def setup_qa_tab(self):
        """Set up the Q&A tab."""
        # Clear any existing widgets
        if not hasattr(self, 'qa_tab'):
            self.qa_tab = QWidget()
            self.qa_layout = QVBoxLayout(self.qa_tab)
            
            # Add Q&A tab to the tab widget
            self.tab_widget.addTab(self.qa_tab, "Q&A")
        else:
            # Clear existing widgets
            for i in reversed(range(self.qa_layout.count())): 
                widget = self.qa_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
        
        # Create a scroll area for the chat history
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # Container for messages
        self.qa_history_widget = QWidget()
        self.qa_history_layout = QVBoxLayout(self.qa_history_widget)
        self.qa_history_layout.setSpacing(10)
        self.qa_history_layout.setContentsMargins(5, 5, 5, 5)
        self.qa_history_layout.addStretch()
        
        scroll.setWidget(self.qa_history_widget)
        
        # Input area
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        
        self.qa_input = QLineEdit()
        self.qa_input.setPlaceholderText("Ask a question about the document...")
        self.qa_input.returnPressed.connect(self.ask_question)
        
        self.ask_btn = QPushButton("Ask")
        self.ask_btn.clicked.connect(self.ask_question)
        
        input_layout.addWidget(self.qa_input)
        input_layout.addWidget(self.ask_btn)
        
        # Progress bar for Q&A
        self.qa_progress = QProgressBar()
        self.qa_progress.setRange(0, 100)
        self.qa_progress.setValue(0)
        self.qa_progress.setTextVisible(True)
        self.qa_progress.setFormat("Ready")
        self.qa_progress.hide()
        
        # Add widgets to layout
        self.qa_layout.addWidget(scroll)
        self.qa_layout.addWidget(self.qa_progress)
        self.qa_layout.addWidget(input_widget)
        
        # Restore history if any
        for qa in self.qa_history:
            self.add_message_to_qa("user", qa['question'])
            self.add_message_to_qa("assistant", qa['answer'])
    
    def ask_question(self):
        """Process a question about the document."""
        if not self.model:
            QMessageBox.warning(self, "No Model", "No AI model available for Q&A.")
            return
            
        if not self.analysis or not self.analysis.get('content'):
            QMessageBox.warning(self, "No Content", "No document content available for Q&A.")
            return
            
        question = self.qa_input.text().strip()
        if not question:
            return
            
        # Add question to chat
        self.add_message_to_qa("user", question)
        self.qa_input.clear()
        
        # Show progress
        self.ask_btn.setEnabled(False)
        self.qa_progress.show()
        self.qa_progress.setValue(0)
        self.qa_progress.setFormat("Thinking...")
        
        # Start Q&A in a separate thread
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            
        self.worker = QAWorker(
            model=self.model,
            content=self.analysis.get('content', ''),
            question=question,
            history=self.qa_history
        )
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.progress.connect(self.on_worker_progress)
        self.worker.start()
    
    def add_message_to_qa(self, role: str, content: str):
        """Add a message to the Q&A history."""
        if not hasattr(self, 'qa_history_layout'):
            return
            
        # Create message widget
        message = QTextEdit()
        message.setReadOnly(True)
        message.setFrameShape(QFrame.NoFrame)
        message.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        message.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        message.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Set style based on role
        if role == "user":
            message.setStyleSheet("""
                QTextEdit {
                    background-color: #2a2a4a;
                    border-radius: 10px;
                    padding: 8px;
                    color: white;
                }
            """)
            message.setAlignment(Qt.AlignRight)
        else:  # assistant
            message.setStyleSheet("""
                QTextEdit {
                    background-color: #1a1a2e;
                    border-radius: 10px;
                    padding: 8px;
                    color: #e0e0e0;
                }
            """)
            message.setAlignment(Qt.AlignLeft)
        
        # Set content
        message.setPlainText(content)
        
        # Calculate height
        doc = message.document()
        doc.setTextWidth(message.viewport().width())
        height = int(doc.size().height() + 10)
        message.setFixedHeight(min(height, 300))  # Limit max height
        
        # Add to layout
        self.qa_history_layout.insertWidget(self.qa_history_layout.count() - 1, message)
        
        # Scroll to bottom
        scroll = self.qa_history_widget.parent().parent()
        if isinstance(scroll, QScrollArea):
            scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
    
    def clear_qa_history(self):
        """Clear the Q&A history display."""
        if not hasattr(self, 'qa_history_layout'):
            return
            
        # Remove all widgets except the stretch
        while self.qa_history_layout.count() > 1:
            item = self.qa_history_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def on_qa(self):
        """Handle Q&A button click from menu/toolbar."""
        # Switch to Q&A tab if it exists
        if hasattr(self, 'qa_tab'):
            index = self.tab_widget.indexOf(self.qa_tab)
            if index >= 0:
                self.tab_widget.setCurrentIndex(index)
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in a human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    @staticmethod
    def format_timestamp(timestamp: float) -> str:
        """Format a timestamp in a human-readable format."""
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
