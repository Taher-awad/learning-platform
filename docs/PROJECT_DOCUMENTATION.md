# Cloud-Based Learning Platform (Phase 2) - Comprehensive Documentation

## 1. Executive Summary
This project implements the Microservices & Kafka Layer (Phase 2) of a Cloud-Based Learning Platform. It is designed as a scalable, event-driven architecture using Docker for containerization and Kafka for asynchronous communication. The system provides document processing, AI-powered chat, quiz generation, and audio synthesis/transcription services.

## 2. Architecture Overview
### 2.1 Microservices
The platform consists of five core microservices built with Python (FastAPI):
1.  **Document Reader Service**: Handles file uploads (PDF, DOCX, TXT) and text extraction. Soursce of truth for document data.
2.  **Chat Service**: Provides RAG-based conversational AI implementation using Google Gemini.
3.  **Quiz Service**: Generates educational quizzes from processed documents.
4.  **TTS (Text-to-Speech) Service**: Converts text to audio using ElevenLabs API.
5.  **STT (Speech-to-Text) Service**: Transcribes audio to text using SpeechRecognition.

### 2.2 Infrastructure
*   **API Gateway (Nginx)**: Single entry point `http://localhost:80`. Handles routing, CORS, and Rate Limiting (10 req/s).
*   **Apache Kafka**: 3-Node Cluster (in K8s) / 1-Node (Local) for event streaming.
*   **Zookeeper**: Coordinates Kafka brokers.
*   **PostgreSQL**: Relational database for metadata.
*   **MinIO**: High-performance object storage (S3 compatible) for files.
*   **Redis**: In-memory caching for chat history.

### 2.3 Deployment Diagrams
*   **Local Development**: `docker-compose.yml` orchestrates all containers on a single network.
*   **Production**: Kubernetes manifests (`k8s/`) provided for scalable deployment (Deployments, Services, Ingress).

## 3. API Reference
All services are exposed via the API Gateway.

### 3.1 Document Service (`/api/documents`)
*   `POST /upload`: Upload a file.
*   `GET /`: List all documents.
*   `GET /{id}`: Get document metadata.
*   `DELETE /{id}`: Delete a document.

### 3.2 Chat Service (`/api/chat`)
*   `POST /message`: Send a chat message (context-aware).
*   `GET /conversations`: List conversation history.
*   `DELETE /conversations/{id}`: Delete a conversation.

### 3.3 Quiz Service (`/api/quiz`)
*   `POST /generate`: Create a quiz from a document.
*   `GET /{id}`: Retrieve a quiz.
*   `POST /{id}/submit`: Submit answers.

### 3.4 TTS Service (`/api/tts`)
*   `POST /synthesize`: Generate audio from text.
*   `GET /audio/{id}`: Download generated audio.
*   `DELETE /audio/{id}`: Delete audio.

### 3.5 STT Service (`/api/stt`)
*   `POST /transcribe`: Upload audio for transcription.
*   `GET /transcription/{id}`: Get transcription status/result.

## 4. Kafka Event Registry
The system is event-driven. Services subscribe to these topics:

| Topic Schema | Producer | Consumer | Description |
| :--- | :--- | :--- | :--- |
| `document.uploaded` | Document Service | (System) | Notification of new file. |
| `document.processed` | Document Service | Chat Service | Text extracted, ready for RAG. |
| `notes.generated` | Document Service | Quiz Service | Summary available for quiz gen. |
| `quiz.requested` | (Frontend) | Quiz Service | User asked for a quiz. |
| `quiz.generated` | Quiz Service | (Frontend) | Quiz ready. |
| `chat.message` | Chat Service | Analytics | Chat interaction log. |
| `audio.generation.requested` | (Frontend) | TTS Service | User requested audio. |
| `audio.generation.completed` | TTS Service | (Frontend) | Audio file ready in MinIO. |
| `audio.transcription.requested` | (Frontend) | STT Service | User uploaded audio. |
| `audio.transcription.completed` | STT Service | (Frontend) | Text ready. |

## 5. Setup & Validation
### 5.1 Prerequisites
*   Docker Desktop installed.
*   API Keys for Google Gemini and ElevenLabs.

### 5.2 Running the Project
1.  **Extract**: Unzip the project.
2.  **Config**: Ensure `.env` is present (included in zip).
3.  **Start**: Run `run.bat` (Windows) or `docker-compose up -d --build`.

### 5.3 Testing
The project includes a comprehensive test suite covering Unit, Integration, and Infrastructure.
*   Run `test.bat` to execute all verification checks.

### 5.4 Monitoring
*   **Kafka UI**: Accessible at `http://localhost:8080` to view brokers, topics, and consumers.
*   **Nginx Logs**: Mapped to `docker-compose logs api-gateway`.
