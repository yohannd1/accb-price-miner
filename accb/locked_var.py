from typing import TypeVar, Generic, Any
from threading import Lock

T = TypeVar("T")


class LockedVar(Generic[T]):
    def __init__(self, value: T) -> None:
        self._value = value
        self._lock = Lock()

    def set(self, value: T) -> None:
        with self:
            self._value = value

    def __enter__(self) -> T:
        self._lock.__enter__()
        return self._value

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        self._lock.__exit__(*args, **kwargs)
