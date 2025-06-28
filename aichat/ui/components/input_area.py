from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, QPushButton,
    QToolButton, QMenu, QFileDialog, QLabel, QSizePolicy, QFrame
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QTextCursor, QTextCharFormat, QTextBlockFormat, QTextList
import os

class FormatButton(QToolButton):
    """A button for text formatting options."""
    
    def __init__(self, icon_name, tooltip, parent=None):
        super().__init__(parent)
        self.setIcon(QIcon.fromTheme(icon_name, QIcon(f":/icons/{icon_name}")))
        self.setToolTip(tooltip)
        self.setFixedSize(32, 32)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px;
            }
            QToolButton:hover {
                background: rgba(110, 68, 255, 0.2);
            }
            QToolButton:checked {
                background: rgba(110, 68, 255, 0.3);
            }
            QToolButton:pressed {
                background: rgba(110, 68, 255, 0.4);
            }
        """)

class InputArea(QFrame):
    """An enhanced text input area with formatting controls."""
    
    # Signals
    send_message = pyqtSignal(str)
    file_dropped = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("inputArea")
        self.setup_ui()
        self.setup_connections()
        self.setup_styles()
    
    def setup_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 12)
        main_layout.setSpacing(8)
        
        # Formatting toolbar
        self.toolbar = QWidget()
        self.toolbar_layout = QHBoxLayout(self.toolbar)
        self.toolbar_layout.setContentsMargins(4, 4, 4, 4)
        self.toolbar_layout.setSpacing(2)
        
        # Add formatting buttons
        self.bold_btn = FormatButton("format-text-bold", "Bold (Ctrl+B)")
        self.italic_btn = FormatButton("format-text-italic", "Italic (Ctrl+I)")
        self.code_btn = FormatButton("code-tags", "Code (Ctrl+`)")
        self.link_btn = FormatButton("link", "Insert Link (Ctrl+K)")
        self.attach_btn = FormatButton("paperclip", "Attach File")
        
        # Add buttons to toolbar
        self.toolbar_layout.addWidget(self.bold_btn)
        self.toolbar_layout.addWidget(self.italic_btn)
        self.toolbar_layout.addWidget(self.code_btn)
        self.toolbar_layout.addWidget(self.link_btn)
        self.toolbar_layout.addStretch()
        self.toolbar_layout.addWidget(self.attach_btn)
        
        # Text edit area
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Type a message...")
        self.text_edit.setAcceptRichText(False)
        self.text_edit.setMinimumHeight(80)
        self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # File attachment label
        self.attachment_label = QLabel()
        self.attachment_label.setVisible(False)
        self.attachment_label.setStyleSheet("""
            QLabel {
                color: #a0a0c0;
                font-size: 12px;
                padding: 4px 8px;
                background: rgba(74, 74, 106, 0.3);
                border-radius: 4px;
                margin-right: 8px;
            }
        """)
        
        # Bottom bar (attachment + send button)
        bottom_bar = QHBoxLayout()
        bottom_bar.addWidget(self.attachment_label)
        bottom_bar.addStretch()
        
        # Send button
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedWidth(100)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #6e44ff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5d3be0;
            }
            QPushButton:disabled {
                background-color: #4a3a7a;
                color: #6a6a8a;
            }
        """)
        
        bottom_bar.addWidget(self.send_btn)
        
        # Add widgets to main layout
        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(self.text_edit)
        main_layout.addLayout(bottom_bar)
        
        # Set focus to text edit
        self.text_edit.setFocus()
    
    def setup_connections(self):
        """Set up signal connections."""
        # Formatting buttons
        self.bold_btn.clicked.connect(self.toggle_bold)
        self.italic_btn.clicked.connect(self.toggle_italic)
        self.code_btn.clicked.connect(self.toggle_code)
        self.link_btn.clicked.connect(self.insert_link)
        self.attach_btn.clicked.connect(self.attach_file)
        
        # Send message on Ctrl+Enter or click send button
        self.text_edit.keyPressEvent = self.on_key_press
        self.send_btn.clicked.connect(self.send_text)
        
        # Enable/disable send button based on text content
        self.text_edit.textChanged.connect(self.update_send_button)
        self.update_send_button()
    
    def setup_styles(self):
        """Set up the widget styles."""
        self.setStyleSheet("""
            #inputArea {
                background: #1e1e2e;
                border: 1px solid #2a2a4a;
                border-radius: 12px;
                padding: 8px;
            }
            QTextEdit {
                background: transparent;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                padding: 12px;
                color: #f0f4ff;
                font-size: 14px;
                selection-background-color: #6e44ff;
                selection-color: white;
            }
            QTextEdit:focus {
                border: 1px solid #6e44ff;
            }
            QScrollBar:vertical {
                border: none;
                background: #1e1e2e;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #4a4a6a;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)
    
    def on_key_press(self, event):
        """Handle key press events."""
        # Send message on Ctrl+Enter
        if event.key() == Qt.Key_Return and event.modifiers() & Qt.ControlModifier:
            self.send_text()
            return
        
        # Formatting shortcuts
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_B:
                self.toggle_bold()
                return
            elif event.key() == Qt.Key_I:
                self.toggle_italic()
                return
            elif event.key() == Qt.Key_K:
                self.insert_link()
                return
            elif event.key() == Qt.Key_QuoteLeft:
                self.toggle_code()
                return
        
        # Default behavior
        QTextEdit.keyPressEvent(self.text_edit, event)
    
    def toggle_bold(self):
        """Toggle bold formatting for selected text."""
        fmt = QTextCharFormat()
        if self.text_edit.fontWeight() == QFont.Bold:
            fmt.setFontWeight(QFont.Normal)
        else:
            fmt.setFontWeight(QFont.Bold)
        
        self.merge_format_on_word_or_selection(fmt)
    
    def toggle_italic(self):
        """Toggle italic formatting for selected text."""
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.text_edit.fontItalic())
        self.merge_format_on_word_or_selection(fmt)
    
    def toggle_code(self):
        """Toggle code formatting for selected text."""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            # Get the selected text
            selected_text = cursor.selectedText()
            
            # Check if the text is already wrapped in backticks
            if selected_text.startswith('`') and selected_text.endswith('`'):
                # Remove backticks
                cursor.insertText(selected_text[1:-1])
            else:
                # Add backticks
                cursor.insertText(f'`{selected_text}`')
        else:
            # Insert empty backticks and position cursor between them
            cursor.insertText('``')
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 1)
            self.text_edit.setTextCursor(cursor)
    
    def insert_link(self):
        """Insert a link at the current cursor position."""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            # Get the selected text to use as link text
            link_text = cursor.selectedText()
            url, ok = QInputDialog.getText(self, "Insert Link", "URL:", text="https://")
            if ok and url:
                # Insert markdown link
                cursor.insertText(f"[{link_text}]({url})")
    
    def attach_file(self):
        """Open a file dialog to attach a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf);;Images (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            self.file_dropped.emit(file_path)
            
            # Show the file name in the attachment label
            file_name = os.path.basename(file_path)
            self.attachment_label.setText(f"📎 {file_name}")
            self.attachment_label.setVisible(True)
    
    def clear_attachment(self):
        """Clear the current attachment."""
        self.attachment_label.clear()
        self.attachment_label.setVisible(False)
    
    def merge_format_on_word_or_selection(self, format):
        """Apply the given format to the current word or selection."""
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(format)
        self.text_edit.mergeCurrentCharFormat(format)
    
    def send_text(self):
        """Emit the send_message signal with the current text."""
        text = self.text_edit.toPlainText().strip()
        if text:
            self.send_message.emit(text)
            self.text_edit.clear()
            self.clear_attachment()
    
    def update_send_button(self):
        """Enable/disable the send button based on text content."""
        has_text = bool(self.text_edit.toPlainText().strip())
        self.send_btn.setEnabled(has_text)
    
    def set_placeholder_text(self, text):
        """Set the placeholder text for the input field."""
        self.text_edit.setPlaceholderText(text)
    
    def clear(self):
        """Clear the input field and any attachments."""
        self.text_edit.clear()
        self.clear_attachment()
    
    def set_focus(self):
        """Set focus to the input field."""
        self.text_edit.setFocus()
