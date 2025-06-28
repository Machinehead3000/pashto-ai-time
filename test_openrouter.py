import requests

def test_openrouter_api(api_key):
    """Test OpenRouter API with the provided API key."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Try the models endpoint
    print("Testing OpenRouter API...")
    print("1. Testing /api/v1/models endpoint...")
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers=headers,
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}..." if response.text else "No response body")
        
        if response.status_code == 200:
            print("✅ Successfully connected to OpenRouter API!")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to OpenRouter API: {str(e)}")
    
    # Try the auth endpoint
    print("\n2. Testing /api/v1/auth/me endpoint...")
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/auth/me",
            headers=headers,
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}..." if response.text else "No response body")
        
        if response.status_code == 200:
            print("✅ Successfully authenticated with OpenRouter API!")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error authenticating with OpenRouter API: {str(e)}")
    
    return False

if __name__ == "__main__":
    from aichat.utils.api_key_manager import APIKeyManager
    
    # Get the API key
    api_key = APIKeyManager().get_api_key('openrouter')
    if not api_key:
        print("❌ No OpenRouter API key found!")
        exit(1)
    
    print(f"🔑 Found API key: {api_key[:10]}...{api_key[-4:]}")
    
    # Test the API
    if not test_openrouter_api(api_key):
        print("\n❌ Failed to connect to OpenRouter API. Please check your API key and internet connection.")
        print("   - Make sure your API key is valid and has the correct permissions")
        print("   - Check if you have an active internet connection")
        print("   - Visit https://openrouter.ai/keys to verify your API key")
        exit(1)
