import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, resolve, sep } from "node:path";
import { pathToFileURL } from "node:url";

const root = resolve(import.meta.dirname, "..");
const dist = resolve(root, "dist");
const playwrightModule =
  process.env.PLAYWRIGHT_MODULE ||
  resolve(
    root,
    "..",
    "..",
    "frames-n0-kit-01",
    "node_modules",
    "playwright",
    "index.mjs",
  );
const { chromium } = await import(pathToFileURL(playwrightModule));

const mime = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".jpg": "image/jpeg",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".ttf": "font/ttf",
  ".webp": "image/webp",
  ".woff2": "font/woff2",
};

const server = createServer(async (request, response) => {
  try {
    const pathname = decodeURIComponent(
      new URL(request.url, "http://local.test").pathname,
    );
    const candidate = resolve(
      dist,
      `.${pathname.endsWith("/") ? `${pathname}index.html` : pathname}`,
    );
    if (candidate !== dist && !candidate.startsWith(`${dist}${sep}`))
      throw new Error("PATH_OUTSIDE_DIST");
    const bytes = await readFile(candidate);
    response.writeHead(200, {
      "content-type": mime[extname(candidate)] || "application/octet-stream",
    });
    response.end(bytes);
  } catch {
    response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
    response.end("Not found");
  }
});
await new Promise((accept) => server.listen(0, "127.0.0.1", accept));
const address = server.address();
const origin = `http://127.0.0.1:${address.port}`;

const locales = ["es", "en", "pt"];
const audiences = ["persona", "empresa"];
const resources = ["landing", "workbook", "playbook", "prompts", "deck"];
const themes = ["light", "dark"];
const widths = [320, 390, 768, 1440];
const expectedMarks = {
  landing: 2,
  workbook: 0,
  playbook: 4,
  prompts: 1,
  deck: 0,
};
const expectedAlt = {
  es: "A²(R)E — Aprender, Aprehender, (R)Evolucionar",
  en: "A²(R)E — Learn, Apprehend, (R)Evolve",
  pt: "A²(R)E — Aprender, Apreender, (R)Evolucionar",
};

function route(locale, audience, resource) {
  const parts = [];
  if (locale !== "es") parts.push(locale);
  if (audience === "empresa") parts.push("empresa");
  if (resource !== "landing") parts.push(resource);
  return `${parts.join("/")}${parts.length ? "/" : ""}`;
}

