from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import redis
from pymongo import MongoClient

from app.crypto.manager import CryptoManager


BANK_STORAGE = {
    6: {"storage": "mongo", "db": "banco_ganadero_db", "collection": "cuentas"},
    7: {"storage": "mongo", "db": "banco_economico_db", "collection": "cuentas"},
    8: {"storage": "mongo", "db": "banco_prodem_db", "collection": "cuentas"},
    9: {"storage": "mongo", "db": "banco_solidario_db", "collection": "cuentas"},
    10: {"storage": "mongo", "db": "banco_fortaleza_db", "collection": "cuentas"},
    11: {"storage": "mongo", "db": "banco_fie_db", "collection": "cuentas"},
    12: {"storage": "mongo", "db": "banco_comunidad_db", "collection": "cuentas"},
    13: {"storage": "mongo", "db": "banco_desarrollo_productivo_db", "collection": "cuentas"},
    14: {"storage": "redis", "prefix": "bna"},
}


def _encrypt_record(crypto: CryptoManager, bank_id: int, ci: str, numero_cuenta: str, saldo_usd: str) -> dict:
    plain = {
        "id_banco": bank_id,
        "ci": ci,
        "numero_cuenta": numero_cuenta,
        "saldo_usd": saldo_usd,
        "saldo_bs": "",
    }
    return crypto.encrypt_sensitive_fields(plain)


def main() -> None:
    print("[seed_non_relational] Iniciando carga no relacional 6..14")

    dataset_path = os.path.join(os.path.dirname(__file__), "dataset.csv")
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"No existe dataset.csv en: {dataset_path}")

    mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", "6379"))
    redis_password = os.environ.get("REDIS_PASSWORD", "redis123")

    df = pd.read_csv(dataset_path, dtype={"NroCuenta": str, "Identificacion": str})
    df.columns = df.columns.str.strip()
    sample = df.sample(frac=0.01, random_state=42)

    print(f"[seed_non_relational] Total dataset: {len(df)}")
    print(f"[seed_non_relational] Muestra 1%: {len(sample)}")

    mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    mongo_client.admin.command("ping")
    redis_client = redis.Redis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)

    for cfg in BANK_STORAGE.values():
        if cfg["storage"] == "mongo":
            db_name = cfg["db"]
            if db_name in mongo_client.list_database_names():
                mongo_client.drop_database(db_name)
    redis_client.flushdb()

    crypto = CryptoManager()
    now_iso = datetime.utcnow().isoformat()

    total_mongo = 0
    total_redis = 0

    for bank_id, cfg in BANK_STORAGE.items():
        if cfg["storage"] != "mongo":
            continue

        bank_rows = sample[sample["IdBanco"] == bank_id]
        if len(bank_rows) == 0:
            continue

        collection = mongo_client[cfg["db"]][cfg["collection"]]
        docs = []

        for _, row in bank_rows.iterrows():
            ci = str(row["Identificacion"])
            numero_cuenta = str(row["NroCuenta"])
            saldo_usd = str(row["Saldo"])

            try:
                encrypted = _encrypt_record(crypto, bank_id, ci, numero_cuenta, saldo_usd)
            except Exception as exc:
                print(f"[seed_non_relational] Banco {bank_id} cuenta {numero_cuenta} omitida: {exc}")
                continue

            docs.append(
                {
                    "id_banco": bank_id,
                    "id": numero_cuenta,
                    "ci_cipher": encrypted.get("ci", ""),
                    "numero_cuenta_cipher": encrypted.get("numero_cuenta", ""),
                    "saldo_usd_cipher": encrypted.get("saldo_usd", ""),
                    "saldo_bs_cipher": encrypted.get("saldo_bs", ""),
                    "nombres": str(row["Nombres"]),
                    "apellidos": str(row["Apellidos"]),
                    "codigo_verificacion": "00000000",
                    "created_at": now_iso,
                    "updated_at": now_iso,
                    "is_active": True,
                }
            )

        if docs:
            result = collection.insert_many(docs)
            collection.create_index("id")
            collection.create_index("saldo_bs_cipher")
            total_mongo += len(result.inserted_ids)
            print(f"[seed_non_relational] Banco {bank_id} Mongo: {len(result.inserted_ids)}")

    bank14_rows = sample[sample["IdBanco"] == 14]
    if len(bank14_rows) > 0:
        redis_prefix = BANK_STORAGE[14]["prefix"]
        for _, row in bank14_rows.iterrows():
            numero_cuenta = str(row["NroCuenta"])
            ci = str(row["Identificacion"])
            saldo_usd = str(row["Saldo"])

            try:
                encrypted = _encrypt_record(crypto, 14, ci, numero_cuenta, saldo_usd)
            except Exception as exc:
                print(f"[seed_non_relational] Banco 14 cuenta {numero_cuenta} omitida: {exc}")
                continue

            redis_key = f"{redis_prefix}:cuenta:{numero_cuenta}"
            redis_client.hset(
                redis_key,
                mapping={
                    "id_banco": "14",
                    "id": numero_cuenta,
                    "ci_cipher": encrypted.get("ci", ""),
                    "numero_cuenta_cipher": encrypted.get("numero_cuenta", ""),
                    "saldo_usd_cipher": encrypted.get("saldo_usd", ""),
                    "saldo_bs_cipher": encrypted.get("saldo_bs", ""),
                    "nombres": str(row["Nombres"]),
                    "apellidos": str(row["Apellidos"]),
                    "codigo_verificacion": "00000000",
                    "created_at": now_iso,
                    "updated_at": now_iso,
                    "is_active": "1",
                },
            )
            redis_client.sadd(f"{redis_prefix}:cuentas", numero_cuenta)
            total_redis += 1

        print(f"[seed_non_relational] Banco 14 Redis: {total_redis}")

    print(f"[seed_non_relational] OK Mongo total: {total_mongo}")
    print(f"[seed_non_relational] OK Redis total: {total_redis}")


if __name__ == "__main__":
    main()
