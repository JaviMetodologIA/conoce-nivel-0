#!/usr/bin/env python3
"""Read back every M1-to-candidate comparison report and its material evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "qa/reports"
DIST = ROOT / "dist"
MODULES = {
    "2": "module-02-de-ocupado-a-productivo",
    "3": "module-03-trabajar-amplificado",
    "4": "module-04-trabajo-agentico",
}
CODE_MODULES = {"2": "ocupado-productivo", "3": "trabajo-amplificado", "4": "trabajo-agentico"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: dict[str, object]) -> str:
    payload = {key: item for key, item in value.items() if key != "self_sha256"}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"REPORT_NOT_OBJECT:{path}")
    return value


def verify(candidate: str) -> tuple[int, int]:
    folder = REPORTS / f"module-01-vs-{int(candidate):02d}"
    code = load(folder / "code-comparison.json")
    visual = load(folder / "visual-comparison.json")
    if code.get("self_sha256") != canonical_hash(code):
        raise AssertionError(f"CODE_REPORT_SELF_HASH:{candidate}")
    summary = code.get("summary", {})
    if (
        code.get("candidate_module") != CODE_MODULES[candidate]
        or summary.get("pairs") != 24
        or summary.get("output_parity") != "PASS"
        or summary.get("code_identity") != "NOT_REQUIRED_AND_NOT_PRESENT"
    ):
        raise AssertionError(f"CODE_REPORT_CONTRACT:{candidate}")
    if visual.get("self_sha256") != canonical_hash(visual):
        raise AssertionError(f"VISUAL_REPORT_SELF_HASH:{candidate}")
    visual_summary = visual.get("summary", {})
    if (
        visual.get("candidate_module") != MODULES[candidate]
        or len(visual.get("pairs", [])) != 8
        or visual_summary.get("image_count") != 32
        or visual_summary.get("verdict") != "PASS"
        or visual.get("publication_authorized") is not False
        or visual.get("state") != "RENDERED_DRAFT"
    ):
        raise AssertionError(f"VISUAL_REPORT_CONTRACT:{candidate}")
    inputs = visual.get("inputs", {})
    expected_inputs = {
        "build_manifest_sha256": sha(DIST / "build-manifest.json"),
        "build_receipt_sha256": sha(DIST / "build-receipt.json"),
        "definition_of_done_sha256": sha(ROOT / "src/module-resource-definition-of-done-v1.json"),
        "css_sha256": sha(ROOT / "src/site.css"),
        "runtime_sha256": sha(ROOT / "src/site.js"),
    }
    for key, expected in expected_inputs.items():
        if inputs.get(key) != expected:
            raise AssertionError(f"VISUAL_REPORT_INPUT:{candidate}:{key}")
    images = 0
    for pair in visual["pairs"]:
        for side in ("reference", "candidate"):
            for image in pair[side]["images"]:
                path = folder / "visual" / image["file"]
                if not path.is_file() or path.is_symlink() or sha(path) != image["sha256"]:
                    raise AssertionError(f"VISUAL_IMAGE_READBACK:{candidate}:{image['file']}")
                images += 1
    html = (folder / "visual-comparison.html").read_text(encoding="utf-8")
    if html.count(f'data-report-sha256="{visual["self_sha256"]}"') != 1:
        raise AssertionError(f"VISUAL_HTML_BINDING:{candidate}")
    return len(code["pairs"]), images


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=("2", "3", "4", "all"), default="all")
    args = parser.parse_args()
    selected = tuple(MODULES) if args.candidate == "all" else (args.candidate,)
    pair_total = image_total = 0
    for candidate in selected:
        pairs, images = verify(candidate)
        pair_total += pairs
        image_total += images
    print(
        "[EVIDENCE:MODULE_COMPARISON_REPORTS] MODULE_COMPARISON_REPORTS_PASS "
        f"candidates={','.join(selected)} code_pairs={pair_total} images={image_total} "
        "readback=sha256 state=RENDERED_DRAFT publication=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
