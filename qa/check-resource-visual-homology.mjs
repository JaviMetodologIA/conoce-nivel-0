import fs from 'node:fs';
import {relative, resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const root = resolve(import.meta.dirname, '..');
const dist = resolve(root, 'dist');
const playwrightModule = process.env.PLAYWRIGHT_MODULE
  || resolve(root, '..', '..', 'frames-n0-kit-01', 'node_modules', 'playwright', 'index.mjs');
const chromeExecutable = process.env.CHROME_EXECUTABLE
  || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const {chromium} = await import(pathToFileURL(playwrightModule));

const resources = ['masterclass', 'workbook', 'playbook', 'prompts'];
const referenceRoutes = {
  masterclass: 'deck/index.html',
  workbook: 'workbook/index.html',
  playbook: 'playbook/index.html',
  prompts: 'prompts/index.html',
};
const representativeRoutes = [
  ...resources.map((resource) => ({
    resource,
    route: `modulos/02-de-ocupado-a-productivo/${resource}/index.html`,
  })),
  ...resources.map((resource) => ({
    resource,
    route: `en/empresa/modules/03-amplified-work/${resource}/index.html`,
  })),
  ...resources.map((resource) => ({
    resource,
    route: `pt/empresa/modulos/04-trabalho-agentico/${resource}/index.html`,
  })),
];
const widths = [320, 390, 768, 1440];
const themes = ['light', 'dark'];
const failures = new Map();

function walk(folder) {
  return fs.readdirSync(folder, {withFileTypes: true}).flatMap((entry) =>
    entry.isDirectory() ? walk(resolve(folder, entry.name)) : [resolve(folder, entry.name)],
  );
}

function count(source, needle) {
  return source.split(needle).length - 1;
}

function record(code, route, detail, width = '-', theme = '-') {
  const key = `${code}|${route}|${width}|${theme}|${detail}`;
  failures.set(key, {code, route, width, theme, detail});
}

function resourceFromRoute(route) {
  return resources.find((resource) => route.includes(`/${resource}/`) || route.startsWith(`${resource}/`));
}

const nestedRoutes = walk(dist)
  .filter((file) => file.endsWith('index.html'))
  .map((file) => relative(dist, file))
  .filter((route) => route.includes('/modulos/') || route.includes('/modules/') || route.startsWith('modulos/'))
  .sort();

if (nestedRoutes.length !== 72) {
  record('ROUTE_COUNT', 'dist', `expected=72 actual=${nestedRoutes.length}`);
}
for (const resource of resources) {
  const actual = nestedRoutes.filter((route) => resourceFromRoute(route) === resource).length;
  if (actual !== 18) record('RESOURCE_ROUTE_COUNT', resource, `expected=18 actual=${actual}`);
}
for (const route of Object.values(referenceRoutes)) {
  if (!fs.existsSync(resolve(dist, route))) record('REFERENCE_ROUTE_MISSING', route, 'missing M1 homologue');
}
for (const {route} of representativeRoutes) {
  if (!nestedRoutes.includes(route)) record('REPRESENTATIVE_ROUTE_MISSING', route, 'missing visual representative');
}

// Static topology runs over all 72 nested pages. It deliberately checks component
// grammar, not localized copy length or module-specific editorial counts.
const commonMarkers = [
  ['data-conoce-header', 1],
  ['data-conoce-footer', 1],
  ['data-conoce-preferences', 1],
  ['data-intrapage-nav', 1],
  ['id="main"', 1],
];
const resourceMarkers = {
  masterclass: [
    ['class="official-masterclass"', 1],
    ['class="official-pdf-card"', 1],
    ['class="official-pdf-object"', 1],
    ['class="masterclass-player"', 1],
    ['class="module-resource-strip"', 1],
  ],
  workbook: [
    ['class="doc-hero workbook-hero"', 1],
    ['class="workbook-sheets"', 1],
    ['class="sheet-tabs"', 1],
    ['class="print-link"', 1],
  ],
  playbook: [
    ['class="playbook-hero-grid"', 1],
    ['class="playbook-toc"', 1],
    ['id="intro"', 1],
    ['class="playbook-content"', 1],
  ],
  prompts: [
    ['data-notebook-execution-guide', 1],
    ['class="shell prompt-library-secondary-map"', 1],
    ['class="library-prompt-list"', 1],
    ['data-prompt-card-disclosure', null],
  ],
};
for (const route of nestedRoutes) {
  const resource = resourceFromRoute(route);
  if (!resource) {
    record('UNKNOWN_RESOURCE_ROUTE', route, 'cannot resolve resource archetype');
    continue;
  }
  const html = fs.readFileSync(resolve(dist, route), 'utf8');
  for (const [marker, expected] of commonMarkers) {
    const actual = count(html, marker);
    if (actual !== expected) record('SHELL_TOPOLOGY', route, `${marker} expected=${expected} actual=${actual}`);
  }
  if (count(html, `data-module-resource="${resource}"`) !== 1) {
    record('RESOURCE_IDENTITY', route, `missing exact data-module-resource=${resource}`);
  }
  for (const [marker, expected] of resourceMarkers[resource]) {
    const actual = count(html, marker);
    if (expected === null ? actual < 1 : actual !== expected) {
      record('RESOURCE_TOPOLOGY', route, `${marker} expected=${expected ?? '>=1'} actual=${actual}`);
    }
  }
  if (resource === 'masterclass') {
    const pdf = html.indexOf('class="official-pdf-card"');
    const strip = html.indexOf('class="module-resource-strip"');
    const guide = html.indexOf('class="masterclass-player"');
    if (!(pdf >= 0 && strip > pdf && guide > strip)) {
      record('MASTERCLASS_READING_ORDER', route, `expected PDF < sibling navigation < HTML guide; got ${pdf}/${strip}/${guide}`);
    }
  }
}

const browser = await chromium.launch({headless: true, executablePath: chromeExecutable});
let visualScenarios = 0;

async function openPage(context, route, theme) {
  const page = await context.newPage();
  const runtimeErrors = [];
  page.on('pageerror', (error) => runtimeErrors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error') runtimeErrors.push(`console:${message.text()}`);
  });
  await page.goto(pathToFileURL(resolve(dist, route)).href, {waitUntil: 'domcontentloaded'});
  // Typography is part of the visual contract. Measuring before the bundled
  // faces settle can turn a transient fallback-font wrap into a false density
  // or overflow regression, especially at 320 px.
  await page.evaluate(() => document.fonts?.ready);
  await page.evaluate((value) => {
    document.documentElement.dataset.theme = value;
    window.scrollTo(0, 0);
  }, theme);
  await page.evaluate(() => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done))));
  return {page, runtimeErrors};
}

