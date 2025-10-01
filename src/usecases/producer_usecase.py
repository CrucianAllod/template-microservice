import json
import logging

from src.usecases.interfaces.rabbit_interfaces.rabbit_out_in_interface import OutInRabbitMQRepositoryInterface

_log = logging.getLogger(__name__)


class ProducerUseCase:
    def __init__(self, rabbit_repo: OutInRabbitMQRepositoryInterface):
        self.rabbit_repo = rabbit_repo

    async def push_test_message(self, data: dict):
        payload_str = json.dumps(data)
        _log.info(f"API: Pushing task to RabbitMQ. Payload size: {len(payload_str)} bytes")
        await self.rabbit_repo.push_task(payload=payload_str)
        return {"status": "Task successfully pushed", "data": data}