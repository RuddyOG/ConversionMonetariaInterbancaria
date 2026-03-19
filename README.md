# 📊 Proyecto de Bases de Datos Relacionales - ASFI

Guía completa para levantar y cargar datos en 6 bases de datos relacionales (5 bancos + 1 central ASFI).

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- ✅ **Docker Desktop** (iniciado y ejecutándose)
- ✅ **Python 3.8+**
- ✅ **pip** (administrador de paquetes de Python)
- ✅ **Visual Studio Code** (opcional pero recomendado)

### Verificación en Windows
- En Windows, verifica que Docker esté usando **Linux containers** (no Windows containers)
- El dataset CSV (`01 - Practica 2 Dataset.csv`) debe estar en la carpeta raíz del proyecto

---

## 📁 Estructura del Proyecto

```
practica_asfi/
├── docker-compose.yml
├── 01 - Practica 2 Dataset.csv
├── load_1pct_bancos_only.py
├── README.md
├── asfi_central/
│   └── init.sql
├── banco_union/
│   └── init.sql
├── banco_mercantil/
│   └── init.sql
├── banco_bnb/
│   └── init.sql
├── banco_bcp/
│   └── init.sql
└── banco_bisa/
    └── init.sql
```

---

## 🗄️ Motores de Bases de Datos

| Banco | Motor | Puerto |
|-------|-------|--------|
| 🏦 Banco Unión | PostgreSQL | 5433 |
| 💼 Banco Mercantil | MySQL | 3307 |
| 🏛️ Banco BNB | MariaDB | 3308 |
| 🏢 Banco BCP | PostgreSQL | 5434 |
| 🔷 Banco BISA | MySQL | 3309 |
| 📍 ASFI Central | PostgreSQL | 5435 |

---

## 🚀 Guía Paso a Paso

### **PASO 1: Abrir Docker Desktop**

1. Abre la aplicación **Docker Desktop**
2. Espera a que aparezca el ícono en la bandeja del sistema
3. Verifica que esté ejecutándose con: `docker version`

---

### **PASO 2: Levantar las Bases de Datos**

Abre una terminal (PowerShell, CMD o Git Bash) en la carpeta del proyecto y ejecuta:

```bash
docker compose up -d
```

Este comando crea y levanta todos los contenedores automáticamente.

### Verificar que todo está corriendo:

```bash
docker compose ps
```

Deberías ver 6 contenedores en estado **Up**:
- ✅ db_union_pg
- ✅ db_mercantil_mysql
- ✅ db_bnb_mariadb
- ✅ db_bcp_pg
- ✅ db_bisa_mysql
- ✅ db_asfi_pg

---

### **PASO 3: Instalar Dependencias de Python**

En la misma terminal, ejecuta:

```bash
pip install pandas "psycopg[binary]" mysql-connector-python
```

Esto instala las librerías necesarias para:
- 📖 **pandas**: leer y procesar el archivo CSV
- 🐘 **psycopg**: conectarse a PostgreSQL
- 🐬 **mysql-connector-python**: conectarse a MySQL y MariaDB

---

### **PASO 4: Ejecutar el Script de Carga de Datos**

```bash
python .\load_1pct_bancos_only.py
```

### ¿Qué hace este script?

1. Lee el archivo CSV (`01 - Practica 2 Dataset.csv`)
2. Toma una muestra del **1%** (1,238 registros de 123,791 totales)
3. Filtra los datos de los 5 bancos relacionales
4. Cifra los campos sensibles
5. Inserta los datos en cada base de datos

**⏱️ Tiempo estimado**: 1-3 minutos

---

### **PASO 5: Verificar que los Datos se Insertaron Correctamente**

Elige tu base de datos y ejecuta los comandos correspondientes:

#### 🏦 Banco Unión (PostgreSQL - Puerto 5433)

```bash
docker exec -it db_union_pg psql -U admin -d banco_union
```

Dentro de PostgreSQL ejecuta:
```sql
SELECT COUNT(*) FROM cuentas_banco;
SELECT * FROM cuentas_banco LIMIT 5;
\q
```

---

#### 🏢 Banco BCP (PostgreSQL - Puerto 5434)

```bash
docker exec -it db_bcp_pg psql -U admin -d banco_bcp
```

Dentro de PostgreSQL ejecuta:
```sql
SELECT COUNT(*) FROM cuentas_banco;
SELECT * FROM cuentas_banco LIMIT 5;
\q
```

---

#### 💼 Banco Mercantil (MySQL - Puerto 3307)

```bash
docker exec -it db_mercantil_mysql mysql -u admin -pmercantil123 banco_mercantil
```

