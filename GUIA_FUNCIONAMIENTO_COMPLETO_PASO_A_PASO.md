# GUIA_FUNCIONAMIENTO_COMPLETO_PASO_A_PASO

Esta guía te deja correr **todo el proyecto** de punta a punta:
- Bancos relacionales (1..5)
- Bancos no relacionales (6..14)
- API de bancos
- ASFI central (conversión, registro, auditoría)

---

## 0) Requisitos previos

- Docker Desktop abierto.
- Python 3 instalado.
- Estar en Windows PowerShell.

Ruta del proyecto:

`d:\DISCO (D)\UNIVALLE\7°mo Semestre\Sistemas Distribuidos\Practica2\ConversionMonetariaInterbancaria`

---

## 1) Instalar dependencias

```powershell
cd "d:\DISCO (D)\UNIVALLE\7°mo Semestre\Sistemas Distribuidos\Practica2\ConversionMonetariaInterbancaria"
python -m pip install -r requirements.txt
```

---

## 2) Levantar y poblar bancos relacionales (1..5)

```powershell
cd "d:\DISCO (D)\UNIVALLE\7°mo Semestre\Sistemas Distribuidos\Practica2\ConversionMonetariaInterbancaria\BackendRelacional"
docker compose up -d
python load_1pct_relacionales.py
```

Esto levanta PostgreSQL/MySQL/MariaDB y carga muestra 1% para bancos 1..5.

---

## 3) Levantar y poblar no relacionales (6..14)

```powershell
cd "d:\DISCO (D)\UNIVALLE\7°mo Semestre\Sistemas Distribuidos\Practica2\ConversionMonetariaInterbancaria"
docker compose up -d
python "app/db/seed(datos)/seed_non_relational.py"
```

Esto levanta MongoDB/Redis y siembra datos cifrados para bancos 6..14.

> Si banco 11 (RSA) no tiene llaves RSA reales válidas, puede omitirse en seed/ejecución y quedar operativo 13/14.

---

## 4) Levantar API de bancos (1..14)

En una terminal nueva:

```powershell
cd "d:\DISCO (D)\UNIVALLE\7°mo Semestre\Sistemas Distribuidos\Practica2\ConversionMonetariaInterbancaria"
python -m uvicorn app.banks_api.server:app --host 0.0.0.0 --port 9000
```

Probar health:

```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost:9000/health"
```

Debe responder con status ok.

---

## 5) Ejecutar ASFI central (1..14)

En otra terminal nueva (dejando API corriendo):

```powershell
cd "d:\DISCO (D)\UNIVALLE\7°mo Semestre\Sistemas Distribuidos\Practica2\ConversionMonetariaInterbancaria"
python -c "from app.asfi.run_asfi_14banks import run; run(limit_per_bank=200, max_workers=8, truncate_asfi=False, currency_rate='6.96')"
```

### Parámetros importantes

- `limit_per_bank`: cuántas cuentas procesar por banco (demo: 50, 100, 200).
- `max_workers`: paralelismo (más alto = más rápido, según máquina).
- `currency_rate`: tipo de cambio (ejemplo `6.96`, `6.97`, etc.).
- `truncate_asfi=True`: limpia ASFI antes de correr.

---

## 6) Verificar resultados

### 6.1 Conteo en ASFI central

```powershell
docker exec -it db_asfi_pg psql -U admin -d asfi_central -c "SELECT COUNT(*) FROM cuentas_asfi;"
```

### 6.2 Ver algunas conversiones

```powershell
docker exec -it db_asfi_pg psql -U admin -d asfi_central -c "SELECT banco_id, id_origen, saldo_usd_original, saldo_bs_convertido, codigo_verificacion, fecha_conversion FROM cuentas_asfi ORDER BY id DESC LIMIT 20;"
```

### 6.3 Revisar auditoría

Archivo:

`logs/auditoria.csv`

Revisar columnas: timestamp, tipo_cambio_aplicado, banco_id, cuenta_id, saldos, código, estado (OK/INC/ERR), detalle.

---

## 7) Ejecución en un solo comando (recomendado para demo)

Puedes usar el script automático:

```powershell
& "d:\DISCO (D)\UNIVALLE\7°mo Semestre\Sistemas Distribuidos\Practica2\ConversionMonetariaInterbancaria\run_demo_integrante4.ps1" -TipoCambio 6.96 -LimitPorBanco 200 -Workers 8 -ResetASFI
```

Si quieres otra tasa:

```powershell
& "d:\DISCO (D)\UNIVALLE\7°mo Semestre\Sistemas Distribuidos\Practica2\ConversionMonetariaInterbancaria\run_demo_integrante4.ps1" -TipoCambio 6.97 -LimitPorBanco 200 -Workers 8 -ResetASFI
```

---

## 8) Problemas frecuentes

### Puerto 9000 ocupado

Cierra proceso y vuelve a correr uvicorn.

### `Payload inválido o replay detected`

No reutilices el mismo body firmado; deja que ASFI/API generen nonce nuevo por request.

### Banco 11 RSA falla

Es esperado si no hay llaves reales RSA en `configs/keys.json`. Opera 13/14 y documenta esta limitación.

### No hay registros en ASFI

Revisa:
- API levantada en puerto 9000
- Seeds ejecutados
- `limit_per_bank` > 0

---

## 9) Qué mostrar en defensa (rápido)

1. `/health` de la API.
2. Ejecución runner ASFI 1..14 en paralelo.
3. `COUNT(*)` en `cuentas_asfi`.
4. Muestra de `auditoria.csv`.
5. Explicar que tipo de cambio es configurable y que ASFI registra todo centralmente.
