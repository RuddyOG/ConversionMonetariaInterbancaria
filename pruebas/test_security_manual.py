from app.security.keys import KeyManager
from app.security.nonce import NonceManager
from app.security.payload_security import PayloadSecurity
from app.security.verification_code import generate_verification_code


def main():
    key_manager = KeyManager()
    nonce_manager = NonceManager()
    payload_security = PayloadSecurity(key_manager, nonce_manager)

    sample_payload = {
        "id": 20617,
        "ci": "CIFRADO_AQUI",
        "nombres": "Sofia Elena",
        "apellidos": "Perez Rodriguez",
        "nro_cuenta": "CIFRADO_AQUI",
        "id_banco": 5,
        "saldo_usd": "CIFRADO_AQUI",
        "tipo_cambio": "6.9600",
        "saldo_bs": None,
        "algoritmo_cifrado": "hill",
        "created_at": "2026-03-17T10:30:00+00:00",
        "updated_at": "2026-03-17T10:30:00+00:00",
        "created_by": "seed_script",
        "modified_by": "seed_script",
    }

    secure_payload = payload_security.secure_payload(sample_payload, bank_id=5)
    print("PAYLOAD SEGURO:")
    print(secure_payload)

    is_valid = payload_security.validate_payload(secure_payload, bank_id=5)
    print("\n¿Payload válido?:", is_valid)

    code = generate_verification_code()
    print("\nCódigo de verificación:", code)


if __name__ == "__main__":
    main()