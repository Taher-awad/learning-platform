from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic_settings import BaseSettings, SettingsConfigDict
from contextlib import asynccontextmanager
from confluent_kafka import Producer
import boto3
import uuid
import json
import io
import speech_recognition as sr
from pydub import AudioSegment

class Settings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:29092"
    S3_BUCKET_NAME: str = "learning-platform-stt-storage-dev"
    AWS_REGION: str = "us-east-1"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# S3 Client
s3_client = boto3.client('s3', region_name=settings.AWS_REGION)

# Kafka Producer
producer_conf = {'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS}
producer = Producer(producer_conf)

def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify bucket exists (optional check)
    try:
        s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
    except Exception as e:
        print(f"Warning: Bucket {settings.S3_BUCKET_NAME} check failed: {e}")
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/api/stt/transcribe")
async def transcribe(file: UploadFile = File(...)):
    try:
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split(".")[-1]
        object_name = f"{file_id}.{file_extension}"
        
        # Read file content
        content = await file.read()
        
        # Upload to S3
        s3_client.upload_fileobj(
            io.BytesIO(content),
            settings.S3_BUCKET_NAME,
            object_name
        )
        
        # Perform Transcription (using SpeechRecognition for simplicity)
        # Convert to wav if needed
        recognizer = sr.Recognizer()
        audio_data = None
        
        try:
            # Convert bytes to audio segment
            audio = AudioSegment.from_file(io.BytesIO(content), format=file_extension)
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            wav_io.seek(0)
            
            with sr.AudioFile(wav_io) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
        except Exception as e:
            print(f"Transcription failed: {e}")
            text = "Transcription failed or audio format not supported."

        # Produce completion event
        producer.produce(
            "audio.transcription.completed",
            key=file_id,
            value=json.dumps({
                "transcription_id": file_id,
                "text": text,
                "s3_bucket": settings.S3_BUCKET_NAME,
                "s3_key": object_name
            }),
            callback=delivery_report
        )
        producer.flush()
        
        return {"id": file_id, "text": text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stt/transcription/{transcription_id}")
def get_transcription(transcription_id: str):
    # Mock implementation (in real world, fetch from Postgres)
    return {"id": transcription_id, "text": "This is a mocked transcription for retrieval.", "status": "completed"}

@app.get("/api/stt/transcriptions")
def list_transcriptions():
    # List objects from S3
    try:
        response = s3_client.list_objects_v2(Bucket=settings.S3_BUCKET_NAME)
        objects = response.get('Contents', [])
        return [{"id": obj['Key'], "size": obj['Size']} for obj in objects]
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def read_root():
    return {"message": "STT Service is running"}

@app.get("/api/stt/")
def read_root_prefix():
    return {"message": "STT Service is running"}
