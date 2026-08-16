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
  candidate = candidate.replace(/(<h3[^>]*>)[\s\S]*?(<\/h3>)/, `$1${longToken}$2`);
  candidate = candidate.replace(/(<pre class="prompt-format-panel"[^>]*>)[\s\S]*?(<\/pre>)/, `$1${longToken}$2`);
  if (resource === "prompts") candidate = candidate.replace(/(<dd>)[\s\S]*?(<\/dd>)/, `$1${longToken}$2`);
  else candidate = candidate.replace(/(<p>)[\s\S]*?(<\/p>)/, `$1${longToken}$2`);
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
          ? [{ selector: node.className, left: box.left, right: box.right, width: box.width, viewport, internal, mayScroll }]
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
let noJsChecks = 0;
let zoomChecks = 0;
let axeChecks = 0;
let mutationChecks = 0;
try {
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
        await page.locator('[data-prompt-format="spec"]').evaluateAll((tabs) => tabs.forEach((tab) => tab.click()));
        const panels = page.locator('[id$="-spec"][data-prompt-template]:not([hidden])');
        const expectedPanels = resource === "prompts" ? 14 : 13;
        if ((await panels.count()) !== expectedPanels) throw new Error(`PROMPT_SPEC_VISIBLE_COUNT:${locale}:${audience}:${resource}:${view.label}`);
        const overflow = await overflowState(page);
        if (overflow.pageOverflow > 2 || overflow.offenders.length || errors.length)
          throw new Error(`PROMPT_OVERFLOW:${locale}:${audience}:${resource}:${theme}:${view.label}:${JSON.stringify({ overflow, errors })}`);

        await page.addScriptTag({ content: axeSource });
        const axe = await page.evaluate(async (resource) => {
          const root = document.querySelector(resource === "prompts" ? ".library-prompt-card" : ".brain-prompt-card");
          const result = await window.axe.run(root, { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa"] } });
          return result.violations.map((item) => ({ id: item.id, impact: item.impact, nodes: item.nodes.length }));
        }, resource);
        if (axe.length) throw new Error(`PROMPT_AXE:${locale}:${audience}:${resource}:${theme}:${view.label}:${JSON.stringify(axe)}`);
        axeChecks += 1;

        await page.evaluate(({ resource, longToken }) => {
          const root = document.querySelector(resource === "prompts" ? ".library-prompt-card" : ".brain-prompt-card");
          const brief = resource === "prompts" ? root?.querySelector("dd") : document.querySelector(".step p");
          const targets = [root?.querySelector("h3"), brief, root?.querySelector(".prompt-format-panel:not([hidden])")];
          targets.forEach((node) => { if (node) node.textContent = longToken; });
        }, { resource, longToken });
        const mutatedOverflow = await overflowState(page);
        if (mutatedOverflow.pageOverflow > 2 || mutatedOverflow.offenders.length)
          throw new Error(`PROMPT_MUTATION_OVERFLOW:${locale}:${audience}:${resource}:${theme}:${view.label}:${JSON.stringify(mutatedOverflow)}`);
        mutationChecks += 1;

        if (width === 390 && theme === "light") {
          const firstLibrary = page.locator("[data-prompt-library]:has([data-format-copy])").first();
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
          const expected = await firstLibrary.locator('[id$="-spec"][data-prompt-template]').textContent();
          const copied = await page.evaluate(() => navigator.clipboard.readText());
          if (copied !== expected || !(await copy.getAttribute("aria-label"))?.includes("✓")) {
            const status = await firstLibrary.locator(".prompt-copy-status").textContent();
            if (copied !== expected || !status?.trim()) throw new Error(`PROMPT_COPY:${locale}:${audience}:${resource}`);
          }
          copyChecks += 1;
        }
        states += 1;
        if (view.zoom === 2) zoomChecks += 1;
        await context.close();
      }

  for (const locale of ["es", "en", "pt"])
    for (const audience of ["persona", "empresa"])
      for (const resource of ["prompts", "workbook"]) {
      const context = await browser.newContext({ viewport: { width: 320, height: 900 }, javaScriptEnabled: false });
      const page = await context.newPage();
      await page.goto(`${origin}/${route(locale, audience, resource)}?mutation=long`, { waitUntil: "load" });
      const summaries = page.locator(".prompt-level-fallback > summary");
      const specPanels = page.locator('[id$="-spec"][data-prompt-template]');
      const expectedPanels = resource === "prompts" ? 14 : 13;
      if ((await summaries.count()) !== expectedPanels * 4 || (await specPanels.count()) !== expectedPanels)
        throw new Error(`PROMPT_NO_JS_STRUCTURE:${locale}:${audience}:${resource}`);
      await summaries.nth(2).click();
      if (!(await page.locator(".prompt-level-fallback").nth(2).evaluate((node) => node.open)))
        throw new Error(`PROMPT_NO_JS_DISCLOSURE:${locale}:${audience}:${resource}`);
      const overflow = await overflowState(page);
      if (overflow.pageOverflow > 2 || overflow.offenders.length)
        throw new Error(`PROMPT_NO_JS_OVERFLOW:${locale}:${audience}:${resource}:${JSON.stringify(overflow)}`);
      noJsChecks += 1;
      await context.close();
    }
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}

console.log(`PROMPT_SPEC_VISUAL_OK states=${states} zoom_200=${zoomChecks} axe=${axeChecks} mutations=${mutationChecks} keyboard=${keyboardChecks} copy=${copyChecks} no_js=${noJsChecks}`);