async function snapshot(page, resource, nested) {
  return page.evaluate(({resource, nested}) => {
    const visible = (node) => Boolean(node && (
      typeof node.checkVisibility === 'function'
        ? node.checkVisibility({opacityProperty: true, visibilityProperty: true})
        : node.getClientRects().length
    ));
    const rect = (node) => {
      if (!node) return null;
      const value = node.getBoundingClientRect();
      return {
        x: value.x,
        y: value.y,
        top: value.top,
        right: value.right,
        bottom: value.bottom,
        left: value.left,
        width: value.width,
        height: value.height,
      };
    };
    const overlapArea = (a, b) => {
      if (!a || !b) return 0;
      return Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left))
        * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
    };
    const one = (selector) => document.querySelector(selector);
    const main = one('main#main');
    const h1 = main?.querySelector('h1');
    const rootStyle = getComputedStyle(document.documentElement);
    const shellSelectors = ['.mdg-header', '.mdg-footer', '.mdg-controls', '.intrapage-nav', '.intrapage-trigger'];
    const shellCounts = Object.fromEntries(shellSelectors.map((selector) => [selector, document.querySelectorAll(selector).length]));
    const keyOverflowSelectors = {
      masterclass: ['.official-pdf-card', '.masterclass-player-head', '.masterclass-player .deck'],
      workbook: ['.workbook-hero-grid', '.workbook-flow', '.workbook-sheets'],
      playbook: ['.playbook-hero-grid', '.playbook-content', '.playbook-toc'],
      prompts: ['.prompt-library-hero-grid', '.notebook-execution-guide', '.library-prompt-list', '.library-prompt-card'],
    }[resource];
    const boxOverflow = keyOverflowSelectors.flatMap((selector) =>
      [...document.querySelectorAll(selector)]
        .filter(visible)
        .flatMap((node) => {
          if (node.scrollWidth - node.clientWidth <= 1) return [];
          const bounds = rect(node);
          const clipped = [...node.querySelectorAll('h1,h2,h3,h4,p,li,summary,a,button,textarea,code,dt,dd,strong,pre')]
            .filter(visible)
            .filter((child) => {
              const childBounds = rect(child);
              return childBounds.left < bounds.left - 1 || childBounds.right > bounds.right + 1;
            })
            .slice(0, 4)
            .map((child) => `${child.tagName.toLowerCase()}${child.id ? `#${child.id}` : ''}`);
          return clipped.length ? [{selector, client: node.clientWidth, scroll: node.scrollWidth, clipped}] : [];
        })
        .slice(0, 3),
    );
    const controls = ['.mdg-controls', '.intrapage-trigger']
      .map((selector) => ({selector, node: one(selector)}))
      .filter(({node}) => visible(node))
      .map(({selector, node}) => ({selector, rect: rect(node)}));
    const controlPairs = [];
    for (let left = 0; left < controls.length; left += 1) {
      for (let right = left + 1; right < controls.length; right += 1) {
        const area = overlapArea(controls[left].rect, controls[right].rect);
        if (area > 1) controlPairs.push(`${controls[left].selector}/${controls[right].selector}:${Math.round(area)}`);
      }
    }
    const controlChrome = [];
    for (const control of controls) {
      for (const target of [...document.querySelectorAll('.conoce-menu,.conoce-brand,.conoce-parent-cta')].filter(visible)) {
        const area = overlapArea(control.rect, rect(target));
        if (area > 1) {
          controlChrome.push(`${control.selector}/${target.matches('.conoce-menu') ? '.conoce-menu' : target.matches('.conoce-brand') ? '.conoce-brand' : '.conoce-parent-cta'}:${Math.round(area)}`);
        }
      }
    }
    const criticalSelector = 'main h1,main h2,main h3,main p,main li,main summary,main a,main button,main textarea,main code,main dt,main dd,main strong';
    const critical = [...document.querySelectorAll(criticalSelector)].filter((node) =>
      visible(node) && !node.closest('.mdg-controls,.intrapage-trigger,.intrapage-nav,.mdg-header'),
    );
    const controlContent = [];
    for (const control of controls) {
      for (const target of critical) {
        const area = overlapArea(control.rect, rect(target));
        if (area > 16) {
          const label = `${target.tagName.toLowerCase()}${target.id ? `#${target.id}` : ''}${target.className && typeof target.className === 'string' ? `.${target.className.trim().split(/\s+/).slice(0, 2).join('.')}` : ''}`;
          controlContent.push(`${control.selector}/${label}:${Math.round(area)}`);
          if (controlContent.length >= 8) break;
        }
      }
    }
    const common = {
      shellCounts,
      mainRect: rect(main),
      pageOverflow: document.documentElement.scrollWidth - innerWidth,
      boxOverflow,
      controlPairs,
      controlChrome,
      controlContent,
      duplicateIds: [...document.querySelectorAll('[id]')]
        .map((node) => node.id)
        .filter((id, index, ids) => ids.indexOf(id) !== index)
        .filter((id, index, ids) => ids.indexOf(id) === index),
      tokens: {
        head: rootStyle.getPropertyValue('--mdg-head').trim(),
        body: rootStyle.getPropertyValue('--mdg-body').trim(),
        gold: rootStyle.getPropertyValue('--gold-ui').trim(),
        ink: rootStyle.getPropertyValue('--ink').trim(),
        mainFont: main ? getComputedStyle(main).fontFamily : '',
        headingFont: h1 ? getComputedStyle(h1).fontFamily : '',
        headerBackground: one('.mdg-header') ? getComputedStyle(one('.mdg-header')).backgroundColor : '',
      },
    };

    if (resource === 'masterclass') {
      const official = one('.official-masterclass .shell');
      const pdf = one('.official-pdf-card');
      const pdfObject = one('.official-pdf-object');
      const strip = one('.module-resource-strip');
      const guide = one('.masterclass-player');
      return {common, resource: {
        officialCount: document.querySelectorAll('.official-masterclass').length,
        pdfCount: document.querySelectorAll('.official-pdf-card[data-official-masterclass]').length,
        objectCount: document.querySelectorAll('.official-pdf-object[type="application/pdf"]').length,
        guideCount: document.querySelectorAll('.masterclass-player').length,
        pdfBeforeStrip: !strip || Boolean(pdf?.compareDocumentPosition(strip) & Node.DOCUMENT_POSITION_FOLLOWING),
        pdfBeforeGuide: Boolean(pdf?.compareDocumentPosition(guide) & Node.DOCUMENT_POSITION_FOLLOWING),
        pdfWidthRatio: pdf && official ? rect(pdf).width / rect(official).width : 0,
        pdfHeight: rect(pdfObject)?.height || 0,
        pdfLocal: Boolean(pdfObject && !/^(?:https?:)?\/\//i.test(pdfObject.getAttribute('data') || '')),
      }};
    }

    if (resource === 'workbook') {
      const fields = [...document.querySelectorAll('.field textarea')];
      const visibleFields = fields.filter(visible);
      const print = one('.print-link');
      const consolidation = one('#sheet-consolidation');
      const stageTabs = [...document.querySelectorAll('.sheet-tabs [role="tab"]')];
      return {common, resource: {
        heroCount: document.querySelectorAll('.workbook-hero-grid').length,
        outcomeCount: document.querySelectorAll('.workbook-outcome').length,
        fields: fields.length,
        visibleFields: visibleFields.length,
        unnamedFields: fields.filter((field) => {
          const labelledBy = field.getAttribute('aria-labelledby');
          return !field.getAttribute('aria-label')
            && !(labelledBy && document.getElementById(labelledBy)?.textContent.trim())
            && !field.closest('label')?.textContent.trim();
        }).length,
        firstField: rect(visibleFields[0]),
        printCount: document.querySelectorAll('.print-link').length,
        printRect: rect(print),
        printAction: print?.getAttribute('onclick') || '',
        tabCount: document.querySelectorAll('.sheet-tabs [role="tab"]').length,
        selectedTabs: document.querySelectorAll('.sheet-tabs [role="tab"][aria-selected="true"]').length,
        locale: document.documentElement.lang,
        tabTexts: stageTabs.map((tab) => tab.textContent.trim().replace(/\s+/g, ' ')),
        stageIds: stageTabs.map((tab) => tab.dataset.workbookStage || ''),
        gateCount: document.querySelectorAll('[data-consolidation-gate]').length,
        gateInConsolidation: Boolean(consolidation?.querySelector('[data-consolidation-gate]')),
        rubricInConsolidation: Boolean(consolidation?.querySelector('#workbook-rubric')),
        transferInConsolidation: Boolean(consolidation?.querySelector('#transferencia')),
      }};
    }

    if (resource === 'playbook') {
      const grid = one('.playbook-hero-grid');
      const copy = one('.playbook-hero-copy');
      const companion = grid?.querySelector('.workbook-outcome,.playbook-mark');
      const toc = one('.playbook-toc');
      const tocLinks = [...document.querySelectorAll('.playbook-toc a[href^="#"]')];
      const introTitle = one('#intro h2');
      const titleStyle = introTitle ? getComputedStyle(introTitle) : null;
      return {common, resource: {
        gridCount: document.querySelectorAll('.playbook-hero-grid').length,
        gridDisplay: grid ? getComputedStyle(grid).display : '',
        gridColumns: grid ? getComputedStyle(grid).gridTemplateColumns : '',
        copyRect: rect(copy),
        companionRect: rect(companion),
        tocCount: document.querySelectorAll('.playbook-toc').length,
        tocOpen: Boolean(toc?.open),
        tocSummaryHeight: rect(toc?.querySelector(':scope > summary'))?.height || 0,
        brokenTocLinks: tocLinks.filter((link) => !one(link.getAttribute('href'))).map((link) => link.getAttribute('href')),
        introCount: document.querySelectorAll('#intro').length,
        introTitle: introTitle?.textContent.trim() || '',
        introTitleLines: introTitle && titleStyle ? rect(introTitle).height / Number.parseFloat(titleStyle.lineHeight) : 0,
        introLead: one('#intro .lead')?.textContent.trim() || '',
      }};
    }

    const cards = [...document.querySelectorAll('.library-prompt-card')];
    const guide = one('.notebook-execution-guide');
    const guideGrid = one('.prompt-library-hero-grid');
    const firstSummary = one('.library-prompt-disclosure > summary');
    return {common, resource: {
      guideCount: document.querySelectorAll('[data-notebook-execution-guide]').length,
      guideTabs: document.querySelectorAll('.notebook-execution-guide [role="tab"]').length,
      guideOfficialLinks: [...document.querySelectorAll('.notebook-execution-guide a')]
        .filter((link) => /notebooklm\.google\.com|notebook\.google\.com/i.test(link.href)).length,
      uiFontToken: rootStyle.getPropertyValue('--font-ui').trim(),
      guideWidthRatio: guide && guideGrid ? rect(guide).width / rect(guideGrid).width : 0,
      secondaryMapCount: document.querySelectorAll('.prompt-library-secondary-map').length,
      secondaryMapOpen: Boolean(one('.prompt-library-secondary-map')?.open),
      cards: cards.length,
      openCards: cards.filter((card) => card.querySelector('.library-prompt-disclosure')?.open).length,
      firstSummaryHeight: rect(firstSummary)?.height || 0,
      hasList: document.querySelectorAll('.library-prompt-list').length,
      nested,
    }};
  }, {resource, nested});
}

