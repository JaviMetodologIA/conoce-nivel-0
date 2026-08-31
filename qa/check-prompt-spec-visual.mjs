import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { pathToFileURL } from "node:url";

const root = path.resolve(import.meta.dirname, "..");
const dist = path.join(root, "dist");
const playwrightModule =
  process.env.PLAYWRIGHT_MODULE ||
  path.resolve(root, "..", "..", "frames-n0-kit-01", "node_modules", "playwright", "index.mjs");
const { chromium } = await import(pathToFileURL(playwrightModule));
const executablePath =
  process.env.CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const axePath =
  process.env.AXE_PATH ||
  "/Users/deonto/Library/pnpm/store/v11/links/@/axe-core/4.12.1/b7c50e7913b3703b5001a11d2efeed145f43557f7e102bc3785e95708dc85687/node_modules/axe-core/axe.min.js";
const axeSource = fs.readFileSync(axePath, "utf8");
const longToken = "SPECIFICITY_WITHOUT_BREAKS_".repeat(420);

function mutateServerHtml(html, resource) {
  const marker = resource === "prompts" ? '<article class="library-prompt-card"' : '<article class="brain-prompt-card"';
  const start = html.indexOf(marker);
  if (start < 0) return html;
  const before = html.slice(0, start);
  let candidate = html.slice(start);
  candidate = resource === "prompts"
    ? candidate.replace(/(<strong class="library-prompt-title">)[\s\S]*?(<\/strong>)/, `$1${longToken}$2`)
    : candidate.replace(/(<h3[^>]*>)[\s\S]*?(<\/h3>)/, `$1${longToken}$2`);
  candidate = candidate.replace(/(<pre class="prompt-format-panel"[^>]*>)[\s\S]*?(<\/pre>)/, `$1${longToken}$2`);
  if (resource === "prompts") {
    candidate = candidate.replace(/(<dd>)[\s\S]*?(<\/dd>)/, `$1${longToken}$2`);
    candidate = candidate.replace(/(<div class="prompt-limit-compact"><dt>[\s\S]*?<\/dt><dd>)[\s\S]*?(<\/dd>)/, `$1${longToken}$2`);
  } else {
    candidate = candidate.replace(/(<p>)[\s\S]*?(<\/p>)/, `$1${longToken}$2`);
    candidate = candidate.replace(/(<p class="prompt-limit-compact"><strong>[\s\S]*?<\/strong><span>)[\s\S]*?(<\/span>)/, `$1${longToken}$2`);
  }
  return before + candidate;
}

function serve() {
  const server = http.createServer((request, response) => {
    const url = new URL(request.url, "http://127.0.0.1");
    const relative = decodeURIComponent(url.pathname).replace(/^\/+/, "") || "index.html";
    const target = path.resolve(dist, relative.endsWith("/") ? `${relative}index.html` : relative);
    if (!target.startsWith(`${dist}${path.sep}`) || !fs.existsSync(target)) {
      response.writeHead(404);
      response.end("Not found");
      return;
    }
    const type = target.endsWith(".html")
      ? "text/html; charset=utf-8"
      : target.endsWith(".js")
        ? "text/javascript; charset=utf-8"
        : target.endsWith(".css")
          ? "text/css; charset=utf-8"
          : "application/octet-stream";
    response.writeHead(200, { "content-type": type, "cache-control": "no-store" });
    if (target.endsWith(".html") && url.searchParams.get("mutation") === "long") {
      const resource = url.pathname.includes("/workbook/") ? "workbook" : "prompts";
      response.end(mutateServerHtml(fs.readFileSync(target, "utf8"), resource));
    } else fs.createReadStream(target).pipe(response);
  });
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => resolve(server));
  });
}

function route(locale, audience, resource) {
  const parts = [];
  if (locale !== "es") parts.push(locale);
  if (audience === "empresa") parts.push("empresa");
  parts.push(resource);
  return `${parts.join("/")}/`;
}

