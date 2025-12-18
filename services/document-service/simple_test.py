import requests
import os

def test_document_upload():
    # Create a dummy file to upload
    filename = "test_upload.txt"
    with open(filename, "w") as f:
        f.write("This is a test document uploaded via the simple test script.")
        
    print(f"Testing Document Upload with file: {filename}")
    
    url = "http://localhost/api/documents/upload"
    
    try:
        with open(filename, "rb") as f:
            files = {"file": (filename, f, "text/plain")}
            response = requests.post(url, files=files)
            
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Upload Success!")
            print("------------------------------------------------")
            print(f"Document ID: {data.get('id')}")
            print(f"Server Message: {data.get('message')}")
            print("------------------------------------------------")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error connecting to service: {e}")
    finally:
        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    test_document_upload()
