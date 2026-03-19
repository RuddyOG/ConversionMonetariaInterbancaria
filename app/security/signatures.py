#Firma este payload con HMAC y verifica si fue alterado
import hashlib
import hmac
import json
from typing import Any, Dict

from app.security.constants import DEFAULT_HASH_ALGORITHM


def canonical_json(data: Dict[str, Any]) -> str:
    """
    Convierte un diccionario a JSON canónico para que el hash/HMAC
    sea consistente aunque cambie el orden de las claves.
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def generate_hash(data: Dict[str, Any], algorithm: str = DEFAULT_HASH_ALGORITHM) -> str:
    payload = canonical_json(data).encode("utf-8")
    hasher = hashlib.new(algorithm)
    hasher.update(payload)
    return hasher.hexdigest()


def generate_hmac(data: Dict[str, Any], secret_key: str, algorithm: str = "sha256") -> str:
    payload = canonical_json(data).encode("utf-8")
    key = secret_key.encode("utf-8")
    return hmac.new(key, payload, getattr(hashlib, algorithm)).hexdigest()


def verify_hmac(
    data: Dict[str, Any],
    secret_key: str,
    received_hmac: str,
    algorithm: str = "sha256",
) -> bool:
    expected_hmac = generate_hmac(data, secret_key, algorithm=algorithm)
    return hmac.compare_digest(expected_hmac, received_hmac)


def extract_hmac_from_payload(payload: Dict[str, Any]) -> tuple[Dict[str, Any], str]:
    payload_copy = dict(payload)
    received_hmac = payload_copy.pop("hmac", None)

    if not received_hmac:
        raise ValueError("El payload no contiene el campo 'hmac'.")

    return payload_copy, received_hmac