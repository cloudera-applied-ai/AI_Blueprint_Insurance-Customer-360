"""Resolve locale-aware synthetic seed bundles (LLM, cache, or profile fallback)."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from customer360.agent.json_parse import load_first_json_object
from customer360.paths import project_root
from customer360.territory.languages import (
    LANGUAGE_LABELS,
    get_foreclosure_labels,
    get_interaction_copy,
    get_language,
)
from customer360.territory.models import ForeclosureAssetLabels, InteractionCopy, TerritoryProfile

logger = logging.getLogger(__name__)

CACHE_DIR = project_root() / "data" / "seed_cache"


@dataclass(frozen=True)
class SeedMaterial:
    """Textual / geographic seed fields for a region + language pair."""

    territory_id: str
    seed_language: str
    source: str
    first_names: tuple[str, ...]
    last_names: tuple[str, ...]
    cities: tuple[tuple[str, str, int], ...]
    city_aliases: dict[str, str]
    employers: tuple[tuple[int, str], ...]
    corp_names: dict[int, str]
    funds: tuple[tuple[int, int, str], ...]
    marital_map: dict[str, str]
    customer_type_map: dict[int, str]
    interaction_copy: InteractionCopy
    foreclosure_labels: ForeclosureAssetLabels

    def canonical_cities(self) -> tuple[str, ...]:
        return tuple(c[0] for c in self.cities)


def _cache_path(territory_id: str, seed_language: str) -> Path:
    return CACHE_DIR / f"{territory_id}_{seed_language}.json"


def _aliases_for_cities(cities: tuple[tuple[str, str, int], ...], extra: dict[str, str]) -> dict[str, str]:
    out = dict(extra)
    for city, _street, _zip in cities:
        out.setdefault(city.lower(), city)
    return out


def material_from_profile(profile: TerritoryProfile, seed_language: str, *, source: str = "profile") -> SeedMaterial:
    lang = get_language(seed_language)
    return SeedMaterial(
        territory_id=profile.id,
        seed_language=lang,
        source=source,
        first_names=profile.first_names,
        last_names=profile.last_names,
        cities=profile.cities,
        city_aliases=dict(profile.known_cities_map()),
        employers=profile.employers,
        corp_names=dict(profile.corp_names),
        funds=profile.funds,
        marital_map=dict(profile.marital_map),
        customer_type_map=dict(profile.customer_type_map),
        interaction_copy=get_interaction_copy(lang),
        foreclosure_labels=get_foreclosure_labels(lang),
    )


def _parse_interaction_copy(raw: dict[str, Any]) -> InteractionCopy:
    topics: list[tuple[str, str, bool]] = []
    for item in raw.get("agent_topics") or []:
        if isinstance(item, dict):
            topics.append(
                (
                    str(item.get("title") or item.get("query") or ""),
                    str(item.get("topic") or "general"),
                    bool(item.get("resolved_default", item.get("resolved", True))),
                )
            )
        elif isinstance(item, (list, tuple)) and len(item) >= 3:
            topics.append((str(item[0]), str(item[1]), bool(item[2])))
    return InteractionCopy(
        product_searches=tuple(str(x) for x in raw.get("product_searches") or []),
        help_searches=tuple(str(x) for x in raw.get("help_searches") or []),
        agent_topics=tuple(topics),
        review_titles=tuple(str(x) for x in raw.get("review_titles") or []),
        review_detail_positive=str(raw.get("review_detail_positive") or ""),
        review_detail_negative=str(raw.get("review_detail_negative") or ""),
        agent_detail_resolved=str(raw.get("agent_detail_resolved") or ""),
        agent_detail_unresolved=str(raw.get("agent_detail_unresolved") or ""),
        web_session_detail=str(raw.get("web_session_detail") or ""),
    )


def _parse_foreclosure(raw: dict[str, Any]) -> ForeclosureAssetLabels:
    return ForeclosureAssetLabels(
        yes=str(raw.get("yes") or "Yes"),
        no=str(raw.get("no") or "No"),
        policy=str(raw.get("policy") or "Policy"),
        claim=str(raw.get("claim") or "Claim"),
    )


def _parse_cities(raw: list[Any]) -> tuple[tuple[str, str, int], ...]:
    cities: list[tuple[str, str, int]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("city") or "").strip()
        street = str(item.get("street") or item.get("street_name") or "Main Street").strip()
        postal = item.get("postal_code", item.get("zipcode", 10000))
        try:
            zipcode = int(postal)
        except (TypeError, ValueError):
            zipcode = 10000
        if name:
            cities.append((name, street, zipcode))
    return tuple(cities)


def _parse_employers(raw: list[Any], template: tuple[tuple[int, str], ...]) -> tuple[tuple[int, str], ...]:
    by_id = {num: desc for num, desc in template}
    out: list[tuple[int, str]] = []
    for item in raw:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            num, desc = int(item[0]), str(item[1])
        elif isinstance(item, dict):
            num = int(item.get("id") or item.get("employer_num") or 0)
            desc = str(item.get("name") or item.get("description") or "")
        else:
            continue
        if num in by_id and desc.strip():
            out.append((num, desc.strip()))
    if len(out) != len(template):
        return template
    return tuple(out)


def _parse_funds(raw: list[Any], template: tuple[tuple[int, int, str], ...]) -> tuple[tuple[int, int, str], ...]:
    keys = {(mng, fund_id) for mng, fund_id, _ in template}
    parsed: dict[tuple[int, int], str] = {}
    for item in raw:
        if isinstance(item, (list, tuple)) and len(item) >= 3:
            mng, fund_id, name = int(item[0]), int(item[1]), str(item[2])
        elif isinstance(item, dict):
            mng = int(item.get("mng_company_code") or item.get("mng") or 0)
            fund_id = int(item.get("fund_id") or 0)
            name = str(item.get("name") or item.get("fund_name") or "")
        else:
            continue
        if (mng, fund_id) in keys and name.strip():
            parsed[(mng, fund_id)] = name.strip()
    if len(parsed) != len(keys):
        return template
    return tuple((mng, fund_id, parsed[(mng, fund_id)]) for mng, fund_id, _ in template)


def _parse_corp_names(raw: dict[str, Any], template: dict[int, str]) -> dict[int, str]:
    out = dict(template)
    for key, val in raw.items():
        try:
            code = int(key)
        except (TypeError, ValueError):
            continue
        if code in template and str(val).strip():
            out[code] = str(val).strip()
    return out


def _parse_marital(raw: list[Any], template: dict[str, str]) -> dict[str, str]:
    out = dict(template)
    for item in raw:
        if isinstance(item, dict):
            code = str(item.get("code") or "").strip()
            label = str(item.get("label") or item.get("description") or "").strip()
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            code, label = str(item[0]).strip(), str(item[1]).strip()
        else:
            continue
        if code in template and label:
            out[code] = label
    return out


def _parse_customer_types(raw: list[Any], template: dict[int, str]) -> dict[int, str]:
    out = dict(template)
    for item in raw:
        if isinstance(item, dict):
            try:
                ctype = int(item.get("type") or item.get("customer_type") or 0)
            except (TypeError, ValueError):
                continue
            label = str(item.get("label") or item.get("description") or "").strip()
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            ctype, label = int(item[0]), str(item[1]).strip()
        else:
            continue
        if ctype in template and label:
            out[ctype] = label
    return out


def material_from_llm_json(
    profile: TerritoryProfile,
    seed_language: str,
    data: dict[str, Any],
    *,
    source: str = "llm",
) -> SeedMaterial:
    lang = get_language(seed_language)
    first_names = tuple(str(x).strip() for x in data.get("first_names") or [] if str(x).strip())
    last_names = tuple(str(x).strip() for x in data.get("last_names") or [] if str(x).strip())
    cities = _parse_cities(list(data.get("cities") or []))
    if len(first_names) < 8 or len(last_names) < 8 or len(cities) < 4:
        raise ValueError("LLM seed JSON missing minimum names or cities")

    aliases_raw = data.get("city_aliases") or {}
    extra_aliases = {str(k).lower(): str(v) for k, v in aliases_raw.items()} if isinstance(aliases_raw, dict) else {}

    employers = _parse_employers(list(data.get("employers") or []), profile.employers)
    funds = _parse_funds(list(data.get("funds") or []), profile.funds)
    corp_names = _parse_corp_names(data.get("corp_names") or {}, profile.corp_names)
    marital_map = _parse_marital(list(data.get("marital_status") or []), profile.marital_map)
    customer_type_map = _parse_customer_types(list(data.get("customer_types") or []), profile.customer_type_map)
    interaction = _parse_interaction_copy(data.get("interaction_copy") or {})
    foreclosure = _parse_foreclosure(data.get("foreclosure_labels") or {})

    if not interaction.product_searches or not interaction.help_searches:
        interaction = get_interaction_copy(lang)

    return SeedMaterial(
        territory_id=profile.id,
        seed_language=lang,
        source=source,
        first_names=first_names,
        last_names=last_names,
        cities=cities,
        city_aliases=_aliases_for_cities(cities, extra_aliases),
        employers=employers,
        corp_names=corp_names,
        funds=funds,
        marital_map=marital_map,
        customer_type_map=customer_type_map,
        interaction_copy=interaction,
        foreclosure_labels=foreclosure,
    )


def material_to_dict(material: SeedMaterial) -> dict[str, Any]:
    ic = material.interaction_copy
    fl = material.foreclosure_labels
    return {
        "territory_id": material.territory_id,
        "seed_language": material.seed_language,
        "source": material.source,
        "first_names": list(material.first_names),
        "last_names": list(material.last_names),
        "cities": [
            {"name": c, "street": s, "postal_code": z} for c, s, z in material.cities
        ],
        "city_aliases": material.city_aliases,
        "employers": [[num, desc] for num, desc in material.employers],
        "corp_names": {str(k): v for k, v in material.corp_names.items()},
        "funds": [[mng, fund_id, name] for mng, fund_id, name in material.funds],
        "marital_status": [{"code": k, "label": v} for k, v in material.marital_map.items()],
        "customer_types": [{"type": k, "label": v} for k, v in material.customer_type_map.items()],
        "interaction_copy": {
            "product_searches": list(ic.product_searches),
            "help_searches": list(ic.help_searches),
            "agent_topics": [
                {"title": t, "topic": topic, "resolved_default": resolved}
                for t, topic, resolved in ic.agent_topics
            ],
            "review_titles": list(ic.review_titles),
            "review_detail_positive": ic.review_detail_positive,
            "review_detail_negative": ic.review_detail_negative,
            "agent_detail_resolved": ic.agent_detail_resolved,
            "agent_detail_unresolved": ic.agent_detail_unresolved,
            "web_session_detail": ic.web_session_detail,
        },
        "foreclosure_labels": {
            "yes": fl.yes,
            "no": fl.no,
            "policy": fl.policy,
            "claim": fl.claim,
        },
    }


def save_material_cache(material: SeedMaterial) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(material.territory_id, material.seed_language)
    payload = material_to_dict(material)
    payload["source"] = material.source
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_material_cache(profile: TerritoryProfile, seed_language: str) -> SeedMaterial | None:
    path = _cache_path(profile.id, get_language(seed_language))
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return material_from_llm_json(profile, seed_language, data, source=str(data.get("source") or "cache"))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("Could not load seed cache %s: %s", path, exc)
        return None


def _sample_lines(values: tuple[str, ...], n: int = 4) -> str:
    return ", ".join(values[:n])


def _build_llm_prompts(profile: TerritoryProfile, seed_language: str) -> tuple[str, str]:
    lang_label = LANGUAGE_LABELS[get_language(seed_language)]
    sample_cities = [
        {"name": c, "street": s, "postal_code": z} for c, s, z in profile.cities[:3]
    ]
    sample_funds = [[mng, fund_id, name] for mng, fund_id, name in profile.funds[:3]]
    user = json.dumps(
        {
            "region_id": profile.id,
            "region_display_name": profile.display_name,
            "currency": profile.default_currency,
            "seed_language": seed_language,
            "seed_language_label": lang_label,
            "market_context": profile.llm_market_context,
            "samples": {
                "first_names": list(profile.first_names[:5]),
                "last_names": list(profile.last_names[:5]),
                "cities": sample_cities,
                "employers": [[n, d] for n, d in profile.employers],
                "corp_names": {str(k): v for k, v in profile.corp_names.items()},
                "funds": sample_funds,
                "marital_status": [{"code": k, "label": v} for k, v in profile.marital_map.items()],
                "customer_types": [{"type": k, "label": v} for k, v in profile.customer_type_map.items()],
            },
            "requirements": {
                "first_names_count": 20,
                "last_names_count": 20,
                "cities_count": 8,
                "keep_employer_ids": [n for n, _ in profile.employers],
                "keep_fund_keys": [[m, f] for m, f, _ in profile.funds],
                "keep_corp_name_keys": list(profile.corp_names.keys()),
                "keep_marital_codes": list(profile.marital_map.keys()),
                "keep_customer_type_codes": list(profile.customer_type_map.keys()),
            },
        },
        ensure_ascii=False,
        indent=2,
    )
    system = """