function checkCommon(route, width, theme, state, baseline) {
  for (const [selector, actual] of Object.entries(state.shellCounts)) {
    if (actual !== 1) record('SHELL_COUNT', route, `${selector} expected=1 actual=${actual}`, width, theme);
  }
  if (!state.mainRect || state.mainRect.left < -1 || state.mainRect.right > width + 1 || state.mainRect.width < 1) {
    record('MAIN_BOUNDS', route, JSON.stringify(state.mainRect), width, theme);
  }
  if (state.pageOverflow > 1) record('PAGE_OVERFLOW', route, `overflow=${state.pageOverflow}`, width, theme);
  if (state.boxOverflow.length) record('COMPONENT_OVERFLOW', route, JSON.stringify(state.boxOverflow), width, theme);
  if (state.duplicateIds.length) record('DUPLICATE_IDS', route, state.duplicateIds.slice(0, 8).join(','), width, theme);
  if (width <= 390 && state.controlPairs.length) {
    record('MOBILE_CONTROL_COLLISION', route, state.controlPairs.join(','), width, theme);
  }
  if (width <= 390 && state.controlChrome.length) {
    record('MOBILE_CONTROL_HEADER_COLLISION', route, state.controlChrome.join(','), width, theme);
  }
  if (width <= 390 && state.controlContent.length) {
    record('MOBILE_CONTROL_OBSCURES_CONTENT', route, state.controlContent.join(','), width, theme);
  }
  if (baseline) {
    for (const token of ['head', 'body', 'gold', 'ink', 'mainFont', 'headingFont', 'headerBackground']) {
      if (state.tokens[token] !== baseline.tokens[token]) {
        record('BRAND_GRAMMAR', route, `${token} baseline=${baseline.tokens[token]} actual=${state.tokens[token]}`, width, theme);
      }
    }
  }
}

