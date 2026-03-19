// app/db/seed_datos/mongo-init.js
// Mapeo de IDs a nombres de bancos
const bancos = {
    6: "banco_ganadero",
    7: "banco_economico",
    8: "banco_prodem",
    9: "banco_solidario",
    10: "banco_fortaleza",
    11: "banco_fie",
    12: "banco_comunidad",
    13: "banco_desarrollo_productivo"
};

// Conectar como admin
db = db.getSiblingDB('admin');
const adminUser = process.env.MONGO_INITDB_ROOT_USERNAME || 'admin';
const adminPass = process.env.MONGO_INITDB_ROOT_PASSWORD || 'admin123';
db.auth(adminUser, adminPass);

print('🚀 Inicializando bases de datos para bancos 6-13...');

// Crear bases de datos para bancos 6-13 usando nombres descriptivos
for (let banco_id = 6; banco_id <= 13; banco_id++) {
    let nombre_banco = bancos[banco_id];
    let dbName = `${nombre_banco}_db`;
    let collectionName = `cuentas_${nombre_banco}`;
    
    let dbInstance = db.getSiblingDB(dbName);
    
    // Crear la colección
    dbInstance.createCollection(collectionName);
    
    // Crear índices básicos
    dbInstance[collectionName].createIndex({ "ci": 1 });
    dbInstance[collectionName].createIndex({ "nro_cuenta": 1 });
    
    print(`✅ Base de datos ${dbName} lista para ${nombre_banco} (ID: ${banco_id})`);
}

print('🎉 Inicialización de MongoDB completada');