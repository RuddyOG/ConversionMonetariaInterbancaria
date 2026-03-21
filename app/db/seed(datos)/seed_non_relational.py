import pandas as pd
import os
from pymongo import MongoClient
import redis
from datetime import datetime
import base64
import hashlib
import secrets
from Crypto.Cipher import DES, DES3, Blowfish, AES, ChaCha20
from Crypto.Util.Padding import pad, unpad

# =========================
# 📋 CONFIGURACIÓN DE ENCRIPTACIÓN POR BANCO
# =========================

def generar_claves():
    claves = {}
    
    # DES (56 bits) - Banco 6
    claves['des'] = os.urandom(8)
    
    # 3DES (168 bits) - Banco 7
    claves['3des'] = os.urandom(24)
    
    # Blowfish (16 bytes) - Banco 8
    claves['blowfish'] = os.urandom(16)
    
    # Twofish (32 bytes usando AES) - Banco 9
    claves['twofish'] = os.urandom(32)
    
    # AES (256 bits) - Bancos 10, 11, 12, 13
    claves['aes'] = os.urandom(32)
    
    # ChaCha20 (32 bytes) - Banco 14
    claves['chacha20'] = os.urandom(32)
    
    return claves

# Generar claves globales
print("🔑 Generando claves de encriptación...")
CLAVES = generar_claves()
print("✅ Claves generadas correctamente")

# =========================
# 📋 MAPEO DE BANCOS CON SUS ALGORITMOS
# =========================
bancos = {
    6: {
        "nombre_db": "banco_ganadero_db",
        "nombre_comercial": "Banco Ganadero S.A.",
        "algoritmo": "DES",
        "clave": CLAVES['des']
    },
    7: {
        "nombre_db": "banco_economico_db",
        "nombre_comercial": "Banco Económico S.A.",
        "algoritmo": "3DES",
        "clave": CLAVES['3des']
    },
    8: {
        "nombre_db": "banco_prodem_db",
        "nombre_comercial": "Banco Prodem S.A.",
        "algoritmo": "Blowfish",
        "clave": CLAVES['blowfish']
    },
    9: {
        "nombre_db": "banco_solidario_db",
        "nombre_comercial": "Banco Solidario S.A.",
        "algoritmo": "Twofish",
        "clave": CLAVES['twofish']
    },
    10: {
        "nombre_db": "banco_fortaleza_db",
        "nombre_comercial": "Banco Fortaleza S.A.",
        "algoritmo": "AES",
        "clave": CLAVES['aes']
    },
    11: {
        "nombre_db": "banco_fie_db",
        "nombre_comercial": "Banco FIE S.A.",
        "algoritmo": "AES",
        "clave": CLAVES['aes']
    },
    12: {
        "nombre_db": "banco_comunidad_db",
        "nombre_comercial": "Banco PYME de la Comunidad S.A.",
        "algoritmo": "AES",
        "clave": CLAVES['aes']
    },
    13: {
        "nombre_db": "banco_desarrollo_productivo_db",
        "nombre_comercial": "Banco de Desarrollo Productivo S.A.M.",
        "algoritmo": "AES",
        "clave": CLAVES['aes']
    },
    14: {
        "nombre_db": "banco_nacion_argentina_db",
        "nombre_comercial": "Banco de la Nación Argentina",
        "algoritmo": "ChaCha20",
        "clave": CLAVES['chacha20']
    }
}

# =========================
# 🔐 FUNCIONES DE ENCRIPTACIÓN
# =========================

def generar_codigo_verificacion(ci, numero_cuenta):
    """Genera un código de verificación único de 20 caracteres"""
    data = f"{ci}_{numero_cuenta}_{datetime.now().timestamp()}"
    return hashlib.sha256(data.encode()).hexdigest()[:20]

def generar_id_unico():
    """Genera un ID único similar al ObjectId de MongoDB"""
    timestamp = int(datetime.now().timestamp() * 1000)
    random = secrets.token_hex(8)
    contador = secrets.randbits(24)
    return f"{timestamp:x}{random}{contador:x}"[:24]

def encriptar_des(valor, clave):
    """Encriptación DES - Banco 6"""
    cipher = DES.new(clave[:8], DES.MODE_CBC)
    texto = str(valor) if isinstance(valor, (int, float)) else valor
    texto_bytes = texto.encode()
    padded = pad(texto_bytes, DES.block_size)
    encriptado = cipher.iv + cipher.encrypt(padded)
    return base64.b64encode(encriptado).decode()

def encriptar_3des(valor, clave):
    """Encriptación 3DES - Banco 7"""
    cipher = DES3.new(clave[:24], DES3.MODE_CBC)
    texto = str(valor) if isinstance(valor, (int, float)) else valor
    texto_bytes = texto.encode()
    padded = pad(texto_bytes, DES3.block_size)
    encriptado = cipher.iv + cipher.encrypt(padded)
    return base64.b64encode(encriptado).decode()

