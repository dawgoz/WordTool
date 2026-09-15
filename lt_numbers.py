"""Lithuanian number-to-words helpers using num2words."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from num2words import num2words


def _split_amount(amount: Decimal) -> tuple[int, int]:
    """Split a monetary amount into (whole, cents), rounding to 2 decimals."""
    quantized = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    whole = int(quantized)
    cents = int((quantized - whole) * 100)
    return whole, abs(cents)


def _eur_word(n: int) -> str:
    """Return the correctly declined Lithuanian word for 'euro(s)'."""
    # Lithuanian plural rules: 1 -> euras, 2..9 (except 11..19) -> eurai, else eurų
    last_two = abs(n) % 100
    last = abs(n) % 10
    if 11 <= last_two <= 19:
        return "eurų"
    if last == 1:
        return "euras"
    if 2 <= last <= 9:
        return "eurai"
    return "eurų"


def _cent_word(n: int) -> str:
    """Return the correctly declined Lithuanian word for 'cent(s)'."""
    last_two = abs(n) % 100
    last = abs(n) % 10
    if 11 <= last_two <= 19:
        return "centų"
    if last == 1:
        return "centas"
    if 2 <= last <= 9:
        return "centai"
    return "centų"


def price_to_lithuanian_words(amount: Decimal | float | str) -> str:
    """Convert a monetary amount to Lithuanian words.

    Example: 1234.56 -> "vienas tūkstantis du šimtai trisdešimt keturi eurai 56 ct"
    """
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    whole, cents = _split_amount(amount)
    whole_words = num2words(whole, lang="lt")
    return f"{whole_words} {_eur_word(whole)} {cents:02d} {_cent_word(cents)}"


def price_to_lithuanian_words_full(amount: Decimal | float | str) -> str:
    """Same as `price_to_lithuanian_words` but cents are also spelled out."""
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    whole, cents = _split_amount(amount)
    whole_words = num2words(whole, lang="lt")
    cent_words = num2words(cents, lang="lt") if cents else "nulis"
    return (
        f"{whole_words} {_eur_word(whole)} "
        f"{cent_words} {_cent_word(cents)}"
    )
