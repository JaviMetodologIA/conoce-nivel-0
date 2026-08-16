#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
sys.path.insert(0, str(ROOT / "scripts"))

from brand import (  # noqa: E402
    AUDIENCES,
    EDITORIAL_PAGES,
    EDITORIAL_SPEC,
    LOCALES,
    PAGES,
    canonical_self,
    page_dir,
    validate_editorial_document,
    validate_editorial_spec,
)

PUBLIC = "https://conoce.metodologia.info/"


def reject(code: str, mutate) -> None:
    candidate = copy.deepcopy(source)
    mutate(candidate)
    if code != "EDITORIAL_SITEMAP_BINDING_INVALID":
        candidate["self_sha256"] = canonical_self(candidate, "self_sha256")
    try:
        validate_editorial_document(candidate)
    except RuntimeError as error:
        if str(error) != code:
            raise AssertionError(f"Expected {code}, got {error}") from error
    else:
        raise AssertionError(f"Mutation passed unexpectedly: {code}")


source = json.loads(EDITORIAL_SPEC.read_text(encoding="utf-8"))
validate_editorial_spec()


def copy_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from copy_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from copy_strings(item)


# [METODOLOGIA] The editorial contract must remain useful to a cold reader and
# neutral about future participation. Slugs and chrome labels are intentionally
# outside this copy-only oracle.
productive_copy = "\n".join(copy_strings({
    "copy": source["copy"],
    "audience_copy": source["audience_copy"],
}))
forbidden_copy = re.compile(
    r"\b(?:cohort(?:e|s)?|cohortes|turmas?|fechas?|dates?|datas?|"
    r"capacidades?|cupos?|places?|vagas?|inscripci[oó]n(?:es)?|"
    r"enrolments?|enrollments?|precios?|prices?|pagos?|payments?|"
    r"licencias?|licen[cs]es?|garantiz(?:a|ado|ada|amos|ed)|"
    r"16\s+(?:semanas?|weeks?))\b|1\s*(?:→|->|a|to)\s*4",
    re.IGNORECASE,
)
match = forbidden_copy.search(productive_copy)
if match:
    raise AssertionError(f"EDITORIAL_COPY_UNVERIFIED_CLAIM:{match.group(0)}")

fluency_markers = {
    "es": ("fluida", "falsa", "no técnico"),
    "en": ("fluent", "false", "non-technical"),
    "pt": ("fluente", "falsa", "não técnico"),
}
functional_terms = {
    "workbook-resource": "workbook",
    "playbook-resource": "playbook",
}
locale_corpora = {}
for locale in LOCALES:
    pages = source["copy"][locale]
    locale_corpora[locale] = " ".join(copy_strings(pages)).casefold()
    level0 = pages["level0"]
    level0_text = " ".join(copy_strings(level0)).casefold()
    for marker in fluency_markers[locale]:
        if marker.casefold() not in level0_text:
            raise AssertionError(f"EDITORIAL_COPY_COLD_START_MISSING:{locale}:{marker}")
    if "método" not in level0_text and "method" not in level0_text and "metodo" not in level0_text:
        raise AssertionError(f"EDITORIAL_COPY_METHOD_MISSING:{locale}")
    how_text = " ".join(copy_strings(pages["how"])).casefold()
    if "90" not in how_text or "120" not in how_text:
        raise AssertionError(f"EDITORIAL_COPY_DURATION_MISSING:{locale}")
    if not any(marker in how_text for marker in ("a tu ritmo", "your pace", "seu ritmo")):
        raise AssertionError(f"EDITORIAL_COPY_SELF_PACED_MISSING:{locale}")
    for page, item in pages.items():
        if len(item["lead"]) > 160 or len(re.findall(r"[.!?](?:\s|$)", item["lead"])) > 2:
            raise AssertionError(f"EDITORIAL_COPY_BLUF_INVALID:{locale}:{page}")
    resources = {item["id"]: item for item in pages["resources_index"]["sections"]}
    for section_id, term in functional_terms.items():
        item = resources[section_id]
        if term in item["title"].casefold() or term not in item["body"].casefold():
            raise AssertionError(f"EDITORIAL_COPY_TERM_ORDER_INVALID:{locale}:{section_id}")
    if "metaprompt" in locale_corpora[locale]:
        raise AssertionError(f"EDITORIAL_COPY_UNDEFINED_METAPROMPT:{locale}")
    for page in EDITORIAL_PAGES:
        persona = source["audience_copy"][locale]["persona"][page]
        empresa = source["audience_copy"][locale]["empresa"][page]
        if " ".join(copy_strings(persona)).casefold() == " ".join(copy_strings(empresa)).casefold():
            raise AssertionError(f"EDITORIAL_COPY_AUDIENCE_CLONE:{locale}:{page}")

