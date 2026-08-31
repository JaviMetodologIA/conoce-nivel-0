import fs from 'node:fs';
import { resolve, relative, dirname } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = resolve(import.meta.dirname, '..');
const dist = resolve(root, 'dist');
const playwrightModule = process.env.PLAYWRIGHT_MODULE || resolve(root, '..', '..', 'frames-n0-kit-01', 'node_modules', 'playwright', 'index.mjs');
const axePath = process.env.AXE_PATH || '/Users/deonto/Library/pnpm/store/v11/links/@/axe-core/4.12.1/b7c50e7913b3703b5001a11d2efeed145f43557f7e102bc3785e95708dc85687/node_modules/axe-core/axe.min.js';
const { chromium } = await import(pathToFileURL(playwrightModule));
const browser = await chromium.launch({headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});

function walk(folder) {
  return fs.readdirSync(folder, {withFileTypes: true}).flatMap((entry) => entry.isDirectory() ? walk(resolve(folder, entry.name)) : [resolve(folder, entry.name)]);
}
const routes = walk(dist).filter((file) => file.endsWith('index.html')).map((file) => relative(dist, file));
if (routes.length !== 126) throw new Error(`BREADCRUMB_VISUAL_ROUTE_COUNT ${routes.length}`);
const local = (route) => pathToFileURL(resolve(dist, route)).href;

const page = await browser.newPage({viewport: {width: 390, height: 844}});
let nestedCount = 0;
for (const route of routes) {
  for (const theme of ['light', 'dark']) {
    const errors = [];
    const listener = (error) => errors.push(error.message);
    page.on('pageerror', listener);
    await page.goto(local(route));
    await page.evaluate((value) => { document.documentElement.dataset.theme = value; }, theme);
    await page.addScriptTag({path: axePath});
    const state = await page.evaluate(async () => {
      const crumb = document.querySelector('[data-conoce-breadcrumbs]');
      const trigger = document.querySelector('[data-intrapage-open]');
      const pageId = document.body.dataset.page;
      const moduleId = document.body.dataset.moduleId;
      const resource = ['deck', 'workbook', 'playbook', 'prompts'].includes(pageId);
      const nested = resource && moduleId !== 'ia-panorama';
      const expectedItems = pageId === 'landing' ? 1 : resource ? (nested ? 4 : 3) : 2;
      const crumbTargets = [...crumb.querySelectorAll('a,[aria-current="page"]')].map((node) => node.getBoundingClientRect());
      const triggerRect = trigger.getBoundingClientRect();
      const intersects = crumbTargets.some((rect) => !(rect.right <= triggerRect.left || rect.left >= triggerRect.right || rect.bottom <= triggerRect.top || rect.top >= triggerRect.bottom));
      const result = await axe.run(crumb, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa']}});
      return {
        axeVersion: axe.version,
        violations: result.violations.map((item) => item.id),
        breadcrumbCount: document.querySelectorAll('[data-conoce-breadcrumbs]').length,
        currentCount: crumb.querySelectorAll('[aria-current="page"]').length,
        itemCount: crumb.querySelectorAll('ol > li').length,
        expectedItems,
        nested,
        nestedModuleLink: nested ? crumb.querySelector('ol > li:nth-child(3) a[href*="#module-"]') !== null : true,
        lastIsCurrent: crumb.querySelector('li:last-child > span[aria-current="page"]') !== null,
        singletonShell: ['[data-conoce-header]', '[data-conoce-footer]', '[data-conoce-preferences]', '[data-intrapage-nav]'].every((selector) => document.querySelectorAll(selector).length === 1),
        visible: crumb.getClientRects().length > 0,
        overflow: document.documentElement.scrollWidth - innerWidth,
        overlap: intersects,
      };
    });
    page.off('pageerror', listener);
    if (errors.length || state.axeVersion !== '4.12.1' || state.violations.length || state.breadcrumbCount !== 1 || state.currentCount !== 1 || state.itemCount !== state.expectedItems || !state.nestedModuleLink || !state.lastIsCurrent || !state.singletonShell || !state.visible || state.overflow > 0 || state.overlap) {
      throw new Error(`BREADCRUMB_VISUAL_FAILED ${route}:${theme} ${JSON.stringify({errors, state})}`);
    }
    if (theme === 'light' && state.nested) nestedCount += 1;
  }
  await page.locator('[data-conoce-menu]').evaluate((node) => node.click());
  await page.waitForFunction(() => document.querySelector('[data-conoce-home-link]')?.getClientRects().length > 0);
  const home = await page.locator('[data-conoce-home-link]').evaluate((node) => ({rect: node.getBoundingClientRect(), hash: node.hash, current: node.getAttribute('aria-current')}));
  if (home.rect.width < 44 || home.rect.height < 44 || home.hash) throw new Error(`BREADCRUMB_HEADER_HOME_VISUAL ${route}:${JSON.stringify(home)}`);
  await page.keyboard.press('Escape');
}
await page.close();
if (nestedCount !== 72) throw new Error(`BREADCRUMB_VISUAL_NESTED_COUNT ${nestedCount}`);

for (const [width, route] of [
  [320, 'playbook/index.html'],
  [390, 'empresa/modulos/02-de-ocupado-a-productivo/prompts/index.html'],
  [768, 'en/empresa/modules/03-amplified-work/workbook/index.html'],
  [1440, 'pt/modulos/04-trabalho-agentico/masterclass/index.html'],
]) {
  const test = await browser.newPage({viewport: {width, height: 900}});
  await test.goto(local(route));
  const state = await test.evaluate(() => {
    const crumb = document.querySelector('[data-conoce-breadcrumbs]').getBoundingClientRect();
    const header = document.querySelector('[data-conoce-header]').getBoundingClientRect();
    const rail = document.querySelector('[data-intrapage-nav]').getBoundingClientRect();
    return {overflow: document.documentElement.scrollWidth - innerWidth, crumb, header, rail};
  });
  if (state.overflow > 0 || state.crumb.top < state.header.bottom - 1 || (width > 1180 && state.crumb.left < 260)) throw new Error(`BREADCRUMB_BREAKPOINT_FAILED ${width}:${route}:${JSON.stringify(state)}`);
  await test.close();
}

const noJs = await browser.newContext({javaScriptEnabled: false, viewport: {width: 390, height: 844}});
for (const route of [
  'index.html',
  'nivel-0/index.html',
  'recursos/index.html',
  'playbook/index.html',
  'empresa/modulos/02-de-ocupado-a-productivo/prompts/index.html',
]) {
  const test = await noJs.newPage();
  await test.goto(local(route));
  const state = await test.evaluate(() => ({visible: document.querySelector('[data-conoce-breadcrumbs]').getClientRects().length > 0, current: document.querySelectorAll('[data-conoce-breadcrumbs] [aria-current="page"]').length, home: document.querySelectorAll('[data-conoce-home-link]').length}));
  if (!state.visible || state.current !== 1 || state.home !== 1) throw new Error(`BREADCRUMB_NO_JS_FAILED ${route}:${JSON.stringify(state)}`);
  await test.close();
}
await noJs.close();
await browser.close();
console.log('[EVIDENCE:BREADCRUMB_VISUAL] BREADCRUMB_VISUAL_OK pages=126 nested_4_level=72 themes=2 axe=4.12.1 breakpoints=320/390/768/1440 no_js=5');
