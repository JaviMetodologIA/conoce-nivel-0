# Fase B3 · Crítica adversarial por intención — briefs de elevación

Estado: `RENDERED_DRAFT`. Ningún brief autoriza publicación. Los contratos de
fase 4 se escriben contra este documento; la carta de tono (§C) y las anclas
(§D) quedan **congeladas** al cierre de esta fase. [CONFIG]

Fuentes leídas: `snapshots/baseline/prompt-snapshot-{es,en,pt}.json` (textos
`natural` de los 27 × 2 audiencias × 3 locales), `src/prompt-library-spec-v1.json`,
`src/workbook-prompts-v1.json`, `src/workbook-advanced-v1.json`,
`prompt-intent-contract-v1.md`, `src/prompt-intent-authority-v2.json`,
`src/claim-ledger.json`, `qa/check-prompt-contracts.py`. [DOC]

## Hallazgos transversales (aplican a los 27; no se repiten por brief)

1. **Clon de audiencia total.** En los tres locales, `persona` y `empresa` son
   byte-idénticos en los 27 intents (verificado mecánicamente: 0 diferencias).
   [CÓDIGO] La celda empresa hoy no existe: es la misma pieza con otra
   etiqueta. Fase 4 debe diferenciar los 5 campos materiales
   (`purpose,when,example,evidence,prompt`) o `PROMPT_CONTRACT_AUDIENCE_CLONE`
   bloquea.
2. **Déficit de variables.** El contrato exige ≥2 variables `[X]` distintas en
   `prompt`. Conteo actual (es): W02=0, W03=1, W05=1, W07=1, W08=1, B1=0,
   B3=0. [CÓDIGO] W04 tiene 2 "variables" que en realidad son tokens de
   veredicto (`[BASE SUFICIENTE]`, `[REPETIR INVESTIGACIÓN]`), no huecos a
   rellenar: pasan el regex pero engañan al usuario; fase 4 debe añadir
   variables reales sin eliminar los tokens de veredicto.
3. **Criterios de éxito ausentes.** Casi ningún texto define cuándo la salida
   es aceptable (excepciones parciales: 01 "criterio observable", M4
   "listo o coverage_gap"). Los `why_it_works.acceptance_criteria` de fase 4
   deben ser observables, no adjetivos ("honesta", "realista", "concisa" son
   promesas no verificables que abundan hoy). [INFERENCIA]
4. **Presupuesto 2×.** `len(prompt)` ≤ 2× el natural congelado por celda.
   Cada brief anota el presupuesto es; los briefs con presupuesto <520c
   (W06, W07, W08, W09) exigen diferenciación de audiencia con tokens cortos.
   [CONFIG]
5. **Claims.** Prohibido introducir claims neurocientíficos nuevos y prohibido
   `accuracy guarantee` / `replacement of human judgment`
   (`src/claim-ledger.json → prohibited_claims`). Trazabilidad solo contra el
   allowlist (2 `reference_sources` + fuentes del ledger + `method_internal`).
   [CONFIG]
6. **Señales de locale.** Los marcadores de tono usan solo léxico nativo de
   cada locale; `forbidden_locale_signals` del library spec sigue vigente.
   [CONFIG]

Formato de cada brief: **Fallas** · **Dirección de elevación** (alimenta
`why_it_works` y `level_spec`, NO son los prompts finales) · **Marcadores de
audiencia** · (workbook W01–W05) **Eco** · **Anclas a preservar** (fase 4 debe
conservarlas como substring NFKD-sin-acentos-casefold; las `evidence` en
`prompt` **y** `evidence`).

---

## A. Briefs library (01–10, M1–M4)

### 01 · Blueprint de investigación (Aprender) — presupuesto es 894c

