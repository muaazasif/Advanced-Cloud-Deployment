# Deployment Documentation

## Local Development with Minikube

### Prerequisites
- Docker
- kubectl
- minikube
- dapr CLI

### Steps to Deploy Locally

1. Start Minikube:
   ```bash
   minikube start
   ```

2. Install Dapr:
   ```bash
   dapr init -k
   ```

3. Build Docker images:
   ```bash
   eval $(minikube docker-env)
   docker build -t todo-api:latest .
   docker build -t todo-frontend:latest ./frontend
   ```

4. Deploy Kafka:
   ```bash
   kubectl apply -f minikube/kafka-deployment.yaml
   ```

5. Deploy Dapr components:
   ```bash
   kubectl apply -f dapr/
   ```

6. Deploy the application:
   ```bash
   kubectl apply -f deployments/
   ```

### Automated Deployment

Alternatively, you can use the automated deployment script:
```bash
./deploy_minikube.sh
```

## Cloud Deployment

### Azure AKS

1. Create an AKS cluster
2. Connect kubectl to your cluster
3. Install Dapr: `dapr init -k`
4. Build and push your images to a container registry
5. Update the deployment files with your image names
6. Deploy: `kubectl apply -f deployments/aks-deployment.yaml`

### Google GKE

1. Create a GKE cluster
2. Connect kubectl to your cluster
3. Install Dapr: `dapr init -k`
4. Build and push your images to a container registry
5. Update the deployment files with your image names
6. Deploy: `kubectl apply -f deployments/gke-deployment.yaml`

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │────│     API         │────│     Kafka       │
│   (Next.js)     │    │   (FastAPI)     │    │   (Streaming)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                            │
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   (Database)    │
                    └─────────────────┘

                    ┌─────────────────┐
                    │     Dapr        │
                    │  (Runtime)      │
                    └─────────────────┘
```

## Services

- **API Service**: Handles all business logic and communicates with the database and Kafka
- **Frontend Service**: Provides the user interface for interacting with the todo app
- **Kafka**: Manages event streaming for the event-driven architecture
- **PostgreSQL**: Stores the application data
- **Dapr**: Provides distributed application runtime capabilities

## Event Flow

1. User creates a task via the frontend
2. Frontend calls the API
3. API creates the task and publishes a "task.created" event to Kafka
4. Various services consume the event and perform actions (logging, notifications, etc.)
5. For recurring tasks, the consumer creates new tasks when the previous one is completed
6. For tasks with due dates, the scheduler sends reminders at the appropriate time