import pandas as pd
import os
from pymongo import MongoClient
import redis
from datetime import datetime

# =========================
# 🔐 CONFIGURACIÓN
# =========================

# MongoDB Atlas
MONGO_URI = "mongodb+srv://danielEP_db_user:Vx3iNXwqRGtUb4RI@cluster0.lqq9mzh.mongodb.net/"

# Redis Cloud
redis_client = redis.Redis(
    host="redis-18018.c85.us-east-1-2.ec2.cloud.redislabs.com",
    port=18018,
    username="default",
    password="zPBvzJOmNtFQkeJlscg31cQV91VniicI",
    ssl=False,
    decode_responses=True
)

# =========================
# 📂 1. LEER CSV EXISTENTE
# =========================

print("📂 Leyendo dataset.csv...")
ruta = os.path.join(os.path.dirname(__file__), "dataset.csv")

df = pd.read_csv(ruta, dtype={
    "NroCuenta": str,
    "Identificacion": str
})

# Limpiar columnas
df.columns = df.columns.str.strip()

# Tomar 1% de la muestra
muestra = df.sample(frac=0.01, random_state=42)

print(f"Total registros originales: {len(df)}")
print(f"Registros a insertar (1%): {len(muestra)}")

# Verificar distribución por banco
print("\n📊 Distribución por banco en la muestra:")
print(muestra["IdBanco"].value_counts().sort_index())

# =========================
# ☁️ 2. CONEXIÓN MONGODB
# =========================

print("\n🔄 Conectando a MongoDB Atlas...")
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.admin.command('ping')
    print("✅ Conexión exitosa a MongoDB Atlas")
except Exception as e:
    print(f"❌ Error conectando a MongoDB: {e}")
    exit(1)

# =========================
# 🧹 3. LIMPIEZA DE BASES
# =========================

print("\n🧹 Limpiando datos anteriores...")

# Limpiar bases de MongoDB para bancos 6-13
for banco_id in range(6, 14):  # 6 al 13
    db_name = f"banco_{banco_id}_db"
    collection_name = f"cuentas_banco_{banco_id}"
    
    try:
        mongo_client[db_name][collection_name].delete_many({})
        print(f"  ✅ Limpiado {db_name}.{collection_name}")
    except Exception as e:
        print(f"  ⚠️ Error limpiando {db_name}.{collection_name}: {e}")

# Limpiar Redis
try:
    redis_client.ping()
    print("✅ Conexión a Redis verificada")
    
    claves_banco14 = list(redis_client.keys("banco14:*"))
    if claves_banco14:
        redis_client.delete(*claves_banco14)
    print(f"  ✅ Limpiadas {len(claves_banco14)} claves del banco 14 en Redis")
    
except Exception as e:
    print(f"❌ Error conectando a Redis: {e}")
    exit(1)

print("✅ Bases limpias")

# =========================
# 🍃 4. INSERTAR EN MONGODB (BANCOS 6-13)
# =========================

print("\n📦 Insertando en MongoDB (Bancos 6 al 13)...")

# Filtrar registros para bancos 6-13
bancos_mongo = range(6, 14)  # 6 al 13
df_mongo = muestra[muestra["IdBanco"].isin(bancos_mongo)]

fecha_actual = datetime.now().isoformat()

if len(df_mongo) > 0:
    print(f"Registros para MongoDB (bancos 6-13): {len(df_mongo)}")
    
    # Agrupar por banco para inserción
    for banco_id in bancos_mongo:
        df_banco = df_mongo[df_mongo["IdBanco"] == banco_id]
        
        if len(df_banco) > 0:
            db_name = f"banco_{banco_id}_db"
            collection_name = f"cuentas_banco_{banco_id}"
            collection = mongo_client[db_name][collection_name]
            
            documentos = []
            for _, row in df_banco.iterrows():
                doc = {
                    "ci": str(row["Identificacion"]),
                    "nombres": str(row["Nombres"]),
                    "apellidos": str(row["Apellidos"]),
                    "nro_cuenta": str(row["NroCuenta"]),
                    "saldo_bolivianos": float(row["Saldo"]),
                    "saldo_dolares": 0.0,  # 👈 NUEVO CAMPO con valor por defecto
                    
                    # Campos de auditoría
                    "created_at": fecha_actual,
                    "updated_at": fecha_actual,
                    "created_by": "system",
                    "updated_by": "system",
                    "is_active": True
                }
                documentos.append(doc)
            
            # Insertar documentos
            if documentos:
                collection.insert_many(documentos)
                
                # Crear índices
                collection.create_index("ci")
                collection.create_index("nro_cuenta")
                collection.create_index("is_active")
                collection.create_index("created_at")
                collection.create_index("saldo_dolares")  # Índice para búsquedas por saldo
                
                print(f"  ✅ Banco {banco_id}: {len(documentos)} registros insertados")
else:
    print("No hay registros para bancos 6-13 en la muestra")

# =========================
# ⚡ 5. INSERTAR EN REDIS (BANCO 14)
# =========================

print("\n⚡ Insertando en Redis (Banco 14)...")

