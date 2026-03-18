CREATE TABLE cuentas (
    id BIGSERIAL PRIMARY KEY,
    ci VARCHAR(20) NOT NULL UNIQUE,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    tipo_cuenta VARCHAR(20) NOT NULL CHECK (tipo_cuenta IN ('ahorro', 'corriente')),
    saldo_bolivianos NUMERIC(14,2) NOT NULL DEFAULT 0.00 CHECK (saldo_bolivianos >= 0),
    saldo_dolares NUMERIC(14,2) NOT NULL DEFAULT 0.00 CHECK (saldo_dolares >= 0),
    codigo_verificacion VARCHAR(20) NOT NULL,

    -- auditoría básica
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(50) NOT NULL DEFAULT 'system',
    updated_by VARCHAR(50) NOT NULL DEFAULT 'system',
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_cuentas_updated_at
BEFORE UPDATE ON cuentas
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();