# Verificación · 2026-08-17 · post-elevación a contratos de intención

Estado: `RENDERED_DRAFT` · publicación no autorizada.
Rama `codex/nivel-0-prompt-elevation-v1`, HEAD `731a7bf`.

## Paquete compilado

- Manifest `dist/build-manifest.json` — sha256 de bytes:
  `f089af063b6b3c6c663a7e732624c116e1040fddf19c8d7e7f35a18fa89a3833`;
  `self_sha256` (`sha256(sorted-json-without-self_sha256)` + `\n`):
  `ea378a90ea2e9894ddbf99e9c91ff6784df1d730f1b86ddfd5fff9b6a9266fbd`.
- Receipt `dist/build-receipt.json` — `self_sha256`
  (`sha256(sorted-json-without-self)`, sin newline final):
  `e453b6cb823bdcb297f0156e85c2a16d0c0ab60f8d12c65a07b27788459f9dd8`;
  sha256 de bytes:
  `92daaaa79bca65dae59532e2c4e09e084d72a383c91b9eb9f3f2471034f1e6e4`.
- Autoridad de anclas `src/prompt-intent-authority-v2.json` —
  `status: frozen_phase_3`, `self_sha256`
  `9e43b4826ef76b63c9fa1cca25ca29a9fd02510f07149680d967e49d9f5b4b86`,
  `source_sha256`
  `52bdcdd85faf0e211f3672bf1b86a41344bd567f3b0f715484eb165ac154e20a`.
- Integridad: **75/75 outputs** y **72/72 fuentes** presentes y coincidentes con
  sus hashes del manifest; el `self_sha256` de manifest y receipt reproduce al
  recomputarlo. Los 27 `self_sha256` de contrato quedan re-emitidos en el
  receipt bajo `prompt_library.prompt_contracts`.
- Determinismo: dos compilaciones consecutivas producen un `dist/` byte-idéntico
  (hash agregado de los 75 archivos: `4af88f29c5f56d2d02cbe49395033e6317acac3a2b5cd50e78eb1bf9c58b5998`).
- Alcance: **54 rutas HTML** (9 páginas × 3 locales × 2 audiencias), el PDF
  oficial de 18 páginas, cuatro retratos de fundadores, fuentes locales y
  recursos de marca (21 outputs no-HTML en total).

Todas las cifras y hashes de este reporte se midieron sobre el árbol limpio en
`731a7bf`. En paralelo hay un cambio solo-CSS en curso en `src/site.css`
(`overflow-wrap` en `.prompt-why-body li`) del workstream de QA: cuando se
comprometa, manifest y receipt quedarán re-pineados y estos tres hashes cambian
sin que cambie ninguna cifra estructural.

## Modelo de prompts verificado

- [CONFIG] 27 contratos `prompt-intent-contract-v1` en `src/prompt-contracts/`;
  `contract_count=27`, `rendered_cells=162`, `fallback_policy: forbidden`,
  `why_panel: true` en el receipt.
- [CONFIG] `dist/` contiene **648** paneles de nivel (`data-prompt-level="1..4"`)
  = 27 intenciones × 3 locales × 2 audiencias × 4 niveles, y **162** paneles
  «por qué funciona» (`class="prompt-why"`), uno por celda.
- [CONFIG] Reparto del tope de longitud `max(2 × baseline, 600)`: 132 celdas
  quedan gobernadas por el término 2× y 30 (las de `W06`–`W10`) por el piso de
  600. El prompt más largo del corpus mide 1376 caracteres.
- [CONFIG] Los 10 prompts de taller viven ahora en `src/workbook-prompts-v1.json`
  (`schema_version: workbook-prompts-v1`), no en tuplas de `scripts/build.py`.
- [METODOLOGIA] Trazabilidad: 576 entradas `traceability` contra un allowlist
  cerrado de 8 fuentes (`reference_sources` del library spec ∪ `source` del
  claim ledger ∪ `method_internal`). 237 de ellas son `method_internal`.

## Suite de QA ejecutada

Gates deterministas (`python3`):

```
BREADCRUMBS_OK pages=54 header_home=54 jsonld=54 mutations=5 fragments=0
CONOCE_CHROME_MUTATIONS_OK 15/15 source_variants=54
EDITORIAL_PARITY_OK routes=54 fields=378 mutations=214 strings=13755 pdf=5df5533a29652184f492b2f797ecfa0f1fa47cdb682bfcefb8f30c96014ce402
EDITORIAL_SITEMAP_OK canonicals=54 editorial=24 header_fragments=0 audience_material=24
PROMPT_CONTRACTS_OK contracts=27 ids=27 locales=3 audiences=2 mutations=15 warnings=6
```

