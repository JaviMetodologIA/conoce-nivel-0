#!/usr/bin/env python3
"""Gate the governed NotebookLM launch guidance and compact prompt UI."""

from html.parser import HTMLParser
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "src" / "notebooklm-execution-spec-v1.json"
DIST = ROOT / "dist"
LOCALES = ("es", "en", "pt")
AUDIENCES = ("persona", "empresa")
LIBRARY_IDS = {f"{number:02d}" for number in range(1, 11)} | {f"M{number}" for number in range(1, 5)}
ALL_IDS = LIBRARY_IDS | {"B1", "B2", "B3"} | {f"W{number:02d}" for number in range(1, 11)}
OFFICIAL_PREFIX = "https://support.google.com/notebooklm/answer/"


class PromptPageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.guides = 0
        self.tabs = []
        self.panels = []
        self.cards = []
        self.disclosures = 0
        self.filters = []
        self.official_links = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if "data-notebook-execution-guide" in data:
            self.guides += 1
        if "data-notebook-tab" in data:
            self.tabs.append(data)
        if "data-notebook-panel" in data:
            self.panels.append(data)
        if "data-library-prompt" in data:
            self.cards.append(data)
        if "data-prompt-card-disclosure" in data:
            self.disclosures += 1
        if "data-prompt-surface-filter" in data:
            self.filters.append(data)
        href = data.get("href", "")
        if href.startswith(OFFICIAL_PREFIX):
            self.official_links.append(href)


def route(locale, audience):
    parts = []
    if locale != "es":
        parts.append(locale)
    if audience == "empresa":
        parts.append("empresa")
    parts.extend(("prompts", "index.html"))
    return DIST.joinpath(*parts)


def assert_spec(spec):
    expected_fields = {
        "schema_version", "state", "publication_authorized", "last_verified",
        "product", "official_sources", "intent_routes", "locales",
    }
    assert set(spec) == expected_fields, "NOTEBOOK_SPEC_FIELDS"
    assert spec["schema_version"] == "notebooklm-execution-spec-v1", "NOTEBOOK_SPEC_VERSION"
    assert spec["state"] == "RENDERED_DRAFT" and spec["publication_authorized"] is False, "NOTEBOOK_SPEC_STATE"
    assert spec["product"] == {
        "display_name": "NotebookLM",
        "url": "https://notebook.google.com/",
        "network_required": False,
    }, "NOTEBOOK_PRODUCT"
    assert set(spec["official_sources"]) == {"chat", "source_search"}, "NOTEBOOK_OFFICIAL_SOURCE_KEYS"
    assert all(item["url"].startswith(OFFICIAL_PREFIX) for item in spec["official_sources"].values()), "NOTEBOOK_OFFICIAL_SOURCE_AUTHORITY"
    assert set(spec["intent_routes"]) == ALL_IDS, "NOTEBOOK_INTENT_MATRIX"
    for intent_id, item in spec["intent_routes"].items():
        assert set(item) == {"launch", "mode", "handoff"}, f"NOTEBOOK_ROUTE_FIELDS:{intent_id}"
        assert item["launch"] in {"chat", "source_search"}, f"NOTEBOOK_LAUNCH:{intent_id}"
        assert item["mode"] in {"selected_sources", "deep_research", "research_brief"}, f"NOTEBOOK_MODE:{intent_id}"
        assert item["handoff"] in {None, "chat", "source_search"}, f"NOTEBOOK_HANDOFF:{intent_id}"
        if item["launch"] == "source_search":
            assert item["mode"] == "deep_research" and item["handoff"] == "chat", f"NOTEBOOK_SEARCH_FLOW:{intent_id}"
    assert set(spec["locales"]) == set(LOCALES), "NOTEBOOK_LOCALES"
    localized_fields = set(spec["locales"]["es"])
    assert len(localized_fields) == 21, "NOTEBOOK_LOCALIZED_FIELD_COUNT"
    for locale, copy in spec["locales"].items():
        assert set(copy) == localized_fields and all(isinstance(value, str) and value.strip() for value in copy.values()), f"NOTEBOOK_COPY:{locale}"
        assert "Fast Research" in copy["search_body"] and "Deep Research" in copy["search_body"], f"NOTEBOOK_RESEARCH_MODES:{locale}"


def assert_pages(spec):
    page_count = card_count = 0
    expected_surfaces = {intent_id.lower(): spec["intent_routes"][intent_id]["launch"] for intent_id in LIBRARY_IDS}
    for locale in LOCALES:
        copy = spec["locales"][locale]
        for audience in AUDIENCES:
            path = route(locale, audience)
            assert path.is_file(), f"NOTEBOOK_PAGE_MISSING:{path.relative_to(DIST)}"
            text = path.read_text(encoding="utf-8")
            parser = PromptPageParser()
            parser.feed(text)
            assert parser.guides == 1, f"NOTEBOOK_GUIDE_COUNT:{path.relative_to(DIST)}"
            assert len(parser.tabs) == 2 and {item["data-notebook-tab"] for item in parser.tabs} == {"chat", "source_search"}, f"NOTEBOOK_TABS:{path.relative_to(DIST)}"
            assert len(parser.panels) == 2 and {item["data-notebook-panel"] for item in parser.panels} == {"chat", "source_search"}, f"NOTEBOOK_PANELS:{path.relative_to(DIST)}"
            assert len(parser.cards) == 14 and parser.disclosures == 14, f"NOTEBOOK_CARDS:{path.relative_to(DIST)}"
            assert len(parser.filters) == 3 and {item["data-prompt-surface-filter"] for item in parser.filters} == {"all", "chat", "source_search"}, f"NOTEBOOK_FILTERS:{path.relative_to(DIST)}"
            assert set(parser.official_links) == {source["url"] for source in spec["official_sources"].values()}, f"NOTEBOOK_LINKS:{path.relative_to(DIST)}"
            assert all(key in text for key in (copy["lead"], copy["chat_body"], copy["search_body"], copy["bridge"])), f"NOTEBOOK_COPY_RENDER:{path.relative_to(DIST)}"
            rendered = {item["id"].removeprefix("prompt-"): item["data-notebook-surface"] for item in parser.cards}
            assert rendered == expected_surfaces, f"NOTEBOOK_CARD_ROUTE:{path.relative_to(DIST)}"
            assert {key for key, value in rendered.items() if value == "source_search"} == {"01", "03"}, f"NOTEBOOK_LIBRARY_SEARCH_SET:{path.relative_to(DIST)}"
            page_count += 1
            card_count += len(parser.cards)
    return page_count, card_count


def main():
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert_spec(spec)
    pages, cards = assert_pages(spec)
    print(f"NOTEBOOKLM_EXECUTION_OK specs=1 intents={len(ALL_IDS)} pages={pages} cards={cards} official_sources=2")


if __name__ == "__main__":
    main()
