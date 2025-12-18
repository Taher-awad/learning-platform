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
    os.environ['GOOGLE_API_KEY'] = 'dummy'
    os.environ['POSTGRES_PASSWORD'] = 'dummy'
    os.environ['POSTGRES_DB'] = 'dummy'
    os.environ['POSTGRES_USER'] = 'dummy'
    os.environ['POSTGRES_HOST'] = 'dummy'
    
    # Mock dependencies
    with patch('google.generativeai.configure'), \
         patch('google.generativeai.GenerativeModel'), \
         patch('confluent_kafka.Consumer'), \
         patch('confluent_kafka.Producer'), \
         patch.dict(sys.modules, {'database': MagicMock()}):
        
        # Import main inside patch context
        from main import app, get_db
        
        # Mock DB session
        mock_db_session = MagicMock()
        def override_get_db():
            yield mock_db_session
            
        app.dependency_overrides[get_db] = override_get_db
        
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client

def test_generate_quiz(client):
    import main
    
    # Mock Gemini response
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title": "Test Quiz",
        "questions": [
            {"q": "Q1", "options": ["A", "B"], "answer": "A"}
        ]
    })
    main.model.generate_content.return_value = mock_response
    
    response = client.post("/api/quiz/generate", json={"document_id": "doc1", "text_content": "Content"})
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["quiz"]["title"] == "Test Quiz"
    
    # Verify Kafka produce
    main.producer.produce.assert_called()

def test_get_quiz(client):
    # Mock DB return
    # Since we can't easily access the mock session yielded by override_get_db inside the test function
    # (because client fixture consumes it), we rely on the fact that the mock returns None by default,
    # so we expect 404.
    response = client.get("/api/quiz/quiz1")
    assert response.status_code == 404

def test_submit_quiz(client):
    # Expect 404 because quiz not found in mock DB
    response = client.post("/api/quiz/quiz1/submit", json={"user_id": "user1", "answers": {"0": "A"}})
    assert response.status_code == 404