Gates visuales y de accesibilidad (`node`, Playwright + axe 4.12.1):

```
A2RE_VISUAL_PASS states=240 rendered_marks=336 external_requests=0
BREADCRUMB_VISUAL_OK pages=54 themes=2 axe=4.12.1 breakpoints=320/390/768/1440 no_js=4
CONOCE_CHROME_VISUAL_OK widths=4 no_js=PASS
CONOCE_CHROME_OK 54/54 zero-fragment-header
CONOCE_DARK_CONTRAST_OK axe=4.12.1 width=390 nodes=12 min=8.05
CONOCE_DARK_CONTRAST_OK axe=4.12.1 width=1440 nodes=12 min=8.05
EDITORIAL_VISUAL_OK pages=24 themes=2 axe=4.12.1 responsive=320/390/768/1440 no_js=PASS
INTRAPAGE_NAVIGATION_OK 54/54
METHOD_IDENTITY_PASS pages=54 relevant=18 marks=42 outputs=75 mutations=24
OFFICIAL_MASTERCLASS_OK routes=6 pages=18 mutations=4 sha256=5df5533a29652184f492b2f797ecfa0f1fa47cdb682bfcefb8f30c96014ce402
PROMPT_SPEC_VISUAL_OK states=120 zoom_200=24 axe=120 mutations=120 why=120 keyboard=12 copy=12 no_js=12
PREFERENCE_TOGGLES_OK routes=54 protocols=2 scenarios=108 clicks=432
```

Dos gates **no** pasan en este HEAD; ambos están en `qa/` y ambos son lectores
del modelo retirado, no defectos del paquete compilado. Ver «Coverage gaps».

## Proceso de calidad de la elevación

[METODOLOGIA] La elevación se ejecutó en siete fases con evidencia por fase:
0 baseline y snapshot determinista · 1 esquema `prompt-intent-contract-v1`,
autoridad v2 y validadores parametrizados · 2 migración byte-idéntica de los 10
prompts de taller de Python a JSON · 3 crítica adversarial (27 briefs, cuatro
fronteras con regla de decisión, carta de tono, autoridad congelada) · 4 autoría
en siete lotes · 5 cutover del build · 6 QA y documentación.

[METODOLOGIA] Cada lote de la fase 4 pasó por autor → revisor adversarial
independiente → corrección verificada ítem por ítem. El lote L3 fue rechazado
entero y re-autorado (`a7d5855`). Las revisiones produjeron seis reglas nuevas,
todas mecanizadas en `qa/check-prompt-contracts.py`:

1. **R8** no hay promesa sin productor (`PROMPT_CONTRACT_PROMISE_NO_PRODUCER`).
2. **R9** autoridad citada = autoridad existente (`PROMPT_CONTRACT_AUTHORITY_UNRESOLVED`).
3. Negación por mecanismo, nunca por id desnudo (`PROMPT_CONTRACT_BARE_ID`,
   `PROMPT_CONTRACT_ID_NOT_IN_BOUNDARY`).
4. Regresión de audiencia prohibida (`PROMPT_CONTRACT_AUDIENCE_CLONE` +
   carta §E persona/empresa).
5. Carta de tono mecanizada (`PROMPT_CONTRACT_TONE_MARKER`).
6. Simetría de fronteras (`PROMPT_CONTRACT_ASYMMETRIC_BOUNDARY`) y clon
   cross-intent (`PROMPT_CONTRACT_CROSS_INTENT_CLONE`).

[CONFIG] El gate creció de 8 a **15 mutaciones internas** que deben fallar. La
carta de tono §E recibió dos enmiendas ratificadas: ampliación de `P4-pt`
(`seu `, `voce` además de `sua `) y acotación de aplicabilidad de `E3`, que no
aplica a intenciones sin autoridad de decisión (caso nombrado: `02`), porque
exigir léxico de gobernanza allí produce exactamente la promesa sin productor
que R8 prohíbe.

## Aceptación

- [CONFIG] Paridad estructural ES/EN/PT en las 54 rutas: `EDITORIAL_PARITY_OK`
  cubre 378 campos y 13 755 cadenas con 214 mutaciones rechazadas.
- [CONFIG] Las 12 páginas de prompts y workbook exponen solo los iconos
  numéricos `1–4`, una parada de tabulación por grupo, flechas/Home/End, copia
  localizada y feedback `aria-live`. Sin JavaScript los 648 paneles de nivel y
  los 162 paneles «por qué funciona» se conservan en disclosures nativos.
