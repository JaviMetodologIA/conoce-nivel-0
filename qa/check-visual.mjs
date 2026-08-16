import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const root = resolve(import.meta.dirname, "..");
const qaRoot = process.env.QA_SCREENSHOT_ROOT
  ? resolve(process.env.QA_SCREENSHOT_ROOT)
  : resolve(root, "qa");
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
const local = (route = "") => pathToFileURL(resolve(root, "dist", route)).href;

const browser = await chromium.launch({
  headless: true,
  executablePath:
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});
const routes = [
  "index.html",
  "workbook/index.html",
  "playbook/index.html",
  "prompts/index.html",
  "deck/index.html",
  "en/index.html",
  "en/workbook/index.html",
  "en/playbook/index.html",
  "en/prompts/index.html",
  "en/deck/index.html",
  "pt/index.html",
  "pt/workbook/index.html",
  "pt/playbook/index.html",
  "pt/prompts/index.html",
  "pt/deck/index.html",
];
const landingSections = [
  "entrada",
  "tension",
  "ruta",
  "demostracion",
  "experiencia",
  "resultados",
  "metodo",
  "convocatoria",
];
for (const route of routes) {
  const width = 390;
  const page = await browser.newPage({ viewport: { width, height: 844 } });
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(local(route));
  await page.waitForLoadState("load");
  await page.waitForTimeout(50);
  const data = await page.evaluate(() => ({
    stylesheets: [...document.styleSheets].map((sheet) => sheet.href),
    background: getComputedStyle(document.body).backgroundColor,
    font: getComputedStyle(document.body).fontFamily,
    overflow: document.documentElement.scrollWidth - window.innerWidth,
    logo: document.querySelector(".mark")?.getAttribute("src"),
    styledCards: getComputedStyle(
      document.querySelector(
        ".card, .slide, .tension-card, .pdf-sheet img, .founders-letter, .library-prompt-card",
      ),
    ).borderRadius,
    sections: [
      ...document.querySelectorAll("main.landing-v2 > section.chapter"),
    ].map((section) => section.id),
  }));
  const verboseActions = await page.evaluate(() =>
    [
      ...document.querySelectorAll(
        ".btn, .text-link, .official-link, .pdf-download, .access-card strong, .video-cover strong, .open-skill-card strong, .print-link",
      ),
    ]
      .map((node) => node.textContent.trim().replace(/\s+/g, " "))
      .filter((label) => label && label.split(/\s+/).length > 3),
  );
  if (verboseActions.length)
    throw new Error(
      `VERBOSE_ACTIONS_FAILED ${route}: ${JSON.stringify(verboseActions)}`,
    );
  if (
    route.endsWith("index.html") &&
    !route.includes("workbook") &&
    !route.includes("playbook") &&
    !route.includes("prompts") &&
    !route.includes("masterclass") &&
    !route.includes("deck")
  ) {
    if (JSON.stringify(data.sections) !== JSON.stringify(landingSections)) {
      throw new Error(
        `LANDING_SECTIONS_FAILED ${route}: ${JSON.stringify(data.sections)}`,
      );
    }
    const featuredLinks = await page.locator(".resource-cover[href]").count();
    const featuredVideos = await page
      .locator('.video-cover[href*="youtube.com/watch"]')
      .count();
    if (featuredLinks !== 3 || featuredVideos !== 2)
      throw new Error(
        `FEATURED_VIDEO_STATE_FAILED ${route}: ${JSON.stringify({ featuredLinks, featuredVideos })}`,
      );
    const openSkills = await page
      .locator(
        '.open-skill-card[href="https://github.com/JaviMontano/material-educativo-metodologia/tree/main/skills/aprender-aprehender-revolucionar"]',
      )
      .count();
    if (openSkills !== 1)
      throw new Error(`OPEN_SKILL_STATE_FAILED ${route}: ${openSkills}`);
    const catalogState = await page.evaluate(() => ({
      classes: document.querySelectorAll(".catalog-class").length,
      resources: document.querySelectorAll(".catalog-resource").length,
      available: document.querySelectorAll(".catalog-resource.available[href]")
        .length,
      pendingLinks: document.querySelectorAll(".catalog-resource.pending[href]")
        .length,
      paths: document.querySelectorAll(".catalog-resource .resource-path")
        .length,
      titled: [
        ...document.querySelectorAll(".catalog-resource > strong"),
      ].filter((node) => node.textContent.trim()).length,
    }));
    if (
      catalogState.classes !== 4 ||
      catalogState.resources !== 16 ||
      catalogState.available !== 4 ||
      catalogState.pendingLinks !== 0 ||
      catalogState.paths !== 16 ||
      catalogState.titled !== 16
    ) {
      throw new Error(
        `RESOURCE_CATALOG_FAILED ${route}: ${JSON.stringify(catalogState)}`,
      );
    }
    const editorialLetters = await page.locator(".letter-card").count();
    if (editorialLetters !== 2)
      throw new Error(`EDITORIAL_LETTERS_FAILED ${route}: ${editorialLetters}`);
    const storyParts = {
      hooks: await page.locator(".route-hook").count(),
      takeaways: await page.locator(".route-takeaway").count(),
      punchlines: await page.locator(".route-punchline").count(),
    };
    if (Object.values(storyParts).some((count) => count !== 4)) {
      throw new Error(
        `SESSION_STORY_FAILED ${route}: ${JSON.stringify(storyParts)}`,
      );
    }
    const publicCopy = (await page.locator("body").innerText()).toLowerCase();
    const locale = route.startsWith("en/")
      ? "en"
      : route.startsWith("pt/")
        ? "pt"
        : "es";
    const monthlyIntake = {
      es: [
        "1 convocatoria al mes · primera semana",
        "una convocatoria al mes · primera semana",
      ],
      en: ["1 monthly intake · first week", "one monthly intake · first week"],
      pt: [
        "1 turma por mês · primeira semana",
        "uma turma por mês · primeira semana",
      ],
    }[locale];
    const metaDescription = await page
      .locator('meta[name="description"]')
      .getAttribute("content");
    if (
      !monthlyIntake.every((copy) => publicCopy.includes(copy)) ||
      !/una convocatoria|one intake|uma turma/i.test(metaDescription || "")
    ) {
      throw new Error(
        `MONTHLY_INTAKE_COPY_FAILED ${route}: ${JSON.stringify({ monthlyIntake, metaDescription })}`,
      );
    }
    if (
      /dos convocatorias|two calls|duas chamadas|2 convocatorias|2 calls|2 chamadas/i.test(
        `${publicCopy} ${metaDescription}`,
      )
    ) {
      throw new Error(`STALE_DUAL_INTAKE_COPY ${route}`);
    }
    if (/\bbluf\b|\bbluff\b/.test(publicCopy)) {
      throw new Error(`INTERNAL_EDITORIAL_LABEL_EXPOSED ${route}`);
    }
    const n0Principles = await page.locator(".n0-principle").count();
    const n0Labels = await page.locator(".n0-principle span").allTextContents();
    const n0Values = await page
      .locator(".n0-principle strong")
      .allTextContents();
    const n0Caption = await page.locator(".n0-caption").textContent();
    if (
      n0Principles !== 3 ||
      n0Labels.some((label) => !label.trim()) ||
      JSON.stringify(n0Values) !== JSON.stringify(["0", "0", "0"]) ||
      !/triple|triplo/i.test(n0Caption || "")
    ) {
      throw new Error(
        `N0_PROMISE_FAILED ${route}: ${JSON.stringify({ n0Principles, n0Labels, n0Values, n0Caption })}`,
      );
    }
    if (/riesgo cero|zero risk|risco zero/.test(publicCopy.toLowerCase())) {
      throw new Error(`UNSUPPORTED_ZERO_RISK_CLAIM ${route}`);
    }
    const exposedDecorativeNumbers = await page
      .locator(
        '.route-number:not([aria-hidden="true"]), .outcome-num:not([aria-hidden="true"])',
      )
      .count();
    if (exposedDecorativeNumbers)
      throw new Error(`DECORATIVE_NUMBER_EXPOSED ${route}`);
  }
  if (route.includes("workbook")) {
    const tableRegion = page.locator(".table-wrap");
    if (
      (await tableRegion.getAttribute("tabindex")) !== "0" ||
      (await tableRegion.getAttribute("role")) !== "region"
    ) {
      throw new Error(`SCROLLABLE_TABLE_NOT_FOCUSABLE ${route}`);
    }
    const workbookState = await page.evaluate(() => ({
      heroes: document.querySelectorAll(".workbook-hero").length,
      accessCards: document.querySelectorAll(".access-card[href]").length,
      routes: document.querySelectorAll(".route-choice-grid > article").length,
      preparation: document.querySelectorAll(".prep-card").length,
      concepts: document.querySelectorAll(".concept-grid > article").length,
      expertSteps: document.querySelectorAll(".expert-steps > li").length,
      tabs: document.querySelectorAll('.sheet-tabs [role="tab"]').length,
      steps: document.querySelectorAll(".step").length,
      writingSurfaces: document.querySelectorAll(
        ".workbook-sheets .field textarea",
      ).length,
      guideSteps: document.querySelectorAll(".guide-steps > li").length,
      providerLinks: document.querySelectorAll(".provider-notice a[href]")
        .length,
      brainInputs: document.querySelectorAll("[data-brain-dump]").length,
      brainPrompts: document.querySelectorAll(".brain-prompt-card").length,
      brainFormats: document.querySelectorAll(
        ".brain-prompt-card .prompt-format-panel",
      ).length,
      workshopFormats: document.querySelectorAll(
        ".workbook-sheets .prompt-format-panel",
      ).length,
      promptLibraries: document.querySelectorAll("[data-prompt-library]")
        .length,
      useCases: document.querySelectorAll(".use-cases li").length,
      foreignBrand: /amaris/i.test(document.body.innerText),
    }));
    if (
      workbookState.heroes !== 1 ||
      workbookState.accessCards !== 3 ||
      workbookState.routes !== 3 ||
      workbookState.preparation !== 3 ||
      workbookState.concepts !== 2 ||
      workbookState.expertSteps !== 10 ||
      workbookState.tabs !== 3 ||
      workbookState.steps !== 10 ||
      workbookState.writingSurfaces !== 5 ||
      workbookState.guideSteps !== 5 ||
      workbookState.providerLinks !== 4 ||
      workbookState.brainInputs !== 1 ||
      workbookState.brainPrompts !== 3 ||
      workbookState.brainFormats !== 12 ||
      workbookState.workshopFormats !== 40 ||
      workbookState.promptLibraries !== 13 ||
      workbookState.useCases !== 7 ||
      workbookState.foreignBrand
    ) {
      throw new Error(
        `WORKBOOK_STRUCTURE_FAILED ${route}: ${JSON.stringify(workbookState)}`,
      );
    }
    if ((await page.locator(".breadcrumbs li").count()) !== 3)
      throw new Error(`WORKBOOK_BREADCRUMB_FAILED ${route}`);
  }
  if (route.includes("playbook")) {
    const playbookState = await page.evaluate(() => ({
      sections: document.querySelectorAll("[data-playbook-section]").length,
      founders: document.querySelectorAll(".founders-letter li").length,
      founderPhotos: document.querySelectorAll(
        '.founders-letter img[src^="../assets/"], .founders-letter img[src^="../../assets/"]',
      ).length,
      founderAlts: new Set(
        [...document.querySelectorAll(".founders-letter img")].map((image) =>
          image.alt.trim(),
        ),
      ).size,
      founderSquares: [
        ...document.querySelectorAll(".founders-letter img"),
      ].every(
        (image) =>
          Math.abs(
            image.getBoundingClientRect().width -
              image.getBoundingClientRect().height,
          ) < 1,
      ),
      assistants: document.querySelectorAll(
        '.playbook-assistant[data-custom-gpt][href^="https://chatgpt.com/g/"]',
      ).length,
      assistantTargets: [
        ...document.querySelectorAll(".playbook-assistant"),
      ].every(
        (link) =>
          link.target === "_blank" &&
          link.rel.split(/\s+/).includes("noopener") &&
          link.rel.split(/\s+/).includes("noreferrer"),
      ),
      prompts: document.querySelectorAll(".playbook-prompt[href]").length,
      toc: document.querySelectorAll(".playbook-toc a[href]").length,
      close: document.querySelectorAll(".playbook-close").length,
      skill: [...document.querySelectorAll("a[href]")].filter((link) =>
        link.href.includes("material-educativo-metodologia"),
      ).length,
      foreignBrand: /amaris/i.test(document.body.innerText),
    }));
    if (
      playbookState.sections !== 19 ||
      playbookState.founders !== 4 ||
      playbookState.founderPhotos !== 4 ||
      playbookState.founderAlts !== 4 ||
      !playbookState.founderSquares ||
      playbookState.assistants !== 3 ||
      !playbookState.assistantTargets ||
      playbookState.prompts !== 14 ||
      playbookState.toc !== 22 ||
      playbookState.close !== 1 ||
      playbookState.skill < 1 ||
      playbookState.foreignBrand
    ) {
      throw new Error(
        `PLAYBOOK_STRUCTURE_FAILED ${route}: ${JSON.stringify(playbookState)}`,
      );
    }
    if ((await page.locator(".breadcrumbs li").count()) !== 3)
      throw new Error(`PLAYBOOK_BREADCRUMB_FAILED ${route}`);
  }
  if (route.includes("prompts")) {
    const promptState = await page.evaluate(() => ({
      prompts: document.querySelectorAll("[data-library-prompt]").length,
      direct: document.querySelectorAll('[data-prompt-kind="direct"]').length,
      meta: document.querySelectorAll('[data-prompt-kind="meta"]').length,
      libraries: document.querySelectorAll("[data-prompt-library]").length,
      levels: document.querySelectorAll("[data-prompt-format]").length,
      panels: document.querySelectorAll(".prompt-format-panel").length,
      copies: document.querySelectorAll(".prompt-format-copy svg").length,
      examples: document.querySelectorAll(".library-prompt-brief").length,
      duplicateIds: [...document.querySelectorAll("[id]")]
        .map((x) => x.id)
        .filter((id, i, all) => all.indexOf(id) !== i),
      foreignBrand: /amaris/i.test(document.body.innerText),
    }));
    if (
      promptState.prompts !== 14 ||
      promptState.direct !== 10 ||
      promptState.meta !== 4 ||
      promptState.libraries !== 14 ||
      promptState.levels !== 56 ||
      promptState.panels !== 56 ||
      promptState.copies !== 14 ||
      promptState.examples !== 14 ||
      promptState.duplicateIds.length ||
      promptState.foreignBrand
    ) {
      throw new Error(
        `PROMPT_LIBRARY_FAILED ${route}: ${JSON.stringify(promptState)}`,
      );
    }
    if ((await page.locator(".breadcrumbs li").count()) !== 3)
      throw new Error(`PROMPT_LIBRARY_BREADCRUMB_FAILED ${route}`);
  }
  if (route.includes("deck")) {
    const deckState = await page.evaluate(() => ({
      locale: document.documentElement.lang,
      player: Boolean(document.querySelector(".masterclass-player")),
      title: document.querySelector(".masterclass-player-head h2")?.textContent.trim(),
      officialPdf: document.querySelector(".official-pdf-object")?.getAttribute("data"),
      officialHash: document.querySelector("[data-official-masterclass]")?.getAttribute("data-official-masterclass-sha256"),
      pages: document.querySelectorAll(".slide").length,
      indexItems: document.querySelectorAll("[data-slide]").length,
      phases: document.querySelectorAll(".outline-group").length,
      current: document.querySelector(".slide.active")?.id,
      currentStep: document
        .querySelector('[data-slide][aria-current="step"]')
        ?.getAttribute("data-slide"),
      progressRole: document
        .querySelector(".deck-controls .progress")
        ?.getAttribute("role"),
      facilitatorNotes: document.querySelectorAll(".fac-note").length,
      workbookLinks: document.querySelectorAll(
        'a[href*="workbook/index.html#step-"]',
      ).length,
      prev: Boolean(document.querySelector("[data-prev]")),
      next: Boolean(document.querySelector("[data-next]")),
      continuation: document
        .querySelector('.slide#slide-18 a[href*="youtube.com"]')
        ?.getAttribute("href"),
      duplicatedSelfLinks: document.querySelectorAll(
        '.slide a[href^="../deck/index.html"]',
      ).length,
      durationLabel: document
        .querySelector(".deck-mode-group")
        ?.getAttribute("aria-label"),
      modeLabels: [...document.querySelectorAll(".deck-mode")].map((button) =>
        button.getAttribute("aria-label"),
      ),
    }));
    const expectedModes = {
      es: {
        group: "Duración de la guía",
        buttons: ["Ruta base · 90 min", "Con práctica extendida · 120 min"],
      },
      en: {
        group: "Guide duration",
        buttons: ["Core route · 90 min", "With extended practice · 120 min"],
      },
      pt: {
        group: "Duração da guia",
        buttons: ["Rota base · 90 min", "Com prática estendida · 120 min"],
      },
    }[deckState.locale];
    if (
      deckState.player !== true ||
      !deckState.title ||
      !deckState.officialPdf?.includes("assets/masterclass-ia-nivel-0.pdf") ||
      deckState.officialHash !== "5df5533a29652184f492b2f797ecfa0f1fa47cdb682bfcefb8f30c96014ce402" ||
      deckState.pages !== 18 ||
      deckState.indexItems !== 18 ||
      deckState.phases !== 3 ||
      deckState.current !== "slide-1" ||
      deckState.currentStep !== "0" ||
      deckState.progressRole !== "progressbar" ||
      deckState.facilitatorNotes !== 18 ||
      deckState.workbookLinks !== 5 ||
      deckState.prev !== true ||
      deckState.next !== true ||
      deckState.duplicatedSelfLinks !== 0 ||
      deckState.durationLabel !== expectedModes?.group ||
      JSON.stringify(deckState.modeLabels) !==
        JSON.stringify(expectedModes?.buttons) ||
      !deckState.continuation?.includes("youtube.com")
    ) {
      throw new Error(
        `DECK_VIEWER_FAILED ${route}: ${JSON.stringify(deckState)}`,
      );
    }
  }
  if (
    route === "index.html" ||
    route === "workbook/index.html" ||
    route === "playbook/index.html" ||
    route === "prompts/index.html" ||
    route === "deck/index.html"
  ) {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.screenshot({
      path: resolve(qaRoot, `${route.replaceAll("/", "-")}.png`),
      fullPage: true,
    });
  }
  if (
    data.stylesheets.length < 2 ||
    data.background === "rgba(0, 0, 0, 0)" ||
    data.styledCards === "0px" ||
    data.overflow !== 0 ||
    errors.length
  ) {
    throw new Error(JSON.stringify({ route, width, data, errors }));
  }
  console.log(JSON.stringify({ route, width, ...data, errors }));
  await page.close();
}
for (const route of [
  "playbook/index.html",
  "en/playbook/index.html",
  "pt/playbook/index.html",
]) {
  for (const width of [320, 390, 768, 1440]) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    await page.goto(local(route));
    await page.waitForLoadState("load");
    const foundersLayout = await page.evaluate(() => {
      const founder = document.querySelector(".founders-letter");
      const copy = document.querySelector(".founders-letter-copy");
      const title = document.querySelector(".founders-letter h2");
      const cards = [...document.querySelectorAll(".founders-letter li")];
      const intersects = (a, b) =>
        a.left < b.right &&
        a.right > b.left &&
        a.top < b.bottom &&
        a.bottom > b.top;
      const titleBox = title.getBoundingClientRect();
      const copyBox = copy.getBoundingClientRect();
      const cardBoxes = cards.map((card) => card.getBoundingClientRect());
      return {
        documentOverflow: document.documentElement.scrollWidth - innerWidth,
        sectionOverflow: founder.scrollWidth - founder.clientWidth,
        titleOverflow: title.scrollWidth - title.clientWidth,
        titleCardCollisions: cardBoxes.filter((box) =>
          intersects(titleBox, box),
        ).length,
        copyCardCollisions: cardBoxes.filter((box) => intersects(copyBox, box))
          .length,
        mobileDecorativeLabelVisible:
          innerWidth <= 600 &&
          getComputedStyle(founder, "::before").display !== "none"
            ? 1
            : 0,
      };
    });
    if (Object.values(foundersLayout).some((value) => value !== 0)) {
      throw new Error(
        `PLAYBOOK_FOUNDERS_LAYOUT_FAILED ${route}@${width}: ${JSON.stringify(foundersLayout)}`,
      );
    }
    await page.close();
  }
}
const desktop = await browser.newPage({
  viewport: { width: 1440, height: 900 },
});
await desktop.emulateMedia({ reducedMotion: "reduce" });
await desktop.goto(local("index.html"));
await desktop.screenshot({
  path: resolve(qaRoot, "landing-1440.png"),
  fullPage: true,
});
const desktopMetrics = await desktop.evaluate(() => ({
  overflow: document.documentElement.scrollWidth - window.innerWidth,
  font: getComputedStyle(document.body).fontFamily,
}));
if (desktopMetrics.overflow !== 0)
  throw new Error(JSON.stringify(desktopMetrics));
