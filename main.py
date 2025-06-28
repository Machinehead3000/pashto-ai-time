import sys
import os
import requests
import json
from pathlib import Path
from typing import Dict, Any, Optional
import threading
import subprocess
from PyQt5.QtWidgets import QMessageBox, QDialog

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QComboBox, QLabel, QStatusBar, QSplitter, QMessageBox,
    QScrollBar, QInputDialog, QAction, QMenu, QMenuBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl, QTimer, QObject, QMetaObject, Q_ARG
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QTextCursor, QDesktopServices

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import local modules
try:
    from aichat.ui.api_key_dialog import APIKeyDialog
    from aichat.utils.api_key_manager import APIKeyManager
    from aichat.ui.plugin_manager import PluginManagerWidget
    from aichat.ui.tts_widget import TTSWidget
    from aichat.memory import manager as memory
    from aichat.profiles import manager as profiles
except ImportError:
    # Fallback for direct execution
    from aichat.ui.api_key_dialog import APIKeyDialog
    from aichat.utils.api_key_manager import APIKeyManager
    from aichat.ui.plugin_manager import PluginManagerWidget
    from aichat.ui.tts_widget import TTSWidget
    from aichat.memory import manager as memory
    from aichat.profiles import manager as profiles

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import re

import multimodal

# --- Model Configuration ---
# Centralized configuration with added support for streaming and conversation history.
# Payloads are now functions that format the entire chat history for the specific API.
# Parsers handle both streaming chunks and full responses.
OPENROUTER_MODELS = {
    "Fastest Available": {
        "model": "mistralai/mistral-7b-instruct",
        "display": "Fastest Available (Auto)",
    },
    "Llama-3-8B": {
        "model": "meta-llama/llama-3-8b-instruct",
        "display": "Llama-3-8B (OpenRouter)",
    },
    "Mistral-7B": {
        "model": "mistralai/mistral-7b-instruct",
        "display": "Mistral-7B (OpenRouter)",
    },
    "DeepSeek-Chat": {
        "model": "deepseek/deepseek-chat",
        "display": "DeepSeek-Chat (OpenRouter)",
    },
}

# Track model health
MODEL_HEALTH = {k: True for k in OPENROUTER_MODELS}

def ensure_package(pkg, import_name=None):
    try:
        __import__(import_name or pkg)
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        except Exception as e:
            QMessageBox.critical(None, "Dependency Error", f"Failed to install required package: {pkg}\nError: {e}")
            sys.exit(1)

required_pkgs = [
    ("PyQt5", None),
    ("requests", None),
    ("transformers", None),
    ("PyPDF2", None),
    ("python-docx", "docx"),
    ("matplotlib", None),
    ("qtpy", None),
    ("html2text", None),
    ("beautifulsoup4", "bs4"),
]
for pkg, import_name in required_pkgs:
    ensure_package(pkg, import_name)

