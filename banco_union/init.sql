CREATE TABLE cuentas_banco (
    id BIGSERIAL PRIMARY KEY,
    ci_cipher TEXT NOT NULL,
    nombres_cipher TEXT NOT NULL,
    apellidos_cipher TEXT NOT NULL,
    numero_cuenta_cipher TEXT NOT NULL UNIQUE,
    tipo_cuenta_cipher TEXT,
    saldo_usd_cipher TEXT NOT NULL,
    saldo_bs_cipher TEXT,
    codigo_verificacion CHAR(8) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
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