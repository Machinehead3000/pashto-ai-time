"""
Chat widget component for displaying and handling chat messages.
"""
from typing import Optional, Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QScrollArea, QSizePolicy, QSpacerItem, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor, QPixmap, QPainter, QLinearGradient

from aichat.learning.data_collector import DataCollector
from aichat.ui.feedback_dialog import FeedbackDialog, FeedbackButton
from aichat.ui.prompt_library_dialog import PromptLibraryDialog

class ChatMessage(QWidget):
    """A single chat message widget with avatar, bubble styling, and feedback."""
    
    feedback_submitted = pyqtSignal(dict)  # Signal emitted when feedback is submitted
    
    def __init__(self, text: str, is_user: bool, message_id: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.message_id = message_id or str(id(self))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # Message container
        message_container = QWidget()
        message_layout = QHBoxLayout()
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(10)
        
        # Avatar
        avatar = QLabel()
        avatar.setFixedSize(32, 32)
        avatar.setStyleSheet("""
            QLabel {
                border-radius: 16px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                          stop:0 #ff00ff, stop:1 #00f0ff);
                color: #0a0a12;
                font-weight: bold;
                text-align: center;
                line-height: 32px;
            }
        """)
        avatar.setText("AI" if not is_user else "U")
        
        # Message bubble
        bubble = QTextEdit()
        bubble.setReadOnly(True)
        bubble.setFrameShape(QFrame.NoFrame)
        bubble.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        bubble.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        bubble.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        bubble.setStyleSheet("""
            QTextEdit {
                background: transparent;
                color: #e0e0ff;
                border: none;
                padding: 10px 15px;
                border-radius: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
        
        # Set message text with proper formatting
        cursor = bubble.textCursor()
        format = QTextCharFormat()
        format.setTextOutline(QColor("#00f0ff" if not is_user else "#ff00ff"))
        cursor.insertText(text, format)
        
        # Adjust height
        doc = bubble.document()
        doc.setTextWidth(bubble.viewport().width())
        height = int(doc.size().height() + 20)  # Add some padding
        bubble.setFixedHeight(min(height, 300))  # Max height of 300px
        
        # Add to layout based on message type
        if is_user:
            message_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
            message_layout.addWidget(bubble, 1)
            message_layout.addWidget(avatar)
            bubble.setStyleSheet(bubble.styleSheet() + """
                QTextEdit {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                              stop:0 #6a00ff, stop:1 #00f0ff);
                    color: #0a0a12;
                    border-top-right-radius: 2px;
                }
            """)
        else:
            message_layout.addWidget(avatar)
            message_layout.addWidget(bubble, 1)
            bubble.setStyleSheet(bubble.styleSheet() + """
                QTextEdit {
                    background: rgba(26, 26, 46, 0.8);
                    border: 1px solid #00f0ff;
                    border-top-left-radius: 2px;
                    box-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
                }
            """)
        
        # Add message container to main layout
        message_container.setLayout(message_layout)
        layout.addWidget(message_container)
        
        # Add feedback button for AI messages
        if not is_user:
            self.feedback_btn = FeedbackButton()
            self.feedback_btn.setVisible(False)  # Hidden by default, shown on hover
            self.feedback_btn.feedback_requested.connect(self.on_feedback_requested)
            
            # Create a container for the feedback button
            feedback_container = QWidget()
            feedback_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            feedback_layout = QHBoxLayout(feedback_container)
            feedback_layout.setContentsMargins(42, 0, 0, 5)  # Align with message text
            feedback_layout.addWidget(self.feedback_btn)
            feedback_layout.addStretch()
            
            layout.addWidget(feedback_container)
            
            # Show/hide feedback button on hover
            message_container.enterEvent = lambda e: self.feedback_btn.setVisible(True)
            message_container.leaveEvent = lambda e: self.feedback_btn.setVisible(False)
        
        self.setLayout(layout)
    
    def on_feedback_requested(self, feedback_data: Dict[str, Any]) -> None:
        """Handle feedback submission for this message.
        
        Args:
            feedback_data: Dictionary containing rating, tags, and comments
        """
        feedback_data["message_id"] = self.message_id
        feedback_data["is_user_message"] = self.is_user
        self.feedback_submitted.emit(feedback_data)


class TypingIndicator(QWidget):
    """Animated typing indicator for the chat."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 20)
        self.dots = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(300)  # Update every 300ms
    
    def animate(self):
        self.dots = (self.dots + 1) % 4
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw dots
        dot_size = 6
        spacing = 8
        start_x = 5
        y = (self.height() - dot_size) / 2
        
        for i in range(3):
            if i < self.dots:
                gradient = QLinearGradient(0, 0, 0, dot_size)
                gradient.setColorAt(0, QColor("#00f0ff"))
                gradient.setColorAt(1, QColor("#008c99"))
                painter.setBrush(gradient)
            else:
                painter.setBrush(QColor(100, 100, 120))
            
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(start_x + i * spacing), int(y), dot_size, dot_size)


class ChatWidget(QWidget):
    """Main chat widget that handles message display and input with feedback."""
    
    send_message = pyqtSignal(str)  # Signal emitted when user sends a message
    
    def __init__(self, data_collector: Optional[DataCollector] = None, parent=None):
        """Initialize the chat widget.
        
        Args:
            data_collector: Optional DataCollector instance for storing feedback
            parent: Parent widget
        """
        super().__init__(parent)
        self.data_collector = data_collector
        self.message_history: List[Dict[str, Any]] = []
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 5, 15, 15)
        layout.setSpacing(10)
        
        # Chat history area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #0a0a12;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #00f0ff;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(5, 5, 5, 5)
        self.chat_layout.setSpacing(5)
        self.chat_layout.addStretch()
        
        self.scroll_area.setWidget(self.chat_container)
        
        # Typing indicator
        self.typing_indicator = TypingIndicator()
        self.typing_indicator.hide()
        
        # Message input
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.setMaximumHeight(100)
        self.message_input.setStyleSheet("""
            QTextEdit {
                background: rgba(26, 26, 46, 0.8);
                color: #e0e0ff;
                border: 1px solid #00f0ff;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                selection-background-color: #00f0ff;
                selection-color: #0a0a12;
            }
            QTextEdit:focus {
                border: 1px solid #ff00ff;
                box-shadow: 0 0 10px rgba(255, 0, 255, 0.3);
            }
        """)
        
        # Prompt Library button
        self.prompt_library_btn = QPushButton("Prompts")
        self.prompt_library_btn.setFixedSize(80, 40)
        self.prompt_library_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                          stop:0 #00f0ff, stop:1 #ff00ff);
                color: #0a0a12;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #00c8d7, stop:1 #ff69b4);
                box-shadow: 0 0 15px rgba(255, 0, 255, 0.5);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #008c99, stop:1 #cc00cc);
            }
        """)
        self.prompt_library_btn.clicked.connect(self.open_prompt_library)
        
        # Send button
        self.send_button = QPushButton("SEND")
        self.send_button.setFixedSize(100, 40)
        self.send_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                          stop:0 #ff00ff, stop:1 #00f0ff);
                color: #0a0a12;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #ff69b4, stop:1 #00c8d7);
                box-shadow: 0 0 15px rgba(0, 240, 255, 0.5);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #cc00cc, stop:1 #008c99);
            }
            QPushButton:disabled {
                background: #333344;
                color: #666677;
            }
        """)
        
        # Input layout
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.prompt_library_btn)
        input_layout.addWidget(self.send_button)
        
        # Add widgets to main layout
        layout.addWidget(self.scroll_area)
        layout.addWidget(self.typing_indicator, 0, Qt.AlignLeft)
        layout.addLayout(input_layout)
        
        # Set main layout
        self.setLayout(layout)
        
        # Connect signals
        self.send_button.clicked.connect(self.on_send_clicked)
        self.message_input.returnPressed.connect(self.on_send_clicked)
    
    def add_message(self, text: str, is_user: bool = False, message_id: Optional[str] = None) -> ChatMessage:
        """Add a message to the chat.
        
        Args:
            text: The message text
            is_user: Whether the message is from the user
            message_id: Optional message ID for tracking
            
        Returns:
            The created ChatMessage widget
        """
        message = ChatMessage(text, is_user, message_id, self)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, message)
        self.scroll_to_bottom()
        
        # Connect feedback signal if this is an AI message
        if not is_user and self.data_collector:
            message.feedback_submitted.connect(self.handle_feedback_submission)
        
        # Add to message history
        self.message_history.append({
            "id": message_id or str(id(message)),
            "text": text,
            "is_user": is_user,
            "timestamp": QDateTime.currentDateTime().toString(Qt.ISODate)
        })
        
        return message
    
    def show_typing(self, show: bool = True):
        """Show or hide the typing indicator."""
        self.typing_indicator.setVisible(show)
        self.scroll_to_bottom()
    
    def scroll_to_bottom(self):
        """Scroll the chat to the bottom."""
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
    
    def on_send_clicked(self):
        """Handle send button click."""
        text = self.message_input.toPlainText().strip()
        if text:
            self.send_message.emit(text)
            self.message_input.clear()
    
    def clear_chat(self):
        """Clear all messages from the chat."""
        # Clear the layout
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
        # Clear message history
        self.message_history.clear()
        
        # Start a new conversation in the data collector if available
        if self.data_collector:
            self.data_collector.start_new_conversation()
        
        # Add a welcome message
        self.add_message("Welcome to the chat! Type a message to begin.")
    
    def handle_feedback_submission(self, feedback_data: Dict[str, Any]) -> None:
        """Handle feedback submission for a message.
        
        Args:
            feedback_data: Dictionary containing feedback details
        """
        if not self.data_collector:
            return
            
        try:
            # Save the feedback
            message_id = feedback_data.pop("message_id")
            
            # Find the message in history
            message = next(
                (msg for msg in self.message_history if str(msg["id"]) == str(message_id)),
                None
            )
            
            if message:
                # Add message context to feedback
                feedback_data.update({
                    "message_text": message["text"],
                    "is_user_message": message["is_user"],
                    "timestamp": QDateTime.currentDateTime().toString(Qt.ISODate)
                })
                
                # Save conversation with feedback
                self.data_collector.save_conversation(
                    rating=feedback_data.get("rating"),
                    comments=feedback_data.get("comments", ""),
                    **{"tags": feedback_data.get("tags", [])}
                )
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Feedback Submitted",
                    "Thank you for your feedback! It will help improve the AI's responses.",
                    QMessageBox.Ok
                )
            
        except Exception as e:
            logger.error(f"Error saving feedback: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save feedback: {str(e)}",
                QMessageBox.Ok
            )
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
            self.on_send_clicked()
            return
        super().keyPressEvent(event)

    def open_prompt_library(self):
        dialog = PromptLibraryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            prompt_text = dialog.get_selected_prompt_text()
            if prompt_text:
                self.message_input.setPlainText(prompt_text)
