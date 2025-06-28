"""
Test script for API key functionality.
"""
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from aichat.utils.api_key_manager import APIKeyManager, test_api_key

def main():
    """Test API key functionality."""
    print("=== Pashto AI API Key Tester ===")
    print("This script will help you test your OpenRouter API key.")
    
    # Initialize the API key manager
    key_manager = APIKeyManager()
    
    # Check if we already have a saved key
    saved_key = key_manager.get_api_key("openrouter")
    if saved_key:
        print("\nFound a saved API key.")
        test_result, message = test_api_key(saved_key, "openrouter")
        if test_result:
            print(f"✅ The saved API key is valid! {message}")
            print("You can now run the application with: python modern_main.py")
            return
        else:
            print(f"❌ The saved API key is invalid: {message}")
            print("Please enter a new API key below.")
    
    # Prompt for a new API key
    while True:
        print("\nPlease enter your OpenRouter API key (or 'q' to quit):")
        print("You can get one at: https://openrouter.ai/keys")
        api_key = input("> ").strip()
        
        if api_key.lower() == 'q':
            print("Exiting...")
            return
        
        # Test the API key
        print("\nTesting API key...")
        test_result, message = test_api_key(api_key, "openrouter")
        
        if test_result:
            print(f"✅ {message}")
            # Save the key
            if key_manager.save_api_key("openrouter", api_key):
                print("✅ API key saved successfully!")
                print("\nYou can now run the application with: python modern_main.py")
                return
            else:
                print("❌ Failed to save API key. Please try again.")
        else:
            print(f"❌ {message}")
            print("Please check your API key and try again.")

if __name__ == "__main__":
    main()
