# Inventario golden · biblioteca de prompts del módulo de referencia

Estado: `RENDERED_DRAFT`
Autoridad: `src/module-01-prompt-inventory-v1.json`
Módulo: `ia-panorama` · Clase 01 · “IA: qué está pasando y cómo sacarle provecho”

## Dos perímetros que no deben confundirse

| Perímetro | Contratos | Composición | Textos copiables en ES/EN/PT × Persona/Empresa |
|---|---:|---|---:|
| Biblioteca visible | 14 | 10 prompts de trabajo + 4 metaprompts | 672 |
| Workbook | 13 | 3 de preparación + 10 de recorrido | 624 |
| Módulo completo | 27 | biblioteca + workbook | 1.296 |

La paridad exigida en esta unidad corresponde a la **biblioteca visible**. La
paridad integral del workbook queda registrada como un gate separado; no se
presenta la primera como si acreditara la segunda.

## Composición de la biblioteca

| Slot | Familia | Superficie NotebookLM | Función |
|---|---|---|---|
| 01 | Aprender | Fuentes · Deep Research | Plan inicial de investigación |
| 02 | Aprender | Chat · fuentes seleccionadas | Coach basado en fuentes |
| 03 | Aprender | Fuentes · Deep Research | Investigación profunda |
| 04 | Aprender | Chat · fuentes seleccionadas | Verificación cruzada |
| 05 | Aprehender | Chat · fuentes seleccionadas | Auditoría de relevancia |
| 06 | Aprehender | Chat · fuentes seleccionadas | Generador de práctica |
| 07 | Aprehender | Chat · fuentes seleccionadas | Auditoría del Notebook |
| 08 | Aprehender | Chat · fuentes seleccionadas | Evaluador progresivo |
| 09 | (R)Evolucionar | Chat · fuentes seleccionadas | Simulador de entrevista |
| 10 | (R)Evolucionar | Chat · fuentes seleccionadas | Coach de presentación |
| M1 | Meta | Chat · fuentes seleccionadas | Generador de coach |
| M2 | Meta | Chat · fuentes seleccionadas | Generador de evaluador |
| M3 | Meta | Chat · fuentes seleccionadas | Generador de entrevistador |
| M4 | Meta | Chat · fuentes seleccionadas | Generador de preparador |

Distribución invariable: `4 aprender + 4 aprehender + 2 evolucionar + 4 meta`,
con `12 Chat + 2 Fuentes` por variante.

## Anatomía visual de una tarjeta

El golden no es solo contenido: fija un orden de lectura compacto y repetible.

1. Resumen cerrado con número, familia, título, propósito y superficie de
   NotebookLM.
2. Al abrir, bloque lateral **Antes de copiar** con `Recibe → Produce`, gate
   externo cuando aplica y acceso al siguiente paso.
3. Selector **Plantilla | Demo** y leyenda breve de sintaxis.
4. Disclosure de inputs con nombre, explicación y ejemplo localizado.
5. Tabs **N1 Directo · N2 Estructurado · N3 Especificado · N4 Orquestado**.
6. Un solo prompt visible, control de copia ligado al nivel y modo activos.
7. Disclosure final **Por qué funciona** con cinco grupos verificables.

La pauta usa navy, dorado y superficies claras/oscuras del sistema actual;
acordeones y tabs preservan densidad sin ocultar contenido esencial cuando no
hay JavaScript. La igualdad exigida a M2–M4 es de esta anatomía, no de un DOM o
copy literalmente idénticos.

## Versiones de cada prompt

1. **N1 · Directo:** objetivo, datos, frameworks, orden, entregables y límite.
2. **N2 · Estructurado:** parámetros, inputs, opcionales, tarea, frameworks,
   flujo, límites y salida esperada.
3. **N3 · Especificado:** SPEC MetodologIA 2.0 con S/P/E/C, Definition of Done,
   procedencia, metadata y política de razonamiento privado.
4. **N4 · Orquestado:** pareja `System/User`; separa reglas invariantes de los
   datos y parámetros del caso.

El nivel indica cuánto contrato necesita la tarea. No implica que N4 sea
“mejor” que N1 para una solicitud simple.

## Plantilla y Demo

**Plantilla** conserva:

- inputs explicados como `<TEMA · qué escribir · ej.: verificar una respuesta>`;
- parámetros editables como `LONGITUD = concisa`;
- instrucciones opcionales completas entre `[]`, eliminables sin romper la frase.

**Demo**:

- resuelve todos los inputs con valores sintéticos localizados;
- conserva el objetivo, los límites y los criterios de la Plantilla;
- no deja `<...>`, `[...]` ni `{{...}}`;
- funciona de forma autónoma sin fingir evidencia real.

## Profundidad mínima por variante

- 2–6 inputs usados realmente.
- 4–6 parámetros; longitud, estructura, tono y profundidad como base.
- 5–6 pasos de workflow.
- Exactamente 3 frameworks aplicados.
- 3–5 guardrails.
- 3–4 criterios de aceptación.
- Exactamente 3 casos borde en el SPEC.
- 3–5 registros de trazabilidad claim → fuente.
- “Por qué funciona” con aceptación, casos borde, trade-offs, supuestos y límites.

## Grafo de la demostración

Ruta principal:

```text
01 → 05 → 03 → 04 → 07 → 02 → 06 → 08 → 10 → 09
```

Ramas reutilizables:

```text
07 → M1 → 02
06 → M2 → 08
08 → M4 → 10
10 → M3 → 09
```

Cada prompt puede usarse solo si se aporta el artefacto que declara recibir.
La Demo usa un artefacto sintético gobernado; nunca inventa una salida previa.

## Definition of Done para M2–M4

- 14 tarjetas por módulo: 10 de trabajo y 4 meta.
- 6 variantes explícitas, sin fallback entre idioma o audiencia.
- 4 niveles y 2 modos por tarjeta: 112 textos copiables por página.
- Misma anatomía, nombres, superficies y controles que el golden.
- Inputs y parámetros específicos de la intención; se prohíbe `CONTEXTO` como
  marcador único universal.
- Copy temático propio del módulo; se prohíbe reutilizar literalmente M1.
- Persona y Empresa cambian responsable, alcance, evidencia y decisión.
- Todos los outputs resuelven un consumidor o un cierre declarado.
- Build y QA deben fallar ante conteos 8/10/8, metaprompts ausentes, Demo sin
  resolver, SPEC incompleto o formatos DOM distintos.

[PEDAGOGIA] La igualdad es de arquitectura, utilidad y profundidad; no de número
de palabras ni de copy literal.

[NEUROCIENCIA] Este inventario no introduce afirmaciones cognitivas ni promete
porcentajes de mejora.

[SUPUESTO] “Módulo 0” designa aquí el módulo inicial que el código identifica
como `ia-panorama` y la interfaz presenta como Clase 01.
