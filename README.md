# Ruta Nivel 0 · funnel local Brand Ready

[METODOLOGIA] Producción local y determinista de la ruta Nivel 0: landing,
cuatro módulos y, para cada módulo, Masterclass, Workbook, Playbook y
biblioteca de prompts. La identidad visible es exclusivamente MetodologIA.

## Fuente y salida

```
src/  →  scripts/build.py  →  dist/
```

- `src/`: contratos de intención, `landing-spec-v2`, contenido localizado,
  design system y ledger de claims.
- `src/prompt-contracts/`: los 27 contratos `prompt-intent-contract-v2`. Es la
  única fuente de los prompts renderizados; el build no tiene fallback.
- `src/prompt-artifact-labels-v1.json`: nombres concretos y localizados de los
  documentos que cada prompt recibe y produce; las claves técnicas nunca se
  muestran al lector.
- `src/modules/module-depth-profile-v1.json`: contrato común de profundidad
  para M2–M4. Sus overlays se ligan por ID y hash a los payloads importados;
  nunca los modifican ni usan fallback entre idioma o audiencia.
- `scripts/build.py`: compilador determinista.
- `dist/`: 126 rutas HTML (30 globales/editoriales + 96 recursos), 150 outputs registrados
  totales y receipts hash-bound sobre 87 fuentes de `src/`.

Compilar:

```sh
python3 scripts/build.py
```

Verificar (gates locales, todos sin red):

