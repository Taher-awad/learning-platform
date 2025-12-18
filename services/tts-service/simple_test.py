import requests
import os
import sys
import json
import time
from confluent_kafka import Consumer

# Windows-specific sound player
def play_sound(file_path):
    print(f"🔊 Playing {file_path}...")
    try:
        os.startfile(file_path)
    except Exception as e:
        print(f"Could not play sound automatically: {e}")
        print("Please open the file manually.")

def test_tts():
    text = "Hello! This is a test of the Text to Speech service."
    print(f"Testing TTS with text: '{text}'")
    
    # 1. Submit Request
    url = "http://localhost/api/tts/synthesize"
    payload = {"text": text}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"❌ Failed to submit request: {response.text}")
            return
            
        request_id = response.json().get("request_id")
        print(f"✅ Request submitted! ID: {request_id}")
        print("⏳ Waiting for audio generation (listening to Kafka)...")
        
    except Exception as e:
        print(f"❌ Error connecting to service: {e}")
        return

    # 2. Listen for Completion Event
    conf = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'simple-test-consumer',
        'auto.offset.reset': 'latest'
    }
    
    consumer = Consumer(conf)
    consumer.subscribe(['audio.generation.completed'])
    
    audio_id = None
    start_time = time.time()
    
    try:
        while time.time() - start_time < 30: # 30s timeout
            msg = consumer.poll(1.0)
            if msg is None: continue
            if msg.error():
                print(f"Kafka Error: {msg.error()}")
                continue
                
            data = json.loads(msg.value().decode('utf-8'))
            if data.get("original_request_id") == request_id:
                audio_id = data.get("audio_id")
                print(f"✅ Generation Complete! Audio ID: {audio_id}")
                break
                
    finally:
        consumer.close()
        
    if not audio_id:
        print("❌ Timeout waiting for audio generation.")
        return

    # 3. Download Audio
    print("⬇️ Downloading audio...")
    download_url = f"http://localhost/api/tts/audio/{audio_id}"
    try:
        audio_resp = requests.get(download_url)
        if audio_resp.status_code == 200:
            output_file = "test_output.mp3"
            with open(output_file, "wb") as f:
                f.write(audio_resp.content)
            print(f"✅ Saved to: {output_file}")
            play_sound(output_file)
        else:
            print(f"❌ Failed to download: {audio_resp.status_code}")
    except Exception as e:
         print(f"❌ Download error: {e}")

if __name__ == "__main__":
    test_tts()
