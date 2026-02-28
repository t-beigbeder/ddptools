import threading
import typing
import queue
import logging


_gllock: threading.Lock | None = None
_gldict: typing.Any | None = None
_glqueue: typing.Any | None = None


def initialize() -> None:
    if not threading.current_thread() is threading.main_thread():
        raise Exception("gllk.initialize must be called from the main thread")
    global _gllock
    if _gllock is None:
        _gllock = threading.Lock()


class _GlDict:
    def __init__(self) -> None:
        global _gldict
        self.lock = threading.Lock()
        self.d: dict[typing.Any, typing.Any] = dict()
        assert _gldict is None
        _gldict = self

    def put(self, k, v) -> None:
        with self.lock:
            self.d[k] = v

    def exists(self, k) -> bool:
        return k in self.d

    def delete(self, k) -> None:
        with self.lock:
            del self.d[k]

    def get(self, k) -> typing.Any:
        return self.d[k]

    def named_lock_get(self, k) -> threading.Lock:
        acquired = False
        while True:
            try:
                self.lock.acquire()
                acquired = True
                if k in self.d:
                    logging.debug(f"named_lock_get {k}: already acquired")
                    nl: threading.Lock = self.d[k]
                    acquired = False
                    self.lock.release()
                    with nl:
                        logging.debug(f"named_lock_get {k}: looping")
                        pass
                    continue
                self.d[k] = threading.Lock()
                self.d[k].acquire()
                logging.debug(f"named_lock_get {k}: acquired")
                return self.d[k]
            finally:
                if acquired:
                    logging.debug(f"named_lock_get {k}: release global")
                    self.lock.release()

    def named_lock_delete(self, k) -> None:
        with self.lock:
            logging.debug(f"named_lock_delete {k}")
            nl: threading.Lock = self.d[k]
            nl.release()
            del self.d[k]


def GlDict() -> _GlDict:
    global _gldict
    if _gldict is None:
        assert _gllock is not None
        with _gllock:
            if _gldict is None:
                _gldict = _GlDict()
    return _gldict


class _GlQueue:
    def __init__(self) -> None:
        global _glqueue
        self.lock = threading.Lock()
        self.queues: dict[str, queue.Queue[bytes]] = dict()
        self.max_value_sizes: dict[str, int] = dict()
        assert _glqueue is None
        _glqueue = self

    def create(self, topic: str, size: int, max_value_size: int) -> None:
        with self.lock:
            if topic in self.queues:
                raise KeyError(f"topic {topic} already created")
            self.queues[topic] = queue.Queue(size)
            self.max_value_sizes[topic] = max_value_size

    def delete(self, topic: str) -> None:
        self.queues[topic].shutdown(immediate=True)
        with self.lock:
            del self.queues[topic]
            del self.max_value_sizes[topic]

    def exists(self, topic: str) -> bool:
        return topic in self.queues

    def shutdown(self, topic: str, immediate) -> None:
        self.queues[topic].shutdown(immediate)

    def put(self, topic: str, value: bytes) -> None:
        if len(value) >= self.max_value_sizes[topic]:
            raise ValueError(f"len {len(value)}")
        self.queues[topic].put(value)

    def get(self, topic: str) -> bytes | None:
        try:
            v = self.queues[topic].get()
            self.queues[topic].task_done()
            return v
        except queue.ShutDown:
            return None

    def join(self, topic: str) -> None:
        return self.queues[topic].join()


def GlQueue() -> _GlQueue:
    global _glqueue
    if _glqueue is None:
        assert _gllock is not None
        with _gllock:
            if _glqueue is None:
                _glqueue = _GlQueue()
    return _glqueue
