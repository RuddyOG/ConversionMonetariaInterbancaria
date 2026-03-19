from app.crypto.manager import CryptoManager


def main():
    crypto = CryptoManager()

    ejemplos = [
        {
            "id_banco": 1,
            "ci": "12345678",
            "numero_cuenta": "1019441616706120",
            "saldo_usd": "1500.2500",
            "saldo_bs": "0.0000",
        },
        {
            "id_banco": 2,
            "ci": "87654321",
            "numero_cuenta": "2022334455667788",
            "saldo_usd": "999.9900",
            "saldo_bs": "0.0000",
        },
        {
            "id_banco": 3,
            "ci": "45678912",
            "numero_cuenta": "3033445566778899",
            "saldo_usd": "250.5000",
            "saldo_bs": "0.0000",
        },
        {
            "id_banco": 4,
            "ci": "11223344",
            "numero_cuenta": "4044556677889900",
            "saldo_usd": "3000.7500",
            "saldo_bs": "0.0000",
        },
        {
            "id_banco": 5,
            "ci": "99887766",
            "numero_cuenta": "5055667788990011",
            "saldo_usd": "120.1000",
            "saldo_bs": "0.0000",
        },
    ]

    for original in ejemplos:
        print("\n" + "=" * 70)
        print(f"Banco {original['id_banco']} - ORIGINAL")
        print(original)

        cifrado = crypto.encrypt_sensitive_fields(original)
        print("\nCIFRADO")
        print(cifrado)

        descifrado = crypto.decrypt_sensitive_fields(cifrado)
        print("\nDESCIFRADO")
        print(descifrado)

        assert descifrado["ci"] == original["ci"], "CI no coincide"
        assert descifrado["numero_cuenta"] == original["numero_cuenta"], "Número de cuenta no coincide"
        assert descifrado["saldo_usd"] == original["saldo_usd"], "Saldo USD no coincide"
        assert descifrado["saldo_bs"] == original["saldo_bs"], "Saldo Bs no coincide"

    print("\n✅ Prueba 1 exitosa: cifrado/descifrado correcto en bancos 1 al 5.")


if __name__ == "__main__":
    main()