function checkResource(route, width, theme, resource, state, baseline, nested) {
  if (resource === 'masterclass') {
    if (state.officialCount !== 1 || state.pdfCount !== 1 || state.objectCount !== 1 || state.guideCount !== 1) {
      record('MASTERCLASS_STRUCTURE', route, JSON.stringify(state), width, theme);
    }
    if (!state.pdfBeforeGuide || (nested && !state.pdfBeforeStrip)) {
      record('MASTERCLASS_PDF_FIRST', route, `beforeStrip=${state.pdfBeforeStrip} beforeGuide=${state.pdfBeforeGuide}`, width, theme);
    }
    if (!state.pdfLocal) record('MASTERCLASS_REMOTE_PDF', route, 'PDF object must resolve locally', width, theme);
    if (state.pdfHeight < (width <= 390 ? 360 : 480)) {
      record('MASTERCLASS_PDF_VIEWPORT', route, `height=${state.pdfHeight}`, width, theme);
    }
    if (baseline && Math.abs(state.pdfWidthRatio - baseline.pdfWidthRatio) > 0.12) {
      record('MASTERCLASS_WIDTH_HOMOLOGY', route, `baseline=${baseline.pdfWidthRatio.toFixed(3)} actual=${state.pdfWidthRatio.toFixed(3)}`, width, theme);
    }
    return;
  }

  if (resource === 'workbook') {
    if (state.heroCount !== 1 || state.outcomeCount !== 1 || state.fields < 1 || state.visibleFields < 1) {
      record('WORKBOOK_STRUCTURE', route, JSON.stringify(state), width, theme);
    }
    if (state.unnamedFields) record('WORKBOOK_FIELD_NAME', route, `unnamed=${state.unnamedFields}`, width, theme);
    if (!state.firstField || state.firstField.width < Math.min(220, width * 0.62) || state.firstField.height < 64) {
      record('WORKBOOK_FIELD_GEOMETRY', route, JSON.stringify(state.firstField), width, theme);
    }
    if (state.printCount !== 1 || !state.printAction.includes('window.print')) {
      record('WORKBOOK_PRINT_CONTROL', route, `count=${state.printCount} action=${state.printAction}`, width, theme);
    }
    if (!state.printRect || state.printRect.width < 44 || state.printRect.height < 44) {
      record('WORKBOOK_PRINT_TARGET', route, JSON.stringify(state.printRect), width, theme);
    }
    if (state.tabCount !== 3 || state.selectedTabs !== 1) {
      record('WORKBOOK_TABS', route, `tabs=${state.tabCount} selected=${state.selectedTabs}`, width, theme);
    }
    const stageLabels = {
      es: ['En clase', 'Profundización', 'Consolidación'],
      en: ['In class', 'Deepening', 'Consolidation'],
      pt: ['Em aula', 'Aprofundamento', 'Consolidação'],
    }[state.locale] || [];
    if (stageLabels.some((label, index) => !state.tabTexts[index]?.includes(label))) {
      record('WORKBOOK_STAGE_LABELS', route, JSON.stringify(state.tabTexts), width, theme);
    }
    if (state.gateCount !== 1 || !state.gateInConsolidation || !state.rubricInConsolidation) {
      record('WORKBOOK_CONSOLIDATION_GATE', route, JSON.stringify({
        count: state.gateCount,
        inPanel: state.gateInConsolidation,
        rubric: state.rubricInConsolidation,
      }), width, theme);
    }
    if (nested && (
      state.stageIds.join('/') !== 'in-class/deepening/consolidation'
      || !state.transferInConsolidation
    )) {
      record('WORKBOOK_NESTED_CYCLE', route, JSON.stringify({
        stageIds: state.stageIds,
        transfer: state.transferInConsolidation,
      }), width, theme);
    }
    return;
  }

  if (resource === 'playbook') {
    if (state.gridCount !== 1 || state.gridDisplay !== 'grid' || !state.copyRect || !state.companionRect) {
      record('PLAYBOOK_HERO_GRID', route, JSON.stringify(state), width, theme);
    }
    if (state.copyRect && state.copyRect.width < Math.min(250, width * 0.6)) {
      record('PLAYBOOK_COPY_WIDTH', route, `width=${state.copyRect.width}`, width, theme);
    }
    const columns = state.gridColumns.trim().split(/\s+/).filter(Boolean).length;
    if ((width === 1440 && columns !== 2) || (width <= 768 && columns !== 1)) {
      record('PLAYBOOK_GRID_COLUMNS', route, `columns=${state.gridColumns}`, width, theme);
    }
    if (state.tocCount !== 1 || state.tocOpen || state.tocSummaryHeight < 44 || state.brokenTocLinks.length) {
      record('PLAYBOOK_TOC', route, `count=${state.tocCount} open=${state.tocOpen} height=${state.tocSummaryHeight} broken=${state.brokenTocLinks.join(',')}`, width, theme);
    }
    if (state.introCount !== 1 || !state.introLead || state.introTitle.length > 80 || state.introTitleLines > 3.1) {
      record('PLAYBOOK_INTRO', route, `count=${state.introCount} titleChars=${state.introTitle.length} lines=${state.introTitleLines.toFixed(2)} lead=${Boolean(state.introLead)}`, width, theme);
    }
    if (baseline && state.copyRect && baseline.copyRect && state.copyRect.width < baseline.copyRect.width * 0.66) {
      record('PLAYBOOK_GRID_HOMOLOGY', route, `baselineCopy=${baseline.copyRect.width} actualCopy=${state.copyRect.width}`, width, theme);
    }
    return;
  }

  if (state.guideCount !== 1 || state.guideTabs !== 2 || state.guideOfficialLinks < 1 || state.cards < 1 || state.hasList < 1) {
    record('PROMPTS_STRUCTURE', route, JSON.stringify(state), width, theme);
  }
  if (!state.uiFontToken) {
    record('PROMPTS_UI_FONT_TOKEN', route, '--font-ui is unresolved; prompt UI font shorthands fall back to inherited body sizing', width, theme);
  }
  if (nested && (state.secondaryMapCount !== 1 || state.secondaryMapOpen)) {
    record('PROMPTS_SECONDARY_MAP', route, `count=${state.secondaryMapCount} open=${state.secondaryMapOpen}`, width, theme);
  }
  if (!nested && state.secondaryMapCount !== 0) {
    record('PROMPTS_REFERENCE_MAP', route, `M1 unexpected secondary map count=${state.secondaryMapCount}`, width, theme);
  }
  if (state.openCards !== 0 || state.firstSummaryHeight < 44) {
    record('PROMPTS_CARD_DEFAULT', route, `open=${state.openCards} summaryHeight=${state.firstSummaryHeight}`, width, theme);
  }
  const compactSummaryLimit = width <= 390 ? 240 : (width <= 768 ? 200 : 140);
  if (state.firstSummaryHeight > compactSummaryLimit) {
    record('PROMPTS_CARD_DENSITY', route, `height=${state.firstSummaryHeight.toFixed(2)} limit=${compactSummaryLimit}`, width, theme);
  }
  if (baseline && state.guideWidthRatio < baseline.guideWidthRatio * 0.72) {
    record('PROMPTS_GUIDE_HOMOLOGY', route, `baseline=${baseline.guideWidthRatio.toFixed(3)} actual=${state.guideWidthRatio.toFixed(3)}`, width, theme);
  }
}

