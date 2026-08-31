from __future__ import annotations

import hashlib
import html
import json
import posixpath
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "src" / "brand-release-v3"
CHROME_SPEC = ROOT / "src" / "conoce-chrome-spec-v1.json"
EDITORIAL_SPEC = ROOT / "src" / "editorial-sitemap-spec-v1.json"
MANIFEST_RAW = "3deaa35db4120e227325867d8165b0cb448756455698651f8a0dfa1405d99686"
RECEIPT_RAW = "966bf64511232853becff2d33e99181f5ab21cf724fd51dd9a9a98b0faaa1243"
LOCALES = ("es", "en", "pt")
AUDIENCES = ("persona", "empresa")
RESOURCE_PAGES = ("landing", "deck", "workbook", "playbook", "prompts")
EDITORIAL_PAGES = ("level0", "how", "resources_index", "intakes")
PAGES = RESOURCE_PAGES + EDITORIAL_PAGES
ALLOWED_STORAGE = ("mdg_theme", "mdg_locale", "mdg_audience")
PARENT = "https://metodologia.info/"
PUBLIC = "https://javimetodologia.github.io/conoce-nivel-0/"
DEFAULT_MODULE_ID = "ia-panorama"
MODULE_IDS = (DEFAULT_MODULE_ID, "ocupado-productivo", "trabajo-amplificado", "trabajo-agentico")
MODULE_ROUTES = {
    DEFAULT_MODULE_ID: {
        "order": 1,
        "slugs": {"es": None, "en": None, "pt": None},
        "labels": {
            "es": "Módulo 01 · IA: qué está pasando y cómo sacarle provecho",
            "en": "Module 01 · AI: what is happening and how to benefit",
            "pt": "Módulo 01 · IA: o que está acontecendo e como aproveitar",
        },
    },
    "ocupado-productivo": {
        "order": 2,
        "slugs": {
            "es": "02-de-ocupado-a-productivo",
            "en": "02-from-busy-to-productive",
            "pt": "02-de-ocupado-a-produtivo",
        },
        "labels": {
            "es": "Módulo 02 · De ocupado a productivo",
            "en": "Module 02 · From busy to productive",
            "pt": "Módulo 02 · De ocupado a produtivo",
        },
    },
    "trabajo-amplificado": {
        "order": 3,
        "slugs": {
            "es": "03-trabajo-amplificado",
            "en": "03-amplified-work",
            "pt": "03-trabalho-amplificado",
        },
        "labels": {
            "es": "Módulo 03 · Trabajo amplificado",
            "en": "Module 03 · Amplified work",
            "pt": "Módulo 03 · Trabalho amplificado",
        },
    },
    "trabajo-agentico": {
        "order": 4,
        "slugs": {
            "es": "04-trabajo-agentico",
            "en": "04-agentic-work",
            "pt": "04-trabalho-agentico",
        },
        "labels": {
            "es": "Módulo 04 · Trabajo agéntico",
            "en": "Module 04 · Agentic work",
            "pt": "Módulo 04 · Trabalho agêntico",
        },
    },
}
RESOURCE_SEGMENTS = {"deck": "masterclass", "workbook": "workbook", "playbook": "playbook", "prompts": "prompts"}

ICON_MOON = '<svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
ICON_GLOBE = '<svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'
ICON_USER = '<svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
ICON_BUILDING = '<svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4M8 6h.01M16 6h.01M12 6h.01M12 10h.01M12 14h.01M16 10h.01M16 14h.01M8 10h.01M8 14h.01"/></svg>'
ICON_CHEVRON = '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><path d="m7 10 5 5 5-5"/></svg>'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_self(value: dict, field: str) -> str:
    payload = {key: item for key, item in value.items() if key != field}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    return hashlib.sha256(raw.encode()).hexdigest()


