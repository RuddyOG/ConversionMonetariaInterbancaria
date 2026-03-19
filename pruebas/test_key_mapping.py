from app.security.keys import KeyManager
from app.crypto.manager import CryptoManager


def main():
    key_manager = KeyManager()
    crypto = CryptoManager()

    for bank_id in range(1, 15):
        try:
            config = key_manager.get_bank_config(bank_id)
            algorithm = config["algorithm"]
            print(f"Banco {bank_id}: {algorithm}")

            if bank_id == 11:
                print("  ⚠️ RSA pendiente de llaves reales")
                continue

            module = crypto._get_cipher_module(bank_id)
            print(f"  ✅ Módulo cargado: {module.__name__}")

        except Exception as e:
            print(f"  ❌ Error en banco {bank_id}: {e}")

if __name__ == "__main__":
    main()