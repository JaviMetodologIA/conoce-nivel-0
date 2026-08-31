#!/usr/bin/env python3
"""Byte-exact gate over the committed prompt snapshot (1,296 entries).

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
CONTRACTS_DIR = ROOT / "src" / "prompt-contracts"
LOCALES = ("es", "en", "pt")
ENTRIES_PER_LOCALE = 432
TOTAL_ENTRIES = ENTRIES_PER_LOCALE * len(LOCALES)

# The contract gate keeps the authored N1 body under the frozen v1 ceiling.
# This gate then keeps each rendered Template/Demo N1 projection under 2x that
# authored v2 body; inline help/examples are projection metadata, not an excuse
# to expand the underlying editorial argument.
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
    contracts = {}
    for path in CONTRACTS_DIR.glob("*.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        contracts[(document["surface"], document["intent_id"])] = document
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

            for key, value in entries.items():
                text = value["text"]
                if value["chars"] != len(text) or value["sha256"] != hashlib.sha256(text.encode("utf-8")).hexdigest():
                    raise SystemExit(f"SNAPSHOT_ENTRY_INCONSISTENT:{locale}:{key}")
                parts = key.split("/")
                if parts[-1] not in CAPPED_LEVELS:
                    continue
                surface, intent, _, audience = parts[:4]
                contract = contracts.get((surface, intent))
                if contract is None:
                    raise SystemExit(f"SNAPSHOT_CONTRACT_MISSING:{locale}:{key}")
                authored = contract["locales"][locale][audience]["prompt"]
                cap = length_cap(len(authored))
                if value["chars"] > cap:
                    raise SystemExit(f"SNAPSHOT_LENGTH_EXCESS:{locale}:{key}:{value['chars']}>{cap}")
            total += len(entries)

    if total != TOTAL_ENTRIES:
        raise SystemExit(f"SNAPSHOT_TOTAL_COUNT:{total}")
    print(f"PROMPT_SNAPSHOT_OK entries={total} locales={len(LOCALES)} capped_levels={','.join(CAPPED_LEVELS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
