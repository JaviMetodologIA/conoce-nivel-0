# Prompt intent contract v1

Esquema normativo de los **27 contratos de intención** de `src/prompt-contracts/`.
Escrito en la fase 1 y actualizado tras el cutover: hoy los contratos existen, el
build los consume y las reglas que aquí se listan son las que el gate aplica.
Este documento es la referencia para escribir un contrato nuevo.

- Contratos: `src/prompt-contracts/*.json` — uno por intención, 27 archivos.
- Validador: `qa/check-prompt-contracts.py` (standalone, stdlib). Un directorio
  ausente o vacío sigue siendo PASS con nota `contracts_dir_empty_pass`.
- Autoridad de anclas: `src/prompt-intent-authority-v2.json`
  (`status: frozen_phase_3`). Re-pin con `scripts/repin-authority.py`.
- Consumidor: `scripts/build.py` — `load_prompt_contracts()` y
  `compose_prompt_documents()`; `fallback_policy: forbidden`.
- Estado: `RENDERED_DRAFT`; ningún contrato autoriza publicación.

## Identificadores

| surface | ids | superficie renderizada |
|---|---|---|
| `library` | `01`–`10`, `M1`–`M4` | biblioteca de prompts |
| `workbook` | `W01`–`W10` | hojas del taller |
| `workbook_brain` | `B1`–`B3` | preparación pre-taller |

Total: 27 intenciones × 3 locales × 2 audiencias = 162 celdas; × 4 niveles = 648
variantes renderizadas. La línea base de longitud está congelada en
`snapshots/baseline/prompt-snapshot-{es,en,pt}.json` con claves
`{surface}/{id}/{locale}/{audience}/{level}`.

## Top level

```json
{
  "schema_version": "prompt-intent-contract-v1",
  "intent_id": "01",
  "surface": "library",
  "phase": "Aprender",
  "state": "RENDERED_DRAFT",
  "publication_authorized": false,
  "boundary": {"distinct_from": ["02"], "decision_rule": "…"},
  "locales": {"es": {…}, "en": {…}, "pt": {…}},
  "self_hash_model": "sha256(sorted-json-without-self_sha256)",
  "self_sha256": "…"
}
```

1. Conjunto de claves exacto: sin extras, sin faltantes
   (`PROMPT_CONTRACT_SHAPE_INVALID`).
2. `surface` ∈ {`library`,`workbook`,`workbook_brain`} y `intent_id` debe
   pertenecer a esa superficie (`PROMPT_CONTRACT_SURFACE_INVALID`).
3. `state` siempre `RENDERED_DRAFT` y `publication_authorized` siempre `false`
   (`PROMPT_CONTRACT_GOVERNANCE_INVALID`).
   `RENDERED_DRAFT != HUMAN_APPROVED != READY != PUBLISHED`.
4. `phase` es una cadena no vacía (`PROMPT_CONTRACT_PHASE_INVALID`).
5. `boundary` tiene exactamente `distinct_from` (lista) y `decision_rule`
   (cadena no vacía) (`PROMPT_CONTRACT_BOUNDARY_INVALID`).
6. `self_sha256` = sha256 del JSON canónico ordenado sin `self_sha256` + `\n`
   (`PROMPT_CONTRACT_SELF_DRIFT`).

## Celda (`locales.{es,en,pt}.{persona,empresa}`)

```json
{
  "title": "…", "purpose": "…", "when": "…", "example": "…",
  "evidence": "…", "prompt": "…",
  "level_spec": {
    "role": "…", "spec_role": "…", "objective": "…",
    "parameters": [["clave", "valor"], …],
    "workflow": ["…"], "guardrails": ["…"], "output": ["…"],
    "dod": "…", "edge_cases": ["…"]
  },
  "why_it_works": {
    "acceptance_criteria": ["…"], "edge_cases": ["…"],
    "tradeoffs": ["…"], "assumptions": ["…"], "limits": ["…"]
  },
  "traceability": [{"claim": "…", "source": "…"}]
}
```

