from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QTextEdit,
    QFrame, QSizePolicy, QToolButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QColor, QTextDocument, QTextCursor

class ChatMessage(QFrame):
    """A single chat message widget with support for different message types and styling."""
    
    def __init__(self, message, is_user=False, parent=None):
        super().__init__(parent)
        self.message = message
        self.is_user = is_user
        self.init_ui()
        self.setup_styles()
        
    def init_ui(self):
        """Initialize the UI components."""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Avatar/icon
        self.avatar = QLabel()
        self.avatar.setFixedSize(32, 32)
        self.avatar.setScaledContents(True)
        self.avatar.setStyleSheet("""
            QLabel {
                border-radius: 16px;
                background: %s;
                color: white;
                font-weight: bold;
                font-size: 14px;
                qproperty-alignment: AlignCenter;
            }
        """ % ("#6e44ff" if self.is_user else "#4a4a6a"))
        self.avatar.setText("👤" if self.is_user else "🤖")
        
        # Message content
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)
        
        # Sender label
        self.sender_label = QLabel("You" if self.is_user else "AI Assistant")
        self.sender_label.setStyleSheet("""
            QLabel {
                color: %s;
                font-weight: bold;
                font-size: 12px;
                margin-bottom: 2px;
            }
        """ % ("#9d7aff" if self.is_user else "#a0a0c0"))
        
        # Message text
        self.message_text = QTextEdit()
        self.message_text.setReadOnly(True)
        self.message_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.message_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.message_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.message_text.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                color: #f0f4ff;
                font-size: 14px;
                padding: 0;
                margin: 0;
            }
            QTextEdit:focus { border: none; outline: none; }
        """)
        
        # Set markdown content
        self.set_content(self.message)
        
        # Add widgets to layout
        content_layout.addWidget(self.sender_label)
        content_layout.addWidget(self.message_text)
        
        # Add to main layout based on message type
        if self.is_user:
            layout.addStretch()
            layout.addWidget(content_widget, stretch=1)
            layout.addWidget(self.avatar)
            self.setProperty("class", "user-message")
        else:
            layout.addWidget(self.avatar)
            layout.addWidget(content_widget, stretch=1)
            self.setProperty("class", "ai-message")
    
    def set_content(self, content):
        """Set the message content with markdown support."""
        # Convert markdown to HTML with syntax highlighting for code blocks
        from pygments import highlight
        from pygments.lexers import get_lexer_by_name, guess_lexer
        from pygments.formatters import HtmlFormatter
        import re
        
        # Split content by code blocks
        parts = re.split(r'(```(?:\w*\n)?|\n```)', content)
        in_code_block = False
        current_lang = ''
        html_parts = []
        
        for part in parts:
            if part.startswith('```'):
                if in_code_block:
                    in_code_block = False
                    current_lang = ''
                else:
                    in_code_block = True
                    # Extract language if specified
                    lang_match = re.match(r'```(\w*)', part)
                    current_lang = lang_match.group(1) if lang_match else ''
                    if current_lang:
                        current_lang = current_lang.strip()
                continue
                
            if in_code_block and part.strip():
                try:
                    lexer = get_lexer_by_name(current_lang) if current_lang else guess_lexer(part)
                    formatter = HtmlFormatter(
                        style='monokai',
                        noclasses=True,
                        nobackground=True,
                        wrapcode=True
                    )
                    code_html = highlight(part, lexer, formatter)
                    html_parts.append(f'<div class="code-block">{code_html}</div>')
                except:
                    # Fallback for unknown languages or errors
                    html_parts.append(f'<pre><code>{part}</code></pre>')
            else:
                # Convert markdown to HTML (simplified)
                if part.strip():
                    # Convert **bold**
                    part = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', part)
                    # Convert *italic*
                    part = re.sub(r'\*(.*?)\*', r'<i>\1</i>', part)
                    # Convert `code`
                    part = re.sub(r'`([^`]+)`', r'<code>\1</code>', part)
                    # Convert URLs to links
                    part = re.sub(
                        r'(https?://[^\s]+)',
                        r'<a href="\1" style="color: #6e9cff; text-decoration: none;">\1</a>',
                        part
                    )
                    # Convert newlines to <br>
                    part = part.replace('\n', '<br>')
                    html_parts.append(part)
        
        # Combine all parts
        html_content = ''.join(html_parts)
        self.message_text.setHtml(html_content)
        
        # Adjust height to content
        self.adjust_size()
    
    def adjust_size(self):
        """Adjust the height of the message to fit its content."""
        doc = self.message_text.document()
        doc.setTextWidth(self.message_text.viewport().width())
        height = int(doc.size().height() + 10)  # Add some padding
        self.message_text.setFixedHeight(height)
    
    def setup_styles(self):
        """Set up the widget styles."""
        self.setStyleSheet("""
            ChatMessage {
                background: %s;
                border-radius: 12px;
                padding: 10px 16px;
                margin: 8px 0;
                max-width: 80%%;
                border: 1px solid %s;
            }
            ChatMessage[class="user-message"] {
                background: rgba(110, 68, 255, 0.15);
                border-color: rgba(110, 68, 255, 0.3);
                margin-left: 60px;
                margin-right: 12px;
                border-top-right-radius: 4px;
            }
            ChatMessage[class="ai-message"] {
                background: rgba(32, 33, 35, 0.8);
                border-color: rgba(86, 88, 105, 0.3);
                margin-right: 60px;
                margin-left: 12px;
                border-top-left-radius: 4px;
            }
            QTextEdit {
                background: transparent;
                border: none;
                color: #f0f4ff;
                font-size: 14px;
                padding: 0;
                margin: 0;
            }
            QTextEdit:focus { border: none; outline: none; }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #4a4a6a;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            code {
                background: rgba(110, 68, 255, 0.1);
                color: #f0f4ff;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
            pre {
                background: #1e1e2e;
                border-left: 3px solid #6e44ff;
                padding: 10px;
                border-radius: 4px;
                margin: 8px 0;
                overflow-x: auto;
            }
            a {
                color: #6e9cff;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        """)

    def resizeEvent(self, event):
        """Handle resize events to adjust the message height."""
        super().resizeEvent(event)
        self.adjust_size()

    def sizeHint(self):
        """Provide a size hint based on content."""
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        """Calculate the minimum size hint based on content."""
        doc = self.message_text.document()
        doc.setTextWidth(self.message_text.viewport().width())
        height = doc.size().height() + 60  # Add padding for avatar and margins
        return QSize(200, height)