async function overflowState(page) {
  return page.evaluate(() => {
    const viewport = document.documentElement.clientWidth;
    const pageOverflow = Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - viewport;
    const roots = [...document.querySelectorAll(".library-prompt-card, .brain-prompt-card, .step")];
    const nodes = [...new Set(roots.flatMap((root) => [root, ...root.querySelectorAll("*")]))]
      .filter((node) => node instanceof HTMLElement && !node.classList.contains("sr-only") && node.getClientRects().length && node.clientWidth > 0);
    const offenders = nodes
      .flatMap((node) => {
        const box = node.getBoundingClientRect();
        const horizontal = box.left < -1 || box.right > viewport + 1;
        const internal = node.scrollWidth - node.clientWidth > 2;
        const mayScroll = node.matches(".prompt-format-panel") && getComputedStyle(node).overflowX === "auto";
        return horizontal || (internal && !mayScroll)
          ? [{
              tag: node.tagName.toLowerCase(),
              selector: node.className,
              parent: node.parentElement?.className,
              root: node.closest(".library-prompt-card, .brain-prompt-card, .step")?.className,
              text: node.textContent?.trim().replace(/\s+/g, " ").slice(0, 72),
              left: box.left,
              right: box.right,
              width: box.width,
              viewport,
              internal,
              mayScroll,
            }]
          : [];
      });
    return { pageOverflow, offenders };
  });
}