- [CONFIG] `PROMPT_SPEC_VISUAL_OK` valida 120 estados con axe, zoom 200 % en 24
  combinaciones, 120 mutaciones y los 120 paneles `why` de la biblioteca.
- [CONFIG] Breadcrumbs semánticos, JSON-LD y regreso a la clase 1 en las 54
  páginas; cero fragmentos de header y cero enlaces internos rotos.
- [CONFIG] Contraste en tema oscuro: mínimo 8.05 sobre 12 nodos medidos a 390 y
  1440 px.
- [METODOLOGIA] El PDF oficial conserva su hash declarado
  `5df5533a29652184f492b2f797ecfa0f1fa47cdb682bfcefb8f30c96014ce402`; cualquier
  cambio de bytes bloquea el build.
- [METODOLOGIA] Identidad de método: 42 marcas en 18 páginas relevantes, 24
  mutaciones rechazadas, cero solicitudes externas en 240 estados renderizados.
- [CONFIG] El manifest vincula recursivamente los 72 inputs de `src`, incluidos
  los recursos binarios. El paquete público no contiene rutas privadas, enlaces
  `/edit`, PII, transcripciones ni locators de Drive.
- [NEUROCIENCIA] No se incorporaron afirmaciones neurocientíficas.

Las aceptaciones editoriales de la revisión del 2026-08-13 (composición A³ del
playbook, carta de fundadores, visor de la masterclass, mapa de 16 entregables,
videos públicos verificados por oEmbed, política de Antigravity y del MCP
comunitario de NotebookLM) siguen vigentes: la elevación no tocó `src/site.js`
ni ninguna de esas superficies. No se revalidaron manualmente en este ciclo.

## Fuentes y autoridad

- [METODOLOGIA] PDF suministrado por el propietario: 18 páginas, SHA-256
  `5df5533a29652184f492b2f797ecfa0f1fa47cdb682bfcefb8f30c96014ce402`.
- [METODOLOGIA] Logo oficial: `https://metodologia.info/favicon.svg`.
- [METODOLOGIA] Foto y perfil público de Javier: `https://github.com/JaviMontano`.
- [METODOLOGIA] Fuentes de referencia de la biblioteca: `prompt-amplificado`
  (biblioteca y creación de prompts) y tres artículos de soporte de NotebookLM.
- [CONFIG] Línea base de longitud congelada en
  `snapshots/baseline/prompt-snapshot-{es,en,pt}.json` (216 claves por locale,
  648 en total).

## Coverage gaps

- [CÓDIGO] **`qa/check-prompt-spec.py` falla**: `PROMPT_NATURAL_DRIFT:es:persona:01`.
  El checker compara el nivel 1 renderizado contra los `items` de
  `src/prompt-library-spec-v1.json`, que el cutover dejó de renderizar. Es el
  lector que impide retirar esos `items`; el retiro sigue pendiente y este gate
  debe reescribirse contra los contratos antes de cerrarlo.
- [CÓDIGO] **`qa/check-visual.mjs` falla**: `NO_JS_WORKBOOK_FAILED`, campo
  `inputsHeadings` = 9 con 12 esperados. Los tres `brain-prompt-card` conservan
  sus 4 niveles, pero el nivel 1 ya no es el texto con encabezado `# Inputs`
  sino el `prompt` del contrato. La aserción quedó desactualizada por el
  cutover; el valor correcto es 9 (3 niveles derivados × 3 tarjetas). Cambio
  pendiente en `qa/`, no en el paquete.
- [CÓDIGO] **6 warnings R8 en `library-09`**
  (`WARN:PROMPT_CONTRACT_PROMISE_NO_PRODUCER`, campo `dod`, es/en/pt ×
  persona/empresa: «sesión reproducible», «ensayo revisable» y sus
  traducciones). Son falsos positivos calibrados por diseño: el checker bloquea
  fragmentos de ≥3 términos de contenido y solo advierte en los de 2, donde el
  fragmento suele ser un par de adjetivos de calidad. La calibración y su techo
  están documentados en el propio código (`PROMISE_BLOCK_TERMS`). No bloquean.
- [CÓDIGO] `minimum_lexical_diversity` (0.7) y `minimum_anchor_count` (2) están
  declarados en `spec_contract.semantic_specificity` y **no** están
  implementados en `qa/check-prompt-contracts.py`. Sí se aplican a los 27
  contratos en tiempo de build, vía
  `compose_prompt_documents()` → `validate_prompt_library()` en
  `scripts/build.py`. El hueco es de cobertura doble, no de regla sin aplicar:
  el validador standalone no rechazaría por sí solo un prompt con relleno
  redundante.
