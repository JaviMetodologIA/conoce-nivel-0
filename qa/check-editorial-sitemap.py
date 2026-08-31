#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
sys.path.insert(0, str(ROOT / "scripts"))

from brand import (  # noqa: E402
    AUDIENCES,
    DEFAULT_MODULE_ID,
    EDITORIAL_PAGES,
    EDITORIAL_SPEC,
    LOCALES,
    MODULE_IDS,
    RESOURCE_SEGMENTS,
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
audience_source = json.loads((ROOT / "src/audience-spec-v1.json").read_text(encoding="utf-8"))
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
    "masterclass-resource": "masterclass",
    "workbook-resource": "workbook",
    "playbook-resource": "playbook",
    "prompts-resource": "prompt",
}
four_labels = {"es": "cuatro", "en": "four", "pt": "quatro"}
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
        title = item["title"].casefold()
        body = item["body"].casefold()
        if not title.startswith(four_labels[locale]) or term not in f"{title} {body}":
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

def route_variants():
    for locale in LOCALES:
        for audience in AUDIENCES:
            for page in ("landing", *EDITORIAL_PAGES):
                yield locale, audience, page, DEFAULT_MODULE_ID
            for module_id in MODULE_IDS:
                for page in RESOURCE_SEGMENTS:
                    yield locale, audience, page, module_id


# [EVIDENCE:CANONICAL_ROUTE_MATRIX] 30 global/editorial + 96 resources.
variants = list(route_variants())
expected_paths = []
for locale, audience, page, module_id in variants:
    route = page_dir(locale, audience, page, module_id)
    expected_paths.append((DIST if route == "." else DIST / route) / "index.html")
if len(expected_paths) != 126 or len(set(expected_paths)) != 126:
    raise AssertionError("EDITORIAL_ROUTE_MATRIX_INVALID")
actual_paths = sorted(DIST.rglob("index.html"))
if set(actual_paths) != set(expected_paths):
    raise AssertionError("EDITORIAL_ROUTE_TREE_DRIFT")

unsafe = re.compile(r"inscripciones abiertas|enrollment open|inscrições abertas|join cohort|inscribirme|inscrever-me", re.I)
target_ids_cache: dict[Path, set[str]] = {}
for path in actual_paths:
    html = path.read_text(encoding="utf-8")
    page = re.search(r'<body data-page="([^"]+)"', html).group(1)
    module_id = re.search(r'<body[^>]+data-module-id="([^"]+)"', html).group(1)
    locale = re.search(r'<html lang="([^"]+)"', html).group(1)
    audience = re.search(r'<html[^>]+data-audience="([^"]+)"', html).group(1)
    route = page_dir(locale, audience, page, module_id)
    canonical = PUBLIC + ("" if route == "." else route + "/")
    if f'<link rel="canonical" href="{canonical}">' not in html:
        raise AssertionError(f"EDITORIAL_CANONICAL_DRIFT:{path.relative_to(DIST)}")
    alternates = dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">', html))
    expected_alternates = {
        code: PUBLIC + (
            "" if page_dir(code, audience, page, module_id) == "."
            else page_dir(code, audience, page, module_id) + "/"
        )
        for code in LOCALES
    }
    expected_alternates["x-default"] = expected_alternates["es"]
    if alternates != expected_alternates:
        raise AssertionError(f"EDITORIAL_HREFLANG_DRIFT:{path.relative_to(DIST)}")
    nav = re.search(r'<nav class="mdg-nav conoce-nav"[\s\S]*?</nav>', html).group(0)
    nav_soup = BeautifulSoup(nav, "html.parser")
    fragment_links = [node for node in nav_soup.select("a[href*='#']")]
    fragment_ids = sorted(node.get("href", "").split("#", 1)[1] for node in fragment_links)
    if (
        any(not node.has_attr("data-conoce-module-link") for node in fragment_links)
        or fragment_ids != ["module-01", "module-02", "module-03", "module-04"]
    ):
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
        path_part, _, fragment = href.partition("#")
        local = path_part.split("?", 1)[0]
        if not local or local.startswith(("http:", "https:", "mailto:", "tel:", "data:", "javascript:")):
            if not local and fragment:
                target = path.resolve()
            else:
                continue
        else:
            target = (path.parent / local).resolve()
        if target.is_dir() or local.endswith("/"):
            target /= "index.html"
        try:
            target.relative_to(DIST.resolve())
        except ValueError as error:
            raise AssertionError(f"EDITORIAL_INTERNAL_LINK_ESCAPE:{path.relative_to(DIST)}:{href}") from error
        if not target.exists():
            raise AssertionError(f"EDITORIAL_INTERNAL_LINK_MISSING:{path.relative_to(DIST)}:{href}")
        if fragment and target.suffix == ".html":
            if target not in target_ids_cache:
                target_soup = BeautifulSoup(target.read_text(encoding="utf-8"), "html.parser")
                target_ids_cache[target] = {
                    str(node.get("id")) for node in target_soup.select("[id]")
                }
            if fragment not in target_ids_cache[target]:
                raise AssertionError(f"EDITORIAL_INTERNAL_FRAGMENT_MISSING:{path.relative_to(DIST)}:{href}")

