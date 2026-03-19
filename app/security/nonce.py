#Genera nonce y timestamp; valida que no se repita
import secrets
from collections import deque
from datetime import datetime
from typing import Deque, Set

from app.security.constants import (
    DEFAULT_TIMEZONE,
    NONCE_CACHE_MAX_SIZE,
    NONCE_NBYTES,
    TIMESTAMP_TOLERANCE_SECONDS,
)


class NonceManager:
    def __init__(self, max_size: int = NONCE_CACHE_MAX_SIZE):
        self.max_size = max_size
        self._used_nonces: Set[str] = set()
        self._nonce_order: Deque[str] = deque()

    def generate_nonce(self) -> str:
        return secrets.token_hex(NONCE_NBYTES).upper()

    def generate_timestamp(self) -> str:
        return datetime.now(DEFAULT_TIMEZONE).isoformat()

    def is_timestamp_valid(
        self,
        timestamp_str: str,
        max_seconds: int = TIMESTAMP_TOLERANCE_SECONDS,
    ) -> bool:
        try:
            request_time = datetime.fromisoformat(timestamp_str)
            now = datetime.now(DEFAULT_TIMEZONE)
            delta = abs((now - request_time).total_seconds())
            return delta <= max_seconds
        except Exception:
            return False

    def register_nonce(self, nonce: str) -> bool:
        nonce = nonce.strip().upper()

        if nonce in self._used_nonces:
            return False

        self._used_nonces.add(nonce)
        self._nonce_order.append(nonce)

        while len(self._nonce_order) > self.max_size:
            oldest = self._nonce_order.popleft()
            self._used_nonces.discard(oldest)

        return True

    def is_replay(self, nonce: str) -> bool:
        return nonce.strip().upper() in self._used_nonces