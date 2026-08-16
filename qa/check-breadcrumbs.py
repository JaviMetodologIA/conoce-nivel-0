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

from brand import AUDIENCES, EDITORIAL_PAGES, LOCALES, PAGES, page_dir, relative_page, validate_chrome_spec, validate_editorial_spec  # noqa: E402

PUBLIC = "https://conoce.metodologia.info/"
EDITORIAL = validate_editorial_spec()
CHROME = validate_chrome_spec()
LABELS = {
    "es": {"home": "Inicio", "resources": "Recursos", "deck": "Masterclass", "workbook": "Workbook", "playbook": "Playbook", "prompts": "Biblioteca de prompts"},
    "en": {"home": "Home", "resources": "Resources", "deck": "Masterclass", "workbook": "Workbook", "playbook": "Playbook", "prompts": "Prompt library"},
    "pt": {"home": "Início", "resources": "Recursos", "deck": "Masterclass", "workbook": "Workbook", "playbook": "Playbook", "prompts": "Biblioteca de prompts"},
}


def absolute(locale: str, audience: str, page: str) -> str:
    route = page_dir(locale, audience, page)
    return PUBLIC + ("" if route == "." else route + "/")


def model(locale: str, audience: str, page: str) -> list[dict[str, str]]:
    labels = LABELS[locale]
    result = [{"label": labels["home"], "page": "landing"}]
    if page in ("deck", "workbook", "playbook", "prompts"):
        result.append({"label": labels["resources"], "page": "resources_index"})
    if page != "landing":
        current = EDITORIAL["copy"][locale][page]["title"] if page in EDITORIAL_PAGES else labels[page]
        result.append({"label": current, "page": page})
    return result


def validate_html(html: str, locale: str, audience: str, page: str) -> None:
    soup = BeautifulSoup(html, "html.parser")
    expected = model(locale, audience, page)
    header = soup.select_one("[data-conoce-nav]")
    home = header.select("[data-conoce-home-link]") if header else []
    if len(home) != 1 or home[0].get_text(" ", strip=True) != LABELS[locale]["home"]:
        raise AssertionError("BREADCRUMB_HEADER_HOME_MISSING")
    if home[0].get("href") != relative_page(locale, audience, page, locale, audience, "landing") or "#" in home[0].get("href", ""):
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
            href = relative_page(locale, audience, page, locale, audience, wanted["page"])
            if not link or link.get("href") != href or "#" in href or current:
                raise AssertionError("BREADCRUMB_LINK_ROUTE")
    if len(navs[0].select('[aria-current="page"]')) != 1:
        raise AssertionError("BREADCRUMB_DUPLICATE_CURRENT")


html_count = 0
sample = None
for locale in LOCALES:
    for audience in AUDIENCES:
        for page in PAGES:
            route = page_dir(locale, audience, page)
            path = (DIST if route == "." else DIST / route) / "index.html"
            html = path.read_text(encoding="utf-8")
            validate_html(html, locale, audience, page)
            soup = BeautifulSoup(html, "html.parser")
            structured = json.loads(soup.select_one("[data-conoce-structured]").string)
            lists = [item for item in structured["@graph"] if item.get("@type") == "BreadcrumbList"]
            expected = model(locale, audience, page)
            if len(lists) != 1:
                raise AssertionError("BREADCRUMB_JSONLD_COUNT")
            elements = lists[0].get("itemListElement", [])
            wanted = [{"@type": "ListItem", "position": index, "name": item["label"], "item": absolute(locale, audience, item["page"])} for index, item in enumerate(expected, 1)]
            if elements != wanted or lists[0].get("@id") != absolute(locale, audience, page) + "#breadcrumb":
                raise AssertionError("BREADCRUMB_JSONLD_HIERARCHY")
            if sample is None and page == "playbook" and locale == "es" and audience == "persona":
                sample = html
            html_count += 1

mutations = [
    sample.replace(" data-conoce-home-link", "", 1),
    sample.replace('href="../index.html" data-conoce-home-link', 'href="../index.html#entrada" data-conoce-home-link', 1),
    sample.replace('<span aria-current="page">Playbook</span>', '<a href="./index.html" aria-current="page">Playbook</a>', 1),
    sample.replace('<a href="../recursos/index.html">Recursos</a>', '<a href="../recursos/index.html" aria-current="page">Recursos</a>', 1),
    sample.replace('data-conoce-breadcrumbs', 'data-breadcrumb-removed', 1),
]
for mutation in mutations:
    try:
        validate_html(mutation, "es", "persona", "playbook")
    except AssertionError:
        pass
    else:
        raise AssertionError("BREADCRUMB_MUTATION_PASSED")

manifest = json.loads((DIST / "build-manifest.json").read_text(encoding="utf-8"))
if manifest.get("build_id") != "nivel-0-learning-resources-v9" or manifest.get("conoce_chrome", {}).get("breadcrumbs") != CHROME["breadcrumbs"]:
    raise AssertionError("BREADCRUMB_MANIFEST_BINDING")

print(f"BREADCRUMBS_OK pages={html_count} header_home=54 jsonld=54 mutations={len(mutations)} fragments=0")
