"""Admin-persisted territory and UI localization preferences."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from customer360.admin_store import admin_connect, ensure_admin_schema
from customer360.territory import TERRITORY_IDS, get_territory, list_territories, territory_catalog_entry
from customer360.territory.languages import LANGUAGE_IDS, UI_LANGUAGE_IDS, language_catalog
from customer360.territory.localization import localization_options

VALID_UI_LOCALE_CODES = frozenset(LANGUAGE_IDS)


def default_supported_ui_locales() -> list[str]:
    return list(UI_LANGUAGE_IDS)


@dataclass
class LocalizationAdminConfig:
    territory_id: str | None = None
    ui_locale: str | None = None
    supported_ui_locales: list[str] | None = None
    updated_at: str | None = None

    def normalized_territory_id(self) -> str | None:
        if not self.territory_id or not str(self.territory_id).strip():
            return None
        tid = str(self.territory_id).strip().lower()
        if tid not in TERRITORY_IDS:
            raise ValueError(f"Unknown territory {tid!r}; expected one of: {', '.join(TERRITORY_IDS)}")
        return tid

    def normalized_ui_locale(self, *, territory_id: str) -> str | None:
        if not self.ui_locale or not str(self.ui_locale).strip():
            return None
        code = str(self.ui_locale).strip().lower()
        if code == "il":
            code = "he"
        if code not in VALID_UI_LOCALE_CODES:
            raise ValueError(f"Unknown UI locale {code!r}; expected one of: {', '.join(LANGUAGE_IDS)}")
        get_territory(territory_id)
        return code

    def normalized_supported_ui_locales(self) -> list[str]:
        raw = self.supported_ui_locales
        if raw is None:
            return default_supported_ui_locales()
        if not raw:
            raise ValueError("At least one supported UI language is required.")
        seen: list[str] = []
        for item in raw:
            code = str(item).strip().lower()
            if code == "il":
                code = "he"
            if code not in VALID_UI_LOCALE_CODES:
                raise ValueError(
                    f"Unknown supported UI locale {code!r}; expected one of: {', '.join(LANGUAGE_IDS)}",
                )
            if code not in seen:
                seen.append(code)
        if not seen:
            raise ValueError("At least one supported UI language is required.")
        return seen


def resolve_supported_ui_locales(config: LocalizationAdminConfig | None = None) -> list[str]:
    if config is None:
        config = load_localization_admin()
    try:
        return config.normalized_supported_ui_locales()
    except ValueError:
        return default_supported_ui_locales()


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _parse_supported_json(raw: str | None) -> list[str] | None:
    if raw is None or not str(raw).strip():
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, list):
        return None
    return [str(x) for x in parsed]


def load_localization_admin(conn: sqlite3.Connection | None = None) -> LocalizationAdminConfig:
    own = conn is None
    if own:
        conn = admin_connect()
    else:
        ensure_admin_schema(conn)
    row = conn.execute("SELECT * FROM APP_ADMIN_LOCALIZATION WHERE ID = 1").fetchone()
    if own:
        conn.close()
    if row is None:
        return LocalizationAdminConfig()
    keys = row.keys() if hasattr(row, "keys") else []
    supported = None
    if "SUPPORTED_UI_LOCALES" in keys:
        supported = _parse_supported_json(row["SUPPORTED_UI_LOCALES"])
    return LocalizationAdminConfig(
        territory_id=row["TERRITORY_ID"] if "TERRITORY_ID" in keys else row[1],
        ui_locale=row["UI_LOCALE"] if "UI_LOCALE" in keys else row[2],
        supported_ui_locales=supported,
        updated_at=row["UPDATED_AT"] if "UPDATED_AT" in keys else row[-1],
    )


def save_localization_admin(
    config: LocalizationAdminConfig,
    conn: sqlite3.Connection | None = None,
) -> LocalizationAdminConfig:
    own = conn is None
    if own:
        conn = admin_connect()
    else:
        ensure_admin_schema(conn)
    now = _stamp()
    supported_json = json.dumps(config.normalized_supported_ui_locales())
    conn.execute(
        """
        INSERT INTO APP_ADMIN_LOCALIZATION (
            ID, TERRITORY_ID, UI_LOCALE, SUPPORTED_UI_LOCALES, UPDATED_AT
        )
        VALUES (1, ?, ?, ?, ?)
        ON CONFLICT(ID) DO UPDATE SET
            TERRITORY_ID = excluded.TERRITORY_ID,
            UI_LOCALE = excluded.UI_LOCALE,
            SUPPORTED_UI_LOCALES = excluded.SUPPORTED_UI_LOCALES,
            UPDATED_AT = excluded.UPDATED_AT
        """,
        (config.territory_id, config.ui_locale, supported_json, now),
    )
    conn.commit()
    if own:
        conn.close()
    return LocalizationAdminConfig(
        territory_id=config.territory_id,
        ui_locale=config.ui_locale,
        supported_ui_locales=config.normalized_supported_ui_locales(),
        updated_at=now,
    )


def admin_localization_for_api(
    *,
    warehouse_territory_id: str | None,
    warehouse_seed_language: str | None = None,
) -> dict:
    admin = load_localization_admin()
    effective_tid = admin.normalized_territory_id() if admin.territory_id else None
    if not effective_tid:
        from customer360.territory.registry import DEFAULT_TERRITORY_ID

        effective_tid = warehouse_territory_id or DEFAULT_TERRITORY_ID
    profile = get_territory(effective_tid)
    locs = localization_options(profile)
    supported = resolve_supported_ui_locales(admin)
    ui = admin.ui_locale
    if ui:
        try:
            ui = admin.normalized_ui_locale(territory_id=effective_tid)
        except ValueError:
            ui = None
    if ui and ui not in supported:
        ui = None
    mismatch = bool(
        warehouse_territory_id
        and admin.territory_id
        and admin.normalized_territory_id() != warehouse_territory_id
    )
    seed_lang = warehouse_seed_language or profile.default_seed_language
    return {
        "territory_id": effective_tid,
        "admin_territory_id": admin.territory_id,
        "warehouse_territory_id": warehouse_territory_id,
        "warehouse_seed_language": seed_lang,
        "ui_locale": ui,
        "supported_ui_locales": supported,
        "territory_mismatch": mismatch,
        "available_territories": [territory_catalog_entry(p) for p in list_territories()],
        "available_languages": language_catalog(),
        "localizations": locs,
        "updated_at": admin.updated_at,
    }