console.log(
  JSON.stringify({ route: "index.html", width: 1440, ...desktopMetrics }),
);
await desktop.close();
const workbookDesktop = await browser.newPage({
  viewport: { width: 1440, height: 900 },
});
await workbookDesktop.emulateMedia({ reducedMotion: "reduce" });
await workbookDesktop.goto(local("workbook/index.html"));
await workbookDesktop.screenshot({
  path: resolve(qaRoot, "workbook-1440.png"),
  fullPage: true,
});
await workbookDesktop.close();
for (const width of [320, 360, 390, 430, 768, 1024, 1280, 1440, 1920]) {
  const page = await browser.newPage({ viewport: { width, height: 900 } });
  await page.goto(local("index.html"));
  const state = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - innerWidth,
    sections: document.querySelectorAll("main.landing-v2 > section.chapter")
      .length,
    hiddenReveals: [...document.querySelectorAll(".reveal")].filter(
      (element) => getComputedStyle(element).opacity === "0",
    ).length,
    shellWidth: document.querySelector(".shell")?.getBoundingClientRect().width,
    heroSize: Number.parseFloat(
      getComputedStyle(document.querySelector(".hero-title")).fontSize,
    ),
  }));
  if (state.overflow !== 0 || state.sections !== 8)
    throw new Error(JSON.stringify({ width, state }));
  if (width <= 430 && (state.shellWidth > width - 28 || state.heroSize > 55)) {
    throw new Error(
      `MOBILE_PROPORTION_FAILED: ${JSON.stringify({ width, state })}`,
    );
  }
  if (width === 320 || width === 390) {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.screenshot({
      path: resolve(qaRoot, `landing-${width}.png`),
      fullPage: true,
    });
  }
  console.log(JSON.stringify({ landingViewport: width, ...state }));
  await page.close();
}
for (const localeRoute of ["index.html", "en/index.html", "pt/index.html"]) {
  for (const [width, height] of [
    [1280, 650],
    [1366, 768],
    [1440, 900],
    [1486, 738],
    [1536, 864],
    [1728, 1080],
  ]) {
    const page = await browser.newPage({ viewport: { width, height } });
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto(local(localeRoute));
    const heroFit = await page.evaluate(() => {
      const header = document
        .querySelector(".mdg-header")
        .getBoundingClientRect();
      const hero = document.querySelector(".hero-v2").getBoundingClientRect();
      const offer = document
        .querySelector(".offer-strip")
        .getBoundingClientRect();
      return {
        headerBottom: header.bottom,
        heroBottom: hero.bottom,
        offerBottom: offer.bottom,
        viewportBottom: innerHeight,
        titleSize: Number.parseFloat(
          getComputedStyle(document.querySelector(".hero-title")).fontSize,
        ),
      };
    });
    if (heroFit.heroBottom > height + 1 || heroFit.offerBottom > height + 1) {
      throw new Error(
        `HERO_ABOVE_FOLD_FAILED: ${JSON.stringify({ localeRoute, width, height, heroFit })}`,
      );
    }
    if (localeRoute === "index.html" && width === 1486 && height === 738) {
      await page.screenshot({
        path: resolve(qaRoot, "hero-1486x738.png"),
        fullPage: false,
      });
    }
    console.log(
      JSON.stringify({
        heroRoute: localeRoute,
        heroViewport: `${width}x${height}`,
        ...heroFit,
      }),
    );
    await page.close();
  }
}
const interaction = await browser.newPage({
  viewport: { width: 390, height: 844 },
});
await interaction.goto(`${local("index.html")}#experiencia`);
const compactControlSizes = await interaction
  .locator(".mdg-control")
  .evaluateAll((elements) =>
    elements.map((element) => ({
      label: element.getAttribute("aria-label") || element.textContent.trim(),
      width: element.getBoundingClientRect().width,
      height: element.getBoundingClientRect().height,
    })),
  );
