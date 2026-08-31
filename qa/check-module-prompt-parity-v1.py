#!/usr/bin/env python3
"""Fail-closed parity gate for the M2-M4 prompt libraries.

The gate reads authored module payloads and rendered HTML, but never writes a
report.  It independently checks the semantic N1-N4 projection, the
Template/Demo contract, locale and audience parity, and NotebookLM surfaces.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DIST = ROOT / "dist"

LOCALES = ("es", "en", "pt")
AUDIENCES = ("persona", "empresa")
MODULE_COUNTS = {2: 8, 3: 10, 4: 8}
EXPECTED_PAGES = 18
EXPECTED_CARDS = 156
EXPECTED_LEVELS = 624
EXPECTED_TEXTAREAS = 1248
EXPECTED_SURFACES = {"chat": 132, "source_search": 24}

LOCALIZED: Mapping[str, Mapping[str, Any]] = {
    "es": {
        "n1": ("Objetivo", "Datos", "Aplica", "Orden", "Entrega", "Límite"),
        "n2": (
            "# PARÁMETROS",
            "# INPUTS",
            "# Ajustes opcionales",
            "# Tarea",
            "# MARCOS Y BUENAS PRÁCTICAS",
            "# Flujo",
            "# Límites",
            "# Salida esperada",
        ),
        "spec": (
            "## S — Situación",
            "## P — Propósito y alcance",
            "## E — Estándares y ejecución",
            "## C — Criterios verificables",
        ),
        "provenance": "## Procedencia",
        "case_data": "Datos del caso",
        "synthetic": "Demo sintética",
        "authorities": "Autoridades declaradas:",
        "policy": "no expongas razonamiento privado ni cadena de pensamiento.",
        "example": "ej.:",
        "parameters": {
            "ESTRUCTURA": {"tabla breve + decisión", "tabla breve + veredicto"},
            "LONGITUD": {"concisa"},
            "PROFUNDIDAD": {"ejecutiva", "operativa"},
            "APROBACIÓN": {"humana obligatoria"},
        },
        "core_parameters": {"ESTRUCTURA", "LONGITUD", "PROFUNDIDAD"},
    },
    "en": {
        "n1": ("Objective", "Data", "Apply", "Order", "Deliver", "Boundary"),
        "n2": (
            "# PARAMETERS",
            "# INPUTS",
            "# Optional adjustments",
            "# Task",
            "# FRAMEWORKS AND BEST PRACTICES",
            "# Workflow",
            "# Boundaries",
            "# Expected output",
        ),
        "spec": (
            "## S — Situation",
            "## P — Purpose and scope",
            "## E — Standards and execution",
            "## C — Verifiable criteria",
        ),
        "provenance": "## Provenance",
        "case_data": "Case data",
        "synthetic": "Synthetic demo",
        "authorities": "Declared authorities:",
        "policy": "do not expose private reasoning or chain of thought.",
        "example": "e.g.:",
        "parameters": {
            "STRUCTURE": {"short table + decision", "short table + verdict"},
            "LENGTH": {"concise"},
            "DEPTH": {"executive", "operational"},
            "APPROVAL": {"human required"},
        },
        "core_parameters": {"STRUCTURE", "LENGTH", "DEPTH"},
    },
    "pt": {
        "n1": ("Objetivo", "Dados", "Aplique", "Ordem", "Entregue", "Limite"),
        "n2": (
            "# PARÂMETROS",
            "# INPUTS",
            "# Ajustes opcionais",
            "# Tarefa",
            "# FRAMEWORKS E BOAS PRÁTICAS",
            "# Fluxo",
            "# Limites",
            "# Saída esperada",
        ),
        "spec": (
            "## S — Situação",
            "## P — Propósito e escopo",
            "## E — Padrões e execução",
            "## C — Critérios verificáveis",
        ),
        "provenance": "## Procedência",
        "case_data": "Dados do caso",
        "synthetic": "Demo sintética",
        "authorities": "Autoridades declaradas:",
        "policy": "não exponha raciocínio privado nem cadeia de pensamento.",
        "example": "ex.:",
        "parameters": {
            "ESTRUTURA": {"tabela breve + decisão", "tabela breve + veredito"},
            "EXTENSÃO": {"concisa"},
            "PROFUNDIDADE": {"executiva", "operacional"},
            "APROVAÇÃO": {"humana obrigatória"},
        },
        "core_parameters": {"ESTRUTURA", "EXTENSÃO", "PROFUNDIDADE"},
    },
}

ANGLE_INPUT = re.compile(r"<([^<>\n]+)>")
SQUARE_INPUT = re.compile(r"\[[^\[\]\n]+\]")
INPUT_KEY = re.compile(r"^[A-ZÁÉÍÓÚÂÊÔÃÕÇ_][A-Z0-9ÁÉÍÓÚÂÊÔÃÕÇ_]*$")


def fail(code: str, where: str = "") -> None:
    suffix = f":{where}" if where else ""
    raise SystemExit(f"MODULE_PROMPT_PARITY_{code}{suffix}")


def load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        fail("SOURCE_MISSING", str(path.relative_to(ROOT)))
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        fail("SOURCE_INVALID", f"{path.relative_to(ROOT)}:{error}")
    if not isinstance(value, dict):
        fail("SOURCE_NOT_OBJECT", str(path.relative_to(ROOT)))
    return value


def one(nodes: Sequence[Any], code: str, where: str) -> Any:
    if len(nodes) != 1:
        fail(code, f"{where}:count={len(nodes)}")
    return nodes[0]


def ordered_once(text: str, headings: Sequence[str], code: str, where: str) -> List[int]:
    positions: List[int] = []
    for heading in headings:
        matches = list(re.finditer(rf"(?m)^{re.escape(heading)}\s*$", text))
        if len(matches) != 1:
            fail(code, f"{where}:{heading}:count={len(matches)}")
        positions.append(matches[0].start())
    if positions != sorted(positions) or len(set(positions)) != len(positions):
        fail(code, f"{where}:order")
    return positions


def section(text: str, heading: str, following: Sequence[str], where: str) -> str:
    start_match = re.search(rf"(?m)^{re.escape(heading)}\s*$", text)
    if start_match is None:
        fail("SECTION_MISSING", f"{where}:{heading}")
    end = len(text)
    for candidate in following:
        match = re.search(rf"(?m)^{re.escape(candidate)}\s*$", text[start_match.end():])
        if match is not None:
            end = min(end, start_match.end() + match.start())
    value = text[start_match.end():end].strip()
    if not value:
        fail("SECTION_EMPTY", f"{where}:{heading}")
    return value


def validate_template_inputs(text: str, locale: str, where: str) -> None:
    if "{{" in text or "}}" in text:
        fail("TEMPLATE_LEGACY_INPUT", where)
    tokens = ANGLE_INPUT.findall(text)
    if len(tokens) != 1:
        fail("TEMPLATE_INPUT_COUNT", f"{where}:count={len(tokens)}")
    parts = [part.strip() for part in tokens[0].split(" · ")]
    if len(parts) < 3 or not INPUT_KEY.fullmatch(parts[0]) or LOCALIZED[locale]["example"] not in parts[-1]:
        fail("TEMPLATE_INPUT_UNEXPLAINED", f"{where}:<{tokens[0]}>")


def validate_demo(text: str, locale: str, where: str) -> None:
    if ANGLE_INPUT.search(text) or SQUARE_INPUT.search(text) or "{{" in text or "}}" in text:
        fail("DEMO_UNRESOLVED_INPUT", where)
    if LOCALIZED[locale]["synthetic"] not in text:
        fail("DEMO_SYNTHETIC_LABEL", where)


def validate_parameters(text: str, locale: str, where: str) -> None:
    labels = LOCALIZED[locale]
    heading = labels["n2"][0]
    block = section(text, heading, labels["n2"][1:], where)
    parsed: Dict[str, str] = {}
    for line in block.splitlines():
        match = re.fullmatch(r"([^=]+?)\s*=\s*(\S(?:.*\S)?)", line)
        if match is None:
            fail("PARAMETER_SYNTAX", f"{where}:{line}")
        key, value = match.group(1).strip(), match.group(2).strip()
        if key in parsed:
            fail("PARAMETER_DUPLICATE", f"{where}:{key}")
        parsed[key] = value
    allowed = labels["parameters"]
    if not labels["core_parameters"].issubset(parsed) or not set(parsed).issubset(allowed):
        fail("PARAMETER_KEYS", f"{where}:{sorted(parsed)}")
    for key, value in parsed.items():
        if value not in allowed[key]:
            fail("PARAMETER_VALUE", f"{where}:{key}={value}")


def validate_n1(text: str, locale: str, where: str) -> None:
    labels = LOCALIZED[locale]["n1"]
    patterns = [rf"(?m)^{re.escape(label)}:\s*(\S.*)$" for label in labels]
    matches = []
    for label, pattern in zip(labels, patterns):
        found = list(re.finditer(pattern, text))
        if len(found) != 1:
            fail("N1_SEMANTIC_FIELD", f"{where}:{label}:count={len(found)}")
        matches.append(found[0])
    if [match.start() for match in matches] != sorted(match.start() for match in matches):
        fail("N1_SEMANTIC_ORDER", where)
    values = [match.group(1).strip() for match in matches]
    if "=" not in values[1] or len([item for item in values[2].split(";") if item.strip()]) < 2:
        fail("N1_DATA_OR_FRAMEWORKS", where)
    if "→" not in values[3] or ";" not in values[4]:
        fail("N1_FLOW_OR_DELIVERABLE", where)


def validate_n2(text: str, locale: str, where: str) -> None:
    headings = LOCALIZED[locale]["n2"]
    ordered_once(text, headings, "N2_HEADINGS", where)
    for index, heading in enumerate(headings):
        section(text, heading, headings[index + 1:], where)
    validate_parameters(text, locale, where)
    if len(re.findall(r"(?m)^- \S", section(text, headings[4], headings[5:], where))) < 2:
        fail("N2_FRAMEWORKS", where)
    if len(re.findall(r"(?m)^\d+\. \S", section(text, headings[5], headings[6:], where))) < 2:
        fail("N2_WORKFLOW", where)
    if len(re.findall(r"(?m)^- \S", section(text, headings[6], headings[7:], where))) < 2:
        fail("N2_BOUNDARIES", where)
    if len(re.findall(r"(?m)^- \S", section(text, headings[7], (), where))) < 2:
        fail("N2_OUTPUT", where)


def validate_n3(
    text: str,
    locale: str,
    mode: str,
    module_id: str,
    prompt_id: str,
    surface: str,
    where: str,
) -> None:
    labels = LOCALIZED[locale]
    if not text.startswith("# SPEC MetodologIA\nversion: 2.0\nstatus: executable\n"):
        fail("N3_HEADER", where)
    headings = (*labels["spec"], labels["provenance"], "## Metadata")
    ordered_once(text, headings, "N3_SECTIONS", where)
    for index, heading in enumerate(headings):
        section(text, heading, headings[index + 1:], where)
    validate_parameters(text, locale, where)
    if "# Definition of Done:" not in text or "Trade-off:" not in text:
        fail("N3_ACCEPTANCE", where)
    provenance = section(text, labels["provenance"], ("## Metadata",), where)
    expected_origin = labels["synthetic"] if mode == "demo" else labels["case_data"]
    if expected_origin not in provenance or labels["authorities"] not in provenance:
        fail("N3_PROVENANCE", where)
    metadata = section(text, "## Metadata", (), where)
    metadata_lines = {}
    for line in metadata.splitlines():
        match = re.fullmatch(r"- (module|prompt|surface): (\S(?:.*\S)?)", line)
        if match is not None:
            metadata_lines[match.group(1)] = match.group(2)
    module_code = re.match(r"module-(\d{2})-", module_id)
    allowed_module_values = {module_id}
    if module_code is not None:
        allowed_module_values.add(module_code.group(1))
    if (
        set(metadata_lines) != {"module", "prompt", "surface"}
        or metadata_lines["module"] not in allowed_module_values
        or metadata_lines["prompt"] != prompt_id
        or metadata_lines["surface"] != surface
    ):
        fail("N3_METADATA", f"{where}:actual={metadata_lines}")
    if not text.rstrip().endswith(labels["policy"]):
        fail("N3_REASONING_POLICY", where)


def validate_n4(text: str, locale: str, where: str) -> None:
    labels = LOCALIZED[locale]
    system_heading, user_heading = "# system", "# user"
    positions = ordered_once(text, (system_heading, user_heading), "N4_PAIR", where)
    if positions[0] != 0:
        fail("N4_SYSTEM_FIRST", where)
    system = section(text, system_heading, (user_heading,), where)
    user = section(text, user_heading, (), where)
    required_system = (labels["n2"][4], labels["n2"][6], "# Definition of Done")
    required_user = (
        labels["n2"][0], labels["n2"][1], labels["n2"][2],
        labels["n2"][3], labels["n2"][5], labels["n2"][7],
    )
    ordered_once(system, required_system, "N4_SYSTEM_CONTRACT", where)
    ordered_once(user, required_user, "N4_USER_CONTRACT", where)
    validate_parameters(user, locale, where)


def expected_variants() -> Tuple[Dict[Tuple[str, str, str], Dict[str, Any]], Dict[str, int]]:
    curriculum = load_json(SRC / "curriculum-spec-v2.json")
    classes = curriculum.get("classes")
    if not isinstance(classes, list):
        fail("CURRICULUM_CLASSES")
    selected = [item for item in classes if isinstance(item, dict) and item.get("order") in MODULE_COUNTS]
    if len(selected) != len(MODULE_COUNTS) or {item.get("order") for item in selected} != set(MODULE_COUNTS):
        fail("CURRICULUM_MODULE_MATRIX")

    variants: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    orders: Dict[str, int] = {}
    for module in selected:
        order = module["order"]
        alias = module.get("id")
        module_id = module.get("module_id")
        content = module.get("content")
        validation = module.get("variant_validation")
        if (
            not isinstance(alias, str)
            or not isinstance(module_id, str)
            or not isinstance(content, dict)
            or not isinstance(content.get("ref"), str)
            or not isinstance(validation, dict)
            or validation.get("exact_variants") != 6
            or validation.get("prompts_per_variant") != MODULE_COUNTS[order]
        ):
            fail("CURRICULUM_MODULE_CONTRACT", str(order))
        depth_ref = module.get("depth_overlay")
        if not isinstance(depth_ref, dict) or not isinstance(depth_ref.get("ref"), str):
            fail("CURRICULUM_DEPTH_CONTRACT", str(order))
        payload = load_json(SRC / content["ref"])
        depth = load_json(SRC / depth_ref["ref"])
        if payload.get("moduleId") != module_id:
            fail("PAYLOAD_MODULE_ID", str(order))
        raw_variants = payload.get("variants")
        if not isinstance(raw_variants, list) or len(raw_variants) != 6:
            fail("PAYLOAD_VARIANT_COUNT", str(order))
        depth_variants = depth.get("variants")
        if not isinstance(depth_variants, list) or len(depth_variants) != 6:
            fail("DEPTH_VARIANT_COUNT", str(order))
        depth_by_variant = {
            (item.get("locale"), item.get("audience")): item
            for item in depth_variants
            if isinstance(item, dict)
        }
        if len(depth_by_variant) != 6:
            fail("DEPTH_VARIANT_MATRIX", str(order))
        orders[alias] = order
        for raw in raw_variants:
            if not isinstance(raw, dict):
                fail("PAYLOAD_VARIANT_TYPE", str(order))
            locale, audience = raw.get("locale"), raw.get("audience")
            key = (alias, locale, audience)
            if locale not in LOCALES or audience not in AUDIENCES or key in variants:
                fail("PAYLOAD_VARIANT_MATRIX", f"{order}:{locale}:{audience}")
            inner = raw.get("module")
            library = inner.get("promptLibrary") if isinstance(inner, dict) else None
            prompts = library.get("prompts") if isinstance(library, dict) else None
            if not isinstance(prompts, list) or len(prompts) != MODULE_COUNTS[order]:
                fail("PAYLOAD_PROMPT_COUNT", f"{order}:{locale}:{audience}")
            expected_ids = [f"prompt-{index:02d}" for index in range(1, MODULE_COUNTS[order] + 1)]
            if [item.get("id") for item in prompts if isinstance(item, dict)] != expected_ids:
                fail("PAYLOAD_PROMPT_IDS", f"{order}:{locale}:{audience}")
            depth_variant = depth_by_variant.get((locale, audience))
            depth_prompts_root = depth_variant.get("prompts") if isinstance(depth_variant, dict) else None
            depth_prompts = depth_prompts_root.get("items") if isinstance(depth_prompts_root, dict) else None
            if not isinstance(depth_prompts, list) or [item.get("id") for item in depth_prompts if isinstance(item, dict)] != expected_ids:
                fail("DEPTH_PROMPT_IDS", f"{order}:{locale}:{audience}")
            depth_by_id = {item["id"]: item for item in depth_prompts}
            demo_artifacts: Dict[str, str] = {}
            for prompt in prompts:
                if not isinstance(prompt, dict):
                    fail("PAYLOAD_PROMPT_TYPE", f"{order}:{locale}:{audience}")
                consumes = prompt.get("consumeIds")
                if not isinstance(consumes, list):
                    fail("PAYLOAD_CONSUMES_TYPE", f"{order}:{locale}:{audience}:{prompt.get('id')}")
                if consumes:
                    artifact = depth_by_id[prompt["id"]].get("demo_artifact")
                    if not isinstance(artifact, str) or len(artifact.strip()) < 40:
                        fail("DEMO_ARTIFACT_MISSING", f"{order}:{locale}:{audience}:{prompt['id']}")
                    demo_artifacts[prompt["id"]] = artifact.strip()
            if len(set(demo_artifacts.values())) != len(demo_artifacts):
                fail("DEMO_ARTIFACT_DUPLICATE", f"{order}:{locale}:{audience}")
            raw_surfaces = [item.get("surface") for item in prompts]
            surface_projection = {"chat": "chat", "sources": "source_search"}
            if any(surface not in surface_projection for surface in raw_surfaces):
                fail("PAYLOAD_SURFACE", f"{order}:{locale}:{audience}:{raw_surfaces}")
            surfaces = [surface_projection[surface] for surface in raw_surfaces]
            variants[key] = {
                "order": order,
                "module_id": module_id,
                "prompt_ids": expected_ids,
                "surfaces": surfaces,
                "demo_artifacts": demo_artifacts,
            }
    expected_keys = {
        (alias, locale, audience)
        for alias in orders
        for locale in LOCALES
        for audience in AUDIENCES
    }
    if set(variants) != expected_keys:
        fail("PAYLOAD_VARIANT_MATRIX")
    return variants, orders


def rendered_pages(orders: Mapping[str, int]) -> Dict[Tuple[str, str, str], Tuple[Path, BeautifulSoup]]:
    pages: Dict[Tuple[str, str, str], Tuple[Path, BeautifulSoup]] = {}
    if not DIST.is_dir():
        fail("DIST_MISSING")
    for path in sorted(DIST.rglob("index.html")):
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            fail("HTML_READ", f"{path.relative_to(ROOT)}:{error}")
        if 'data-page="prompts"' not in raw:
            continue
        soup = BeautifulSoup(raw, "html.parser")
        if soup.body is None or soup.html is None:
            fail("HTML_IDENTITY", str(path.relative_to(ROOT)))
        alias = soup.body.get("data-module-id")
        if alias == "ia-panorama":
            continue
        if alias not in orders:
            fail("HTML_MODULE_UNKNOWN", f"{path.relative_to(ROOT)}:{alias}")
        locale, audience = soup.html.get("lang"), soup.html.get("data-audience")
        key = (alias, locale, audience)
        if locale not in LOCALES or audience not in AUDIENCES or key in pages:
            fail("HTML_VARIANT_MATRIX", f"{path.relative_to(ROOT)}:{locale}:{audience}")
        pages[key] = (path, soup)
    if len(pages) != EXPECTED_PAGES:
        fail("PAGE_COUNT", f"{len(pages)}!={EXPECTED_PAGES}")
    return pages


def validate_page(
    key: Tuple[str, str, str],
    path: Path,
    soup: BeautifulSoup,
    expected: Mapping[str, Any],
    totals: Counter,
) -> Dict[str, Dict[Tuple[int, str], str]]:
    alias, locale, audience = key
    route = str(path.relative_to(DIST))
    where_page = f"{expected['order']}:{locale}:{audience}:{route}"
    main = one(soup.select('main[data-module-resource="prompts"]'), "MAIN_COUNT", where_page)
    if (
        main.get("data-module-id") != expected["module_id"]
        or main.get("data-module-order") != str(expected["order"])
        or main.get("data-locale") != locale
        or main.get("data-audience") != audience
    ):
        fail("MAIN_IDENTITY", where_page)

    guides = soup.select("[data-notebook-execution-guide]")
    if len(guides) != 1:
        fail("NOTEBOOK_GUIDE", f"{where_page}:count={len(guides)}")
    guide = guides[0]
    tabs = {node.get("data-notebook-tab") for node in guide.select("[data-notebook-tab]")}
    panels = {node.get("data-notebook-panel") for node in guide.select("[data-notebook-panel]")}
    filters = {node.get("data-prompt-surface-filter") for node in main.select("[data-prompt-surface-filter]")}
    if tabs != set(EXPECTED_SURFACES) or panels != set(EXPECTED_SURFACES) or filters != {"all", *EXPECTED_SURFACES}:
        fail("NOTEBOOK_SURFACES", where_page)

    cards = main.select("[data-library-prompt]")
    if len(cards) != len(expected["prompt_ids"]):
        fail("CARD_COUNT", f"{where_page}:count={len(cards)}")
    if [card.get("id") for card in cards] != expected["prompt_ids"]:
        fail("CARD_IDS", where_page)
    sources_by_prompt: Dict[str, Dict[Tuple[int, str], str]] = {}
    page_source_count = 0
    for prompt_id, expected_surface, card in zip(expected["prompt_ids"], expected["surfaces"], cards):
        where_card = f"{where_page}:{prompt_id}"
        surface = card.get("data-notebook-surface")
        if surface != expected_surface:
            fail("CARD_SURFACE", f"{where_card}:{surface}!={expected_surface}")
        totals[f"surface:{surface}"] += 1
        library = one(card.select("[data-prompt-library]"), "LIBRARY_COUNT", where_card)
        mode_buttons = [node.get("data-prompt-mode-select") for node in library.select("[data-prompt-mode-select]")]
        if mode_buttons != ["template", "demo"]:
            fail("MODE_CONTROLS", f"{where_card}:{mode_buttons}")
        tab_matrix = [
            (node.get("data-prompt-format"), node.get("data-level-number"))
            for node in library.select("[data-prompt-format]")
        ]
        if tab_matrix != [(f"n{level}", str(level)) for level in range(1, 5)]:
            fail("LEVEL_TABS", f"{where_card}:{tab_matrix}")
        levels = library.select("details[data-prompt-level]")
        if [node.get("data-prompt-level") for node in levels] != ["1", "2", "3", "4"]:
            fail("LEVEL_MATRIX", where_card)
        prompt_sources: Dict[Tuple[int, str], str] = {}
        for number, level in enumerate(levels, 1):
            nodes = level.select("textarea[data-prompt-source][data-prompt-mode]")
            modes = [node.get("data-prompt-mode") for node in nodes]
            if len(nodes) != 2 or set(modes) != {"template", "demo"}:
                fail("TEXTAREA_MATRIX", f"{where_card}:n{number}:{modes}")
            for mode in ("template", "demo"):
                node = one([item for item in nodes if item.get("data-prompt-mode") == mode], "TEXTAREA_MODE", where_card)
                text = node.get_text()
                where = f"{where_card}:n{number}:{mode}"
                if not text.strip():
                    fail("TEXTAREA_EMPTY", where)
                if mode == "template":
                    validate_template_inputs(text, locale, where)
                else:
                    validate_demo(text, locale, where)
                    artifact = expected["demo_artifacts"].get(prompt_id)
                    if artifact is not None and artifact not in text:
                        fail("DEMO_ARTIFACT_NOT_RENDERED", where)
                if number == 1:
                    validate_n1(text, locale, where)
                elif number == 2:
                    validate_n2(text, locale, where)
                elif number == 3:
                    validate_n3(text, locale, mode, expected["module_id"], prompt_id, surface, where)
                else:
                    validate_n4(text, locale, where)
                prompt_sources[(number, mode)] = text
                page_source_count += 1
                totals["textareas"] += 1
            if prompt_sources[(number, "template")] == prompt_sources[(number, "demo")]:
                fail("MODE_NOT_DISTINCT", f"{where_card}:n{number}")
            totals["levels"] += 1
        sources_by_prompt[prompt_id] = prompt_sources
        totals["cards"] += 1
    if len(main.select("textarea[data-prompt-source]")) != page_source_count:
        fail("TEXTAREA_STRAY", where_page)
    totals["pages"] += 1
    return sources_by_prompt


def validate_audience_parity(
    pages: Mapping[Tuple[str, str, str], Dict[str, Dict[Tuple[int, str], str]]]
) -> int:
    pairs = 0
    aliases = sorted({key[0] for key in pages})
    for alias in aliases:
        for locale in LOCALES:
            persona = pages[(alias, locale, "persona")]
            empresa = pages[(alias, locale, "empresa")]
            if list(persona) != list(empresa):
                fail("AUDIENCE_PROMPT_IDS", f"{alias}:{locale}")
            for prompt_id in persona:
                left, right = persona[prompt_id], empresa[prompt_id]
                if set(left) != set(right):
                    fail("AUDIENCE_SOURCE_MATRIX", f"{alias}:{locale}:{prompt_id}")
                changed = sum(left[cell] != right[cell] for cell in left)
                if left[(1, "template")] == right[(1, "template")] or left[(1, "demo")] == right[(1, "demo")]:
                    fail("AUDIENCE_N1_NOT_DISTINCT", f"{alias}:{locale}:{prompt_id}")
                if changed < 6:
                    fail("AUDIENCE_NOT_MATERIAL", f"{alias}:{locale}:{prompt_id}:changed={changed}/8")
            pairs += 1
    return pairs


def main() -> int:
    expected, orders = expected_variants()
    rendered = rendered_pages(orders)
    if set(rendered) != set(expected):
        fail("PAGE_MATRIX", f"missing={sorted(set(expected)-set(rendered))}:extra={sorted(set(rendered)-set(expected))}")
    totals: Counter = Counter()
    extracted: Dict[Tuple[str, str, str], Dict[str, Dict[Tuple[int, str], str]]] = {}
    for key in sorted(expected):
        path, soup = rendered[key]
        extracted[key] = validate_page(key, path, soup, expected[key], totals)
    pairs = validate_audience_parity(extracted)
    actual = (totals["pages"], totals["cards"], totals["levels"], totals["textareas"])
    wanted = (EXPECTED_PAGES, EXPECTED_CARDS, EXPECTED_LEVELS, EXPECTED_TEXTAREAS)
    if actual != wanted:
        fail("TOTALS", f"actual={actual}:wanted={wanted}")
    surfaces = {surface: totals[f"surface:{surface}"] for surface in EXPECTED_SURFACES}
    if surfaces != EXPECTED_SURFACES:
        fail("SURFACE_TOTALS", f"actual={surfaces}:wanted={EXPECTED_SURFACES}")
    print(
        "[EVIDENCE:MODULE_PROMPT_PARITY] MODULE_PROMPT_PARITY_OK "
        f"pages={totals['pages']} cards={totals['cards']} levels={totals['levels']} "
        f"textareas={totals['textareas']} locales={len(LOCALES)} audiences={len(AUDIENCES)} "
        f"audience_pairs={pairs} chat={surfaces['chat']} source_search={surfaces['source_search']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
