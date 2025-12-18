from sqlalchemy import create_engine, Column, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database Configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DEBUG: DATABASE_URL env var NOT found. Using fallback.")
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"
else:
    print("DEBUG: DATABASE_URL env var FOUND.")

# Mask password for logging
safe_url = DATABASE_URL.replace(POSTGRES_PASSWORD, "******") if POSTGRES_PASSWORD in DATABASE_URL else DATABASE_URL
print(f"DEBUG: Connecting to: {safe_url}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    summary = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True) # UUID
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String) # user or ai
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