async function exercisePrompt(page, route, width, theme) {
  const firstCard = page.locator('.library-prompt-disclosure').first();
  await firstCard.evaluate((node) => { node.open = true; });
  const library = firstCard.locator('[data-prompt-library]');
  const before = await library.evaluate((node) => ({
    tabs: node.querySelectorAll('[role="tab"]').length,
    selected: node.querySelectorAll('[role="tab"][aria-selected="true"]').length,
    visiblePanels: [...node.querySelectorAll('pre[role="tabpanel"]')].filter((panel) => panel.checkVisibility()).length,
    copyButtons: node.querySelectorAll('[data-format-copy]').length,
  }));
  if (before.tabs !== 4 || before.selected !== 1 || before.visiblePanels !== 1 || before.copyButtons !== 1) {
    record('PROMPTS_TABS_INITIAL', route, JSON.stringify(before), width, theme);
  }
  // Exercise both the parameterized level and the longest SPEC projection.
  // The latter catches the mobile overflow that a collapsed card cannot show.
  await library.locator('[data-prompt-format]').nth(1).evaluate((node) => { node.click(); });
  await library.locator('[data-prompt-format]').nth(2).evaluate((node) => { node.click(); });
  await library.locator('[data-prompt-mode-select="demo"]').evaluate((node) => { node.click(); });
  const after = await library.evaluate((node) => {
    const selected = node.querySelector('[role="tab"][aria-selected="true"]');
    const controls = selected?.getAttribute('aria-controls') || '';
    const controlled = controls.split(/\s+/).filter(Boolean).map((id) => document.getElementById(id)).filter(Boolean);
    return {
      selectedIndex: [...node.querySelectorAll('[role="tab"]')].indexOf(selected),
      selectedTabs: node.querySelectorAll('[role="tab"][aria-selected="true"]').length,
      demoPressed: node.querySelectorAll('[data-prompt-mode-select="demo"][aria-pressed="true"]').length,
      visiblePanels: [...node.querySelectorAll('pre[role="tabpanel"]')].filter((panel) => panel.checkVisibility()).length,
      controlledVisible: controlled.filter((panel) => panel.checkVisibility()).length,
      controls,
      libraryOverflow: node.scrollWidth - node.clientWidth,
      panelOverflow: controlled.length === 1 ? controlled[0].scrollWidth - controlled[0].clientWidth : -1,
      pageOverflow: document.documentElement.scrollWidth - innerWidth,
    };
  });
  if (
    after.selectedIndex !== 2 || after.selectedTabs !== 1 || after.demoPressed !== 1
    || after.visiblePanels !== 1 || after.controlledVisible !== 1
  ) {
    record('PROMPTS_TAB_MODE_SEMANTICS', route, JSON.stringify(after), width, theme);
  }
  if (after.libraryOverflow > 1 || after.panelOverflow > 1 || after.pageOverflow > 1) {
    record('PROMPTS_SPEC_OVERFLOW', route, JSON.stringify(after), width, theme);
  }
}

