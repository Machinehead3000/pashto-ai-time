"""
Profile management dialog for creating and editing AI profiles.
"""
from typing import Optional, Dict, Any, Callable

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QComboBox, QCheckBox, QPushButton, QLabel, QMessageBox,
    QTabWidget, QWidget, QListWidget, QListWidgetItem, QAbstractItemView,
    QInputDialog, QFileDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal

from ..profiles.manager import ProfileManager
from ..profiles.models import Profile, AIModelConfig, UIPreferences, ModelProvider, ModelCapability


class ProfileDialog(QDialog):
    """Dialog for creating and editing AI profiles."""
    
    profile_saved = pyqtSignal(Profile)
    
    def __init__(self, profile_manager: ProfileManager, 
                 profile: Optional[Profile] = None, 
                 parent=None):
        """
        Initialize the profile dialog.
        
        Args:
            profile_manager: Profile manager instance
            profile: Optional profile to edit. If None, creates a new profile.
            parent: Parent widget
        """
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.profile = profile
        self.is_new = profile is None
        
        self.setWindowTitle("Edit Profile" if not self.is_new else "Create Profile")
        self.setMinimumSize(600, 500)
        
        self.init_ui()
        
        if self.profile is None:
            self.profile = Profile(
                id="",
                name="",
                description="",
                is_default=False
            )
        else:
            self.load_profile_data()
    
    def init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # General tab
        self.general_tab = QWidget()
        self.init_general_tab()
        self.tab_widget.addTab(self.general_tab, "General")
        
        # Models tab
        self.models_tab = QWidget()
        self.init_models_tab()
        self.tab_widget.addTab(self.models_tab, "Models")
        
        # UI Preferences tab
        self.ui_tab = QWidget()
        self.init_ui_tab()
        self.tab_widget.addTab(self.ui_tab, "UI Preferences")
        
        # Tools tab
        self.tools_tab = QWidget()
        self.init_tools_tab()
        self.tab_widget.addTab(self.tools_tab, "Tools")
        
        layout.addWidget(self.tab_widget)
        
        # Dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        # Add save button for new profiles
        if self.is_new:
            save_button = QPushButton("Save")
            save_button.clicked.connect(self.save_profile)
            self.button_box.addButton(save_button, QDialogButtonBox.AcceptRole)
        
        layout.addWidget(self.button_box)
    
    def init_general_tab(self) -> None:
        """Initialize the General tab."""
        layout = QFormLayout()
        self.general_tab.setLayout(layout)
        
        # Name
        self.name_edit = QLineEdit()
        layout.addRow("Name:", self.name_edit)
        
        # Description
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        layout.addRow("Description:", self.desc_edit)
        
        # Default profile
        self.default_checkbox = QCheckBox("Set as default profile")
        layout.addRow("", self.default_checkbox)
        
        # Author
        self.author_edit = QLineEdit()
        layout.addRow("Author:", self.author_edit)
    
    def init_models_tab(self) -> None:
        """Initialize the Models tab."""
        layout = QVBoxLayout()
        self.models_tab.setLayout(layout)
        
        # Model list
        self.model_list = QListWidget()
        self.model_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.model_list.itemSelectionChanged.connect(self.on_model_selected)
        layout.addWidget(self.model_list)
        
        # Model buttons
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add Model")
        self.add_btn.clicked.connect(self.add_model)
        btn_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_model)
        self.edit_btn.setEnabled(False)
        btn_layout.addWidget(self.edit_btn)
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_model)
        self.remove_btn.setEnabled(False)
        btn_layout.addWidget(self.remove_btn)
        
        layout.addLayout(btn_layout)
        
        # Model details
        self.model_details = QLabel("Select a model to view or edit its details.")
        self.model_details.setWordWrap(True)
        layout.addWidget(self.model_details)
    
    def init_ui_tab(self) -> None:
        """Initialize the UI Preferences tab."""
        layout = QFormLayout()
        self.ui_tab.setLayout(layout)
        
        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light", "system"])
        layout.addRow("Theme:", self.theme_combo)
        
        # Font family
        self.font_family_edit = QLineEdit()
        layout.addRow("Font Family:", self.font_family_edit)
        
        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(12)
        layout.addRow("Font Size:", self.font_size_spin)
        
        # Show line numbers
        self.line_numbers_check = QCheckBox()
        self.line_numbers_check.setChecked(True)
        layout.addRow("Show Line Numbers:", self.line_numbers_check)
        
        # Word wrap
        self.word_wrap_check = QCheckBox()
        self.word_wrap_check.setChecked(True)
        layout.addRow("Word Wrap:", self.word_wrap_check)
        
        # Auto-save
        self.auto_save_check = QCheckBox()
        self.auto_save_check.setChecked(True)
        layout.addRow("Auto-save:", self.auto_save_check)
        
        # Auto-save interval
        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(10, 600)
        self.auto_save_interval.setValue(60)
        self.auto_save_interval.setSuffix(" seconds")
        layout.addRow("Auto-save Interval:", self.auto_save_interval)
    
    def init_tools_tab(self) -> None:
        """Initialize the Tools tab."""
        layout = QVBoxLayout()
        self.tools_tab.setLayout(layout)
        
        # Available tools list
        self.tools_list = QListWidget()
        self.tools_list.setSelectionMode(QAbstractItemView.MultiSelection)
        
        # Add available tools (this would be dynamic in a real app)
        self.available_tools = [
            "python_interpreter",
            "file_analyzer",
            "web_browser",
            "code_search",
            "document_processor",
            "image_generator",
            "terminal"
        ]
        
        for tool in self.available_tools:
            item = QListWidgetItem(tool)
            self.tools_list.addItem(item)
        
        layout.addWidget(QLabel("Enable tools for this profile:"))
        layout.addWidget(self.tools_list)
    
    def load_profile_data(self) -> None:
        """Load profile data into the UI."""
        if not self.profile:
            return
            
        # General tab
        self.name_edit.setText(self.profile.name)
        self.desc_edit.setPlainText(self.profile.description)
        self.default_checkbox.setChecked(self.profile.is_default)
        self.author_edit.setText(self.profile.author)
        
        # Models tab
        self.update_models_list()
        
        # UI tab
        self.theme_combo.setCurrentText(self.profile.ui_preferences.theme)
        self.font_family_edit.setText(self.profile.ui_preferences.font_family)
        self.font_size_spin.setValue(self.profile.ui_preferences.font_size)
        self.line_numbers_check.setChecked(self.profile.ui_preferences.show_line_numbers)
        self.word_wrap_check.setChecked(self.profile.ui_preferences.word_wrap)
        self.auto_save_check.setChecked(self.profile.ui_preferences.auto_save)
        self.auto_save_interval.setValue(self.profile.ui_preferences.auto_save_interval)
        
        # Tools tab
        for i in range(self.tools_list.count()):
            item = self.tools_list.item(i)
            item.setSelected(item.text() in self.profile.tools_enabled)
    
    def update_models_list(self) -> None:
        """Update the models list widget with current models."""
        self.model_list.clear()
        
        if not self.profile.models:
            return
            
        for model_name, model in self.profile.models.items():
            item = QListWidgetItem(f"{model_name} ({model.provider.value}:{model.model_id})")
            item.setData(Qt.UserRole, model_name)
            self.model_list.addItem(item)
    
    def on_model_selected(self) -> None:
        """Handle model selection change."""
        selected = self.model_list.selectedItems()
        self.edit_btn.setEnabled(len(selected) > 0)
        self.remove_btn.setEnabled(len(selected) > 0)
        
        if not selected:
            self.model_details.setText("Select a model to view or edit its details.")
            return
            
        model_name = selected[0].data(Qt.UserRole)
        model = self.profile.models.get(model_name)
        
        if model:
            details = f"""
            <b>Name:</b> {model.name}<br/>
            <b>Provider:</b> {model.provider.value}<br/>
            <b>Model ID:</b> {model.model_id}<br/>
            <b>Temperature:</b> {model.temperature}<br/>
            <b>Max Tokens:</b> {model.max_tokens}<br/>
            <b>Capabilities:</b> {', '.join(cap.value for cap in model.capabilities)}<br/>
            """
            self.model_details.setText(details)
    
    def add_model(self) -> None:
        """Add a new model to the profile."""
        from .model_dialog import ModelDialog
        
        dialog = ModelDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            model_config = dialog.get_model_config()
            if model_config.name in self.profile.models:
                QMessageBox.warning(
                    self,
                    "Model Exists",
                    f"A model with the name '{model_config.name}' already exists."
                )
                return
                
            self.profile.models[model_config.name] = model_config
            self.update_models_list()
    
    def edit_model(self) -> None:
        """Edit the selected model."""
        selected = self.model_list.selectedItems()
        if not selected:
            return
            
        model_name = selected[0].data(Qt.UserRole)
        model = self.profile.models.get(model_name)
        
        if not model:
            return
            
        from .model_dialog import ModelDialog
        
        dialog = ModelDialog(model=model, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            updated_model = dialog.get_model_config()
            
            # If the name changed, remove the old entry and add the new one
            if updated_model.name != model_name:
                del self.profile.models[model_name]
                
            self.profile.models[updated_model.name] = updated_model
            self.update_models_list()
    
    def remove_model(self) -> None:
        """Remove the selected model."""
        selected = self.model_list.selectedItems()
        if not selected:
            return
            
        model_name = selected[0].data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove the model '{model_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.profile.models[model_name]
            self.update_models_list()
    
    def get_profile_data(self) -> Profile:
        """
        Get the profile data from the UI.
        
        Returns:
            Profile object with data from the UI
        """
        if not self.profile:
            self.profile = Profile(
                id="",
                name="",
                description="",
                is_default=False
            )
        
        # General tab
        self.profile.name = self.name_edit.text().strip()
        self.profile.description = self.desc_edit.toPlainText().strip()
        self.profile.is_default = self.default_checkbox.isChecked()
        self.profile.author = self.author_edit.text().strip()
        
        # UI Preferences
        self.profile.ui_preferences = UIPreferences(
            theme=self.theme_combo.currentText(),
            font_family=self.font_family_edit.text(),
            font_size=self.font_size_spin.value(),
            show_line_numbers=self.line_numbers_check.isChecked(),
            word_wrap=self.word_wrap_check.isChecked(),
            auto_save=self.auto_save_check.isChecked(),
            auto_save_interval=self.auto_save_interval.value()
        )
        
        # Tools
        self.profile.tools_enabled = [
            self.tools_list.item(i).text()
            for i in range(self.tools_list.count())
            if self.tools_list.item(i).isSelected()
        ]
        
        # Models are updated in-place
        
        return self.profile
    
    def accept(self) -> None:
        """Handle dialog acceptance (OK button)."""
        try:
            self.get_profile_data()
            
            # Validate
            if not self.profile.name:
                QMessageBox.warning(self, "Validation Error", "Profile name cannot be empty.")
                return
                
            # Save the profile
            self.profile = self.profile_manager.update_profile(
                self.profile.id,
                **self.profile.to_dict()
            )
            
            # Set as default if requested
            if self.profile.is_default:
                self.profile_manager.set_default_profile(self.profile.id)
            
            self.profile_saved.emit(self.profile)
            super().accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Profile",
                f"An error occurred while saving the profile: {str(e)}"
            )
    
    @staticmethod
    def create_profile(profile_manager: ProfileManager, parent=None) -> Optional[Profile]:
        """
        Show a dialog to create a new profile.
        
        Args:
            profile_manager: Profile manager instance
            parent: Parent widget
            
        Returns:
            The created profile, or None if canceled
        """
        dialog = ProfileDialog(profile_manager, parent=parent)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.profile
        return None
    
    @staticmethod
    def edit_profile(profile_manager: ProfileManager, profile_id: str, parent=None) -> bool:
        """
        Show a dialog to edit an existing profile.
        
        Args:
            profile_manager: Profile manager instance
            profile_id: ID of the profile to edit
            parent: Parent widget
            
        Returns:
            True if the profile was saved, False otherwise
        """
        try:
            profile = profile_manager.get_profile(profile_id)
            dialog = ProfileDialog(profile_manager, profile, parent)
            return dialog.exec_() == QDialog.Accepted
        except Exception as e:
            QMessageBox.critical(
                parent,
                "Error",
                f"Failed to edit profile: {str(e)}"
            )
            return False
