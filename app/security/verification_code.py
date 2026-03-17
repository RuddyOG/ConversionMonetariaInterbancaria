#Genera el código hexadecimal de 8 caracteres
import secrets

from app.security.constants import (
    VERIFICATION_CODE_ALPHABET,
    VERIFICATION_CODE_LENGTH,
)


def generate_verification_code(length: int = VERIFICATION_CODE_LENGTH) -> str:
    return "".join(secrets.choice(VERIFICATION_CODE_ALPHABET) for _ in range(length))


def is_valid_verification_code(code: str, length: int = VERIFICATION_CODE_LENGTH) -> bool:
    if not isinstance(code, str):
        return False

    if len(code) != length:
        return False

    return all(char in VERIFICATION_CODE_ALPHABET for char in code.upper())