from __future__ import annotations

import secrets
from datetime import datetime
from typing import Dict, Callable

import pandas as pd
import psycopg
import mysql.connector

HEX_ALPHABET = "0123456789ABCDEF"
TOTAL_MUESTRA = 1238

BANKS: Dict[int, dict] = {
    1: {
        "name": "Banco Union",
        "algo": "caesar",
        "engine": "postgres",
        "host": "localhost",
        "port": 5433,
        "dbname": "banco_union",
        "user": "admin",
        "password": "union123",
    },
    2: {
        "name": "Banco Mercantil Santa Cruz",
        "algo": "atbash",
        "engine": "mysql",
        "host": "localhost",
        "port": 3307,
        "dbname": "banco_mercantil",
        "user": "admin",
        "password": "mercantil123",
    },
    3: {
        "name": "Banco Nacional de Bolivia",
        "algo": "vigenere",
        "engine": "mariadb",
        "host": "localhost",
        "port": 3308,
        "dbname": "banco_bnb",
        "user": "admin",
        "password": "bnb123",
    },
    4: {
        "name": "Banco de Credito de Bolivia",
        "algo": "playfair",
        "engine": "postgres",
        "host": "localhost",
        "port": 5434,
        "dbname": "banco_bcp",
        "user": "admin",
        "password": "bcp123",
    },
    5: {
        "name": "Banco BISA",
        "algo": "hill",
        "engine": "mysql",
        "host": "localhost",
        "port": 3309,
        "dbname": "banco_bisa",
        "user": "admin",
        "password": "bisa123",
    },
}


def to_hex_text(value: str) -> str:
    return str(value).encode("utf-8").hex().upper()


def gen_verification_code() -> str:
    return "".join(secrets.choice(HEX_ALPHABET) for _ in range(8))


def caesar_hex(text: str, shift: int = 3) -> str:
    source = to_hex_text(text)
    return "".join(HEX_ALPHABET[(HEX_ALPHABET.index(ch) + shift) % 16] for ch in source)


def atbash_hex(text: str) -> str:
    source = to_hex_text(text)
    return "".join(HEX_ALPHABET[15 - HEX_ALPHABET.index(ch)] for ch in source)


def vigenere_hex(text: str, key: str = "B0A1") -> str:
    source = to_hex_text(text)
    key = "".join(ch for ch in key.upper() if ch in HEX_ALPHABET)
    out = []
    for i, ch in enumerate(source):
        p = HEX_ALPHABET.index(ch)
        k = HEX_ALPHABET.index(key[i % len(key)])
        out.append(HEX_ALPHABET[(p + k) % 16])
    return "".join(out)


def build_playfair_matrix(key_text: str = "BCP2026"):
    key_hex = to_hex_text(key_text)
    seen = []
    for ch in key_hex + HEX_ALPHABET:
        if ch in HEX_ALPHABET and ch not in seen:
            seen.append(ch)
    matrix = [seen[i:i + 4] for i in range(0, 16, 4)]
    pos = {matrix[r][c]: (r, c) for r in range(4) for c in range(4)}
    return matrix, pos


def playfair_prepare(source: str, filler: str = "F") -> list[str]:
    pairs = []
    i = 0
    while i < len(source):
        a = source[i]
        if i + 1 >= len(source):
            b = filler
            i += 1
        else:
            b = source[i + 1]
            if a == b:
                b = filler
                i += 1
            else:
                i += 2
        pairs.append(a + b)
    return pairs


def playfair_hex(text: str, key_text: str = "BCP2026") -> str:
    source = to_hex_text(text)
    matrix, pos = build_playfair_matrix(key_text)
    pairs = playfair_prepare(source)
    out = []
    for pair in pairs:
        a, b = pair[0], pair[1]
        ra, ca = pos[a]
        rb, cb = pos[b]
        if ra == rb:
            out.append(matrix[ra][(ca + 1) % 4])
            out.append(matrix[rb][(cb + 1) % 4])
        elif ca == cb:
            out.append(matrix[(ra + 1) % 4][ca])
            out.append(matrix[(rb + 1) % 4][cb])
        else:
            out.append(matrix[ra][cb])
            out.append(matrix[rb][ca])
    return "".join(out)


