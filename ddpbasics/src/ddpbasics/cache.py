import functools
import hashlib
import pathlib
from typing import Generator

from ddpbasics import gllk, xdg, adapters
# import s3utils


COPY_BUFSIZE = 64 * 1024

gllk.initialize()


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


@functools.lru_cache
def get_s3_cache_path_for(
    name: str,
    category: str,
    suffix: str,
) -> str:
    hn = hashlib.sha256(bytes(name, "utf-8")).digest().hex()
    return f"cache/otvl/data/{category}/{hn}{suffix}"


# def s3_cache_streamer(
#     bucket: str, profile_name: str | None,
#     name: str, category: str, suffix: str, streamer: Generator[bytes]
# ) -> Generator[bytes]:
#     object_path = get_s3_cache_path_for(name, category, suffix)
#     if s3utils.exists(bucket, object_path, profile_name):
#         yield from s3utils.download(bucket, object_path, profile_name)
#         return
#     nl = None
#     ln = f"s3_cache_streamer:{cf}"
#     try:
#         nl = gllk.GlDict().named_lock_get(ln)

#         with cf.open("wb", buffering=COPY_BUFSIZE) as of:
#             for chunk in streamer:
#                 of.write(chunk)
#                 yield chunk
#     except Exception:
#         raise
#     finally:
#         if nl:
#             gllk.GlDict().named_lock_delete(ln)