if (compactControlSizes.some(({ width, height }) => width < 44 || height < 44)) {
  throw new Error(
    `COMPACT_TARGET_FAILED: ${JSON.stringify(compactControlSizes)}`,
  );
}
const themeBefore = await interaction
  .locator("html")
  .getAttribute("data-theme");
await interaction.click("button[data-mdg-theme]");
if (
  (await interaction.locator("html").getAttribute("data-theme")) === themeBefore
) {
  throw new Error("THEME_TOGGLE_FAILED");
}
if (
  (await interaction
    .locator("button[data-mdg-theme]")
    .getAttribute("aria-checked")) !== "true"
) {
  throw new Error("THEME_TOGGLE_STATE_FAILED");
}
await interaction.click('[data-mdg-locale="en"]');
await interaction.waitForLoadState("load");
if (
  !interaction.url().includes("/dist/en/") ||
  !interaction.url().endsWith("#experiencia")
) {
  throw new Error(`LOCALE_ROUTE_FAILED: ${interaction.url()}`);
}
await interaction.click(
  '.catalog-resource.available[href="workbook/index.html"]',
);
await interaction.waitForLoadState("load");
if (!interaction.url().includes("/dist/en/workbook/")) {
  throw new Error(`RESOURCE_ROUTE_FAILED: ${interaction.url()}`);
}
console.log(
  JSON.stringify({ interaction: "theme-language-resource", status: "PASS" }),
);
await interaction.close();
const landingInteraction = await browser.newPage({
  viewport: { width: 390, height: 844 },
});
await landingInteraction.goto(`${local("index.html")}#tension`);
const beforeStorage = await landingInteraction.evaluate(() => ({
  local: { ...localStorage },
  session: { ...sessionStorage },
}));
await landingInteraction.click("[data-tension]");
if (
  (await landingInteraction
    .locator('[data-tension][aria-pressed="true"]')
    .count()) !== 1
) {
  throw new Error("TENSION_SELECTOR_FAILED");
}
const afterStorage = await landingInteraction.evaluate(() => ({
  local: { ...localStorage },
  session: { ...sessionStorage },
}));
if (JSON.stringify(beforeStorage) !== JSON.stringify(afterStorage))
  throw new Error("TENSION_PERSISTENCE_FORBIDDEN");
