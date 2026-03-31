from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


ASCII_PATTERN = re.compile(r"^[\x20-\x7E]*$")


def to_upper_ascii(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_text.upper()


def ensure_ascii(value: str) -> bool:
    return bool(ASCII_PATTERN.fullmatch(value))


def pad_left_zeros(value: str | int, length: int) -> str:
    return str(value).zfill(length)[-length:]


def pad_right_spaces(value: str, length: int) -> str:
    return value[:length].ljust(length)


def pad_left_spaces(value: str, length: int) -> str:
    return value[:length].rjust(length)


def amount_to_cents(value: str | Decimal) -> int:
    decimal_value = Decimal(str(value))
    quantized = decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(quantized * 100)


def parse_amount(value: str) -> Decimal:
    try:
        decimal_value = Decimal(value.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError("Amount must be a valid decimal value.") from exc

    if decimal_value <= 0:
        raise ValueError("Amount must be greater than zero.")
    if decimal_value.as_tuple().exponent < -2:
        raise ValueError("Amount can have at most 2 decimal places.")
    return decimal_value


def mask_account_number(account_number: str) -> str:
    account_number = account_number.strip()
    if len(account_number) <= 4:
        return "*" * len(account_number)
    return "*" * (len(account_number) - 4) + account_number[-4:]

