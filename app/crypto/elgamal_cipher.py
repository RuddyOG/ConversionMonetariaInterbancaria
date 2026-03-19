from app.crypto.aes_cipher import encrypt as aes_encrypt, decrypt as aes_decrypt


def encrypt(value: str, key: str) -> str:
    return aes_encrypt(value, key)


def decrypt(value: str, key: str) -> str:
    return aes_decrypt(value, key)