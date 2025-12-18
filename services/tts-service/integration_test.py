import requests
import time
from minio import Minio
import os
import io

# Configuration
API_GATEWAY_URL = "http://api-gateway"
MINIO_ENDPOINT = "minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
TTS_BUCKET = "tts-service-storage-dev"

def run_integration_test():
    print("--- Starting TTS -> STT Integration Test ---")

    # 1. Request TTS
    text_to_speak = "Hello world, this is a test of the integration."
    print(f"1. Sending TTS request: '{text_to_speak}'")
    try:
        tts_response = requests.post(
            f"{API_GATEWAY_URL}/api/tts/synthesize",
            json={"text": text_to_speak}
        )
        tts_response.raise_for_status()
        print(f"   TTS Request Submitted: {tts_response.json()}")
    except Exception as e:
        print(f"   FAILED to submit TTS request: {e}")
        return

    # 2. Wait for Audio Generation
    print("2. Waiting 15 seconds for audio generation...")
    time.sleep(15)

    # 3. Retrieve Audio from MinIO
    print("3. Retrieving latest audio file from MinIO...")
    try:
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        
        objects = list(minio_client.list_objects(TTS_BUCKET))
        if not objects:
            print("   FAILED: No objects found in TTS bucket.")
            return
        
        # Sort by last modified
        latest_obj = max(objects, key=lambda x: x.last_modified)
        print(f"   Found latest file: {latest_obj.object_name}")
        
        # Get object
        response = minio_client.get_object(TTS_BUCKET, latest_obj.object_name)
        audio_data = response.read()
        response.close()
        response.release_conn()
        print(f"   Downloaded {len(audio_data)} bytes.")
        
    except Exception as e:
        print(f"   FAILED to retrieve audio from MinIO: {e}")
        return

    # 4. Send to STT
    print("4. Sending audio to STT service...")
    try:
        # Create a file-like object
        files = {'file': ('generated_audio.mp3', audio_data, 'audio/mpeg')}
        
        stt_response = requests.post(
            f"{API_GATEWAY_URL}/api/stt/transcribe",
            files=files
        )
        
        if stt_response.status_code == 200:
            print(f"   STT Response: {stt_response.json()}")
            transcription = stt_response.json().get("text")
            print(f"   Transcription: '{transcription}'")
            
            if transcription and "transcription failed" not in transcription.lower():
                 print("   SUCCESS: Integration test passed!")
            else:
                 print("   WARNING: Transcription might have failed (check text above).")
        else:
            print(f"   FAILED STT Request: {stt_response.status_code} - {stt_response.text}")
            
    except Exception as e:
        print(f"   FAILED to contact STT service: {e}")

if __name__ == "__main__":
    run_integration_test()
