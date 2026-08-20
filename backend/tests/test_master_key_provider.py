"""
Tests for master_key_provider.py — the piece that makes real KMS possible.

The AWS KMS provider tests mock boto3 entirely (no real AWS calls, no
credentials needed), verifying: (1) the correct KMS API calls are made
with the correct arguments, and (2) wrap/unwrap correctly round-trips
through the mocked KMS responses. This proves the *integration code* is
correct; it does not (and cannot, without real AWS credentials) prove
that a real KMS key policy is configured correctly — that still needs to
be verified once against a real (even sandbox/dev) AWS account before
relying on it in production.
"""
import os
import sys
import pytest

from app.core import master_key_provider as mkp_module
from app.core.master_key_provider import (
    LocalDevMasterKeyProvider,
    get_master_key_provider,
    reset_provider_cache_for_tests,
)


@pytest.fixture(autouse=True)
def _reset_provider_state(monkeypatch):
    reset_provider_cache_for_tests()
    monkeypatch.delenv("SANJEEVANI_ENCRYPTION_PROVIDER", raising=False)
    monkeypatch.delenv("SANJEEVANI_MASTER_KEY", raising=False)
    monkeypatch.delenv("SANJEEVANI_KMS_KEY_ID", raising=False)
    yield
    reset_provider_cache_for_tests()


class TestLocalDevProvider:
    def test_roundtrip(self):
        provider = LocalDevMasterKeyProvider()
        plaintext_dek = os.urandom(32)
        wrapped = provider.wrap_dek(plaintext_dek)
        assert wrapped != plaintext_dek
        assert provider.unwrap_dek(wrapped) == plaintext_dek

    def test_defaults_to_local_dev_when_env_unset(self, monkeypatch):
        provider = get_master_key_provider()
        assert isinstance(provider, LocalDevMasterKeyProvider)

    def test_explicit_local_dev_selection(self, monkeypatch):
        monkeypatch.setenv("SANJEEVANI_ENCRYPTION_PROVIDER", "local_dev")
        provider = get_master_key_provider()
        assert isinstance(provider, LocalDevMasterKeyProvider)

    def test_unknown_provider_raises(self, monkeypatch):
        monkeypatch.setenv("SANJEEVANI_ENCRYPTION_PROVIDER", "not_a_real_provider")
        with pytest.raises(RuntimeError):
            get_master_key_provider()


class TestAWSKMSProvider:
    """Mocks boto3 entirely — no real AWS account or network needed to run
    these, but they do require the `boto3` package to be installed
    (it's a lazy import inside AWSKMSMasterKeyProvider)."""

    def test_missing_key_id_raises_clear_error(self, monkeypatch):
        pytest.importorskip("boto3")
        monkeypatch.setenv("SANJEEVANI_ENCRYPTION_PROVIDER", "aws_kms")
        # SANJEEVANI_KMS_KEY_ID intentionally left unset
        with pytest.raises(RuntimeError, match="SANJEEVANI_KMS_KEY_ID"):
            get_master_key_provider()

    def test_wrap_and_unwrap_call_correct_kms_apis(self, monkeypatch):
        boto3 = pytest.importorskip("boto3")
        from app.core.master_key_provider import AWSKMSMasterKeyProvider

        monkeypatch.setenv("SANJEEVANI_KMS_KEY_ID", "arn:aws:kms:us-east-1:123456789012:key/test-key")

        calls = {}

        class FakeKMSClient:
            def encrypt(self, KeyId, Plaintext):
                calls["encrypt"] = {"KeyId": KeyId, "Plaintext": Plaintext}
                return {"CiphertextBlob": b"WRAPPED[" + Plaintext + b"]"}

            def decrypt(self, KeyId, CiphertextBlob):
                calls["decrypt"] = {"KeyId": KeyId, "CiphertextBlob": CiphertextBlob}
                # Reverse the fake wrapping done above
                assert CiphertextBlob.startswith(b"WRAPPED[") and CiphertextBlob.endswith(b"]")
                return {"Plaintext": CiphertextBlob[len(b"WRAPPED["):-1]}

        monkeypatch.setattr(boto3, "client", lambda service, region_name=None: FakeKMSClient())

        provider = AWSKMSMasterKeyProvider()
        plaintext_dek = os.urandom(32)

        wrapped = provider.wrap_dek(plaintext_dek)
        assert calls["encrypt"]["KeyId"] == "arn:aws:kms:us-east-1:123456789012:key/test-key"
        assert calls["encrypt"]["Plaintext"] == plaintext_dek
        assert wrapped != plaintext_dek

        unwrapped = provider.unwrap_dek(wrapped)
        assert calls["decrypt"]["CiphertextBlob"] == wrapped
        assert unwrapped == plaintext_dek
