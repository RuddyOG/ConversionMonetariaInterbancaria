HEX_ALPHABET = "0123456789ABCDEF"


def _to_hex_text(value: str) -> str:
    return str(value).encode("utf-8").hex().upper()


def _from_hex_text(value: str) -> str:
    return bytes.fromhex(value).decode("utf-8")


def _normalize_key(key: str) -> str:
    key = str(key).upper()
    normalized = "".join(ch for ch in key if ch in HEX_ALPHABET)
    if not normalized:
        raise ValueError("La llave Vigenere debe contener al menos un carácter hexadecimal válido.")
    return normalized


def encrypt(value: str, key: str) -> str:
    source = _to_hex_text(value)
    key = _normalize_key(key)

    out = []
    for i, ch in enumerate(source):
        p = HEX_ALPHABET.index(ch)
        k = HEX_ALPHABET.index(key[i % len(key)])
        out.append(HEX_ALPHABET[(p + k) % 16])

    return "".join(out)


def decrypt(value: str, key: str) -> str:
    key = _normalize_key(key)
    value = value.upper()

    decoded_hex = []
    for i, ch in enumerate(value):
        p = HEX_ALPHABET.index(ch)
        k = HEX_ALPHABET.index(key[i % len(key)])
        decoded_hex.append(HEX_ALPHABET[(p - k) % 16])

    return _from_hex_text("".join(decoded_hex))