@lru_cache(maxsize=1)
def validate_release() -> tuple[dict, dict, dict]:
    manifest_path = RELEASE / "brand-release-manifest-v1.json"
    receipt_path = RELEASE / "brand-release-receipt-v1.json"
    if sha(manifest_path) != MANIFEST_RAW or sha(receipt_path) != RECEIPT_RAW:
        raise RuntimeError("DIGITAL_BRAND_RAW_BINDING_DRIFT")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if manifest["manifestSha256"] != canonical_self(manifest, "manifestSha256"):
        raise RuntimeError("DIGITAL_BRAND_MANIFEST_SELF_DRIFT")
    if receipt["receiptSha256"] != canonical_self(receipt, "receiptSha256"):
        raise RuntimeError("DIGITAL_BRAND_RECEIPT_SELF_DRIFT")
    if receipt["manifestSha256"] != MANIFEST_RAW or receipt["outputCount"] != len(manifest["outputs"]):
        raise RuntimeError("DIGITAL_BRAND_RECEIPT_BINDING_DRIFT")
    if manifest["locales"] != list(LOCALES) or manifest["audiences"] != list(AUDIENCES):
        raise RuntimeError("DIGITAL_BRAND_VARIANT_DRIFT")
    if manifest["networkRequired"] or manifest["publicationAuthority"]:
        raise RuntimeError("DIGITAL_BRAND_EFFECT_DRIFT")
    for ref, expected in manifest["outputs"].items():
        if sha(RELEASE / ref) != expected:
            raise RuntimeError(f"DIGITAL_BRAND_OUTPUT_DRIFT:{ref}")
    config = json.loads((RELEASE / "brand-config.json").read_text(encoding="utf-8"))
    return manifest, receipt, config


