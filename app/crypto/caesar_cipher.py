ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-"
ALPHABET_INDEX = {char: idx for idx, char in enumerate(ALPHABET)}
ALPHABET_LEN = len(ALPHABET)


def encrypt(value: str, key: int) -> str:
    value = value.upper()
    result = []

    for char in value:
        if char in ALPHABET_INDEX:
            new_index = (ALPHABET_INDEX[char] + key) % ALPHABET_LEN
            result.append(ALPHABET[new_index])
        else:
            result.append(char)

    return "".join(result)


def decrypt(value: str, key: int) -> str:
    value = value.upper()
    result = []

    for char in value:
        if char in ALPHABET_INDEX:
            new_index = (ALPHABET_INDEX[char] - key) % ALPHABET_LEN
            result.append(ALPHABET[new_index])
        else:
            result.append(char)

    return "".join(result)