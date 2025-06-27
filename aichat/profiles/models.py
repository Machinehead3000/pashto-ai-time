"""
Data models for AI profiles.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json

class ModelProvider(str, Enum):
    """Supported AI model providers."""
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    CUSTOM = "custom"

class ModelCapability(str, Enum):
    """Capabilities that a model might support."""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    IMAGE_GENERATION = "image_generation"
    IMAGE_ANALYSIS = "image_analysis"
    DOCUMENT_PROCESSING = "document_processing"
    WEB_BROWSING = "web_browsing"
    TOOL_USE = "tool_use"

@dataclass
class AIModelConfig:
    """Configuration for an AI model within a profile."""
    name: str
    provider: ModelProvider
    model_id: str
    api_key_name: str = "default"
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = field(default_factory=list)
    capabilities: List[ModelCapability] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary."""
        data = asdict(self)
        data['provider'] = self.provider.value
        data['capabilities'] = [cap.value for cap in self.capabilities]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIModelConfig':
        """Create from a dictionary."""
        if isinstance(data.get('provider'), str):
            data['provider'] = ModelProvider(data['provider'])
        if 'capabilities' in data and all(isinstance(c, str) for c in data['capabilities']):
            data['capabilities'] = [ModelCapability(c) for c in data['capabilities']]
        return cls(**data)

@dataclass
class UIPreferences:
    """UI preferences for a profile."""
    theme: str = "dark"
    font_family: str = "Segoe UI, Arial, sans-serif"
    font_size: int = 12
    show_line_numbers: bool = True
    word_wrap: bool = True
    auto_save: bool = True
    auto_save_interval: int = 60  # seconds
    show_sidebar: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIPreferences':
        """Create from a dictionary."""
        return cls(**data)

@dataclass
class Profile:
    """A complete AI profile configuration."""
    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    created_at: str = ""  # ISO format datetime
    updated_at: str = ""  # ISO format datetime
    is_default: bool = False
    models: Dict[str, AIModelConfig] = field(default_factory=dict)
    ui_preferences: UIPreferences = field(default_factory=UIPreferences)
    tools_enabled: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary."""
        data = asdict(self)
        data['models'] = {name: model.to_dict() for name, model in self.models.items()}
        data['ui_preferences'] = self.ui_preferences.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        """Create from a dictionary."""
        models_data = data.pop('models', {})
        ui_prefs_data = data.pop('ui_preferences', {})
        
        profile = cls(**data)
        
        # Convert models
        for name, model_data in models_data.items():
            profile.models[name] = AIModelConfig.from_dict(model_data)
        
        # Convert UI preferences
        profile.ui_preferences = UIPreferences.from_dict(ui_prefs_data)
        
        return profile
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Profile':
        """Create from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
