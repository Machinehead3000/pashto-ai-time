"""
Dialog for managing saved conversations.
"""
from typing import Dict, List, Optional, Callable
from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QInputDialog, QMessageBox, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap

from ..utils.conversation import ConversationManager

class ConversationDialog(QDialog):
    """Dialog for managing saved conversations."""
    
    conversation_selected = pyqtSignal(str)  # Signal emitted when a conversation is selected
    
    def __init__(self, conversation_manager: ConversationManager, parent=None):
        """Initialize the conversation dialog.
        
        Args:
            conversation_manager: Instance of ConversationManager
            parent: Parent widget
        """
        super().__init__(parent)
        self.conversation_manager = conversation_manager
        self.selected_id = None
        
        self.setWindowTitle("CONVERSATION HISTORY")
        self.setMinimumSize(600, 500)
        self.setup_ui()
        self.load_conversations()
    
    def setup_ui(self):
        """Initialize the user interface."""
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("SAVED CONVERSATIONS")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #00f0ff;")
        layout.addWidget(title)
        
        # Conversation list
        self.conversation_list = QListWidget()
        self.conversation_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.conversation_list.setStyleSheet("""
            QListWidget {
                background: #0a0a12;
                border: 1px solid #00f0ff;
                border-radius: 5px;
                padding: 5px;
                color: #e0e0ff;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #1a1a2a;
            }
            QListWidget::item:selected {
                background: rgba(0, 240, 255, 0.2);
                border: 1px solid #00f0ff;
                border-radius: 3px;
            }
            QListWidget::item:hover {
                background: rgba(0, 240, 255, 0.1);
            }
        """)
        self.conversation_list.itemDoubleClicked.connect(self.on_conversation_double_clicked)
        layout.addWidget(self.conversation_list, 1)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Load button
        self.load_btn = QPushButton("LOAD")
        self.load_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                          stop:0 #ff00ff, stop:1 #00f0ff);
                color: #0a0a12;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 12px;
                min-width: 100px;
            }
            QPushButton:disabled {
                background: #333344;
                color: #666677;
            }
            QPushButton:hover:!disabled {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #ff69b4, stop:1 #00c8d7);
                box-shadow: 0 0 15px rgba(0, 240, 255, 0.5);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #cc00cc, stop:1 #008c99);
            }
        """)
        self.load_btn.setEnabled(False)
        self.load_btn.clicked.connect(self.on_load_clicked)
        
        # Delete button
        self.delete_btn = QPushButton("DELETE")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ff5555;
                border: 1px solid #ff5555;
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 12px;
            }
            QPushButton:disabled {
                color: #666677;
                border-color: #666677;
            }
            QPushButton:hover:!disabled {
                background: rgba(255, 85, 85, 0.1);
                color: #ff9999;
                border-color: #ff9999;
            }
            QPushButton:pressed {
                background: rgba(255, 85, 85, 0.2);
            }
        """)
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        
        # New button
        self.new_btn = QPushButton("NEW CHAT")
        self.new_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #00f0ff;
                border: 1px solid #00f0ff;
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(0, 240, 255, 0.1);
                border-color: #ff00ff;
                color: #ff00ff;
            }
            QPushButton:pressed {
                background: rgba(255, 0, 255, 0.2);
            }
        """)
        self.new_btn.clicked.connect(self.on_new_clicked)
        
        # Add buttons to layout
        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.new_btn)
        
        layout.addLayout(button_layout)
        
        # Connect selection changed signal
        self.conversation_list.itemSelectionChanged.connect(self.on_selection_changed)
        
        self.setLayout(layout)
    
    def load_conversations(self):
        """Load and display saved conversations."""
        self.conversation_list.clear()
        
        try:
            conversations = self.conversation_manager.list_conversations()
            
            if not conversations:
                item = QListWidgetItem("No saved conversations")
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
                item.setTextAlignment(Qt.AlignCenter)
                self.conversation_list.addItem(item)
                return
            
            for conv in conversations:
                try:
                    # Format date
                    updated = datetime.fromisoformat(conv['updated_at'])
                    date_str = updated.strftime('%b %d, %Y %H:%M')
                    
                    # Create item text
                    msg_count = conv.get('message_count', 0)
                    msg_text = f"{msg_count} message{'s' if msg_count != 1 else ''}"
                    
                    item_text = f"<b>{conv['title']}</b><br><span style='color: #9090a0;'>{date_str} • {msg_text}</span>"
                    
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, conv['id'])
                    item.setToolTip(f"Double-click to load this conversation")
                    self.conversation_list.addItem(item)
                except Exception as e:
                    print(f"Error loading conversation {conv.get('id')}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error listing conversations: {e}")
            item = QListWidgetItem("Error loading conversations")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            item.setTextAlignment(Qt.AlignCenter)
            self.conversation_list.addItem(item)
    
    def on_selection_changed(self):
        """Handle conversation selection change."""
        selected = self.conversation_list.selectedItems()
        has_selection = bool(selected)
        
        self.load_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        
        if has_selection:
            self.selected_id = selected[0].data(Qt.UserRole)
    
    def on_conversation_double_clicked(self, item):
        """Handle double-click on a conversation."""
        if item.flags() & Qt.ItemIsSelectable:
            self.accept()
            self.conversation_selected.emit(item.data(Qt.UserRole))
    
    def on_load_clicked(self):
        """Handle load button click."""
        selected = self.conversation_list.selectedItems()
        if selected:
            self.accept()
            self.conversation_selected.emit(selected[0].data(Qt.UserRole))
    
    def on_delete_clicked(self):
        """Handle delete button click."""
        selected = self.conversation_list.selectedItems()
        if not selected:
            return
            
        item = selected[0]
        conv_id = item.data(Qt.UserRole)
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 'Delete Conversation',
            f"Are you sure you want to delete '{item.text().split('<br>')[0].replace('<b>', '').replace('</b>', '')}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.conversation_manager.delete_conversation(conv_id):
                    self.load_conversations()
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to delete conversation: {str(e)}')
    
    def on_new_clicked(self):
        """Handle new chat button click."""
        self.accept()
        self.conversation_selected.emit(None)
