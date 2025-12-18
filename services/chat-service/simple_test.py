import requests

def test_chat():
    message = "Explain quantum computing in one sentence."
    print(f"Testing Chat with message: '{message}'")
    
    url = "http://localhost/api/chat/message"
    payload = {
        "user_id": "simple_test_user",
        "message": message
    }
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Chat Response:")
            print("------------------------------------------------")
            print(data.get("response"))
            print("------------------------------------------------")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error connecting to service: {e}")

if __name__ == "__main__":
    test_chat()
