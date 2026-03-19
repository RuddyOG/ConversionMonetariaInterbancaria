from app.crypto import (
    caesar_cipher,
    atbash_cipher,
    vigenere_cipher,
    playfair_cipher,
    hill_cipher,
    des_cipher,
    triple_des_cipher,
    blowfish_cipher,
    aes_cipher,
    rsa_cipher,
    chacha20_cipher,
)
from app.crypto.normalizer import normalize_text, normalize_balance
from app.security.constants import ENCRYPTED_FIELDS
from app.security.keys import KeyManager


class CryptoManager:
    def __init__(self):
        self.key_manager = KeyManager()

        self.algorithms = {
            "caesar": caesar_cipher,
            "atbash": atbash_cipher,
            "vigenere": vigenere_cipher,
            "playfair": playfair_cipher,
            "hill": hill_cipher,
            "des": des_cipher,
            "3des": triple_des_cipher,
            "blowfish": blowfish_cipher,
            "aes": aes_cipher,
            "rsa": rsa_cipher,
            "chacha20": chacha20_cipher,
        }

    def _get_cipher_module(self, bank_id: int | str):
        algorithm = self.key_manager.get_algorithm(bank_id).lower()

        if algorithm not in self.algorithms:
            raise ValueError(f"Algoritmo no soportado todavía: {algorithm}")

        return self.algorithms[algorithm]

    def encrypt_field(self, bank_id: int | str, field_name: str, value):
        cipher_module = self._get_cipher_module(bank_id)
        key = self.key_manager.get_encryption_key(bank_id)

        if field_name in ("saldo_usd", "saldo_bs"):
            normalized_value = normalize_balance(value if value not in (None, "") else 0)
        else:
            normalized_value = normalize_text(value)

        return cipher_module.encrypt(normalized_value, key)

    def decrypt_field(self, bank_id: int | str, field_name: str, value):
        cipher_module = self._get_cipher_module(bank_id)
        key = self.key_manager.get_encryption_key(bank_id)

        decrypted_value = cipher_module.decrypt(value, key)

        if field_name in ("saldo_usd", "saldo_bs"):
            return normalize_balance(decrypted_value)

        return decrypted_value

    def encrypt_sensitive_fields(self, record: dict) -> dict:
        bank_id = record["id_banco"]
        encrypted_record = dict(record)

        for field in ENCRYPTED_FIELDS:
            value = encrypted_record.get(field)
            if value not in (None, ""):
                encrypted_record[field] = self.encrypt_field(bank_id, field, value)

        encrypted_record["algoritmo_cifrado"] = self.key_manager.get_algorithm(bank_id)
        return encrypted_record

    def decrypt_sensitive_fields(self, record: dict) -> dict:
        bank_id = record["id_banco"]
        decrypted_record = dict(record)

        for field in ENCRYPTED_FIELDS:
            value = decrypted_record.get(field)
            if value not in (None, ""):
                decrypted_record[field] = self.decrypt_field(bank_id, field, value)

        return decrypted_record