def encriptar_blowfish(valor, clave):
    """Encriptación Blowfish - Banco 8"""
    cipher = Blowfish.new(clave[:16], Blowfish.MODE_CBC)
    texto = str(valor) if isinstance(valor, (int, float)) else valor
    texto_bytes = texto.encode()
    padded = pad(texto_bytes, Blowfish.block_size)
    encriptado = cipher.iv + cipher.encrypt(padded)
    return base64.b64encode(encriptado).decode()

def encriptar_twofish(valor, clave):
    """Encriptación Twofish (usando AES) - Banco 9"""
    texto = str(valor) if isinstance(valor, (int, float)) else valor
    texto_bytes = texto.encode()
    cipher = AES.new(clave[:32], AES.MODE_CBC)
    padded = pad(texto_bytes, AES.block_size)
    encriptado = cipher.iv + cipher.encrypt(padded)
    return base64.b64encode(encriptado).decode()

def encriptar_aes(valor, clave):
    """Encriptación AES-256 - Bancos 10, 11, 12, 13"""
    texto = str(valor) if isinstance(valor, (int, float)) else valor
    texto_bytes = texto.encode()
    cipher = AES.new(clave[:32], AES.MODE_CBC)
    padded = pad(texto_bytes, AES.block_size)
    encriptado = cipher.iv + cipher.encrypt(padded)
    return base64.b64encode(encriptado).decode()

def encriptar_chacha20(valor, clave):
    """Encriptación ChaCha20 - Banco 14"""
    nonce = os.urandom(8)
    cipher = ChaCha20.new(key=clave[:32], nonce=nonce)
    texto = str(valor) if isinstance(valor, (int, float)) else valor
    texto_bytes = texto.encode()
    encriptado = nonce + cipher.encrypt(texto_bytes)
    return base64.b64encode(encriptado).decode()

def encriptar_por_banco(banco_id, valor):
    """Encripta un valor según el algoritmo del banco"""
    if banco_id not in bancos:
        return valor
    
    banco = bancos[banco_id]
    algoritmo = banco["algoritmo"]
    
    try:
        if algoritmo == "DES":
            return encriptar_des(valor, banco["clave"])
        elif algoritmo == "3DES":
            return encriptar_3des(valor, banco["clave"])
        elif algoritmo == "Blowfish":
            return encriptar_blowfish(valor, banco["clave"])
        elif algoritmo == "Twofish":
            return encriptar_twofish(valor, banco["clave"])
        elif algoritmo == "AES":
            return encriptar_aes(valor, banco["clave"])
        elif algoritmo == "ChaCha20":
            return encriptar_chacha20(valor, banco["clave"])
        else:
            return valor
    except Exception as e:
        print(f"  ⚠️ Error encriptando con {algoritmo}: {e}")
        return valor

# =========================
# 🔐 CONFIGURACIÓN PARA DOCKER LOCAL
# =========================

MONGO_URI = "mongodb://localhost:27017/"
redis_client = redis.Redis(host="localhost", port=6379, password="redis123", decode_responses=True)

# =========================
# 📂 LEER CSV
# =========================

print("📂 Leyendo dataset.csv...")
ruta = os.path.join(os.path.dirname(__file__), "dataset.csv")

df = pd.read_csv(ruta, dtype={"NroCuenta": str, "Identificacion": str})
df.columns = df.columns.str.strip()
muestra = df.sample(frac=0.01, random_state=42)

print(f"Total registros: {len(df)}")
print(f"Muestra 1%: {len(muestra)}")

print("\n📊 Distribución por banco:")
print(muestra["IdBanco"].value_counts().sort_index())

# =========================
# CONEXIÓN MONGODB
# =========================

print("\n🔄 Conectando a MongoDB...")
mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
mongo_client.admin.command('ping')
print("✅ Conexión exitosa")

# =========================
# 🧹 LIMPIEZA DE BASES
# =========================

print("\n🧹 Limpiando datos anteriores...")

for banco_id in range(6, 14):
    if banco_id in bancos:
        db_name = bancos[banco_id]["nombre_db"]
        if db_name in mongo_client.list_database_names():
            mongo_client.drop_database(db_name)
            print(f"  ✅ Eliminada {db_name}")

redis_client.flushdb()
print("  ✅ Redis limpiado")

# =========================
# 📦 INSERTAR EN MONGODB
# =========================

print("\n📦 Insertando en MongoDB con encriptación...")

fecha_actual = datetime.now().isoformat()
total_mongo = 0

