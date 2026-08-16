import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = resolve(import.meta.dirname, '..');
const playwrightModule = process.env.PLAYWRIGHT_MODULE || resolve(root, '..', '..', 'frames-n0-kit-01', 'node_modules', 'playwright', 'index.mjs');
const { chromium } = await import(pathToFileURL(playwrightModule));
const browser = await chromium.launch({headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
const local = (route) => pathToFileURL(resolve(root, 'dist', route)).href;

for (const width of [320, 390, 768, 1440]) {
  const page = await browser.newPage({viewport: {width, height: 900}});
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(local(width === 768 ? 'en/workbook/index.html' : 'index.html'));
  await page.waitForLoadState('load');
  const state = await page.evaluate(() => {
    const targets = [...document.querySelectorAll('[data-conoce-header] a, [data-conoce-header] button, [data-conoce-header] summary, [data-conoce-preferences] a, [data-conoce-preferences] button')].filter((item) => item.getClientRects().length > 0);
    return {
      overflow: document.documentElement.scrollWidth - innerWidth,
      headerHeight: document.querySelector('[data-conoce-header]').getBoundingClientRect().height,
      smallTargets: targets.map((item) => ({label: item.textContent.trim() || item.getAttribute('aria-label'), rect: item.getBoundingClientRect()})).filter((item) => item.rect.width < 44 || item.rect.height < 44),
      identityName: document.querySelector('.conoce-brand strong')?.textContent.trim(),
      identityLevel: document.querySelector('.conoce-brand small')?.firstChild?.textContent.trim(),
      parentTarget: document.querySelector('[data-conoce-parent]')?.target,
    };
  });
  if (errors.length || state.overflow > 0 || state.headerHeight < 44 || state.smallTargets.length || state.identityName !== 'Conoce' || state.identityLevel !== 'Nivel 0' || state.parentTarget) throw new Error(`Chrome viewport failed ${width}: ${JSON.stringify({errors, state})}`);
  if (width <= 1180) {
    await page.locator('[data-conoce-menu]').click();
    await page.waitForTimeout(40);
    if (await page.locator('[data-conoce-menu]').getAttribute('aria-expanded') !== 'true') throw new Error(`Mobile menu did not open ${width}`);
    const focused = await page.evaluate(() => document.activeElement?.matches('[data-conoce-nav] a, [data-conoce-nav] summary'));
    if (!focused) throw new Error(`Mobile menu focus did not enter nav ${width}`);
    await page.locator('[data-conoce-resources] summary').click();
    if (!await page.locator('[data-conoce-resources]').evaluate((node) => node.open)) throw new Error(`Resources did not open ${width}`);
    await page.keyboard.press('Escape');
    if (await page.locator('[data-conoce-menu]').getAttribute('aria-expanded') !== 'false' || !await page.locator('[data-conoce-menu]').evaluate((node) => node === document.activeElement)) throw new Error(`Escape/focus return failed ${width}`);
    await page.locator('[data-conoce-menu]').click();
    await page.locator('[data-intrapage-open]').evaluate((node) => node.click());
    await page.waitForTimeout(40);
    if (await page.locator('[data-conoce-menu]').getAttribute('aria-expanded') !== 'false' || await page.locator('[data-intrapage-open]').getAttribute('aria-expanded') !== 'true') throw new Error(`Header/sidebar mutual exclusion failed ${width}`);
    await page.keyboard.press('Escape');
  } else {
    await page.locator('[data-conoce-resources] summary').click();
    await page.locator('[data-conoce-resource-link]').first().focus();
    await page.keyboard.press('Escape');
    const desktopDisclosure = await page.locator('[data-conoce-resources]').evaluate((node) => ({open: node.open, summaryFocused: node.querySelector('summary') === document.activeElement}));
    if (desktopDisclosure.open || !desktopDisclosure.summaryFocused) throw new Error(`Desktop resources Escape/focus return failed ${width}: ${JSON.stringify(desktopDisclosure)}`);
  }
  await page.close();
}

const noJs = await browser.newContext({javaScriptEnabled: false, viewport: {width: 390, height: 844}});
const noJsPage = await noJs.newPage();
await noJsPage.goto(local('pt/prompts/index.html'));
const noJsState = await noJsPage.evaluate(() => ({
  navDisplay: getComputedStyle(document.querySelector('[data-conoce-nav]')).display,
  visibleResourceLinks: [...document.querySelectorAll('[data-conoce-resource-link]')].filter((item) => getComputedStyle(item).display !== 'none' && item.getClientRects().length).length,
  preferences: document.querySelectorAll('[data-conoce-preferences]').length,
}));
if (noJsState.navDisplay === 'none' || noJsState.visibleResourceLinks !== 4 || noJsState.preferences !== 1) throw new Error(`No-JS chrome failed: ${JSON.stringify(noJsState)}`);
await noJs.close();
await browser.close();
console.log('CONOCE_CHROME_VISUAL_OK widths=4 no_js=PASS');
