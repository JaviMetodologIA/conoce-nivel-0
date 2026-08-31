#!/usr/bin/env python3
"""Fail-closed golden gate for the Module 01 prompt-library inventory.

This gate deliberately freezes both representations of every M1 library
contract: the raw source bytes and the canonical self hash.  The governed
inventory may describe the reference, but it cannot redefine it by changing
the inventory and the contracts together.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DIST = ROOT / "dist"
INVENTORY_PATH = SRC / "module-01-prompt-inventory-v1.json"
CONTRACTS_DIR = SRC / "prompt-contracts"
NOTEBOOK_PATH = SRC / "notebooklm-execution-spec-v1.json"
LEVELS_PATH = SRC / "workbook-advanced-v1.json"

LOCALES = ("es", "en", "pt")
AUDIENCES = ("persona", "empresa")
DIRECT_IDS = tuple(f"{index:02d}" for index in range(1, 11))
META_IDS = ("M1", "M2", "M3", "M4")
IDS = DIRECT_IDS + META_IDS

# A version change is required to move this golden.  Raw hashes prevent a
# co-mutated contract from silently becoming its own authority; self hashes
# independently verify the semantic document model.
CONTRACT_GOLDEN = {
    "01": ("library-01.json", "b8a28013751ae1dc24840c011b7c660041b7ac712c75c68caa4d63f4885c49b5", "9b176eb85561b23e7c90e2f405b8130fe5e4a0631d6c048a3a05c2fa5b5b427c"),
    "02": ("library-02.json", "3eda15bf22f0bea7a46ae0ab0799d7a32f0468742742864d0762271bd2827fa7", "371b5b8a700c9dfa75e1dcaf1774136df0579d3aeb03eff21ab2b54731bad74b"),
    "03": ("library-03.json", "a13438203a109ddbfdc10fb41c45c350fe3dee7f4ea20e5205d2c2ffb4ae8455", "373602755437353946223c83480f0f1e5f1b0170bcc2d7e65cafe74a162169fe"),
    "04": ("library-04.json", "32be7e3e2dd29068c744efe7c8115dc3f045e7525e8cbd5342796a47294e8874", "9eccb14ed4a19b94c15c7fa892408915aa51b9f8ff13b887d2ce96280c1eac0a"),
    "05": ("library-05.json", "9d33799b1c6ccc58e727c3a8899d215542d608555778c3a0cae0c01bb7ef1b10", "ea629704313b0aee25376f82f8979a47267417ef087329a21987c5284a10d685"),
    "06": ("library-06.json", "e95e84b45910a5fd99e0d5c47385c5f5a6621dd75b38e9a7a46130632d34a50a", "0acc6a54f8589785aa72ce840faf8e26460b5417fe80e44d02121a98e8af03c2"),
    "07": ("library-07.json", "d6d0ef09efadbeedc932a62f6f51b1ad634423f73565e9dbe8f764fa7497b3dd", "9bb117c049802c52ea315f7f0971f4feca675ad0bad3eabe8e14ba4200ad0dd4"),
    "08": ("library-08.json", "6b23ac8a30049bc74d1d46dfdbdab3d846fb13f18c7c2aedff5bdede12302883", "b843c632d9b8ce7b670e8f3e71e2dabd9bcc82087581bc9b5ca4bbde8918f3f4"),
    "09": ("library-09.json", "305fafa099a6af7e16f27ede646ae3779121d5ae03fd0fa7f221174a3ad8bab8", "d845a1b59469146ee8cdc1641c4af36a6653c12c1778ca56c8b16a5f769a1f2e"),
    "10": ("library-10.json", "9761b46a238396acb0c3c370b579af819a292d407fba58ba7f4d8913e48c3e3d", "93a2171ef84e4110c5fa52962c87cca2073e3ee9330702cf4c354dcd56abd724"),
    "M1": ("library-m1.json", "8327864125eab7e4f278bfed62ae9b82608a89ed6242abb4b3ffcaf9973279f3", "9186290e48deea29cf79d4eb4ae3898c6e16b8e2997c7df14cd298de4ff2ad60"),
    "M2": ("library-m2.json", "f7e5a9e9fbc29f89dd2e8a5fa81f3f247257bc77d78a195df46bd455b67354e5", "2f13eb2bf7ba4bd613742a856e7d59f2267cc4ab8a9b8d9555aa4dc9a710ddb9"),
    "M3": ("library-m3.json", "424e9a9da5ed0d0a4b6598f7e65460a3f851c53edce62f977a1127fa6ffb66c6", "63b66163786d9cbdc0b5603c212a6364b0ad1cb07abf22f346ee2b1c9622169e"),
    "M4": ("library-m4.json", "f9f8cdb6ef821203f7795b400ec46a134113bba955e7245e18bea02a34be38a7", "039d0532820c2c94214b24a83ec5f2a536e26cab1595b9258344055e11b69873"),
}

ROOT_FIELDS = {
    "schema_version", "inventory_id", "authority", "state",
    "publication_authorized", "reference_module", "cardinality", "families",
    "levels", "modes", "contract_anatomy", "editorial_ranges", "cards",
    "parity_policy", "source_contract_self_sha256", "self_hash_model",
    "self_sha256",
    "ecosystem_cardinality", "capability_families", "editorial_floors",
    "source_contract_bindings", "surface_authority_binding",
}
CONTRACT_FIELDS = {
    "schema_version", "intent_id", "surface", "phase", "state",
    "publication_authorized", "boundary", "locales", "self_hash_model",
    "self_sha256", "flow",
}
CELL_FIELDS = {
    "title", "purpose", "when", "example", "evidence", "prompt",
    "level_spec", "why_it_works", "traceability", "inputs", "parameters",
    "optional_clauses",
}
LEVEL_SPEC_FIELDS = {
    "role", "spec_role", "objective", "constraints", "frameworks",
    "workflow", "guardrails", "output", "dod", "edge_cases",
}
WHY_FIELDS = {
    "acceptance_criteria", "edge_cases", "tradeoffs", "assumptions", "limits",
}
INPUT_FIELDS = {
    "key", "label", "help", "example", "required", "type", "source",
    "demo_value",
}
PARAMETER_FIELDS = {"key", "label", "default", "choices"}
OPTIONAL_FIELDS = {"key", "text", "default_enabled"}
FLOW_FIELDS = {
    "route", "order", "previous", "next", "branches", "consumes",
    "produces", "external_gate", "loop_to", "standalone",
}

EXPECTED_CARDINALITY = {
    "cards_per_variant": 14,
    "direct_prompts": 10,
    "metaprompts": 4,
    "levels_per_card": 4,
    "modes_per_level": 2,
    "copyable_prompts_per_card": 8,
    "copyable_prompts_per_page": 112,
    "locales": 3,
    "audiences": 2,
    "page_variants": 6,
    "copyable_prompts_in_reference_matrix": 672,
    "chat_cards_per_variant": 12,
    "source_search_cards_per_variant": 2,
}
EXPECTED_PHASES = Counter({"Aprender": 4, "Aprehender": 4, "(R)Evolucionar": 2, "Metaprompt": 4})
MATERIAL_FLOORS = {"purpose": 45, "when": 35, "example": 35, "evidence": 40, "prompt": 300}
NOTEBOOK_RAW_SHA256 = "92cc587b975dfceec4726d2a044088b08397a37353c1c2e7d2d7817bbb36fdd9"
EXPECTED_RANGES = {
    "inputs_per_card": {"minimum": 2, "maximum": 6},
    "parameters_per_card": {"minimum": 4, "maximum": 6},
    "acceptance_criteria": {"minimum": 3, "maximum": 4},
    "edge_cases": {"minimum": 2, "maximum": 3},
    "tradeoffs": {"minimum": 1, "maximum": 5},
    "assumptions": {"minimum": 1, "maximum": 2},
    "limits": {"minimum": 1, "maximum": 3},
    "traceability_claims": {"minimum": 3, "maximum": 5},
}
EXPECTED_DEPTH_RANGES = {
    "frameworks": (3, 3),
    "workflow": (5, 6),
    "guardrails": (3, 5),
    "output": (3, 4),
    "constraints": (4, 5),
    "level_edge_cases": (3, 3),
}
EXPECTED_FORMATS = ("natural", "parameters", "spec", "pair")
FORMAT_EXAMPLE = {"es": "ej.", "en": "e.g.", "pt": "ex."}

N1_FIELDS = {
    "es": ("Objetivo", "Datos", "Aplica", "Orden", "Entrega", "Límite"),
    "en": ("Objective", "Data", "Apply", "Order", "Deliver", "Boundary"),
    "pt": ("Objetivo", "Dados", "Aplique", "Ordem", "Entregue", "Limite"),
}
N2_HEADINGS = {
    "es": ("# PARÁMETROS", "# INPUTS", "# Tarea", "# MARCOS Y BUENAS PRÁCTICAS", "# Flujo", "# Límites", "# Salida esperada"),
    "en": ("# PARAMETERS", "# INPUTS", "# Task", "# FRAMEWORKS AND BEST PRACTICES", "# Workflow", "# Boundaries", "# Expected output"),
    "pt": ("# PARÂMETROS", "# INPUTS", "# Tarefa", "# FRAMEWORKS E BOAS PRÁTICAS", "# Fluxo", "# Limites", "# Saída esperada"),
}
N3_HEADINGS = {
    "es": ("## S — Situación", "## P — Pedido", "## E — Ejecución", "## C — Criterio", "## Etiquetas de procedencia", "## Metadata de cierre"),
    "en": ("## S — Situation", "## P — Request", "## E — Execution", "## C — Criterion", "## Provenance tags", "## Closing metadata"),
    "pt": ("## S — Situação", "## P — Pedido", "## E — Execução", "## C — Critério", "## Etiquetas de procedência", "## Metadados de encerramento"),
}


def fail(code: str, where: str = "") -> None:
    raise SystemExit(f"MODULE_01_PROMPT_INVENTORY_{code}{':' + where if where else ''}")


def canonical_self(document: dict[str, Any]) -> str:
    payload = {key: value for key, value in document.items() if key != "self_sha256"}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def read_json(path: Path, code: str) -> tuple[dict[str, Any], bytes]:
    if not path.is_file() or path.is_symlink():
        fail(code, str(path.relative_to(ROOT)))
    raw = path.read_bytes()
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        fail(code, f"{path.relative_to(ROOT)}:{error}")
    if not isinstance(document, dict):
        fail(code, f"{path.relative_to(ROOT)}:not_object")
    return document, raw


def reseal(document: dict[str, Any]) -> dict[str, Any]:
    document["self_sha256"] = canonical_self(document)
    return document


def load_contracts() -> dict[str, dict[str, Any]]:
    contracts: dict[str, dict[str, Any]] = {}
    for intent_id, (filename, raw_sha, self_sha) in CONTRACT_GOLDEN.items():
        path = CONTRACTS_DIR / filename
        contract, raw = read_json(path, "CONTRACT_MISSING_OR_INVALID")
        if hashlib.sha256(raw).hexdigest() != raw_sha:
            fail("CONTRACT_RAW_DRIFT", intent_id)
        if contract.get("self_sha256") != self_sha or canonical_self(contract) != self_sha:
            fail("CONTRACT_SELF_DRIFT", intent_id)
        if contract.get("intent_id") != intent_id:
            fail("CONTRACT_ID", intent_id)
        contracts[intent_id] = contract
    actual_files = {path.name for path in CONTRACTS_DIR.glob("library-*.json")}
    expected_files = {value[0] for value in CONTRACT_GOLDEN.values()}
    if actual_files != expected_files:
        fail("CONTRACT_FILE_SET", f"actual={sorted(actual_files)}")
    return contracts


def validate_contract_matrix(contracts: dict[str, dict[str, Any]]) -> dict[str, dict[str, int]]:
    measures: dict[str, list[int]] = {
        "inputs_per_card": [], "parameters_per_card": [],
        "acceptance_criteria": [], "edge_cases": [], "tradeoffs": [],
        "assumptions": [], "limits": [], "traceability_claims": [],
        **{key: [] for key in EXPECTED_DEPTH_RANGES},
    }
    for intent_id in IDS:
        contract = contracts[intent_id]
        if set(contract) != CONTRACT_FIELDS or contract.get("schema_version") != "prompt-intent-contract-v2":
            fail("CONTRACT_SHAPE", intent_id)
        if contract.get("surface") != "library" or contract.get("state") != "RENDERED_DRAFT" or contract.get("publication_authorized") is not False:
            fail("CONTRACT_GOVERNANCE", intent_id)
        if contract.get("self_hash_model") != "sha256(sorted-json-without-self_sha256)":
            fail("CONTRACT_HASH_MODEL", intent_id)
        if set(contract.get("flow", {})) != FLOW_FIELDS or contract["flow"].get("standalone") is not True:
            fail("CONTRACT_FLOW", intent_id)
        if set(contract.get("locales", {})) != set(LOCALES):
            fail("CONTRACT_LOCALES", intent_id)
        for locale in LOCALES:
            cells = contract["locales"][locale]
            if set(cells) != set(AUDIENCES):
                fail("CONTRACT_AUDIENCES", f"{intent_id}:{locale}")
            for field in ("purpose", "when", "example", "evidence", "prompt"):
                if cells["persona"].get(field) == cells["empresa"].get(field):
                    fail("CONTRACT_AUDIENCE_CLONE", f"{intent_id}:{locale}:{field}")
            for audience in AUDIENCES:
                where = f"{intent_id}:{locale}:{audience}"
                cell = cells[audience]
                if set(cell) != CELL_FIELDS:
                    fail("CELL_SHAPE", where)
                if any(not isinstance(cell[key], str) or not cell[key].strip() for key in ("title", "purpose", "when", "example", "evidence", "prompt")):
                    fail("CELL_COPY", where)
                for key, minimum in MATERIAL_FLOORS.items():
                    if len(cell[key].strip()) < minimum:
                        fail("CELL_MATERIAL_FLOOR", f"{where}:{key}")
                inputs = cell["inputs"]
                parameters = cell["parameters"]
                optionals = cell["optional_clauses"]
                if not 2 <= len(inputs) <= 6:
                    fail("CELL_INPUT_COUNT", where)
                if not 4 <= len(parameters) <= 6:
                    fail("CELL_PARAMETER_COUNT", where)
                if not 0 <= len(optionals) <= 1:
                    fail("CELL_OPTIONAL_COUNT", where)
                if len({item.get("key") for item in inputs}) != len(inputs):
                    fail("CELL_INPUT_DUPLICATE", where)
                for item in inputs:
                    if set(item) != INPUT_FIELDS or item.get("required") is not True or item.get("type") not in {"text", "long_text"} or item.get("source") not in {"user", "previous_output"}:
                        fail("CELL_INPUT", where)
                    if any(not isinstance(item.get(key), str) or not item[key].strip() for key in ("key", "label", "help", "example", "demo_value")):
                        fail("CELL_INPUT_COPY", where)
                    if f"<{item['label']}>" not in cell["prompt"]:
                        fail("CELL_INPUT_UNUSED", f"{where}:{item['key']}")
                for item in parameters:
                    if set(item) != PARAMETER_FIELDS or not item.get("choices") or item.get("default") not in item["choices"]:
                        fail("CELL_PARAMETER", where)
                for item in optionals:
                    if set(item) != OPTIONAL_FIELDS or item.get("default_enabled") is not True or not isinstance(item.get("text"), str) or not item["text"].strip():
                        fail("CELL_OPTIONAL", where)
                level_spec = cell["level_spec"]
                why = cell["why_it_works"]
                if set(level_spec) != LEVEL_SPEC_FIELDS or set(why) != WHY_FIELDS:
                    fail("CELL_LEVEL_OR_WHY_SHAPE", where)
                if any(not isinstance(level_spec[key], str) or not level_spec[key].strip() for key in ("role", "spec_role", "objective", "dod")):
                    fail("CELL_LEVEL_COPY", where)
                if any(not isinstance(level_spec[key], list) or not level_spec[key] for key in ("constraints", "frameworks", "workflow", "guardrails", "output", "edge_cases")):
                    fail("CELL_LEVEL_LIST", where)
                if any(not isinstance(why[key], list) or not why[key] for key in WHY_FIELDS):
                    fail("CELL_WHY_LIST", where)
                if not isinstance(cell["traceability"], list) or not cell["traceability"]:
                    fail("CELL_TRACEABILITY", where)
                measures["inputs_per_card"].append(len(inputs))
                measures["parameters_per_card"].append(len(parameters))
                measures["traceability_claims"].append(len(cell["traceability"]))
                for key in WHY_FIELDS:
                    measures[key].append(len(why[key]))
                measures["frameworks"].append(len(level_spec["frameworks"]))
                measures["workflow"].append(len(level_spec["workflow"]))
                measures["guardrails"].append(len(level_spec["guardrails"]))
                measures["output"].append(len(level_spec["output"]))
                measures["constraints"].append(len(level_spec["constraints"]))
                measures["level_edge_cases"].append(len(level_spec["edge_cases"]))
    observed = {key: {"minimum": min(values), "maximum": max(values)} for key, values in measures.items()}
    for key, bounds in EXPECTED_DEPTH_RANGES.items():
        if (observed[key]["minimum"], observed[key]["maximum"]) != bounds:
            fail("CONTRACT_DEPTH_RANGE", f"{key}:{observed[key]}")
    return observed


def expected_levels(levels_document: dict[str, Any]) -> list[dict[str, Any]]:
    semantics = (
        ["objective", "data", "frameworks", "order", "deliverables", "boundary"],
        ["parameters", "inputs", "optional_clauses", "task", "frameworks", "workflow", "boundaries", "expected_output"],
        ["spec_header", "situation", "purpose", "standards", "verifiable_criteria", "definition_of_done", "provenance", "metadata", "private_reasoning_policy"],
        ["system_rules", "user_case_data", "frameworks", "boundaries", "definition_of_done", "parameters", "inputs", "workflow", "expected_output"],
    )
    names = {locale: levels_document["locales"][locale]["level_convention"]["items"] for locale in LOCALES}
    if any(tuple(item["key"] for item in names[locale]) != EXPECTED_FORMATS for locale in LOCALES):
        fail("LEVEL_SOURCE_FORMATS")
    return [
        {
            "number": index + 1,
            "format_id": format_id,
            "name": {locale: names[locale][index]["name"] for locale in LOCALES},
            "required_semantics": semantics[index],
        }
        for index, format_id in enumerate(EXPECTED_FORMATS)
    ]


def expected_cards(contracts: dict[str, dict[str, Any]], notebook: dict[str, Any]) -> list[dict[str, Any]]:
    cards = []
    for intent_id in IDS:
        contract = contracts[intent_id]
        flow = contract["flow"]
        route = notebook["intent_routes"][intent_id]
        cards.append({
            "id": intent_id,
            "kind": "meta" if intent_id.startswith("M") else "direct",
            "family_id": (
                "learn" if intent_id in {"01", "02", "03", "04"}
                else "embody" if intent_id in {"05", "06", "07", "08"}
                else "evolve" if intent_id in {"09", "10"}
                else "meta"
            ),
            "phase": contract["phase"],
            "surface": route["launch"],
            "mode": route["mode"],
            "title_es": contract["locales"]["es"]["persona"]["title"],
            "consumes": flow["consumes"],
            "produces": flow["produces"],
            "external_gate": flow["external_gate"],
        })
    return cards


def validate_inventory(
    inventory: dict[str, Any],
    contracts: dict[str, dict[str, Any]],
    notebook: dict[str, Any],
    levels_document: dict[str, Any],
    observed: dict[str, dict[str, int]],
) -> None:
    if set(inventory) != ROOT_FIELDS:
        fail("ROOT_FIELDS")
    if inventory.get("schema_version") != "module-01-prompt-inventory-v1" or inventory.get("inventory_id") != "nivel-zero-module-01-prompt-golden-v1" or inventory.get("authority") != "MetodologIA":
        fail("IDENTITY")
    if inventory.get("state") != "RENDERED_DRAFT" or inventory.get("publication_authorized") is not False:
        fail("GOVERNANCE")
    if inventory.get("self_hash_model") != "sha256(sorted-json-without-self_sha256)" or inventory.get("self_sha256") != canonical_self(inventory):
        fail("SELF_HASH")
    if inventory.get("reference_module") != {
        "module_id": "ia-panorama",
        "display_name": "IA: qué está pasando y cómo sacarle provecho",
        "technical_order": 1,
        "route": "/prompts/",
        "source_contract": "prompt-intent-contract-v2",
    }:
        fail("REFERENCE_MODULE")
    if inventory.get("cardinality") != EXPECTED_CARDINALITY:
        fail("CARDINALITY")
    if inventory.get("ecosystem_cardinality") != {
        "visible_library_contracts": 14,
        "workbook_preparation_contracts": 3,
        "workbook_route_contracts": 10,
        "total_module_prompt_contracts": 27,
        "localized_components": 162,
        "copyable_prompts_across_four_levels_and_two_modes": 1296,
        "parity_scope_of_this_inventory": "visible-prompt-library",
        "integral_module_parity_status": "separate-future-gate",
    }:
        fail("ECOSYSTEM_CARDINALITY")
    families = inventory.get("families", {})
    if set(families) != {"direct", "meta"} or tuple(families["direct"].get("ids", ())) != DIRECT_IDS or tuple(families["meta"].get("ids", ())) != META_IDS:
        fail("FAMILIES")
    if inventory.get("capability_families") != {
        "learn": {"ids": ["01", "02", "03", "04"], "count": 4},
        "embody": {"ids": ["05", "06", "07", "08"], "count": 4},
        "evolve": {"ids": ["09", "10"], "count": 2},
        "meta": {"ids": ["M1", "M2", "M3", "M4"], "count": 4},
    }:
        fail("CAPABILITY_FAMILIES")
    if inventory.get("levels") != expected_levels(levels_document):
        fail("LEVELS")
    expected_modes = {
        "template": {
            "count_per_card": 4,
            "requirements": ["explained_angle_inputs", "localized_examples", "editable_parameters", "removable_optional_clauses", "no_demo_values"],
        },
        "demo": {
            "count_per_card": 4,
            "requirements": ["all_inputs_resolved", "synthetic_label", "runnable_without_user_input", "no_angle_or_square_placeholders", "same_logic_as_template"],
        },
    }
    if inventory.get("modes") != expected_modes:
        fail("MODES")
    if inventory.get("editorial_ranges") != EXPECTED_RANGES:
        fail("EDITORIAL_RANGES")
    if inventory.get("editorial_floors") != {
        "material_characters": MATERIAL_FLOORS,
        "level_spec": {
            "workflow": {"minimum": 5, "maximum": 6},
            "frameworks": {"exact": 3},
            "guardrails": {"minimum": 3, "maximum": 5},
            "edge_cases": {"exact": 3},
            "output": {"minimum": 3, "maximum": 4},
            "constraints": {"minimum": 4, "maximum": 5},
        },
        "required_non_empty": ["role", "spec_role", "objective", "definition_of_done"],
    }:
        fail("EDITORIAL_FLOORS")
    for key, expected in EXPECTED_RANGES.items():
        if observed[key] != expected:
            fail("EDITORIAL_OBSERVED", f"{key}:{observed[key]}")
    if inventory.get("cards") != expected_cards(contracts, notebook):
        fail("CARD_BINDING")
    if Counter(card["phase"] for card in inventory["cards"]) != EXPECTED_PHASES:
        fail("PHASE_DISTRIBUTION")
    if Counter(card["kind"] for card in inventory["cards"]) != Counter({"direct": 10, "meta": 4}):
        fail("FAMILY_DISTRIBUTION")
    if Counter(card["surface"] for card in inventory["cards"]) != Counter({"chat": 12, "source_search": 2}):
        fail("SURFACE_DISTRIBUTION")
    expected_selfs = {intent_id: CONTRACT_GOLDEN[intent_id][2] for intent_id in IDS}
    if inventory.get("source_contract_self_sha256") != expected_selfs:
        fail("CONTRACT_SELF_BINDING")
    expected_bindings = {
        intent_id: {
            "ref": f"prompt-contracts/{CONTRACT_GOLDEN[intent_id][0]}",
            "raw_sha256": CONTRACT_GOLDEN[intent_id][1],
            "self_sha256": CONTRACT_GOLDEN[intent_id][2],
        }
        for intent_id in IDS
    }
    if inventory.get("source_contract_bindings") != expected_bindings:
        fail("CONTRACT_RAW_SELF_BINDINGS")
    if inventory.get("surface_authority_binding") != {
        "ref": "notebooklm-execution-spec-v1.json",
        "raw_sha256": NOTEBOOK_RAW_SHA256,
        "route_ids": list(IDS),
    }:
        fail("SURFACE_AUTHORITY_BINDING")
    parity = inventory.get("parity_policy", {})
    if parity != {
        "applies_to": ["module-02-de-ocupado-a-productivo", "module-03-trabajo-amplificado", "module-04-trabajo-agentico"],
        "exact_cardinality_required": True,
        "exact_family_distribution_required": True,
        "exact_level_and_mode_semantics_required": True,
        "exact_surface_distribution_required": True,
        "editorial_ranges_required": True,
        "literal_copy_identity_required": False,
        "module_specific_purpose_required": True,
        "fallback_to_reference_copy": "forbidden",
    }:
        fail("PARITY_POLICY")
    anatomy = inventory.get("contract_anatomy", {})
    if set(anatomy) != {"root_fields", "localized_cell_fields", "card_ui", "why_it_works_sections", "flow_fields"}:
        fail("ANATOMY_FIELDS")
    if set(anatomy["root_fields"]) != CONTRACT_FIELDS or set(anatomy["localized_cell_fields"]) != CELL_FIELDS or set(anatomy["why_it_works_sections"]) != WHY_FIELDS or set(anatomy["flow_fields"]) != FLOW_FIELDS:
        fail("ANATOMY_BINDING")


def page_path(locale: str, audience: str) -> Path:
    parts: list[str] = []
    if locale != "es":
        parts.append(locale)
    if audience == "empresa":
        parts.append("empresa")
    return DIST.joinpath(*parts, "prompts", "index.html")


def resolved_demo(template: str, cell: dict[str, Any], locale: str) -> str:
    value = template
    for item in cell["inputs"]:
        token = f'<{item["label"]} · {item["help"]} · {FORMAT_EXAMPLE[locale]}: {item["example"]}>'
        value = value.replace(token, item["demo_value"])
    for item in cell["optional_clauses"]:
        value = value.replace(f'[{item["text"]}]', item["text"] if item["default_enabled"] else "")
    return value


def validate_level_semantics(text: str, locale: str, level: int, where: str) -> None:
    if level == 1:
        positions = []
        for label in N1_FIELDS[locale]:
            matches = list(re.finditer(rf"(?m)^{re.escape(label)}:\s+\S", text))
            if len(matches) != 1:
                fail("RENDER_N1_FIELD", f"{where}:{label}")
            positions.append(matches[0].start())
        if positions != sorted(positions):
            fail("RENDER_N1_ORDER", where)
    elif level == 2:
        positions = [text.find(heading) for heading in N2_HEADINGS[locale]]
        if any(value < 0 for value in positions) or positions != sorted(positions):
            fail("RENDER_N2", where)
    elif level == 3:
        if not text.startswith("# SPEC MetodologIA\nversion: 2.0\nstatus: executable\n"):
            fail("RENDER_N3_HEADER", where)
        positions = [text.find(heading) for heading in N3_HEADINGS[locale]]
        if any(value < 0 for value in positions) or positions != sorted(positions):
            fail("RENDER_N3", where)
    else:
        if not text.startswith("# system\n") or text.count("# system\n") != 1 or text.count("# user\n") != 1 or text.find("# user\n") <= 0:
            fail("RENDER_N4", where)


def validate_rendered(contracts: dict[str, dict[str, Any]], notebook: dict[str, Any]) -> tuple[int, int]:
    cards_total = sources_total = 0
    for locale in LOCALES:
        for audience in AUDIENCES:
            path = page_path(locale, audience)
            if not path.is_file() or path.is_symlink():
                fail("RENDER_PAGE", str(path.relative_to(ROOT)))
            soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
            cards = soup.select("[data-library-prompt]")
            if [card.get("id") for card in cards] != [f"prompt-{intent_id.lower()}" for intent_id in IDS]:
                fail("RENDER_CARDS", f"{locale}:{audience}")
            for intent_id, card in zip(IDS, cards):
                where = f"{locale}:{audience}:{intent_id}"
                contract = contracts[intent_id]
                cell = contract["locales"][locale][audience]
                route = notebook["intent_routes"][intent_id]
                if card.get("data-prompt-kind") != ("meta" if intent_id.startswith("M") else "direct") or card.get("data-notebook-surface") != route["launch"]:
                    fail("RENDER_CARD_METADATA", where)
                library = card.select("[data-prompt-library]")
                levels = card.select("details[data-prompt-level]")
                tabs = card.select("[data-prompt-format]")
                sources = card.select("textarea[data-prompt-source][data-prompt-mode]")
                if len(library) != 1 or [item.get("data-prompt-level") for item in levels] != ["1", "2", "3", "4"] or [item.get("data-prompt-format") for item in tabs] != list(EXPECTED_FORMATS):
                    fail("RENDER_LEVEL_MATRIX", where)
                if len(sources) != 8 or Counter(item.get("data-prompt-mode") for item in sources) != Counter({"template": 4, "demo": 4}):
                    fail("RENDER_MODE_MATRIX", where)
                if len(card.select("[data-prompt-flow]")) != 1 or len(card.select(".prompt-input-guide li")) != len(cell["inputs"]):
                    fail("RENDER_FLOW_OR_INPUT_GUIDE", where)
                why = card.select("[data-prompt-why]")
                if len(why) != 1 or len(why[0].select(".prompt-why-body > section")) != 5:
                    fail("RENDER_WHY", where)
                for level_number, level in enumerate(levels, 1):
                    template_node = level.select_one('textarea[data-prompt-mode="template"]')
                    demo_node = level.select_one('textarea[data-prompt-mode="demo"]')
                    if template_node is None or demo_node is None:
                        fail("RENDER_SOURCE", f"{where}:{level_number}")
                    template = template_node.get_text()
                    demo = demo_node.get_text()
                    if "{{" in template or "}}" in template or "{{" in demo or "}}" in demo:
                        fail("RENDER_LEGACY_MARKER", f"{where}:{level_number}")
                    for item in cell["inputs"]:
                        token = f'<{item["label"]} · {item["help"]} · {FORMAT_EXAMPLE[locale]}: {item["example"]}>'
                        if token not in template:
                            fail("RENDER_TEMPLATE_INPUT", f"{where}:{level_number}:{item['key']}")
                    allowed_optionals = {item["text"] for item in cell["optional_clauses"]}
                    square_values = set(re.findall(r"\[([^\[\]\n]+)\]", template))
                    expected_optionals = allowed_optionals if level_number >= 2 else set()
                    if square_values != expected_optionals:
                        fail("RENDER_TEMPLATE_OPTIONAL", f"{where}:{level_number}")
                    if re.search(r"<[^<>\n]+>|\[[^\[\]\n]+\]", demo):
                        fail("RENDER_DEMO_UNRESOLVED", f"{where}:{level_number}")
                    if resolved_demo(template, cell, locale) != demo:
                        fail("RENDER_DEMO_LOGIC_DRIFT", f"{where}:{level_number}")
                    validate_level_semantics(template, locale, level_number, f"{where}:{level_number}:template")
                    validate_level_semantics(demo, locale, level_number, f"{where}:{level_number}:demo")
                sources_total += len(sources)
            cards_total += len(cards)
    if cards_total != 84 or sources_total != 672:
        fail("RENDER_TOTALS", f"cards={cards_total}:sources={sources_total}")
    return cards_total, sources_total


def mutation_checks(
    inventory: dict[str, Any],
    contracts: dict[str, dict[str, Any]],
    notebook: dict[str, Any],
    levels_document: dict[str, Any],
    observed: dict[str, dict[str, int]],
) -> int:
    mutations: list[tuple[str, dict[str, Any], str]] = []

    candidate = copy.deepcopy(inventory)
    candidate["publication_authorized"] = True
    mutations.append(("publication", reseal(candidate), "MODULE_01_PROMPT_INVENTORY_GOVERNANCE"))

    candidate = copy.deepcopy(inventory)
    candidate["cardinality"]["cards_per_variant"] = 13
    mutations.append(("cardinality", reseal(candidate), "MODULE_01_PROMPT_INVENTORY_CARDINALITY"))

    candidate = copy.deepcopy(inventory)
    candidate["families"]["meta"]["ids"].pop()
    mutations.append(("family", reseal(candidate), "MODULE_01_PROMPT_INVENTORY_FAMILIES"))

    candidate = copy.deepcopy(inventory)
    candidate["levels"][2]["required_semantics"].remove("provenance")
    mutations.append(("level", reseal(candidate), "MODULE_01_PROMPT_INVENTORY_LEVELS"))

    candidate = copy.deepcopy(inventory)
    candidate["editorial_ranges"]["inputs_per_card"]["minimum"] = 1
    mutations.append(("editorial", reseal(candidate), "MODULE_01_PROMPT_INVENTORY_EDITORIAL_RANGES"))

    candidate = copy.deepcopy(inventory)
    candidate["cards"][0]["surface"] = "chat"
    mutations.append(("surface", reseal(candidate), "MODULE_01_PROMPT_INVENTORY_CARD_BINDING"))

    candidate = copy.deepcopy(inventory)
    candidate["source_contract_self_sha256"]["01"] = "0" * 64
    mutations.append(("contract_hash", reseal(candidate), "MODULE_01_PROMPT_INVENTORY_CONTRACT_SELF_BINDING"))

    candidate = copy.deepcopy(inventory)
    candidate["self_sha256"] = "0" * 64
    mutations.append(("self_hash", candidate, "MODULE_01_PROMPT_INVENTORY_SELF_HASH"))

    for name, candidate, expected in mutations:
        try:
            validate_inventory(candidate, contracts, notebook, levels_document, observed)
        except SystemExit as error:
            if not str(error).startswith(expected):
                fail("MUTATION_WRONG_REJECTION", f"{name}:{error}")
            continue
        fail("MUTATION_PASSED", name)
    return len(mutations)


def main() -> None:
    inventory, _ = read_json(INVENTORY_PATH, "INVENTORY_MISSING_OR_INVALID")
    contracts = load_contracts()
    notebook, notebook_raw = read_json(NOTEBOOK_PATH, "NOTEBOOK_MISSING_OR_INVALID")
    if hashlib.sha256(notebook_raw).hexdigest() != NOTEBOOK_RAW_SHA256:
        fail("NOTEBOOK_RAW_DRIFT")
    levels_document, _ = read_json(LEVELS_PATH, "LEVELS_MISSING_OR_INVALID")
    if set(notebook.get("intent_routes", {})) < set(IDS):
        fail("NOTEBOOK_ROUTE_MATRIX")
    observed = validate_contract_matrix(contracts)
    validate_inventory(inventory, contracts, notebook, levels_document, observed)
    cards, sources = validate_rendered(contracts, notebook)
    mutations = mutation_checks(inventory, contracts, notebook, levels_document, observed)
    print(
        "MODULE_01_PROMPT_INVENTORY_OK "
        f"contracts={len(contracts)} cells={len(contracts) * len(LOCALES) * len(AUDIENCES)} "
        f"cards={cards} prompts={sources} direct=10 meta=4 phases=4/4/2/4 "
        f"surfaces=12/2 levels=4 modes=2 mutations={mutations}"
    )


if __name__ == "__main__":
    main()
