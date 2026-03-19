CREATE TABLE cuentas_banco (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ci TEXT NOT NULL,
    nombres TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    numero_cuenta TEXT NOT NULL,
    saldo_usd TEXT NOT NULL,
    saldo_bs TEXT NULL,
    codigo_verificacion CHAR(8) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by TEXT,
    updated_by TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);