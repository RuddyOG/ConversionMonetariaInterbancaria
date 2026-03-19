import base64
import hashlib

from Crypto.Cipher import ChaCha20


NONCE_SIZE = 12


def _derive_key(key: str | bytes) -> bytes:
    if isinstance(key, str):
        key = key.encode("utf-8")
    return hashlib.sha256(key).digest()  # 32 bytes


def encrypt(value: str, key: str) -> str:
    plaintext = str(value).encode("utf-8")
    chacha_key = _derive_key(key)

    cipher = ChaCha20.new(key=chacha_key)
    ciphertext = cipher.encrypt(plaintext)

    payload = cipher.nonce + ciphertext
    return base64.b64encode(payload).decode("utf-8")


def decrypt(value: str, key: str) -> str:
    raw = base64.b64decode(value)
    chacha_key = _derive_key(key)

    nonce = raw[:8] if len(raw) >= 8 else b""
    ciphertext = raw[8:]

    cipher = ChaCha20.new(key=chacha_key, nonce=nonce)
    plaintext = cipher.decrypt(ciphertext)

    return plaintext.decode("utf-8")