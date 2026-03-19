CREATE TABLE bancos (
    banco_id INT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    algoritmo_encriptacion VARCHAR(50) NOT NULL
);

CREATE TABLE cuentas_asfi (
    id BIGSERIAL PRIMARY KEY,
    banco_id INT NOT NULL,
    id_origen BIGINT NOT NULL,
    saldo_usd_original NUMERIC(18,4) NOT NULL DEFAULT 0.0000,
    saldo_bs_convertido NUMERIC(18,4) NOT NULL DEFAULT 0.0000,
    fecha_conversion TIMESTAMPTZ,
    codigo_verificacion CHAR(8) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_cuentas_asfi_banco
        FOREIGN KEY (banco_id)
        REFERENCES bancos (banco_id),
    CONSTRAINT uq_banco_id_origen
        UNIQUE (banco_id, id_origen)
);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_cuentas_asfi_updated_at
BEFORE UPDATE ON cuentas_asfi
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

INSERT INTO bancos (banco_id, nombre, algoritmo_encriptacion) VALUES
(1, 'Banco Union', 'Cesar'),
(2, 'Banco Mercantil Santa Cruz', 'Atbash'),
(3, 'Banco Nacional de Bolivia', 'Vigenere'),
(4, 'Banco de Credito de Bolivia', 'Playfair'),
(5, 'Banco BISA', 'Hill');