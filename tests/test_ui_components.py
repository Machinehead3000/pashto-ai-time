"""
Tests for UI components and their integration with localization.
"""
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import Qt

# Import the application modules
from aichat.localization import i18n, tr
from aichat.ui.chat_widget import ChatWidget, ChatMessage
from aichat.learning.data_collector import DataCollector

# Create a QApplication instance for testing
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

def test_chat_message_creation():
    """Test creation of chat messages with different parameters."""
    # Test user message
    user_msg = ChatMessage("Hello, world!", is_user=True)
    assert user_msg.is_user is True
    assert "Hello, world!" in user_msg.findChild(QTextEdit).toPlainText()
    
    # Test AI message
    ai_msg = ChatMessage("Hello, how can I help you?", is_user=False)
    assert ai_msg.is_user is False
    assert "how can I help you?" in ai_msg.findChild(QTextEdit).toPlainText()
    
    # Test with message ID
    msg_with_id = ChatMessage("Test", is_user=True, message_id="test123")
    assert msg_with_id.message_id == "test123"

def test_chat_widget_basic():
    """Test basic functionality of the ChatWidget."""
    data_collector = DataCollector()
    widget = ChatWidget(data_collector)
    
    # Test adding messages
    widget.add_message("User message", is_user=True)
    widget.add_message("AI response", is_user=False)
    
    # Check that messages were added
    assert widget.message_history[0]["is_user"] is True
    assert widget.message_history[1]["is_user"] is False
    
    # Test clearing the chat
    widget.clear_chat()
    assert len(widget.message_history) == 0

def test_chat_widget_localization():
    """Test that the ChatWidget uses localized strings."""
    data_collector = DataCollector()
    widget = ChatWidget(data_collector)
    
    # Check that the send button has a localized tooltip
    send_button = widget.findChild(QPushButton)
    assert send_button is not None
    assert send_button.toolTip() == tr("send_message_tooltip")

def test_typing_indicator():
    """Test the typing indicator functionality."""
    data_collector = DataCollector()
    widget = ChatWidget(data_collector)
    
    # Show typing indicator
    widget.show_typing(True)
    
    # Check that typing indicator is visible
    typing_indicator = widget.findChild(QLabel, "typingIndicator")
    assert typing_indicator is not None
    assert typing_indicator.isVisible()
    
    # Hide typing indicator
    widget.show_typing(False)
    assert not typing_indicator.isVisible()

def test_feedback_submission():
    """Test feedback submission from chat messages."""
    data_collector = DataCollector()
    widget = ChatWidget(data_collector)
    
    # Add a message
    msg_widget = widget.add_message("Test message", is_user=False)
    
    # Simulate feedback submission
    feedback_data = {
        "message_id": msg_widget.message_id,
        "rating": 5,
        "comment": "Great response!"
    }
    
    # Connect to the feedback signal
    feedback_received = []
    def on_feedback(data):
        feedback_received.append(data)
    
    widget.feedback_submitted.connect(on_feedback)
    
    # Emit the signal
    msg_widget.feedback_submitted.emit(feedback_data)
    
    # Check that feedback was received
    assert len(feedback_received) == 1
    assert feedback_received[0]["message_id"] == msg_widget.message_id
    assert feedback_received[0]["rating"] == 5

if __name__ == "__main__":
    pytest.main(["-v", "test_ui_components.py"])
