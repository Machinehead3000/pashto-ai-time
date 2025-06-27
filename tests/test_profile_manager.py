"""
Tests for the ProfileManager and related classes.
"""
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from aichat.profiles.manager import ProfileManager, ProfileNotFoundError
from aichat.profiles.models import Profile, AIModelConfig, ModelProvider, ModelCapability, UIPreferences

class TestProfileManager(unittest.TestCase):
    """Test cases for the ProfileManager class."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test profiles
        self.test_dir = tempfile.mkdtemp(prefix="test_profiles_")
        self.manager = ProfileManager(profiles_dir=self.test_dir)
        
        # Create a sample profile for testing
        self.sample_profile = Profile(
            id="test_profile_1",
            name="Test Profile",
            description="A test profile",
            author="Tester",
            is_default=False,
            models={
                "default": AIModelConfig(
                    name="Test Model",
                    provider=ModelProvider.OPENROUTER,
                    model_id="test/model",
                    capabilities=[ModelCapability.TEXT_GENERATION]
                )
            },
            ui_preferences=UIPreferences(
                theme="dark",
                font_family="Arial",
                font_size=12
            ),
            tools_enabled=["python_interpreter", "file_analyzer"]
        )
    
    def tearDown(self):
        """Clean up after each test."""
        # Remove the temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_create_profile(self):
        """Test creating a new profile."""
        profile = self.manager.create_profile(
            name="Test Profile",
            description="A test profile",
            author="Tester"
        )
        
        self.assertIsNotNone(profile.id)
        self.assertEqual(profile.name, "Test Profile")
        self.assertEqual(profile.description, "A test profile")
        self.assertEqual(profile.author, "Tester")
        self.assertFalse(profile.is_default)
        
        # Verify the profile was saved to disk
        profile_path = Path(self.test_dir) / f"{profile.id}.json"
        self.assertTrue(profile_path.exists())
    
    def test_get_profile(self):
        """Test retrieving a profile by ID."""
        # Create a profile
        profile = self.manager.create_profile(
            name="Test Profile",
            description="A test profile"
        )
        
        # Retrieve the profile
        retrieved = self.manager.get_profile(profile.id)
        
        self.assertEqual(profile.id, retrieved.id)
        self.assertEqual(profile.name, retrieved.name)
        self.assertEqual(profile.description, retrieved.description)
    
    def test_get_nonexistent_profile(self):
        """Test retrieving a non-existent profile raises an error."""
        with self.assertRaises(ProfileNotFoundError):
            self.manager.get_profile("nonexistent_id")
    
    def test_update_profile(self):
        """Test updating a profile."""
        # Create a profile
        profile = self.manager.create_profile(
            name="Old Name",
            description="Old Description"
        )
        
        # Update the profile
        updated = self.manager.update_profile(
            profile.id,
            name="New Name",
            description="New Description"
        )
        
        # Verify the profile was updated
        self.assertEqual(updated.name, "New Name")
        self.assertEqual(updated.description, "New Description")
        
        # Verify the update is reflected when retrieving the profile
        retrieved = self.manager.get_profile(profile.id)
        self.assertEqual(retrieved.name, "New Name")
        self.assertEqual(retrieved.description, "New Description")
    
    def test_delete_profile(self):
        """Test deleting a profile."""
        # Create a profile
        profile = self.manager.create_profile(
            name="Test Profile",
            description="A test profile"
        )
        
        # Delete the profile
        self.manager.delete_profile(profile.id)
        
        # Verify the profile no longer exists
        with self.assertRaises(ProfileNotFoundError):
            self.manager.get_profile(profile.id)
        
        # Verify the profile file was deleted
        profile_path = Path(self.test_dir) / f"{profile.id}.json"
        self.assertFalse(profile_path.exists())
    
    def test_set_default_profile(self):
        """Test setting a profile as the default."""
        # Create two profiles
        profile1 = self.manager.create_profile("Profile 1")
        profile2 = self.manager.create_profile("Profile 2")
        
        # Set the first profile as default
        self.manager.set_default_profile(profile1.id)
        
        # Verify only the first profile is marked as default
        self.assertTrue(self.manager.get_profile(profile1.id).is_default)
        self.assertFalse(self.manager.get_profile(profile2.id).is_default)
        
        # Set the second profile as default
        self.manager.set_default_profile(profile2.id)
        
        # Verify the default has been updated
        self.assertFalse(self.manager.get_profile(profile1.id).is_default)
        self.assertTrue(self.manager.get_profile(profile2.id).is_default)
    
    def test_get_default_profile(self):
        """Test getting the default profile."""
        # Initially, there should be no default profile
        self.assertIsNone(self.manager.get_default_profile())
        
        # Create a profile and set it as default
        profile = self.manager.create_profile("Default Profile")
        self.manager.set_default_profile(profile.id)
        
        # Verify the default profile is returned
        default = self.manager.get_default_profile()
        self.assertIsNotNone(default)
        self.assertEqual(default.id, profile.id)
    
    def test_import_export_profile(self):
        """Test importing and exporting profiles."""
        # Create a profile to export
        profile = self.manager.create_profile("Export Test", "A test profile")
        
        # Export the profile to a temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            export_path = f.name
        
        try:
            # Export the profile
            self.manager.export_profile(profile.id, export_path)
            
            # Delete the existing profile
            self.manager.delete_profile(profile.id)
            
            # Import the profile back
            imported = self.manager.import_profile(export_path)
            
            # Verify the imported profile matches the original
            self.assertEqual(imported.name, profile.name)
            self.assertEqual(imported.description, profile.description)
            
        finally:
            # Clean up the temporary file
            if os.path.exists(export_path):
                os.unlink(export_path)
    
    def test_create_default_profiles(self):
        """Test creating default profiles."""
        # Clear any existing profiles
        for profile in self.manager.list_profiles():
            self.manager.delete_profile(profile.id)
        
        # Create default profiles
        self.manager.create_default_profiles()
        
        # Verify default profiles were created
        profiles = self.manager.list_profiles()
        self.assertGreaterEqual(len(profiles), 1)  # At least one default profile
        
        # Verify the default profile is set
        default = self.manager.get_default_profile()
        self.assertIsNotNone(default)
        self.assertTrue(default.is_default)
        
        # Verify the default profile has models
        self.assertGreater(len(default.models), 0)
        
        # Verify at least one model has the text generation capability
        has_text_gen = any(
            ModelCapability.TEXT_GENERATION in model.capabilities
            for model in default.models.values()
        )
        self.assertTrue(has_text_gen)


class TestProfileModels(unittest.TestCase):
    """Test cases for Profile and related model classes."""
    
    def test_profile_serialization(self):
        """Test serializing and deserializing a Profile."""
        # Create a profile with all fields set
        profile = Profile(
            id="test_id",
            name="Test Profile",
            description="A test profile",
            version="1.0.0",
            author="Tester",
            created_at="2023-01-01T00:00:00",
            updated_at="2023-01-02T00:00:00",
            is_default=True,
            models={
                "default": AIModelConfig(
                    name="Test Model",
                    provider=ModelProvider.OPENROUTER,
                    model_id="test/model",
                    capabilities=[ModelCapability.TEXT_GENERATION]
                )
            },
            ui_preferences=UIPreferences(
                theme="dark",
                font_family="Arial",
                font_size=12,
                show_line_numbers=True,
                word_wrap=True,
                auto_save=True,
                auto_save_interval=60
            ),
            tools_enabled=["python_interpreter", "file_analyzer"],
            metadata={"key": "value"}
        )
        
        # Convert to dict and back
        data = profile.to_dict()
        deserialized = Profile.from_dict(data)
        
        # Verify all fields match
        self.assertEqual(profile.id, deserialized.id)
        self.assertEqual(profile.name, deserialized.name)
        self.assertEqual(profile.description, deserialized.description)
        self.assertEqual(profile.version, deserialized.version)
        self.assertEqual(profile.author, deserialized.author)
        self.assertEqual(profile.created_at, deserialized.created_at)
        self.assertEqual(profile.updated_at, deserialized.updated_at)
        self.assertEqual(profile.is_default, deserialized.is_default)
        self.assertEqual(profile.tools_enabled, deserialized.tools_enabled)
        self.assertEqual(profile.metadata, deserialized.metadata)
        
        # Verify models
        self.assertEqual(len(profile.models), len(deserialized.models))
        for model_name, model in profile.models.items():
            self.assertIn(model_name, deserialized.models)
            deserialized_model = deserialized.models[model_name]
            self.assertEqual(model.name, deserialized_model.name)
            self.assertEqual(model.provider, deserialized_model.provider)
            self.assertEqual(model.model_id, deserialized_model.model_id)
            self.assertEqual(model.capabilities, deserialized_model.capabilities)
        
        # Verify UI preferences
        self.assertEqual(profile.ui_preferences.theme, deserialized.ui_preferences.theme)
        self.assertEqual(profile.ui_preferences.font_family, deserialized.ui_preferences.font_family)
        self.assertEqual(profile.ui_preferences.font_size, deserialized.ui_preferences.font_size)
        self.assertEqual(profile.ui_preferences.show_line_numbers, deserialized.ui_preferences.show_line_numbers)
        self.assertEqual(profile.ui_preferences.word_wrap, deserialized.ui_preferences.word_wrap)
        self.assertEqual(profile.ui_preferences.auto_save, deserialized.ui_preferences.auto_save)
        self.assertEqual(profile.ui_preferences.auto_save_interval, deserialized.ui_preferences.auto_save_interval)
    
    def test_aimodelconfig_serialization(self):
        """Test serializing and deserializing an AIModelConfig."""
        model = AIModelConfig(
            name="Test Model",
            provider=ModelProvider.OPENROUTER,
            model_id="test/model",
            api_key_name="test_key",
            temperature=0.7,
            max_tokens=2048,
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.5,
            stop_sequences=["\n"],
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION
            ],
            parameters={"test_param": 123}
        )
        
        # Convert to dict and back
        data = model.to_dict()
        deserialized = AIModelConfig.from_dict(data)
        
        # Verify all fields match
        self.assertEqual(model.name, deserialized.name)
        self.assertEqual(model.provider, deserialized.provider)
        self.assertEqual(model.model_id, deserialized.model_id)
        self.assertEqual(model.api_key_name, deserialized.api_key_name)
        self.assertEqual(model.temperature, deserialized.temperature)
        self.assertEqual(model.max_tokens, deserialized.max_tokens)
        self.assertEqual(model.top_p, deserialized.top_p)
        self.assertEqual(model.frequency_penalty, deserialized.frequency_penalty)
        self.assertEqual(model.presence_penalty, deserialized.presence_penalty)
        self.assertEqual(model.stop_sequences, deserialized.stop_sequences)
        self.assertEqual(model.capabilities, deserialized.capabilities)
        self.assertEqual(model.parameters, deserialized.parameters)


if __name__ == "__main__":
    unittest.main()
