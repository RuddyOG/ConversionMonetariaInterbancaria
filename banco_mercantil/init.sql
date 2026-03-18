CREATE TABLE cuentas_banco (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ci_cipher TEXT NOT NULL,
    nombres_cipher TEXT NOT NULL,
    apellidos_cipher TEXT NOT NULL,
    numero_cuenta_cipher TEXT NOT NULL,
    tipo_cuenta_cipher TEXT NULL,
    saldo_usd_cipher TEXT NOT NULL,
    saldo_bs_cipher TEXT NULL,
    codigo_verificacion CHAR(8) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);