#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import sys
from itertools import product
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DIST = ROOT / "dist"
sys.path.insert(0, str(ROOT / "scripts"))
import build as compiler
LANGS = ("es", "en", "pt")
AUDIENCES = ("persona", "empresa")
IDS = ("01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "M1", "M2", "M3", "M4")

# After the contract cutover dist is rendered from the 27 prompt-intent
# contracts, not from the library spec `items`. Every dist assertion below
# resolves its expectation from the (intent_id, locale, audience) contract cell.
CONTRACTS = compiler.PROMPT_CONTRACTS
WHY_SECTIONS = compiler.WHY_SECTIONS
WHY_PANEL_TOTAL = 162
COMPACT_LIMIT_TOTAL = 162
AUDIENCE_PAIR_TOTAL = len(compiler.PROMPT_INTENT_IDS) * len(LANGS)

_exporter_spec = importlib.util.spec_from_file_location(
    "prompt_snapshot_exporter", ROOT / "scripts" / "export-prompt-snapshot.py")
exporter = importlib.util.module_from_spec(_exporter_spec)
_exporter_spec.loader.exec_module(exporter)
classify = exporter.classify  # dist group id -> (surface, intent_id)


def cell_of(intent_id, locale, audience):
    return CONTRACTS[intent_id]["locales"][locale][audience]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(source: dict) -> None:
    contract = source.get("spec_contract", {})
    if contract.get("anatomy") != ["situation", "request", "execution", "criterion"]:
        raise ValueError("SPEC_ANATOMY_ORDER")
    if contract.get("chain_of_thought_policy") != "never_request_store_or_expose_private_reasoning":
        raise ValueError("SPEC_PRIVATE_REASONING_POLICY")
    if contract.get("provenance_required") is not True or contract.get("publication_authorized") is not False:
        raise ValueError("SPEC_GOVERNANCE")
    references = source.get("reference_sources", [])
    if len(references) != 2 or any(item.get("role") != "secondary_reference" or not item.get("rights") for item in references):
        raise ValueError("SPEC_REFERENCE_GOVERNANCE")
    required = {
        "situation", "request", "execution", "criterion", "context", "example_label",
        "expert_role", "default_role", "deliverable", "scope_in", "scope_out", "scope_out_value",
        "steps", "edge_cases", "edge_case_items", "output", "observable_criteria", "criterion_items",
        "dod", "dod_value", "provenance", "provenance_items", "metadata", "metadata_items",
        "reasoning_policy", "step_review", "step_finish",
    }
    if set(source.get("locales", {})) != set(LANGS):
        raise ValueError("SPEC_LOCALE_MATRIX")
    for locale in LANGS:
        localized = source["locales"][locale]
        if [item.get("id") for item in localized.get("items", [])] != list(IDS):
            raise ValueError(f"SPEC_PROMPT_MATRIX:{locale}")
        labels = localized.get("spec_format", {})
        if required - set(labels) or any(not labels[key] for key in required):
            raise ValueError(f"SPEC_LOCALE_FIELDS:{locale}")
        expected_labels = {
            "es": ("Situación", "Pedido", "Ejecución", "Criterio"),
            "en": ("Situation", "Request", "Execution", "Criterion"),
            "pt": ("Situação", "Pedido", "Execução", "Critério"),
        }[locale]
        if tuple(labels[key] for key in ("situation", "request", "execution", "criterion")) != expected_labels:
            raise ValueError(f"SPEC_LOCALE_LANGUAGE:{locale}")
        if len(labels["edge_case_items"]) < 3 or len(labels["criterion_items"]) < 3 or len(labels["provenance_items"]) < 4 or len(labels["metadata_items"]) < 4:
            raise ValueError(f"SPEC_LOCALE_DEPTH:{locale}")


source_path = SRC / "prompt-library-spec-v1.json"
authority_path = SRC / "prompt-spec-authority-v1.json"
source = json.loads(source_path.read_text(encoding="utf-8"))
authority = json.loads(authority_path.read_text(encoding="utf-8"))
validate(source)
compiler.validate_prompt_spec_authority(authority)
compiler.validate_prompt_library(source, authority)

rendered = 0
for locale, audience in product(LANGS, AUDIENCES):
    parts = []
    if locale != "es":
        parts.append(locale)
    if audience == "empresa":
        parts.append("empresa")
    parts.append("prompts")
    route = DIST.joinpath(*parts, "index.html")
    soup = BeautifulSoup(route.read_text(encoding="utf-8"), "html.parser")
    labels = source["locales"][locale]["spec_format"]
    legacy_pair_role = {
        "es": "Asistente MetodologIA orientado a evidencia",
        "en": "Evidence-oriented MetodologIA assistant",
        "pt": "Assistente MetodologIA orientado a evidências",
    }[locale]
    cards = soup.select("[data-library-prompt]")
    if len(cards) != len(IDS):
        raise SystemExit(f"PROMPT_SPEC_CARD_COUNT:{locale}:{audience}:{len(cards)}")
    for prompt_id, card in zip(IDS, cards):
        panel = card.select_one('[id$="-spec"][data-prompt-template]')
        if panel is None:
            raise SystemExit(f"PROMPT_SPEC_PANEL_MISSING:{locale}:{audience}:{prompt_id}")
        text = panel.get_text("\n", strip=True)
        headings = [
            f"## S — {labels['situation']}",
            f"## P — {labels['request']}",
            f"## E — {labels['execution']}",
            f"## C — {labels['criterion']}",
        ]
        positions = [text.find(heading) for heading in headings]
        if any(position < 0 for position in positions) or positions != sorted(positions) or len(set(positions)) != 4:
            raise SystemExit(f"PROMPT_SPEC_ANATOMY:{locale}:{audience}:{prompt_id}:{positions}")
        cell = cell_of(prompt_id, locale, audience)
        level_spec = cell["level_spec"]
        natural = card.select_one('[id$="-natural"][data-prompt-template]')
        parameters = card.select_one('[id$="-parameters"][data-prompt-template]')
        pair = card.select_one('[id$="-pair"][data-prompt-template]')
        expected_modes = {
            mode: compiler.structured_variants(locale, cell["title"], cell["prompt"], level_spec, cell, mode)
            for mode in ("template", "demo")
        }
        # Level 1 projects the contract body into an explained template and a
        # fully resolved demo; the contract remains the single authority.
        natural_source = card.select_one('details[data-prompt-level="1"] textarea[data-prompt-mode="template"]')
        if natural is None or natural_source is None or natural_source.get_text() != expected_modes["template"]["natural"]:
            raise SystemExit(f"PROMPT_NATURAL_DRIFT:{locale}:{audience}:{prompt_id}")
        demo_natural = card.select_one('[id$="-natural-demo"][data-prompt-demo]')
        demo_natural_source = card.select_one('details[data-prompt-level="1"] textarea[data-prompt-mode="demo"]')
        if demo_natural is None or demo_natural_source is None or demo_natural_source.get_text() != expected_modes["demo"]["natural"]:
            raise SystemExit(f"PROMPT_DEMO_NATURAL_DRIFT:{locale}:{audience}:{prompt_id}")
        if re.search(r"<[^>]+>|\{\{[^}]+\}\}", demo_natural.get_text()):
            raise SystemExit(f"PROMPT_DEMO_UNRESOLVED:{locale}:{audience}:{prompt_id}")
        # Level 2 exposes execution parameters and typed inputs.
        parameters_text = "" if parameters is None else parameters.get_text("\n", strip=True)
        parameters_fragments = (
            *(f"{item['label']} = {item['default']}" for item in cell["parameters"]),
            *(item["label"] for item in cell["inputs"]),
            level_spec["objective"], *level_spec["workflow"], *level_spec["guardrails"], *level_spec["output"],
        )
        if parameters is None or "## S —" in parameters_text or any(
                fragment not in parameters_text for fragment in parameters_fragments):
            raise SystemExit(f"PROMPT_PARAMETERS_DRIFT:{locale}:{audience}:{prompt_id}")
        if any(framework not in parameters_text for framework in level_spec["frameworks"]):
            raise SystemExit(f"PROMPT_PARAMETERS_FRAMEWORK_GAP:{locale}:{audience}:{prompt_id}")
        # Level 4 carries `level_spec.role` per intent; the generic role is gone.
        pair_text = "" if pair is None else pair.get_text("\n", strip=True)
        pair_fragments = (
            level_spec["role"], level_spec["dod"], level_spec["objective"],
            *level_spec["workflow"], *level_spec["guardrails"], *level_spec["output"],
        )
        if pair is None or "## S —" in pair_text or legacy_pair_role in pair_text or any(
                fragment not in pair_text for fragment in pair_fragments):
            raise SystemExit(f"PROMPT_PAIR_DRIFT:{locale}:{audience}:{prompt_id}")
        if any(framework not in pair_text for framework in level_spec["frameworks"]):
            raise SystemExit(f"PROMPT_PAIR_FRAMEWORK_GAP:{locale}:{audience}:{prompt_id}")
        # Level 3 SPEC quotes the contract cell (not the spec `items`) plus the
        # localized anatomy labels.
        required_fragments = (
            cell["when"], cell["example"], cell["purpose"], cell["evidence"],
            level_spec["spec_role"], *level_spec["workflow"], *level_spec["output"],
            labels["expert_role"], labels["deliverable"], labels["scope_in"], labels["scope_out"],
            labels["edge_cases"], labels["observable_criteria"], labels["dod"], labels["provenance"], labels["metadata"],
            labels["reasoning_policy"],
        )
        if any(fragment not in text for fragment in required_fragments):
            raise SystemExit(f"PROMPT_SPEC_CONTENT_GAP:{locale}:{audience}:{prompt_id}")
        if any(framework not in text for framework in level_spec["frameworks"]):
            raise SystemExit(f"PROMPT_SPEC_FRAMEWORK_GAP:{locale}:{audience}:{prompt_id}")
        forbidden_reasoning_requests = (
            "show your chain of thought", "reveal your chain of thought",
            "muestra tu cadena de pensamiento", "expón tu cadena de pensamiento",
            "mostre sua cadeia de pensamento", "exponha sua cadeia de pensamento",
        )
        if any(phrase in text.lower() for phrase in forbidden_reasoning_requests):
            raise SystemExit(f"PROMPT_SPEC_PRIVATE_REASONING_REQUEST:{locale}:{audience}:{prompt_id}")
        rendered += 1

def why_panel_facts(soup, locale, audience):
    """[surface, intent, locale, audience, [[heading, [items]], ...]] per rendered
    `data-prompt-why` panel. Lists (not tuples) so mutations can rewrite them."""
    facts = []
    for panel in soup.select("[data-prompt-why]"):
        surface, intent = classify(panel["data-prompt-why"], locale)
        sections = [[section.h4.get_text(strip=True),
                     [entry.get_text(strip=True) for entry in section.select("li")]]
                    for section in panel.select(".prompt-why-body > section")]
        facts.append([surface, intent, locale, audience, sections])
    return facts


def assert_why_panels(facts):
    """Every card carries a why panel whose 5 sections are populated from the
    matching contract cell, labelled in the route's own language."""
    if len(facts) != WHY_PANEL_TOTAL:
        raise SystemExit(f"PROMPT_WHY_PANEL_COUNT:{len(facts)}")
    for surface, intent, locale, audience, sections in facts:
        where = f"{locale}:{audience}:{intent}"
        why = cell_of(intent, locale, audience)["why_it_works"]
        why_labels = source["locales"][locale]["why_format"]
        if [heading for heading, _ in sections] != [why_labels[key] for key in WHY_SECTIONS]:
            raise SystemExit(f"PROMPT_WHY_SECTION_LABELS:{where}")
        for key, (_, entries) in zip(WHY_SECTIONS, sections):
            if not entries:
                raise SystemExit(f"PROMPT_WHY_SECTION_EMPTY:{where}:{key}")
            if entries != why[key]:
                raise SystemExit(f"PROMPT_WHY_SECTION_DRIFT:{where}:{key}")
    return len(facts)


def compact_limit_facts(soup, locale, audience):
    """Validate the single selection boundary exposed before each prompt."""
    facts = []
    expected_label = compiler.PROMPT_LIMIT_LABELS[locale]
    for node in soup.select(".prompt-limit-compact"):
        card = node.find_parent(["article"])
        block = None if card is None else card.select_one("[data-prompt-library]")
        if block is None:
            raise SystemExit(f"PROMPT_COMPACT_LIMIT_ORPHAN:{locale}:{audience}")
        surface, intent = classify(block["data-prompt-library"], locale)
        label_node = node.select_one("dt, strong")
        value_node = node.select_one("dd, span")
        if label_node is None or label_node.get_text(strip=True) != expected_label:
            raise SystemExit(f"PROMPT_COMPACT_LIMIT_LABEL:{locale}:{audience}:{intent}")
        if value_node is None:
            raise SystemExit(f"PROMPT_COMPACT_LIMIT_EMPTY:{locale}:{audience}:{intent}")
        value = value_node.get_text(" ", strip=True)
        expected = cell_of(intent, locale, audience)["why_it_works"]["limits"][0]
        if value != expected:
            raise SystemExit(f"PROMPT_COMPACT_LIMIT_DRIFT:{locale}:{audience}:{intent}")
        facts.append((surface, intent, locale, audience, value))
    return facts


def natural_sources(soup, locale, audience):
    """{(surface, intent, locale, audience): level-1 copyable source}."""
    sources = {}
    for block in soup.select("[data-prompt-library]"):
        surface, intent = classify(block["data-prompt-library"], locale)
        node = block.select_one('details[data-prompt-level="1"] textarea[data-prompt-source][data-prompt-mode="template"]')
        if node is None:
            raise SystemExit(f"PROMPT_AUDIENCE_NATURAL_MISSING:{locale}:{audience}:{intent}")
        sources[(surface, intent, locale, audience)] = node.get_text()
    return sources


def assert_audience_divergence(sources):
    """The cutover made level 1 audience-specific. Before it, every persona /
    empresa pair was byte-identical; a re-clone must now fail."""
    pairs = 0
    for (surface, intent, locale, audience), text in sorted(sources.items()):
        if audience != "persona":
            continue
        twin = sources.get((surface, intent, locale, "empresa"))
        if twin is None:
            raise SystemExit(f"PROMPT_AUDIENCE_NATURAL_MISSING:{locale}:empresa:{intent}")
        if twin == text:
            raise SystemExit(f"PROMPT_AUDIENCE_NATURAL_CLONE:{locale}:{intent}")
        pairs += 1
    for (_, intent, locale, audience), text in sorted(sources.items()):
        cell = cell_of(intent, locale, audience)
        expected = compiler.structured_variants(locale, cell["title"], cell["prompt"], cell["level_spec"], cell, "template")["natural"]
        if text != expected:
            raise SystemExit(f"PROMPT_AUDIENCE_NATURAL_DRIFT:{locale}:{audience}:{intent}")
    if pairs != AUDIENCE_PAIR_TOTAL:
        raise SystemExit(f"PROMPT_AUDIENCE_PAIR_COUNT:{pairs}")
    return pairs


all_spec_panels = 0
why_facts = []
compact_limit_facts_all = []
natural_by_cell = {}
for route in sorted(DIST.rglob("index.html")):
    soup = BeautifulSoup(route.read_text(encoding="utf-8"), "html.parser")
    # M1 keeps the governed 27-contract prompt system. Modules 2–4 use their
    # imported curriculum contracts and are verified by the expansion and
    # module-renderer gates, so they must not be coerced into M1 intent IDs.
    if soup.body and soup.body.get("data-module-id") != compiler.DEFAULT_MODULE_ID:
        continue
    locale = soup.html.get("lang")
    audience = soup.html.get("data-audience")
    labels = source["locales"][locale]["spec_format"]
    why_facts.extend(why_panel_facts(soup, locale, audience))
    compact_limit_facts_all.extend(compact_limit_facts(soup, locale, audience))
    natural_by_cell.update(natural_sources(soup, locale, audience))
    headings = [
        f"## S — {labels['situation']}",
        f"## P — {labels['request']}",
        f"## E — {labels['execution']}",
        f"## C — {labels['criterion']}",
    ]
    for tab in soup.select('[data-prompt-format="spec"]'):
        panel = soup.find(id=tab.get("aria-controls"))
        if panel is None:
            raise SystemExit(f"PROMPT_SPEC_CONTROL_TARGET:{route.relative_to(DIST)}")
        text = panel.get_text("\n", strip=True)
        positions = [text.find(heading) for heading in headings]
        if any(position < 0 for position in positions) or positions != sorted(positions):
            raise SystemExit(f"PROMPT_SPEC_GLOBAL_ANATOMY:{route.relative_to(DIST)}:{positions}")
        if labels["edge_cases"] not in text or labels["observable_criteria"] not in text or labels["reasoning_policy"] not in text:
            raise SystemExit(f"PROMPT_SPEC_GLOBAL_CONTENT:{route.relative_to(DIST)}:{panel.get('id')}")
        all_spec_panels += 1
if all_spec_panels != 162:
    raise SystemExit(f"PROMPT_SPEC_GLOBAL_COUNT:{all_spec_panels}")
why_panels = assert_why_panels(why_facts)
if len(compact_limit_facts_all) != COMPACT_LIMIT_TOTAL:
    raise SystemExit(f"PROMPT_COMPACT_LIMIT_COUNT:{len(compact_limit_facts_all)}")
audience_pairs = assert_audience_divergence(natural_by_cell)

manifest = json.loads((DIST / "build-manifest.json").read_text(encoding="utf-8"))
receipt = json.loads((DIST / "build-receipt.json").read_text(encoding="utf-8"))
binding = manifest.get("prompt_library", {})
if binding.get("source_sha256") != sha256(source_path) or binding.get("anatomy") != source["spec_contract"]["anatomy"]:
    raise SystemExit("PROMPT_SPEC_MANIFEST_BINDING")
authority_binding = binding.get("intent_authority", {})
if authority_binding != {
    "schema_version": "prompt-spec-authority-v1",
    "source": "src/prompt-spec-authority-v1.json",
    "source_sha256": sha256(authority_path),
    "self_sha256": authority["self_sha256"],
    "rights": authority["source_provenance"]["rights"],
    "state": "RENDERED_DRAFT",
    "publication_authorized": False,
}:
    raise SystemExit("PROMPT_SPEC_AUTHORITY_MANIFEST_BINDING")
if receipt.get("prompt_library") != binding or binding.get("state") != "RENDERED_DRAFT" or binding.get("publication_authorized") is not False:
    raise SystemExit("PROMPT_SPEC_RECEIPT_BINDING")

mutations = []
candidate = copy.deepcopy(source); candidate["spec_contract"]["anatomy"][1:3] = reversed(candidate["spec_contract"]["anatomy"][1:3]); mutations.append(("order", candidate))
candidate = copy.deepcopy(source); candidate["spec_contract"]["chain_of_thought_policy"] = "request_reasoning"; mutations.append(("reasoning", candidate))
candidate = copy.deepcopy(source); candidate["reference_sources"][0]["rights"] = ""; mutations.append(("rights", candidate))
candidate = copy.deepcopy(source); candidate["locales"]["pt"]["spec_format"].pop("criterion"); mutations.append(("missing_locale_field", candidate))
candidate = copy.deepcopy(source); candidate["locales"]["pt"]["spec_format"]["situation"] = "Situación"; mutations.append(("wrong_language", candidate))
candidate = copy.deepcopy(source); candidate["locales"]["en"]["spec_format"]["edge_case_items"] = []; mutations.append(("missing_edge_cases", candidate))
candidate = copy.deepcopy(source); candidate["locales"]["es"]["items"].pop(); mutations.append(("missing_prompt", candidate))
generic_mutations = {
    "es": ("Tarea genérica", "una tarea genérica.", "una entrada genérica.", "un ejemplo genérico.", "un resultado genérico.", "Analiza [ENTRADA] para [USO] y entrega una respuesta genérica."),
    "en": ("Generic task", "a generic task.", "a generic input.", "a generic example.", "a generic result.", "Analyze [INPUT] for [USE] and provide a generic response."),
    "pt": ("Tarefa genérica", "uma tarefa genérica.", "uma entrada genérica.", "um exemplo genérico.", "um resultado genérico.", "Analise [ENTRADA] para [USO] e entregue uma resposta genérica."),
}
for locale, values in generic_mutations.items():
    candidate = copy.deepcopy(source)
    item = candidate["locales"][locale]["items"][0]
    for field, value in zip(("title", "purpose", "when", "example", "evidence", "prompt"), values):
        item[field] = value
    mutations.append((f"generic_shell_{locale}", candidate))
long_generic_mutations = {
    "es": (
        "Análisis general estructurado",
        "Producir un análisis general, claro y ampliamente útil para cualquier tarea.",
        "cuando una persona necesita una respuesta general sin requisitos específicos.",
        "Revisar una entrada cualquiera y proponer recomendaciones aplicables en general.",
        "análisis general con recomendaciones, resumen y próximos pasos claros.",
        "Analiza [ENTRADA] para [USO] y entrega un análisis completo, claro y estructurado. "
        "Resume la información disponible, identifica aspectos relevantes, explica consideraciones importantes, "
        "propone recomendaciones genéricas y presenta próximos pasos útiles. Incluye contexto, observaciones, "
        "opciones, ventajas, limitaciones y una conclusión. Mantén un tono profesional, organiza la respuesta "
        "en secciones fáciles de leer y procura que el resultado sea generalmente útil para distintas situaciones.",
    ),
    "en": (
        "General structured analysis",
        "Produce a general, clear and broadly useful analysis for any task or situation.",
        "when someone needs a general response without prompt-specific requirements.",
        "Review any input and propose recommendations that are generally applicable.",
        "general analysis with recommendations, summary and clear next steps.",
        "Analyze [INPUT] for [USE] and provide a thorough, clear, structured, generally useful analysis. "
        "Summarize the available information, identify relevant aspects, explain important considerations, "
        "offer generic recommendations and present useful next steps. Include context, observations, options, "
        "advantages, limitations and a conclusion. Keep a professional tone, organize the response into readable "
        "sections and make the result broadly applicable across different situations and common user needs.",
    ),
    "pt": (
        "Análise geral estruturada",
        "Produzir uma análise geral, clara e amplamente útil para qualquer tarefa ou situação.",
        "quando alguém precisa de uma resposta geral sem requisitos específicos do prompt.",
        "Revisar qualquer entrada e propor recomendações aplicáveis de maneira geral.",
        "análise geral com recomendações, resumo e próximos passos claros.",
        "Analise [ENTRADA] para [USO] e entregue uma análise completa, clara, estruturada e geralmente útil. "
        "Resuma as informações disponíveis, identifique aspectos relevantes, explique considerações importantes, "
        "ofereça recomendações genéricas e apresente próximos passos úteis. Inclua contexto, observações, opções, "
        "vantagens, limitações e uma conclusão. Mantenha tom profissional, organize a resposta em seções legíveis "
        "e faça o resultado ser amplamente aplicável a diferentes situações e necessidades comuns.",
    ),
}
for locale, values in long_generic_mutations.items():
    candidate = copy.deepcopy(source)
    item = candidate["locales"][locale]["items"][0]
    for field, value in zip(("title", "purpose", "when", "example", "evidence", "prompt"), values):
        item[field] = value
    mutations.append((f"padded_generic_shell_{locale}", candidate))
for locale in ("en", "pt"):
    candidate = copy.deepcopy(source)
    candidate["locales"][locale]["items"][0] = copy.deepcopy(candidate["locales"]["es"]["items"][0])
    mutations.append((f"spanish_locale_leak_{locale}", candidate))
for locale in ("en", "pt"):
    candidate = copy.deepcopy(source)
    candidate["locales"][locale]["items"][0]["prompt"] += " Quiero una respuesta útil y clara."
    mutations.append((f"single_sentence_spanish_leak_{locale}", candidate))
candidate = copy.deepcopy(source); candidate["spec_contract"]["semantic_specificity"]["intent_authority"]["source_sha256"] = "0" * 64; mutations.append(("authority_source_binding_drift", candidate))
candidate = copy.deepcopy(source); candidate["spec_contract"]["semantic_specificity"]["intent_authority"]["self_sha256"] = "0" * 64; mutations.append(("authority_self_binding_drift", candidate))
candidate = copy.deepcopy(source); candidate["locales"]["en"]["items"][1]["prompt"] = candidate["locales"]["en"]["items"][0]["prompt"]; mutations.append(("prompt_clone", candidate))
candidate = copy.deepcopy(source); candidate["locales"]["pt"]["items"][0]["prompt"] = re.sub(r"\[[^]]+\]", "input", candidate["locales"]["pt"]["items"][0]["prompt"]); mutations.append(("variables_removed", candidate))
expected_rejections = {
    "padded_generic_shell_es": "PROMPT_LIBRARY_INTENT_ANCHOR_MISSING",
    "padded_generic_shell_en": "PROMPT_LIBRARY_INTENT_ANCHOR_MISSING",
    "padded_generic_shell_pt": "PROMPT_LIBRARY_INTENT_ANCHOR_MISSING",
    "single_sentence_spanish_leak_en": "PROMPT_LIBRARY_LOCALE_LEAK",
    "single_sentence_spanish_leak_pt": "PROMPT_LIBRARY_LOCALE_LEAK",
    "authority_source_binding_drift": "PROMPT_LIBRARY_AUTHORITY_BINDING_INVALID",
    "authority_self_binding_drift": "PROMPT_LIBRARY_AUTHORITY_BINDING_INVALID",
}
for name, candidate in mutations:
    try:
        validate(candidate)
        compiler.validate_prompt_library(candidate, authority)
    except (ValueError, SystemExit) as error:
        expected = expected_rejections.get(name)
        if expected and not str(error).startswith(expected):
            raise SystemExit(f"PROMPT_SPEC_MUTATION_WRONG_REJECTION:{name}:{error}")
        continue
    raise SystemExit(f"PROMPT_SPEC_MUTATION_PASSED:{name}")

authority_mutations = []
candidate_authority = copy.deepcopy(authority)
candidate_authority["locales"]["en"]["01"]["intent"] = ["general", "analysis"]
authority_mutations.append(("authority_anchor_drift", copy.deepcopy(source), candidate_authority, "PROMPT_SPEC_AUTHORITY_SELF_DRIFT"))
candidate_authority = copy.deepcopy(authority)
candidate_authority["self_sha256"] = "0" * 64
authority_mutations.append(("authority_self_hash_drift", copy.deepcopy(source), candidate_authority, "PROMPT_SPEC_AUTHORITY_SELF_DRIFT"))
candidate_source = copy.deepcopy(source)
candidate_item = candidate_source["locales"]["en"]["items"][0]
for field, value in zip(("title", "purpose", "when", "example", "evidence", "prompt"), long_generic_mutations["en"]):
    candidate_item[field] = value
candidate_authority = copy.deepcopy(authority)
candidate_authority["locales"]["en"]["01"] = {
    "intent": ["general", "analysis"],
    "evidence": ["recommend", "summary"],
}
candidate_authority["self_sha256"] = compiler.canonical_self(candidate_authority, "self_sha256")
candidate_source["spec_contract"]["semantic_specificity"]["intent_authority"]["self_sha256"] = candidate_authority["self_sha256"]
candidate_source["spec_contract"]["semantic_specificity"]["intent_authority"]["source_sha256"] = hashlib.sha256((json.dumps(candidate_authority, ensure_ascii=False, indent=2) + "\n").encode("utf-8")).hexdigest()
authority_mutations.append(("co_mutated_generic_and_authority", candidate_source, candidate_authority, "PROMPT_SPEC_AUTHORITY_SELF_DRIFT"))
for name, candidate_source, candidate_authority, expected in authority_mutations:
    try:
        validate(candidate_source)
        compiler.validate_prompt_library(candidate_source, candidate_authority)
    except (ValueError, SystemExit) as error:
        if not str(error).startswith(expected):
            raise SystemExit(f"PROMPT_SPEC_AUTHORITY_MUTATION_WRONG_REJECTION:{name}:{error}")
        continue
    raise SystemExit(f"PROMPT_SPEC_AUTHORITY_MUTATION_PASSED:{name}")

# Mutations for the two dist-model gates the cutover introduced. They mutate the
# facts harvested from dist, which is what these gates read.
dist_mutations = []
candidate_facts = copy.deepcopy(why_facts)
candidate_facts[0][4][0][1] = []
dist_mutations.append(("why_panel_empty", assert_why_panels, candidate_facts, "PROMPT_WHY_SECTION_EMPTY"))
candidate_sources = copy.deepcopy(natural_by_cell)
surface, intent, locale, _ = next(key for key in sorted(candidate_sources) if key[3] == "persona")
candidate_sources[(surface, intent, locale, "empresa")] = candidate_sources[(surface, intent, locale, "persona")]
dist_mutations.append(("audience_natural_clone", assert_audience_divergence, candidate_sources, "PROMPT_AUDIENCE_NATURAL_CLONE"))
for name, check, payload, expected in dist_mutations:
    try:
        check(payload)
    except SystemExit as error:
        if not str(error).startswith(expected):
            raise SystemExit(f"PROMPT_DIST_MUTATION_WRONG_REJECTION:{name}:{error}")
        continue
    raise SystemExit(f"PROMPT_DIST_MUTATION_PASSED:{name}")

print(
    f"PROMPT_SPEC_OK library_panels={rendered} all_panels={all_spec_panels} why_panels={why_panels} "
    f"audience_pairs={audience_pairs} prompts={len(IDS)} locales=3 audiences=2 "
    f"mutations={len(mutations)+len(authority_mutations)+len(dist_mutations)}")
