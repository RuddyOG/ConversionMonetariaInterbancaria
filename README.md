# ConversionMonetariaInterbancaria

Plataforma distribuida de conversión monetaria interbancaria – ASFI

Este README explica cómo ejecutar la demo actual usando:
- Backend relacional en Docker (`BackendRelacional/`)
- API de bancos (Integrante 4) en FastAPI
- Runner ASFI (Integrante 4) que orquesta GET/PUT, descifra, convierte (tasa 6.96) y registra en ASFI central

## Documentación

- Flujo/arquitectura: `ARQUITECTURA.md`, `ANALISIS_PROYECTO.md`, `PRESENTACION_AVANCES.md`
- Backend relacional (Docker): `BackendRelacional/README.md`
- Estado del repo: `ANALISIS_PROYECTO_ACTUAL.md`, `ANALISIS_BACKEND_RELACIONAL.md`

## Requisitos

1. Docker Desktop funcionando (Linux containers).
2. Python 3.x.
3. Instalar dependencias del proyecto:

```bash
python -m pip install -r requirements.txt
```

## Puertos utilizados (demo)

- BackendRelacional (bases relacionales + ASFI central): definidos por el `docker-compose.yml` dentro de `BackendRelacional/`
- Bank API (Integrante 4): `http://localhost:9000`
- ASFI runner: corre como script (no expone endpoints por sí mismo)

## Paso 1: Levantar BackendRelacional con Docker

1. Abre una terminal en:

`BackendRelacional/`

2. Levanta contenedores:

```bash
docker compose up -d
```

## Paso 2: Cargar datos de prueba (1%)

1. Desde la carpeta `BackendRelacional/`, ejecuta el script de carga:

```bash
python load_1pct_relacionales.py
```

Este script:
- Lee `01 - Practica 2 Dataset.csv`
- Toma una muestra (~1%)
- Inserta filas cifradas en las 5 bases relacionales (bancos 1..5)

## Paso 3: Levantar la API de los bancos (bancos 1..5 por ahora)

Desde la raíz del proyecto `ConversionMonetariaInterbancaria/`, ejecuta:

```bash
python -m uvicorn app.banks_api.server:app --host 0.0.0.0 --port 9000
```

Verifica que responde:

```text
GET http://localhost:9000/health
```

Debe retornar `{ "status": "ok" }`.

### Endpoints principales (lo usa el runner ASFI)

- `POST /banks/{bank_id}/cuentas/pendientes` (devuelve cuentas con campos cifrados)
- `PUT /banks/{bank_id}/cuentas/{cuenta_id}/saldo` (actualiza `saldo_bs_cipher` y `codigo_verificacion`)

## Paso 4: Ejecutar el runner ASFI (conversión y registro central)

Desde la raíz del proyecto, ejecuta:

```bash
python -c "from app.asfi.run_asfi_5banks import run; run(limit_per_bank=200, max_workers=5, truncate_asfi=False, truncate_banks=False)"
```

Sugerencia para demo rápida:
- `limit_per_bank=1` si solo quieres ver que todo funciona
- `limit_per_bank=50` o `200` si quieres mostrar resultados sin tardar demasiado

### Qué hace este runner

Para cada banco 1..5:

1. Llama a la API del banco: GET (vía POST) cuentas pendientes
2. Descifra los campos sensibles usando la compatibilidad del cifrado del seed relacional
3. Convierte USD -> Bs. con tasa fija `6.96`
4. Calcula y registra `saldo_bs_convertido` con 4 decimales
5. Genera `codigo_verificacion` (8 caracteres hex)
6. Inserta en la BD ASFI central (`asfi_central.cuentas_asfi`)
7. Envía PUT al banco con `saldo_bs` + `codigo_verificacion`
8. Valida consistencia (comparando código y saldo)
9. Escribe el log de auditoría

## Paso 5: Verificar resultados

### 1) Ver cuántas conversiones se registraron en ASFI

Ejecuta en Docker:

```bash
docker exec -it db_asfi_pg psql -U admin -d asfi_central -c "SELECT COUNT(*) FROM cuentas_asfi;"
```

### 2) Revisar el log de auditoría (archivo)

El runner guarda:

`logs/auditoria.csv`

Columnas mínimas:
- timestamp
- tipo_cambio_aplicado
- banco_id
- cuenta_id
- saldo_usd_original
- saldo_bs_convertido
- codigo_verificacion

## Estado actual (importante)

- Esta demo está funcional end-to-end para **bancos relacionales 1..5** (los que ya existen en `BackendRelacional/`).
- Las APIs están preparadas para el modelo de 14 bancos, pero la ejecución del runner hoy solo procesa 1..5.
- Cuando tus compañeros te pasen las BDs no relacionales (Mongo/Redis) se extiende el adapter para bancos 6..14 y el runner procesará también esos bancos.

## Correr “limpio” (paso opcional)

Si quieres reiniciar el estado antes de una corrida:
- Puedes habilitar truncado (opciones `truncate_asfi=True`, `truncate_banks=True`) en el runner.
