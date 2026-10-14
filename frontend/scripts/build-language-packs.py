#!/usr/bin/env python3
"""Build fr.json, es.json, and ar.json from en.json (with rate-limited translation)."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1] / "src" / "locales"

try:
    from deep_translator import MyMemoryTranslator
except ImportError:
    MyMemoryTranslator = None  # type: ignore

MYMEMORY_LOCALE = {
    "fr": ("en-GB", "fr-FR"),
    "es": ("en-GB", "es-ES"),
    "ar": ("en-GB", "ar-SA"),
}

BATCH_SIZE = 18
BATCH_PAUSE_SEC = 1.25

# Keep product / API tokens in English across locales.
SKIP_SUBSTRINGS = (
    "Amazon Bedrock",
    "PrivateAI",
    "FastAPI",
    "SQLite",
    "Cloudera",
    "Customer 360",
    "Insurance Customer 360",
    "npm",
    "uvicorn",
    "python3",
    "APP_",
    "DWH_",
    "CDSW_",
    "CUSTOMER360_",
    "AWS",
)


def deep_merge(base: dict, patch: dict) -> dict:
    for key, val in patch.items():
        if key in base and isinstance(base[key], dict) and isinstance(val, dict):
            deep_merge(base[key], val)
        else:
            base[key] = val
    return base


def collect_strings(node: Any, prefix: str = "") -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for key, val in node.items():
            path = f"{prefix}.{key}" if prefix else key
            out.extend(collect_strings(val, path))
    elif isinstance(node, str):
        out.append((prefix, node))
    return out


def apply_strings(node: Any, mapping: dict[str, str], prefix: str = "") -> Any:
    if isinstance(node, dict):
        return {k: apply_strings(v, mapping, f"{prefix}.{k}" if prefix else k) for k, v in node.items()}
    if isinstance(node, str):
        return mapping.get(prefix, node)
    return node


def should_skip_translation(text: str) -> bool:
    if not text or not text.strip():
        return True
    if any(token in text for token in SKIP_SUBSTRINGS):
        return True
    # Mostly code paths / env var names
    if re.fullmatch(r"[\w./\-_{}]+", text) and ("_" in text or "/" in text or text.isupper()):
        return True
    return False


def protect_placeholders(text: str) -> tuple[str, list[str]]:
    protected: list[str] = []

    def repl(match: re.Match[str]) -> str:
        protected.append(match.group(0))
        return f"__PH{len(protected) - 1}__"

    work = re.sub(r"\{\{[^}]+\}\}", repl, text)
    return work, protected


def restore_placeholders(text: str, protected: list[str]) -> str:
    out = text
    for idx, token in enumerate(protected):
        out = out.replace(f"__PH{idx}__", token)
    return out


def cache_path(lang: str) -> Path:
    return ROOT / f".translate-cache-{lang}.json"


def load_cache(lang: str) -> dict[str, str]:
    path = cache_path(lang)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_cache(lang: str, mapping: dict[str, str]) -> None:
    cache_path(lang).write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def translate_batch_mymemory(texts: list[str], lang_code: str) -> list[str]:
    if MyMemoryTranslator is None:
        return texts
    src, tgt = MYMEMORY_LOCALE[lang_code]
    translator = MyMemoryTranslator(source=src, target=tgt)
    prepared: list[tuple[str, list[str]]] = []
    for text in texts:
        work, protected = protect_placeholders(text)
        prepared.append((work, protected))
    raw = translator.translate_batch([p[0] for p in prepared])
    out: list[str] = []
    for (work, protected), translated in zip(prepared, raw, strict=True):
        out.append(restore_placeholders(translated, protected))
    return out


def build_lang(base: dict, lang_code: str) -> dict:
    pairs = collect_strings(base)
    mapping = load_cache(lang_code)
    pending: list[tuple[str, str]] = []
    for path, text in pairs:
        if path in mapping:
            continue
        if should_skip_translation(text):
            mapping[path] = text
            continue
        pending.append((path, text))

    total = len(pending)
    for start in range(0, total, BATCH_SIZE):
        chunk = pending[start : start + BATCH_SIZE]
        texts = [text for _, text in chunk]
        try:
            translated = translate_batch_mymemory(texts, lang_code)
        except Exception as exc:
            print(f"  batch {start}-{start + len(chunk)} failed: {exc}", flush=True)
            translated = texts
        for (path, original), result in zip(chunk, translated, strict=True):
            mapping[path] = result if result else original
        save_cache(lang_code, mapping)
        done = min(start + len(chunk), total)
        print(f"  {lang_code}: {done}/{total} strings", flush=True)
        if start + BATCH_SIZE < total:
            time.sleep(BATCH_PAUSE_SEC)

    return apply_strings(json.loads(json.dumps(base)), mapping)


def merge_patches(lang: str, data: dict) -> dict:
    for patch_name in (
        f"i18n-patch-{lang}.json",
        f"i18n-patch-{lang}-titles.json",
        f"i18n-patch-a11y-{lang}.json",
        f"{lang}-patch.json",
    ):
        patch_path = ROOT / patch_name
        if patch_path.is_file():
            patch = json.loads(patch_path.read_text(encoding="utf-8"))
            deep_merge(data, patch)
    return data


def main() -> None:
    import os
    import sys

    en_path = ROOT / "en.json"
    en = json.loads(en_path.read_text(encoding="utf-8"))
    en = merge_patches("en", en)
    if os.environ.get("CUSTOMER360_I18N_REFRESH_EN", "").strip().lower() in ("1", "true", "yes"):
        en_path.write_text(json.dumps(en, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Refreshed en.json from patches")

    all_targets = ("fr", "es", "ar")
    only = os.environ.get("CUSTOMER360_I18N_LANGS", "").strip()
    if only:
        wanted = {c.strip().lower() for c in only.split(",") if c.strip()}
        targets = tuple(t for t in all_targets if t in wanted)
        if not targets:
            print(f"No matching languages in CUSTOMER360_I18N_LANGS={only!r}", file=sys.stderr)
            sys.exit(1)
    else:
        targets = all_targets

    skip_translate = os.environ.get("CUSTOMER360_I18N_SKIP_TRANSLATE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if MyMemoryTranslator is None or skip_translate:
        reason = "skip flag" if skip_translate else "deep-translator not installed"
        print(f"{reason}; copying en structure with patch overlays only.")
        for lang in targets:
            pack = merge_patches(lang, json.loads(json.dumps(en)))
            out = ROOT / f"{lang}.json"
            out.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Wrote {out.name} (overlay-only)")
        return

    for lang in targets:
        print(f"Translating {lang}…", flush=True)
        pack = build_lang(en, lang)
        pack = merge_patches(lang, pack)
        out = ROOT / f"{lang}.json"
        out.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {out.name}", flush=True)


if __name__ == "__main__":
    main()