await landingInteraction.emulateMedia({ reducedMotion: "reduce" });
const reducedHidden = await landingInteraction.evaluate(
  () =>
    [...document.querySelectorAll(".reveal")].filter(
      (element) => getComputedStyle(element).opacity === "0",
    ).length,
);
if (reducedHidden !== 0)
  throw new Error(`REDUCED_MOTION_HIDDEN_CONTENT: ${reducedHidden}`);
console.log(
  JSON.stringify({
    interaction: "tension-reduced-motion-no-persistence",
    status: "PASS",
  }),
);
await landingInteraction.close();
const brainInteraction = await browser.newPage({
  viewport: { width: 390, height: 844 },
});
await brainInteraction.goto(local("workbook/index.html"));
const brainStorageBefore = await brainInteraction.evaluate(() => ({
  local: { ...localStorage },
  session: { ...sessionStorage },
}));
await brainInteraction.evaluate(() => {
  navigator.clipboard.writeText = async (text) => {
    window.__copiedBrainPrompt = text;
  };
});
const levelContract = await brainInteraction.evaluate(() => ({
  guides: document.querySelectorAll(".prompt-level-guide").length,
  libraries: document.querySelectorAll("[data-prompt-library]").length,
  levels: [...document.querySelectorAll("[data-prompt-library]")].map(
    (library) =>
      [...library.querySelectorAll("[data-prompt-format]")].map(
        (tab) => tab.dataset.levelNumber,
      ),
  ),
  visibleLevelText: [...document.querySelectorAll("[data-prompt-format]")].map(
    (tab) => tab.textContent.trim(),
  ),
  copyIcons: document.querySelectorAll(".prompt-format-copy svg").length,
  tabbablePerLibrary: [
    ...document.querySelectorAll("[data-prompt-library]"),
  ].map(
    (library) =>
      [...library.querySelectorAll("[data-prompt-format]")].filter(
        (tab) => tab.tabIndex === 0,
      ).length,
  ),
}));
if (
  levelContract.guides !== 0 ||
  levelContract.libraries !== 13 ||
  levelContract.levels.some((levels) => levels.join("|") !== "1|2|3|4") ||
  levelContract.visibleLevelText.some(
    (text) => !["1", "2", "3", "4"].includes(text),
  ) ||
  levelContract.copyIcons !== 13 ||
  levelContract.tabbablePerLibrary.some((count) => count !== 1)
) {
  throw new Error(
    `PROMPT_LEVEL_CONVENTION_FAILED: ${JSON.stringify(levelContract)}`,
  );
}
const firstLevelTab = brainInteraction
  .locator('[data-prompt-library="brain-prompt-es-1"] [data-prompt-format]')
  .first();
