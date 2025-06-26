"""
Feedback dialog for collecting user feedback on AI responses.
"""

from typing import Optional, Callable, Dict, Any
from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QComboBox, QWidget, QSizePolicy, QSpacerItem
)
from qtpy.QtCore import Qt, Signal, QSize
from qtpy.QtGui import QIcon, QPixmap

class FeedbackDialog(QDialog):
    """Dialog for collecting user feedback on AI responses."""
    
    feedback_submitted = Signal(dict)  # Signal emitted when feedback is submitted
    
    def __init__(
        self, 
        parent: Optional[QWidget] = None,
        user_message: str = "",
        ai_response: str = ""
    ) -> None:
        """Initialize the feedback dialog.
        
        Args:
            parent: Parent widget
            user_message: The user's message that was responded to
            ai_response: The AI's response being rated
        """
        super().__init__(parent)
        self.user_message = user_message
        self.ai_response = ai_response
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("Provide Feedback")
        self.setMinimumWidth(500)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Rating
        rating_layout = QHBoxLayout()
        rating_layout.addWidget(QLabel("Rating:"))
        
        self.rating_combo = QComboBox()
        self.rating_combo.addItems([
            "Select a rating...",
            "⭐☆☆☆☆ - Poor",
            "⭐⭐☆☆☆ - Fair",
            "⭐⭐⭐☆☆ - Good",
            "⭐⭐⭐⭐☆ - Very Good",
            "⭐⭐⭐⭐⭐ - Excellent"
        ])
        self.rating_combo.setCurrentIndex(0)
        rating_layout.addWidget(self.rating_combo, 1)
        
        # Tags
        self.tags_edit = QTextEdit()
        self.tags_edit.setPlaceholderText("Tags (comma-separated): helpful, inaccurate, etc.")
        self.tags_edit.setMaximumHeight(60)
        
        # Comments
        self.comments_edit = QTextEdit()
        self.comments_edit.setPlaceholderText("Additional comments...")
        self.comments_edit.setMinimumHeight(100)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.submit_btn = QPushButton("Submit Feedback")
        self.submit_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; border: none; "
            "padding: 8px 16px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        self.submit_btn.clicked.connect(self.submit_feedback)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.submit_btn)
        
        # Add widgets to layout
        layout.addLayout(rating_layout)
        layout.addWidget(QLabel("Tags:"))
        layout.addWidget(self.tags_edit)
        layout.addWidget(QLabel("Comments:"))
        layout.addWidget(self.comments_edit)
        layout.addLayout(button_layout)
        
        # Style
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: #e0e0e0;
                font-size: 12px;
            }
            QLabel {
                color: #bbbbbb;
            }
            QComboBox, QTextEdit {
                background-color: #3d3d3d;
                color: #e0e0e0;
                border: 1px solid #4d4d4d;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QPushButton {
                background-color: #4d4d4d;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5d5d5d;
            }
        """)
    
    def get_feedback_data(self) -> Dict[str, Any]:
        """Get the feedback data as a dictionary.
        
        Returns:
            Dictionary containing rating, tags, and comments
        """
        rating = max(0, self.rating_combo.currentIndex())  # 0 if no selection
        tags = [tag.strip() for tag in self.tags_edit.toPlainText().split(",") if tag.strip()]
        
        return {
            "rating": rating,
            "tags": tags,
            "comments": self.comments_edit.toPlainText().strip()
        }
    
    def submit_feedback(self) -> None:
        """Submit the feedback and close the dialog."""
        feedback = self.get_feedback_data()
        if feedback["rating"] == 0:  # No rating selected
            return
            
        self.feedback_submitted.emit(feedback)
        self.accept()


class FeedbackButton(QPushButton):
    """Button for providing feedback on AI responses."""
    
    feedback_requested = Signal(dict)  # Signal emitted when feedback is requested
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the feedback button."""
        super().__init__(parent)
        self.setIconSize(QSize(16, 16))
        self.setFixedSize(24, 24)
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        
        # Set icon (using emoji as fallback)
        try:
            self.setIcon(QIcon.fromTheme("emblem-favorite"))
        except:
            self.setText("⭐")  # Fallback
        
        self.setToolTip("Provide feedback on this response")
        self.setStyleSheet("""
            QPushButton {
                border: none;
                color: #666666;
                background: transparent;
            }
            QPushButton:hover {
                color: #FFD700;
            }
        """)
        
        self.clicked.connect(self.show_feedback_dialog)
    
    def show_feedback_dialog(self) -> None:
        """Show the feedback dialog."""
        dialog = FeedbackDialog(self.parent())
        if dialog.exec_() == QDialog.Accepted:
            self.feedback_requested.emit(dialog.get_feedback_data())