class AIWorker(QThread):
    token_received = pyqtSignal(str)
    response_completed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, history, model_name, api_key):
        super().__init__()
        self.history = history
        self.model_name = model_name
        self.api_key = api_key

    def run(self):
        # Uncommented: Real API call for AI response
        import requests
        try:
            print(f"[DEBUG] Starting AI request with model: {self.model_name}")
            print(f"[DEBUG] API Key: {self.api_key[:5]}...{self.api_key[-5:] if self.api_key else 'None'}")
            
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Get the actual model ID from OPENROUTER_MODELS
            model_id = OPENROUTER_MODELS.get(self.model_name, {}).get("model", self.model_name)
            
            payload = {
                "model": model_id,
                "messages": self.history,
                "stream": True
            }
            
            print(f"[DEBUG] Sending request to {url}")
            print(f"[DEBUG] Model ID: {model_id}")
            print(f"[DEBUG] Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(url, headers=headers, json=payload, timeout=120, stream=True)
            
            print(f"[DEBUG] Response status code: {response.status_code}")
            print(f"[DEBUG] Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                error_content = response.text
                print(f"[AIWorker API Error] Status: {response.status_code}")
                print(f"[AIWorker API Error] Response: {error_content}")
                
                try:
                    err_json = response.json()
                    print(f"[AIWorker API Error] JSON: {err_json}")
                    if 'error' in err_json:
                        err_msg = err_json['error'].get('message', error_content)
                        error_msg = f"API Error ({response.status_code}): {err_msg}"
                    else:
                        error_msg = f"API Error ({response.status_code}): {error_content}"
                except Exception as ex:
                    print(f"[AIWorker API Error - JSON parse]: {ex}")
                    error_msg = f"API Error ({response.status_code}): {error_content}"
                
                print(f"[AIWorker] Emitting error: {error_msg}")
                self.error_occurred.emit(error_msg)
                return
            full_response = ""
            print("[DEBUG] Starting to process response stream...")
            
            for line in response.iter_lines():
                if line:
                    try:
                        # Remove 'data: ' prefix if present
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            line_str = line_str[6:].strip()
                        
                        # Skip empty lines or [DONE] message
                        if not line_str or line_str == '[DONE]':
                            print("[DEBUG] Received empty line or [DONE]")
                            continue
                            
                        print(f"[DEBUG] Raw line: {line_str}")
                        data = json.loads(line_str)
                        
                        if 'choices' in data and data['choices']:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta and delta['content']:
                                token = delta['content']
                                print(f"[DEBUG] Received token: {token}")
                                full_response += token
                                self.token_received.emit(token)
                            
                            # Check for finish reason
                            finish_reason = data['choices'][0].get('finish_reason')
                            if finish_reason:
                                print(f"[DEBUG] Finish reason: {finish_reason}")
                                if finish_reason == 'stop':
                                    break
                                elif finish_reason == 'length':
                                    print("[WARNING] Response was truncated due to max_tokens limit")
                                    break
                    except json.JSONDecodeError as je:
                        print(f"[ERROR] Failed to parse JSON: {line_str}")
                        print(f"[ERROR] JSON Error: {je}")
                    except Exception as ex:
                        print(f"[ERROR] Error processing stream: {ex}")
                        print(f"[ERROR] Raw line that caused error: {line}")
            
            print(f"[DEBUG] Completed response. Total tokens: {len(full_response)}")
            if not full_response:
                print("[WARNING] Empty response received from the API")
            
            self.response_completed.emit(full_response)
        except Exception as e:
            import traceback
            print(f"[AIWorker Exception]: {e}\n{traceback.format_exc()}")
            self.error_occurred.emit(f"System Error: {str(e)}")

class FreeAIChatApp(QMainWindow):
    model_test_result = pyqtSignal(int, bool, str)

    def __init__(self):
        try:
            super().__init__()
            self.setWindowTitle("Pashto AI")
            self.setGeometry(100, 100, 1000, 800)
            
            # Initialize API key manager
            self.api_key_manager = APIKeyManager()
            
            # Initialize memory manager
            self.memory_manager = memory.MemoryManager.get_default()
            self.user_preferences = self.memory_manager.preferences.to_dict()
            self.conversation_history = []
            current_conv = self.memory_manager.get_current_conversation()
            if current_conv:
                for msg in current_conv.get_messages():
                    self.conversation_history.append({"role": msg.role.value, "content": msg.content})
            
            # Initialize profile manager
            self.profile_manager = profiles.ProfileManager()
            
            # Get API key from secure storage
            self.api_key = self.api_key_manager.get_api_key("openrouter") or ""
            
            # Initialize UI
            self.is_closing = False
            self.model_test_result.connect(self.on_model_test_result)
            self.init_ui()
            self.set_dark_theme()
            
            # Check if we need to prompt for API key
            if not self.api_key:
                self.manage_api_keys()
            
            self.statusBar().showMessage("Ready. Select a model and start a conversation!")
        except Exception as e:
            import traceback
            print(f"[UI INIT ERROR]: {e}\n{traceback.format_exc()}")
    
    def manage_api_keys(self):
        """Open the API key management dialog."""
        dialog = APIKeyDialog(
            service_name="OpenRouter",
            parent=self,
            test_endpoint="https://openrouter.ai/api/v1/auth/me",
            key_help_url="https://openrouter.ai/keys"
        )
        
        # Connect signals
        dialog.api_key_saved.connect(self.on_api_key_saved)
        
        # Show dialog
        if dialog.exec_() == QDialog.Accepted:
            # API key was saved successfully
            self.api_key = dialog.api_key_edit.text().strip()
            self.statusBar().showMessage("API key saved successfully", 3000)
        elif not self.api_key:
            # No API key and user cancelled - show warning
            QMessageBox.warning(
                self,
                "API Key Required",
                "An API key is required to use this application. "
                "You can set it later from the Settings menu.",
                QMessageBox.Ok
            )
    
    def on_api_key_saved(self, service_name: str, api_key: str):
        """Handle API key saved event."""
        self.api_key = api_key
        # Update the user preferences for backward compatibility
        self.user_preferences["openrouter_api_key"] = api_key
        self.save_memory()
        
        # Update status bar
        self.statusBar().showMessage(f"{service_name.capitalize()} API key saved successfully", 3000)
        
        # Enable any UI elements that require an API key
        self.update_api_key_status()
    
    def init_ui(self):
        try:
            # Create menu bar
            self.create_menu_bar()
            
            # Main widget and layout
            main_widget = QWidget()
            main_layout = QVBoxLayout()

            # Instructions
            instructions = QLabel(
                "Manage your API keys for different AI services. "
                "Your keys are stored securely on your computer.\n\n"
                "Go to Settings > API Keys to manage your API keys."
            )
            instructions.setWordWrap(True)
            instructions.setStyleSheet("color: #a0a0c0; padding: 10px;")
            main_layout.addWidget(instructions)
            
            # Add API key status indicator
            self.api_key_status = QLabel()
            self.update_api_key_status()
            main_layout.addWidget(self.api_key_status)
            
            # Add a button to manage API keys
            manage_keys_btn = QPushButton("Manage API Keys")
            manage_keys_btn.clicked.connect(self.manage_api_keys)
            manage_keys_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a4a6a;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                    margin: 10px;
                }
                QPushButton:hover {
                    background-color: #3a5a7a;
                }
            """)
            main_layout.addWidget(manage_keys_btn, 0, Qt.AlignCenter)
            
            pref_layout = QHBoxLayout()
            self.pref_label = QLabel(self.get_pref_summary())
            pref_layout.addWidget(self.pref_label)
            pref_layout.addStretch()
            main_layout.addLayout(pref_layout)
            
            model_layout = QHBoxLayout()
            model_label = QLabel("Select AI Model:")
            model_label.setStyleSheet("color: #f0f4ff; font-weight: bold;")
            model_layout.addWidget(model_label)
            self.model_combo = QComboBox()
            self.model_combo.addItems([OPENROUTER_MODELS[k]["display"] for k in OPENROUTER_MODELS])
            self.model_combo.setStyleSheet("""
                QComboBox { background-color: #2a2a4a; color: #f0f4ff; border: 1px solid #6e44ff; border-radius: 5px; padding: 5px; }
                QComboBox::drop-down { border: none; }
            """)
            model_layout.addWidget(model_label)
            model_layout.addWidget(self.model_combo)
            # Add Test Model button and status label
            self.test_model_btn = QPushButton("Test Model")
            self.test_model_btn.setStyleSheet("""
                QPushButton { background-color: #4caf50; color: white; border: none; border-radius: 5px; padding: 5px 10px; font-weight: bold; }
                QPushButton:hover { background-color: #388e3c; }
            """)
            self.test_model_btn.clicked.connect(self.test_selected_model)
            self.model_status_label = QLabel()
            model_layout.addWidget(self.test_model_btn)
            model_layout.addWidget(self.model_status_label)
            model_layout.addStretch()
            main_layout.addLayout(model_layout)
            splitter = QSplitter(Qt.Vertical)
            self.output_text = QTextEdit()
            self.output_text.setReadOnly(True)
            self.output_text.setMinimumHeight(350)
            self.input_text = QTextEdit()
            self.input_text.setPlaceholderText("Type your message here...")
            self.input_text.setMinimumHeight(120)
            splitter.addWidget(self.output_text)
            splitter.addWidget(self.input_text)
            splitter.setSizes([450, 150])
            main_layout.addWidget(splitter, 1)

            # Speak button for TTS
            self.speak_button = QPushButton("🔊 Speak Last AI Response")
            self.speak_button.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold; border-radius: 6px; padding: 8px 16px;")
            self.speak_button.clicked.connect(self.speak_last_ai_response)
            main_layout.addWidget(self.speak_button, 0, Qt.AlignLeft)

            # TTSWidget (hidden, used for speech)
            self.tts_widget = TTSWidget(self)
            self.tts_widget.hide()

            button_layout = QHBoxLayout()
            self.send_button = QPushButton("Send Message")
            self.send_button.setStyleSheet("""
                QPushButton { background-color: #6e44ff; color: white; border: none; border-radius: 5px; padding: 10px 20px; font-weight: bold; }
                QPushButton:hover { background-color: #5d3be0; }
                QPushButton:disabled { background-color: #4a3a7a; }
            """)
            self.send_button.clicked.connect(self.send_message)
            clear_button = QPushButton("Clear Conversation")
            clear_button.setStyleSheet("""
                QPushButton { background-color: #3a3a5a; color: #f0f4ff; border: 1px solid #5d5d8a; border-radius: 5px; padding: 10px 20px; }
                QPushButton:hover { background-color: #4a4a6a; }
            """)
            clear_button.clicked.connect(self.clear_chat)
            button_layout.addWidget(self.send_button)
            button_layout.addWidget(clear_button)
            button_layout.addStretch()
            main_layout.addLayout(button_layout)
            self.status_label = QLabel("Status: Ready")
            self.status_label.setStyleSheet("color: #8a8aa3; padding: 5px;")
            main_layout.addWidget(self.status_label)

            # Set minimum and preferred sizes for main widgets
            main_widget.setMinimumSize(900, 650)
            self.output_text.setMinimumHeight(350)
            self.input_text.setMinimumHeight(120)
            self.model_combo.setMinimumWidth(220)
            self.send_button.setMinimumWidth(160)
            self.send_button.setMinimumHeight(40)
            self.status_label.setMinimumHeight(28)

            main_widget.setLayout(main_layout)
            self.setCentralWidget(main_widget)
            # Set a fixed initial window size
            self.resize(1100, 800)
            self.setMinimumSize(900, 650)
            self.show()
            self.raise_()
            print("[DEBUG] UI initialized and main window shown.")
            # self.auto_test_models()  # TEMPORARILY DISABLED for debugging
        except Exception as e:
            import traceback
            print(f"[UI INIT ERROR]: {e}\n{traceback.format_exc()}")

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        # File menu
        file_menu = menu_bar.addMenu("&File")
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        # Features menu
        features_menu = menu_bar.addMenu("&Features")
        plugin_manager_action = QAction("Plugin Manager", self)
        plugin_manager_action.triggered.connect(self.show_plugin_manager)
        features_menu.addAction(plugin_manager_action)
        profiles_action = QAction("Profiles", self)
        profiles_action.triggered.connect(self.show_profiles_dialog)
        features_menu.addAction(profiles_action)
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings_dialog)
        features_menu.addAction(settings_action)
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def show_about_dialog(self):
        QMessageBox.about(self, "About FreeAIChatApp", "<b>FreeAIChatApp</b><br>AI chat assistant with pro features.")

    def get_pref_summary(self):
        name = self.user_preferences.get("name", "(no name)")
        style = self.user_preferences.get("style", "(default)")
        return f"User: {name} | Style: {style}"

    def show_preferences_dialog(self):
        name, ok1 = QInputDialog.getText(self, "Set Name", "What should I call you?", text=self.user_preferences.get("name", ""))
        if not ok1:
            return
        style, ok2 = QInputDialog.getText(self, "Set Style", "How should I explain things? (e.g., like I'm a beginner)", text=self.user_preferences.get("style", ""))
        if not ok2:
            return
        api_key, ok3 = QInputDialog.getText(self, "OpenRouter API Key", "Enter your OpenRouter API key:", text=self.api_key)
        if ok3 and api_key:
            self.api_key = api_key.strip()
            self.user_preferences["openrouter_api_key"] = self.api_key
        self.user_preferences["name"] = name
        self.user_preferences["style"] = style
        self.pref_label.setText(self.get_pref_summary())
        self.save_memory()

    def show_profiles_dialog(self):
        profiles_list = self.profile_manager.list_profiles()
        items = [profile.name for profile in profiles_list]
        if not items:
            QMessageBox.information(self, "Profiles", "No profiles saved yet.")
            return
        item, ok = QInputDialog.getItem(self, "Select Profile", "Choose a profile:", items, editable=False)
        if ok and item:
            selected_profile = next((p for p in profiles_list if p.name == item), None)
            if selected_profile:
                self.user_preferences.update(selected_profile.ui_preferences.to_dict())
                self.pref_label.setText(self.get_pref_summary())
                self.save_memory()

    def save_memory(self):
        # Save preferences
        self.memory_manager.update_preferences(**self.user_preferences)
        # Save conversation
        current_conv = self.memory_manager.get_current_conversation()
        if current_conv:
            current_conv.messages = []
            for msg in self.conversation_history:
                from aichat.memory.models import Message, MessageRole, MessageType
                current_conv.add_message(Message(
                    role=MessageRole(msg["role"]),
                    content=msg["content"],
                    message_type=MessageType.TEXT
                ))
            self.memory_manager._save_conversations()

    def send_message(self):
        prompt = self.input_text.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Empty Input", "Please enter a message.")
            return
            
        # Add user preferences if any
        if self.user_preferences.get("name") or self.user_preferences.get("style"):
            pref_str = f"(Call me {self.user_preferences.get('name', '')} and always explain like {self.user_preferences.get('style', '')})\n"
            prompt = pref_str + prompt
            
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": prompt})
        self.redisplay_chat_history()
        self.input_text.clear()
        
        # Get selected model
        model_index = self.model_combo.currentIndex()
        model_name = list(OPENROUTER_MODELS.keys())[model_index]
        
        # If Fastest Available, pick the fastest healthy model
        if model_name == "Fastest Available":
            self.select_fastest_model()
            model_index = self.model_combo.currentIndex()
            model_name = list(OPENROUTER_MODELS.keys())[model_index]
            
        # Disable send button and show typing indicator
        self.send_button.setEnabled(False)
        self.status_label.setText(f"Status: Generating response with {OPENROUTER_MODELS[model_name]['display']}...")
        self.show_typing_spinner(True)
        
        # Create system message with instructions for the AI
        system_message = {
            "role": "system",
            "content": "You are a helpful and friendly AI assistant. Provide clear, concise, and accurate responses. "
                      "Be conversational and engaging, but get straight to the point when needed."
        }
        
        # Prepare the messages for the API call
        messages = [system_message] + self.conversation_history
        
        # Create and start the worker thread
        self.worker = AIWorker(messages, model_name, self.api_key)
        self.worker.response_completed.connect(self.on_ai_response)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()
        
        # Save the conversation state
        self.save_memory()
        
    def on_ai_response(self, response):
        """Handle the AI's response and update the UI."""
        # Add the AI's response to the conversation history
        self.conversation_history.append({"role": "assistant", "content": response})
        self.redisplay_chat_history()
        
        # Update UI state
        self.status_label.setText("Status: Ready")
        self.send_button.setEnabled(True)
        self.show_typing_spinner(False)
        
        # Save the updated conversation
        self.save_memory()



    def append_ai_message(self, text):
        self.conversation_history.append({"role": "assistant", "content": text})
        self.redisplay_chat_history()

    def run_model_step(self, prompt, model_name, callback):
        # Helper to run a single model step and call callback with the result
        self.worker = AIWorker(
            [{"role": "user", "content": prompt}],
            model_name,
            self.api_key
        )
        def on_complete(result):
            callback(result)
        self.worker.response_completed.connect(on_complete)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()

    def show_typing_spinner(self, show):
        if show:
            self.status_label.setText("<span style='color: #4caf50;'>AI is thinking…</span>")
        else:
            self.status_label.setText("Status: Ready")

    def handle_error(self, error_msg):
        print(f"[UI ERROR]: {error_msg}")
        self.output_text.append(f"<p style='color: #ff4444;'><b>System Error:</b> {error_msg}</p>")
        self.status_label.setText("Status: Error occurred")
        self.send_button.setEnabled(True)
        self.show_typing_spinner(False)
        if self.conversation_history and self.conversation_history[-1]["role"] == "assistant":
            self.conversation_history.pop()
        self.save_memory()
        # Show a message box for critical errors
        QMessageBox.critical(self, "AI Error", error_msg)

    def clear_chat(self):
        self.conversation_history.clear()
        self.output_text.clear()
        self.status_label.setText("Status: Conversation cleared")
        self.save_memory()

    def redisplay_chat_history(self, is_streaming=False):
        html = ""
        # Use a dark theme for pygments that matches the app
        formatter = HtmlFormatter(style='monokai', noclasses=True, nobackground=True)

        for message in self.conversation_history:
            role = message["role"]
            content = message["content"]

            if role == "user":
                html += f"""
                <div style='background-color: #2a2a4a; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                    <p style='color: #a0a0ff; font-weight: bold; margin-bottom: 5px;'>You:</p>
                    <p style='color: #f0f4ff; white-space: pre-wrap;'>{content}</p>
                </div>
                """
            elif role == "assistant":
                # For the final render, apply syntax highlighting. Skip for streaming to avoid lag.
                if not is_streaming and '```' in content:
                    parts = re.split(r'(```(?:\w+)?\n.*?\n```)', content, flags=re.DOTALL)
                    processed_content = ""
                    for part in parts:
                        match = re.match(r'```(\w+)?\n(.*?)\n```', part, flags=re.DOTALL)
                        if match:
                            lang = match.group(1) or 'text'
                            code = match.group(2)
                            try:
                                lexer = get_lexer_by_name(lang, stripall=True)
                                processed_content += highlight(code, lexer, formatter)
                            except:
                                processed_content += f"<pre><code>{code}</code></pre>"
                        else:
                            processed_content += f"<p style='white-space: pre-wrap;'>{part}</p>"
                    content_html = processed_content
                else:
                    content_html = f"<p style='white-space: pre-wrap;'>{content}</p>"

                html += f"""
                <div style='background-color: #1a1a2e; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                    <p style='color: #6e44ff; font-weight: bold; margin-bottom: 5px;'>AI ({self.model_combo.currentText()}):</p>
                    {content_html}
                </div>
                """
        
        self.output_text.setHtml(html)
        # Auto-scroll to the bottom
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_api_key_status(self):
        if hasattr(self, 'api_key_status'):
            if self.api_key:
                self.api_key_status.setText('<span style="color: #4caf50;">API Key: Set &#x2714;</span>')
            else:
                self.api_key_status.setText('<span style="color: #ff5555;">API Key: Not Set &#x26A0;</span>')

    def set_dark_theme(self):
        dark_stylesheet = """
            QMainWindow, QWidget {
                background-color: #181828;
                color: #e0e0ff;
            }
            QLabel {
                color: #e0e0ff;
            }
            QPushButton {
                background-color: #2a2a4a;
                color: #f0f4ff;
                border: 1px solid #6e44ff;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #3a3a5a;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #23233a;
                color: #e0e0ff;
                border: 1px solid #6e44ff;
                border-radius: 4px;
            }
            QMenuBar, QMenu {
                background-color: #23233a;
                color: #e0e0ff;
            }
            QMenu::item:selected {
                background-color: #6e44ff;
                color: #fff;
            }
        """
        self.setStyleSheet(dark_stylesheet)

    def test_selected_model(self, model_index=None):
        if model_index is None:
            model_index = self.model_combo.currentIndex()
        model_name = list(OPENROUTER_MODELS.keys())[model_index]
        api_key = self.api_key
        import requests
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": OPENROUTER_MODELS[model_name]["model"],
            "messages": [{"role": "user", "content": "Hello!"}],
            "stream": False
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            self.model_test_result.emit(model_index, True, "")
        except Exception as e:
            err_msg = str(e)
            try:
                err_json = response.json()
                if 'error' in err_json:
                    err_msg = err_json['error'].get('message', err_msg)
            except Exception:
                pass
            self.model_test_result.emit(model_index, False, err_msg)

    def on_model_test_result(self, model_index, ok, err_msg):
        if self.is_closing or not self.isVisible():
            return
        try:
            if not hasattr(self, 'model_status_label') or self.model_status_label is None:
                return
            if not hasattr(self, 'model_combo'):
                return
            model_name = list(OPENROUTER_MODELS.keys())[model_index]
            if ok:
                self.model_status_label.setText('<span style="color: #4caf50;">&#x2714; Model OK</span>')
                MODEL_HEALTH[model_name] = True
                self.model_combo.model().item(model_index).setEnabled(True)
            else:
                self.model_status_label.setText('<span style="color: #ff5555;">&#x26A0; Model Error</span>')
                MODEL_HEALTH[model_name] = False
                self.model_combo.model().item(model_index).setEnabled(False)
                QMessageBox.critical(self, "Model Test Failed", f"<b>Model test failed:</b><br>{err_msg}<br><br>See <a href='https://openrouter.ai/models'>OpenRouter Models</a> for valid model names.")
        except Exception as e:
            import traceback
            print(f"[Model Test Result UI Update Error]: {e}\n{traceback.format_exc()}")

    def auto_test_models(self):
        # Test all models in a background thread, but update UI in main thread
        import threading
        def test_all():
            for i, model_name in enumerate(OPENROUTER_MODELS):
                if model_name == "Fastest Available":
                    continue
                # Only do network request in thread, UI update via signal
                self.test_selected_model(model_index=i)
        threading.Thread(target=test_all, daemon=True).start()

    def select_fastest_model(self):
        # Pick the first healthy model (prefer Mistral)
        for name in ["Mistral-7B", "Llama-3-8B", "DeepSeek-Chat"]:
            if MODEL_HEALTH.get(name, False):
                idx = list(OPENROUTER_MODELS.keys()).index(name)
                self.model_combo.setCurrentIndex(idx)
                self.status_label.setText(f"Auto-selected fastest model: {name}")
                return
        self.status_label.setText("No healthy models available!")

    def closeEvent(self, event):
        self.is_closing = True
        try:
            self.model_test_result.disconnect(self.on_model_test_result)
        except Exception:
            pass
        super().closeEvent(event)

    def show_plugin_manager(self):
        dlg = PluginManagerWidget(self)
        dlg.setWindowTitle("Plugin Manager")
        dlg.resize(900, 700)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    def show_settings_dialog(self):
        QMessageBox.information(self, "Settings", "Settings dialog coming soon!")

    def speak_last_ai_response(self):
        # Find the last assistant message
        for msg in reversed(self.conversation_history):
            if msg["role"] == "assistant" and msg["content"].strip():
                self.tts_widget.speak_text(msg["content"])
                return
        QMessageBox.information(self, "No AI Response", "There is no AI response to speak yet.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = FreeAIChatApp()
    window.show()
    
    sys.exit(app.exec_()) 