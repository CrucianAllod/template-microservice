import asyncio
import logging
import sys

from src.container import container

from src.config import LoggingConfig
from src.usecases.consumer_usecase import ConsumerUseCase
from src.usecases.interfaces.rabbit_interfaces.rabbit_out_in_interface import OutInRabbitMQRepositoryInterface

_log = logging.getLogger(__name__)

logging.basicConfig(
    level=LoggingConfig().LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

async def message_handler(message_data: dict):
    try:
        consumer_usecase: ConsumerUseCase = container.resolve(ConsumerUseCase)
        _log.info(f"Worker task received. Starting processing.")
        await consumer_usecase.process_inbound_message(message_data)
        _log.info("Worker task processing completed successfully.")

    except Exception as e:
        _log.error(f"Error processing worker task: {e}")

async def main():
    _log.info("Starting RabbitMQ Worker...")
    try:
        rabbit_repo: OutInRabbitMQRepositoryInterface = container.resolve(OutInRabbitMQRepositoryInterface)

        await rabbit_repo.connect_and_declare()
        _log.info("Worker connected. Starting to listen to the queue...")
        await rabbit_repo.consume_tasks(on_message_callback=message_handler)

    except Exception as e:
        _log.critical(f"A critical error occurred while starting the worker: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _log.info("Worker stopped by user.")