#!/usr/bin/env python3
"""Fail-closed gate for the M2-M4 editorial-depth expansion.

The imported payloads remain immutable records.  This gate validates their
ID-bound depth overlays, then verifies the 54 global/M1 pages against the
explicit approved golden baseline.
"""

from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import math
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DIST = ROOT / "dist"
PROFILE_PATH = SRC / "modules" / "module-depth-profile-v1.json"
CURRICULUM_PATH = SRC / "curriculum-spec-v2.json"
GOLDEN_PATH = ROOT / "qa" / "goldens" / "module-depth-m1-global-v1.json"

LOCALES = ("es", "en", "pt")
AUDIENCES = ("persona", "empresa")
EXPECTED_VARIANTS = {(locale, audience) for locale in LOCALES for audience in AUDIENCES}
EXPECTED_MODULES = {
    "module-02-de-ocupado-a-productivo",
    "module-03-trabajar-amplificado",
    "module-04-trabajo-agentico",
}
RESOURCE_NAMES = ("masterclass", "workbook", "playbook", "prompts")
EXPECTED_HTML = 126
EXPECTED_NESTED_HTML = 72

# Deliberately narrow patterns: declarations that forbid a claim are allowed,
# but an affirmative occurrence in authored depth copy fails closed.
PROHIBITED_CLAIMS = {
    "10x": re.compile(r"(?<![\w])10\s*[x\u00d7](?![\w])", re.IGNORECASE),
    "percentage": re.compile(r"(?<![\w])\d+(?:[.,]\d+)?\s*%"),
    "neuroscience": re.compile(
        r"\b(?:neuro(?:ciencia|science|ci[eê]ncia|cient\w*)|brain|cerebro|c[eé]rebro|"
        r"neuronal|dopamin\w*)\b",
        re.IGNORECASE,
    ),
}
NEGATION_MARKERS = re.compile(
    r"\b(?:no|not|never|without|do not|does not|must not|n[aã]o|sem|"
    r"prohibid\w*|forbid\w*|excluded?|exclu[ií]d\w*|reject\w*|rechaz\w*)\b",
    re.IGNORECASE,
)

# Obvious, discriminative residues only.  Shared cognates and product names are
# intentionally absent to keep this signal useful rather than noisy.
EN_SPANISH = re.compile(
    r"[\u00bf\u00a1\u00f1]|\b(?:qu[eé]|c[oó]mo|cu[aá]ndo|d[oó]nde|siguiente|"
    r"entregable|aprendizaje|fuentes|trabajo|equipo|t[uú]|usted(?:es)?|"
    r"debe|puede|sin|decisión|revisión|acción)\b",
    re.IGNORECASE,
)
PT_SPANISH = re.compile(
    r"[\u00bf\u00a1\u00f1]|\b(?:qué|cómo|cuándo|dónde|siguiente|"
    r"entregable|aprendizaje|fuentes|trabajo|equipo|tú|usted(?:es)?|"
    r"debe|puede|sin|decisión|revisión|acción)\b",
    re.IGNORECASE,
)

SEMANTIC_SKIP_KEYS = {
    "id",
    "locale",
    "audience",
    "phase",
    "level",
    "prompt_ref",
    "library_ref",
    "authority_refs",
    "concept_ids",
    "moment_ids",
    "next",
}
REPETITION_SKIP_KEYS = SEMANTIC_SKIP_KEYS | {"guardrails", "limits"}

DEPTH_MARKERS = {
    "masterclass": ("masterclass-depth", "module-depth-disclosure"),
    "workbook": ("workbook-step-depth", "module-depth-orientation", "module-depth-rubric"),
    "playbook": ("playbook-depth", "module-depth-reference", "module-depth-closing"),
    "prompts": ("prompt-contract-depth", "module-depth-graph"),
}


class GateFailure(AssertionError):
    """Raised with stable evidence codes when any depth invariant fails."""


