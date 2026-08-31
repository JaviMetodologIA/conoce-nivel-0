import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const dist = path.join(root, 'dist');
const specPath = path.join(root, 'src/conoce-chrome-spec-v1.json');
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));

function walk(dir) {
  return fs.readdirSync(dir, {withFileTypes: true}).flatMap((entry) => {
    const target = path.join(dir, entry.name);
    return entry.isDirectory() ? walk(target) : [target];
  });
}
function count(source, fragment) { return source.split(fragment).length - 1; }
function decodeAttribute(source) {
  return source
    .replaceAll('&quot;', '"')
    .replaceAll('&#x27;', "'")
    .replaceAll('&lt;', '<')
    .replaceAll('&gt;', '>')
    .replaceAll('&amp;', '&');
}
function sha(buffer) { return crypto.createHash('sha256').update(buffer).digest('hex'); }
function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(',')}]`;
  if (value && typeof value === 'object') return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stable(value[key])}`).join(',')}}`;
  return JSON.stringify(value);
}
function canonicalSelf(value, field) {
  const payload = Object.fromEntries(Object.entries(value).filter(([key]) => key !== field));
  return sha(Buffer.from(stable(payload) + '\n'));
}
function validateStructured(html) {
  const source = html.match(/<script type="application\/ld\+json" data-conoce-structured>([\s\S]*?)<\/script>/)?.[1];
  if (!source) throw new Error('Conoce structured data missing');
  const document = JSON.parse(source);
  const graph = document['@graph'];
  if (document['@context'] !== 'https://schema.org' || !Array.isArray(graph) || graph.length !== 3) throw new Error('Conoce structured data shape drift');
  const website = graph.find((item) => item['@type'] === 'WebSite');
  const page = graph.find((item) => item['@type'] === 'CollectionPage');
  const breadcrumb = graph.find((item) => item['@type'] === 'BreadcrumbList');
  for (const item of [website, page]) {
    if (!item || item.name !== 'Conoce · Nivel 0' || item.publisher?.name !== 'MetodologIA' || item.isPartOf?.url !== 'https://metodologia.info/') throw new Error('Conoce structured data authority drift');
  }
  if (!website.url.startsWith(spec.canonical_origin) || !page.url.startsWith(spec.canonical_origin)) throw new Error('Conoce structured data origin drift');
  if (!breadcrumb || !Array.isArray(breadcrumb.itemListElement) || !breadcrumb.itemListElement.length || breadcrumb.itemListElement.some((item, index) => item['@type'] !== 'ListItem' || item.position !== index + 1 || !item.name || !item.item?.startsWith(spec.canonical_origin))) throw new Error('Conoce breadcrumb structured data drift');
  return document;
}
function validateChromeAuthority(html) {
  for (const marker of ['data-conoce-header', 'data-conoce-footer', 'data-conoce-preferences']) {
    if (count(html, marker) !== 1) throw new Error(`${marker} count drift`);
  }
  if (count(html, 'data-conoce-home-link') !== 1 || count(html, 'data-conoce-editorial-link') !== 3 || count(html, 'data-conoce-resource-overview') !== 1 || count(html, 'data-conoce-module-link') !== 4 || count(html, 'data-conoce-resource-link') !== 0) throw new Error('Chrome route count drift');
  if (count(html, 'data-conoce-breadcrumbs') !== 1 || count(html, 'data-intrapage-nav') !== 1) throw new Error('Chrome singleton experience drift');
  const nav = html.match(/<nav class="mdg-nav conoce-nav"[\s\S]*?<\/nav>/)?.[0] ?? '';
  const fragmentLinks = [...nav.matchAll(/<a\b[^>]*href="[^"]*#([^"]+)"[^>]*>/g)];
  const fragmentIds = fragmentLinks.map((match) => match[1]).sort();
  if (fragmentLinks.some((match) => !match[0].includes('data-conoce-module-link')) || JSON.stringify(fragmentIds) !== JSON.stringify(['module-01', 'module-02', 'module-03', 'module-04'])) throw new Error('Global navigation fragment drift');
  if (count(nav, 'aria-current="page"') !== 1) throw new Error('Global navigation current drift');
  if (['data-mdg-header', 'data-mdg-controls', 'data-mdg-footer'].some((slot) => html.includes(slot))) throw new Error('Corporate shell slot present');
  if (html.includes('brand-shell.js') || html.includes('MetodologiaBrand.mount')) throw new Error('Corporate mount present');
  const parent = html.match(/<a class="mdg-header-cta conoce-parent-cta"([^>]*)>/)?.[1] ?? '';
  if (!parent.includes('href="https://metodologia.info/"') || !parent.includes('data-conoce-parent') || /target=/.test(parent)) throw new Error('Parent contract drift');
}
function validateStorage(source) {
  const keys = [...source.matchAll(/(?:getItem|setItem|readPreference|writePreference)\(['"](mdg_[a-z]+)['"]/g)].map((match) => match[1]);
  if ([...new Set(keys)].sort().join('|') !== [...spec.allowed_storage_keys].sort().join('|')) throw new Error(`Storage key contract drift: ${keys}`);
}

if (spec.self_sha256 !== canonicalSelf(spec, 'self_sha256')) throw new Error('Chrome spec self hash drift');
const pages = walk(dist).filter((file) => file.endsWith('.html'));
if (pages.length !== 126) throw new Error(`Expected 126 pages, found ${pages.length}`);

const DEFAULT_MODULE_ID = 'ia-panorama';
const MODULE_IDS = new Set(['ia-panorama', 'ocupado-productivo', 'trabajo-amplificado', 'trabajo-agentico']);
const RESOURCE_PAGES = new Set(spec.resources.map((item) => item.page));
const GLOBAL_EDITORIAL_PAGES = new Set(['landing', 'level0', 'how', 'resources_index', 'intakes']);
const records = new Map();
for (const file of pages) {
  const html = fs.readFileSync(file, 'utf8');
  const page = html.match(/<body data-page="([^"]+)"/)?.[1];
  const moduleId = html.match(/<body[^>]+data-module-id="([^"]+)"/)?.[1];
  const locale = html.match(/<html lang="([^"]+)"/)?.[1];
  const audience = html.match(/<html[^>]+data-audience="([^"]+)"/)?.[1];
  records.set(path.resolve(file), {file, html, page, moduleId, locale, audience});
}

let globalEditorialCount = 0;
let resourceCount = 0;
let nestedCount = 0;
let toggleCount = 0;
for (const record of records.values()) {
  const {file, html, page, moduleId, locale, audience} = record;
  validateChromeAuthority(html);
  if (!spec.pages.includes(page)) throw new Error(`Unknown page type: ${file}`);
  if (!MODULE_IDS.has(moduleId)) throw new Error(`Unknown module: ${file}:${moduleId}`);
  if (GLOBAL_EDITORIAL_PAGES.has(page) && moduleId === DEFAULT_MODULE_ID) globalEditorialCount += 1;
  else if (RESOURCE_PAGES.has(page)) {
    resourceCount += 1;
    nestedCount += moduleId === DEFAULT_MODULE_ID ? 0 : 1;
  } else throw new Error(`Route/module classification drift: ${file}`);
  if (!html.includes('<strong>Conoce</strong><small>Nivel 0 ')) throw new Error(`Identity translation drift: ${file}`);
  const canonical = html.match(/<link rel="canonical" href="([^"]+)">/)?.[1] ?? '';
  if (!canonical.startsWith(spec.canonical_origin)) throw new Error(`Canonical origin drift: ${file}`);
  const title = html.match(/<title>([^<]+)<\/title>/)?.[1] ?? '';
  const ogTitle = html.match(/<meta property="og:title" content="([^"]+)">/)?.[1] ?? '';
  if (!title.includes('Conoce · Nivel 0 · MetodologIA') || title !== ogTitle) throw new Error(`Title authority drift: ${file}`);
  validateStructured(html);
  // [EVIDENCE:MODULE_ACTIVE_STATE] Exactly one module is active on each of 96 resource routes.
  const moduleLinks = [...html.matchAll(/<a\b[^>]*data-conoce-module-link[^>]*>/g)].map((match) => match[0]);
  const activeModules = moduleLinks.filter((tag) => tag.includes('aria-current="page"'));
  if (RESOURCE_PAGES.has(page)) {
    if (activeModules.length !== 1 || !activeModules[0].includes(`data-module-id="${moduleId}"`)) throw new Error(`Module active state drift: ${file}`);
  } else if (activeModules.length !== 0) throw new Error(`Module active state drift: ${file}`);

  // [EVIDENCE:TOGGLE_MODULE_PRESERVATION] Locale/audience changes never fall back to M1.
  const matrixSource = html.match(/data-variant-links="([^"]+)"/)?.[1];
  if (!matrixSource) throw new Error(`Variant matrix missing: ${file}`);
  const matrix = JSON.parse(decodeAttribute(matrixSource));
  if (JSON.stringify(Object.keys(matrix).sort()) !== JSON.stringify(['en', 'es', 'pt'])) throw new Error(`Variant locales drift: ${file}`);
  for (const targetLocale of ['es', 'en', 'pt']) {
    if (JSON.stringify(Object.keys(matrix[targetLocale] ?? {}).sort()) !== JSON.stringify(['empresa', 'persona'])) throw new Error(`Variant audiences drift: ${file}`);
    for (const targetAudience of ['persona', 'empresa']) {
      const href = matrix[targetLocale][targetAudience];
      const localHref = href.split('#', 1)[0].split('?', 1)[0];
      const target = records.get(path.resolve(path.dirname(file), localHref));
      if (!target || target.page !== page || target.moduleId !== moduleId || target.locale !== targetLocale || target.audience !== targetAudience) {
        throw new Error(`Variant module route drift: ${file}:${targetLocale}:${targetAudience}:${href}`);
      }
      toggleCount += 1;
    }
  }
  const footer = html.match(/<footer class="mdg-footer conoce-footer"[\s\S]*?<\/footer>/)?.[0] ?? '';
  if (count(footer, '<nav ') !== 3) throw new Error(`Footer group drift: ${file}`);
  for (const href of ['https://metodologia.info/', 'https://metodologia.info/metodo/', 'https://campus.metodologia.info/', 'https://metodologia.info/contacto/', 'https://metodologia.info/legal/']) {
    if (!footer.includes(`href="${href}"`)) throw new Error(`Footer parent route missing ${href}: ${file}`);
  }
}
if (globalEditorialCount !== 30 || resourceCount !== 96 || nestedCount !== 72 || toggleCount !== 756) throw new Error(`Chrome matrix drift: ${JSON.stringify({globalEditorialCount, resourceCount, nestedCount, toggleCount})}`);

const sample = fs.readFileSync(pages[0], 'utf8');
for (const mutation of [
  sample.replace('"name":"Conoce · Nivel 0"', '"name":"Other"'),
  sample.replace('"url":"https://metodologia.info/"', '"url":"https://example.com/"'),
  sample.replace('"url":"https://conoce.metodologia.info/', '"url":"https://example.com/'),
]) {
  let rejected = false;
  try { validateStructured(mutation); } catch { rejected = true; }
  if (!rejected) throw new Error('Structured data mutation passed');
}
for (const mutation of [
  sample.replace('</head>', '<script src="brand-shell.js"></script></head>'),
  sample.replace('class="mdg-shell conoce-shell"', 'class="mdg-shell conoce-shell" data-mdg-header'),
  sample.replace('class="mdg-shell conoce-preferences-shell"', 'class="mdg-shell conoce-preferences-shell" data-mdg-controls'),
  sample.replace('<footer class="mdg-footer conoce-footer"', '<div data-mdg-footer><footer class="mdg-footer conoce-footer"'),
  sample.replace(' data-conoce-parent', ''),
  sample.replace('href="https://metodologia.info/" data-conoce-parent', 'href="https://example.com/" data-conoce-parent'),
  sample.replace(' data-conoce-module-link', ''),
  sample.replace(' data-conoce-home-link', ''),
]) {
  let rejected = false;
  try { validateChromeAuthority(mutation); } catch { rejected = true; }
  if (!rejected) throw new Error('Chrome authority mutation passed');
}

if (fs.existsSync(path.join(dist, 'assets/brand/runtime/brand-shell.js'))) throw new Error('Corporate runtime copied to dist');
const siteJs = fs.readFileSync(path.join(root, 'src/site.js'), 'utf8');
validateStorage(siteJs);
let storageRejected = false;
try { validateStorage(`${siteJs}\nlocalStorage.setItem('mdg_tracking','1');`); } catch { storageRejected = true; }
if (!storageRejected) throw new Error('Storage mutation passed');

const manifest = JSON.parse(fs.readFileSync(path.join(dist, 'build-manifest.json'), 'utf8'));
const receiptBytes = fs.readFileSync(path.join(dist, 'build-receipt.json'));
const receipt = JSON.parse(receiptBytes);
if (manifest.self_sha256 !== canonicalSelf(manifest, 'self_sha256')) throw new Error('Manifest self drift');
if (receipt.self_sha256 !== canonicalSelf(receipt, 'self_sha256').replace(/^$/, '')) {
  // Receipt v1 canonical form omits the trailing newline.
  const payload = Object.fromEntries(Object.entries(receipt).filter(([key]) => key !== 'self_sha256'));
  if (receipt.self_sha256 !== sha(Buffer.from(stable(payload)))) throw new Error('Receipt self drift');
}
if (receipt.manifest_sha256 !== sha(fs.readFileSync(path.join(dist, 'build-manifest.json')))) throw new Error('Receipt manifest binding drift');
if (manifest.conoce_chrome.source_sha256 !== sha(fs.readFileSync(specPath)) || receipt.conoce_chrome.source_sha256 !== manifest.conoce_chrome.source_sha256) throw new Error('Chrome source binding drift');
if (manifest.conoce_chrome.rendered_pages !== 126 || manifest.variants?.canonical_pages !== 126 || manifest.digital_brand.runtime_mount !== false || manifest.state !== 'RENDERED_DRAFT' || receipt.state !== 'RENDERED_DRAFT' || manifest.publication_authorized !== false || receipt.publication_authorized !== false) throw new Error('Governance state drift');

console.log('[EVIDENCE:CONOCE_CHROME] CONOCE_CHROME_OK 126/126 global_editorial=30 resources=96 nested=72 toggles=756 shell=singleton module_fragments=4 state=RENDERED_DRAFT publication=false');
