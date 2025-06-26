"""
Settings dialog for the AI Chat application.
"""
from typing import Dict, Any, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QSpinBox, QDoubleSpinBox, QFormLayout, QCheckBox,
    QGroupBox, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal

class SettingsDialog(QDialog):
    """Dialog for application settings."""
    
    settings_updated = pyqtSignal(dict)  # Signal emitted when settings are saved
    
    def __init__(self, current_settings: Optional[Dict[str, Any]] = None, parent=None):
        """Initialize the settings dialog.
        
        Args:
            current_settings: Dictionary of current settings
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("SYSTEM SETTINGS")
        self.setFixedSize(600, 500)
        
        # Default settings
        self.default_settings = {
            "theme": "cyberpunk",
            "font_size": 12,
            "max_tokens": 2048,
            "temperature": 0.7,
            "top_p": 0.9,
            "stream_responses": True,
            "show_timestamps": True,
            "show_typing_indicator": True,
        }
        
        # Use provided settings or defaults
        self.current_settings = current_settings or {}
        self.settings = {**self.default_settings, **self.current_settings}
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Set dialog style
        self.setStyleSheet("""
            QDialog {
                background-color: #0a0a12;
                color: #e0e0ff;
                font-family: 'Consolas', 'Monaco', monospace;
            }
            QLabel {
                color: #a0a0c0;
            }
            QGroupBox::title {
                color: #00f0ff;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        # Scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #0a0a12;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #00f0ff;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Container widget for scroll area
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        
        # Main form layout
        form_layout = QVBoxLayout(container)
        form_layout.setContentsMargins(5, 5, 15, 5)
        form_layout.setSpacing(20)
        
        # Appearance Group
        appearance_group = QGroupBox("APPEARANCE")
        appearance_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #00f0ff;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
        """)
        
        appearance_layout = QFormLayout()
        appearance_layout.setContentsMargins(15, 15, 15, 15)
        appearance_layout.setSpacing(10)
        
        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["cyberpunk", "dark", "light"])
        self.theme_combo.setCurrentText(self.settings["theme"])
        self.theme_combo.setStyleSheet("""
            QComboBox {
                background: #0a0a12;
                color: #e0e0ff;
                border: 1px solid #00f0ff;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 150px;
            }
            QComboBox:hover {
                border: 1px solid #ff00ff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
        """)
        appearance_layout.addRow("Theme:", self.theme_combo)
        
        # Font Size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(self.settings["font_size"])
        self.font_size_spin.setStyleSheet("""
            QSpinBox {
                background: #0a0a12;
                color: #e0e0ff;
                border: 1px solid #00f0ff;
                border-radius: 4px;
                padding: 5px;
                min-width: 60px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                border: none;
            }
        """)
        appearance_layout.addRow("Font Size:", self.font_size_spin)
        
        appearance_group.setLayout(appearance_layout)
        
        # AI Settings Group
        ai_group = QGroupBox("AI SETTINGS")
        ai_group.setStyleSheet(appearance_group.styleSheet())
        
        ai_layout = QFormLayout()
        ai_layout.setContentsMargins(15, 15, 15, 15)
        ai_layout.setSpacing(10)
        
        # Max Tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 4096)
        self.max_tokens_spin.setValue(self.settings["max_tokens"])
        self.max_tokens_spin.setStyleSheet(self.font_size_spin.styleSheet())
        ai_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        # Temperature
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.1, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(self.settings["temperature"])
        self.temp_spin.setStyleSheet(self.font_size_spin.styleSheet())
        ai_layout.addRow("Temperature:", self.temp_spin)
        
        # Top P
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.1, 1.0)
        self.top_p_spin.setSingleStep(0.1)
        self.top_p_spin.setValue(self.settings["top_p"])
        self.top_p_spin.setStyleSheet(self.font_size_spin.styleSheet())
        ai_layout.addRow("Top P:", self.top_p_spin)
        
        ai_group.setLayout(ai_layout)
        
        # Chat Settings Group
        chat_group = QGroupBox("CHAT SETTINGS")
        chat_group.setStyleSheet(appearance_group.styleSheet())
        
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(15, 15, 15, 15)
        chat_layout.setSpacing(10)
        
        # Stream Responses
        self.stream_check = QCheckBox("Stream responses")
        self.stream_check.setChecked(self.settings["stream_responses"])
        chat_layout.addWidget(self.stream_check)
        
        # Show Timestamps
        self.timestamps_check = QCheckBox("Show message timestamps")
        self.timestamps_check.setChecked(self.settings["show_timestamps"])
        chat_layout.addWidget(self.timestamps_check)
        
        # Show Typing Indicator
        self.typing_check = QCheckBox("Show typing indicator")
        self.typing_check.setChecked(self.settings["show_typing_indicator"])
        chat_layout.addWidget(self.typing_check)
        
        chat_group.setLayout(chat_layout)
        
        # Add groups to form
        form_layout.addWidget(appearance_group)
        form_layout.addWidget(ai_group)
        form_layout.addWidget(chat_group)
        form_layout.addStretch()
        
        # Set scroll widget
        scroll.setWidget(container)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Reset Button
        self.reset_btn = QPushButton("DEFAULT")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #00f0ff;
                border: 1px solid #00f0ff;
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: rgba(0, 240, 255, 0.1);
                border: 1px solid #ff00ff;
                color: #ff00ff;
            }
            QPushButton:pressed {
                background: rgba(255, 0, 255, 0.2);
            }
        """)
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        
        # Cancel Button
        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ff5555;
                border: 1px solid #ff5555;
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: rgba(255, 85, 85, 0.1);
                border: 1px solid #ff9999;
                color: #ff9999;
            }
            QPushButton:pressed {
                background: rgba(255, 85, 85, 0.2);
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        # Save Button
        self.save_btn = QPushButton("SAVE CHANGES")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                          stop:0 #ff00ff, stop:1 #00f0ff);
                color: #0a0a12;
                border: none;
                border-radius: 4px;
                padding: 8px 25px;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 1px;
                min-width: 150px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #ff69b4, stop:1 #00c8d7);
                box-shadow: 0 0 15px rgba(0, 240, 255, 0.5);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #cc00cc, stop:1 #008c99);
            }
        """)
        self.save_btn.clicked.connect(self.accept)
        
        # Add buttons to layout
        buttons_layout.addWidget(self.reset_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.save_btn)
        
        # Add widgets to main layout
        main_layout.addWidget(scroll)
        main_layout.addLayout(buttons_layout)
        
        # Set main layout
        self.setLayout(main_layout)
        
        # Apply cyberpunk style to checkboxes
        checkbox_style = """
            QCheckBox {
                color: #e0e0ff;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #00f0ff;
                border-radius: 3px;
                background: #0a0a12;
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                          stop:0 #ff00ff, stop:1 #00f0ff);
                border: 1px solid #00f0ff;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #ff00ff;
            }
        """
        
        for checkbox in [self.stream_check, self.timestamps_check, self.typing_check]:
            checkbox.setStyleSheet(checkbox_style)
    
    def get_settings(self) -> Dict[str, Any]:
        """Get the current settings from the UI."""
        return {
            "theme": self.theme_combo.currentText(),
            "font_size": self.font_size_spin.value(),
            "max_tokens": self.max_tokens_spin.value(),
            "temperature": self.temp_spin.value(),
            "top_p": self.top_p_spin.value(),
            "stream_responses": self.stream_check.isChecked(),
            "show_timestamps": self.timestamps_check.isChecked(),
            "show_typing_indicator": self.typing_check.isChecked(),
        }
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        self.theme_combo.setCurrentText(self.default_settings["theme"])
        self.font_size_spin.setValue(self.default_settings["font_size"])
        self.max_tokens_spin.setValue(self.default_settings["max_tokens"])
        self.temp_spin.setValue(self.default_settings["temperature"])
        self.top_p_spin.setValue(self.default_settings["top_p"])
        self.stream_check.setChecked(self.default_settings["stream_responses"])
        self.timestamps_check.setChecked(self.default_settings["show_timestamps"])
        self.typing_check.setChecked(self.default_settings["show_typing_indicator"])
    
    def accept(self):
        """Handle dialog accept (Save button)."""
        self.settings = self.get_settings()
        self.settings_updated.emit(self.settings)
        super().accept()
