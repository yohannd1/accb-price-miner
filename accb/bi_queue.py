from threading import Thread, Lock
from queue import Queue
from typing import Callable, Any

class BiQueue:
    """Um meio de comunicação many-to-1, iniciando um Thread responsável por receber as mensagens e responder algo.
    Só suporta uma request por vez, via `BiQueue.exchange()`
    """

    _sender_queue: Queue
    _receiver_queue: Queue
    _receiver_thread: Thread

    def __init__(self, handler_target: Callable[[Queue, Queue], None]) -> None:
        """Inicializa a classe.

        Um thread é criado, chamando `handler_target`, e passando duas filas: a primeira, de onde ele lê mensagens, e a segunda, onde ele coloca respostas.
        """
        self._sender_queue = Queue()
        self._receiver_queue = Queue()
        self._receiver_thread: Thread = Thread(target=lambda: handler_target(self._sender_queue, self._receiver_queue))
        self._receiver_thread.start()
        self._exchange_lock = Lock()

    def exchange(self, msg: Any) -> Any:
        with self._exchange_lock:
            self._sender_queue.put(msg)
            return self._receiver_queue.get()
