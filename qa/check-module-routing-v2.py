#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from brand import (  # noqa: E402
    AUDIENCES,
    DEFAULT_MODULE_ID,
    LOCALES,
    MODULE_IDS,
    RESOURCE_SEGMENTS,
    breadcrumb_model,
    canonical_url,
    hreflang_urls,
    page_dir,
    relative_page,
    shell,
)

SLUGS = {
    "ocupado-productivo": {
        "es": "02-de-ocupado-a-productivo",
        "en": "02-from-busy-to-productive",
        "pt": "02-de-ocupado-a-produtivo",
    },
    "trabajo-amplificado": {
        "es": "03-trabajo-amplificado",
        "en": "03-amplified-work",
        "pt": "03-trabalho-amplificado",
    },
    "trabajo-agentico": {
        "es": "04-trabajo-agentico",
        "en": "04-agentic-work",
        "pt": "04-trabalho-agentico",
    },
}


def expected_route(locale: str, audience: str, page: str, module_id: str) -> str:
    parts = [] if locale == "es" else [locale]
    if audience == "empresa":
        parts.append("empresa")
    parts.extend([
        "modules" if locale == "en" else "modulos",
        SLUGS[module_id][locale],
        RESOURCE_SEGMENTS[page],
    ])
    return "/".join(parts)


# [EVIDENCE:MODULE_ROUTE_MATRIX] Exact localized M2-M4 routes, including empresa placement.
route_count = 0
for module_id in MODULE_IDS[1:]:
    for locale in LOCALES:
        for audience in AUDIENCES:
            for page in RESOURCE_SEGMENTS:
                wanted = expected_route(locale, audience, page, module_id)
                actual = page_dir(locale, audience, page, module_id)
                if actual != wanted:
                    raise AssertionError(f"MODULE_ROUTE_MISMATCH:{module_id}:{locale}:{audience}:{page}:{actual}")
                if canonical_url(module_id, page, locale, audience) != f"https://conoce.metodologia.info/{wanted}/":
                    raise AssertionError("MODULE_CANONICAL_MISMATCH")
                route_count += 1

# [EVIDENCE:M1_BACKWARD_COMPATIBILITY] Default and explicit M1 retain the original flat routes.
for locale in LOCALES:
    for audience in AUDIENCES:
        for page in RESOURCE_SEGMENTS:
            implicit = page_dir(locale, audience, page)
            explicit = page_dir(locale, audience, page, DEFAULT_MODULE_ID)
            prefix = ([] if locale == "es" else [locale]) + (["empresa"] if audience == "empresa" else [])
            wanted = "/".join(prefix + [page])
            if implicit != explicit or implicit != wanted:
                raise AssertionError(f"M1_FLAT_ROUTE_DRIFT:{locale}:{audience}:{page}")

# [EVIDENCE:TOGGLE_AND_HREFLANG_PARITY] Locale/audience changes stay on the same module and resource.
toggle_count = 0
for module_id in MODULE_IDS[1:]:
    for locale in LOCALES:
        for audience in AUDIENCES:
            page = "deck"
            rendered = shell(locale, audience, page, module_id)
            matrix_match = re.search(r'data-variant-links="([^"]+)"', rendered["controls"])
            if not matrix_match:
                raise AssertionError("MODULE_TOGGLE_MATRIX_MISSING")
            matrix = json.loads(html.unescape(matrix_match.group(1)))
            for target_locale in LOCALES:
                for target_audience in AUDIENCES:
                    wanted = relative_page(
                        locale, audience, page,
                        target_locale, target_audience, page,
                        module_id, module_id,
                    )
                    if matrix[target_locale][target_audience] != wanted:
                        raise AssertionError("MODULE_TOGGLE_ROUTE_MISMATCH")
                    toggle_count += 1
            alternates = hreflang_urls(module_id, page, locale, audience)
            if set(alternates) != {*LOCALES, "x-default"} or alternates["x-default"] != alternates["es"]:
                raise AssertionError("MODULE_HREFLANG_MATRIX_MISMATCH")

# [EVIDENCE:HEADER_CATALOG] One catalog link plus four stable module anchors; no 16-resource expansion.
header = shell("es", "persona", "workbook", "trabajo-amplificado")["header"]
anchors = re.findall(r'data-conoce-module-link data-module-id="([^"]+)"', header)
if anchors != list(MODULE_IDS):
    raise AssertionError(f"MODULE_HEADER_LINKS_MISMATCH:{anchors}")
if header.count("data-conoce-resource-overview") != 1 or "data-conoce-resource-link" in header:
    raise AssertionError("MODULE_HEADER_CATALOG_SHAPE_INVALID")
for order in range(1, 5):
    if f"#module-{order:02d}" not in header:
        raise AssertionError("MODULE_HEADER_ANCHOR_MISSING")

# [EVIDENCE:NESTED_BREADCRUMBS] Nested resources add the module tier; M1 remains three levels.
for module_id in MODULE_IDS[1:]:
    items = breadcrumb_model(module_id, "prompts", "pt", "empresa")
    if [item["id"] for item in items] != ["home", "resources_overview", module_id, "prompts"]:
        raise AssertionError("MODULE_BREADCRUMB_HIERARCHY_MISMATCH")
    if not items[2]["href"].endswith(f"#module-0{MODULE_IDS.index(module_id) + 1}"):
        raise AssertionError("MODULE_BREADCRUMB_ANCHOR_MISMATCH")
if [item["id"] for item in breadcrumb_model(DEFAULT_MODULE_ID, "prompts", "es", "persona")] != [
    "home", "resources_overview", "prompts"
]:
    raise AssertionError("M1_BREADCRUMB_DRIFT")

print(
    "MODULE_ROUTING_V2_OK "
    f"routes={route_count} toggles={toggle_count} locales={len(LOCALES)} audiences={len(AUDIENCES)} "
    "header=catalog+4-modules breadcrumbs=nested-4-level m1=flat"
)
