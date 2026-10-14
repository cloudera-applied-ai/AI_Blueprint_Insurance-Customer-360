"""Territory-aware agent money formatting."""

from __future__ import annotations

from customer360.territory_formatting import format_territory_money, territory_currency_code


def test_format_territory_money_uses_gbp_symbol(monkeypatch):
    monkeypatch.setattr(
        "customer360.territory_formatting.territory_payload",
        lambda _conn: {"currency": "GBP", "intl_locale": "en-GB"},
    )
    assert territory_currency_code(None) == "GBP"
    assert format_territory_money(1234, None).startswith("£")
