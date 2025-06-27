"""
API key management dialog with validation and testing.
"""
from typing import Optional, Callable, Dict, Any

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QUrl
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QMessageBox, QSizePolicy,
    QSpacerItem, QFrame, QComboBox, QToolButton
)
import requests

from ..utils.api_key_manager import APIKeyManager, test_api_key

class APIKeyDialog(QDialog):
    """Dialog for managing API keys with validation and testing."""
    
    # Signal emitted when API key is successfully saved
    api_key_saved = pyqtSignal(str, str)  # service_name, api_key
    
    def __init__(
        self,
        service_name: str = "OpenRouter",
        parent=None,
        test_endpoint: Optional[str] = None,
        key_help_url: Optional[str] = None
    ):
        """Initialize the API key dialog.
        
        Args:
            service_name: Name of the service (e.g., "OpenRouter")
            parent: Parent widget
            test_endpoint: Optional endpoint to test the API key
            key_help_url: URL to documentation about getting an API key
        """
        super().__init__(parent)
        self.service_name = service_name.lower()
        self.test_endpoint = test_endpoint
        self.key_help_url = key_help_url or "https://openrouter.ai/keys"
        self.api_key_manager = APIKeyManager()
        self.setup_ui()
        self.load_existing_key()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(f"{self.service_name.capitalize()} API Key")
        self.setMinimumWidth(500)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Description
        description = QLabel(
            f"An API key is required to use {self.service_name.capitalize()} services. "
            "Your API key is stored securely on your device."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #a0a0c0;")
        layout.addWidget(description)
        
        # Form layout for API key input
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 10, 0, 10)
        form_layout.setSpacing(15)
        
        # Service selector (for future multi-service support)
        self.service_combo = QComboBox()
        self.service_combo.addItem(self.service_name.capitalize(), self.service_name)
        self.service_combo.setEnabled(False)  # For now, only one service
        
        # API key input
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("Paste your API key here...")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.textChanged.connect(self.on_api_key_changed)
        
        # Toggle password visibility
        self.toggle_visibility_btn = QToolButton()
        self.toggle_visibility_btn.setIcon(QIcon.fromTheme("eye-off"))
        self.toggle_visibility_btn.setCheckable(True)
        self.toggle_visibility_btn.toggled.connect(self.toggle_password_visibility)
        
        # Layout for API key input with toggle button
        key_layout = QHBoxLayout()
        key_layout.addWidget(self.api_key_edit)
        key_layout.addWidget(self.toggle_visibility_btn)
        
        form_layout.addRow("Service:", self.service_combo)
        form_layout.addRow("API Key:", key_layout)
        
        # Status indicator
        self.status_indicator = QLabel()
        self.status_indicator.setAlignment(Qt.AlignCenter)
        self.status_indicator.setMinimumHeight(24)
        
        # Test button
        self.test_btn = QPushButton("Test Key")
        self.test_btn.setEnabled(False)
        self.test_btn.clicked.connect(self.test_api_key)
        
        # Get API key button
        self.get_key_btn = QPushButton(f"Get {self.service_name.capitalize()} API Key")
        self.get_key_btn.clicked.connect(self.open_api_key_help)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.get_key_btn)
        button_layout.addWidget(self.test_btn)
        
        # Add to main layout
        layout.addLayout(form_layout)
        layout.addWidget(self.status_indicator)
        layout.addLayout(button_layout)
        
        # Dialog buttons
        button_box = QHBoxLayout()
        button_box.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.accept)
        
        button_box.addWidget(self.cancel_btn)
        button_box.addWidget(self.save_btn)
        
        layout.addLayout(button_box)
        self.setLayout(layout)
        
        # Apply styles
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
                color: #e0e0ff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #a0a0c0;
            }
            QLineEdit, QComboBox {
                background-color: #0a0a12;
                color: #e0e0ff;
                border: 1px solid #2a2a4a;
                border-radius: 4px;
                padding: 8px;
                min-height: 24px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #6e44ff;
            }
            QPushButton {
                background-color: #2a2a4a;
                color: #e0e0ff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3a3a5a;
            }
            QPushButton:disabled {
                background-color: #1a1a2e;
                color: #6a6a8a;
            }
            QPushButton#test_btn:enabled {
                background-color: #2a5a2a;
            }
            QPushButton#test_btn:enabled:hover {
                background-color: #3a6a3a;
            }
            QPushButton#save_btn:enabled {
                background-color: #2a4a6a;
                font-weight: bold;
            }
            QPushButton#save_btn:enabled:hover {
                background-color: #3a5a7a;
            }
        """)
        
        # Set object names for styling
        self.test_btn.setObjectName("test_btn")
        self.save_btn.setObjectName("save_btn")
    
    def toggle_password_visibility(self, checked: bool):
        """Toggle password visibility."""
        if checked:
            self.api_key_edit.setEchoMode(QLineEdit.Normal)
            self.toggle_visibility_btn.setIcon(QIcon.fromTheme("eye"))
        else:
            self.api_key_edit.setEchoMode(QLineEdit.Password)
            self.toggle_visibility_btn.setIcon(QIcon.fromTheme("eye-off"))
    
    def on_api_key_changed(self, text: str):
        """Handle API key text changes."""
        has_text = bool(text.strip())
        self.test_btn.setEnabled(has_text)
        self.save_btn.setEnabled(has_text)
    
    def load_existing_key(self):
        """Load existing API key if it exists."""
        existing_key = self.api_key_manager.get_api_key(self.service_name)
        if existing_key:
            self.api_key_edit.setText(existing_key)
            self.status_indicator.setText("Found existing API key")
            self.status_indicator.setStyleSheet("color: #4caf50;")
    
    def test_api_key(self):
        """Test the API key with the service."""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            self.show_status("Please enter an API key", "error")
            return
        
        self.set_ui_loading(True)
        
        # Use QTimer to prevent UI freeze
        QTimer.singleShot(100, lambda: self._perform_key_test(api_key))
    
    def _perform_key_test(self, api_key: str):
        """Perform the actual API key test in a non-blocking way."""
        try:
            is_valid = test_api_key(api_key, self.service_name)
            if is_valid:
                self.show_status("✓ API key is valid", "success")
                self.save_btn.setEnabled(True)
            else:
                self.show_status("✗ Invalid API key", "error")
                self.save_btn.setEnabled(False)
        except Exception as e:
            self.show_status(f"Error: {str(e)}", "error")
            self.save_btn.setEnabled(False)
        finally:
            self.set_ui_loading(False)
    
    def set_ui_loading(self, loading: bool):
        """Set UI loading state."""
        self.test_btn.setEnabled(not loading)
        self.save_btn.setEnabled(not loading and bool(self.api_key_edit.text().strip()))
        
        if loading:
            self.test_btn.setText("Testing...")
            self.status_indicator.setText("Testing API key...")
            self.status_indicator.setStyleSheet("color: #ffa500;")
        else:
            self.test_btn.setText("Test Key")
    
    def show_status(self, message: str, status_type: str = "info"):
        """Show a status message.
        
        Args:
            message: The message to show
            status_type: One of "info", "success", "error", "warning"
        """
        self.status_indicator.setText(message)
        
        colors = {
            "info": "#2196F3",
            "success": "#4CAF50",
            "error": "#F44336",
            "warning": "#FFC107"
        }
        
        self.status_indicator.setStyleSheet(f"color: {colors.get(status_type, '#a0a0c0')};")
    
    def open_api_key_help(self):
        """Open the API key help URL in the default browser."""
        from PyQt5.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl(self.key_help_url))
    
    def accept(self):
        """Handle dialog accept (Save button)."""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            self.show_status("Please enter an API key", "error")
            return
        
        # Save the API key
        if self.api_key_manager.save_api_key(self.service_name, api_key):
            self.api_key_saved.emit(self.service_name, api_key)
            super().accept()
        else:
            self.show_status("Failed to save API key", "error")
