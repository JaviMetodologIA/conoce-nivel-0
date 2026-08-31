#!/usr/bin/env python3
"""Fail-closed validation for Nivel 0 editorial depth overlays.

The imported module payloads remain immutable provenance records.  A depth
overlay may only add content to existing IDs and is consumed independently by
the renderer.  Positional merges, implicit locale fallbacks and undeclared
fields are deliberately rejected.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


LOCALES = ("es", "en", "pt")
AUDIENCES = ("persona", "empresa")
_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")


class DepthContractError(ValueError):
    """Raised when a depth overlay cannot be bound safely to its base."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DepthContractError(f"{path}: expected JSON object")
    return value


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DepthContractError(f"{path}: expected mapping")
    return value


def _sequence(value: Any, path: str, minimum: int = 0, maximum: int | None = None) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise DepthContractError(f"{path}: expected sequence")
    if len(value) < minimum or (maximum is not None and len(value) > maximum):
        suffix = f"..{maximum}" if maximum is not None else "+"
        raise DepthContractError(f"{path}: expected {minimum}{suffix} items, got {len(value)}")
    return value


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DepthContractError(f"{path}: expected non-empty text")
    return value.strip()


def _stable_id(value: Any, path: str) -> str:
    value = _text(value, path)
    if not _ID_RE.fullmatch(value):
        raise DepthContractError(f"{path}: expected stable kebab-case id")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], path: str) -> None:
    actual = set(value)
    if actual != expected:
        raise DepthContractError(
            f"{path}: exact keys required; missing={sorted(expected-actual)} extra={sorted(actual-expected)}"
        )


def _text_list(value: Any, path: str, minimum: int, maximum: int | None = None) -> list[str]:
    items = _sequence(value, path, minimum, maximum)
    return [_text(item, f"{path}[{index}]") for index, item in enumerate(items)]


def _refs(value: Any, path: str, allowed: set[str]) -> list[str]:
    refs = [_stable_id(item, f"{path}[{index}]") for index, item in enumerate(_sequence(value, path, 1))]
    if len(refs) != len(set(refs)):
        raise DepthContractError(f"{path}: duplicate authority reference")
    unknown = set(refs) - allowed
    if unknown:
        raise DepthContractError(f"{path}: unknown authority refs {sorted(unknown)}")
    return refs


def _concept_refs(value: Any, path: str, allowed: set[str]) -> list[str]:
    refs = [_stable_id(item, f"{path}[{index}]") for index, item in enumerate(_sequence(value, path, 1))]
    if len(refs) != len(set(refs)) or set(refs) - allowed:
        raise DepthContractError(f"{path}: concept refs must be unique and declared")
    return refs


