import base64
import hashlib

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


BLOCK_SIZE = AES.block_size  # 16


def _derive_key(key: str | bytes, length: int = 32) -> bytes:
    """Deriva una clave de la longitud especificada usando SHA-256"""
    # Si la clave ya es bytes, usarla directamente
    if isinstance(key, bytes):
        key_bytes = key
    else:
        # Convertir string a bytes
        key_bytes = key.encode("utf-8")
    
    # Si la clave es exactamente de la longitud requerida, devolverla
    if len(key_bytes) == length:
        return key_bytes
    
    # Si no, derivar usando SHA-256
    return hashlib.sha256(key_bytes).digest()[:length]


def encrypt(value: str, key: str | bytes) -> str:
    """Encripta un valor usando AES-256 en modo CBC"""
    plaintext = str(value).encode("utf-8")
    aes_key = _derive_key(key, 32)

    cipher = AES.new(aes_key, AES.MODE_CBC)
    ciphertext = cipher.encrypt(pad(plaintext, BLOCK_SIZE))

    payload = cipher.iv + ciphertext
    return base64.b64encode(payload).decode("utf-8")


def decrypt(value: str, key: str | bytes) -> str:
    """Descifra un valor usando AES-256 en modo CBC"""
    raw = base64.b64decode(value)
    aes_key = _derive_key(key, 32)

    iv = raw[:BLOCK_SIZE]
    ciphertext = raw[BLOCK_SIZE:]

    cipher = AES.new(aes_key, AES.MODE_CBC, iv=iv)
    plaintext = unpad(cipher.decrypt(ciphertext), BLOCK_SIZE)

    return plaintext.decode("utf-8")