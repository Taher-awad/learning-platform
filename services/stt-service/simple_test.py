import requests
import os

def test_stt():
    # Use the sample audio file we have in the tests folder
    # Assuming this script is run from services/stt-service/ or similar
    # We will look for the file in relative paths
    
    possible_paths = [
        "sample.mp3",
        "../../tests/test_audio.mp3",
        "test_audio.mp3"
    ]
    
    audio_path = None
    for p in possible_paths:
        if os.path.exists(p):
            audio_path = p
            break
            
    if not audio_path:
        print("❌ Could not find sample audio file (test_audio.mp3).")
        print("Please copy an mp3 file here and name it 'sample.mp3'")
        return

    print(f"Testing STT with audio file: {audio_path}")
    
    url = "http://localhost/api/stt/transcribe"
    
    try:
        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, "audio/mpeg")}
            response = requests.post(url, files=files)
            
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Transcription Success!")
            print("------------------------------------------------")
            print(f"TEXT: {data.get('text')}")
            print("------------------------------------------------")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error connecting to service: {e}")
        print("Ensure the services are running.")

if __name__ == "__main__":
    test_stt()
