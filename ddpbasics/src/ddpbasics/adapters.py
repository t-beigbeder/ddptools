from typing import Generator, Any


def file_streamer(fp: str, size: int = 128 * 1024) -> Generator[bytes]:
    with open(fp, "rb") as fd:
        while True:
            bs = fd.read(size)
            if not len(bs):
                return
            yield bs


class StreamReader:
    def __init__(self, streamer: Generator[bytes]) -> None:
        self.streamer = streamer
        self.left = bytes()

    def read(self, size: int = -1) -> bytes:
        if size == -1:
            bs = self.left
            for chunk in self.streamer:
                bs += chunk
            return bs
        bs = bytes()
        while len(bs) != size:
            if len(self.left) >= size:
                bs = self.left[0:size]
                self.left = self.left[size:-1]
                return bs
            bs = self.left
            chunk2 = next(self.streamer, None)
            if chunk2 is None:
                self.left = bytes()
                return bs
            chunk = chunk2
            if len(bs) + len(chunk) < size:
                bs += chunk
                self.left = bs
                continue
            ln = len(bs)
            bs += chunk[:size-len(bs)]
            self.left = chunk[size-ln:-1]
            return bs
        return bs


def stream_reader(streamer: Generator[bytes]) -> Any:
    return StreamReader(streamer)
