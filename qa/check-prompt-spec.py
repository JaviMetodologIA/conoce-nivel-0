#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
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
    items = {item["id"]: item for item in source["locales"][locale]["items"]}
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
        item = items[prompt_id]
        natural = card.select_one('[id$="-natural"][data-prompt-template]')
        parameters = card.select_one('[id$="-parameters"][data-prompt-template]')
        pair = card.select_one('[id$="-pair"][data-prompt-template]')
        if natural is None or natural.get_text() != item["prompt"]:
            raise SystemExit(f"PROMPT_NATURAL_DRIFT:{locale}:{audience}:{prompt_id}")
        if parameters is None or item["prompt"] not in parameters.get_text() or "## S —" in parameters.get_text():
            raise SystemExit(f"PROMPT_PARAMETERS_DRIFT:{locale}:{audience}:{prompt_id}")
        if pair is None or legacy_pair_role not in pair.get_text() or item["prompt"] not in pair.get_text() or "## S —" in pair.get_text():
            raise SystemExit(f"PROMPT_PAIR_DRIFT:{locale}:{audience}:{prompt_id}")
        required_fragments = (
            item["when"], item["example"], item["purpose"], item["evidence"], item["prompt"],
            labels["expert_role"], labels["deliverable"], labels["scope_in"], labels["scope_out"],
            labels["edge_cases"], labels["observable_criteria"], labels["dod"], labels["provenance"], labels["metadata"],
            labels["reasoning_policy"],
        )
        if any(fragment not in text for fragment in required_fragments):
            raise SystemExit(f"PROMPT_SPEC_CONTENT_GAP:{locale}:{audience}:{prompt_id}")
        forbidden_reasoning_requests = (
            "show your chain of thought", "reveal your chain of thought",
            "muestra tu cadena de pensamiento", "expón tu cadena de pensamiento",
            "mostre sua cadeia de pensamento", "exponha sua cadeia de pensamento",
        )
        if any(phrase in text.lower() for phrase in forbidden_reasoning_requests):
            raise SystemExit(f"PROMPT_SPEC_PRIVATE_REASONING_REQUEST:{locale}:{audience}:{prompt_id}")
        rendered += 1

all_spec_panels = 0
for route in sorted(DIST.rglob("index.html")):
    soup = BeautifulSoup(route.read_text(encoding="utf-8"), "html.parser")
    locale = soup.html.get("lang")
    labels = source["locales"][locale]["spec_format"]
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

print(f"PROMPT_SPEC_OK library_panels={rendered} all_panels={all_spec_panels} prompts={len(IDS)} locales=3 audiences=2 mutations={len(mutations)+len(authority_mutations)}")
