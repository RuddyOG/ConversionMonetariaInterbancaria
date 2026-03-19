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

        try:
            descifrado = crypto.decrypt_sensitive_fields(row)
            print("\nREGISTRO DESCIFRADO")
            print(descifrado)
            print("\n✅ OK")
        except Exception as e:
            print(f"\n❌ Error al descifrar: {e}")


if __name__ == "__main__":
    main()