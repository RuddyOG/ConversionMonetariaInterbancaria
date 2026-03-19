from app.security.keys import KeyManager
from app.security.nonce import NonceManager
from app.security.payload_security import PayloadSecurity


def main():
    key_manager = KeyManager()
    nonce_manager = NonceManager()
    payload_security = PayloadSecurity(key_manager, nonce_manager)

    bank_id = 10
    payload = {
        "id_banco": bank_id,
        "ci": "ABC12345",
        "numero_cuenta": "10011223344556677",
        "saldo_usd": "1500.2500",
        "saldo_bs": "0.0000",
        "nombres": "Carlos",
        "apellidos": "Lopez",
    }

    seguro = payload_security.secure_payload(payload, bank_id)

    print("\n" + "=" * 70)
    print("PAYLOAD ORIGINAL")
    print(payload)

    print("\nPAYLOAD SEGURO")
    print(seguro)

    valido = payload_security.validate_payload(seguro, bank_id)
    print(f"\n¿Payload válido?: {valido}")

    replay = payload_security.validate_payload(seguro, bank_id)
    print(f"¿Replay detectado?: {not replay}")

    assert valido is True
    assert replay is False

    print("\n✅ Prueba payload moderno exitosa.")


if __name__ == "__main__":
    main()