"""Territory profile datatypes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class InteractionCopy:
    product_searches: tuple[str, ...]
    help_searches: tuple[str, ...]
    agent_topics: tuple[tuple[str, str, bool], ...]
    review_titles: tuple[str, ...]
    review_detail_positive: str
    review_detail_negative: str
    agent_detail_resolved: str
    agent_detail_unresolved: str
    web_session_detail: str


@dataclass(frozen=True)
class ForeclosureAssetLabels:
    yes: str
    no: str
    policy: str
    claim: str


@dataclass(frozen=True)
class TerritoryProfile:
    """Locale/territory bundle used when seeding and serving the app."""

    id: str
    display_name: str
    default_currency: str
    default_intl_locale: str
    supported_ui_locales: tuple[str, ...]
    primary_ui_locale: str
    default_seed_language: str
    llm_market_context: str
    email_domain: str
    portal_sms_url_template: str
    mobile_prefixes: tuple[str, ...]
    use_mobile_kosher_flag: bool
    cities: tuple[tuple[str, str, int], ...]
    city_aliases: dict[str, str]
    first_names: tuple[str, ...]
    last_names: tuple[str, ...]
    employers: tuple[tuple[int, str], ...]
    corp_names: dict[int, str]
    funds: tuple[tuple[int, int, str], ...]
    customer_type_map: dict[int, str]
    marital_map: dict[str, str]
    generate_customer_id: Callable[..., int]

    def canonical_cities(self) -> tuple[str, ...]:
        return tuple(c[0] for c in self.cities)

    def known_cities_map(self) -> dict[str, str]:
        """Lowercase alias → canonical city name stored in the warehouse."""
        out = dict(self.city_aliases)
        for city, _street, _zip in self.cities:
            key = city.lower()
            out.setdefault(key, city)
        return out
