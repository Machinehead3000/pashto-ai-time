"""
Test script for the ThemeManager class.

This script provides a simple test application to verify theme switching
and customization functionality.
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton,
    QComboBox, QLabel, QHBoxLayout, QGroupBox, QScrollArea, QColorDialog
)
from PyQt5.QtCore import Qt

# Add the project root to the Python path
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the ThemeManager
try:
    from aichat.ui.theme_manager import ThemeManager
except ImportError as e:
    print(f"Error importing ThemeManager: {e}")
    sys.exit(1)

class ThemeTester(QMainWindow):
    """Test application for ThemeManager."""
    
    def __init__(self):
        """Initialize the test application."""
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("Theme Manager Tester")
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Controls
        control_panel = QGroupBox("Theme Controls")
        control_layout = QVBoxLayout(control_panel)
        
        # Theme selection
        self.theme_combo = QComboBox()
        control_layout.addWidget(QLabel("Select Theme:"))
        control_layout.addWidget(self.theme_combo)
        
        # Add some test buttons
        self.test_buttons = []
        for i in range(5):
            btn = QPushButton(f"Test Button {i+1}")
            self.test_buttons.append(btn)
            control_layout.addWidget(btn)
        
        # Add some styled widgets
        control_layout.addWidget(QLabel("Styled Widgets:"))
        
        # Line edit
        self.line_edit = QLineEdit("Sample text input")
        control_layout.addWidget(self.line_edit)
        
        # Checkbox
        self.checkbox = QCheckBox("Check me")
        control_layout.addWidget(self.checkbox)
        
        # Radio buttons
        radio_group = QGroupBox("Radio Buttons")
        radio_layout = QVBoxLayout(radio_group)
        for i in range(3):
            radio = QRadioButton(f"Option {i+1}")
            if i == 0:
                radio.setChecked(True)
            radio_layout.addWidget(radio)
        control_layout.addWidget(radio_group)
        
        # Add stretch to push everything up
        control_layout.addStretch()
        
        # Right panel - Preview
        preview_panel = QGroupBox("Theme Preview")
        preview_layout = QVBoxLayout(preview_panel)
        
        # Add some sample content
        self.preview_label = QLabel("This is a preview of the selected theme.")
        preview_layout.addWidget(self.preview_label)
        
        # Add some styled widgets
        self.preview_buttons = []
        for i in range(3):
            btn = QPushButton(f"Preview Button {i+1}")
            if i == 0:
                btn.setProperty("class", ["AccentButton"])
            elif i == 1:
                btn.setProperty("class", ["SuccessButton"])
            else:
                btn.setProperty("class", ["DangerButton"])
            self.preview_buttons.append(btn)
            preview_layout.addWidget(btn)
        
        # Add a scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Add some sample text
        for i in range(20):
            label = QLabel(f"Sample text line {i+1}")
            scroll_layout.addWidget(label)
        
        scroll.setWidget(scroll_content)
        preview_layout.addWidget(scroll)
        
        # Add panels to main layout
        main_layout.addWidget(control_panel, 1)
        main_layout.addWidget(preview_panel, 2)
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(QApplication.instance())
        
        # Populate theme combo
        self.update_theme_list()
        
        # Connect signals
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        self.theme_manager.theme_changed.connect(self.on_theme_changed)
    
    def update_theme_list(self):
        """Update the theme list in the combo box."""
        current_theme = self.theme_combo.currentText()
        self.theme_combo.clear()
        
        # Add built-in themes
        self.theme_combo.addItems(self.theme_manager.theme_names)
        
        # Restore selection if possible
        if current_theme and current_theme in self.theme_manager.theme_names:
            self.theme_combo.setCurrentText(current_theme)
        elif self.theme_manager.current_theme:
            self.theme_combo.setCurrentText(self.theme_manager.current_theme)
    
    def change_theme(self, theme_name: str):
        """Change the current theme."""
        self.theme_manager.set_theme(theme_name)
    
    def on_theme_changed(self, theme_name: str):
        """Handle theme change events."""
        self.preview_label.setText(f"Current theme: {theme_name}")
        self.update_theme_list()

def main():
    """Run the theme tester application."""
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = ThemeTester()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