for banco_id in range(6, 14):
    if banco_id in bancos:
        df_banco = muestra[muestra["IdBanco"] == banco_id]
        
        if len(df_banco) > 0:
            banco = bancos[banco_id]
            db_name = banco["nombre_db"]
            collection_name = f"cuentas_{db_name.replace('_db', '')}"
            collection = mongo_client[db_name][collection_name]
            
            documentos = []
            for _, row in df_banco.iterrows():
                ci = str(row["Identificacion"])
                numero_cuenta = str(row["NroCuenta"])
                saldo_bs = float(row["Saldo"])
                codigo_verificacion = generar_codigo_verificacion(ci, numero_cuenta)
                
                doc = {
                    "ci": encriptar_por_banco(banco_id, ci),
                    "nombres": str(row["Nombres"]),
                    "apellidos": str(row["Apellidos"]),
                    "numero_cuenta": encriptar_por_banco(banco_id, numero_cuenta),
                    "saldo_bs": encriptar_por_banco(banco_id, saldo_bs),
                    "saldo_usd": encriptar_por_banco(banco_id, 0.0),
                    "codigo_verificacion": codigo_verificacion,
                    "created_at": fecha_actual,
                    "updated_at": fecha_actual,
                    "created_by": "system",
                    "updated_by": "system",
                    "is_active": True
                }
                documentos.append(doc)
            
            if documentos:
                result = collection.insert_many(documentos)
                collection.create_index("ci")
                collection.create_index("numero_cuenta")
                total_mongo += len(result.inserted_ids)
                print(f"  ✅ {banco['nombre_comercial']} ({banco['algoritmo']}): {len(result.inserted_ids)} registros")

print(f"\n📊 TOTAL MONGODB: {total_mongo} registros")

# =========================
# ⚡ INSERTAR EN REDIS (BANCO 14)
# =========================

print("\n⚡ Insertando en Redis con ChaCha20...")

df_redis = muestra[muestra["IdBanco"] == 14]
banco14 = bancos[14]
nombre_redis = banco14["nombre_db"].replace('_db', '')

if len(df_redis) > 0:
    contador = 0
    for _, row in df_redis.iterrows():
        cuenta = str(row["NroCuenta"])
        ci = str(row["Identificacion"])
        saldo_bs = float(row["Saldo"])
        codigo_verificacion = generar_codigo_verificacion(ci, cuenta)
        id_unico = generar_id_unico()
        
        redis_client.hset(f"{nombre_redis}:cuenta:{cuenta}", mapping={
            "id": id_unico,
            "ci": encriptar_chacha20(ci, banco14["clave"]),
            "nombres": str(row["Nombres"]),
            "apellidos": str(row["Apellidos"]),
            "numero_cuenta": encriptar_chacha20(cuenta, banco14["clave"]),
            "saldo_bs": encriptar_chacha20(saldo_bs, banco14["clave"]),
            "saldo_usd": encriptar_chacha20(0.0, banco14["clave"]),
            "codigo_verificacion": codigo_verificacion,
            "created_at": fecha_actual,
            "updated_at": fecha_actual,
            "created_by": "system",
            "updated_by": "system",
            "is_active": "1"
        })
        redis_client.sadd(f"{nombre_redis}:cuentas", cuenta)
        contador += 1
    
    print(f"  ✅ {banco14['nombre_comercial']}: {contador} registros")

# =========================
# 🔍 VALIDACIÓN FINAL
# =========================

print("\n" + "="*70)
print("🔍 VALIDACIÓN FINAL")
print("="*70)

print("\n📊 MONGODB:")
for banco_id in range(6, 14):
    if banco_id in bancos:
        try:
            db_name = bancos[banco_id]["nombre_db"]
            collection_name = f"cuentas_{db_name.replace('_db', '')}"
            
            if db_name in mongo_client.list_database_names():
                count = mongo_client[db_name][collection_name].count_documents({})
                print(f"  ✅ {bancos[banco_id]['nombre_comercial']} ({bancos[banco_id]['algoritmo']}): {count} registros")
                
                if banco_id == 6:
                    ejemplo = mongo_client[db_name][collection_name].find_one()
                    print(f"\n  📝 Ejemplo {bancos[banco_id]['nombre_comercial']} (MongoDB):")
                    print(f"      _id: {ejemplo.get('_id')}")
                    print(f"      ci: {ejemplo.get('ci')[:40]}...")
                    print(f"      nombres: {ejemplo.get('nombres')}")
                    print(f"      numero_cuenta: {ejemplo.get('numero_cuenta')[:40]}...")
                    print(f"      codigo_verificacion: {ejemplo.get('codigo_verificacion')}")
        except Exception as e:
            pass

print("\n⚡ REDIS:")
try:
    cuentas_redis = redis_client.scard(f"{nombre_redis}:cuentas")
    print(f"  ✅ {banco14['nombre_comercial']} (ChaCha20): {cuentas_redis} cuentas")
    
    if cuentas_redis > 0:
        ejemplo_cuenta = redis_client.srandmember(f"{nombre_redis}:cuentas")
        if ejemplo_cuenta:
            ejemplo_data = redis_client.hgetall(f"{nombre_redis}:cuenta:{ejemplo_cuenta}")
            print(f"\n  📝 Ejemplo {banco14['nombre_comercial']} (Redis):")
            print(f"      id: {ejemplo_data.get('id')}")
            print(f"      ci: {ejemplo_data.get('ci')[:40]}...")
            print(f"      nombres: {ejemplo_data.get('nombres')}")
            print(f"      codigo_verificacion: {ejemplo_data.get('codigo_verificacion')}")
    
except Exception as e:
    print(f"  ❌ Error en Redis: {e}")

print("\n" + "="*70)
print("🚀 PROCESO COMPLETADO CON ENCRIPTACIÓN")
print("="*70)