`level_spec` tiene la misma forma que `brain_prompt_specs` de
`src/workbook-advanced-v1.json`: es el parámetro `spec` que acepta
`structured_variants()` en `scripts/build.py`. **De él se derivan los niveles
2–4 de esa celda**; no hay plantilla genérica compartida entre intenciones.
`why_it_works` alimenta el panel expandible «por qué funciona» que ve el lector.

Claves obligatorias y no vacías: celda (`PROMPT_CONTRACT_CELL_SHAPE_INVALID`),
`level_spec` (`PROMPT_CONTRACT_LEVEL_SPEC_INVALID`), pares de `parameters` de
exactamente dos cadenas no vacías
(`PROMPT_CONTRACT_LEVEL_SPEC_PARAMETERS_INVALID`), `why_it_works` con sus cinco
listas no vacías (`PROMPT_CONTRACT_WHY_INVALID`).

## Reglas de validación

Todas evalúan por substring sobre NFKD sin acentos + casefold, con corchetes
literales. Salvo indicación, un fallo aborta.

### Estructura y matriz

1. **Matriz completa**: 3 locales × 2 audiencias (`PROMPT_CONTRACT_CELL_MATRIX`).
2. **Ids únicos** entre archivos (`PROMPT_CONTRACT_DUPLICATE_INTENT`).

### Contenido material

3. **Mínimos de caracteres** de
   `prompt-library-spec-v1.json → spec_contract.semantic_specificity.minimum_characters`
   (`purpose` 45 · `when` 35 · `example` 35 · `evidence` 40 · `prompt` 300) →
   `PROMPT_CONTRACT_FIELD_GENERIC`.
4. **Variables**: ≥ 2 variables `[X]` distintas en `prompt`
   (`PROMPT_CONTRACT_VARIABLES`).
5. **Regresión de audiencia**: para cada campo material
   (`purpose`,`when`,`example`,`evidence`,`prompt`),
   `persona[campo].casefold() != empresa[campo].casefold()`
   (`PROMPT_CONTRACT_AUDIENCE_CLONE`). Se evalúa **antes** que el contenido, para
   que una celda clonada reporte el clon y no el defecto de tono que el clon
   produce.
6. **Clon cross-intent**: dentro de una columna (locale, audiencia), ningún campo
   material puede repetirse entre dos intenciones
   (`PROMPT_CONTRACT_CROSS_INTENT_CLONE`). Cubre el caso de una celda eco que
   copia su original (`W08` vs `08`), invisible a la regla 5.

### Anclas de intención y evidencia (autoridad v2)

7. Cada ancla `intent` (≥ 4 caracteres) debe aparecer en `prompt` **o** en
   `title+purpose` (`PROMPT_CONTRACT_INTENT_ANCHOR_MISSING`), y **al menos una**
   debe estar simultáneamente en `prompt` **y** en `title+purpose`
   (`PROMPT_CONTRACT_INTENT_DIVERGENCE`). Armonizado con
   `validate_prompt_library` de `scripts/build.py`, que es la lectura estricta y
   gana el conflicto: la intención que el lector ve en la tarjeta no puede
   divergir de la que ejecuta el prompt pegado.
8. Cada ancla `evidence` debe aparecer en `prompt` **y** en `evidence`
   (`PROMPT_CONTRACT_EVIDENCE_ANCHOR_MISSING`).
9. La autoridad misma se valida al cargar: esquema, `status` ∈
   {`provisional_until_phase_3`,`frozen_phase_3`}, self hash, matriz de 27 ids
   por locale y firmas de ancla únicas
   (`PROMPT_CONTRACT_AUTHORITY_SHAPE_INVALID`, `…_SELF_DRIFT`,
   `…_MATRIX_INVALID`, `…_SIGNATURE_CLONE`).

### Tope de longitud

