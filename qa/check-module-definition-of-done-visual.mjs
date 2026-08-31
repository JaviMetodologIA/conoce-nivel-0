import fs from 'node:fs';
import {relative, resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const root = resolve(import.meta.dirname, '..');
const dist = resolve(root, 'dist');
const playwrightModule = process.env.PLAYWRIGHT_MODULE
  || resolve(root, '..', '..', 'frames-n0-kit-01', 'node_modules', 'playwright', 'index.mjs');
const axePath = process.env.AXE_PATH
  || '/Users/deonto/Library/pnpm/store/v11/links/@/axe-core/4.12.1/b7c50e7913b3703b5001a11d2efeed145f43557f7e102bc3785e95708dc85687/node_modules/axe-core/axe.min.js';
const {chromium} = await import(pathToFileURL(playwrightModule));

const requested = process.argv.find((value) => value.startsWith('--module='))?.split('=')[1] || 'all';
if (!['2', '3', '4', 'all'].includes(requested)) throw new Error(`MODULE_DOD_ARGUMENT:${requested}`);
const orders = requested === 'all' ? ['02', '03', '04'] : [requested.padStart(2, '0')];
const resources = ['masterclass', 'workbook', 'playbook', 'prompts'];

function walk(folder) {
  return fs.readdirSync(folder, {withFileTypes: true}).flatMap((entry) =>
    entry.isDirectory() ? walk(resolve(folder, entry.name)) : [resolve(folder, entry.name)],
  );
}

function resourceOf(route) {
  return resources.find((resource) => route.includes(`/${resource}/`));
}

const routes = walk(dist)
  .filter((file) => file.endsWith('index.html'))
  .map((file) => relative(dist, file))
  .filter((route) => (route.includes('/modulos/') || route.includes('/modules/') || route.startsWith('modulos/')))
  .filter((route) => orders.some((order) => route.split('/').some((part) => part.startsWith(`${order}-`))))
  .filter((route) => resourceOf(route))
  .sort();
if (routes.length !== orders.length * 24) throw new Error(`MODULE_DOD_ROUTE_COUNT:${routes.length}`);

const canonical = routes.filter((route) => route.startsWith('modulos/') && !route.startsWith('empresa/'));
if (canonical.length !== orders.length * 4) throw new Error(`MODULE_DOD_CANONICAL_COUNT:${canonical.length}`);

const failures = [];
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.CHROME_EXECUTABLE || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
});
let scenarios = 0;
let axeRuns = 0;

async function open(context, route, theme) {
  const page = await context.newPage();
  const runtime = [];
  page.on('pageerror', (error) => runtime.push(error.message));
  page.on('console', (message) => { if (message.type() === 'error') runtime.push(`console:${message.text()}`); });
  await page.goto(pathToFileURL(resolve(dist, route)).href, {waitUntil: 'domcontentloaded'});
  await page.evaluate(() => document.fonts?.ready);
  await page.evaluate((value) => { document.documentElement.dataset.theme = value; window.scrollTo(0, 0); }, theme);
  await page.evaluate(() => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done))));
  return {page, runtime};
}

