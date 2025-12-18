from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from confluent_kafka import Consumer, Producer, KafkaException
import boto3
import threading
import json
import requests
import io
import uuid

class Settings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:29092"
    ELEVENLABS_API_KEY: str
    S3_BUCKET_NAME: str = "learning-platform-tts-storage-dev"
    AWS_REGION: str = "us-east-1"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# S3 Client
s3_client = boto3.client('s3', region_name=settings.AWS_REGION)

# Kafka Consumer
consumer_conf = {
    'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
    'group.id': 'tts-service-group-v3',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(consumer_conf)

# Kafka Producer
producer_conf = {'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS}
producer = Producer(producer_conf)

def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure bucket exists (optional check)
    try:
        s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
    except Exception as e:
        print(f"Warning: Bucket {settings.S3_BUCKET_NAME} check failed: {e}")
    
    print("Starting consumer thread...")
    t = threading.Thread(target=consume_messages)
    t.daemon = True
    t.start()
    yield
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

def consume_messages():
    print("Starting consumer loop...")
    consumer.subscribe(['audio.generation.requested'])
    try:
        while True:
            # print("Polling...")
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == -191: # _PARTITION_EOF
                    continue
                else:
                    print(msg.error())
                    break
            
            # Process message
            try:
                data = json.loads(msg.value().decode('utf-8'))
                print(f"Received TTS request: {data}")
                
                if 'text' in data:
                    # Generate Audio using ElevenLabs
                    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM" # Rachel voice
                    headers = {
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": settings.ELEVENLABS_API_KEY
                    }
                    payload = {
                        "text": data['text'],
                        "model_id": "eleven_flash_v2_5",
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.5
                        }
                    }
                    
                    response = requests.post(url, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        audio_content = response.content
                        file_id = str(uuid.uuid4())
                        object_name = f"{file_id}.mp3"
                        
                        # Upload to S3
                        s3_client.upload_fileobj(
                            io.BytesIO(audio_content),
                            settings.S3_BUCKET_NAME,
                            object_name,
                            ExtraArgs={'ContentType': "audio/mpeg"}
                        )
                        
                        # Produce completion event
                        producer.produce(
                            "audio.generation.completed",
                            key=file_id,
                            value=json.dumps({
                                "audio_id": file_id,
                                "s3_bucket": settings.S3_BUCKET_NAME,
                                "s3_key": object_name,
                                "original_request_id": data.get('request_id')
                            }),
                            callback=delivery_report
                        )
                        producer.flush()
                    else:
                        print(f"ElevenLabs API Error: {response.text}")
                        
            except Exception as e:
                print(f"Error processing message: {e}")
                
    finally:
        consumer.close()

@app.get("/api/tts/audio/{file_id}")
def get_audio(file_id: str):
    try:
        # Get object from S3
        response = s3_client.get_object(Bucket=settings.S3_BUCKET_NAME, Key=f"{file_id}.mp3")
        return StreamingResponse(response['Body'], media_type="audio/mpeg")
    except Exception:
        raise HTTPException(status_code=404, detail="Audio file not found")

@app.delete("/api/tts/audio/{file_id}")
def delete_audio(file_id: str):
    try:
        s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=f"{file_id}.mp3")
        return {"message": "Audio deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TTSRequest(BaseModel):
    text: str

@app.post("/api/tts/synthesize")
async def synthesize(request: TTSRequest):
    # Produce request event
    request_id = str(uuid.uuid4())
    producer.produce(
        "audio.generation.requested",
        key=request_id,
        value=json.dumps({"text": request.text, "request_id": request_id}),
        callback=delivery_report
    )
    producer.flush()
    return {"message": "TTS request submitted", "request_id": request_id}

@app.get("/")
def read_root():
    return {"message": "TTS Service is running"}

@app.get("/api/tts/")
def read_root_prefix():
    return {"message": "TTS Service is running"}
