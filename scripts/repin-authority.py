#!/usr/bin/env python3
"""Print (never write) the triple pin for an authority file.

Usage: python3 scripts/repin-authority.py src/prompt-intent-authority-v2.json

Prints the three values a consumer needs to re-pin an authority:
1. source_sha256 — sha256 of the file bytes.
2. self_sha256   — canonical self hash (sorted-json without self_sha256 + newline).
3. intent_authority — the binding block ready to paste into a consumer contract.

Standalone by design: no build.py import, so it works even while build gates fail.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def canonical_self(value, field):
    payload = {key: item for key, item in value.items() if key != field}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip())
        return 2
    path = Path(sys.argv[1])
    if not path.is_absolute():
        path = ROOT / path
    raw = path.read_bytes()
    document = json.loads(raw.decode('utf-8'))
    source_sha256 = hashlib.sha256(raw).hexdigest()
    self_sha256 = canonical_self(document, 'self_sha256')
    declared = document.get('self_sha256')
    consumer_binding = {
        'source': str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        'source_sha256': source_sha256,
        'self_sha256': self_sha256,
        'consumer_override': False,
    }
    manifest_binding = {
        'schema_version': document.get('schema_version'),
        'source': consumer_binding['source'],
        'source_sha256': source_sha256,
        'self_sha256': self_sha256,
        'rights': document.get('source_provenance', {}).get('rights'),
        'state': document.get('state'),
        'publication_authorized': document.get('publication_authorized'),
    }
    print(f'source_sha256: {source_sha256}')
    print(f'self_sha256: {self_sha256}')
    if declared != self_sha256:
        print(f'WARNING: declared self_sha256 ({declared}) != canonical self hash; file needs resealing before pinning')
    print('intent_authority (spec_contract.semantic_specificity binding):')
    print(json.dumps(consumer_binding, ensure_ascii=False, indent=2))
    print('intent_authority (manifest binding):')
    print(json.dumps(manifest_binding, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