def validate_chrome_document(spec: dict) -> dict:
    required = {
        "schema_version", "site_id", "state", "publication_authorized", "network_required",
        "canonical_origin", "self_hash_model", "self_sha256", "brand_authority", "identity",
        "allowed_storage_keys", "locales", "audiences", "pages", "home_navigation", "resource_overview", "resources", "breadcrumbs",
        "parent", "parent_routes", "footer_groups", "copy",
    }
    if set(spec) != required or spec.get("schema_version") != "conoce-chrome-spec-v1" or spec.get("site_id") != "conoce-nivel-0":
        raise RuntimeError("CONOCE_CHROME_SHAPE_INVALID")
    if spec.get("state") != "RENDERED_DRAFT" or spec.get("publication_authorized") is not False or spec.get("network_required") is not False:
        raise RuntimeError("CONOCE_CHROME_STATE_INVALID")
    if spec.get("canonical_origin") != PUBLIC:
        raise RuntimeError("CONOCE_CHROME_ORIGIN_INVALID")
    if spec.get("self_hash_model") != "sha256(sorted-json-without-self_sha256)" or spec.get("self_sha256") != canonical_self(spec, "self_sha256"):
        raise RuntimeError("CONOCE_CHROME_SELF_DRIFT")
    authority = spec.get("brand_authority", {})
    if authority != {
        "release_id": "metodologia-digital-brand-v3",
        "manifest_sha256": MANIFEST_RAW,
        "receipt_sha256": RECEIPT_RAW,
        "immutable": True,
        "roles_reused": ["tokens", "fonts", "organization_mark", "asset_rights"],
    }:
        raise RuntimeError("CONOCE_CHROME_BRAND_AUTHORITY_INVALID")
    identity = spec.get("identity", {})
    if identity != {
        "display_label": "Conoce · Nivel 0",
        "organization": "MetodologIA",
        "organization_relationship": "by",
        "organization_mark_replacement": False,
    }:
        raise RuntimeError("CONOCE_CHROME_IDENTITY_INVALID")
    if spec.get("allowed_storage_keys") != list(ALLOWED_STORAGE):
        raise RuntimeError("CONOCE_CHROME_STORAGE_INVALID")
    if spec.get("locales") != list(LOCALES) or spec.get("audiences") != list(AUDIENCES) or spec.get("pages") != list(PAGES):
        raise RuntimeError("CONOCE_CHROME_VARIANTS_INVALID")
    home = spec.get("home_navigation", [])
    if [(item.get("id"), item.get("page")) for item in home] != [
        ("level0_page", "level0"), ("how_page", "how"), ("intakes_page", "intakes")
    ] or spec.get("resource_overview") != {"id": "resources_overview", "page": "resources_index"}:
        raise RuntimeError("CONOCE_CHROME_HOME_ROUTES_INVALID")
    resources = spec.get("resources", [])
    if [(item.get("id"), item.get("page")) for item in resources] != [
        ("masterclass", "deck"), ("workbook", "workbook"), ("playbook", "playbook"), ("prompts", "prompts")
    ]:
        raise RuntimeError("CONOCE_CHROME_RESOURCE_ROUTES_INVALID")
    if spec.get("breadcrumbs") != {
        "rendered_ssr": True,
        "jsonld_type": "BreadcrumbList",
        "fragments_allowed": False,
        "last_item": "aria-current-page-not-link",
        "hierarchy": {
            "landing": ["home"],
            "editorial": ["home", "current"],
            "resources_index": ["home", "current"],
            "resource": ["home", "resources_overview", "current"],
        },
    }:
        raise RuntimeError("CONOCE_CHROME_BREADCRUMB_INVALID")
    if spec.get("parent") != {"id": "metodologia", "href": PARENT, "same_tab": True}:
        raise RuntimeError("CONOCE_CHROME_PARENT_INVALID")
    parent_routes = spec.get("parent_routes", [])
    if not parent_routes or parent_routes[0] != {"id": "metodologia", "href": PARENT}:
        raise RuntimeError("CONOCE_CHROME_PARENT_ROUTES_INVALID")
    if any(not isinstance(item.get("href"), str) or not (
        item["href"].startswith("https://metodologia.info/") or item["href"] == "https://campus.metodologia.info/"
    ) for item in parent_routes):
        raise RuntimeError("CONOCE_CHROME_PARENT_ROUTE_UNSAFE")
    expected_groups = [
        ("level0", ["level0_page", "how_page", "resources_overview", "intakes_page"]),
        ("resources", ["masterclass", "workbook", "playbook", "prompts"]),
        ("methodology", ["metodologia", "method", "campus", "contact", "legal"]),
    ]
    if [(item.get("id"), item.get("items")) for item in spec.get("footer_groups", [])] != expected_groups:
        raise RuntimeError("CONOCE_CHROME_FOOTER_INVALID")
    required_copy = {
        "skip", "nav_label", "menu_open", "menu_close", "identity_name", "identity_level",
        "identity_by", "identity_accessible", "home", "level0_page", "how_page", "resources_overview", "intakes_page", "resources",
        "masterclass", "workbook", "playbook", "prompts", "parent_cta", "metodologia", "method",
        "campus", "contact", "legal", "level0", "methodology", "footer_description",
        "footer_relationship", "theme", "light", "dark", "language", "audience", "persona", "empresa",
        "change_to", "preferences",
    }
    if set(spec.get("copy", {})) != set(LOCALES):
        raise RuntimeError("CONOCE_CHROME_COPY_LOCALES_INVALID")
    for locale in LOCALES:
        copy = spec["copy"][locale]
        if set(copy) != required_copy or any(not isinstance(copy[key], str) or not copy[key].strip() for key in required_copy):
            raise RuntimeError(f"CONOCE_CHROME_COPY_INVALID:{locale}")
        if copy["identity_level"] != "Nivel 0" or not copy["identity_accessible"].startswith("Conoce · Nivel 0"):
            raise RuntimeError(f"CONOCE_CHROME_IDENTITY_COPY_INVALID:{locale}")
    return spec


@lru_cache(maxsize=1)
def validate_chrome_spec() -> dict:
    validate_release()
    return validate_chrome_document(json.loads(CHROME_SPEC.read_text(encoding="utf-8")))


