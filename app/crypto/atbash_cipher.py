HEX_ALPHABET = "0123456789ABCDEF"


def _to_hex_text(value: str) -> str:
    return str(value).encode("utf-8").hex().upper()


def _from_hex_text(value: str) -> str:
    return bytes.fromhex(value).decode("utf-8")


def encrypt(value: str, key=None) -> str:
    source = _to_hex_text(value)
    return "".join(HEX_ALPHABET[15 - HEX_ALPHABET.index(ch)] for ch in source)


def decrypt(value: str, key=None) -> str:
    decoded_hex = "".join(HEX_ALPHABET[15 - HEX_ALPHABET.index(ch)] for ch in value.upper())
    return _from_hex_text(decoded_hex)