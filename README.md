# Advanced Cloud Deployment - Todo Chatbot

An event-driven todo application with advanced features deployed on Kubernetes using Dapr and Kafka.

## Features

### Advanced Level
- Recurring Tasks
- Due Dates & Reminders

### Intermediate Level
- Priorities
- Tags
- Search
- Filter
- Sort

### Architecture
- Event-driven architecture with Kafka
- Dapr for distributed application runtime
- Microservices deployed on Kubernetes
- CI/CD pipeline with GitHub Actions

## Technologies Used

- Python (FastAPI) for backend API
- Next.js for frontend
- Kafka for event streaming
- Dapr for distributed application runtime
- Kubernetes for orchestration
- Minikube for local development
- Azure AKS/GKE for cloud deployment

## Project Structure

```
├── api/                 # Backend API with FastAPI and MCP tools
├── frontend/            # Next.js frontend application
├── kafka/               # Kafka configurations and schemas
├── dapr/                # Dapr component configurations
├── deployments/         # Kubernetes deployment manifests
├── minikube/            # Minikube-specific configurations
├── docs/                # Documentation
└── .github/workflows/   # CI/CD pipelines
```

## Getting Started

1. Clone the repository
2. Install prerequisites (Docker, kubectl, minikube, dapr)
3. Follow the local deployment guide in the docs