def validate_editorial_document(spec: dict) -> dict:
    required = {"schema_version", "state", "publication_authorized", "network_required", "canonical_origin", "self_hash_model", "self_sha256", "locales", "audiences", "page_order", "pages", "audience_copy", "copy"}
    if set(spec) != required:
        raise RuntimeError("EDITORIAL_SITEMAP_SHAPE_INVALID")
    if spec.get("schema_version") != "editorial-sitemap-spec-v1" or spec.get("state") != "RENDERED_DRAFT":
        raise RuntimeError("EDITORIAL_SITEMAP_CONTRACT_INVALID")
    if spec.get("publication_authorized") is not False or spec.get("network_required") is not False:
        raise RuntimeError("EDITORIAL_SITEMAP_EFFECT_INVALID")
    if spec.get("canonical_origin") != PUBLIC or spec.get("self_sha256") != canonical_self(spec, "self_sha256"):
        raise RuntimeError("EDITORIAL_SITEMAP_BINDING_INVALID")
    if spec.get("locales") != list(LOCALES) or spec.get("audiences") != list(AUDIENCES) or spec.get("page_order") != list(EDITORIAL_PAGES):
        raise RuntimeError("EDITORIAL_SITEMAP_VARIANTS_INVALID")
    pages = spec.get("pages", {})
    if set(pages) != set(EDITORIAL_PAGES):
        raise RuntimeError("EDITORIAL_SITEMAP_PAGES_INVALID")
    for locale in LOCALES:
        slugs = []
        for page in EDITORIAL_PAGES:
            item = pages[page]
            slug = item.get("slugs", {}).get(locale)
            anchors = item.get("anchors", [])
            sections = spec.get("copy", {}).get(locale, {}).get(page, {}).get("sections", [])
            if not isinstance(slug, str) or not re_full_slug(slug) or len(anchors) != 5 or len(set(anchors)) != 5:
                raise RuntimeError(f"EDITORIAL_SITEMAP_ROUTE_INVALID:{locale}:{page}")
            if anchors[1:] != [section.get("id") for section in sections]:
                raise RuntimeError(f"EDITORIAL_SITEMAP_ANCHORS_INVALID:{locale}:{page}")
            slugs.append(slug)
            for audience in AUDIENCES:
                audience_copy = spec.get("audience_copy", {}).get(locale, {}).get(audience, {}).get(page, {})
                if set(audience_copy) != {"label", "body", "points"} or not audience_copy["label"] or not audience_copy["body"] or not audience_copy["points"]:
                    raise RuntimeError(f"EDITORIAL_SITEMAP_AUDIENCE_INVALID:{locale}:{audience}:{page}")
        if len(slugs) != len(set(slugs)):
            raise RuntimeError(f"EDITORIAL_SITEMAP_SLUG_COLLISION:{locale}")
    serialized = json.dumps(spec, ensure_ascii=False).lower()
    if any(value in serialized for value in ("inscripciones abiertas", "enrollment open", "inscrições abertas")) or any(f"20{year:02d}-{month:02d}" in serialized for year in range(27) for month in range(1, 13)):
        raise RuntimeError("EDITORIAL_SITEMAP_TEMPORAL_CLAIM_INVALID")
    return spec


def re_full_slug(value: str) -> bool:
    return bool(value) and all(char.isalnum() or char == "-" for char in value) and value == value.lower()


@lru_cache(maxsize=1)
def validate_editorial_spec() -> dict:
    return validate_editorial_document(json.loads(EDITORIAL_SPEC.read_text(encoding="utf-8")))


def _validate_route_variant(locale: str, audience: str, page: str, module_id: str) -> None:
    if locale not in LOCALES or audience not in AUDIENCES or page not in PAGES or module_id not in MODULE_IDS:
        raise RuntimeError("CONOCE_CHROME_RENDER_VARIANT_INVALID")


def module_anchor(module_id: str) -> str:
    if module_id not in MODULE_IDS:
        raise RuntimeError("CONOCE_MODULE_INVALID")
    return f'module-{MODULE_ROUTES[module_id]["order"]:02d}'


