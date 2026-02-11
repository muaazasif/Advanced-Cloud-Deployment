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

## Deployment Options

### Local Deployment with Minikube
1. Install prerequisites:
   - Docker
   - kubectl
   - minikube
   - dapr CLI

2. Run the deployment script:
   ```bash
   ./deploy_minikube.sh
   ```

### Cloud Deployment
The application can be deployed to:
- Azure AKS
- Google GKE
- Oracle OKE
- Railway (for simplified deployment)

### Railway Deployment
Railway provides a simple way to deploy the application:

1. Sign up at [Railway](https://railway.app/)
2. Create a new project and link it to this GitHub repository
3. Add the following environment variables:
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `KAFKA_BOOTSTRAP_SERVERS`: Your Kafka broker URL
   - `USE_DAPR`: Set to "false" for Railway deployment
4. Deploy the application using Railway's interface

### Production Deployment
For production deployments on cloud platforms:

1. Set up your cloud provider (Azure, GCP, or Oracle)
2. Create a Kubernetes cluster
3. Install Dapr in the cluster
4. Configure your Kafka provider (Redpanda Cloud, Confluent Cloud, or self-hosted)
5. Update the deployment configurations with your specific cloud settings
6. Deploy using kubectl

## Event-Driven Architecture

The application uses Kafka for event streaming:
- `task-events` topic: All task CRUD operations
- `reminders` topic: Scheduled reminder triggers
- `task-updates` topic: Real-time client sync

Services communicate through events rather than direct API calls, enabling loose coupling and scalability.

## Dapr Integration

Dapr provides the following building blocks:
- Pub/Sub: Kafka abstraction
- State Management: Conversation state storage
- Service Invocation: Inter-service communication
- Bindings: Cron triggers for scheduled reminders
- Secrets Management: Secure credential storage