# Filtrar registros para banco 14
df_redis = muestra[muestra["IdBanco"] == 14]

if len(df_redis) > 0:
    print(f"Registros para Redis (banco 14): {len(df_redis)}")
    
    for _, row in df_redis.iterrows():
        cuenta = str(row["NroCuenta"])
        
        # Guardar información de la cuenta con campos de auditoría
        redis_client.hset(f"banco14:cuenta:{cuenta}", mapping={
            "ci": str(row["Identificacion"]),
            "nombres": str(row["Nombres"]),
            "apellidos": str(row["Apellidos"]),
            "nro_cuenta": cuenta,
            "saldo_bolivianos": str(float(row["Saldo"])),
            "saldo_dolares": "0.0",  # 👈 NUEVO CAMPO con valor por defecto (como string en Redis)
            
            # Campos de auditoría
            "created_at": fecha_actual,
            "updated_at": fecha_actual,
            "created_by": "system",
            "updated_by": "system",
            "is_active": "1"  # "1" para True
        })
        
        # Índice por CI
        redis_client.set(f"banco14:ci:{str(row['Identificacion'])}", cuenta)
        
        # Agregar a lista de cuentas del banco 14
        redis_client.sadd("banco14:cuentas", cuenta)
        
        # Índice por estado activo
        redis_client.sadd("banco14:activas", cuenta)
        
        # Índice por saldo en dólares (para consultas rápidas)
        # Usamos un sorted set para poder ordenar por saldo
        redis_client.zadd("banco14:saldos_dolares", {cuenta: 0.0})
    
    print(f"  ✅ Banco 14: {len(df_redis)} registros insertados en Redis")
else:
    print("No hay registros para banco 14 en la muestra")

# =========================
# 🔍 6. VALIDACIÓN
# =========================

print("\n" + "="*50)
print("🔍 VALIDACIÓN FINAL")
print("="*50)

# Validar MongoDB (bancos 6-13)
print("\n📊 MONGODB:")
total_mongo = 0
for banco_id in range(6, 14):
    db_name = f"banco_{banco_id}_db"
    collection_name = f"cuentas_banco_{banco_id}"
    
    try:
        count = mongo_client[db_name][collection_name].count_documents({})
        activas = mongo_client[db_name][collection_name].count_documents({"is_active": True})
        
        if count > 0:
            print(f"  Banco {banco_id}: {count} registros ({activas} activas)")
            
            # Mostrar ejemplo del primer banco con datos
            if total_mongo == 0 and count > 0:
                ejemplo = mongo_client[db_name][collection_name].find_one()
                print(f"\n  📝 Ejemplo Banco {banco_id}:")
                print(f"      CI: {ejemplo.get('ci')}")
                print(f"      Nombres: {ejemplo.get('nombres')} {ejemplo.get('apellidos')}")
                print(f"      Cuenta: {ejemplo.get('nro_cuenta')}")
                print(f"      Saldo Bs: {ejemplo.get('saldo_bolivianos')}")
                print(f"      Saldo USD: {ejemplo.get('saldo_dolares')} (por defecto)")
                print(f"      is_active: {ejemplo.get('is_active')}")
                print(f"      created_at: {ejemplo.get('created_at')}")
        else:
            print(f"  Banco {banco_id}: 0 registros")
        
        total_mongo += count
    except Exception as e:
        print(f"  Banco {banco_id}: Error - {e}")

print(f"\n  TOTAL MONGODB: {total_mongo} registros")
print(f"  Todos con saldo_dolares = 0 (por defecto)")

# Validar Redis (banco 14)
print("\n⚡ REDIS (Banco 14):")

try:
    # Contar cuentas
    cuentas_redis = list(redis_client.smembers("banco14:cuentas"))
    activas_redis = list(redis_client.smembers("banco14:activas"))
    print(f"  Cuentas: {len(cuentas_redis)}")
    print(f"  Activas: {len(activas_redis)}")
    
    # Contar índices por CI
    ci_keys = list(redis_client.keys("banco14:ci:*"))
    print(f"  Índices por CI: {len(ci_keys)}")
    
    # Verificar saldos en dólares
    saldos_count = redis_client.zcard("banco14:saldos_dolares")
    print(f"  Registros con saldo_dolares: {saldos_count}")
    
    # Mostrar ejemplo si existe
    if len(cuentas_redis) > 0:
        ejemplo_cuenta = list(cuentas_redis)[0]
        ejemplo_data = redis_client.hgetall(f"banco14:cuenta:{ejemplo_cuenta}")
        print(f"\n  📝 Ejemplo Banco 14:")
        print(f"      Cuenta: {ejemplo_cuenta}")
        for campo, valor in ejemplo_data.items():
            print(f"      {campo}: {valor}")
        
        # Mostrar saldo en dólares del ejemplo
        saldo_usd = redis_client.zscore("banco14:saldos_dolares", ejemplo_cuenta)
        print(f"      saldo_dolares (sorted set): {saldo_usd}")
    
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "="*50)
print("🚀 PROCESO COMPLETADO CON ÉXITO")
print("="*50)