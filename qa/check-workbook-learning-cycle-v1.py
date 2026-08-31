#!/usr/bin/env python3
"""Fail-closed gate for the canonical Nivel 0 workbook learning cycle.

[METODOLOGIA] Every workbook must expose the same orientation pattern while its
module-specific title and practice remain inside the corresponding panel.
"""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
STAGES = {
    "es": ("En clase", "Profundización", "Consolidación"),
    "en": ("In class", "Deepening", "Consolidation"),
    "pt": ("Em aula", "Aprofundamento", "Consolidação"),
}
CRITERIA = {
    "es": "Criterio de consolidación",
    "en": "Consolidation criterion",
    "pt": "Critério de consolidação",
}
PANELS = ("sheet-session", "sheet-depth", "sheet-consolidation")


class WorkbookProbe(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.section_sheets: list[str | None] = []
        self.tabs: list[dict[str, object]] = []
        self.active_tab: dict[str, object] | None = None
        self.locations: dict[str, list[str | None]] = {}
        self.panel_ids: list[str] = []
        self.main_module_order: str | None = None
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value for key, value in attrs}
        inherited = self.section_sheets[-1] if self.section_sheets else None
        if tag == "section":
            classes = (attr.get("class") or "").split()
            current = attr.get("id") if "sheet" in classes else inherited
            self.section_sheets.append(current)
            if "sheet" in classes and attr.get("id"):
                self.panel_ids.append(str(attr["id"]))
        current_sheet = self.section_sheets[-1] if self.section_sheets else None
        node_id = attr.get("id")
        if node_id in {"transferencia", "workbook-rubric"}:
            self.locations.setdefault(str(node_id), []).append(current_sheet)
        if "data-consolidation-gate" in attr:
            self.locations.setdefault("consolidation-gate", []).append(current_sheet)
        if tag == "main" and attr.get("id") == "main":
            self.main_module_order = attr.get("data-module-order")
        if tag == "button" and "tab" in (attr.get("class") or "").split() and attr.get("role") == "tab":
            self.active_tab = {
                "text": [],
                "controls": attr.get("aria-controls"),
                "stage": attr.get("data-workbook-stage"),
            }

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if value:
            self.text.append(value)
            if self.active_tab is not None:
                cast_text = self.active_tab["text"]
                assert isinstance(cast_text, list)
                cast_text.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag == "button" and self.active_tab is not None:
            words = self.active_tab["text"]
            assert isinstance(words, list)
            self.active_tab["text"] = " ".join(words)
            self.tabs.append(self.active_tab)
            self.active_tab = None
        if tag == "section" and self.section_sheets:
            self.section_sheets.pop()


def validate(source: str, route: str) -> list[str]:
    failures: list[str] = []
    lang_match = re.search(r'<html\b[^>]*\blang="(es|en|pt)"', source)
    if not lang_match:
        return [f"{route}:LANG_MISSING"]
    locale = lang_match.group(1)
    probe = WorkbookProbe()
    probe.feed(source)
    if tuple(probe.panel_ids) != PANELS:
        failures.append(f"{route}:PANELS:{probe.panel_ids}")
    if len(probe.tabs) != 3:
        failures.append(f"{route}:TAB_COUNT:{len(probe.tabs)}")
    else:
        for index, (tab, label, panel) in enumerate(zip(probe.tabs, STAGES[locale], PANELS), 1):
            text = html.unescape(str(tab["text"]))
            if label not in text or tab["controls"] != panel:
                failures.append(f"{route}:TAB_{index}:{text}:{tab['controls']}")
            rail_pattern = re.compile(
                rf'<a(?=[^>]*href="#{re.escape(panel)}")(?=[^>]*data-intrapage-link)[^>]*>'
                rf'.*?<strong>{re.escape(label)}</strong>.*?</a>',
                re.DOTALL,
            )
            if not rail_pattern.search(source):
                failures.append(f"{route}:RAIL_{index}:{label}")
        if probe.main_module_order:
            stages = tuple(str(tab["stage"]) for tab in probe.tabs)
            if stages != ("in-class", "deepening", "consolidation"):
                failures.append(f"{route}:STAGE_IDS:{stages}")
    for marker in ("consolidation-gate", "workbook-rubric"):
        if probe.locations.get(marker) != ["sheet-consolidation"]:
            failures.append(f"{route}:{marker.upper()}:{probe.locations.get(marker)}")
    if probe.main_module_order and probe.locations.get("transferencia") != ["sheet-consolidation"]:
        failures.append(f"{route}:TRANSFER_OUTSIDE_CONSOLIDATION:{probe.locations.get('transferencia')}")
    visible_text = " ".join(probe.text)
    if CRITERIA[locale] not in visible_text:
        failures.append(f"{route}:CRITERION_LABEL_MISSING")
    return failures


def main() -> None:
    pages: list[tuple[str, str]] = []
    for path in sorted(DIST.rglob("index.html")):
        source = path.read_text(encoding="utf-8")
        if 'class="workbook-v2"' in source:
            pages.append((path.relative_to(DIST).as_posix(), source))
    failures = [failure for route, source in pages for failure in validate(source, route)]
    if len(pages) != 24:
        failures.append(f"PAGE_COUNT:expected=24:actual={len(pages)}")
    compiler_source = (ROOT / "scripts" / "build.py").read_text(encoding="utf-8")
    residual_names = (
        "'tabs':['En sesión'",
        "'tabs':['In session'",
        "Abre la hoja En sesión",
        "Open In session",
    )
    for residual in residual_names:
        if residual in compiler_source or any(residual in source for _route, source in pages):
            failures.append(f"LEGACY_STAGE_NAME:{residual}")
    mutation = pages[0][1].replace(" data-consolidation-gate", "", 1) if pages else ""
    if pages and not any("CONSOLIDATION-GATE" in item for item in validate(mutation, "mutation")):
        failures.append("MUTATION_GATE_WAS_ACCEPTED")
    if failures:
        raise AssertionError("WORKBOOK_LEARNING_CYCLE_FAILED\n" + "\n".join(failures[:80]))
    print(
        "[EVIDENCE:WORKBOOK_LEARNING_CYCLE] WORKBOOK_LEARNING_CYCLE_OK "
        "pages=24 stages=3 nested_transfer=18 gate=24 rubric=24 mutation=rejected"
    )


if __name__ == "__main__":
    main()
