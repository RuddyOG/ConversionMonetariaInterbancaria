from __future__ import annotations

import csv
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import httpx
import mysql.connector
import psycopg
import redis
from pymongo import MongoClient

from app.config.relational_connections_5banks import ASFI_CENTRAL, DbConfig, RELATIONAL_BANKS_1_TO_5
from app.crypto.manager import CryptoManager
from app.security.keys import KeyManager
from app.security.nonce import NonceManager
from app.security.payload_security import PayloadSecurity
from app.security.verification_code import generate_verification_code


@dataclass(frozen=True)
class RunConfig:
    bank_api_base_url: str
    limit_per_bank: Optional[int] = None
    truncate_asfi: bool = False
    currency_rate: str = "6.96"
    max_workers: int = 8


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

MONGO_URI = "mongodb://localhost:27017/"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_PASSWORD = "redis123"

mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True,
)

crypto = CryptoManager()
key_manager = KeyManager()
nonce_manager = NonceManager()
payload_security = PayloadSecurity(key_manager, nonce_manager)


def _ensure_asfi_bancos_1_to_14() -> None:
    conn = _connect_postgres(ASFI_CENTRAL)
    try:
        with conn.cursor() as cur:
            for bank_id in range(1, 15):
                cfg = key_manager.get_bank_config(bank_id)
                nombre = cfg.get("bank_name", f"Banco {bank_id}")
                algoritmo = cfg.get("algorithm", "unknown")
                cur.execute(
                    """
                    INSERT INTO bancos (banco_id, nombre, algoritmo_encriptacion)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (banco_id)
                    DO UPDATE SET
                        nombre = EXCLUDED.nombre,
                        algoritmo_encriptacion = EXCLUDED.algoritmo_encriptacion
                    """,
                    (bank_id, nombre, algoritmo),
                )
        conn.commit()
    finally:
        conn.close()


def _connect_postgres(cfg: DbConfig):
    return psycopg.connect(
        host=cfg.host,
        port=cfg.port,
        dbname=cfg.database,
        user=cfg.user,
        password=cfg.password,
    )


def _connect_mysql(cfg: DbConfig):
    return mysql.connector.connect(
        host=cfg.host,
        port=cfg.port,
        database=cfg.database,
        user=cfg.user,
        password=cfg.password,
    )


def _connect(cfg: DbConfig):
    if cfg.engine == "postgres":
        return _connect_postgres(cfg)
    return _connect_mysql(cfg)


def _has_relational_column(conn, cfg: DbConfig, table_name: str, column_name: str) -> bool:
    if cfg.engine == "postgres":
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
                LIMIT 1
                """,
                (table_name, column_name),
            )
            return cur.fetchone() is not None

    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = %s
              AND column_name = %s
            LIMIT 1
            """,
            (table_name, column_name),
        )
        return cur.fetchone() is not None
    finally:
        cur.close()


def _truncate_asfi_central() -> None:
    conn = _connect_postgres(ASFI_CENTRAL)
    try:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE cuentas_asfi RESTART IDENTITY;")
        conn.commit()
    finally:
        conn.close()


def _ensure_audit_log(log_path: str) -> None:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    if not os.path.exists(log_path):
        with open(log_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "timestamp",
                    "tipo_cambio_aplicado",
                    "banco_id",
                    "cuenta_id",
                    "saldo_usd_original",
                    "saldo_bs_convertido",
                    "codigo_verificacion",
                    "estado",
                    "detalle",
                ]
            )


def _append_audit_row(log_path: str, row: List[Any]) -> None:
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)


