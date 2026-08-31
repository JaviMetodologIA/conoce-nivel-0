#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
CURRICULUM_PATH = SRC / "curriculum-spec-v2.json"
LEDGER_PATH = SRC / "curriculum-provenance-rights-v2.json"
RESOURCE_PATH = SRC / "public-resource-spec-v1.json"
DEPTH_PROFILE_PATH = SRC / "modules" / "module-depth-profile-v1.json"

RESOURCE_KEYS = {"masterclass", "workbook", "playbook", "prompt_library"}
VARIANTS = {
    (locale, audience)
    for locale in ("es", "en", "pt")
    for audience in ("persona", "empresa")
}
ALLOWED_SOURCE_STATES = {"CONTENT_DRAFT", "RENDERED_DRAFT"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pdf_metadata(path: Path) -> tuple[int, bool]:
    try:
        result = subprocess.run(
            ["pdfinfo", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise AssertionError("CURRICULUM_PDFINFO_UNAVAILABLE") from error
    except subprocess.CalledProcessError as error:
        raise AssertionError(f"CURRICULUM_PDFINFO_FAILED:{path.name}") from error
    pages = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, re.MULTILINE)
    tagged = re.search(r"^Tagged:\s+(yes|no)\s*$", result.stdout, re.MULTILINE)
    if not pages or not tagged:
        raise AssertionError(f"CURRICULUM_PDFINFO_INCOMPLETE:{path.name}")
    return int(pages.group(1)), tagged.group(1) == "yes"


curriculum = load(CURRICULUM_PATH)
ledger = load(LEDGER_PATH)
resources = load(RESOURCE_PATH)

# [EVIDENCE:GOVERNANCE_CEILING] Local import authority never grants publication.
if (
    curriculum.get("schema_version") != "curriculum-spec-v2"
    or curriculum.get("local_only") is not True
    or curriculum.get("publication_authorized") is not False
):
    raise AssertionError("CURRICULUM_GOVERNANCE_INVALID")
scope = ledger.get("scope", {})
if (
    ledger.get("schema_version") != "curriculum-provenance-rights-v2"
    or scope.get("local_only") is not True
    or scope.get("publication_authorized") is not False
    or scope.get("network_required") is not False
    or scope.get("external_mutation") is not False
):
    raise AssertionError("CURRICULUM_LEDGER_GOVERNANCE_INVALID")
depth_policy = ledger.get("editorial_depth_policy", {})
if (
    depth_policy.get("profile_ref") != "modules/module-depth-profile-v1.json"
    or depth_policy.get("profile_sha256") != sha256(DEPTH_PROFILE_PATH)
    or depth_policy.get("base_payloads_immutable") is not True
    or depth_policy.get("notebooklm_queries", {}).get("authority_granted") is not False
    or depth_policy.get("local_only") is not True
    or depth_policy.get("publication_authorized") is not False
):
    raise AssertionError("CURRICULUM_DEPTH_POLICY_INVALID")
if resources.get("state") != "RENDERED_DRAFT" or resources.get("publication_authorized") is not False:
    raise AssertionError("CURRICULUM_M1_STATE_INVALID")

classes = curriculum.get("classes", [])
if [item.get("id") for item in classes] != [
    "ia-panorama",
    "ocupado-productivo",
    "trabajo-amplificado",
    "trabajo-agentico",
]:
    raise AssertionError("CURRICULUM_CLASS_ORDER_INVALID")
if any(set(item.get("resource_state", {})) != RESOURCE_KEYS for item in classes):
    raise AssertionError("CURRICULUM_RESOURCE_MATRIX_INVALID")
logical_resources = sum(len(item["resource_state"]) for item in classes)
if logical_resources != 16:
    raise AssertionError(f"CURRICULUM_LOGICAL_RESOURCE_COUNT:{logical_resources}")

required_variants = {
    (item.get("locale"), item.get("audience"))
    for item in curriculum.get("required_variants", [])
}
if required_variants != VARIANTS or len(curriculum.get("required_variants", [])) != 6:
    raise AssertionError("CURRICULUM_REQUIRED_VARIANTS_INVALID")

ledger_entries = {item.get("module_id"): item for item in ledger.get("entries", [])}
if len(ledger_entries) != 3:
    raise AssertionError("CURRICULUM_LEDGER_ENTRY_COUNT")

# M1 remains the governed flat-route source and contributes the fourth official PDF.
m1_deck = resources.get("deck", {})
pdf_contracts = [
    {
        "module_id": "ia-panorama",
        "path": SRC / m1_deck.get("source_asset", ""),
        "sha256": m1_deck.get("sha256"),
        "page_count": m1_deck.get("page_count"),
        "tagged": False,
    }
]

variant_count = 0
for item in classes[1:]:
    module_id = item.get("module_id")
    if item.get("maximum_source_state") not in ALLOWED_SOURCE_STATES:
        raise AssertionError(f"CURRICULUM_SOURCE_STATE_INVALID:{module_id}")
    content = item.get("content", {})
    depth = item.get("depth_overlay", {})
    official_pdf = item.get("official_pdf", {})
    content_path = SRC / content.get("ref", "")
    depth_path = SRC / depth.get("ref", "")
    pdf_path = SRC / official_pdf.get("ref", "")
    entry = ledger_entries.get(module_id)
    if not entry:
        raise AssertionError(f"CURRICULUM_LEDGER_ENTRY_MISSING:{module_id}")

    # [EVIDENCE:HASH_BINDING] Spec, imported bytes, payload and provenance ledger agree.
    if not content_path.is_file() or sha256(content_path) != content.get("sha256"):
        raise AssertionError(f"CURRICULUM_PAYLOAD_HASH_INVALID:{module_id}")
    if not depth_path.is_file() or sha256(depth_path) != depth.get("sha256"):
        raise AssertionError(f"CURRICULUM_DEPTH_HASH_INVALID:{module_id}")
    if not pdf_path.is_file() or sha256(pdf_path) != official_pdf.get("sha256"):
        raise AssertionError(f"CURRICULUM_PDF_HASH_INVALID:{module_id}")
    if (
        entry.get("payload", {}).get("imported_ref") != content.get("ref")
        or entry.get("payload", {}).get("source_sha256") != content.get("sha256")
        or entry.get("payload", {}).get("imported_sha256") != content.get("sha256")
        or entry.get("payload", {}).get("exact_copy") is not True
        or entry.get("editorial_depth_overlay", {}).get("ref") != depth.get("ref")
        or entry.get("editorial_depth_overlay", {}).get("sha256") != depth.get("sha256")
        or entry.get("editorial_depth_overlay", {}).get("base_payload_sha256") != content.get("sha256")
        or entry.get("editorial_depth_overlay", {}).get("profile_ref") != "modules/module-depth-profile-v1.json"
        or entry.get("editorial_depth_overlay", {}).get("exact_copy_of_external_run") is not False
        or entry.get("editorial_depth_overlay", {}).get("local_only") is not True
        or entry.get("editorial_depth_overlay", {}).get("publication_authorized") is not False
        or entry.get("official_pdf", {}).get("imported_ref") != official_pdf.get("ref")
        or entry.get("official_pdf", {}).get("source_sha256") != official_pdf.get("sha256")
        or entry.get("official_pdf", {}).get("imported_sha256") != official_pdf.get("sha256")
        or entry.get("official_pdf", {}).get("exact_copy") is not True
    ):
        raise AssertionError(f"CURRICULUM_LEDGER_BINDING_INVALID:{module_id}")

    payload = load(content_path)
    if payload.get("moduleId") != module_id:
        raise AssertionError(f"CURRICULUM_PAYLOAD_MODULE_INVALID:{module_id}")
    payload_pdf = payload.get("officialPdf", {})
    payload_pdf_pages = payload_pdf.get("pageCount", payload_pdf.get("pages"))
    if payload_pdf.get("sha256") != official_pdf.get("sha256") or payload_pdf_pages != official_pdf.get("page_count"):
        raise AssertionError(f"CURRICULUM_PAYLOAD_PDF_BINDING_INVALID:{module_id}")

    variants = payload.get("variants", [])
    actual_variants = {(variant.get("locale"), variant.get("audience")) for variant in variants}
    if actual_variants != VARIANTS or len(variants) != 6:
        raise AssertionError(f"CURRICULUM_VARIANT_MATRIX_INVALID:{module_id}")
    expected = item.get("variant_validation", {})
    for variant in variants:
        module = variant.get("module", {})
        moments = module.get("masterclass", {}).get("moments", [])
        routes = module.get("workbook", {}).get("routes", [])
        workbook_steps = sum(len(route.get("steps", [])) for route in routes)
        chapters = module.get("playbook", {}).get("chapters", [])
        prompts = module.get("promptLibrary", {}).get("prompts", [])
        counts = {
            "moments_per_variant": len(moments),
            "workbook_steps_per_variant": workbook_steps,
            "playbook_chapters_per_variant": len(chapters),
            "prompts_per_variant": len(prompts),
        }
        if any(counts[key] != expected.get(key) for key in counts):
            raise AssertionError(
                f"CURRICULUM_VARIANT_COUNTS_INVALID:{module_id}:"
                f"{variant.get('locale')}:{variant.get('audience')}:{counts}"
            )
        if module.get("moduleId") != module_id or module.get("order") != item.get("order"):
            raise AssertionError(f"CURRICULUM_VARIANT_MODULE_INVALID:{module_id}")
    variant_count += len(variants)

    # [EVIDENCE:PROVENANCE_TAGS] Each import carries material hash, scope and rights evidence.
    evidence = set(item.get("evidence_tags", []))
    if not {
        f"payload:sha256:{content['sha256']}",
        f"depth-overlay:sha256:{depth['sha256']}",
        f"pdf:sha256:{official_pdf['sha256']}",
        "scope:local-only",
        "publication:false",
    }.issubset(evidence):
        raise AssertionError(f"CURRICULUM_EVIDENCE_TAGS_INVALID:{module_id}")
    ledger_evidence = set(entry.get("evidence_tags", []))
    if not {
        "payload-hash-verified",
        "depth-overlay-hash-verified",
        "depth-base-bound",
        "audience-depth-verified",
        "pdf-hash-verified",
        "page-count-verified",
        "variant-counts-verified",
        "local-only",
        "publication-false",
    }.issubset(ledger_evidence):
        raise AssertionError(f"CURRICULUM_LEDGER_EVIDENCE_TAGS_INVALID:{module_id}")

    pdf_contracts.append(
        {
            "module_id": module_id,
            "path": pdf_path,
            "sha256": official_pdf.get("sha256"),
            "page_count": official_pdf.get("page_count"),
            "tagged": official_pdf.get("tagged"),
        }
    )

if variant_count != 18:
    raise AssertionError(f"CURRICULUM_IMPORTED_VARIANT_COUNT:{variant_count}")

# [EVIDENCE:PDF_BYTES] All four official PDFs are byte-bound and page-count verified.
if [item["page_count"] for item in pdf_contracts] != [18, 11, 12, 15]:
    raise AssertionError("CURRICULUM_PDF_PAGE_SEQUENCE_INVALID")
for item in pdf_contracts:
    path = item["path"]
    if not path.is_file() or sha256(path) != item["sha256"]:
        raise AssertionError(f"CURRICULUM_PDF_BYTES_INVALID:{item['module_id']}")
    actual_pages, actual_tagged = pdf_metadata(path)
    if actual_pages != item["page_count"] or actual_tagged is not item["tagged"]:
        raise AssertionError(f"CURRICULUM_PDF_METADATA_INVALID:{item['module_id']}")

print(
    "[EVIDENCE:CURRICULUM_EXPANSION_V2] CURRICULUM_EXPANSION_V2_OK "
    f"logical_resources={logical_resources} variants={variant_count} pdfs={len(pdf_contracts)} "
    "pages=18/11/12/15 state_ceiling=RENDERED_DRAFT publication=false"
)