if len(set(locale_corpora.values())) != len(LOCALES):
    raise AssertionError("EDITORIAL_COPY_LOCALE_CLONE")

reject("EDITORIAL_SITEMAP_EFFECT_INVALID", lambda item: item.update(publication_authorized=True))
reject("EDITORIAL_SITEMAP_EFFECT_INVALID", lambda item: item.update(network_required=True))
reject("EDITORIAL_SITEMAP_SHAPE_INVALID", lambda item: item.update(event_schema={"@type": "Event"}))
reject("EDITORIAL_SITEMAP_BINDING_INVALID", lambda item: item.update(self_sha256="0" * 64))
reject("EDITORIAL_SITEMAP_VARIANTS_INVALID", lambda item: item["page_order"].pop())
reject("EDITORIAL_SITEMAP_ROUTE_INVALID:es:level0", lambda item: item["pages"]["level0"]["slugs"].update(es="../x"))
reject("EDITORIAL_SITEMAP_SLUG_COLLISION:es", lambda item: item["pages"]["how"]["slugs"].update(es="nivel-0"))
reject("EDITORIAL_SITEMAP_ANCHORS_INVALID:es:level0", lambda item: item["pages"]["level0"]["anchors"].__setitem__(1, "other"))
reject("EDITORIAL_SITEMAP_AUDIENCE_INVALID:es:persona:level0", lambda item: item["audience_copy"]["es"]["persona"]["level0"].update(points=[]))
reject("EDITORIAL_SITEMAP_TEMPORAL_CLAIM_INVALID", lambda item: item["copy"]["es"]["intakes"].update(lead="Inscripciones abiertas 2026-09"))

expected_paths = []
for locale in LOCALES:
    for audience in AUDIENCES:
        for page in PAGES:
            route = page_dir(locale, audience, page)
            expected_paths.append((DIST if route == "." else DIST / route) / "index.html")
if len(expected_paths) != 54 or len(set(expected_paths)) != 54:
    raise AssertionError("EDITORIAL_ROUTE_MATRIX_INVALID")
actual_paths = sorted(DIST.rglob("index.html"))
if set(actual_paths) != set(expected_paths):
    raise AssertionError("EDITORIAL_ROUTE_TREE_DRIFT")

