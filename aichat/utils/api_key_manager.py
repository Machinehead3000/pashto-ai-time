"""
API key management with validation and secure storage.
"""
import os
import json
import base64
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Manages API keys with secure storage and validation."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize the API key manager.
        
        Args:
            config_dir: Directory to store the encrypted API keys
        """
        if config_dir is None:
            config_dir = os.path.join(str(Path.home()), ".pashto_ai", "config")
        
        self.config_dir = config_dir
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Derive a key from the system username for encryption
        self.encryption_key = self._derive_key()
        self.keys_file = os.path.join(self.config_dir, "api_keys.enc")
    
    def _derive_key(self) -> bytes:
        """Derive an encryption key from the system username."""
        # Use the username as salt - this is just to make it harder to decrypt without the key
        salt = os.environ.get("USERNAME", "default_salt").encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(b"pashto_ai_encryption_key"))
    
    def _encrypt(self, data: str) -> str:
        """Encrypt the given data."""
        f = Fernet(self.encryption_key)
        return f.encrypt(data.encode()).decode()
    
    def _decrypt(self, token: str) -> str:
        """Decrypt the given token."""
        f = Fernet(self.encryption_key)
        return f.decrypt(token.encode()).decode()
    
    @staticmethod
    def validate_api_key_format(key: str) -> bool:
        """Validate the format of an API key.
        
        Args:
            key: The API key to validate
            
        Returns:
            bool: True if the key format is valid, False otherwise
        """
        if not key or not isinstance(key, str):
            return False
        # Basic validation - check if it's a reasonably long string
        # This is a basic check - actual validation should be done by trying to use the key
        return len(key.strip()) >= 20
    
    def save_api_key(self, service: str, key: str) -> bool:
        """Save an API key securely.
        
        Args:
            service: The service name (e.g., 'openrouter')
            key: The API key to save
            
        Returns:
            bool: True if the key was saved successfully, False otherwise
        """
        if not self.validate_api_key_format(key):
            logger.warning("Invalid API key format")
            return False
            
        try:
            # Load existing keys
            keys = self.load_all_keys()
            # Update with new key
            keys[service] = self._encrypt(key)
            
            # Save back to file
            with open(self.keys_file, 'w', encoding='utf-8') as f:
                json.dump(keys, f)
                
            return True
        except Exception as e:
            logger.error(f"Failed to save API key: {e}")
            return False
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get a decrypted API key.
        
        Args:
            service: The service name
            
        Returns:
            str: The decrypted API key, or None if not found or error
        """
        try:
            keys = self.load_all_keys()
            encrypted_key = keys.get(service)
            if encrypted_key:
                return self._decrypt(encrypted_key)
            return None
        except Exception as e:
            logger.error(f"Failed to get API key: {e}")
            return None
    
    def load_all_keys(self) -> Dict[str, str]:
        """Load all encrypted API keys.
        
        Returns:
            dict: Dictionary of service names to encrypted keys
        """
        if not os.path.exists(self.keys_file):
            return {}
            
        try:
            with open(self.keys_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load API keys: {e}")
            return {}
    
    def delete_api_key(self, service: str) -> bool:
        """Delete an API key.
        
        Args:
            service: The service name
            
        Returns:
            bool: True if the key was deleted, False otherwise
        """
        try:
            keys = self.load_all_keys()
            if service in keys:
                del keys[service]
                with open(self.keys_file, 'w', encoding='utf-8') as f:
                    json.dump(keys, f)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete API key: {e}")
            return False


def test_api_key(api_key: str, service: str = "openrouter") -> bool:
    """Test if an API key is valid by making a test request.
    
    Args:
        api_key: The API key to test
        service: The service to test against
        
    Returns:
        bool: True if the key is valid, False otherwise
    """
    if not api_key:
        return False
        
    try:
        if service == "openrouter":
            url = "https://openrouter.ai/api/v1/auth/me"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            response = requests.get(url, headers=headers, timeout=10)
            return response.status_code == 200
            
        # Add other services as needed
        
        return False
    except Exception as e:
        logger.error(f"API key test failed: {e}")
        return False
