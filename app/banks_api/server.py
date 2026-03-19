from __future__ import annotations

import os
from decimal import Decimal
from typing import Any, Dict, List, Optional

import mysql.connector
import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.asfi.hex_crypto_compat_load import encrypt_balance_to_cipher
from app.config.relational_connections_5banks import RELATIONAL_BANKS_1_TO_5, algorithm_for_bank_1_to_5, DbConfig
from app.security.keys import KeyManager
from app.security.nonce import NonceManager
from app.security.payload_security import PayloadSecurity


app = FastAPI(title="Bank API - Integrante 4 (bancos relacionales 1..5)")

key_manager = KeyManager()
nonce_manager = NonceManager()
payload_security = PayloadSecurity(key_manager, nonce_manager)


def _get_bank_db_config(bank_id: int) -> Optional[DbConfig]:
    return RELATIONAL_BANKS_1_TO_5.get(bank_id)


def _connect(cfg: DbConfig):
    if cfg.engine == "postgres":
        return psycopg.connect(
            host=cfg.host,
            port=cfg.port,
            dbname=cfg.database,
            user=cfg.user,
            password=cfg.password,
        )
    # mysql/mariadb
    return mysql.connector.connect(
        host=cfg.host,
        port=cfg.port,
        database=cfg.database,
        user=cfg.user,
        password=cfg.password,
    )


def _fetch_pending_accounts_postgres(conn, limit: int) -> List[Dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                id,
                ci_cipher,
                nombres_cipher,
                apellidos_cipher,
                numero_cuenta_cipher,
                tipo_cuenta_cipher,
                saldo_usd_cipher,
                saldo_bs_cipher,
                codigo_verificacion
            FROM cuentas_banco
            WHERE saldo_bs_cipher IS NULL OR saldo_bs_cipher = ''
            ORDER BY id
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
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


def _fetch_pending_accounts_mysql(conn, limit: int) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT
                id,
                ci_cipher,
                nombres_cipher,
                apellidos_cipher,
                numero_cuenta_cipher,
                tipo_cuenta_cipher,
                saldo_usd_cipher,
                saldo_bs_cipher,
                codigo_verificacion
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


def fetch_pending_accounts(bank_id: int, limit: int) -> List[Dict[str, Any]]:
    cfg = _get_bank_db_config(bank_id)
    if cfg is None:
        return []
    conn = _connect(cfg)
    try:
        if cfg.engine == "postgres":
            return _fetch_pending_accounts_postgres(conn, limit)
        return _fetch_pending_accounts_mysql(conn, limit)
    finally:
        conn.close()


def update_saldo_bs_and_code(bank_id: int, cuenta_id: int, saldo_bs_plain: str, codigo_verificacion: str) -> bool:
    cfg = _get_bank_db_config(bank_id)
    if cfg is None:
        # Stub: si en el futuro hay bancos no relacionales, se implementa el adapter.
        return False

    if not codigo_verificacion or len(codigo_verificacion) != 8:
        raise ValueError("codigo_verificacion debe tener 8 caracteres.")

    # Cifrar saldo Bs según algoritmo del banco.
    saldo_bs_plain_norm = str(Decimal(saldo_bs_plain)).strip()
    saldo_bs_plain_norm = f"{Decimal(saldo_bs_plain_norm).quantize(Decimal('0.0001')):.4f}"
    saldo_bs_cipher = encrypt_balance_to_cipher(bank_id, saldo_bs_plain_norm)

    conn = _connect(cfg)
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
                    (saldo_bs_cipher, codigo_verificacion, cuenta_id),
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
                (saldo_bs_cipher, codigo_verificacion, cuenta_id),
            )
            updated = cur.rowcount
            conn.commit()
        finally:
            cur.close()
        return updated > 0
    finally:
        conn.close()


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
    ok = payload_security.validate_payload(payload, bank_id=bank_id)
    if not ok:
        raise HTTPException(status_code=401, detail="Payload inválido o replay detected.")


@app.post("/banks/{bank_id}/cuentas/pendientes")
def cuentas_pendientes(bank_id: int, req: SecurePendingRequest):
    cfg = _get_bank_db_config(bank_id)
    # Si el banco no existe aún (no relacional), devolver [].
    if cfg is None:
        return {"bank_id": bank_id, "cuentas": []}

    payload = req.model_dump()
    _validate_secure_payload(payload, bank_id=bank_id)

    accounts = fetch_pending_accounts(bank_id, req.limit)
    return {"bank_id": bank_id, "cuentas": accounts}


@app.put("/banks/{bank_id}/cuentas/{cuenta_id}/saldo")
def update_saldo(bank_id: int, cuenta_id: int, req: SecureUpdateSaldoRequest):
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
    return {"status": "ok"}

