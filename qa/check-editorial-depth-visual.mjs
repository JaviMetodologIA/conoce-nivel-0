import fs from 'node:fs';
import {resolve, relative} from 'node:path';
import {pathToFileURL} from 'node:url';

const root = resolve(import.meta.dirname, '..');
const dist = resolve(root, 'dist');
const playwrightModule = process.env.PLAYWRIGHT_MODULE || resolve(root, '..', '..', 'frames-n0-kit-01', 'node_modules', 'playwright', 'index.mjs');
const axePath = process.env.AXE_PATH || '/Users/deonto/Library/pnpm/store/v11/links/@/axe-core/4.12.1/b7c50e7913b3703b5001a11d2efeed145f43557f7e102bc3785e95708dc85687/node_modules/axe-core/axe.min.js';
const {chromium} = await import(pathToFileURL(playwrightModule));

function walk(folder) {
  return fs.readdirSync(folder, {withFileTypes: true}).flatMap((entry) =>
    entry.isDirectory() ? walk(resolve(folder, entry.name)) : [resolve(folder, entry.name)],
  );
}

const nestedRoutes = walk(dist)
  .filter((file) => file.endsWith('index.html'))
  .map((file) => relative(dist, file))
  .filter((route) => route.includes('/modulos/') || route.includes('/modules/') || route.startsWith('modulos/'));
if (nestedRoutes.length !== 72) throw new Error(`EDITORIAL_DEPTH_VISUAL_ROUTE_COUNT:${nestedRoutes.length}`);
const visibleBaseline = JSON.parse(fs.readFileSync(resolve(root, 'qa/goldens/module-depth-visible-word-baseline-v1.json'), 'utf8'));
if (visibleBaseline.schema_version !== 'module-depth-visible-word-baseline-v1' || visibleBaseline.expected_pages !== 72) {
  throw new Error('EDITORIAL_DEPTH_VISIBLE_BASELINE_INVALID');
}

const archetypes = ['masterclass', 'workbook', 'playbook', 'prompts'];
const representative = [
  ...archetypes.map((resource) => `modulos/02-de-ocupado-a-productivo/${resource}/index.html`),
  ...archetypes.map((resource) => `en/empresa/modules/03-amplified-work/${resource}/index.html`),
  ...archetypes.map((resource) => `pt/empresa/modulos/04-trabalho-agentico/${resource}/index.html`),
];
for (const route of representative) {
  if (!nestedRoutes.includes(route)) throw new Error(`EDITORIAL_DEPTH_VISUAL_ROUTE_MISSING:${route}`);
}