10. `len(prompt) ≤ max(2 × baseline, 600)`, con `baseline` = caracteres del
    texto natural congelado en la clave
    `{surface}/{intent_id}/{locale}/{audience}/natural`
    (`PROMPT_CONTRACT_LENGTH_EXCESS`; baseline ausente →
    `PROMPT_CONTRACT_BASELINE_MISSING`).

    **Por qué el piso de 600.** La regla 2× pura es insatisfacible sobre las
    líneas base cortas del taller (239–286 c ⇒ topes de 478–572 c). Los tokens
    de calidad obligatorios de un prompt elevado —piso epistémico (~31 c),
    negación por mecanismo (55–100 c), variable organizacional E1 (8–10 c)—
    consumen 20–29 % de un tope de 478 c y no dejan espacio para las reglas que
    la elevación existe para codificar. 600 es el valor mínimo que mantiene
    autorable las 30 celdas de `W06`–`W10`. Las líneas base largas (`01`–`M4`,
    `B1`–`B3`) siguen gobernadas por el término 2×, más estricto: hoy 132 de las
    162 celdas caen bajo 2× y 30 bajo el piso.

### Carta de tono §E (mecanizada)

11. `PROMPT_CONTRACT_TONE_MARKER`. La carta congelada vive en
    `prompt-elevation-briefs.md §E` y está espejada en el encabezado del
    validador. Resumen operativo:

    - `persona`: **P3 obligatorio** (cero variables organizacionales en
      `prompt`), ≥ 2 marcadores de {P1 primera persona, P2 posesivos, P6 cero
      léxico de gobernanza} en `prompt`, y ≥ 1 marcador P4 en `purpose`/`when`.
    - `empresa`: **E1 obligatorio** (≥ 1 variable organizacional en `prompt`),
      ≥ 2 marcadores de {E2 marco colectivo, E3 gobernanza, E4 riesgo
      organizacional, E5 entregable compartible} en `prompt`, y ≥ 1 de ellos en
      `purpose`/`when`.
    - **Excepción de anclas**: un ancla de la autoridad v2 prevalece sobre
      cualquier prohibición de la carta.
    - **E2–E5 se puntúan sobre `prompt` solamente**, aunque la prosa de E3 diga
      «en prompt o evidence». La escapatoria por `evidence` fue lo que dejó pasar
      cuatro celdas defectuosas en revisión adversarial.
    - **E3 no aplica a intenciones sin autoridad de decisión** (caso nombrado:
      `02`, coach basado en fuentes). Exigir léxico de gobernanza donde ninguna
      instrucción lo produce es exactamente la promesa sin productor que R8
      prohíbe. No hay caso especial en el código: el umbral de ≥ 2 se cubre con
      E2, E4 y E5. E1 y el umbral no se relajan.
    - **E5 acepta la forma variable** (`reutilizable por [EQUIPO]` /
      `reusable by [TEAM]` / `reutilizavel pela [EQUIPE]`) además de la literal
      con artículo. Es la forma que escribe un prompt `empresa` bien formado.

### R8 · no hay promesa sin productor

12. `PROMPT_CONTRACT_PROMISE_NO_PRODUCER`. Todo término de contenido prometido
    en `evidence` y en `level_spec.dod` debe ser producido por una instrucción de
    la **misma celda** (`prompt` + `level_spec.workflow` + `level_spec.output`).
    Coincidencia por raíz de 4 caracteres, por fragmento (separado por
    puntuación y conjunciones) y con **un** productor basta, no todos.
    Fragmentos con ≥ 3 términos de contenido **bloquean**; los de 2 términos se
    reportan como `WARN:` porque a ese tamaño suelen ser un par de adjetivos de
    calidad. Hoy el corpus deja 6 warnings, todos en `09`/`dod`.

### R9 · autoridad citada = autoridad existente

13. `PROMPT_CONTRACT_AUTHORITY_UNRESOLVED`. En `why_it_works` y en los `claim`
    de `traceability`: todo archivo citado (`*.json|md|py|yml`) debe existir en el
    repo, y toda prohibición atribuida al claim ledger debe corresponder a un
    `prohibited_claims` real.

### R10/R11 · ids

14. **Id desnudo prohibido en texto material** (`title` y los cinco campos
    materiales): `PROMPT_CONTRACT_BARE_ID`. El `prompt` es texto que el usuario
    pega en un chat; un id ahí es una referencia colgante. La negación se escribe
    **por mecanismo**, no por id. Los ids siguen siendo legales en `boundary`,
    `guardrails`, `limits` y `assumptions`. Techo aceptado: el `10` desnudo se
    ignora en texto material porque es indistinguible del cardinal diez.