def page_dir(locale: str, audience: str, page: str, module_id: str = DEFAULT_MODULE_ID) -> str:
    """Return a canonical output directory while preserving the original flat M1 routes."""
    _validate_route_variant(locale, audience, page, module_id)
    parts = [] if locale == "es" else [locale]
    if audience == "empresa":
        parts.append("empresa")
    if module_id != DEFAULT_MODULE_ID and page in RESOURCE_SEGMENTS:
        parts.extend([
            "modules" if locale == "en" else "modulos",
            MODULE_ROUTES[module_id]["slugs"][locale],
            RESOURCE_SEGMENTS[page],
        ])
    elif page in EDITORIAL_PAGES:
        parts.append(validate_editorial_spec()["pages"][page]["slugs"][locale])
    elif page != "landing":
        parts.append(page)
    return "/".join(parts) or "."


def page_ref(locale: str, audience: str, page: str, module_id: str = DEFAULT_MODULE_ID) -> str:
    return posixpath.join(page_dir(locale, audience, page, module_id), "index.html")


def relative_page(source_locale: str, source_audience: str, source_page: str,
                  target_locale: str, target_audience: str, target_page: str,
                  source_module_id: str = DEFAULT_MODULE_ID,
                  target_module_id: str | None = None) -> str:
    target_module_id = source_module_id if target_module_id is None else target_module_id
    ref = posixpath.relpath(
        page_ref(target_locale, target_audience, target_page, target_module_id),
        page_dir(source_locale, source_audience, source_page, source_module_id),
    )
    return ref if ref.startswith(".") else f"./{ref}"


def absolute_page(locale: str, audience: str, page: str,
                  module_id: str = DEFAULT_MODULE_ID, origin: str = PUBLIC) -> str:
    route = page_dir(locale, audience, page, module_id)
    return origin.rstrip("/") + "/" + ("" if route == "." else route + "/")


def canonical_url(module_id: str, page: str, locale: str, audience: str,
                  origin: str = PUBLIC) -> str:
    """Return the canonical URL for the explicit module/page/locale/audience tuple."""
    return absolute_page(locale, audience, page, module_id, origin)


def hreflang_urls(module_id: str, page: str, locale: str, audience: str,
                  origin: str = PUBLIC) -> dict[str, str]:
    """Return same-module locale alternates plus the Spanish x-default."""
    _validate_route_variant(locale, audience, page, module_id)
    alternates = {
        code: absolute_page(code, audience, page, module_id, origin)
        for code in LOCALES
    }
    alternates["x-default"] = alternates["es"]
    return alternates


def breadcrumb_model(module_id: str, page: str, locale: str, audience: str) -> list[dict[str, str | bool]]:
    """Build route-bound breadcrumb data, including the module tier on nested resources."""
    _validate_route_variant(locale, audience, page, module_id)
    spec = validate_chrome_spec()
    copy = spec["copy"][locale]
    items: list[dict[str, str | bool]] = [{
        "id": "home",
        "label": copy["home"],
        "href": relative_page(locale, audience, page, locale, audience, "landing", module_id, DEFAULT_MODULE_ID),
        "current": page == "landing",
    }]
    if page in RESOURCE_SEGMENTS:
        overview = spec["resource_overview"]
        overview_href = relative_page(
            locale, audience, page, locale, audience, overview["page"], module_id, DEFAULT_MODULE_ID
        )
        items.append({"id": overview["id"], "label": copy["resources"], "href": overview_href, "current": False})
        if module_id != DEFAULT_MODULE_ID:
            items.append({
                "id": module_id,
                "label": MODULE_ROUTES[module_id]["labels"][locale],
                "href": f"{overview_href}#{module_anchor(module_id)}",
                "current": False,
            })
    if page != "landing":
        current_id = next((item["id"] for item in spec["resources"] if item["page"] == page), page)
        current_label = copy.get(current_id, current_id)
        items.append({"id": current_id, "label": current_label, "href": "", "current": True})
    return items


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _link(href: str, label: str, current: bool = False, attrs: str = "") -> str:
    active = ' aria-current="page"' if current else ""
    return f'<a href="{esc(href)}"{active}{attrs}>{esc(label)}</a>'


