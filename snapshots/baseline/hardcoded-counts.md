# Baseline — conteos cableados relacionados a prompts/paneles/rutas

Fase B0 del plan de elevación. Inventario grep sobre el tip `d2ee278`
(branch `codex/nivel-0-prompt-elevation-v1`). Cada fila: valor duro,
archivo:línea, qué representa. [CÓDIGO]

## 162 — paneles de prompt globales (library 84 + workbook 52 + extra)

| Valor | Ubicación | Significado |
|---|---|---|
| 162 | `qa/check-prompt-spec.py:157` | `all_spec_panels != 162` — total global de paneles spec verificados |
| 14 (implícito) | `qa/check-prompt-spec.py:21` | tupla `IDS` = 01..10 + M1..M4 (library) |
| 4 | `qa/check-prompt-spec.py:106` | 4 posiciones/niveles por prompt (`len(set(positions)) != 4`) |

## 54 — rutas canónicas (build + specs + QA)

| Valor | Ubicación | Significado |
|---|---|---|
| 54 | `scripts/build.py:118` | `canonical_routes: 54` en validación de matriz de paridad |
| 54 | `scripts/build.py:1055` | `len(html_outputs)!=54` — total de HTML renderizados |
| 54 | `src/editorial-parity-spec-v1.json:13` | `"canonical_routes": 54` |
| 54 | `qa/check-editorial-parity.py:31` | `route_count != 54` en inventario de strings |
| 54 | `qa/check-editorial-parity.py:40` | rutas únicas del inventario |
| 54 | `qa/check-editorial-parity.py:143` | literal en línea de salida `routes=54` |
| 54 | `qa/check-editorial-sitemap.py:142` | `len(expected_paths) != 54` |
| 54 | `qa/check-editorial-sitemap.py:211` | `len(locs) != 54` (sitemap) |
| 54 | `qa/check-editorial-sitemap.py:218` | `canonical_count != 54` en binding |
| 54 | `qa/check-breadcrumbs.py:120` | literal de salida `header_home=54 jsonld=54` |
| 54 | `qa/check-breadcrumbs-visual.mjs:16` | `routes.length !== 54` |
| 54 | `qa/check-conoce-chrome.mjs:63` | `pages.length !== 54` |
| 54 | `qa/check-conoce-chrome.mjs:131` | `rendered_pages !== 54` en manifest |
| 54 | `qa/check-conoce-chrome.py:59` | literal de salida `source_variants=54` |
| 54 | `qa/check-intrapage-navigation.mjs:20` | `pages.length !== 54` |
| 54 | `qa/check-intrapage-navigation.mjs:45` | `rendered_pages !== 54` en manifest |

## 56/14/10/4/13 — contrato visual de prompts (qa/check-visual.mjs)

| Valor | Ubicación | Significado |
|---|---|---|
| 14 | `qa/check-visual.mjs:364` | `promptState.prompts !== 14` (cards library) |
| 10 | `qa/check-visual.mjs:365` | `promptState.direct !== 10` (prompts directos) |
| 4 | `qa/check-visual.mjs:366` | `promptState.meta !== 4` (meta-prompts M1..M4) |
| 14 | `qa/check-visual.mjs:367` | `promptState.libraries !== 14` |
| 56 | `qa/check-visual.mjs:368` | `promptState.levels !== 56` (14×4 tabs) |
| 56 | `qa/check-visual.mjs:369` | `promptState.panels !== 56` (14×4 paneles) |
| 14 | `qa/check-visual.mjs:370` | `promptState.copies !== 14` (botones copiar) |
| 14 | `qa/check-visual.mjs:371` | `promptState.examples !== 14` |
| 14 | `qa/check-visual.mjs:335` | `playbookState.prompts !== 14` |
| 13 | `qa/check-visual.mjs:276` | `workbookState.promptLibraries !== 13` (W01..W10 + B1..B3) |
| 10 | `qa/check-visual.mjs:266,268` | `expertSteps !== 10`, `steps !== 10` (workbook) |
| 4 | `qa/check-visual.mjs:271` | `providerLinks !== 4` |
| 13 | `qa/check-visual.mjs:769` | `levelContract.libraries !== 13` (workbook, contrato de niveles) |
| 13 | `qa/check-visual.mjs:779` | `levelContract.copyIcons !== 13` |
| 4 | `qa/check-visual.mjs:770,777` | secuencia de niveles `1|2|3|4` por librería |
| 14 | `qa/check-visual.mjs:1261` | `noJsPromptState.prompts !== 14` (no-JS) |
| 56 | `qa/check-visual.mjs:1262` | `noJsPromptState.panels !== 56` (no-JS) |
| 14 | `qa/check-visual.mjs:1263` | `noJsPromptState.open !== 14` (no-JS, details open) |
| 4 | `qa/check-prompt-spec-visual.mjs:155` | `heroContract.levels !== 4` |

## 18 — deck de slides

| Valor | Ubicación | Significado |
|---|---|---|
| 18 | `qa/check-visual.mjs:437,438,443` | `deckState.pages/indexItems/facilitatorNotes !== 18` |
| 18 | `qa/check-visual.mjs:1021,1046,1047,1136,1139,1152` | navegación `2 / 18`, `#slide-18` |
| 18 (implícito) | `scripts/build.py:859-861` | 18 tuplas de slides por locale (es/en/pt) |

## 378 — campos de paridad editorial

| Valor | Ubicación | Significado |
|---|---|---|
| 378 | `qa/check-editorial-parity.py:143` | literal de salida `fields=378` (54 rutas × 7 campos) |

## Otros conteos duros relacionados

| Valor | Ubicación | Significado |
|---|---|---|
| 24 | `qa/check-editorial-sitemap.py:218,223` | `rendered_pages != 24` (páginas editoriales) y `editorial=24` |
| 2 | `qa/check-prompt-spec.py:37` | `len(references) != 2` referencias secundarias por prompt |
| 3 | `qa/check-prompt-spec-visual.mjs:154` | `heroContract.metrics !== 3` |

## Derivados observados en el baseline (no cableados, salida real)

- `PROMPT_SPEC_OK library_panels=84 all_panels=162 prompts=14 locales=3 audiences=2 mutations=24` [CÓDIGO]
- `EDITORIAL_PARITY_OK routes=54 fields=378 mutations=214 strings=10504` [CÓDIGO]
- Snapshot baseline: 216 entradas por locale (27 intents × 2 audiencias × 4 niveles), 648 global. [CÓDIGO]
