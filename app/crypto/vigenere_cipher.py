ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-"
ALPHABET_INDEX = {char: idx for idx, char in enumerate(ALPHABET)}
ALPHABET_LEN = len(ALPHABET)


def _extend_key(text: str, key: str) -> str:
    key = key.upper()
    filtered = [char for char in text.upper() if char in ALPHABET_INDEX]

    repeated_key = []
    key_index = 0

    for _ in filtered:
        repeated_key.append(key[key_index % len(key)])
        key_index += 1

    return "".join(repeated_key)


def encrypt(value: str, key: str) -> str:
    value = value.upper()
    extended_key = _extend_key(value, key)
    result = []
    key_pos = 0

    for char in value:
        if char in ALPHABET_INDEX:
            shift = ALPHABET_INDEX[extended_key[key_pos]]
            new_index = (ALPHABET_INDEX[char] + shift) % ALPHABET_LEN
            result.append(ALPHABET[new_index])
            key_pos += 1
        else:
            result.append(char)

    return "".join(result)


def decrypt(value: str, key: str) -> str:
    value = value.upper()
    extended_key = _extend_key(value, key)
    result = []
    key_pos = 0

    for char in value:
        if char in ALPHABET_INDEX:
            shift = ALPHABET_INDEX[extended_key[key_pos]]
            new_index = (ALPHABET_INDEX[char] - shift) % ALPHABET_LEN
            result.append(ALPHABET[new_index])
            key_pos += 1
        else:
            result.append(char)

    return "".join(result)