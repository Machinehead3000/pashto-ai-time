"""
Modern main window for the Pashto AI application with enhanced UI components.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List, Any

from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer, QUrl, QSettings, QThread
from PyQt5.QtGui import QIcon, QKeySequence, QDesktopServices, QFontDatabase
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QStatusBar,
    QToolBar, QToolButton, QAction, QActionGroup, QMenu, QMenuBar, QLabel, QMessageBox, QFileDialog,
    QSizePolicy, QDockWidget, QTabWidget, QFrame, QApplication, QPushButton, QLineEdit,
    QInputDialog
)

from aichat.services.ai_service import AIService
from aichat.workers.ai_worker import AIWorker
from aichat.utils.settings import SettingsManager

from .components.chat_view import ChatContainer
from .components.input_area import InputArea
from .components.model_selector import ModelSelector
from .theme import ThemeManager

# Configure logging
logger = logging.getLogger(__name__)

class ModernMainWindow(QMainWindow):
    """Modern main window with enhanced UI components and AI integration."""
    
    # Signals
    api_key_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize the main window with AI integration."""
        super().__init__(parent)
        self.setWindowTitle("Pashto AI")
        self.setGeometry(100, 100, 1200, 900)
        
        # Initialize settings
        self.settings = SettingsManager()
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(QApplication.instance())
        
        # Initialize models and conversation
        self.models = {}
        self.current_model = self.settings.get("chat.model", "openai/gpt-3.5-turbo")
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Initialize AI worker and thread
        self.ai_worker = None
        self.ai_thread = None
        
        # Setup AI worker in a separate thread
        self.setup_ai_worker()
        
        # Initialize UI
        self.setup_ui()
        
        # Apply saved theme or default
        saved_theme = self.settings.get("app.theme", "dark")
        self.theme_manager.set_theme(saved_theme)
        
        # Load window state
        self.settings.restore_window_state(self)
        
        # Set status bar message
        self.statusBar().showMessage("Ready. Select a model and start chatting!")
        
        # Check for API key and load models if available
        if self.settings.get("api.api_key"):
            self.ai_worker.load_models()
        else:
            self.show_api_key_dialog()
    
    def setup_ai_worker(self):
        """Set up the AI worker in a separate thread."""
        # Create and start the worker thread
        self.ai_thread = QThread()
        self.ai_worker = AIWorker(api_key=self.settings.get("api.api_key"))
        self.ai_worker.moveToThread(self.ai_thread)
        
        # Connect signals
        self.ai_worker.response_chunk.connect(self.on_ai_response_chunk)
        self.ai_worker.response_complete.connect(self.on_ai_response_complete)
        self.ai_worker.error_occurred.connect(self.on_ai_error)
        self.ai_worker.models_loaded.connect(self.on_models_loaded)
        
        # Start the thread
        self.ai_thread.started.connect(self.ai_worker.start)
        self.ai_thread.finished.connect(self.ai_worker.deleteLater)
        self.ai_thread.start()
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save window state
        self.settings.save_window_state(self)
        
        # Stop AI worker
        if self.ai_worker:
            self.ai_worker.stop()
        if self.ai_thread and self.ai_thread.isRunning():
            self.ai_thread.quit()
            self.ai_thread.wait()
        
        # Accept the close event
        event.accept()
    
    # API Key Management
    def show_api_key_dialog(self, message: str = None):
        """Show dialog to enter API key."""
        api_key, ok = QInputDialog.getText(
            self,
            "API Key Required",
            message or "Please enter your OpenRouter API key:",
            QLineEdit.Password
        )
        
        if ok and api_key:
            self.set_api_key(api_key)
    
    def set_api_key(self, api_key: str):
        """Set the API key and save to settings."""
        self.settings.set("api.api_key", api_key)
        if self.ai_worker:
            self.ai_worker.set_api_key(api_key)
            self.ai_worker.load_models()
        self.statusBar().showMessage("API key updated. Loading models...")
    
    # Message Handling
    def on_send_message(self, message: str):
        """Handle sending a message to the AI with validation and feedback."""
        # Validate input
        message = message.strip()
        if not message:
            self.statusBar().showMessage("Message cannot be empty", 3000)
            return
            
        # Check message length
        max_length = 4000  # Reasonable limit to prevent abuse
        if len(message) > max_length:
            self.statusBar().showMessage(
                f"Message is too long. Maximum {max_length} characters allowed.", 
                5000
            )
            return
            
        # Check for API key
        if not self.settings.get("api.api_key"):
            self.show_api_key_dialog(
                "API key is required to send messages.\n\n"
                "Please enter your OpenRouter API key:"
            )
            return
            
        # Disable input while processing
        self.input_area.setEnabled(False)
        
        try:
            # Add user message to chat
            self.chat_container.add_message("user", message)
            self.conversation_history.append({"role": "user", "content": message})
            
            # Auto-scroll to the new message
            self.chat_container.scroll_to_bottom()
            
            # Show typing indicator
            self.chat_container.set_typing(True)
            self.statusBar().showMessage("Sending message...")
            
            # Prepare messages for API
            messages = self._prepare_messages()
            
            # Send to AI worker
            self.ai_worker.send_message(
                messages=messages,
                model=self.current_model,
                temperature=0.7,
                max_tokens=2000
            )
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}", exc_info=True)
            self.on_ai_error(f"Failed to send message: {str(e)}")
            self.input_area.setEnabled(True)
    
    def _prepare_messages(self) -> List[Dict[str, str]]:
        """Prepare messages for the API, ensuring we don't exceed the context window."""
        # Start with system message
        messages = [{"role": "system", "content": "You are a helpful AI assistant that responds in Pashto."}]
        
        # Add conversation history, most recent first until we hit the token limit
        max_history = 10  # Limit to last 10 messages to avoid excessive context
        for msg in self.conversation_history[-max_history:]:
            messages.append(msg)
            
        return messages
    
    # AI Worker Signal Handlers
    def on_ai_response_chunk(self, chunk: str):
        """Handle a chunk of the AI response."""
        if not hasattr(self, 'current_ai_message'):
            self.current_ai_message = ""
            self.chat_container.add_message("assistant", "")
        
        self.current_ai_message += chunk
        self.chat_container.update_last_message("assistant", self.current_ai_message)
    
    def on_ai_response_complete(self, full_response: str):
        """Handle completion of AI response with cleanup and user feedback."""
        try:
            # Update UI
            self.chat_container.set_typing(False)
            
            # Add to conversation history
            self.conversation_history.append({"role": "assistant", "content": full_response})
            
            # Auto-scroll to show the complete response
            self.chat_container.scroll_to_bottom()
            
            # Update status bar with token count
            token_count = len(full_response.split())  # Simple word count as token estimate
            self.statusBar().showMessage(
                f"Response received ({token_count} tokens)", 
                3000
            )
            
        except Exception as e:
            logger.error(f"Error processing AI response: {str(e)}", exc_info=True)
            self.statusBar().showMessage("Error processing response", 5000)
            
        finally:
            # Always re-enable input and clean up
            self.input_area.setEnabled(True)
            if hasattr(self, 'current_ai_message'):
                del self.current_ai_message
    
    def on_ai_error(self, error: str):
        """Handle errors from the AI worker with user-friendly messages."""
        self.chat_container.set_typing(False)
        
        # Remove any existing error messages
        if hasattr(self, 'current_ai_message'):
            del self.current_ai_message
        
        # Add error message to chat
        error_html = f"""
        <div style='color: #ef4444; background-color: #fef2f2; 
                   border-left: 4px solid #ef4444; padding: 0.75rem; 
                   margin: 0.5rem 0; border-radius: 0.25rem;'>
            <strong>Error:</strong> {error}
        </div>
        """
        self.chat_container.add_message("error", error_html, is_html=True)
        
        # Show error in status bar
        self.statusBar().showMessage(f"Error: {error}", 5000)
        
        # Handle specific error cases
        if any(code in error.lower() for code in ["401", "unauthorized"]):
            self.settings.set("api.api_key", "")
            self.show_api_key_dialog("Invalid API key. Please enter a valid OpenRouter API key:")
        elif "rate limit" in error.lower():
            self.statusBar().showMessage("Please wait before sending more messages.", 5000)
    
    def on_models_loaded(self, models: Dict[str, Dict[str, Any]]):
        """Handle loaded models from the AI worker."""
        self.models = models
        self.model_selector.update_models(models)
        
        # Select the first model if none selected
        if not self.current_model and models:
            self.current_model = next(iter(models.keys()))
            self.settings.set("chat.model", self.current_model)
        
        self.statusBar().showMessage(f"Loaded {len(models)} models. Ready to chat!")
    
    def setup_ui(self):
        """Set up the user interface."""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create toolbar
        self.setup_toolbar()
        
        # Create main content area
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Create left sidebar
        self.sidebar = self.create_sidebar()
        content_layout.addWidget(self.sidebar, stretch=1)
        
        # Create main chat area
        chat_area = self.create_chat_area()
        content_layout.addWidget(chat_area, stretch=4)
        
        # Add content to main layout
        main_layout.addWidget(content_widget, stretch=1)
        
        # Create status bar
        self.setup_status_bar()
        
        # Set window icon
        self.setWindowIcon(QIcon(":/icons/app_icon"))
        
        # Connect signals
        self.connect_signals()
    
    def connect_signals(self):
        """Connect UI signals to slots."""
        # Connect input area
        self.input_area.message_sent.connect(self.on_send_message)
        
        # Connect model selector
        self.model_selector.model_selected.connect(self.on_model_selected)
    
    def setup_toolbar(self):
        """Set up the application toolbar."""
        # Create toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # New chat action
        new_chat_action = QAction(QIcon(":/icons/new_chat"), "New Chat", self)
        new_chat_action.setShortcut(QKeySequence.New)
        new_chat_action.triggered.connect(self.new_chat)
        toolbar.addAction(new_chat_action)
        
        # Add separator
        toolbar.addSeparator()
        
        # Theme selector
        theme_menu = QMenu("Theme", self)
        
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        
        for theme_id, theme_data in self.theme_manager.THEMES.items():
            action = QAction(theme_data["name"], self, checkable=True)
            action.setData(theme_id)
            action.triggered.connect(lambda checked, t=theme_id: self.change_theme(t))
            theme_menu.addAction(action)
            theme_group.addAction(action)
            
            # Check current theme
            if theme_id == self.settings.get("app.theme", "dark"):
                action.setChecked(True)
        
        theme_action = toolbar.addAction(QIcon(":/icons/theme"), "Theme")
        theme_action.setMenu(theme_menu)
        toolbar.widgetForAction(theme_action).setPopupMode(QToolButton.InstantPopup)
        
        # Add spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)
        
        # Settings action
        settings_action = QAction(QIcon(":/icons/settings"), "Settings", self)
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)
    
    def create_sidebar(self) -> QWidget:
        """Create the sidebar widget."""
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(200)
        sidebar.setMaximumWidth(300)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Model selector
        model_label = QLabel("AI Model")
        model_label.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        
        self.model_selector = ModelSelector(self.models)
        self.model_selector.model_changed.connect(self.change_model)
        
        # Set initial model
        if self.current_model in self.models:
            self.model_selector.set_current_model(self.current_model)
        
        # Add widgets to layout
        layout.addWidget(model_label)
        layout.addWidget(self.model_selector)
    def create_chat_area(self) -> QWidget:
        """Create the main chat area with message list and input."""
        # Create main container
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create chat container for messages
        self.chat_container = ChatContainer()
        
        # Create input area
        self.input_area = InputArea()
        
        # Add widgets to layout
        layout.addWidget(self.chat_container, stretch=1)
        layout.addWidget(self.input_area)
        
        return container
    
    def setup_status_bar(self):
        """Set up the status bar."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Model info
        self.model_status = QLabel()
        self.update_model_status()
        status_bar.addPermanentWidget(self.model_status)
        
        # Connection status
        self.connection_status = QLabel("Disconnected")
        status_bar.addPermanentWidget(self.connection_status)
    
    def update_model_status(self):
        """Update the model status in the status bar."""
        if self.current_model in self.models:
            model = self.models[self.current_model]
            self.model_status.setText(f"{model['display']} ({model['provider']})")
    
    def change_theme(self, theme_name: str):
        """Change the application theme."""
        self.theme_manager.set_theme(theme_name)
        self.settings.setValue("theme", theme_name)
    
    def on_model_selected(self, model_id: str):
        """Handle model selection from the model selector."""
        if model_id in self.models:
            self.current_model = model_id
            self.settings.set("chat.model", model_id)
            self.update_model_status()
            
            # Update input area placeholder
            model = self.models[model_id]
            self.input_area.set_placeholder_text(f"Message {model.get('display', model_id)}...")
            
            self.statusBar().showMessage(f"Switched to {model.get('display', model_id)}", 3000)
    
    def on_new_chat(self):
        """Start a new chat session."""
        # Clear conversation history
        self.conversation_history = []
        self.chat_container.clear_messages()
        self.statusBar().showMessage("Started a new chat session", 3000)
        
        # Show typing indicator
        self.chat_view.chat_view.add_typing_indicator()
        
        # Simulate AI response (replace with actual API call)
        QTimer.singleShot(1000, lambda: self.simulate_ai_response(message))
    
    def simulate_ai_response(self, user_message: str):
        """Simulate an AI response (for testing)."""
        # Remove typing indicator
        self.chat_view.chat_view.remove_typing_indicator()
        
        # Add AI response
        response = f"This is a simulated response to: {user_message}"
        self.chat_view.chat_view.add_message(response, is_user=False)
    
    def new_chat(self):
        """Start a new chat."""
        # Clear chat view
        self.chat_view.chat_view.clear_messages()
        
        # Reset conversation history
        self.conversation_history = []
        
    def show_settings(self):
        """Show the settings dialog."""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QGroupBox, QLabel, QComboBox, QDialogButtonBox
        
        # Create a simple settings dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # API Key section
        api_key_group = QGroupBox("API Settings")
        api_layout = QVBoxLayout()
        
        api_key_btn = QPushButton("Update API Key")
        api_key_btn.clicked.connect(lambda: self.show_api_key_dialog())
        
        api_layout.addWidget(api_key_btn)
        api_key_group.setLayout(api_layout)
        
        # Theme section
        theme_group = QGroupBox("Appearance")
        theme_layout = QVBoxLayout()
        
        theme_label = QLabel("Theme:")
        theme_combo = QComboBox()
        theme_combo.addItems(["dark", "light", "system"])
        
        current_theme = self.settings.get("app.theme", "dark")
        theme_combo.setCurrentText(current_theme)
        theme_combo.currentTextChanged.connect(self.change_theme)
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(theme_combo)
        theme_group.setLayout(theme_layout)
        
        # Add sections to main layout
        layout.addWidget(api_key_group)
        layout.addWidget(theme_group)
        
        # Add close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec_()
        self.restoreState(self.settings.value("window_state"))
    
    def save_window_state(self):
        """Save the window state to settings."""
        # Save window geometry
        self.settings.setValue("window_geometry", self.saveGeometry())
        
        # Save window state
        self.settings.setValue("window_state", self.saveState())
    
    def restore_window_state(self):
        """Restore the window state from settings."""
        # Restore window geometry
        geometry = self.settings.value("window_geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Restore window state
        state = self.settings.value("window_state")
        if state:
            self.restoreState(state)
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save window state
        self.save_window_state()
        
        # Stop AI worker
        if self.ai_worker:
            self.ai_worker.stop()
        if self.ai_thread and self.ai_thread.isRunning():
            self.ai_thread.quit()
            self.ai_thread.wait()
        
        # Accept the close event
        event.accept()


def main():
    """Main entry point for the application."""
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create application
    app = QApplication(sys.argv)
    
    # Set application info
    app.setApplicationName("Pashto AI")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PashtoAI")
    app.setOrganizationDomain("pashto.ai")
    
    # Set style
    app.setStyle("Fusion")
    
    # Load fonts
    font_dir = Path(__file__).parent.parent / "resources" / "fonts"
    if font_dir.exists():
        for font_file in font_dir.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(font_file))
    
    # Set application font
    font = app.font()
    font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)
    
    # Create and show main window
    window = ModernMainWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