for locale in LOCALES:
    for page in EDITORIAL_PAGES:
        persona = ((DIST if page_dir(locale, "persona", page) == "." else DIST / page_dir(locale, "persona", page)) / "index.html").read_text(encoding="utf-8")
        empresa = ((DIST if page_dir(locale, "empresa", page) == "." else DIST / page_dir(locale, "empresa", page)) / "index.html").read_text(encoding="utf-8")
        if '<aside class="editorial-audience">' in persona or '<aside class="editorial-audience">' in empresa:
            raise AssertionError(f"EDITORIAL_AUDIENCE_ASIDE_PRESENT:{locale}:{page}")
        pair = []
        for variant, html in (("persona", persona), ("empresa", empresa)):
            soup = BeautifulSoup(html, "html.parser")
            rendered = {}
            for field in audience_source["fields"]:
                nodes = soup.select(f'[data-audience-field="{field}"]')
                if len(nodes) != 1:
                    raise AssertionError(f"EDITORIAL_AUDIENCE_FIELD_MISSING:{locale}:{page}:{variant}:{field}")
                rendered[field] = " ".join(nodes[0].get_text(" ", strip=True).split())
                if rendered[field] != audience_source["locales"][locale][variant][page][field]:
                    raise AssertionError(f"EDITORIAL_AUDIENCE_FIELD_DRIFT:{locale}:{page}:{variant}:{field}")
            pair.append(rendered)
        if any(pair[0][field] == pair[1][field] for field in audience_source["fields"]):
            raise AssertionError(f"EDITORIAL_AUDIENCE_NOT_MATERIAL:{locale}:{page}")

sitemap_root = ET.parse(DIST / "sitemap.xml").getroot()
locs = [node.text for node in sitemap_root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
expected_locs = [
    PUBLIC + (
        "" if page_dir(locale, audience, page, module_id) == "."
        else page_dir(locale, audience, page, module_id) + "/"
    )
    for locale, audience, page, module_id in variants
]
if len(locs) != 126 or len(set(locs)) != 126 or set(locs) != set(expected_locs):
    raise AssertionError("EDITORIAL_SITEMAP_OUTPUT_DRIFT")

manifest_payload = (DIST / "build-manifest.json").read_bytes()
manifest = json.loads(manifest_payload)
receipt = json.loads((DIST / "build-receipt.json").read_text(encoding="utf-8"))
binding = manifest.get("editorial_sitemap", {})
if binding.get("source_sha256") != hashlib.sha256(EDITORIAL_SPEC.read_bytes()).hexdigest() or binding.get("rendered_pages") != 24 or binding.get("canonical_count") != 126:
    raise AssertionError("EDITORIAL_MANIFEST_BINDING_DRIFT")
if receipt.get("editorial_sitemap") != binding or receipt.get("manifest_sha256") != hashlib.sha256(manifest_payload).hexdigest():
    raise AssertionError("EDITORIAL_RECEIPT_BINDING_DRIFT")
if (
    manifest.get("state") != "RENDERED_DRAFT"
    or receipt.get("state") != "RENDERED_DRAFT"
    or manifest.get("publication_authorized") is not False
    or receipt.get("publication_authorized") is not False
):
    raise AssertionError("EDITORIAL_GOVERNANCE_STATE_DRIFT")

print("[EVIDENCE:EDITORIAL_SITEMAP] EDITORIAL_SITEMAP_OK canonicals=126 global_editorial=30 resources=96 editorial=24 internal_links=all audience_material=24 state=RENDERED_DRAFT publication=false")
