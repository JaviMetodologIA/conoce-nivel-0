#!/usr/bin/env python3
"""Adversarial gate for input syntax, demo resolution and prompt journeys."""
from __future__ import annotations

import json
import re
import sys
from itertools import product
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DIST = ROOT / "dist"
LANGS = ("es", "en", "pt")
AUDIENCES = ("persona", "empresa")
LIBRARY_ROUTE = ["01", "05", "03", "04", "07", "02", "06", "08", "10", "09"]
WORKBOOK_ROUTE = ["B1", "B2", "B3"] + [f"W{i:02d}" for i in range(1, 11)]
BRANCHES = {"07": ["M1"], "06": ["M2"], "08": ["M4"], "10": ["M3"]}
BRANCH_POSITION = {"M1": ("07", "02"), "M2": ("06", "08"), "M4": ("08", "10"), "M3": ("10", "09")}
OUTPUTS = {
    "01": "PLAN_INICIAL_DE_INVESTIGACION", "05": "BASE_AUDITADA", "03": "INFORME_DE_INVESTIGACION",
    "04": "VERIFICACION_CRUZADA", "07": "MAPA_DE_CASOS", "02": "COACH_CONFIGURADO",
    "06": "PRACTICA_GENERADA", "08": "EVALUACION_PROGRESIVA", "10": "ENSAYO_DE_ENTREGA",
    "09": "BORRADOR_DE_ENTREGA", "M1": "CONFIG_COACH", "M2": "CONFIG_EVALUADOR",
    "M3": "CONFIG_ENTREVISTADOR", "M4": "CONFIG_PREPARADOR", "B1": "NOTAS_CONFIRMADAS",
    "B2": "PLAN_DE_ESTUDIO", "B3": "PLAN_DE_NOTEBOOKLM", "W01": "BASE_INICIAL",
    "W02": "DIAGNOSTICO_DE_BASE", "W03": "PLAN_DE_INVESTIGACION", "W04": "VEREDICTO_DE_BASE",
    "W05": "ROL_ACTIVADO", "W06": "MATERIAL_DE_APRENDIZAJE", "W07": "CASOS_PRIORIZADOS",
    "W08": "PREGUNTAS_DE_COMPRENSION", "W09": "ENSAYO_DE_DEFENSA", "W10": "PLAN_DE_TRANSFERENCIA",
}
CONSUMES = {
    "05": ["01"], "03": ["05"], "04": ["03"], "07": ["05", "04"], "02": ["07"],
    "06": ["02"], "08": ["06"], "10": ["04", "08"], "09": ["10"], "M1": ["07"],
    "M2": ["06"], "M4": ["08"], "M3": ["10"], "B2": ["B1"], "B3": ["B2"],
    "W01": ["B3"], "W02": ["W01"], "W03": ["W02"], "W04": ["W03"], "W05": ["W04"],
    "W06": ["W04", "W05"], "W07": ["W04", "W06"], "W08": ["W04", "W05"],
    "W09": ["W06", "W08"], "W10": ["W04", "W07", "W09"],
}


def page_path(locale: str, audience: str, page: str) -> Path:
    parts = []
    if locale != "es":
        parts.append(locale)
    if audience == "empresa":
        parts.append("empresa")
    parts.append(page)
    return DIST.joinpath(*parts, "index.html")


def classify(group: str, locale: str) -> str:
    patterns = (
        (rf"library-{locale}-(\d{{2}})", lambda m: m.group(1)),
        (rf"library-{locale}-m(\d)", lambda m: "M" + m.group(1)),
        (rf"p(\d+)-{locale}", lambda m: f"W{int(m.group(1)):02d}"),
        (rf"brain-prompt-{locale}-(\d)", lambda m: "B" + m.group(1)),
    )
    for pattern, render in patterns:
        match = re.fullmatch(pattern, group)
        if match:
            return render(match)
    raise SystemExit(f"PROMPT_V2_GROUP_UNKNOWN:{locale}:{group}")


contracts = {}
for path in sorted((SRC / "prompt-contracts").glob("*.json")):
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema_version") != "prompt-intent-contract-v2":
        raise SystemExit(f"PROMPT_V2_SCHEMA:{path.name}")
    contracts[document["intent_id"]] = document
