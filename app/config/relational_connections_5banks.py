"""
Conexiones para los 5 bancos relacionales que ya existen en `BackendRelacional`.

Nota: estos datos están hardcodeados para que la integración sea rápida para la demo.
En una versión final conviene moverlos a variables de entorno.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Dict, Any


DBEngine = Literal["postgres", "mysql", "mariadb"]


@dataclass(frozen=True)
class DbConfig:
    engine: DBEngine
    host: str
    port: int
    database: str
    user: str
    password: str


# Importante: estos puertos coinciden con el `docker-compose.yml` del BackendRelacional.
RELATIONAL_BANKS_1_TO_5: Dict[int, DbConfig] = {
    1: DbConfig(
        engine="postgres",
        host="localhost",
        port=5433,
        database="banco_union",
        user="admin",
        password="union123",
    ),
    2: DbConfig(
        engine="mysql",
        host="localhost",
        port=3307,
        database="banco_mercantil",
        user="admin",
        password="mercantil123",
    ),
    3: DbConfig(
        engine="mariadb",
        host="localhost",
        port=3308,
        database="banco_bnb",
        user="admin",
        password="bnb123",
    ),
    4: DbConfig(
        engine="postgres",
        host="localhost",
        port=5434,
        database="banco_bcp",
        user="admin",
        password="bcp123",
    ),
    5: DbConfig(
        engine="mysql",
        host="localhost",
        port=3309,
        database="banco_bisa",
        user="admin",
        password="bisa123",
    ),
}


ASFI_CENTRAL: DbConfig = DbConfig(
    engine="postgres",
    host="localhost",
    port=5435,
    database="asfi_central",
    user="admin",
    password="asfi123",
)


def algorithm_for_bank_1_to_5(bank_id: int) -> str:
    """
    Algoritmos compatibles con `BackendRelacional/load_1pct_relacionales.py`.
    """

    mapping = {
        1: "caesar",
        2: "atbash",
        3: "vigenere",
        4: "playfair",
        5: "hill",
    }
    if bank_id not in mapping:
        raise KeyError(f"Bank {bank_id} no está soportado por este módulo.")
    return mapping[bank_id]