def _insert_into_asfi_central(
    banco_id: int,
    id_origen: str,
    saldo_usd_original: str,
    saldo_bs_convertido: str,
    codigo_verificacion: str,
    fecha_conversion: datetime,
) -> None:
    conn = _connect_postgres(ASFI_CENTRAL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cuentas_asfi
                    (banco_id, id_origen, saldo_usd_original, saldo_bs_convertido, fecha_conversion, codigo_verificacion)
                VALUES
                    (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (banco_id, id_origen)
                DO UPDATE SET
                    saldo_usd_original = EXCLUDED.saldo_usd_original,
                    saldo_bs_convertido = EXCLUDED.saldo_bs_convertido,
                    fecha_conversion = EXCLUDED.fecha_conversion,
                    codigo_verificacion = EXCLUDED.codigo_verificacion,
                    updated_at = NOW()
                """,
                (
                    banco_id,
                    int(id_origen),
                    saldo_usd_original,
                    saldo_bs_convertido,
                    fecha_conversion,
                    codigo_verificacion,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def _convert_usd_to_bs(saldo_usd: str, tasa: str) -> str:
    value = Decimal(str(saldo_usd)) * Decimal(str(tasa))
    return format(value.quantize(Decimal("0.0001")), ".4f")


def _fetch_bank_row(bank_id: int, cuenta_id: str) -> Optional[Dict[str, Any]]:
    if bank_id in RELATIONAL_BANKS_1_TO_5:
        cfg = RELATIONAL_BANKS_1_TO_5[bank_id]
        conn = _connect(cfg)
        try:
            has_cipher_schema = _has_relational_column(conn, cfg, "cuentas_banco", "saldo_bs_cipher")
            if cfg.engine == "postgres":
                with conn.cursor() as cur:
                    if has_cipher_schema:
                        cur.execute(
                            "SELECT id, saldo_bs_cipher, codigo_verificacion FROM cuentas_banco WHERE id = %s",
                            (int(cuenta_id),),
                        )
                    else:
                        cur.execute(
                            "SELECT id, saldo_bs AS saldo_bs_cipher, codigo_verificacion FROM cuentas_banco WHERE id = %s",
                            (int(cuenta_id),),
                        )
                    row = cur.fetchone()
            else:
                cur = conn.cursor()
                try:
                    if has_cipher_schema:
                        cur.execute(
                            "SELECT id, saldo_bs_cipher, codigo_verificacion FROM cuentas_banco WHERE id = %s",
                            (int(cuenta_id),),
                        )
                    else:
                        cur.execute(
                            "SELECT id, saldo_bs AS saldo_bs_cipher, codigo_verificacion FROM cuentas_banco WHERE id = %s",
                            (int(cuenta_id),),
                        )
                    row = cur.fetchone()
                finally:
                    cur.close()

            if not row:
                return None

            return {
                "id": str(row[0]),
                "saldo_bs_cipher": row[1],
                "codigo_verificacion": row[2],
            }
        finally:
            conn.close()

    if bank_id in NON_RELATIONAL_MONGO:
        cfg = NON_RELATIONAL_MONGO[bank_id]
        doc = mongo_client[cfg["db"]][cfg["collection"]].find_one({"id": str(cuenta_id)})
        if not doc:
            return None
        return {
            "id": str(doc.get("id", "")),
            "saldo_bs_cipher": doc.get("saldo_bs_cipher") or doc.get("saldo_bs") or "",
            "codigo_verificacion": doc.get("codigo_verificacion") or "",
        }

    if bank_id == 14:
        key = f"{REDIS_BANK_14_PREFIX}:cuenta:{cuenta_id}"
        data = redis_client.hgetall(key)
        if not data:
            return None
        return {
            "id": str(data.get("id", "")),
            "saldo_bs_cipher": data.get("saldo_bs_cipher") or data.get("saldo_bs") or "",
            "codigo_verificacion": data.get("codigo_verificacion") or "",
        }

    return None


def _build_pending_payload(cfg: RunConfig, bank_id: int) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    if cfg.limit_per_bank is not None:
        payload["limit"] = cfg.limit_per_bank
    return payload_security.secure_payload(payload, bank_id=bank_id)


def process_bank(bank_id: int, cfg: RunConfig, audit_log_path: str) -> Tuple[int, int, int]:
    fecha_now = datetime.now(timezone.utc)
    ok = 0
    inconsistencias = 0
    errores = 0

    with httpx.Client(timeout=60) as client:
        pending_url = f"{cfg.bank_api_base_url}/banks/{bank_id}/cuentas/pendientes"
        secure_req = _build_pending_payload(cfg, bank_id)

        pending_resp = client.post(pending_url, json=secure_req)
        pending_resp.raise_for_status()
        cuentas = pending_resp.json().get("cuentas", [])

        for cuenta in cuentas:
            cuenta_id = str(cuenta.get("id", "")).strip()
            saldo_usd_cipher = cuenta.get("saldo_usd_cipher", "")

            if not cuenta_id:
                errores += 1
                _append_audit_row(
                    audit_log_path,
                    [
                        fecha_now.isoformat(),
                        cfg.currency_rate,
                        bank_id,
                        "",
                        "",
                        "",
                        "",
                        "ERR",
                        "Cuenta sin id recibido desde API",
                    ],
                )
                continue

            try:
                saldo_usd_original = crypto.decrypt_field(bank_id, "saldo_usd", saldo_usd_cipher)
                saldo_bs_convertido = _convert_usd_to_bs(saldo_usd_original, cfg.currency_rate)
                codigo_verificacion = generate_verification_code()

                _insert_into_asfi_central(
                    banco_id=bank_id,
                    id_origen=cuenta_id,
                    saldo_usd_original=saldo_usd_original,
                    saldo_bs_convertido=saldo_bs_convertido,
                    codigo_verificacion=codigo_verificacion,
                    fecha_conversion=fecha_now,
                )

                update_url = f"{cfg.bank_api_base_url}/banks/{bank_id}/cuentas/{cuenta_id}/saldo"
                secure_update = payload_security.secure_payload(
                    {"saldo_bs": saldo_bs_convertido, "codigo_verificacion": codigo_verificacion},
                    bank_id=bank_id,
                )
                update_resp = client.put(update_url, json=secure_update)
                update_resp.raise_for_status()

                db_row = _fetch_bank_row(bank_id, cuenta_id)
                if not db_row:
                    inconsistencias += 1
                    _append_audit_row(
                        audit_log_path,
                        [
                            fecha_now.isoformat(),
                            cfg.currency_rate,
                            bank_id,
                            cuenta_id,
                            saldo_usd_original,
                            saldo_bs_convertido,
                            codigo_verificacion,
                            "INC",
                            "No se encontró cuenta actualizada en origen",
                        ],
                    )
                    continue

                if (db_row.get("codigo_verificacion") or "").strip() != codigo_verificacion:
                    inconsistencias += 1
                    _append_audit_row(
                        audit_log_path,
                        [
                            fecha_now.isoformat(),
                            cfg.currency_rate,
                            bank_id,
                            cuenta_id,
                            saldo_usd_original,
                            saldo_bs_convertido,
                            codigo_verificacion,
                            "INC",
                            "Código de verificación no coincide",
                        ],
                    )
                    continue

                saldo_bs_from_bank = crypto.decrypt_field(
                    bank_id,
                    "saldo_bs",
                    db_row.get("saldo_bs_cipher", ""),
                )

                if Decimal(str(saldo_bs_from_bank)) != Decimal(str(saldo_bs_convertido)):
                    inconsistencias += 1
                    _append_audit_row(
                        audit_log_path,
                        [
                            fecha_now.isoformat(),
                            cfg.currency_rate,
                            bank_id,
                            cuenta_id,
                            saldo_usd_original,
                            saldo_bs_convertido,
                            codigo_verificacion,
                            "INC",
                            "Saldo en origen no coincide",
                        ],
                    )
                    continue

                ok += 1
                _append_audit_row(
                    audit_log_path,
                    [
                        fecha_now.isoformat(),
                        cfg.currency_rate,
                        bank_id,
                        cuenta_id,
                        saldo_usd_original,
                        saldo_bs_convertido,
                        codigo_verificacion,
                        "OK",
                        "Consistente",
                    ],
                )

            except Exception as exc:
                errores += 1
                _append_audit_row(
                    audit_log_path,
                    [
                        fecha_now.isoformat(),
                        cfg.currency_rate,
                        bank_id,
                        cuenta_id,
                        "",
                        "",
                        "",
                        "ERR",
                        str(exc),
                    ],
                )

    return ok, inconsistencias, errores


def run(
    limit_per_bank: Optional[int] = None,
    max_workers: int = 8,
    truncate_asfi: bool = False,
    currency_rate: str = "6.96",
) -> None:
    cfg = RunConfig(
        bank_api_base_url=os.environ.get("BANK_API_BASE_URL", "http://localhost:9000"),
        limit_per_bank=limit_per_bank,
        truncate_asfi=truncate_asfi,
        currency_rate=currency_rate,
        max_workers=max_workers,
    )

    audit_log_path = os.environ.get("AUDIT_LOG_PATH", "logs/auditoria.csv")
    _ensure_audit_log(audit_log_path)

    if cfg.truncate_asfi:
        _truncate_asfi_central()

    _ensure_asfi_bancos_1_to_14()

    bank_ids = list(range(1, 15))
    results: Dict[int, Tuple[int, int, int]] = {}

    with ThreadPoolExecutor(max_workers=cfg.max_workers) as executor:
        future_map = {
            executor.submit(process_bank, bank_id, cfg, audit_log_path): bank_id
            for bank_id in bank_ids
        }
        for future, bank_id in future_map.items():
            results[bank_id] = future.result()

    print("Resumen corrida ASFI (bancos 1..14)")
    for bank_id in bank_ids:
        ok, inc, err = results.get(bank_id, (0, 0, 0))
        print(f"- Banco {bank_id}: procesadas={ok}, inconsistencias={inc}, errores={err}")


if __name__ == "__main__":
    run(limit_per_bank=None, truncate_asfi=True)