""
Internationalization (i18n) package for the Pashto AI Chat application.

This package provides localization and internationalization support,
including language management, string translation, and RTL language support.
"""

# Import the main localization manager
from .localization import (
    LocalizationManager,
    init_localization,
    get_localization,
    tr,
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES
)

# Export public API
__all__ = [
    'LocalizationManager',
    'init_localization',
    'get_localization',
    'tr',
    'DEFAULT_LANGUAGE',
    'SUPPORTED_LANGUAGES'
]
