from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

import mysql.connector
import psycopg
import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pymongo import MongoClient

from app.config.relational_connections_5banks import DbConfig, RELATIONAL_BANKS_1_TO_5
from app.crypto.manager import CryptoManager
from app.security.keys import KeyManager
from app.security.nonce import NonceManager
from app.security.payload_security import PayloadSecurity

app = FastAPI(title="Bank API - Integrante 4 (1..14)")

# Seguridad (usar lo que ya implementó Integrante 3)
key_manager = KeyManager()
nonce_manager = NonceManager()
payload_security = PayloadSecurity(key_manager, nonce_manager)
crypto = CryptoManager()

# No relacional
MONGO_URI = "mongodb://localhost:27017/"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_PASSWORD = "redis123"

mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)

NON_RELATIONAL_MONGO = {
    6: {"db": "banco_ganadero_db", "collection": "cuentas"},
    7: {"db": "banco_economico_db", "collection": "cuentas"},
    8: {"db": "banco_prodem_db", "collection": "cuentas"},
    9: {"db": "banco_solidario_db", "collection": "cuentas"},
    10: {"db": "banco_fortaleza_db", "collection": "cuentas"},
    11: {"db": "banco_fie_db", "collection": "cuentas"},
    12: {"db": "banco_comunidad_db", "collection": "cuentas"},
    13: {"db": "banco_desarrollo_productivo_db", "collection": "cuentas"},
}
REDIS_BANK_14_PREFIX = "bna"


class SecurePendingRequest(BaseModel):
    limit: int = Field(default=100, ge=1, le=50000)
    timestamp: str
    nonce: str
    hmac: str


class SecureUpdateSaldoRequest(BaseModel):
    saldo_bs: str
    codigo_verificacion: str
    timestamp: str
    nonce: str
    hmac: str


def _validate_secure_payload(payload: Dict[str, Any], bank_id: int | str) -> None:
    if not payload_security.validate_payload(payload, bank_id=bank_id):
        raise HTTPException(status_code=401, detail="Payload inválido o replay detected.")


def _get_relational_cfg(bank_id: int) -> Optional[DbConfig]:
    return RELATIONAL_BANKS_1_TO_5.get(bank_id)


def _connect_relational(cfg: DbConfig):
    if cfg.engine == "postgres":
        return psycopg.connect(
            host=cfg.host,
            port=cfg.port,
            dbname=cfg.database,
            user=cfg.user,
            password=cfg.password,
        )
    return mysql.connector.connect(
        host=cfg.host,
        port=cfg.port,
        database=cfg.database,
        user=cfg.user,
        password=cfg.password,
    )


def _fetch_relational_pending(bank_id: int, limit: int) -> List[Dict[str, Any]]:
    cfg = _get_relational_cfg(bank_id)
    if cfg is None:
        return []

    conn = _connect_relational(cfg)
    try:
        if cfg.engine == "postgres":
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, ci_cipher, nombres_cipher, apellidos_cipher,
                           numero_cuenta_cipher, tipo_cuenta_cipher,
                           saldo_usd_cipher, saldo_bs_cipher, codigo_verificacion
                    FROM cuentas_banco
                    WHERE saldo_bs_cipher IS NULL OR saldo_bs_cipher = ''
                    ORDER BY id
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
        else:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    SELECT id, ci_cipher, nombres_cipher, apellidos_cipher,
                           numero_cuenta_cipher, tipo_cuenta_cipher,
                           saldo_usd_cipher, saldo_bs_cipher, codigo_verificacion
                    FROM cuentas_banco
                    WHERE saldo_bs_cipher IS NULL OR saldo_bs_cipher = ''
                    ORDER BY id
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
            finally:
                cur.close()

        cols = [
            "id",
            "ci_cipher",
            "nombres_cipher",
            "apellidos_cipher",
            "numero_cuenta_cipher",
            "tipo_cuenta_cipher",
            "saldo_usd_cipher",
            "saldo_bs_cipher",
            "codigo_verificacion",
        ]
        return [dict(zip(cols, row)) for row in rows]
    finally:
        conn.close()


def _normalize_nonrel_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc.get("id") or doc.get("_id") or ""),
        "ci_cipher": doc.get("ci_cipher") or doc.get("ci") or "",
        "nombres_cipher": doc.get("nombres_cipher") or "",
        "apellidos_cipher": doc.get("apellidos_cipher") or "",
        "numero_cuenta_cipher": doc.get("numero_cuenta_cipher") or doc.get("numero_cuenta") or "",
        "tipo_cuenta_cipher": doc.get("tipo_cuenta_cipher") or "",
        "saldo_usd_cipher": doc.get("saldo_usd_cipher") or doc.get("saldo_usd") or "",
        "saldo_bs_cipher": doc.get("saldo_bs_cipher") or doc.get("saldo_bs") or "",
        "codigo_verificacion": doc.get("codigo_verificacion") or "",
    }


def _fetch_mongo_pending(bank_id: int, limit: int) -> List[Dict[str, Any]]:
    cfg = NON_RELATIONAL_MONGO.get(bank_id)
    if not cfg:
        return []

    collection = mongo_client[cfg["db"]][cfg["collection"]]
    cursor = collection.find(
        {
            "$or": [
                {"saldo_bs_cipher": {"$exists": False}},
                {"saldo_bs_cipher": None},
                {"saldo_bs_cipher": ""},
                {"saldo_bs": {"$exists": False}},
                {"saldo_bs": None},
                {"saldo_bs": ""},
            ]
        }
    ).limit(limit)

    return [_normalize_nonrel_doc(doc) for doc in cursor]


