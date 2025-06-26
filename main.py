import sys
import requests
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QComboBox, QLabel, QStatusBar, QSplitter, QMessageBox,
    QScrollBar, QInputDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QTextCursor

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import re

import memory
import profiles
import multimodal

# --- Model Configuration ---
# Centralized configuration with added support for streaming and conversation history.
# Payloads are now functions that format the entire chat history for the specific API.
# Parsers handle both streaming chunks and full responses.
OPENROUTER_MODELS = {
    "Llama-3-8B": {
        "model": "meta-llama/llama-3-8b-instruct",
        "display": "Llama-3-8B (OpenRouter)",
    },
    "Mistral-7B": {
        "model": "mistralai/mistral-7b-instruct",
        "display": "Mistral-7B (OpenRouter)",
    },
    "DeepSeek-Chat": {
        "model": "deepseek-ai/deepseek-chat",
        "display": "DeepSeek-Chat (OpenRouter)",
    },
}

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
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": OPENROUTER_MODELS[self.model_name]["model"],
                "messages": self.history,
                "stream": False
            }
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            result = data['choices'][0]['message']['content']
            self.response_completed.emit(result)
        except Exception as e:
            self.error_occurred.emit(f"System Error: {str(e)}")

class FreeAIChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pashto ai")
        self.setGeometry(100, 100, 900, 700)
        self.setWindowIcon(QIcon(":ai_icon"))
        self.memory_data = memory.load_memory()
        self.conversation_history = self.memory_data.get("history", [])
        self.user_preferences = self.memory_data.get("preferences", {})
        self.api_key = self.user_preferences.get("openrouter_api_key", "")
        self.init_ui()
        self.set_dark_theme()
        self.statusBar().showMessage("Ready. Select a model and start a conversation!")
        if not self.api_key:
            self.prompt_api_key()
    def prompt_api_key(self):
        msg = ("Enter your OpenRouter API key.\n" 
               "Get a free key at https://openrouter.ai/ (sign up, go to API Keys).\n" 
               "You can change this later in Preferences.")
        key, ok = QInputDialog.getText(self, "OpenRouter API Key Required", msg, text="")
        if ok and key:
            self.api_key = key.strip()
            self.user_preferences["openrouter_api_key"] = self.api_key
            self.save_memory()
        else:
            QMessageBox.warning(self, "API Key Required", "You must enter an API key to use pashto ai.")
            self.prompt_api_key()
    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        header = QLabel("pashto ai")
        header_font = QFont("Arial", 16, QFont.Bold)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #6e44ff; padding: 15px;")
        main_layout.addWidget(header)
        pref_layout = QHBoxLayout()
        self.pref_label = QLabel(self.get_pref_summary())
        self.pref_label.setStyleSheet("color: #8a8aa3; font-size: 10pt;")
        pref_btn = QPushButton("Preferences")
        pref_btn.clicked.connect(self.show_preferences_dialog)
        profile_btn = QPushButton("Profiles")
        profile_btn.clicked.connect(self.show_profiles_dialog)
        pref_layout.addWidget(self.pref_label)
        pref_layout.addWidget(pref_btn)
        pref_layout.addWidget(profile_btn)
        pref_layout.addStretch()
        main_layout.addLayout(pref_layout)
        model_layout = QHBoxLayout()
        model_label = QLabel("Select AI Model:")
        model_label.setStyleSheet("color: #f0f4ff; font-weight: bold;")
        self.model_combo = QComboBox()
        self.model_combo.addItems([OPENROUTER_MODELS[k]["display"] for k in OPENROUTER_MODELS])
        self.model_combo.setStyleSheet("""
            QComboBox { background-color: #2a2a4a; color: #f0f4ff; border: 1px solid #6e44ff; border-radius: 5px; padding: 5px; }
            QComboBox::drop-down { border: none; }
        """)
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        main_layout.addLayout(model_layout)
        splitter = QSplitter(Qt.Vertical)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(300)
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Type your message here...")
        self.input_text.setMinimumHeight(150)
        splitter.addWidget(self.output_text)
        splitter.addWidget(self.input_text)
        splitter.setSizes([450, 150])
        main_layout.addWidget(splitter, 1)
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
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
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
        profiles_data = profiles.load_profiles()
        items = list(profiles_data.keys())
        if not items:
            QMessageBox.information(self, "Profiles", "No profiles saved yet.")
            return
        item, ok = QInputDialog.getItem(self, "Select Profile", "Choose a profile:", items, editable=False)
        if ok and item:
            self.current_profile = profiles_data[item]
            self.user_preferences.update(self.current_profile.get("preferences", {}))
            self.pref_label.setText(self.get_pref_summary())
            self.save_memory()
    def save_memory(self):
        self.memory_data["preferences"] = self.user_preferences
        self.memory_data["history"] = self.conversation_history
        memory.save_memory(self.memory_data)
    def send_message(self):
        prompt = self.input_text.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Empty Input", "Please enter a message.")
            return
        if self.user_preferences.get("name") or self.user_preferences.get("style"):
            pref_str = f"(Call me {self.user_preferences.get('name', '')} and always explain like {self.user_preferences.get('style', '')})\n"
            prompt = pref_str + prompt
        self.conversation_history.append({"role": "user", "content": prompt})
        self.redisplay_chat_history()
        self.input_text.clear()
        model_index = self.model_combo.currentIndex()
        model_name = list(OPENROUTER_MODELS.keys())[model_index]
        self.send_button.setEnabled(False)
        self.status_label.setText(f"Status: Processing with {OPENROUTER_MODELS[model_name]['display']}...")
        self.conversation_history.append({"role": "assistant", "content": ""})
        self.worker = AIWorker(self.conversation_history, model_name, self.api_key)
        self.worker.response_completed.connect(self.handle_response_completed)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()
        self.save_memory()
    def handle_response_completed(self, response):
        self.conversation_history[-1]["content"] = response
        self.redisplay_chat_history()
        self.status_label.setText("Status: Ready")
        self.send_button.setEnabled(True)
        self.save_memory()
    def handle_error(self, error_msg):
        self.output_text.append(f"<p style='color: #ff4444;'><b>System Error:</b> {error_msg}</p>")
        self.status_label.setText("Status: Error occurred")
        self.send_button.setEnabled(True)
        if self.conversation_history and self.conversation_history[-1]["role"] == "assistant":
            self.conversation_history.pop()
        self.save_memory()
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = FreeAIChatApp()
    window.show()
    
    sys.exit(app.exec_()) 