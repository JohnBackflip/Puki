import aio_pika
import json
import os
from typing import Dict, Any

class EventPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    
    async def connect(self):
        """Connect to RabbitMQ"""
        if self.test_mode:
            print("Test mode: Skipping RabbitMQ connection")
            return
            
        try:
            # Get RabbitMQ configuration from environment variables
            rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
            rabbitmq_user = os.getenv("RABBITMQ_USER", "guest")
            rabbitmq_pass = os.getenv("RABBITMQ_PASS", "guest")
            
            # Create connection
            self.connection = await aio_pika.connect_robust(
                f"amqp://{rabbitmq_user}:{rabbitmq_pass}@{rabbitmq_host}/"
            )
            
            # Create channel
            self.channel = await self.connection.channel()
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                "hotel_events",
                aio_pika.ExchangeType.TOPIC
            )
            
        except Exception as e:
            print(f"Error connecting to RabbitMQ: {e}")
            self.connection = None
            self.channel = None
            self.exchange = None
    
    async def publish(self, routing_key: str, message: Dict[str, Any]):
        """Publish an event"""
        if self.test_mode:
            print(f"Test mode: Would publish {message} to {routing_key}")
            return
            
        if not self.exchange:
            print("No RabbitMQ connection available")
            return
            
        try:
            # Convert message to JSON
            message_body = json.dumps(message).encode()
            
            # Create message
            message = aio_pika.Message(
                body=message_body,
                content_type="application/json"
            )
            
            # Publish message
            await self.exchange.publish(
                message,
                routing_key=routing_key
            )
            
        except Exception as e:
            print(f"Error publishing message: {e}")
    
    async def close(self):
        """Close the connection"""
        if self.test_mode:
            return
            
        try:
            if self.connection:
                await self.connection.close()
        except Exception as e:
            print(f"Error closing connection: {e}")
        finally:
            self.connection = None
            self.channel = None
            self.exchange = None 