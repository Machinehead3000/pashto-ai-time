"""
AI Plugins - Extendable functionality for the AI system.

This module provides a plugin architecture for adding new capabilities to the AI system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class AIPlugin(ABC):
    """Base class for AI plugins."""
    
    def __init__(self, name: str, description: str = "", version: str = "1.0.0"):
        """Initialize the plugin.
        
        Args:
            name: Unique name for the plugin.
            description: Short description of what the plugin does.
            version: Plugin version string.
        """
        self.name = name
        self.description = description
        self.version = version
        self.enabled = True
    
    @abstractmethod
    def process(self, context: Any, input_data: Any, **kwargs) -> Any:
        """Process input and return output.
        
        Args:
            context: The current AI context.
            input_data: Input data to process.
            **kwargs: Additional parameters.
            
        Returns:
            Processed output data.
        """
        pass
    
    def on_enable(self) -> None:
        """Called when the plugin is enabled."""
        self.enabled = True
        logger.info(f"Enabled plugin: {self.name}")
    
    def on_disable(self) -> None:
        """Called when the plugin is disabled."""
        self.enabled = False
        logger.info(f"Disabled plugin: {self.name}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the plugin.
        
        Returns:
            Dict containing plugin status information.
        """
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'enabled': self.enabled
        }

class PluginManager:
    """Manages AI plugins."""
    
    def __init__(self):
        """Initialize the plugin manager."""
        self.plugins: Dict[str, AIPlugin] = {}
    
    def register_plugin(self, plugin: AIPlugin) -> bool:
        """Register a plugin.
        
        Args:
            plugin: The plugin instance to register.
            
        Returns:
            bool: True if registration was successful.
        """
        if not isinstance(plugin, AIPlugin):
            logger.error(f"Plugin must be an instance of AIPlugin, got {type(plugin)}")
            return False
            
        if plugin.name in self.plugins:
            logger.warning(f"Plugin '{plugin.name}' is already registered")
            return False
            
        self.plugins[plugin.name] = plugin
        logger.info(f"Registered plugin: {plugin.name} (v{plugin.version})")
        return True
    
    def get_plugin(self, name: str) -> Optional[AIPlugin]:
        """Get a plugin by name.
        
        Args:
            name: Name of the plugin to retrieve.
            
        Returns:
            The plugin instance or None if not found.
        """
        return self.plugins.get(name)
    
    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin.
        
        Args:
            name: Name of the plugin to enable.
            
        Returns:
            bool: True if the plugin was enabled, False otherwise.
        """
        plugin = self.get_plugin(name)
        if not plugin:
            logger.warning(f"Cannot enable unknown plugin: {name}")
            return False
            
        if plugin.enabled:
            return True
            
        try:
            plugin.on_enable()
            return True
        except Exception as e:
            logger.error(f"Error enabling plugin {name}: {e}", exc_info=True)
            return False
    
    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin.
        
        Args:
            name: Name of the plugin to disable.
            
        Returns:
            bool: True if the plugin was disabled, False otherwise.
        """
        plugin = self.get_plugin(name)
        if not plugin:
            logger.warning(f"Cannot disable unknown plugin: {name}")
            return False
            
        if not plugin.enabled:
            return True
            
        try:
            plugin.on_disable()
            return True
        except Exception as e:
            logger.error(f"Error disabling plugin {name}: {e}", exc_info=True)
            return False
    
    def get_plugins_status(self) -> List[Dict[str, Any]]:
        """Get status of all plugins.
        
        Returns:
            List of plugin status dictionaries.
        """
        return [plugin.get_status() for plugin in self.plugins.values()]
    
    def process_with_plugins(self, context: Any, input_data: Any, **kwargs) -> Any:
        """Process input through all enabled plugins.
        
        Args:
            context: The current AI context.
            input_data: Input data to process.
            **kwargs: Additional parameters.
            
        Returns:
            Processed output data.
        """
        result = input_data
        
        for plugin in [p for p in self.plugins.values() if p.enabled]:
            try:
                result = plugin.process(context, result, **kwargs)
            except Exception as e:
                logger.error(f"Error in plugin {plugin.name}: {e}", exc_info=True)
                continue
                
        return result

# Global plugin manager instance
plugin_manager = PluginManager()

def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance."""
    return plugin_manager