if len(contracts) != 27:
    raise SystemExit(f"PROMPT_V2_CONTRACT_COUNT:{len(contracts)}")

artifact_spec = json.loads((SRC / "prompt-artifact-labels-v1.json").read_text(encoding="utf-8"))
artifact_labels = artifact_spec.get("artifacts", {})
if artifact_spec.get("schema_version") != "prompt-artifact-labels-v1" or artifact_spec.get("policy", {}).get("fallback") != "forbidden":
    raise SystemExit("PROMPT_V2_ARTIFACT_SPEC")
if set(artifact_labels) != set(OUTPUTS.values()):
    raise SystemExit("PROMPT_V2_ARTIFACT_MATRIX")
for artifact, labels in artifact_labels.items():
    if set(labels) != set(LANGS) or any(not isinstance(value, str) or not value.strip() for value in labels.values()):
        raise SystemExit(f"PROMPT_V2_ARTIFACT_LABEL:{artifact}")


def expected_flow(intent: str) -> tuple[str | None, str | None, list[str]]:
    if intent in BRANCH_POSITION:
        previous, next_id = BRANCH_POSITION[intent]
        return previous, next_id, []
    route = LIBRARY_ROUTE if intent in LIBRARY_ROUTE else WORKBOOK_ROUTE
    index = route.index(intent)
    return (route[index - 1] if index else None,
            route[index + 1] if index + 1 < len(route) else None,
            BRANCHES.get(intent, []))


for intent, contract in contracts.items():
    flow = contract["flow"]
    previous, next_id, branches = expected_flow(intent)
    if (flow["previous"], flow["next"], flow["branches"]) != (previous, next_id, branches):
        raise SystemExit(f"PROMPT_V2_FLOW_ORDER:{intent}")
    if flow["standalone"] is not True or flow["produces"] != OUTPUTS[intent]:
        raise SystemExit(f"PROMPT_V2_FLOW_STANDALONE:{intent}")
    if flow["consumes"] != [OUTPUTS[item] for item in CONSUMES.get(intent, [])]:
        raise SystemExit(f"PROMPT_V2_FLOW_HANDOFF:{intent}:{flow['consumes']}")
    unknown_consumers = set(flow["consumes"]) - set(OUTPUTS.values())
    if unknown_consumers:
        raise SystemExit(f"PROMPT_V2_FLOW_CONSUMER_UNKNOWN:{intent}:{sorted(unknown_consumers)}")
    if flow["loop_to"] is not None and (intent, flow["loop_to"]) != ("W04", "W03"):
        raise SystemExit(f"PROMPT_V2_FLOW_LOOP:{intent}")
    for locale, audiences in contract["locales"].items():
        banned = r"\bencargos?\b|Research brief|Blueprint" if locale in {"es", "pt"} else r"\bassignments?\b|Research brief|Blueprint"
        for audience, cell in audiences.items():
            visible_contract = json.dumps(cell, ensure_ascii=False)
            if re.search(banned, visible_contract, re.I):
                raise SystemExit(f"PROMPT_V2_AMBIGUOUS_DELIVERABLE:{intent}:{locale}:{audience}")


