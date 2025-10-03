import json
from collections.abc import Awaitable, Callable
from types import TracebackType
from typing import Self, Any

from redis.asyncio import Redis

from src.usecases.errors import ClientNotInitializedError
from src.usecases.interfaces.cache_interface import Cache


class RedisCacheRepository(Cache):
    def __init__(
            self,
            prefix: str = "",
            **redis_kwargs,
    ) -> None:
        self.prefix = prefix + ":" if prefix else ""
        self._redis_kwargs = redis_kwargs
        self._redis_kwargs["decode_responses"] = True
        self._redis_client: Redis | None = None

    async def build_client(self) -> Redis:
        return Redis(**self._redis_kwargs)

    async def __aenter__(self) -> Self:
        self._redis_client = await self.build_client()
        await self._redis_client.__aenter__()
        return self

    @property
    def _client(self) -> Redis:
        if self._redis_client is None:
            raise ClientNotInitializedError(self.__class__.__name__)
        return self._redis_client

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
    ) -> None:
        if self._redis_client:
            await self._redis_client.close()

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        async with self as repo:
            await repo._client.set(self.prefix + key, value, ex=ttl)

    async def get(self, key: str) -> str | None:
        async with self as repo:
            return await repo._client.get(self.prefix + key)

    async def delete(self, *keys: str) -> None:
        if not keys:
            return
        async with self as repo:
            await repo._client.delete(*[self.prefix + key for key in keys])

    async def pop(self, key: str) -> str | None:
        async with self as repo:
            return await repo._client.getdel(self.prefix + key)

    async def keys(self, prefix: str = "") -> list[str]:
        async with self as repo:
            cursor, keys = (0, [])
            while True:
                cursor, keys_page = await repo._client.scan(cursor=cursor, match=self.prefix + prefix + "*")
                keys.extend([key[len(self.prefix):] for key in keys_page])
                if cursor == 0:
                    return keys

    async def clear(self) -> None:
        keys_to_delete = await self.keys()
        if not keys_to_delete:
            return
        await self.delete(*keys_to_delete)

    async def get_cached_or_call[T](
            self,
            func: Callable[..., Awaitable[T]],
            *args: Any,
            key: str,
            ttl: int | None = None,
            **kwargs: Any,
    ) -> T:
        async with self as repo:
            if cached := await repo.get(key):
                return json.loads(cached)

            result = await func(*args, **kwargs)
            try:
                if hasattr(result, 'model_dump_json'):
                    value_to_cache = result.model_dump_json()
                else:
                    value_to_cache = json.dumps(result)
            except TypeError as e:
                raise TypeError(f"The result of function {func.__name__} is not JSON serializable: {e}")

            await repo.set(key=key, value=value_to_cache, ttl=ttl)
            return result