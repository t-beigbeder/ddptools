from typing import Generator

import boto3
import botocore.exceptions

from .adapters import stream_reader


class S3UtilsFileError(Exception):
    pass


def delete(bucket: str, object_path: str, profile_name: str | None = None) -> None:
    b3s = boto3.Session(profile_name=profile_name)
    s3c = b3s.client("s3")
    _ = s3c.delete_object(Bucket=bucket, Key=object_path)
    # always ok


def upload(
    streamer: Generator[bytes],
    bucket: str,
    object_path: str,
    profile_name: str | None = None,
) -> None:
    b3s = boto3.Session(profile_name=profile_name)
    s3c = b3s.client("s3")
    # not documented elsewhere
    # https://botocore.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html
    s3c.upload_fileobj(stream_reader(streamer), bucket, object_path)


def download(
    bucket: str,
    object_path: str,
    profile_name: str | None = None,
) -> Generator[bytes]:
    b3s = boto3.Session(profile_name=profile_name)
    s3_obj = b3s.resource("s3").Object(bucket_name=bucket, key=object_path)
    s3_body = s3_obj.get()["Body"] if s3_obj is not None else None
    if s3_body is None:
        raise S3UtilsFileError(f"s3 file {bucket} {object_path} read error")
    # https://botocore.amazonaws.com/v1/documentation/api/latest/reference/response.html
    # botocore.response.StreamingBody / IOBase
    with s3_body:
        while True:
            bs = s3_body.read(128 * 1024)
            yield bs
            if not bs:
                return


def exists(
    bucket: str,
    object_path: str,
    profile_name: str | None = None,
) -> bool:
    b3s = boto3.Session(profile_name=profile_name)
    s3c = b3s.client("s3")
    try:
        s3c.head_object(Bucket=bucket, Key=object_path)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise e
    return True
