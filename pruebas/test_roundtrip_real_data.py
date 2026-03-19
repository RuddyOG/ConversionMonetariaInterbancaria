import psycopg
import mysql.connector

from app.crypto.manager import CryptoManager


BANKS = {
    1: {
        "name": "Banco Unión",
        "engine": "postgres",
        "host": "localhost",
        "port": 5433,
        "dbname": "banco_union",
        "user": "admin",
        "password": "union123",
    },
    2: {
        "name": "Banco Mercantil Santa Cruz",
        "engine": "mysql",
        "host": "localhost",
        "port": 3307,
        "dbname": "banco_mercantil",
        "user": "admin",
        "password": "mercantil123",
    },
    3: {
        "name": "Banco Nacional de Bolivia",
        "engine": "mysql",
        "host": "localhost",
        "port": 3308,
        "dbname": "banco_bnb",
        "user": "admin",
        "password": "bnb123",
    },
    4: {
        "name": "Banco de Crédito de Bolivia",
        "engine": "postgres",
        "host": "localhost",
        "port": 5434,
        "dbname": "banco_bcp",
        "user": "admin",
        "password": "bcp123",
    },
    5: {
        "name": "Banco BISA",
        "engine": "mysql",
        "host": "localhost",
        "port": 3309,
        "dbname": "banco_bisa",
        "user": "admin",
        "password": "bisa123",
    },
}


def get_postgres_conn(cfg):
    return psycopg.connect(
        host=cfg["host"],
        port=cfg["port"],
        dbname=cfg["dbname"],
        user=cfg["user"],
        password=cfg["password"],
    )


def get_mysql_conn(cfg):
    return mysql.connector.connect(
        host=cfg["host"],
        port=cfg["port"],
        database=cfg["dbname"],
        user=cfg["user"],
        password=cfg["password"],
    )


def fetch_one_record(cfg):
    sql = """
        SELECT id, ci, numero_cuenta, saldo_usd, saldo_bs
        FROM cuentas_banco
        LIMIT 1
    """

    if cfg["engine"] == "postgres":
        conn = get_postgres_conn(cfg)
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                row = cur.fetchone()
                if not row:
                    return None
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        finally:
            conn.close()

    conn = get_mysql_conn(cfg)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql)
        row = cur.fetchone()
        cur.close()
        return row
    finally:
        conn.close()


def main():
    crypto = CryptoManager()

    for bank_id, cfg in BANKS.items():
        print("\n" + "=" * 70)
        print(f"{cfg['name']} (Banco {bank_id})")

        row = fetch_one_record(cfg)
        if not row:
            print("⚠️ Sin registros")
            continue

        row["id_banco"] = bank_id

        print("\nREGISTRO CIFRADO DESDE BD")
        print(row)

        descifrado = crypto.decrypt_sensitive_fields(row)
        print("\nREGISTRO DESCIFRADO")
        print(descifrado)

        re_cifrado = crypto.encrypt_sensitive_fields(descifrado)
        print("\nREGISTRO RE-CIFRADO")
        print(re_cifrado)

        re_descifrado = crypto.decrypt_sensitive_fields(re_cifrado)
        print("\nREGISTRO RE-DESCIFRADO")
        print(re_descifrado)

        assert re_descifrado["ci"] == descifrado["ci"]
        assert re_descifrado["numero_cuenta"] == descifrado["numero_cuenta"]
        assert re_descifrado["saldo_usd"] == descifrado["saldo_usd"]

        if descifrado.get("saldo_bs") not in (None, ""):
            assert re_descifrado["saldo_bs"] == descifrado["saldo_bs"]

        print("\n✅ Roundtrip real correcto")

    print("\n🎉 Prueba roundtrip real completada.")
    

if __name__ == "__main__":
    main()