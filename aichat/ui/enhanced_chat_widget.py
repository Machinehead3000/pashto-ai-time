from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QScrollArea, QSizePolicy, QSpacerItem, QFrame, QMessageBox, QFileDialog, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QDateTime
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor, QPixmap, QPainter, QLinearGradient, QIcon
import markdown2
import os
from PIL import Image
from PyQt5.QtGui import QImage, QPixmap
import speech_recognition as sr
import pyttsx3
import emoji

class EnhancedChatMessage(QWidget):
    """A single chat message widget with avatar, bubble styling, markdown/code, and feedback."""
    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        avatar = QLabel()
        avatar.setFixedSize(32, 32)
        avatar.setText("U" if is_user else "AI")
        avatar.setStyleSheet("border-radius: 16px; background: #00f0ff; color: #0a0a12; font-weight: bold;")
        bubble = QTextEdit()
        bubble.setReadOnly(True)
        bubble.setFrameShape(QFrame.NoFrame)
        # Markdown/code support
        html = markdown2.markdown(text, extras=["fenced-code-blocks", "tables", "strike", "target-blank-links"])
        bubble.setHtml(html)
        bubble.setStyleSheet("background: #222244; color: #e0e0ff; border-radius: 8px; padding: 10px;")
        if is_user:
            layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
            layout.addWidget(bubble, 1)
            layout.addWidget(avatar)
        else:
            layout.addWidget(avatar)
            layout.addWidget(bubble, 1)
        # Feedback buttons for AI
        if not is_user:
            feedback_layout = QHBoxLayout()
            thumbs_up = QPushButton(QIcon.fromTheme("thumb-up"), "👍")
            thumbs_down = QPushButton(QIcon.fromTheme("thumb-down"), "👎")
            thumbs_up.setFixedSize(28, 28)
            thumbs_down.setFixedSize(28, 28)
            feedback_layout.addWidget(thumbs_up)
            feedback_layout.addWidget(thumbs_down)
            feedback_layout.addStretch()
            layout.addLayout(feedback_layout)

class TypingIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 20)
        self.dots = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(300)
    def animate(self):
        self.dots = (self.dots + 1) % 4
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
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

