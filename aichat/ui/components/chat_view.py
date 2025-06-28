from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QPalette, QColor

class ChatView(QScrollArea):
    """A scrollable chat view that manages chat messages."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.NoFrame)
        
        # Create container widget
        self.container = QWidget()
        self.container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Main layout
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(8)
        self.layout.addStretch()  # Push messages to top
        
        self.setWidget(self.container)
        
        # Style
        self.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QWidget#container {
                background: transparent;
            }
        """)
    
    def add_message(self, message, is_user=False):
        """Add a new message to the chat."""
        from .chat_message import ChatMessage
        
        message_widget = ChatMessage(message, is_user=is_user)
        self.layout.insertWidget(self.layout.count() - 1, message_widget)
        
        # Scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)
        
        return message_widget
    
    def add_typing_indicator(self):
        """Add a typing indicator to the chat."""
        from .typing_indicator import TypingIndicator
        
        self.typing_indicator = TypingIndicator()
        self.layout.insertWidget(self.layout.count() - 1, self.typing_indicator)
        QTimer.singleShot(100, self.scroll_to_bottom)
        
        return self.typing_indicator
    
    def remove_typing_indicator(self):
        """Remove the typing indicator from the chat."""
        if hasattr(self, 'typing_indicator'):
            self.typing_indicator.deleteLater()
            del self.typing_indicator
    
    def clear_messages(self):
        """Clear all messages from the chat."""
        # Remove all widgets except the stretch at the end
        while self.layout.count() > 1:  # Keep the stretch item
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
    
    def scroll_to_bottom(self):
        """Scroll the chat to the bottom."""
        # Animate scroll to bottom
        scroll_bar = self.verticalScrollBar()
        if scroll_bar.maximum() > 0:
            animation = QPropertyAnimation(scroll_bar, b"value")
            animation.setDuration(200)
            animation.setStartValue(scroll_bar.value())
            animation.setEndValue(scroll_bar.maximum())
            animation.setEasingCurve(QEasingCurve.OutQuad)
            animation.start()
    
    def resizeEvent(self, event):
        """Handle resize events to update message sizes."""
        super().resizeEvent(event)
        # Update all message sizes when the view is resized
        for i in range(self.layout.count() - 1):  # Skip the stretch item
            item = self.layout.itemAt(i)
            if item and item.widget():
                item.widget().adjustSize()

class ChatContainer(QFrame):
    """A container widget for the chat view with a background."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("chatContainer")
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Chat view
        self.chat_view = ChatView()
        layout.addWidget(self.chat_view)
        
        # Style
        self.setStyleSheet("""
            ChatContainer {
                background: #1e1e2e;
                border-radius: 12px;
                border: 1px solid #2a2a4a;
            }
        """)
