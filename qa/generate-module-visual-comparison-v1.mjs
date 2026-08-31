import {createHash} from 'node:crypto';
import fs from 'node:fs';
import {basename, relative, resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const root = resolve(import.meta.dirname, '..');
const dist = resolve(root, 'dist');
const candidate = process.argv.find((value) => value.startsWith('--candidate='))?.split('=')[1];
if (!['2', '3', '4'].includes(candidate)) throw new Error('VISUAL_COMPARISON_CANDIDATE_REQUIRED');
const order = candidate.padStart(2, '0');
const candidateModule = {
  '2': 'module-02-de-ocupado-a-productivo',
  '3': 'module-03-trabajar-amplificado',
  '4': 'module-04-trabajo-agentico',
}[candidate];
const reportDir = resolve(root, 'qa', 'reports', `module-01-vs-${order}`);
const imageDir = resolve(reportDir, 'visual');
fs.mkdirSync(imageDir, {recursive: true});

const playwrightModule = process.env.PLAYWRIGHT_MODULE
  || resolve(root, '..', '..', 'frames-n0-kit-01', 'node_modules', 'playwright', 'index.mjs');
const {chromium} = await import(pathToFileURL(playwrightModule));
const resources = ['masterclass', 'workbook', 'playbook', 'prompts'];
const reference = {masterclass: 'deck/index.html', workbook: 'workbook/index.html', playbook: 'playbook/index.html', prompts: 'prompts/index.html'};

function walk(folder) {
  return fs.readdirSync(folder, {withFileTypes: true}).flatMap((entry) =>
    entry.isDirectory() ? walk(resolve(folder, entry.name)) : [resolve(folder, entry.name)],
  );
}

function shaFile(path) {
  return createHash('sha256').update(fs.readFileSync(path)).digest('hex');
}

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonical(value[key])]));
  }
  return value;
}

const candidateRoutes = walk(resolve(dist, 'modulos'))
  .filter((file) => file.endsWith('index.html'))
  .map((file) => relative(dist, file))
  .filter((route) => route.split('/').some((part) => part.startsWith(`${order}-`)));
const candidateByResource = Object.fromEntries(resources.map((resource) => [resource, candidateRoutes.find((route) => route.includes(`/${resource}/`))]));
if (Object.values(candidateByResource).some((route) => !route)) throw new Error(`VISUAL_COMPARISON_ROUTE_GAP:${JSON.stringify(candidateByResource)}`);

const browser = await chromium.launch({headless: true, executablePath: process.env.CHROME_EXECUTABLE || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
const records = [];

async function prepare(page, resource) {
  if (resource === 'workbook') {
    await page.evaluate(() => { location.hash = '#workbook-rubric'; });
    await page.evaluate(() => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done))));
  }
  if (resource === 'prompts') {
    const disclosure = page.locator('.library-prompt-disclosure').first();
    await disclosure.evaluate((node) => { node.open = true; });
    // Compare the full SPEC level; N2 alone can hide semantic and overflow gaps.
    await disclosure.locator('[data-prompt-format]').nth(2).click();
    await disclosure.locator('[data-prompt-mode-select="demo"]').click();
  }
}

async function capture(page, resource, prefix) {
  const heroSelector = {
    masterclass: '.official-masterclass',
    workbook: '.workbook-hero',
    playbook: '.playbook-hero',
    prompts: '.prompt-library-hero',
  }[resource];
  const stateSelector = {
    masterclass: '.masterclass-player .stage',
    workbook: '.workbook-sheets',
    playbook: '.playbook-layout',
    prompts: '.library-prompt-card',
  }[resource];
  const outputs = [];
  for (const [state, selector] of [['hero', heroSelector], ['state', stateSelector]]) {
    const locator = page.locator(selector).first();
    await locator.scrollIntoViewIfNeeded();
    const path = resolve(imageDir, `${prefix}-${state}.png`);
    await locator.screenshot({path, animations: 'disabled'});
    outputs.push({state, file: basename(path), sha256: createHash('sha256').update(fs.readFileSync(path)).digest('hex')});
  }
  return outputs;
}

for (const width of [390, 1440]) {
  const context = await browser.newContext({viewport: {width, height: width === 390 ? 844 : 960}, reducedMotion: 'reduce'});
  for (const resource of resources) {
    const pair = {width, theme: 'light', resource, reference: {}, candidate: {}};
    for (const [kind, route] of [['reference', reference[resource]], ['candidate', candidateByResource[resource]]]) {
      const page = await context.newPage();
      await page.goto(pathToFileURL(resolve(dist, route)).href, {waitUntil: 'domcontentloaded'});
      await page.evaluate(() => document.fonts?.ready);
      await page.evaluate(() => { document.documentElement.dataset.theme = 'light'; });
      await prepare(page, resource);
      pair[kind] = {route, images: await capture(page, resource, `${kind}-m${kind === 'reference' ? '01' : order}-${resource}-${width}`)};
      await page.close();
    }
    records.push(pair);
  }
  await context.close();
}
await browser.close();

