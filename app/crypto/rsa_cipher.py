import base64
from typing import Any

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256


def _get_public_key(key_data: Any) -> RSA.RsaKey:
    if isinstance(key_data, dict):
        public_key_pem = key_data.get("public_key")
        if not public_key_pem:
            raise ValueError("La configuración RSA requiere 'public_key'.")
        return RSA.import_key(public_key_pem)

    raise ValueError("La llave RSA debe ser un dict con 'public_key' y 'private_key'.")


def _get_private_key(key_data: Any) -> RSA.RsaKey:
    if isinstance(key_data, dict):
        private_key_pem = key_data.get("private_key")
        if not private_key_pem:
            raise ValueError("La configuración RSA requiere 'private_key'.")
        return RSA.import_key(private_key_pem)

    raise ValueError("La llave RSA debe ser un dict con 'public_key' y 'private_key'.")


def encrypt(value: str, key: Any) -> str:
    plaintext = str(value).encode("utf-8")
    public_key = _get_public_key(key)

    cipher = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)
    ciphertext = cipher.encrypt(plaintext)

    return base64.b64encode(ciphertext).decode("utf-8")


def decrypt(value: str, key: Any) -> str:
    ciphertext = base64.b64decode(value)
    private_key = _get_private_key(key)

    cipher = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)
    plaintext = cipher.decrypt(ciphertext)

    return plaintext.decode("utf-8")