from typing import Dict, Any, Optional

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLabel, QToolButton, QMenu, QSizePolicy,
    QFrame, QVBoxLayout, QSpacerItem, QStyledItemDelegate, QStyle
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect, QEvent
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QLinearGradient, QFont, QFontMetrics

class ModelSelector(QComboBox):
    """Dropdown for selecting AI models with rich information display."""
    
    model_changed = pyqtSignal(str)  # Signal emitted when model is changed
    
    def __init__(self, models: Dict[str, Dict[str, Any]] = None, parent=None):
        """Initialize the model selector.
        
        Args:
            models: Dictionary of model IDs to model info
            parent: Parent widget
        """
        super().__init__(parent)
        self.models = models or {}
        self.setup_ui()
        
        # Set up tooltip timer
        self.tooltip_timer = QTimer(self)
        self.tooltip_timer.setSingleShot(True)
        self.tooltip_timer.setInterval(500)  # 500ms delay before showing tooltip
        self.tooltip_timer.timeout.connect(self.show_model_tooltip)
        
        # Connect events
        self.view().viewport().installEventFilter(self)
    
    def setup_ui(self):
        """Set up the model selector UI."""
        self.setMinimumWidth(250)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Set item delegate for custom rendering
        self.setItemDelegate(ModelItemDelegate())
        
        # Configure view
        self.view().setMinimumWidth(300)
        self.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Populate models
        self.populate_models()
        
        # Connect signals
        self.currentIndexChanged.connect(self._on_model_changed)
    
    def update_models(self, models: Dict[str, Dict[str, Any]]):
        """Update the list of available models."""
        self.models = models or {}
        self.populate_models()
    
    def populate_models(self):
        """Populate the dropdown with available models."""
        current_model = self.currentData()
        self.blockSignals(True)
        
        try:
            self.clear()
            
            if not self.models:
                self.addItem("No models available", None)
                self.setEnabled(False)
                return
                
            self.setEnabled(True)
            
            # Sort models by provider and then by name
            sorted_models = sorted(
                self.models.items(),
                key=lambda x: (x[1].get('provider', 'Other').lower(), 
                             x[1].get('name', x[0]).lower())
            )
            
            current_provider = None
            for model_id, model_info in sorted_models:
                provider = model_info.get('provider', 'Other')
                
                # Add model with rich data
                display_name = model_info.get('name', model_id)
                description = model_info.get('description', 'No description available')
                context = model_info.get('context_window', 'N/A')
                
                # Create model data dict
                model_data = {
                    'id': model_id,
                    'name': display_name,
                    'provider': provider,
                    'description': description,
                    'context_window': context,
                    'supports_images': model_info.get('supports_images', False),
                    'supports_code': model_info.get('supports_code', False)
                }
                
                self.addItem(display_name, model_data)
                
                # Set item tooltip
                idx = self.count() - 1
                self.setItemData(idx, self._create_tooltip(model_data), Qt.ToolTipRole)
                
                # Set item icon based on provider
                provider_icon = self._get_provider_icon(provider)
                if provider_icon:
                    self.setItemIcon(idx, provider_icon)
            
            # Restore selection if possible
            if current_model:
                idx = self.findData(current_model, Qt.UserRole)
                if idx >= 0:
                    self.setCurrentIndex(idx)
                    
        finally:
            self.blockSignals(False)
    
    def _create_tooltip(self, model_data: Dict[str, Any]) -> str:
        """Create a rich tooltip for a model."""
        return f"""
        <b>{model_data['name']}</b><br>
        <small>Provider: {model_data['provider']}</small><br>
        <p>{model_data['description']}</p>
        <table>
            <tr><td><b>Context:</b></td><td>{model_data['context_window']} tokens</td></tr>
            <tr><td><b>Images:</b></td><td>{'✓' if model_data['supports_images'] else '✗'}</td></tr>
            <tr><td><b>Code:</b></td><td>{'✓' if model_data['supports_code'] else '✗'}</td></tr>
        </table>
        <small><i>ID: {model_data['id']}</i></small>
        """
    
    def _get_provider_icon(self, provider: str) -> Optional[QIcon]:
        """Get icon for a provider."""
        provider_icons = {
            'OpenAI': ':/icons/openai',
            'Anthropic': ':/icons/anthropic',
            'Meta': ':/icons/meta',
            'Mistral AI': ':/icons/mistral',
            'Google': ':/icons/google',
        }
        icon_path = provider_icons.get(provider)
        return QIcon(icon_path) if icon_path and QIcon.hasThemeIcon(icon_path) else None
    
    def eventFilter(self, source, event):
        """Handle hover events for tooltips."""
        if event.type() == QEvent.ToolTip and source is self.view().viewport():
            index = self.view().indexAt(event.pos())
            if index.isValid():
                self.tooltip_timer.start()
                return True
        return super().eventFilter(source, event)
    
    def show_model_tooltip(self):
        """Show tooltip for the currently hovered model."""
        index = self.view().currentIndex()
        if index.isValid():
            tooltip = self.itemData(index, Qt.ToolTipRole)
            if tooltip:
                QToolTip.showText(
                    QCursor.pos(), 
                    tooltip, 
                    self,
                    self.view().visualRect(index),
                    3000  # Show for 3 seconds
                )
    
    def set_current_model(self, model_id: str):
        """Set the currently selected model.
        
        Args:
            model_id: ID of the model to select
        """
        for i in range(self.count()):
            model_data = self.itemData(i)
            if model_data and model_data.get('id') == model_id:
                self.setCurrentIndex(i)
                return
    
    def _on_model_changed(self, index: int):
        """Handle model selection change."""
        if index < 0:
            return
            
        model_data = self.itemData(index)
        if model_data and 'id' in model_data:
            self.model_changed.emit(model_data['id'])
            
    def current_model_id(self) -> Optional[str]:
        """Get the ID of the currently selected model."""
        model_data = self.currentData()
        return model_data.get('id') if isinstance(model_data, dict) else None


