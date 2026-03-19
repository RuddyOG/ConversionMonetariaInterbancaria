from app.security.keys import KeyManager
from app.security.nonce import NonceManager
from app.security.payload_security import PayloadSecurity


def main():
    key_manager = KeyManager()
    nonce_manager = NonceManager()
    payload_security = PayloadSecurity(key_manager, nonce_manager)

    bank_id = 1
    payload = {
        "id_banco": bank_id,
        "ci": "ABC12345",
        "numero_cuenta": "1019441616706120",
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
    assert valido is True, "El payload debería ser válido"

    replay = payload_security.validate_payload(seguro, bank_id)
    print(f"¿Replay detectado?: {not replay}")
    assert replay is False, "El replay debería ser detectado"

    print("\n✅ Prueba 2 exitosa: HMAC, timestamp y nonce funcionando.")


if __name__ == "__main__":
    main()