"""Territory-aware money and number formatting for LLM context (no fixed locale symbols)."""

from __future__ import annotations

import sqlite3

from customer360.territory_runtime import territory_payload

NARROW_CURRENCY_SYMBOL: dict[str, str] = {
    "ILS": "₪",
    "GBP": "£",
    "EUR": "€",
    "SAR": "ر.س",
    "USD": "$",
}


def territory_currency_code(conn: sqlite3.Connection | None = None) -> str:
    code = str(territory_payload(conn).get("currency") or "USD").strip().upper()
    return code or "USD"


def _grouped_integer(value: float | int, *, intl_locale: str) -> str:
    n = int(round(float(value)))
    lang = (intl_locale or "en").split("-")[0].lower()
    if lang in ("fr", "he", "ar"):
        return f"{n:,}".replace(",", "\u202f")
    if lang == "es":
        return f"{n:,}".replace(",", ".")
    return f"{n:,}"


def format_territory_money(value: float, conn: sqlite3.Connection | None = None) -> str:
    payload = territory_payload(conn)
    currency = territory_currency_code(conn)
    symbol = NARROW_CURRENCY_SYMBOL.get(currency, f"{currency} ")
    grouped = _grouped_integer(value, intl_locale=str(payload.get("intl_locale") or "en"))
    return f"{symbol}{grouped}"


def format_territory_integer(value: float, conn: sqlite3.Connection | None = None) -> str:
    payload = territory_payload(conn)
    return _grouped_integer(value, intl_locale=str(payload.get("intl_locale") or "en"))
