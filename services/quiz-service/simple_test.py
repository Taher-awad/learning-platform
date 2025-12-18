import requests
import json

def test_quiz():
    text = """
    Python is a high-level, general-purpose programming language. 
    Its design philosophy emphasizes code readability with the use of significant indentation.
    Python is dynamically typed and garbage-collected. 
    It supports multiple programming paradigms, including structured, object-oriented and functional programming.
    """
    
    print("Testing Quiz Generation...")
    print(f"Input Text: {text.strip()[:100]}...")
    
    url = "http://localhost/api/quiz/generate"
    # Note: 'document_id' is required by schema but can be dummy for this test
    payload = {
        "document_id": "test_doc_123",
        "text_content": text
    }
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Quiz Generated:")
            print("------------------------------------------------")
            # Parse the inner JSON string if the model returned it as a string
            quiz_content = data.get("quiz")
            print(quiz_content)
            print("------------------------------------------------")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error connecting to service: {e}")

if __name__ == "__main__":
    test_quiz()
