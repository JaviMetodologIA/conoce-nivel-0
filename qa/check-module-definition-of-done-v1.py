#!/usr/bin/env python3
"""Fail-closed structural gate for the Nivel 0 module Definition of Done."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
SRC = ROOT / "src"
WORKBOOK_GOLDEN_SHA256 = "ed1245d57e7ca887c8fd562b2b092d7097205d8103ccbdde1f0d250fb718ec8c"
sys.path.insert(0, str(ROOT / "scripts"))

from brand import AUDIENCES, DEFAULT_MODULE_ID, MODULE_IDS, page_dir  # noqa: E402


LOCALES = ("es", "en", "pt")
PAGE_TO_RESOURCE = {
    "deck": "masterclass",
    "workbook": "workbook",
    "playbook": "playbook",
    "prompts": "prompts",
}
EXPECTED_STAGE_LABELS = {
    "es": ("En clase", "Profundización", "Consolidación"),
    "en": ("In class", "Deepening", "Consolidation"),
    "pt": ("Em aula", "Aprofundamento", "Consolidação"),
}
WORKBOOK_PREPARATION_LABELS = {
    "es": ("Prerrequisitos", "Inputs", "Límites"),
    "en": ("Prerequisites", "Inputs", "Limits"),
    "pt": ("Pré-requisitos", "Inputs", "Limites"),
}
DEMO_LABELS = {
    "es": "Datos sintéticos disponibles:",
    "en": "Available synthetic data:",
    "pt": "Dados sintéticos disponíveis:",
}
RECEIVE_LABELS = {
    "module-03-trabajar-amplificado": {
        "es": "Plan de prueba + bitácora de ejecución",
        "en": "Test plan + execution log",
        "pt": "Plano de teste + registro de execução",
    },
    "module-04-trabajo-agentico": {
        "es": "Plan aprobado + salida observada + bitácora de ejecución",
        "en": "Approved plan + observed output + execution log",
        "pt": "Plano aprovado + saída observada + registro de execução",
    },
}
RENDER_FORBIDDEN = (
    "Treat demo artifacts as synthetic.",
    "Usa el artefacto sintético del paso anterior:",
    "Use the synthetic artifact from the previous step:",
    "Use o artefato sintético da etapa anterior:",
)
DEPTH_PROMPT_REQUIREMENTS = {
    "module-03-trabajar-amplificado": {
        "prompt_count": 10,
        "gate_id": "prompt-08",
        "receive_id": "prompt-09",
        "error_prefix": "M03",
    },
    "module-04-trabajo-agentico": {
        "prompt_count": 8,
        "gate_id": "prompt-06",
        "receive_id": "prompt-07",
        "error_prefix": "M04",
    },
}


class Document(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.references: list[tuple[str, str]] = []
        self.main_attrs: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "main":
            self.main_attrs.append(values)
        for name in ("aria-controls", "aria-labelledby", "aria-describedby"):
            for target in values.get(name, "").split():
                self.references.append((name, target))


def canonical_hash(document: dict[str, object]) -> str:
    payload = {key: value for key, value in document.items() if key != "self_sha256"}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def selected_modules(value: str) -> tuple[str, ...]:
    if value == "all":
        return tuple(MODULE_IDS[1:])
    order = int(value)
    return (MODULE_IDS[order - 1],)


def page_path(locale: str, audience: str, page: str, module_id: str) -> Path:
    route = page_dir(locale, audience, page, module_id)
    return (DIST if route == "." else DIST / route) / "index.html"


def inner_block(source: str, marker: str, closing: str = "</nav>") -> str:
    start = source.find(marker)
    if start < 0:
        return ""
    end = source.find(closing, start)
    return source[start : end + len(closing)] if end >= 0 else ""


def verify_page(path: Path, locale: str, audience: str, module: dict[str, object], page: str) -> list[str]:
    route = str(path.relative_to(DIST))
    if not path.is_file():
        return [f"MISSING:{route}"]
    source = path.read_text(encoding="utf-8")
    parsed = Document()
    parsed.feed(source)
    errors: list[str] = []
    if len(parsed.main_attrs) != 1:
        errors.append(f"MAIN_COUNT:{route}:{len(parsed.main_attrs)}")
        return errors
    main = parsed.main_attrs[0]
    expected = {
        "data-module-id": str(module["module_id"]),
        "data-module-order": str(module["order"]),
        "data-module-resource": PAGE_TO_RESOURCE[page],
        "data-locale": locale,
        "data-audience": audience,
    }
    for name, value in expected.items():
        if main.get(name) != value:
            errors.append(f"MAIN_IDENTITY:{route}:{name}:{main.get(name)}!={value}")
    if len(parsed.ids) != len(set(parsed.ids)):
        duplicates = sorted({value for value in parsed.ids if parsed.ids.count(value) > 1})
        errors.append(f"DUPLICATE_ID:{route}:{','.join(duplicates[:6])}")
    ids = set(parsed.ids)
    for name, target in parsed.references:
        if target not in ids:
            errors.append(f"ARIA_TARGET:{route}:{name}:{target}")
    for target in re.findall(r'href="#([A-Za-z][A-Za-z0-9_-]*)"', source):
        if target not in ids:
            errors.append(f"HASH_TARGET:{route}:{target}")
    for marker in ("data-conoce-header", "data-conoce-footer", "data-conoce-preferences", "data-intrapage-nav"):
        if source.count(marker) != 1:
            errors.append(f"SHELL:{route}:{marker}:{source.count(marker)}")
    trigger = re.search(r'<button class="intrapage-trigger"[^>]*>', source)
    if not trigger or not re.search(r'\saria-label="[^"]+"', trigger.group(0)):
        errors.append(f"INTRAPAGE_TRIGGER_NAME:{route}")
    sibling = inner_block(source, "<nav class=\"actions\" data-module-siblings")
    current_count = sibling.count('aria-current="page"')
    if not sibling or current_count != 1:
        errors.append(f"SIBLING_CURRENT:{route}:{current_count}")

    resource = PAGE_TO_RESOURCE[page]
    if resource == "masterclass":
        pdf = source.find('class="official-pdf-card"')
        strip = source.find('class="module-resource-strip"')
        guide = source.find('class="masterclass-player"')
        if not (0 <= pdf < strip < guide):
            errors.append(f"MASTERCLASS_ORDER:{route}:{pdf}/{strip}/{guide}")
        for control in ("data-prev", "data-next"):
            match = re.search(rf'<button[^>]*{control}[^>]*>(.*?)</button>', source, re.S)
            if not match or 'class="ui-icon"' not in match.group(1):
                errors.append(f"MASTERCLASS_VISIBLE_CONTROL:{route}:{control}")
        if source.count('class="official-pdf-object"') != 1 or re.search(r'class="official-pdf-object"[^>]+data="https?://', source):
            errors.append(f"MASTERCLASS_PDF:{route}")
    elif resource == "workbook":
        outcome = re.search(r'<aside class="workbook-outcome"[^>]*data-module-number="([0-9]{2})"', source)
        if not outcome or outcome.group(1) != f'{int(module["order"]):02d}':
            errors.append(f"WORKBOOK_OUTCOME_NUMBER:{route}:{outcome.group(1) if outcome else 'missing'}")
        guide = re.search(r'<ol class="guide-steps">(.*?)</ol>', source, re.S)
        if not guide or guide.group(1).count("<li") != 5:
            errors.append(f"WORKBOOK_GUIDE_MILESTONES:{route}")
        case_fields = re.findall(r'<textarea\b(?=[^>]*data-ephemeral-input="([^"]+)")([^>]*)>', source)
        if len(case_fields) != 3 or {key for key, _attrs in case_fields} != {"case", "result", "evidence"}:
            errors.append(f"WORKBOOK_CASE_INTAKE:{route}:{[key for key, _attrs in case_fields]}")
        elif any('autocomplete="off"' not in attrs or re.search(r'\bname=', attrs) for _key, attrs in case_fields):
            errors.append(f"WORKBOOK_CASE_PERSISTENCE:{route}")
        prep = re.search(r'<section class="workbook-prep".*?<div class="prep-grid">(.*?)</div></section>', source, re.S)
        if not prep or any(label not in html.unescape(prep.group(1)) for label in WORKBOOK_PREPARATION_LABELS[locale]):
            errors.append(f"WORKBOOK_PREPARATION_CONTRACT:{route}")
        prompt_cards = re.findall(r'<article class="card module-depth-prompt">(.*?)</article>', source, re.S)
        if len(prompt_cards) != 3:
            errors.append(f"WORKBOOK_PREPARATION_PROMPTS:{route}:{len(prompt_cards)}")
        else:
            for index, card in enumerate(prompt_cards, 1):
                if card.count('<dl class="workbook-prompt-flow">') != 1 or 'data-preparation-reference' not in card:
                    errors.append(f"WORKBOOK_PROMPT_FLOW:{route}:{index}")
                reference = re.search(r'data-preparation-reference href="([^"]+#prompt-[0-9]+)"', card)
                if not reference:
                    errors.append(f"WORKBOOK_PROMPT_REFERENCE:{route}:{index}")
        tabs = re.findall(r'<button class="tab"[^>]+data-workbook-stage="([^"]+)"[^>]*>(.*?)</button>', source, re.S)
        if [value for value, _ in tabs] != ["in-class", "deepening", "consolidation"]:
            errors.append(f"WORKBOOK_STAGES:{route}:{[value for value, _ in tabs]}")
        tab_text = tuple(re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).strip() for _, body in tabs)
        if any(label not in text for label, text in zip(EXPECTED_STAGE_LABELS[locale], tab_text)):
            errors.append(f"WORKBOOK_STAGE_LABEL:{route}:{tab_text}")
        consolidation_start = source.find('<section class="sheet" id="sheet-consolidation"')
        consolidation = source[consolidation_start:] if consolidation_start >= 0 else ""
        for marker in ("data-consolidation-gate", 'id="workbook-rubric"', 'id="transferencia"'):
            if marker not in consolidation:
                errors.append(f"WORKBOOK_CONSOLIDATION:{route}:{marker}")
        if source.count('class="module-depth-disclosure workbook-step-depth"') < 6:
            errors.append(f"WORKBOOK_STEP_DISCLOSURES:{route}")
        if 'data-resource-next="playbook"' not in source:
            errors.append(f"WORKBOOK_NEXT_RESOURCE:{route}")
    elif resource == "playbook":
        hero = inner_block(source, '<section class="playbook-hero"', "</section>")
        if 'href="#intro"' not in hero or 'class="btn"' not in hero:
            errors.append(f"PLAYBOOK_HERO_CTA:{route}")
        toc = inner_block(source, '<details class="playbook-toc"', "</details>")
        if not toc or not re.findall(r'href="#[^"]+"', toc):
            errors.append(f"PLAYBOOK_INDEX:{route}")
    elif resource == "prompts":
        cards = source.count('class="library-prompt-card"')
        expected_cards = int(module["variant_validation"]["prompts_per_variant"])
        if cards != expected_cards:
            errors.append(f"PROMPTS_COUNT:{route}:{cards}!={expected_cards}")
        if source.count("data-prompt-format=") != cards * 4:
            errors.append(f"PROMPTS_LEVELS:{route}")
        if source.count('data-prompt-mode-select="template"') != cards or source.count('data-prompt-mode-select="demo"') != cards:
            errors.append(f"PROMPTS_MODES:{route}")
        if source.count("data-notebook-execution-guide") != 1:
            errors.append(f"PROMPTS_EXECUTION_GUIDE:{route}")
        demos = re.findall(r'<textarea[^>]+data-prompt-mode="demo"[^>]*>(.*?)</textarea>', source, re.S)
        if len(demos) != cards * 4 or any("&lt;" in value or "{{" in value for value in demos):
            errors.append(f"PROMPTS_DEMO_UNRESOLVED:{route}:{len(demos)}")
        module_id = str(module["module_id"])
        if module_id in DEPTH_PROMPT_REQUIREMENTS:
            prefix = DEPTH_PROMPT_REQUIREMENTS[module_id]["error_prefix"]
            if source.count("data-prompt-execution-gate") != 1:
                errors.append(f"{prefix}_PROMPTS_EXECUTION_GATE:{route}:{source.count('data-prompt-execution-gate')}")
            if RECEIVE_LABELS[module_id][locale] not in source:
                errors.append(f"{prefix}_PROMPTS_EXECUTION_RECEIVE:{route}")
            if any(DEMO_LABELS[locale] not in html.unescape(value) for value in demos):
                errors.append(f"{prefix}_PROMPTS_DEMO_NOT_SELF_CONTAINED:{route}")
            for forbidden in RENDER_FORBIDDEN:
                if forbidden in source:
                    errors.append(f"{prefix}_PROMPTS_DEMO_RESIDUAL:{route}:{forbidden}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", choices=("2", "3", "4", "all"), default="all")
    args = parser.parse_args()
    dod = json.loads((SRC / "module-resource-definition-of-done-v1.json").read_text(encoding="utf-8"))
    curriculum = json.loads((SRC / "curriculum-spec-v2.json").read_text(encoding="utf-8"))
    if canonical_hash(dod) != dod.get("self_sha256"):
        raise SystemExit("MODULE_DOD_SELF_HASH_INVALID")
    if dod.get("module_gate", {}).get("next_module_requires") != "PASS" or dod.get("state") != "RENDERED_DRAFT" or dod.get("publication_authorized") is not False:
        raise SystemExit("MODULE_DOD_GOVERNANCE_INVALID")
    if dod.get("comparison_policy", {}).get("code_identity_required") is not False:
        raise SystemExit("MODULE_DOD_CODE_IDENTITY_POLICY_INVALID")
    classes = {item["id"]: item for item in curriculum["classes"]}
    errors: list[str] = []
    pages = 0
    for module_id in selected_modules(args.module):
        module = classes[module_id]
        if module.get("module_id") in DEPTH_PROMPT_REQUIREMENTS:
            requirement = DEPTH_PROMPT_REQUIREMENTS[module["module_id"]]
            prefix = requirement["error_prefix"]
            depth = json.loads((SRC / module["depth_overlay"]["ref"]).read_text(encoding="utf-8"))
            for variant in depth.get("variants", []):
                items = variant.get("prompts", {}).get("items", [])
                key = f"{variant.get('locale')}:{variant.get('audience')}"
                expected_ids = [f"prompt-{index:02d}" for index in range(1, requirement["prompt_count"] + 1)]
                if (
                    len(items) != requirement["prompt_count"]
                    or [item.get("id") for item in items] != expected_ids
                    or any(not item.get("demo_artifact") for item in items)
                ):
                    errors.append(f"{prefix}_DEMO_ARTIFACT_CONTRACT:{key}")
                    continue
                gates = [item for item in items if "execution_gate" in item]
                if (
                    [item.get("id") for item in gates] != [requirement["gate_id"]]
                    or set(gates[0].get("execution_gate", {})) != {"action", "produces", "criteria"}
                    or any(not isinstance(gates[0]["execution_gate"].get(field), str) or not gates[0]["execution_gate"][field].strip() for field in ("action", "produces", "criteria"))
                ):
                    errors.append(f"{prefix}_EXECUTION_GATE_CONTRACT:{key}")
                receives = [item for item in items if "receive_override" in item]
                if [item.get("id") for item in receives] != [requirement["receive_id"]] or not receives[0].get("receive_override"):
                    errors.append(f"{prefix}_EXECUTION_RECEIVE_CONTRACT:{key}")
        for locale in LOCALES:
            for audience in AUDIENCES:
                for page in PAGE_TO_RESOURCE:
                    pages += 1
                    errors.extend(verify_page(page_path(locale, audience, page, module_id), locale, audience, module, page))
    css = (SRC / "site.css").read_text(encoding="utf-8")
    if 'nav[data-module-siblings] a[aria-current="page"]' not in css:
        errors.append("SIBLING_CURRENT_STYLE_MISSING")
    if '.workbook-v2[data-module-order] .workbook-outcome[data-module-number]:after' not in css:
        errors.append("WORKBOOK_MODULE_WATERMARK_STYLE_MISSING")
    runtime = (SRC / "site.js").read_text(encoding="utf-8")
    if "data-ephemeral-input" in runtime or set(re.findall(r"(?:readPreference|writePreference)\('([^']+)'", runtime)) - {"mdg_theme", "mdg_locale", "mdg_audience"}:
        errors.append("WORKBOOK_EPHEMERAL_STORAGE_VIOLATION")
    golden_path = DIST / "workbook" / "index.html"
    if not golden_path.is_file() or hashlib.sha256(golden_path.read_bytes()).hexdigest() != WORKBOOK_GOLDEN_SHA256:
        errors.append("WORKBOOK_GOLDEN_DRIFT")
    workbook_pages = [
        path for path in DIST.rglob("index.html")
        if 'class="workbook-v2"' in path.read_text(encoding="utf-8")
    ]
    if len(workbook_pages) != 24:
        errors.append(f"WORKBOOK_VARIANT_COUNT:{len(workbook_pages)}")
    manifest_path = DIST / "build-manifest.json"
    receipt_path = DIST / "build-receipt.json"
    if manifest_path.is_file() and receipt_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        binding = manifest.get("module_definition_of_done", {})
        if binding.get("self_sha256") != dod["self_sha256"] or receipt.get("module_definition_of_done") != binding:
            errors.append("MODULE_DOD_BUILD_BINDING_INVALID")
        if manifest.get("state") != "RENDERED_DRAFT" or manifest.get("publication_authorized") is not False or receipt.get("publication_authorized") is not False:
            errors.append("MODULE_DOD_STATE_INVALID")
    else:
        errors.append("MODULE_DOD_BUILD_EVIDENCE_MISSING")
    if errors:
        print(f"[EVIDENCE:MODULE_DEFINITION_OF_DONE] MODULE_DOD_FAILED module={args.module} pages={pages} failures={len(errors)}")
        for error in errors[:120]:
            print(error)
        return 1
    criteria_count = len(dod["common_criteria"]) + len(dod["editorial_criteria"]) + sum(len(group) for group in dod["resource_criteria"].values())
    print(f"[EVIDENCE:MODULE_DEFINITION_OF_DONE] MODULE_DOD_PASS module={args.module} pages={pages} criteria={criteria_count} code_identity_required=false next_module_requires=PASS state=RENDERED_DRAFT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
