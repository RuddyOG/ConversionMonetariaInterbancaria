# ConversionMonetariaInterbancaria

Plataforma distribuida de conversión monetaria interbancaria (Banco ↔ ASFI).

## Qué ya está implementado

- API de bancos en `app/banks_api/server.py` con endpoints para bancos `1..14`.
- Runner ASFI para `1..5` en `app/asfi/run_asfi_5banks.py`.
- Runner ASFI extendido para `1..14` en `app/asfi/run_asfi_14banks.py`.
- Seguridad reutilizada del equipo (`keys.py`, `nonce.py`, `signatures.py`, `payload_security.py`, `verification_code.py`).
- Cifrado por `CryptoManager` para bancos clásicos y modernos.

## Documentación

- `GUIA_PRUEBA_PASO_A_PASO.md`
- `ARQUITECTURA.md`
- `ANALISIS_PROYECTO_PROFUNDO.md`
- `BackendRelacional/README.md`

## Requisitos

```bash
python -m pip install -r requirements.txt
```

Además:
- Docker Desktop activo
- Puerto `9000` libre para la API

## 1) Levantar bases relacionales (bancos 1..5 + ASFI)

Desde `BackendRelacional/`:

```bash
docker compose up -d
python load_1pct_relacionales.py
```

## 2) Levantar bases no relacionales (bancos 6..14)

Desde la raíz del proyecto:

```bash
docker compose up -d
python "app/db/seed(datos)/seed_non_relational.py"
```

> Nota: si banco 11 (RSA) no tiene llaves reales en `configs/keys.json`, sus cuentas se omiten y el sistema queda operativo en 13/14 bancos.

## 3) Levantar API de bancos

Desde la raíz del proyecto:

```bash
python -m uvicorn app.banks_api.server:app --host 0.0.0.0 --port 9000
```

Health check:

- `GET http://localhost:9000/health`

## 4) Ejecutar ASFI

### Opción A (demo original 1..5)

```bash
python -c "from app.asfi.run_asfi_5banks import run; run(limit_per_bank=200, max_workers=5, truncate_asfi=False, truncate_banks=False)"
```

### Opción B (integración completa 1..14)

```bash
python -c "from app.asfi.run_asfi_14banks import run; run(limit_per_bank=200, max_workers=8, truncate_asfi=False)"
```

## 5) Verificación

### Conteo en ASFI central

```bash
docker exec -it db_asfi_pg psql -U admin -d asfi_central -c "SELECT COUNT(*) FROM cuentas_asfi;"
```

### Auditoría

Archivo generado:

- `logs/auditoria.csv`

Campos clave:
- `timestamp`
- `tipo_cambio_aplicado`
- `banco_id`
- `cuenta_id`
- `saldo_usd_original`
- `saldo_bs_convertido`
- `codigo_verificacion`
- `estado` (`OK`/`INC`/`ERR`)

## Endpoints banco API

- `POST /banks/{bank_id}/cuentas/pendientes`
- `PUT /banks/{bank_id}/cuentas/{cuenta_id}/saldo`

Ambos endpoints validan `timestamp + nonce + hmac` con `PayloadSecurity`.
