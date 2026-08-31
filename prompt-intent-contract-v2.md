# Prompt intent contract v2

[METODOLOGIA] Esquema normativo de las 27 intenciones renderizadas en la
biblioteca y el workbook. Cada contrato conserva seis celdas editoriales
(`es|en|pt × persona|empresa`) y añade inputs tipados, parámetros de ejecución,
ajustes opcionales y un handoff explícito. Estado máximo: `RENDERED_DRAFT`.

## Sintaxis pública

- `<TEMA · asunto concreto · ej.: verificar respuestas de IA>`: contenido que
  la persona reemplaza. La clave canónica vive en `inputs[].key`; la etiqueta,
  ayuda, ejemplo y valor Demo están localizados en la misma celda.
- `LONGITUD = concisa`: configuración editable declarada en `parameters`; el
  valor predeterminado siempre pertenece a `choices`.
- `[Si mejora la comprensión, abre con un esquema breve.]`: cláusula gobernada
  en `optional_clauses`; puede ajustarse o borrarse completa.
- Un output nunca se disfraza de input. Las opciones cerradas son parámetros y
  los artefactos heredados usan `source: previous_output`.

## Forma del contrato

El nivel superior usa exactamente: identidad, superficie, fase, gobierno,
`boundary`, `flow`, matriz `locales`, modelo de self-hash y `self_sha256`.
`flow` declara ruta, orden, anterior, siguiente, ramas, artefactos consumidos,
artefacto producido, gate externo, ciclo permitido y capacidad standalone.
Los handoffs usan claves estables en mayúsculas (`BASE_AUDITADA`,
`MAPA_DE_CASOS`, `BORRADOR_DE_ENTREGA`); una salida nunca cambia de nombre por
idioma ni se muestra como un input que el lector deba inventar.

Cada celda contiene los campos editoriales de v1 más:

- `inputs[]`: `key`, `label`, `help`, `example`, `required`, `type`, `source`,
  `demo_value`.
- `parameters[]`: `key`, `label`, `default`, `choices`.
- `optional_clauses[]`: `key`, `text`, `default_enabled`.
- `level_spec.constraints`: decisiones de la intención que antes podían
  confundirse con parámetros editables.
- `level_spec.frameworks`: de una a tres prácticas reconocibles, nombradas y
  explicadas en lenguaje simple. No se admiten listas decorativas ni métodos
  que no gobiernen una acción del prompt.

## Proyecciones

`scripts/build.py` resuelve `(intención, nivel, idioma, audiencia, modo)` sin
fallback:

1. Natural: mandato ejecutivo breve con objetivo, datos, marcos, una acción
   central, entregables y límite principal.
2. Parámetros: configuración, inputs, tarea, marcos, flujo, límites y salida.
3. SPEC: Situación, Pedido, Ejecución y Criterio; los marcos se declaran dentro
   de Ejecución y no alteran la anatomía SPEC.
4. System/User: reglas invariantes y marcos separados de datos y ajustes.

`template` conserva los marcadores. `demo` los sustituye por el caso sintético
“Aprender a aprender con IA mediante Formas de Trabajo de Alto Rendimiento”,
adaptado materialmente a Persona o Empresa. Un fixture Demo es una demostración,
no evidencia de una ejecución real. [INFERENCIA]

## Rutas

- Biblioteca: `01 → 05 → 03 → 04 → 07 → 02 → 06 → 08 → 10 → 09`, con
  M1 antes de 02, M2 antes de 08, M4 antes de 10 y M3 antes de 09.
- Workbook: `B1 → B2 → B3 → W01 → … → W10`; solo W04 puede volver a W03.

Cada prompt puede abrirse por separado. En Plantilla pide únicamente los
artefactos que consume; en Demo usa valores sintéticos explícitos.

## Gates

- `qa/check-prompt-contracts.py`: forma, gobierno, tono, trazabilidad, límites,
  inputs, parámetros, opcionales, entre una y tres prácticas nombradas, flow,
  hashes y mutaciones.
- `qa/check-prompt-experience-v2.py`: 162 tarjetas, 1.296 prompts, resolución
  Demo, sintaxis, rutas, UI de handoff y cero storage adicional.
- `qa/check-prompt-spec.py`: anatomía SPEC y fidelidad por intención.
- `qa/check-prompt-snapshot.py`: snapshot byte-exacto y techo 2×.

[PEDAGOGIA] La ayuda y el ejemplo reducen la carga de inferir qué escribir sin
convertir el prompt en un formulario extenso. [NEUROCIENCIA] El contrato no
introduce afirmaciones neurocientíficas. Publicación no autorizada.
