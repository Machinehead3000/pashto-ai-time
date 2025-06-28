from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPainterPath

class TypingDot(QWidget):
    """A single animated dot in the typing indicator."""
    
    def __init__(self, parent=None, delay=0):
        super().__init__(parent)
        self.setFixedSize(10, 10)
        self.opacity = 0.3
        self.delay = delay
        self.animation = None
        self.start_animation()
    
    def start_animation(self):
        """Start the bounce animation with a delay."""
        if self.delay > 0:
            QTimer.singleShot(self.delay, self._start_animation_impl)
        else:
            self._start_animation_impl()
    
    def _start_animation_impl(self):
        """Start the actual animation."""
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(1000)
        self.animation.setStartValue(0.3)
        self.animation.setKeyValueAt(0.5, 1.0)
        self.animation.setEndValue(0.3)
        self.animation.setLoopCount(-1)  # Loop forever
        self.animation.start()
    
    def get_opacity(self):
        """Get the current opacity."""
        return self.opacity
    
    def set_opacity(self, value):
        """Set the opacity and trigger a repaint."""
        self.opacity = value
        self.update()
    
    def paintEvent(self, event):
        """Paint the dot with the current opacity."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw dot with current opacity
        color = QColor(110, 68, 255)
        color.setAlphaF(self.opacity)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        
        # Draw a rounded dot
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 5, 5)
        painter.fillPath(path, color)
    
    opacity = property(get_opacity, set_opacity)

class TypingIndicator(QWidget):
    """A typing indicator that shows animated dots."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(0)
        
        # Container for the dots
        self.dots_container = QWidget()
        dots_layout = QHBoxLayout(self.dots_container)
        dots_layout.setContentsMargins(12, 8, 12, 8)
        dots_layout.setSpacing(6)
        
        # Add dots with staggered delays
        self.dots = []
        for i in range(3):
            dot = TypingDot(delay=i * 150)
            self.dots.append(dot)
            dots_layout.addWidget(dot)
        
        # Add container to layout
        layout.addWidget(self.dots_container)
        
        # Style
        self.setStyleSheet("""
            QWidget {
                background: rgba(74, 74, 106, 0.3);
                border-radius: 16px;
                max-width: 80px;
                margin: 8px 0 8px 12px;
            }
        """)
    
    def start_animation(self):
        """Start the typing animation."""
        for dot in self.dots:
            dot.start_animation()
    
    def stop_animation(self):
        """Stop the typing animation."""
        for dot in self.dots:
            if dot.animation:
                dot.animation.stop()
    
    def showEvent(self, event):
        """Start animation when shown."""
        super().showEvent(event)
        self.start_animation()
    
    def hideEvent(self, event):
        """Stop animation when hidden."""
        super().hideEvent(event)
        self.stop_animation()
    
    def sizeHint(self):
        """Provide a size hint."""
        return QSize(80, 40)