def _routes(spec: dict, locale: str, audience: str, page: str,
            module_id: str = DEFAULT_MODULE_ID) -> dict[str, str]:
    landing = relative_page(
        locale, audience, page, locale, audience, "landing", module_id, DEFAULT_MODULE_ID
    )
    routes = {
        item["id"]: relative_page(
            locale, audience, page, locale, audience, item["page"], module_id, DEFAULT_MODULE_ID
        )
        for item in spec["home_navigation"]
    }
    routes[spec["resource_overview"]["id"]] = relative_page(
        locale, audience, page, locale, audience, spec["resource_overview"]["page"], module_id, DEFAULT_MODULE_ID
    )
    routes.update({
        item["id"]: relative_page(
            locale, audience, page, locale, audience, item["page"], module_id, module_id
        )
        for item in spec["resources"]
    })
    routes.update({
        candidate: f'{routes[spec["resource_overview"]["id"]]}#{module_anchor(candidate)}'
        for candidate in MODULE_IDS
    })
    routes.update({item["id"]: item["href"] for item in spec["parent_routes"]})
    routes["home"] = landing
    return routes


def _controls(spec: dict, locale: str, audience: str, page: str,
              module_id: str = DEFAULT_MODULE_ID) -> str:
    copy = spec["copy"][locale]
    variants = {
        lang: {
            target: relative_page(locale, audience, page, lang, target, page, module_id, module_id)
            for target in AUDIENCES
        } for lang in LOCALES
    }
    next_locale = LOCALES[(LOCALES.index(locale) + 1) % len(LOCALES)]
    next_audience = "empresa" if audience == "persona" else "persona"
    theme_label = f'{copy["theme"]}: {copy["light"]}. {copy["change_to"]} {copy["dark"]}'
    locale_label = f'{copy["language"]}: {locale.upper()}. {copy["change_to"]} {next_locale.upper()}'
    audience_label = f'{copy["audience"]}: {copy[audience]}. {copy["change_to"]} {copy[next_audience]}'
    matrix = esc(json.dumps(variants, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return (
        f'<div class="mdg-controls" role="group" aria-label="{esc(copy["preferences"])}" '
        f'data-conoce-preferences data-module-id="{esc(module_id)}" data-locale="{locale}" data-audience="{audience}" data-variant-links="{matrix}" '
        f'data-theme-label="{esc(copy["theme"])}" data-light-label="{esc(copy["light"])}" data-dark-label="{esc(copy["dark"])}" data-change-label="{esc(copy["change_to"])}">'
        f'<button class="mdg-control" type="button" role="switch" aria-checked="false" aria-label="{esc(theme_label)}" data-mdg-theme>{ICON_MOON}</button>'
        f'<a class="mdg-control" href="{esc(variants[next_locale][audience])}" aria-label="{esc(locale_label)}" data-mdg-locale="{next_locale}">{ICON_GLOBE}</a>'
        f'<a class="mdg-control" href="{esc(variants[locale][next_audience])}" aria-label="{esc(audience_label)}" data-mdg-audience="{next_audience}">{ICON_BUILDING if audience == "empresa" else ICON_USER}</a>'
        '<span class="mdg-sr-only" aria-live="polite" data-mdg-status></span></div>'
    )


@lru_cache(maxsize=216)
def shell(locale: str, audience: str, page: str,
          module_id: str = DEFAULT_MODULE_ID) -> dict:
    _validate_route_variant(locale, audience, page, module_id)
    spec = validate_chrome_spec()
    copy = spec["copy"][locale]
    routes = _routes(spec, locale, audience, page, module_id)
    source_dir = page_dir(locale, audience, page, module_id)
    root_ref = posixpath.relpath("assets/brand", source_dir)
    root_ref = root_ref if root_ref.startswith(".") else f"./{root_ref}"
    editorial_links = {
        item["id"]: _link(routes[item["id"]], copy[item["id"]], item["page"] == page, ' data-conoce-editorial-link')
        for item in spec["home_navigation"]
    }
    home_link = _link(routes["home"], copy["home"], page == "landing", ' data-conoce-home-link')
    overview = spec["resource_overview"]
    overview_link = _link(routes[overview["id"]], copy[overview["id"]], page == overview["page"], ' data-conoce-resource-overview')
    module_links = "".join(
        _link(
            routes[candidate],
            MODULE_ROUTES[candidate]["labels"][locale],
            candidate == module_id and page in RESOURCE_SEGMENTS,
            f' data-conoce-module-link data-module-id="{esc(candidate)}"',
        )
        for candidate in MODULE_IDS
    )
    resource_current = page in RESOURCE_PAGES[1:] or page == "resources_index"
    resource_state = ' data-current="true"' if resource_current else ""
    header = (
        f'<a class="mdg-skip" href="#main">{esc(copy["skip"])}</a>'
        '<header class="mdg-header conoce-header" data-conoce-header>'
        f'<button class="mdg-menu conoce-menu" type="button" aria-expanded="false" aria-controls="conoce-primary-nav" aria-label="{esc(copy["menu_open"])}" data-open-label="{esc(copy["menu_open"])}" data-close-label="{esc(copy["menu_close"])}" data-conoce-menu><span aria-hidden="true"></span></button>'
        f'<a class="mdg-brand conoce-brand" href="{esc(routes["home"])}" aria-label="{esc(copy["identity_accessible"])}">'
        f'<img src="{esc(root_ref)}/assets/metodologia-logo.svg" width="36" height="36" alt="">'
        f'<span><strong>{esc(copy["identity_name"])}</strong><small>{esc(copy["identity_level"])} <em>· {esc(copy["identity_by"])}</em></small></span></a>'
        f'<nav class="mdg-nav conoce-nav" id="conoce-primary-nav" aria-label="{esc(copy["nav_label"])}" data-conoce-nav>{home_link}{editorial_links["level0_page"]}{editorial_links["how_page"]}'
        f'<details class="conoce-resources" data-conoce-resources{resource_state}><summary>{esc(copy["resources"])}{ICON_CHEVRON}</summary><div class="conoce-resource-menu">{overview_link}{module_links}</div></details>{editorial_links["intakes_page"]}</nav>'
        f'<a class="mdg-header-cta conoce-parent-cta" href="{esc(PARENT)}" data-conoce-parent>{esc(copy["parent_cta"])}</a></header>'
    )
    footer_groups = []
    for group in spec["footer_groups"]:
        links = "".join(_link(routes[item_id], copy[item_id]) for item_id in group["items"])
        footer_groups.append(f'<nav aria-label="{esc(copy[group["id"]])}"><h3>{esc(copy[group["id"]])}</h3>{links}</nav>')
    footer = (
        '<footer class="mdg-footer conoce-footer" data-conoce-footer><div class="mdg-footer-grid">'
        f'<div class="conoce-footer-identity"><h2>{esc(copy["identity_name"])} <span>· {esc(copy["identity_level"])}</span></h2>'
        f'<p>{esc(copy["footer_description"])}</p><small>{esc(copy["footer_relationship"])}</small></div>'
        f'{"".join(footer_groups)}</div><div class="mdg-footer-bottom"><span>© 2026 MetodologIA · Copyleft</span><span>RENDERED_DRAFT</span></div></footer>'
    )
    return {
        "header": header,
        "controls": _controls(spec, locale, audience, page, module_id),
        "footer": footer,
        "stylesheetBase": f"{root_ref}/runtime",
        "moduleId": module_id,
        "route": page_dir(locale, audience, page, module_id),
        "spec": deepcopy(spec),
    }


def theme_bootstrap() -> str:
    return '<script>try{var t=localStorage.getItem("mdg_theme");if(t==="light"||t==="dark")document.documentElement.dataset.theme=t}catch(e){}</script>'
