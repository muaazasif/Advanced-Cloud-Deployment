# Railway Environment Variables Configuration

The following environment variables should be set in your Railway project:

## Required Variables:
DATABASE_URL=postgresql://username:password@host:port/database_name
USE_DAPR=false

## Optional Variables (for Kafka, if you set up a managed service):
KAFKA_BOOTSTRAP_SERVERS=your-kafka-brokers-list