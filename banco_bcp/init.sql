CREATE TABLE cuentas_banco (
    id BIGSERIAL PRIMARY KEY,
    ci TEXT NOT NULL,
    nombres TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    numero_cuenta TEXT NOT NULL UNIQUE,
    saldo_usd TEXT NOT NULL,
    saldo_bs TEXT,
    codigo_verificacion CHAR(8) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT,
    updated_by TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_cuentas_banco_updated_at
BEFORE UPDATE ON cuentas_banco
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();