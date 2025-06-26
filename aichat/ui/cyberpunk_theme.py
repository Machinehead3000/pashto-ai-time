"""
Cyberpunk theme for the AI Chat application.
"""
from PyQt5.QtGui import QColor, QPalette, QFont, QFontDatabase
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QTextEdit, QScrollBar, QComboBox

def load_cyberpunk_fonts():
    """Load and register cyberpunk fonts if available."""
    try:
        # Try to load some cyberpunk-style fonts if they're available
        font_paths = [
            "C:/Windows/Fonts/Orbitron-Bold.ttf",
            "C:/Windows/Fonts/Rajdhani-Medium.ttf",
            "C:/Windows/Fonts/Aldrich-Regular.ttf",
        ]
        
        for font_path in font_paths:
            try:
                QFontDatabase.addApplicationFont(font_path)
            except:
                pass
    except:
        pass

def apply_cyberpunk_theme(app):
    """Apply cyberpunk theme to the application."""
    # Load fonts
    load_cyberpunk_fonts()
    
    # Define colors
    colors = {
        'background': '#0a0a12',
        'darker_bg': '#050508',
        'lighter_bg': '#12121e',
        'text': '#e0e0ff',
        'bright_text': '#ffffff',
        'accent': '#00f0ff',  # Cyan
        'accent_glow': 'rgba(0, 240, 255, 0.3)',
        'accent_dark': '#008c99',
        'pink': '#ff00ff',
        'pink_glow': 'rgba(255, 0, 255, 0.3)',
        'purple': '#9d00ff',
        'red': '#ff0055',
        'yellow': '#ffcc00',
        'border': '#2a2a4a',
        'border_light': '#4a4a7a',
        'scroll_handle': '#4a4a7a',
        'scroll_bg': '#12121e',
    }
    
    # Set application-wide stylesheet
    app.setStyleSheet(f"""
        /* Base styles */
        QWidget {{
            color: {colors['text']};
            background-color: {colors['background']};
            font-family: 'Segoe UI', 'Arial', sans-serif;
            font-size: 13px;
            selection-background-color: {colors['accent']};
            selection-color: {colors['darker_bg']};
        }}
        
        /* Main window */
        QMainWindow, QDialog {{
            background-color: {colors['background']};
            border: 1px solid {colors['accent']};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: transparent;
            color: {colors['bright_text']};
            border: 1px solid {colors['accent']};
            border-radius: 4px;
            padding: 6px 15px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            min-width: 80px;
        }}
        
        QPushButton:hover {{
            background-color: {colors['accent']};
            color: {colors['darker_bg']};
            border: 1px solid {colors['accent']};
            box-shadow: 0 0 10px {colors['accent_glow']};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['accent_dark']};
            border: 1px solid {colors['accent_dark']};
        }}
        
        QPushButton:disabled {{
            background-color: #1a1a2a;
            color: #6a6a8a;
            border: 1px solid #2a2a4a;
        }}
        
        /* Text edits */
        QTextEdit, QPlainTextEdit, QLineEdit {{
            background-color: {colors['darker_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 8px;
            selection-background-color: {colors['accent']};
            selection-color: {colors['darker_bg']};
            font-family: 'Consolas', 'Monaco', monospace;
        }}
        
        QTextEdit:focus, QPlainTextEdit:focus, QLineEdit:focus {{
            border: 1px solid {colors['accent']};
            box-shadow: 0 0 8px {colors['accent_glow']};
        }}
        
        /* Scroll bars */
        QScrollBar:vertical {{
            background: {colors['scroll_bg']};
            width: 12px;
            margin: 0px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {colors['scroll_handle']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {colors['accent']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        
        /* Combo boxes */
        QComboBox {{
            background-color: {colors['darker_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 5px 10px;
            min-width: 100px;
        }}
        
        QComboBox:hover {{
            border: 1px solid {colors['accent']};
        }}
        
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid {colors['border']};
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px;
        }}
        
        QComboBox::down-arrow {{
            image: url(down_arrow.png);
            width: 12px;
            height: 12px;
        }}
        
        QComboBox QAbstractItemView {{
            background: {colors['darker_bg']};
            color: {colors['text']};
            selection-background-color: {colors['accent']};
            selection-color: {colors['darker_bg']};
            border: 1px solid {colors['accent']};
            outline: none;
        }}
        
        /* Menu bar */
        QMenuBar {{
            background-color: {colors['darker_bg']};
            color: {colors['text']};
            border-bottom: 1px solid {colors['accent']};
            padding: 2px;
        }}
        
        QMenuBar::item {{
            background: transparent;
            padding: 5px 10px;
            border-radius: 4px;
        }}
        
        QMenuBar::item:selected {{
            background: {colors['accent']};
            color: {colors['darker_bg']};
        }}
        
        QMenuBar::item:pressed {{
            background: {colors['accent_dark']};
        }}
        
        /* Menus */
        QMenu {{
            background-color: {colors['darker_bg']};
            color: {colors['text']};
            border: 1px solid {colors['accent']};
            padding: 5px;
        }}
        
        QMenu::item:selected {{
            background-color: {colors['accent']};
            color: {colors['darker_bg']};
        }}
        
        /* Tabs */
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            border-top: none;
            background: {colors['darker_bg']};
        }}
        
        QTabBar::tab {{
            background: {colors['darker_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 5px 10px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected, QTabBar::tab:hover {{
            background: {colors['accent']};
            color: {colors['darker_bg']};
        }}
        
        /* Tool tips */
        QToolTip {{
            background-color: {colors['accent']};
            color: {colors['darker_bg']};
            border: 1px solid {colors['accent']};
            padding: 5px;
            border-radius: 4px;
            font-size: 12px;
        }}
        
        /* Status bar */
        QStatusBar {{
            background: {colors['darker_bg']};
            color: {colors['text']};
            border-top: 1px solid {colors['accent']};
        }}
        
        /* Custom widgets */
        .message-user {{
            background-color: {colors['accent']};
            color: {colors['darker_bg']};
            border-radius: 15px;
            border-bottom-right-radius: 5px;
            padding: 10px 15px;
            margin: 5px 20px 5px 100px;
        }}
        
        .message-assistant {{
            background-color: {colors['lighter_bg']};
            color: {colors['text']};
            border: 1px solid {colors['accent']};
            border-radius: 15px;
            border-bottom-left-radius: 5px;
            padding: 10px 15px;
            margin: 5px 100px 5px 20px;
        }}
        
        .typing-indicator {{
            color: {colors['accent']};
            font-style: italic;
            margin: 5px 20px;
        }}
        
        /* Custom animations */
        @keyframes glow {{
            0% {{ box-shadow: 0 0 5px {colors['accent_glow']}; }}
            50% {{ box-shadow: 0 0 20px {colors['accent_glow']}; }}
            100% {{ box-shadow: 0 0 5px {colors['accent_glow']}; }}
        }}
        
        .glow-effect {{
            animation: glow 2s infinite;
        }}
    """)
    
    # Set application palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(colors['background']))
    palette.setColor(QPalette.WindowText, QColor(colors['text']))
    palette.setColor(QPalette.Base, QColor(colors['darker_bg']))
    palette.setColor(QPalette.AlternateBase, QColor(colors['lighter_bg']))
    palette.setColor(QPalette.ToolTipBase, QColor(colors['accent']))
    palette.setColor(QPalette.ToolTipText, QColor(colors['darker_bg']))
    palette.setColor(QPalette.Text, QColor(colors['text']))
    palette.setColor(QPalette.Button, QColor(colors['darker_bg']))
    palette.setColor(QPalette.ButtonText, QColor(colors['text']))
    palette.setColor(QPalette.BrightText, QColor(colors['pink']))
    palette.setColor(QPalette.Highlight, QColor(colors['accent']))
    palette.setColor(QPalette.HighlightedText, QColor(colors['darker_bg']))
    
    app.setPalette(palette)
    
    # Set application font
    font = QFont()
    font_family = "Orbitron"
    if font_family in QFontDatabase().families():
        font.setFamily(font_family)
    else:
        font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)