async function exerciseWorkbookCycle(page, route, width, theme, nested) {
  for (const id of ['workbook-rubric', ...(nested ? ['transferencia'] : [])]) {
    await page.evaluate((targetId) => {
      location.hash = `#${targetId}`;
      return new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)));
    }, id);
    const state = await page.evaluate((targetId) => {
      const selected = document.querySelector('.sheet-tabs [role="tab"][aria-selected="true"]');
      const panel = document.querySelector('#sheet-consolidation');
      const target = document.getElementById(targetId);
      return {
        selected: selected?.getAttribute('aria-controls') || '',
        panelHidden: panel?.hidden ?? true,
        targetVisible: Boolean(target?.checkVisibility()),
      };
    }, id);
    if (state.selected !== 'sheet-consolidation' || state.panelHidden || !state.targetVisible) {
      record('WORKBOOK_DEEP_LINK', route, `${id}:${JSON.stringify(state)}`, width, theme);
    }
  }
}

async function exerciseMobileControlOcclusion(page, route, width, theme) {
  if (width > 390) return;
  const collisions = await page.evaluate(async () => {
    const findings = [];
    const seen = new Set();
    const maxScroll = Math.max(0, document.documentElement.scrollHeight - innerHeight);
    for (const fraction of [0, 0.25, 0.5, 0.75, 0.95, 1]) {
      window.scrollTo(0, Math.round(maxScroll * fraction));
      await new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)));
      for (const selector of ['.mdg-controls', '.intrapage-trigger']) {
        const control = document.querySelector(selector);
        if (!control?.checkVisibility()) continue;
        const bounds = control.getBoundingClientRect();
        for (let column = 1; column <= 5; column += 1) {
          for (let row = 1; row <= 5; row += 1) {
            const x = bounds.left + (bounds.width * column) / 6;
            const y = bounds.top + (bounds.height * row) / 6;
            const underlay = document.elementsFromPoint(x, y).find((node) =>
              !node.closest('.mdg-controls,.intrapage-trigger,.mdg-header,.intrapage-nav'),
            );
            const content = underlay?.closest(
              'main h1,main h2,main h3,main h4,main p,main li,main summary,main a,main button,main textarea,main code,main dt,main dd,main strong,main small,main span.eyebrow',
            );
            if (!content || content.matches('.sr-only') || content.closest('.sr-only')) continue;
            const finding = {
              fraction,
              control: selector,
              target: `${content.tagName.toLowerCase()}${content.id ? `#${content.id}` : ''}${content.className && typeof content.className === 'string' ? `.${content.className.trim().split(/\s+/).slice(0, 2).join('.')}` : ''}`,
              text: content.textContent.trim().replace(/\s+/g, ' ').slice(0, 72),
            };
            const key = `${finding.fraction}|${finding.control}|${finding.target}|${finding.text}`;
            if (seen.has(key)) continue;
            seen.add(key);
            findings.push(finding);
            if (findings.length >= 8) break;
          }
          if (findings.length >= 8) break;
        }
        if (findings.length >= 8) break;
      }
      if (findings.length >= 8) break;
    }
    window.scrollTo(0, 0);
    return findings;
  });
  if (collisions.length) {
    record('MOBILE_CONTROL_SCROLL_OCCLUSION', route, JSON.stringify(collisions), width, theme);
  }
}

