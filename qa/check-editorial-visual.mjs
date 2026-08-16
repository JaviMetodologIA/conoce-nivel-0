import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = resolve(import.meta.dirname, '..');
const playwrightModule = process.env.PLAYWRIGHT_MODULE || resolve(root, '..', '..', 'frames-n0-kit-01', 'node_modules', 'playwright', 'index.mjs');
const axePath = process.env.AXE_PATH || '/Users/deonto/Library/pnpm/store/v11/links/@/axe-core/4.12.1/b7c50e7913b3703b5001a11d2efeed145f43557f7e102bc3785e95708dc85687/node_modules/axe-core/axe.min.js';
const { chromium } = await import(pathToFileURL(playwrightModule));
const browser = await chromium.launch({headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
const local = (route) => pathToFileURL(resolve(root, 'dist', route, 'index.html')).href;

const slugs = {
  es: ['nivel-0', 'como-funciona', 'recursos', 'convocatorias'],
  en: ['level-0', 'how-it-works', 'resources', 'intakes'],
  pt: ['nivel-0', 'como-funciona', 'recursos', 'turmas'],
};
const routes = [];
for (const [locale, pages] of Object.entries(slugs)) {
  for (const audience of ['persona', 'empresa']) {
    const prefix = [locale === 'es' ? '' : locale, audience === 'empresa' ? 'empresa' : ''].filter(Boolean).join('/');
    for (const page of pages) routes.push([prefix, page].filter(Boolean).join('/'));
  }
}

for (const route of routes) {
  for (const theme of ['light', 'dark']) {
    const page = await browser.newPage({viewport: {width: 390, height: 844}});
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto(local(route));
    await page.evaluate((value) => { document.documentElement.dataset.theme = value; }, theme);
    await page.addScriptTag({path: axePath});
    const state = await page.evaluate(async () => {
      const links = [...document.querySelectorAll('.editorial-link')];
      const result = await axe.run(document.querySelector('main'), {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa']}});
      return {
        axeVersion: axe.version,
        violations: result.violations.map((item) => ({id: item.id, nodes: item.nodes.length})),
        overflow: document.documentElement.scrollWidth - innerWidth,
        hero: document.querySelector('.editorial-hero')?.getBoundingClientRect(),
        audience: document.querySelector('.editorial-audience')?.getBoundingClientRect(),
        sections: document.querySelectorAll('.editorial-section').length,
        sidebar: document.querySelectorAll('[data-intrapage-nav]').length,
        smallLinks: links.filter((item) => item.getBoundingClientRect().height < 44).map((item) => item.textContent.trim()),
      };
    });
    if (errors.length || state.axeVersion !== '4.12.1' || state.violations.length || state.overflow > 0 || !state.hero?.height || !state.audience?.height || state.sections !== 4 || state.sidebar !== 1 || state.smallLinks.length) {
      throw new Error(`EDITORIAL_VISUAL_FAILED ${route} ${theme}: ${JSON.stringify({errors, state})}`);
    }
    await page.close();
  }
}

for (const [width, route] of [[320, 'convocatorias'], [768, 'en/empresa/how-it-works'], [1440, 'pt/empresa/recursos']]) {
  const page = await browser.newPage({viewport: {width, height: 900}});
  await page.goto(local(route));
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
  if (overflow > 0) throw new Error(`EDITORIAL_RESPONSIVE_OVERFLOW ${width}:${route}:${overflow}`);
  if (width <= 1180) {
    await page.locator('[data-intrapage-open]').click();
    await page.waitForFunction(() => document.querySelector('[data-intrapage-close]') === document.activeElement);
    if (!await page.locator('[data-intrapage-close]').evaluate((node) => node === document.activeElement)) throw new Error(`EDITORIAL_DRAWER_FOCUS ${width}:${route}`);
    await page.keyboard.press('Escape');
    if (!await page.locator('[data-intrapage-open]').evaluate((node) => node === document.activeElement)) throw new Error(`EDITORIAL_DRAWER_RETURN ${width}:${route}`);
  }
  await page.close();
}

const noJs = await browser.newContext({javaScriptEnabled: false, viewport: {width: 390, height: 844}});
const noJsPage = await noJs.newPage();
await noJsPage.goto(local('pt/turmas'));
const noJsState = await noJsPage.evaluate(() => ({
  navVisible: document.querySelector('[data-intrapage-nav]').getClientRects().length > 0,
  links: document.querySelectorAll('[data-intrapage-link]').length,
  targets: [...document.querySelectorAll('[data-intrapage-link]')].every((link) => document.querySelector(link.hash)),
}));
if (!noJsState.navVisible || noJsState.links !== 5 || !noJsState.targets) throw new Error(`EDITORIAL_NO_JS_FAILED ${JSON.stringify(noJsState)}`);
await noJs.close();
await browser.close();
console.log(`EDITORIAL_VISUAL_OK pages=${routes.length} themes=2 axe=4.12.1 responsive=320/390/768/1440 no_js=PASS`);
