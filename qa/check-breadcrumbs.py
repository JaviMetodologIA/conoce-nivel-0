#!/usr/bin/env python3
from __future__ import annotations

import json
import posixpath
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
sys.path.insert(0, str(ROOT / "scripts"))

from brand import (  # noqa: E402
    AUDIENCES,
    DEFAULT_MODULE_ID,
    EDITORIAL_PAGES,
    LOCALES,
    MODULE_IDS,
    MODULE_ROUTES,
    RESOURCE_SEGMENTS,
    module_anchor,
    page_dir,
    relative_page,
    validate_chrome_spec,
    validate_editorial_spec,
)
from build import RESOURCE_NAMES  # noqa: E402

PUBLIC = "https://conoce.metodologia.info/"
EDITORIAL = validate_editorial_spec()
CHROME = validate_chrome_spec()
LABELS = {
    "es": {"home": "Inicio", "resources": "Recursos", "deck": "Masterclass", "workbook": "Workbook", "playbook": "Playbook", "prompts": "Biblioteca de prompts"},
    "en": {"home": "Home", "resources": "Resources", "deck": "Masterclass", "workbook": "Workbook", "playbook": "Playbook", "prompts": "Prompt library"},
    "pt": {"home": "Início", "resources": "Recursos", "deck": "Masterclass", "workbook": "Workbook", "playbook": "Playbook", "prompts": "Biblioteca de prompts"},
}


def absolute(locale: str, audience: str, page: str,
             module_id: str = DEFAULT_MODULE_ID) -> str:
    route = page_dir(locale, audience, page, module_id)
    return PUBLIC + ("" if route == "." else route + "/")


def model(locale: str, audience: str, page: str,
          module_id: str = DEFAULT_MODULE_ID) -> list[dict[str, str]]:
    labels = LABELS[locale]
    result = [{
        "label": labels["home"],
        "href": relative_page(
            locale, audience, page, locale, audience, "landing",
            module_id, DEFAULT_MODULE_ID,
        ),
        "item": absolute(locale, audience, "landing"),
    }]
    if page in RESOURCE_SEGMENTS:
        overview_href = relative_page(
            locale, audience, page, locale, audience, "resources_index",
            module_id, DEFAULT_MODULE_ID,
        )
        result.append({
            "label": labels["resources"],
            "href": overview_href,
            "item": absolute(locale, audience, "resources_index"),
        })
        if module_id != DEFAULT_MODULE_ID:
            result.append({
                "label": MODULE_ROUTES[module_id]["labels"][locale],
                "href": f"{overview_href}#{module_anchor(module_id)}",
                # The module tier is an anchored catalogue concept, not a
                # second canonical page; JSON-LD binds it to that catalogue.
                "item": absolute(locale, audience, "resources_index"),
            })
    if page != "landing":
        if page in EDITORIAL_PAGES:
            current = EDITORIAL["copy"][locale][page]["title"]
        elif module_id == DEFAULT_MODULE_ID:
            current = labels[page]
        else:
            resource_key = {"deck": "masterclass", "workbook": "workbook", "playbook": "playbook", "prompts": "prompts"}[page]
            current = RESOURCE_NAMES[locale][MODULE_ROUTES[module_id]["order"] - 1][resource_key]
        result.append({
            "label": current,
            "href": "",
            "item": absolute(locale, audience, page, module_id),
        })
    return result


def validate_html(html: str, locale: str, audience: str, page: str,
                  module_id: str = DEFAULT_MODULE_ID) -> None:
    soup = BeautifulSoup(html, "html.parser")
    expected = model(locale, audience, page, module_id)
    header = soup.select_one("[data-conoce-nav]")
    home = header.select("[data-conoce-home-link]") if header else []
    if len(home) != 1 or home[0].get_text(" ", strip=True) != LABELS[locale]["home"]:
        raise AssertionError("BREADCRUMB_HEADER_HOME_MISSING")
    if home[0].get("href") != relative_page(
        locale, audience, page, locale, audience, "landing",
        module_id, DEFAULT_MODULE_ID,
    ) or "#" in home[0].get("href", ""):
        raise AssertionError("BREADCRUMB_HEADER_HOME_ROUTE")
    header_currents = header.select('[aria-current="page"]')
    if len(header_currents) != 1 or (page == "landing") != (header_currents[0] is home[0]):
        raise AssertionError("BREADCRUMB_HEADER_CURRENT")
    navs = soup.select("[data-conoce-breadcrumbs]")
    if len(navs) != 1:
        raise AssertionError("BREADCRUMB_SSR_COUNT")
    items = navs[0].select("ol > li")
    if len(items) != len(expected):
        raise AssertionError("BREADCRUMB_HIERARCHY")
    for index, (item, wanted) in enumerate(zip(items, expected)):
        if item.get_text(" ", strip=True) != wanted["label"]:
            raise AssertionError("BREADCRUMB_LABEL")
        link = item.find("a")
        current = item.select('[aria-current="page"]')
        if index == len(items) - 1:
            if link or len(current) != 1 or current[0].name != "span":
                raise AssertionError("BREADCRUMB_LAST_SEMANTICS")
        else:
            href = wanted["href"]
            fragment_expected = module_id != DEFAULT_MODULE_ID and index == 2
            if (
                not link
                or link.get("href") != href
                or ("#" in href) != fragment_expected
                or current
            ):
                raise AssertionError("BREADCRUMB_LINK_ROUTE")
    if len(navs[0].select('[aria-current="page"]')) != 1:
        raise AssertionError("BREADCRUMB_DUPLICATE_CURRENT")


