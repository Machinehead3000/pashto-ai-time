"""
Resource Loader - Utility for loading application resources like icons and images.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any
from PyQt5.QtGui import QIcon, QPixmap, QColor, QFont, QFontDatabase
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import Qt, QByteArray, QBuffer, QIODevice, QSize

logger = logging.getLogger(__name__)

class ResourceLoader:
    """Handles loading and caching of application resources."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Create a singleton instance."""
        if cls._instance is None:
            cls._instance = super(ResourceLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the resource loader."""
        if self._initialized:
            return
            
        self._resource_dirs = []
        self._icon_cache = {}
        self._pixmap_cache = {}
        self._font_cache = {}
        self._svg_renderer_cache = {}
        
        # Add default resource directories
        self.add_resource_dir('resources')
        
        # If running from a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            self.add_resource_dir(os.path.join(sys._MEIPASS, 'resources'))
        
        self._initialized = True
    
    def add_resource_dir(self, path: Union[str, Path]) -> bool:
        """Add a directory to search for resources.
        
        Args:
            path: Path to the resource directory.
            
        Returns:
            bool: True if directory was added, False otherwise.
        """
        try:
            path = Path(path).resolve()
            if path.is_dir() and path not in self._resource_dirs:
                self._resource_dirs.append(path)
                logger.debug(f"Added resource directory: {path}")
                return True
        except Exception as e:
            logger.warning(f"Failed to add resource directory {path}: {e}")
        return False
    
    def find_resource(self, resource_path: str) -> Optional[Path]:
        """Find a resource file in the resource directories.
        
        Args:
            resource_path: Relative path to the resource file.
            
        Returns:
            Optional[Path]: Full path to the resource if found, None otherwise.
        """
        resource_path = resource_path.replace('\\', '/')
        
        # Check cache first
        for base_dir in self._resource_dirs:
            full_path = base_dir / resource_path
            if full_path.exists():
                return full_path
        
        # Not found in any resource directory
        logger.warning(f"Resource not found: {resource_path}")
        return None
    
    def load_icon(self, icon_path: str, color: str = None, size: QSize = None) -> Optional[QIcon]:
        """Load an icon from the resource directories.
        
        Args:
            icon_path: Relative path to the icon file.
            color: Optional color to apply to the icon (e.g., '#FF0000' for red).
            size: Optional size for the icon.
            
        Returns:
            Optional[QIcon]: The loaded icon, or None if not found.
        """
        cache_key = f"{icon_path}:{color or ''}:{size.width() if size else 0}x{size.height() if size else 0}"
        
        # Check cache
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]
        
        # Find the icon file
        icon_file = self.find_resource(icon_path)
        if not icon_file:
            return None
        
        try:
            # Handle SVG icons
            if icon_file.suffix.lower() == '.svg':
                renderer = QSvgRenderer(str(icon_file))
                
                if not renderer.isValid():
                    logger.error(f"Invalid SVG file: {icon_file}")
                    return None
                
                # Create a pixmap to render the SVG into
                pixmap_size = size if size else QSize(32, 32)
                pixmap = QPixmap(pixmap_size)
                pixmap.fill(Qt.transparent)
                
                # Render SVG to pixmap
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                
                # Apply color if specified
                if color:
                    image = pixmap.toImage()
                    for x in range(image.width()):
                        for y in range(image.height()):
                            pixel_color = image.pixelColor(x, y)
                            if pixel_color.alpha() > 0:  # Only recolor non-transparent pixels
                                image.setPixelColor(x, y, QColor(color))
                    pixmap = QPixmap.fromImage(image)
                
                icon = QIcon(pixmap)
            else:
                # For other image formats
                icon = QIcon(str(icon_file))
                
                # Apply color if specified (only works well for monochrome icons)
                if color:
                    # Convert icon to image, apply color, and back to icon
                    pixmap = icon.pixmap(size if size else QSize(32, 32))
                    image = pixmap.toImage()
                    
                    for x in range(image.width()):
                        for y in range(image.height()):
                            pixel_color = image.pixelColor(x, y)
                            if pixel_color.alpha() > 0:  # Only recolor non-transparent pixels
                                image.setPixelColor(x, y, QColor(color))
                    
                    icon = QIcon(QPixmap.fromImage(image))
            
            # Cache the result
            self._icon_cache[cache_key] = icon
            return icon
            
        except Exception as e:
            logger.error(f"Failed to load icon {icon_path}: {e}", exc_info=True)
            return None
    
    def load_pixmap(self, image_path: str, size: QSize = None) -> Optional[QPixmap]:
        """Load a pixmap from the resource directories.
        
        Args:
            image_path: Relative path to the image file.
            size: Optional size for the pixmap.
            
        Returns:
            Optional[QPixmap]: The loaded pixmap, or None if not found.
        """
        cache_key = f"{image_path}:{size.width() if size else 0}x{size.height() if size else 0}"
        
        # Check cache
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]
        
        # Find the image file
        image_file = self.find_resource(image_path)
        if not image_file:
            return None
        
        try:
            # Load the pixmap
            pixmap = QPixmap(str(image_file))
            
            # Resize if needed
            if size and not size.isNull() and not size.isEmpty():
                pixmap = pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Cache the result
            self._pixmap_cache[cache_key] = pixmap
            return pixmap
            
        except Exception as e:
            logger.error(f"Failed to load pixmap {image_path}: {e}", exc_info=True)
            return None
    
    def load_font(self, font_path: str) -> bool:
        """Load a font from the resource directories.
        
        Args:
            font_path: Relative path to the font file.
            
        Returns:
            bool: True if the font was loaded successfully, False otherwise.
        """
        # Check cache
        if font_path in self._font_cache:
            return self._font_cache[font_path]
        
        # Find the font file
        font_file = self.find_resource(font_path)
        if not font_file:
            return False
        
        try:
            # Load the font
            font_id = QFontDatabase.addApplicationFont(str(font_file))
            if font_id == -1:
                logger.error(f"Failed to load font: {font_path}")
                self._font_cache[font_path] = False
                return False
            
            self._font_cache[font_path] = True
            logger.debug(f"Loaded font: {font_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading font {font_path}: {e}", exc_info=True)
            self._font_cache[font_path] = False
            return False
    
    def get_font_family(self, font_path: str) -> Optional[str]:
        """Get the font family name from a font file.
        
        Args:
            font_path: Relative path to the font file.
            
        Returns:
            Optional[str]: The font family name, or None if not found.
        """
        # Find the font file
        font_file = self.find_resource(font_path)
        if not font_file:
            return None
        
        try:
            # Load the font and get its family
            font_id = QFontDatabase.addApplicationFont(str(font_file))
            if font_id == -1:
                return None
                
            families = QFontDatabase.applicationFontFamilies(font_id)
            return families[0] if families else None
            
        except Exception as e:
            logger.error(f"Error getting font family for {font_path}: {e}", exc_info=True)
            return None
    
    def get_style_sheet(self, style_sheet_path: str) -> str:
        """Load a style sheet from the resource directories.
        
        Args:
            style_sheet_path: Relative path to the style sheet file.
            
        Returns:
            str: The loaded style sheet, or an empty string if not found.
        """
        # Find the style sheet file
        style_sheet_file = self.find_resource(style_sheet_path)
        if not style_sheet_file:
            return ""
        
        try:
            with open(style_sheet_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load style sheet {style_sheet_path}: {e}", exc_info=True)
            return ""

# Singleton instance
resource_loader = ResourceLoader()

def load_icon(icon_path: str, color: str = None, size: QSize = None) -> Optional[QIcon]:
    """Load an icon from the resource directories.
    
    Args:
        icon_path: Relative path to the icon file.
        color: Optional color to apply to the icon.
        size: Optional size for the icon.
        
    Returns:
        Optional[QIcon]: The loaded icon, or None if not found.
    """
    return resource_loader.load_icon(icon_path, color, size)

def load_pixmap(image_path: str, size: QSize = None) -> Optional[QPixmap]:
    """Load a pixmap from the resource directories.
    
    Args:
        image_path: Relative path to the image file.
        size: Optional size for the pixmap.
        
    Returns:
        Optional[QPixmap]: The loaded pixmap, or None if not found.
    """
    return resource_loader.load_pixmap(image_path, size)

def load_font(font_path: str) -> bool:
    """Load a font from the resource directories.
    
    Args:
        font_path: Relative path to the font file.
        
    Returns:
        bool: True if the font was loaded successfully, False otherwise.
    """
    return resource_loader.load_font(font_path)

def get_font_family(font_path: str) -> Optional[str]:
    """Get the font family name from a font file.
    
    Args:
        font_path: Relative path to the font file.
        
    Returns:
        Optional[str]: The font family name, or None if not found.
    """
    return resource_loader.get_font_family(font_path)

def get_style_sheet(style_sheet_path: str) -> str:
    """Load a style sheet from the resource directories.
    
    Args:
        style_sheet_path: Relative path to the style sheet file.
        
    Returns:
        str: The loaded style sheet, or an empty string if not found.
    """
    return resource_loader.get_style_sheet(style_sheet_path)