Dentro de MySQL ejecuta:
```sql
SELECT COUNT(*) FROM cuentas_banco;
SELECT * FROM cuentas_banco LIMIT 5;
exit
```

---

#### 🔷 Banco BISA (MySQL - Puerto 3309)

```bash
docker exec -it db_bisa_mysql mysql -u admin -pbisa123 banco_bisa
```

Dentro de MySQL ejecuta:
```sql
SELECT COUNT(*) FROM cuentas_banco;
SELECT * FROM cuentas_banco LIMIT 5;
exit
```

---

#### 🏛️ Banco BNB (MariaDB - Puerto 3308)

```bash
docker exec -it db_bnb_mariadb mariadb -u admin -pbnb123 banco_bnb
```

Dentro de MariaDB ejecuta:
```sql
SELECT COUNT(*) FROM cuentas_banco;
SELECT * FROM cuentas_banco LIMIT 5;
exit
```

---

#### 📍 ASFI Central (PostgreSQL - Puerto 5435)

```bash
docker exec -it db_asfi_pg psql -U admin -d asfi_central
```

Dentro de PostgreSQL ejecuta:
```sql
SELECT * FROM bancos;
SELECT COUNT(*) FROM cuentas_asfi;
\q
```

---

## 🔌 Conexión desde Cliente Visual

Si prefieres usar una herramienta gráfica (DBeaver, TablePlus, pgAdmin, etc.):

| Campo | Banco Unión | Banco BCP | Banco Mercantil | Banco BISA | Banco BNB | ASFI Central |
|-------|------------|----------|-----------------|-----------|-----------|--------------|
| **Motor** | PostgreSQL | PostgreSQL | MySQL | MySQL | MariaDB | PostgreSQL |
| **Host** | localhost | localhost | localhost | localhost | localhost | localhost |
| **Puerto** | 5433 | 5434 | 3307 | 3309 | 3308 | 5435 |
| **Usuario** | admin | admin | admin | admin | admin | admin |
| **Contraseña** | union123 | bcp123 | mercantil123 | bisa123 | bnb123 | asfi123 |
| **Base de Datos** | banco_union | banco_bcp | banco_mercantil | banco_bisa | banco_bnb | asfi_central |

---

## 🛠️ Solución de Problemas

### ❌ Docker no responde

**Problema**: Error al ejecutar comandos de Docker

**Solución**:
1. Abre Docker Desktop manualmente
2. Verifica que esté corriendo con: `docker version`

---

### ❌ Los cambios en init.sql no aparecen

**Problema**: Modificaste un `init.sql` pero la base no refleja los cambios

**Solución**: Recrear los contenedores y volúmenes
```bash
docker compose down -v
docker compose up -d
python .\load_1pct_bancos_only.py
```

---

### ❌ No conecta desde un cliente visual

**Problema**: La conexión falla aunque el contenedor está encendido

**Verificación**:
- ✅ ¿Usas el motor correcto? (PostgreSQL, MySQL o MariaDB)
- ✅ ¿El puerto es el correcto?
- ✅ ¿Las credenciales son correctas?

Si seleccionas el motor incorrecto, la conexión fallará aunque el contenedor esté corriendo.

---

## ⚡ Resumen de Ejecución Rápida

```bash
# 1. Abrir Docker Desktop (manual)

# 2. Levantar bases de datos
docker compose up -d

# 3. Instalar dependencias
pip install pandas "psycopg[binary]" mysql-connector-python

# 4. Cargar datos
python .\load_1pct_bancos_only.py

# 5. Verificar datos (elegir una base)
docker exec -it db_union_pg psql -U admin -d banco_union
SELECT COUNT(*) FROM cuentas_banco;
\q
```

---

## 📊 Información del Dataset

- **Total de registros**: 123,791
- **Muestra cargada (1%)**: 1,238 registros
- **Campos cifrados**: Información sensible de cuentas
- **Bancos cargados**: 5 (Unión, Mercantil, BNB, BCP, BISA)

---

## 📝 Notas Importantes

⚠️ **Para Windows**: Verifica que Docker use "Linux containers"

⚠️ **Credenciales**: Las contraseñas están configuradas en `docker-compose.yml`, cámbialas en producción

⚠️ **Dataset**: Asegúrate de que `01 - Practica 2 Dataset.csv` está en la carpeta raíz

---

## 🆘 ¿Necesitas Ayuda?

Si algoritno no funciona:

1. Verifica que Docker Desktop esté corriendo
2. Ejecuta `docker compose ps` para ver el estado de los contenedores
3. Revisa los logs con `docker compose logs`
4. Recrea los contenedores con `docker compose down -v && docker compose up -d`

¡Éxito! 🎉