const server = await serve();
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true, executablePath });
let states = 0;
let keyboardChecks = 0;
let copyChecks = 0;
let modeChecks = 0;
let variantModeChecks = 0;
let noJsChecks = 0;
let zoomChecks = 0;
let axeChecks = 0;
let mutationChecks = 0;
let whyChecks = 0;
try {
  if (process.env.PROMPT_VISUAL_SCOPE !== "mode") {
  for (const locale of ["es", "en", "pt"])
    for (const audience of ["persona", "empresa"])
      for (const resource of ["prompts", "workbook"])
        for (const theme of ["light", "dark"])
          for (const view of [
            { width: 320, label: "320" },
            { width: 390, label: "390" },
            { width: 768, label: "768" },
            { width: 1440, label: "1440" },
            { width: 720, label: "1440@200%", zoom: 2 },
          ]) {
        const { width } = view;
        const context = await browser.newContext({ viewport: { width, height: 900 } });
        await context.grantPermissions(["clipboard-read", "clipboard-write"], { origin });
        const page = await context.newPage();
        const errors = [];
        page.on("pageerror", (error) => errors.push(error.message));
        page.on("console", (message) => message.type() === "error" && errors.push(message.text()));
        const response = await page.goto(`${origin}/${route(locale, audience, resource)}`, { waitUntil: "load" });
        if (!response?.ok()) throw new Error(`PROMPT_ROUTE_FAILED:${locale}:${audience}:${resource}:${view.label}`);
        if (theme === "dark") await page.locator("[data-mdg-theme]").click();
        if (resource === "prompts") {
          const heroContract = await page.evaluate(() => {
            const hero = document.querySelector(".prompt-library-hero");
            const copy = hero?.querySelector(".prompt-library-hero-copy");
            const title = hero?.querySelector("h1");
            const guide = hero?.querySelector("[data-notebook-execution-guide]");
            const tabs = [...(guide?.querySelectorAll("[data-notebook-tab]") || [])];
            const panels = [...(guide?.querySelectorAll("[data-notebook-panel]") || [])];
            const box = (node) => node?.getBoundingClientRect();
            const heroBox = box(hero);
            const copyBox = box(copy);
            const titleBox = box(title);
            const guideBox = box(guide);
            return {
              tabs: tabs.length,
              panels: panels.length,
              selectedTabs: tabs.filter((node) => node.getAttribute("aria-selected") === "true").length,
              visiblePanels: panels.filter((node) => !node.hidden).length,
              titleText: title?.textContent?.trim(),
              heroOverflow: document.documentElement.scrollWidth > innerWidth + 2,
              titleOverflow: Boolean(title && (title.scrollWidth > title.clientWidth + 2 || title.scrollHeight > title.clientHeight + 16) && getComputedStyle(title).overflow !== "visible"),
              guideOverflow: Boolean(guide && guide.scrollWidth > guide.clientWidth + 2),
              tabTargets: tabs.map((node) => box(node)?.height || 0),
              horizontal: Boolean(copyBox && guideBox && guideBox.left > copyBox.right),
              stacked: Boolean(copyBox && guideBox && guideBox.top > copyBox.bottom),
              guideTop: guideBox?.top,
              heroRight: heroBox?.right,
              guideRight: guideBox?.right,
              titleHeight: titleBox?.height,
            };
          });
          if (
            heroContract.tabs !== 2 ||
            heroContract.panels !== 2 ||
            heroContract.selectedTabs !== 1 ||
            heroContract.visiblePanels !== 1 ||
            !heroContract.titleText ||
            heroContract.heroOverflow ||
            heroContract.titleOverflow ||
            heroContract.guideOverflow ||
            heroContract.tabTargets.some((height) => height < 44) ||
            (width > 1050 && !heroContract.horizontal) ||
            (width <= 1050 && !heroContract.stacked) ||
            heroContract.guideRight > width + 1
          ) throw new Error(`PROMPT_HERO_CONTRACT:${locale}:${audience}:${theme}:${view.label}:${JSON.stringify(heroContract)}`);

          await page.locator('[data-notebook-tab="source_search"]').click();
          const tabState = await page.evaluate(() => ({
            selected: document.querySelector('[data-notebook-tab="source_search"]')?.getAttribute("aria-selected"),
            chatHidden: document.querySelector('[data-notebook-panel="chat"]')?.hidden,
            searchHidden: document.querySelector('[data-notebook-panel="source_search"]')?.hidden,
          }));
          if (tabState.selected !== "true" || !tabState.chatHidden || tabState.searchHidden)
            throw new Error(`NOTEBOOK_TAB_STATE:${locale}:${audience}:${theme}:${view.label}:${JSON.stringify(tabState)}`);
          const firstDisclosure = page.locator("[data-prompt-card-disclosure]").first();
          if (!(await firstDisclosure.evaluate((node) => node.open))) await firstDisclosure.locator(":scope > summary").click();
        }
        await page.locator('[data-prompt-format="spec"]').evaluateAll((tabs) => tabs.forEach((tab) => tab.click()));
        const panels = page.locator('[id$="-spec"][data-prompt-template]:not([hidden])');
        const expectedPanels = resource === "prompts" ? 14 : 13;
        if ((await panels.count()) !== expectedPanels) throw new Error(`PROMPT_SPEC_VISIBLE_COUNT:${locale}:${audience}:${resource}:${view.label}`);
        // The rationale panel ships open for the rest of this state so the
        // overflow, axe and long-token mutation checks below all see it.
        await page.locator("[data-prompt-why]").evaluateAll((panels) => panels.forEach((panel) => { panel.open = true; }));
        const whyContract = await page.evaluate((expectedPanels) => {
          const panels = [...document.querySelectorAll("[data-prompt-why]")];
          const compactLimits = [...document.querySelectorAll(".prompt-limit-compact")];
          return {
            panels: panels.length,
            expectedPanels,
            compactLimits: compactLimits.length,
            compactLimitsPopulated: compactLimits.every((node) => {
              const label = node.querySelector("dt, strong");
              const value = node.querySelector("dd, span");
              return Boolean(label?.textContent?.trim() && value?.textContent?.trim());
            }),
            summaries: panels.filter((panel) => panel.querySelector("summary")?.textContent?.trim()).length,
            sections: panels.map((panel) => panel.querySelectorAll(".prompt-why-body > section").length),
            populated: panels.every((panel) => [...panel.querySelectorAll(".prompt-why-body > section")]
              .every((section) => section.querySelector("h4")?.textContent?.trim() && section.querySelectorAll("li").length)),
            clipped: panels.some((panel) => {
              const body = panel.querySelector(".prompt-why-body");
              return Boolean(body && body.scrollHeight > body.clientHeight + 2 && getComputedStyle(body).overflowY !== "visible");
            }),
          };
        }, expectedPanels);
        if (
          whyContract.panels !== expectedPanels ||
          whyContract.compactLimits !== expectedPanels ||
          !whyContract.compactLimitsPopulated ||
          whyContract.summaries !== expectedPanels ||
          whyContract.sections.some((count) => count !== 5) ||
          !whyContract.populated ||
          whyContract.clipped
        ) throw new Error(`PROMPT_WHY_CONTRACT:${locale}:${audience}:${resource}:${theme}:${view.label}:${JSON.stringify(whyContract)}`);
        whyChecks += 1;

        const overflow = await overflowState(page);
        if (overflow.pageOverflow > 2 || overflow.offenders.length || errors.length)
          throw new Error(`PROMPT_OVERFLOW:${locale}:${audience}:${resource}:${theme}:${view.label}:${JSON.stringify({ overflow, errors })}`);

        await page.addScriptTag({ content: axeSource });
        const axe = await page.evaluate(async (resource) => {
          const roots = [document.querySelector(resource === "prompts" ? ".library-prompt-card" : ".brain-prompt-card")];
          if (resource === "prompts") roots.push(document.querySelector(".prompt-library-hero"));
          const violations = [];
          for (const root of roots) {
            const result = await window.axe.run(root, { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa"] } });
            violations.push(...result.violations.map((item) => ({
              id: item.id,
              impact: item.impact,
              nodes: item.nodes.map((node) => ({ target: node.target, html: node.html.slice(0, 180) })),
            })));
          }
          return violations;
        }, resource);
        if (axe.length) throw new Error(`PROMPT_AXE:${locale}:${audience}:${resource}:${theme}:${view.label}:${JSON.stringify(axe)}`);
        axeChecks += 1;

        const uiContract = await page.evaluate((resource) => {
          const card = document.querySelector(resource === "prompts" ? ".library-prompt-card" : ".brain-prompt-card");
          const library = card?.querySelector("[data-prompt-library]");
          const tabs = [...(library?.querySelectorAll("[data-prompt-format]") || [])];
          const mode = library?.dataset.activeMode || "template";
          const activeLevel = library?.querySelector('details[data-prompt-level][open]');
          const panel = activeLevel?.querySelector(mode === "demo" ? "[data-prompt-demo]" : "[data-prompt-template]");
          const context = panel?.closest("details")?.querySelector(".prompt-level-context");
          const cardBox = card?.getBoundingClientRect();
          const libraryBox = library?.getBoundingClientRect();
          return {
            activeLevel: library?.dataset.activeLevel,
            activeFormat: library?.dataset.activeFormat,
            cardLevel: card?.dataset.promptActiveLevel,
            tabNames: tabs.map((tab) => tab.querySelector("strong")?.textContent?.trim()),
            tabLabels: tabs.map((tab) => tab.getAttribute("aria-label")),
            tabOverflow: tabs.some((tab) => tab.scrollWidth > tab.clientWidth + 2),
            panelClipped: Boolean(panel && panel.scrollHeight > panel.clientHeight + 2 && getComputedStyle(panel).overflowY !== "visible"),
            contextVisible: Boolean(context && context.getClientRects().length && context.querySelector("p")?.textContent?.trim()),
            sections: panel?.querySelectorAll(".prompt-line-section").length || 0,
            lineCount: panel?.querySelectorAll(".prompt-line").length || 0,
            expandedRatio: cardBox && libraryBox ? libraryBox.width / cardBox.width : 0,
          };
        }, resource);
        if (
          uiContract.activeLevel !== "3" ||
          uiContract.activeFormat !== "spec" ||
          uiContract.cardLevel !== "3" ||
          uiContract.tabNames.some((name) => !name) ||
          uiContract.tabLabels.some((label) => !label?.includes(" · ")) ||
          uiContract.tabOverflow ||
          uiContract.panelClipped ||
          !uiContract.contextVisible ||
          uiContract.sections < 4 ||
          uiContract.lineCount < 20 ||
          (resource === "prompts" && width >= 768 && uiContract.expandedRatio < 0.55)
        ) throw new Error(`PROMPT_UI_CONTRACT:${locale}:${audience}:${resource}:${theme}:${view.label}:${JSON.stringify(uiContract)}`);

        if (resource === "prompts" && width === 390 && theme === "light") {
          const disclosures = page.locator("[data-prompt-card-disclosure]");
          await disclosures.nth(1).locator(":scope > summary").click();
          await page.waitForTimeout(40);
          const accordionState = await disclosures.evaluateAll((nodes) => nodes.slice(0, 2).map((node) => node.open));
          if (accordionState[0] || !accordionState[1])
            throw new Error(`PROMPT_ACCORDION:${locale}:${audience}:${JSON.stringify(accordionState)}`);
          await disclosures.first().locator(":scope > summary").click();
          for (const [surface, expected] of [["source_search", 2], ["chat", 8], ["all", 10]]) {
            await page.locator(`[data-prompt-surface-filter="${surface}"]`).click();
            const visible = await page.locator("#directos [data-library-prompt]:visible").count();
            if (visible !== expected) throw new Error(`PROMPT_SURFACE_FILTER:${locale}:${audience}:${surface}:${visible}`);
          }
          const sourceTab = page.locator('[data-notebook-tab="source_search"]');
          await sourceTab.focus();
          await page.keyboard.press("Home");
          const chatTab = page.locator('[data-notebook-tab="chat"]');
          if ((await chatTab.getAttribute("aria-selected")) !== "true" || !(await chatTab.evaluate((node) => node === document.activeElement)))
            throw new Error(`NOTEBOOK_TAB_KEYBOARD:${locale}:${audience}`);
        }

        await page.evaluate(({ resource, longToken }) => {
          const root = document.querySelector(resource === "prompts" ? ".library-prompt-card" : ".brain-prompt-card");
          const brief = resource === "prompts" ? root?.querySelector("dd") : document.querySelector(".step p");
          const library = root?.querySelector("[data-prompt-library]");
          const activeLevel = library?.querySelector('details[data-prompt-level][open]');
          const targets = [root?.querySelector(resource === "prompts" ? ".library-prompt-title" : "h3"), brief, activeLevel?.querySelector("[data-prompt-template]"), root?.querySelector("[data-prompt-why] li")];
          targets.forEach((node) => { if (node) node.textContent = longToken; });
        }, { resource, longToken });
        const mutatedOverflow = await overflowState(page);
        if (mutatedOverflow.pageOverflow > 2 || mutatedOverflow.offenders.length)
          throw new Error(`PROMPT_MUTATION_OVERFLOW:${locale}:${audience}:${resource}:${theme}:${view.label}:${JSON.stringify(mutatedOverflow)}`);
        mutationChecks += 1;

        if (width === 390 && theme === "light") {
          if (resource === "prompts") {
            const disclosure = page.locator("[data-prompt-card-disclosure]").first();
            if (!(await disclosure.evaluate((node) => node.open))) await disclosure.locator(":scope > summary").click();
          }
          const firstLibrary = page.locator("[data-prompt-library]:has([data-format-copy])").first();
          for (const [level, key] of ["natural", "parameters", "spec", "pair"].entries()) {
            const tab = firstLibrary.locator(`[data-prompt-format="${key}"]`);
            await tab.click();
            const levelState = await firstLibrary.evaluate((library, expected) => {
              const mode = library.dataset.activeMode || "template";
              const activeLevel = library.querySelector('details[data-prompt-level][open]');
              const panel = activeLevel?.querySelector(mode === "demo" ? "[data-prompt-demo]" : "[data-prompt-template]");
              const source = activeLevel?.querySelector(`[data-prompt-source][data-prompt-mode="${mode}"]`);
              const context = panel?.closest("details")?.querySelector(".prompt-level-context");
              return {
                activeLevel: library.dataset.activeLevel,
                activeFormat: library.dataset.activeFormat,
                cardLevel: library.closest(".library-prompt-card,.brain-prompt-card,.step")?.dataset.promptActiveLevel,
                panelClass: panel?.className,
                sourceLength: source?.value.length || 0,
                context: context?.textContent?.trim(),
                clipped: Boolean(panel && panel.scrollHeight > panel.clientHeight + 2 && getComputedStyle(panel).overflowY !== "visible"),
                expected,
              };
            }, { number: String(level + 1), key });
            if (
              levelState.activeLevel !== String(level + 1) ||
              levelState.activeFormat !== key ||
              levelState.cardLevel !== String(level + 1) ||
              !levelState.panelClass?.includes(`prompt-format-panel-${key}`) ||
              !levelState.sourceLength ||
              !levelState.context ||
              levelState.clipped
            ) throw new Error(`PROMPT_LEVEL_UI:${locale}:${audience}:${resource}:${key}:${JSON.stringify(levelState)}`);
          }
          const natural = firstLibrary.locator('[data-prompt-format="natural"]');
          await natural.focus();
          await page.keyboard.press("End");
          const pair = firstLibrary.locator('[data-prompt-format="pair"]');
          if ((await pair.getAttribute("aria-selected")) !== "true" || !(await pair.evaluate((node) => node === document.activeElement)))
            throw new Error(`PROMPT_KEYBOARD_END:${locale}:${audience}:${resource}`);
          await page.keyboard.press("ArrowLeft");
          const spec = firstLibrary.locator('[data-prompt-format="spec"]');
          if ((await spec.getAttribute("aria-selected")) !== "true" || !(await spec.evaluate((node) => node === document.activeElement)))
            throw new Error(`PROMPT_KEYBOARD_SPEC:${locale}:${audience}:${resource}`);
          keyboardChecks += 1;

          const copy = firstLibrary.locator("[data-format-copy]");
          await copy.click();
          const expected = await firstLibrary.locator('[data-prompt-level="3"] [data-prompt-source][data-prompt-mode="template"]').inputValue();
          const copied = await page.evaluate(() => navigator.clipboard.readText());
          if (copied !== expected || !(await copy.getAttribute("aria-label"))?.includes("✓")) {
            const status = await firstLibrary.locator(".prompt-copy-status").textContent();
            if (copied !== expected || !status?.trim()) throw new Error(`PROMPT_COPY:${locale}:${audience}:${resource}`);
          }
          copyChecks += 1;

          await firstLibrary.locator('[data-prompt-mode-select="demo"]').click();
          const demoState = await page.evaluate(() => ({
            modes: [...document.querySelectorAll("[data-prompt-library]")].map((node) => node.dataset.activeMode),
            query: location.search,
            unresolved: [...document.querySelectorAll('[data-prompt-source][data-prompt-mode="demo"]')]
              .filter((node) => /<[^>]+>|\{\{|\}\}|\[[^\]]+\]/.test(node.value)).length,
          }));
          await copy.click();
          const expectedDemo = await firstLibrary.locator('[data-prompt-level="3"] [data-prompt-source][data-prompt-mode="demo"]').inputValue();
          const copiedDemo = await page.evaluate(() => navigator.clipboard.readText());
          if (
            demoState.modes.some((mode) => mode !== "demo") ||
            !demoState.query.includes("mode=demo") ||
            demoState.unresolved ||
            copiedDemo !== expectedDemo
          ) throw new Error(`PROMPT_DEMO_MODE:${locale}:${audience}:${resource}:${JSON.stringify(demoState)}`);
          await firstLibrary.locator('[data-prompt-mode-select="template"]').click();
          const templateReset = await page.evaluate(() => ({
            modes: [...document.querySelectorAll("[data-prompt-library]")].map((node) => node.dataset.activeMode),
            query: location.search,
          }));
          if (templateReset.modes.some((mode) => mode !== "template") || templateReset.query.includes("mode="))
            throw new Error(`PROMPT_TEMPLATE_RESET:${locale}:${audience}:${resource}:${JSON.stringify(templateReset)}`);
          modeChecks += 1;
        }
        states += 1;
        if (view.zoom === 2) zoomChecks += 1;
        await context.close();
      }
  }

  {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
    const page = await context.newPage();
    await page.goto(`${origin}/prompts/#prompt-01`, { waitUntil: "load" });
    await page.locator("[data-prompt-library] [data-prompt-mode-select=demo]").first().click();
    for (const [selector, path] of [
      ['[data-mdg-locale="en"]', "/en/prompts/index.html"],
      ['[data-mdg-audience="empresa"]', "/en/empresa/prompts/index.html"],
      ['[data-mdg-locale="pt"]', "/pt/empresa/prompts/index.html"],
      ['[data-mdg-audience="persona"]', "/pt/prompts/index.html"],
    ]) {
      await Promise.all([page.waitForNavigation({ waitUntil: "load" }), page.locator(selector).click()]);
      const state = await page.evaluate(() => ({
        path: location.pathname,
        search: location.search,
        hash: location.hash,
        modes: [...document.querySelectorAll("[data-prompt-library]")].map((node) => node.dataset.activeMode),
      }));
      if (
        state.path !== path ||
        state.search !== "?mode=demo" ||
        state.hash !== "#prompt-01" ||
        state.modes.some((mode) => mode !== "demo")
      ) throw new Error(`PROMPT_MODE_VARIANT:${selector}:${JSON.stringify(state)}`);
      variantModeChecks += 1;
    }
    await context.close();
  }

  if (process.env.PROMPT_VISUAL_SCOPE !== "mode") {
  for (const locale of ["es", "en", "pt"])
    for (const audience of ["persona", "empresa"])
      for (const resource of ["prompts", "workbook"]) {
      const context = await browser.newContext({ viewport: { width: 320, height: 900 }, javaScriptEnabled: false });
      const page = await context.newPage();
      await page.goto(`${origin}/${route(locale, audience, resource)}?mutation=long`, { waitUntil: "load" });
      if (resource === "prompts") await page.locator("[data-prompt-card-disclosure] > summary").first().click();
      const summaries = page.locator(".prompt-level-fallback > summary");
      const specPanels = page.locator('[id$="-spec"][data-prompt-template]');
      const sources = page.locator("[data-prompt-source]");
      const demoDisclosures = page.locator(".prompt-demo-native");
      const whyPanels = page.locator("[data-prompt-why]");
      const expectedPanels = resource === "prompts" ? 14 : 13;
      if (
        (await whyPanels.count()) !== expectedPanels ||
        (await summaries.count()) !== expectedPanels * 4 ||
        (await specPanels.count()) !== expectedPanels ||
        (await sources.count()) !== expectedPanels * 8 ||
        (await demoDisclosures.count()) !== expectedPanels * 4 ||
        !(await summaries.nth(2).textContent())?.includes(locale === "es" ? "Especificado" : locale === "en" ? "Specified" : "Especificado")
      )
        throw new Error(`PROMPT_NO_JS_STRUCTURE:${locale}:${audience}:${resource}`);
      await summaries.nth(2).click();
      if (!(await page.locator(".prompt-level-fallback").nth(2).evaluate((node) => node.open)))
        throw new Error(`PROMPT_NO_JS_DISCLOSURE:${locale}:${audience}:${resource}`);
      await whyPanels.evaluateAll((panels) => panels.forEach((panel) => { panel.open = true; }));
      if (!(await whyPanels.first().evaluate((node) => node.open && node.querySelectorAll(".prompt-why-body > section li").length > 0)))
        throw new Error(`PROMPT_NO_JS_WHY:${locale}:${audience}:${resource}`);
      const overflow = await overflowState(page);
      if (overflow.pageOverflow > 2 || overflow.offenders.length)
        throw new Error(`PROMPT_NO_JS_OVERFLOW:${locale}:${audience}:${resource}:${JSON.stringify(overflow)}`);
      noJsChecks += 1;
      await context.close();
    }
  }
} finally {
  await browser.close();
  server.close();
  server.closeAllConnections?.();
}

console.log(`PROMPT_SPEC_VISUAL_OK states=${states} zoom_200=${zoomChecks} axe=${axeChecks} mutations=${mutationChecks} why=${whyChecks} keyboard=${keyboardChecks} copy=${copyChecks} modes=${modeChecks} variant_modes=${variantModeChecks} no_js=${noJsChecks}`);
