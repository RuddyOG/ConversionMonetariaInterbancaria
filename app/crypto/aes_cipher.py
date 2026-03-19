import base64
import hashlib

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


BLOCK_SIZE = AES.block_size  # 16


def _derive_key(key: str | bytes, length: int = 32) -> bytes:
    if isinstance(key, str):
        key = key.encode("utf-8")
    return hashlib.sha256(key).digest()[:length]


def encrypt(value: str, key: str) -> str:
    plaintext = str(value).encode("utf-8")
    aes_key = _derive_key(key, 32)

    cipher = AES.new(aes_key, AES.MODE_CBC)
    ciphertext = cipher.encrypt(pad(plaintext, BLOCK_SIZE))

    payload = cipher.iv + ciphertext
    return base64.b64encode(payload).decode("utf-8")


def decrypt(value: str, key: str) -> str:
    raw = base64.b64decode(value)
    aes_key = _derive_key(key, 32)

    iv = raw[:BLOCK_SIZE]
    ciphertext = raw[BLOCK_SIZE:]

    cipher = AES.new(aes_key, AES.MODE_CBC, iv=iv)
    plaintext = unpad(cipher.decrypt(ciphertext), BLOCK_SIZE)

    return plaintext.decode("utf-8")