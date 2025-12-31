# Learning Platform - Final Cloud-Native Codebase 🚀

A comprehensive, production-ready microservices platform built with a cloud-native mindset. This repository represents the culmination of three development phases, focusing on scalability, security, and automated delivery.

## 🛠 Project Architecture & Phases

### Phase 1: AWS Infrastructure Layer
The foundation of the platform lies in a robust AWS Global Infrastructure setup, ensuring high availability and secure data management.
- **Networking**: Custom VPC with isolated Private/Public subnets across multiple Availability Zones.
- **Persistence**: Four dedicated RDS PostgreSQL instances (User, Chat, Documentation, Quiz) providing reliable data storage.
- **Compute**: Auto Scaling Group (ASG) of EC2 instances serving as the host for our containerized workload.
- **Traffic Management**: Application Load Balancer (ALB) for entry-point traffic routing and health monitoring.

### Phase 2: Microservices & Event Integration
Transitioned from monolithic thinking to a distributed microservices architecture empowered by AI and events.
- **AI Gatekeepers**: Nginx-based API Gateway handling rate limiting, JWT authentication, and routing.
- **Event-Driven**: Kafka cluster integration enabling asynchronous processing for document analysis and quiz generation.
- **AI-Powered Services**: 
  - **Chat Service**: Integrated with Google Gemini AI for intelligent tutoring.
  - **TTS Service**: Integrated with ElevenLabs for high-quality audio narration.
  - **STT/Document Service**: Automated extraction and transcription logic.

### Phase 3: Containerization & Production Readiness
Enhanced the codebase for production stability and automated operations.
- **Containerization**: Full Dockerization of all 9 services with optimized multi-stage builds.
- **Orchestration**: AWS ECS (EC2 Launch Type) managing the lifecycle and placement of service tasks.
- **Security**: 
  - **AWS WAF**: Integrated with ALB to provide Layer 7 protection (SQLi, Rate-limiting).
  - **Data Privacy**: RDS SSL enforcement and S3 encryption-at-rest.
- **Observability**: Centralized OpenAPI (Swagger) documentation exposed through the gateway.

## 🚀 CI/CD Pipeline (GitHub Actions)

The repository features a fully automated CI/CD pipeline tailored for AWS deployment.

### Workflow: `ci_cd.yml`
Located at `.github/workflows/ci_cd.yml`, the pipeline automates the "Test -> Build -> Deploy" cycle:

1. **Automated Testing**: 
   - Runs on every `push` and `pull_request` to `main`.
   - Executes a comprehensive `pytest` suite covering unit and operational logic.
2. **Docker Build & Push**:
   - Authenticates with Amazon ECR.
   - Builds optimized Docker images for all microservices.
3. **Automated ECS Deployment**:
   - Triggered only on successful `push` to `main`.
   - Forces a new deployment of all ECS services.

> [!IMPORTANT]
> **To enable automated deployments**, you must add your AWS credentials to your GitHub Repository Secrets:
> 1. Go to `Settings` > `Secrets and variables` > `Actions`.
> 2. Add `AWS_ACCESS_KEY_ID`: Your IAM user access key.
> 3. Add `AWS_SECRET_ACCESS_KEY`: Your IAM user secret key.
> 4. Ensure your IAM user has the `AdministratorAccess` or specific ECR/ECS permissions.

## 📂 Repository Structure

```tree
.
├── services/               # Microservices (Auth, Chat, Document, Quiz, etc.)
├── frontend/               # React/Static UI hosted on S3
├── tests/                  # End-to-end and Unit Test Suite
├── k8s/                    # Kubernetes Manifests (Multi-cloud support)
├── docs/                   # Architecture Diagrams and API Spec
└── docker-compose.yml      # Local development environment
```

## 🚥 Getting Started

### Local Setup
Run the entire platform on your machine:
```bash
docker-compose up --build
```


