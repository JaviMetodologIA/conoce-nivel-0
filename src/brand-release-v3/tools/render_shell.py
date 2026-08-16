#!/usr/bin/env python3
import argparse
import html
import json
from pathlib import Path


LOCALES = ["es", "en", "pt"]
AUDIENCES = ["persona", "empresa"]
ICON_MOON = '<svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
ICON_GLOBE = '<svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'
ICON_USER = '<svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
ICON_BUILDING = '<svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01M16 6h.01M12 6h.01M12 10h.01M12 14h.01M16 10h.01M16 14h.01M8 10h.01M8 14h.01"/></svg>'


def fail(code: str, detail: str = "") -> None:
    raise SystemExit(f"{code}{':' + detail if detail else ''}")


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail("SHELL_CONFIG_INVALID", f"{path}:{exc}")


def load_brand_config(release: Path) -> dict:
    candidates = [release / "brand-config.json", release / "dist" / "brand-config.json"]
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        fail("SHELL_BRAND_CONFIG_MISSING", str(candidates[0]))
    brand = load(path)
    if set(brand) != {"schemaVersion", "locales", "audiences", "profiles", "routes", "copy"}:
        fail("SHELL_BRAND_CONFIG_KEYS_INVALID")
    if brand["schemaVersion"] != "brand-shell-config-v1":
        fail("SHELL_BRAND_CONFIG_VERSION_INVALID")
    if brand["locales"] != LOCALES or set(brand["copy"]) != set(LOCALES):
        fail("SHELL_BRAND_LOCALES_INVALID")
    if brand["audiences"] != AUDIENCES:
        fail("SHELL_BRAND_AUDIENCES_INVALID")
    profiles = brand["profiles"]
    if set(profiles) != {"schemaVersion", "profiles"} or profiles["schemaVersion"] != "brand-profile-set-v1":
        fail("SHELL_BRAND_PROFILES_INVALID")
    profile_ids = [item.get("id") for item in profiles["profiles"] if isinstance(item, dict)]
    if len(profile_ids) != len(set(profile_ids)) or set(profile_ids) != {"marketing", "learning", "thematic", "campus", "application"}:
        fail("SHELL_BRAND_PROFILES_INVALID")
    return {"copy": brand["copy"], "profiles": profile_ids, "routes": brand["routes"]}


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def local_ref(value) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and not value.startswith("//")
        and not any(char == "\\" or ord(char) <= 32 or ord(char) == 127 for char in value)
        and (value == "." or value.startswith(("/", "./", "../")))
    )


def route_link(routes: dict, route_id: str, copy: dict, current: str) -> str:
    href = routes[route_id]
    external = href.startswith("https://")
    attrs = ' target="_blank" rel="noopener noreferrer"' if external else ""
    active = ' aria-current="page"' if route_id == current else ""
    return f'<a href="{esc(href)}"{active}{attrs}>{esc(copy[route_id])}</a>'