def base_authority_refs(payload: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    for index, raw in enumerate(_sequence(payload.get("sourceMap"), "base.sourceMap", 1)):
        item = _mapping(raw, f"base.sourceMap[{index}]")
        for key in ("evidenceId", "sourceId"):
            if key in item:
                refs.add(_stable_id(item[key], f"base.sourceMap[{index}].{key}"))
        for claim_index, claim in enumerate(item.get("claimIds", [])):
            refs.add(_stable_id(claim, f"base.sourceMap[{index}].claimIds[{claim_index}]"))
    if not refs:
        raise DepthContractError("base.sourceMap: no resolvable authority refs")
    return refs


def _validate_moment(
    item: Mapping[str, Any], path: str, phase_ids: set[str], concept_ids: set[str], authority_ids: set[str]
) -> list[str]:
    expected = {
        "id", "phase", "explanation", "key_points", "application", "check_question",
        "micro_practice", "takeaway", "handoff", "concept_ids", "authority_refs",
    }
    _exact_keys(item, expected, path)
    _stable_id(item["id"], f"{path}.id")
    if _stable_id(item["phase"], f"{path}.phase") not in phase_ids:
        raise DepthContractError(f"{path}.phase: unknown phase")
    for key in ("explanation", "application", "check_question", "micro_practice", "takeaway", "handoff"):
        _text(item[key], f"{path}.{key}")
    _text_list(item["key_points"], f"{path}.key_points", 2, 3)
    concepts = _concept_refs(item["concept_ids"], f"{path}.concept_ids", concept_ids)
    _refs(item["authority_refs"], f"{path}.authority_refs", authority_ids)
    return concepts


def _validate_workbook_step(
    item: Mapping[str, Any], path: str, prompt_ids: set[str], concept_ids: set[str], authority_ids: set[str]
) -> list[str]:
    expected = {
        "id", "title", "brief", "actions", "deliverable", "example", "criteria",
        "watch_out", "reflection", "next_connection", "prompt_ref", "concept_ids", "authority_refs",
    }
    _exact_keys(item, expected, path)
    _stable_id(item["id"], f"{path}.id")
    for key in ("title", "brief", "deliverable", "example", "watch_out", "reflection", "next_connection"):
        _text(item[key], f"{path}.{key}")
    _text_list(item["actions"], f"{path}.actions", 2, 3)
    _text_list(item["criteria"], f"{path}.criteria", 2, 3)
    if _stable_id(item["prompt_ref"], f"{path}.prompt_ref") not in prompt_ids:
        raise DepthContractError(f"{path}.prompt_ref: must resolve to a base prompt")
    concepts = _concept_refs(item["concept_ids"], f"{path}.concept_ids", concept_ids)
    _refs(item["authority_refs"], f"{path}.authority_refs", authority_ids)
    return concepts


def _validate_chapter(
    item: Mapping[str, Any], path: str, prompt_ids: set[str], concept_ids: set[str], authority_ids: set[str]
) -> list[str]:
    expected = {
        "id", "principle", "explanation", "decision", "actions", "rule", "example",
        "antipattern", "checklist", "expected_evidence", "limit", "prompt_ref", "concept_ids", "authority_refs",
    }
    _exact_keys(item, expected, path)
    _stable_id(item["id"], f"{path}.id")
    for key in ("principle", "explanation", "decision", "rule", "example", "antipattern", "expected_evidence", "limit"):
        _text(item[key], f"{path}.{key}")
    _text_list(item["actions"], f"{path}.actions", 3, 4)
    _text_list(item["checklist"], f"{path}.checklist", 2, 3)
    if _stable_id(item["prompt_ref"], f"{path}.prompt_ref") not in prompt_ids:
        raise DepthContractError(f"{path}.prompt_ref: must resolve to a base prompt")
    concepts = _concept_refs(item["concept_ids"], f"{path}.concept_ids", concept_ids)
    _refs(item["authority_refs"], f"{path}.authority_refs", authority_ids)
    return concepts


def _validate_prompt_item(
    item: Mapping[str, Any], path: str, concept_ids: set[str], authority_ids: set[str]
) -> list[str]:
    required = {
        "id", "purpose", "when", "workflow", "frameworks", "guardrails",
        "acceptance_criteria", "edge_cases", "tradeoff", "limits", "next", "concept_ids", "authority_refs",
    }
    optional = {"demo_artifact", "receive_override", "execution_gate"}
    actual = set(item)
    if not required.issubset(actual) or actual - required - optional:
        raise DepthContractError(
            f"{path}: required/optional keys invalid; "
            f"missing={sorted(required-actual)} extra={sorted(actual-required-optional)}"
        )
    _stable_id(item["id"], f"{path}.id")
    for key in ("purpose", "when", "tradeoff", "next"):
        _text(item[key], f"{path}.{key}")
    _text_list(item["workflow"], f"{path}.workflow", 3, 5)
    _text_list(item["frameworks"], f"{path}.frameworks", 1, 3)
    _text_list(item["guardrails"], f"{path}.guardrails", 2, 3)
    _text_list(item["acceptance_criteria"], f"{path}.acceptance_criteria", 2, 4)
    _text_list(item["edge_cases"], f"{path}.edge_cases", 1, 2)
    _text_list(item["limits"], f"{path}.limits", 1, 2)
    if "demo_artifact" in item:
        _text(item["demo_artifact"], f"{path}.demo_artifact")
    if "receive_override" in item:
        _text(item["receive_override"], f"{path}.receive_override")
    if "execution_gate" in item:
        gate = _mapping(item["execution_gate"], f"{path}.execution_gate")
        _exact_keys(gate, {"action", "produces", "criteria"}, f"{path}.execution_gate")
        for key in ("action", "produces", "criteria"):
            _text(gate[key], f"{path}.execution_gate.{key}")
    concepts = _concept_refs(item["concept_ids"], f"{path}.concept_ids", concept_ids)
    _refs(item["authority_refs"], f"{path}.authority_refs", authority_ids)
    return concepts


def _difference_count(left: Mapping[str, Any], right: Mapping[str, Any], ignored: set[str]) -> int:
    """Count materially authored fields that differ between two audience units."""

    return sum(left.get(key) != right.get(key) for key in left if key not in ignored)


def _require_audience_depth(
    locale: str, persona: Mapping[str, Any], empresa: Mapping[str, Any]
) -> None:
    """Reject cosmetic audience variants while allowing shared governed facts.

    Every learning unit must alter at least one practical field. Orientation,
    rubric and transfer carry stronger minimums because they define who acts,
    what counts as evidence and how the result is reused.
    """

    orientation_keys = ("title", "body", "use_case", "ready_when", "inputs")
    orientation_diff = sum(
        persona["workbook"]["orientation"][key] != empresa["workbook"]["orientation"][key]
        for key in orientation_keys
    )
    if orientation_diff < 3:
        raise DepthContractError(
            f"overlay.variants.{locale}: audience orientation must differ materially"
        )

    rubric_pairs = zip(persona["workbook"]["rubric"], empresa["workbook"]["rubric"])
    if any(left["description"] == right["description"] for left, right in rubric_pairs):
        raise DepthContractError(
            f"overlay.variants.{locale}: each rubric level needs audience-specific evidence"
        )

    transfer_keys = ("title", "brief", "actions", "evidence", "review_after")
    transfer_diff = sum(
        persona["workbook"]["transfer_challenge"][key]
        != empresa["workbook"]["transfer_challenge"][key]
        for key in transfer_keys
    )
    if transfer_diff < 3:
        raise DepthContractError(
            f"overlay.variants.{locale}: transfer challenge must change actors and evidence"
        )

    unit_sets = (
        (
            "masterclass.moments",
            persona["masterclass"]["moments"],
            empresa["masterclass"]["moments"],
            {"id", "phase", "concept_ids", "authority_refs"},
        ),
        (
            "workbook.steps",
            [step for route in persona["workbook"]["routes"] for step in route["steps"]],
            [step for route in empresa["workbook"]["routes"] for step in route["steps"]],
            {"id", "prompt_ref", "concept_ids", "authority_refs"},
        ),
        (
            "playbook.chapters",
            persona["playbook"]["chapters"],
            empresa["playbook"]["chapters"],
            {"id", "prompt_ref", "concept_ids", "authority_refs"},
        ),
        (
            "prompts.items",
            persona["prompts"]["items"],
            empresa["prompts"]["items"],
            {"id", "next", "concept_ids", "authority_refs"},
        ),
    )
    for resource, personal_units, enterprise_units, ignored in unit_sets:
        if len(personal_units) != len(enterprise_units):
            raise DepthContractError(
                f"overlay.variants.{locale}.{resource}: audience unit count mismatch"
            )
        for index, (personal_unit, enterprise_unit) in enumerate(zip(personal_units, enterprise_units)):
            if _difference_count(personal_unit, enterprise_unit, ignored) < 1:
                raise DepthContractError(
                    f"overlay.variants.{locale}.{resource}[{index}]: audience clone"
                )


def validate_depth_overlay(
    profile: Mapping[str, Any], overlay: Mapping[str, Any], base_payload: Mapping[str, Any], base_sha256: str
) -> dict[tuple[str, str], Mapping[str, Any]]:
    """Validate and index an overlay without mutating its imported base."""

    if profile.get("schema_version") != "module-depth-profile-v1" or profile.get("publication_authorized") is not False:
        raise DepthContractError("profile: governance invalid")
    top_keys = {
        "schema_version", "overlay_id", "module_id", "base_payload_sha256", "depth_profile_ref",
        "maximum_state", "publication_authorized", "examples_are_synthetic", "concepts", "variants",
    }
    _exact_keys(_mapping(overlay, "overlay"), top_keys, "overlay")
    if overlay.get("schema_version") != "module-depth-overlay-v1":
        raise DepthContractError("overlay.schema_version: invalid")
    _stable_id(overlay.get("overlay_id"), "overlay.overlay_id")
    module_id = _stable_id(overlay.get("module_id"), "overlay.module_id")
    if module_id != _stable_id(base_payload.get("moduleId"), "base.moduleId"):
        raise DepthContractError("overlay.module_id: base mismatch")
    if overlay.get("base_payload_sha256") != base_sha256:
        raise DepthContractError("overlay.base_payload_sha256: base mismatch")
    if overlay.get("depth_profile_ref") != "module-depth-profile-v1.json":
        raise DepthContractError("overlay.depth_profile_ref: invalid")
    if overlay.get("maximum_state") != "RENDERED_DRAFT" or overlay.get("publication_authorized") is not False:
        raise DepthContractError("overlay: state or publication authority invalid")
    if overlay.get("examples_are_synthetic") is not True:
        raise DepthContractError("overlay.examples_are_synthetic: must be true")

    authority_ids = base_authority_refs(base_payload)
    concepts_raw = _sequence(overlay.get("concepts"), "overlay.concepts", 6, 10)
    concept_ids: set[str] = set()
    for index, raw in enumerate(concepts_raw):
        path = f"overlay.concepts[{index}]"
        concept = _mapping(raw, path)
        _exact_keys(concept, {"id", "title", "summary", "authority_refs"}, path)
        concept_id = _stable_id(concept["id"], f"{path}.id")
        if concept_id in concept_ids:
            raise DepthContractError(f"{path}.id: duplicate")
        concept_ids.add(concept_id)
        for field in ("title", "summary"):
            localized = _mapping(concept[field], f"{path}.{field}")
            if set(localized) != set(LOCALES):
                raise DepthContractError(f"{path}.{field}: expected exact locale map")
            for locale in LOCALES:
                _text(localized[locale], f"{path}.{field}.{locale}")
        _refs(concept["authority_refs"], f"{path}.authority_refs", authority_ids)

    base_variants = {
        (item.get("locale"), item.get("audience")): _mapping(item, "base.variant")
        for item in _sequence(base_payload.get("variants"), "base.variants", 6, 6)
    }
    expected_variants = {(locale, audience) for locale in LOCALES for audience in AUDIENCES}
    if set(base_variants) != expected_variants:
        raise DepthContractError("base.variants: expected exact 3x2 matrix")

    indexed: dict[tuple[str, str], Mapping[str, Any]] = {}
    for variant_index, raw in enumerate(_sequence(overlay.get("variants"), "overlay.variants", 6, 6)):
        path = f"overlay.variants[{variant_index}]"
        variant = _mapping(raw, path)
        _exact_keys(variant, {"locale", "audience", "masterclass", "workbook", "playbook", "prompts"}, path)
        key = (_text(variant["locale"], f"{path}.locale"), _text(variant["audience"], f"{path}.audience"))
        if key not in expected_variants or key in indexed:
            raise DepthContractError(f"{path}: invalid or duplicate variant {key}")
        base_variant = base_variants[key]
        base_module = _mapping(base_variant.get("module"), f"base.variants[{key}].module")
        base_prompt_ids = [item["id"] for item in base_module["promptLibrary"]["prompts"]]
        prompt_ids = set(base_prompt_ids)
        coverage = {resource: set() for resource in ("masterclass", "workbook", "playbook", "prompts")}

        masterclass = _mapping(variant["masterclass"], f"{path}.masterclass")
        _exact_keys(masterclass, {"phases", "moments"}, f"{path}.masterclass")
        phases = _sequence(masterclass["phases"], f"{path}.masterclass.phases", 3, 3)
        phase_ids: set[str] = set()
        phase_moments: list[str] = []
        for phase_index, raw_phase in enumerate(phases):
            phase_path = f"{path}.masterclass.phases[{phase_index}]"
            phase = _mapping(raw_phase, phase_path)
            _exact_keys(phase, {"id", "label", "purpose", "moment_ids"}, phase_path)
            phase_id = _stable_id(phase["id"], f"{phase_path}.id")
            if phase_id in phase_ids:
                raise DepthContractError(f"{phase_path}.id: duplicate")
            phase_ids.add(phase_id)
            _text(phase["label"], f"{phase_path}.label")
            _text(phase["purpose"], f"{phase_path}.purpose")
            phase_moments.extend(
                _stable_id(value, f"{phase_path}.moment_ids[{moment_index}]")
                for moment_index, value in enumerate(_sequence(phase["moment_ids"], f"{phase_path}.moment_ids", 1))
            )
        base_moment_ids = [item["id"] for item in base_module["masterclass"]["moments"]]
        if phase_moments != base_moment_ids:
            raise DepthContractError(f"{path}.masterclass.phases: moment coverage/order mismatch")
        moments = _sequence(masterclass["moments"], f"{path}.masterclass.moments", len(base_moment_ids), len(base_moment_ids))
        if [item.get("id") for item in moments] != base_moment_ids:
            raise DepthContractError(f"{path}.masterclass.moments: base ID/order mismatch")
        for moment_index, raw_moment in enumerate(moments):
            coverage["masterclass"].update(
                _validate_moment(_mapping(raw_moment, f"{path}.masterclass.moments[{moment_index}]"), f"{path}.masterclass.moments[{moment_index}]", phase_ids, concept_ids, authority_ids)
            )

        workbook = _mapping(variant["workbook"], f"{path}.workbook")
        _exact_keys(workbook, {"orientation", "preparation_prompts", "routes", "rubric", "transfer_challenge"}, f"{path}.workbook")
        orientation = _mapping(workbook["orientation"], f"{path}.workbook.orientation")
        _exact_keys(orientation, {"title", "body", "use_case", "ready_when", "inputs"}, f"{path}.workbook.orientation")
        for field in ("title", "body", "use_case", "ready_when"):
            _text(orientation[field], f"{path}.workbook.orientation.{field}")
        _text_list(orientation["inputs"], f"{path}.workbook.orientation.inputs", 2, 4)
        prep_ids: set[str] = set()
        for prep_index, raw_prep in enumerate(_sequence(workbook["preparation_prompts"], f"{path}.workbook.preparation_prompts", 3, 3)):
            prep_path = f"{path}.workbook.preparation_prompts[{prep_index}]"
            prep = _mapping(raw_prep, prep_path)
            _exact_keys(prep, {"id", "title", "purpose", "prompt", "produces", "library_ref", "authority_refs"}, prep_path)
            prep_id = _stable_id(prep["id"], f"{prep_path}.id")
            if prep_id in prep_ids:
                raise DepthContractError(f"{prep_path}.id: duplicate")
            prep_ids.add(prep_id)
            for field in ("title", "purpose", "prompt", "produces"):
                _text(prep[field], f"{prep_path}.{field}")
            if _stable_id(prep["library_ref"], f"{prep_path}.library_ref") not in prompt_ids:
                raise DepthContractError(f"{prep_path}.library_ref: unknown prompt")
            _refs(prep["authority_refs"], f"{prep_path}.authority_refs", authority_ids)
        base_routes = base_module["workbook"]["routes"]
        routes = _sequence(workbook["routes"], f"{path}.workbook.routes", len(base_routes), len(base_routes))
        if [item.get("id") for item in routes] != [item["id"] for item in base_routes]:
            raise DepthContractError(f"{path}.workbook.routes: base ID/order mismatch")
        for route_index, (raw_route, base_route) in enumerate(zip(routes, base_routes)):
            route_path = f"{path}.workbook.routes[{route_index}]"
            route = _mapping(raw_route, route_path)
            _exact_keys(route, {"id", "title", "brief", "steps"}, route_path)
            _text(route["title"], f"{route_path}.title")
            _text(route["brief"], f"{route_path}.brief")
            steps = _sequence(route["steps"], f"{route_path}.steps", len(base_route["steps"]), len(base_route["steps"]))
            if [item.get("id") for item in steps] != [item["id"] for item in base_route["steps"]]:
                raise DepthContractError(f"{route_path}.steps: base ID/order mismatch")
            for step_index, raw_step in enumerate(steps):
                coverage["workbook"].update(
                    _validate_workbook_step(_mapping(raw_step, f"{route_path}.steps[{step_index}]"), f"{route_path}.steps[{step_index}]", prompt_ids, concept_ids, authority_ids)
                )
        rubric = _sequence(workbook["rubric"], f"{path}.workbook.rubric", 3, 3)
        for rubric_index, raw_rubric in enumerate(rubric, 1):
            rubric_path = f"{path}.workbook.rubric[{rubric_index-1}]"
            item = _mapping(raw_rubric, rubric_path)
            _exact_keys(item, {"level", "label", "description"}, rubric_path)
            if item["level"] != rubric_index:
                raise DepthContractError(f"{rubric_path}.level: expected {rubric_index}")
            _text(item["label"], f"{rubric_path}.label")
            _text(item["description"], f"{rubric_path}.description")
        transfer = _mapping(workbook["transfer_challenge"], f"{path}.workbook.transfer_challenge")
        _exact_keys(transfer, {"title", "brief", "actions", "evidence", "review_after", "authority_refs"}, f"{path}.workbook.transfer_challenge")
        for field in ("title", "brief", "evidence", "review_after"):
            _text(transfer[field], f"{path}.workbook.transfer_challenge.{field}")
        _text_list(transfer["actions"], f"{path}.workbook.transfer_challenge.actions", 2, 3)
        _refs(transfer["authority_refs"], f"{path}.workbook.transfer_challenge.authority_refs", authority_ids)

        playbook = _mapping(variant["playbook"], f"{path}.playbook")
        _exact_keys(playbook, {"chapters", "glossary", "faq", "closing_checklist"}, f"{path}.playbook")
        base_chapters = base_module["playbook"]["chapters"]
        chapters = _sequence(playbook["chapters"], f"{path}.playbook.chapters", len(base_chapters), len(base_chapters))
        if [item.get("id") for item in chapters] != [item["id"] for item in base_chapters]:
            raise DepthContractError(f"{path}.playbook.chapters: base ID/order mismatch")
        for chapter_index, raw_chapter in enumerate(chapters):
            coverage["playbook"].update(
                _validate_chapter(_mapping(raw_chapter, f"{path}.playbook.chapters[{chapter_index}]"), f"{path}.playbook.chapters[{chapter_index}]", prompt_ids, concept_ids, authority_ids)
            )
        for glossary_index, raw_glossary in enumerate(_sequence(playbook["glossary"], f"{path}.playbook.glossary", 4, 6)):
            glossary_path = f"{path}.playbook.glossary[{glossary_index}]"
            item = _mapping(raw_glossary, glossary_path)
            _exact_keys(item, {"term", "definition"}, glossary_path)
            _text(item["term"], f"{glossary_path}.term")
            _text(item["definition"], f"{glossary_path}.definition")
        for faq_index, raw_faq in enumerate(_sequence(playbook["faq"], f"{path}.playbook.faq", 3, 4)):
            faq_path = f"{path}.playbook.faq[{faq_index}]"
            item = _mapping(raw_faq, faq_path)
            _exact_keys(item, {"question", "answer"}, faq_path)
            _text(item["question"], f"{faq_path}.question")
            _text(item["answer"], f"{faq_path}.answer")
        _text_list(playbook["closing_checklist"], f"{path}.playbook.closing_checklist", 3, 6)

        prompts = _mapping(variant["prompts"], f"{path}.prompts")
        _exact_keys(prompts, {"graph_summary", "items"}, f"{path}.prompts")
        graph = _mapping(prompts["graph_summary"], f"{path}.prompts.graph_summary")
        _exact_keys(graph, {"title", "body", "independent_use"}, f"{path}.prompts.graph_summary")
        for field in ("title", "body", "independent_use"):
            _text(graph[field], f"{path}.prompts.graph_summary.{field}")
        prompt_items = _sequence(prompts["items"], f"{path}.prompts.items", len(base_prompt_ids), len(base_prompt_ids))
        if [item.get("id") for item in prompt_items] != base_prompt_ids:
            raise DepthContractError(f"{path}.prompts.items: base ID/order mismatch")
        for prompt_index, raw_prompt in enumerate(prompt_items):
            prompt_path = f"{path}.prompts.items[{prompt_index}]"
            prompt_item = _mapping(raw_prompt, prompt_path)
            expected_next = base_prompt_ids[prompt_index + 1] if prompt_index + 1 < len(base_prompt_ids) else "module-next"
            if prompt_item.get("next") != expected_next:
                raise DepthContractError(f"{prompt_path}.next: expected {expected_next}")
            coverage["prompts"].update(
                _validate_prompt_item(prompt_item, prompt_path, concept_ids, authority_ids)
            )

        for resource, covered in coverage.items():
            if covered != concept_ids:
                raise DepthContractError(
                    f"{path}.{resource}: concept coverage mismatch missing={sorted(concept_ids-covered)}"
                )
        indexed[key] = variant

    if set(indexed) != expected_variants:
        raise DepthContractError("overlay.variants: expected exact 3x2 matrix")
    for locale in LOCALES:
        if json.dumps(indexed[(locale, "persona")], ensure_ascii=False, sort_keys=True) == json.dumps(indexed[(locale, "empresa")], ensure_ascii=False, sort_keys=True):
            raise DepthContractError(f"overlay.variants.{locale}: audience clone")
        _require_audience_depth(
            locale,
            indexed[(locale, "persona")],
            indexed[(locale, "empresa")],
        )
    return indexed


__all__ = (
    "DepthContractError",
    "base_authority_refs",
    "load_json",
    "sha256_file",
    "validate_depth_overlay",
)
