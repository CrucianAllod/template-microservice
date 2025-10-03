from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

class Cache(ABC):
    @abstractmethod
    async def get(self, key: str) -> str | None:
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        pass

    @abstractmethod
    async def delete(self, *keys: str) -> None:
        pass

    @abstractmethod
    async def pop(self, key: str) -> str | None:
        pass

    @abstractmethod
    async def keys(self, prefix: str = "") -> list[str]:
        pass

    @abstractmethod
    async def clear(self) -> None:
        pass

    @abstractmethod
    async def get_cached_or_call[T](
            self,
            func: Callable[..., Awaitable[T]],
            *args: Any,
            key: str,
            ttl: int | None = None,
            **kwargs: Any,
    ) -> T:
        pass