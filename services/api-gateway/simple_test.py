import requests

def test_gateway():
    print("🌍 Testing API Gateway Routes...")
    print("--------------------------------")
    
    # We will test the gateway by verifying it can reach the root endpoints of the services
    # (Checking if the proxy_pass directives are working)
    
    endpoints = [
        ("Chat Service", "http://localhost/api/chat/"),
        ("Quiz Service", "http://localhost/api/quiz/"),
        ("TTS Service", "http://localhost/api/tts/"),
        ("Document Service", "http://localhost/api/documents/")
    ]
    
    overall_success = True
    
    for name, url in endpoints:
        print(f"Testing route to {name}...", end=" ")
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                print(f"✅ OK ({resp.json().get('message', 'Running')})")
            else:
                print(f"❌ Failed ({resp.status_code})")
                overall_success = False
        except Exception as e:
            print(f"❌ Error: {e}")
            overall_success = False
            
    print("--------------------------------")
    if overall_success:
        print("✅ API Gateway is functioning correctly.")
    else:
        print("⚠️ Some routes failed. Check if services are running.")

if __name__ == "__main__":
    test_gateway()
