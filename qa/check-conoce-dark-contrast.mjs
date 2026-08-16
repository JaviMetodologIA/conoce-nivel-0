import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = resolve(import.meta.dirname, '..');
const playwrightModule = process.env.PLAYWRIGHT_MODULE || resolve(root, '..', '..', 'frames-n0-kit-01', 'node_modules', 'playwright', 'index.mjs');
const axePath = process.env.AXE_PATH || '/Users/deonto/Library/pnpm/store/v11/links/@/axe-core/4.12.1/b7c50e7913b3703b5001a11d2efeed145f43557f7e102bc3785e95708dc85687/node_modules/axe-core/axe.min.js';
const { chromium } = await import(pathToFileURL(playwrightModule));
const browser = await chromium.launch({headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
const local = pathToFileURL(resolve(root, 'dist/index.html')).href;

function channels(css) {
  const match = css.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (!match) throw new Error(`Unsupported computed color: ${css}`);
  return match.slice(1).map(Number);
}
function luminance(rgb) {
  const linear = rgb.map((value) => { const channel = value / 255; return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4; });
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
}
function contrast(foreground, background) {
  const values = [luminance(channels(foreground)), luminance(channels(background))].sort((a, b) => b - a);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

for (const width of [390, 1440]) {
  const page = await browser.newPage({viewport: {width, height: 900}});
  await page.goto(local);
  await page.evaluate(() => { document.documentElement.dataset.theme = 'dark'; });
  await page.addScriptTag({path: axePath});
  const audit = await page.evaluate(async () => ({version: axe.version, result: await axe.run(document.querySelector('.tension-grid'), {runOnly: {type: 'rule', values: ['color-contrast']}})}));
  if (audit.version !== '4.12.1' || audit.result.violations.length) throw new Error(`AXE_DARK_CONTRAST_FAILED width=${width} ${JSON.stringify(audit.result.violations)}`);
  const computed = await page.locator('.tension-card').evaluateAll((cards) => cards.flatMap((card, cardIndex) => {
    const background = getComputedStyle(card).backgroundColor;
    return [...card.querySelectorAll('.tension-num,strong,span:not(.tension-num),em')].map((node) => ({card: cardIndex + 1, selector: node.matches('.tension-num') ? '.tension-num' : node.tagName.toLowerCase(), foreground: getComputedStyle(node).color, background}));
  }));
  if (computed.length !== 12) throw new Error(`TENSION_ORACLE_NODE_COUNT width=${width} count=${computed.length}`);
  for (const item of computed) {
    item.ratio = contrast(item.foreground, item.background);
    if (item.ratio < 4.5) throw new Error(`TENSION_CONTRAST_FAILED width=${width} ${JSON.stringify(item)}`);
  }
  const minimum = Math.min(...computed.map((item) => item.ratio));
  console.log(`CONOCE_DARK_CONTRAST_OK axe=${audit.version} width=${width} nodes=${computed.length} min=${minimum.toFixed(2)}`);
  await page.close();
}
await browser.close();
