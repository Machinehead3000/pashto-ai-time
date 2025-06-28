import json
import os

def update_api_key(new_key):
    """Update the OpenRouter API key in the memory file."""
    memory_file = 'pashto_ai_memory.json'
    
    try:
        # Read the existing memory file
        with open(memory_file, 'r') as f:
            data = json.load(f)
        
        # Update the API key
        data['preferences']['openrouter_api_key'] = new_key
        
        # Write back to the file
        with open(memory_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Successfully updated API key in {memory_file}")
        return True
    except Exception as e:
        print(f"❌ Error updating API key: {e}")
        return False

if __name__ == "__main__":
    print("OpenRouter API Key Updater")
    print("=========================")
    
    # Get new API key from user
    new_key = input("\nPlease enter your new OpenRouter API key: ").strip()
    
    if not new_key:
        print("❌ No API key provided. Exiting.")
    else:
        if update_api_key(new_key):
            print("\nKey updated successfully! You can now use the application with your new API key.")
        else:
            print("\nFailed to update the API key. Please check the error message above.")
