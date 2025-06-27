"""
Test script for the LocalizationManager class.

This script provides a simple test application to verify language switching
and translation functionality.
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QComboBox, QLabel, QGroupBox, QFormLayout, QLineEdit, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QCoreApplication

# Add the project root to the Python path
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the LocalizationManager
try:
    from aichat.i18n.localization import init_localization, get_localization, tr
    from aichat.ui.theme_manager import ThemeManager
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

class LocalizationTester(QMainWindow):
    """Test application for LocalizationManager."""
    
    def __init__(self):
        """Initialize the test application."""
        super().__init__()
        
        # Set window properties
        self.setWindowTitle(tr("app.title"))
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Controls
        control_panel = QGroupBox(tr("settings.title"))
        control_layout = QVBoxLayout(control_panel)
        
        # Language selection
        self.locale_manager = get_localization()
        self.language_combo = QComboBox()
        
        # Add available languages to the combo box
        for code, info in self.locale_manager.available_languages.items():
            self.language_combo.addItem(f"{info['name']} ({info['native']})", code)
        
        # Set current language
        current_index = self.language_combo.findData(self.locale_manager.current_language)
        if current_index >= 0:
            self.language_combo.setCurrentIndex(current_index)
        
        # Connect signals
        self.language_combo.currentIndexChanged.connect(self.change_language)
        
        # Theme selection (for testing theme switching with RTL)
        self.theme_manager = ThemeManager(QApplication.instance())
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.theme_manager.theme_names)
        
        # Form layout for settings
        form_layout = QFormLayout()
        form_layout.addRow(tr("settings.language"), self.language_combo)
        form_layout.addRow(tr("settings.theme"), self.theme_combo)
        
        control_layout.addLayout(form_layout)
        
        # Add some test buttons
        self.test_buttons = []
        for i in range(3):
            btn = QPushButton(tr(f"action.button_{i+1}", default=f"Test Button {i+1}"))
            self.test_buttons.append(btn)
            control_layout.addWidget(btn)
        
        # Add a form with various input fields
        self.form_group = QGroupBox(tr("form.title", default="Test Form"))
        form_fields = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.notes_edit = QTextEdit()
        
        form_fields.addRow(tr("form.name", default="Name:"), self.name_edit)
        form_fields.addRow(tr("form.email", default="Email:"), self.email_edit)
        form_fields.addRow(tr("form.notes", default="Notes:"), self.notes_edit)
        
        # Add form buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton(tr("action.save", default="Save"))
        self.cancel_btn = QPushButton(tr("action.cancel", default="Cancel"))
        self.reset_btn = QPushButton(tr("action.reset", default="Reset"))
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.reset_btn)
        
        form_fields.addRow(button_layout)
        self.form_group.setLayout(form_fields)
        
        control_layout.addWidget(self.form_group)
        
        # Add stretch to push everything up
        control_layout.addStretch()
        
        # Right panel - Preview
        preview_panel = QGroupBox(tr("preview.title", default="Preview"))
        preview_layout = QVBoxLayout(preview_panel)
        
        # Add some sample content
        self.preview_label = QLabel(tr("preview.sample_text", 
            default="This is a preview of the selected language and theme."))
        preview_layout.addWidget(self.preview_label)
        
        # Add some styled widgets
        self.preview_buttons = []
        for i in range(3):
            btn = QPushButton(tr(f"preview.button_{i+1}", default=f"Preview Button {i+1}"))
            if i == 0:
                btn.setProperty("class", ["AccentButton"])
            elif i == 1:
                btn.setProperty("class", ["SuccessButton"])
            else:
                btn.setProperty("class", ["DangerButton"])
            self.preview_buttons.append(btn)
            preview_layout.addWidget(btn)
        
        # Add a text area with sample text
        self.sample_text = QTextEdit()
        self.sample_text.setReadOnly(True)
        self.sample_text.setPlainText(tr(
            "preview.sample_content",
            default=("This is a sample text to demonstrate the current language and directionality. "
                   "The text should flow from left to right (LTR) for most languages, "
                   "but from right to left (RTL) for languages like Arabic, Hebrew, and Persian.")
        ))
        preview_layout.addWidget(self.sample_text)
        
        # Add panels to main layout
        main_layout.addWidget(control_panel, 1)
        main_layout.addWidget(preview_panel, 2)
        
        # Connect signals
        self.save_btn.clicked.connect(self.on_save_clicked)
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)
        self.reset_btn.clicked.connect(self.on_reset_clicked)
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        
        # Connect to language changed signal
        self.locale_manager.language_changed.connect(self.on_language_changed)
    
    def change_language(self, index: int):
        """Change the application language."""
        language_code = self.language_combo.currentData()
        if language_code:
            self.locale_manager.set_language(language_code)
    
    def change_theme(self, theme_name: str):
        """Change the application theme."""
        self.theme_manager.set_theme(theme_name)
    
    def on_language_changed(self, language_code: str):
        """Handle language change events."""
        # Update window title
        self.setWindowTitle(tr("app.title"))
        
        # Update control panel title
        self.control_panel.setTitle(tr("settings.title"))
        
        # Update form group title
        self.form_group.setTitle(tr("form.title", default="Test Form"))
        
        # Update preview panel title
        self.preview_panel.setTitle(tr("preview.title", default="Preview"))
        
        # Update preview label
        self.preview_label.setText(tr(
            "preview.sample_text", 
            default="This is a preview of the selected language and theme."
        ))
        
        # Update sample text
        self.sample_text.setPlainText(tr(
            "preview.sample_content",
            default=("This is a sample text to demonstrate the current language and directionality. "
                   "The text should flow from left to right (LTR) for most languages, "
                   "but from right to left (RTL) for languages like Arabic, Hebrew, and Persian.")
        ))
        
        # Update RTL layout if needed
        is_rtl = self.locale_manager.is_rtl()
        self.setLayoutDirection(Qt.RightToLeft if is_rtl else Qt.LeftToRight)
        
        # Update form labels
        self.form_layout.itemAt(0, QFormLayout.LabelRole).widget().setText(tr("form.name", default="Name:"))
        self.form_layout.itemAt(1, QFormLayout.LabelRole).widget().setText(tr("form.email", default="Email:"))
        self.form_layout.itemAt(2, QFormLayout.LabelRole).widget().setText(tr("form.notes", default="Notes:"))
        
        # Update button texts
        self.save_btn.setText(tr("action.save", default="Save"))
        self.cancel_btn.setText(tr("action.cancel", default="Cancel"))
        self.reset_btn.setText(tr("action.reset", default="Reset"))
        
        # Update test buttons
        for i, btn in enumerate(self.test_buttons):
            btn.setText(tr(f"action.button_{i+1}", default=f"Test Button {i+1}"))
        
        # Update preview buttons
        for i, btn in enumerate(self.preview_buttons):
            btn.setText(tr(f"preview.button_{i+1}", default=f"Preview Button {i+1}"))
    
    def on_save_clicked(self):
        """Handle save button click."""
        QMessageBox.information(
            self,
            tr("success.title", default="Success"),
            tr("success.saved", default="Settings saved successfully!")
        )
    
    def on_cancel_clicked(self):
        """Handle cancel button click."""
        reply = QMessageBox.question(
            self,
            tr("confirm.title", default="Confirm"),
            tr("confirm.discard_changes", default="Discard all changes?"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.reset_form()
    
    def on_reset_clicked(self):
        """Handle reset button click."""
        self.reset_form()
    
    def reset_form(self):
        """Reset the form to its default state."""
        self.name_edit.clear()
        self.email_edit.clear()
        self.notes_edit.clear()

def main():
    """Run the localization tester application."""
    app = QApplication(sys.argv)
    
    # Initialize localization
    init_localization(app)
    
    # Create and show the main window
    window = LocalizationTester()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