const browser = await chromium.launch({headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
const local = (route) => pathToFileURL(resolve(dist, route)).href;
let scenarios = 0;

for (const width of [320, 390, 768, 1440]) {
  for (const theme of ['light', 'dark']) {
    const context = await browser.newContext({
      viewport: {width, height: 960},
      reducedMotion: 'reduce',
    });
    for (const route of representative) {
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', (error) => errors.push(error.message));
      await page.goto(local(route));
      await page.evaluate((value) => { document.documentElement.dataset.theme = value; }, theme);
      const promptCard = page.locator('.library-prompt-disclosure').first();
      if (await promptCard.count()) {
        const promptSummary = promptCard.locator(':scope > summary');
        await promptSummary.focus();
        await page.keyboard.press('Enter');
        if (!(await promptCard.evaluate((node) => node.open))) {
          throw new Error(`EDITORIAL_DEPTH_KEYBOARD_PROMPT_CARD:${width}:${theme}:${route}`);
        }
      }
      await page.locator('.module-depth-disclosure').first().scrollIntoViewIfNeeded();
      const summary = page.locator('.module-depth-disclosure > summary').first();
      await summary.focus();
      await page.keyboard.press('Enter');
      if (!(await summary.evaluate((node) => node.parentElement.open))) {
        throw new Error(`EDITORIAL_DEPTH_KEYBOARD_DISCLOSURE:${width}:${theme}:${route}`);
      }
      await page.locator('.module-depth-disclosure').evaluateAll((items) => items.forEach((item) => { item.open = true; }));
      await page.addScriptTag({path: axePath});
      const state = await page.evaluate(async () => {
        const main = document.querySelector('main[data-editorial-depth="nivel-0-editorial-depth-v1"]');
        const targetSizes = [...main.querySelectorAll('summary,button,a.btn')].filter((node) => node.getClientRects().length).map((node) => {
          const rect = node.getBoundingClientRect();
          return {tag: node.tagName, width: rect.width, height: rect.height};
        });
        const boxes = [...main.querySelectorAll('.module-depth-disclosure,.module-depth-card-grid,.module-depth-orientation,.module-depth-graph')]
          .map((node) => ({client: node.clientWidth, scroll: node.scrollWidth}));
        const audit = await axe.run(main, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa']}});
        return {
          markerCount: document.querySelectorAll('main[data-editorial-depth="nivel-0-editorial-depth-v1"]').length,
          disclosures: main.querySelectorAll('.module-depth-disclosure').length,
          openDisclosures: main.querySelectorAll('.module-depth-disclosure[open]').length,
          pageOverflow: document.documentElement.scrollWidth - innerWidth,
          boxOverflow: boxes.filter((item) => item.scroll - item.client > 1),
          smallTargets: targetSizes.filter((item) => item.width < 44 || item.height < 44),
          axeVersion: axe.version,
          violations: audit.violations.map((item) => ({
            id: item.id,
            nodes: item.nodes.slice(0, 4).map((node) => ({
              target: node.target,
              html: node.html,
              summary: node.failureSummary,
            })),
          })),
        };
      });
      if (
        errors.length || state.markerCount !== 1 || state.disclosures < 1 ||
        state.openDisclosures !== state.disclosures || state.pageOverflow > 0 ||
        state.boxOverflow.length || state.smallTargets.length ||
        state.axeVersion !== '4.12.1' || state.violations.length
      ) {
        throw new Error(`EDITORIAL_DEPTH_VISUAL_FAILED:${width}:${theme}:${route}:${JSON.stringify({errors, state})}`);
      }
      scenarios += 1;
      await page.close();
    }
    await context.close();
  }
}

const densityContext = await browser.newContext({viewport: {width: 1440, height: 1000}, reducedMotion: 'reduce'});
let maximumVisibleRatio = 0;
for (const route of nestedRoutes) {
  const baseline = visibleBaseline.word_counts[route];
  if (!Number.isInteger(baseline) || baseline < 1) throw new Error(`EDITORIAL_DEPTH_VISIBLE_BASELINE_MISSING:${route}`);
  const page = await densityContext.newPage();
  await page.goto(local(route), {waitUntil: 'domcontentloaded'});
  const current = await page.evaluate(() => (document.body.innerText.match(/\p{L}+/gu) || []).length);
  const ratio = current / baseline;
  maximumVisibleRatio = Math.max(maximumVisibleRatio, ratio);
  if (ratio > 2) throw new Error(`EDITORIAL_DEPTH_VISIBLE_DENSITY:${route}:${current}/${baseline}=${ratio.toFixed(3)}`);
  await page.close();
}
await densityContext.close();

const noJs = await browser.newContext({javaScriptEnabled: false, viewport: {width: 390, height: 900}});
for (const route of representative) {
  const page = await noJs.newPage();
  await page.goto(local(route));
  const state = await page.evaluate(() => ({
    markerCount: document.querySelectorAll('main[data-editorial-depth="nivel-0-editorial-depth-v1"]').length,
    summaries: [...document.querySelectorAll('.module-depth-disclosure > summary')].filter((node) => node.getClientRects().length).length,
    pageOverflow: document.documentElement.scrollWidth - innerWidth,
  }));
  if (state.markerCount !== 1 || state.summaries < 1 || state.pageOverflow > 0) {
    throw new Error(`EDITORIAL_DEPTH_NO_JS_FAILED:${route}:${JSON.stringify(state)}`);
  }
  await page.close();
}
await noJs.close();
await browser.close();

console.log(`[EVIDENCE:EDITORIAL_DEPTH_VISUAL] EDITORIAL_DEPTH_VISUAL_OK routes=12 scenarios=${scenarios} themes=2 breakpoints=320/390/768/1440 visible_density_72_max=${maximumVisibleRatio.toFixed(3)}x reduced_motion=true no_js=12 axe=4.12.1`);
