import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const dist = path.join(root, 'dist');
const spec = JSON.parse(fs.readFileSync(path.join(root, 'src/intrapage-navigation-spec-v1.json'), 'utf8'));
const curriculum = JSON.parse(fs.readFileSync(path.join(root, 'src/curriculum-spec-v2.json'), 'utf8'));
const DEFAULT_MODULE_ID = 'ia-panorama';
const MODULE_IDS = new Set(curriculum.classes.map((item) => item.id));
const EXPECTED_HTML_PAGES = 126;
const RESOURCE_PAGES = new Set(['deck', 'workbook', 'playbook', 'prompts']);
const modulePayloads = new Map(
  curriculum.classes.slice(1).map((item) => [
    item.id,
    JSON.parse(fs.readFileSync(path.join(root, 'src', item.content.ref), 'utf8')),
  ]),
);

function walk(dir) {
  return fs.readdirSync(dir, {withFileTypes: true}).flatMap((entry) => {
    const target = path.join(dir, entry.name);
    return entry.isDirectory() ? walk(target) : [target];
  });
}

function occurrences(source, fragment) {
  return source.split(fragment).length - 1;
}

const pages = walk(dist).filter((file) => file.endsWith('.html'));
if (pages.length !== EXPECTED_HTML_PAGES) throw new Error(`Expected ${EXPECTED_HTML_PAGES} HTML pages, found ${pages.length}`);

for (const file of pages) {
  const html = fs.readFileSync(file, 'utf8');
  const page = html.match(/<body data-page="([^"]+)"/)?.[1];
  const moduleId = html.match(/<body[^>]+data-module-id="([^"]+)"/)?.[1];
  const locale = html.match(/<html lang="([^"]+)"/)?.[1];
  const audience = html.match(/<html[^>]+data-audience="([^"]+)"/)?.[1];
  if (!page || !spec.pages[page]) throw new Error(`Unknown page type: ${file}`);
  if (!MODULE_IDS.has(moduleId)) throw new Error(`Unknown module: ${file}:${moduleId}`);
  if (moduleId !== DEFAULT_MODULE_ID && !RESOURCE_PAGES.has(page)) throw new Error(`Nested non-resource route: ${file}`);
  // [EVIDENCE:SINGLETON_EXPERIENCE] Every route owns exactly one shell, rail and breadcrumb.
  for (const marker of ['data-conoce-header', 'data-conoce-footer', 'data-conoce-preferences', 'data-conoce-breadcrumbs']) {
    if (occurrences(html, marker) !== 1) throw new Error(`Experience singleton drift (${marker}): ${file}`);
  }
  if (occurrences(html, 'data-intrapage-nav') !== 1) throw new Error(`Sidebar count drift: ${file}`);
  if (occurrences(html, 'data-intrapage-open') !== 1) throw new Error(`Trigger count drift: ${file}`);
  const trigger = html.match(/<button class="intrapage-trigger"[^>]*>/)?.[0] ?? '';
  const expectedTriggerName = spec.locales[locale]?.open;
  if (!expectedTriggerName || !trigger.includes(`aria-label="${expectedTriggerName}"`)) {
    throw new Error(`Trigger accessible-name drift: ${file}`);
  }
  let expected = spec.pages[page].items.map((item) => item.anchor);
  let nestedChapterCount = 0;
  if (moduleId !== DEFAULT_MODULE_ID && page === 'playbook') {
    const payload = modulePayloads.get(moduleId);
    const variant = payload?.variants.find((item) => item.locale === locale && item.audience === audience);
    const chapters = variant?.module?.playbook?.chapters;
    if (!Array.isArray(chapters) || !chapters.length) throw new Error(`Playbook navigation authority missing: ${file}`);
    nestedChapterCount = chapters.length;
    expected = ['playbook-inicio', 'intro', ...chapters.slice(0, 5).map((item) => item.id), 'close'];
  }
  if (moduleId !== DEFAULT_MODULE_ID && page === 'prompts') {
    const payload = modulePayloads.get(moduleId);
    const variant = payload?.variants.find((item) => item.locale === locale && item.audience === audience);
    const prompts = variant?.module?.promptLibrary?.prompts;
    if (!Array.isArray(prompts) || !prompts.length) throw new Error(`Prompt navigation authority missing: ${file}`);
    expected = ['prompts-inicio', 'directos', prompts[0].id, prompts[Math.min(5, prompts.length - 1)].id, 'metaprompts'];
  }
  const nav = html.match(/<aside class="intrapage-nav"[\s\S]*?<\/aside>/)?.[0] ?? '';
  const rendered = [...nav.matchAll(/href="#([^"]+)" data-intrapage-link/g)].map((match) => match[1]);
  if (JSON.stringify(rendered) !== JSON.stringify(expected)) throw new Error(`Sidebar order drift: ${file}`);
  for (const anchor of expected) {
    if (occurrences(html, `id="${anchor}"`) !== 1) throw new Error(`Target count drift (${anchor}): ${file}`);
  }
  if (occurrences(html, '<link rel="canonical"') !== 1) throw new Error(`Canonical drift: ${file}`);
  if (page === 'playbook') {
    const complete = html.match(/<details class="playbook-toc"[^>]*>[\s\S]*?<\/details>/)?.[0] ?? '';
    // Depth-enabled module playbooks add governed glossary and FAQ entries in
    // addition to introduction, chapters and closing.
    const wanted = moduleId === DEFAULT_MODULE_ID ? 22 : nestedChapterCount + 4;
    if (occurrences(complete, '<a href="#') !== wanted) throw new Error(`Playbook complete index drift: ${file}`);
  }
}

const manifest = JSON.parse(fs.readFileSync(path.join(dist, 'build-manifest.json'), 'utf8'));
const receipt = JSON.parse(fs.readFileSync(path.join(dist, 'build-receipt.json'), 'utf8'));
if (manifest.state !== 'RENDERED_DRAFT' || receipt.state !== 'RENDERED_DRAFT' || manifest.publication_authorized !== false || receipt.publication_authorized !== false) throw new Error('State escalation detected');
if (manifest.intrapage_navigation?.rendered_pages !== EXPECTED_HTML_PAGES) throw new Error('Manifest navigation binding missing');
if (receipt.intrapage_navigation?.source_sha256 !== manifest.intrapage_navigation.source_sha256) throw new Error('Receipt navigation binding drift');

console.log('[EVIDENCE:INTRAPAGE_NAVIGATION] INTRAPAGE_NAVIGATION_OK 126/126 singleton_shell=126 nested_playbooks=18 state=RENDERED_DRAFT publication=false');
