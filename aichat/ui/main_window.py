"""
Main application window for the AI Chat application.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from PyQt5.QtCore import (
    QFile, QSize, Qt, QTextStream, QThread, QTimer, QUrl, pyqtSignal, pyqtSlot
)
from PyQt5.QtGui import (
    QColor, QDesktopServices, QFont, QFontDatabase, QIcon, QKeySequence, QPalette,
    QTextCharFormat, QTextCursor
)
from PyQt5.QtWidgets import (
    QAction, QApplication, QComboBox, QDockWidget, QFileDialog, QHBoxLayout,
    QLabel, QMainWindow, QMenu, QMenuBar, QMessageBox, QPushButton, QSizePolicy,
    QSplitter, QStatusBar, QStyle, QStyleFactory, QTabWidget, QToolBar, QVBoxLayout,
    QWidget
)

from ..learning.data_collector import DataCollector
from ..localization import i18n, tr
from ..models import DeepSeekModel, MistralModel
from ..models.base import BaseModel
from .chat_widget import ChatWidget
from .code_execution_widget import CodeExecutionWidget
from .conversation_dialog import ConversationDialog
from .cyberpunk_theme import apply_cyberpunk_theme
from .file_upload_widget import FileUploadWidget
from .settings_dialog import SettingsDialog

# Configure logging
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, parent=None):
        """Initialize the main window."""
        super().__init__(parent)
        self.setWindowTitle("Pashto AI")
        self.setGeometry(100, 100, 1200, 900)
        
        # Initialize data collector
        self.data_dir = os.path.join(str(Path.home()), ".pashto_ai", "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.data_collector = DataCollector(data_dir=self.data_dir)
        
        # Initialize models with data collector
        self.models = {
            "DeepSeek-R1": DeepSeekModel(data_collector=self.data_collector),
            "Mistral-7B": MistralModel(data_collector=self.data_collector),
        }
        self.current_model = "DeepSeek-R1"
        
        # Initialize file upload widget
        self.file_upload_widget = None
        self.code_execution_widget = None
        
        # Initialize UI
        self.init_ui()
        
        # Apply cyberpunk theme
        apply_cyberpunk_theme(QApplication.instance())
        
        # Start a new conversation
        self.data_collector.start_new_conversation()
        
        # Load settings
        self.load_settings()
        
        self.statusBar().showMessage("Ready. Select a model and start chatting!")
    
    def init_ui(self):
        """Initialize the user interface."""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # Left panel - Chat
        self.chat_widget = ChatWidget(data_collector=self.data_collector)
        self.splitter.addWidget(self.chat_widget)
        
        # Right panel - Tools (initially hidden)
        self.tools_dock = QDockWidget("Tools", self)
        self.tools_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.tools_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tools_dock.setWidget(self.tabs)
        self.addDockWidget(Qt.RightDockWidgetArea, self.tools_dock)
        self.tools_dock.hide()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Connect signals
        self.chat_widget.send_message.connect(self.on_send_message)
        
        # Set initial sizes
        self.splitter.setSizes([self.width() * 0.7, self.width() * 0.3])
    
    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_chat_action = QAction("New Chat", self)
        new_chat_action.setShortcut("Ctrl+N")
        new_chat_action.triggered.connect(self.new_chat)
        file_menu.addAction(new_chat_action)
        
        save_chat_action = QAction("Save Chat", self)
        save_chat_action.setShortcut("Ctrl+S")
        save_chat_action.triggered.connect(self.save_chat)
        file_menu.addAction(save_chat_action)
        
        load_chat_action = QAction("Load Chat", self)
        load_chat_action.setShortcut("Ctrl+O")
        load_chat_action.triggered.connect(self.load_chat)
        file_menu.addAction(load_chat_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        edit_menu.addAction(settings_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        toggle_tools_action = QAction("Toggle Tools Panel", self)
        toggle_tools_action.setShortcut("F4")
        toggle_tools_action.triggered.connect(self.toggle_tools_panel)
        view_menu.addAction(toggle_tools_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        file_upload_action = QAction("File Upload", self)
        file_upload_action.triggered.connect(self.show_file_upload)
        tools_menu.addAction(file_upload_action)
        
        code_editor_action = QAction("Code Editor", self)
        code_editor_action.triggered.connect(self.show_code_editor)
        tools_menu.addAction(code_editor_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        docs_action = QAction("Documentation", self)
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)
    
    def create_toolbar(self):
        """Create the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # Model selection
        self.model_combo = QComboBox()
        self.model_combo.addItems(self.models.keys())
        self.model_combo.setCurrentText(self.current_model)
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        toolbar.addWidget(QLabel("Model: "))
        toolbar.addWidget(self.model_combo)
        
        toolbar.addSeparator()
        
        # File actions
        new_chat_action = QAction(self.style().standardIcon(getattr(self.style(), 'SP_FileIcon')), "New Chat", self)
        new_chat_action.triggered.connect(self.new_chat)
        toolbar.addAction(new_chat_action)
        
        save_chat_action = QAction(self.style().standardIcon(getattr(self.style(), 'SP_DialogSaveButton')), "Save Chat", self)
        save_chat_action.triggered.connect(self.save_chat)
        toolbar.addAction(save_chat_action)
        
        load_chat_action = QAction(self.style().standardIcon(getattr(self.style(), 'SP_DialogOpenButton')), "Load Chat", self)
        load_chat_action.triggered.connect(self.load_chat)
        toolbar.addAction(load_chat_action)
        
        toolbar.addSeparator()
        
        # Tool actions
        file_upload_action = QAction(self.style().standardIcon(getattr(self.style(), 'SP_FileDialogContentsView')), "Upload Files", self)
        file_upload_action.triggered.connect(self.show_file_upload)
        toolbar.addAction(file_upload_action)
        
        code_editor_action = QAction(self.style().standardIcon(getattr(self.style(), 'SP_FileDialogDetailedView')), "Code Editor", self)
        code_editor_action.triggered.connect(self.show_code_editor)
        toolbar.addAction(code_editor_action)
        
        settings_action = QAction(self.style().standardIcon(getattr(self.style(), 'SP_ComputerIcon')), "Settings", self)
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)
        
        # Add stretch to push the rest to the left
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)
        
        # Theme toggle
        self.theme_action = QAction(self.style().standardIcon(getattr(self.style(), 'SP_DesktopIcon')), "Toggle Theme", self)
        self.theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(self.theme_action)
    
    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        new_chat = file_menu.addAction('New Chat')
        new_chat.setShortcut('Ctrl+N')
        new_chat.triggered.connect(self.chat_widget.clear_chat)
        
        save_chat = file_menu.addAction('Save Chat')
        save_chat.setShortcut('Ctrl+S')
        save_chat.triggered.connect(self.save_chat)
        
        load_chat = file_menu.addAction('Load Chat')
        load_chat.setShortcut('Ctrl+O')
        load_chat.triggered.connect(self.load_chat)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction('Exit')
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = menubar.addMenu('&Edit')
        
        copy_action = edit_menu.addAction('Copy')
        copy_action.setShortcut('Ctrl+C')
        copy_action.triggered.connect(self.chat_widget.copy_selected_text)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = help_menu.addAction('About')
        about_action.triggered.connect(self.show_about)
        
        help_action = help_menu.addAction('Help')
        help_action.triggered.connect(self.show_help)
    
    def set_dark_theme(self):
        """Legacy method kept for compatibility. Theme is now set via apply_cyberpunk_theme."""
        pass
    
    def on_model_changed(self, model_name):
        """Handle model change."""
        self.current_model = model_name
        
        # Update data collector reference if model supports it
        model = self.models[model_name]
        if hasattr(model, 'set_data_collector'):
            model.set_data_collector(self.data_collector)
            
        self.statusBar().showMessage(f"Switched to {model_name}", 3000)
    
    def send_message(self, message: str):
        """
        Send a message to the current model with enhanced error handling and user feedback.
            
        Args:
            message: The message text to send
        """
        if not message or not message.strip():
            self.statusBar().showMessage("Cannot send empty message", 3000)
            return
            
        # Define callbacks first to avoid indentation issues
        def on_token_received(token: str):
            try:
                self.chat_widget.append_to_last_message(token)
                QApplication.processEvents()
                return True
            except Exception as e:
                logger.error(f"Error processing token: {str(e)}")
                return False  # Stop streaming on error
        
        def on_response_complete(response: str):
            try:
                self.chat_widget.show_typing_indicator(False)
                self.chat_widget.scroll_to_bottom()
                self.statusBar().showMessage("Response generated", 3000)
            except Exception as e:
                logger.error(f"Error completing response: {str(e)}")
        
        def on_error(error: str, details: str = None):
            try:
                self.chat_widget.show_typing_indicator(False)
                error_msg = f"I encountered an error: {error}"
                if details:
                    error_msg += f"\n\nTechnical details: {details}"
                
                # Add error message to chat
                self.chat_widget.add_message("assistant", error_msg, is_error=True)
                
                # Show error in status bar
                self.statusBar().showMessage(f"Error: {error}", 5000)
                
                # Log the error
                logger.error(f"Error in send_message: {error}")
            except Exception as e:
                logger.critical(f"Critical error in error handler: {str(e)}")
        
        def call_model():
            try:
                response = model.generate_response(
                    message=message,
                    history=history,
                    on_token=on_token_received if hasattr(model, 'supports_streaming') and model.supports_streaming else None
                )
                on_response_complete(response)
            except Exception as e:
                on_error(str(e), str(e.__class__.__name__))
        
        try:
            # Add user message to chat
            self.chat_widget.add_message("user", message)
            
            # Get the selected model with validation
            model = self.models.get(self.current_model)
            if not model:
                raise ValueError("No AI model is currently selected")
            
            if not hasattr(model, 'generate_response'):
                raise AttributeError("Selected model does not support text generation")
            
            # Show typing indicator and update status
            self.chat_widget.show_typing_indicator(True)
            self.statusBar().showMessage("Generating response...")
            
            # Prepare the conversation history
            history = self.chat_widget.get_conversation_history()
            
            # Import threading here to avoid circular imports
            import threading
            
            # Start the model thread
            model_thread = threading.Thread(target=call_model)
            model_thread.daemon = True
            model_thread.start()
            
        except Exception as e:
            # Handle any other unexpected errors
            error_msg = f"An unexpected error occurred: {str(e)}"
            self.chat_widget.add_message("system", error_msg, is_error=True)
            self.statusBar().showMessage(f"Error: {str(e)}", 5000)
            logger.error(f"Unexpected error in send_message: {str(e)}", exc_info=True)
            
            # Re-enable UI elements
            self.send_button.setEnabled(True)
            self.message_input.setEnabled(True)
            self.message_input.setFocus()
            
            # Ensure typing indicator is hidden
            self.chat_widget.show_typing_indicator(False)
            error_msg = str(e) or "An unknown error occurred"
            error_type = type(e).__name__
            self.chat_widget.add_message(
                "system",
                f"Error generating response: {error_msg}",
                is_error=True
            )
            logger.error(f"Error in send_message: {error_type}: {error_msg}", exc_info=True)
            
            # Re-enable UI elements
            self.send_button.setEnabled(True)
            self.message_input.setEnabled(True)
            self.message_input.setFocus()
    
    def show_settings(self):
        """Show the settings dialog."""
        dialog = SettingsDialog(self.models[self.current_model], self)
        if dialog.exec_():
            # Apply settings
            pass
    
    def save_chat(self):
        """Save the current chat to a file."""
        # TODO: Implement chat saving
        QMessageBox.information(self, "Info", "Save chat functionality coming soon!")
    
    def load_chat(self):
        """Load a chat from a file."""
        # TODO: Implement chat loading
        QMessageBox.information(self, "Info", "Load chat functionality coming soon!")
    
    def show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About AI Chat Pro",
            "<h2>AI Chat Pro</h2>"
            "<p>Version 0.1.0</p>"
            "<p>A desktop application for chatting with various AI models.</p>"
            "<p>© 2025 Your Name</p>"
        )
    
    def show_help(self):
        """Show the help dialog."""
        QMessageBox.information(
            self,
            "Help",
            "<h2>AI Chat Pro Help</h2>"
            "<p><b>To start chatting:</b> Type your message in the input box and press Enter or click Send.</p>"
            "<p><b>To switch models:</b> Use the dropdown menu to select a different AI model.</p>"
            "<p><b>Keyboard Shortcuts:</b></p>"
            "<ul>"
            "<li>Ctrl+N: New Chat</li>"
            "<li>Ctrl+O: Open Chat</li>"
            "<li>Ctrl+S: Save Chat</li>"
            "<li>Ctrl+Q: Quit</li>"
            "<li>Ctrl+C: Copy selected text</li>"
            "</ul>"
        )

    def show_file_upload(self):
        """Show the file upload widget in the tools panel."""
        if not self.file_upload_widget:
            self.file_upload_widget = FileUploadWidget()
            self.file_upload_widget.files_processed.connect(self.on_files_processed)
        
        self.show_tool("File Upload", self.file_upload_widget)
    
    def show_code_editor(self):
        """Show the code editor in the tools panel."""
        if not self.code_execution_widget:
            self.code_execution_widget = CodeExecutionWidget()
            self.code_execution_widget.execution_finished.connect(self.on_code_execution_finished)
        
        self.show_tool("Code Editor", self.code_execution_widget)
    
    def show_tool(self, name: str, widget: QWidget):
        """Show a tool in the tools panel."""
        # Check if tool is already open
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == name:
                self.tabs.setCurrentIndex(i)
                self.tools_dock.show()
                return
        
        # Add new tab
        index = self.tabs.addTab(widget, name)
        self.tabs.setCurrentIndex(index)
        self.tools_dock.show()
    
    def close_tab(self, index: int):
        """Close a tab in the tools panel."""
        widget = self.tabs.widget(index)
        self.tabs.removeTab(index)
        
        # If this was the last tab, hide the dock
        if self.tabs.count() == 0:
            self.tools_dock.hide()
    
    def toggle_tools_panel(self):
        """Toggle the visibility of the tools panel."""
        self.tools_dock.setVisible(not self.tools_dock.isVisible())
    
    def on_files_processed(self, results: Dict[str, Any]):
        """Handle processed files."""
        for file_path, file_info in results.items():
            if file_info.get('error'):
                QMessageBox.warning(self, "File Error", 
                                  f"Error processing {file_info['name']}: {file_info['error']}")
            else:
                # Add file info to chat
                self.chat_widget.add_message(
                    f"Uploaded file: {file_info['name']} ({file_info['size']} bytes)",
                    is_user=True
                )
    
    def on_code_execution_finished(self, result: Dict[str, Any]):
        """Handle code execution finished."""
        if not result.get('success'):
            QMessageBox.warning(self, "Code Execution Error", 
                              f"Error executing code: {result.get('error', 'Unknown error')}")
    
    def on_send_message(self, message: str):
        """Handle sending a message."""
        # Get the current model
        model = self.models.get(self.current_model)
        if not model:
            QMessageBox.warning(self, "Error", "No model selected")
            return
        
        # Add user message to chat
        self.chat_widget.add_message(message, is_user=True)
        
        # Get response from model
        try:
            response = model.generate_response(message)
            self.chat_widget.add_message(response, is_user=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate response: {str(e)}")
    
    def on_model_changed(self, model_name: str):
        """Handle model change."""
        if model_name in self.models:
            self.current_model = model_name
            self.statusBar().showMessage(f"Switched to {model_name}", 3000)
    
    def new_chat(self):
        """Start a new chat."""
        if self.chat_widget.maybe_save():
            self.chat_widget.clear_chat()
            self.data_collector.start_new_conversation()
    
    def save_chat(self):
        """Save the current chat."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Chat", "", "Chat Files (*.json);;All Files (*)")
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.chat_widget.get_chat_history(), f, indent=2)
                self.statusBar().showMessage(f"Chat saved to {file_path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save chat: {str(e)}")
    
    def load_chat(self):
        """Load a chat from file."""
        if not self.chat_widget.maybe_save():
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Chat", "", "Chat Files (*.json);;All Files (*)")
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    chat_data = json.load(f)
                
                self.chat_widget.clear_chat()
                self.chat_widget.load_chat_history(chat_data)
                self.statusBar().showMessage(f"Chat loaded from {file_path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load chat: {str(e)}")
    
    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        if dialog.exec_():
            # Apply settings
            pass
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About Pashto AI",
                         "<h2>Pashto AI</h2>"
                         "<p>Version 1.0.0</p>"
                         "<p>An AI-powered chat application with code execution and file analysis capabilities.</p>"
                         "<p>© 2023 Pashto AI Team</p>")
    
    def show_documentation(self):
        """Open documentation in default browser."""
        QDesktopServices.openUrl(QUrl("https://github.com/yourusername/pashto-ai"))
    
    def toggle_theme(self):
        """Toggle between light and dark theme."""
        # This would be implemented to toggle the theme
        pass
    
    def load_settings(self):
        """Load application settings."""
        settings_path = os.path.join(str(Path.home()), ".pashto_ai", "settings.json")
        
        try:
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                
                # Apply settings
                if 'geometry' in settings:
                    self.restoreGeometry(settings['geometry'])
                if 'window_state' in settings:
                    self.restoreState(settings['window_state'])
                if 'model' in settings and settings['model'] in self.models:
                    self.current_model = settings['model']
                    self.model_combo.setCurrentText(self.current_model)
                
        except Exception as e:
            logging.error(f"Error loading settings: {str(e)}")
    
    def save_settings(self):
        """Save application settings."""
        settings_dir = os.path.join(str(Path.home()), ".pashto_ai")
        os.makedirs(settings_dir, exist_ok=True)
        
        settings = {
            'geometry': self.saveGeometry(),
            'window_state': self.saveState(),
            'model': self.current_model
        }
        
        try:
            with open(os.path.join(settings_dir, "settings.json"), 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            logging.error(f"Error saving settings: {str(e)}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.chat_widget.maybe_save():
            self.save_settings()
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    # Set up logging
    log_dir = os.path.join(str(Path.home()), ".pashto_ai", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "pashto_ai.log")),
            logging.StreamHandler()
        ]
    )
    
    # Create and run the application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Set application info
    app.setApplicationName("Pashto AI")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Pashto AI")
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())