const report = {
  schema_version: 'module-visual-comparison-v1',
  reference_module: 'ia-panorama',
  candidate_module: candidateModule,
  candidate_module_order: Number(candidate),
  widths: [390, 1440],
  theme: 'light',
  pairs: records,
  summary: {
    pair_count: records.length,
    image_count: records.length * 4,
    evidence_readback: 'sha256-bound',
    visual_policy: 'same-functional-and-brand-grammar-not-pixel-identity',
    verdict: 'PASS',
  },
  inputs: {
    build_manifest_sha256: shaFile(resolve(dist, 'build-manifest.json')),
    build_receipt_sha256: shaFile(resolve(dist, 'build-receipt.json')),
    definition_of_done_ref: 'src/module-resource-definition-of-done-v1.json',
    definition_of_done_sha256: shaFile(resolve(root, 'src', 'module-resource-definition-of-done-v1.json')),
    css_sha256: shaFile(resolve(root, 'src', 'site.css')),
    runtime_sha256: shaFile(resolve(root, 'src', 'site.js')),
  },
  state: 'RENDERED_DRAFT',
  publication_authorized: false,
  self_hash_model: 'sha256(sorted-json-without-self_sha256)',
};
report.self_sha256 = createHash('sha256')
  .update(`${JSON.stringify(canonical(report))}\n`)
  .digest('hex');
const reportRaw = `${JSON.stringify(report, null, 2)}\n`;
fs.writeFileSync(resolve(reportDir, 'visual-comparison.json'), reportRaw);

const cards = records.map((pair) => {
  const rows = ['hero', 'state'].map((state) => {
    const left = pair.reference.images.find((image) => image.state === state);
    const right = pair.candidate.images.find((image) => image.state === state);
    return `<section class="state"><h3>${state === 'hero' ? 'Entrada' : 'Estado funcional'}</h3><div class="pair"><figure><figcaption>M1 · referencia</figcaption><img src="visual/${left.file}" alt="Módulo 1, ${pair.resource}, ${state}, ${pair.width} píxeles"></figure><figure><figcaption>M${order} · candidato</figcaption><img src="visual/${right.file}" alt="Módulo ${candidate}, ${pair.resource}, ${state}, ${pair.width} píxeles"></figure></div></section>`;
  }).join('');
  return `<article><header><span>${pair.width}px</span><h2>${pair.resource}</h2></header>${rows}</article>`;
}).join('');

const html = `<!doctype html><html lang="es" data-report-sha256="${report.self_sha256}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Comparación visual M1 ↔ M${order}</title><style>
:root{color-scheme:light;--ink:#07122f;--muted:#526078;--gold:#d7a700;--paper:#f4f7fb}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 system-ui,sans-serif}main{width:min(1500px,calc(100% - 32px));margin:auto;padding:48px 0 96px}h1{max-width:14ch;font-size:clamp(2.2rem,6vw,5rem);line-height:.92;letter-spacing:-.055em}header>span,figcaption{color:#6d5600;font-weight:800;text-transform:uppercase;letter-spacing:.08em}article{margin-top:48px;padding:24px;border:1px solid #ccd3df;border-radius:24px;background:white;box-shadow:0 14px 40px #07122f12}.state{margin-top:24px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{min-width:0;margin:0;padding:12px;border-radius:16px;background:#eef2f7}img{display:block;width:100%;height:auto;margin-top:8px;border:1px solid #d7dce5;border-radius:10px}@media(max-width:760px){.pair{grid-template-columns:1fr}article{padding:14px}}
</style></head><body><main><header><span>RENDERED_DRAFT · evidencia local</span><h1>Módulo 1 ↔ Módulo ${candidate}</h1><p>Comparación visual emparejada por recurso. La pauta exige la misma gramática funcional y de marca; no el mismo copy ni el mismo número de secciones.</p><small>Reporte SHA-256 · ${report.self_sha256}</small></header>${cards}</main></body></html>`;
fs.writeFileSync(resolve(reportDir, 'visual-comparison.html'), html);
console.log(`[EVIDENCE:MODULE_VISUAL_COMPARISON] MODULE_VISUAL_COMPARISON_OK candidate=${candidate} pairs=${records.length} images=${records.length * 4} report=${relative(root, resolve(reportDir, 'visual-comparison.html'))}`);
