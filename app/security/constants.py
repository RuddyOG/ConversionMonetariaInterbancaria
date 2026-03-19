from datetime import timezone

DEFAULT_HASH_ALGORITHM = "sha256"
DEFAULT_HMAC_ALGORITHM = "sha256"

NONCE_NBYTES = 8
NONCE_CACHE_MAX_SIZE = 10000

TIMESTAMP_TOLERANCE_SECONDS = 300
DEFAULT_TIMEZONE = timezone.utc

VERIFICATION_CODE_LENGTH = 8
VERIFICATION_CODE_ALPHABET = "0123456789ABCDEF"

ENCRYPTED_FIELDS = {
    "ci",
    "numero_cuenta",
    "saldo_usd",
    "saldo_bs",
}

INTEGRITY_FIELDS = {
    "id",
    "ci",
    "nombres",
    "apellidos",
    "numero_cuenta",
    "id_banco",
    "saldo_usd",
    "tipo_cambio",
    "saldo_bs",
    "algoritmo_cifrado",
    "codigo_verificacion",
    "created_at",
    "updated_at",
    "created_by",
    "updated_by",
    "is_active",
}