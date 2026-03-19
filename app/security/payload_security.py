#Arma y valida mensajes seguros entre banco y ASFI
from typing import Any, Dict

from app.security.keys import KeyManager
from app.security.nonce import NonceManager
from app.security.signatures import extract_hmac_from_payload, generate_hmac, verify_hmac


class PayloadSecurity:
    def __init__(self, key_manager: KeyManager, nonce_manager: NonceManager):
        self.key_manager = key_manager
        self.nonce_manager = nonce_manager

    def secure_payload(self, payload: Dict[str, Any], bank_id: int | str) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise TypeError("El payload debe ser un diccionario.")

        secure_payload = dict(payload)
        secure_payload["timestamp"] = self.nonce_manager.generate_timestamp()
        secure_payload["nonce"] = self.nonce_manager.generate_nonce()

        secret_key = self.key_manager.get_hmac_key(bank_id)
        secure_payload["hmac"] = generate_hmac(secure_payload, secret_key)

        return secure_payload

    def validate_payload(self, payload: Dict[str, Any], bank_id: int | str) -> bool:
        if not isinstance(payload, dict):
            return False

        try:
            payload_without_hmac, received_hmac = extract_hmac_from_payload(payload)

            timestamp = payload_without_hmac.get("timestamp")
            nonce = payload_without_hmac.get("nonce")

            if not timestamp or not nonce:
                return False

            if not self.nonce_manager.is_timestamp_valid(timestamp):
                return False

            if not self.nonce_manager.register_nonce(nonce):
                return False

            secret_key = self.key_manager.get_hmac_key(bank_id)
            return verify_hmac(payload_without_hmac, secret_key, received_hmac)

        except Exception:
            return False