await firstLevelTab.focus();
await brainInteraction.keyboard.press("End");
if (
  (await brainInteraction
    .locator('[data-prompt-library="brain-prompt-es-1"] [aria-selected="true"]')
    .getAttribute("data-level-number")) !== "4"
)
  throw new Error("PROMPT_LEVEL_END_FAILED");
await brainInteraction.keyboard.press("Home");
if (
  (await brainInteraction
    .locator('[data-prompt-library="brain-prompt-es-1"] [aria-selected="true"]')
    .getAttribute("data-level-number")) !== "1"
)
  throw new Error("PROMPT_LEVEL_HOME_FAILED");
const hostileDump =
  '<script>alert("no")</script> Quiero estudiar un tema y revisar dos adjuntos.';
await brainInteraction.fill("[data-brain-dump]", hostileDump);
await brainInteraction.click(
  '[data-prompt-library="brain-prompt-es-1"] [data-prompt-format="spec"]',
);
await brainInteraction.click('[data-brain-copy="brain-prompt-es-1"]');
if (
  !(
    (await brainInteraction
      .locator('[data-prompt-library="brain-prompt-es-1"] .prompt-copy-status')
      .textContent()) || ""
  ).includes("Copiado · Nivel 3")
)
  throw new Error("PROMPT_COPY_STATUS_FAILED");
const brainState = await brainInteraction.evaluate(() => ({
  copied: window.__copiedBrainPrompt,
  scripts: document.querySelectorAll("script:not([src])").length,
  renderedHostile: [...document.querySelectorAll("pre")].some((node) =>
    node.textContent.includes('<script>alert("no")</script>'),
  ),
  local: { ...localStorage },
  session: { ...sessionStorage },
}));
if (
  !brainState.copied?.includes("# SPEC MetodologIA") ||
  !brainState.copied?.includes("# Inputs") ||
  !brainState.copied?.includes(hostileDump) ||
  brainState.renderedHostile ||
  JSON.stringify(brainStorageBefore) !==
    JSON.stringify({ local: brainState.local, session: brainState.session })
) {
  throw new Error(`BRAIN_DUMP_CONTRACT_FAILED: ${JSON.stringify(brainState)}`);
}
await brainInteraction.click(
  '[data-prompt-library="p1-es"] [data-prompt-format="pair"]',
);
await brainInteraction.click('[data-format-copy="p1-es"]');
const workshopPair = await brainInteraction.evaluate(
  () => window.__copiedBrainPrompt,
);
if (!workshopPair?.includes("# system") || !workshopPair?.includes("# user"))
  throw new Error(`WORKSHOP_FORMAT_COPY_FAILED: ${workshopPair}`);
console.log(
  JSON.stringify({ interaction: "brain-dump-ephemeral-input", status: "PASS" }),
);
await brainInteraction.close();
const promptInteraction = await browser.newPage({
  viewport: { width: 390, height: 844 },
});
await promptInteraction.goto(local("prompts/index.html"));
await promptInteraction.evaluate(() => {
  navigator.clipboard.writeText = async (text) => {
    window.__copiedLibraryPrompt = text;
  };
});
const promptTab = promptInteraction
  .locator('[data-prompt-library="library-es-01"] [data-prompt-format]')
  .first();
await promptTab.focus();
await promptInteraction.keyboard.press("End");
if (
  (await promptInteraction
    .locator('[data-prompt-library="library-es-01"] [aria-selected="true"]')
    .getAttribute("data-level-number")) !== "4"
)
  throw new Error("LIBRARY_LEVEL_END_FAILED");
