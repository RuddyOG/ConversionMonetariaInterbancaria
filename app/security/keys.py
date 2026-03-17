#Dame la llave y el algoritmo del banco 5
import json
from pathlib import Path
from typing import Any, Dict


BASE_DIR = Path(__file__).resolve().parents[2]
KEYS_FILE = BASE_DIR / "configs" / "keys.json"


class KeyManager:
    def __init__(self, keys_file: Path = KEYS_FILE):
        self.keys_file = keys_file
        self._keys_data = self._load_keys()

    def _load_keys(self) -> Dict[str, Dict[str, Any]]:
        if not self.keys_file.exists():
            raise FileNotFoundError(f"No se encontró el archivo de llaves: {self.keys_file}")

        with open(self.keys_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("El archivo keys.json debe contener un objeto JSON en la raíz.")

        return data

    def reload(self) -> None:
        self._keys_data = self._load_keys()

    def get_bank_config(self, bank_id: int | str) -> Dict[str, Any]:
        bank_id_str = str(bank_id)
        config = self._keys_data.get(bank_id_str)

        if config is None:
            raise KeyError(f"No existe configuración de llaves para el banco con id {bank_id_str}")

        return config

    def get_bank_name(self, bank_id: int | str) -> str:
        return self.get_bank_config(bank_id).get("bank_name", "")

    def get_algorithm(self, bank_id: int | str) -> str:
        algorithm = self.get_bank_config(bank_id).get("algorithm")
        if not algorithm:
            raise ValueError(f"El banco {bank_id} no tiene algoritmo configurado.")
        return algorithm

    def get_encryption_key(self, bank_id: int | str) -> Any:
        return self.get_bank_config(bank_id).get("encryption_key")

    def get_hmac_key(self, bank_id: int | str) -> str:
        hmac_key = self.get_bank_config(bank_id).get("hmac_key")
        if not hmac_key:
            raise ValueError(f"El banco {bank_id} no tiene hmac_key configurada.")
        return hmac_key

    def get_signature_key(self, bank_id: int | str) -> str | None:
        return self.get_bank_config(bank_id).get("signature_key")