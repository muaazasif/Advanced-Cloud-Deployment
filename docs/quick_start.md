# Quick Start Guide

## Local Development Setup

### Prerequisites
- Docker
- Python 3.9+
- Poetry (recommended) or pip
- kubectl
- minikube (for local Kubernetes)
- dapr CLI

### Step 1: Clone and Setup
```bash
git clone https://github.com/muaazasif/Advanced-Cloud-Deployment.git
cd Advanced-Cloud-Deployment

# Install dependencies
poetry install  # or pip install -r requirements.txt
```

### Step 2: Start Local Infrastructure
```bash
# Start Kafka and PostgreSQL locally
docker-compose up -d

# Wait for services to be ready
sleep 30
```

### Step 3: Run the Application
```bash
# Run the API directly
poetry run dev

# Or run with Dapr
dapr run --app-id todo-api --app-port 8000 -- python -m api.main
```

The API will be available at `http://localhost:8000`.

## Minikube Deployment

### Step 1: Start Minikube
```bash
minikube start
minikube addons enable ingress
```

### Step 2: Install Dapr
```bash
dapr init -k
```

### Step 3: Deploy the Application
```bash
# Build Docker images
eval $(minikube docker-env)
docker build -t todo-api:latest .
docker build -t todo-frontend:latest ./frontend

# Deploy Kafka
kubectl apply -f minikube/kafka-deployment.yaml

# Deploy Dapr components
kubectl apply -f dapr/

# Deploy the application
kubectl apply -f deployments/

# Check deployment status
kubectl get pods
```

### Step 4: Access the Application
```bash
minikube service todo-api-service
minikube service todo-frontend-service
```

## Environment Variables

The application uses the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `sqlite:///./test.db` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker addresses | `localhost:9092` |
| `USE_DAPR` | Enable Dapr integration | `false` |

## API Endpoints

### Tasks Management
- `GET /tasks/` - Get all tasks with filtering and sorting
- `POST /tasks/` - Create a new task
- `GET /tasks/{task_id}` - Get a specific task
- `PUT /tasks/{task_id}` - Update a task
- `DELETE /tasks/{task_id}` - Delete a task
- `POST /tasks/{task_id}/complete` - Mark a task as complete

### Query Parameters for GET /tasks/
- `status`: Filter by task status (todo, in_progress, completed)
- `priority`: Filter by priority (low, medium, high)
- `tag`: Filter by tag
- `due_after`: Filter tasks due after this date
- `due_before`: Filter tasks due before this date
- `search`: Search in title and description
- `sort_by`: Sort by (created_at, due_date, priority)
- `sort_order`: Sort order (asc, desc)
- `skip`: Number of records to skip
- `limit`: Maximum number of records to return

## Example Usage

### Create a Task
```bash
curl -X POST http://localhost:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete project",
    "description": "Finish the advanced cloud deployment project",
    "priority": "high",
    "due_date": "2023-12-31T23:59:59",
    "tags": "work,priority",
    "recurrence_pattern": "weekly"
  }'
```

### Get Tasks with Filters
```bash
curl "http://localhost:8000/tasks/?status=todo&priority=high&sort_by=due_date&sort_order=asc"
```

### Complete a Task
```bash
curl -X POST http://localhost:8000/tasks/1/complete
```

## Troubleshooting

### Common Issues

1. **Kafka Connection Issues**
   - Ensure Kafka is running: `docker-compose ps`
   - Check Kafka logs: `docker-compose logs kafka`

2. **Database Connection Issues**
   - Verify PostgreSQL is accessible
   - Check DATABASE_URL environment variable

3. **Dapr Sidecar Issues**
   - Ensure Dapr is installed: `dapr --version`
   - Check Dapr status: `dapr status -k`

4. **Minikube Service Access**
   - Use `minikube tunnel` in a separate terminal for LoadBalancer services
   - Or use `minikube service <service-name> --url` to get the URL

### Useful Commands

```bash
# Check all pods
kubectl get pods

# Check logs for a specific pod
kubectl logs -l app=todo-api

# Port forward to access services locally
kubectl port-forward svc/todo-api-service 8080:80

# Check Dapr sidecars
kubectl get pods -l app=todo-api -o yaml | grep dapr
```