class ReadableTextParser(HTMLParser):
    """Collect visible text plus accessibility names, excluding runtime data."""

    ACCESSIBLE_ATTRS = {"alt", "aria-label", "placeholder", "title"}
    SKIPPED_TAGS = {"script", "style"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self.fragments: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIPPED_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        for key, value in attrs:
            if key in self.ACCESSIBLE_ATTRS and value:
                self.fragments.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIPPED_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and data.strip():
            self.fragments.append(data)


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise GateFailure(f"EDITORIAL_DEPTH_FILE_MISSING:{path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GateFailure(f"EDITORIAL_DEPTH_JSON_OBJECT_REQUIRED:{path.relative_to(ROOT)}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def under(root: Path, relative: str, evidence: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as error:
        raise GateFailure(f"{evidence}:PATH_ESCAPE:{relative}") from error
    return candidate


def import_depth_validator() -> Any:
    path = ROOT / "scripts" / "module_depth.py"
    spec = importlib.util.spec_from_file_location("nivel0_module_depth", path)
    if not spec or not spec.loader:
        raise GateFailure("EDITORIAL_DEPTH_VALIDATOR_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def walk_strings(
    value: Any,
    *,
    parent_key: str = "",
    skip_keys: set[str] | frozenset[str] = SEMANTIC_SKIP_KEYS,
) -> Iterable[str]:
    if isinstance(value, str):
        text = " ".join(value.split())
        if text:
            yield text
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key not in skip_keys:
                yield from walk_strings(child, parent_key=key, skip_keys=skip_keys)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for child in value:
            yield from walk_strings(child, parent_key=parent_key, skip_keys=skip_keys)


def normalized_phrase(value: str) -> str:
    value = unicodedata.normalize("NFKC", html.unescape(value)).casefold()
    value = re.sub(r"\s+", " ", value).strip()
    return value


def lexical_words(value: str) -> list[str]:
    return re.findall(r"[^\W\d_]+(?:[-'][^\W\d_]+)*", value, re.UNICODE)


def resource_unit_count(resource: str, value: Mapping[str, Any]) -> int:
    if resource == "masterclass":
        return len(value.get("moments", []))
    if resource == "workbook":
        steps = sum(len(route.get("steps", [])) for route in value.get("routes", []))
        return steps + len(value.get("preparation_prompts", []))
    if resource == "playbook":
        return len(value.get("chapters", []))
    if resource == "prompts":
        return len(value.get("items", []))
    raise GateFailure(f"EDITORIAL_DEPTH_UNKNOWN_RESOURCE:{resource}")


def repeated_phrases(resource: str, value: Mapping[str, Any]) -> list[tuple[str, int, int]]:
    """Return exact boilerplate repeated across too many learning units.

    Short labels and fragments are excluded.  A substantive phrase may repeat
    in at most 45% of a surface, with an absolute floor of three occurrences.
    This allows a small invariant reminder without letting it replace authored
    explanations, criteria or examples.
    """

    units = resource_unit_count(resource, value)
    threshold = max(3, math.ceil(units * 0.45))
    phrases = [
        normalized_phrase(text)
        for text in walk_strings(value, skip_keys=REPETITION_SKIP_KEYS)
        if len(text) >= 28 and len(lexical_words(text)) >= 6
    ]
    return [
        (phrase, count, threshold)
        for phrase, count in Counter(phrases).most_common()
        if count > threshold
    ]


def affirmative_claims(overlay: Mapping[str, Any]) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for text in walk_strings(overlay):
        for name, pattern in PROHIBITED_CLAIMS.items():
            if pattern.search(text) and not NEGATION_MARKERS.search(text):
                findings.append((name, text))
    return findings


def enormous_tokens(texts: Iterable[str], limit: int = 120) -> list[str]:
    findings: list[str] = []
    for text in texts:
        for token in re.findall(r"\S+", text):
            stripped = token.strip(".,;:!?()[]{}<>\"'")
            if len(stripped) <= limit:
                continue
            if stripped.startswith(("http://", "https://", "data:")):
                continue
            if re.fullmatch(r"[a-f0-9]{64}", stripped, re.IGNORECASE):
                continue
            findings.append(stripped[:80])
    return findings


def audience_similarity(persona: Mapping[str, Any], empresa: Mapping[str, Any]) -> float:
    def tokens(value: Mapping[str, Any]) -> set[str]:
        corpus = " ".join(walk_strings(value)).casefold()
        return {
            token
            for token in re.findall(r"[^\W\d_]{4,}", corpus, re.UNICODE)
            if token not in {"para", "with", "from", "that", "this", "como", "com", "uma", "the"}
        }

    left, right = tokens(persona), tokens(empresa)
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def validate_overlay_sources() -> tuple[dict[tuple[str, str, str], Mapping[str, Any]], list[str]]:
    profile = load_json(PROFILE_PATH)
    curriculum = load_json(CURRICULUM_PATH)
    validator = import_depth_validator()
    errors: list[str] = []
    indexed: dict[tuple[str, str, str], Mapping[str, Any]] = {}

    if profile.get("schema_version") != "module-depth-profile-v1":
        errors.append("EDITORIAL_DEPTH_PROFILE_SCHEMA")
    policy = profile.get("variant_policy", {})
    if (
        policy.get("exact_variants") != 6
        or tuple(policy.get("locales", [])) != LOCALES
        or tuple(policy.get("audiences", [])) != AUDIENCES
        or policy.get("fallback_allowed") is not False
    ):
        errors.append("EDITORIAL_DEPTH_PROFILE_VARIANTS")

    classes = curriculum.get("classes", [])
    imported = [item for item in classes if item.get("module_id")]
    if {item.get("module_id") for item in imported} != EXPECTED_MODULES or len(imported) != 3:
        errors.append("EDITORIAL_DEPTH_CURRICULUM_MODULES")
        return indexed, errors

    for item in imported:
        module_id = item["module_id"]
        content = item.get("content", {})
        depth = item.get("depth_overlay", {})
        if set(depth) != {"ref", "sha256"}:
            errors.append(f"EDITORIAL_DEPTH_BINDING_MISSING:{module_id}")
            continue
        base_path = under(SRC, content.get("ref", ""), "EDITORIAL_DEPTH_BASE")
        overlay_path = under(SRC, depth.get("ref", ""), "EDITORIAL_DEPTH_OVERLAY")
        if not base_path.is_file() or sha256(base_path) != content.get("sha256"):
            errors.append(f"EDITORIAL_DEPTH_BASE_HASH:{module_id}")
            continue
        if not overlay_path.is_file() or sha256(overlay_path) != depth.get("sha256"):
            errors.append(f"EDITORIAL_DEPTH_OVERLAY_HASH:{module_id}")
            continue
        base = load_json(base_path)
        overlay = load_json(overlay_path)
        try:
            variants = validator.validate_depth_overlay(profile, overlay, base, content["sha256"])
        except Exception as error:  # Contract error class belongs to the loaded module.
            errors.append(f"EDITORIAL_DEPTH_CONTRACT:{module_id}:{error}")
            continue
        if set(variants) != EXPECTED_VARIANTS or len(variants) != 6:
            errors.append(f"EDITORIAL_DEPTH_VARIANTS:{module_id}")
            continue

        concept_claims = affirmative_claims({"concepts": overlay.get("concepts", [])})
        if concept_claims:
            errors.append(
                f"EDITORIAL_DEPTH_CONCEPT_CLAIM:{module_id}:"
                f"{concept_claims[0][0]}:{concept_claims[0][1][:100]}"
            )
        concept_tokens = enormous_tokens(walk_strings({"concepts": overlay.get("concepts", [])}))
        if concept_tokens:
            errors.append(f"EDITORIAL_DEPTH_CONCEPT_LONG_TOKEN:{module_id}:{concept_tokens[0]}")
        for concept in overlay.get("concepts", []):
            for locale in ("en", "pt"):
                residue = EN_SPANISH if locale == "en" else PT_SPANISH
                localized = [concept.get("title", {}).get(locale, ""), concept.get("summary", {}).get(locale, "")]
                match = next(
                    ((residue.search(text), text) for text in localized if residue.search(text)),
                    None,
                )
                if match:
                    found, text = match
                    errors.append(
                        f"EDITORIAL_DEPTH_CONCEPT_LANGUAGE_RESIDUE:{module_id}:{locale}:"
                        f"{found.group(0)}:{text[:100]}"
                    )

        for locale, audience in sorted(EXPECTED_VARIANTS):
            variant = variants[(locale, audience)]
            indexed[(module_id, locale, audience)] = variant
            claims = affirmative_claims(variant)
            if claims:
                errors.append(
                    f"EDITORIAL_DEPTH_PROHIBITED_CLAIM:{module_id}:{locale}:{audience}:"
                    f"{claims[0][0]}:{claims[0][1][:100]}"
                )
            huge = enormous_tokens(walk_strings(variant))
            if huge:
                errors.append(
                    f"EDITORIAL_DEPTH_LONG_TOKEN:{module_id}:{locale}:{audience}:{huge[0]}"
                )
            residue = EN_SPANISH if locale == "en" else PT_SPANISH if locale == "pt" else None
            if residue:
                for text in walk_strings(variant):
                    match = residue.search(text)
                    if match:
                        errors.append(
                            f"EDITORIAL_DEPTH_LANGUAGE_RESIDUE:{module_id}:{locale}:{audience}:"
                            f"{match.group(0)}:{text[:100]}"
                        )
                        break
            for resource in RESOURCE_NAMES:
                repeated = repeated_phrases(resource, variant[resource])
                if repeated:
                    phrase, count, limit = repeated[0]
                    errors.append(
                        f"EDITORIAL_DEPTH_BOILERPLATE:{module_id}:{locale}:{audience}:"
                        f"{resource}:{count}>{limit}:{phrase[:100]}"
                    )

        for locale in LOCALES:
            persona = variants[(locale, "persona")]
            empresa = variants[(locale, "empresa")]
            similarity = audience_similarity(persona, empresa)
            if similarity >= 0.96:
                errors.append(
                    f"EDITORIAL_DEPTH_AUDIENCE_NEAR_CLONE:{module_id}:{locale}:{similarity:.3f}"
                )

    return indexed, errors


def readable_fragments(markup: str) -> list[str]:
    parser = ReadableTextParser()
    parser.feed(markup)
    return [" ".join(fragment.split()) for fragment in parser.fragments if fragment.strip()]


def validate_m1_global_goldens() -> list[str]:
    errors: list[str] = []
    golden = load_json(GOLDEN_PATH)
    expected = golden.get("html_sha256", {})
    if (
        golden.get("schema_version") != "module-depth-m1-global-golden-v1"
        or golden.get("expected_pages") != 54
        or not isinstance(expected, dict)
        or len(expected) != 54
    ):
        return ["EDITORIAL_DEPTH_GOLDEN_CONTRACT"]
    for relative, expected_hash in sorted(expected.items()):
        page = under(DIST, relative, "EDITORIAL_DEPTH_GOLDEN")
        if not page.is_file():
            errors.append(f"EDITORIAL_DEPTH_GOLDEN_MISSING:{relative}")
        elif sha256(page) != expected_hash:
            errors.append(f"EDITORIAL_DEPTH_M1_GLOBAL_DRIFT:{relative}")
    return errors


def validate_rendered_site(
    variants: Mapping[tuple[str, str, str], Mapping[str, Any]],
) -> list[str]:
    errors: list[str] = []
    pages = sorted(DIST.rglob("index.html"))
    if len(pages) != EXPECTED_HTML:
        return [f"EDITORIAL_DEPTH_HTML_COUNT:{len(pages)}!={EXPECTED_HTML}"]

    nested: list[tuple[Path, str, str, str, str]] = []
    for page in pages:
        markup = page.read_text(encoding="utf-8")
        main_match = re.search(
            r'<main\b[^>]*data-module-id="(module-0[234]-[^"]+)"[^>]*'
            r'data-module-resource="(masterclass|workbook|playbook|prompts)"[^>]*'
            r'data-locale="(es|en|pt)"[^>]*data-audience="(persona|empresa)"',
            markup,
        )
        if main_match:
            nested.append((page, *main_match.groups()))
    if len(nested) != EXPECTED_NESTED_HTML:
        return [f"EDITORIAL_DEPTH_NESTED_COUNT:{len(nested)}!={EXPECTED_NESTED_HTML}"]

    rendered_keys: set[tuple[str, str, str, str]] = set()
    for page, module_id, resource, locale, audience in nested:
        relative = page.relative_to(DIST)
        markup = page.read_text(encoding="utf-8")
        key = (module_id, locale, audience)
        if key not in variants:
            errors.append(f"EDITORIAL_DEPTH_RENDERED_VARIANT_UNKNOWN:{relative}")
            continue
        rendered_key = (module_id, locale, audience, resource)
        if rendered_key in rendered_keys:
            errors.append(f"EDITORIAL_DEPTH_RENDERED_DUPLICATE:{rendered_key}")
        rendered_keys.add(rendered_key)
        for marker in DEPTH_MARKERS[resource]:
            if marker not in markup:
                errors.append(f"EDITORIAL_DEPTH_MARKER_MISSING:{relative}:{marker}")

        fragments = readable_fragments(markup)
        huge = enormous_tokens(fragments)
        if huge:
            errors.append(f"EDITORIAL_DEPTH_RENDERED_LONG_TOKEN:{relative}:{huge[0]}")
        residue = EN_SPANISH if locale == "en" else PT_SPANISH if locale == "pt" else None
        if residue:
            for fragment in fragments:
                match = residue.search(fragment)
                if match:
                    errors.append(
                        f"EDITORIAL_DEPTH_RENDERED_LANGUAGE_RESIDUE:{relative}:"
                        f"{match.group(0)}:{fragment[:100]}"
                    )
                    break

    expected_keys = {
        (module_id, locale, audience, resource)
        for module_id in EXPECTED_MODULES
        for locale, audience in EXPECTED_VARIANTS
        for resource in RESOURCE_NAMES
    }
    if rendered_keys != expected_keys:
        missing = sorted(expected_keys - rendered_keys)
        extra = sorted(rendered_keys - expected_keys)
        errors.append(f"EDITORIAL_DEPTH_RENDERED_MATRIX:missing={missing[:2]} extra={extra[:2]}")
    return errors


def main() -> None:
    variants, errors = validate_overlay_sources()
    errors.extend(validate_m1_global_goldens())
    errors.extend(validate_rendered_site(variants))
    if errors:
        preview = "\n".join(f"- {error}" for error in errors[:30])
        remainder = len(errors) - min(len(errors), 30)
        if remainder:
            preview += f"\n- ... {remainder} additional failure(s)"
        raise GateFailure(f"EDITORIAL_DEPTH_V1_FAILED ({len(errors)})\n{preview}")
    print(
        "[EVIDENCE:EDITORIAL_DEPTH_V1] EDITORIAL_DEPTH_V1_OK "
        "modules=3 variants=18 resources=72 html=126 preserved_m1_global=54 "
        "state_ceiling=RENDERED_DRAFT publication=false"
    )


if __name__ == "__main__":
    main()
