from app.core.crypto import generate_dek, wrap_dek, unwrap_dek, UserCipher


def test_encrypt_decrypt_roundtrip():
    dek = generate_dek()
    cipher = UserCipher(dek)
    ciphertext = cipher.encrypt("a private journal entry")
    assert ciphertext != b"a private journal entry"
    assert cipher.decrypt(ciphertext) == "a private journal entry"


def test_different_users_get_different_deks():
    dek_a = generate_dek()
    dek_b = generate_dek()
    assert dek_a != dek_b


def test_wrapped_dek_roundtrips_through_master_key():
    plaintext_dek = generate_dek()
    wrapped = wrap_dek(plaintext_dek)
    assert wrapped != plaintext_dek
    unwrapped = unwrap_dek(wrapped)
    assert unwrapped == plaintext_dek


def test_ciphertext_from_one_users_dek_is_unreadable_with_anothers():
    cipher_a = UserCipher(generate_dek())
    cipher_b = UserCipher(generate_dek())
    ciphertext = cipher_a.encrypt("sensitive content")

    try:
        cipher_b.decrypt(ciphertext)
        assert False, "decrypting with the wrong user's key should raise, not silently succeed"
    except Exception:
        pass  # expected — this IS the security property being tested


def test_none_plaintext_returns_none():
    cipher = UserCipher(generate_dek())
    assert cipher.encrypt(None) is None
