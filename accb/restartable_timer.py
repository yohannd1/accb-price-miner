from threading import Timer
from typing import Callable, Optional


class RestartableTimer:
    def __init__(self, timeout: float, callback: Callable[[], None]) -> None:
        self._timeout = timeout
        self._callback = callback
        self._timer: Optional[Timer] = None

    def start(self) -> None:
        if self._timer is not None:
            return

        self._timer = Timer(self._timeout, self._callback)
        self._timer.start()

    def cancel(self) -> None:
        if self._timer is None:
            return

        self._timer.cancel()
        self._timer = None
