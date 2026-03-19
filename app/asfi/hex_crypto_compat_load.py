"""
Compatibilidad con el cifrado usado por:
`BackendRelacional/load_1pct_relacionales.py`

El seed relacional cifra valores sensibles convirtiéndolos primero a HEX
(utf-8 bytes -> hex uppercase) y luego aplicando cifrados sobre el alfabeto
HEX: 0-9, A-F.

Este módulo implementa cifrado/descifrado sobre HEX para que ASFI pueda:
- descifrar `saldo_usd_cipher`
- cifrar `saldo_bs_cipher` (cuando sea necesario en Banco API)
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple

HEX_ALPHABET = "0123456789ABCDEF"
_HEX_ALPHABET_INDEX = {ch: idx for idx, ch in enumerate(HEX_ALPHABET)}

# Parámetros *coinciden con BackendRelacional/load_1pct_relacionales.py*
CAESAR_SHIFT = 3
VIGENERE_KEY = "B0A1"
PLAYFAIR_KEY = "BCP2026"
HILL_MATRIX = ((3, 3), (2, 5))  # [[a,b],[c,d]]
PLAYFAIR_FILLER = "F"


def to_hex_text(value: str) -> str:
    return str(value).encode("utf-8").hex().upper()


def from_hex_text(hex_text: str) -> str:
    # hex_text debe tener longitud par
    raw = bytes.fromhex(hex_text)
    return raw.decode("utf-8")


def _normalize_balance_to_4_decimals_str(value: str | Decimal) -> str:
    decimal_value = Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return format(decimal_value, ".4f")


def caesar_hex_encrypt(text: str, shift: int = CAESAR_SHIFT) -> str:
    source = to_hex_text(text)
    return "".join(
        HEX_ALPHABET[(_HEX_ALPHABET_INDEX[ch] + shift) % 16] for ch in source if ch in _HEX_ALPHABET_INDEX
    )


def caesar_hex_decrypt(cipher_hex: str, shift: int = CAESAR_SHIFT) -> str:
    return "".join(
        HEX_ALPHABET[(_HEX_ALPHABET_INDEX[ch] - shift) % 16] for ch in cipher_hex if ch in _HEX_ALPHABET_INDEX
    )


def atbash_hex_encrypt(text: str) -> str:
    source = to_hex_text(text)
    return "".join(HEX_ALPHABET[15 - _HEX_ALPHABET_INDEX[ch]] for ch in source if ch in _HEX_ALPHABET_INDEX)


def atbash_hex_decrypt(cipher_hex: str) -> str:
    # Atbash es auto-inverso en este esquema.
    return "".join(HEX_ALPHABET[15 - _HEX_ALPHABET_INDEX[ch]] for ch in cipher_hex if ch in _HEX_ALPHABET_INDEX)


def vigenere_hex_encrypt(text: str, key: str = VIGENERE_KEY) -> str:
    source = to_hex_text(text)
    key = "".join(ch for ch in key.upper() if ch in _HEX_ALPHABET_INDEX)
    out: List[str] = []
    for i, ch in enumerate(source):
        p = _HEX_ALPHABET_INDEX[ch]
        k = _HEX_ALPHABET_INDEX[key[i % len(key)]]
        out.append(HEX_ALPHABET[(p + k) % 16])
    return "".join(out)


def vigenere_hex_decrypt(cipher_hex: str, key: str = VIGENERE_KEY) -> str:
    key = "".join(ch for ch in key.upper() if ch in _HEX_ALPHABET_INDEX)
    out: List[str] = []
    for i, ch in enumerate(cipher_hex):
        c = _HEX_ALPHABET_INDEX[ch]
        k = _HEX_ALPHABET_INDEX[key[i % len(key)]]
        out.append(HEX_ALPHABET[(c - k) % 16])
    return "".join(out)


def _build_playfair_matrix(key_text: str = PLAYFAIR_KEY) -> Tuple[List[List[str]], dict[str, Tuple[int, int]]]:
    key_hex = to_hex_text(key_text)
    seen: List[str] = []
    for ch in key_hex + HEX_ALPHABET:
        if ch in _HEX_ALPHABET_INDEX and ch not in seen:
            seen.append(ch)
    matrix = [seen[i : i + 4] for i in range(0, 16, 4)]
    pos = {matrix[r][c]: (r, c) for r in range(4) for c in range(4)}
    return matrix, pos


def _playfair_prepare(source: str, filler: str = PLAYFAIR_FILLER) -> List[str]:
    pairs: List[str] = []
    i = 0
    while i < len(source):
        a = source[i]
        if i + 1 >= len(source):
            b = filler
            i += 1
        else:
            b = source[i + 1]
            if a == b:
                b = filler
                i += 1
            else:
                i += 2
        pairs.append(a + b)
    return pairs


def playfair_hex_encrypt(text: str, key_text: str = PLAYFAIR_KEY) -> str:
    source = to_hex_text(text)
    matrix, pos = _build_playfair_matrix(key_text)
    pairs = _playfair_prepare(source)
    out: List[str] = []
    for pair in pairs:
        a, b = pair[0], pair[1]
        ra, ca = pos[a]
        rb, cb = pos[b]
        if ra == rb:
            out.append(matrix[ra][(ca + 1) % 4])
            out.append(matrix[rb][(cb + 1) % 4])
        elif ca == cb:
            out.append(matrix[(ra + 1) % 4][ca])
            out.append(matrix[(rb + 1) % 4][cb])
        else:
            out.append(matrix[ra][cb])
            out.append(matrix[rb][ca])
    return "".join(out)


def playfair_hex_decrypt(cipher_hex: str, key_text: str = PLAYFAIR_KEY) -> str:
    if len(cipher_hex) % 2 != 0:
        raise ValueError("playfair_hex_decrypt: cipher_hex debe tener longitud par.")

    matrix, pos = _build_playfair_matrix(key_text)
    out: List[str] = []

    for i in range(0, len(cipher_hex), 2):
        a = cipher_hex[i]
        b = cipher_hex[i + 1]
        ra, ca = pos[a]
        rb, cb = pos[b]

        if ra == rb:
            out.append(matrix[ra][(ca - 1) % 4])
            out.append(matrix[rb][(cb - 1) % 4])
        elif ca == cb:
            out.append(matrix[(ra - 1) % 4][ca])
            out.append(matrix[(rb - 1) % 4][cb])
        else:
            out.append(matrix[ra][cb])
            out.append(matrix[rb][ca])

    plain_hex_with_fillers = "".join(out)

    # Limpieza compatible con _playfair_prepare():
    # - cuando a==b se inserta filler como "segundo nibble" del par,
    #   y el nibble repetido (igual a a) queda como primer nibble del siguiente par.
    #
    # Regla:
    # - si en el par i el segundo nibble == filler y el primer nibble del par i+1 == a,
    #   entonces el segundo nibble del par i era filler insertado y se elimina.
    filler = PLAYFAIR_FILLER
    pairs = [plain_hex_with_fillers[i : i + 2] for i in range(0, len(plain_hex_with_fillers), 2)]
    cleaned_parts: List[str] = []
    for idx, p in enumerate(pairs):
        a = p[0]
        b = p[1]
        if b == filler and idx + 1 < len(pairs) and pairs[idx + 1][0] == a:
            cleaned_parts.append(a)
        else:
            cleaned_parts.append(a + b)
    return "".join(cleaned_parts)


def hill_hex_encrypt(text: str, matrix: Tuple[Tuple[int, int], Tuple[int, int]] = HILL_MATRIX) -> str:
    source = to_hex_text(text)
    if len(source) % 2 != 0:
        source += "F"

    a, b = matrix[0]
    c, d = matrix[1]

    out: List[str] = []
    for i in range(0, len(source), 2):
        x = _HEX_ALPHABET_INDEX[source[i]]
        y = _HEX_ALPHABET_INDEX[source[i + 1]]
        e1 = (a * x + b * y) % 16
        e2 = (c * x + d * y) % 16
        out.append(HEX_ALPHABET[e1])
        out.append(HEX_ALPHABET[e2])
    return "".join(out)


def hill_hex_decrypt(cipher_hex: str, matrix: Tuple[Tuple[int, int], Tuple[int, int]] = HILL_MATRIX) -> str:
    if len(cipher_hex) % 2 != 0:
        raise ValueError("hill_hex_decrypt: cipher_hex debe tener longitud par.")

    a, b = matrix[0]
    c, d = matrix[1]

    det = (a * d - b * c) % 16
    # Para la matriz usada por el proyecto (3,3,2,5), det=9 y su inverso módulo 16 es 9.
    # Calculamos por seguridad genérica: det_inv = x tal que det*x % 16 == 1
    det_inv = None
    for x in range(16):
        if (det * x) % 16 == 1:
            det_inv = x
            break
    if det_inv is None:
        raise ValueError("hill_hex_decrypt: matriz no invertible módulo 16.")

    # Inversa: det^{-1} * [[d,-b],[-c,a]] mod 16
    inv_a = (det_inv * d) % 16
    inv_b = (det_inv * (-b)) % 16
    inv_c = (det_inv * (-c)) % 16
    inv_d = (det_inv * a) % 16

    out: List[str] = []
    for i in range(0, len(cipher_hex), 2):
        e1 = _HEX_ALPHABET_INDEX[cipher_hex[i]]
        e2 = _HEX_ALPHABET_INDEX[cipher_hex[i + 1]]
        x = (inv_a * e1 + inv_b * e2) % 16
        y = (inv_c * e1 + inv_d * e2) % 16
        out.append(HEX_ALPHABET[x])
        out.append(HEX_ALPHABET[y])
    return "".join(out)


def encrypt_balance_to_cipher(bank_id: int, saldo_plain: str) -> str:
    algo = {1: "caesar", 2: "atbash", 3: "vigenere", 4: "playfair", 5: "hill"}[bank_id]
    if algo == "caesar":
        return caesar_hex_encrypt(saldo_plain)
    if algo == "atbash":
        return atbash_hex_encrypt(saldo_plain)
    if algo == "vigenere":
        return vigenere_hex_encrypt(saldo_plain)
    if algo == "playfair":
        return playfair_hex_encrypt(saldo_plain)
    if algo == "hill":
        return hill_hex_encrypt(saldo_plain)
    raise ValueError(f"Algoritmo no soportado para banco {bank_id}: {algo}")


def decrypt_cipher_to_balance(bank_id: int, cipher_hex: str) -> str:
    algo = {1: "caesar", 2: "atbash", 3: "vigenere", 4: "playfair", 5: "hill"}[bank_id]
    cipher_hex = (cipher_hex or "").strip()

    if algo == "caesar":
        hex_plain = caesar_hex_decrypt(cipher_hex)
    elif algo == "atbash":
        hex_plain = atbash_hex_decrypt(cipher_hex)
    elif algo == "vigenere":
        hex_plain = vigenere_hex_decrypt(cipher_hex)
    elif algo == "playfair":
        hex_plain = playfair_hex_decrypt(cipher_hex)
    elif algo == "hill":
        hex_plain = hill_hex_decrypt(cipher_hex)
    else:
        raise ValueError(f"Algoritmo no soportado para banco {bank_id}: {algo}")

    decoded_text = from_hex_text(hex_plain)
    # Normalizar a 4 decimales para consistencia del modelo ASFI.
    return _normalize_balance_to_4_decimals_str(decoded_text)


def convert_usd_to_bs_6_96(saldo_usd_str: str) -> str:
    saldo_usd = Decimal(str(saldo_usd_str))
    saldo_bs = saldo_usd * Decimal("6.96")
    saldo_bs = saldo_bs.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return format(saldo_bs, ".4f")