- [CÓDIGO] **Retiro pendiente** de `src/prompt-spec-authority-v1.json` y de los
  `items` de `src/prompt-library-spec-v1.json`. Ambos conservan lectores vivos:
  `scripts/build.py` (`validate_prompt_library()` sin argumentos y el binding
  `prompt_library` del manifest), `qa/check-prompt-spec.py` y el fixture de
  mutación de `qa/check-prompt-contracts.py`. Hasta retirarlos coexisten dos
  autoridades de anclas (v1 y v2).
- [CONFIG] `qa/check-preference-toggles.mjs` es intermitente: falló una vez de
  tres con `Variant state drift` (`locale: ""`, `preferenceGroups: 0`) en
  `/en/playbook/index.html` inmediatamente después de una navegación por click,
  y pasó las otras dos. Es una carrera del checker contra la navegación, no una
  regresión del paquete; la aserción necesita esperar el `load` de destino.
- [CONFIG] Los gates de Playwright/axe dependen de un módulo externo al repo
  (`../../frames-n0-kit-01/node_modules/playwright`) y de Google Chrome local.
  En un entorno sin ellos quedan como `coverage_gap`.
- [SUPUESTO] Queda pendiente una prueba manual con lector de pantalla real; la
  cobertura automatizada de axe no la sustituye.
- [SUPUESTO] Lighthouse y Core Web Vitals requieren la URL desplegada para una
  medición de campo representativa. El PDF pesa 14 MB y no forma parte de la
  carga inicial de la landing.
- [CONFIG] No aplican prueba HTTP pública ni receipt de despliegue mientras el
  paquete permanezca local y sin publicar.

Estado final: `RENDERED_DRAFT`. `RENDERED_DRAFT != HUMAN_APPROVED != READY !=
PUBLISHED`. Publicación no autorizada.

## Verificación total — fase 7 (2026-08-18)

Ejecutada sobre `09ba097`. Toda cifra proviene de ejecución, no de reporte previo. [CÓDIGO]

### Determinismo
Doble compilación con `manifest_sha256` idéntico: `ea1960efedac4187dfe9da0b3fa64d839c542d8daa84127ab72ae4a57f828b05`. `git status` deja `dist/` y `src/` limpios tras la segunda corrida.

### Gates Python (7/7 PASS)
- `PROMPT_SPEC_OK library_panels=84 all_panels=162 why_panels=162 audience_pairs=81 prompts=14 locales=3 audiences=2 mutations=26`
- `PROMPT_CONTRACTS_OK contracts=27 ids=27 locales=3 audiences=2 mutations=15 warnings=6`
- `EDITORIAL_PARITY_OK routes=54 fields=378 mutations=214 strings=13755`
- `PROMPT_SNAPSHOT_OK entries=648 locales=3 capped_levels=natural`
- `EDITORIAL_SITEMAP_OK canonicals=54 editorial=24 audience_material=24`
- `BREADCRUMBS_OK pages=54 header_home=54 jsonld=54 mutations=5`
- `CONOCE_CHROME_MUTATIONS_OK 15/15 source_variants=54`

### Gates visuales (5/5 PASS)
`PROMPT_SPEC_VISUAL_OK states=120 zoom_200=24 axe=120 mutations=120 why=120 keyboard=12 copy=12 no_js=12` · `check-visual.mjs` rc=0 · `check-method-identity.mjs` rc=0 · `INTRAPAGE_NAVIGATION_OK 54/54` · `check-preference-toggles.mjs` **3/3 PASS**.

Sobre el `Variant state drift` observado en una corrida previa de `check-preference-toggles.mjs`: no se reprodujo en tres corridas consecutivas. Se clasifica como **carrera del checker**, no defecto del paquete. [INFERENCIA]

### Invariante de publicación
`RENDERED_DRAFT` + `publication_authorized: false` en **27/27 contratos** y en los 14 specs que declaran estado. `dist/build-manifest.json` y `dist/build-receipt.json`: cero ocurrencias de `PUBLISHED` y cero `publication_authorized: true`. 10 aserciones de estado en `scripts/build.py`. **Ningún push, ningún despliegue.** [CÓDIGO]