You generate synthetic insurance warehouse seed data as one JSON object only.
Match the geographic region (cities, names, employers) and write all human-readable strings
in the requested seed language (interaction copy, fund names, marital labels, etc.).
Keep every numeric id/key from requirements exactly; only change descriptive text.
Return valid JSON with keys:
first_names, last_names, cities, city_aliases, employers, corp_names, funds,
marital_status, customer_types, foreclosure_labels, interaction_copy.
interaction_copy must include product_searches, help_searches, agent_topics (title/topic/resolved_default),
review_titles, review_detail_positive, review_detail_negative, agent_detail_resolved,
agent_detail_unresolved, web_session_detail.
No markdown fences or commentary.
""".strip()
    return system, user


def generate_material_via_llm(profile: TerritoryProfile, seed_language: str) -> SeedMaterial:
    from customer360.llm import router as llm_router

    system, user = _build_llm_prompts(profile, seed_language)
    raw, model_id = llm_router.invoke_text(system_prompt=system, user_prompt=user, json_mode=True)
    logger.info("LLM seed material from %s for %s/%s", model_id, profile.id, seed_language)
    data = load_first_json_object(raw)
    material = material_from_llm_json(profile, seed_language, data, source="llm")
    save_material_cache(material)
    return material


def resolve_seed_material(profile: TerritoryProfile, seed_language: str) -> SeedMaterial:
    """Load seed bundle for region + language (LLM when configured, else cache/profile)."""
    lang = get_language(seed_language)
    environ = os.environ
    skip_llm = environ.get("CUSTOMER360_SEED_SKIP_LLM", "").strip().lower() in ("1", "true", "yes")
    require_llm = environ.get("CUSTOMER360_SEED_REQUIRE_LLM", "").strip().lower() in ("1", "true", "yes")
    refresh = environ.get("CUSTOMER360_SEED_LLM_REFRESH", "").strip().lower() in ("1", "true", "yes")

    if not skip_llm and not refresh:
        from customer360.llm.router import is_llm_configured

        if is_llm_configured():
            try:
                return generate_material_via_llm(profile, lang)
            except Exception as exc:
                logger.warning("LLM seed generation failed: %s", exc)
                if require_llm:
                    raise RuntimeError(f"LLM seed required but generation failed: {exc}") from exc

    if not refresh:
        cached = load_material_cache(profile, lang)
        if cached is not None:
            return cached

    if skip_llm or not require_llm:
        base = material_from_profile(profile, lang, source="profile")
        save_material_cache(base)
        return base

    raise RuntimeError("LLM seed required but provider is not configured")
