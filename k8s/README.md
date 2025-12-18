
# Kubernetes Deployment
This folder contains standard Kubernetes manifests to deploy the platform on any K8s cluster (Minikube, EKS, GKE, etc.).

## Files
- `01-infrastructure.yaml`: Deployments and Services for Kafka, Zookeeper, Redis, Postgres, and MinIO.
- `02-services.yaml`: Deployments and Services for all 5 Python microservices.
- `03-ingress.yaml`: Ingress definition to route external traffic to services.

## How to Deploy
1. Ensure your specific environment secrets (API Keys) are set (for production, use K8s Secrets).
2. Apply the manifests:
   ```bash
   kubectl apply -f 01-infrastructure.yaml
   kubectl apply -f 02-services.yaml
   kubectl apply -f 03-ingress.yaml
   ```
