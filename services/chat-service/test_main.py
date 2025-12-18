import os
import sys
from unittest.mock import MagicMock, patch
import pytest

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
        yield TestClient(app)

def test_chat_message(client):
    # We need to patch the producer/redis/model used in the endpoint
    # Since we imported app, we need to patch objects in main module
    # But main was imported inside fixture.
    # We can patch them here using sys.modules['main'] or similar?
    # Or better, patch them in the fixture?
    
    # Actually, main.producer etc are module level variables.
    # We mocked Producer class, so main.producer is a Mock.
    
    import main
    
    # Mock Redis
    main.redis_client = MagicMock()
    main.redis_client.get.return_value = None
    
    # Mock Model response
    mock_response = MagicMock()
    mock_response.text = "Hello from AI"
    main.model.generate_content.return_value = mock_response
    
    response = client.post("/api/chat/message", json={"user_id": "user1", "message": "Hello", "context_id": "doc123"})
    
    assert response.status_code == 200
    assert response.json()["response"] == "Hello from AI"
    assert "conversation_id" in response.json()
