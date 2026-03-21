from app.crypto.manager import CryptoManager


def main():
    crypto = CryptoManager()

    ejemplos = [
        {
            "id_banco": 6,
            "ci": "12345678",
            "numero_cuenta": "6011223344556677",
            "saldo_usd": "1500.2500",
            "saldo_bs": "0.0000",
        },
        {
            "id_banco": 7,
            "ci": "87654321",
            "numero_cuenta": "7011223344556677",
            "saldo_usd": "999.9900",
            "saldo_bs": "0.0000",
        },
        {
            "id_banco": 8,
            "ci": "45678912",
            "numero_cuenta": "8011223344556677",
            "saldo_usd": "250.5000",
            "saldo_bs": "0.0000",
        },
        {
            "id_banco": 9,
            "ci": "11223344",
            "numero_cuenta": "9011223344556677",
            "saldo_usd": "3000.7500",
            "saldo_bs": "0.0000",
        },
        {
            "id_banco": 10,
            "ci": "99887766",
            "numero_cuenta": "10011223344556677",
            "saldo_usd": "120.1000",
            "saldo_bs": "0.0000",
        },
        {
            "id_banco": 11,  # ✅ agregado correctamente
            "ci": "55566677",
            "numero_cuenta": "11011223344556677",
            "saldo_usd": "777.7700",
            "saldo_bs": "0.0000",
        },
        {
            "id_banco": 12,
            "ci": "14725836",
            "numero_cuenta": "12011223344556677",
            "saldo_usd": "555.5500",
            "saldo_bs": "0.0000",
        },
        {
            "id_banco": 13,
            "ci": "36925814",
            "numero_cuenta": "13011223344556677",
            "saldo_usd": "777.7700",
            "saldo_bs": "0.0000",
        },
        {
            "id_banco": 14,
            "ci": "74185296",
            "numero_cuenta": "14011223344556677",
            "saldo_usd": "888.8800",
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

    print("\n✅ Prueba exitosa: cifrado/descifrado correcto en bancos 6–14 (incluyendo 11).")


if __name__ == "__main__":
    main()
