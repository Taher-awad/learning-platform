# Learning Platform - Final Codebase

Unified repository for the cloud-based learning platform, featuring microservices, AI integrations, and event-driven architecture.

## Repository Structure

- `services/`: All microservices (Auth, Chat, Document, Quiz, TTS, STT, and API Gateway).
- `frontend/`: The static frontend for the platform.
- `tests/`: End-to-end and unit tests for the backend services.
- `k8s/`: Kubernetes manifests for cluster deployment.
- `docs/`: Project documentation and architecture details.
- `docker-compose.yml`: Local development setup for services and Kafka.

## Key Features
- **Microservices**: Containerized services with dedicated database/storage.
- **AI-Powered**: Gemini AI for chat/quiz and ElevenLabs for TTS.
- **Event-Driven**: Kafka used for cross-service events.
- **Secured**: API management, JWT authentication, and Rate Limiting.

## Getting Started

### Local Development
To run the entire system locally using Docker Compose:
```bash
docker-compose up --build
```

### Deployment
Refer to the `k8s/` directory for Kubernetes deployment scripts or individual service `Dockerfiles` for ECS/general container hosting.

---
*Authorized Final Export - 18/12/2025*
