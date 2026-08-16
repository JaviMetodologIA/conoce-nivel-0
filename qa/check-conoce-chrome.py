#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from brand import AUDIENCES, CHROME_SPEC, LOCALES, MANIFEST_RAW, PAGES, RECEIPT_RAW, canonical_self, sha, shell, validate_chrome_document, validate_chrome_spec  # noqa: E402


def expect(code: str, mutate) -> None:
    candidate = copy.deepcopy(source)
    mutate(candidate)
    if code != "CONOCE_CHROME_SELF_DRIFT":
        candidate["self_sha256"] = canonical_self(candidate, "self_sha256")
    try:
        validate_chrome_document(candidate)
    except RuntimeError as error:
        if str(error) != code:
            raise AssertionError(f"Expected {code}, got {error}") from error
    else:
        raise AssertionError(f"Mutation passed unexpectedly: {code}")


source = json.loads(CHROME_SPEC.read_text(encoding="utf-8"))
validate_chrome_spec()
for locale in LOCALES:
    for audience in AUDIENCES:
        for page in PAGES:
            rendered = shell(locale, audience, page)
            chrome = rendered["header"] + rendered["controls"] + rendered["footer"]
            if any(slot in chrome for slot in ("data-mdg-header", "data-mdg-controls", "data-mdg-footer")):
                raise AssertionError(f"Corporate source slot rendered: {locale}:{audience}:{page}")
expect("CONOCE_CHROME_STATE_INVALID", lambda item: item.update(state="FINAL"))
expect("CONOCE_CHROME_STATE_INVALID", lambda item: item.update(publication_authorized=True))
expect("CONOCE_CHROME_ORIGIN_INVALID", lambda item: item.update(canonical_origin="https://example.com/"))
expect("CONOCE_CHROME_SELF_DRIFT", lambda item: item.update(self_sha256="0" * 64))
expect("CONOCE_CHROME_BRAND_AUTHORITY_INVALID", lambda item: item["brand_authority"].update(manifest_sha256="0" * 64))
expect("CONOCE_CHROME_BRAND_AUTHORITY_INVALID", lambda item: item["brand_authority"].update(receipt_sha256="0" * 64))
expect("CONOCE_CHROME_STORAGE_INVALID", lambda item: item["allowed_storage_keys"].append("tracking"))
expect("CONOCE_CHROME_HOME_ROUTES_INVALID", lambda item: item["home_navigation"][0].update(page="landing"))
expect("CONOCE_CHROME_RESOURCE_ROUTES_INVALID", lambda item: item["resources"][0].update(page="masterclass"))
expect("CONOCE_CHROME_RESOURCE_ROUTES_INVALID", lambda item: item["resources"].pop())
expect("CONOCE_CHROME_BREADCRUMB_INVALID", lambda item: item["breadcrumbs"].update(fragments_allowed=True))
expect("CONOCE_CHROME_VARIANTS_INVALID", lambda item: item["locales"].pop())
expect("CONOCE_CHROME_PARENT_INVALID", lambda item: item["parent"].update(href="https://example.com/"))
expect("CONOCE_CHROME_PARENT_INVALID", lambda item: item["parent"].update(same_tab=False))
expect("CONOCE_CHROME_FOOTER_INVALID", lambda item: item["footer_groups"][2]["items"].remove("legal"))

if sha(ROOT / "src/brand-release-v3/brand-release-manifest-v1.json") != MANIFEST_RAW:
    raise AssertionError("Brand manifest changed")
if sha(ROOT / "src/brand-release-v3/brand-release-receipt-v1.json") != RECEIPT_RAW:
    raise AssertionError("Brand receipt changed")

print("CONOCE_CHROME_MUTATIONS_OK 15/15 source_variants=54")
