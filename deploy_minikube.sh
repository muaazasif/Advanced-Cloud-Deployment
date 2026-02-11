#!/bin/bash

# Script to deploy the Todo Chatbot application to Minikube with Dapr and Kafka

set -e  # Exit on any error

echo "Starting Minikube deployment..."

# Check if minikube is installed
if ! command -v minikube &> /dev/null; then
    echo "Minikube is not installed. Please install minikube first."
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Start Minikube
echo "Starting Minikube..."
minikube start

# Enable required Minikube addons
minikube addons enable ingress
minikube addons enable metrics-server

# Check if dapr is installed
if ! command -v dapr &> /dev/null; then
    echo "Installing Dapr CLI..."
    wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash
fi

# Initialize Dapr on Kubernetes
echo "Initializing Dapr..."
dapr init -k

# Wait for Dapr to be ready
echo "Waiting for Dapr to be ready..."
kubectl wait --for=condition=ready pod -l app=dapr-operator --namespace=dapr-system --timeout=300s

# Build Docker images
echo "Building Docker images..."
eval $(minikube docker-env)
docker build -t todo-api:latest .
docker build -t todo-frontend:latest ./frontend

# Deploy Kafka to Minikube
echo "Deploying Kafka..."
kubectl apply -f minikube/kafka-deployment.yaml

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
kubectl wait --for=condition=ready pod -l app=kafka --timeout=300s

# Deploy Dapr components
echo "Deploying Dapr components..."
kubectl apply -f dapr/

# Wait for Dapr components to be ready
kubectl wait --for=condition=ready pod -l app=todo-api --timeout=600s || true

# Deploy the application
echo "Deploying the application..."
kubectl apply -f deployments/api-deployment.yaml
kubectl apply -f deployments/frontend-deployment.yaml

# Wait for deployments to be ready
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=ready pod -l app=todo-api --timeout=600s
kubectl wait --for=condition=ready pod -l app=todo-frontend --timeout=600s

echo "Application deployed successfully!"
echo "API URL: $(minikube service todo-api-service --url)"
echo "Frontend URL: $(minikube service todo-frontend-service --url)"

echo "Deployment completed!"