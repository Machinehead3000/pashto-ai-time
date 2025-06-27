"""
Dialog for creating and editing AI model configurations.
"""
from typing import Optional, Dict, Any, List

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QCheckBox, QPushButton, QLabel, QMessageBox,
    QSpinBox, QDoubleSpinBox, QListWidget, QListWidgetItem, QAbstractItemView,
    QDialogButtonBox, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal

from ..profiles.models import AIModelConfig, ModelProvider, ModelCapability


class ModelDialog(QDialog):
    """Dialog for creating and editing AI model configurations."""
    
    def __init__(self, model: Optional[AIModelConfig] = None, parent=None):
        """
        Initialize the model dialog.
        
        Args:
            model: Optional model configuration to edit. If None, creates a new model.
            parent: Parent widget
        """
        super().__init__(parent)
        self.model = model
        self.is_new = model is None
        
        self.setWindowTitle("Edit Model" if not self.is_new else "Add Model")
        self.setMinimumSize(500, 400)
        
        self.init_ui()
        
        if self.model is not None:
            self.load_model_data()
    
    def init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # General settings group
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout()
        
        # Name
        self.name_edit = QLineEdit()
        general_layout.addRow("Name:", self.name_edit)
        
        # Provider
        self.provider_combo = QComboBox()
        self.provider_combo.addItems([p.value for p in ModelProvider])
        general_layout.addRow("Provider:", self.provider_combo)
        
        # Model ID
        self.model_id_edit = QLineEdit()
        general_layout.addRow("Model ID:", self.model_id_edit)
        
        # API Key Name
        self.api_key_edit = QLineEdit("default")
        general_layout.addRow("API Key Name:", self.api_key_edit)
        
        general_group.setLayout(general_layout)
        
        # Parameters group
        params_group = QGroupBox("Model Parameters")
        params_layout = QFormLayout()
        
        # Temperature
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(0.7)
        params_layout.addRow("Temperature:", self.temp_spin)
        
        # Max Tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 100000)
        self.max_tokens_spin.setValue(2048)
        params_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        # Top P
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.0, 1.0)
        self.top_p_spin.setSingleStep(0.05)
        self.top_p_spin.setValue(1.0)
        params_layout.addRow("Top P:", self.top_p_spin)
        
        # Frequency Penalty
        self.freq_penalty_spin = QDoubleSpinBox()
        self.freq_penalty_spin.setRange(-2.0, 2.0)
        self.freq_penalty_spin.setSingleStep(0.1)
        self.freq_penalty_spin.setValue(0.0)
        params_layout.addRow("Frequency Penalty:", self.freq_penalty_spin)
        
        # Presence Penalty
        self.presence_penalty_spin = QDoubleSpinBox()
        self.presence_penalty_spin.setRange(-2.0, 2.0)
        self.presence_penalty_spin.setSingleStep(0.1)
        self.presence_penalty_spin.setValue(0.0)
        params_layout.addRow("Presence Penalty:", self.presence_penalty_spin)
        
        params_group.setLayout(params_layout)
        
        # Capabilities group
        caps_group = QGroupBox("Capabilities")
        caps_layout = QVBoxLayout()
        
        self.capabilities_list = QListWidget()
        self.capabilities_list.setSelectionMode(QAbstractItemView.MultiSelection)
        
        # Add all capabilities
        for capability in ModelCapability:
            item = QListWidgetItem(capability.value)
            item.setData(Qt.UserRole, capability)
            self.capabilities_list.addItem(item)
        
        caps_layout.addWidget(QLabel("Select capabilities for this model:"))
        caps_layout.addWidget(self.capabilities_list)
        caps_group.setLayout(caps_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        
        # Add all to main layout
        layout.addWidget(general_group)
        layout.addWidget(params_group)
        layout.addWidget(caps_group)
        layout.addWidget(button_box)
    
    def load_model_data(self) -> None:
        """Load model data into the UI."""
        if not self.model:
            return
            
        # General settings
        self.name_edit.setText(self.model.name)
        self.provider_combo.setCurrentText(self.model.provider.value)
        self.model_id_edit.setText(self.model.model_id)
        self.api_key_edit.setText(self.model.api_key_name)
        
        # Parameters
        self.temp_spin.setValue(self.model.temperature)
        self.max_tokens_spin.setValue(self.model.max_tokens)
        self.top_p_spin.setValue(self.model.top_p)
        self.freq_penalty_spin.setValue(self.model.frequency_penalty)
        self.presence_penalty_spin.setValue(self.model.presence_penalty)
        
        # Capabilities
        for i in range(self.capabilities_list.count()):
            item = self.capabilities_list.item(i)
            capability = item.data(Qt.UserRole)
            item.setSelected(capability in self.model.capabilities)
    
    def get_model_config(self) -> AIModelConfig:
        """
        Get the model configuration from the UI.
        
        Returns:
            AIModelConfig object with data from the UI
        """
        # Get capabilities
        capabilities = []
        for i in range(self.capabilities_list.count()):
            item = self.capabilities_list.item(i)
            if item.isSelected():
                capabilities.append(item.data(Qt.UserRole))
        
        # Create or update model config
        if self.model is None:
            self.model = AIModelConfig(
                name=self.name_edit.text().strip(),
                provider=ModelProvider(self.provider_combo.currentText()),
                model_id=self.model_id_edit.text().strip(),
                api_key_name=self.api_key_edit.text().strip(),
                temperature=self.temp_spin.value(),
                max_tokens=self.max_tokens_spin.value(),
                top_p=self.top_p_spin.value(),
                frequency_penalty=self.freq_penalty_spin.value(),
                presence_penalty=self.presence_penalty_spin.value(),
                capabilities=capabilities
            )
        else:
            # Update existing model
            self.model.name = self.name_edit.text().strip()
            self.model.provider = ModelProvider(self.provider_combo.currentText())
            self.model.model_id = self.model_id_edit.text().strip()
            self.model.api_key_name = self.api_key_edit.text().strip()
            self.model.temperature = self.temp_spin.value()
            self.model.max_tokens = self.max_tokens_spin.value()
            self.model.top_p = self.top_p_spin.value()
            self.model.frequency_penalty = self.freq_penalty_spin.value()
            self.model.presence_penalty = self.presence_penalty_spin.value()
            self.model.capabilities = capabilities
        
        return self.model
    
    def validate_and_accept(self) -> None:
        """Validate inputs and accept the dialog if valid."""
        # Validate required fields
        name = self.name_edit.text().strip()
        model_id = self.model_id_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Model name cannot be empty.")
            return
            
        if not model_id:
            QMessageBox.warning(self, "Validation Error", "Model ID cannot be empty.")
            return
            
        # Validate at least one capability is selected
        if not any(self.capabilities_list.item(i).isSelected() 
                  for i in range(self.capabilities_list.count())):
            QMessageBox.warning(
                self, 
                "Validation Error", 
                "Please select at least one capability for the model."
            )
            return
        
        # All valid, accept the dialog
        self.accept()