def route_variants():
    for locale in LOCALES:
        for audience in AUDIENCES:
            for page in ("landing", *EDITORIAL_PAGES):
                yield locale, audience, page, DEFAULT_MODULE_ID
            for module_id in MODULE_IDS:
                for page in RESOURCE_SEGMENTS:
                    yield locale, audience, page, module_id


# [EVIDENCE:BREADCRUMB_MATRIX] 30 global/editorial + 96 resource routes.
variants = list(route_variants())
if len(variants) != 126 or len({page_dir(*item) for item in variants}) != 126:
    raise AssertionError("BREADCRUMB_ROUTE_MATRIX")

html_count = 0
nested_count = 0
sample = None
for locale, audience, page, module_id in variants:
    route = page_dir(locale, audience, page, module_id)
    path = (DIST if route == "." else DIST / route) / "index.html"
    html = path.read_text(encoding="utf-8")
    validate_html(html, locale, audience, page, module_id)
    soup = BeautifulSoup(html, "html.parser")
    if soup.body.get("data-module-id") != module_id:
        raise AssertionError("BREADCRUMB_MODULE_BINDING")
    structured = json.loads(soup.select_one("[data-conoce-structured]").string)
    lists = [item for item in structured["@graph"] if item.get("@type") == "BreadcrumbList"]
    expected = model(locale, audience, page, module_id)
    if len(lists) != 1:
        raise AssertionError("BREADCRUMB_JSONLD_COUNT")
    elements = lists[0].get("itemListElement", [])
    wanted = [
        {
            "@type": "ListItem",
            "position": index,
            "name": item["label"],
            "item": item["item"],
        }
        for index, item in enumerate(expected, 1)
    ]
    if elements != wanted or lists[0].get("@id") != absolute(locale, audience, page, module_id) + "#breadcrumb":
        raise AssertionError("BREADCRUMB_JSONLD_HIERARCHY")
    if module_id != DEFAULT_MODULE_ID:
        if len(expected) != 4:
            raise AssertionError("BREADCRUMB_NESTED_HIERARCHY")
        nested_count += 1
        if sample is None and page == "playbook" and locale == "es" and audience == "persona":
            sample = html
    html_count += 1

if nested_count != 72 or sample is None:
    raise AssertionError("BREADCRUMB_NESTED_COUNT")

mutations = [
    sample.replace(" data-conoce-home-link", "", 1),
    re.sub(r'(href="[^"]+" data-conoce-home-link)', lambda match: match.group(1).replace('" data-', '#entrada" data-'), sample, count=1),
    re.sub(r'<span aria-current="page">([^<]+)</span>', r'<a href="./index.html" aria-current="page">\1</a>', sample, count=1),
    re.sub(r'(<a href="[^"]+">Recursos</a>)', lambda match: match.group(1).replace('>', ' aria-current="page">', 1), sample, count=1),
    sample.replace('data-conoce-breadcrumbs', 'data-breadcrumb-removed', 1),
    re.sub(r'<li><a href="[^"]+#module-02">[^<]+</a></li>', "", sample, count=1),
]
for mutation in mutations:
    try:
        validate_html(mutation, "es", "persona", "playbook", MODULE_IDS[1])
    except AssertionError:
        pass
    else:
        raise AssertionError("BREADCRUMB_MUTATION_PASSED")

manifest = json.loads((DIST / "build-manifest.json").read_text(encoding="utf-8"))
receipt = json.loads((DIST / "build-receipt.json").read_text(encoding="utf-8"))
if manifest.get("build_id") != "nivel-0-learning-resources-v15" or manifest.get("conoce_chrome", {}).get("breadcrumbs") != CHROME["breadcrumbs"]:
    raise AssertionError("BREADCRUMB_MANIFEST_BINDING")
if (
    manifest.get("conoce_chrome", {}).get("rendered_pages") != 126
    or manifest.get("state") != "RENDERED_DRAFT"
    or receipt.get("state") != "RENDERED_DRAFT"
    or manifest.get("publication_authorized") is not False
    or receipt.get("publication_authorized") is not False
):
    raise AssertionError("BREADCRUMB_GOVERNANCE_BINDING")

print(
    "[EVIDENCE:BREADCRUMBS] BREADCRUMBS_OK "
    f"pages={html_count} header_home=126 jsonld=126 nested_4_level={nested_count} "
    f"mutations={len(mutations)} header_fragments=0 publication=false"
)
