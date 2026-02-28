import functools
import hashlib
import pathlib
import queue
import threading
from typing import Generator

from ddpbasics import adapters, gllk, xdg
from . import s3utils


COPY_BUFSIZE = 64 * 1024

gllk.initialize()


@functools.lru_cache(maxsize=4096)
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


def cache_streamer(
    name: str, category: str, suffix: str, streamer: Generator[bytes]
) -> Generator[bytes]:
    cf = pathlib.Path(get_cache_path_for(name, category, suffix))
    if cf.exists():
        yield from adapters.file_streamer(str(cf))
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


@functools.lru_cache(maxsize=4096)
def get_s3_cache_path_for(
    name: str,
    category: str,
    suffix: str = "",
) -> str:
    hn = hashlib.sha256(bytes(name, "utf-8")).digest().hex()
    return f"cache/otvl/data/{category}/{hn}{suffix}"


def _s3_stream_uploader(
    bucket: str,
    object_path: str,
    profile_name: str | None,
    chunks_queue: queue.Queue,
) -> None:
    def _streamer() -> Generator[bytes]:
        while True:
            chunk = chunks_queue.get()
            chunks_queue.task_done()
            if chunk is None:
                return
            yield chunk
    s3utils.upload(_streamer(), bucket, object_path, profile_name)


def s3_cache_streamer(
    bucket: str,
    profile_name: str | None,
    name: str,
    category: str,
    suffix: str,
    streamer: Generator[bytes],
) -> Generator[bytes]:
    object_path = get_s3_cache_path_for(name, category, suffix)
    if s3utils.exists(bucket, object_path, profile_name):
        yield from s3utils.download(bucket, object_path, profile_name)
        return
    nl = None
    ln = f"s3_cache_streamer:{object_path}"
    try:
        nl = gllk.GlDict().named_lock_get(ln)
        chunks_queue: queue.Queue = queue.Queue(32)
        ssu_thread = threading.Thread(
            target=_s3_stream_uploader,
            args=(bucket, object_path, profile_name, chunks_queue),
            daemon=True,
        )
        ssu_thread.start()
        for chunk in streamer:
            yield chunk
            chunks_queue.put(chunk)
        chunks_queue.put(None)
        ssu_thread.join()
    except Exception:
        raise
    finally:
        if nl:
            gllk.GlDict().named_lock_delete(ln)
