"""
Master Key Provider abstraction (Chapter 1, Sec.6).

This is the piece that was previously a TODO. Two implementations:

  - LocalDevMasterKeyProvider: a Fernet key read from an env var. Fine for
    local development ONLY. Never use in any shared or production
    environment — the key lives in application config, which defeats the
    point of envelope encryption.

  - AWSKMSMasterKeyProvider: wraps/unwraps DEKs using a real AWS KMS
    Customer Master Key (CMK) via the KMS Encrypt/Decrypt API. The
    plaintext master key material never exists outside AWS KMS itself —
    this process only ever holds the wrapped (ciphertext) form or a
    briefly-unwrapped DEK in memory, never the master key.

Which provider is used is controlled by SANJEEVANI_ENCRYPTION_PROVIDER:
  - "aws_kms" (recommended for any real deployment)
  - "local_dev" (default if unset — intentionally loud about this, see
    get_master_key_provider() below, so nobody ships local_dev silently)

app/core/crypto.py is written entirely against the MasterKeyProvider
interface (wrap_dek/unwrap_dek) and does not need to change based on
which provider is active.
"""
import os
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class MasterKeyProvider(ABC):
    @abstractmethod
    def wrap_dek(self, plaintext_dek: bytes) -> bytes:
        """Encrypt a plaintext DEK for storage."""

    @abstractmethod
    def unwrap_dek(self, wrapped_dek: bytes) -> bytes:
        """Decrypt a stored DEK back to plaintext, in memory only."""


class LocalDevMasterKeyProvider(MasterKeyProvider):
    """Dev-only. Master key material lives in an env var / process memory.
    Do not use this for any environment real users' data touches."""

    def __init__(self):
        from cryptography.fernet import Fernet

        self._Fernet = Fernet
        key = os.getenv("SANJEEVANI_MASTER_KEY")
        if not key:
            key = Fernet.generate_key().decode()
            os.environ["SANJEEVANI_MASTER_KEY"] = key
            logger.warning(
                "No SANJEEVANI_MASTER_KEY set — generated an ephemeral one "
                "for this process. This is fine for local dev, but data "
                "encrypted now will be UNREADABLE after restart unless you "
                "pin SANJEEVANI_MASTER_KEY explicitly. Never rely on this "
                "path outside local development."
            )
        self._fernet = Fernet(key.encode())

    def wrap_dek(self, plaintext_dek: bytes) -> bytes:
        return self._fernet.encrypt(plaintext_dek)

    def unwrap_dek(self, wrapped_dek: bytes) -> bytes:
        return self._fernet.decrypt(wrapped_dek)


class AWSKMSMasterKeyProvider(MasterKeyProvider):
    """
    Production provider. Requires:
      - SANJEEVANI_KMS_KEY_ID env var — the ARN or key ID of an AWS KMS
        Customer Master Key (symmetric, ENCRYPT_DECRYPT usage)
      - AWS credentials available via the normal boto3 resolution chain
        (IAM role in production; env vars / ~/.aws/credentials locally)
      - The `boto3` package installed (see requirements.txt)

    IAM permissions needed on the CMK's key policy / an attached policy:
      kms:Encrypt, kms:Decrypt  (kms:GenerateDataKey not required, since
      DEKs are generated locally and only wrapped/unwrapped via KMS)

    boto3 is imported lazily so the rest of the app can be imported/tested
    without it installed when this provider isn't the active one.
    """

    def __init__(self):
        import boto3  # lazy import — see class docstring

        self._key_id = os.getenv("SANJEEVANI_KMS_KEY_ID")
        if not self._key_id:
            raise RuntimeError(
                "SANJEEVANI_ENCRYPTION_PROVIDER=aws_kms but SANJEEVANI_KMS_KEY_ID "
                "is not set. Set it to your KMS CMK's ARN or key ID."
            )
        region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
        self._client = boto3.client("kms", region_name=region) if region else boto3.client("kms")

    def wrap_dek(self, plaintext_dek: bytes) -> bytes:
        response = self._client.encrypt(KeyId=self._key_id, Plaintext=plaintext_dek)
        return response["CiphertextBlob"]

    def unwrap_dek(self, wrapped_dek: bytes) -> bytes:
        response = self._client.decrypt(KeyId=self._key_id, CiphertextBlob=wrapped_dek)
        return response["Plaintext"]


_provider_instance = None


def get_master_key_provider() -> MasterKeyProvider:
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    mode = os.getenv("SANJEEVANI_ENCRYPTION_PROVIDER", "local_dev").lower()

    if mode == "aws_kms":
        _provider_instance = AWSKMSMasterKeyProvider()
        logger.info("Using AWS KMS as the master key provider.")
    elif mode == "local_dev":
        logger.warning(
            "SANJEEVANI_ENCRYPTION_PROVIDER is 'local_dev' (or unset). This "
            "is NOT safe for any environment with real user data. Set "
            "SANJEEVANI_ENCRYPTION_PROVIDER=aws_kms and SANJEEVANI_KMS_KEY_ID "
            "before deploying anywhere real users can reach."
        )
        _provider_instance = LocalDevMasterKeyProvider()
    else:
        raise RuntimeError(f"Unknown SANJEEVANI_ENCRYPTION_PROVIDER: {mode!r}")

    return _provider_instance


def reset_provider_cache_for_tests():
    """Test-only helper — clears the cached provider so tests can swap
    env vars and get a fresh provider instance."""
    global _provider_instance
    _provider_instance = None
