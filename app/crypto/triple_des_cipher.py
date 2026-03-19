import base64
import hashlib

from Crypto.Cipher import DES3
from Crypto.Util.Padding import pad, unpad


BLOCK_SIZE = DES3.block_size  # 8


def _derive_key(key: str | bytes) -> bytes:
    if isinstance(key, str):
        key = key.encode("utf-8")

    # 24 bytes para 3DES
    raw_key = hashlib.sha256(key).digest()[:24]
    return DES3.adjust_key_parity(raw_key)


def encrypt(value: str, key: str) -> str:
    plaintext = str(value).encode("utf-8")
    tdes_key = _derive_key(key)

    cipher = DES3.new(tdes_key, DES3.MODE_CBC)
    ciphertext = cipher.encrypt(pad(plaintext, BLOCK_SIZE))

    payload = cipher.iv + ciphertext
    return base64.b64encode(payload).decode("utf-8")


def decrypt(value: str, key: str) -> str:
    raw = base64.b64decode(value)
    tdes_key = _derive_key(key)

    iv = raw[:BLOCK_SIZE]
    ciphertext = raw[BLOCK_SIZE:]

    cipher = DES3.new(tdes_key, DES3.MODE_CBC, iv=iv)
    plaintext = unpad(cipher.decrypt(ciphertext), BLOCK_SIZE)

    return plaintext.decode("utf-8")