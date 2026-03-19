import base64
import hashlib

from Crypto.Cipher import Blowfish
from Crypto.Util.Padding import pad, unpad


BLOCK_SIZE = Blowfish.block_size  # 8


def _derive_key(key: str | bytes, length: int = 16) -> bytes:
    if isinstance(key, str):
        key = key.encode("utf-8")
    return hashlib.sha256(key).digest()[:length]


def encrypt(value: str, key: str) -> str:
    plaintext = str(value).encode("utf-8")
    bf_key = _derive_key(key, 16)

    cipher = Blowfish.new(bf_key, Blowfish.MODE_CBC)
    ciphertext = cipher.encrypt(pad(plaintext, BLOCK_SIZE))

    payload = cipher.iv + ciphertext
    return base64.b64encode(payload).decode("utf-8")


def decrypt(value: str, key: str) -> str:
    raw = base64.b64decode(value)
    bf_key = _derive_key(key, 16)

    iv = raw[:BLOCK_SIZE]
    ciphertext = raw[BLOCK_SIZE:]

    cipher = Blowfish.new(bf_key, Blowfish.MODE_CBC, iv=iv)
    plaintext = unpad(cipher.decrypt(ciphertext), BLOCK_SIZE)

    return plaintext.decode("utf-8")