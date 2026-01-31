import functools
import hashlib
import os
import pathlib
import threading
from typing import Callable, Generator, IO

from ddpbasics import gllk, xdg


COPY_BUFSIZE = 64 * 1024

gllk.initialize()


class HashError(Exception):
    pass


@functools.lru_cache
def _get_cache_path_df_for(
    name: str,
    category: str = "default",
    suffix: str = "",
) -> tuple[str, str]:
    hn = hashlib.sha256(bytes(name, "utf-8")).digest().hex()
    return (
        f"{xdg.xdg_cache_dir()}/otvl/data/{category}/{hn[0:3]}",
        f"{hn[3:]}{suffix}",
    )


def get_cache_path_for(
    name: str,
    category: str = "default",
    suffix: str = "",
) -> str:
    return "/".join(_get_cache_path_df_for(name, category, suffix))


def _streamer(fp: pathlib.Path) -> Generator[bytes]:
    with open(fp, "rb") as fd:
        while True:
            bs = fd.read(COPY_BUFSIZE)
            if not len(bs):
                return
            yield bs


def cache_streamer(
    name: str, category: str, suffix: str, streamer: Generator[bytes]
) -> Generator[bytes]:
    cf = pathlib.Path(get_cache_path_for(name, category, suffix))
    if cf.exists():
        yield from _streamer(cf)
        return
    nl = None
    ln = f"cache_streamer:{cf}"
    try:
        nl = gllk.GlDict().named_lock_get(ln)
        cf.parent.mkdir(parents=True, exist_ok=True)
        with cf.open("wb", buffering=COPY_BUFSIZE) as of:
            for chunk in streamer:
                of.write(chunk)
                yield chunk
    except Exception:
        raise
    finally:
        if nl:
            gllk.GlDict().named_lock_delete(ln)


def _copy(fdst, is_binary, fsrc, length, hashes, hr):
    while buf := fsrc.read(length):
        bbuf = None
        for h in hashes:
            if bbuf is None:
                bbuf = bytes(str(buf), "utf-8") if not is_binary else buf
            hr[h].update(bbuf)
        fdst.write(buf)


class _FilesLock:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.files_locks: dict[str, threading.Lock] = {}

    def acquire_file_locker(self, path: str) -> threading.Lock:
        with self.lock:
            if path not in self.files_locks:
                self.files_locks[path] = threading.Lock()
            return self.files_locks[path]

    def release_file_locker(self, path: str):
        with self.lock:
            if path in self.files_locks:
                if not self.files_locks[path].locked():
                    del self.files_locks[path]


@functools.cache
def get_files_locker() -> _FilesLock:
    return _FilesLock()


def stream_from_cache(name: str, category: str, suffix: str, streamer):
    cp = pathlib.Path(get_cache_path_for(name, category, suffix))
    if cp.exists():
        with cp.open(mode="rb") as if_:
            for bs in if_:
                yield bs


def _cache(
    name: str,
    fsrc,
    src_path: str | None,
    category: str,
    mode: str,
    length: int,
    suffix: str,
    hashes: dict[str, str],
) -> str:
    is_binary = "b" in mode
    if not length:
        length = COPY_BUFSIZE
    cd, fn = _get_cache_path_df_for(name, category, suffix)
    cf = f"{cd}/{fn}"
    try:
        cfl = get_files_locker().acquire_file_locker(cf)
        with cfl:
            if not pathlib.Path(cf).exists():
                hr = {h: hashlib.new(h) for h in hashes}
                pathlib.PosixPath(cd).mkdir(parents=True, exist_ok=True)
                wmode = "wb" if is_binary else "w"
                with pathlib.PosixPath(cf).open(mode=wmode, buffering=length) as fdst:
                    if src_path is not None:
                        rmode = "rb" if is_binary else "r"
                        with open(src_path, rmode) as fsrc:
                            _copy(fdst, is_binary, fsrc, length, hashes, hr)
                    else:
                        _copy(fdst, is_binary, fsrc, length, hashes, hr)
                for h in hashes:
                    if hashes[h] and hashes[h] != hr[h].digest().hex():
                        os.remove(pathlib.PosixPath(cf))
                        raise HashError(
                            f"category {category} name {name} hash {h} wanted {hashes[h]} actual {hr[h].digest().hex()}"
                        )
                    hashes[h] = hr[h].digest().hex()
    finally:
        get_files_locker().release_file_locker(cf)
    return cf


def stream_cache(
    name: str,
    fsrc,
    category="default",
    mode: str = "r",
    length=0,
    suffix="",
    hashes: dict[str, str] = {},
) -> IO:
    if not length:
        length = COPY_BUFSIZE
    cf = _cache(name, fsrc, None, category, mode, length, suffix, hashes)
    return pathlib.Path(cf).open(mode=mode, buffering=length)


def stream_cache_path(
    name: str,
    fsrc,
    category="default",
    mode: str = "r",
    length=0,
    suffix="",
    hashes: dict[str, str] = {},
) -> str:
    return _cache(name, fsrc, None, category, mode, length, suffix, hashes)


def file_cache(
    name: str,
    src_path: str,
    category="default",
    mode: str = "r",
    length=0,
    suffix="",
    hashes: dict[str, str] = {},
) -> IO:
    if not length:
        length = COPY_BUFSIZE
    cf = _cache(name, None, src_path, category, mode, length, suffix, hashes)
    return pathlib.Path(cf).open(mode=mode, buffering=length)


def file_cache_path(
    name: str,
    src_path: str,
    category="default",
    mode: str = "r",
    length=0,
    suffix="",
    hashes: dict[str, str] = {},
) -> str:
    return _cache(name, None, src_path, category, mode, length, suffix, hashes)


def get_cache_or_stream(
    name: str,
    get_stream_fn: Callable,
    category="default",
    mode: str = "r",
    length=0,
    suffix="",
    hashes: dict[str, str] = {},
) -> IO:
    if not length:
        length = COPY_BUFSIZE
    fcp = get_cache_path_for(name, category, suffix)
    if os.path.exists(fcp):
        # make sure other thread creating it is done
        cfl = get_files_locker().acquire_file_locker(fcp)
        with cfl:
            pass
        get_files_locker().release_file_locker(fcp)
        return pathlib.Path(fcp).open(mode=mode, buffering=length)
    # will open the stream with get_stream_fn
    return stream_cache(name, get_stream_fn(), category, mode, length, suffix, hashes)
