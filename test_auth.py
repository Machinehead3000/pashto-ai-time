import requests

def test_auth(api_key):
    """Test authentication with OpenRouter API."""
    print(f"Testing API key: {api_key[:8]}...{api_key[-4:]}" if api_key else "No API key provided")
    
    # Test auth/me endpoint
    print("\nTesting /auth/me endpoint:")
    url = "https://openrouter.ai/api/v1/auth/me"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test models endpoint
    print("\nTesting /models endpoint:")
    url = "https://openrouter.ai/api/v1/models"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:200]}..." if response.text else "No response")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test chat completions with a simple request
    print("\nTesting /chat/completions endpoint:")
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Get API key from memory file
    try:
        import json
        with open('pashto_ai_memory.json', 'r') as f:
            api_key = json.load(f)['preferences']['openrouter_api_key']
    except Exception as e:
        print(f"Error reading API key: {e}")
        api_key = input("Please enter your OpenRouter API key: ").strip()
    
    test_auth(api_key)
