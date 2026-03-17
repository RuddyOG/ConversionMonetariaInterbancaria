from decimal import Decimal, ROUND_HALF_UP


def normalize_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_balance(value) -> str:
    decimal_value = Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return format(decimal_value, ".4f")