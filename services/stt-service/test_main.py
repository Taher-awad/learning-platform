import os
import sys
from unittest.mock import MagicMock, patch
import pytest
import json
import io

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def client():
    # Set dummy env vars
    os.environ['MINIO_ENDPOINT'] = 'dummy'
    os.environ['MINIO_ACCESS_KEY'] = 'dummy'
    os.environ['MINIO_SECRET_KEY'] = 'dummy'
    
    # Mock dependencies
    with patch('confluent_kafka.Producer'), \
         patch('minio.Minio'), \
         patch('speech_recognition.Recognizer'), \
         patch('speech_recognition.AudioFile'), \
         patch('pydub.AudioSegment'):
        
        from main import app
        from fastapi.testclient import TestClient
        
        with TestClient(app) as client:
            yield client

def test_transcribe(client):
    import main
    
    # Mock AudioSegment and SR
    mock_audio = MagicMock()
    main.AudioSegment.from_file.return_value = mock_audio
    
    mock_recognizer = MagicMock()
    mock_recognizer.recognize_google.return_value = "Transcribed Text"
    main.sr.Recognizer.return_value = mock_recognizer
    
    # Create dummy file
    file_content = b"fake audio content"
    files = {"file": ("test.wav", file_content, "audio/wav")}
    
    response = client.post("/api/stt/transcribe", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Transcribed Text"
    
    # Verify Kafka produce
    main.producer.produce.assert_called()

def test_list_transcriptions(client):
    import main
    mock_obj = MagicMock()
    mock_obj.object_name = "file1.txt"
    mock_obj.size = 100
    main.minio_client.list_objects.return_value = [mock_obj]
    
    response = client.get("/api/stt/transcriptions")
    assert response.status_code == 200
    assert len(response.json()) == 1
