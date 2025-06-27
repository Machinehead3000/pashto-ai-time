"""Image generation dialog for the Pashto AI application."""
import os
from typing import Optional, Dict, Any

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QSpinBox, QCheckBox, QGroupBox, QFileDialog, QMessageBox,
    QTextEdit, QSizePolicy, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QIcon, QFont, QTextCursor

from ...multimodal import MultiModalProcessor


class ImageGenerationDialog(QDialog):
    """Dialog for generating images using AI models."""
    
    # Signal emitted when an image is successfully generated
    image_generated = pyqtSignal(str)  # path to generated image
    
    def __init__(self, parent=None, multimodal_processor: Optional[MultiModalProcessor] = None):
        """Initialize the image generation dialog.
        
        Args:
            parent: Parent widget
            multimodal_processor: Instance of MultiModalProcessor for image generation
        """
        super().__init__(parent)
        self.multimodal_processor = multimodal_processor
        self.generated_image_path = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Generate Image with AI")
        self.setMinimumSize(700, 800)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Prompt group
        prompt_group = QGroupBox("Image Prompt")
        prompt_layout = QVBoxLayout()
        
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("Describe the image you want to generate...")
        self.prompt_edit.setMinimumHeight(100)
        prompt_layout.addWidget(self.prompt_edit)
        
        # Negative prompt
        self.negative_prompt_edit = QTextEdit()
        self.negative_prompt_edit.setPlaceholderText("Elements to avoid in the generated image (optional)...")
        self.negative_prompt_edit.setMaximumHeight(80)
        prompt_layout.addWidget(QLabel("Avoid:"))
        prompt_layout.addWidget(self.negative_prompt_edit)
        
        prompt_group.setLayout(prompt_layout)
        
        # Settings group
        settings_group = QGroupBox("Generation Settings")
        settings_layout = QVBoxLayout()
        
        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["DALL-E 3", "Stable Diffusion XL", "Midjourney"])
        model_layout.addWidget(self.model_combo)
        settings_layout.addLayout(model_layout)
        
        # Size selection
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Size:"))
        self.size_combo = QComboBox()
        self.size_combo.addItems(["1024x1024 (Square)", "1792x1024 (Wide)", "1024x1792 (Tall)"])
        size_layout.addWidget(self.size_combo)
        settings_layout.addLayout(size_layout)
        
        # Quality and style (for DALL-E 3)
        quality_style_layout = QHBoxLayout()
        
        quality_layout = QVBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Standard", "HD"])
        quality_layout.addWidget(self.quality_combo)
        
        style_layout = QVBoxLayout()
        style_layout.addWidget(QLabel("Style:"))
        self.style_combo = QComboBox()
        self.style_combo.addItems(["Vivid", "Natural"])
        style_layout.addWidget(self.style_combo)
        
        quality_style_layout.addLayout(quality_layout)
        quality_style_layout.addLayout(style_layout)
        settings_layout.addLayout(quality_style_layout)
        
        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_group.setCheckable(True)
        advanced_group.setChecked(False)
        advanced_layout = QVBoxLayout()
        
        # Number of images
        num_images_layout = QHBoxLayout()
        num_images_layout.addWidget(QLabel("Number of images:"))
        self.num_images_spin = QSpinBox()
        self.num_images_spin.setRange(1, 4)
        self.num_images_spin.setValue(1)
        num_images_layout.addWidget(self.num_images_spin)
        advanced_layout.addLayout(num_images_layout)
        
        # Seed
        seed_layout = QHBoxLayout()
        self.seed_check = QCheckBox("Set random seed:")
        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 2**32 - 1)
        self.seed_spin.setEnabled(False)
        self.seed_check.toggled.connect(self.seed_spin.setEnabled)
        seed_layout.addWidget(self.seed_check)
        seed_layout.addWidget(self.seed_spin)
        seed_layout.addStretch()
        advanced_layout.addLayout(seed_layout)
        
        advanced_group.setLayout(advanced_layout)
        settings_layout.addWidget(advanced_group)
        settings_group.setLayout(settings_layout)
        
        # Preview area
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(300)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a2e;
                border: 2px dashed #2a2a4a;
                border-radius: 8px;
                color: #6e6e8e;
                font-style: italic;
            }
        """)
        self.preview_label.setText("Generated image will appear here")
        preview_layout.addWidget(self.preview_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        preview_layout.addWidget(self.progress_bar)
        
        preview_group.setLayout(preview_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate Image")
        self.generate_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_MediaPlay')))
        self.generate_btn.clicked.connect(self.generate_image)
        
        self.save_btn = QPushButton("Save Image")
        self.save_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_DialogSaveButton')))
        self.save_btn.clicked.connect(self.save_image)
        self.save_btn.setEnabled(False)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        # Add all to main layout
        layout.addWidget(prompt_group)
        layout.addWidget(settings_group)
        layout.addWidget(preview_group, 1)  # Allow preview to expand
        layout.addLayout(button_layout)
        
        # Connect model change to update UI
        self.model_combo.currentTextChanged.connect(self.update_ui_for_model)
        
        # Set initial UI state
        self.update_ui_for_model()
    
    def update_ui_for_model(self):
        """Update UI elements based on selected model."""
        model = self.model_combo.currentText()
        
        # Enable/disable DALL-E 3 specific options
        is_dalle = "DALL-E" in model
        self.quality_combo.setEnabled(is_dalle)
        self.style_combo.setEnabled(is_dalle)
    
    def generate_image(self):
        """Generate an image based on the current settings."""
        if not self.multimodal_processor:
            QMessageBox.critical(self, "Error", "Image generation is not available.")
            return
        
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Missing Prompt", "Please enter a description for the image you want to generate.")
            return
        
        # Prepare generation parameters
        params = {
            "prompt": prompt,
            "model": self.model_combo.currentText().lower().replace(" ", "-"),
            "size": self.size_combo.currentText().split(" ")[0],
            "num_images": self.num_images_spin.value(),
        }
        
        # Add optional parameters
        if negative_prompt := self.negative_prompt_edit.toPlainText().strip():
            params["negative_prompt"] = negative_prompt
        
        if self.seed_check.isChecked():
            params["seed"] = self.seed_spin.value()
        
        # DALL-E 3 specific
        if "dall-e" in params["model"]:
            params["quality"] = self.quality_combo.currentText().lower()
            params["style"] = self.style_combo.currentText().lower()
        
        # Disable UI during generation
        self.set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Generate in a separate thread to keep UI responsive
        from threading import Thread
        
        def generation_thread():
            try:
                # Call the MultiModalProcessor to generate the image
                result = self.multimodal_processor.generate_image(**params)
                
                # Handle the result on the main thread
                if "error" in result:
                    self.show_error.emit(f"Failed to generate image: {result['error']}")
                else:
                    self.generation_complete.emit(result["image_path"])
            except Exception as e:
                self.show_error.emit(f"Error during image generation: {str(e)}")
            finally:
                self.generation_finished.emit()
        
        # Create signals for thread communication
        self.show_error = pyqtSignal(str)
        self.generation_complete = pyqtSignal(str)
        self.generation_finished = pyqtSignal()
        
        # Connect signals
        self.show_error.connect(lambda msg: QMessageBox.critical(self, "Error", msg))
        self.generation_complete.connect(self.on_generation_complete)
        self.generation_finished.connect(self.on_generation_finished)
        
        # Start the generation thread
        self.generation_thread = Thread(target=generation_thread, daemon=True)
        self.generation_thread.start()
    
    def on_generation_complete(self, image_path: str):
        """Handle successful image generation."""
        self.generated_image_path = image_path
        self.preview_image(image_path)
        self.save_btn.setEnabled(True)
        
        # Emit signal that image was generated
        self.image_generated.emit(image_path)
    
    def on_generation_finished(self):
        """Clean up after generation completes."""
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
    
    def preview_image(self, image_path: str):
        """Display the generated image in the preview area."""
        if not os.path.exists(image_path):
            return
            
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale pixmap to fit the preview while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load image: {str(e)}")
    
    def save_image(self):
        """Save the generated image to a file."""
        if not self.generated_image_path or not os.path.exists(self.generated_image_path):
            QMessageBox.warning(self, "No Image", "No image to save.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image As",
            "",
            "PNG Images (*.png);;JPEG Images (*.jpg *.jpeg);;All Files (*)"
        )
        
        if file_path:
            try:
                import shutil
                shutil.copy2(self.generated_image_path, file_path)
                QMessageBox.information(self, "Success", f"Image saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save image: {str(e)}")
    
    def set_ui_enabled(self, enabled: bool):
        """Enable or disable UI elements during generation."""
        self.generate_btn.setEnabled(enabled)
        self.save_btn.setEnabled(enabled and bool(self.generated_image_path))
        self.prompt_edit.setEnabled(enabled)
        self.negative_prompt_edit.setEnabled(enabled)
        self.model_combo.setEnabled(enabled)
        self.size_combo.setEnabled(enabled)
        self.quality_combo.setEnabled(enabled and "DALL-E" in self.model_combo.currentText())
        self.style_combo.setEnabled(enabled and "DALL-E" in self.model_combo.currentText())
        self.num_images_spin.setEnabled(enabled)
        self.seed_check.setEnabled(enabled)
        self.seed_spin.setEnabled(enabled and self.seed_check.isChecked())
    
    def resizeEvent(self, event):
        """Handle window resize events to update the preview."""
        super().resizeEvent(event)
        if hasattr(self, 'generated_image_path') and self.generated_image_path:
            self.preview_image(self.generated_image_path)
