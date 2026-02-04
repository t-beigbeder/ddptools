import threading
import typing
import queue


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
        assert _gllock is not None
        self.lock = _gllock
        self.d: dict = dict()
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


def GlDict() -> _GlDict:
    global _gldict
    assert _gllock is not None
    with _gllock:
        if _gldict is None:
            _gldict = _GlDict()
    return _gldict


class _GlQueue:
    def __init__(self) -> None:
        global _glqueue
        assert _gllock is not None
        self.lock = _gllock
        self.queues: dict = dict()
        self.max_value_sizes: dict = dict()
        assert _glqueue is None
        _glqueue = self

    def create(self, topic: str, size: int, max_value_size: int) -> None:
        with self.lock:
            if topic in self.queues:
                raise KeyError(f"topic {topic} already created")
            self.queues[topic] = queue.Queue(size)
            self.max_value_sizes[topic] = max_value_size

    def delete(self, topic: str) -> None:
        with self.lock:
            self.queues[topic].shutdown(immediate=True)
            del self.queues[topic]
            del self.max_value_sizes[topic]

    def exists(self, topic: str) -> bool:
        return topic in self.queues

    def shutdown(self, topic: str, immediate) -> None:
        with self.lock:
            self.queues[topic].shutdown(immediate)

    def put(self, topic: str, value: bytes) -> None:
        with self.lock:
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
    assert _gllock is not None
    with _gllock:
        if _glqueue is None:
            _glqueue = _GlQueue()
    return _glqueue