for (const width of widths) {
  for (const theme of themes) {
    const context = await browser.newContext({viewport: {width, height: 960}, reducedMotion: 'reduce'});
    const baselines = {};
    for (const resource of resources) {
      const route = referenceRoutes[resource];
      const {page, runtimeErrors} = await openPage(context, route, theme);
      if (runtimeErrors.length) record('RUNTIME_ERROR', route, runtimeErrors.join(' | '), width, theme);
      const state = await snapshot(page, resource, false);
      checkCommon(route, width, theme, state.common, null);
      checkResource(route, width, theme, resource, state.resource, null, false);
      await exerciseMobileControlOcclusion(page, route, width, theme);
      if (resource === 'prompts') await exercisePrompt(page, route, width, theme);
      if (resource === 'workbook') await exerciseWorkbookCycle(page, route, width, theme, false);
      baselines[resource] = state;
      visualScenarios += 1;
      await page.close();
    }
    for (const {resource, route} of representativeRoutes) {
      const {page, runtimeErrors} = await openPage(context, route, theme);
      if (runtimeErrors.length) record('RUNTIME_ERROR', route, runtimeErrors.join(' | '), width, theme);
      const state = await snapshot(page, resource, true);
      checkCommon(route, width, theme, state.common, baselines[resource].common);
      checkResource(route, width, theme, resource, state.resource, baselines[resource].resource, true);
      await exerciseMobileControlOcclusion(page, route, width, theme);
      if (resource === 'prompts') await exercisePrompt(page, route, width, theme);
      if (resource === 'workbook') await exerciseWorkbookCycle(page, route, width, theme, true);
      visualScenarios += 1;
      await page.close();
    }
    await context.close();
  }
}

