#Guarda configuraciones fijas de seguridad
from datetime import timezone

# Seguridad de mensajes
DEFAULT_HASH_ALGORITHM = "sha256"
DEFAULT_HMAC_ALGORITHM = "sha256"

# Nonce
NONCE_NBYTES = 8  # 16 caracteres hex
NONCE_CACHE_MAX_SIZE = 10000

# Timestamp
TIMESTAMP_TOLERANCE_SECONDS = 300  # 5 minutos
DEFAULT_TIMEZONE = timezone.utc

# Código de verificación
VERIFICATION_CODE_LENGTH = 8
VERIFICATION_CODE_ALPHABET = "0123456789ABCDEF"

# Campos que se cifran en esta primera versión
ENCRYPTED_FIELDS = {"ci", "nro_cuenta", "saldo_usd"}

# Campos que pueden ir protegidos por integridad
INTEGRITY_FIELDS = {
    "id",
    "ci",
    "nombres",
    "apellidos",
    "nro_cuenta",
    "id_banco",
    "saldo_usd",
    "tipo_cambio",
    "saldo_bs",
    "algoritmo_cifrado",
    "created_at",
    "updated_at",
    "created_by",
    "modified_by",
}