**Fallas.** `[FECHA O REGIÓN]` funde dos restricciones distintas (vigencia
temporal vs jurisdicción) en una variable: el usuario elige una y pierde la
otra. "Criterio observable para decidir cuándo la base es suficiente" se pide
pero nunca se ejemplifica qué cuenta como observable. "No inventes fuentes ni
certeza" es guardrail correcto pero no accionable (¿qué hace el modelo cuando
no hay fuentes? no dice declarar el vacío). Sin caso borde para un `[TEMA]` ya
estrecho: el prompt siempre "delimita", incluso cuando delimitar es destruir
alcance útil. Colinda con 03 sin regla: ambos "investigan". [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: alcance con dentro/fuera
explícito; cada fuente recomendada con autor+fecha+enlace+razón; criterio de
suficiencia formulado como condición comprobable ("puedo responder X sin
adjetivos"). edge_cases: tema ya delimitado (validar, no re-delimitar);
cero fuentes primarias disponibles → declarar coverage_gap; horizonte
temporal y regional en conflicto. tradeoffs: delimitar reduce cobertura a
cambio de verificabilidad. assumptions: el usuario aún NO tiene base
construida (si la tiene, frontera → 03/05). limits: no ejecuta la
investigación, solo la delimita; no garantiza exactitud.

**Marcadores de audiencia.** persona: `[DECISIÓN O RESULTADO]` individual,
"mi contexto", riesgo personal de decidir mal. empresa: obligatorio
`[EQUIPO]` o `[PROCESO]` (p.ej. quién consumirá la base), decisión con
responsable y gobernanza de fuentes (derechos de uso para uso interno).

**Anclas a preservar.** es `delimit·tema` / `fuente·tension` · en
`bound·topic` / `source·tension` · pt `delimit·tema` / `fonte·tenso`.

### 02 · Coach basado en fuentes (Aprender) — presupuesto es 850c

**Fallas.** "Cita cada afirmación material" sin definir material: en la
práctica el modelo decide qué citar. Sin condición de parada: "una idea por
turno" no dice cuántas rondas ni cuándo el aprendizaje terminó. Sin regla
cuando `[FUENTES O NOTEBOOK]` no cubre la pregunta del usuario (debería
declarar el límite, no improvisar). La calidad de la reformulación del
usuario no tiene criterio: "detecta errores" contra ¿qué rúbrica? La variable
`[FUENTES O NOTEBOOK]` mezcla dos modos de operación distintos (lista de
fuentes vs Notebook configurado). [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: toda explicación con cita
verificable; cada ronda cierra con pregunta de recuperación + fuente exacta;
sesión termina cuando el usuario reformula sin error N ideas seguidas
(condición observable). edge_cases: pregunta fuera de la base → declarar y
no responder; usuario reformula con error dos veces → cambiar de analogía,
no repetir. tradeoffs: ritmo lento (una idea/turno) a cambio de retención
verificable. assumptions: existe base con derechos de uso. limits: enseña,
NUNCA califica nivel (frontera 3: eso es 08/M2/W08).

**Marcadores de audiencia.** persona: "qué intento lograr", reformulación
"con mis palabras". empresa: `[EQUIPO]` como aprendiz colectivo o `[PROCESO]`
donde se aplicará lo aprendido; evidencia de sesión compartible con el
equipo.

**Anclas a preservar.** es `aprend·coach` / `fuente·pregunta` · en
`learn·source` / `source·question` · pt `aprend·coach` / `fonte·pergunta`.

### 03 · Investigación profunda (Aprender) — presupuesto es 870c

**Fallas.** Presupone un `[VACÍO]` ya diagnosticado pero es pieza autónoma de
biblioteca: no declara la precondición (a diferencia de W03, que cita "el
diagnóstico anterior"). La columna `confianza` de la tabla no tiene escala
(¿alta/media/baja? ¿0–1?): cada corrida inventa la suya. "Riesgo residual" se
pide sin umbral de aceptación. "Máximo tres preguntas" es buen guardrail pero
no dice qué hacer si tras las tres preguntas sigue faltando contexto.
[INFERENCIA]

**Dirección de elevación.** acceptance_criteria: cada afirmación de la tabla
con evidencia citada y confianza en escala declarada; contradicciones listadas
con ambas fuentes; riesgo residual nombrado con condición que lo cerraría.
edge_cases: vacío incerrable con fuentes públicas → veredicto explícito "no
demostrable con el alcance dado"; vacío que muta al investigar → re-declarar
alcance antes de seguir. tradeoffs: profundidad en un vacío a cambio de no
ampliar cobertura. assumptions: existe un diagnóstico previo (05/W02) que
nombró el vacío. limits: no re-delimita el tema completo (frontera 1: eso
es 01); scope_out: abrir temas nuevos.

**Marcadores de audiencia.** persona: vacío que bloquea decisión propia.
empresa: vacío que bloquea `[PROCESO]` o decisión de `[EQUIPO]`; criterios de
aceptación revisables por un tercero (verificador ≠ productor).

**Anclas a preservar.** es `vacio·alcance` / `vacio·residual` · en
`scope·research` / `cited·residual` · pt `lacuna·escopo` / `lacuna·residual`.
Nota: en es el discriminante contra 01 es `vacio` (el ancla `alcance` también
aparece en el texto de 01; no anclar la frontera sobre ella). [CÓDIGO]

### 04 · Verificación cruzada (Aprender) — presupuesto es 782c

**Fallas.** "Evidencia independiente" sin definición operativa: dos medios que
citan la misma nota de prensa pasan por independientes (el texto pide
distinguir "coincidencia real de repetición" pero no da el criterio: mismo
origen ≠ independencia). Sin mínimo de fuentes para emitir veredicto. `[USO]`
se declara y nunca se usa: el veredicto no cambia según el riesgo del uso.
Caso borde ausente: afirmación no verificable por diseño (evento futuro,
dato privado). [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: veredicto ∈ {CONFIRMADA,
REFUTADA, NO DEMOSTRABLE} con ≥2 fuentes de origen distinto o declaración de
que no existen; "qué cambiaría el veredicto" formulado como evidencia
concreta faltante. edge_cases: cadena de citas con un solo origen → contar
como una fuente; afirmación mixta (parte cierta, parte no) → dividirla antes
de verificar. tradeoffs: veredicto conservador a cambio de menos falsos
CONFIRMADA. assumptions: la afirmación es atómica y fechable. limits: no
audita bases completas (eso es 05); no garantiza exactitud.

**Marcadores de audiencia.** persona: `[USO]` personal (cita en entrevista,
compra, decisión propia). empresa: `[USO]` con exposición organizacional
(propuesta a cliente, decisión de `[EQUIPO]`); trazabilidad exigible en
revisión.

**Anclas a preservar.** es `verific·afirmacion` / `veredicto·demostrable` ·
en `verif·claim` / `verdict·demonstrable` · pt `verif·afirm` /
`veredito·demonstravel`.

### 05 · Auditoría de relevancia (Aprehender) — presupuesto es 772c

**Fallas.** "No premies cantidad" es eslogan, no regla: nada impide que la
tabla conserve todo. Siete dimensiones de evaluación (autoridad, vigencia,
cobertura, redundancia, sesgo, contradicciones, derecho de uso) sin peso ni
orden: el veredicto binario BASE SUFICIENTE/REPETIR no dice qué dimensión lo
decidió. "Derecho de uso" se evalúa sin pedir el dato (licencia/origen) que
lo haría evaluable. Caso borde ausente: base vacía o propósito ambiguo.
[INFERENCIA]

**Dirección de elevación.** acceptance_criteria: cada fuente con decisión
{conservar, actualizar, retirar} + evidencia de la decisión; veredicto final
ligado a los vacíos priorizados (suficiente ⇔ ningún vacío bloquea el
propósito). edge_cases: propósito no declarado → pedirlo antes de auditar;
todas las fuentes redundantes → veredicto REPETIR aunque el volumen sea alto.
tradeoffs: retirar fuentes reduce cobertura aparente a cambio de señal.
assumptions: el propósito es único (una base multi-propósito se audita por
propósito). limits: no configura el asistente ni redacta instrucciones
(frontera 2: eso es 07/W10); scope_out: comportamiento del Notebook.

**Marcadores de audiencia.** persona: biblioteca propia, propósito individual.
empresa: base compartida por `[EQUIPO]`; columna extra de responsable de cada
acción; derechos de uso como bloqueo de gobernanza, no como preferencia.

**Anclas a preservar.** es `audit·conserv` / `veredicto·suficien` · en
`audit·retain` / `verdict·sufficien` · pt `audit·manter` /
`veredito·suficien`.

### 06 · Generador de práctica (Aprehender) — presupuesto es 830c

**Fallas.** Tensión interna no declarada: "aplicación a un caso nuevo" pide
por definición material fuera de las fuentes, mientras el guardrail ordena
"no evalúes contenido ausente de las fuentes" — el texto exige ambas cosas
sin regla de resolución. "Errores frecuentes" se definen aunque las fuentes
no los documenten: invitación a inventar. "Rúbrica observable" sin niveles.
[INFERENCIA]

**Dirección de elevación.** acceptance_criteria: cada momento con respuesta
esperada anclada a fuente; el caso nuevo declara qué elementos vienen de las
fuentes y cuáles son escenario sintético (resolver la tensión: aplicar
conceptos de la base a contexto nuevo, evaluar solo los conceptos).
edge_cases: fuentes sin ejemplos aplicables → práctica de recuperación y
explicación solamente, declarándolo; usuario falla la recuperación →
retroceder, no avanzar. tradeoffs: práctica corta y citada a cambio de menos
variedad. assumptions: `[AUDIENCIA]` tiene nivel declarable. limits: diseña
práctica puntual, no evaluación de nivel (eso es 08).

**Marcadores de audiencia.** persona: práctica auto-administrada, segundo
intento propio. empresa: práctica facilitable a `[EQUIPO]` con rúbrica usable
por un tercero y registro de resultados por `[PROCESO]`.

**Anclas a preservar.** es `practic·aplica` / `practic·rubrica` · en
`practice·application` / `practice·rubric` · pt `pratic·aplica` /
`pratic·rubrica`.

### 07 · Auditoría de notebook (Aprehender) — presupuesto es 794c

**Fallas.** Dos entregables en un prompt: auditoría (diagnóstico, matriz,
fuentes a retirar) **y** configuración recomendada del asistente — difumina
la frontera 2 dentro de sí mismo y contra W10. "Pruebas adversariales" sin
número ni forma (¿prompts de ataque? ¿preguntas fuera de base?). "Privacidad"
se revisa sin regla de acción (¿retirar, redactar, aislar?). `[USUARIO]` en
singular no escala al caso empresa. [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: matriz completa
hallazgo|evidencia|riesgo|corrección; N pruebas adversariales definidas con
resultado esperado (el asistente declara límite, no inventa); lista explícita
de tareas prohibidas con esta base. edge_cases: fuente con derechos dudosos →
retirar por defecto (fail-closed); Notebook sin propósito declarado →
detener la auditoría y pedirlo. tradeoffs: auditar el contenedor, no cada
fuente en detalle (eso es 05). assumptions: existe un Notebook operativo.
limits: la "configuración recomendada" es insumo para 07→W10, no la
instrucción final; scope_out: re-decidir relevancia fuente por fuente.

**Marcadores de audiencia.** persona: `[USUARIO]` = yo; privacidad de
material personal. empresa: usuarios múltiples por rol (`[EQUIPO]`),
privacidad y derechos como riesgo organizacional, tareas prohibidas
ratificables por un responsable.

**Anclas a preservar.** es `notebook·proposito` / `diagnost·configur` · en
`notebook·source` / `diagnos·configur` · pt `notebook·proposito` /
`diagnost·configur`.

### 08 · Evaluador progresivo (Aprehender) — presupuesto es 756c

**Fallas.** "Rúbrica breve" sin niveles ni descriptores: cada corrida califica
distinto. El segundo intento no tiene efecto declarado sobre la calificación.
"Transferencia" comparte la tensión de 06 (caso nuevo vs solo-fuentes) sin
resolverla. "Nivel demostrado" final sin escala ni umbral de aprobación.
[INFERENCIA]

**Dirección de elevación.** acceptance_criteria: rúbrica con niveles
nombrados y descriptor observable por nivel; regla explícita de avance entre
fundamentos→relaciones→aplicación→transferencia; reporte final con nivel,
evidencia por dimensión y práctica correctiva ligada a 06. edge_cases:
respuesta parcialmente correcta → calificar por dimensión, no binario; usuario
responde fuera de la base → señalar sin penalizar conocimiento externo, no
evaluarlo. tradeoffs: una pregunta a la vez alarga la sesión a cambio de
diagnóstico limpio. assumptions: las `[FUENTES]` cubren los cuatro niveles.
limits: mide, no enseña (frontera 3: enseñar es 02/M1/W05); scope_out:
explicar contenido nuevo más allá de la corrección citada.

**Marcadores de audiencia.** persona: autoevaluación, plan de estudio propio.
empresa: evaluación aplicable a `[EQUIPO]` con reporte comparable entre
personas y decisión de habilitación ligada a `[PROCESO]`.

**Anclas a preservar.** es `evalu·transfer` / `nivel·practic` · en
`assess·transfer` / `level·practice` · pt `avali·transfer` / `nivel·pratic`.

### 09 · Simulador de entrevista ((R)Evolucionar) — presupuesto es 762c

**Fallas.** **Sin variable `[FUENTES]`**: exige "evidencia" y "respuestas
reescritas con citas" pero nunca declara de qué base salen las citas — la
falla estructural más grave de la biblioteca: invita a citar de la nada.
"Aumenta la dificultad" sin regla de calibración (¿contra qué respuesta?).
"Honestidad" como criterio de evaluación no es observable sin definición
(p.ej. declarar incertidumbre en vez de aparentar certeza). [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: cada objeción trazable a un
riesgo real del `[TEMA]`; evaluación por criterio con evidencia de la
respuesta del usuario; las tres respuestas reescritas citan la base declarada.
edge_cases: usuario colapsa en la primera pregunta → bajar dificultad y
registrarlo; pregunta cuya respuesta honesta es "no sé" → puntuar la
declaración de límite como acierto (operativiza "honestidad"). tradeoffs:
presión creciente a cambio de sesión incómoda pero diagnóstica. assumptions:
el contenido a defender ya existe (frontera 4: si no existe, es M4/10).
limits: no redacta ni reestructura el entregable; scope_out: construir
narrativa.

**Marcadores de audiencia.** persona: entrevista de trabajo, defensa
individual; riesgo personal (puesto, reputación). empresa: QBR/defensa ante
dirección; objeciones de gobernanza, costo y riesgo organizacional del
`[PROCESO]` o del `[EQUIPO]`.

**Anclas a preservar.** es `simul·entrevist` / `objecion·respuesta` · en
`simulat·difficulty` / `objection·answer` · pt `simul·dificuldade` /
`objec·resposta`. (en/pt intent cambiadas en esta fase, ver §D.)

### 10 · Coach de presentación ((R)Evolucionar) — presupuesto es 766c

**Fallas.** Dos modos en un prompt (construcción de narrativa + ensayo por
secciones) sin regla de transición: el modelo decide cuándo dejar de
construir y empezar a ensayar. "Estructura visual concisa" no es medible.
`[TIEMPO]` se declara pero la estructura no se deriva de él (8 min ≠ 30 min).
"Preguntas probables" sin número. Solapa con M4 (preparador) sin regla: 10
prepara+ensaya una presentación; M4 genera un preparador. [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: tesis en una frase; tres
ideas cada una con evidencia citada de `[FUENTES]`; estructura derivada de
`[TIEMPO]` (bloques con minutos); transición explícita construcción→ensayo a
confirmación del usuario. edge_cases: evidencia insuficiente para una idea →
degradarla a hipótesis declarada o eliminarla; audiencia hostil vs neutral →
ajustar tensión y llamado a la acción. tradeoffs: guion más corto y citado a
cambio de menos "wow". assumptions: la comprensión ya existe (si no,
retroceder a 01–08). limits: ensaya secciones, no simula interrogatorio
adversarial completo (eso es 09).

**Marcadores de audiencia.** persona: presentación propia, notas de orador en
primera persona. empresa: decisión de `[EQUIPO]`/dirección como `[RESULTADO]`,
narrativa defendible en revisión y reutilizable por otros presentadores.

**Anclas a preservar.** es `presenta·orador` / `estructura·pregunta` · en
`present·narrat` / `structure·question` · pt `apresent·narrativ` /
`estrutura·pergunta`. (es intent cambiada en esta fase, ver §D.)

### M1 · Generar coach (Metaprompt) — presupuesto es 846c

**Fallas.** "Tres pruebas adversariales que demuestren que no inventa" pide
una demostración imposible: una prueba no demuestra ausencia de invención,
solo la ausencia de fallo en esa prueba — promesa de garantía implícita que
roza `accuracy guarantee` (prohibido). Sin criterios de aceptación para el
system prompt generado (¿cuándo está bien diseñado?). El intent-set es de
anclas idéntico a 02 en es/pt (`coach·aprend`): la separación usar-coach vs
generar-coach descansa solo en las anclas de evidencia (`prompt·limite`) —
fase 4 debe reforzar léxico de diseño ("diseña", "system prompt
reutilizable") sin perder anclas. [CÓDIGO] [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: system prompt con rol,
base, flujo, límites y mensaje inicial completos; cada prueba adversarial con
ataque + respuesta esperada (declarar límite); reformular la promesa como
"pruebas que intentan inducir invención y documentan la respuesta correcta".
edge_cases: `[FUENTES]` insuficientes para el `[RESULTADO]` → el coach
generado debe abrir con coverage_gap; audiencia experta vs novata → preguntas
de diagnóstico distintas. tradeoffs: coach limitado a la base a cambio de
confiabilidad. assumptions: quien lo use mantendrá la base. limits: genera el
instrumento, no imparte la sesión (eso es 02); no garantiza que el coach
nunca falle.

**Marcadores de audiencia.** persona: coach para mi propio plan de estudio.
empresa: coach desplegable a `[EQUIPO]` con owner del instrumento, criterios
de mantenimiento de la base y límites ratificados por gobernanza.

**Anclas a preservar.** es `coach·aprend` / `prompt·limite` · en
`coach·source` / `prompt·limit` · pt `coach·aprend` / `prompt·limite`.

### M2 · Generar evaluador (Metaprompt) — presupuesto es 740c

**Fallas.** "Ocho tareas graduadas" sin decir la dimensión de graduación
(¿dificultad? ¿nivel cognitivo?). El evaluador generado no hereda el
anti-leak de 06 ("no reveles la solución antes del intento"): nada impide que
el evaluador regale respuestas. "Permitir reintento" sin límite ni efecto en
la regla de avance. Sin formato del reporte final. [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: rúbrica del evaluador con
descriptores observables; las 8 tareas mapeadas a
recuperación/explicación/aplicación/transferencia; regla de avance y regla de
reintento explícitas (máximo, efecto en puntaje); guardrail anti-revelación
heredado. edge_cases: evaluado que responde con conocimiento externo correcto
→ registrar sin puntuar (fuera de base); tarea sin cobertura en `[FUENTES]` →
excluirla, no inventarla. tradeoffs: evaluación estrecha (solo-base) a cambio
de veredicto defendible. assumptions: la base cubre los 4 niveles. limits:
genera el instrumento, no ejecuta la evaluación (eso es 08); frontera 3: el
evaluador generado no enseña.

**Marcadores de audiencia.** persona: instrumento para autoevaluarme.
empresa: instrumento aplicable a `[EQUIPO]` con resultados comparables,
verificador distinto del productor y decisión de habilitación documentada.

**Anclas a preservar.** es `evalu·observ` / `evaluador·rubrica` · en
`evaluat·observ` / `evaluator·rubric` · pt `avali·observ` / `prompt·rubrica`.

### M3 · Generar entrevistador (Metaprompt) — presupuesto es 756c

**Fallas.** "Objeciones realistas" sin fuente de realismo (¿de `[FUENTES]`?
¿del rol?). "Mapa de 10 preguntas" + "ramificaciones por respuesta" es
combinatorio sin tope de profundidad: instrumento inejecutable tal como se
pide. No exige verificar que `[FUENTES]` alcancen para sostener las
objeciones antes de generar. "Límites de simulación" se piden sin ejemplo
(¿qué NO debe simular? ¿personas reales?). [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: cada objeción del mapa
trazable a evidencia o a un riesgo declarado del `[ESCENARIO]`;
ramificaciones con profundidad máxima declarada; rúbrica con los 4 criterios
de 09 (claridad, fundamento, criterio, honestidad) definidos
observablemente. edge_cases: escenario sin fuentes suficientes → generar
versión reducida y declarar el vacío; rol que implicaría imitar a una persona
real identificable → rechazar y ofrecer arquetipo. tradeoffs: mapa acotado a
cambio de ejecutabilidad. assumptions: el usuario final del instrumento ya
tiene contenido que defender. limits: genera el simulador, no la sesión
(eso es 09); no prepara el entregable (frontera 4: M4).

**Marcadores de audiencia.** persona: entrevistador para mi preparación
individual. empresa: panel simulado para `[EQUIPO]` (comité, seguridad,
dirección) con objeciones de gobernanza y feedback agregable.

**Anclas a preservar.** es `entrevist·audiencia` / `prompt·rubrica` · en
`interview·audience` / `prompt·rubric` · pt `entrevist·publico` /
`prompt·rubrica`.

### M4 · Generar preparador (Metaprompt) — presupuesto es 818c

**Fallas.** El mejor cierre de la biblioteca ("criterios para declarar listo o
coverage_gap") convive con la peor definición de tarea: "comprobar
transferencia" no significa nada para un entregable (¿transferir a quién?).
La "plantilla del entregable" es única para `[ENTREGABLE]` ∈ {presentación,
clase, memo, decisión}: cuatro formas distintas con una sola plantilla.
Seis variables sin jerarquía: no dice cuáles son opcionales. [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: flujo de preparación con
gates observables (propósito confirmado → narrativa → evidencia seleccionada
→ ensayo → listo/coverage_gap); plantilla ramificada por tipo de
`[ENTREGABLE]` o supuesto explícito de tipo único; "transferencia" redefinida
como "la audiencia puede actuar con lo entregado" con evidencia. edge_cases:
`[TIEMPO]` incompatible con el `[RESULTADO]` → recortar alcance antes de
preparar; evidencia clave sin derechos de uso → excluir y declarar.
tradeoffs: checklist estricta a cambio de menos flexibilidad creativa.
assumptions: `[FUENTES]` ya auditadas (05/07). limits: prepara y ensaya por
partes; no aplica presión adversarial creciente (frontera 4: eso es 09/M3).

**Marcadores de audiencia.** persona: mi entregable, mi ensayo. empresa:
entregable con revisión de `[EQUIPO]` antes del gate, checklist auditable y
criterio "listo" ratificado por un responsable distinto del autor.

**Anclas a preservar.** es `prepar·entreg` / `preparacion·checklist` · en
`prepar·deliver` / `preparation·checklist` · pt `prepar·entreg` /
`preparacao·checklist`.

---

## B. Briefs workbook (W01–W10)

### W01 · Primera base con propósito — presupuesto es 1030c

**Fallas.** Pide en un solo turno delimitar + explicar + priorizar fuentes +
entregar informe citado: cuatro entregables sin orden de fallo (si no hay
fuentes primarias, ¿se entrega informe igual?). "Cambios recientes" sin
ancla temporal (¿recientes respecto a qué fecha?). "No presentes como certeza
lo que las fuentes no permiten afirmar" correcto pero sin mecanismo (etiqueta
de incertidumbre). [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: informe con secciones
fijas (alcance, conceptos, tensiones, fuentes recomendadas con
título+autor+fecha+enlace+razón); incertidumbre marcada inline. edge_cases:
tema sin fuentes primarias accesibles → informe reducido + vacíos declarados
para W03; `[DECISIÓN, PROYECTO O RESULTADO]` ausente → preguntar antes de
delimitar. tradeoffs: informe inicial imperfecto a cambio de arrancar el
ciclo del taller. assumptions: el informe se importará a NotebookLM como
primera fuente. limits: primera base, no base suficiente (la suficiencia se
decide en W04).

**Eco (par: 01).** W01 REFERENCIA el blueprint 01: misma anatomía
(delimitar, separar hechos/interpretaciones, fuentes primarias con razón).
Diferencia de encuadre: 01 es biblioteca autónoma que termina en un criterio
de suficiencia (delimita ANTES de investigar); W01 es el paso 1 del taller
guiado y termina en un **informe citado** que se convierte en la primera
fuente del Notebook y encadena a W02. El contrato W01 debe declarar la
herencia en `why_it_works.assumptions` y diferenciarse en `evidence`
(informe importable, no criterio). [DOC]

**Marcadores de audiencia.** persona: base para decisión propia. empresa:
base fundacional de `[EQUIPO]`/`[PROCESO]` con derechos de uso aptos para
compartir.

**Anclas a preservar.** es `verificab·conocimiento` / `informe·primarias` ·
en `verifiable·knowledge` / `cited report·primary` · pt
`verificavel·conhecimento` / `relatorio·primarias`.

### W02 · Auditar la base — presupuesto es 674c

**Fallas.** **Cero variables** `[X]`: el gate exige ≥2 — falla estructural a
resolver en fase 4 (candidatas: propósito y audiencia de la auditoría).
"Conclusión honesta sobre qué puedo afirmar hoy" es adjetivo, no criterio: la
lista de afirmables debe salir con cita o no salir. No emite veredicto de
suficiencia (correcto: lo difiere a W04) pero no lo dice — el usuario espera
un veredicto y no llega. [CÓDIGO] [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: resumen ≤8 líneas (ya
verificable, conservar); tabla completa con cada hallazgo citado; lista "qué
puedo afirmar hoy" donde cada entrada lleva su fuente; nota explícita "la
suficiencia se decide en el paso 4". edge_cases: base de una sola fuente →
auditoría de sesgo obligatoria; hallazgos contradictorios entre fuentes →
tipificarlos como tensión, no promediar. tradeoffs: formato fijo a cambio de
comparabilidad entre iteraciones. assumptions: la base fue construida con
W01. limits: no redacta instrucciones del asistente (frontera 2); no decide
suficiencia (W04).

**Eco (par: 05).** W02 REFERENCIA la auditoría de relevancia 05: mismas
dimensiones núcleo (cobertura, vigencia, sesgo, redundancia). Diferencia de
encuadre: 05 (biblioteca) audita una base madura contra un `[PROPÓSITO]` y
cierra con veredicto BASE SUFICIENTE/REPETIR; W02 (taller) audita la base
recién construida, con formato fijo de taller, y **no** emite veredicto: su
salida alimenta W03 y el veredicto vive en W04. [DOC]

**Marcadores de audiencia.** persona: qué puedo afirmar yo hoy. empresa: qué
puede afirmar el `[EQUIPO]` hoy y quién es responsable de cada acción de la
tabla.

**Anclas a preservar.** es `audita·hallazgo` / `cobertura·priorizados` · en
`audit this·finding` / `coverage·prioritized` · pt `audite·achado` /
`cobertura·priorizadas`.

### W03 · Investigación a medida — presupuesto es 698c

**Fallas.** Solo 1 variable (`[RESULTADO]`): el gate exige ≥2. Su output es un
**prompt para Deep Research**, no la investigación — meta-nivel que el título
("Investigación a medida") oculta. "El vacío de mayor impacto" se elige sin
criterio de impacto declarado (¿bloquea la decisión? ¿afecta más
afirmaciones?). Depende de "el diagnóstico anterior" sin decir qué pasa si no
existe. [CÓDIGO] [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: el prompt generado contiene
objetivo, dentro/fuera, evidencia mínima y criterios de aceptación (checklist
mecánica); la elección del vacío justificada contra `[RESULTADO]`.
edge_cases: sin diagnóstico previo → pedir correr W02 primero, no inventar
vacíos; dos vacíos empatados en impacto → preguntar, no decidir por el
usuario. tradeoffs: un solo vacío por iteración a cambio de control de
alcance. assumptions: Deep Research disponible (claim del ledger: mayores de
18, disponibilidad por plan — no prometer disponibilidad). limits: genera el
encargo, no ejecuta la investigación. [CONFIG]

**Eco (par: 03).** W03 REFERENCIA la investigación profunda 03: misma
anatomía del encargo (dentro/fuera, tensiones, evidencia mínima,
aceptación). Diferencia de encuadre: 03 (biblioteca) EJECUTA la
investigación del vacío y entrega hallazgos citados; W03 (taller) PRODUCE el
prompt listo para pegar en Deep Research, encadenado al diagnóstico de W02.
[DOC]

**Marcadores de audiencia.** persona: vacío que bloquea mi decisión.
empresa: vacío que bloquea al `[EQUIPO]`; el prompt generado debe ser
ejecutable por otra persona del equipo sin contexto adicional.

**Anclas a preservar.** es `diagnostico·impacto` / `aceptacion·research` ·
en `diagnosis·highest-impact` / `acceptance·research` · pt
`diagnostico·impacto` / `aceitacao·research`.

### W04 · Cerrar o repetir — presupuesto es 710c

**Fallas.** Sus dos "variables" son tokens de veredicto, no huecos: el
usuario no tiene nada que rellenar y el gate de variables se satisface con
falsos positivos — fase 4 debe añadir ≥2 variables reales (p.ej. propósito y
vacío auditado) conservando los tokens. "No busques perfección" es consejo,
no regla: falta el criterio de suficiencia contra propósito. "Valor de
fuentes" sin escala. [CÓDIGO] [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: comparación explícita contra
la auditoría anterior punto por punto (vacío, afirmaciones, tensiones,
riesgo residual); veredicto SIEMPRE acompañado: SUFICIENTE+límites o
REPETIR+siguiente prompt. edge_cases: nuevas fuentes que contradicen la base
→ el veredicto no puede ser SUFICIENTE sin resolver la tensión; ciclo >3
iteraciones → recomendar re-delimitar con W01/01 (evitar loop infinito).
tradeoffs: detenerse con evidencia suficiente a cambio de cobertura
incompleta declarada. assumptions: existe auditoría W02 previa e importación
real de fuentes. limits: decide suficiencia; no verifica afirmaciones una a
una en profundidad (eso es 04).

**Eco (par: 04).** W04 REFERENCIA la verificación cruzada 04 en su núcleo
("afirmaciones confirmadas o refutadas") y toma de 05 el veredicto de
suficiencia. Diferencia de encuadre: 04 (biblioteca) verifica UNA afirmación
con veredicto triple; W04 (taller) verifica el DELTA de la base tras importar
fuentes y cierra el ciclo del taller con veredicto de suficiencia. Declarar
ambos vínculos en `boundary.distinct_from` (04, 05). [DOC]

**Marcadores de audiencia.** persona: suficiente para mi decisión. empresa:
suficiente para el `[PROCESO]`/decisión del `[EQUIPO]`, con límites
comunicables a quien no participó del taller.

**Anclas a preservar.** es `importe·refutadas` / `residual·suficiente` · en
`imported·refuted` / `residual·sufficient` · pt `importei·refutadas` /
`residual·suficiente`.

### W05 · Activar un rol — presupuesto es 616c

**Fallas.** 1 variable (el selector de rol): falta ≥1 real (p.ej. resultado a
lograr, que hoy se pide por conversación). Los tres roles
(PROFESOR|ASESOR|COACH) no se diferencian en el texto: mismo comportamiento
con distinto nombre — el selector es cosmético. "Adapta la profundidad" sin
señal de adaptación. "El siguiente paso del rol" indefinido por rol.
[CÓDIGO] [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: comportamiento diferencial
por rol declarado (profesor: explica y pregunta; asesor: recomienda con
opciones y riesgo; coach: pregunta y hace reformular — mapa mínimo); cada
turno con cita o declaración de límite. edge_cases: pregunta fuera de la
base → declarar y sugerir W03; usuario pide certeza que la base no da →
mostrar la evidencia disponible y el vacío. tradeoffs: rol acotado a la base
a cambio de confiabilidad. assumptions: base declarada suficiente en W04.
limits: activa un rol conversacional; no diseña la instrucción persistente
del Notebook (frontera 2: eso es W10) ni califica nivel (frontera 3: W08).

**Eco (par: 02).** W05 REFERENCIA el coach basado en fuentes 02: misma regla
madre (basar todo en fuentes, citar, distinguir evidencia/inferencia/dato
faltante). Diferencia de encuadre: 02 (biblioteca) es un coach pedagógico
completo con flujo fijo (reformulación, contraejemplo, pregunta de
recuperación); W05 (taller) es la activación ligera de un rol triple dentro
del Notebook ya auditado, que abre confirmando rol y resultado. [DOC]

**Marcadores de audiencia.** persona: rol a mi servicio, profundidad según
mi nivel. empresa: rol consultable por `[EQUIPO]`, con límites del rol
visibles para cualquier usuario del Notebook.

**Anclas a preservar.** es `especializado·notebook` / `inferencia·faltante` ·
en `specialized·notebook` / `inference·missing` · pt
`especializado·notebook` / `inferencia·ausente`.

### W06 · Generar contenido — presupuesto es 502c

**Fallas.** Presupuesto 2× más estrecho del workbook junto a W07–W09:
diferenciación de audiencia con tokens cortos obligatoria. "Tres decisiones
editoriales" es el único criterio original y no dice de qué tipo (¿tono?
¿estructura? ¿omisiones?). "No añadas hechos externos" choca con `[TIPO DE
CONTENIDO]` persuasivo (un post necesita gancho: ¿de dónde sale?) — tensión
sin regla. Sin longitud objetivo de la pieza. [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: pieza con tesis única,
citas por afirmación material e inferencias marcadas; decisiones editoriales
tipificadas (qué se omitió, qué se simplificó, qué se destacó). edge_cases:
base sin evidencia para la tesis pedida → proponer tesis alternativa
sostenible, no forzar; contenido para audiencia externa → revisar derechos
de cita antes de entregar. tradeoffs: pieza menos viral a cambio de
trazabilidad. assumptions: base auditada. limits: crea la pieza; no la
publica (RENDERED_DRAFT ≠ PUBLISHED) ni decide el canal. [CONFIG]

**Marcadores de audiencia.** persona: mi voz, mi pieza. empresa: pieza a
nombre del `[EQUIPO]`/marca con revisión editorial previa y decisiones
editoriales auditables.

**Anclas a preservar.** es `contenido·tesis` / `editoriales·pieza` · en
`content type·thesis` / `editorial·final piece` · pt `conteudo·tese` /
`editoriais·peca`.

### W07 · Diseñar casos de uso — presupuesto es 522c

**Fallas.** 1 variable. Diez casos × diez atributos en un turno = tabla
superficial garantizada; ningún criterio de calidad por caso. "Ordena valor
frente a esfuerzo" sin escala de ninguno de los dos. "Experimento de 7 días"
sin criterio de éxito del experimento. Riesgo de inventar ROI (el deep_meta
del workbook ya lo prohíbe: "no inventar ROI" — el prompt no hereda ese
guardrail). [CÓDIGO] [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: cada caso con evidencia
citada de la base (si no hay evidencia, el caso se marca especulativo);
escalas declaradas para valor y esfuerzo; experimento con métrica observable
a 7 días. edge_cases: base sin material del dominio del `[ROL/EQUIPO]` →
menos de 10 casos y vacío declarado, no relleno; empate en el ranking →
criterio de desempate explícito (menor esfuerzo). tradeoffs: menos casos,
más defendibles. assumptions: quien prioriza es humano (la recomendación no
decide). limits: no estima ROI ni precios; no reemplaza el juicio humano.
[CONFIG]

**Marcadores de audiencia.** persona: casos para mi rol individual. empresa:
casos para `[EQUIPO]`/`[PROCESO]` con owner por experimento y control de
riesgo organizacional por caso.

**Anclas a preservar.** es `casos de uso·experimento` / `esfuerzo·complejidad`
· en `use cases·experiment` / `effort·complexity` · pt
`casos de uso·experimento` / `esforco·complexidade`.

### W08 · Evaluar comprensión — presupuesto es 478c

**Fallas.** Presupuesto más estrecho de los 27 tras W09: cada token cuenta.
1 variable. Versión comprimida de 08 que perdió justo lo operativo: sin
rúbrica (08 la tiene "breve"), sin segundo intento, sin regla de avance entre
los cuatro niveles. "Evalúa cada respuesta, explica y cita" — explicar es
tarea del coach: microfuga hacia la frontera 3 dentro del propio texto.
[CÓDIGO] [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: una pregunta por turno;
calificación por nivel con evidencia citada; cierre con
fortalezas/lagunas/fuentes/práctica (ya presente: conservar). Acotar
"explica" a la corrección citada (no enseñar contenido nuevo). edge_cases:
usuario sin respuestas en fundamentos → no avanzar de nivel; pregunta sin
cobertura en fuentes → sustituirla. tradeoffs: menos profundidad que 08 a
cambio de sesión de taller corta. assumptions: fuentes = Notebook del
taller. limits: mide dentro del taller; el instrumento reutilizable es M2.

**Eco (adyacencia, no par obligatorio): referencia a 08** — W08 es su forma
taller (cuatro niveles renombrados); el contrato debe apuntar
`distinct_from: 08, W05`. [DOC]

**Marcadores de audiencia.** persona: `evalúame` (ancla) sobre mi nivel.
empresa: evaluación de taller aplicada a `[EQUIPO]` con resultados agregables
por el facilitador.

**Anclas a preservar.** es `evaluame·fundamentos` / `fortalezas·lagunas` · en
`assess me·foundations` / `strengths·revisit` · pt `avalie-me·fundamentos` /
`forcas·revisar`. Nota: el ancla es/en/pt es un clítico de primera persona —
la celda empresa TAMBIÉN debe contenerlo (el hablante sigue siendo una
persona; el contexto es organizacional). La carta de tono §C lo contempla.
[CÓDIGO]

### W09 · Simular una conversación — presupuesto es 486c

**Fallas.** Comparte la falla estructural de 09 (cita sin base declarada) en
formato aún más corto. "Pregunta audiencia, resultado y tiempo" convierte en
diálogo lo que 09 resuelve con variables: correcto para taller pero no está
dicho por qué (guiado vs autónomo). Sin escalada de dificultad (09 la tiene).
"Tres mejoras" sin formato. [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: apertura que fija
audiencia/resultado/tiempo antes de la primera pregunta; cada evaluación con
evidencia de la respuesta; cierre con tres mejoras accionables citando la
base del Notebook. edge_cases: usuario sin material que defender → derivar a
W06/M4 antes de simular; tiempo declarado corto → reducir número de
preguntas, no la calidad de evaluación. tradeoffs: simulación ligera de
taller a cambio de menor presión que 09. assumptions: Notebook activo como
base de evidencia. limits: no reescribe el entregable (frontera 4).

**Eco (adyacencia): referencia a 09** — forma taller guiada (pregunta el
contexto en vez de variables); `distinct_from: 09, W08`. [DOC]

**Marcadores de audiencia.** persona: ensayo de mi conversación. empresa:
ensayo de QBR/defensa del `[EQUIPO]` con objeciones de gobernanza y costo.

**Anclas a preservar.** es `simula·entrevista` / `alternativas·mejoras` · en
`simulate·interview` / `alternatives·improvements` · pt `simule·entrevista` /
`alternativas·melhorias`.

### W10 · Configurar el Notebook — presupuesto es 568c

**Fallas.** "Exactamente 10 prompts de inicio" es el criterio más verificable
de los 27 (conservar) pero nada dice qué hace bueno a un prompt de inicio
(¿cubren los casos de uso? ¿evitan solapamiento?). "Guía de prueba en 5
líneas" sin qué probar (¿límites? ¿citas?). La instrucción personalizada no
exige heredar los límites detectados en W02/W04: la configuración puede
contradecir la auditoría. [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: instrucción con rol, tareas,
límites y regla de citas coherentes con el veredicto de W04; los 10 prompts
de inicio cubren sin duplicar los casos del taller; guía de prueba con al
menos una prueba de límite (pregunta fuera de base → debe declarar).
edge_cases: `[RESTRICCIONES]` contradicen el `[PROPÓSITO]` → señalar antes de
configurar; base con material privado → límite explícito de no exposición.
tradeoffs: configuración conservadora a cambio de menos alcance aparente.
assumptions: base declarada suficiente (W04) y auditada (W02/07).
limits: configura el asistente; no re-audita fuentes (frontera 2); no
autoriza publicación ni conectores. [CONFIG]

**Eco (adyacencia): referencia a 07** — 07 audita el Notebook y RECOMIENDA
configuración; W10 la DISEÑA final; `distinct_from: 07, W05`. [DOC]

**Marcadores de audiencia.** persona: asistente para `[USUARIO]` = yo.
empresa: asistente multi-usuario por rol del `[EQUIPO]`, límites ratificados
por un responsable, prueba de límites ejecutable por cualquiera.

**Anclas a preservar.** es `configuracion·personalizada` / `inicio·calidad` ·
en `configuration·personalized` / `starter·test guide` · pt
`configuracao·personalizada` / `iniciais·teste`.

---

## C. Briefs brain (B1–B3)

### B1 · Descargar, limpiar y confirmar — presupuesto es 1648c

**Fallas.** **Cero variables `[X]`** (usa `{{BRAIN_DUMP}}` y placeholder
`<...>`): el gate exige ≥2 variables en el prompt del contrato — fase 4 debe
introducirlas (p.ej. `[PROPÓSITO DE LA SESIÓN]`, `[NIVEL DE LIMPIEZA]`) sin
romper el contrato de formato `{{BRAIN_DUMP}}`. "Máximo tres preguntas
estratégicas" bien acotado, pero "descubrir oportunidad, cuestionar un
supuesto o aumentar valor" son tres propósitos distintos sin prioridad. "No
propongas todavía una solución" correcto; no dice qué hacer si el usuario la
pide (declinar citando el paso). Qué es "vocabulario importante" queda a
juicio del modelo. [CÓDIGO] [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: versión limpia que conserva
términos del hablante (sin parafraseo de vocabulario técnico propio);
confirmación ≤5 puntos; lo no interpretable declarado, nunca completado.
edge_cases: dictado vacío o ininteligible → pedir re-dictado, no inventar;
usuario responde las 3 preguntas con nuevas divagaciones → una segunda pasada
de limpieza máxima y cierre. tradeoffs: fidelidad a la voz a cambio de
prosa menos pulida. assumptions: el dictado es la única fuente (no hay
adjuntos implícitos). limits: no clasifica el encargo (B2) ni diseña el
Notebook (B3); no propone solución.

**Marcadores de audiencia.** persona: mi dictado, mis matices, decisión
pendiente mía. empresa: dictado de una reunión o de un responsable de
`[EQUIPO]`; separar además QUIÉN dijo qué cuando hay varias voces; decisiones
pendientes con dueño.

**Anclas a preservar.** es `dictado·repeticiones` / `estrategicas·entendido` ·
en `dictation·repetition` / `strategic·understanding` · pt
`ditado·repeticoes` / `estrategicas·entendimento`.

### B2 · Definir el encargo de aprendizaje — presupuesto es 1454c

**Fallas.** La clasificación de intención (7 categorías) no dice qué hacer con
intenciones mixtas ("aprender Y crear") ni con ninguna. La frase de propósito
tiene plantilla (bien) pero "evidencia mínima de avance" no tiene ejemplo de
qué cuenta como evidencia. "Pide confirmación" sin formato de confirmación
(¿qué confirma el usuario exactamente?). Depende de B1 ("versión limpia")
sin regla si se usa suelto. [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: brief de una página con
secciones fijas (intención, propósito, audiencia, plazo, nivel, restricciones,
evidencia mínima, fuera de alcance, decisión humana); intención mixta →
declarar principal y secundaria con orden. edge_cases: input sin B1 previo →
correr una confirmación mínima antes de clasificar; usuario que pide saltar a
herramientas → declinar citando el orden del método. tradeoffs: un paso más
antes de NotebookLM a cambio de no construir el Notebook equivocado.
assumptions: la decisión final es humana (nunca prometer reemplazo del
juicio humano). limits: produce el encargo; no elige herramienta ni fuentes.
[CONFIG]

**Marcadores de audiencia.** persona: mi encargo, mi plazo, mi nivel actual.
empresa: encargo con audiencia = `[EQUIPO]`, restricciones de `[PROCESO]` y
decisión que "seguirá siendo humana" asignada a un rol concreto.

**Anclas a preservar.** es `encargo·herramientas` / `brief·confirmacion` · en
`assignment·tools` / `brief·confirmation` · pt `encargo·ferramentas` /
`brief·confirmacao`.

### B3 · Convertir en preplan de NotebookLM — presupuesto es 1926c

**Fallas.** **Cero variables `[X]`.** Solapa con B2 sin regla: ambos
clasifican el caso y formulan propósito — B3 repite el trabajo de B2 en vez
de consumirlo (sus Inputs piden el dictado crudo, no el brief confirmado).
"Materiales que no deben cargarse por privacidad o derechos" es la mejor
regla de gobernanza de los 27 (conservar y reforzar). "Los cinco pasos del
taller" se citan sin nombrarlos: dependencia implícita del documento del
taller. [CÓDIGO] [INFERENCIA]

**Dirección de elevación.** acceptance_criteria: preplan con propósito
("Este Notebook existe para…"), audiencia, resultado observable, decisión
humana, fuentes iniciales + vacíos, exclusiones por privacidad/derechos, rol
con límite y primera evidencia; los cinco pasos nombrados (construir,
auditar, investigar, decidir suficiencia, activar rol). edge_cases: caso que
no encaja en las 7 categorías → declarar y proponer el más cercano; todas
las fuentes candidatas son privadas/sin derechos → preplan bloqueado con
gap declarado, no degradado en silencio. tradeoffs: preplan conservador a
cambio de arranque limpio. assumptions: idealmente consume el brief de B2
(declarar la cadena B1→B2→B3 en assumptions). limits: preplanifica; no crea
el Notebook, no carga fuentes, no promete capacidades de NotebookLM más allá
de lo documentado en el ledger. [CONFIG]

**Marcadores de audiencia.** persona: mi Notebook, mi primera evidencia.
empresa: Notebook de `[EQUIPO]` con exclusiones de privacidad/derechos como
política, decisión humana final asignada y preplan revisable por un tercero.

**Anclas a preservar.** es `preplanificacion·notebooklm` / `taller·evidencia`
· en `preplan·notebooklm` / `workshop·evidence` · pt
`pre-planejamento·notebooklm` / `oficina·evidencia`.

---

## D. Las 4 fronteras (decision_rule → boundary; cara negativa → scope_out)

Nota de mapeo trazable: el encargo de fase 3 cita las fronteras 2 y 3 como
"auditoría de fuentes 02" y "coach 05/M1". En los textos reales, la auditoría
de fuentes de biblioteca es **05** y la del workbook es **W02**; el coach de
biblioteca es **02**, su activación de taller es **W05** y su generador es
**M1** (05 es auditoría, no coach). Las reglas se fijan sobre los ids
reales del uso. [DOC]

### F1 · Blueprint (01) vs Deep Research (03)

- **decision_rule**: "Si todavía no existe una base ni un diagnóstico,
  delimita la investigación completa con 01; si un diagnóstico previo ya
  nombró un vacío concreto que bloquea el resultado, investiga solo ese vacío
  con 03."
- **scope_out** (cara negativa): 01 no cierra vacíos ya diagnosticados ni
  entrega hallazgos citados; 03 no abre temas nuevos ni redefine el alcance
  global.
- **distinct_from**: 01 → [03, W01] · 03 → [01, 05, W03].

### F2 · Auditoría de fuentes (05/W02) vs configuración de Notebook (07/W10)

- **decision_rule**: "Si la pregunta es si las fuentes sirven al propósito —
  qué conservar, actualizar o retirar y si la base es suficiente — audita con
  05/W02; si la base ya fue trabajada y la pregunta es cómo debe comportarse
  el Notebook como asistente — instrucción, límites, prompts de inicio,
  privacidad y derechos — usa 07/W10."
- **scope_out**: 05/W02 no redactan instrucciones ni prompts de inicio del
  asistente; 07/W10 no re-deciden la relevancia fuente por fuente ni emiten
  el veredicto de suficiencia.
- **distinct_from**: 05 → [04, 07, W02, W04] · 07 → [05, W05, W10] ·
  W02 → [05, W04] · W10 → [07, W05].
- Nota: 07 vive del lado "contenedor/configuración" pero su entregable de
  configuración es recomendación (insumo), no la instrucción final de W10.

### F3 · Evaluador (08/M2/W08) vs coach (02/M1/W05)

- **decision_rule**: "Si necesitas medir nivel con rúbrica, calificación y
  veredicto por evidencia, usa el evaluador (08, M2, W08); si necesitas
  comprender mediante explicación, reformulación y contraejemplo sin
  calificación, usa el coach (02, M1, W05)."
- **scope_out**: el coach no emite niveles, puntajes ni veredictos; el
  evaluador no enseña contenido nuevo más allá de la corrección citada.
- **distinct_from**: 08 → [02, 06, M2, W08] · M2 → [08, M1, M3] ·
  02 → [08, M1, W05] · M1 → [02, M2, M4] · W05 → [02, W08, W10] ·
  W08 → [08, W05].

### F4 · Simulador (09/W09/M3) vs preparador (M4/10)

- **decision_rule**: "Si el contenido a defender ya existe y necesitas
  presión adversarial creciente que lo pruebe, simula con 09/W09/M3; si el
  entregable aún no existe y necesitas construir narrativa, seleccionar
  evidencia y ensayar por partes, prepara con M4/10."
- **scope_out**: el simulador no redacta ni reestructura el entregable; el
  preparador no aplica interrogatorio adversarial creciente ni califica bajo
  presión.
- **distinct_from**: 09 → [10, M3, M4, W09] · M4 → [09, 10, M1] ·
  M3 → [09, M2] · 10 → [09, M4] · W09 → [09, W08].

---

## E. Carta de tono por audiencia × locale (6 celdas) — CONGELADA

Reglas de evaluación (mecánicas, mismas normas del gate: substring sobre
NFKD sin acentos + casefold; corchetes literales): [CONFIG]

- **Obligatorio absoluto**: en cada celda `empresa`, el marcador E1 (variable
  organizacional). En cada celda `persona`, el marcador P3 (ausencia de
  variables organizacionales).
- **Además**, cada celda debe satisfacer ≥2 marcadores adicionales de su
  lista en `prompt` y ≥1 en los campos de tarjeta (`purpose`/`when`).
- **Excepción de anclas**: las anclas de la autoridad v2 prevalecen sobre
  cualquier prohibición de la carta (p.ej. `evaluame`/`assess me`/`avalie-me`
  en W08 aparece en AMBAS audiencias: el hablante siempre es una persona; la
  audiencia `empresa` marca contexto organizacional, no despersonaliza la
  voz). [CÓDIGO]
- Los marcadores usan léxico nativo por locale y no violan
  `forbidden_locale_signals`. [CONFIG]

### persona-es

1. **P1** `prompt` contiene ≥1 de: `quiero` · `necesito` · `ayudame` ·
   `mi contexto` (voz de primera persona singular).
2. **P2** `prompt` contiene ≥2 apariciones de `mi ` o `mis ` (riesgo y
   contexto personales).
3. **P3 (obligatorio)** `prompt` NO contiene `[equipo]`, `[proceso]`,
   `[area]`, `nuestro equipo`, `nuestra organizacion`.
4. **P4** `purpose` o `when` interpela en 2ª singular: ≥1 de `necesitas` ·
   `quieres` · `debes` · `tu `.
5. **P5** decisión individual: contiene `[decision` sin el modificador
   `del equipo` dentro del mismo corchete.
6. **P6** cero léxico de gobernanza: `gobernanza` · `comite` ·
   `aprobacion` · `trazabilidad del proceso` (salvo ancla).

### empresa-es

1. **E1 (obligatorio)** `prompt` contiene ≥1 variable de: `[equipo]` ·
   `[proceso]` · `[area]` · `[rol responsable]`.
2. **E2** marco colectivo: ≥1 de `nuestro equipo` · `nuestra organizacion` ·
   `del equipo` · `el proceso`.
3. **E3** gobernanza: ≥1 de `gobernanza` · `aprobacion` · `responsable` ·
   `trazabilidad` · `comite` · `direccion` (en `prompt` o `evidence`).
4. **E4** riesgo organizacional: ≥1 de `riesgo operativo` ·
   `riesgo organizacional` · `impacto en el proceso`.
5. **E5** entregable compartible/reutilizable: ≥1 de
   `reutilizable por el equipo` · `listo para revision` ·
   `para compartir con` · `comparable entre`.

### persona-en

1. **P1** `prompt` contains ≥1 of: `i want` · `i need` · `help me` ·
   `my context`.
2. **P2** ≥2 occurrences of `my ` in `prompt`.
3. **P3 (obligatorio)** no `[team]`, `[process]`, `[business area]`,
   `our team`, `our organization` in `prompt`.
4. **P4** `purpose`/`when` address the reader: ≥1 of `you want` ·
   `you need` · `you must` · `your `.
5. **P5** individual decision: contains `[decision` without `team` inside
   the same bracket.
6. **P6** zero governance lexicon: `governance` · `approval` · `sign-off` ·
   `committee` (salvo ancla).

### empresa-en

1. **E1 (obligatorio)** `prompt` contains ≥1 of: `[team]` · `[process]` ·
   `[business area]` · `[owner role]`.
2. **E2** collective frame: ≥1 of `our team` · `the team` ·
   `our organization`.
3. **E3** governance: ≥1 of `governance` · `approval` · `accountable` ·
   `traceability` · `leadership` (in `prompt` or `evidence`).
4. **E4** organizational risk: ≥1 of `operational risk` ·
   `organizational risk` · `process impact`.
5. **E5** shareable/reusable deliverable: ≥1 of `reusable by the team` ·
   `ready for review` · `to share with` · `comparable across`.

### persona-pt

1. **P1** `prompt` contém ≥1 de: `quero` · `preciso` · `ajude-me` ·
   `meu contexto`.
2. **P2** ≥2 ocorrências de `meu ` ou `minha ` em `prompt`.
3. **P3 (obligatorio)** `prompt` NÃO contém `[equipe]`, `[processo]`,
   `[area]`, `nossa equipe`, `nossa organizacao`.
4. **P4** `purpose`/`when` em 2ª pessoa: ≥1 de `voce precisa` ·
   `voce quer` · `deve` · `sua `.
5. **P5** decisão individual: contém `[decisao` sem `da equipe` dentro do
   mesmo colchete.
6. **P6** zero léxico de governança: `governanca` · `comite` · `aprovacao` ·
   `rastreabilidade` (salvo âncora).

### empresa-pt

1. **E1 (obligatorio)** `prompt` contém ≥1 de: `[equipe]` · `[processo]` ·
   `[area]` · `[responsavel]`.
2. **E2** marco coletivo: ≥1 de `nossa equipe` · `nosso time` ·
   `nossa organizacao` · `da equipe`.
3. **E3** governança: ≥1 de `governanca` · `aprovacao` · `responsavel` ·
   `rastreabilidade` · `comite` · `diretoria` (em `prompt` ou `evidence`).
4. **E4** risco organizacional: ≥1 de `risco operacional` ·
   `risco organizacional` · `impacto no processo`.
5. **E5** entregável compartilhável: ≥1 de `reutilizavel pela equipe` ·
   `pronto para revisao` · `para compartilhar com` · `comparavel entre`.

Restricción de presupuesto: los marcadores E2–E5 son listas "≥1 de" para que
las celdas con tope 2× estrecho (W06–W09) puedan cumplir con tokens cortos.
La diferencia `persona`≠`empresa` exigida por el clone-gate queda garantizada
por E1+P3 en `prompt` y por P4/E2 en los campos de tarjeta. [INFERENCIA]

---

## F. Anclas v2 definitivas y pines congelados

### Verificación

Las 27×3 entradas (intent + evidence) de la autoridad se verificaron
mecánicamente como substring (NFKD sin acentos, casefold) de los textos
naturales ACTUALES; para library, las anclas `evidence` además aparecen en el
campo `evidence` del spec. Resultado: 100% válidas tras los cambios.
[CÓDIGO]

### Cambios (3 anclas; el resto se congela tal cual)

| Locale/ID | Antes | Después | Razón |
|---|---|---|---|
| es/10 intent | `presenta·eviden` | `presenta·orador` | `eviden` aparece en 21/27 textos es: poder discriminante nulo; ancla mal la intención. `orador` aparece solo en 10 ("notas de orador"). [CÓDIGO] |
| en/09 intent | `simulat·evidence` | `simulat·difficulty` | `evidence` aparece en 21/27 textos en, incluido M4: colisiona con la frontera F4 (simulador vs preparador). `difficulty` ("increase difficulty") aparece en 3/27 y no en M4. [CÓDIGO] |
| pt/09 intent | `simul·evidencia` | `simul·dificuldade` | Mismo caso que en/09: `evidencia` 21/27 y presente en M4; `dificuldade` ("aumente a dificuldade") 3/27 y ausente en M4. [CÓDIGO] |

Nota es/09: su intent es `simul·entrevist` (no contenía `eviden`), por eso no
cambia. Cada brief lista sus "anclas a preservar": fase 4 debe conservarlas en
las seis celdas del contrato (intent en `prompt` o `title+purpose`; evidence
en `prompt` **y** `evidence`).

### Pines v2 congelados (usar en fase 5)

- Archivo: `src/prompt-intent-authority-v2.json`
- `status`: `frozen_phase_3`
- `source_sha256`: `52bdcdd85faf0e211f3672bf1b86a41344bd567f3b0f715484eb165ac154e20a`
- `self_sha256`: `9e43b4826ef76b63c9fa1cca25ca29a9fd02510f07149680d967e49d9f5b4b86`
- Verificado con `scripts/repin-authority.py` (sin WARNING: declarado ==
  canónico). [CÓDIGO]

### Ajuste de gate derivado (trazabilidad)

`qa/check-prompt-contracts.py` exigía literalmente
`status == 'provisional_until_phase_3'`; congelar la autoridad lo rompía. Se
amplió el check a `status in {'provisional_until_phase_3', 'frozen_phase_3'}`
(una línea). Gates tras el cambio: `python3 qa/check-prompt-contracts.py` →
`PROMPT_CONTRACTS_OK contracts=0 ids=27 locales=3 audiences=2 mutations=8` ·
`python3 scripts/build.py` → exit 0. [CÓDIGO]

---

## G. Cierre de fase

- Artefactos: este documento + autoridad v2 congelada + ajuste de gate.
- Estado: `RENDERED_DRAFT`; nada de esta fase autoriza publicación.
- Gap conocido: los contratos (`src/prompt-contracts/*.json`) no existen aún —
  se autoran en fase 4 contra estos briefs, la carta §E y las anclas §F.
- Siguiente gate: fase 4 escribe los 27 contratos; el clone-gate, el tope 2×,
  las variables mínimas y las anclas congeladas deben pasar en
  `qa/check-prompt-contracts.py`. [CONFIG]
