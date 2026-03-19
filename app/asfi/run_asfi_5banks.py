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

from app.asfi.hex_crypto_compat_load import convert_usd_to_bs_6_96, decrypt_cipher_to_balance
from app.config.relational_connections_5banks import RELATIONAL_BANKS_1_TO_5, ASFI_CENTRAL, algorithm_for_bank_1_to_5, DbConfig
from app.security.keys import KeyManager
from app.security.nonce import NonceManager
from app.security.payload_security import PayloadSecurity
from app.security.verification_code import generate_verification_code


@dataclass(frozen=True)
class RunConfig:
    bank_api_base_url: str
    limit_per_bank: int
    truncate_asfi: bool = False
    truncate_banks: bool = False
    currency_rate: str = "6.96"
    max_workers: int = 5


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


def _truncate_bank_tables():
    # Limpia solo bancos 1..5
    for bank_id, cfg in RELATIONAL_BANKS_1_TO_5.items():
        conn = _connect(cfg)
        try:
            cur = conn.cursor()
            try:
                if cfg.engine == "postgres":
                    cur.execute("TRUNCATE TABLE cuentas_banco RESTART IDENTITY;")
                else:
                    cur.execute("TRUNCATE TABLE cuentas_banco;")
                conn.commit()
            finally:
                cur.close()
        finally:
            conn.close()


def _truncate_asfi_central():
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
            w = csv.writer(f)
            w.writerow(["timestamp", "tipo_cambio_aplicado", "banco_id", "cuenta_id", "saldo_usd_original", "saldo_bs_convertido", "codigo_verificacion"])


def _append_audit_row(log_path: str, row: List[Any]) -> None:
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(row)


def _db_fetch_account_by_id(bank_id: int, cuenta_id: int) -> Optional[Dict[str, Any]]:
    cfg = RELATIONAL_BANKS_1_TO_5.get(bank_id)
    if cfg is None:
        return None
    conn = _connect(cfg)
    try:
        if cfg.engine == "postgres":
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, saldo_bs_cipher, codigo_verificacion
                    FROM cuentas_banco
                    WHERE id = %s
                    """,
                    (cuenta_id,),
                )
                r = cur.fetchone()
                if not r:
                    return None
                return {"id": r[0], "saldo_bs_cipher": r[1], "codigo_verificacion": r[2]}
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT id, saldo_bs_cipher, codigo_verificacion
                FROM cuentas_banco
                WHERE id = %s
                """,
                (cuenta_id,),
            )
            r = cur.fetchone()
            if not r:
                return None
            return {"id": r[0], "saldo_bs_cipher": r[1], "codigo_verificacion": r[2]}
        finally:
            cur.close()
    finally:
        conn.close()