15. **Id nombrado debe ser frontera declarada**: un id que aparezca en
    `guardrails` o en `why_it_works.limits` debe estar en
    `boundary.distinct_from` de este contrato (o ser el propio)
    (`PROMPT_CONTRACT_ID_NOT_IN_BOUNDARY`).
16. **Simetría de frontera**: si `A` declara a `B` vecino distinto y `B` está en
    disco, `B` debe declarar a `A` (`PROMPT_CONTRACT_ASYMMETRIC_BOUNDARY`).

### Trazabilidad

17. `traceability` es una lista no vacía de `{claim, source}`; `source` debe
    pertenecer al allowlist = `reference_sources[].url` del library spec ∪
    `source` de los claims de `src/claim-ledger.json` ∪ `"method_internal"`
    (8 valores hoy) → `PROMPT_CONTRACT_TRACE_INVALID`.

## Códigos de error del validador

`PROMPT_CONTRACT_SHAPE_INVALID` · `PROMPT_CONTRACT_SURFACE_INVALID` ·
`PROMPT_CONTRACT_GOVERNANCE_INVALID` · `PROMPT_CONTRACT_PHASE_INVALID` ·
`PROMPT_CONTRACT_BOUNDARY_INVALID` · `PROMPT_CONTRACT_SELF_DRIFT` ·
`PROMPT_CONTRACT_CELL_MATRIX` · `PROMPT_CONTRACT_CELL_SHAPE_INVALID` ·
`PROMPT_CONTRACT_LEVEL_SPEC_INVALID` ·
`PROMPT_CONTRACT_LEVEL_SPEC_PARAMETERS_INVALID` ·
`PROMPT_CONTRACT_WHY_INVALID` · `PROMPT_CONTRACT_AUDIENCE_CLONE` ·
`PROMPT_CONTRACT_CROSS_INTENT_CLONE` · `PROMPT_CONTRACT_FIELD_GENERIC` ·
`PROMPT_CONTRACT_VARIABLES` · `PROMPT_CONTRACT_INTENT_ANCHOR_MISSING` ·
`PROMPT_CONTRACT_INTENT_DIVERGENCE` ·
`PROMPT_CONTRACT_EVIDENCE_ANCHOR_MISSING` ·
`PROMPT_CONTRACT_BASELINE_MISSING` · `PROMPT_CONTRACT_LENGTH_EXCESS` ·
`PROMPT_CONTRACT_TRACE_INVALID` · `PROMPT_CONTRACT_TONE_MARKER` ·
`PROMPT_CONTRACT_PROMISE_NO_PRODUCER` (bloquea con ≥ 3 términos, `WARN:` con 2) ·
`PROMPT_CONTRACT_AUTHORITY_UNRESOLVED` · `PROMPT_CONTRACT_BARE_ID` ·
`PROMPT_CONTRACT_ID_NOT_IN_BOUNDARY` ·
`PROMPT_CONTRACT_ASYMMETRIC_BOUNDARY` · `PROMPT_CONTRACT_DUPLICATE_INTENT` ·
`PROMPT_CONTRACT_AUTHORITY_SHAPE_INVALID` ·
`PROMPT_CONTRACT_AUTHORITY_SELF_DRIFT` ·
`PROMPT_CONTRACT_AUTHORITY_MATRIX_INVALID` ·
`PROMPT_CONTRACT_AUTHORITY_SIGNATURE_CLONE`.

Resultado agregado: `PROMPT_CONTRACTS_OK …` o `PROMPT_CONTRACTS_FAILED …`.
Fallos del arnés: `PROMPT_CONTRACT_MUTATION_PASSED` (un mutante pasó) y
`PROMPT_CONTRACT_MUTATION_WRONG_REJECTION` (falló por el código equivocado).

## Arnés de mutaciones

