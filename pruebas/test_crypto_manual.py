from app.crypto.manager import CryptoManager
from app.security.keys import KeyManager
from app.security.nonce import NonceManager
from app.security.payload_security import PayloadSecurity
from app.security.verification_code import generate_verification_code


def main():
    crypto = CryptoManager()
    key_manager = KeyManager()
    nonce_manager = NonceManager()
    payload_security = PayloadSecurity(key_manager, nonce_manager)

    sample_record = {
        "id": 20617,
        "ci": "5977236805",
        "nombres": "Sofia Elena",
        "apellidos": "Perez Rodriguez",
        "nro_cuenta": "6490200000000001",
        "id_banco": 1,
        "saldo_usd": "3499999.2130",
        "tipo_cambio": "6.9600",
        "saldo_bs": None,
        "created_at": "2026-03-17T10:30:00+00:00",
        "updated_at": "2026-03-17T10:30:00+00:00",
        "created_by": "seed_script",
        "modified_by": "seed_script"
    }

    print("REGISTRO ORIGINAL:")
    print(sample_record)

    encrypted_record = crypto.encrypt_sensitive_fields(sample_record)
    print("\nREGISTRO CIFRADO:")
    print(encrypted_record)

    secure_payload = payload_security.secure_payload(encrypted_record, bank_id=sample_record["id_banco"])
    print("\nPAYLOAD SEGURO:")
    print(secure_payload)

    is_valid = payload_security.validate_payload(secure_payload, bank_id=sample_record["id_banco"])
    print("\n¿PAYLOAD VÁLIDO?:", is_valid)

    decrypted_record = crypto.decrypt_sensitive_fields(encrypted_record)
    print("\nREGISTRO DESCIFRADO:")
    print(decrypted_record)

    verification_code = generate_verification_code()
    print("\nCÓDIGO DE VERIFICACIÓN:", verification_code)


if __name__ == "__main__":
    main()