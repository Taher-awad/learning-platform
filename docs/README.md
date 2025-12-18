# Cloud-Based Learning Platform - Phase 2

## Quick Start (For Teammates)
1. **Install Docker Desktop**: Ensure it is installed and running.
2. **Extract the Zip**: Unzip the project folder.
3. **Run**: Double-click `run.bat`.
   - The `.env` file with API keys is already included.
   - The system will build and start automatically.

## Project Overview
This project is a microservices-based learning platform implementing:
- **Document Reader**: Uploads and processes documents.
- **Chat Service**: AI-powered chat using RAG (Retrieval Augmented Generation).
- **Quiz Service**: Generates quizzes from documents.
- **TTS Service**: Text-to-Speech generation.
- **STT Service**: Speech-to-Text transcription.

The infrastructure is built on **Docker** and includes:
- **Kafka & Zookeeper**: Event streaming.
- **PostgreSQL**: Relational database.
- **MinIO**: S3-compatible object storage.
- **Redis**: Caching.
- **API Gateway (Nginx)**: Single entry point for all services.

## Prerequisites
- **Docker** and **Docker Compose** installed.
- **Python 3.11+** (optional, for running local scripts).
- API Keys for:
    - **Google Gemini** (Free Tier)
    - **ElevenLabs** (Free Tier)

## Setup Instructions

1.  **Clone the repository** (or extract the project folder).
2.  **Navigate to the project directory**:
    ```powershell
    cd "path/to/phase 2"
    ```
3.  **Configure Environment Variables**:
    - Copy `.env.example` to `.env`.
    - Open `.env` and fill in your API keys.
    ```powershell
    copy .env.example .env
    ```
    - **GOOGLE_API_KEY**: Get from [Google AI Studio](https://aistudio.google.com/).
    - **ELEVENLABS_API_KEY**: Get from [ElevenLabs](https://elevenlabs.io/).

## Running the Project

### Using the Run Script (Windows)
Simply double-click `run.bat` or execute it in PowerShell:
```powershell
.\run.bat
```
This script will build and start all services in detached mode.

### Manual Start
```powershell
docker-compose up -d --build
```

# Cloud-Based Learning Platform - Phase 2

## Quick Start (For Teammates)
1. **Install Docker Desktop**: Ensure it is installed and running.
2. **Extract the Zip**: Unzip the project folder.
3. **Run**: Double-click `run.bat`.
   - The `.env` file with API keys is already included.
   - The system will build and start automatically.

## Project Overview
This project is a microservices-based learning platform implementing:
- **Document Reader**: Uploads and processes documents.
- **Chat Service**: AI-powered chat using RAG (Retrieval Augmented Generation).
- **Quiz Service**: Generates quizzes from documents.
- **TTS Service**: Text-to-Speech generation.
- **STT Service**: Speech-to-Text transcription.

The infrastructure is built on **Docker** and includes:
- **Kafka & Zookeeper**: Event streaming.
- **PostgreSQL**: Relational database.
- **MinIO**: S3-compatible object storage.
- **Redis**: Caching.
- **API Gateway (Nginx)**: Single entry point for all services.

## Prerequisites
- **Docker** and **Docker Compose** installed.
- **Python 3.11+** (optional, for running local scripts).
- API Keys for:
    - **Google Gemini** (Free Tier)
    - **ElevenLabs** (Free Tier)

## Setup Instructions

1.  **Clone the repository** (or extract the project folder).
2.  **Navigate to the project directory**:
    ```powershell
    cd "path/to/phase 2"
    ```
3.  **Configure Environment Variables**:
    - Copy `.env.example` to `.env`.
    - Open `.env` and fill in your API keys.
    ```powershell
    copy .env.example .env
    ```
    - **GOOGLE_API_KEY**: Get from [Google AI Studio](https://aistudio.google.com/).
    - **ELEVENLABS_API_KEY**: Get from [ElevenLabs](https://elevenlabs.io/).

## Running the Project

### Using the Run Script (Windows)
Simply double-click `run.bat` or execute it in PowerShell:
```powershell
.\run.bat
```
This script will build and start all services in detached mode.

### Manual Start
```powershell
docker-compose up -d --build
```

## Stopping the Project
```powershell
docker-compose down
```

## Architecture
- **API Gateway**: `http://localhost:80`
    - Rate Limited: 10 req/s
- **Kafka Dashboard**: `http://localhost:8080`
- **Microservices**:
    - TTS: Internal Port 8000 (Exposed via Gateway)
## Troubleshooting
- **Service not starting?** Check logs: `docker-compose logs <service-name>`
- **Kafka errors?** Ensure Zookeeper is running first. The services are configured to wait, but sometimes a restart helps.
- **API 404?** Ensure you are using the correct path via the API Gateway (e.g., `/api/chat/message`).
