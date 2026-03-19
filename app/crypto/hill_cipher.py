HEX_ALPHABET = "0123456789ABCDEF"
HEX_INDEX = {char: idx for idx, char in enumerate(HEX_ALPHABET)}
MODULUS = 16


def _to_hex_text(value: str) -> str:
    return str(value).encode("utf-8").hex().upper()


def _from_hex_text(value: str) -> str:
    return bytes.fromhex(value).decode("utf-8")


def _mod_inverse(a: int, m: int) -> int:
    a = a % m
    for x in range(1, m):
        if (a * x) % m == 1:
            return x
    raise ValueError(f"No existe inverso modular para {a} en módulo {m}.")


def _matrix_inverse_2x2(matrix, modulus: int):
    a, b = matrix[0]
    c, d = matrix[1]

    determinant = (a * d - b * c) % modulus
    det_inv = _mod_inverse(determinant, modulus)

    inverse = [
        [(d * det_inv) % modulus, (-b * det_inv) % modulus],
        [(-c * det_inv) % modulus, (a * det_inv) % modulus],
    ]
    return inverse


def encrypt(value: str, key) -> str:
    if not isinstance(key, list) or len(key) != 2 or len(key[0]) != 2 or len(key[1]) != 2:
        raise ValueError("La llave Hill debe ser una matriz 2x2.")

    source = _to_hex_text(value)

    if len(source) % 2 != 0:
        source += "F"

    out = []
    for i in range(0, len(source), 2):
        x = HEX_INDEX[source[i]]
        y = HEX_INDEX[source[i + 1]]

        e1 = (key[0][0] * x + key[0][1] * y) % MODULUS
        e2 = (key[1][0] * x + key[1][1] * y) % MODULUS

        out.append(HEX_ALPHABET[e1])
        out.append(HEX_ALPHABET[e2])

    return "".join(out)


def decrypt(value: str, key) -> str:
    if not isinstance(key, list) or len(key) != 2 or len(key[0]) != 2 or len(key[1]) != 2:
        raise ValueError("La llave Hill debe ser una matriz 2x2.")

    value = value.upper()

    if len(value) % 2 != 0:
        raise ValueError("El texto cifrado Hill debe tener longitud par.")

    inverse_key = _matrix_inverse_2x2(key, MODULUS)

    out = []
    for i in range(0, len(value), 2):
        y1 = HEX_INDEX[value[i]]
        y2 = HEX_INDEX[value[i + 1]]

        x1 = (inverse_key[0][0] * y1 + inverse_key[0][1] * y2) % MODULUS
        x2 = (inverse_key[1][0] * y1 + inverse_key[1][1] * y2) % MODULUS

        out.append(HEX_ALPHABET[x1])
        out.append(HEX_ALPHABET[x2])

    decoded_hex = "".join(out)
    return _from_hex_text(decoded_hex)