"""
Plugin Manager UI - A graphical interface for managing AI plugins.
"""

from typing import Dict, List, Optional, Callable, Any
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QLabel,
    QPushButton, QTabWidget, QTextEdit, QLineEdit, QFormLayout, QCheckBox,
    QMessageBox, QInputDialog, QComboBox, QGroupBox, QSplitter, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor

from aichat.ai.plugins import get_plugin_manager, AIPlugin
from aichat.utils.resource_loader import load_icon

logger = logging.getLogger(__name__)

class PluginConfigWidget(QWidget):
    """Widget for configuring a single plugin."""
    
    config_updated = pyqtSignal(dict)  # Emitted when plugin config is updated
    
    def __init__(self, plugin: AIPlugin, parent=None):
        """Initialize the plugin config widget.
        
        Args:
            plugin: The plugin to configure.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.plugin = plugin
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Plugin header
        header = QHBoxLayout()
        
        # Plugin icon
        icon_label = QLabel()
        icon_pixmap = QPixmap(64, 64)
        icon_pixmap.fill(QColor(200, 200, 200))
        icon_label.setPixmap(icon_pixmap)
        header.addWidget(icon_label)
        
        # Plugin info
        info_layout = QVBoxLayout()
        self.name_label = QLabel(f"<h2>{self.plugin.name}</h2>")
        self.version_label = QLabel(f"Version: {getattr(self.plugin, 'version', '1.0.0')}")
        self.author_label = QLabel(f"Author: {getattr(self.plugin, 'author', 'Unknown')}")
        
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.version_label)
        info_layout.addWidget(self.author_label)
        info_layout.addStretch()
        
        header.addLayout(info_layout)
        header.addStretch()
        
        # Enable/disable toggle
        self.enable_checkbox = QCheckBox("Enabled")
        self.enable_checkbox.setChecked(self.plugin.enabled)
        self.enable_checkbox.stateChanged.connect(self._on_enable_changed)
        header.addWidget(self.enable_checkbox)
        
        layout.addLayout(header)
        
        # Description
        description = QLabel(getattr(self.plugin, 'description', 'No description available.'))
        description.setWordWrap(True)
        description.setStyleSheet("font-style: italic;")
        layout.addWidget(description)
        
        # Configuration form
        config_group = QGroupBox("Configuration")
        self.config_form = QFormLayout()
        self.config_inputs = {}
        
        # Add configuration fields based on plugin attributes
        config_schema = getattr(self.plugin, 'config_schema', {})
        for field, field_info in config_schema.items():
            label = field_info.get('label', field.replace('_', ' ').title())
            field_type = field_info.get('type', 'string')
            default = getattr(self.plugin, field, field_info.get('default', ''))
            
            if field_type == 'boolean':
                widget = QCheckBox()
                widget.setChecked(bool(default))
            elif field_type == 'select':
                widget = QComboBox()
                options = field_info.get('options', [])
                widget.addItems(options)
                if default in options:
                    widget.setCurrentText(str(default))
            else:  # string, number, etc.
                widget = QLineEdit(str(default))
                if field_type == 'password':
                    widget.setEchoMode(QLineEdit.Password)
            
            self.config_inputs[field] = widget
            self.config_form.addRow(label, widget)
        
        if not self.config_inputs:
            self.config_form.addRow(QLabel("No configuration required."))
        
        config_group.setLayout(self.config_form)
        layout.addWidget(config_group)
        
        # Documentation/Help
        help_text = getattr(self.plugin, '__doc__', 'No documentation available.')
        help_group = QGroupBox("Documentation")
        help_layout = QVBoxLayout()
        help_text_edit = QTextEdit()
        help_text_edit.setReadOnly(True)
        help_text_edit.setHtml(f"<pre>{help_text}</pre>")
        help_layout.addWidget(help_text_edit)
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)
        
        # Save button
        if self.config_inputs:
            save_btn = QPushButton("Save Configuration")
            save_btn.clicked.connect(self._on_save_clicked)
            layout.addWidget(save_btn, alignment=Qt.AlignRight)
        
        layout.addStretch()
    
    def _on_enable_changed(self, state: int) -> None:
        """Handle enable/disable toggle."""
        enabled = state == Qt.Checked
        self.plugin.enabled = enabled
        if enabled:
            self.plugin.on_enable()
        else:
            self.plugin.on_disable()
        
        # Notify parent of config change
        self.config_updated.emit({'enabled': enabled})
    
    def _on_save_clicked(self) -> None:
        """Handle save configuration button click."""
        config = {}
        
        for field, widget in self.config_inputs.items():
            if isinstance(widget, QCheckBox):
                value = widget.isChecked()
            elif isinstance(widget, QComboBox):
                value = widget.currentText()
            else:  # QLineEdit
                value = widget.text()
            
            # Type conversion if needed
            field_type = getattr(self.plugin, 'config_schema', {}).get(field, {}).get('type', 'string')
            if field_type == 'number':
                try:
                    value = float(value) if '.' in value else int(value)
                except ValueError:
                    QMessageBox.warning(self, "Invalid Input", f"Please enter a valid number for {field}")
                    return
            
            config[field] = value
            setattr(self.plugin, field, value)
        
        # Notify parent of config change
        self.config_updated.emit(config)
        
        QMessageBox.information(self, "Success", "Configuration saved successfully!")


class PluginManagerWidget(QWidget):
    """Main plugin manager widget."""
    
    plugin_state_changed = pyqtSignal(str, bool)  # plugin_name, enabled
    
    def __init__(self, parent=None):
        """Initialize the plugin manager."""
        super().__init__(parent)
        self.plugin_widgets = {}
        self._init_ui()
        self._load_plugins()
    
    def _init_ui(self):
        """Initialize the user interface."""
        main_layout = QHBoxLayout(self)
        
        # Left panel - Plugin list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Search/filter
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search plugins...")
        self.search_input.textChanged.connect(self._filter_plugins)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        
        # Plugin list
        self.plugin_list = QListWidget()
        self.plugin_list.setIconSize(QSize(32, 32))
        self.plugin_list.itemSelectionChanged.connect(self._on_plugin_selected)
        
        # Buttons
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_plugins)
        
        install_btn = QPushButton("Install Plugin...")
        install_btn.clicked.connect(self._install_plugin)
        
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(install_btn)
        
        left_layout.addLayout(search_layout)
        left_layout.addWidget(QLabel("Available Plugins:"))
        left_layout.addWidget(self.plugin_list)
        left_layout.addLayout(btn_layout)
        
        # Right panel - Plugin details
        self.details_stack = QStackedWidget()
        
        # Welcome/placeholder widget
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.addWidget(QLabel("<h2>Plugin Manager</h2>"))
        welcome_layout.addWidget(QLabel("Select a plugin from the list to view and configure it."))
        welcome_layout.addStretch()
        
        self.details_stack.addWidget(welcome_widget)
        
        # Splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.details_stack)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
    
    def _load_plugins(self):
        """Load available plugins."""
        self.plugin_list.clear()
        
        # Clear existing plugin widgets
        for i in range(self.details_stack.count() - 1):
            self.details_stack.removeWidget(self.details_stack.widget(1))
        
        self.plugin_widgets = {}
        
        # Get all registered plugins
        plugin_manager = get_plugin_manager()
        
        for plugin_name, plugin in plugin_manager.plugins.items():
            item = QListWidgetItem(plugin_name)
            item.setData(Qt.UserRole, plugin_name)
            
            # Set icon if available
            icon_path = getattr(plugin, 'icon', None)
            if icon_path:
                icon = QIcon(icon_path)
                item.setIcon(icon)
            
            self.plugin_list.addItem(item)
            
            # Create config widget for the plugin
            config_widget = PluginConfigWidget(plugin)
            config_widget.config_updated.connect(
                lambda config, name=plugin_name: self._on_plugin_config_updated(name, config)
            )
            
            self.plugin_widgets[plugin_name] = config_widget
            self.details_stack.addWidget(config_widget)
    
    def _filter_plugins(self, text: str):
        """Filter plugins based on search text."""
        for i in range(self.plugin_list.count()):
            item = self.plugin_list.item(i)
            plugin_name = item.data(Qt.UserRole)
            item.setHidden(text.lower() not in plugin_name.lower())
    
    def _on_plugin_selected(self):
        """Handle plugin selection."""
        selected_items = self.plugin_list.selectedItems()
        if not selected_items:
            self.details_stack.setCurrentIndex(0)  # Show welcome widget
            return
            
        plugin_name = selected_items[0].data(Qt.UserRole)
        if plugin_name in self.plugin_widgets:
            widget = self.plugin_widgets[plugin_name]
            index = self.details_stack.indexOf(widget)
            self.details_stack.setCurrentIndex(index)
    
    def _on_plugin_config_updated(self, plugin_name: str, config: dict):
        """Handle plugin configuration updates."""
        if 'enabled' in config:
            self.plugin_state_changed.emit(plugin_name, config['enabled'])
    
    def _install_plugin(self):
        """Handle install plugin button click."""
        # TODO: Implement plugin installation from file or URL
        QMessageBox.information(
            self,
            "Install Plugin",
            "Plugin installation will be implemented in a future version.",
            QMessageBox.Ok
        )


# Example usage
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # Register some test plugins if needed
    from aichat.ai.plugins.translation import TranslationPlugin
    from aichat.ai.plugins.context import ContextPlugin
    
    app = QApplication(sys.argv)
    
    # Register plugins
    plugin_manager = get_plugin_manager()
    plugin_manager.register_plugin(TranslationPlugin())
    plugin_manager.register_plugin(ContextPlugin())
    
    # Create and show plugin manager
    manager = PluginManagerWidget()
    manager.setWindowTitle("AI Chat - Plugin Manager")
    manager.resize(800, 600)
    manager.show()
    
    sys.exit(app.exec_())