const browser = await chromium.launch({
  headless: true,
  executablePath:
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});
let states = 0;
let marks = 0;
try {
  for (const locale of locales)
    for (const audience of audiences)
      for (const resource of resources) {
        for (const theme of themes)
          for (const width of widths) {
            const context = await browser.newContext({
              viewport: { width, height: 900 },
              colorScheme: theme,
            });
            const page = await context.newPage();
            const errors = [];
            const externalRequests = [];
            page.on(
              "console",
              (message) =>
                message.type() === "error" && errors.push(message.text()),
            );
            page.on("pageerror", (error) => errors.push(error.message));
            page.on("request", (request) => {
              const url = new URL(request.url());
              if (url.origin !== origin) externalRequests.push(request.url());
            });
            const currentRoute = route(locale, audience, resource);
            const response = await page.goto(`${origin}/${currentRoute}`, {
              waitUntil: "load",
            });
            if (!response?.ok())
              throw new Error(
                `ROUTE_FAILED ${currentRoute} ${response?.status()}`,
              );
            if (theme === "dark") {
              await page.locator("[data-mdg-theme]").click();
              await page.waitForTimeout(300);
            }
            await page
              .locator("[data-method-mark]")
              .evaluateAll(async (nodes) => {
                for (const node of nodes) {
                  node.loading = "eager";
                  node.scrollIntoView({ block: "center" });
                  await node.decode();
                }
              });
            await page.waitForTimeout(30);
            const result = await page.evaluate(
              ({
                locale,
                audience,
                resource,
                theme,
                expectedCount,
                expectedAlt,
              }) => {
                const intersects = (a, b) =>
                  a.left < b.right - 1 &&
                  a.right > b.left + 1 &&
                  a.top < b.bottom - 1 &&
                  a.bottom > b.top + 1;
                const rect = (node) => {
                  const value = node.getBoundingClientRect();
                  return {
                    left: value.left,
                    right: value.right,
                    top: value.top,
                    bottom: value.bottom,
                    width: value.width,
                    height: value.height,
                  };
                };
                const marks = [
                  ...document.querySelectorAll("[data-method-mark]"),
                ];
                const collisionPairs = [
                  [
                    ".cover-method-mark",
                    ".playbook-cover h3, .playbook-cover p, .playbook-cover strong, .playbook-cover .cover-type",
                  ],
                  [
                    ".open-skill-mark",
                    ".open-skill-card .eyebrow, .open-skill-card h3, .open-skill-card p, .open-skill-card strong, .open-skill-meta",
                  ],
                  [".playbook-primary-mark", ".playbook-hero-copy"],
                  [".playbook-fact-mark", ".playbook-hero-facts dd"],
                  [
                    ".playbook-close-lockup",
                    ".playbook-close h2, .playbook-close p, .playbook-close .actions",
                  ],
                  [
                    ".prompt-method-mark",
                    ".prompt-library-score > strong, .prompt-library-score > span",
                  ],
                ];
                const collisions = [];
                for (const [markSelector, peerSelector] of collisionPairs) {
                  const mark = document.querySelector(markSelector);
                  if (!mark) continue;
                  for (const peer of document.querySelectorAll(peerSelector)) {
                    if (intersects(rect(mark), rect(peer)))
                      collisions.push(`${markSelector}:${peerSelector}`);
                  }
                }
                const markProblems = marks.flatMap((mark) => {
                  const box = rect(mark);
                  const variant = mark.dataset.methodMark;
                  const minimum = variant === "primary" ? 64 : 40;
                  const decorative =
                    mark.getAttribute("aria-hidden") === "true";
                  const expectedFile =
                    variant === "primary"
                      ? "method-a2re-primary.svg"
                      : "method-a2re-compact.svg";
                  const problems = [];
                  if (
                    !mark.complete ||
                    mark.naturalWidth < 1 ||
                    mark.naturalHeight < 1
                  )
                    problems.push("not-decoded");
                  if (!mark.currentSrc.endsWith(expectedFile))
                    problems.push("wrong-source");
                  if (box.width < minimum || box.height < 1)
                    problems.push("below-minimum");
                  if (box.left < -1 || box.right > innerWidth + 1)
                    problems.push("horizontal-clipping");
                  if (decorative ? mark.alt !== "" : mark.alt !== expectedAlt)
                    problems.push("accessible-name");
                  return problems.map((problem) => `${variant}:${problem}`);
                });
                const storageKeys = Object.keys(localStorage);
                const controls = [
                  ...document.querySelectorAll(".mdg-control"),
                ].map((control) => rect(control));
                return {
                  language: document.documentElement.lang,
                  audience: document.documentElement.dataset.audience,
                  theme: document.documentElement.dataset.theme,
                  overflow: document.documentElement.scrollWidth - innerWidth,
                  markCount: marks.length,
                  expectedCount,
                  markProblems,
                  collisions,
                  controls: controls.length,
                  undersizedControls: controls.filter(
                    (box) => box.width < 44 || box.height < 44,
                  ).length,
                  storageKeys,
                  stale: document.body.textContent.includes(`A\u00b3`),
                  resource,
                };
              },
              {
                locale,
                audience,
                resource,
                theme,
                expectedCount: expectedMarks[resource],
                expectedAlt: expectedAlt[locale],
              },
            );
            const allowedStorage = new Set([
              "mdg_theme",
              "mdg_locale",
              "mdg_audience",
            ]);
            const unexpectedStorage = result.storageKeys.filter(
              (key) => !allowedStorage.has(key),
            );
            if (
              result.language !== locale ||
              result.audience !== audience ||
              result.theme !== theme ||
              result.overflow !== 0 ||
              result.markCount !== result.expectedCount ||
              result.markProblems.length ||
              result.collisions.length ||
              result.controls !== 3 ||
              result.undersizedControls ||
              result.stale ||
              unexpectedStorage.length ||
              errors.length ||
              externalRequests.length
            ) {
              throw new Error(
                `VISUAL_MATRIX_FAILED ${JSON.stringify({ currentRoute, width, ...result, unexpectedStorage, errors, externalRequests })}`,
              );
            }
            states += 1;
            marks += result.markCount;
            await context.close();
          }
      }
  console.log(
    `A2RE_VISUAL_PASS states=${states} rendered_marks=${marks} external_requests=0`,
  );
} finally {
  await browser.close();
  await new Promise((accept) => server.close(accept));
}
