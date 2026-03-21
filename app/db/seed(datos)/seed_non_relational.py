from __future__ import annotations

import os
from datetime import datetime
import base64
import hashlib
import secrets

from Crypto.Cipher import DES, DES3, Blowfish, AES, ChaCha20
from Crypto.Util.Padding import pad

import pandas as pd
import redis
from pymongo import MongoClient


# =========================
# 🔑 GENERACIÓN DE CLAVES
# =========================
def generar_claves():
    claves = {}

    claves['des'] = os.urandom(8)
    claves['3des'] = os.urandom(24)
    claves['blowfish'] = os.urandom(16)
    claves['twofish'] = os.urandom(32)
    claves['aes'] = os.urandom(32)
    claves['chacha20'] = os.urandom(32)

    return claves


CLAVES = generar_claves()


# =========================
# 📋 MAPEO DE BANCOS
# =========================
bancos = {
    6: {"nombre_db": "banco_ganadero_db", "algoritmo": "DES", "clave": CLAVES['des']},
    7: {"nombre_db": "banco_economico_db", "algoritmo": "3DES", "clave": CLAVES['3des']},
    8: {"nombre_db": "banco_prodem_db", "algoritmo": "Blowfish", "clave": CLAVES['blowfish']},
    9: {"nombre_db": "banco_solidario_db", "algoritmo": "Twofish", "clave": CLAVES['twofish']},
    10: {"nombre_db": "banco_fortaleza_db", "algoritmo": "AES", "clave": CLAVES['aes']},
    11: {"nombre_db": "banco_fie_db", "algoritmo": "AES", "clave": CLAVES['aes']},
    12: {"nombre_db": "banco_comunidad_db", "algoritmo": "AES", "clave": CLAVES['aes']},
    13: {"nombre_db": "banco_desarrollo_productivo_db", "algoritmo": "AES", "clave": CLAVES['aes']},
    14: {"nombre_db": "banco_nacion_argentina_db", "algoritmo": "ChaCha20", "clave": CLAVES['chacha20']}
}


# =========================
# 🧠 UTILIDADES
# =========================
def generar_codigo_verificacion(ci, numero_cuenta):
    data = f"{ci}_{numero_cuenta}_{datetime.now().timestamp()}"
    return hashlib.sha256(data.encode()).hexdigest()[:20]


def generar_id_unico():
    timestamp = int(datetime.now().timestamp() * 1000)
    random_part = secrets.token_hex(8)
    contador = secrets.randbits(24)
    return f"{timestamp:x}{random_part}{contador:x}"[:24]


# =========================
# 🔐 FUNCIONES DE ENCRIPTACIÓN
# =========================
def encriptar_des(valor, clave):
    cipher = DES.new(clave[:8], DES.MODE_CBC)
    data = str(valor).encode()
    return base64.b64encode(cipher.iv + cipher.encrypt(pad(data, DES.block_size))).decode()


def encriptar_3des(valor, clave):
    cipher = DES3.new(clave[:24], DES3.MODE_CBC)
    data = str(valor).encode()
    return base64.b64encode(cipher.iv + cipher.encrypt(pad(data, DES3.block_size))).decode()


def encriptar_blowfish(valor, clave):
    cipher = Blowfish.new(clave[:16], Blowfish.MODE_CBC)
    data = str(valor).encode()
    return base64.b64encode(cipher.iv + cipher.encrypt(pad(data, Blowfish.block_size))).decode()


def encriptar_twofish(valor, clave):
    cipher = AES.new(clave[:32], AES.MODE_CBC)  # simulación
    data = str(valor).encode()
    return base64.b64encode(cipher.iv + cipher.encrypt(pad(data, AES.block_size))).decode()


def encriptar_aes(valor, clave):
    cipher = AES.new(clave[:32], AES.MODE_CBC)
    data = str(valor).encode()
    return base64.b64encode(cipher.iv + cipher.encrypt(pad(data, AES.block_size))).decode()


def encriptar_chacha20(valor, clave):
    nonce = os.urandom(8)
    cipher = ChaCha20.new(key=clave[:32], nonce=nonce)
    data = str(valor).encode()
    return base64.b64encode(nonce + cipher.encrypt(data)).decode()


def encriptar_por_banco(banco_id, valor):
    banco = bancos.get(banco_id)
    if not banco:
        return valor

    algoritmo = banco["algoritmo"]
    clave = banco["clave"]

    try:
        if algoritmo == "DES":
            return encriptar_des(valor, clave)
        elif algoritmo == "3DES":
            return encriptar_3des(valor, clave)
        elif algoritmo == "Blowfish":
            return encriptar_blowfish(valor, clave)
        elif algoritmo == "Twofish":
            return encriptar_twofish(valor, clave)
        elif algoritmo == "AES":
            return encriptar_aes(valor, clave)
        elif algoritmo == "ChaCha20":
            return encriptar_chacha20(valor, clave)
    except Exception as e:
        print(f"⚠️ Error encriptando: {e}")
        return valor


# =========================
# 🚀 MAIN
# =========================
def main():
    print("🚀 Iniciando carga...")

    df = pd.read_csv("dataset.csv")
    muestra = df.sample(frac=0.01, random_state=42)

    mongo_client = MongoClient("mongodb://localhost:27017/")
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

    redis_client.flushdb()

    fecha_actual = datetime.now().isoformat()

    # =========================
    # 📦 MONGODB
    # =========================
    for banco_id in range(6, 14):
        if banco_id not in bancos:
            continue

        df_banco = muestra[muestra["IdBanco"] == banco_id]
        if df_banco.empty:
            continue

        banco = bancos[banco_id]
        db = mongo_client[banco["nombre_db"]]
        col = db["cuentas"]

        docs = []
        for _, row in df_banco.iterrows():
            docs.append({
                "ci": encriptar_por_banco(banco_id, row["Identificacion"]),
                "numero_cuenta": encriptar_por_banco(banco_id, row["NroCuenta"]),
                "saldo": encriptar_por_banco(banco_id, row["Saldo"]),
                "codigo_verificacion": generar_codigo_verificacion(row["Identificacion"], row["NroCuenta"]),
                "created_at": fecha_actual
            })

        col.insert_many(docs)
        print(f"✅ Banco {banco_id}: {len(docs)} registros")

    # =========================
    # ⚡ REDIS (BANCO 14)
    # =========================
    df_redis = muestra[muestra["IdBanco"] == 14]

    for _, row in df_redis.iterrows():
        cuenta = str(row["NroCuenta"])

        redis_client.hset(f"banco14:{cuenta}", mapping={
            "ci": encriptar_chacha20(row["Identificacion"], bancos[14]["clave"]),
            "saldo": encriptar_chacha20(row["Saldo"], bancos[14]["clave"]),
            "created_at": fecha_actual
        })

    print("⚡ Redis cargado")


if __name__ == "__main__":
    main()
