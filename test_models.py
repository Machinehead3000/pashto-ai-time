import time
import json
import requests
from datetime import datetime

# Models to test
MODELS = {
    "Mistral-7B": "mistralai/mistral-7b-instruct",
    "Llama-3-8B": "meta-llama/llama-3-8b-instruct",
    "DeepSeek-Chat": "deepseek/deepseek-chat"
}

def test_model(api_key: str, model_name: str, model_id: str) -> dict:
    """Test a single model and return metrics."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Simple test prompt
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Tell me a short joke about artificial intelligence."}
    ]
    
    payload = {
        "model": model_id,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            return {
                "model": model_name,
                "status": "success",
                "response_time": round(end_time - start_time, 2),
                "tokens_used": result.get('usage', {}).get('total_tokens', 0),
                "response": result['choices'][0]['message']['content'].strip()
            }
        else:
            return {
                "model": model_name,
                "status": "error",
                "error": f"API error: {response.status_code} - {response.text}"
            }
    except Exception as e:
        return {
            "model": model_name,
            "status": "error",
            "error": str(e)
        }

def main():
    # Get API key
    try:
        with open('pashto_ai_memory.json', 'r') as f:
            api_key = json.load(f)['preferences']['openrouter_api_key']
    except Exception as e:
        print(f"Error reading API key: {e}")
        return

    print(f"Testing models at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    results = []
    for name, model_id in MODELS.items():
        print(f"\nTesting {name}...")
        result = test_model(api_key, name, model_id)
        results.append(result)
        
        if result['status'] == 'success':
            print(f"✅ {name} - {result['response_time']}s - {result['tokens_used']} tokens")
            print(f"   Response: {result['response'][:100]}...")
        else:
            print(f"❌ {name} - Error: {result.get('error', 'Unknown error')}")
    
    # Save results to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'model_test_results_{timestamp}.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nTest completed. Results saved to file.")

if __name__ == "__main__":
    main()
