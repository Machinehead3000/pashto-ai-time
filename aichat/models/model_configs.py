"""
Model-specific configurations and prompt templates.
"""
from typing import Dict, Any, List, Optional

# Base configuration template
BASE_CONFIG = {
    'temperature': 0.7,
    'max_tokens': 2048,
    'top_p': 0.9,
    'frequency_penalty': 0.0,
    'presence_penalty': 0.6,
    'stop': None,
}

# Model-specific configurations
MODEL_CONFIGS = {
    'deepseek-r1': {
        **BASE_CONFIG,
        'model': 'deepseek-r1',
        'temperature': 0.7,
        'max_tokens': 4096,
        'supports_streaming': True,
        'supports_image': False,
        'supports_voice': True,
        'supports_code': True,
        'context_window': 32768,
    },
    'mistral-7b': {
        **BASE_CONFIG,
        'model': 'mistral-7b',
        'temperature': 0.8,
        'max_tokens': 2048,
        'supports_streaming': True,
        'supports_image': False,
        'supports_voice': False,
        'supports_code': True,
        'context_window': 8192,
    },
}

# System prompts for different tasks
SYSTEM_PROMPTS = {
    'default': "You are a helpful AI assistant. Provide clear, concise, and accurate responses.",
    'code': "You are an expert programming assistant. Provide clean, efficient, and well-documented code solutions.",
    'creative': "You are a creative writing assistant. Provide imaginative and engaging content.",
    'analytical': "You are an analytical assistant. Provide detailed, structured, and well-reasoned analysis.",
}

def get_model_config(model_name: str) -> Dict[str, Any]:
    """Get configuration for a specific model."""
    model_name = model_name.lower()
    config = MODEL_CONFIGS.get(model_name, BASE_CONFIG.copy())
    config['model'] = model_name  # Ensure model name is set
    return config

def get_system_prompt(task: str = 'default') -> str:
    """Get the system prompt for a specific task."""
    return SYSTEM_PROMPTS.get(task.lower(), SYSTEM_PROMPTS['default'])

def format_prompt(
    messages: List[Dict[str, str]],
    task: str = 'default',
    model_name: Optional[str] = None
) -> List[Dict[str, str]]:
    """Format messages with appropriate system prompt and model-specific formatting."""
    system_prompt = get_system_prompt(task)
    
    # Add system message if not present
    if not any(msg.get('role') == 'system' for msg in messages):
        messages = [{'role': 'system', 'content': system_prompt}] + messages
    
    # Apply model-specific formatting if needed
    if model_name and 'mistral' in model_name.lower():
        # Mistral-specific formatting
        for msg in messages:
            if msg['role'] == 'system':
                msg['content'] = f"<s>[INST] {msg['content']} [/INST]"
            elif msg['role'] == 'user':
                msg['content'] = f"<s>[INST] {msg['content']} [/INST]"
            elif msg['role'] == 'assistant':
                msg['content'] = f" {msg['content']} </s>"
    
    return messages
