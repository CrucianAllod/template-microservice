import logging
import aio_pika

from tenacity import retry, stop_after_delay, wait_fixed
from src.config import RabbitMQConfig

_log = logging.getLogger(__name__)


class BaseRabbitMQRepository:
    def __init__(self):
        self.connection = None
        self.channel = None

    @retry(
        stop=stop_after_delay(RabbitMQConfig().CONNECTION_TIMEOUT),
        wait=wait_fixed(RabbitMQConfig().RETRY_INTERVAL)
    )
    async def connect(self) -> None:
        try:
            _log.debug(f"Connecting to RabbitMQ: {RabbitMQConfig().URL}")
            self.connection = await aio_pika.connect_robust(RabbitMQConfig().URL)
            self.channel = await self.connection.channel()
            _log.info("Successfully connected to RabbitMQ")
        except Exception as e:
            _log.error(f"RabbitMQ connection failed: {e}")
            raise

    @staticmethod
    async def _declare_queue_and_exchange(queue_name: str, exchange_name: str, channel) -> (aio_pika.Queue, aio_pika.Exchange):
        _log.debug(f"Declaring queue {queue_name} and exchange {exchange_name}")
        exchange = await channel.declare_exchange(
            exchange_name,
            aio_pika.ExchangeType.DIRECT,
            durable=True,
            auto_delete=False
        )
        queue = await channel.declare_queue(
            queue_name,
            durable=True,
            arguments={'x-max-priority': 1}
        )
        await queue.bind(exchange, routing_key=queue_name)
        _log.debug(f"Queue {queue_name} and exchange {exchange_name} declared successfully")
        return queue, exchange