def hill_hex(text: str) -> str:
    source = to_hex_text(text)
    if len(source) % 2 != 0:
        source += "F"
    out = []
    a, b, c, d = 3, 3, 2, 5
    for i in range(0, len(source), 2):
        x = HEX_ALPHABET.index(source[i])
        y = HEX_ALPHABET.index(source[i + 1])
        e1 = (a * x + b * y) % 16
        e2 = (c * x + d * y) % 16
        out.append(HEX_ALPHABET[e1])
        out.append(HEX_ALPHABET[e2])
    return "".join(out)


ENCRYPTORS: Dict[str, Callable[[str], str]] = {
    "caesar": caesar_hex,
    "atbash": atbash_hex,
    "vigenere": vigenere_hex,
    "playfair": playfair_hex,
    "hill": hill_hex,
}


def pg_connect(cfg: dict):
    return psycopg.connect(
        host=cfg["host"],
        port=cfg["port"],
        dbname=cfg["dbname"],
        user=cfg["user"],
        password=cfg["password"],
    )


def mysql_connect(cfg: dict):
    return mysql.connector.connect(
        host=cfg["host"],
        port=cfg["port"],
        database=cfg["dbname"],
        user=cfg["user"],
        password=cfg["password"],
    )


def get_conn(cfg: dict):
    if cfg["engine"] == "postgres":
        return pg_connect(cfg)
    return mysql_connect(cfg)


def insert_bank_record(conn, engine: str, record: dict) -> int:
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
        record["created_by"],
        record["updated_by"],
        record["is_active"],
    )

    if engine == "postgres":
        sql += " RETURNING id"

    with conn.cursor() as cur:
        cur.execute(sql, values)
        if engine == "postgres":
            return cur.fetchone()[0]
        return cur.lastrowid


def main():
    csv_path = "01 - Practica 2 Dataset.csv"

    df = pd.read_csv(csv_path, dtype=str).fillna("")

    if "IdBanco" not in df.columns:
        raise ValueError("No se encontró la columna 'IdBanco' en el CSV.")

    df["IdBanco"] = df["IdBanco"].astype(int)

    # Solo bancos relacionales 1..5
    df = df[df["IdBanco"].isin(BANKS.keys())].copy()

    # Tomar exactamente 1238 registros
    muestra = df.sample(n=TOTAL_MUESTRA, random_state=42).copy()

    total_insertados = 0
    resumen = {}

    for banco_id, cfg in BANKS.items():
        bank_df = muestra[muestra["IdBanco"] == banco_id].copy()
        resumen[cfg["name"]] = len(bank_df)

        if bank_df.empty:
            continue

        encrypt = ENCRYPTORS[cfg["algo"]]
        bank_conn = get_conn(cfg)

        try:
            for _, row in bank_df.iterrows():
                codigo = gen_verification_code()
                now = datetime.now().isoformat()

                identificacion = row.get("Identificacion", row.get("Identification", ""))
                nro_cuenta = row.get("NroCuenta", "")
                nombres = row.get("Nombres", "")
                apellidos = row.get("Apellidos", "")
                saldo = row.get("Saldo", "0")

                bank_record = {
                    "ci": str(identificacion),
                    "nombres": str(nombres),
                    "apellidos": str(apellidos),
                    "numero_cuenta": str(nro_cuenta),
                    "saldo_usd": str(saldo),
                    "saldo_bs": "",
                    "codigo_verificacion": codigo,
                    "created_at": now,
                    "updated_at": now,
                    "created_by": None,
                    "updated_by": None,
                    "is_active": True,
                }

                insert_bank_record(bank_conn, cfg["engine"], bank_record)
                total_insertados += 1

            bank_conn.commit()
            print(f"[OK] {cfg['name']}: {len(bank_df)} registros insertados.")
        except Exception:
            bank_conn.rollback()
            raise
        finally:
            bank_conn.close()

    print("\nResumen por banco:")
    for banco, cantidad in resumen.items():
        print(f"- {banco}: {cantidad}")

    print(f"\nCarga finalizada. Total insertado: {total_insertados}")


if __name__ == "__main__":
    main()