example_label = {"es": "ej.:", "en": "e.g.:", "pt": "ex.:"}
DEMO_GRAMMAR_PATTERNS = {
    "es": (r"\b(?:mi|nuestro|nuestra|su) (?:el|la|un|una)\b", r"\bpara mi una\b", r"\bantes de si\b", r"\bpara qué forma\b"),
    "en": (r"\b(?:my|our|the) the\b", r"\bfor my an?\b", r"\bbefore whether\b", r"\bfor which way\b"),
    "pt": (r"\b(?:meu|minha|nosso|nossa) (?:o|a|um|uma)\b", r"\bpara meu uma\b", r"\bantes de se\b", r"\bpara qual forma\b", r"\bcaminho para meu\b"),
}
total_libraries = total_sources = total_flows = 0
for locale, audience, page in product(LANGS, AUDIENCES, ("prompts", "workbook")):
    route = page_path(locale, audience, page)
    soup = BeautifulSoup(route.read_text(encoding="utf-8"), "html.parser")
    libraries = soup.select("[data-prompt-library]")
    expected_count = 14 if page == "prompts" else 13
    if len(libraries) != expected_count:
        raise SystemExit(f"PROMPT_V2_LIBRARY_COUNT:{locale}:{audience}:{page}:{len(libraries)}")
    total_libraries += len(libraries)
    for library in libraries:
        intent = classify(library["data-prompt-library"], locale)
        cell = contracts[intent]["locales"][locale][audience]
        sources = library.select("textarea[data-prompt-source][data-prompt-mode]")
        if len(sources) != 8:
            raise SystemExit(f"PROMPT_V2_SOURCE_COUNT:{locale}:{audience}:{intent}:{len(sources)}")
        total_sources += len(sources)
        modes = {(node.get("data-prompt-mode"), node.find_parent("details", attrs={"data-prompt-level": True})["data-prompt-level"]) for node in sources}
        if modes != {(mode, str(level)) for mode in ("template", "demo") for level in range(1, 5)}:
            raise SystemExit(f"PROMPT_V2_MODE_MATRIX:{locale}:{audience}:{intent}")
        allowed_optional = {item["text"] for item in cell["optional_clauses"]}
        for node in sources:
            text = node.get_text()
            mode = node["data-prompt-mode"]
            if "{{" in text or "}}" in text:
                raise SystemExit(f"PROMPT_V2_LEGACY_MARKER:{locale}:{audience}:{intent}:{mode}")
            squares = {value.strip() for value in re.findall(r"\[([^]]+)\]", text)}
            if mode == "demo":
                if re.search(r"<[^>]+>", text) or squares:
                    raise SystemExit(f"PROMPT_V2_DEMO_UNRESOLVED:{locale}:{audience}:{intent}")
                level = node.find_parent("details", attrs={"data-prompt-level": True})["data-prompt-level"]
                if level == "1" and any(re.search(pattern, text, re.I) for pattern in DEMO_GRAMMAR_PATTERNS[locale]):
                    raise SystemExit(f"PROMPT_V2_DEMO_GRAMMAR:{locale}:{audience}:{intent}")
            else:
                if not squares.issubset(allowed_optional):
                    raise SystemExit(f"PROMPT_V2_OPTIONAL_UNKNOWN:{locale}:{audience}:{intent}")
                for token in re.findall(r"<([^>]+)>", text):
                    if "|" in token or " · " not in token or example_label[locale] not in token:
                        raise SystemExit(f"PROMPT_V2_INPUT_UNEXPLAINED:{locale}:{audience}:{intent}:{token}")
        flow = library.find_parent("article").select_one(f'[data-prompt-flow="{intent}"]')
        if flow is None:
            raise SystemExit(f"PROMPT_V2_FLOW_UI_MISSING:{locale}:{audience}:{intent}")
        codes = [node.get_text(strip=True) for node in flow.select("code")]
        expected_output = artifact_labels[contracts[intent]["flow"]["produces"]][locale]
        if not codes or codes[-1] != expected_output:
            raise SystemExit(f"PROMPT_V2_FLOW_UI_ARTIFACT:{locale}:{audience}:{intent}:{codes}")
        if any(value in flow.get_text(" ") for value in OUTPUTS.values()):
            raise SystemExit(f"PROMPT_V2_FLOW_RAW_ARTIFACT:{locale}:{audience}:{intent}")
        total_flows += 1

if total_libraries != 162 or total_sources != 1296 or total_flows != 162:
    raise SystemExit(f"PROMPT_V2_TOTALS:libraries={total_libraries}:sources={total_sources}:flows={total_flows}")

runtime = (SRC / "site.js").read_text(encoding="utf-8")
if "URLSearchParams(location.search)" not in runtime or "searchParams.set('mode','demo')" not in runtime:
    raise SystemExit("PROMPT_V2_QUERY_MODE_MISSING")
storage_keys = set(re.findall(r"(?:readPreference|writePreference)\('([^']+)'", runtime))
if storage_keys - {"mdg_theme", "mdg_locale", "mdg_audience"}:
    raise SystemExit(f"PROMPT_V2_STORAGE_KEY:{sorted(storage_keys)}")

print(f"PROMPT_EXPERIENCE_V2_OK contracts={len(contracts)} libraries={total_libraries} prompts={total_sources} flows={total_flows} routes=2")
