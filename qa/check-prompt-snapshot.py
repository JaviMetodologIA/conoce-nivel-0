#!/usr/bin/env python3
"""Byte-exact gate over the committed prompt snapshot (648 entries).

Regenerates the snapshot from dist/ with the same exporter that produced the
baseline, into a throwaway directory, and requires byte equality with the
committed snapshots/prompt-snapshot-{locale}.json. Any prompt text change that
is not accompanied by a regenerated snapshot fails here.

Stdlib only. Run after: python3 scripts/build.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS = ROOT / "snapshots"
BASELINE = SNAPSHOTS / "baseline"
LOCALES = ("es", "en", "pt")
ENTRIES_PER_LOCALE = 216
TOTAL_ENTRIES = ENTRIES_PER_LOCALE * len(LOCALES)

# Length cap ratified with qa/check-prompt-contracts.py: max(2 x baseline, 600).
# It governs the authored level-1 text — the workbook baselines it was sized
# against (239-286c) are natural prompts, and the floor exists because the
# mandatory quality tokens ate 20-29% of a 478c cap. Levels 2-4 are mechanically
# derived from `level_spec` by scripts/build.py, not authored, so the same
# formula does not apply to them; their fidelity is covered by the byte-exact
# comparison above.
LENGTH_FLOOR = 600
CAPPED_LEVELS = ("natural",)


def length_cap(baseline_chars: int) -> int:
    return max(2 * baseline_chars, LENGTH_FLOOR)


def load_exporter():
    spec = importlib.util.spec_from_file_location(
        "prompt_snapshot_exporter", ROOT / "scripts" / "export-prompt-snapshot.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    exporter = load_exporter()
    with tempfile.TemporaryDirectory() as workdir:
        regenerated = Path(workdir)
        exporter.ROOT = regenerated
        exporter.OUT_DIR = regenerated
        exporter.export()

        total = 0
        for locale in LOCALES:
            committed_path = SNAPSHOTS / f"prompt-snapshot-{locale}.json"
            if not committed_path.is_file():
                raise SystemExit(f"SNAPSHOT_MISSING:{committed_path.relative_to(ROOT)}")
            fresh_bytes = (regenerated / f"prompt-snapshot-{locale}.json").read_bytes()
            if committed_path.read_bytes() != fresh_bytes:
                raise SystemExit(f"SNAPSHOT_BYTE_DRIFT:{locale}")

            document = json.loads(committed_path.read_text(encoding="utf-8"))
            entries = {key: value for key, value in document.items() if key != "self_sha256"}
            if len(entries) != ENTRIES_PER_LOCALE:
                raise SystemExit(f"SNAPSHOT_ENTRY_COUNT:{locale}:{len(entries)}")
            if document.get("self_sha256") != exporter.canonical_self(entries):
                raise SystemExit(f"SNAPSHOT_SELF_DRIFT:{locale}")

            baseline = json.loads((BASELINE / f"prompt-snapshot-{locale}.json").read_text(encoding="utf-8"))
            for key, value in entries.items():
                text = value["text"]
                if value["chars"] != len(text) or value["sha256"] != hashlib.sha256(text.encode("utf-8")).hexdigest():
                    raise SystemExit(f"SNAPSHOT_ENTRY_INCONSISTENT:{locale}:{key}")
                if key.rsplit("/", 1)[-1] not in CAPPED_LEVELS:
                    continue
                reference = baseline.get(key)
                if reference is None:
                    raise SystemExit(f"SNAPSHOT_BASELINE_MISSING:{locale}:{key}")
                cap = length_cap(reference["chars"])
                if value["chars"] > cap:
                    raise SystemExit(f"SNAPSHOT_LENGTH_EXCESS:{locale}:{key}:{value['chars']}>{cap}")
            total += len(entries)

    if total != TOTAL_ENTRIES:
        raise SystemExit(f"SNAPSHOT_TOTAL_COUNT:{total}")
    print(f"PROMPT_SNAPSHOT_OK entries={total} locales={len(LOCALES)} capped_levels={','.join(CAPPED_LEVELS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
