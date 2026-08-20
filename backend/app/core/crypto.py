"""
Envelope encryption for clinical/emotional content (Chapter 1, Sec.6).

Design: every user gets their own randomly-generated Data Encryption Key
(DEK) — a raw 256-bit AES key. The DEK is encrypted ("wrapped") by a
Master Key, managed via MasterKeyProvider (see master_key_provider.py —
either a real AWS KMS Customer Master Key in production, or a local dev
key for local development only), and stored in the database as
ciphertext. Content is encrypted with the user's DEK using AES-256-GCM
directly, not via the master key.

Why AES-GCM directly instead of Fernet (the previous implementation):
Fernet requires its own specific key format, which meant this module
could never actually receive a real KMS-generated data key without an
awkward conversion step. Raw AES-256-GCM has no such constraint — the
same DEK bytes work identically whether they were generated locally or
returned by AWS KMS, so switching master key providers is a one-line
config change (see master_key_provider.py), not a re-encryption event.

Why per-user DEKs at all, over a single global key:
  - A single compromised DEK exposes one user's data, not everyone's.
  - Per-user keys can be individually revoked (e.g., on account deletion,
    the wrapped DEK's row is marked revoked — "crypto-shredding" — making
    that user's ciphertext permanently unreadable without deleting rows).
"""
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.master_key_provider import get_master_key_provider

AES_KEY_SIZE = 32   # 256-bit DEK
NONCE_SIZE = 12      # 96-bit nonce, standard for AES-GCM


def generate_dek() -> bytes:
    """Generate a new random per-user Data Encryption Key (raw AES-256 key)."""
    return os.urandom(AES_KEY_SIZE)


def wrap_dek(plaintext_dek: bytes) -> bytes:
    """Encrypt a DEK under the active Master Key provider, for storage."""
    return get_master_key_provider().wrap_dek(plaintext_dek)


def unwrap_dek(wrapped_dek: bytes) -> bytes:
    """Decrypt a stored (wrapped) DEK back to its plaintext form, in memory only."""
    return get_master_key_provider().unwrap_dek(wrapped_dek)


def encrypt_with_dek(plaintext: str, dek: bytes) -> bytes:
    """AES-256-GCM encrypt. Output layout: nonce (12 bytes) || ciphertext+tag."""
    if plaintext is None:
        return None
    aesgcm = AESGCM(dek)
    nonce = os.urandom(NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
    return nonce + ciphertext


def decrypt_with_dek(blob: bytes, dek: bytes) -> str:
    if blob is None:
        return None
    aesgcm = AESGCM(dek)
    nonce, ciphertext = blob[:NONCE_SIZE], blob[NONCE_SIZE:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
    return plaintext.decode("utf-8")


class UserCipher:
    """
    Convenience wrapper bound to one user's unwrapped DEK, so call sites
    (routers) don't have to juggle wrap/unwrap on every call. Construct
    once per request via `get_user_cipher()` in encryption_dep.py.
    """

    def __init__(self, dek: bytes):
        self._dek = dek

    def encrypt(self, plaintext: str) -> bytes:
        return encrypt_with_dek(plaintext, self._dek)

    def decrypt(self, ciphertext: bytes) -> str:
        return decrypt_with_dek(ciphertext, self._dek)
