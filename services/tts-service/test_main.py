import os
import sys
from unittest.mock import MagicMock, patch
import pytest
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def client():
    # Set dummy env vars
    os.environ['ELEVENLABS_API_KEY'] = 'dummy'
    os.environ['MINIO_ENDPOINT'] = 'dummy'
    os.environ['MINIO_ACCESS_KEY'] = 'dummy'
    os.environ['MINIO_SECRET_KEY'] = 'dummy'
    
    # Mock dependencies
    with patch('confluent_kafka.Consumer'), \
         patch('confluent_kafka.Producer'), \
         patch('minio.Minio'), \
         patch('requests.post'):
        
        from main import app
        from fastapi.testclient import TestClient
        
        with TestClient(app) as client:
            yield client

def test_synthesize_request(client):
    import main
    
    response = client.post("/api/tts/synthesize", json={"text": "Hello World"})
    assert response.status_code == 200
    assert "request_id" in response.json()
    
    # Verify Kafka produce
    main.producer.produce.assert_called()

def test_get_audio(client):
    # Mock MinIO get_object
    import main
    mock_data = MagicMock()
    mock_data.read.return_value = b"audio_data"
    main.minio_client.get_object.return_value = mock_data
    
    response = client.get("/api/tts/audio/file1")
    assert response.status_code == 200
    assert response.content == b"audio_data"

def test_delete_audio(client):
    response = client.delete("/api/tts/audio/file1")
    assert response.status_code == 200
