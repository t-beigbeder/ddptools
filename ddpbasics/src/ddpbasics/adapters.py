import io
from typing import Any, Generator
import urllib.request


def file_streamer(fp: str, size: int = 128 * 1024) -> Generator[bytes]:
    with open(fp, "rb") as fd:
        while True:
            bs = fd.read(size)
            if not len(bs):
                return
            yield bs


def url_streamer(url: str, size: int = 128 * 1024) -> Generator[bytes]:
    with urllib.request.urlopen(url) as is_:
        while True:
            bs = is_.read(size)
            if not len(bs):
                return
            yield bs


class _StreamReader:
    def __init__(self, streamer: Generator[bytes]) -> None:
        self.streamer = streamer
        self.left = bytes()

    def read(self, size: int = -1) -> bytes:
        if size == -1:
            bs = self.left
            for chunk in self.streamer:
                bs += chunk
            self.left = bytes()
            return bs

        if len(self.left) >= size:
            bs = self.left[0:size]
            self.left = self.left[size:]
            return bs

        bs = bytes()
        while len(bs) != size:
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
            bs += chunk[: size - len(bs)]
            self.left = chunk[size - ln:]
            return bs
        return bs


def stream_reader(streamer: Generator[bytes]) -> Any:
    return _StreamReader(streamer)


class StringOThenI(io.StringIO):
    def __init__(
        self, initial_value: str | None = "", newline: str | None = "\n"
    ) -> None:
        super().__init__(initial_value, newline)
        self.seeked = False

    def write(self, s: str, /) -> int:
        self.seeked = False
        return super().write(s)

    def read(self, size: int | None = -1, /) -> str:
        if not self.seeked:
            self.seek(0)
            self.seeked = True
        return super().read(size)

    def __str__(self) -> str:
        return self.read()
