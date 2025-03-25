# room/events.py
import aio_pika
import json
import asyncio
from typing import Callable
import os

class EventPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        
    async def connect(self):
        if not self.connection:
            self.connection = await aio_pika.connect_robust(os.getenv("RABBITMQ_URL"))
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                "hotel_events", aio_pika.ExchangeType.TOPIC
            )
    
    async def publish(self, routing_key: str, message: dict):
        await self.connect()
        await self.exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key=routing_key
        )

class EventConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None
        
    async def connect(self):
        if not self.connection:
            self.connection = await aio_pika.connect_robust(os.getenv("RABBITMQ_URL"))
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                "hotel_events", aio_pika.ExchangeType.TOPIC
            )
            
    async def subscribe(self, routing_key: str, callback: Callable):
        await self.connect()
        self.queue = await self.channel.declare_queue("", exclusive=True)
        await self.queue.bind(self.exchange, routing_key)
        
        async def process_message(message: aio_pika.IncomingMessage):
            async with message.process():
                data = json.loads(message.body.decode())
                await callback(data)
        
        await self.queue.consume(process_message)

# Global event publisher instance
_publisher = EventPublisher()

async def publish_event(routing_key: str, message: dict):
    """Publish an event to RabbitMQ"""
    await _publisher.publish(routing_key, message)