import os
from enum import Enum
from urllib.parse import urlencode

import boto3
from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client
from mypy_boto3_s3.type_defs import (
    GetObjectTaggingOutputTypeDef,
    HeadObjectOutputTypeDef,
)


class S3Path(Enum):
    path_to_obj = "path/to/obj"


class S3Bucket(Enum):
    default = "bucket-name"


class AWSSettings:
    access_key_id: str
    secret_access_key: str
    region: str


config = AWSSettings()


class S3:
    def __init__(self):
        self.s3_client: S3Client = boto3.client(
            "s3",
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region,
        )

    def upload_file_with_bytes(
        self,
        bucket: S3Bucket,
        directory: S3Path,
        filename: str,
        file_bytes: bytes,
        content_type: str = "application/octet-stream",
        tagging: dict | None = None,
    ):
        self.s3_client.put_object(
            Bucket=bucket.value,
            Key=f"{directory.value}/{filename}",
            Body=file_bytes,
            ContentType=content_type,
            Tagging=urlencode(tagging) if tagging else None,
        )

    def upload_file(
        self,
        bucket: S3Bucket,
        directory: S3Path,
        filename: str,
        current_file_path: str,
        content_type: str = "application/octet-stream",
        tagging: dict | None = None,
    ):
        extra_args = {"ContentType": content_type}
        if tagging:
            extra_args["Tagging"] = urlencode(tagging)
        self.s3_client.upload_file(
            current_file_path,
            bucket.value,
            f"{directory.value}/{filename}",
            ExtraArgs=extra_args,
        )

    def download_file(
        self,
        bucket: S3Bucket,
        directory: S3Path,
        filename: str,
        local_path: str,
    ):
        self.s3_client.download_file(
            bucket.value, f"{directory.value}/{filename}", local_path
        )

    def create_file_download_url(
        self,
        bucket: S3Bucket,
        directory: S3Path,
        filename: str,
        expires_in: int = 3600,
    ) -> str:
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket.value, "Key": f"{directory.value}/{filename}"},
            ExpiresIn=expires_in,
        )

    def get_metadata(
        self,
        bucket: S3Bucket,
        directory: S3Path,
        filename: str,
    ) -> HeadObjectOutputTypeDef:
        return self.s3_client.head_object(
            Bucket=bucket.value, Key=f"{directory.value}/{filename}"
        )

    def get_tagging(
        self,
        bucket: S3Bucket,
        directory: S3Path,
        filename: str,
    ) -> GetObjectTaggingOutputTypeDef:
        return self.s3_client.get_object_tagging(
            Bucket=bucket.value, Key=f"{directory.value}/{filename}"
        )

    def get_object(
        self,
        bucket: S3Bucket,
        directory: S3Path,
        filename: str,
    ):
        try:
            response = self.s3_client.get_object(
                Bucket=bucket.value, Key=f"{directory.value}/{filename}"
            )
            return response
        except Exception:
            return None

    def copy_s3_file_if_not_exists(
        self,
        src_bucket: S3Bucket,
        src_key: str,
        dst_bucket: S3Bucket,
        dst_key: str,
        content_type: str | None = None,
    ):
        try:
            self.s3_client.head_object(Bucket=dst_bucket.value, Key=dst_key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                try:
                    if content_type:
                        self.s3_client.copy_object(
                            Bucket=dst_bucket.value,
                            CopySource={"Bucket": src_bucket.value, "Key": src_key},
                            Key=dst_key,
                            ContentType=content_type,
                        )
                    else:
                        self.s3_client.copy_object(
                            Bucket=dst_bucket.value,
                            CopySource={"Bucket": src_bucket.value, "Key": src_key},
                            Key=dst_key,
                        )
                except Exception as e:
                    print(f"Error copying file: {e}")
                    pass
            else:
                raise e

    def check_file_exists(
        self,
        bucket: S3Bucket,
        directory: S3Path,
        filename: str,
    ) -> bool:
        try:
            self.s3_client.head_object(
                Bucket=bucket.value, Key=os.path.join(directory.value, filename)
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                raise e

    def delete_object(
        self,
        bucket: S3Bucket,
        directory: S3Path,
        filename: str,
    ):
        key = f"{directory.value}/{filename}"
        try:
            self.s3_client.head_object(Bucket=bucket.value, Key=key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return
            else:
                raise e
        self.s3_client.delete_object(Bucket=bucket.value, Key=key)

    def delete_objects(
        self,
        bucket: S3Bucket,
        directory: S3Path,
        filename_list: list[str],
    ):
        if not filename_list:
            return
        objects = [
            {"Key": f"{directory.value}/{filename}"} for filename in filename_list
        ]

        self.s3_client.delete_objects(Bucket=bucket.value, Delete={"Objects": objects})
