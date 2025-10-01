import asyncio
import logging

_log = logging.getLogger(__name__)


class ConsumerUseCase:

    @staticmethod
    async def process_inbound_message(data: dict):
        _log.info(f"WORKER: ✅ Message consumed. Processing data: {data}")
        await asyncio.sleep(1)
        _log.info(f"WORKER: Finished processing data: {data['content']}")