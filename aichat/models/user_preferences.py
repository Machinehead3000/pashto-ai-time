"""User preferences and memory management for AI chat."""
import json
from typing import Dict, Any, Optional
from pathlib import Path

class UserPreferences:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".aichat" / "preferences.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.preferences: Dict[str, Any] = self._load_preferences()

    def _load_preferences(self) -> Dict[str, Any]:
        if self.storage_path.exists():
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'name': '',
            'explanation_style': 'default',
            'personality': {},
            'model_preferences': {},
            'ui_preferences': {}
        }

    def save_preferences(self) -> None:
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.preferences, f, indent=2, ensure_ascii=False)

    def set_user_name(self, name: str) -> None:
        self.preferences['name'] = name
        self.save_preferences()

    def set_explanation_style(self, style: str) -> None:
        self.preferences['explanation_style'] = style
        self.save_preferences()

    def set_personality(self, role: str, traits: Dict[str, Any]) -> None:
        self.preferences['personality'][role] = traits
        self.save_preferences()

    def get_user_name(self) -> str:
        return self.preferences.get('name', '')

    def get_explanation_style(self) -> str:
        return self.preferences.get('explanation_style', 'default')

    def get_personality(self, role: str) -> Dict[str, Any]:
        return self.preferences.get('personality', {}).get(role, {})