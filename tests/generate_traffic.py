import requests
import time
import json

BASE_URL = "http://localhost:80"

import sys

def generate_traffic():
    print("🚀 Starting Traffic Generation...")
    print("--------------------------------")
    success = True

    # 1. Upload a Document -> Triggers 'document.uploaded'
    print("\n[1] Uploading Document...")
    files = {'file': ('traffic_test.txt', b'This is a real traffic test.', 'text/plain')}
    try:
        resp = requests.post(f"{BASE_URL}/api/documents/upload", files=files)
        if resp.status_code == 200:
            print("   ✅ Document Uploaded (Check 'document.uploaded' topic)")
        else:
            print(f"   ❌ Failed: {resp.status_code} - {resp.text}")
            success = False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        success = False

    time.sleep(1)

    # 2. Send Chat Message -> Triggers 'chat.message'
    print("\n[2] Sending Chat Message...")
    chat_payload = {"user_id": "test_user", "message": "Hello from Traffic Script!", "context_id": "none"}
    try:
        resp = requests.post(f"{BASE_URL}/api/chat/message", json=chat_payload)
        if resp.status_code == 200:
            print("   ✅ Chat Sent (Check 'chat.message' topic)")
        else:
            print(f"   ⚠️ Chat Request made: {resp.status_code}")
            # Chat might fail if Gemini key is invalid, but we want the test to proceed
    except Exception as e:
        print(f"   ❌ Error: {e}")
        success = False

    time.sleep(1)

    # 3. Request TTS -> Triggers 'audio.generation.requested'
    print("\n[3] Requesting TTS...")
    tts_payload = {"text": "This is a traffic test.", "voice": "default"}
    try:
        resp = requests.post(f"{BASE_URL}/api/tts/synthesize", json=tts_payload)
        if resp.status_code == 200:
            print("   ✅ TTS Requested (Check 'audio.generation.requested' topic)")
        else:
             print(f"   ⚠️ TTS Request made: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        success = False

    time.sleep(1)

    # 4. Request Quiz -> Triggers 'quiz.requested'
    print("\n[4] Requesting Quiz...")
    # Matches endpoint in main.py: class QuizRequest(BaseModel): document_id: str, text_content: str
    quiz_payload = {"document_id": "1", "text_content": "Cloud computing is the on-demand availability of computer system resources..."} 
    try:
        # endpoint is /api/quiz/generate (singular) as per main.py and nginx.conf
        resp = requests.post(f"{BASE_URL}/api/quiz/generate", json=quiz_payload)
        if resp.status_code == 200:
            print("   ✅ Quiz Requested (Check 'quiz.generated' topic)")
        else:
            print(f"   ⚠️ Quiz Request made: {resp.status_code}")
            print(f"   (Payload was: {quiz_payload})")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        success = False

    time.sleep(1)

    # 5. Request STT -> Triggers 'audio.transcription.requested'
    print("\n[5] Requesting STT Transcription (Real Audio)...")
    import os
    # Prefer the MP3 file if it exists, otherwise fallback to WAV
    audio_file_path = os.path.join(os.path.dirname(__file__), 'test_audio.mp3')
    content_type = 'audio/mpeg'
    
    if not os.path.exists(audio_file_path):
        # Fallback to WAV
        audio_file_path = os.path.join(os.path.dirname(__file__), 'test_audio.wav')
        content_type = 'audio/wav'
        import wave
        if not os.path.exists(audio_file_path):
             with wave.open(audio_file_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(44100)
                wf.writeframes(b'\x00' * 44100)
    
    try:
        filename = os.path.basename(audio_file_path)
        with open(audio_file_path, 'rb') as f:
            files_stt = {'file': (filename, f, content_type)}
            resp = requests.post(f"{BASE_URL}/api/stt/transcribe", files=files_stt)
            
        if resp.status_code == 200:
            print(f"   ✅ STT Requested (File: {filename})")
            print(f"      Response: {resp.json().get('text', 'No text')}")
        else:
            print(f"   ⚠️ STT Request made: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        success = False

    print("\n--------------------------------")
    print("Traffic generation complete.")
    print("👉 Now check Kafka UI at http://localhost:8080")
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    generate_traffic()
