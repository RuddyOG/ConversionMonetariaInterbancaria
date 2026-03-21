from pathlib import Path
from datetime import datetime
import pandas as pd
from pymongo import MongoClient
import redis

from app.crypto.manager import CryptoManager

# =========================
# CONFIG
# =========================
MONGO_URI = "mongodb://localhost:27017/"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_PASSWORD = "redis123"

# =========================
# BANCOS NO RELACIONALES
# =========================
BANCOS_MONGO = {
    6: "banco_ganadero_db",
    7: "banco_economico_db",
    8: "banco_prodem_db",
    9: "banco_solidario_db",
    10: "banco_fortaleza_db",
    11: "banco_fie_db",
    12: "banco_comunidad_db",
    13: "banco_desarrollo_productivo_db",
}

# =========================
# INIT
# =========================
crypto = CryptoManager()
mongo_client = MongoClient(MONGO_URI)
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

# =========================
# MAIN
# =========================
def main():
    print("🚀 Iniciando carga de bancos no relacionales...")

    base_dir = Path(__file__).resolve().parent
    csv_path = base_dir / "dataset.csv"

    df = pd.read_csv(csv_path)
    muestra = df.sample(frac=0.01, random_state=42)

    fecha_actual = datetime.now().isoformat()

    # =========================
    # LIMPIAR REDIS
    # =========================
    redis_client.flushdb()

    # =========================
    # 📦 MONGO (BANCOS 6–13)
    # =========================
    for banco_id, db_name in BANCOS_MONGO.items():
        df_banco = muestra[muestra["IdBanco"] == banco_id]

        if df_banco.empty:
            print(f"⚠ Banco {banco_id} sin datos")
            continue

        db = mongo_client[db_name]
        col = db["cuentas"]

        col.delete_many({})

        docs = []

        for _, row in df_banco.iterrows():
            cuenta_id = str(row["NroCuenta"])

            doc = {
                "id": cuenta_id,

                # DATOS CIFRADOS (requisito práctica)
                "ci": crypto.encrypt_field(banco_id, "ci", row["Identificacion"]),
                "numero_cuenta": crypto.encrypt_field(banco_id, "numero_cuenta", row["NroCuenta"]),
                "saldo_usd_cipher": crypto.encrypt_field(banco_id, "saldo_usd", row["Saldo"]),

                # CAMPOS PARA ASFI
                "saldo_bs_cipher": "",
                "codigo_verificacion": "",

                # METADATA
                "id_banco": banco_id,
                "algoritmo_cifrado": crypto.key_manager.get_algorithm(banco_id),
                "created_at": fecha_actual,
                "updated_at": fecha_actual,
                "is_active": True
            }

            docs.append(doc)

        col.insert_many(docs)

        print(f"✅ Banco {banco_id}: {len(docs)} registros insertados")

    # =========================
    # 🔴 REDIS (BANCO 14)
    # =========================
    df_14 = muestra[muestra["IdBanco"] == 14]

    for _, row in df_14.iterrows():
        cuenta_id = str(row["NroCuenta"])

        redis_client.hset(f"bna:cuenta:{cuenta_id}", mapping={
            "id": cuenta_id,
            "id_banco": 14,

            # CIFRADO
            "ci": crypto.encrypt_field(14, "ci", row["Identificacion"]),
            "numero_cuenta": crypto.encrypt_field(14, "numero_cuenta", row["NroCuenta"]),
            "saldo_usd_cipher": crypto.encrypt_field(14, "saldo_usd", row["Saldo"]),

            # CAMPOS ASFI
            "saldo_bs_cipher": "",
            "codigo_verificacion": "",

            # METADATA
            "algoritmo_cifrado": crypto.key_manager.get_algorithm(14),
            "created_at": fecha_actual,
            "updated_at": fecha_actual,
            "is_active": "true"
        })

    print(f"✅ Banco 14: {len(df_14)} registros en Redis")

    print("🎯 Seed completado correctamente")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()