from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import jwt
import os
import hashlib
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://dbadmin:ChangeMe123@learning-platform-user-db.cenk4a2ywbwo.us-east-1.rds.amazonaws.com:5432/userdb?sslmode=require"
    JWT_SECRET: str = "secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_HOURS: int = 24
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Database setup
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Pydantic models - using str instead of EmailStr to avoid email-validator dependency
class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str = ""

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRES_HOURS)
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/register")
def register(user: UserRegister):
    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == user.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        new_user = User(
            email=user.email,
            password_hash=hash_password(user.password),
            full_name=user.full_name
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {"id": new_user.id, "email": new_user.email, "full_name": new_user.full_name}
    finally:
        db.close()

@app.post("/login")
def login(user: UserLogin):
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.email == user.email).first()
        if not db_user or db_user.password_hash != hash_password(user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_token(db_user.id, db_user.email)
        return TokenResponse(access_token=token)
    finally:
        db.close()

@app.get("/me")
def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=401, detail="Invalid Authentication Scheme")
        
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return {"id": payload.get("sub"), "email": payload.get("email")}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Token")

@app.get("/verify")
def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=401, detail="Invalid Authentication Scheme")
        
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return Response(status_code=200)
    except Exception as e:
        print(f"Auth Failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid Token")

@app.get("/")
def health():
    return {"status": "ok", "service": "auth-service"}