await promptInteraction.click('[data-format-copy="library-es-01"]');
const libraryCopy = await promptInteraction.evaluate(
  () => window.__copiedLibraryPrompt,
);
const libraryStatus = await promptInteraction
  .locator('[data-prompt-library="library-es-01"] .prompt-copy-status')
  .textContent();
if (
  !libraryCopy?.includes("# system") ||
  !libraryCopy?.includes("# user") ||
  !libraryStatus?.includes("Copiado · Nivel 4")
)
  throw new Error("LIBRARY_COPY_FAILED");
console.log(
  JSON.stringify({
    interaction: "prompt-library-keyboard-copy",
    status: "PASS",
  }),
);
await promptInteraction.close();
for (const width of [320, 390, 768, 1440]) {
  const officialDeck = await browser.newPage({
    viewport: { width, height: width < 700 ? 844 : 900 },
  });
  const remoteRequests = [];
  officialDeck.on("request", (request) => {
    if (/^https?:/i.test(request.url())) remoteRequests.push(request.url());
  });
  await officialDeck.goto(local("deck/index.html"));
  await officialDeck.waitForTimeout(500);
  const officialState = await officialDeck.evaluate(() => ({
    scrollY,
    hash: location.hash,
    firstSurface: document.querySelector("main")?.firstElementChild?.id,
    objectData: document.querySelector(".official-pdf-object")?.getAttribute("data"),
    objectVisible: (() => {
      const box = document.querySelector(".official-pdf-card")?.getBoundingClientRect();
      return Boolean(box && box.bottom > 72 && box.top < innerHeight);
    })(),
    overflow: document.documentElement.scrollWidth - innerWidth,
    smallActions: [...document.querySelectorAll(".official-pdf-toolbar .btn")]
      .filter((item) => {
        const box = item.getBoundingClientRect();
        return box.width < 44 || box.height < 44;
      }).length,
    breadcrumbTriggerOverlap: (() => {
      const breadcrumb = document.querySelector(".official-masterclass .breadcrumbs")?.getBoundingClientRect();
      const trigger = document.querySelector("[data-intrapage-open]")?.getBoundingClientRect();
      return Boolean(breadcrumb && trigger && !(breadcrumb.right <= trigger.left || breadcrumb.left >= trigger.right || breadcrumb.bottom <= trigger.top || breadcrumb.top >= trigger.bottom));
    })(),
  }));
  if (
    officialState.scrollY !== 0 ||
    officialState.hash !== "" ||
    officialState.firstSurface !== "masterclass-inicio" ||
    !officialState.objectData?.includes("assets/masterclass-ia-nivel-0.pdf") ||
    !officialState.objectVisible ||
    officialState.overflow !== 0 ||
    officialState.smallActions !== 0 ||
    officialState.breadcrumbTriggerOverlap ||
    remoteRequests.length
  )
    throw new Error(
      `OFFICIAL_MASTERCLASS_PRIMARY_FAILED:${JSON.stringify({ width, officialState, remoteRequests })}`,
    );
  await officialDeck.close();
}
console.log(JSON.stringify({ interaction: "official-masterclass-primary", status: "PASS" }));
for (const anchor of ["masterclass-inicio", "masterclass-pdf", "masterclass-guia"]) {
  const deepLinkedOfficial = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await deepLinkedOfficial.goto(`${local("pt/deck/index.html")}#${anchor}`);
  await deepLinkedOfficial.waitForFunction((wanted) => {
    const target = document.getElementById(wanted);
    const current = document.querySelector(`[data-intrapage-link][href="#${wanted}"]`);
    if (!target || current?.getAttribute("aria-current") !== "location") return false;
    const box = target.getBoundingClientRect();
    return box.top >= 70 && box.top < 180;
  }, anchor);
  await deepLinkedOfficial.close();
}
console.log(JSON.stringify({ interaction: "official-masterclass-deep-links", status: "PASS" }));
const officialDrawer = await browser.newPage({ viewport: { width: 390, height: 844 } });
await officialDrawer.goto(local("pt/deck/index.html"));
await officialDrawer.locator("[data-intrapage-open]").click();
await officialDrawer.locator('[data-intrapage-link][href="#masterclass-pdf"]').click();
const officialDrawerState = await officialDrawer.evaluate(() => ({
  hash: location.hash,
  panelHidden: document.querySelector("[data-intrapage-nav]")?.hidden,
  focusedInTarget: Boolean(document.activeElement?.closest("#masterclass-pdf")),
  focusedHeading: document.activeElement?.matches("#masterclass-pdf h2"),
}));
if (
  officialDrawerState.hash !== "#masterclass-pdf" ||
  !officialDrawerState.panelHidden ||
  !officialDrawerState.focusedInTarget ||
  !officialDrawerState.focusedHeading
)
  throw new Error(`OFFICIAL_MASTERCLASS_DRAWER_FOCUS_FAILED:${JSON.stringify(officialDrawerState)}`);
