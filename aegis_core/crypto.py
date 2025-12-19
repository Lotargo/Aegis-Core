from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

class CryptoEngine:
    """
    Инкапсулирует всю криптографическую логику для Aegis Core.
    """

    def __init__(self):
        self._private_key = ec.generate_private_key(ec.SECP384R1())
        self.public_key_bytes = self._private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def derive_shared_key(self, peer_public_key_bytes: bytes) -> bytes:
        peer_public_key = serialization.load_pem_public_key(peer_public_key_bytes)
        shared_secret = self._private_key.exchange(ec.ECDH(), peer_public_key)

        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'aegis-session-key',
        ).derive(shared_secret)

        return derived_key

    @staticmethod
    def encrypt(key: bytes, plaintext: bytes, associated_data: bytes) -> bytes:
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
        return nonce + ciphertext

    @staticmethod
    def decrypt(key: bytes, ciphertext_with_nonce: bytes, associated_data: bytes) -> bytes:
        nonce = ciphertext_with_nonce[:12]
        ciphertext = ciphertext_with_nonce[12:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, associated_data)
