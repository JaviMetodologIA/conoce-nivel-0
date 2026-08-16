(() => {
  "use strict";
  const ALLOWED_STORAGE = new Set(["mdg_theme", "mdg_locale", "mdg_audience"]);
  const PROFILES = new Set(["marketing","learning","thematic","campus","application"]);
  const COPY_KEYS = ["about","audience","campus","changeTo","companies","connect","contact","controls","ctaEmpresa","ctaPersona","dark","empresa","explore","home","language","learn","legal","light","menu","method","navLabel","people","persona","programs","quote","resources","services","theme"];
  const ICON_SUN = `<svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`;
  const ICON_MOON = `<svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;
  const ICON_GLOBE = `<svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>`;
  const ICON_USER = `<svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;
  const ICON_BUILDING = `<svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01M16 6h.01M12 6h.01M12 10h.01M12 14h.01M16 10h.01M16 14h.01M8 10h.01M8 14h.01"/></svg>`;
  const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
  const safeStore = (key, value) => { if (!ALLOWED_STORAGE.has(key)) throw new Error("MDG_STORAGE_KEY_FORBIDDEN"); try { localStorage.setItem(key, value); } catch {} };
  const safeRead = (key) => { if (!ALLOWED_STORAGE.has(key)) throw new Error("MDG_STORAGE_KEY_FORBIDDEN"); try { return typeof localStorage.getItem === "function" ? localStorage.getItem(key) : null; } catch { return null; } };
  const localRef = (value) => typeof value === "string" && /^(?:\/(?!\/)|\.\.?\/|\.$)/.test(value) && !/[\\\u0000-\u0020\u007f]/.test(value);
  const safeHref = (value) => localRef(value) || (typeof value === "string" && /^https:\/\/[^\s]+$/.test(value));
  const hrefWithFragment = (href) => `${href}${location.hash || ""}`;
  const link = (href, label, active, external = false) => `<a href="${escapeHtml(href)}"${active ? ' aria-current="page"' : ""}${external ? ' target="_blank" rel="noopener noreferrer"' : ""}>${escapeHtml(label)}</a>`;

  const storedTheme = safeRead("mdg_theme");
  if (["light","dark"].includes(storedTheme)) document.documentElement.dataset.theme = storedTheme;

  function validate(config) {
    for (const key of ["locale","audience","currentRoute","copy","routes","variantLinks","assetBase","header","footer","profile"]) if (!config[key]) throw new Error(`MDG_CONFIG_MISSING:${key}`);
    if (!["es","en","pt"].includes(config.locale)) throw new Error("MDG_LOCALE_INVALID");
    if (!["persona","empresa"].includes(config.audience)) throw new Error("MDG_AUDIENCE_INVALID");
    if (!PROFILES.has(config.profile)) throw new Error("MDG_PROFILE_INVALID");
    if (![undefined,"light","dark"].includes(document.documentElement.dataset.theme)) throw new Error("MDG_THEME_INVALID");
    if (config.assetBase === "/" || !localRef(config.assetBase)) throw new Error("MDG_ASSET_BASE_INVALID");
    if (!config.routes || Object.values(config.routes).some((href) => !safeHref(href))) throw new Error("MDG_ROUTE_INVALID");
    if (!config.routes[config.currentRoute]) throw new Error("MDG_CURRENT_ROUTE_INVALID");
    if (Object.keys(config.copy).sort().join("|") !== [...COPY_KEYS].sort().join("|") || COPY_KEYS.some((key) => typeof config.copy[key] !== "string" || !config.copy[key].trim())) throw new Error("MDG_COPY_INVALID");
    if (!Array.isArray(config.header) || config.header.some((id) => !config.routes[id])) throw new Error("MDG_HEADER_INVALID");
    if (!config.footer || Object.values(config.footer).some((ids) => !Array.isArray(ids) || ids.some((id) => !config.routes[id]))) throw new Error("MDG_FOOTER_INVALID");
    if (Object.keys(config.variantLinks).sort().join("|") !== "en|es|pt") throw new Error("MDG_VARIANT_LOCALES_INVALID");
    for (const locale of ["es","en","pt"]) {
      if (!config.variantLinks[locale]) throw new Error(`MDG_VARIANT_LOCALE_MISSING:${locale}`);
      if (Object.keys(config.variantLinks[locale]).sort().join("|") !== "empresa|persona") throw new Error(`MDG_VARIANT_AUDIENCES_INVALID:${locale}`);
      for (const audience of ["persona","empresa"]) {
        const href = config.variantLinks[locale][audience];
        if (!href) throw new Error(`MDG_VARIANT_AUDIENCE_MISSING:${locale}:${audience}`);
        if (!localRef(href)) throw new Error(`MDG_VARIANT_LINK_INVALID:${locale}:${audience}`);
      }
    }
    const targets = Object.values(config.variantLinks).flatMap((items) => Object.values(items));
    if (new Set(targets).size !== 6) throw new Error("MDG_VARIANT_TARGETS_DUPLICATED");
  }

  function renderHeader(config) {
    const t = config.copy;
    const nav = config.header.map((id) => link(config.routes[id], t[id], id === config.currentRoute, /^https:/.test(config.routes[id]))).join("");
    const cta = config.audience === "empresa" ? t.ctaEmpresa : t.ctaPersona;
    return `<a class="mdg-skip" href="#main">${escapeHtml(t.navLabel)}</a><header class="mdg-header"><button class="mdg-menu" type="button" aria-expanded="false" aria-controls="mdg-primary-nav" aria-label="${escapeHtml(t.menu)}">${escapeHtml(t.menu)}</button><a class="mdg-brand" href="${escapeHtml(config.routes.home)}" aria-label="MetodologIA"><img src="${escapeHtml(config.assetBase)}/metodologia-logo.svg" width="36" height="36" alt=""><span><strong>Metodolog<span>IA</span></strong><small>${escapeHtml(config.profile)}</small></span></a><nav class="mdg-nav" id="mdg-primary-nav" aria-label="${escapeHtml(t.navLabel)}">${nav}</nav><a class="mdg-header-cta" href="${escapeHtml(config.routes.contact)}">${escapeHtml(cta)}</a></header>`;
  }

  function renderControls(config) {
    const t = config.copy;
    const dark = document.documentElement.dataset.theme === "dark";
    const locales = ["es","en","pt"];
    const nextLocale = locales[(locales.indexOf(config.locale) + 1) % locales.length];
    const nextAudience = config.audience === "persona" ? "empresa" : "persona";
    const themeLabel = `${t.theme}: ${dark ? t.dark : t.light}. ${t.changeTo} ${dark ? t.light : t.dark}`;
    const localeLabel = `${t.language}: ${config.locale.toUpperCase()}. ${t.changeTo} ${nextLocale.toUpperCase()}`;
    const audienceLabel = `${t.audience}: ${t[config.audience]}. ${t.changeTo} ${t[nextAudience]}`;
    return `<div class="mdg-controls" role="group" aria-label="${escapeHtml(t.controls)}"><button class="mdg-control" type="button" role="switch" aria-checked="${dark}" aria-label="${escapeHtml(themeLabel)}" data-mdg-theme>${dark ? ICON_SUN : ICON_MOON}</button><a class="mdg-control" href="${escapeHtml(hrefWithFragment(config.variantLinks[nextLocale][config.audience]))}" aria-label="${escapeHtml(localeLabel)}" data-mdg-locale="${nextLocale}">${ICON_GLOBE}</a><a class="mdg-control" href="${escapeHtml(hrefWithFragment(config.variantLinks[config.locale][nextAudience]))}" aria-label="${escapeHtml(audienceLabel)}" data-mdg-audience="${nextAudience}">${config.audience === "empresa" ? ICON_BUILDING : ICON_USER}</a><span class="mdg-sr-only" aria-live="polite" data-mdg-status></span></div>`;
  }

  function renderFooter(config) {
    const t = config.copy;
    const groups = Object.entries(config.footer).map(([group, ids]) => `<nav aria-label="${escapeHtml(t[group])}"><h3>${escapeHtml(t[group])}</h3>${ids.map((id) => link(config.routes[id], t[id], false, /^https:/.test(config.routes[id]))).join("")}</nav>`).join("");
    return `<footer class="mdg-footer"><div class="mdg-footer-grid"><div><h2>Metodolog<span>IA</span></h2><p>${escapeHtml(t.quote)}</p></div>${groups}</div><div class="mdg-footer-bottom"><span>© 2026 MetodologIA · Copyleft</span><span>RENDERED_DRAFT</span></div></footer>`;
  }

  function mount(config) {
    validate(config);
    const storedLocale = safeRead("mdg_locale");
    const storedAudience = safeRead("mdg_audience");
    const locale = ["es","en","pt"].includes(storedLocale) ? storedLocale : config.locale;
    const audience = ["persona","empresa"].includes(storedAudience) ? storedAudience : config.audience;
    if (locale !== config.locale || audience !== config.audience) {
      const href = hrefWithFragment(config.variantLinks[locale][audience]);
      const target = location.href ? new URL(href, location.href) : null;
      if (target && location.origin && target.origin !== location.origin) throw new Error("MDG_PREFERENCE_TARGET_CROSS_ORIGIN");
      if (target && target.href === location.href) {
        safeStore("mdg_locale", config.locale);
        safeStore("mdg_audience", config.audience);
        throw new Error("MDG_PREFERENCE_TARGET_SELF");
      }
      location.replace(href);
      return;
    }
    document.documentElement.lang = config.locale;
    document.documentElement.dataset.audience = config.audience;
    const header = document.querySelector("[data-mdg-header]");
    const controls = document.querySelector("[data-mdg-controls]");
    const footer = document.querySelector("[data-mdg-footer]");
    if (!header || !controls || !footer) throw new Error("MDG_SHELL_MOUNT_MISSING");
    document.documentElement.classList.add("mdg-enhanced");
    header.innerHTML = renderHeader(config);
    controls.innerHTML = renderControls(config);
    footer.innerHTML = renderFooter(config);
    const menu = header.querySelector(".mdg-menu");
    const nav = header.querySelector(".mdg-nav");
    menu.addEventListener("click", () => { const open = menu.getAttribute("aria-expanded") !== "true"; menu.setAttribute("aria-expanded", String(open)); nav.dataset.open = String(open); });
    controls.querySelector("[data-mdg-theme]").addEventListener("click", (event) => { const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark"; document.documentElement.dataset.theme = next; event.currentTarget.setAttribute("aria-checked", String(next === "dark")); event.currentTarget.setAttribute("aria-label", `${config.copy.theme}: ${config.copy[next]}. ${config.copy.changeTo} ${config.copy[next === "dark" ? "light" : "dark"]}`); event.currentTarget.innerHTML = next === "dark" ? ICON_SUN : ICON_MOON; controls.querySelector("[data-mdg-status]").textContent = `${config.copy.theme}: ${config.copy[next]}`; safeStore("mdg_theme", next); });
    const preserveFragment = (item) => {
      const baseHref = item.getAttribute("href").split("#", 1)[0];
      item.setAttribute("href", hrefWithFragment(baseHref));
    };
    controls.querySelectorAll("[data-mdg-locale]").forEach((item) => item.addEventListener("click", () => {
      preserveFragment(item);
      safeStore("mdg_locale", item.dataset.mdgLocale);
    }));
    controls.querySelectorAll("[data-mdg-audience]").forEach((item) => item.addEventListener("click", () => {
      preserveFragment(item);
      safeStore("mdg_audience", item.dataset.mdgAudience);
    }));
  }
  window.MetodologiaBrand = Object.freeze({mount});
})();