### Contra el encargo original
- **Extensión**: baseline 712.452 c → 1.043.565 c = **×1,465**, bajo el techo de ×2. Ninguna celda excede su tope (`max(2 × baseline, 600)` sobre el nivel autoral). Cero textos encogidos.
- **Divergencia persona/empresa**: 324/324 pares distintos (baseline: 0). Muestreo de tres superficies confirma divergencia de **mecanismo**, no cosmética: `library-05/es` «Pide licencia» → «Exige licencia … y registra el riesgo operativo de [EQUIPO]»; `workbook-07/en` empresa añade `accountable owner` por caso; `workbook-brain-2/pt` reencuadra sujeto y destino (`[DECISÃO OU USO]` → `[PROCESSO]`).
- **Contenido de valor**: muestreo de `why_it_works` confirma criterios decidibles con procedimiento («Honesta está definida en la sesión: declarar el límite sin respaldo puntúa acierto»), casos borde accionables, tradeoffs con su razón y límites que nombran la frontera. No es relleno.
- **Trazabilidad**: 576 claims, **100 % dentro del allowlist** de 6 fuentes (237 `method_internal`, 258 biblioteca/crear-prompts del método, 81 documentación de NotebookLM).
- **Sin claims neurocientíficos**: barrido de 9 raíces sobre los 27 contratos → 3 coincidencias, todas del token de superficie `{{BRAIN_DUMP}}` y de la frase «brain dump prompt». Cero afirmaciones sobre el cerebro. [CÓDIGO]

### Coverage gaps
- 6 warnings `PROMPT_CONTRACT_PROMISE_NO_PRODUCER` en `library-09` (`dod`): falsos positivos calibrados y documentados en el checker; titulillos de dos términos cuyo contenido define la cláusula siguiente del mismo campo.
- Retiro pendiente de `src/prompt-spec-authority-v1.json` y de los `items` de `prompt-library-spec-v1.json`: **conservan lectores** (guardan la puerta semántica vía `validate_prompt_library`, ya no el render).
- Enmienda de E5 (forma con variable `reutilizable por [EQUIPO]`) pendiente de reconciliar en la carta §E congelada; el gate ya la acepta.
- Playwright, Chrome y axe-core son dependencia externa al repo (`../../frames-n0-kit-01`).
- Sin cobertura: lectores de pantalla reales y Lighthouse de campo.
- `src/landing-spec-v2.json` declara `HUMAN_SELECTED_DIRECTION` (preexistente, ajeno a esta elevación); `publication_authorized: false` igualmente.

### Veredicto
**Listo como `RENDERED_DRAFT`. Cero bloqueantes.** Publicación no autorizada; el estado no fue promovido en ningún punto.

## Cierre de selección — límite compacto (2026-08-28)

[PEDAGOGIA] Las 162 celdas muestran ahora una sola frontera de selección
localizada (`Límite` / `Limit` / `Limite`) antes del prompt. El texto se deriva
exactamente de `why_it_works.limits[0]`; la crítica completa permanece en «Por
qué funciona», de modo que la tarjeta ayuda a elegir sin repetir ni inflar el
contenido.

[CÓDIGO] `qa/check-prompt-spec.py` exige 162 límites compactos, etiqueta correcta
y coincidencia exacta con el contrato. La matriz visual muta también ese campo
con un token de 11.340 caracteres y comprueba contención junto con título,
brief y panel.

Gates del freeze local:

- `PROMPT_CONTRACTS_OK contracts=27 ... mutations=15 warnings=6`.
- `PROMPT_SPEC_OK library_panels=84 all_panels=162 why_panels=162 audience_pairs=81`.
- `PROMPT_SNAPSHOT_OK entries=648 locales=3 capped_levels=natural`.
- `EDITORIAL_PARITY_OK routes=54 fields=378 mutations=214 strings=13767`.
- `PROMPT_SPEC_VISUAL_OK states=120 zoom_200=24 axe=120 mutations=120 why=120 keyboard=12 copy=12 no_js=12`.
- `PREFERENCE_TOGGLES_OK routes=54 protocols=2 scenarios=108 clicks=432`.
- Dos builds consecutivos byte-idénticos: `DIST 13869916e57c553211b0624ab15c3a52276c2a70523fe13b67253a2334a34728`; manifest raw `3ea68abcb2094855ad85290338e1f9f18d76d8b998f940712abcbfe399a1e9db`, self `619e72d880dabfcba389f430d434a1f8177edda79be5b9c1dd03f7da18137207`; receipt raw `8bff0a9790f50515173a376d8ebac1602e81e2544d4616ea2c1ce124c0231d2c`, self `757a25b4c84026cd93e3c91cd54beb9a627f3282dfb8b59d17baa563dbd658ae`.

[CONFIG] Google Chrome 151 se cerró de forma intermitente durante dos corridas
headless. El mismo gate pasó completo con Chromium 141 emparejado con Playwright
1.61.1; se clasifica como gap del navegador del host, no como bypass del gate.
El estado continúa `RENDERED_DRAFT`; no hubo push ni publicación.
