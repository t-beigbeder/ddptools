import os
import pathlib
from typing import Generator

import boto3
from botocore.exceptions import ClientError
from ddpbasics.cache import cache_streamer, get_cache_path_for
from ddpbasics.sqix import SqixFileConsumption, SqixFileCreation, SqixFileError


def _file_streamer(fp: str) -> Generator[bytes]:
    with open(fp, "rb") as fd:
        while True:
            bs = fd.read(128 * 1024)
            if not len(bs):
                return
            yield bs


class S3SqixFileError(SqixFileError):
    pass


def _s3obj_streamer(
    bucket: str, object_path: str, profile_name: str | None = None
) -> Generator[bytes]:
    b3s = boto3.Session(profile_name=profile_name)
    s3_obj = b3s.resource("s3").Object(bucket_name=bucket, key=object_path)
    s3_body = s3_obj.get()["Body"] if s3_obj is not None else None
    if s3_body is None:
        raise S3SqixFileError(f"s3 file {bucket} {object_path} read error")
    # https://botocore.amazonaws.com/v1/documentation/api/latest/reference/response.html
    # botocore.response.StreamingBody / IOBase
    with s3_body:
        while True:
            bs = s3_body.read(128 * 1024)
            yield bs
            if not bs:
                return


class S3SqixFileCreation(SqixFileCreation):
    def __init__(
        self,
        bucket: str,
        temp_dir: str,
        path: str,
        category: str = "default",
        profile_name: str | None = None,
    ):
        self.s3c = None
        self.bucket = bucket
        self.object_path = path
        self.category = category

        b3s = boto3.Session(profile_name=profile_name)
        s3c = b3s.client("s3")
        try:
            _ = s3c.head_bucket(Bucket=bucket)
        except ClientError as e:
            raise S3SqixFileError(f"s3 file {bucket} {path} access error: {e}")
        self.s3c = s3c
        temp_path = f"{temp_dir}/{path}"
        os.makedirs(pathlib.Path(temp_path).parent, 0o700, exist_ok=True)
        super().__init__(temp_path)

    def _close(self):
        if self.s3c is None:
            return
        super()._close()
        if self.ofd is None:
            return
        for _ in cache_streamer(
            self.object_path, self.category, ".sqix", _file_streamer(self.path)
        ):
            pass
        with open(self.path, "rb") as f:
            self.s3c.upload_fileobj(f, self.bucket, self.object_path)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._close()
        return None

    def close(self):
        self._close()


class S3SqixFileService:
    def __init__(
        self,
        bucket: str,
        temp_dir: str,
        db_name: str,
        profile_name: str | None = None,
    ):
        self.bucket = bucket
        self.temp_dir = temp_dir
        self.db_name = db_name
        self.profile_name = profile_name
        self.nums: dict[str, int] = {}

    def new_s3sqix_file(self, category: str) -> S3SqixFileCreation:
        if category not in self.nums:
            self.nums[category] = -1
        self.nums[category] += 1
        return S3SqixFileCreation(
            self.bucket,
            self.temp_dir,
            f"{self.db_name}/{category}/{self.nums[category]}",
            category,
            self.profile_name,
        )


class S3SqixFileConsumption(SqixFileConsumption):
    def __init__(
        self,
        bucket: str,
        path: str,
        category: str = "default",
        profile_name: str | None = None,
    ):
        for _ in cache_streamer(
            path, category, ".sqix", _s3obj_streamer(bucket, path, profile_name)
        ):
            pass
        super().__init__(get_cache_path_for(path, category, ".sqix"))

    def _close(self):
        super()._close()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._close()
        return None

    def close(self):
        self._close()


class S3SqixEntryService:
    def __init__(
        self,
        bucket: str,
        profile_name: str | None = None,
    ):
        self.bucket = bucket
        self.profile_name = profile_name
        self.nums: dict[str, int] = {}

    def read_s3sqix_entry(self, path: str, category: str, index: int) -> bytes:
        sfc = S3SqixFileConsumption(self.bucket, path, category, self.profile_name)
        return sfc.read_entry(index)
