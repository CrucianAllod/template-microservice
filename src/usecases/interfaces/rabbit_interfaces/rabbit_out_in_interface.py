from abc import ABC, abstractmethod


class OutInRabbitMQRepositoryInterface(ABC):

    @abstractmethod
    async def connect_and_declare(self) -> None:
       pass

    @abstractmethod
    async def push_task(self, payload: str) -> None:
        pass

    async def consume_tasks(self, on_message_callback=None) -> None:
        pass