import asyncio
import json
import logging

import aio_pika

from src.config import RabbitMQConfig
from src.repositories.rabbit_repositories.rabbit_repository import BaseRabbitMQRepository
from src.usecases.interfaces.rabbit_interfaces.rabbit_out_in_interface import OutInRabbitMQRepositoryInterface

_log = logging.getLogger(__name__)

class OutInRabbitMQRepository(OutInRabbitMQRepositoryInterface, BaseRabbitMQRepository):

    def __init__(self):
        super().__init__()
        self.out_task_queue = None
        self.out_task_exchange = None
        self.in_task_queue = None
        self.in_task_exchange = None

    async def connect_and_declare(self) -> None:
        await self.connect()
        self.out_task_queue, self.out_task_exchange = await self._declare_queue_and_exchange(
            RabbitMQConfig().OUT_TASK_QUEUE,
            RabbitMQConfig().OUT_TASK_EXCHANGE,
            self.channel
        )
        self.in_task_queue, self.in_task_exchange = await self._declare_queue_and_exchange(
            RabbitMQConfig().IN_TASK_QUEUE,
            RabbitMQConfig().IN_TASK_EXCHANGE,
            self.channel
        )
        _log.info("In-specific queues declared successfully.")

    async def push_task(self, payload: str) -> None:
        try:
            if self.channel is None:
                _log.warning("Channel is closed or None. Reconnecting...")
                await self.connect_and_declare()

            message = aio_pika.Message(
                body=payload.encode("utf-8"),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type='application/json'
            )
            _log.debug(f"Publishing message to out_task_queue: {payload[:100]}...")

            await self.out_task_exchange.publish(message, RabbitMQConfig().OUT_TASK_QUEUE)

        except Exception as e:
            _log.error(f"Failed to publish message to RabbitMQ: {e}")
            raise

    async def consume_tasks(self, on_message_callback=None) -> None:
        while True:
            try:
                _log.info(f"Starting message consumption from {RabbitMQConfig().IN_TASK_QUEUE}")
                async with self.in_task_queue.iterator() as stream:
                    async for message in stream:
                        try:
                            async with message.process():
                                data = json.loads(message.body)
                                _log.info(f"Message received: {data}")

                                if on_message_callback:
                                    await on_message_callback(data)

                        except json.JSONDecodeError as e:
                            _log.error(f"Failed to parse message JSON: {e}, body: {message.body}")
                        except Exception as e:
                            _log.error(f"Error processing message: {e}")

            except aio_pika.AMQPException as e:
                _log.error(f"AMQP error in consumer: {e}, attempting reconnection...")
                await self.connect_and_declare()
            except Exception as e:
                _log.error(f"Unexpected error in consumer: {e}, restarting consumption...")
                await asyncio.sleep(5)