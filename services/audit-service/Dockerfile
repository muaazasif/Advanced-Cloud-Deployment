# Dockerfile for Audit Service
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy poetry files
COPY ./pyproject.toml ./poetry.lock* /app/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-interaction

# Copy project
COPY . /app/

# Run the application
CMD ["python", "-m", "audit_service.main"]