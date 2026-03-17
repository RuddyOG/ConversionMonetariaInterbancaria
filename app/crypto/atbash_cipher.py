ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-"
REVERSED_ALPHABET = ALPHABET[::-1]
MAP = {a: b for a, b in zip(ALPHABET, REVERSED_ALPHABET)}
REVERSE_MAP = {b: a for a, b in zip(ALPHABET, REVERSED_ALPHABET)}


def encrypt(value: str, key=None) -> str:
    value = value.upper()
    return "".join(MAP.get(char, char) for char in value)


def decrypt(value: str, key=None) -> str:
    value = value.upper()
    return "".join(REVERSE_MAP.get(char, char) for char in value)