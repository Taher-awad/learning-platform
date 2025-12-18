from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from confluent_kafka import Consumer, Producer, KafkaException
import threading
import json
import google.generativeai as genai
import redis
import uuid
from sqlalchemy.orm import Session
from fastapi import Depends
from database import init_db, get_db, Conversation, Message as DBMessage


class Settings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:29092"
    GOOGLE_API_KEY: str
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "db"
    POSTGRES_HOST: str = "postgres"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Configure Gemini
genai.configure(api_key=settings.GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

app = FastAPI()

# Redis Client
redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

# Kafka Consumer
consumer_conf = {
    'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
    'group.id': 'chat-service-group',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(consumer_conf)

# Kafka Producer
# Kafka Producer
producer_conf = {'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS}
producer = Producer(producer_conf)

def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

class ChatMessage(BaseModel):
    user_id: str
    message: str
    context_id: str = None # Could be document ID

def consume_messages():
    consumer.subscribe(['document.processed'])
    try:
        while True:
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
                print(f"Received document processed event: {data}")
                # Store document context in Redis for RAG
                if 'document_id' in data and 'text_content' in data:
                    redis_client.set(f"doc:{data['document_id']}", data['text_content'])
            except Exception as e:
                print(f"Error processing message: {e}")
                
    finally:
        consumer.close()

@app.on_event("startup")
def startup_event():
    # Initialize Database
    init_db()
    
    # Start consumer in background thread
    t = threading.Thread(target=consume_messages)
    t.daemon = True
    t.start()

@app.post("/api/chat/message")
async def chat(message: ChatMessage, db: Session = Depends(get_db)):
    try:
        context = ""
        if message.context_id:
            stored_context = redis_client.get(f"doc:{message.context_id}")
            if stored_context:
                context = f"Context from document: {stored_context.decode('utf-8')[:2000]}...\n\n"
        
        prompt = f"{context}User: {message.message}\nAI:"
        response = model.generate_content(prompt)
        
        # Store in DB
        conversation_id = message.context_id or str(uuid.uuid4())
        
        # Check if conversation exists, if not create
        db_conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not db_conv:
            db_conv = Conversation(id=conversation_id, user_id=message.user_id, summary=message.message[:50])
            db.add(db_conv)
            db.commit()
            
        # Store User Message
        user_msg = DBMessage(id=str(uuid.uuid4()), conversation_id=conversation_id, role="user", content=message.message)
        db.add(user_msg)
        
        # Store AI Message
        ai_msg = DBMessage(id=str(uuid.uuid4()), conversation_id=conversation_id, role="ai", content=response.text)
        db.add(ai_msg)
        
        db.commit()
        
        # Produce chat.message event
        try:
            producer.produce(
                "chat.message",
                key=message.user_id,
                value=json.dumps({
                    "user_id": message.user_id,
                    "message": message.message,
                    "response": response.text,
                    "conversation_id": conversation_id
                }),
                callback=delivery_report
            )
            producer.flush()
        except Exception as e:
            print(f"Failed to produce kafka event: {e}")
        
        return {"response": response.text, "conversation_id": conversation_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/conversations")
def list_conversations(db: Session = Depends(get_db)):
    conversations = db.query(Conversation).all()
    return conversations

@app.get("/api/chat/conversations/{conversation_id}")
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Format history
    history = []
    for msg in conversation.messages:
        history.append({"role": msg.role, "message": msg.content, "timestamp": msg.created_at})
        
    return {
        "id": conversation.id,
        "history": history
    }

@app.delete("/api/chat/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete messages first (cascade should handle this but explicit is safe)
    db.query(DBMessage).filter(DBMessage.conversation_id == conversation_id).delete()
    db.delete(conversation)
    db.commit()
    
    return {"message": f"Conversation {conversation_id} deleted"}

@app.get("/")
def read_root():
    return {"message": "Chat Service is running"}

@app.get("/api/chat/")
def read_root_prefix():
    return {"message": "Chat Service is running"}