await officialDrawer.close();
console.log(JSON.stringify({ interaction: "official-masterclass-drawer-focus", status: "PASS" }));
for (const width of [320, 390, 768, 1440]) {
  const deck = await browser.newPage({
    viewport: { width, height: width < 700 ? 844 : 900 },
  });
  await deck.goto(`${local("deck/index.html")}#slide-1`);
  await deck.keyboard.press("ArrowRight");
  const deckState = await deck.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - innerWidth,
    hash: location.hash,
    current: document.querySelector("[data-count]")?.textContent.trim(),
    now: document
      .querySelector(".deck-controls .progress")
      ?.getAttribute("aria-valuenow"),
    controlsOverlap: (() => {
      const controls = document
        .querySelector(".deck-controls")
        .getBoundingClientRect();
      const page = document
        .querySelector(".slide.active")
        .getBoundingClientRect();
      return !(controls.bottom <= page.top || controls.top >= page.bottom);
    })(),
    smallTargets: [
      ...document.querySelectorAll(
        ".deck button, .deck summary, .slide-actions a",
      ),
    ]
      .filter((target) => {
        const style = getComputedStyle(target);
        const box = target.getBoundingClientRect();
        return style.display !== "none" && style.visibility !== "hidden" && box.width > 0;
      })
      .filter((target) => {
        const box = target.getBoundingClientRect();
        return box.width < 44 || box.height < 44;
      })
      .map((target) => ({
        selector:
          target.getAttribute("data-mode") ||
          target.getAttribute("data-slide") ||
          target.getAttribute("data-next") ||
          target.getAttribute("data-prev") ||
          target.tagName,
        width: target.getBoundingClientRect().width,
        height: target.getBoundingClientRect().height,
      })),
  }));
  if (
    deckState.overflow !== 0 ||
    deckState.hash !== "#slide-2" ||
    deckState.current !== "2 / 18" ||
    deckState.now !== "2" ||
    deckState.controlsOverlap ||
    deckState.smallTargets.length
  ) {
    throw new Error(
      `DECK_KEYBOARD_RESPONSIVE_FAILED: ${JSON.stringify({ width, deckState })}`,
    );
  }
  await deck.locator(".stage").scrollIntoViewIfNeeded();
  const beforeEndY = await deck.evaluate(() => scrollY);
  await deck.locator(".stage").click({ position: { x: 8, y: 8 } });
  await deck.keyboard.press("End");
  const endState = await deck.evaluate(() => ({
    hash: location.hash,
    current: document.querySelector(".slide.active")?.id,
    visible: (() => {
      const box = document.querySelector(".slide.active").getBoundingClientRect();
      return box.bottom > 0 && box.top < innerHeight;
    })(),
  }));
  endState.scrollShift = Math.abs(
    (await deck.evaluate(() => scrollY)) - beforeEndY,
  );
  if (
    endState.hash !== "#slide-18" ||
    endState.current !== "slide-18" ||
    endState.scrollShift > 1 ||
    !endState.visible
  )
    throw new Error(
      `DECK_END_STATE_FAILED: ${JSON.stringify({ width, endState })}`,
    );
  const beforeHomeY = await deck.evaluate(() => scrollY);
  await deck.keyboard.press("Home");
  const homeState = await deck.evaluate(() => ({
    hash: location.hash,
    current: document.querySelector(".slide.active")?.id,
    scrollY,
  }));
  if (
    homeState.hash !== "#slide-1" ||
    homeState.current !== "slide-1" ||
    Math.abs(homeState.scrollY - beforeHomeY) > 1
  )
    throw new Error(
      `DECK_HOME_STATE_FAILED: ${JSON.stringify({ width, homeState })}`,
    );
  const noteSummary = deck.locator(".slide.active .fac-note summary");
  await noteSummary.focus();
  await deck.keyboard.press("ArrowRight");
  const noteFocusState = await deck.evaluate(() => ({
    current: document.querySelector(".slide.active")?.id,
    focusIsSummary: document.activeElement?.matches(".fac-note summary"),
  }));
  if (
    noteFocusState.current !== "slide-1" ||
    !noteFocusState.focusIsSummary
  )
    throw new Error(
      `DECK_DISCLOSURE_FOCUS_FAILED: ${JSON.stringify({ width, noteFocusState })}`,
    );
  if (width === 390) {
    const outline = deck.locator("details.outline");
    await outline.locator("summary").click();
    await outline.locator('[data-slide="2"]').focus();
    await deck.keyboard.press("Enter");
    const mobileFocusState = await deck.evaluate(() => ({
      current: document.querySelector(".slide.active")?.id,
      outlineOpen: document.querySelector("details.outline")?.open,
      focusedTitle: document.activeElement?.id,
    }));
    if (
      mobileFocusState.current !== "slide-3" ||
      mobileFocusState.outlineOpen ||
      mobileFocusState.focusedTitle !== "slide-title-3"
    )
      throw new Error(
        `DECK_MOBILE_OUTLINE_FOCUS_FAILED: ${JSON.stringify(mobileFocusState)}`,
      );
  }
  if (width === 1440) {
    const summary = deck.locator(".outline > summary");
    await summary.click();
    const collapsed = await deck.evaluate(() => ({
      open: document.querySelector("details.outline").open,
      height: document.querySelector(".outline-list").getBoundingClientRect().height,
    }));
    await summary.focus();
    await deck.keyboard.press("Enter");
    const expanded = await deck.evaluate(() => ({
      open: document.querySelector("details.outline").open,
      height: document.querySelector(".outline-list").getBoundingClientRect().height,
    }));
    if (
      collapsed.open ||
      collapsed.height !== 0 ||
      !expanded.open ||
      expanded.height === 0
    )
      throw new Error(
        `DECK_DISCLOSURE_FAILED: ${JSON.stringify({ collapsed, expanded })}`,
      );
  }
  if (width === 1440) {
    await deck.screenshot({
      path: resolve(qaRoot, "deck-1440.png"),
      fullPage: false,
    });
  }
  await deck.close();
}
const deepLinkedDeck = await browser.newPage({
  viewport: { width: 390, height: 844 },
});
await deepLinkedDeck.goto(`${local("deck/index.html")}#slide-18`);
await deepLinkedDeck.waitForFunction(() => {
  const active = document.querySelector(".slide.active");
  if (active?.id !== "slide-18") return false;
  const box = active.getBoundingClientRect();
  return box.bottom > 0 && box.top < innerHeight;
});
const deepLinkState = await deepLinkedDeck.evaluate(() => ({
  hash: location.hash,
  current: document.querySelector(".slide.active")?.id,
  visible: (() => {
    const box = document.querySelector(".slide.active").getBoundingClientRect();
    return box.bottom > 0 && box.top < innerHeight;
  })(),
}));
if (
  deepLinkState.hash !== "#slide-18" ||
  deepLinkState.current !== "slide-18" ||
  !deepLinkState.visible
)
  throw new Error(`DECK_DEEP_LINK_FAILED: ${JSON.stringify(deepLinkState)}`);
