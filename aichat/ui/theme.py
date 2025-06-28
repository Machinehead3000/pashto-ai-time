import os
import json
import platform
from typing import Dict, Optional, Union, List, Any

from PyQt5.QtCore import Qt, QFile, QTextStream, QObject, pyqtSignal, QSettings
from PyQt5.QtGui import QColor, QPalette, QFont, QFontDatabase, QIcon

# Platform-specific imports
try:
    if platform.system() == 'Windows':
        import winreg
    elif platform.system() == 'Darwin':  # macOS
        from Foundation import NSUserDefaults
    elif platform.system() == 'Linux':
        import subprocess
except ImportError:
    pass

class ThemeManager(QObject):
    # Signal emitted when the theme is changed
    theme_changed = pyqtSignal(str, dict)
    
    # Signal emitted when system theme changes (light/dark)
    system_theme_changed = pyqtSignal(str)  # 'light' or 'dark'
    """Manages application themes and styles."""
    
    THEMES = {
        "dark": {
            "name": "Dark",
            "background": "#1e1e2e",
            "background_secondary": "#2a2a4a",
            "background_tertiary": "#3a3a6a",
            "text_primary": "#f0f4ff",
            "text_secondary": "#c0c4d0",
            "text_tertiary": "#a0a0c0",
            "accent": "#6e44ff",
            "accent_light": "#8d6aff",
            "accent_dark": "#4d22e0",
            "success": "#4caf50",
            "warning": "#ff9800",
            "error": "#f44336",
            "border": "#3a3a6a",
            "border_light": "#4a4a7a",
            "shadow": "rgba(0, 0, 0, 0.3)",
            "highlight": "rgba(110, 68, 255, 0.2)",
            "tooltip_bg": "#2a2a4a",
            "tooltip_text": "#f0f4ff",
            "scrollbar": "#4a4a6a",
            "scrollbar_hover": "#5a5a8a",
            "selection_bg": "#6e44ff",
            "selection_text": "#ffffff",
        },
        "light": {
            "name": "Light",
            "background": "#f8f9fa",
            "background_secondary": "#ffffff",
            "background_tertiary": "#e9ecef",
            "text_primary": "#212529",
            "text_secondary": "#495057",
            "text_tertiary": "#6c757d",
            "accent": "#6e44ff",
            "accent_light": "#8d6aff",
            "accent_dark": "#4d22e0",
            "success": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545",
            "border": "#dee2e6",
            "border_light": "#e9ecef",
            "shadow": "rgba(0, 0, 0, 0.1)",
            "highlight": "rgba(110, 68, 255, 0.1)",
            "tooltip_bg": "#495057",
            "tooltip_text": "#f8f9fa",
            "scrollbar": "#ced4da",
            "scrollbar_hover": "#adb5bd",
            "selection_bg": "#6e44ff",
            "selection_text": "#ffffff",
        },
        "oled": {
            "name": "OLED",
            "background": "#000000",
            "background_secondary": "#0a0a0a",
            "background_tertiary": "#1a1a1a",
            "text_primary": "#f0f4ff",
            "text_secondary": "#c0c4d0",
            "text_tertiary": "#a0a0c0",
            "accent": "#6e44ff",
            "accent_light": "#8d6aff",
            "accent_dark": "#4d22e0",
            "success": "#4caf50",
            "warning": "#ff9800",
            "error": "#f44336",
            "border": "#1a1a1a",
            "border_light": "#2a2a2a",
            "shadow": "rgba(0, 0, 0, 0.5)",
            "highlight": "rgba(110, 68, 255, 0.3)",
            "tooltip_bg": "#1a1a1a",
            "tooltip_text": "#f0f4ff",
            "scrollbar": "#2a2a2a",
            "scrollbar_hover": "#3a3a3a",
            "selection_bg": "#6e44ff",
            "selection_text": "#ffffff",
        },
        "solarized_dark": {
            "name": "Solarized Dark",
            "background": "#002b36",
            "background_secondary": "#073642",
            "background_tertiary": "#0a4b5a",
            "text_primary": "#93a1a1",
            "text_secondary": "#839496",
            "text_tertiary": "#657b83",
            "accent": "#2aa198",
            "accent_light": "#2aa198",
            "accent_dark": "#268bd2",
            "success": "#859900",
            "warning": "#b58900",
            "error": "#dc322f",
            "border": "#073642",
            "border_light": "#0a4b5a",
            "shadow": "rgba(0, 0, 0, 0.3)",
            "highlight": "rgba(42, 161, 152, 0.2)",
            "tooltip_bg": "#073642",
            "tooltip_text": "#93a1a1",
            "scrollbar": "#0a4b5a",
            "scrollbar_hover": "#0d5c6e",
            "selection_bg": "#2aa198",
            "selection_text": "#fdf6e3",
        },
        "nord": {
            "name": "Nord",
            "background": "#2e3440",
            "background_secondary": "#3b4252",
            "background_tertiary": "#4c566a",
            "text_primary": "#e5e9f0",
            "text_secondary": "#d8dee9",
            "text_tertiary": "#81a1c1",
            "accent": "#5e81ac",
            "accent_light": "#81a1c1",
            "accent_dark": "#4c6a8c",
            "success": "#a3be8c",
            "warning": "#ebcb8b",
            "error": "#bf616a",
            "border": "#4c566a",
            "border_light": "#5e677a",
            "shadow": "rgba(0, 0, 0, 0.3)",
            "highlight": "rgba(94, 129, 172, 0.2)",
            "tooltip_bg": "#3b4252",
            "tooltip_text": "#e5e9f0",
            "scrollbar": "#4c566a",
            "scrollbar_hover": "#5e677a",
            "selection_bg": "#5e81ac",
            "selection_text": "#eceff4",
        },
    }
    
    def __init__(self, app, default_theme="auto"):
        """Initialize the theme manager.
        
        Args:
            app: The QApplication instance
            default_theme: The default theme to use, or 'auto' for system theme
        """
        super().__init__(app)
        self.app = app
        self.settings = QSettings("PashtoAI", "ThemeManager")
        self.current_theme = default_theme
        self.custom_themes = {}
        self.load_fonts()
        self._setup_theme_watcher()
    
    def _setup_theme_watcher(self):
        """Set up system theme change detection if available."""
        if platform.system() == 'Windows':
            # Windows 10/11 theme detection
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                )
                # Check every 5 seconds for theme changes
                self.theme_timer = self.startTimer(5000)
            except WindowsError:
                pass
        elif platform.system() == 'Darwin':
            # macOS theme detection
            try:
                self.theme_timer = self.startTimer(5000)
            except Exception:
                pass

    def timerEvent(self, event):
        """Handle timer events for theme change detection."""
        if event.timerId() == getattr(self, 'theme_timer', None):
            current_system_theme = self.get_system_theme()
            if hasattr(self, '_last_system_theme') and self._last_system_theme != current_system_theme:
                self.system_theme_changed.emit(current_system_theme)
                if self.current_theme == 'auto':
                    self.set_theme('auto')
            self._last_system_theme = current_system_theme

    def get_system_theme(self) -> str:
        """Detect the current system theme (light or dark)."""
        if platform.system() == 'Windows':
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                )
                value = winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
                return 'light' if value == 1 else 'dark'
            except (WindowsError, OSError):
                pass
        elif platform.system() == 'Darwin':  # macOS
            try:
                # This requires PyObjC to be installed
                style = NSUserDefaults.standardUserDefaults().stringForKey_('AppleInterfaceStyle')
                return 'dark' if style == 'Dark' else 'light'
            except Exception:
                pass
        elif platform.system() == 'Linux':
            try:
                # Try to use gsettings (GNOME)
                result = subprocess.run(
                    ['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'],
                    capture_output=True, text=True
                )
                if 'dark' in result.stdout.lower():
                    return 'dark'
            except (FileNotFoundError, subprocess.SubprocessError):
                pass
        
        # Default to light theme if detection fails
        return 'light'

    def load_fonts(self):
        """Load custom fonts if available."""
        # Try to load Inter font if available
        font_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts', 'Inter-VariableFont_slnt,wght.ttf'),
            "/usr/share/fonts/Inter/Inter-VariableFont_slnt,wght.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/System/Library/Fonts/SFNSDisplay.ttf"
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                font_id = QFontDatabase.addApplicationFont(path)
                if font_id != -1:  # -1 means font loading failed
                    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                    print(f"Loaded font: {font_family} from {path}")
                    break
        
        # Set default font with fallbacks
        self.default_font = QFont()
        font_db = QFontDatabase()
        available_families = font_db.families()
        if 'Inter' in available_families:
            self.default_font.setFamily('Inter')
        elif 'Segoe UI' in available_families:
            self.default_font.setFamily('Segoe UI')
        elif 'SF Pro Display' in available_families:
            self.default_font.setFamily('SF Pro Display')
        else:
            self.default_font.setFamily('Arial')
        
        self.default_font.setPointSize(10)
        self.app.setFont(self.default_font)
    
    def get_theme(self, theme_name=None) -> Dict[str, Any]:
        """Get a theme by name, or the current theme if None is provided.
        
        Args:
            theme_name: Name of the theme to get, or None for current theme
            
        Returns:
            Dict containing theme properties
        """
        if theme_name is None or theme_name == 'auto':
            theme_name = self.current_theme
        
        if theme_name == 'auto':
            system_theme = self.get_system_theme()
            return self.THEMES.get(system_theme, self.THEMES["dark"])
        
        # Check built-in themes first, then custom themes
        if theme_name in self.THEMES:
            return self.THEMES[theme_name]
        elif theme_name in self.custom_themes:
            return self.custom_themes[theme_name]
        else:
            # Fall back to dark theme if not found
            return self.THEMES.get("dark")
    
    def set_theme(self, theme_name: str) -> bool:
        """Set the current theme and apply it to the application.
        
        Args:
            theme_name: Name of the theme to set, or 'auto' for system theme
            
        Returns:
            bool: True if theme was set successfully, False otherwise
        """
        if theme_name == 'auto':
            theme = self.get_theme('auto')
            theme_name = self.get_system_theme()
        elif theme_name in self.THEMES or theme_name in self.custom_themes:
            theme = self.get_theme(theme_name)
        else:
            print(f"Theme '{theme_name}' not found, using default")
            theme_name = "dark"
            theme = self.THEMES["dark"]
            
        self.current_theme = theme_name
        self.settings.setValue("current_theme", theme_name)
        
        # Set application style
        self.app.setStyle("Fusion")
        
        # Create a palette
        palette = QPalette()
        
        # Base colors
        palette.setColor(QPalette.Window, QColor(theme["background"]))
        palette.setColor(QPalette.WindowText, QColor(theme["text_primary"]))
        palette.setColor(QPalette.Base, QColor(theme["background_secondary"]))
        palette.setColor(QPalette.AlternateBase, QColor(theme["background_tertiary"]))
        palette.setColor(QPalette.ToolTipBase, QColor(theme["tooltip_bg"]))
        palette.setColor(QPalette.ToolTipText, QColor(theme["tooltip_text"]))
        palette.setColor(QPalette.Text, QColor(theme["text_primary"]))
        palette.setColor(QPalette.Button, QColor(theme["background_secondary"]))
        palette.setColor(QPalette.ButtonText, QColor(theme["text_primary"]))
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(theme["accent"]))
        palette.setColor(QPalette.Highlight, QColor(theme["accent"]))
        palette.setColor(QPalette.HighlightedText, QColor(theme["selection_text"]))
        
        # Disabled colors
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(theme["text_tertiary"]))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(theme["text_tertiary"]))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(theme["text_tertiary"]))
        
        # Set the palette
        self.app.setPalette(palette)
        
        # Set application font
        font = QFont("Inter" if "Inter" in QFontDatabase.families() else "Segoe UI")
        font.setPointSize(10)
        self.app.setFont(font)
        
        # Apply stylesheet
        self._apply_stylesheet(theme)
    
    def load_custom_theme(self, file_path: str) -> bool:
        """Load a custom theme from a JSON file.
        
        Args:
            file_path: Path to the JSON theme file
            
        Returns:
            bool: True if theme was loaded successfully, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
            
            # Validate theme data
            required_fields = {
                'name', 'background', 'background_secondary', 'text_primary',
                'accent', 'accent_light', 'accent_dark', 'success', 'warning', 'error'
            }
            
            if not all(field in theme_data for field in required_fields):
                print("Invalid theme: Missing required fields")
                return False
                
            theme_name = os.path.splitext(os.path.basename(file_path))[0]
            self.custom_themes[theme_name] = theme_data
            self.settings.beginGroup("CustomThemes")
            self.settings.setValue(theme_name, file_path)
            self.settings.endGroup()
            
            return True
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading theme from {file_path}: {e}")
            return False
    
    def get_available_themes(self) -> Dict[str, str]:
        """Get a dictionary of available theme names and their display names.
        
        Returns:
            Dict[str, str]: Dictionary mapping theme IDs to display names
        """
        themes = {
            'auto': 'System Theme',
            **{k: v['name'] for k, v in self.THEMES.items()},
            **{k: v.get('name', k) for k, v in self.custom_themes.items()}
        }
        return themes
    
    def generate_theme_preview(self, theme_name: str, size=(200, 100)) -> str:
        """Generate an HTML/CSS preview of a theme.
        
        Args:
            theme_name: Name of the theme to preview
            size: Tuple of (width, height) for the preview
            
        Returns:
            str: HTML/CSS string for the preview
        """
        theme = self.get_theme(theme_name)
        width, height = size
        
        return f"""
        <div style="
            width: {width}px;
            height: {height}px;
            background: {theme['background']};
            border: 1px solid {theme['border']};
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        ">
            <div style="
                background: {theme['background_secondary']};
                padding: 8px;
                color: {theme['text_primary']};
                font-weight: bold;
                border-bottom: 1px solid {theme['border']};
            ">
                {theme.get('name', theme_name).title()}
            </div>
            <div style="
                flex: 1;
                padding: 8px;
                display: flex;
                flex-direction: column;
                gap: 4px;
            ">
                <div style="
                    background: {theme['accent']};
                    height: 12px;
                    border-radius: 2px;
                    width: 80%;
                "></div>
                <div style="
                    background: {theme['background_tertiary']};
                    height: 8px;
                    border-radius: 2px;
                    width: 60%;
                "></div>
                <div style="
                    background: {theme['success']};
                    height: 4px;
                    border-radius: 2px;
                    width: 40%;
                    margin-top: 8px;
                "></div>
                <div style="
                    background: {theme['warning']};
                    height: 4px;
                    border-radius: 2px;
                    width: 30%;
                "></div>
                <div style="
                    background: {theme['error']};
                    height: 4px;
                    border-radius: 2px;
                    width: 20%;
                "></div>
            </div>
        </div>
        """
    
    def _apply_stylesheet(self, theme: Dict[str, str]) -> None:
        """Apply the stylesheet for the current theme.
        
        Args:
            theme: Dictionary containing theme properties
        """
        # Generate CSS variables for easier theming
        css_vars = '\n'.join(f'    --{k.replace("_", "-")}: {v};' for k, v in theme.items())
        
        # Base stylesheet with CSS variables
        stylesheet = f"""
        /* CSS Variables for theming */
        :root {{
{css_vars}
        }}
        
        /* Base styles */
            /* Global Styles */
            QWidget {{
                color: {theme['text_primary']};
                selection-background-color: {theme['selection_bg']};
                selection-color: {theme['selection_text']};
            }}
            
            /* Scroll Bars */
            QScrollBar:vertical {{
                border: none;
                background: {theme['background_secondary']};
                width: 8px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {theme['scrollbar']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {theme['scrollbar_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            
            /* Buttons */
            QPushButton {{
                background-color: {theme['background_tertiary']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {theme['accent']};
                border-color: {theme['accent_light']};
            }}
            QPushButton:pressed {{
                background-color: {theme['accent_dark']};
            }}
            QPushButton:disabled {{
                background-color: {theme['background_secondary']};
                color: {theme['text_tertiary']};
                border-color: {theme['border']};
            }}
            
            /* Line Edits */
            QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
                background-color: {theme['background_secondary']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
                padding: 6px 8px;
                selection-background-color: {theme['accent']};
                selection-color: {theme['selection_text']};
            }}
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, 
            QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 1px solid {theme['accent']};
            }}
            
            /* Tabs */
            QTabBar::tab {{
                background: {theme['background_secondary']};
                color: {theme['text_secondary']};
                border: 1px solid {theme['border']};
                border-bottom: none;
                padding: 6px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected, QTabBar::tab:hover {{
                background: {theme['background']};
                color: {theme['text_primary']};
                border-bottom: 2px solid {theme['accent']};
            }}
            QTabWidget::pane {{
                border: 1px solid {theme['border']};
                border-top: none;
                border-radius: 0 0 4px 4px;
            }}
            
            /* Tool Tips */
            QToolTip {{
                background-color: var(--tooltip-bg);
                color: var(--tooltip-text);
                border: 1px solid var(--border);
                padding: 6px 8px;
                border-radius: 4px;
                opacity: 240;
            }}
            
            /* Checkboxes and Radio Buttons */
            QCheckBox, QRadioButton {{
                spacing: 6px;
            }}
            QCheckBox::indicator, QRadioButton::indicator {{
                width: 16px;
                height: 16px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 1px solid var(--border);
                background: var(--background-secondary);
            }}
            QCheckBox::indicator:checked {{
                border: 1px solid var(--accent);
                background: var(--accent);
            }}
            QRadioButton::indicator:unchecked {{
                border: 1px solid var(--border);
                background: var(--background-secondary);
                border-radius: 8px;
            }}
            QRadioButton::indicator:checked {{
                border: 1px solid var(--accent);
                background: var(--accent);
                border-radius: 8px;
            }}
            
            /* Progress Bars */
            QProgressBar {{
                border: 1px solid var(--border);
                border-radius: 4px;
                text-align: center;
                background: var(--background-secondary);
            }}
            QProgressBar::chunk {{
                background: var(--accent);
                border-radius: 2px;
                margin: 1px;
            }}
            
            /* Group Boxes */
            QGroupBox {{
                border: 1px solid var(--border);
                border-radius: 4px;
                margin-top: 1em;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }}
            
            /* Accessibility: High Contrast Mode */
            .high-contrast * {{
                border: 1px solid var(--text-primary) !important;
            }}
            
            /* Reduced Motion */
            @media (prefers-reduced-motion: reduce) {{
                * {{
                    transition: none !important;
                    animation: none !important;
                }}
            }}
            QToolTip {{
                background-color: {theme['tooltip_bg']};
                color: {theme['tooltip_text']};
                border: 1px solid {theme['border']};
                padding: 4px 8px;
                border-radius: 4px;
            }}
            
            /* Menu Bar */
            QMenuBar {{
                background-color: {theme['background_secondary']};
                color: {theme['text_primary']};
                border-bottom: 1px solid {theme['border']};
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 4px 8px;
            }}
            QMenuBar::item:selected {{
                background: {theme['highlight']};
                border-radius: 4px;
            }}
            QMenu {{
                background-color: {theme['background_secondary']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border']};
                padding: 4px;
            }}
            QMenu::item:selected {{
                background: {theme['highlight']};
                border-radius: 2px;
            }}
            
            /* Status Bar */
            QStatusBar {{
                background: {theme['background_secondary']};
                color: {theme['text_secondary']};
                border-top: 1px solid {theme['border']};
            }}
            
            /* Dialogs */
            QDialog {{
                background: {theme['background']};
            }}
            QDialogButtonBox {{
                border-top: 1px solid {theme['border']};
                padding: 8px;
            }}
            
            /* Custom Widgets */
            #chatContainer, #inputArea, #modelSelector {{
                border: 1px solid {theme['border']};
                border-radius: 8px;
                background: {theme['background_secondary']};
            }}
            
            /* Custom Scroll Areas */
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            
            /* Custom Buttons */
            .primary-button {{
                background: {theme['accent']};
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }}
            .primary-button:hover {{
                background: {theme['accent_light']};
            }}
            .primary-button:pressed {{
                background: {theme['accent_dark']};
            }}
            
            /* Success, Warning, Error */
            .success {{
                color: {theme['success']};
            }}
            .warning {{
                color: {theme['warning']};
            }}
            .error {{
                color: {theme['error']};
            }}
            
            /* Custom Widgets */
            .message-user {{
                background: {theme['accent']}20;
                border-left: 3px solid {theme['accent']};
                border-radius: 0 8px 8px 0;
                margin: 4px 0;
                padding: 8px 12px;
            }}
            .message-ai {{
                background: {theme['background_tertiary']};
                border-radius: 8px 0 0 8px;
                margin: 4px 0;
                padding: 8px 12px;
            }}
        """
        
        # Apply the stylesheet
        self.app.setStyleSheet(stylesheet)
        
        # Emit theme changed signal
        self.theme_changed.emit(self.current_theme, theme)
        
        # Notify system of theme change for platform integration
        if platform.system() == 'Windows':
            try:
                # This helps with Windows 10/11 taskbar and title bar theming
                from ctypes import windll
                hwnd = self.app.activeWindow().winId() if self.app.activeWindow() else 0
                if hwnd:
                    windll.user32.SetWindowTheme(hwnd, 'DarkMode_Explorer' if self.current_theme == 'dark' else 'Explorer', None)
            except Exception:
                pass
