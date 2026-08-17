# Prompt intent contract v1

Esquema normativo de los 27 contratos de intención de prompt (fase B1 del plan
de elevación). Vive separado de `design-qa.md` porque aquel es un reporte de QA
visual fechado; este documento es autoridad de esquema estable para fases 2–3.

- Ubicación futura de contratos: `src/prompt-contracts/*.json` (uno por intent).
- Validador: `qa/check-prompt-contracts.py` (PASS con nota si el directorio no
  existe o está vacío; los contratos se autoran en fase 3).
- Autoridad de anclas: `src/prompt-intent-authority-v2.json`
  (`status: provisional_until_phase_3`; re-pin con `scripts/repin-authority.py`).
- Estado: `RENDERED_DRAFT`; ningún contrato autoriza publicación.

## Identificadores

| surface | ids | fuente actual del texto natural |
|---|---|---|
| `library` | `01`–`10`, `M1`–`M4` | `src/prompt-library-spec-v1.json` items |
| `workbook` | `W01`–`W10` | `scripts/build.py` `PROMPTS_ES/EN/PT` |
| `workbook_brain` | `B1`–`B3` | `src/workbook-advanced-v1.json` `brain_prompts` |

Total: 27. La línea base de longitud está congelada en
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

Reglas top-level:

1. Conjunto de claves exacto (sin extras, sin faltantes).
2. `surface` ∈ {`library`,`workbook`,`workbook_brain`} y `intent_id` debe
   pertenecer a esa superficie.
3. `state` es siempre `RENDERED_DRAFT` y `publication_authorized` es siempre
   `false` — `RENDERED_DRAFT != HUMAN_APPROVED != READY != PUBLISHED`.
4. `boundary.distinct_from` lista los intents vecinos; `decision_rule` explica
   cuándo usar este y no aquellos (anti-clon semántico entre intents).
5. `self_sha256` = sha256 del JSON canónico ordenado sin `self_sha256` + `\n`
   (modelo `canonical_self` de `scripts/build.py`).

## Celda (`locales.{es,en,pt}.{persona,empresa}`)

Cada locale tiene exactamente dos audiencias. Cada celda:

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
`src/workbook-advanced-v1.json`: es el parámetro `spec` que ya acepta
`structured_variants()` en `scripts/build.py`, de modo que la fase 2 pueda
derivar los niveles 2–4 sin transformación adicional.

## Reglas de validación (qa/check-prompt-contracts.py)

1. **Matriz completa**: 3 locales × 2 audiencias; falta una →
   `PROMPT_CONTRACT_CELL_MATRIX`.
2. **Mínimos de caracteres**: los mismos de
   `prompt-library-spec-v1.json → spec_contract.semantic_specificity.minimum_characters`
   (`purpose` 45 · `when` 35 · `example` 35 · `evidence` 40 · `prompt` 300).
3. **Variables**: ≥ 2 variables `[X]` distintas en `prompt`.
4. **Anclas v2**: por locale, cada ancla `intent` de
   `prompt-intent-authority-v2.json` debe aparecer (NFKD sin acentos,
   casefold) en `prompt` o en `title+purpose`; cada ancla `evidence` en
   `prompt` **y** en `evidence`. Anclas ≥ 4 caracteres, firmas únicas por
   locale.
5. **Clone-gate de audiencia** (`PROMPT_CONTRACT_AUDIENCE_CLONE`): para cada
   campo material (`purpose`,`when`,`example`,`evidence`,`prompt`),
   `persona[campo].casefold() != empresa[campo].casefold()`.
6. **Tope 2×** (`PROMPT_CONTRACT_LENGTH_EXCESS`): `len(prompt)` ≤ 2 × chars del
   texto natural congelado en
   `snapshots/baseline/prompt-snapshot-{locale}.json`
   clave `{surface}/{intent_id}/{locale}/{audience}/natural`.
7. **Trazabilidad** (`PROMPT_CONTRACT_TRACE_INVALID`): cada `source` debe estar
   en el allowlist = `reference_sources[].url` del library spec ∪ `source` de
   los claims de `src/claim-ledger.json` ∪ `"method_internal"`.
8. **Invariantes de estado**: regla 3 de top-level; violación →
   `PROMPT_CONTRACT_GOVERNANCE_INVALID`.
9. **Integridad**: `self_sha256` válido (`PROMPT_CONTRACT_SELF_DRIFT`); ids
   duplicados entre archivos → `PROMPT_CONTRACT_DUPLICATE_INTENT`.

El validador incluye 8 mutaciones internas que deben fallar (clone de
audiencia, exceso 2×, ancla ausente, pin falso, traza fuera de allowlist,
audiencia única, publicación autorizada, id fuera de superficie); si alguna
pasa, el gate aborta.

## Integración con build (fase 2, no activa)

`scripts/build.py` expone `compose_prompt_documents(contracts, intent_authority)`:
arma dos documentos sintéticos (persona/empresa) con `items` por locale
compatibles con `validate_prompt_library(document, authority_document,
prompt_ids=…, intent_authority_binding=…, authority_options=…)`. Los defaults
de ambos validadores reproducen el comportamiento v1 exacto; el build activo
no consume contratos ni la autoridad v2 en esta fase.

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