def _insert_into_asfi_central(
    banco_id: int,
    id_origen: int,
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
                """,
                (banco_id, id_origen, saldo_usd_original, saldo_bs_convertido, fecha_conversion, codigo_verificacion),
            )
        conn.commit()
    finally:
        conn.close()


def process_bank(bank_id: int, cfg: RunConfig, audit_log_path: str) -> Tuple[int, int]:
    """
    Retorna: (procesadas_ok, inconsistencias)
    """
    key_manager = KeyManager()
    nonce_manager = NonceManager()
    payload_security = PayloadSecurity(key_manager, nonce_manager)

    log_tipo_cambio = cfg.currency_rate
    fecha_now = datetime.now(timezone.utc)

    with httpx.Client(timeout=60) as client:
        # 1) Solicitar cuentas pendientes
        pending_url = f"{cfg.bank_api_base_url}/banks/{bank_id}/cuentas/pendientes"
        secure_req = payload_security.secure_payload({"limit": cfg.limit_per_bank}, bank_id=bank_id)
        pending_resp = client.post(pending_url, json=secure_req)
        pending_resp.raise_for_status()
        pending = pending_resp.json()
        cuentas: List[Dict[str, Any]] = pending.get("cuentas", [])

        ok = 0
        inconsistencias = 0

        for cuenta in cuentas:
            cuenta_id = int(cuenta["id"])
            saldo_usd_cipher = cuenta["saldo_usd_cipher"]

            # 2) Descifrar saldo USD (compat con load_1pct_relacionales.py)
            saldo_usd_original = decrypt_cipher_to_balance(bank_id, saldo_usd_cipher)

            # 3) Convertir a Bs (fijo 6.96 según consigna del inge)
            # Nota: usamos convert_usd_to_bs_6_96 del módulo de compatibilidad.
            saldo_bs_convertido = convert_usd_to_bs_6_96(saldo_usd_original)

            # 4) Generar código de verificación
            codigo_verificacion = generate_verification_code()

            # 5) Registrar en ASFI central (BD)
            _insert_into_asfi_central(
                banco_id=bank_id,
                id_origen=cuenta_id,
                saldo_usd_original=saldo_usd_original,
                saldo_bs_convertido=saldo_bs_convertido,
                codigo_verificacion=codigo_verificacion,
                fecha_conversion=fecha_now,
            )

            # 6) Enviar actualización al banco (PUT)
            update_url = f"{cfg.bank_api_base_url}/banks/{bank_id}/cuentas/{cuenta_id}/saldo"
            secure_update = payload_security.secure_payload(
                {"saldo_bs": saldo_bs_convertido, "codigo_verificacion": codigo_verificacion},
                bank_id=bank_id,
            )
            up_resp = client.put(update_url, json=secure_update)
            up_resp.raise_for_status()

            # 7) Validación mínima: leer de BD del banco y comparar saldo/código
            db_row = _db_fetch_account_by_id(bank_id, cuenta_id)
            if not db_row:
                inconsistencias += 1
                continue

            if (db_row["codigo_verificacion"] or "").strip() != codigo_verificacion:
                inconsistencias += 1
                continue

            saldo_bs_plain_from_bank = decrypt_cipher_to_balance(bank_id, db_row["saldo_bs_cipher"])
            if Decimal(saldo_bs_plain_from_bank) != Decimal(saldo_bs_convertido):
                inconsistencias += 1
                continue

            ok += 1

            _append_audit_row(
                audit_log_path,
                [
                    fecha_now.isoformat(),
                    log_tipo_cambio,
                    bank_id,
                    cuenta_id,
                    saldo_usd_original,
                    saldo_bs_convertido,
                    codigo_verificacion,
                ],
            )

    return ok, inconsistencias


def run(limit_per_bank: int = 50, max_workers: int = 5, truncate_asfi: bool = False, truncate_banks: bool = False) -> None:
    bank_api_base_url = os.environ.get("BANK_API_BASE_URL", "http://localhost:9000")
    cfg = RunConfig(
        bank_api_base_url=bank_api_base_url,
        limit_per_bank=limit_per_bank,
        truncate_asfi=truncate_asfi,
        truncate_banks=truncate_banks,
        max_workers=max_workers,
    )

    audit_log_path = os.environ.get("AUDIT_LOG_PATH", "logs/auditoria.csv")
    _ensure_audit_log(audit_log_path)

    if cfg.truncate_banks:
        _truncate_bank_tables()
    if cfg.truncate_asfi:
        _truncate_asfi_central()

    bank_ids = [1, 2, 3, 4, 5]

    results: Dict[int, Tuple[int, int]] = {}
    with ThreadPoolExecutor(max_workers=cfg.max_workers) as ex:
        futs = {ex.submit(process_bank, bank_id, cfg, audit_log_path): bank_id for bank_id in bank_ids}
        for fut in futs:
            bank_id = futs[fut]
            ok, inc = fut.result()
            results[bank_id] = (ok, inc)

    print("Resumen corrida ASFI (bancos 1..5)")
    for bank_id in bank_ids:
        ok, inc = results.get(bank_id, (0, 0))
        print(f"- Banco {bank_id}: procesadas={ok}, inconsistencias={inc}")


if __name__ == "__main__":
    run()

