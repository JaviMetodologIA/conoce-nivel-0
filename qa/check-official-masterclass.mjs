#!/usr/bin/env node
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const spec = JSON.parse(fs.readFileSync(path.join(root, 'src/public-resource-spec-v1.json'), 'utf8'));
const nav = JSON.parse(fs.readFileSync(path.join(root, 'src/intrapage-navigation-spec-v1.json'), 'utf8'));
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'dist/build-manifest.json'), 'utf8'));
const receipt = JSON.parse(fs.readFileSync(path.join(root, 'dist/build-receipt.json'), 'utf8'));
const pdfPath = path.join(root, 'dist', spec.deck.source_asset);
const sha256 = (value) => crypto.createHash('sha256').update(value).digest('hex');
const occurrences = (text, fragment) => text.split(fragment).length - 1;

function assertPage(html, file, locale) {
  const pdfRef = html.match(/<object class="official-pdf-object" data="([^"#]+)#page=1&amp;view=FitH"/)?.[1];
  if (occurrences(html, 'data-official-masterclass ') !== 1) throw new Error(`OFFICIAL_PDF_SURFACE_DRIFT:${file}`);
  if (occurrences(html, '<object class="official-pdf-object"') !== 1) throw new Error(`OFFICIAL_PDF_OBJECT_DRIFT:${file}`);
  if (!pdfRef || /^(?:https?:|\/\/|data:|javascript:)/i.test(pdfRef)) throw new Error(`OFFICIAL_PDF_REFERENCE_UNSAFE:${file}`);
  if (path.resolve(path.dirname(file), pdfRef) !== pdfPath) throw new Error(`OFFICIAL_PDF_REFERENCE_DRIFT:${file}`);
  if (!html.includes(`data-official-masterclass-sha256="${spec.deck.sha256}"`)) throw new Error(`OFFICIAL_PDF_HASH_BINDING_DRIFT:${file}`);
  if (occurrences(html, `href="${pdfRef}"`) < 3) throw new Error(`OFFICIAL_PDF_FALLBACK_DRIFT:${file}`);
  if (occurrences(html, '<section class="slide') !== 18) throw new Error(`MASTERCLASS_GUIDE_COUNT_DRIFT:${file}`);
  if (!html.includes(spec.deck.locales[locale].language_note)) throw new Error(`OFFICIAL_PDF_LANGUAGE_NOTE_DRIFT:${file}`);
  for (const item of nav.pages.deck.items) if (!html.includes(`id="${item.anchor}"`) || !html.includes(`href="#${item.anchor}"`)) throw new Error(`OFFICIAL_PDF_NAV_DRIFT:${file}:${item.anchor}`);
}

if (spec.deck.media_type !== 'application/pdf' || spec.deck.document_language !== 'es' || spec.deck.page_count !== 18) throw new Error('OFFICIAL_PDF_CONTRACT_DRIFT');
if (sha256(fs.readFileSync(pdfPath)) !== spec.deck.sha256) throw new Error('OFFICIAL_PDF_BYTES_DRIFT');
const info = execFileSync('pdfinfo', [pdfPath], { encoding: 'utf8' });
if (!/^Pages:\s+18$/m.test(info) || !/^JavaScript:\s+no$/m.test(info)) throw new Error('OFFICIAL_PDF_INFO_DRIFT');
const routes = [];
for (const audience of ['persona', 'empresa']) for (const locale of ['es', 'en', 'pt']) {
  const parts = [...(locale === 'es' ? [] : [locale]), ...(audience === 'persona' ? [] : ['empresa']), 'deck', 'index.html'];
  const file = path.join(root, 'dist', ...parts);
  assertPage(fs.readFileSync(file, 'utf8'), file, locale);
  routes.push(file);
}
if (manifest.official_masterclass?.sha256 !== spec.deck.sha256 || manifest.official_masterclass?.rendered_variants !== 6 || manifest.official_masterclass?.primary_surface !== true) throw new Error('OFFICIAL_PDF_MANIFEST_DRIFT');
if (receipt.official_masterclass?.sha256 !== spec.deck.sha256 || receipt.official_masterclass?.publication_authorized !== false) throw new Error('OFFICIAL_PDF_RECEIPT_DRIFT');
if (manifest.outputs?.[spec.deck.source_asset] !== spec.deck.sha256) throw new Error('OFFICIAL_PDF_OUTPUT_DRIFT');

const sample = fs.readFileSync(routes[0], 'utf8');
for (const [name, mutated] of [
  ['missing-object', sample.replace('<object class="official-pdf-object"', '<div class="official-pdf-object"')],
  ['remote-object', sample.replace(/data="[^"#]+#page=1&amp;view=FitH"/, 'data="https://example.com/masterclass.pdf#page=1&amp;view=FitH"')],
  ['wrong-hash', sample.replace(spec.deck.sha256, '0'.repeat(64))],
  ['missing-language-note', sample.replaceAll(spec.deck.locales.es.language_note, '')],
]) {
  let rejected = false;
  try { assertPage(mutated, routes[0], 'es'); } catch { rejected = true; }
  if (!rejected) throw new Error(`OFFICIAL_PDF_MUTATION_FALSE_GREEN:${name}`);
}

console.log(`OFFICIAL_MASTERCLASS_OK routes=${routes.length} pages=${spec.deck.page_count} mutations=4 sha256=${spec.deck.sha256}`);