await deepLinkedDeck.close();
console.log(
  JSON.stringify({
    interaction: "deck-keyboard-hash-responsive",
    status: "PASS",
  }),
);
const noJs = await browser.newPage({
  viewport: { width: 390, height: 844 },
  javaScriptEnabled: false,
});
await noJs.goto(local("index.html"));
const noJsState = await noJs.evaluate(() => ({
  sections: document.querySelectorAll("main.landing-v2 > section.chapter")
    .length,
  hidden: [...document.querySelectorAll(".reveal")].filter(
    (element) => getComputedStyle(element).opacity === "0",
  ).length,
  resourceLinks: document.querySelectorAll(".resource-cover[href]").length,
  openSkills: document.querySelectorAll(
    '.open-skill-card[href="https://github.com/JaviMontano/material-educativo-metodologia/tree/main/skills/aprender-aprehender-revolucionar"]',
  ).length,
  formLinks: [...document.querySelectorAll("a[href]")].filter((link) =>
    link.href.includes("docs.google.com/forms"),
  ).length,
  letters: document.querySelectorAll(".letter-card").length,
}));
if (
  noJsState.sections !== 8 ||
  noJsState.hidden !== 0 ||
  noJsState.resourceLinks !== 3 ||
  noJsState.openSkills !== 1 ||
  noJsState.formLinks < 2 ||
  noJsState.letters !== 2
) {
  throw new Error(`NO_JS_FAILED: ${JSON.stringify(noJsState)}`);
}
console.log(
  JSON.stringify({
    interaction: "no-js-complete-content",
    ...noJsState,
    status: "PASS",
  }),
);
await noJs.close();
const noJsWorkbook = await browser.newPage({
  viewport: { width: 390, height: 844 },
  javaScriptEnabled: false,
});
await noJsWorkbook.goto(local("workbook/index.html"));
const noJsWorkbookState = await noJsWorkbook.evaluate(() => ({
  prompts: document.querySelectorAll(".brain-prompt-card").length,
  inputsHeadings: [
    ...document.querySelectorAll(".brain-prompt-card pre"),
  ].filter((node) => node.textContent.includes("# Inputs")).length,
  brainFormats: document.querySelectorAll(
    ".brain-prompt-card .prompt-format-panel",
  ).length,
  workshopFormats: document.querySelectorAll(
    ".workbook-sheets .prompt-format-panel",
  ).length,
  input: document.querySelectorAll("[data-brain-dump]").length,
  useCases: document.querySelectorAll(".use-cases li").length,
  overflow: document.documentElement.scrollWidth - innerWidth,
}));
if (
  noJsWorkbookState.prompts !== 3 ||
  noJsWorkbookState.inputsHeadings !== 12 ||
  noJsWorkbookState.brainFormats !== 12 ||
  noJsWorkbookState.workshopFormats !== 40 ||
  noJsWorkbookState.input !== 1 ||
  noJsWorkbookState.useCases !== 7 ||
  noJsWorkbookState.overflow !== 0
) {
  throw new Error(
    `NO_JS_WORKBOOK_FAILED: ${JSON.stringify(noJsWorkbookState)}`,
  );
}
console.log(
  JSON.stringify({
    interaction: "no-js-workbook",
    ...noJsWorkbookState,
    status: "PASS",
  }),
);
await noJsWorkbook.close();
const noJsPrompts = await browser.newPage({
  viewport: { width: 390, height: 844 },
  javaScriptEnabled: false,
});
await noJsPrompts.goto(local("prompts/index.html"));
const noJsPromptState = await noJsPrompts.evaluate(() => ({
  prompts: document.querySelectorAll("[data-library-prompt]").length,
  panels: document.querySelectorAll(".prompt-format-panel").length,
  open: document.querySelectorAll(".prompt-level-fallback[open]").length,
  visibleTabs: [...document.querySelectorAll(".prompt-format-tabs")].filter(
    (x) => getComputedStyle(x).display !== "none",
  ).length,
  visibleCopy: [...document.querySelectorAll(".prompt-format-copy")].filter(
    (x) => x.offsetParent !== null,
  ).length,
  overflow: document.documentElement.scrollWidth - innerWidth,
}));
if (
  noJsPromptState.prompts !== 14 ||
  noJsPromptState.panels !== 56 ||
  noJsPromptState.open !== 14 ||
  noJsPromptState.visibleTabs !== 0 ||
  noJsPromptState.visibleCopy !== 0 ||
  noJsPromptState.overflow !== 0
)
  throw new Error(`NO_JS_PROMPTS_FAILED: ${JSON.stringify(noJsPromptState)}`);
console.log(
  JSON.stringify({
    interaction: "no-js-prompt-library",
    ...noJsPromptState,
    status: "PASS",
  }),
);
await noJsPrompts.close();
const noJsDeck = await browser.newPage({
  viewport: { width: 390, height: 844 },
  javaScriptEnabled: false,
});
await noJsDeck.goto(local("deck/index.html"));
const noJsDeckState = await noJsDeck.evaluate(() => ({
  officialPdf: document.querySelector(".official-pdf-object")?.getAttribute("data"),
  officialVisible:
    getComputedStyle(document.querySelector(".official-pdf-object")).display !== "none",
  pages: [...document.querySelectorAll(".slide")].filter(
    (page) => getComputedStyle(page).display !== "none",
  ).length,
  extendedVisible:
    getComputedStyle(document.querySelector(".extended")).display !== "none",
  visiblePlayerControls: [...
    document.querySelectorAll(".outline, .deck-controls"),
  ].filter((control) => getComputedStyle(control).display !== "none").length,
  overflow: document.documentElement.scrollWidth - innerWidth,
}));
if (
  !noJsDeckState.officialPdf?.includes("assets/masterclass-ia-nivel-0.pdf") ||
  !noJsDeckState.officialVisible ||
  noJsDeckState.pages !== 18 ||
  !noJsDeckState.extendedVisible ||
  noJsDeckState.visiblePlayerControls !== 0 ||
  noJsDeckState.overflow !== 0
)
  throw new Error(`NO_JS_DECK_FAILED: ${JSON.stringify(noJsDeckState)}`);
console.log(
  JSON.stringify({
    interaction: "no-js-deck",
    ...noJsDeckState,
    status: "PASS",
  }),
);
await noJsDeck.close();
const intrapageFocus = await browser.newPage({
  viewport: { width: 390, height: 844 },
});
await intrapageFocus.goto(local("index.html"));
await intrapageFocus.locator("[data-intrapage-open]").click();
await intrapageFocus.waitForFunction(
  () => document.activeElement?.matches("[data-intrapage-close]"),
);
const intrapageOpenState = await intrapageFocus.evaluate(() => ({
  expanded: document
    .querySelector("[data-intrapage-open]")
    ?.getAttribute("aria-expanded"),
  active: document.activeElement?.getAttribute("data-intrapage-close") !== null,
  visible:
    getComputedStyle(document.querySelector("[data-intrapage-nav]")).visibility ===
    "visible",
}));
if (
  intrapageOpenState.expanded !== "true" ||
  !intrapageOpenState.active ||
  !intrapageOpenState.visible
)
  throw new Error(
    `INTRAPAGE_OPEN_FOCUS_FAILED: ${JSON.stringify(intrapageOpenState)}`,
  );
await intrapageFocus.locator('[data-intrapage-link][href="#tension"]').click();
const intrapageDestinationState = await intrapageFocus.evaluate(() => ({
  hash: location.hash,
  panelHidden: document.querySelector("[data-intrapage-nav]")?.hidden,
  activeInTarget: document
    .querySelector("#tension")
    ?.contains(document.activeElement),
  activeInPanel: document
    .querySelector("[data-intrapage-nav]")
    ?.contains(document.activeElement),
}));
if (
  intrapageDestinationState.hash !== "#tension" ||
  !intrapageDestinationState.panelHidden ||
  !intrapageDestinationState.activeInTarget ||
  intrapageDestinationState.activeInPanel
)
  throw new Error(
    `INTRAPAGE_DESTINATION_FOCUS_FAILED: ${JSON.stringify(intrapageDestinationState)}`,
  );
console.log(
  JSON.stringify({
    interaction: "intrapage-drawer-focus",
    open: intrapageOpenState,
    destination: intrapageDestinationState,
    status: "PASS",
  }),
);
await intrapageFocus.close();
await browser.close();