unsafe = re.compile(r"inscripciones abiertas|enrollment open|inscrições abertas|join cohort|inscribirme|inscrever-me", re.I)
for path in actual_paths:
    html = path.read_text(encoding="utf-8")
    page = re.search(r'<body data-page="([^"]+)"', html).group(1)
    locale = re.search(r'<html lang="([^"]+)"', html).group(1)
    audience = re.search(r'<html[^>]+data-audience="([^"]+)"', html).group(1)
    route = page_dir(locale, audience, page)
    canonical = PUBLIC + ("" if route == "." else route + "/")
    if f'<link rel="canonical" href="{canonical}">' not in html:
        raise AssertionError(f"EDITORIAL_CANONICAL_DRIFT:{path.relative_to(DIST)}")
    alternates = dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">', html))
    expected_alternates = {code: PUBLIC + ("" if page_dir(code, audience, page) == "." else page_dir(code, audience, page) + "/") for code in LOCALES}
    expected_alternates["x-default"] = expected_alternates["es"]
    if alternates != expected_alternates:
        raise AssertionError(f"EDITORIAL_HREFLANG_DRIFT:{path.relative_to(DIST)}")
    nav = re.search(r'<nav class="mdg-nav conoce-nav"[\s\S]*?</nav>', html).group(0)
    if "#" in "".join(re.findall(r'href="([^"]+)"', nav)):
        raise AssertionError(f"EDITORIAL_HEADER_FRAGMENT:{path.relative_to(DIST)}")
    if unsafe.search(html):
        raise AssertionError(f"EDITORIAL_UNVERIFIED_INTAKE_CLAIM:{path.relative_to(DIST)}")
    structured = json.loads(re.search(r'<script type="application/ld\+json" data-conoce-structured>([\s\S]*?)</script>', html).group(1))
    if any(item.get("@type") == "Event" for item in structured.get("@graph", [])):
        raise AssertionError(f"EDITORIAL_EVENT_SCHEMA:{path.relative_to(DIST)}")
    if page in EDITORIAL_PAGES:
        if html.count('data-editorial-page=') != 1 or html.count('data-editorial-audience=') != 1:
            raise AssertionError(f"EDITORIAL_RENDER_MISSING:{path.relative_to(DIST)}")
        for anchor in source["pages"][page]["anchors"]:
            if html.count(f'id="{anchor}"') != 1 or html.count(f'href="#{anchor}"') < 1:
                raise AssertionError(f"EDITORIAL_ANCHOR_DRIFT:{path.relative_to(DIST)}:{anchor}")
    for href in re.findall(r'href="([^"]+)"', html):
        local = href.split("#", 1)[0].split("?", 1)[0]
        if not local or local.startswith(("http:", "https:", "mailto:", "tel:", "data:", "javascript:")):
            continue
        target = (path.parent / local).resolve()
        if target.is_dir() or local.endswith("/"):
            target /= "index.html"
        if not target.exists():
            raise AssertionError(f"EDITORIAL_INTERNAL_LINK_MISSING:{path.relative_to(DIST)}:{href}")

for locale in LOCALES:
    for page in EDITORIAL_PAGES:
        persona = ((DIST if page_dir(locale, "persona", page) == "." else DIST / page_dir(locale, "persona", page)) / "index.html").read_text(encoding="utf-8")
        empresa = ((DIST if page_dir(locale, "empresa", page) == "." else DIST / page_dir(locale, "empresa", page)) / "index.html").read_text(encoding="utf-8")
        p_card = re.search(r'<aside class="editorial-audience">([\s\S]*?)</aside>', persona).group(1)
        e_card = re.search(r'<aside class="editorial-audience">([\s\S]*?)</aside>', empresa).group(1)
        if p_card == e_card:
            raise AssertionError(f"EDITORIAL_AUDIENCE_NOT_MATERIAL:{locale}:{page}")

sitemap_root = ET.parse(DIST / "sitemap.xml").getroot()
locs = [node.text for node in sitemap_root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
expected_locs = [PUBLIC + ("" if page_dir(locale, audience, page) == "." else page_dir(locale, audience, page) + "/") for audience in AUDIENCES for locale in LOCALES for page in PAGES]
if len(locs) != 54 or len(set(locs)) != 54 or set(locs) != set(expected_locs):
    raise AssertionError("EDITORIAL_SITEMAP_OUTPUT_DRIFT")

manifest_payload = (DIST / "build-manifest.json").read_bytes()
manifest = json.loads(manifest_payload)
receipt = json.loads((DIST / "build-receipt.json").read_text(encoding="utf-8"))
binding = manifest.get("editorial_sitemap", {})
if binding.get("source_sha256") != hashlib.sha256(EDITORIAL_SPEC.read_bytes()).hexdigest() or binding.get("rendered_pages") != 24 or binding.get("canonical_count") != 54:
    raise AssertionError("EDITORIAL_MANIFEST_BINDING_DRIFT")
if receipt.get("editorial_sitemap") != binding or receipt.get("manifest_sha256") != hashlib.sha256(manifest_payload).hexdigest():
    raise AssertionError("EDITORIAL_RECEIPT_BINDING_DRIFT")

print("EDITORIAL_SITEMAP_OK canonicals=54 editorial=24 header_fragments=0 audience_material=24")
