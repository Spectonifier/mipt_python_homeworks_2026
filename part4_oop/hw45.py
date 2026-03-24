from collections.abc import Callable
from typing import Any

from part4_oop.interfaces import HasCache, K, Policy, Storage, V


class DictStorage(Storage[K, V]):
    def set(self, key: K, value: V) -> None:
        raise NotImplementedError

    def get(self, key: K) -> V | None:
        raise NotImplementedError

    def exists(self, key: K) -> bool:
        raise NotImplementedError

    def remove(self, key: K) -> None:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError


class LRUPolicy(Policy[K]):
    def register_access(self, key: K) -> None:
        raise NotImplementedError

    def get_key_to_evict(self) -> K | None:
        raise NotImplementedError


class FIFOPolicy(Policy[K]):
    def register_access(self, key: K) -> None:
        raise NotImplementedError

    def get_key_to_evict(self) -> K | None:
        raise NotImplementedError


class CachedProperty[V]:
    def __init__(self, func: Callable[..., V]) -> None: ...
    def __get__(self, instance: HasCache[Any, Any] | None, owner: type) -> V: ...  # type: ignore[empty-body]
