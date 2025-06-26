"""
Learning and adaptation module for the AI Chat application.

This package contains components for collecting training data, fine-tuning models,
and enabling the AI to learn from interactions and improve over time.
"""

from typing import List

from .data_collector import DataCollector
from .model_trainer import ModelTrainer

# Define public API
__all__: List[str] = [
    'DataCollector',
    'ModelTrainer',
]

# Package version
__version__ = '0.1.0'

# Initialize package-level logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
