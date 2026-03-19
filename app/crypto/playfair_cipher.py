HEX_ALPHABET = "0123456789ABCDEF"
GRID_SIZE = 4


def _to_hex_text(value: str) -> str:
    return str(value).encode("utf-8").hex().upper()


def _from_hex_text(value: str) -> str:
    return bytes.fromhex(value).decode("utf-8")


def _normalize_key(key: str) -> str:
    key = str(key).upper()
    normalized = "".join(
        ch for ch in key.encode("utf-8").hex().upper()
        if ch in HEX_ALPHABET
    )
    if not normalized:
        normalized = HEX_ALPHABET
    return normalized


def _build_matrix(key: str):
    key_hex = _normalize_key(key)
    seen = []
    for ch in key_hex + HEX_ALPHABET:
        if ch in HEX_ALPHABET and ch not in seen:
            seen.append(ch)

    matrix = [seen[i:i + GRID_SIZE] for i in range(0, 16, GRID_SIZE)]
    pos = {matrix[r][c]: (r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)}
    return matrix, pos


def _prepare_pairs(source: str, filler: str = "F") -> list[str]:
    pairs = []
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


def encrypt(value: str, key: str) -> str:
    source = _to_hex_text(value)
    matrix, pos = _build_matrix(key)
    pairs = _prepare_pairs(source)

    out = []
    for pair in pairs:
        a, b = pair[0], pair[1]
        ra, ca = pos[a]
        rb, cb = pos[b]

        if ra == rb:
            out.append(matrix[ra][(ca + 1) % GRID_SIZE])
            out.append(matrix[rb][(cb + 1) % GRID_SIZE])
        elif ca == cb:
            out.append(matrix[(ra + 1) % GRID_SIZE][ca])
            out.append(matrix[(rb + 1) % GRID_SIZE][cb])
        else:
            out.append(matrix[ra][cb])
            out.append(matrix[rb][ca])

    return "".join(out)


def _looks_like_financial_text(text: str) -> bool:
    """
    Acepta cadenas típicas del banco 4:
    - vacía
    - dígitos
    - dígitos con punto decimal
    """
    if text == "":
        return True

    allowed = set("0123456789.")
    if any(ch not in allowed for ch in text):
        return False

    if text.count(".") > 1:
        return False

    return True


def _recover_hex_with_ambiguous_fillers(decoded_hex: str) -> str:
    """
    El Playfair original insertó 'F' como filler a nivel de nibble hex.
    Al reconstruir bytes, eso puede producir secuencias como '3F'.

    Esta función prueba remover combinaciones de nibble 'F' y se queda con
    la única opción que decode a texto financiero válido.
    """
    from itertools import combinations

    f_positions = [i for i, ch in enumerate(decoded_hex) if ch == "F"]

    candidates = []

    for r in range(len(f_positions) + 1):
        for subset in combinations(f_positions, r):
            candidate_hex = "".join(
                ch for i, ch in enumerate(decoded_hex)
                if i not in subset
            )

            if len(candidate_hex) % 2 != 0:
                continue

            try:
                text = _from_hex_text(candidate_hex)
            except Exception:
                continue

            if _looks_like_financial_text(text):
                candidates.append((candidate_hex, text))

    if not candidates:
        raise ValueError(
            f"No se pudo reconstruir un texto válido desde el hex Playfair: {decoded_hex}"
        )

    # Quitar duplicados por si varias rutas dan el mismo resultado
    unique = []
    seen = set()
    for candidate_hex, text in candidates:
        key = (candidate_hex, text)
        if key not in seen:
            seen.add(key)
            unique.append((candidate_hex, text))

    if len(unique) > 1:
        texts = [text for _, text in unique]
        raise ValueError(
            f"Descifrado Playfair ambiguo. Posibles resultados: {texts}"
        )

    return unique[0][0]


def decrypt(value: str, key: str) -> str:
    matrix, pos = _build_matrix(key)
    value = value.upper()

    if len(value) % 2 != 0:
        raise ValueError("El texto cifrado Playfair debe tener longitud par.")

    out = []
    for i in range(0, len(value), 2):
        a, b = value[i], value[i + 1]
        ra, ca = pos[a]
        rb, cb = pos[b]

        if ra == rb:
            out.append(matrix[ra][(ca - 1) % GRID_SIZE])
            out.append(matrix[rb][(cb - 1) % GRID_SIZE])
        elif ca == cb:
            out.append(matrix[(ra - 1) % GRID_SIZE][ca])
            out.append(matrix[(rb - 1) % GRID_SIZE][cb])
        else:
            out.append(matrix[ra][cb])
            out.append(matrix[rb][ca])

    decoded_hex = "".join(out)
    recovered_hex = _recover_hex_with_ambiguous_fillers(decoded_hex)
    return _from_hex_text(recovered_hex)