def render_variant(spec: dict, routes_doc: dict, config: dict, locale: str, audience: str) -> dict:
    copy = spec["copy"][locale]
    routes = routes_doc["routes"]
    current = config["currentRoute"]
    if current not in routes: fail("SHELL_CURRENT_ROUTE_INVALID", current)
    variants = config["variantLinks"]
    if set(variants) != set(LOCALES): fail("SHELL_VARIANT_LOCALES_INVALID")
    for item_locale in LOCALES:
        if set(variants[item_locale]) != set(AUDIENCES): fail("SHELL_VARIANT_AUDIENCES_INVALID", item_locale)
    targets = [variants[item_locale][item_audience] for item_locale in LOCALES for item_audience in AUDIENCES]
    if len(set(targets)) != len(targets): fail("SHELL_VARIANT_TARGETS_DUPLICATED")
    navigation = "".join(route_link(routes, route_id, copy, current) for route_id in routes_doc["header"])
    cta = copy["ctaEmpresa"] if audience == "empresa" else copy["ctaPersona"]
    header = (
        f'<a class="mdg-skip" href="#main">{esc(copy["navLabel"])}</a>'
        f'<header class="mdg-header"><button class="mdg-menu" type="button" aria-expanded="false" '
        f'aria-controls="mdg-primary-nav" aria-label="{esc(copy["menu"])}">{esc(copy["menu"])}</button>'
        f'<a class="mdg-brand" href="{esc(routes["home"])}" aria-label="MetodologIA">'
        f'<img src="{esc(config["assetBase"])}/metodologia-logo.svg" width="36" height="36" alt="">'
        f'<span><strong>Metodolog<span>IA</span></strong><small>{esc(config["profile"])}</small></span></a>'
        f'<nav class="mdg-nav" id="mdg-primary-nav" aria-label="{esc(copy["navLabel"])}">{navigation}</nav>'
        f'<a class="mdg-header-cta" href="{esc(routes["contact"])}">{esc(cta)}</a></header>'
    )
    next_locale = LOCALES[(LOCALES.index(locale) + 1) % len(LOCALES)]
    next_audience = "empresa" if audience == "persona" else "persona"
    theme_label = f'{copy["theme"]}: {copy["light"]}. {copy["changeTo"]} {copy["dark"]}'
    locale_label = f'{copy["language"]}: {locale.upper()}. {copy["changeTo"]} {next_locale.upper()}'
    audience_label = f'{copy["audience"]}: {copy[audience]}. {copy["changeTo"]} {copy[next_audience]}'
    controls = (
        f'<div class="mdg-controls" role="group" aria-label="{esc(copy["controls"])}" data-locale="{locale}" data-audience="{audience}">'
        f'<button class="mdg-control" type="button" role="switch" aria-checked="false" aria-label="{esc(theme_label)}" data-mdg-theme>{ICON_MOON}</button>'
        f'<a class="mdg-control" href="{esc(variants[next_locale][audience])}" aria-label="{esc(locale_label)}" data-mdg-locale="{next_locale}">{ICON_GLOBE}</a>'
        f'<a class="mdg-control" href="{esc(variants[locale][next_audience])}" aria-label="{esc(audience_label)}" data-mdg-audience="{next_audience}">{ICON_BUILDING if audience == "empresa" else ICON_USER}</a>'
        '<span class="mdg-sr-only" aria-live="polite" data-mdg-status></span></div>'
    )
    footer_groups = "".join(
        f'<nav aria-label="{esc(copy[group])}"><h3>{esc(copy[group])}</h3>'
        + "".join(route_link(routes, route_id, copy, "") for route_id in route_ids)
        + "</nav>"
        for group, route_ids in routes_doc["footer"].items()
    )
    footer = (
        '<footer class="mdg-footer"><div class="mdg-footer-grid"><div><h2>Metodolog<span>IA</span></h2>'
        f'<p>{esc(copy["quote"])}</p></div>{footer_groups}</div><div class="mdg-footer-bottom">'
        '<span>© 2026 MetodologIA · Copyleft</span><span>RENDERED_DRAFT</span></div></footer>'
    )
    return {"locale": locale, "audience": audience, "header": header, "controls": controls, "footer": footer}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    release = args.release_root.resolve()
    brand = load_brand_config(release)
    config = load(args.config.resolve())
    if set(config) != {"currentRoute", "profile", "assetBase", "variantLinks"}: fail("SHELL_CONFIG_KEYS_INVALID")
    if config["profile"] not in brand["profiles"]: fail("SHELL_PROFILE_INVALID")
    if config["assetBase"] == "/" or not local_ref(config["assetBase"]): fail("SHELL_ASSET_BASE_INVALID")
    for locale, audiences in config["variantLinks"].items():
        if not isinstance(audiences, dict): fail("SHELL_VARIANT_AUDIENCES_INVALID", locale)
        for audience, href in audiences.items():
            if not local_ref(href): fail("SHELL_VARIANT_LINK_INVALID", f"{locale}:{audience}")
    output = {
        f"{locale}:{audience}": render_variant(brand, brand["routes"], config, locale, audience)
        for locale in LOCALES
        for audience in AUDIENCES
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"BRAND_SHELL_RENDER_PASS variants={len(output)}")


if __name__ == "__main__":
    main()