class ModelItemDelegate(QStyledItemDelegate):
    """Custom item delegate for rendering model items with rich text."""
    
    def paint(self, painter, option, index):
        """Paint the item with custom formatting."""
        # Let the base class handle the basic painting
        super().paint(painter, option, index)
        
        # Get model data
        model_data = index.data(Qt.UserRole)
        if not isinstance(model_data, dict):
            return
            
        # Set up painter
        painter.save()
        
        # Draw provider badge
        provider = model_data.get('provider', 'Unknown')
        if provider:
            # Calculate text metrics
            font_metrics = QFontMetrics(option.font)
            text_rect = option.rect.adjusted(5, 5, -5, -5)
            
            # Draw provider name in the top-right corner
            provider_rect = QRect(
                option.rect.right() - font_metrics.horizontalAdvance(provider) - 10,
                option.rect.top() + 2,
                font_metrics.horizontalAdvance(provider) + 6,
                font_metrics.height()
            )
            
            # Draw background
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(240, 240, 240) if option.state & QStyle.State_Selected else QColor(230, 230, 230))
            painter.drawRoundedRect(provider_rect, 3, 3)
            
            # Draw text
            painter.setPen(Qt.darkGray)
            painter.drawText(provider_rect, Qt.AlignCenter, provider)
        
        painter.restore()
    
    def sizeHint(self, option, index):
        """Provide size hint for items."""
        size = super().sizeHint(option, index)
        return QSize(size.width(), size.height() + 10)  # Add some vertical padding


