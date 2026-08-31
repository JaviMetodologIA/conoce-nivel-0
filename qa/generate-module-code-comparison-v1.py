#!/usr/bin/env python3
"""Generate a deterministic code/DOM comparison between M1 and one candidate module."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
SRC = ROOT / "src"
REPORTS = ROOT / "qa" / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from brand import AUDIENCES, DEFAULT_MODULE_ID, MODULE_IDS, page_dir  # noqa: E402


LOCALES = ("es", "en", "pt")
PAGES = ("deck", "workbook", "playbook", "prompts")
RESOURCE = {"deck": "masterclass", "workbook": "workbook", "playbook": "playbook", "prompts": "prompts"}
MARKERS = {
    "masterclass": ("official-pdf-card", "masterclass-player", "deck-controls"),
    "workbook": ("workbook-hero-grid", "sheet-tabs", "data-consolidation-gate"),
    "playbook": ("playbook-hero-grid", "playbook-toc", "playbook-content"),
    "prompts": ("data-notebook-execution-guide", "library-prompt-card", "data-prompt-format"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def route_path(locale: str, audience: str, page: str, module_id: str) -> Path:
    route = page_dir(locale, audience, page, module_id)
    return (DIST if route == "." else DIST / route) / "index.html"


def visible_words(source: str) -> int:
    cleaned = re.sub(r"<(?:script|style|textarea)[^>]*>.*?</(?:script|style|textarea)>", " ", source, flags=re.I | re.S)
    cleaned = html.unescape(re.sub(r"<[^>]+>", " ", cleaned))
    return len(re.findall(r"\b[^\W\d_][\wÀ-ÿ’-]*\b", cleaned, re.UNICODE))


def snapshot(path: Path, resource: str) -> dict[str, object]:
    source = path.read_text(encoding="utf-8")
    main = re.search(r"<main\b([^>]*)>", source)
    # Require a real ``id`` attribute boundary. ``\bid`` also matches the
    # ``id`` suffix in ``data-module-id`` and creates false duplicate reports.
    ids = re.findall(r'(?:^|[\s<])id="([^"]+)"', source)
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha(path),
        "bytes": path.stat().st_size,
        "visible_words": visible_words(source),
        "main_identity": {
            name: (re.search(rf'{name}="([^"]+)"', main.group(1)).group(1) if main and re.search(rf'{name}="([^"]+)"', main.group(1)) else None)
            for name in ("data-module-id", "data-module-order", "data-module-resource", "data-locale", "data-audience")
        },
        "markers": {marker: source.count(marker) for marker in MARKERS[resource]},
        "sibling_navigation": source.count("data-module-siblings"),
        "current_resource": source.count('aria-current="page"'),
        "unique_ids": len(ids) == len(set(ids)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=("2", "3", "4"), required=True)
    args = parser.parse_args()
    candidate_id = MODULE_IDS[int(args.candidate) - 1]
    dod = json.loads((SRC / "module-resource-definition-of-done-v1.json").read_text(encoding="utf-8"))
    pairs: list[dict[str, object]] = []
    for locale in LOCALES:
        for audience in AUDIENCES:
            for page in PAGES:
                resource = RESOURCE[page]
                reference = snapshot(route_path(locale, audience, page, DEFAULT_MODULE_ID), resource)
                candidate = snapshot(route_path(locale, audience, page, candidate_id), resource)
                pairs.append({
                    "locale": locale,
                    "audience": audience,
                    "resource": resource,
                    "reference": reference,
                    "candidate": candidate,
                    "semantic_markers_present": all(candidate["markers"][marker] >= 1 for marker in MARKERS[resource]),
                    "visible_density_ratio": round(candidate["visible_words"] / max(reference["visible_words"], 1), 4),
                })
    source_refs = {
        "reference": {
            "pipeline": "legacy-parallel",
            "compiler": "scripts/build.py",
            "entrypoints": ["masterclass", "workbook", "playbook", "prompt_library_page"],
            "main_identity_typed": False,
        },
        "candidate": {
            "pipeline": "typed-module-renderer",
            "compiler": "scripts/build.py",
            "renderer": "scripts/module_renderers.py",
            "entrypoints": ["render_masterclass", "render_workbook", "render_playbook", "render_prompts"],
            "main_identity_typed": True,
        },
        "shared": {
            "ui_primitives": "scripts/ui_primitives.py",
            "css": "src/site.css",
            "runtime": "src/site.js",
            "brand_shell": "scripts/brand.py",
        },
    }
    payload: dict[str, object] = {
        "schema_version": "module-code-comparison-v1",
        "reference_module": DEFAULT_MODULE_ID,
        "candidate_module": candidate_id,
        "definition_of_done": {
            "ref": "src/module-resource-definition-of-done-v1.json",
            "self_sha256": dod["self_sha256"],
            "required_parity": dod["comparison_policy"]["required_parity"],
            "code_identity_required": dod["comparison_policy"]["code_identity_required"],
        },
        "architecture": source_refs,
        "architecture_verdict": "ACCEPTED_DEBT_LEGACY_REFERENCE",
        "pairs": pairs,
        "summary": {
            "pairs": len(pairs),
            "semantic_marker_pass": sum(bool(pair["semantic_markers_present"]) for pair in pairs),
            "unique_candidate_dom": sum(bool(pair["candidate"]["unique_ids"]) for pair in pairs),
            "maximum_visible_density_ratio": max(pair["visible_density_ratio"] for pair in pairs),
            "output_parity": "PASS" if all(pair["semantic_markers_present"] and pair["candidate"]["unique_ids"] for pair in pairs) else "GAP",
            "code_identity": "NOT_REQUIRED_AND_NOT_PRESENT",
            "state": "RENDERED_DRAFT",
            "publication_authorized": False,
        },
        "inputs": {
            "build_manifest_sha256": sha(DIST / "build-manifest.json"),
            "build_receipt_sha256": sha(DIST / "build-receipt.json"),
            "build_py_sha256": sha(ROOT / "scripts" / "build.py"),
            "renderer_sha256": sha(ROOT / "scripts" / "module_renderers.py"),
            "css_sha256": sha(SRC / "site.css"),
            "runtime_sha256": sha(SRC / "site.js"),
        },
        "self_hash_model": "sha256(sorted-json-without-self_sha256)",
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    payload["self_sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    folder = REPORTS / f"module-01-vs-{int(args.candidate):02d}"
    folder.mkdir(parents=True, exist_ok=True)
    json_path = folder / "code-comparison.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"# Comparación de código · Módulo 1 ↔ Módulo {int(args.candidate)}",
        "",
        f"- Paridad de salida: **{payload['summary']['output_parity']}**",
        f"- Identidad de código: **{payload['summary']['code_identity']}**",
        f"- Deuda explícita: **{payload['architecture_verdict']}**",
        f"- Pares ES/EN/PT × Persona/Empresa × cuatro recursos: **{len(pairs)}**",
        f"- Densidad visible máxima frente a M1: **{payload['summary']['maximum_visible_density_ratio']}×**",
        "",
        "M1 conserva su renderer legacy; el candidato usa payloads y renderers tipados. El DoD exige la misma gramática visual, funcional y semántica, no bytes ni implementación idénticos.",
        "",
        "| Recurso | Pares | Marcadores | Densidad máxima |",
        "|---|---:|---:|---:|",
    ]
    for resource in MARKERS:
        selected = [pair for pair in pairs if pair["resource"] == resource]
        lines.append(f"| {resource} | {len(selected)} | {sum(bool(pair['semantic_markers_present']) for pair in selected)}/{len(selected)} | {max(pair['visible_density_ratio'] for pair in selected)}× |")
    (folder / "code-comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[EVIDENCE:MODULE_CODE_COMPARISON] MODULE_CODE_COMPARISON_OK candidate={args.candidate} pairs={len(pairs)} output={payload['summary']['output_parity']} code_identity=not_required report={json_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
