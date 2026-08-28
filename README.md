# Ruta Nivel 0 · funnel local Brand Ready

[METODOLOGIA] Producción local y determinista de la landing, masterclass,
workbook, playbook y biblioteca de prompts de la primera clase. La identidad
visible es exclusivamente MetodologIA.

## Fuente y salida

```
src/  →  scripts/build.py  →  dist/
```

- `src/`: contratos de intención, `landing-spec-v2`, contenido localizado,
  design system y ledger de claims.
- `src/prompt-contracts/`: los 27 contratos `prompt-intent-contract-v1`. Es la
  única fuente de los prompts renderizados; el build no tiene fallback.
- `scripts/build.py`: compilador determinista.
- `dist/`: 54 rutas HTML (9 páginas × 3 locales × 2 audiencias), 75 outputs
  totales y receipts hash-bound sobre 72 fuentes de `src/`.

Compilar:

```sh
python3 scripts/build.py
```

Verificar (gates locales, todos sin red):

```sh
python3 qa/check-prompt-contracts.py     # gate del modelo de contratos
python3 qa/check-breadcrumbs.py
python3 qa/check-conoce-chrome.py
python3 qa/check-editorial-parity.py
python3 qa/check-editorial-sitemap.py
node   qa/check-prompt-spec-visual.mjs   # requiere Playwright + axe
```

Utilidades: `python3 scripts/repin-authority.py src/prompt-intent-authority-v2.json`
imprime el triple pin de una autoridad; `python3 scripts/export-prompt-snapshot.py`
re-exporta la línea base de longitud desde `dist/`.

## Modelo de prompts: contratos por intención

[METODOLOGIA] Cada intención es un contrato JSON con 6 celdas: 3 locales
(`es`/`en`/`pt`) × 2 audiencias (`persona`/`empresa`). Cada celda declara sus
campos materiales (`purpose`, `when`, `example`, `evidence`, `prompt`), su
`level_spec` propio del que se derivan los niveles 2–4, su `why_it_works` y su
`traceability` contra un allowlist cerrado de 8 fuentes. No existe plantilla
genérica compartida: los niveles superiores de cada intención se escriben desde
el spec de esa intención.

- 27 intenciones: `01`–`10` y `M1`–`M4` (biblioteca), `W01`–`W10` (taller),
  `B1`–`B3` (preparación pre-taller).
- 27 × 3 locales × 2 audiencias × 4 niveles = **648** variantes renderizadas.
- 162 celdas de contrato y 162 paneles «por qué funciona» en `dist/`.

[PEDAGOGIA] Los cuatro niveles son `natural`, `parameters`, `spec` y `pair`; los
números `1–4` son la única etiqueta visual del selector.

[PEDAGOGIA] El panel «por qué funciona» es un `<details>` por intención, locale
y audiencia. Expone criterios de aceptación, casos borde, compensaciones,
supuestos y límites de esa celda. Es lectura opcional: el prompt copiable no
depende de que el lector lo abra.

[PEDAGOGIA] Cada tarjeta anticipa además un único **Límite** compacto, derivado
del primer límite gobernado del contrato. Sirve para descartar una intención
equivocada antes de abrir o copiarla; el análisis completo permanece en el
disclosure y no se duplica en la superficie principal.

[CONFIG] `src/prompt-intent-authority-v2.json` (`status: frozen_phase_3`) fija
las anclas de intención y de evidencia por locale, y `boundary.decision_rule`
declara cuándo usar una intención y no su vecina. `qa/check-prompt-contracts.py`
es el gate del modelo: valida esquema, matriz de celdas, mínimos, anclas, carta
de tono, promesas con productor, autoridad citada, ids desnudos, simetría de
fronteras y clones cross-intent, y ejecuta 15 mutaciones internas que deben
fallar antes de aceptar el conjunto.

## Superficies

[PEDAGOGIA] El workbook implementa tres rutas: sesión guiada, profundización y
consolidación. La masterclass pausa en las diapositivas 9–13 y enlaza a los
pasos 1–5.

[METODOLOGIA] El playbook adopta una composición editorial A³ y presenta la
carta de sus cuatro fundadores con retratos públicos locales, procedencia,
derechos y hashes declarados. La fuente CSS contiene una sola autoridad para
esta experiencia.

[METODOLOGIA] La landing implementa ocho capítulos: entrada, tensión, ruta,
demostración, experiencia, resultados, método y convocatoria. La inscripción es
la conversión principal y los dos recursos abiertos funcionan como demostración
y motor orgánico.

[CONFIG] El selector de tensión es efímero; no guarda ni transmite la selección.
La landing no contiene tracking, píxeles ni grabación de sesión.

[NEUROCIENCIA] El paquete no incorpora claims neurocientíficos.

[SUPUESTO] La revisión humana puede solicitar ajustes editoriales antes de
cualquier promoción.

[INFERENCIA] Los componentes probados en este piloto podrán generalizarse
después de la verificación independiente; no se consideran todavía una skill
publicada.

Estado: `RENDERED_DRAFT`. Publicación no autorizada.
