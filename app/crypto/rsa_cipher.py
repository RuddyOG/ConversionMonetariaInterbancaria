import base64
from typing import Any

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256


# =========================
# UTIL: FIX BASE64 PADDING
# =========================
def _fix_padding(data: str) -> str:
    if not data:
        return data
    return data + "=" * (-len(data) % 4)


# =========================
# LOAD KEYS
# =========================
def _get_public_key(key_data: Any) -> RSA.RsaKey:
    if not isinstance(key_data, dict):
        raise ValueError("RSA requiere dict con 'public_key' y 'private_key'.")

    public_key_pem = key_data.get("public_key")
    if not public_key_pem:
        raise ValueError("Falta 'public_key' en configuración RSA.")

    if isinstance(public_key_pem, str):
        public_key_pem = public_key_pem.encode("utf-8")

    return RSA.import_key(public_key_pem)


def _get_private_key(key_data: Any) -> RSA.RsaKey:
    if not isinstance(key_data, dict):
        raise ValueError("RSA requiere dict con 'public_key' y 'private_key'.")

    private_key_pem = key_data.get("private_key")
    if not private_key_pem:
        raise ValueError("Falta 'private_key' en configuración RSA.")

    if isinstance(private_key_pem, str):
        private_key_pem = private_key_pem.encode("utf-8")

    return RSA.import_key(private_key_pem)


# =========================
# ENCRYPT
# =========================
def encrypt(value: str, key: Any) -> str:
    if value is None:
        value = ""

    plaintext = str(value).encode("utf-8")
    public_key = _get_public_key(key)

    cipher = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)
    ciphertext = cipher.encrypt(plaintext)

    return base64.b64encode(ciphertext).decode("utf-8")


# =========================
# DECRYPT
# =========================
def decrypt(value: str, key: Any) -> str:
    if not value:
        return ""

    try:
        value = _fix_padding(value)
        ciphertext = base64.b64decode(value)

        private_key = _get_private_key(key)

        cipher = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)
        plaintext = cipher.decrypt(ciphertext)

        return plaintext.decode("utf-8")

    except Exception as e:
        raise ValueError(f"Error RSA decrypt: {str(e)}")