class EnhancedChatWidget(QWidget):
    """
    A chat widget that provides a user interface for chatting and integrates with AI models.
    Now with avatars, message bubbles, typing indicator, and modern styling.
    """
    message_sent = pyqtSignal(str)

    def __init__(self, ai_model=None, parent=None):
        super().__init__(parent)
        self.ai_model = ai_model
        self.message_history = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 15)
        layout.setSpacing(10)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(5, 5, 5, 5)
        self.chat_layout.setSpacing(5)
        self.chat_layout.addStretch()
        self.scroll_area.setWidget(self.chat_container)
        self.typing_indicator = TypingIndicator()
        self.typing_indicator.hide()
        # Input bar with file, voice, tts, export
        self.input_line = QLineEdit(self)
        self.input_line.setPlaceholderText("Type your message...")
        self.input_line.setStyleSheet("background: #222244; color: #e0e0ff; border-radius: 8px; padding: 10px;")
        self.send_button = QPushButton("Send", self)
        self.send_button.setFixedSize(100, 40)
        self.send_button.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ff00ff, stop:1 #00f0ff); color: #0a0a12; border-radius: 6px; font-weight: bold;")
        self.file_button = QPushButton(QIcon.fromTheme("document-open"), "")
        self.file_button.setToolTip("Send file or image")
        self.file_button.setFixedSize(36, 36)
        self.voice_button = QPushButton(QIcon.fromTheme("microphone"), "")
        self.voice_button.setToolTip("Voice input")
        self.voice_button.setFixedSize(36, 36)
        self.tts_button = QPushButton(QIcon.fromTheme("media-playback-start"), "")
        self.tts_button.setToolTip("Read last AI message aloud")
        self.tts_button.setFixedSize(36, 36)
        self.export_button = QPushButton(QIcon.fromTheme("document-save"), "")
        self.export_button.setToolTip("Export conversation")
        self.export_button.setFixedSize(36, 36)
        self.emoji_button = QPushButton(emoji.emojize(":smile:"))
        self.emoji_button.setToolTip("Insert emoji")
        self.emoji_button.setFixedSize(36, 36)
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.file_button)
        input_layout.addWidget(self.voice_button)
        input_layout.addWidget(self.emoji_button)
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.tts_button)
        input_layout.addWidget(self.export_button)
        layout.addWidget(self.scroll_area)
        layout.addWidget(self.typing_indicator, 0, Qt.AlignLeft)
        layout.addLayout(input_layout)
        self.send_button.clicked.connect(self.handle_send)
        self.input_line.returnPressed.connect(self.handle_send)
        self.file_button.clicked.connect(self.handle_file_upload)
        self.export_button.clicked.connect(self.export_conversation)
        self.emoji_button.clicked.connect(self.open_emoji_picker)
        self.voice_button.clicked.connect(self.handle_voice_input)
        self.tts_button.clicked.connect(self.handle_tts)

    def add_message(self, text, is_user=False):
        msg = EnhancedChatMessage(text, is_user, self)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, msg)
        self.scroll_to_bottom()
        self.message_history.append({
            "text": text,
            "is_user": is_user,
            "timestamp": QDateTime.currentDateTime().toString(Qt.ISODate)
        })
        # Auto-copy button for each message
        copy_btn = QPushButton(QIcon.fromTheme("edit-copy"), "")
        copy_btn.setToolTip("Copy message")
        copy_btn.setFixedSize(24, 24)
        def copy_text():
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
        copy_btn.clicked.connect(copy_text)
        self.chat_layout.insertWidget(self.chat_layout.count() - 2, copy_btn)

    def handle_send(self):
        user_message = self.input_line.text().strip()
        if user_message:
            self.add_message(user_message, is_user=True)
            self.input_line.clear()
            self.message_sent.emit(user_message)
            self.show_typing(True)
            QTimer.singleShot(800, lambda: self.get_ai_response(user_message))

    def get_ai_response(self, user_message):
        # Placeholder for AI model integration
        if self.ai_model:
            self.show_typing(True)
            response = self.ai_model.generate_response(user_message)
        else:
            response = "[AI response placeholder]"
        self.add_message(response, is_user=False)
        self.show_typing(False)

    def show_typing(self, show=True):
        self.typing_indicator.setVisible(show)
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def handle_file_upload(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select file to send", filter="Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)")
        if file_path:
            filename = os.path.basename(file_path)
            if any(file_path.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]):
                # Show image preview in chat
                img = Image.open(file_path)
                img.thumbnail((200, 200))
                img.save("_preview.png")
                pixmap = QPixmap("_preview.png")
                label = QLabel()
                label.setPixmap(pixmap)
                self.chat_layout.insertWidget(self.chat_layout.count() - 1, label)
                self.add_message(f"[Image sent: {filename}]", is_user=True)
                os.remove("_preview.png")
            else:
                self.add_message(f"[File sent: {filename}]", is_user=True)

    def open_emoji_picker(self):
        # Simple emoji picker: insert a smile emoji for demo
        self.input_line.insert(emoji.emojize(":smile:"))

    def handle_voice_input(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.input_line.setText("Listening...")
            audio = recognizer.listen(source, timeout=5)
        try:
            text = recognizer.recognize_google(audio)
            self.input_line.setText(text)
        except Exception as e:
            self.input_line.setText("")
            QMessageBox.warning(self, "Voice Input", f"Could not recognize speech: {e}")

    def handle_tts(self):
        # Read last AI message aloud
        ai_msgs = [m for m in self.message_history if not m["is_user"]]
        if ai_msgs:
            engine = pyttsx3.init()
            engine.say(ai_msgs[-1]["text"])
            engine.runAndWait()

    def toggle_theme(self):
        # Placeholder: toggle between dark/light (implement with your theme manager)
        QMessageBox.information(self, "Theme", "Theme toggled (implement actual logic)")

    def export_conversation(self):
        export_path, _ = QFileDialog.getSaveFileName(self, "Export Conversation", "chat.md", "Markdown Files (*.md);;Text Files (*.txt)")
        if export_path:
            with open(export_path, "w", encoding="utf-8") as f:
                for msg in self.message_history:
                    sender = "You" if msg["is_user"] else "AI"
                    f.write(f"**{sender}:** {msg['text']}\n\n")
            QMessageBox.information(self, "Exported", f"Conversation exported to {export_path}")

    def clear_chat(self):
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.message_history.clear()
        self.add_message("Welcome to the chat! Type a message to begin.")
