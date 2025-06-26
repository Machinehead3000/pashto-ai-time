"""
Tests for the localization system.
"""
import os
import json
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aichat.localization import Localization, tr, i18n

def test_localization_singleton():
    """Test that Localization is a singleton."""
    loc1 = Localization()
    loc2 = Localization()
    assert loc1 is loc2
    assert i18n is loc1

def test_tr_function():
    """Test the tr() convenience function."""
    # Test with existing key
    assert tr("app_name") == "Pashto AI"
    
    # Test with non-existent key (should return key)
    assert tr("nonexistent_key") == "nonexistent_key"
    
    # Test with format arguments
    assert tr("error_network", error="connection failed") == "Network error: connection failed"

def test_set_language():
    """Test changing the application language."""
    # Save current language to restore later
    current_lang = i18n.get_language()
    
    try:
        # Test setting to a valid language
        i18n.set_language('en')
        assert i18n.get_language() == 'en'
        
        # Test setting to an invalid language (should default to 'en')
        i18n.set_language('nonexistent')
        assert i18n.get_language() == 'en'
    finally:
        # Restore original language
        i18n.set_language(current_lang)

def test_translation_loading(tmp_path):
    """Test loading translations from files."""
    # Create a test translation file
    test_translations = {
        "test_key": "Test Value",
        "greeting": "Hello, {name}!",
        "nested": {
            "key": "Nested Value"
        }
    }
    
    # Create a test language file
    test_lang = 'test'
    test_file = tmp_path / f"{test_lang}.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_translations, f, ensure_ascii=False, indent=2)
    
    # Create a new Localization instance with the test directory
    loc = Localization()
    loc._translations = {}  # Reset translations
    loc._load_translations()
    
    # Test that the test translation was loaded
    loc.set_language(test_lang)
    assert tr("test_key") == "Test Value"
    assert tr("greeting", name="World") == "Hello, World!"
    
    # Test that non-existent keys return the key
    assert tr("nonexistent_key") == "nonexistent_key"

def test_default_translation_creation(tmp_path):
    """Test that default English translation is created if missing."""
    # Create a test directory without any translation files
    test_dir = tmp_path / "locales"
    test_dir.mkdir()
    
    # Create a new Localization instance with the test directory
    loc = Localization()
    loc._translations = {}  # Reset translations
    loc._load_translations()
    
    # Check that the default English file was created
    en_file = test_dir / "en.json"
    assert en_file.exists()
    
    # Load the created file and check some default keys
    with open(en_file, 'r', encoding='utf-8') as f:
        translations = json.load(f)
    
    assert "app_name" in translations
    assert "menu_file" in translations
    assert "error_network" in translations

if __name__ == "__main__":
    # Add the parent directory to the path so we can import the modules
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Run tests directly
    test_localization_singleton()
    test_tr_function()
    test_set_language()
    print("All tests passed successfully!")
