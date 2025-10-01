from abc import ABC, abstractmethod
from collections.abc import Callable

from redis.typing import AbsExpiryT, EncodableT, ExpiryT, KeyT, ResponseT


class Cache(ABC):
    @abstractmethod
    def get(self, key: KeyT) -> ResponseT:
        pass

    @abstractmethod
    def set(
        self,
        key: KeyT,
        value: EncodableT,
        *args: ExpiryT | AbsExpiryT | bool | None,
        **kwargs: ExpiryT | AbsExpiryT | bool | None,
    ) -> ResponseT:
        pass

    @abstractmethod
    def delete(self, *keys: KeyT) -> ResponseT:
        pass

    @abstractmethod
    def exists(self, *keys: KeyT) -> ResponseT:
        pass

    @abstractmethod
    def get_cached_or_call(self, key: KeyT, expire_time: ExpiryT) -> Callable:
        pass
