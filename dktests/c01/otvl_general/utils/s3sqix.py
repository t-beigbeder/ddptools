import os
import pathlib

import boto3
from botocore.exceptions import ClientError

from otvl_general.utils.cache import (
    get_cache_or_stream,
    get_cache_path_for,
    stream_cache,
)
from otvl_general.utils.sqix import SqixFileConsumption, SqixFileCreation, SqixFileError


class S3SqixFileError(SqixFileError):
    pass


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
        with open(self.path, "rb") as f:
            stream_cache(self.object_path, f, self.category, mode="rb", suffix=".sqix")
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


class S3Reader:
    def __init__(
        self,
        bucket: str,
        object_path: str,
        profile_name: str | None = None,
    ):
        self.bucket = bucket
        self.object_path = object_path
        self.profile_name = profile_name
        self.s3_body = None
        self.s3_obj = None

    def read(self, size: int | None = -1) -> bytes:
        if self.s3_body is None:
            b3s = boto3.Session(profile_name=self.profile_name)
            self.s3_obj = b3s.resource("s3").Object(
                bucket_name=self.bucket, key=self.object_path
            )
            self.s3_body = self.s3_obj.get()["Body"] if self.s3_obj is not None else None
        if self.s3_body is None:
            raise S3SqixFileError(
                f"s3 file {self.bucket} {self.object_path} read error"
            )
        return self.s3_body.read(size)


class S3SqixFileConsumption(SqixFileConsumption):
    def __init__(
        self,
        bucket: str,
        path: str,
        category: str = "default",
        profile_name: str | None = None,
    ):
        def _get_stream():
            return S3Reader(bucket, path, profile_name)

        with get_cache_or_stream(
            path, _get_stream, category, mode="rb", suffix=".sqix"
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