class ModelSelectorWidget(QWidget):
    """A dropdown for selecting AI models with additional controls."""
    
    model_changed = pyqtSignal(str)  # Emitted when model is changed
    
    def __init__(self, models, parent=None):
        """Initialize the model selector.
        
        Args:
            models: Dictionary of model IDs to display names
            parent: Parent widget
        """
        super().__init__(parent)
        self.setObjectName("modelSelector")
        self.models = models
        self.current_model = None
        self.setup_ui()
        self.setup_styles()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        # Model icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setPixmap(self._get_model_icon(""))
        
        # Model dropdown
        self.model_combo = ModelSelector(self.models)
        self.model_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.model_combo.setMinimumWidth(200)
        
        # Info button
        self.info_btn = QToolButton()
        self.info_btn.setIcon(QIcon.fromTheme("help-about"))
        self.info_btn.setToolTip("Model Information")
        self.info_btn.setCursor(Qt.PointingHandCursor)
        self.info_btn.clicked.connect(self.show_model_info)
        
        # Settings button
        self.settings_btn = QToolButton()
        self.settings_btn.setIcon(QIcon.fromTheme("preferences-system"))
        self.settings_btn.setToolTip("Model Settings")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.clicked.connect(self.show_model_settings)
        
        # Add widgets to layout
        layout.addWidget(self.icon_label)
        layout.addWidget(self.model_combo, 1)
        layout.addWidget(self.info_btn)
        layout.addWidget(self.settings_btn)
        
        # Connect signals
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        
        # Set initial model
        if self.model_combo.count() > 0:
            self.model_combo.setCurrentIndex(0)
    
    def setup_styles(self):
        """Set up the widget styles."""
        self.setStyleSheet("""
            #modelSelector {
                background: #1e1e2e;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
            }
            QComboBox {
                background: transparent;
                border: 1px solid transparent;
                color: #f0f4ff;
                padding: 6px 12px;
                min-height: 24px;
            }
            QComboBox:hover {
                background: rgba(110, 68, 255, 0.1);
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: url(:/icons/arrow-down);
                width: 16px;
                height: 16px;
            }
            QComboBox QAbstractItemView {
                background: #1e1e2e;
                border: 1px solid #2a2a4a;
                border-radius: 6px;
                padding: 4px;
                outline: none;
                selection-background-color: #6e44ff;
                selection-color: white;
            }
            QToolButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px;
            }
            QToolButton:hover {
                background: rgba(110, 68, 255, 0.2);
            }
        """)
    
    def _get_model_icon(self, model_id):
        """Get the icon for a model."""
        # Default icon
        icon_path = ":/icons/robot"
        
        # Map model IDs to icons
        model_icons = {
            "gpt-4": ":/icons/openai",
            "gpt-3.5": ":/icons/openai",
            "claude": ":/icons/anthropic",
            "llama": ":/icons/llama",
            "mistral": ":/icons/mistral",
        }
        
        # Find matching icon
        for key, icon in model_icons.items():
            if key in model_id.lower():
                icon_path = icon
                break
        
        # Create and return icon
        pixmap = QPixmap(icon_path)
        if pixmap.isNull():
            # Fallback to a default icon if the specified one doesn't exist
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw a gradient circle with the first letter of the model
            gradient = QLinearGradient(0, 0, 24, 24)
            gradient.setColorAt(0, QColor(110, 68, 255))
            gradient.setColorAt(1, QColor(157, 122, 255))
            
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, 24, 24)
            
            # Draw text
            painter.setPen(Qt.white)
            font = painter.font()
            font.setBold(True)
            font.setPixelSize(12)
            painter.setFont(font)
            
            # Use first letter of model ID or '?' if empty
            text = model_id[0].upper() if model_id else '?'
            painter.drawText(0, 0, 24, 24, Qt.AlignCenter, text)
            painter.end()
        
        return pixmap
    
    def _on_model_changed(self, index):
        """Handle model selection change."""
        if index >= 0:
            model_id = self.model_combo.itemData(index)
            self.current_model = model_id
            self.icon_label.setPixmap(self._get_model_icon(model_id))
            self.model_changed.emit(model_id)
    
    def get_current_model(self):
        """Get the currently selected model ID."""
        return self.current_model
    
    def set_current_model(self, model_id):
        """Set the current model by ID."""
        index = self.model_combo.findData(model_id)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
    
    def show_model_info(self):
        """Show information about the current model."""
        if not self.current_model:
            return
            
        model_info = self.models.get(self.current_model, {})
        info_text = f"""
        <h3>{model_info.get('display', self.current_model)}</h3>
        <p><b>Provider:</b> {model_info.get('provider', 'Unknown')}</p>
        <p><b>Context:</b> {model_info.get('context', 'N/A')} tokens</p>
        <p><b>Description:</b> {model_info.get('description', 'No description available.')}</p>
        """
        
        from PyQt5.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setWindowTitle("Model Information")
        msg.setTextFormat(Qt.RichText)
        msg.setText(info_text)
        msg.setIconPixmap(self._get_model_icon(self.current_model).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        msg.exec_()
    
    def show_model_settings(self):
        """Show settings dialog for the current model."""
        # This would open a dialog with model-specific settings
        # For now, just show a message
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Model Settings",
            f"Settings for {self.current_model} would appear here.\n\n"
            "This could include temperature, max tokens, top_p, etc."
        )
