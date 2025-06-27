"""
Stylesheet generation for the application.

This module provides functions to generate Qt stylesheets based on theme data.
"""

def generate_stylesheet(theme: dict) -> str:
    """
    Generate a complete stylesheet for the application based on the theme.
    
    Args:
        theme: Theme data dictionary
        
    Returns:
        str: Generated stylesheet
    """
    colors = theme['colors']
    sizes = theme['sizes']
    
    return f"""
    /* Base styles */
    QWidget {{
        background-color: {colors['window']};
        color: {colors['text']};
        selection-background-color: {colors['selection']};
        selection-color: {colors['selection_text']};
        border-radius: {sizes['border_radius']}px;
    }}
    
    /* Buttons */
    QPushButton {{
        background-color: {colors['button']};
        color: {colors['button_text']};
        border: 1px solid {colors['border']};
        border-radius: {sizes['border_radius']}px;
        padding: {sizes['padding']/2}px {sizes['padding']}px;
        min-width: 80px;
    }}
    
    QPushButton:hover {{
        background-color: {colors['hover']};
    }}
    
    QPushButton:pressed {{
        background-color: {colors['pressed']};
    }}
    
    QPushButton:disabled {{
        background-color: {colors['disabled_button']};
        color: {colors['disabled_text']};
        border-color: {colors['border']};
    }}
    
    /* Line edits */
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QDateTimeEdit, QTimeEdit, QCompleter {{
        background-color: {colors['base']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        border-radius: {sizes['border_radius']}px;
        padding: {sizes['padding']/2}px;
        selection-background-color: {colors['highlight']};
        selection-color: {colors['highlighted_text']};
    }}
    
    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
        background-color: {colors['alternate_base']};
        color: {colors['disabled_text']};
    }}
    
    /* Scrollbars */
    QScrollBar:vertical {{
        border: none;
        background: {colors['alternate_base']};
        width: 12px;
        margin: 0px 0px 0px 0px;
    }}
    
    QScrollBar::handle:vertical {{
        background: {colors['button']};
        min-height: 20px;
        border-radius: 6px;
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    
    /* Tabs */
    QTabBar::tab {{
        background: {colors['button']};
        color: {colors['button_text']};
        padding: 6px 12px;
        margin-right: 2px;
        border: 1px solid {colors['border']};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    
    QTabBar::tab:selected, QTabBar::tab:hover {{
        background: {colors['window']};
        color: {colors['text']};
    }}
    
    QTabWidget::pane {{
        border: 1px solid {colors['border']};
        top: -1px;
    }}
    
    /* Tooltips */
    QToolTip {{
        background-color: {colors['tool_tip_base']};
        color: {colors['tool_tip_text']};
        border: 1px solid {colors['border']};
        padding: 4px;
        border-radius: {sizes['border_radius']}px;
    }}
    
    /* Menu bar */
    QMenuBar {{
        background-color: {colors['window']};
        color: {colors['text']};
    }}
    
    QMenuBar::item:selected {{
        background-color: {colors['highlight']};
        color: {colors['highlighted_text']};
    }}
    
    QMenu {{
        background-color: {colors['window']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        padding: 4px;
    }}
    
    QMenu::item:selected {{
        background-color: {colors['highlight']};
        color: {colors['highlighted_text']};
    }}
    
    /* Status bar */
    QStatusBar {{
        background-color: {colors['alternate_base']};
        color: {colors['text']};
        border-top: 1px solid {colors['border']};
    }}
    
    /* Group boxes */
    QGroupBox {{
        border: 1px solid {colors['border']};
        border-radius: {sizes['border_radius']}px;
        margin-top: 1.5em;
        padding-top: 0.5em;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 3px;
    }}
    
    /* Checkboxes and radio buttons */
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 16px;
        height: 16px;
    }}
    
    QCheckBox::indicator:unchecked {{
        border: 1px solid {colors['border']};
        background: {colors['base']};
    }}
    
    QCheckBox::indicator:checked {{
        border: 1px solid {colors['highlight']};
        background: {colors['highlight']};
    }}
    
    QRadioButton::indicator:unchecked {{
        border: 1px solid {colors['border']};
        background: {colors['base']};
        border-radius: 7px;
    }}
    
    QRadioButton::indicator:checked {{
        border: 1px solid {colors['highlight']};
        background: {colors['highlight']};
        border-radius: 7px;
    }}
    
    /* Progress bar */
    QProgressBar {{
        border: 1px solid {colors['border']};
        border-radius: 3px;
        text-align: center;
    }}
    
    QProgressBar::chunk {{
        background-color: {colors['highlight']};
        width: 10px;
        margin: 0.5px;
    }}
    
    /* Slider */
    QSlider::groove:horizontal {{
        border: 1px solid {colors['border']};
        height: 8px;
        background: {colors['base']};
        margin: 2px 0;
        border-radius: 4px;
    }}
    
    QSlider::handle:horizontal {{
        background: {colors['highlight']};
        border: 1px solid {colors['highlight']};
        width: 16px;
        margin: -4px 0;
        border-radius: 8px;
    }}
    
    /* Scroll area */
    QScrollArea {{
        border: 1px solid {colors['border']};
        border-radius: {sizes['border_radius']}px;
        background: {colors['base']};
    }}
    
    /* Splitter */
    QSplitter::handle {{
        background: {colors['border']};
        width: 1px;
    }}
    
    QSplitter::handle:hover {{
        background: {colors['highlight']};
    }}
    
    /* Table and tree views */
    QHeaderView::section {{
        background-color: {colors['alternate_base']};
        color: {colors['text']};
        padding: 4px;
        border: 1px solid {colors['border']};
    }}
    
    QTreeView, QTableView, QListWidget, QTreeWidget {{
        background-color: {colors['base']};
        alternate-background-color: {colors['alternate_base']};
        border: 1px solid {colors['border']};
        border-radius: {sizes['border_radius']}px;
    }}
    
    QTreeView::item:selected, QTableView::item:selected, QListWidget::item:selected, QTreeWidget::item:selected {{
        background-color: {colors['highlight']};
        color: {colors['highlighted_text']};
    }}
    
    /* Toolbar */
    QToolBar {{
        background-color: {colors['alternate_base']};
        border: none;
        spacing: 4px;
        padding: 4px;
    }}
    
    QToolButton {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: 3px;
        padding: 3px;
    }}
    
    QToolButton:hover, QToolButton:checked {{
        background: {colors['hover']};
        border: 1px solid {colors['border']};
    }}
    
    QToolButton:pressed {{
        background: {colors['pressed']};
    }}
    
    /* Dialogs */
    QDialog {{
        background-color: {colors['window']};
    }}
    
    QDialogButtonBox {{
        border-top: 1px solid {colors['border']};
        padding: 10px;
    }}
    
    /* Custom widgets */
    .TitleBar {{
        background-color: {colors['titlebar']};
        color: {colors['titlebar_text']};
        padding: 4px;
        border-bottom: 1px solid {colors['border']};
    }}
    
    .StatusBar {{
        background-color: {colors['alternate_base']};
        border-top: 1px solid {colors['border']};
        padding: 2px 8px;
    }}
    
    .Card {{
        background-color: {colors['base']};
        border: 1px solid {colors['border']};
        border-radius: {sizes['border_radius']}px;
        padding: {sizes['padding']}px;
        margin: {sizes['margin']/2}px 0;
    }}
    
    .AccentButton {{
        background-color: {colors['accent']};
        color: white;
        font-weight: bold;
        border: none;
        border-radius: {sizes['border_radius']}px;
        padding: 6px 12px;
    }}
    
    .AccentButton:hover {{
        background-color: {colors['accent_light']};
    }}
    
    .AccentButton:pressed {{
        background-color: {colors['accent_dark']};
    }}
    
    .DangerButton {{
        background-color: {colors['error']};
        color: white;
        font-weight: bold;
        border: none;
        border-radius: {sizes['border_radius']}px;
        padding: 6px 12px;
    }}
    
    .DangerButton:hover {{
        background-color: #c82333;
    }}
    
    .SuccessButton {{
        background-color: {colors['success']};
        color: white;
        font-weight: bold;
        border: none;
        border-radius: {sizes['border_radius']}px;
        padding: 6px 12px;
    }}
    
    .SuccessButton:hover {{
        background-color: #218838;
    }}
    
    .WarningButton {{
        background-color: {colors['warning']};
        color: #212529;
        font-weight: bold;
        border: none;
        border-radius: {sizes['border_radius']}px;
        padding: 6px 12px;
    }}
    
    .WarningButton:hover {{
        background-color: #e0a800;
    }}
    
    /* Custom scroll area that doesn't show scrollbars until needed */
    .AutoScrollArea QScrollBar:vertical {{
        width: 0px;
    }}
    
    .AutoScrollArea QScrollBar:horizontal {{
        height: 0px;
    }}
    
    .AutoScrollArea:hover QScrollBar:vertical {{
        width: 12px;
    }}
    
    .AutoScrollArea:hover QScrollBar:horizontal {{
        height: 12px;
    }}
    
    /* Custom tab widget with no frame */
    .NoFrameTabWidget::pane {{
        border: none;
        top: 0px;
    }}
    
    /* Custom line edit with search icon */
    .SearchLineEdit {{
        padding-left: 20px;
        background-image: url(:/icons/search.png);
        background-position: left center;
        background-repeat: no-repeat;
        background-origin: content;
        padding-left: 30px;
    }}
    
    /* Custom message boxes */
    .MessageBoxIcon {{
        qproperty-pixmap: url(:/icons/info.png);
    }}
    
    .MessageBoxWarning .MessageBoxIcon {{
        qproperty-pixmap: url(:/icons/warning.png);
    }}
    
    .MessageBoxCritical .MessageBoxIcon {{
        qproperty-pixmap: url(:/icons/error.png);
    }}
    
    .MessageBoxQuestion .MessageBoxIcon {{
        qproperty-pixmap: url(:/icons/question.png);
    }}
    
    /* Custom tool buttons */
    .ToolButton {{
        border: none;
        background: transparent;
        padding: 4px;
        border-radius: 3px;
    }}
    
    .ToolButton:hover {{
        background: {colors['hover']};
    }}
    
    .ToolButton:pressed {{
        background: {colors['pressed']};
    }}
    
    .ToolButton:disabled {{
        opacity: 0.5;
    }}
    """