// Reader-facing prompt handoffs must name documents, not expose contract keys.
const promptRoutes = nestedRoutes.filter((route) => resourceFromRoute(route) === 'prompts');
const promptLabelContext = await browser.newContext({viewport: {width: 1440, height: 960}, reducedMotion: 'reduce'});
for (const route of promptRoutes) {
  const {page} = await openPage(promptLabelContext, route, 'light');
  const internal = await page.evaluate(() => {
    const machineKey = /\b(?:wb|pb|prompt)-[a-z0-9][a-z0-9-]*(?:-\d{2}|-output)\b|\b[A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+\b/i;
    return [...document.querySelectorAll('.prompt-flow code,.prompt-flow-gate,.library-prompt-brief dd')]
      .map((node) => node.textContent.trim())
      .filter((value) => machineKey.test(value))
      .filter((value, index, values) => values.indexOf(value) === index)
      .slice(0, 8);
  });
  if (internal.length) record('PROMPTS_INTERNAL_IDS', route, internal.join(' | '));
  await page.close();
}
await promptLabelContext.close();

// Print is a separate projection: the action disappears while writable fields remain.
const printContext = await browser.newContext({viewport: {width: 1440, height: 960}, reducedMotion: 'reduce'});
for (const route of [referenceRoutes.workbook, ...representativeRoutes.filter(({resource}) => resource === 'workbook').map(({route}) => route)]) {
  const {page} = await openPage(printContext, route, 'light');
  await page.emulateMedia({media: 'print'});
  const printState = await page.evaluate(() => ({
    printControlVisible: document.querySelector('.print-link')?.checkVisibility() || false,
    visibleFields: [...document.querySelectorAll('.field textarea')].filter((field) => field.checkVisibility()).length,
    mainVisible: document.querySelector('main#main')?.checkVisibility() || false,
  }));
  if (printState.printControlVisible || !printState.mainVisible || printState.visibleFields < 1) {
    record('WORKBOOK_PRINT_PROJECTION', route, JSON.stringify(printState));
  }
  await page.close();
}
await printContext.close();

// Native fallbacks remain useful when the progressive enhancement runtime is absent.
const noJsContext = await browser.newContext({
  viewport: {width: 390, height: 960},
  reducedMotion: 'reduce',
  javaScriptEnabled: false,
});
for (const resource of resources) {
  const route = `modulos/02-de-ocupado-a-productivo/${resource}/index.html`;
  const page = await noJsContext.newPage();
  await page.goto(pathToFileURL(resolve(dist, route)).href, {waitUntil: 'domcontentloaded'});
  const state = await page.evaluate((resource) => {
    const selectors = {
      masterclass: ['.official-pdf-object', '.masterclass-player'],
      workbook: ['.field textarea', '.workbook-sheets', '#sheet-consolidation [data-consolidation-gate]'],
      playbook: ['.playbook-toc > summary', '#intro'],
      prompts: ['.notebook-execution-guide', '.library-prompt-disclosure > summary'],
    }[resource];
    return selectors.map((selector) => ({
      selector,
      count: document.querySelectorAll(selector).length,
      visible: [...document.querySelectorAll(selector)].some((node) => node.checkVisibility()),
    }));
  }, resource);
  const broken = state.filter((item) => item.count < 1 || !item.visible);
  if (broken.length) record('NO_JS_ESSENTIAL_CONTENT', route, JSON.stringify(broken), 390, 'light');
  await page.close();
}
await noJsContext.close();

await browser.close();

if (failures.size) {
  const grouped = {};
  for (const failure of failures.values()) grouped[failure.code] = (grouped[failure.code] || 0) + 1;
  console.error(`[EVIDENCE:RESOURCE_VISUAL_HOMOLOGY] RESOURCE_VISUAL_HOMOLOGY_FAILED failures=${failures.size} scenarios=${visualScenarios} nested=${nestedRoutes.length}`);
  console.error(`FAILURE_COUNTS ${JSON.stringify(grouped)}`);
  for (const failure of [...failures.values()].slice(0, 160)) {
    console.error(`${failure.code}:${failure.width}:${failure.theme}:${failure.route}:${failure.detail}`);
  }
  if (failures.size > 160) console.error(`... ${failures.size - 160} additional failures omitted`);
  process.exitCode = 1;
} else {
  console.log(`[EVIDENCE:RESOURCE_VISUAL_HOMOLOGY] RESOURCE_VISUAL_HOMOLOGY_OK scenarios=${visualScenarios} nested=${nestedRoutes.length} matrix=${widths.join('/')}x${themes.join('/')} no_js=4 print=4`);
}
