# AWS Deployment Guide (Phase 2)

This guide outlines how to deploy the Cloud-Based Learning Platform to AWS using **Amazon EKS (Elastic Kubernetes Service)** and **Amazon ECR (Elastic Container Registry)**, fulfilling the cloud deployment requirements.

## 1. Prerequisites
*   AWS CLI installed and configured (`aws configure`).
*   `kubectl` installed.
*   `eksctl` installed (recommended for creating clusters).
*   Docker installed.

## 2. Infrastructure Setup
### step 2.1: Create ECR Repositories
We need a registry for each microservice image.
```bash
aws ecr create-repository --repository-name tts-service
aws ecr create-repository --repository-name stt-service
aws ecr create-repository --repository-name chat-service
aws ecr create-repository --repository-name document-service
aws ecr create-repository --repository-name quiz-service
aws ecr create-repository --repository-name api-gateway
```

### Step 2.2: Build and Push Images
Log in to ECR:
```bash
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.<region>.amazonaws.com
```

For each service, build and push (repeat for all 6):
```bash
# Example for TTS Service
docker build -t tts-service ./tts-service
docker tag tts-service:latest <aws_account_id>.dkr.ecr.<region>.amazonaws.com/tts-service:latest
docker push <aws_account_id>.dkr.ecr.<region>.amazonaws.com/tts-service:latest
```

### Step 2.3: Create EKS Cluster
Create a 3-node cluster to support our Kafka requirement.
```bash
eksctl create cluster --name learning-platform-cluster --region <region> --nodes 3
```
*This verifies `kubectl` context is automatically updated.*

## 3. Deployment
### Step 3.1: Update Manifests
In the `k8s/` folder, update `02-services.yaml` to point to your new ECR image URIs instead of local tags.
*   Change `image: phase2-tts-service:latest` -> `image: <aws_account_id>.dkr.ecr.../tts-service:latest`

### Step 3.2: Deploy Infrastructure (Kafka, Postgres, MinIO)
Deploy the stateful services.
```bash
kubectl apply -f k8s/01-infrastructure.yaml
```
*Note: In a production environment, you would replace these self-hosted Postgres/MinIO deployments with AWS RDS and AWS S3 respectively for better durability.*

### Step 3.3: Deploy Microservices
```bash
kubectl apply -f k8s/02-services.yaml
```

### Step 3.4: Deploy Ingress (API Gateway)
```bash
kubectl apply -f k8s/03-ingress.yaml
```

## 4. Verification
### 4.1 Check Pods
```bash
kubectl get pods
```
Ensure all pods including `kafka-0`, `kafka-1`, `kafka-2` (3-node cluster) are Running.

### 4.2 Access Application
Get the LoadBalancer URL:
```bash
kubectl get svc api-gateway
```
Use the `EXTERNAL-IP` provided to access the application.

## 5. Clean Up
To avoid AWS charges:
```bash
kubectl delete -f k8s/
eksctl delete cluster --name learning-platform-cluster
```