```sh
python3 qa/check-prompt-contracts.py     # gate del modelo de contratos
python3 qa/check-prompt-experience-v2.py # inputs, Demo y rutas
python3 qa/check-notebooklm-execution.py # Chat vs Fuentes y UI compacta
python3 qa/check-module-prompt-parity-v1.py # N1–N4 de M2–M4 contra la pauta M1
python3 qa/check-curriculum-expansion-v2.py # 16 recursos, 6 variantes y 4 PDF
python3 qa/check-workbook-learning-cycle-v1.py # En clase → Profundización → Consolidación
python3 qa/check-editorial-depth-v1.py   # profundidad M2–M4 y preservación M1
node   qa/check-editorial-depth-visual.mjs # 96 escenarios, axe y densidad
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
`level_spec` propio del que se derivan los niveles 1–4, su `why_it_works` y su
`traceability` contra un allowlist cerrado de 8 fuentes. No existe plantilla
genérica compartida: los niveles superiores de cada intención se escriben desde
el spec de esa intención.

- 27 intenciones: `01`–`10` y `M1`–`M4` (biblioteca), `W01`–`W10` (taller),
  `B1`–`B3` (preparación pre-taller).
- 27 × 3 locales × 2 audiencias × 4 niveles × 2 modos = **1.296** prompts renderizados.
- 162 celdas de contrato y 162 paneles «por qué funciona» en `dist/`.

[PEDAGOGIA] Plantilla usa `<INPUT · ayuda · ejemplo>`, parámetros con defaults
editables y `[]` solo para cláusulas opcionales. Demo resuelve el mismo prompt
con un caso sintético combinado, listo para copiar sin completar inputs.

[PEDAGOGIA] Los cuatro niveles son `natural`, `parameters`, `spec` y `pair`; los
números `1–4` son la única etiqueta visual del selector.

[METODOLOGIA] Las 156 tarjetas de M2–M4 usan la misma progresión semántica:
N1 es una orden ejecutiva; N2 declara parámetros, inputs, marcos, flujo,
límites y salida; N3 es una `SPEC MetodologIA` completa con bloques S/P/E/C,
procedencia y metadata; N4 separa reglas invariantes en `system` de los datos
del caso en `user`. El renderer deriva las cuatro proyecciones desde el overlay
de profundidad y rechaza que el texto heredado de `levels[].body` defina por sí
solo el significado de un nivel.

[PEDAGOGIA] Cada tarjeta modular conserva Plantilla y Demo. Plantilla explica
qué reemplazar; Demo resuelve inputs y artefactos sintéticos sin marcadores
pendientes. El conjunto añade 1.248 prompts copiables verificados en 18 páginas
de módulo, con parámetros y ejemplos localizados para ES/EN/PT.

[METODOLOGIA] Cada intención nombra entre una y tres prácticas que realmente
gobiernan su ejecución. N1 usa solo sus nombres dentro de una orden ejecutiva;
N2–N4 añaden una explicación breve. El gate rechaza listas vacías, duplicadas o
decorativas para evitar *framework theatre*.

[PEDAGOGIA] El panel «por qué funciona» es un `<details>` por intención, locale
y audiencia. Expone criterios de aceptación, casos borde, compensaciones,
supuestos y límites de esa celda. Es lectura opcional: el prompt copiable no
depende de que el lector lo abra.

[PEDAGOGIA] Cada tarjeta anticipa además un único **Límite** compacto, derivado
del primer límite gobernado del contrato. Sirve para descartar una intención
equivocada antes de abrir o copiarla; el análisis completo permanece en el
disclosure y no se duplica en la superficie principal.

[PEDAGOGIA] La progresión usa sustantivos documentales consistentes: **notas
iniciales → plan de estudio → plan de NotebookLM → diagnóstico de fuentes →
plan de investigación → informe de investigación**. Términos internos como
`ENCARGO_DE_*` no forman parte del copy ni del flujo visible.

### Ejecución en NotebookLM

[METODOLOGIA] `src/notebooklm-execution-spec-v1.json` distingue dos superficies
sin alterar el contenido copiable: **Chat** trabaja sobre las fuentes ya
seleccionadas; **Fuentes** ejecuta Fast Research o Deep Research para localizar,
revisar e importar material nuevo. Una consulta puede empezar en Chat para
afinarse, pero la incorporación de fuentes termina en Fuentes. Cada intención
declara su superficie inicial y, cuando aplica, el handoff posterior.

[PEDAGOGIA] La biblioteca presenta esta decisión mediante dos tabs, un filtro
efímero y tarjetas en acordeón. Sin JavaScript, ambas explicaciones y todos los
prompts permanecen disponibles mediante controles HTML nativos.

[CONFIG] `src/prompt-intent-authority-v2.json` (`status: frozen_phase_3`) fija
las anclas de intención y de evidencia por locale, y `boundary.decision_rule`
declara cuándo usar una intención y no su vecina. `qa/check-prompt-contracts.py`
es el gate del modelo: valida esquema, matriz de celdas, mínimos, anclas, carta
de tono, promesas con productor, autoridad citada, ids desnudos, simetría de
fronteras y clones cross-intent, y ejecuta 15 mutaciones internas que deben
fallar antes de aceptar el conjunto.

## Superficies

[PEDAGOGIA] Los módulos 2–4 comparten ahora un contrato funcional de
profundidad: cada concepto se explica, se aplica, se practica, se comprueba y
se transfiere en Masterclass, Workbook, Playbook y Prompts. La primera lectura
permanece compacta; ejemplos, criterios, casos borde y límites viven en capas
desplegables nativas y siguen disponibles sin JavaScript.

[METODOLOGIA] Los payloads importados y los cuatro PDF oficiales permanecen
inmutables. La ampliación editorial se guarda en overlays 3×2 separados,
trazados a las autoridades ya capturadas y limitados a `RENDERED_DRAFT`.

[PEDAGOGIA] El workbook del módulo 1 fija la pauta **En clase → Profundización
→ Consolidación**. Los módulos 2–4 usan esas mismas etapas para orientar, pero
conservan dentro de cada panel sus títulos, decisiones y prácticas propias. La
tercera etapa contiene siempre criterio, evidencia esperada, revisión,
transferencia y rúbrica; el gate permanente valida las 24 páginas Workbook.

[METODOLOGIA] El playbook adopta una composición editorial A²(R)E y presenta la
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