def _fetch_redis_pending(limit: int) -> List[Dict[str, Any]]:
    cuentas = list(redis_client.smembers(f"{REDIS_BANK_14_PREFIX}:cuentas"))
    cuentas = cuentas[:limit]
    out: List[Dict[str, Any]] = []
    for cuenta in cuentas:
        key = f"{REDIS_BANK_14_PREFIX}:cuenta:{cuenta}"
        data = redis_client.hgetall(key)
        if not data:
            continue
        saldo_bs_cipher = data.get("saldo_bs_cipher") or data.get("saldo_bs") or ""
        if saldo_bs_cipher:
            continue
        out.append(_normalize_nonrel_doc(data))
    return out


def fetch_pending_accounts(bank_id: int, limit: int) -> List[Dict[str, Any]]:
    if bank_id in RELATIONAL_BANKS_1_TO_5:
        return _fetch_relational_pending(bank_id, limit)
    if bank_id in NON_RELATIONAL_MONGO:
        return _fetch_mongo_pending(bank_id, limit)
    if bank_id == 14:
        return _fetch_redis_pending(limit)
    return []


def _encrypt_saldo_bs(bank_id: int, saldo_bs_plain: str) -> str:
    saldo_norm = f"{Decimal(str(saldo_bs_plain)).quantize(Decimal('0.0001')):.4f}"
    return crypto.encrypt_field(bank_id, "saldo_bs", saldo_norm)


def _update_relational(bank_id: int, cuenta_id: str, saldo_bs_cipher: str, codigo_verificacion: str) -> bool:
    cfg = _get_relational_cfg(bank_id)
    if cfg is None:
        return False

    conn = _connect_relational(cfg)
    try:
        if cfg.engine == "postgres":
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE cuentas_banco
                    SET saldo_bs_cipher = %s,
                        codigo_verificacion = %s
                    WHERE id = %s
                    """,
                    (saldo_bs_cipher, codigo_verificacion, int(cuenta_id)),
                )
                updated = cur.rowcount
            conn.commit()
            return updated > 0

        cur = conn.cursor()
        try:
            cur.execute(
                """
                UPDATE cuentas_banco
                SET saldo_bs_cipher = %s,
                    codigo_verificacion = %s
                WHERE id = %s
                """,
                (saldo_bs_cipher, codigo_verificacion, int(cuenta_id)),
            )
            updated = cur.rowcount
            conn.commit()
            return updated > 0
        finally:
            cur.close()
    finally:
        conn.close()


def _update_mongo(bank_id: int, cuenta_id: str, saldo_bs_cipher: str, codigo_verificacion: str) -> bool:
    cfg = NON_RELATIONAL_MONGO.get(bank_id)
    if not cfg:
        return False
    collection = mongo_client[cfg["db"]][cfg["collection"]]
    res = collection.update_one(
        {"id": cuenta_id},
        {"$set": {"saldo_bs_cipher": saldo_bs_cipher, "codigo_verificacion": codigo_verificacion}},
    )
    return res.modified_count > 0


def _update_redis(cuenta_id: str, saldo_bs_cipher: str, codigo_verificacion: str) -> bool:
    key = f"{REDIS_BANK_14_PREFIX}:cuenta:{cuenta_id}"
    if not redis_client.exists(key):
        return False
    redis_client.hset(key, mapping={"saldo_bs_cipher": saldo_bs_cipher, "codigo_verificacion": codigo_verificacion})
    return True


def update_saldo_bs_and_code(bank_id: int, cuenta_id: str, saldo_bs_plain: str, codigo_verificacion: str) -> bool:
    if not codigo_verificacion or len(codigo_verificacion) != 8:
        raise ValueError("codigo_verificacion debe tener 8 caracteres.")

    saldo_bs_cipher = _encrypt_saldo_bs(bank_id, saldo_bs_plain)

    if bank_id in RELATIONAL_BANKS_1_TO_5:
        return _update_relational(bank_id, cuenta_id, saldo_bs_cipher, codigo_verificacion)
    if bank_id in NON_RELATIONAL_MONGO:
        return _update_mongo(bank_id, cuenta_id, saldo_bs_cipher, codigo_verificacion)
    if bank_id == 14:
        return _update_redis(cuenta_id, saldo_bs_cipher, codigo_verificacion)
    return False


@app.post("/banks/{bank_id}/cuentas/pendientes")
def cuentas_pendientes(bank_id: int, req: SecurePendingRequest):
    payload = req.model_dump()
    _validate_secure_payload(payload, bank_id=bank_id)
    accounts = fetch_pending_accounts(bank_id, req.limit)
    return {"bank_id": bank_id, "cuentas": accounts}


@app.put("/banks/{bank_id}/cuentas/{cuenta_id}/saldo")
def update_saldo(bank_id: int, cuenta_id: str, req: SecureUpdateSaldoRequest):
    payload = req.model_dump()
    _validate_secure_payload(payload, bank_id=bank_id)

    updated = update_saldo_bs_and_code(
        bank_id=bank_id,
        cuenta_id=cuenta_id,
        saldo_bs_plain=req.saldo_bs,
        codigo_verificacion=req.codigo_verificacion,
    )

    return {"bank_id": bank_id, "cuenta_id": cuenta_id, "updated": bool(updated)}


@app.get("/health")
def health():
    return {"status": "ok", "scope": "banks 1..14"}
