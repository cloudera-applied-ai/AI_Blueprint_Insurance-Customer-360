"""Active territory profile, seed language, and resolved seed material during seeding."""

from __future__ import annotations

from customer360.seed_material import SeedMaterial
from customer360.territory.models import TerritoryProfile

_active: TerritoryProfile | None = None
_seed_language: str | None = None
_material: SeedMaterial | None = None


def set_active_territory(profile: TerritoryProfile) -> None:
    global _active
    _active = profile


def get_active_territory() -> TerritoryProfile | None:
    return _active


def require_territory() -> TerritoryProfile:
    if _active is None:
        from customer360.territory import get_territory, resolve_territory_id

        profile = get_territory(resolve_territory_id())
        set_active_territory(profile)
    return _active


def set_seed_language(language_id: str) -> None:
    global _seed_language
    _seed_language = language_id


def require_seed_language() -> str:
    if _seed_language is None:
        from customer360.territory.languages import resolve_seed_language

        return resolve_seed_language(territory_id=require_territory().id)
    return _seed_language


def set_seed_material(material: SeedMaterial) -> None:
    global _material
    _material = material


def require_seed_material() -> SeedMaterial:
    if _material is None:
        from customer360.seed_material import resolve_seed_material

        profile = require_territory()
        lang = require_seed_language()
        material = resolve_seed_material(profile, lang)
        set_seed_material(material)
        return material
    return _material


def reset_seed_context() -> None:
    global _active, _seed_language, _material
    _active = None
    _seed_language = None
    _material = None
