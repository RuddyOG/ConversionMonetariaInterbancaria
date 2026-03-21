from __future__ import annotations

from datetime import datetime
import pandas as pd

from app.crypto.manager import CryptoManager

import mysql.connector
import psycopg

TOTAL_MUESTRA = 1238
crypto = CryptoManager()


# =========================
# CONEXIÓN REAL (TU DOCKER)
# =========================
def _connect(banco_id):

    # 🟣 BANCO 1 → POSTGRES
    if banco_id == 1:
        return psycopg.connect(
            host="127.0.0.1",
            port=5433,
            dbname="banco_union",
            user="admin",
            password="union123"
        )

    # 🟡 BANCO 2 → MYSQL
    if banco_id == 2:
        return mysql.connector.connect(
            host="127.0.0.1",
            port=3307,
            database="banco_mercantil",
            user="admin",
            password="mercantil123"
        )

    # 🟠 BANCO 3 → MARIADB
    if banco_id == 3:
        return mysql.connector.connect(
            host="127.0.0.1",
            port=3308,
            database="banco_bnb",
            user="admin",
            password="bnb123"
        )

    # 🔵 BANCO 4 → MYSQL (BISA)
    if banco_id == 4:
        return mysql.connector.connect(
            host="127.0.0.1",
            port=3309,
            database="banco_bisa",
            user="admin",
            password="bisa123"
        )

    # 🔴 BANCO 5 → POSTGRES (BCP)
    if banco_id == 5:
        return psycopg.connect(
            host="127.0.0.1",
            port=5434,
            dbname="banco_bcp",
            user="admin",
            password="bcp123"
        )


# =========================
# LIMPIAR TABLA
# =========================
def clear_table(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM cuentas_banco")
    conn.commit()
    cur.close()


# =========================
# INSERT
# =========================
def insert_record(conn, record):
    sql = """
        INSERT INTO cuentas_banco (
            ci,
            nombres,
            apellidos,
            numero_cuenta,
            saldo_usd,
            saldo_bs,
            codigo_verificacion,
            created_at,
            updated_at,
            created_by,
            updated_by,
            is_active
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        record["ci"],
        record["nombres"],
        record["apellidos"],
        record["numero_cuenta"],
        record["saldo_usd"],
        record["saldo_bs"],
        record["codigo_verificacion"],
        record["created_at"],
        record["updated_at"],
        None,
        None,
        True,
    )

    cur = conn.cursor()
    cur.execute(sql, values)
    cur.close()


# =========================
# MAIN
# =========================
def main():
    print("🚀 Seed bancos 1–5 (CONFIG REAL)...")

    df = pd.read_csv("app/db/seed(datos)/dataset.csv", dtype=str).fillna("")
    df["IdBanco"] = df["IdBanco"].astype(int)

    df = df[df["IdBanco"].isin([1, 2, 3, 4, 5])]

    muestra = df.sample(n=TOTAL_MUESTRA, random_state=42)

    for banco_id in [1, 2, 3, 4, 5]:
        print(f"\n🔄 Banco {banco_id}...")

        bank_df = muestra[muestra["IdBanco"] == banco_id]

        if bank_df.empty:
            print(f"⚠ Banco {banco_id} sin datos")
            continue

        conn = _connect(banco_id)

        try:
            clear_table(conn)

            for _, row in bank_df.iterrows():
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                record = {
                    "ci": crypto.encrypt_field(banco_id, "ci", row["Identificacion"]),
                    "nombres": row["Nombres"],
                    "apellidos": row["Apellidos"],
                    "numero_cuenta": crypto.encrypt_field(banco_id, "numero_cuenta", row["NroCuenta"]),
                    "saldo_usd": crypto.encrypt_field(banco_id, "saldo_usd", row["Saldo"]),
                    "saldo_bs": "",
                    "codigo_verificacion": "",
                    "created_at": now,
                    "updated_at": now,
                }

                insert_record(conn, record)

            conn.commit()
            print(f"✅ Banco {banco_id}: {len(bank_df)} registros")

        except Exception as e:
            conn.rollback()
            print(f"❌ Error banco {banco_id}: {e}")

        finally:
            conn.close()

    print("\n🎯 Seed COMPLETADO")


if __name__ == "__main__":
    main()