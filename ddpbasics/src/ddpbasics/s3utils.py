from typing import Generator
import boto3


def delete(bucket: str, object_path: str, profile_name: str | None = None) -> None:
    b3s = boto3.Session(profile_name=profile_name)
    s3c = b3s.client("s3")
    s3c.delete_object(Bucket=bucket, Key=object_path)


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
    s3c.upload_fileobj(None, bucket, object_path)
