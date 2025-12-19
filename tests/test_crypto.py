import pytest
from aegis_core.crypto import CryptoEngine

@pytest.fixture(scope="module")
def crypto_peer_a():
    return CryptoEngine()

@pytest.fixture(scope="module")
def crypto_peer_b():
    return CryptoEngine()

def test_shared_key_derivation_is_symmetric(crypto_peer_a, crypto_peer_b):
    shared_key_a = crypto_peer_a.derive_shared_key(crypto_peer_b.public_key_bytes)
    shared_key_b = crypto_peer_b.derive_shared_key(crypto_peer_a.public_key_bytes)

    assert shared_key_a is not None
    assert shared_key_b is not None
    assert shared_key_a == shared_key_b
    assert len(shared_key_a) == 32

def test_encrypt_decrypt_cycle_is_correct(crypto_peer_a, crypto_peer_b):
    shared_key = crypto_peer_a.derive_shared_key(crypto_peer_b.public_key_bytes)

    plaintext = b"This is a secret message!"
    associated_data = b"metadata"

    encrypted_data = crypto_peer_a.encrypt(shared_key, plaintext, associated_data)
    decrypted_data = crypto_peer_b.decrypt(shared_key, encrypted_data, associated_data)

    assert decrypted_data == plaintext

def test_decryption_fails_with_wrong_key(crypto_peer_a, crypto_peer_b):
    shared_key = crypto_peer_a.derive_shared_key(crypto_peer_b.public_key_bytes)
    wrong_key = b'0' * 32

    plaintext = b"some data"
    associated_data = b"ad"

    encrypted_data = crypto_peer_a.encrypt(shared_key, plaintext, associated_data)

    with pytest.raises(Exception):
        crypto_peer_b.decrypt(wrong_key, encrypted_data, associated_data)

def test_decryption_fails_with_tampered_associated_data(crypto_peer_a, crypto_peer_b):
    shared_key = crypto_peer_a.derive_shared_key(crypto_peer_b.public_key_bytes)

    plaintext = b"some data"
    associated_data = b"ad"
    tampered_ad = b"tampered"

    encrypted_data = crypto_peer_a.encrypt(shared_key, plaintext, associated_data)

    with pytest.raises(Exception):
        crypto_peer_b.decrypt(shared_key, encrypted_data, tampered_ad)
