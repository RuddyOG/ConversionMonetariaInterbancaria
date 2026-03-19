# Arquitectura de comunicación Banco ↔ ASFI

## Decisión adoptada: **Opción A — ASFI como orquestador (pull)**

El flujo de datos entre los 14 bancos y la ASFI sigue un modelo **pull**: la ASFI es quien inicia y orquesta todo el proceso.

---

## Cómo viajan los datos

1. **ASFI consulta a cada banco**  
   ASFI llama a la API de cada entidad (una por banco, 14 servicios). Solicita las cuentas pendientes de conversión.

2. **Cada banco expone su API**  
   Los bancos no envían datos por iniciativa propia. Solo responden cuando ASFI hace una petición (por ejemplo `GET /cuentas` o similar).

3. **Banco → ASFI**  
   El banco devuelve los datos de las cuentas (cifrados según su algoritmo). ASFI recibe, descifra, convierte USD → Bs., registra en su base central y genera el código de verificación.

4. **ASFI → Banco**  
   ASFI envía al banco de origen el resultado: saldo convertido en Bs. y código de verificación (8 caracteres hex). El banco actualiza el saldo del cliente en su propia base y, si aplica, confirma o valida con ASFI.

5. **Resumen del flujo de datos**  
   `Banco → ASFI → Banco` (consulta de cuentas, luego envío del resultado de la conversión).

---

## Responsabilidades por lado

| Actor   | Rol |
|--------|-----|
| **Bancos** | Exponer API (servicio de transferencia de datos por entidad). Responder a GET de cuentas con datos cifrados. Recibir PUT/PATCH con saldo en Bs. y código de verificación y actualizar la cuenta. |
| **ASFI**   | Orquestar: llamar a los 14 bancos, recibir datos, descifrar, obtener tipo de cambio (BCB), calcular, registrar en BD central, generar código de verificación, enviar actualización a cada banco, registrar en log de auditoría y validar consistencia. |

---

## Ventajas de esta opción

- Un solo punto que inicia el proceso (ASFI), fácil de controlar y de ejecutar “una sola vez”.
- ASFI puede hacer el barrido en paralelo (consultas concurrentes a los 14 bancos).
- Los bancos solo exponen endpoints; no necesitan conocer la lógica de conversión ni a los otros bancos.
- Trazabilidad clara: ASFI tiene el registro de qué pidió y qué envió a cada banco.

---

## Documento de referencia

Decisión tomada para el proyecto de Conversión Monetaria Interbancaria – ASFI.  
Flujo detallado paso a paso: ver `PRESENTACION_AVANCES.md` (sección 1).