async function inspect(page, route, width, theme, withAxe) {
  if (withAxe) await page.addScriptTag({path: axePath});
  const state = await page.evaluate(async ({resource, width, withAxe}) => {
    const visible = (node) => Boolean(node && node.getClientRects().length && getComputedStyle(node).visibility !== 'hidden');
    const rect = (node) => node ? node.getBoundingClientRect().toJSON() : null;
    const current = document.querySelector('[data-module-siblings] [aria-current="page"]');
    const peer = document.querySelector('[data-module-siblings] a:not([aria-current])');
    const style = (node) => node ? getComputedStyle(node) : null;
    const currentStyle = style(current);
    const peerStyle = style(peer);
    const markerStyle = current ? getComputedStyle(current, '::before') : null;
    const common = {
      overflow: document.documentElement.scrollWidth - innerWidth,
      currentVisible: visible(current),
      currentDistinct: Boolean(currentStyle && peerStyle && (
        currentStyle.backgroundColor !== peerStyle.backgroundColor
        || currentStyle.borderColor !== peerStyle.borderColor
        || currentStyle.fontWeight !== peerStyle.fontWeight
      )),
      currentMarker: Boolean(markerStyle && Number.parseFloat(markerStyle.width) > 0 && markerStyle.content !== 'none'),
      smallTargets: [...document.querySelectorAll('main button,main summary,main a.btn,main [role="tab"]')]
        .filter(visible)
        .map((node) => ({node, box: node.getBoundingClientRect()}))
        .filter(({box}) => box.width < 44 || box.height < 44)
        .slice(0, 5)
        .map(({node, box}) => `${node.tagName}:${Math.round(box.width)}x${Math.round(box.height)}`),
    };
    const result = {common, resource: {}, axe: []};
    if (resource === 'masterclass') {
      result.resource = Object.fromEntries(['prev', 'next'].map((name) => {
        const button = document.querySelector(`.deck-${name}`);
        const icon = button?.querySelector('.ui-icon');
        return [name, {button: rect(button), icon: rect(icon), iconVisible: visible(icon)}];
      }));
    } else if (resource === 'playbook') {
      const cta = document.querySelector('.playbook-hero a.btn[href="#intro"]');
      result.resource = {cta: rect(cta), firstViewport: Boolean(cta && cta.getBoundingClientRect().top >= 0 && cta.getBoundingClientRect().bottom <= innerHeight)};
    } else if (resource === 'workbook') {
      const selected = document.querySelector('.sheet-tabs [aria-selected="true"]');
      result.resource = {
        tabs: document.querySelectorAll('.sheet-tabs [role="tab"]').length,
        selected: selected?.getAttribute('aria-controls') || '',
        gate: visible(document.querySelector('#sheet-consolidation [data-consolidation-gate]')),
      };
    } else {
      const first = document.querySelector('.library-prompt-disclosure');
      result.resource = {cards: document.querySelectorAll('.library-prompt-card').length, summary: rect(first?.querySelector(':scope > summary'))};
    }
    if (withAxe) {
      const audit = await axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa']}});
      result.axe = audit.violations.map(({id, impact}) => `${id}:${impact}`);
    }
    return result;
  }, {resource: resourceOf(route), width, withAxe});
  if (state.common.overflow > 1) failures.push(`OVERFLOW:${width}:${theme}:${route}:${state.common.overflow}`);
  if (!state.common.currentVisible || !state.common.currentDistinct || !state.common.currentMarker) failures.push(`CURRENT_RESOURCE:${width}:${theme}:${route}:${JSON.stringify(state.common)}`);
  if (state.common.smallTargets.length) failures.push(`TARGET_SIZE:${width}:${theme}:${route}:${state.common.smallTargets.join(',')}`);
  const resource = resourceOf(route);
  if (resource === 'masterclass' && width <= 390) {
    for (const name of ['prev', 'next']) {
      const control = state.resource[name];
      if (!control?.iconVisible || control.icon?.width < 12 || control.icon?.height < 12) failures.push(`MASTERCLASS_MOBILE_CONTROL:${width}:${theme}:${route}:${name}`);
    }
  }
  if (resource === 'playbook' && [320, 390, 1440].includes(width) && !state.resource.firstViewport) failures.push(`PLAYBOOK_FIRST_VIEWPORT_CTA:${width}:${theme}:${route}:${JSON.stringify(state.resource.cta)}`);
  if (resource === 'workbook' && (state.resource.tabs !== 3 || !state.resource.selected)) failures.push(`WORKBOOK_TABS:${width}:${theme}:${route}`);
  if (resource === 'prompts' && (!state.resource.cards || !state.resource.summary || state.resource.summary.height < 44)) failures.push(`PROMPTS_DISCLOSURE:${width}:${theme}:${route}`);
  if (state.axe.length) failures.push(`AXE:${width}:${theme}:${route}:${state.axe.join(',')}`);
}

for (const width of [320, 390, 768, 1440]) {
  for (const theme of ['light', 'dark']) {
    const context = await browser.newContext({viewport: {width, height: 960}, reducedMotion: 'reduce'});
    for (const route of canonical) {
      const {page, runtime} = await open(context, route, theme);
      if (runtime.length) failures.push(`RUNTIME:${width}:${theme}:${route}:${runtime.join('|')}`);
      const withAxe = [390, 1440].includes(width) && theme === 'light';
      await inspect(page, route, width, theme, withAxe);
      axeRuns += withAxe ? 1 : 0;
      scenarios += 1;
      await page.close();
    }
    await context.close();
  }
}

// Every locale/audience variant gets a mobile pass in both themes.
for (const theme of ['light', 'dark']) {
  const context = await browser.newContext({viewport: {width: 390, height: 960}, reducedMotion: 'reduce'});
  for (const route of routes) {
    const {page, runtime} = await open(context, route, theme);
    if (runtime.length) failures.push(`RUNTIME:390:${theme}:${route}:${runtime.join('|')}`);
    await inspect(page, route, 390, theme, false);
    scenarios += 1;
    await page.close();
  }
  await context.close();
}

const noJs = await browser.newContext({viewport: {width: 390, height: 960}, reducedMotion: 'reduce', javaScriptEnabled: false});
for (const route of routes) {
  const page = await noJs.newPage();
  await page.goto(pathToFileURL(resolve(dist, route)).href, {waitUntil: 'domcontentloaded'});
  const essential = await page.evaluate((resource) => {
    const selectors = {
      masterclass: ['.official-pdf-object', '.masterclass-player'],
      workbook: ['.field textarea', '#sheet-consolidation [data-consolidation-gate]'],
      playbook: ['.playbook-hero a[href="#intro"]', '#intro'],
      prompts: ['.notebook-execution-guide', '.library-prompt-disclosure > summary'],
    }[resource];
    return selectors.map((selector) => ({selector, visible: [...document.querySelectorAll(selector)].some((node) => node.getClientRects().length)}));
  }, resourceOf(route));
  const hidden = essential.filter(({visible}) => !visible);
  if (hidden.length) failures.push(`NO_JS:${route}:${hidden.map(({selector}) => selector).join(',')}`);
  await page.close();
}
await noJs.close();
await browser.close();

if (failures.length) {
  console.error(`[EVIDENCE:MODULE_DEFINITION_OF_DONE_VISUAL] MODULE_DOD_VISUAL_FAILED module=${requested} routes=${routes.length} scenarios=${scenarios} axe=${axeRuns} failures=${failures.length}`);
  failures.slice(0, 120).forEach((failure) => console.error(failure));
  process.exitCode = 1;
} else {
  console.log(`[EVIDENCE:MODULE_DEFINITION_OF_DONE_VISUAL] MODULE_DOD_VISUAL_PASS module=${requested} routes=${routes.length} scenarios=${scenarios} axe=${axeRuns} matrix=320/390/768/1440xlight/dark no_js=${routes.length}`);
}
