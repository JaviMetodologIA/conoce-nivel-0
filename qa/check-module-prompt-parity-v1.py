#!/usr/bin/env python3
"""Fail-closed parity gate for the M2-M4 prompt libraries.

The gate reads authored module payloads and rendered HTML, but never writes a
report.  It independently checks the semantic N1-N4 projection, the
Template/Demo contract, locale and audience parity, and NotebookLM surfaces.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Sequence, Tuple

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DIST = ROOT / "dist"

LOCALES = ("es", "en", "pt")
AUDIENCES = ("persona", "empresa")
MODULE_ORDERS = (2, 3, 4)
INVENTORY_PATH = SRC / "module-01-prompt-inventory-v1.json"
COMPOSER_PATH = ROOT / "scripts" / "module_prompt_parity.py"
FORMAT_IDS = ("natural", "parameters", "spec", "pair")
KIND_SEQUENCE = ("direct",) * 10 + ("meta",) * 4
FAMILY_SEQUENCE = ("learn",) * 4 + ("embody",) * 4 + ("evolve",) * 2 + ("meta",) * 4
SLOT_SEQUENCE = tuple(f"{index:02d}" for index in range(1, 11)) + tuple(f"M{index}" for index in range(1, 5))
CARDS_PER_PAGE = 14
EXPECTED_PAGES = 18
EXPECTED_CARDS = 252
EXPECTED_TABS = 1008
EXPECTED_LEVELS = 1008
EXPECTED_TEXTAREAS = 2016
EXPECTED_SURFACES_PER_PAGE = {"chat": 12, "source_search": 2}
EXPECTED_SURFACES = {"chat": 216, "source_search": 36}
EXPECTED_KINDS = {"direct": 10, "meta": 4}
EXPECTED_FAMILIES = {"learn": 4, "embody": 4, "evolve": 2, "meta": 4}

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
        "demo_available": "Datos sintéticos disponibles:",
        "why": "Por qué funciona",
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
        "demo_available": "Available synthetic data:",
        "why": "Why it works",
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
        "demo_available": "Dados sintéticos disponíveis:",
        "why": "Por que funciona",
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
INPUT_KEY = re.compile(r"^[A-ZÁÉÍÓÚÜÑÂÊÔÃÕÇ_][A-Z0-9ÁÉÍÓÚÜÑÂÊÔÃÕÇ_]*$")
STABLE_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")


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


def canonical_self(value: Mapping[str, Any]) -> str:
    payload = {key: item for key, item in value.items() if key != "self_sha256"}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_golden_inventory() -> Dict[str, Any]:
    """Load M1 as the immutable parity authority, not as a loose hint."""

    inventory = load_json(INVENTORY_PATH)
    if (
        inventory.get("schema_version") != "module-01-prompt-inventory-v1"
        or inventory.get("inventory_id") != "nivel-zero-module-01-prompt-golden-v1"
        or inventory.get("authority") != "MetodologIA"
    ):
        fail("GOLDEN_IDENTITY")
    if inventory.get("state") != "RENDERED_DRAFT" or inventory.get("publication_authorized") is not False:
        fail("GOLDEN_GOVERNANCE")
    if (
        inventory.get("self_hash_model") != "sha256(sorted-json-without-self_sha256)"
        or inventory.get("self_sha256") != canonical_self(inventory)
    ):
        fail("GOLDEN_SELF_HASH")

    cardinality = inventory.get("cardinality")
    expected_cardinality = {
        "cards_per_variant": CARDS_PER_PAGE,
        "direct_prompts": EXPECTED_KINDS["direct"],
        "metaprompts": EXPECTED_KINDS["meta"],
        "levels_per_card": len(FORMAT_IDS),
        "modes_per_level": 2,
        "copyable_prompts_per_card": 8,
        "copyable_prompts_per_page": 112,
        "locales": len(LOCALES),
        "audiences": len(AUDIENCES),
        "page_variants": len(LOCALES) * len(AUDIENCES),
        "copyable_prompts_in_reference_matrix": 672,
        "chat_cards_per_variant": EXPECTED_SURFACES_PER_PAGE["chat"],
        "source_search_cards_per_variant": EXPECTED_SURFACES_PER_PAGE["source_search"],
    }
    if cardinality != expected_cardinality:
        fail("GOLDEN_CARDINALITY")

    direct_ids = tuple(str(index).zfill(2) for index in range(1, 11))
    meta_ids = tuple(f"M{index}" for index in range(1, 5))
    families = inventory.get("families")
    if (
        not isinstance(families, dict)
        or set(families) != {"direct", "meta"}
        or tuple(families["direct"].get("ids", ())) != direct_ids
        or tuple(families["meta"].get("ids", ())) != meta_ids
    ):
        fail("GOLDEN_KINDS")
    capability = inventory.get("capability_families")
    expected_capability = {
        "learn": {"ids": list(direct_ids[:4]), "count": 4},
        "embody": {"ids": list(direct_ids[4:8]), "count": 4},
        "evolve": {"ids": list(direct_ids[8:]), "count": 2},
        "meta": {"ids": list(meta_ids), "count": 4},
    }
    if capability != expected_capability:
        fail("GOLDEN_FAMILIES")

    levels = inventory.get("levels")
    if (
        not isinstance(levels, list)
        or len(levels) != len(FORMAT_IDS)
        or tuple(item.get("format_id") for item in levels if isinstance(item, dict)) != FORMAT_IDS
        or tuple(item.get("number") for item in levels if isinstance(item, dict)) != (1, 2, 3, 4)
    ):
        fail("GOLDEN_LEVELS")
    modes = inventory.get("modes")
    if (
        not isinstance(modes, dict)
        or set(modes) != {"template", "demo"}
        or modes["template"].get("count_per_card") != 4
        or modes["demo"].get("count_per_card") != 4
    ):
        fail("GOLDEN_MODES")
    ranges = inventory.get("editorial_ranges")
    if (
        not isinstance(ranges, dict)
        or ranges.get("inputs_per_card") != {"minimum": 2, "maximum": 6}
        or ranges.get("parameters_per_card") != {"minimum": 4, "maximum": 6}
    ):
        fail("GOLDEN_EDITORIAL_RANGES")

    cards = inventory.get("cards")
    if not isinstance(cards, list) or len(cards) != CARDS_PER_PAGE:
        fail("GOLDEN_CARDS")
    if (
        Counter(item.get("kind") for item in cards if isinstance(item, dict)) != Counter(EXPECTED_KINDS)
        or Counter(item.get("family_id") for item in cards if isinstance(item, dict)) != Counter(EXPECTED_FAMILIES)
        or Counter(item.get("surface") for item in cards if isinstance(item, dict)) != Counter(EXPECTED_SURFACES_PER_PAGE)
    ):
        fail("GOLDEN_DISTRIBUTIONS")

    bindings = inventory.get("source_contract_bindings")
    if not isinstance(bindings, dict) or set(bindings) != set((*direct_ids, *meta_ids)):
        fail("GOLDEN_BINDING_MATRIX")
    for intent_id, binding in bindings.items():
        if not isinstance(binding, dict) or set(binding) != {"ref", "raw_sha256", "self_sha256"}:
            fail("GOLDEN_BINDING_SHAPE", intent_id)
        ref = binding.get("ref")
        if not isinstance(ref, str):
            fail("GOLDEN_BINDING_REF", intent_id)
        path = SRC / ref
        if not path.is_file() or path.is_symlink() or sha256(path) != binding.get("raw_sha256"):
            fail("GOLDEN_BINDING_RAW_HASH", intent_id)
        contract = load_json(path)
        if contract.get("self_sha256") != binding.get("self_sha256"):
            fail("GOLDEN_BINDING_SELF_HASH", intent_id)

    surface_binding = inventory.get("surface_authority_binding")
    if not isinstance(surface_binding, dict) or set(surface_binding) != {"ref", "raw_sha256", "route_ids"}:
        fail("GOLDEN_SURFACE_BINDING")
    surface_path = SRC / str(surface_binding["ref"])
    if (
        not surface_path.is_file()
        or surface_path.is_symlink()
        or sha256(surface_path) != surface_binding.get("raw_sha256")
        or tuple(surface_binding.get("route_ids", ())) != (*direct_ids, *meta_ids)
    ):
        fail("GOLDEN_SURFACE_HASH")
    return inventory


def load_composer() -> Callable[[str, Mapping[str, Any], Mapping[str, Any]], Tuple[Mapping[str, Any], Mapping[str, Any]]]:
    """Load the deterministic composition helper without accepting legacy 8/10/8."""

    if not COMPOSER_PATH.is_file() or COMPOSER_PATH.is_symlink():
        fail("COMPOSER_MISSING", str(COMPOSER_PATH.relative_to(ROOT)))
    spec = importlib.util.spec_from_file_location("module_prompt_parity_gate", COMPOSER_PATH)
    if spec is None or spec.loader is None:
        fail("COMPOSER_IMPORT")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as error:
        fail("COMPOSER_IMPORT", str(error))
    composer = getattr(module, "compose_prompt_parity", None)
    if not callable(composer):
        fail("COMPOSER_API")
    return composer


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


def input_token(item: Mapping[str, Any], locale: str) -> str:
    return (
        f'{item["name"]} · {item["description"]} · '
        f'{LOCALIZED[locale]["example"]} {item["example"]}'
    )


def validate_template_inputs(
    text: str,
    locale: str,
    expected_inputs: Sequence[Mapping[str, Any]],
    where: str,
) -> None:
    if "{{" in text or "}}" in text:
        fail("TEMPLATE_LEGACY_INPUT", where)
    tokens = ANGLE_INPUT.findall(text)
    if not 2 <= len(expected_inputs) <= 6 or len(tokens) != len(expected_inputs):
        fail("TEMPLATE_INPUT_COUNT", f"{where}:actual={len(tokens)}:expected={len(expected_inputs)}")
    expected_tokens = [input_token(item, locale) for item in expected_inputs]
    if Counter(tokens) != Counter(expected_tokens):
        fail("TEMPLATE_INPUT_MATRIX", where)
    for token in tokens:
        parts = [part.strip() for part in token.split(" · ", 2)]
        if len(parts) != 3 or not INPUT_KEY.fullmatch(parts[0]) or not parts[1] or not parts[2].startswith(LOCALIZED[locale]["example"]):
            fail("TEMPLATE_INPUT_UNEXPLAINED", f"{where}:<{token}>")


def validate_demo(text: str, locale: str, where: str) -> None:
    if ANGLE_INPUT.search(text) or SQUARE_INPUT.search(text) or "{{" in text or "}}" in text:
        fail("DEMO_UNRESOLVED_INPUT", where)
    if not any(LOCALIZED[locale][label] in text for label in ("synthetic", "demo_available")):
        fail("DEMO_SYNTHETIC_LABEL", where)


def validate_parameters(text: str, locale: str, expected_count: int, where: str) -> Tuple[str, ...]:
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
    if not 4 <= expected_count <= 6 or len(parsed) != expected_count:
        fail("PARAMETER_COUNT", f"{where}:actual={len(parsed)}:expected={expected_count}")
    if not labels["core_parameters"].issubset(parsed) or any(not INPUT_KEY.fullmatch(key) for key in parsed):
        fail("PARAMETER_KEYS", f"{where}:{sorted(parsed)}")
    foreign_core = set().union(
        *(LOCALIZED[candidate]["core_parameters"] for candidate in LOCALES if candidate != locale)
    ) - labels["core_parameters"]
    if set(parsed) & foreign_core:
        fail("PARAMETER_LOCALE", f"{where}:{sorted(set(parsed) & foreign_core)}")
    return tuple(parsed)


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


def validate_n2(text: str, locale: str, expected_parameter_count: int, where: str) -> None:
    labels = LOCALIZED[locale]["n2"]
    required = (labels[0], labels[1], labels[3], labels[4], labels[5], labels[6], labels[7])
    ordered_once(text, required, "N2_HEADINGS", where)
    for index, heading in enumerate(required):
        section(text, heading, required[index + 1:], where)
    validate_parameters(text, locale, expected_parameter_count, where)
    if len(re.findall(r"(?m)^- \S", section(text, labels[4], labels[5:], where))) < 2:
        fail("N2_FRAMEWORKS", where)
    if len(re.findall(r"(?m)^\d+\. \S", section(text, labels[5], labels[6:], where))) < 2:
        fail("N2_WORKFLOW", where)
    if len(re.findall(r"(?m)^- \S", section(text, labels[6], labels[7:], where))) < 2:
        fail("N2_BOUNDARIES", where)
    if len(re.findall(r"(?m)^- \S", section(text, labels[7], (), where))) < 2:
        fail("N2_OUTPUT", where)


def validate_n3(
    text: str,
    locale: str,
    mode: str,
    module_id: str,
    prompt_id: str,
    surface: str,
    expected_parameter_count: int,
    where: str,
) -> None:
    labels = LOCALIZED[locale]
    if not text.startswith("# SPEC MetodologIA\nversion: 2.0\nstatus: executable\n"):
        fail("N3_HEADER", where)
    headings = (*labels["spec"], labels["provenance"], "## Metadata")
    ordered_once(text, headings, "N3_SECTIONS", where)
    for index, heading in enumerate(headings):
        section(text, heading, headings[index + 1:], where)
    validate_parameters(text, locale, expected_parameter_count, where)
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


def validate_n4(text: str, locale: str, expected_parameter_count: int, where: str) -> None:
    labels = LOCALIZED[locale]
    system_heading, user_heading = "# system", "# user"
    positions = ordered_once(text, (system_heading, user_heading), "N4_PAIR", where)
    if positions[0] != 0:
        fail("N4_SYSTEM_FIRST", where)
    system = section(text, system_heading, (user_heading,), where)
    user = section(text, user_heading, (), where)
    required_system = (labels["n2"][4], labels["n2"][6], "# Definition of Done")
    required_user = (
        labels["n2"][0], labels["n2"][1], labels["n2"][3], labels["n2"][5], labels["n2"][7],
    )
    ordered_once(system, required_system, "N4_SYSTEM_CONTRACT", where)
    ordered_once(user, required_user, "N4_USER_CONTRACT", where)
    validate_parameters(user, locale, expected_parameter_count, where)


def as_mapping(value: Any, code: str, where: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        fail(code, where)
    return value


def as_sequence(value: Any, code: str, where: str) -> Sequence[Any]:
    if not isinstance(value, list):
        fail(code, where)
    return value


def source_inputs(prompt: Mapping[str, Any], where: str) -> List[Dict[str, str]]:
    syntax = as_mapping(prompt.get("syntax"), "SOURCE_SYNTAX", where)
    raw_inputs = as_sequence(syntax.get("inputs"), "SOURCE_INPUTS", where)
    if not 2 <= len(raw_inputs) <= 6:
        fail("SOURCE_INPUT_COUNT", f"{where}:{len(raw_inputs)}")
    normalized: List[Dict[str, str]] = []
    for index, raw in enumerate(raw_inputs):
        item = as_mapping(raw, "SOURCE_INPUT", f"{where}:{index}")
        name = next(
            (
                str(item[key]).strip()
                for key in ("name", "label", "key")
                if isinstance(item.get(key), str) and str(item[key]).strip()
            ),
            "",
        )
        description = item.get("description", item.get("help"))
        example = item.get("example")
        if (
            not INPUT_KEY.fullmatch(name)
            or not isinstance(description, str)
            or not description.strip()
            or not isinstance(example, str)
            or not example.strip()
            or not isinstance(item.get("required"), bool)
        ):
            fail("SOURCE_INPUT_SHAPE", f"{where}:{index}")
        normalized.append({"name": name, "description": description.strip(), "example": example.strip()})
    if len({item["name"] for item in normalized}) != len(normalized):
        fail("SOURCE_INPUT_DUPLICATE", where)
    return normalized


def source_parameter_count(prompt: Mapping[str, Any], where: str) -> int:
    syntax = as_mapping(prompt.get("syntax"), "SOURCE_SYNTAX", where)
    raw = syntax.get("parameters")
    if isinstance(raw, dict):
        parameters = list(raw.items())
    elif isinstance(raw, list):
        parameters = []
        for index, raw_parameter in enumerate(raw):
            parameter = as_mapping(raw_parameter, "SOURCE_PARAMETER", f"{where}:{index}")
            parameters.append((parameter.get("key"), parameter.get("default")))
    else:
        fail("SOURCE_PARAMETERS", where)
    if not 4 <= len(parameters) <= 6:
        fail("SOURCE_PARAMETER_COUNT", f"{where}:{len(parameters)}")
    keys = []
    for key, value in parameters:
        if not isinstance(key, str) or not key.strip() or not isinstance(value, (str, int, float)) or isinstance(value, bool):
            fail("SOURCE_PARAMETER_SHAPE", where)
        keys.append(key.strip().casefold())
    if len(set(keys)) != len(keys):
        fail("SOURCE_PARAMETER_DUPLICATE", where)
    return len(parameters)


def validate_source_why(depth_prompt: Mapping[str, Any], where: str) -> None:
    for field in ("workflow", "frameworks", "guardrails", "acceptance_criteria", "edge_cases", "limits"):
        values = depth_prompt.get(field)
        if not isinstance(values, list) or not values or any(not isinstance(item, str) or not item.strip() for item in values):
            fail("SOURCE_WHY", f"{where}:{field}")
    if not isinstance(depth_prompt.get("tradeoff"), str) or not depth_prompt["tradeoff"].strip():
        fail("SOURCE_WHY", f"{where}:tradeoff")


def expected_variants(
    composer: Callable[[str, Mapping[str, Any], Mapping[str, Any]], Tuple[Mapping[str, Any], Mapping[str, Any]]]
) -> Tuple[Dict[Tuple[str, str, str], Dict[str, Any]], Dict[str, int]]:
    curriculum = load_json(SRC / "curriculum-spec-v2.json")
    classes = curriculum.get("classes")
    if not isinstance(classes, list):
        fail("CURRICULUM_CLASSES")
    selected = [item for item in classes if isinstance(item, dict) and item.get("order") in MODULE_ORDERS]
    if len(selected) != len(MODULE_ORDERS) or {item.get("order") for item in selected} != set(MODULE_ORDERS):
        fail("CURRICULUM_MODULE_MATRIX")

    variants: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    orders: Dict[str, int] = {}
    ids_by_module: Dict[str, List[str]] = {}
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
        depth_variants = depth.get("variants")
        if not isinstance(raw_variants, list) or len(raw_variants) != 6:
            fail("PAYLOAD_VARIANT_COUNT", str(order))
        if not isinstance(depth_variants, list) or len(depth_variants) != 6:
            fail("DEPTH_VARIANT_COUNT", str(order))
        depth_by_variant = {
            (item.get("locale"), item.get("audience")): item
            for item in depth_variants
            if isinstance(item, dict)
        }
        if set(depth_by_variant) != {(locale, audience) for locale in LOCALES for audience in AUDIENCES}:
            fail("DEPTH_VARIANT_MATRIX", str(order))
        orders[alias] = order
        for raw in raw_variants:
            if not isinstance(raw, dict):
                fail("PAYLOAD_VARIANT_TYPE", str(order))
            locale, audience = raw.get("locale"), raw.get("audience")
            key = (alias, locale, audience)
            if locale not in LOCALES or audience not in AUDIENCES or key in variants:
                fail("PAYLOAD_VARIANT_MATRIX", f"{order}:{locale}:{audience}")
            depth_variant = depth_by_variant[(locale, audience)]
            try:
                composed = composer(module_id, copy.deepcopy(raw), copy.deepcopy(depth_variant))
            except Exception as error:
                fail("COMPOSER_EXECUTION", f"{order}:{locale}:{audience}:{error}")
            if not isinstance(composed, tuple) or len(composed) != 2:
                fail("COMPOSER_RESULT", f"{order}:{locale}:{audience}")
            composed_variant = as_mapping(composed[0], "COMPOSER_VARIANT", f"{order}:{locale}:{audience}")
            composed_depth = as_mapping(composed[1], "COMPOSER_DEPTH", f"{order}:{locale}:{audience}")
            if composed_variant.get("locale") != locale or composed_variant.get("audience") != audience:
                fail("COMPOSER_VARIANT_IDENTITY", f"{order}:{locale}:{audience}")
            if composed_depth.get("locale") != locale or composed_depth.get("audience") != audience:
                fail("COMPOSER_DEPTH_IDENTITY", f"{order}:{locale}:{audience}")
            inner = as_mapping(composed_variant.get("module"), "COMPOSER_MODULE", f"{order}:{locale}:{audience}")
            if inner.get("moduleId") != module_id:
                fail("COMPOSER_MODULE_ID", f"{order}:{locale}:{audience}")
            library = as_mapping(inner.get("promptLibrary"), "COMPOSER_LIBRARY", f"{order}:{locale}:{audience}")
            prompts = as_sequence(library.get("prompts"), "COMPOSER_PROMPTS", f"{order}:{locale}:{audience}")
            depth_root = as_mapping(composed_depth.get("prompts"), "COMPOSER_DEPTH_PROMPTS", f"{order}:{locale}:{audience}")
            depth_prompts = as_sequence(depth_root.get("items"), "COMPOSER_DEPTH_ITEMS", f"{order}:{locale}:{audience}")
            if len(prompts) != CARDS_PER_PAGE or len(depth_prompts) != CARDS_PER_PAGE:
                fail("COMPOSED_PROMPT_COUNT", f"{order}:{locale}:{audience}:{len(prompts)}/{len(depth_prompts)}")
            prompt_ids = [item.get("id") for item in prompts if isinstance(item, dict)]
            if (
                len(prompt_ids) != CARDS_PER_PAGE
                or len(set(prompt_ids)) != CARDS_PER_PAGE
                or any(not isinstance(item, str) or not STABLE_ID.fullmatch(item) for item in prompt_ids)
                or [item.get("id") for item in depth_prompts if isinstance(item, dict)] != prompt_ids
            ):
                fail("COMPOSED_PROMPT_IDS", f"{order}:{locale}:{audience}")
            if module_id in ids_by_module and ids_by_module[module_id] != prompt_ids:
                fail("COMPOSED_PROMPT_ID_DRIFT", f"{order}:{locale}:{audience}")
            ids_by_module.setdefault(module_id, prompt_ids)

            raw_inner = as_mapping(raw.get("module"), "PAYLOAD_MODULE", f"{order}:{locale}:{audience}")
            raw_library = as_mapping(raw_inner.get("promptLibrary"), "PAYLOAD_LIBRARY", f"{order}:{locale}:{audience}")
            raw_prompts = as_sequence(raw_library.get("prompts"), "PAYLOAD_PROMPTS", f"{order}:{locale}:{audience}")
            raw_ids = [item.get("id") for item in raw_prompts if isinstance(item, dict)]
            if len(raw_ids) != len(raw_prompts) or not set(raw_ids).issubset(prompt_ids):
                fail("COMPOSED_BASE_COVERAGE", f"{order}:{locale}:{audience}")

            depth_by_id = {item["id"]: item for item in depth_prompts if isinstance(item, dict)}
            inputs_by_id: Dict[str, List[Dict[str, str]]] = {}
            parameters_by_id: Dict[str, int] = {}
            demo_artifacts: Dict[str, str] = {}
            for prompt_index, prompt in enumerate(prompts):
                if not isinstance(prompt, dict):
                    fail("COMPOSED_PROMPT_TYPE", f"{order}:{locale}:{audience}:{prompt_index}")
                prompt_id = prompt["id"]
                where_prompt = f"{order}:{locale}:{audience}:{prompt_id}"
                consumes = prompt.get("consumeIds")
                if not isinstance(consumes, list):
                    fail("COMPOSED_CONSUMES_TYPE", where_prompt)
                depth_prompt = as_mapping(depth_by_id[prompt_id], "COMPOSED_DEPTH_ITEM", where_prompt)
                validate_source_why(depth_prompt, where_prompt)
                inputs_by_id[prompt_id] = source_inputs(prompt, where_prompt)
                parameters_by_id[prompt_id] = source_parameter_count(prompt, where_prompt)
                if consumes:
                    artifact = depth_prompt.get("demo_artifact")
                    if not isinstance(artifact, str) or len(artifact.strip()) < 40:
                        fail("DEMO_ARTIFACT_MISSING", where_prompt)
                    demo_artifacts[prompt_id] = artifact.strip()
            kinds = [item.get("kind") for item in prompts]
            families = [item.get("family_id") for item in prompts]
            if tuple(kinds) != KIND_SEQUENCE:
                fail("COMPOSED_KIND_SEQUENCE", f"{order}:{locale}:{audience}:{kinds}")
            if tuple(families) != FAMILY_SEQUENCE:
                fail("COMPOSED_FAMILY_SEQUENCE", f"{order}:{locale}:{audience}:{families}")
            raw_surfaces = [item.get("surface") for item in prompts]
            surface_projection = {"chat": "chat", "sources": "source_search", "source_search": "source_search"}
            if any(surface not in surface_projection for surface in raw_surfaces):
                fail("COMPOSED_SURFACE", f"{order}:{locale}:{audience}:{raw_surfaces}")
            surfaces = [surface_projection[surface] for surface in raw_surfaces]
            if Counter(surfaces) != Counter(EXPECTED_SURFACES_PER_PAGE):
                fail("COMPOSED_SURFACE_MIX", f"{order}:{locale}:{audience}:{Counter(surfaces)}")
            variants[key] = {
                "order": order,
                "module_id": module_id,
                "prompt_ids": prompt_ids,
                "surfaces": surfaces,
                "kinds": kinds,
                "families": families,
                "slots": list(SLOT_SEQUENCE),
                "inputs": inputs_by_id,
                "parameter_counts": parameters_by_id,
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


def m1_prompt_ui_contract(locale: str, audience: str) -> Dict[str, Any]:
    """Read the rendered M1 homologue as the visual and interaction authority."""

    parts: List[str] = []
    if locale != "es":
        parts.append(locale)
    if audience == "empresa":
        parts.append("empresa")
    parts.extend(("prompts", "index.html"))
    path = DIST.joinpath(*parts)
    if not path.is_file() or path.is_symlink():
        fail("M1_UI_REFERENCE_MISSING", str(path.relative_to(ROOT)))
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    cards = soup.select("[data-library-prompt]")
    if len(cards) != CARDS_PER_PAGE:
        fail("M1_UI_REFERENCE_CARDS", f"{locale}:{audience}:{len(cards)}")
    first = cards[0]
    summary = one(first.select(".library-prompt-disclosure > summary"), "M1_UI_SUMMARY", locale)
    discovery = one(first.select(".prompt-card-discovery"), "M1_UI_DISCOVERY", locale)
    input_summary = one(first.select(".prompt-input-guide > summary"), "M1_UI_INPUT", locale)
    copy_button = one(first.select("[data-format-copy]"), "M1_UI_COPY", locale)
    surface_labels: Dict[str, str] = {}
    for card in cards:
        surface = card.get("data-notebook-surface")
        badge = one(card.select(".prompt-launch-badge strong"), "M1_UI_SURFACE", locale)
        label = badge.get_text(" ", strip=True)
        if surface in surface_labels and surface_labels[surface] != label:
            fail("M1_UI_SURFACE_DRIFT", f"{locale}:{audience}:{surface}")
        surface_labels[str(surface)] = label
    return {
        "family_labels": [
            one(card.select(".library-prompt-summary-copy .eyebrow"), "M1_UI_FAMILY", locale).get_text(" ", strip=True)
            for card in cards
        ],
        "summary_child_classes": [tuple(node.get("class", ())) for node in summary.find_all(recursive=False)],
        "discovery_text": discovery.get_text(" ", strip=True),
        "discovery_label": summary.get("data-discovery-label"),
        "mode_labels": [node.get_text(" ", strip=True) for node in first.select("[data-prompt-mode-select]")],
        "tab_labels": [node.get("aria-label") for node in first.select("[data-prompt-format]")],
        "tab_small_labels": [node.get_text(" ", strip=True) for node in first.select(".prompt-tab-copy small")],
        "input_summary": next(input_summary.stripped_strings, ""),
        "syntax": one(first.select(".prompt-syntax"), "M1_UI_SYNTAX", locale).get_text(" ", strip=True),
        "launch_small": one(first.select(".prompt-launch-badge small"), "M1_UI_LAUNCH", locale).get_text(" ", strip=True),
        "surface_labels": surface_labels,
        "copy_label": copy_button.get("data-copy-label"),
        "copied_label": copy_button.get("data-copied-label"),
        "copy_svg_count": len(copy_button.select("svg")),
    }


def validate_page(
    key: Tuple[str, str, str],
    path: Path,
    soup: BeautifulSoup,
    expected: Mapping[str, Any],
    golden_ui: Mapping[str, Any],
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
    if len(cards) != CARDS_PER_PAGE or len(cards) != len(expected["prompt_ids"]):
        fail("CARD_COUNT", f"{where_page}:count={len(cards)}")
    if [card.get("id") for card in cards] != expected["prompt_ids"]:
        fail("CARD_IDS", where_page)
    if Counter(card.get("data-prompt-kind") for card in cards) != Counter(EXPECTED_KINDS):
        fail("CARD_KIND_DISTRIBUTION", where_page)
    if Counter(card.get("data-prompt-family") for card in cards) != Counter(EXPECTED_FAMILIES):
        fail("CARD_FAMILY_DISTRIBUTION", where_page)
    if Counter(card.get("data-notebook-surface") for card in cards) != Counter(EXPECTED_SURFACES_PER_PAGE):
        fail("CARD_SURFACE_DISTRIBUTION", where_page)
    family_labels = [
        one(card.select(".library-prompt-summary-copy .eyebrow"), "CARD_FAMILY_LABEL", where_page).get_text(" ", strip=True)
        for card in cards
    ]
    if family_labels != golden_ui["family_labels"]:
        fail("M1_UI_FAMILY_PARITY", f"{where_page}:{family_labels}")
    direct_section = one(main.select("section#directos"), "DIRECT_SECTION", where_page)
    meta_section = one(main.select("section#metaprompts"), "META_SECTION", where_page)
    if len(direct_section.select("[data-library-prompt]")) != EXPECTED_KINDS["direct"]:
        fail("DIRECT_SECTION_COUNT", where_page)
    if len(meta_section.select("[data-library-prompt]")) != EXPECTED_KINDS["meta"]:
        fail("META_SECTION_COUNT", where_page)
    sources_by_prompt: Dict[str, Dict[Tuple[int, str], str]] = {}
    page_source_count = 0
    for prompt_id, expected_surface, expected_kind, expected_family, expected_slot, card in zip(
        expected["prompt_ids"], expected["surfaces"], expected["kinds"], expected["families"], expected["slots"], cards
    ):
        where_card = f"{where_page}:{prompt_id}"
        surface = card.get("data-notebook-surface")
        if surface != expected_surface:
            fail("CARD_SURFACE", f"{where_card}:{surface}!={expected_surface}")
        if card.get("data-prompt-kind") != expected_kind:
            fail("CARD_KIND", f"{where_card}:{card.get('data-prompt-kind')}!={expected_kind}")
        if card.get("data-prompt-family") != expected_family:
            fail("CARD_FAMILY", f"{where_card}:{card.get('data-prompt-family')}!={expected_family}")
        if card.get("data-prompt-slot") != expected_slot:
            fail("CARD_SLOT", f"{where_card}:{card.get('data-prompt-slot')}!={expected_slot}")
        totals[f"surface:{surface}"] += 1
        disclosure = one(card.select(".library-prompt-disclosure"), "DISCLOSURE_COUNT", where_card)
        if disclosure.has_attr("open"):
            fail("DISCLOSURE_DEFAULT", where_card)
        summary = one(card.select(".library-prompt-disclosure > summary"), "SUMMARY_COUNT", where_card)
        summary_classes = [tuple(node.get("class", ())) for node in summary.find_all(recursive=False)]
        if summary_classes != golden_ui["summary_child_classes"]:
            fail("M1_UI_SUMMARY_STRUCTURE", where_card)
        discovery = one(card.select(".prompt-card-discovery"), "DISCOVERY_CUE", where_card)
        if (
            discovery.get_text(" ", strip=True) != golden_ui["discovery_text"]
            or summary.get("data-discovery-label") != golden_ui["discovery_label"]
        ):
            fail("M1_UI_DISCOVERY_PARITY", where_card)
        badge = one(card.select(".prompt-launch-badge"), "LAUNCH_BADGE", where_card)
        badge_small = one(badge.select("small"), "LAUNCH_BADGE_LABEL", where_card).get_text(" ", strip=True)
        badge_strong = one(badge.select("strong"), "LAUNCH_BADGE_VALUE", where_card).get_text(" ", strip=True)
        if badge_small != golden_ui["launch_small"] or badge_strong != golden_ui["surface_labels"].get(surface):
            fail("M1_UI_LAUNCH_PARITY", f"{where_card}:{badge_small}:{badge_strong}")
        if len(card.select(".prompt-flow")) != 1 or len(card.select(".prompt-flow nav")) != 1:
            fail("M1_UI_FLOW", where_card)
        library = one(card.select("[data-prompt-library]"), "LIBRARY_COUNT", where_card)
        mode_buttons = [node.get("data-prompt-mode-select") for node in library.select("[data-prompt-mode-select]")]
        if mode_buttons != ["template", "demo"]:
            fail("MODE_CONTROLS", f"{where_card}:{mode_buttons}")
        if [node.get_text(" ", strip=True) for node in library.select("[data-prompt-mode-select]")] != golden_ui["mode_labels"]:
            fail("M1_UI_MODE_LABELS", where_card)
        tab_matrix = [
            (node.get("data-prompt-format"), node.get("data-level-number"))
            for node in library.select("[data-prompt-format]")
        ]
        if tab_matrix != [(format_id, str(level)) for level, format_id in enumerate(FORMAT_IDS, 1)]:
            fail("LEVEL_TABS", f"{where_card}:{tab_matrix}")
        if (
            [node.get("aria-label") for node in library.select("[data-prompt-format]")] != golden_ui["tab_labels"]
            or [node.get_text(" ", strip=True) for node in library.select(".prompt-tab-copy small")] != golden_ui["tab_small_labels"]
        ):
            fail("M1_UI_LEVEL_LABELS", where_card)
        syntax = one(library.select(".prompt-syntax"), "PROMPT_SYNTAX", where_card).get_text(" ", strip=True)
        if syntax != golden_ui["syntax"]:
            fail("M1_UI_SYNTAX_PARITY", where_card)
        copy_button = one(library.select("[data-format-copy]"), "COPY_BUTTON", where_card)
        if (
            copy_button.get("data-copy-label") != golden_ui["copy_label"]
            or copy_button.get("data-copied-label") != golden_ui["copied_label"]
            or len(copy_button.select("svg")) != golden_ui["copy_svg_count"]
        ):
            fail("M1_UI_COPY_PARITY", where_card)
        totals["tabs"] += len(tab_matrix)
        levels = library.select("details[data-prompt-level]")
        if [node.get("data-prompt-level") for node in levels] != ["1", "2", "3", "4"]:
            fail("LEVEL_MATRIX", where_card)
        expected_inputs = expected["inputs"][prompt_id]
        expected_parameter_count = expected["parameter_counts"][prompt_id]
        input_guide = one(card.select("details.prompt-input-guide"), "INPUT_GUIDE", where_card)
        input_summary = one(input_guide.select(":scope > summary"), "INPUT_GUIDE_SUMMARY", where_card)
        if next(input_summary.stripped_strings, "") != golden_ui["input_summary"]:
            fail("M1_UI_INPUT_LABEL", where_card)
        guide_lists = input_guide.select("ul")
        if len(guide_lists) != 2:
            fail("INPUT_GUIDE_LISTS", where_card)
        guide_names = [node.get_text(strip=True).strip("<>") for node in guide_lists[0].select("li code")]
        if guide_names != [item["name"] for item in expected_inputs] or not 2 <= len(guide_names) <= 6:
            fail("INPUT_GUIDE_MATRIX", f"{where_card}:{guide_names}")
        why = one(
            card.select("details.prompt-contract-depth[data-prompt-why]"),
            "WHY_UI",
            where_card,
        )
        why_title = why.select_one("summary strong")
        why_sections = why.select(".prompt-why-body > section")
        if (
            why_title is None
            or why_title.get_text(" ", strip=True) != LOCALIZED[locale]["why"]
            or len(why_sections) != 5
            or any(section_node.select_one("h4") is None or not section_node.select("li") for section_node in why_sections)
        ):
            fail("WHY_UI_CONTRACT", where_card)
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
                    validate_template_inputs(text, locale, expected_inputs, where)
                else:
                    validate_demo(text, locale, where)
                    artifact = expected["demo_artifacts"].get(prompt_id)
                    if artifact is not None and artifact not in text:
                        fail("DEMO_ARTIFACT_NOT_RENDERED", where)
                if number == 1:
                    validate_n1(text, locale, where)
                elif number == 2:
                    validate_n2(text, locale, expected_parameter_count, where)
                elif number == 3:
                    validate_n3(
                        text, locale, mode, expected["module_id"], prompt_id, surface,
                        expected_parameter_count, where,
                    )
                else:
                    validate_n4(text, locale, expected_parameter_count, where)
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
    validate_golden_inventory()
    composer = load_composer()
    expected, orders = expected_variants(composer)
    rendered = rendered_pages(orders)
    if set(rendered) != set(expected):
        fail("PAGE_MATRIX", f"missing={sorted(set(expected)-set(rendered))}:extra={sorted(set(rendered)-set(expected))}")
    totals: Counter = Counter()
    extracted: Dict[Tuple[str, str, str], Dict[str, Dict[Tuple[int, str], str]]] = {}
    golden_ui = {
        (locale, audience): m1_prompt_ui_contract(locale, audience)
        for locale in LOCALES
        for audience in AUDIENCES
    }
    for key in sorted(expected):
        path, soup = rendered[key]
        extracted[key] = validate_page(key, path, soup, expected[key], golden_ui[(key[1], key[2])], totals)
    pairs = validate_audience_parity(extracted)
    actual = (totals["pages"], totals["cards"], totals["tabs"], totals["levels"], totals["textareas"])
    wanted = (EXPECTED_PAGES, EXPECTED_CARDS, EXPECTED_TABS, EXPECTED_LEVELS, EXPECTED_TEXTAREAS)
    if actual != wanted:
        fail("TOTALS", f"actual={actual}:wanted={wanted}")
    surfaces = {surface: totals[f"surface:{surface}"] for surface in EXPECTED_SURFACES}
    if surfaces != EXPECTED_SURFACES:
        fail("SURFACE_TOTALS", f"actual={surfaces}:wanted={EXPECTED_SURFACES}")
    print(
        "[EVIDENCE:MODULE_PROMPT_PARITY] MODULE_PROMPT_PARITY_OK "
        f"pages={totals['pages']} cards={totals['cards']} tabs={totals['tabs']} levels={totals['levels']} "
        f"textareas={totals['textareas']} locales={len(LOCALES)} audiences={len(AUDIENCES)} "
        f"direct={EXPECTED_KINDS['direct'] * EXPECTED_PAGES} meta={EXPECTED_KINDS['meta'] * EXPECTED_PAGES} "
        f"families=learn:{EXPECTED_FAMILIES['learn'] * EXPECTED_PAGES},embody:{EXPECTED_FAMILIES['embody'] * EXPECTED_PAGES},"
        f"evolve:{EXPECTED_FAMILIES['evolve'] * EXPECTED_PAGES},meta:{EXPECTED_FAMILIES['meta'] * EXPECTED_PAGES} "
        f"audience_pairs={pairs} chat={surfaces['chat']} source_search={surfaces['source_search']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
