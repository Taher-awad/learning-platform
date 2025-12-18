from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from confluent_kafka import Consumer, Producer, KafkaException
import threading
import json
import google.generativeai as genai

from sqlalchemy.orm import Session
from fastapi import Depends
from config import settings
from contextlib import asynccontextmanager
from database import init_db, get_db, Quiz, QuizResult, SessionLocal
import uuid

# Globals
model = None
consumer = None
producer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, consumer, producer
    
    # Init DB
    init_db()
    
    # Init Gemini
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Init Kafka Consumer
    consumer_conf = {
        'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'quiz-service-group',
        'auto.offset.reset': 'earliest'
    }
    consumer = Consumer(consumer_conf)
    
    # Init Kafka Producer
    producer_conf = {'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS}
    producer = Producer(producer_conf)
    
    # Start consumer thread
    t = threading.Thread(target=consume_messages)
    t.daemon = True
    t.start()
    
    yield
    
    # Cleanup
    if consumer:
        consumer.close()

app = FastAPI(lifespan=lifespan)

def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

def consume_messages():
    consumer.subscribe(['notes.generated', 'quiz.requested'])
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
                print(f"Received event: {data}")
                
                # If quiz requested or notes generated, generate quiz
                if 'text_content' in data:
                    prompt = f"""Generate a quiz with 5 multiple choice questions based on this text: {data['text_content'][:2000]}
                    Return the response as a valid JSON object with the following structure:
                    {{
                        "title": "Quiz Title",
                        "questions": [
                            {{
                                "q": "Question text",
                                "options": ["Option A", "Option B", "Option C", "Option D"],
                                "answer": "Option A"
                            }}
                        ]
                    }}
                    Do not include markdown formatting like ```json.
                    """
                    response = model.generate_content(prompt)
                    quiz_text = response.text.strip().replace("```json", "").replace("```", "")
                    
                    try:
                        quiz_data = json.loads(quiz_text)
                    except json.JSONDecodeError:
                        quiz_data = {"title": "Generated Quiz", "questions": []}
                    
                    quiz_id = str(uuid.uuid4())
                    document_id = data.get('document_id')
                    
                    # Store in DB
                    db = SessionLocal()
                    try:
                        db_quiz = Quiz(
                            id=quiz_id,
                            document_id=document_id,
                            title=quiz_data.get("title", "Quiz"),
                            questions=quiz_data.get("questions", [])
                        )
                        db.add(db_quiz)
                        db.commit()
                    except Exception as db_err:
                        print(f"DB Error: {db_err}")
                        db.rollback()
                    finally:
                        db.close()
                    
                    # Produce quiz.generated event
                    producer.produce(
                        "quiz.generated",
                        key=document_id or 'unknown',
                        value=json.dumps({"quiz_id": quiz_id, "document_id": document_id}),
                        callback=delivery_report
                    )
                    producer.flush()
                    
            except Exception as e:
                print(f"Error processing message: {e}")
                
    finally:
        consumer.close()

# Removed startup_event in favor of lifespan

class QuizRequest(BaseModel):
    document_id: str
    text_content: str # For testing without DB

@app.post("/api/quiz/generate")
async def generate_quiz(request: QuizRequest, db: Session = Depends(get_db)):
    try:
        # Check if quiz already exists for this document? 
        # Requirement doesn't strictly say 1 quiz per doc, but let's allow multiple.
        
        prompt = f"""Generate a quiz with 5 multiple choice questions based on this text: {request.text_content[:2000]}
        Return the response as a valid JSON object with the following structure:
        {{
            "title": "Quiz Title",
            "questions": [
                {{
                    "q": "Question text",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "answer": "Option A"
                }}
            ]
        }}
        Do not include markdown formatting like ```json.
        """
        response = model.generate_content(prompt)
        quiz_text = response.text.strip().replace("```json", "").replace("```", "")
        
        try:
            quiz_data = json.loads(quiz_text)
        except json.JSONDecodeError:
            # Fallback if AI returns bad JSON
            quiz_data = {
                "title": "Generated Quiz",
                "questions": []
            }
        
        quiz_id = str(uuid.uuid4())
        
        # Store in DB
        db_quiz = Quiz(
            id=quiz_id,
            document_id=request.document_id,
            title=quiz_data.get("title", "Quiz"),
            questions=quiz_data.get("questions", [])
        )
        db.add(db_quiz)
        db.commit()
        
        # Produce quiz.generated event
        try:
            producer.produce(
                "quiz.generated",
                key=request.document_id,
                value=json.dumps({"quiz_id": quiz_id, "document_id": request.document_id}),
                callback=delivery_report
            )
            producer.flush()
        except Exception as k_err:
            print(f"Warning: Failed to produce Kafka event: {k_err}")

        return {"id": quiz_id, "quiz": quiz_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quiz/history")
def get_quiz_history(db: Session = Depends(get_db)):
    results = db.query(QuizResult).all()
    return results

@app.get("/api/quiz/{quiz_id}")
def get_quiz(quiz_id: str, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz

class QuizSubmission(BaseModel):
    user_id: str
    answers: dict # {question_index: "Option A"}

@app.post("/api/quiz/{quiz_id}/submit")
def submit_quiz(quiz_id: str, submission: QuizSubmission, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    score = 0
    total = len(quiz.questions)
    
    for idx, q in enumerate(quiz.questions):
        user_answer = submission.answers.get(str(idx))
        if user_answer == q["answer"]:
            score += 1
            
    final_score = (score / total) * 100 if total > 0 else 0
    
    # Store Result
    result_id = str(uuid.uuid4())
    db_result = QuizResult(
        id=result_id,
        quiz_id=quiz_id,
        user_id=submission.user_id,
        score=int(final_score),
        feedback=f"You got {score} out of {total} correct."
    )
    db.add(db_result)
    db.commit()
    
    return {"id": result_id, "score": final_score, "feedback": db_result.feedback}

@app.delete("/api/quiz/{quiz_id}")
def delete_quiz(quiz_id: str, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    db.delete(quiz)
    db.commit()
    return {"message": "Quiz deleted"}

@app.get("/")
def read_root():
    return {"message": "Quiz Service is running"}

@app.get("/api/quiz/")
def read_root_prefix():
    return {"message": "Quiz Service is running"}
