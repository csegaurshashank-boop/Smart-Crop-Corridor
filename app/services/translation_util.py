"""
app/services/translation_util.py

Automatic translation of analysis response dicts using deep-translator (Google free).
Recursively walks the response and translates all string values to the target language.
Skips keys that are obviously non-translatable (IDs, numbers, keys ending with _key, etc.)
"""
from deep_translator import GoogleTranslator  # type: ignore
from typing import Any
import logging

logger = logging.getLogger(__name__)

# Keys whose values should NEVER be translated (technical / ID fields)
_SKIP_KEYS = frozenset({
    "field_id", "crop", "season", "status_key", "icon",
    "grid_position", "health", "key", "color",
    "affected_region", "trend", "urgency", "level",
    "day",  # timeline days like "Day 1"
})

# Keys whose values are numeric only
_NUMERIC_TYPES = (int, float, bool, type(None))


def _should_skip(key: str) -> bool:
    """Return True for keys that should not be translated."""
    if key in _SKIP_KEYS:
        return True
    if key.endswith("_pct") or key.endswith("_id") or key.endswith("_key"):
        return True
    # Already a Hindi field → skip
    if key.endswith("_hi"):
        return True
    return False


def _translate_batch(texts: list[str], target: str) -> list[str]:
    """
    Translate a batch of texts in one API call for efficiency.
    Falls back to originals if translation fails.
    """
    if not texts:
        return []
    try:
        translator = GoogleTranslator(source="en", target=target)
        # deep-translator supports batch via translate_batch
        results = translator.translate_batch(texts)
        return results if results else texts
    except Exception as e:
        logger.warning(f"Translation batch failed: {e}")
        return texts


def translate_response(data: Any, target_lang: str = "hi") -> Any:
    """
    Recursively translate all string values in a dict/list to target language.
    Collects all translatable strings, batch-translates, and places them back.
    """
    if target_lang == "en":
        return data  # No translation needed

    # ── Step 1: Collect all translatable strings with their paths ─────────
    strings_to_translate: list[str] = []
    paths: list[tuple] = []  # each entry is a tuple of keys/indices to reach the value

    def _collect(obj: Any, path: tuple) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if _should_skip(k):
                    continue
                _collect(v, path + (k,))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _collect(v, path + (i,))
        elif isinstance(obj, str) and len(obj) > 1:
            # Only translate non-trivial strings (skip emojis-only, single chars)
            stripped = obj.strip()
            # Skip strings that are just emojis or very short
            if stripped and any(c.isalpha() for c in stripped):
                strings_to_translate.append(obj)
                paths.append(path)

    _collect(data, ())

    if not strings_to_translate:
        return data

    # ── Step 2: Batch translate ───────────────────────────────────────────
    # Split into chunks of 50 to avoid API limits
    chunk_size = 50
    translated_all: list[str] = []
    for i in range(0, len(strings_to_translate), chunk_size):
        chunk = list(strings_to_translate[i : i + chunk_size])  # type: ignore[index]
        translated_chunk = _translate_batch(chunk, target_lang)
        translated_all.extend(translated_chunk)

    # ── Step 3: Place translated strings back ─────────────────────────────
    def _set_value(obj: Any, path: tuple, value: str) -> None:
        for step in tuple(path[:-1]):  # type: ignore[index]
            obj = obj[step]
        obj[path[-1]] = value

    for path, translated in zip(paths, translated_all):
        try:
            _set_value(data, path, translated)
        except (KeyError, IndexError, TypeError):
            pass  # Skip if path is invalid

    return data
