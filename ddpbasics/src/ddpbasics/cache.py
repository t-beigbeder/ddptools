import functools
import hashlib
import pathlib
from typing import Generator

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
