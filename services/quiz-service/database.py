from sqlalchemy import create_engine, Column, String, Integer, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

# Database Configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String, primary_key=True, index=True)
    document_id = Column(String, index=True)
    title = Column(String, nullable=True)
    questions = Column(JSON) # Store questions as JSON for simplicity: [{q, options, answer}]
    
    # We could normalize questions into a separate table, but JSON is flexible for this phase.

class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(String, primary_key=True, index=True)
    quiz_id = Column(String, ForeignKey("quizzes.id"))
    user_id = Column(String, index=True)
    score = Column(Integer)
    feedback = Column(String, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