El validador construye un contrato sintético válido (control positivo) y le
aplica **15 mutaciones** que deben fallar con el código esperado:
`audience_clone` · `length_excess_2x` · `anchor_missing` ·
`intent_anchor_only_in_prompt` · `false_self_pin` · `trace_outside_allowlist` ·
`single_audience` · `publication_flag` · `surface_id_mismatch` ·
`tone_charter_single_marker` · `promise_without_producer` ·
`invented_authority` · `bare_id_in_prompt` · `asymmetric_boundary` ·
`cross_intent_clone`. Si alguna pasa, el gate aborta.

## Cobertura no implementada aquí

`minimum_lexical_diversity` (0.7) y `minimum_anchor_count` (2) están declarados
en `spec_contract.semantic_specificity` y **no** los aplica este validador. Sí se
aplican a los 27 contratos en tiempo de build, vía
`compose_prompt_documents()` → `validate_prompt_library()` en `scripts/build.py`.
Quien escriba un contrato nuevo debe correr **también** el build, no solo el
gate standalone.

## Integración con el build (activa)

`scripts/build.py` carga los contratos en `PROMPT_CONTRACTS`, los valida con
`validate_prompt_spec_authority(PROMPT_INTENT_AUTHORITY, …)` y somete cada
audiencia a `validate_prompt_library()` mediante
`compose_prompt_documents(contracts, intent_authority)`, que arma dos documentos
sintéticos (`persona`/`empresa`) con `items` por locale. De ahí salen los cuatro
niveles (`natural`, `parameters`, `spec`, `pair`) y el panel `why`. El manifest y
el receipt re-emiten el binding con `contract_count`, `rendered_cells`,
`fallback_policy: forbidden`, `why_panel: true` y los 27 `self_sha256`.

## Cómo escribir un contrato nuevo

1. Copiar el archivo de una intención de la misma superficie y vaciar las celdas.
2. Fijar `intent_id`, `surface`, `phase` y `boundary` — y **actualizar el
   `distinct_from` del vecino**, o la simetría falla.
3. Escribir las 6 celdas con texto materialmente distinto entre `persona` y
   `empresa` y distinto de toda otra intención de la misma columna.
4. Revisar que cada promesa de `evidence`/`dod` tenga un productor en
   `prompt`/`workflow`/`output` (R8), que toda autoridad citada exista (R9) y que
   ninguna negación use un id desnudo.
5. Sellar: recalcular `self_sha256` sobre el JSON canónico sin ese campo.
6. Correr `python3 qa/check-prompt-contracts.py` y después
   `python3 scripts/build.py`.

## Ejemplo mínimo (es, recortado)

```json
{
  "schema_version": "prompt-intent-contract-v1",
  "intent_id": "01",
  "surface": "library",
  "phase": "Aprender",
  "state": "RENDERED_DRAFT",
  "publication_authorized": false,
  "boundary": {
    "distinct_from": ["02"],
    "decision_rule": "Usar 01 cuando el objetivo es delimitar una investigación nueva."
  },
  "locales": {
    "es": {
      "persona": {
        "title": "Blueprint de investigación",
        "purpose": "Convierte un tema amplio en una investigación delimitada…",
        "when": "necesitas comprender un tema antes de decidir o producir.",
        "example": "IA generativa para un equipo comercial no técnico.",
        "evidence": "preguntas, alcance, fuentes prioritarias, tensiones…",
        "prompt": "Quiero comprender [TEMA] para [DECISIÓN O RESULTADO]…",
        "level_spec": {"role": "…", "spec_role": "…", "objective": "…",
          "parameters": [["profundidad", "operativa"]], "workflow": ["…"],
          "guardrails": ["…"], "output": ["…"], "dod": "…", "edge_cases": ["…"]},
        "why_it_works": {"acceptance_criteria": ["…"], "edge_cases": ["…"],
          "tradeoffs": ["…"], "assumptions": ["…"], "limits": ["…"]},
        "traceability": [{"claim": "…", "source": "method_internal"}]
      },
      "empresa": {"…": "misma forma, texto materialmente distinto"}
    },
    "en": {"…": "…"}, "pt": {"…": "…"}
  },
  "self_hash_model": "sha256(sorted-json-without-self_sha256)",
  "self_sha256": "…"
}
```

Estado: `RENDERED_DRAFT`. Publicación no autorizada.
