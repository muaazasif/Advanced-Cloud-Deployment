import pytest
from unittest.mock import AsyncMock, MagicMock
from api.kafka_producer import KafkaProducer
import aiokafka


@pytest.mark.asyncio
async def test_kafka_producer_initialization():
    """Test KafkaProducer initialization"""
    producer = KafkaProducer()
    
    # Mock the aiokafka.AIOKafkaProducer
    mock_aioproducer = AsyncMock(spec=aiokafka.AIOKafkaProducer)
    producer.producer = mock_aioproducer
    
    # Test that the producer was initialized properly
    assert producer is not None


@pytest.mark.asyncio
async def test_publish_event():
    """Test publishing an event to Kafka"""
    producer = KafkaProducer()
    
    # Mock the aiokafka.AIOKafkaProducer
    mock_aioproducer = AsyncMock(spec=aiokafka.AIOKafkaProducer)
    producer.producer = mock_aioproducer
    
    # Mock the start and stop methods
    producer.producer.start = AsyncMock()
    producer.producer.stop = AsyncMock()
    producer.producer.send_and_wait = AsyncMock()
    
    # Test publishing an event
    test_topic = "test-topic"
    test_event = {"event_type": "test.event", "data": "test_data"}
    
    await producer.publish_event(test_topic, test_event)
    
    # Verify that send_and_wait was called with the correct parameters
    producer.producer.send_and_wait.assert_called_once_with(
        test_topic,
        value=test_event
    )


@pytest.mark.asyncio
async def test_start_producer():
    """Test starting the Kafka producer"""
    producer = KafkaProducer()
    
    # Mock the aiokafka.AIOKafkaProducer
    mock_aioproducer = AsyncMock(spec=aiokafka.AIOKafkaProducer)
    producer.producer = mock_aioproducer
    
    # Mock the start method
    producer.producer.start = AsyncMock()
    
    await producer.start()
    
    # Verify that start was called
    producer.producer.start.assert_called_once()


@pytest.mark.asyncio
async def test_stop_producer():
    """Test stopping the Kafka producer"""
    producer = KafkaProducer()
    
    # Mock the aiokafka.AIOKafkaProducer
    mock_aioproducer = AsyncMock(spec=aiokafka.AIOKafkaProducer)
    producer.producer = mock_aioproducer
    
    # Mock the stop method
    producer.producer.stop = AsyncMock()
    
    await producer.stop()
    
    # Verify that stop was called
    producer.producer.stop.assert_called_once()