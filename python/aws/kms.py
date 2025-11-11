import boto3
from botocore.exceptions import ClientError


class KMSSettings:
    access_key_id: str
    secret_access_key: str
    region: str
    kms_key_id: str


config = KMSSettings()


class KMS:
    def __init__(self):
        self.kms_client = boto3.client(
            "kms",
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region,
        )
        self.key_id = config.kms_key_id

    def encrypt(self, plaintext: bytes, encryption_context: dict) -> bytes:
        try:
            response = self.kms_client.encrypt(
                KeyId=self.key_id,
                Plaintext=plaintext,
                EncryptionContext=encryption_context,  # salt값 같은 역할
            )
            return response["CiphertextBlob"]
        except ClientError as e:
            raise Exception(f"Encryption failed: {e}")

    def decrypt(self, ciphertext_blob: bytes, encryption_context: dict) -> bytes:
        try:
            response = self.kms_client.decrypt(
                KeyId=self.key_id,
                CiphertextBlob=ciphertext_blob,
                EncryptionContext=encryption_context,  # salt값 같은 역할
            )
            return response["Plaintext"]
        except ClientError as e:
            raise Exception(f"Decryption failed: {e}")
