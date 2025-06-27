"""
Profile management functionality for AI profiles.
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import shutil

from .models import Profile, AIModelConfig, UIPreferences, ModelProvider, ModelCapability

class ProfileError(Exception):
    """Base exception for profile-related errors."""
    pass

class ProfileNotFoundError(ProfileError):
    """Raised when a profile is not found."""
    pass

class ProfileManager:
    """
    Manages AI profiles, including loading, saving, and managing profiles.
    """
    
    DEFAULT_PROFILES_DIR = "profiles"
    PROFILE_EXTENSION = ".json"
    
    def __init__(self, profiles_dir: Optional[str] = None):
        """
        Initialize the profile manager.
        
        Args:
            profiles_dir: Directory to store profiles. If None, uses a default directory.
        """
        self.profiles_dir = Path(profiles_dir) if profiles_dir else Path(self.DEFAULT_PROFILES_DIR)
        self._ensure_profiles_dir()
        self._profiles: Dict[str, Profile] = {}
        self._load_profiles()
    
    def _ensure_profiles_dir(self) -> None:
        """Ensure the profiles directory exists."""
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_profiles(self) -> None:
        """Load all profiles from the profiles directory."""
        self._profiles = {}
        
        # Load each JSON file in the profiles directory
        for file_path in self.profiles_dir.glob(f"*{self.PROFILE_EXTENSION}"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    profile = Profile.from_dict(data)
                    self._profiles[profile.id] = profile
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Error loading profile from {file_path}: {e}")
                continue
    
    def list_profiles(self) -> List[Profile]:
        """
        Get a list of all available profiles.
        
        Returns:
            List of Profile objects
        """
        return list(self._profiles.values())
    
    def get_profile(self, profile_id: str) -> Profile:
        """
        Get a profile by ID.
        
        Args:
            profile_id: ID of the profile to retrieve
            
        Returns:
            The requested Profile
            
        Raises:
            ProfileNotFoundError: If the profile does not exist
        """
        if profile_id not in self._profiles:
            raise ProfileNotFoundError(f"Profile '{profile_id}' not found")
        return self._profiles[profile_id]
    
    def create_profile(self, name: str, description: str = "", **kwargs) -> Profile:
        """
        Create a new profile.
        
        Args:
            name: Name of the new profile
            description: Optional description of the profile
            **kwargs: Additional profile attributes
            
        Returns:
            The newly created Profile
        """
        profile_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        profile = Profile(
            id=profile_id,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
            **kwargs
        )
        
        self._profiles[profile_id] = profile
        self._save_profile(profile)
        return profile
    
    def update_profile(self, profile_id: str, **updates) -> Profile:
        """
        Update an existing profile.
        
        Args:
            profile_id: ID of the profile to update
            **updates: Attributes to update
            
        Returns:
            The updated Profile
            
        Raises:
            ProfileNotFoundError: If the profile does not exist
        """
        if profile_id not in self._profiles:
            raise ProfileNotFoundError(f"Profile '{profile_id}' not found")
        
        profile = self._profiles[profile_id]
        
        # Update profile attributes
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        # Update timestamps
        profile.updated_at = datetime.utcnow().isoformat()
        
        self._save_profile(profile)
        return profile
    
    def delete_profile(self, profile_id: str) -> None:
        """
        Delete a profile.
        
        Args:
            profile_id: ID of the profile to delete
            
        Raises:
            ProfileNotFoundError: If the profile does not exist
        """
        if profile_id not in self._profiles:
            raise ProfileNotFoundError(f"Profile '{profile_id}' not found")
        
        # Delete the profile file
        profile_file = self._get_profile_file_path(profile_id)
        if profile_file.exists():
            profile_file.unlink()
        
        # Remove from memory
        del self._profiles[profile_id]
    
    def set_default_profile(self, profile_id: str) -> None:
        """
        Set a profile as the default profile.
        
        Args:
            profile_id: ID of the profile to set as default
            
        Raises:
            ProfileNotFoundError: If the profile does not exist
        """
        if profile_id not in self._profiles:
            raise ProfileNotFoundError(f"Profile '{profile_id}' not found")
        
        # Clear default flag from all profiles
        for profile in self._profiles.values():
            profile.is_default = False
            self._save_profile(profile)
        
        # Set the new default
        self._profiles[profile_id].is_default = True
        self._save_profile(self._profiles[profile_id])
    
    def get_default_profile(self) -> Optional[Profile]:
        """
        Get the default profile, if one exists.
        
        Returns:
            The default Profile, or None if no default is set
        """
        for profile in self._profiles.values():
            if profile.is_default:
                return profile
        return None
    
    def import_profile(self, file_path: Union[str, Path], overwrite: bool = False) -> Profile:
        """
        Import a profile from a file.
        
        Args:
            file_path: Path to the profile file to import
            overwrite: If True, overwrite if a profile with the same ID exists
            
        Returns:
            The imported Profile
            
        Raises:
            ProfileError: If the profile cannot be imported
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Validate the profile data
            if 'id' not in data:
                raise ProfileError("Invalid profile: missing 'id' field")
                
            # Check for existing profile with the same ID
            if data['id'] in self._profiles and not overwrite:
                raise ProfileError(f"Profile with ID '{data['id']}' already exists")
                
            # Create the profile
            profile = Profile.from_dict(data)
            self._profiles[profile.id] = profile
            self._save_profile(profile)
            
            return profile
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ProfileError(f"Failed to import profile: {e}")
    
    def export_profile(self, profile_id: str, file_path: Union[str, Path]) -> None:
        """
        Export a profile to a file.
        
        Args:
            profile_id: ID of the profile to export
            file_path: Path to save the profile to
            
        Raises:
            ProfileNotFoundError: If the profile does not exist
            ProfileError: If the profile cannot be exported
        """
        if profile_id not in self._profiles:
            raise ProfileNotFoundError(f"Profile '{profile_id}' not found")
            
        try:
            profile = self._profiles[profile_id]
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)
        except (IOError, OSError) as e:
            raise ProfileError(f"Failed to export profile: {e}")
    
    def _get_profile_file_path(self, profile_id: str) -> Path:
        """
        Get the file path for a profile.
        
        Args:
            profile_id: ID of the profile
            
        Returns:
            Path to the profile file
        """
        return self.profiles_dir / f"{profile_id}{self.PROFILE_EXTENSION}"
    
    def _save_profile(self, profile: Profile) -> None:
        """
        Save a profile to disk.
        
        Args:
            profile: Profile to save
        """
        file_path = self._get_profile_file_path(profile.id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)
    
    def create_default_profiles(self) -> None:
        """Create default profiles if none exist."""
        if self._profiles:
            return
            
        # Create a default profile
        default_profile = self.create_profile(
            name="Default Profile",
            description="Default AI profile with common settings",
            is_default=True,
            tools_enabled=["python_interpreter", "file_analyzer", "web_browser"]
        )
        
        # Add default models
        default_profile.models = {
            "text_generation": AIModelConfig(
                name="Text Generation",
                provider=ModelProvider.OPENROUTER,
                model_id="meta-llama/llama-3-8b-instruct",
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.DOCUMENT_PROCESSING
                ]
            ),
            "image_generation": AIModelConfig(
                name="Image Generation",
                provider=ModelProvider.OPENROUTER,
                model_id="stability-ai/sdxl",
                capabilities=[ModelCapability.IMAGE_GENERATION]
            )
        }
        
        self._save_profile(default_profile)
        
        # Create a coding-focused profile
        coding_profile = self.create_profile(
            name="Coding Assistant",
            description="Profile optimized for programming and code generation",
            tools_enabled=["python_interpreter", "file_analyzer", "code_search"]
        )
        
        coding_profile.models = {
            "code_generation": AIModelConfig(
                name="Code Generation",
                provider=ModelProvider.OPENROUTER,
                model_id="meta-llama/llama-3-8b-instruct",
                temperature=0.2,
                capabilities=[
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.TEXT_GENERATION
                ]
            )
        }
        
        self._save_profile(coding_profile)
