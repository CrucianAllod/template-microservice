import pickle
from collections.abc import Callable, Awaitable

from redis.asyncio import Redis
from redis.typing import AbsExpiryT, EncodableT, ExpiryT, KeyT, ResponseT
from config import RedisConfig
from src.usecases.interfaces.cache_interface import Cache


class RedisClient(Cache):
    def __init__(self, redis_config: RedisConfig) -> None:
        self.db = Redis(
            host=redis_config.redis_host,
            port=redis_config.redis_port,
            db=redis_config.redis_db,
            username=redis_config.redis_user,
            password=redis_config.redis_password,
        )

    async def get(self, key: KeyT) -> ResponseT:
        return await self.db.get(name=key)

    async def set(
            self,
            key: KeyT,
            value: EncodableT,
            *args: ExpiryT | AbsExpiryT | bool | None,
            **kwargs: ExpiryT | AbsExpiryT | bool | None,
    ) -> ResponseT:
        return await self.db.set(key, value, *args, **kwargs)

    async def delete(self, *keys: KeyT) -> ResponseT:
        return await self.db.delete(*keys)

    async def exists(self, *keys: KeyT) -> ResponseT:
        return await self.db.exists(*keys)

    async def get_cached_or_call(self, key: KeyT, expire_time: ExpiryT) -> Callable[
        [Callable[..., Awaitable]],
        Callable[..., Awaitable]
    ]:
        def outer(func: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
            async def inner(*args, **kwargs):
                if result := await self.get(key):
                    return pickle.loads(result)
                result = await func(*args, **kwargs)
                to_cache = pickle.dumps(result)
                await self.set(key=key, value=to_cache, ex=expire_time)
                return result

            return inner

        return outer