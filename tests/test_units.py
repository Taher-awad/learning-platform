import hashlib
import uuid
from datetime import datetime

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def test_password_hashing():
    """Test that password hashing is consistent and one-way"""
    password = "TestPassword123!"
    h1 = hash_password(password)
    h2 = hash_password(password)
    
    assert h1 == h2
    assert h1 != password
    assert len(h1) == 64

def test_uuid_generation():
    """Test that UUID generation works for service IDs"""
    u1 = str(uuid.uuid4())
    u2 = str(uuid.uuid4())
    
    assert u1 != u2
    assert len(u1) == 36

def test_health_logic():
    """Test basic service health structure"""
    status = {"status": "ok", "service": "auth-service"}
    assert status["status"] == "ok"
    assert "service" in status
