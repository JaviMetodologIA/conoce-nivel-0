#!/usr/bin/env python3
"""Pure prompt-suite parity composition for Nivel 0 modules 02-04.

The imported module payloads and their editorial depth overlays are provenance
records.  This module never mutates them.  ``compose_prompt_parity`` returns
deep copies projected to the same visible library composition as the reference
module: ten direct prompts, four metaprompts, four levels and two modes.

[METODOLOGIA] The projection is intentionally deterministic and fail-closed.
It does not read files, clocks, environment variables or the network.  The
caller remains responsible for binding the returned copies to source hashes
and for rendering them inside the governed build.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any


LOCALES = ("es", "en", "pt")
AUDIENCES = ("persona", "empresa")
DIRECT_IDS = tuple(f"prompt-{index:02d}" for index in range(1, 11))
META_IDS = tuple(f"prompt-m{index}" for index in range(1, 5))
PROMPT_IDS = DIRECT_IDS + META_IDS
EXPECTED_IMPORTED = {"m02": 8, "m03": 10, "m04": 8}

MODULE_ALIASES = {
    "m02": {
        "module-02-de-ocupado-a-productivo",
        "ocupado-productivo",
        "02-de-ocupado-a-productivo",
        "m02",
    },
    "m03": {
        "module-03-trabajar-amplificado",
        "trabajo-amplificado",
        "03-trabajo-amplificado",
        "m03",
    },
    "m04": {
        "module-04-trabajo-agentico",
        "trabajo-agentico",
        "04-trabajo-agentico",
        "m04",
    },
}


class PromptParityError(ValueError):
    """Raised when a prompt suite cannot be composed without silent fallback."""


def _module_key(module_id: Any) -> str:
    if not isinstance(module_id, str) or not module_id.strip():
        raise PromptParityError("module_id: expected non-empty text")
    value = module_id.strip()
    matches = [key for key, aliases in MODULE_ALIASES.items() if value in aliases]
    if len(matches) != 1:
        raise PromptParityError(f"module_id: unsupported value {value!r}")
    return matches[0]


def _mapping(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise PromptParityError(f"{path}: expected mapping")
    return dict(value)


def _sequence(value: Any, path: str) -> list[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise PromptParityError(f"{path}: expected sequence")
    return list(value)


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PromptParityError(f"{path}: expected non-empty text")
    return value.strip()


def _unique(items: Sequence[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in items:
        item = _text(raw, "text item")
        key = item.casefold()
        if key not in seen:
            result.append(item)
            seen.add(key)
    return result


def _family(prompt_id: str) -> str:
    if prompt_id in META_IDS:
        return "meta"
    number = int(prompt_id.removeprefix("prompt-"))
    if number <= 4:
        return "learn"
    if number <= 8:
        return "embody"
    return "evolve"


LOCAL = {
    "es": {
        "example": "ej.",
        "parameters": "PARÁMETROS",
        "length": "LONGITUD",
        "structure": "ESTRUCTURA",
        "depth": "PROFUNDIDAD",
        "approval": "APROBACIÓN",
        "parameter_values": ("concisa", "tabla breve + decisión", "operativa", "humana obligatoria"),
        "optional": "Señala el dato faltante que cambiaría la decisión.",
        "system": "Actúa como especialista del módulo. No inventes evidencia ni sustituyas la decisión humana.",
        "template_task": "Produce {output} para {theme} con los inputs declarados.",
        "demo_task": "Produce {output} para {theme} con estos datos sintéticos resueltos.",
        "spec": ("SITUACIÓN", "PROPÓSITO", "ESTÁNDARES", "CRITERIOS"),
        "review_step": "Verifica evidencia, límites y consistencia antes de cerrar.",
        "finish_step": "Entrega el artefacto, el siguiente paso y cualquier vacío abierto.",
        "audience": {
            "persona": {
                "scope": "tu práctica personal",
                "owner": "tú conservas la decisión final y revisas la evidencia",
                "guardrail": "No delegues a la IA una decisión que corresponde a tu criterio.",
                "criterion": "Puedes explicar qué decidiste, con qué evidencia y qué revisarás después.",
            },
            "empresa": {
                "scope": "el flujo del equipo",
                "owner": "un responsable decide y una persona distinta revisa la evidencia",
                "guardrail": "No avances sin responsable, derechos de uso y revisión independiente.",
                "criterion": "El responsable, el revisor y la evidencia compartida quedan identificados.",
            },
        },
    },
    "en": {
        "example": "e.g.",
        "parameters": "PARAMETERS",
        "length": "LENGTH",
        "structure": "STRUCTURE",
        "depth": "DEPTH",
        "approval": "APPROVAL",
        "parameter_values": ("concise", "short table + decision", "operational", "human required"),
        "optional": "State the missing fact that would change the decision.",
        "system": "Act as a module specialist. Do not invent evidence or replace human judgment.",
        "template_task": "Produce {output} for {theme} from the declared inputs.",
        "demo_task": "Produce {output} for {theme} from these resolved synthetic data.",
        "spec": ("SITUATION", "PURPOSE", "STANDARDS", "CRITERIA"),
        "review_step": "Check evidence, boundaries and consistency before closing.",
        "finish_step": "Return the artifact, next step and any open gap.",
        "audience": {
            "persona": {
                "scope": "your own practice",
                "owner": "you retain the final decision and review the evidence",
                "guardrail": "Do not delegate a judgment that belongs to you to AI.",
                "criterion": "You can explain what you decided, the evidence used and what you will review next.",
            },
            "empresa": {
                "scope": "the team workflow",
                "owner": "an accountable owner decides and a different person reviews the evidence",
                "guardrail": "Do not proceed without an owner, usage rights and independent review.",
                "criterion": "The accountable owner, reviewer and shared evidence are identified.",
            },
        },
    },
    "pt": {
        "example": "ex.",
        "parameters": "PARÂMETROS",
        "length": "EXTENSÃO",
        "structure": "ESTRUTURA",
        "depth": "PROFUNDIDADE",
        "approval": "APROVAÇÃO",
        "parameter_values": ("concisa", "tabela breve + decisão", "operacional", "humana obrigatória"),
        "optional": "Indique o dado ausente que mudaria a decisão.",
        "system": "Atue como especialista do módulo. Não invente evidência nem substitua a decisão humana.",
        "template_task": "Produza {output} para {theme} com os inputs declarados.",
        "demo_task": "Produza {output} para {theme} com estes dados sintéticos resolvidos.",
        "spec": ("SITUAÇÃO", "PROPÓSITO", "PADRÕES", "CRITÉRIOS"),
        "review_step": "Verifique evidência, limites e consistência antes de concluir.",
        "finish_step": "Entregue o artefato, o próximo passo e qualquer lacuna aberta.",
        "audience": {
            "persona": {
                "scope": "sua prática pessoal",
                "owner": "você mantém a decisão final e revisa a evidência",
                "guardrail": "Não delegue à IA uma decisão que depende do seu critério.",
                "criterion": "Você consegue explicar o que decidiu, a evidência usada e o que revisará depois.",
            },
            "empresa": {
                "scope": "o fluxo da equipe",
                "owner": "um responsável decide e outra pessoa revisa a evidência",
                "guardrail": "Não avance sem responsável, direitos de uso e revisão independente.",
                "criterion": "O responsável, o revisor e a evidência compartilhada ficam identificados.",
            },
        },
    },
}


MODULE = {
    "m02": {
        "themes": {
            "es": "una semana que convierta actividad en resultados",
            "en": "a week that turns activity into outcomes",
            "pt": "uma semana que transforme atividade em resultados",
        },
        "extra_inputs": {
            "es": {
                "persona": (
                    ("RESULTADO_SEMANAL", "resultado observable que quieres cerrar", "propuesta revisada el jueves", "propuesta revisada el jueves"),
                    ("REGISTRO_DISPONIBLE", "evidencia de calendario, tareas o entregas", "bitácora de cinco días", "bitácora personal de cinco días con horas, salidas e interrupciones"),
                ),
                "empresa": (
                    ("RESULTADO_DEL_EQUIPO", "resultado operativo con fecha", "propuesta revisada el jueves", "propuesta del equipo revisada el jueves"),
                    ("RESPONSABLE", "persona que decide o desbloquea", "líder de la propuesta", "líder de la propuesta y revisor de calidad"),
                    ("REGISTRO_COMPARTIDO", "evidencia revisable del equipo", "tablero y calendario de cinco días", "tablero y calendario compartidos con horas, decisiones y bloqueos"),
                ),
            },
            "en": {
                "persona": (
                    ("WEEKLY_OUTCOME", "observable outcome you want to close", "reviewed proposal by Thursday", "reviewed proposal by Thursday"),
                    ("AVAILABLE_RECORD", "calendar, task or delivery evidence", "five-day activity log", "personal five-day log with hours, outputs and interruptions"),
                ),
                "empresa": (
                    ("TEAM_OUTCOME", "dated operational outcome", "reviewed proposal by Thursday", "team proposal reviewed by Thursday"),
                    ("ACCOUNTABLE_OWNER", "person who decides or removes a blocker", "proposal lead", "proposal lead and quality reviewer"),
                    ("SHARED_RECORD", "reviewable team evidence", "five-day board and calendar", "shared board and calendar with hours, decisions and blockers"),
                ),
            },
            "pt": {
                "persona": (
                    ("RESULTADO_SEMANAL", "resultado observável que você quer concluir", "proposta revisada na quinta-feira", "proposta revisada na quinta-feira"),
                    ("REGISTRO_DISPONÍVEL", "evidência de agenda, tarefas ou entregas", "diário de cinco dias", "diário pessoal de cinco dias com horas, saídas e interrupções"),
                ),
                "empresa": (
                    ("RESULTADO_DA_EQUIPE", "resultado operacional com data", "proposta revisada na quinta-feira", "proposta da equipe revisada na quinta-feira"),
                    ("RESPONSÁVEL", "pessoa que decide ou remove um bloqueio", "líder da proposta", "líder da proposta e revisor de qualidade"),
                    ("REGISTRO_COMPARTILHADO", "evidência revisável da equipe", "quadro e agenda de cinco dias", "quadro e agenda compartilhados com horas, decisões e bloqueios"),
                ),
            },
        },
        "fill": {
            "es": {
                "framework": "Definition of Done · cierre semanal observable",
                "guardrail": "No atribuyas causalidad a una práctica con una sola semana de registro.",
                "criterion": "La recomendación conserva fecha, resultado y evidencia revisable.",
                "edges": (
                    "Semana incompleta: entrega una lectura parcial y marca el periodo ausente.",
                    "Prioridades en conflicto: muestra el trade-off y quién debe resolverlo.",
                    "Sin registro verificable: pide la evidencia mínima y detente.",
                ),
            },
            "en": {
                "framework": "Definition of Done · observable weekly close",
                "guardrail": "Do not infer causality from a single week of records.",
                "criterion": "The recommendation retains a date, outcome and reviewable evidence.",
                "edges": (
                    "Incomplete week: return a partial reading and mark the missing period.",
                    "Conflicting priorities: show the trade-off and who must resolve it.",
                    "No verifiable record: request the minimum evidence and stop.",
                ),
            },
            "pt": {
                "framework": "Definition of Done · fechamento semanal observável",
                "guardrail": "Não atribua causalidade a uma prática com apenas uma semana de registros.",
                "criterion": "A recomendação mantém data, resultado e evidência revisável.",
                "edges": (
                    "Semana incompleta: entregue uma leitura parcial e marque o período ausente.",
                    "Prioridades em conflito: mostre o trade-off e quem deve resolvê-lo.",
                    "Sem registro verificável: solicite a evidência mínima e pare.",
                ),
            },
        },
    },
    "m03": {
        "themes": {
            "es": "un flujo de trabajo amplificado, probado y transferible",
            "en": "an amplified, tested and transferable workflow",
            "pt": "um fluxo de trabalho amplificado, testado e transferível",
        },
        "extra_inputs": {
            "es": {
                "persona": (
                    ("SALIDA_ESPERADA", "artefacto que debe producir el flujo", "propuesta lista para decisión", "propuesta lista para decisión"),
                    ("EVIDENCIA_DEL_FLUJO", "casos o registros que permiten probarlo", "tres ejecuciones recientes", "tres ejecuciones recientes con retrabajo y citas corregidas"),
                ),
                "empresa": (
                    ("SALIDA_DEL_PROCESO", "artefacto operativo que debe producir el equipo", "propuesta lista para aprobación", "propuesta lista para aprobación"),
                    ("DUEÑO_DEL_PROCESO", "responsable del estándar y su versión", "líder de operaciones", "líder de operaciones y revisor independiente"),
                    ("EVIDENCIA_DEL_FLUJO", "casos compartidos para probar el estándar", "tres ejecuciones del equipo", "tres ejecuciones del equipo con retrabajo, excepciones y revisiones"),
                ),
            },
            "en": {
                "persona": (
                    ("EXPECTED_OUTPUT", "artifact the workflow must produce", "proposal ready for decision", "proposal ready for decision"),
                    ("WORKFLOW_EVIDENCE", "cases or records that can test it", "three recent runs", "three recent runs with rework and corrected citations"),
                ),
                "empresa": (
                    ("PROCESS_OUTPUT", "operational artifact the team must produce", "proposal ready for approval", "proposal ready for approval"),
                    ("PROCESS_OWNER", "owner of the standard and its version", "operations lead", "operations lead and independent reviewer"),
                    ("WORKFLOW_EVIDENCE", "shared cases used to test the standard", "three team runs", "three team runs with rework, exceptions and reviews"),
                ),
            },
            "pt": {
                "persona": (
                    ("SAÍDA_ESPERADA", "artefato que o fluxo deve produzir", "proposta pronta para decisão", "proposta pronta para decisão"),
                    ("EVIDÊNCIA_DO_FLUXO", "casos ou registros que permitem testá-lo", "três execuções recentes", "três execuções recentes com retrabalho e citações corrigidas"),
                ),
                "empresa": (
                    ("SAÍDA_DO_PROCESSO", "artefato operacional que a equipe deve produzir", "proposta pronta para aprovação", "proposta pronta para aprovação"),
                    ("DONO_DO_PROCESSO", "responsável pelo padrão e sua versão", "líder de operações", "líder de operações e revisor independente"),
                    ("EVIDÊNCIA_DO_FLUXO", "casos compartilhados para testar o padrão", "três execuções da equipe", "três execuções da equipe com retrabalho, exceções e revisões"),
                ),
            },
        },
        "fill": {
            "es": {
                "framework": "Human-in-the-loop · revisión antes de decidir",
                "guardrail": "No declares mejora sin comparar el flujo contra un caso observado.",
                "criterion": "El Mini-SOP conserva versión, responsable, excepción y evidencia de prueba.",
                "edges": (
                    "Flujo sin frontera: define inicio y fin antes de optimizar.",
                    "Prácticas en tensión: registra cuál se prueba y por qué.",
                    "Prueba no ejecutada: conserva el plan y no declares mejora.",
                ),
            },
            "en": {
                "framework": "Human-in-the-loop · review before decision",
                "guardrail": "Do not claim improvement without comparing the workflow against an observed case.",
                "criterion": "The Mini-SOP retains a version, owner, exception and test evidence.",
                "edges": (
                    "Workflow without a boundary: define start and finish before improving it.",
                    "Conflicting practices: record which one will be tested and why.",
                    "Test not run: retain the plan and do not claim improvement.",
                ),
            },
            "pt": {
                "framework": "Human-in-the-loop · revisão antes da decisão",
                "guardrail": "Não declare melhoria sem comparar o fluxo com um caso observado.",
                "criterion": "O Mini-SOP mantém versão, responsável, exceção e evidência de teste.",
                "edges": (
                    "Fluxo sem fronteira: defina início e fim antes de melhorar.",
                    "Práticas em tensão: registre qual será testada e por quê.",
                    "Teste não executado: mantenha o plano e não declare melhoria.",
                ),
            },
        },
    },
    "m04": {
        "themes": {
            "es": "un piloto agéntico acotado, reversible y supervisado",
            "en": "a bounded, reversible and supervised agentic pilot",
            "pt": "um piloto agêntico delimitado, reversível e supervisionado",
        },
        "extra_inputs": {
            "es": {
                "persona": (
                    ("AUTORIDAD", "acciones que puedes aprobar o revocar", "solo lectura sobre una copia local", "solo lectura y vista previa sobre una copia local"),
                    ("EVIDENCIA_DE_CONTROL", "registro que demuestra límites y recuperación", "bitácora sin efectos externos", "bitácora con versión, pausa, salida y recuperación"),
                ),
                "empresa": (
                    ("AUTORIDAD_APROBADA", "acciones autorizadas por el dueño del proceso", "solo lectura sobre una copia aislada", "solo lectura y vista previa sobre una copia aislada"),
                    ("RESPONSABLE_DE_APROBACIÓN", "persona que aprueba versión y efectos", "dueño del proceso", "dueño del proceso y revisor de control"),
                    ("EVIDENCIA_DE_CONTROL", "registro compartido de límites y recuperación", "bitácora sin efectos externos", "bitácora compartida con versión, pausa, salida y recuperación"),
                ),
            },
            "en": {
                "persona": (
                    ("AUTHORITY", "actions you may approve or revoke", "read-only access to a local copy", "read-only access and preview on a local copy"),
                    ("CONTROL_EVIDENCE", "record that proves boundaries and recovery", "log with no external effects", "log with version, pause, output and recovery"),
                ),
                "empresa": (
                    ("APPROVED_AUTHORITY", "actions authorized by the process owner", "read-only access to an isolated copy", "read-only access and preview on an isolated copy"),
                    ("APPROVAL_OWNER", "person who approves version and effects", "process owner", "process owner and control reviewer"),
                    ("CONTROL_EVIDENCE", "shared record of boundaries and recovery", "log with no external effects", "shared log with version, pause, output and recovery"),
                ),
            },
            "pt": {
                "persona": (
                    ("AUTORIDADE", "ações que você pode aprovar ou revogar", "somente leitura sobre uma cópia local", "somente leitura e prévia sobre uma cópia local"),
                    ("EVIDÊNCIA_DE_CONTROLE", "registro que demonstra limites e recuperação", "bitácora sem efeitos externos", "bitácora com versão, pausa, saída e recuperação"),
                ),
                "empresa": (
                    ("AUTORIDADE_APROVADA", "ações autorizadas pelo dono do processo", "somente leitura sobre uma cópia isolada", "somente leitura e prévia sobre uma cópia isolada"),
                    ("RESPONSÁVEL_PELA_APROVAÇÃO", "pessoa que aprova versão e efeitos", "dono do processo", "dono do processo e revisor de controle"),
                    ("EVIDÊNCIA_DE_CONTROLE", "registro compartilhado de limites e recuperação", "bitácora sem efeitos externos", "bitácora compartilhada com versão, pausa, saída e recuperação"),
                ),
            },
        },
        "fill": {
            "es": {
                "framework": "Reversibilidad · salida segura y recuperación probada",
                "guardrail": "No confundas un plan aprobado con autorización para ejecutar efectos externos.",
                "criterion": "La versión, autoridad, punto de control y condición de parada coinciden.",
                "edges": (
                    "Autoridad ambigua: detén el diseño y pide un responsable.",
                    "Versión distinta de la aprobada: invalida el plan y vuelve al gate.",
                    "Recuperación no probada: limita el piloto a una vista previa sin efectos.",
                ),
            },
            "en": {
                "framework": "Reversibility · safe output and tested recovery",
                "guardrail": "Do not treat an approved plan as authority to create external effects.",
                "criterion": "Version, authority, checkpoint and stop condition match.",
                "edges": (
                    "Ambiguous authority: stop design and request an accountable owner.",
                    "Version differs from the approval: invalidate the plan and return to the gate.",
                    "Recovery not tested: limit the pilot to a no-effect preview.",
                ),
            },
            "pt": {
                "framework": "Reversibilidade · saída segura e recuperação testada",
                "guardrail": "Não trate um plano aprovado como autorização para gerar efeitos externos.",
                "criterion": "Versão, autoridade, ponto de controle e condição de parada coincidem.",
                "edges": (
                    "Autoridade ambígua: pare o desenho e solicite um responsável.",
                    "Versão diferente da aprovada: invalide o plano e volte ao gate.",
                    "Recuperação não testada: limite o piloto a uma prévia sem efeitos.",
                ),
            },
        },
    },
}


ADDED_DIRECT = {
    "m02": {
        "es": (
            {
                "id": "prompt-09", "title": "Contrastar la forma de trabajo", "surface": "sources",
                "purpose": "Contrastar la práctica semanal observada con fuentes pertinentes sin reemplazar los datos propios por consejos genéricos.",
                "when": "Cuando ya existe una revisión semanal y necesitas decidir qué práctica externa adoptar, adaptar o descartar.",
                "output": "Nota de contraste de la práctica",
                "workflow": ("Formula una pregunta contrastable desde la revisión semanal.", "Prioriza fuentes primarias o guías con autor y fecha.", "Compara la recomendación externa con el registro observado.", "Explica ajuste, incompatibilidad y evidencia faltante.", "Propón un experimento acotado para la semana siguiente."),
                "frameworks": ("Jerarquía de fuentes", "Evidence-to-decision", "Adaptar antes que imitar"),
                "guardrails": ("No conviertas una recomendación general en causa demostrada.", "No ocultes diferencias entre el contexto de la fuente y tu semana.", "Declara derechos, fecha y límite de cada fuente."),
                "acceptance": ("Cada recomendación tiene fuente y aplicabilidad explícita.", "El contraste separa coincidencia, tensión y vacío.", "El experimento siguiente tiene métrica y límite."),
                "edges": ("Fuentes contradictorias: conserva ambas posiciones.", "Fuente sin fecha: baja la confianza y busca reemplazo.", "Sin aplicabilidad: descarta la práctica con motivo."),
                "tradeoff": "Más contraste reduce consejos genéricos, pero exige limitar el volumen de fuentes.",
                "limits": ("No demuestra causalidad ni garantiza mejora.",),
                "demo": "Revisión semanal sintética: la propuesta terminó el jueves; agrupar mensajes redujo interrupciones observadas, pero una respuesta incumplió el plazo. La decisión es contrastar bloques protegidos y acuerdos de respuesta antes de repetir.",
            },
            {
                "id": "prompt-10", "title": "Convertir la práctica en sistema semanal", "surface": "chat",
                "purpose": "Convertir el contraste y la revisión en un sistema semanal breve que pueda repetirse, explicarse y ajustarse con evidencia.",
                "when": "Cuando una práctica ya fue observada y necesitas conservar solo las reglas que producen una revisión útil.",
                "output": "Sistema semanal versionado",
                "workflow": ("Resume el resultado y el contraste que sostienen la decisión.", "Define preparación, ejecución y revisión de la semana.", "Asigna reglas de prioridad, foco e interrupción.", "Fija evidencia, responsable y momento de revisión.", "Versiona el sistema y declara cuándo ajustarlo o detenerlo."),
                "frameworks": ("Weekly review", "Definition of Done", "Ciclo probar–revisar–ajustar"),
                "guardrails": ("No conviertas preferencias en reglas sin evidencia.", "No añadas controles que nadie pueda revisar.", "Conserva la decisión final bajo responsabilidad humana."),
                "acceptance": ("El sistema cabe en una página y tiene versión.", "Cada regla nombra evidencia y revisión.", "Existe condición para mantener, ajustar o retirar."),
                "edges": ("Resultado no observado: conserva el sistema como hipótesis.", "Reglas en conflicto: prioriza una y declara el costo.", "Sin revisión disponible: no declares consolidación."),
                "tradeoff": "Un sistema corto omite detalle a cambio de repetibilidad y revisión real.",
                "limits": ("Organiza una práctica; no predice productividad futura.",),
                "demo": "Nota de contraste sintética: los bloques protegidos son compatibles con el caso, pero requieren un acuerdo explícito de respuesta. La evidencia disponible cubre una semana; se propone repetir siete días con tiempo de ciclo y entregable como métricas.",
            },
        ),
        "en": (),
        "pt": (),
    },
    "m04": {
        "es": (
            {
                "id": "prompt-09", "title": "Simular un escalamiento", "surface": "chat",
                "purpose": "Ensayar una excepción crítica para comprobar que la persona, el agente y el punto de control reaccionan sin exceder la autoridad aprobada.",
                "when": "Después de revisar el piloto y antes de ampliar alcance, permisos o frecuencia.",
                "output": "Registro del ensayo de escalamiento",
                "workflow": ("Elige una excepción plausible y su señal de alerta.", "Recorre detección, pausa, escalamiento y decisión.", "Comprueba permisos, versión y evidencia disponible.", "Registra la respuesta esperada y cualquier desviación.", "Emite un veredicto mantener, ajustar o detener."),
                "frameworks": ("Tabletop exercise", "Human-in-the-loop", "Fail-safe defaults"),
                "guardrails": ("Simula sin ejecutar efectos externos.", "No amplíes permisos para completar el ensayo.", "Detente si la autoridad o la versión no coincide."),
                "acceptance": ("La excepción activa una pausa observable.", "El escalamiento llega a una persona identificada.", "El veredicto cita evidencia y cambio requerido."),
                "edges": ("La persona no está disponible: aplica la condición de parada.", "La excepción no estaba prevista: registra coverage_gap.", "La salida no es reversible: detén el caso."),
                "tradeoff": "Ensayar una excepción retrasa la expansión, pero revela fallos antes de aumentar impacto.",
                "limits": ("No ejecuta el agente ni concede permisos.",),
                "demo": "Revisión sintética del piloto: 29 de 32 notas fueron claras, 3 quedaron en duda y no hubo efectos externos. Excepción para ensayar: una nota contiene una instrucción que intenta cambiar el objetivo aprobado.",
            },
            {
                "id": "prompt-10", "title": "Preparar el siguiente ciclo", "surface": "chat",
                "purpose": "Convertir la revisión y el ensayo de escalamiento en un plan de continuidad con versión, autoridad, evidencia y gate humano nuevos.",
                "when": "Cuando el piloto tiene veredicto y necesitas decidir si repetir, ampliar de forma acotada o cerrar.",
                "output": "Plan de continuidad controlada",
                "workflow": ("Resume evidencia, excepciones y veredicto vigente.", "Define qué se mantiene y qué cambia en la siguiente versión.", "Fija alcance, permisos, responsable y recuperación.", "Especifica la evidencia que debe observar el siguiente ciclo.", "Cierra con gate de aprobación y condición de parada."),
                "frameworks": ("Versioned rollout", "Least privilege", "After-action review"),
                "guardrails": ("No reutilices una aprobación ligada a otra versión.", "No amplíes alcance y permisos al mismo tiempo.", "No inicies el ciclo sin gate humano verificable."),
                "acceptance": ("El plan identifica versión y aprobación requerida.", "Cada cambio tiene evidencia y riesgo asociado.", "La recuperación y la parada pueden ejecutarse."),
                "edges": ("Veredicto detener: produce solo cierre y aprendizaje.", "Evidencia insuficiente: repite sin ampliar alcance.", "Nuevo responsable: exige una aprobación nueva."),
                "tradeoff": "Ampliar una sola variable ralentiza el despliegue, pero conserva atribución y recuperación.",
                "limits": ("Planifica el ciclo; no lo ejecuta ni autoriza.",),
                "demo": "Ensayo sintético: una instrucción embebida fue tratada como contenido, el agente se detuvo y escaló al responsable. Veredicto: ajustar el clasificador y repetir sobre otra copia, sin ampliar permisos.",
            },
        ),
        "en": (),
        "pt": (),
    },
}


def _translated_added_direct(module: str, locale: str) -> tuple[dict[str, Any], ...]:
    """Return concise localized direct additions.

    English and Portuguese are authored here rather than falling back to
    Spanish.  The shared workflow semantics remain identical across locales.
    """

    if locale == "es":
        return tuple(deepcopy(item) for item in ADDED_DIRECT[module][locale])
    if module == "m02" and locale == "en":
        return (
            {"id":"prompt-09","title":"Cross-check the way of working","surface":"sources","purpose":"Compare the observed weekly practice with relevant sources without replacing local records with generic advice.","when":"Once a weekly review exists and you need to adopt, adapt or reject an external practice.","output":"Practice cross-check note","workflow":("Frame a testable question from the weekly review.","Prioritize primary or dated authoritative sources.","Compare external guidance with the observed record.","State fit, conflict and missing evidence.","Propose one bounded test for the next week."),"frameworks":("Source hierarchy","Evidence-to-decision","Adapt before adopting"),"guardrails":("Do not turn general guidance into a proven cause.","Do not hide differences between the source context and the observed week.","State rights, date and boundary for every source."),"acceptance":("Every recommendation has a source and explicit applicability.","The comparison separates agreement, tension and gap.","The next test has a metric and boundary."),"edges":("Conflicting sources: retain both positions.","Undated source: lower confidence and seek a replacement.","No applicability: reject the practice with a reason."),"tradeoff":"More cross-checking reduces generic advice but requires a strict source limit.","limits":("It does not prove causality or guarantee improvement.",),"demo":"Synthetic weekly review: the proposal finished on Thursday; batching messages reduced observed interruptions, but one reply missed its deadline. The decision is to cross-check protected blocks and response agreements before repeating."},
            {"id":"prompt-10","title":"Turn the practice into a weekly system","surface":"chat","purpose":"Turn the comparison and review into a concise weekly system that can be repeated, explained and adjusted with evidence.","when":"Once a practice has been observed and only useful, reviewable rules should remain.","output":"Versioned weekly system","workflow":("Summarize the outcome and comparison supporting the decision.","Define preparation, execution and review for the week.","Set priority, focus and interruption rules.","Assign evidence, owner and review point.","Version the system and state when to adjust or stop."),"frameworks":("Weekly review","Definition of Done","Test–review–adjust cycle"),"guardrails":("Do not turn preferences into rules without evidence.","Do not add controls nobody can review.","Keep final judgment under human accountability."),"acceptance":("The system fits on one page and has a version.","Every rule names evidence and a review point.","A condition exists to retain, adjust or retire it."),"edges":("Outcome not observed: retain the system as a hypothesis.","Conflicting rules: prioritize one and state the cost.","No reviewer available: do not claim consolidation."),"tradeoff":"A short system omits detail in exchange for repeatability and real review.","limits":("It organizes a practice; it does not predict future productivity.",),"demo":"Synthetic comparison note: protected blocks fit the case but require an explicit response agreement. Evidence covers one week; repeat for seven days using cycle time and completed output as metrics."},
        )
    if module == "m02" and locale == "pt":
        return (
            {"id":"prompt-09","title":"Contrastar a forma de trabalho","surface":"sources","purpose":"Comparar a prática semanal observada com fontes pertinentes sem substituir os registros próprios por conselhos genéricos.","when":"Quando já existe uma revisão semanal e você precisa adotar, adaptar ou descartar uma prática externa.","output":"Nota de contraste da prática","workflow":("Formule uma pergunta verificável a partir da revisão semanal.","Priorize fontes primárias ou guias com autoria e data.","Compare a recomendação externa com o registro observado.","Explique ajuste, incompatibilidade e evidência ausente.","Proponha um teste delimitado para a semana seguinte."),"frameworks":("Hierarquia de fontes","Evidence-to-decision","Adaptar antes de adotar"),"guardrails":("Não transforme uma recomendação geral em causa demonstrada.","Não oculte diferenças entre o contexto da fonte e sua semana.","Declare direitos, data e limite de cada fonte."),"acceptance":("Cada recomendação tem fonte e aplicabilidade explícita.","O contraste separa coincidência, tensão e lacuna.","O próximo teste tem métrica e limite."),"edges":("Fontes contraditórias: mantenha ambas as posições.","Fonte sem data: reduza a confiança e busque substituição.","Sem aplicabilidade: descarte a prática com justificativa."),"tradeoff":"Mais contraste reduz conselhos genéricos, mas exige limitar o volume de fontes.","limits":("Não demonstra causalidade nem garante melhoria.",),"demo":"Revisão semanal sintética: a proposta terminou na quinta-feira; agrupar mensagens reduziu interrupções observadas, mas uma resposta perdeu o prazo. A decisão é contrastar blocos protegidos e acordos de resposta antes de repetir."},
            {"id":"prompt-10","title":"Transformar a prática em sistema semanal","surface":"chat","purpose":"Transformar o contraste e a revisão em um sistema semanal breve, repetível, explicável e ajustável com evidência.","when":"Quando uma prática já foi observada e somente regras úteis e revisáveis devem permanecer.","output":"Sistema semanal versionado","workflow":("Resuma o resultado e o contraste que sustentam a decisão.","Defina preparação, execução e revisão da semana.","Estabeleça regras de prioridade, foco e interrupção.","Atribua evidência, responsável e momento de revisão.","Versione o sistema e declare quando ajustar ou parar."),"frameworks":("Weekly review","Definition of Done","Ciclo testar–revisar–ajustar"),"guardrails":("Não transforme preferências em regras sem evidência.","Não adicione controles que ninguém possa revisar.","Mantenha a decisão final sob responsabilidade humana."),"acceptance":("O sistema cabe em uma página e tem versão.","Cada regra nomeia evidência e revisão.","Existe condição para manter, ajustar ou retirar."),"edges":("Resultado não observado: mantenha o sistema como hipótese.","Regras em conflito: priorize uma e declare o custo.","Sem revisão disponível: não declare consolidação."),"tradeoff":"Um sistema curto omite detalhes em troca de repetibilidade e revisão real.","limits":("Organiza uma prática; não prevê produtividade futura.",),"demo":"Nota de contraste sintética: os blocos protegidos são compatíveis com o caso, mas exigem um acordo explícito de resposta. A evidência cobre uma semana; propõe-se repetir sete dias usando tempo de ciclo e entrega concluída como métricas."},
        )
    if module == "m04" and locale == "en":
        return (
            {"id":"prompt-09","title":"Rehearse an escalation","surface":"chat","purpose":"Rehearse a critical exception to verify that the person, agent and checkpoint respond without exceeding approved authority.","when":"After reviewing the pilot and before expanding scope, permissions or frequency.","output":"Escalation rehearsal record","workflow":("Choose a plausible exception and warning signal.","Walk through detection, pause, escalation and decision.","Check permissions, version and available evidence.","Record the expected response and any deviation.","Issue a retain, adjust or stop verdict."),"frameworks":("Tabletop exercise","Human-in-the-loop","Fail-safe defaults"),"guardrails":("Simulate without external effects.","Do not widen permissions to complete the rehearsal.","Stop when authority or version does not match."),"acceptance":("The exception triggers an observable pause.","Escalation reaches an identified person.","The verdict cites evidence and required change."),"edges":("Person unavailable: apply the stop condition.","Exception was not anticipated: record coverage_gap.","Output is not reversible: stop the case."),"tradeoff":"Rehearsing an exception delays expansion but reveals failures before impact grows.","limits":("It does not run the agent or grant permissions.",),"demo":"Synthetic pilot review: 29 of 32 notes were clear, 3 remained uncertain and there were no external effects. Exception to rehearse: a note contains an instruction attempting to change the approved objective."},
            {"id":"prompt-10","title":"Prepare the next cycle","surface":"chat","purpose":"Turn the review and escalation rehearsal into a continuity plan with a new version, authority, evidence and human gate.","when":"Once the pilot has a verdict and you must repeat, expand one bounded variable or close it.","output":"Controlled continuity plan","workflow":("Summarize evidence, exceptions and current verdict.","Define what remains and what changes in the next version.","Set scope, permissions, owner and recovery.","Specify evidence the next cycle must observe.","Close with an approval gate and stop condition."),"frameworks":("Versioned rollout","Least privilege","After-action review"),"guardrails":("Do not reuse approval tied to another version.","Do not expand scope and permissions together.","Do not begin without a verifiable human gate."),"acceptance":("The plan identifies version and required approval.","Every change has associated evidence and risk.","Recovery and stop can be executed."),"edges":("Stop verdict: produce only closure and learning.","Insufficient evidence: repeat without expanding scope.","New owner: require a new approval."),"tradeoff":"Expanding one variable at a time slows rollout but preserves attribution and recovery.","limits":("It plans the cycle; it does not execute or authorize it.",),"demo":"Synthetic rehearsal: an embedded instruction was treated as content, the agent stopped and escalated. Verdict: adjust the classifier and repeat on another copy without widening permissions."},
        )
    if module == "m04" and locale == "pt":
        return (
            {"id":"prompt-09","title":"Ensaiar um escalonamento","surface":"chat","purpose":"Ensaiar uma exceção crítica para verificar que pessoa, agente e ponto de controle respondem sem exceder a autoridade aprovada.","when":"Depois de revisar o piloto e antes de ampliar escopo, permissões ou frequência.","output":"Registro do ensaio de escalonamento","workflow":("Escolha uma exceção plausível e seu sinal de alerta.","Percorra detecção, pausa, escalonamento e decisão.","Verifique permissões, versão e evidência disponível.","Registre a resposta esperada e qualquer desvio.","Emita veredito manter, ajustar ou parar."),"frameworks":("Tabletop exercise","Human-in-the-loop","Fail-safe defaults"),"guardrails":("Simule sem executar efeitos externos.","Não amplie permissões para concluir o ensaio.","Pare se autoridade ou versão não coincidir."),"acceptance":("A exceção ativa uma pausa observável.","O escalonamento chega a uma pessoa identificada.","O veredito cita evidência e mudança necessária."),"edges":("Pessoa indisponível: aplique a condição de parada.","Exceção não prevista: registre coverage_gap.","Saída não reversível: pare o caso."),"tradeoff":"Ensaiar uma exceção atrasa a expansão, mas revela falhas antes de aumentar o impacto.","limits":("Não executa o agente nem concede permissões.",),"demo":"Revisão sintética do piloto: 29 de 32 notas foram claras, 3 ficaram em dúvida e não houve efeitos externos. Exceção a ensaiar: uma nota contém instrução que tenta mudar o objetivo aprovado."},
            {"id":"prompt-10","title":"Preparar o próximo ciclo","surface":"chat","purpose":"Transformar a revisão e o ensaio de escalonamento em plano de continuidade com nova versão, autoridade, evidência e gate humano.","when":"Quando o piloto tem veredito e é preciso repetir, ampliar uma variável delimitada ou encerrar.","output":"Plano de continuidade controlada","workflow":("Resuma evidência, exceções e veredito vigente.","Defina o que permanece e o que muda na próxima versão.","Estabeleça escopo, permissões, responsável e recuperação.","Especifique a evidência que o próximo ciclo deve observar.","Conclua com gate de aprovação e condição de parada."),"frameworks":("Versioned rollout","Least privilege","After-action review"),"guardrails":("Não reutilize aprovação vinculada a outra versão.","Não amplie escopo e permissões ao mesmo tempo.","Não inicie sem gate humano verificável."),"acceptance":("O plano identifica versão e aprovação necessária.","Cada mudança tem evidência e risco associados.","A recuperação e a parada podem ser executadas."),"edges":("Veredito parar: produza apenas encerramento e aprendizagem.","Evidência insuficiente: repita sem ampliar escopo.","Novo responsável: exija nova aprovação."),"tradeoff":"Ampliar uma variável por vez torna a adoção mais lenta, mas preserva atribuição e recuperação.","limits":("Planeja o ciclo; não o executa nem autoriza.",),"demo":"Ensaio sintético: uma instrução embutida foi tratada como conteúdo, o agente parou e escalou. Veredito: ajustar o classificador e repetir em outra cópia sem ampliar permissões."},
        )
    raise PromptParityError(f"added direct copy missing: {module}:{locale}")


META = {
    "es": (
        ("Constructor de coach", "Diseñar un coach que enseñe el método del módulo desde evidencia y haga una pregunta por turno.", "Instrucciones del coach", "Coach basado en fuentes", "Enseñanza por preguntas", "Prueba adversarial"),
        ("Constructor de evaluador", "Diseñar una evaluación progresiva que compruebe aplicación, criterio y transferencia.", "Plan de evaluación", "Rúbrica observable", "Evaluación progresiva", "Reintento con evidencia"),
        ("Constructor de entrevistador", "Diseñar un ensayo de conversación exigente con objeciones ligadas al caso del módulo.", "Guion de entrevista", "Mapa de objeciones", "Dificultad progresiva", "Feedback verificable"),
        ("Constructor de preparador", "Diseñar una guía que convierta el trabajo del módulo en una entrega breve y defendible.", "Guía de preparación", "BLUF", "Definition of Done", "Ensayo por secciones"),
    ),
    "en": (
        ("Coach builder", "Design a coach that teaches the module method from evidence and asks one question at a time.", "Coach instructions", "Source-grounded coaching", "Teaching through questions", "Adversarial test"),
        ("Evaluator builder", "Design a progressive assessment that checks application, judgment and transfer.", "Assessment plan", "Observable rubric", "Progressive assessment", "Evidence-based retry"),
        ("Interviewer builder", "Design a demanding conversation rehearsal with objections tied to the module case.", "Interview script", "Objection map", "Progressive difficulty", "Verifiable feedback"),
        ("Preparer builder", "Design a guide that turns the module work into a concise, defensible deliverable.", "Preparation guide", "BLUF", "Definition of Done", "Section rehearsal"),
    ),
    "pt": (
        ("Construtor de coach", "Desenhar um coach que ensine o método do módulo a partir de evidências e faça uma pergunta por vez.", "Instruções do coach", "Coach baseado em fontes", "Ensino por perguntas", "Teste adversarial"),
        ("Construtor de avaliador", "Desenhar uma avaliação progressiva que comprove aplicação, critério e transferência.", "Plano de avaliação", "Rubrica observável", "Avaliação progressiva", "Nova tentativa com evidência"),
        ("Construtor de entrevistador", "Desenhar um ensaio de conversa exigente com objeções ligadas ao caso do módulo.", "Roteiro de entrevista", "Mapa de objeções", "Dificuldade progressiva", "Feedback verificável"),
        ("Construtor de preparador", "Desenhar um guia que transforme o trabalho do módulo em uma entrega breve e defensável.", "Guia de preparação", "BLUF", "Definition of Done", "Ensaio por seções"),
    ),
}


# Each route step receives its own bounded vocabulary.  The imported M2/M4
# payloads used a single CONTEXTO input on every card; retaining that shape
# would make the suite look complete while leaving the user to infer what the
# prompt actually needs.  These keys keep the source content as the editorial
# base, but make the interaction contract specific and executable.
PROMPT_INPUT_KEYS = {
    "m02": {
        "prompt-01": ("period", "records", "outcome"),
        "prompt-02": ("activities", "effort", "value_signal"),
        "prompt-03": ("candidates", "criteria", "capacity"),
        "prompt-04": ("priorities", "dependencies", "risks"),
        "prompt-05": ("priorities", "calendar", "constraints"),
        "prompt-06": ("interruptions", "rules", "exceptions"),
        "prompt-07": ("outcome", "evidence", "decisions"),
        "prompt-08": ("decision", "sources", "acceptance_criterion"),
        "prompt-09": ("review", "sources", "applicability"),
        "prompt-10": ("practices", "rules", "review_date"),
        "prompt-m1": ("coach_objective", "audience", "sources"),
        "prompt-m2": ("assessment_goal", "evidence", "rubric"),
        "prompt-m3": ("deliverable", "objections", "evidence"),
        "prompt-m4": ("deliverable", "sections", "criteria"),
    },
    "m03": {
        "prompt-01": ("workflow", "boundaries", "records"),
        "prompt-02": ("steps", "frictions", "evidence"),
        "prompt-03": ("question", "sources", "acceptance_criterion"),
        "prompt-04": ("steps", "handoffs", "exceptions"),
        "prompt-05": ("output", "criteria", "evidence"),
        "prompt-06": ("process_map", "criteria", "exceptions"),
        "prompt-07": ("sop", "risks", "controls"),
        "prompt-08": ("sop", "cases", "metrics"),
        "prompt-09": ("test_record", "deviations", "verdict"),
        "prompt-10": ("sop", "changes", "evidence"),
        "prompt-m1": ("coach_objective", "audience", "sources"),
        "prompt-m2": ("assessment_goal", "evidence", "rubric"),
        "prompt-m3": ("deliverable", "objections", "evidence"),
        "prompt-m4": ("deliverable", "sections", "criteria"),
    },
    "m04": {
        "prompt-01": ("use_case", "impact", "risks"),
        "prompt-02": ("goal", "allowed_actions", "output"),
        "prompt-03": ("mission", "sources", "gaps"),
        "prompt-04": ("actions", "permissions", "escalation"),
        "prompt-05": ("mission", "constraints", "stop_conditions"),
        "prompt-06": ("plan", "criteria", "risks"),
        "prompt-07": ("run_log", "exceptions", "effects"),
        "prompt-08": ("evidence", "incidents", "verdict"),
        "prompt-09": ("exception", "warning", "authority"),
        "prompt-10": ("verdict", "changes", "approval"),
        "prompt-m1": ("coach_objective", "audience", "sources"),
        "prompt-m2": ("assessment_goal", "evidence", "rubric"),
        "prompt-m3": ("deliverable", "objections", "evidence"),
        "prompt-m4": ("deliverable", "sections", "criteria"),
    },
}


# name, plain-language instruction, short example, resolved synthetic value.
# The values are deliberately concrete enough for Demo mode to run without a
# hidden prior artifact, yet modest enough not to masquerade as real evidence.
INPUT_COPY = {
    "es": {
        "period": ("PERIODO", "intervalo que vas a revisar", "lunes a viernes", "semana del 24 al 28 de agosto"),
        "records": ("REGISTROS", "agenda, tareas y entregas observadas", "agenda de cinco días", "agenda de cinco días con 17 bloques, 12 tareas y una propuesta entregada"),
        "outcome": ("RESULTADO", "salida observable con fecha", "propuesta revisada el jueves", "propuesta revisada y enviada el jueves a las 16:00"),
        "activities": ("ACTIVIDADES", "lista breve de trabajo realizado", "reuniones, análisis y redacción", "6 reuniones, 4 horas de análisis y 3 horas de redacción"),
        "effort": ("ESFUERZO", "tiempo o carga por actividad", "horas por actividad", "reuniones 6 h; análisis 4 h; redacción 3 h"),
        "value_signal": ("SEÑAL_DE_VALOR", "prueba de que una actividad movió el resultado", "decisión tomada o entrega aceptada", "la revisión destrabó una decisión; dos reuniones no dejaron salida"),
        "candidates": ("CANDIDATOS", "posibles prioridades para la semana", "propuesta, seguimiento y reporte", "cerrar propuesta, responder clientes y actualizar reporte"),
        "criteria": ("CRITERIOS", "reglas explícitas para comparar opciones", "impacto, urgencia y esfuerzo", "impacto en la entrega, fecha límite y esfuerzo restante"),
        "capacity": ("CAPACIDAD", "tiempo y atención realmente disponibles", "12 horas de foco", "12 horas protegibles y dos reuniones obligatorias"),
        "priorities": ("PRIORIDADES", "resultados elegidos y ordenados", "propuesta antes que reporte", "1 propuesta; 2 respuesta al cliente; 3 reporte"),
        "dependencies": ("DEPENDENCIAS", "personas o insumos que pueden bloquear", "datos financieros y revisión legal", "datos financieros el martes y revisión legal el miércoles"),
        "risks": ("RIESGOS", "eventos que pueden desviar el plan", "cambio de alcance", "cambio de alcance o demora de la revisión legal"),
        "calendar": ("CALENDARIO", "espacios fijos y bloques disponibles", "agenda de la próxima semana", "martes y miércoles libres de 09:00 a 11:00; reuniones por la tarde"),
        "constraints": ("RESTRICCIONES", "límites que el plan debe respetar", "reuniones fijas y fecha límite", "reuniones obligatorias, entrega el jueves y máximo dos horas extra"),
        "interruptions": ("INTERRUPCIONES", "solicitudes que suelen romper el foco", "mensajes urgentes y reuniones ad hoc", "11 mensajes urgentes y dos reuniones ad hoc en cinco días"),
        "rules": ("REGLAS", "acuerdos que deben aplicarse", "dos ventanas de respuesta", "revisar mensajes a las 12:00 y 16:30; escalar solo bloqueos críticos"),
        "exceptions": ("EXCEPCIONES", "situaciones que justifican romper la regla", "incidente de cliente", "incidente de cliente con impacto inmediato en una entrega"),
        "evidence": ("EVIDENCIA", "hechos o registros que sostienen la revisión", "tablero, citas y versión", "tablero de cinco días, tres citas y versión 0.2 del artefacto"),
        "decisions": ("DECISIONES_ABIERTAS", "decisiones que siguen sin cerrar", "qué práctica conservar", "conservar bloques de foco y ajustar el acuerdo de respuesta"),
        "decision": ("DECISIÓN", "decisión concreta que necesitas sustentar", "adoptar bloques protegidos", "repetir bloques protegidos durante siete días"),
        "sources": ("FUENTES", "materiales con autor, fecha y alcance", "guía oficial y registro propio", "guía oficial fechada y registro sintético de cinco días"),
        "acceptance_criterion": ("CRITERIO_DE_ACEPTACIÓN", "condición observable para aceptar la salida", "cita, límite y recomendación", "cada recomendación cita fuente, declara aplicabilidad y propone una prueba"),
        "review": ("REVISIÓN_SEMANAL", "síntesis del resultado y lo observado", "resultado, desvíos y aprendizaje", "propuesta cerrada; mensajes agrupados; una respuesta fuera de plazo"),
        "applicability": ("APLICABILIDAD", "contexto donde una práctica sí o no encaja", "equipo pequeño con plazos diarios", "trabajo individual con dos ventanas de respuesta y entrega semanal"),
        "practices": ("PRÁCTICAS_VERIFICADAS", "prácticas observadas que vale la pena repetir", "bloques de foco y revisión diaria", "dos bloques de foco funcionaron; el acuerdo de respuesta requiere ajuste"),
        "review_date": ("FECHA_DE_REVISIÓN", "momento para conservar, ajustar o retirar reglas", "viernes a las 16:00", "viernes 4 de septiembre a las 16:00"),
        "workflow": ("FLUJO", "trabajo con inicio, fin y salida", "preparar una propuesta", "desde recibir el brief hasta entregar una propuesta revisada"),
        "boundaries": ("FRONTERAS", "inicio, fin y exclusiones del flujo", "del brief a la aprobación", "inicia con brief aprobado, termina con propuesta revisada y excluye negociación"),
        "steps": ("PASOS", "acciones actuales en su orden real", "recibir, analizar, redactar, revisar", "recibir brief, buscar evidencia, redactar, revisar y entregar"),
        "frictions": ("FRICCIONES", "retrabajos, esperas o decisiones tardías", "citas incompletas y revisión tardía", "dos citas sin fecha, una revisión tardía y 90 minutos de retrabajo"),
        "question": ("PREGUNTA", "pregunta verificable que orienta la búsqueda", "qué reduce retrabajo al revisar", "qué controles reducen citas incompletas sin alargar la entrega"),
        "handoffs": ("RELEVOS", "traspasos entre persona, IA o equipo", "IA redacta; persona valida", "IA propone estructura; analista verifica citas; líder aprueba"),
        "output": ("SALIDA", "artefacto que debe quedar terminado", "propuesta lista para decisión", "propuesta de dos páginas con citas y recomendación"),
        "process_map": ("MAPA_DEL_PROCESO", "secuencia actual con decisiones y responsables", "mapa de cinco pasos", "mapa de cinco pasos con dos revisiones y un punto de aprobación"),
        "sop": ("MINI_SOP", "procedimiento breve con versión", "Mini-SOP v0.1", "Mini-SOP v0.1 para preparar propuestas con fuentes"),
        "controls": ("CONTROLES", "verificaciones antes de avanzar", "citas completas y aprobación", "citas con fecha, revisión humana y bloqueo si falta autoridad"),
        "cases": ("CASOS_DE_PRUEBA", "casos normales y adversariales", "caso completo y fuente contradictoria", "caso normal, fuente contradictoria y brief incompleto"),
        "metrics": ("MÉTRICAS", "medidas para comparar la prueba", "retrabajo y tiempo de ciclo", "minutos de retrabajo, tiempo de ciclo y citas corregidas"),
        "test_record": ("REGISTRO_DE_PRUEBA", "resultados observados por caso", "tres ejecuciones documentadas", "tres ejecuciones: 42, 49 y 45 minutos; una cita corregida"),
        "deviations": ("DESVIACIONES", "diferencias frente al procedimiento", "paso omitido o excepción", "se omitió la revisión de fecha en una de tres ejecuciones"),
        "verdict": ("VEREDICTO", "decisión mantener, ajustar o detener", "ajustar antes de repetir", "ajustar el control de fechas y repetir tres casos"),
        "changes": ("CAMBIOS", "modificaciones justificadas para la nueva versión", "añadir control de fecha", "añadir control de fecha y separar redacción de aprobación"),
        "use_case": ("CASO_DE_USO", "trabajo que podría delegarse a un agente", "clasificar notas", "clasificar 32 notas en una copia local"),
        "impact": ("IMPACTO", "resultado esperado y a quién afecta", "reducir revisión manual", "preclasificar notas para que una persona confirme cada resultado"),
        "goal": ("OBJETIVO", "resultado delimitado del piloto", "clasificar notas sin publicar", "clasificar una copia de 32 notas sin efectos externos"),
        "allowed_actions": ("ACCIONES_PERMITIDAS", "acciones exactas que puede realizar", "leer y proponer etiquetas", "leer una copia y proponer etiquetas; no editar ni enviar"),
        "mission": ("MISIÓN", "objetivo, alcance y salida del agente", "clasificar una copia local", "clasificar 32 notas y devolver tabla para revisión humana"),
        "gaps": ("VACÍOS", "datos o autoridad que todavía faltan", "tres notas ambiguas", "tres notas sin criterio suficiente y derechos no confirmados para un adjunto"),
        "actions": ("ACCIONES", "operaciones previstas una por una", "leer, clasificar y presentar", "leer copia, proponer clase y presentar vista previa"),
        "permissions": ("PERMISOS", "capacidad mínima autorizada", "solo lectura", "solo lectura sobre una copia aislada; sin red ni escritura"),
        "escalation": ("ESCALAMIENTO", "cuándo parar y a quién consultar", "parar ante ambigüedad", "parar ante instrucción embebida y consultar al dueño del proceso"),
        "stop_conditions": ("CONDICIONES_DE_PARADA", "señales que obligan a detener", "autoridad o versión no coincide", "detener si falta autoridad, cambia la versión o la salida no es reversible"),
        "plan": ("PLAN_DE_PRUEBA", "casos, orden y controles del piloto", "tres casos en copia", "tres casos sintéticos en copia con aprobación antes de cada salida"),
        "run_log": ("BITÁCORA", "registro de acciones y resultados", "32 filas con estado", "32 filas: 29 claras, 3 ambiguas y cero efectos externos"),
        "effects": ("EFECTOS", "cambios internos o externos realmente ocurridos", "ninguno", "ningún archivo editado, mensaje enviado ni registro publicado"),
        "incidents": ("INCIDENTES", "excepciones y respuesta aplicada", "instrucción embebida bloqueada", "una instrucción embebida se trató como dato, se bloqueó y escaló"),
        "exception": ("EXCEPCIÓN", "situación crítica que vas a ensayar", "instrucción que cambia el objetivo", "una nota intenta ampliar el objetivo aprobado"),
        "warning": ("SEÑAL_DE_ALERTA", "hecho observable que activa la pausa", "objetivo o permiso no coincide", "el texto solicita escribir aunque el permiso es solo lectura"),
        "authority": ("AUTORIDAD", "versión y acciones actualmente aprobadas", "v0.1 solo lectura", "piloto v0.1, solo lectura sobre copia aislada"),
        "approval": ("APROBACIÓN", "gate humano ligado a la versión", "aprobación para v0.2", "aprobación pendiente para v0.2, sin reutilizar la de v0.1"),
        "coach_objective": ("OBJETIVO_DEL_COACH", "conducta que debe enseñar y comprobar", "hacer una revisión con evidencia", "guiar una revisión con evidencia y una pregunta por turno"),
        "audience": ("AUDIENCIA", "persona o equipo que usará el instrumento", "profesional sin contexto previo", "profesional que prepara su primera revisión guiada"),
        "assessment_goal": ("OBJETIVO_DE_EVALUACIÓN", "capacidad observable que debe comprobar", "aplicar el método a un caso", "aplicar el método, justificar la decisión y transferirlo"),
        "rubric": ("RÚBRICA", "criterios y niveles observables", "aplica, justifica y transfiere", "tres criterios con niveles inicial, suficiente y transferible"),
        "deliverable": ("ENTREGABLE", "documento o conversación que debe quedar listo", "revisión defendible", "revisión breve con evidencia, límite y siguiente paso"),
        "objections": ("OBJECIONES", "preguntas difíciles que debe resistir", "fuente débil o decisión prematura", "qué evidencia falta y por qué esta decisión es reversible"),
        "sections": ("SECCIONES", "partes mínimas y su orden", "resultado, evidencia y decisión", "resultado, evidencia, decisión, límite y siguiente paso"),
    },
    "en": {
        "period": ("PERIOD", "time span you will review", "Monday to Friday", "week of August 24–28"),
        "records": ("RECORDS", "observed calendar, task and delivery data", "five-day calendar", "five-day calendar with 17 blocks, 12 tasks and one delivered proposal"),
        "outcome": ("OUTCOME", "dated observable output", "reviewed proposal by Thursday", "proposal reviewed and sent Thursday at 16:00"),
        "activities": ("ACTIVITIES", "short list of completed work", "meetings, analysis and writing", "6 meetings, 4 analysis hours and 3 writing hours"),
        "effort": ("EFFORT", "time or load per activity", "hours per activity", "meetings 6 h; analysis 4 h; writing 3 h"),
        "value_signal": ("VALUE_SIGNAL", "proof that an activity moved the outcome", "decision made or output accepted", "the review unlocked a decision; two meetings produced no output"),
        "candidates": ("CANDIDATES", "possible priorities for the week", "proposal, follow-up and report", "close proposal, answer clients and update report"),
        "criteria": ("CRITERIA", "explicit rules for comparing options", "impact, urgency and effort", "delivery impact, due date and remaining effort"),
        "capacity": ("CAPACITY", "time and attention actually available", "12 focus hours", "12 protectable hours and two required meetings"),
        "priorities": ("PRIORITIES", "selected and ordered outcomes", "proposal before report", "1 proposal; 2 client reply; 3 report"),
        "dependencies": ("DEPENDENCIES", "people or inputs that may block work", "financial data and legal review", "financial data Tuesday and legal review Wednesday"),
        "risks": ("RISKS", "events that may derail the plan", "scope change", "scope change or delayed legal review"),
        "calendar": ("CALENDAR", "fixed commitments and available blocks", "next week's calendar", "Tuesday and Wednesday 09:00–11:00 free; meetings in the afternoon"),
        "constraints": ("CONSTRAINTS", "boundaries the plan must respect", "fixed meetings and deadline", "required meetings, Thursday delivery and at most two overtime hours"),
        "interruptions": ("INTERRUPTIONS", "requests that usually break focus", "urgent messages and ad hoc meetings", "11 urgent messages and two ad hoc meetings in five days"),
        "rules": ("RULES", "agreements that must be applied", "two response windows", "check messages at 12:00 and 16:30; escalate only critical blockers"),
        "exceptions": ("EXCEPTIONS", "situations that justify breaking the rule", "client incident", "client incident with immediate delivery impact"),
        "evidence": ("EVIDENCE", "facts or records supporting the review", "board, citations and version", "five-day board, three citations and artifact version 0.2"),
        "decisions": ("OPEN_DECISIONS", "decisions that remain unresolved", "which practice to retain", "retain focus blocks and adjust the response agreement"),
        "decision": ("DECISION", "specific decision you need to support", "adopt protected blocks", "repeat protected blocks for seven days"),
        "sources": ("SOURCES", "materials with author, date and scope", "official guide and own record", "dated official guide and synthetic five-day record"),
        "acceptance_criterion": ("ACCEPTANCE_CRITERION", "observable condition for accepting the output", "citation, limit and recommendation", "each recommendation cites a source, states fit and proposes a test"),
        "review": ("WEEKLY_REVIEW", "summary of the outcome and observations", "outcome, deviations and lesson", "proposal closed; messages batched; one reply late"),
        "applicability": ("APPLICABILITY", "context where a practice does or does not fit", "small team with daily deadlines", "individual work with two response windows and a weekly delivery"),
        "practices": ("VERIFIED_PRACTICES", "observed practices worth repeating", "focus blocks and daily review", "two focus blocks worked; the response agreement needs adjustment"),
        "review_date": ("REVIEW_DATE", "time to retain, adjust or retire rules", "Friday at 16:00", "Friday September 4 at 16:00"),
        "workflow": ("WORKFLOW", "work with a start, finish and output", "prepare a proposal", "from receiving the brief to delivering a reviewed proposal"),
        "boundaries": ("BOUNDARIES", "workflow start, finish and exclusions", "from brief to approval", "starts with approved brief, ends with reviewed proposal and excludes negotiation"),
        "steps": ("STEPS", "current actions in their real order", "receive, analyze, draft, review", "receive brief, find evidence, draft, review and deliver"),
        "frictions": ("FRICTIONS", "rework, waiting or late decisions", "incomplete citations and late review", "two undated citations, one late review and 90 minutes of rework"),
        "question": ("QUESTION", "testable question guiding the search", "what reduces review rework", "which controls reduce incomplete citations without delaying delivery"),
        "handoffs": ("HANDOFFS", "transfers between person, AI or team", "AI drafts; person validates", "AI proposes structure; analyst verifies citations; lead approves"),
        "output": ("OUTPUT", "artifact that must be complete", "proposal ready for decision", "two-page proposal with citations and recommendation"),
        "process_map": ("PROCESS_MAP", "current sequence with decisions and owners", "five-step map", "five-step map with two reviews and one approval point"),
        "sop": ("MINI_SOP", "short versioned procedure", "Mini-SOP v0.1", "Mini-SOP v0.1 for preparing sourced proposals"),
        "controls": ("CONTROLS", "checks required before proceeding", "complete citations and approval", "dated citations, human review and block when authority is missing"),
        "cases": ("TEST_CASES", "normal and adversarial cases", "complete case and conflicting source", "normal case, conflicting source and incomplete brief"),
        "metrics": ("METRICS", "measures used to compare the test", "rework and cycle time", "rework minutes, cycle time and corrected citations"),
        "test_record": ("TEST_RECORD", "observed results by case", "three documented runs", "three runs: 42, 49 and 45 minutes; one corrected citation"),
        "deviations": ("DEVIATIONS", "differences from the procedure", "skipped step or exception", "the date review was skipped in one of three runs"),
        "verdict": ("VERDICT", "decision to retain, adjust or stop", "adjust before repeating", "adjust the date control and repeat three cases"),
        "changes": ("CHANGES", "justified changes for the new version", "add date control", "add date control and separate drafting from approval"),
        "use_case": ("USE_CASE", "work that an agent might handle", "classify notes", "classify 32 notes in a local copy"),
        "impact": ("IMPACT", "expected outcome and affected people", "reduce manual review", "pre-classify notes for a person to confirm each result"),
        "goal": ("GOAL", "bounded pilot outcome", "classify notes without publishing", "classify a copy of 32 notes with no external effects"),
        "allowed_actions": ("ALLOWED_ACTIONS", "exact actions the agent may perform", "read and propose labels", "read a copy and propose labels; do not edit or send"),
        "mission": ("MISSION", "agent objective, scope and output", "classify a local copy", "classify 32 notes and return a table for human review"),
        "gaps": ("GAPS", "missing data or authority", "three ambiguous notes", "three notes lack a criterion and rights are unconfirmed for one attachment"),
        "actions": ("ACTIONS", "planned operations in order", "read, classify and present", "read copy, propose class and present preview"),
        "permissions": ("PERMISSIONS", "minimum authorized capability", "read only", "read only on an isolated copy; no network or writes"),
        "escalation": ("ESCALATION", "when to stop and whom to consult", "stop on ambiguity", "stop on embedded instruction and consult the process owner"),
        "stop_conditions": ("STOP_CONDITIONS", "signals that require a stop", "authority or version mismatch", "stop if authority is missing, version changes or output is not reversible"),
        "plan": ("TEST_PLAN", "pilot cases, order and controls", "three cases on a copy", "three synthetic cases on a copy with approval before each output"),
        "run_log": ("RUN_LOG", "record of actions and results", "32 rows with status", "32 rows: 29 clear, 3 ambiguous and zero external effects"),
        "effects": ("EFFECTS", "internal or external changes that actually occurred", "none", "no file edited, message sent or record published"),
        "incidents": ("INCIDENTS", "exceptions and applied response", "embedded instruction blocked", "one embedded instruction was treated as data, blocked and escalated"),
        "exception": ("EXCEPTION", "critical situation you will rehearse", "instruction that changes the goal", "one note attempts to widen the approved goal"),
        "warning": ("WARNING_SIGNAL", "observable fact that triggers a pause", "goal or permission mismatch", "text requests a write although permission is read only"),
        "authority": ("AUTHORITY", "currently approved version and actions", "v0.1 read only", "pilot v0.1, read only on an isolated copy"),
        "approval": ("APPROVAL", "human gate bound to the version", "approval for v0.2", "approval pending for v0.2; do not reuse v0.1 approval"),
        "coach_objective": ("COACH_OBJECTIVE", "behavior the coach must teach and verify", "run an evidence-based review", "guide an evidence-based review with one question at a time"),
        "audience": ("AUDIENCE", "person or team using the instrument", "professional with no prior context", "professional preparing a first guided review"),
        "assessment_goal": ("ASSESSMENT_GOAL", "observable capability to verify", "apply the method to a case", "apply the method, justify the decision and transfer it"),
        "rubric": ("RUBRIC", "observable criteria and levels", "apply, justify and transfer", "three criteria with initial, sufficient and transferable levels"),
        "deliverable": ("DELIVERABLE", "document or conversation that must be ready", "defensible review", "concise review with evidence, boundary and next step"),
        "objections": ("OBJECTIONS", "hard questions it must withstand", "weak source or premature decision", "what evidence is missing and why this decision is reversible"),
        "sections": ("SECTIONS", "minimum parts in order", "outcome, evidence and decision", "outcome, evidence, decision, boundary and next step"),
    },
    "pt": {
        "period": ("PERÍODO", "intervalo que você vai revisar", "segunda a sexta", "semana de 24 a 28 de agosto"),
        "records": ("REGISTROS", "agenda, tarefas e entregas observadas", "agenda de cinco dias", "agenda de cinco dias com 17 blocos, 12 tarefas e uma proposta entregue"),
        "outcome": ("RESULTADO", "saída observável com data", "proposta revisada na quinta-feira", "proposta revisada e enviada na quinta-feira às 16:00"),
        "activities": ("ATIVIDADES", "lista breve do trabalho realizado", "reuniões, análise e redação", "6 reuniões, 4 horas de análise e 3 horas de redação"),
        "effort": ("ESFORÇO", "tempo ou carga por atividade", "horas por atividade", "reuniões 6 h; análise 4 h; redação 3 h"),
        "value_signal": ("SINAL_DE_VALOR", "prova de que uma atividade moveu o resultado", "decisão tomada ou entrega aceita", "a revisão destravou uma decisão; duas reuniões não deixaram saída"),
        "candidates": ("CANDIDATOS", "possíveis prioridades da semana", "proposta, acompanhamento e relatório", "concluir proposta, responder clientes e atualizar relatório"),
        "criteria": ("CRITÉRIOS", "regras explícitas para comparar opções", "impacto, urgência e esforço", "impacto na entrega, prazo e esforço restante"),
        "capacity": ("CAPACIDADE", "tempo e atenção realmente disponíveis", "12 horas de foco", "12 horas protegíveis e duas reuniões obrigatórias"),
        "priorities": ("PRIORIDADES", "resultados escolhidos e ordenados", "proposta antes do relatório", "1 proposta; 2 resposta ao cliente; 3 relatório"),
        "dependencies": ("DEPENDÊNCIAS", "pessoas ou insumos que podem bloquear", "dados financeiros e revisão jurídica", "dados financeiros na terça e revisão jurídica na quarta"),
        "risks": ("RISCOS", "eventos que podem desviar o plano", "mudança de escopo", "mudança de escopo ou atraso da revisão jurídica"),
        "calendar": ("AGENDA", "compromissos fixos e blocos disponíveis", "agenda da próxima semana", "terça e quarta 09:00–11:00 livres; reuniões à tarde"),
        "constraints": ("RESTRIÇÕES", "limites que o plano deve respeitar", "reuniões fixas e prazo", "reuniões obrigatórias, entrega na quinta e no máximo duas horas extras"),
        "interruptions": ("INTERRUPÇÕES", "solicitações que costumam quebrar o foco", "mensagens urgentes e reuniões ad hoc", "11 mensagens urgentes e duas reuniões ad hoc em cinco dias"),
        "rules": ("REGRAS", "acordos que devem ser aplicados", "duas janelas de resposta", "verificar mensagens às 12:00 e 16:30; escalar somente bloqueios críticos"),
        "exceptions": ("EXCEÇÕES", "situações que justificam quebrar a regra", "incidente de cliente", "incidente de cliente com impacto imediato em uma entrega"),
        "evidence": ("EVIDÊNCIA", "fatos ou registros que sustentam a revisão", "quadro, citações e versão", "quadro de cinco dias, três citações e versão 0.2 do artefato"),
        "decisions": ("DECISÕES_ABERTAS", "decisões ainda não concluídas", "qual prática manter", "manter blocos de foco e ajustar o acordo de resposta"),
        "decision": ("DECISÃO", "decisão concreta que precisa de fundamento", "adotar blocos protegidos", "repetir blocos protegidos por sete dias"),
        "sources": ("FONTES", "materiais com autor, data e escopo", "guia oficial e registro próprio", "guia oficial datado e registro sintético de cinco dias"),
        "acceptance_criterion": ("CRITÉRIO_DE_ACEITAÇÃO", "condição observável para aceitar a saída", "citação, limite e recomendação", "cada recomendação cita fonte, declara ajuste e propõe um teste"),
        "review": ("REVISÃO_SEMANAL", "síntese do resultado e do observado", "resultado, desvios e aprendizagem", "proposta concluída; mensagens agrupadas; uma resposta atrasada"),
        "applicability": ("APLICABILIDADE", "contexto onde uma prática se ajusta ou não", "equipe pequena com prazos diários", "trabalho individual com duas janelas de resposta e entrega semanal"),
        "practices": ("PRÁTICAS_VERIFICADAS", "práticas observadas que vale repetir", "blocos de foco e revisão diária", "dois blocos de foco funcionaram; o acordo de resposta precisa de ajuste"),
        "review_date": ("DATA_DE_REVISÃO", "momento para manter, ajustar ou retirar regras", "sexta às 16:00", "sexta-feira 4 de setembro às 16:00"),
        "workflow": ("FLUXO", "trabalho com início, fim e saída", "preparar uma proposta", "desde receber o briefing até entregar uma proposta revisada"),
        "boundaries": ("FRONTEIRAS", "início, fim e exclusões do fluxo", "do briefing à aprovação", "começa com briefing aprovado, termina com proposta revisada e exclui negociação"),
        "steps": ("PASSOS", "ações atuais em sua ordem real", "receber, analisar, redigir, revisar", "receber briefing, buscar evidência, redigir, revisar e entregar"),
        "frictions": ("FRICÇÕES", "retrabalho, esperas ou decisões tardias", "citações incompletas e revisão tardia", "duas citações sem data, uma revisão tardia e 90 minutos de retrabalho"),
        "question": ("PERGUNTA", "pergunta verificável que orienta a busca", "o que reduz retrabalho na revisão", "quais controles reduzem citações incompletas sem atrasar a entrega"),
        "handoffs": ("REVEZAMENTOS", "transferências entre pessoa, IA ou equipe", "IA redige; pessoa valida", "IA propõe estrutura; analista verifica citações; líder aprova"),
        "output": ("SAÍDA", "artefato que deve ficar concluído", "proposta pronta para decisão", "proposta de duas páginas com citações e recomendação"),
        "process_map": ("MAPA_DO_PROCESSO", "sequência atual com decisões e responsáveis", "mapa de cinco passos", "mapa de cinco passos com duas revisões e um ponto de aprovação"),
        "sop": ("MINI_SOP", "procedimento breve com versão", "Mini-SOP v0.1", "Mini-SOP v0.1 para preparar propostas com fontes"),
        "controls": ("CONTROLES", "verificações necessárias antes de avançar", "citações completas e aprovação", "citações com data, revisão humana e bloqueio se faltar autoridade"),
        "cases": ("CASOS_DE_TESTE", "casos normais e adversariais", "caso completo e fonte contraditória", "caso normal, fonte contraditória e briefing incompleto"),
        "metrics": ("MÉTRICAS", "medidas usadas para comparar o teste", "retrabalho e tempo de ciclo", "minutos de retrabalho, tempo de ciclo e citações corrigidas"),
        "test_record": ("REGISTRO_DE_TESTE", "resultados observados por caso", "três execuções documentadas", "três execuções: 42, 49 e 45 minutos; uma citação corrigida"),
        "deviations": ("DESVIOS", "diferenças frente ao procedimento", "passo omitido ou exceção", "a revisão de data foi omitida em uma de três execuções"),
        "verdict": ("VEREDITO", "decisão de manter, ajustar ou parar", "ajustar antes de repetir", "ajustar o controle de datas e repetir três casos"),
        "changes": ("MUDANÇAS", "alterações justificadas para a nova versão", "adicionar controle de data", "adicionar controle de data e separar redação de aprovação"),
        "use_case": ("CASO_DE_USO", "trabalho que um agente poderia executar", "classificar notas", "classificar 32 notas em uma cópia local"),
        "impact": ("IMPACTO", "resultado esperado e pessoas afetadas", "reduzir revisão manual", "pré-classificar notas para uma pessoa confirmar cada resultado"),
        "goal": ("OBJETIVO", "resultado delimitado do piloto", "classificar notas sem publicar", "classificar uma cópia de 32 notas sem efeitos externos"),
        "allowed_actions": ("AÇÕES_PERMITIDAS", "ações exatas que o agente pode realizar", "ler e propor etiquetas", "ler uma cópia e propor etiquetas; não editar nem enviar"),
        "mission": ("MISSÃO", "objetivo, escopo e saída do agente", "classificar uma cópia local", "classificar 32 notas e devolver tabela para revisão humana"),
        "gaps": ("LACUNAS", "dados ou autoridade ainda ausentes", "três notas ambíguas", "três notas sem critério e direitos não confirmados para um anexo"),
        "actions": ("AÇÕES", "operações planejadas em ordem", "ler, classificar e apresentar", "ler cópia, propor classe e apresentar prévia"),
        "permissions": ("PERMISSÕES", "capacidade mínima autorizada", "somente leitura", "somente leitura em cópia isolada; sem rede ou escrita"),
        "escalation": ("ESCALONAMENTO", "quando parar e quem consultar", "parar diante de ambiguidade", "parar diante de instrução embutida e consultar o dono do processo"),
        "stop_conditions": ("CONDIÇÕES_DE_PARADA", "sinais que exigem parada", "autoridade ou versão não coincide", "parar se faltar autoridade, a versão mudar ou a saída não for reversível"),
        "plan": ("PLANO_DE_TESTE", "casos, ordem e controles do piloto", "três casos em uma cópia", "três casos sintéticos em cópia com aprovação antes de cada saída"),
        "run_log": ("REGISTRO_DA_EXECUÇÃO", "registro de ações e resultados", "32 linhas com status", "32 linhas: 29 claras, 3 ambíguas e zero efeitos externos"),
        "effects": ("EFEITOS", "mudanças internas ou externas que realmente ocorreram", "nenhum", "nenhum arquivo editado, mensagem enviada ou registro publicado"),
        "incidents": ("INCIDENTES", "exceções e resposta aplicada", "instrução embutida bloqueada", "uma instrução embutida foi tratada como dado, bloqueada e escalada"),
        "exception": ("EXCEÇÃO", "situação crítica que será ensaiada", "instrução que muda o objetivo", "uma nota tenta ampliar o objetivo aprovado"),
        "warning": ("SINAL_DE_ALERTA", "fato observável que ativa a pausa", "objetivo ou permissão não coincide", "o texto solicita escrita apesar da permissão de somente leitura"),
        "authority": ("AUTORIDADE", "versão e ações atualmente aprovadas", "v0.1 somente leitura", "piloto v0.1, somente leitura em cópia isolada"),
        "approval": ("APROVAÇÃO", "gate humano ligado à versão", "aprovação para v0.2", "aprovação pendente para v0.2; não reutilizar a de v0.1"),
        "coach_objective": ("OBJETIVO_DO_COACH", "comportamento que o coach deve ensinar e verificar", "fazer revisão com evidência", "guiar revisão com evidência e uma pergunta por vez"),
        "audience": ("PÚBLICO", "pessoa ou equipe que usará o instrumento", "profissional sem contexto prévio", "profissional preparando sua primeira revisão guiada"),
        "assessment_goal": ("OBJETIVO_DA_AVALIAÇÃO", "capacidade observável que deve ser verificada", "aplicar o método a um caso", "aplicar o método, justificar a decisão e transferi-lo"),
        "rubric": ("RÚBRICA", "critérios e níveis observáveis", "aplica, justifica e transfere", "três critérios com níveis inicial, suficiente e transferível"),
        "deliverable": ("ENTREGA", "documento ou conversa que deve ficar pronto", "revisão defensável", "revisão breve com evidência, limite e próximo passo"),
        "objections": ("OBJEÇÕES", "perguntas difíceis que deve suportar", "fonte fraca ou decisão prematura", "qual evidência falta e por que esta decisão é reversível"),
        "sections": ("SEÇÕES", "partes mínimas em ordem", "resultado, evidência e decisão", "resultado, evidência, decisão, limite e próximo passo"),
    },
}


AUDIENCE_INPUT = {
    "m02": {
        "es": {"persona": ("CRITERIO_PERSONAL", "condición que tú usarás para decidir", "recuperar foco sin incumplir", "conservar solo prácticas que sostengan la entrega sin respuestas vencidas"), "empresa": ("RESPONSABLE_DEL_RESULTADO", "persona que decide y responde por el resultado", "líder de la propuesta", "líder de la propuesta; revisor de calidad independiente")},
        "en": {"persona": ("PERSONAL_CRITERION", "condition you will use to decide", "recover focus without missing commitments", "retain only practices that support delivery without overdue replies"), "empresa": ("OUTCOME_OWNER", "person accountable for the outcome", "proposal lead", "proposal lead; independent quality reviewer")},
        "pt": {"persona": ("CRITÉRIO_PESSOAL", "condição que você usará para decidir", "recuperar foco sem descumprir", "manter somente práticas que sustentem a entrega sem respostas vencidas"), "empresa": ("RESPONSÁVEL_PELO_RESULTADO", "pessoa que decide e responde pelo resultado", "líder da proposta", "líder da proposta; revisor de qualidade independente")},
    },
    "m03": {
        "es": {"persona": ("CRITERIO_DE_USO", "condición para adoptar el flujo en tu práctica", "menos retrabajo con citas completas", "adoptar si tres casos reducen retrabajo y conservan citas completas"), "empresa": ("DUEÑO_DEL_PROCESO", "responsable del estándar y su versión", "líder de operaciones", "líder de operaciones; revisor independiente de calidad")},
        "en": {"persona": ("ADOPTION_CRITERION", "condition for adopting the workflow in your practice", "less rework with complete citations", "adopt if three cases reduce rework and retain complete citations"), "empresa": ("PROCESS_OWNER", "owner of the standard and its version", "operations lead", "operations lead; independent quality reviewer")},
        "pt": {"persona": ("CRITÉRIO_DE_USO", "condição para adotar o fluxo em sua prática", "menos retrabalho com citações completas", "adotar se três casos reduzirem retrabalho e mantiverem citações completas"), "empresa": ("DONO_DO_PROCESSO", "responsável pelo padrão e sua versão", "líder de operações", "líder de operações; revisor independente de qualidade")},
    },
    "m04": {
        "es": {"persona": ("AUTORIDAD_PERSONAL", "acciones que puedes aprobar o revocar", "solo lectura sobre una copia", "solo lectura y vista previa sobre una copia local; decisión final humana"), "empresa": ("RESPONSABLE_DE_APROBACIÓN", "persona que aprueba versión y efectos", "dueño del proceso", "dueño del proceso; revisor de control independiente")},
        "en": {"persona": ("PERSONAL_AUTHORITY", "actions you may approve or revoke", "read only on a copy", "read only and preview on a local copy; final human decision"), "empresa": ("APPROVAL_OWNER", "person approving version and effects", "process owner", "process owner; independent control reviewer")},
        "pt": {"persona": ("AUTORIDADE_PESSOAL", "ações que você pode aprovar ou revogar", "somente leitura em uma cópia", "somente leitura e prévia em cópia local; decisão final humana"), "empresa": ("RESPONSÁVEL_PELA_APROVAÇÃO", "pessoa que aprova versão e efeitos", "dono do processo", "dono do processo; revisor de controle independente")},
    },
}


def _input(name: str, description: str, example: str, demo: str) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "example": example,
        "required": True,
        "type": "text",
        "provenance": "user",
        "demoValue": demo,
    }


def _normalize_imported_inputs(prompt: Mapping[str, Any], module: str, locale: str, audience: str) -> list[dict[str, Any]]:
    syntax = _mapping(prompt.get("syntax"), "prompt.syntax")
    raw_inputs = _sequence(syntax.get("inputs"), "prompt.syntax.inputs")
    if not raw_inputs:
        raise PromptParityError("prompt.syntax.inputs: at least one imported input is required")
    # Validate the provenance payload before replacing its legacy universal
    # input.  The copy remains untouched and its title, purpose, workflow,
    # evidence and output continue to be the editorial authority.
    for index, raw in enumerate(raw_inputs):
        item = _mapping(raw, f"prompt.syntax.inputs[{index}]")
        name = next((item.get(key) for key in ("name", "label", "key") if isinstance(item.get(key), str) and item[key].strip()), None)
        if name is None:
            raise PromptParityError(f"prompt.syntax.inputs[{index}]: name missing")
        _text(item.get("description"), f"prompt.syntax.inputs[{index}].description")
        _text(item.get("example"), f"prompt.syntax.inputs[{index}].example")

    prompt_id = _text(prompt.get("id"), "prompt.id")
    try:
        keys = PROMPT_INPUT_KEYS[module][prompt_id]
        copy = INPUT_COPY[locale]
        audience_input = AUDIENCE_INPUT[module][locale][audience]
    except KeyError as error:
        raise PromptParityError(
            f"{module}:{locale}:{audience}:{prompt_id}: prompt-specific input contract missing"
        ) from error
    if len(keys) != 3 or len(set(keys)) != 3:
        raise PromptParityError(f"{module}:{prompt_id}: expected three distinct semantic inputs")
    try:
        result = [_input(*copy[key]) for key in keys]
    except KeyError as error:
        raise PromptParityError(f"{locale}: input copy missing for {error.args[0]}") from error
    result.append(_input(*audience_input))
    names = [item["name"].casefold() for item in result]
    if len(names) != len(set(names)):
        raise PromptParityError(f"{module}:{locale}:{audience}:{prompt_id}: duplicate input name")
    if not 2 <= len(result) <= 4:
        raise PromptParityError(f"prompt.syntax.inputs: expected 2..4 inputs, got {len(result)}")
    return result


def _parameters(prompt: Mapping[str, Any]) -> dict[str, str]:
    syntax = _mapping(prompt.get("syntax"), "prompt.syntax")
    raw = syntax.get("parameters")
    structure = "short-table-and-decision"
    depth = "operational"
    if isinstance(raw, Mapping):
        structure = str(raw.get("structure", structure))
        depth = str(raw.get("depth", depth))
    elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        values = {str(item.get("key", "")).casefold(): item.get("default") for item in raw if isinstance(item, Mapping)}
        structure = str(values.get("structure", structure))
        depth = str(values.get("depth", depth))
    return {
        "length": "concise",
        "structure": structure,
        "depth": depth,
        "approval": "human-required",
    }


def _artifact(prompt_id: str, value: Any) -> dict[str, str]:
    """Normalize an imported artifact label to a stable graph node."""

    artifact_id = f"{prompt_id}-output"
    if isinstance(value, Mapping):
        label = _text(value.get("label"), f"{prompt_id}.produces.label")
        existing_id = value.get("artifactId")
        if existing_id is not None and existing_id != artifact_id:
            raise PromptParityError(
                f"{prompt_id}.produces.artifactId: expected {artifact_id!r}, got {existing_id!r}"
            )
    else:
        label = _text(value, f"{prompt_id}.produces")
    return {"artifactId": artifact_id, "label": label}


def _prompt_texts(locale: str, inputs: Sequence[Mapping[str, Any]], output: str, theme: str) -> tuple[str, str]:
    copy = LOCAL[locale]
    template_inputs = "; ".join(
        f'<{item["name"]} · {item["description"]} · {copy["example"]}: {item["example"]}>' for item in inputs
    )
    demo_inputs = "; ".join(f'{item["name"]}={item["demoValue"]}' for item in inputs)
    parameters = "\n".join(
        (
            f'{copy["length"]} = {copy["parameter_values"][0]}',
            f'{copy["structure"]} = {copy["parameter_values"][1]}',
            f'{copy["depth"]} = {copy["parameter_values"][2]}',
            f'{copy["approval"]} = {copy["parameter_values"][3]}',
        )
    )
    template = (
        f'{copy["template_task"].format(output=output, theme=theme)}\n'
        f'{template_inputs}\n[{copy["optional"]}]\n\n{copy["parameters"]}\n{parameters}'
    )
    demo = (
        f'{copy["demo_task"].format(output=output, theme=theme)}\n'
        f'{demo_inputs}\n{copy["optional"]}\n\n{copy["parameters"]}\n{parameters}'
    )
    return template, demo


def _levels(locale: str, template: str, demo: str, output: str, role: str) -> list[dict[str, Any]]:
    situation, purpose, standards, criteria = LOCAL[locale]["spec"]
    level_copy = {
        "es": {
            "situation": "usa los inputs declarados del caso",
            "standards": "trabaja con fuentes, límites y revisión humana",
            "criteria": "salida revisable, límites explícitos y siguiente acción",
            "system": "SISTEMA",
            "user": "USUARIO",
        },
        "en": {
            "situation": "use the declared case inputs",
            "standards": "work from sources, boundaries and human review",
            "criteria": "reviewable output, explicit boundaries and next action",
            "system": "SYSTEM",
            "user": "USER",
        },
        "pt": {
            "situation": "use os inputs declarados do caso",
            "standards": "trabalhe com fontes, limites e revisão humana",
            "criteria": "saída revisável, limites explícitos e próxima ação",
            "system": "SISTEMA",
            "user": "USUÁRIO",
        },
    }[locale]
    n3 = (
        f"{situation}: {level_copy['situation']}.\n"
        f"{purpose}: {output}.\n"
        f"{standards}: {level_copy['standards']}.\n"
        f"{criteria}: {level_copy['criteria']}."
    )
    return [
        {"level": 1, "body": template.split(f'\n\n{LOCAL[locale]["parameters"]}', 1)[0]},
        {"level": 2, "body": template},
        {"level": 3, "body": n3},
        {"level": 4, "body": f"{level_copy['system']}: {role}\n{level_copy['user']}:\n{n3}"},
    ]


def _module_evidence(prompts: Sequence[Mapping[str, Any]]) -> list[str]:
    evidence: list[str] = []
    for prompt in prompts:
        for value in _sequence(prompt.get("evidenceIds"), "prompt.evidenceIds"):
            text = _text(value, "prompt.evidenceIds[]")
            if text not in evidence:
                evidence.append(text)
    if not evidence:
        raise PromptParityError("prompt evidence: no module evidence ids available")
    return evidence[:5]


def _depth_refs(items: Sequence[Mapping[str, Any]], key: str) -> list[str]:
    refs: list[str] = []
    for item in items:
        for value in _sequence(item.get(key), f"depth.{key}"):
            text = _text(value, f"depth.{key}[]")
            if text not in refs:
                refs.append(text)
    if not refs:
        raise PromptParityError(f"depth: no {key} available")
    return refs


def _enrich_depth(item: dict[str, Any], module: str, locale: str, audience: str) -> None:
    fill = MODULE[module]["fill"][locale]
    audience_copy = LOCAL[locale]["audience"][audience]
    workflow = _unique(_sequence(item.get("workflow"), "depth.workflow"))
    for candidate in (LOCAL[locale]["review_step"], LOCAL[locale]["finish_step"]):
        if len(workflow) < 5:
            workflow.append(candidate)
    item["workflow"] = workflow[:6]

    frameworks = _unique(_sequence(item.get("frameworks"), "depth.frameworks"))
    framework_fill = (fill["framework"], "BLUF · idea principal primero", "Definition of Done · cierre observable")
    for candidate in framework_fill:
        if len(frameworks) < 3 and candidate.casefold() not in {value.casefold() for value in frameworks}:
            frameworks.append(candidate)
    item["frameworks"] = frameworks[:3]

    guardrails = _unique(_sequence(item.get("guardrails"), "depth.guardrails"))
    for candidate in (fill["guardrail"], audience_copy["guardrail"]):
        if candidate.casefold() not in {value.casefold() for value in guardrails}:
            guardrails.append(candidate)
    item["guardrails"] = guardrails

    acceptance = _unique(_sequence(item.get("acceptance_criteria"), "depth.acceptance_criteria"))
    for candidate in (fill["criterion"], audience_copy["criterion"]):
        if candidate.casefold() not in {value.casefold() for value in acceptance}:
            acceptance.append(candidate)
    item["acceptance_criteria"] = acceptance

    edges = _unique(_sequence(item.get("edge_cases"), "depth.edge_cases"))
    for candidate in fill["edges"]:
        if len(edges) < 3 and candidate.casefold() not in {value.casefold() for value in edges}:
            edges.append(candidate)
    item["edge_cases"] = edges[:3]
    item["limits"] = _unique(_sequence(item.get("limits"), "depth.limits"))


def _new_direct_base(
    spec: Mapping[str, Any], module: str, locale: str, audience: str, evidence_ids: Sequence[str]
) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt_id = _text(spec.get("id"), "added.id")
    output = _text(spec.get("output"), f"{prompt_id}.output")
    theme = MODULE[module]["themes"][locale]
    base_input = {
        "es": ("CASO", "caso y evidencia que recibes", "revisión semanal documentada", _text(spec.get("demo"), f"{prompt_id}.demo")),
        "en": ("CASE", "case and evidence you receive", "documented weekly review", _text(spec.get("demo"), f"{prompt_id}.demo")),
        "pt": ("CASO", "caso e evidência que você recebe", "revisão semanal documentada", _text(spec.get("demo"), f"{prompt_id}.demo")),
    }[locale]
    seed = {"id": prompt_id, "syntax": {"inputs": [_input(*base_input)], "parameters": {}}}
    inputs = _normalize_imported_inputs(seed, module, locale, audience)
    template, demo = _prompt_texts(locale, inputs, output, theme)
    role = LOCAL[locale]["system"]
    prompt = {
        "id": prompt_id,
        "kind": "direct",
        "family_id": _family(prompt_id),
        "title": _text(spec.get("title"), f"{prompt_id}.title"),
        "receive": "pending",
        "consumeIds": [],
        "produces": _artifact(prompt_id, output),
        "surface": _text(spec.get("surface"), f"{prompt_id}.surface"),
        "syntax": {
            "inputs": inputs,
            "parameters": _parameters(seed),
            "optionalClauses": [{"text": LOCAL[locale]["optional"], "removable": True}],
        },
        "template": template,
        "demo": demo,
        "levels": _levels(locale, template, demo, output, role),
        "evidenceIds": list(evidence_ids),
    }
    depth = {
        "id": prompt_id,
        "kind": "direct",
        "family_id": _family(prompt_id),
        "purpose": _text(spec.get("purpose"), f"{prompt_id}.purpose"),
        "when": _text(spec.get("when"), f"{prompt_id}.when"),
        "workflow": list(spec["workflow"]),
        "frameworks": list(spec["frameworks"]),
        "guardrails": list(spec["guardrails"]),
        "acceptance_criteria": list(spec["acceptance"]),
        "edge_cases": list(spec["edges"]),
        "tradeoff": _text(spec.get("tradeoff"), f"{prompt_id}.tradeoff"),
        "limits": list(spec["limits"]),
        "next": "module-next",
        "concept_ids": [],
        "authority_refs": [],
        "demo_artifact": _text(spec.get("demo"), f"{prompt_id}.demo"),
    }
    return prompt, depth


def _new_meta(
    index: int,
    module: str,
    locale: str,
    audience: str,
    evidence_ids: Sequence[str],
    concept_ids: Sequence[str],
    authority_refs: Sequence[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt_id = f"prompt-m{index}"
    title, purpose, output, framework_a, framework_b, framework_c = META[locale][index - 1]
    theme = MODULE[module]["themes"][locale]
    base_input = {
        "es": ("OBJETIVO_DEL_INSTRUMENTO", "comportamiento que debe producir el instrumento", "guiar una revisión semanal", f"guiar {theme} con evidencia y una pregunta por turno"),
        "en": ("INSTRUMENT_OBJECTIVE", "behavior the instrument must produce", "guide a weekly review", f"guide {theme} with evidence and one question at a time"),
        "pt": ("OBJETIVO_DO_INSTRUMENTO", "comportamento que o instrumento deve produzir", "guiar uma revisão semanal", f"guiar {theme} com evidência e uma pergunta por vez"),
    }[locale]
    seed = {"id": prompt_id, "syntax": {"inputs": [_input(*base_input)], "parameters": {}}}
    inputs = _normalize_imported_inputs(seed, module, locale, audience)
    template, demo = _prompt_texts(locale, inputs, output, theme)
    role = LOCAL[locale]["system"]
    prompt = {
        "id": prompt_id,
        "kind": "meta",
        "family_id": "meta",
        "title": title,
        "receive": "pending",
        "consumeIds": [],
        "produces": _artifact(prompt_id, output),
        "surface": "chat",
        "syntax": {
            "inputs": inputs,
            "parameters": _parameters(seed),
            "optionalClauses": [{"text": LOCAL[locale]["optional"], "removable": True}],
        },
        "template": template,
        "demo": demo,
        "levels": _levels(locale, template, demo, output, role),
        "evidenceIds": list(evidence_ids),
    }
    audience_copy = LOCAL[locale]["audience"][audience]
    workflow = {
        "es": ("Declara propósito, audiencia y resultado observable.", "Define reglas invariantes y datos variables.", "Construye el flujo de interacción y sus gates.", "Añade rúbrica, límites y casos adversariales.", "Prueba el instrumento con la Demo y registra ajustes."),
        "en": ("State purpose, audience and observable outcome.", "Separate invariant rules from variable case data.", "Build the interaction flow and its gates.", "Add rubric, boundaries and adversarial cases.", "Test the instrument with the Demo and record adjustments."),
        "pt": ("Declare propósito, público e resultado observável.", "Separe regras invariantes de dados variáveis do caso.", "Construa o fluxo de interação e seus gates.", "Adicione rubrica, limites e casos adversariais.", "Teste o instrumento com a Demo e registre ajustes."),
    }[locale]
    guards = {
        "es": ("Diseña el instrumento; no simules haberlo ejecutado.", "No permitas respuestas fuera de la evidencia declarada.", audience_copy["guardrail"]),
        "en": ("Design the instrument; do not pretend it has been run.", "Do not allow answers beyond the declared evidence.", audience_copy["guardrail"]),
        "pt": ("Desenhe o instrumento; não finja que ele foi executado.", "Não permita respostas além da evidência declarada.", audience_copy["guardrail"]),
    }[locale]
    acceptance = {
        "es": ("El instrumento tiene mensaje inicial, flujo y cierre.", "La rúbrica usa criterios observables.", audience_copy["criterion"]),
        "en": ("The instrument has an opening message, flow and close.", "The rubric uses observable criteria.", audience_copy["criterion"]),
        "pt": ("O instrumento tem mensagem inicial, fluxo e fechamento.", "A rubrica usa critérios observáveis.", audience_copy["criterion"]),
    }[locale]
    edges = {
        "es": ("Falta evidencia: el instrumento declara coverage_gap.", "La solicitud excede el rol: se detiene y explica el límite.", "Respuesta ambigua: formula una pregunta concreta antes de avanzar."),
        "en": ("Evidence is missing: the instrument declares coverage_gap.", "The request exceeds its role: it stops and states the boundary.", "Ambiguous answer: it asks one concrete question before proceeding."),
        "pt": ("Falta evidência: o instrumento declara coverage_gap.", "A solicitação excede o papel: ele para e informa o limite.", "Resposta ambígua: faz uma pergunta concreta antes de avançar."),
    }[locale]
    depth = {
        "id": prompt_id,
        "kind": "meta",
        "family_id": "meta",
        "purpose": purpose,
        "when": {
            "es": f"Cuando necesitas reutilizar {theme} sin copiar una sesión anterior.",
            "en": f"When you need to reuse {theme} without copying a previous session.",
            "pt": f"Quando você precisa reutilizar {theme} sem copiar uma sessão anterior.",
        }[locale],
        "workflow": list(workflow),
        "frameworks": [framework_a, framework_b, framework_c],
        "guardrails": list(guards),
        "acceptance_criteria": list(acceptance),
        "edge_cases": list(edges),
        "tradeoff": {
            "es": "Más estructura aumenta repetibilidad, pero exige mantener el instrumento cuando cambian las fuentes.",
            "en": "More structure improves repeatability but requires maintenance when sources change.",
            "pt": "Mais estrutura aumenta a repetibilidade, mas exige manutenção quando as fontes mudam.",
        }[locale],
        "limits": [{"es":"Configura un instrumento; no produce evidencia por sí solo.","en":"It configures an instrument; it does not produce evidence by itself.","pt":"Configura um instrumento; não produz evidência por si só."}[locale]],
        "next": "module-next",
        "concept_ids": list(concept_ids[:2]),
        "authority_refs": list(authority_refs[:3]),
        "demo_artifact": {
            "es": f"Caso sintético resuelto para {audience_copy['scope']}: {audience_copy['owner']}; objetivo: {theme}; fuentes y límites declarados.",
            "en": f"Resolved synthetic case for {audience_copy['scope']}: {audience_copy['owner']}; objective: {theme}; declared sources and boundaries.",
            "pt": f"Caso sintético resolvido para {audience_copy['scope']}: {audience_copy['owner']}; objetivo: {theme}; fontes e limites declarados.",
        }[locale],
    }
    return prompt, depth


def _rewire(prompts: list[dict[str, Any]], depth_items: list[dict[str, Any]]) -> None:
    prompt_by_id = {prompt["id"]: prompt for prompt in prompts}
    depth_by_id = {item["id"]: item for item in depth_items}
    for index, prompt_id in enumerate(DIRECT_IDS, 1):
        prompt = prompt_by_id[prompt_id]
        if index == 1:
            # Preserve the governed entry artifact from the imported module.
            # M2 and M4 start from a workbook output; M3 starts from a declared
            # workflow context.  Replacing that edge with the first input name
            # would sever the cross-resource route and require an invented
            # artifact label in the renderer.
            prompt["receive"] = _text(prompt.get("receive"), f"{prompt_id}.receive")
            prompt["consumeIds"] = _sequence(prompt.get("consumeIds"), f"{prompt_id}.consumeIds")
        else:
            previous = f"prompt-{index - 1:02d}-output"
            prompt["receive"] = previous
            prompt["consumeIds"] = [previous]
        depth_by_id[prompt_id]["next"] = f"prompt-{index + 1:02d}" if index < 10 else "module-next"

    branch_points = ("prompt-05", "prompt-07", "prompt-09", "prompt-10")
    for prompt_id, branch in zip(META_IDS, branch_points):
        reference = f"{branch}-output"
        prompt_by_id[prompt_id]["receive"] = reference
        prompt_by_id[prompt_id]["consumeIds"] = [reference]
        depth_by_id[prompt_id]["next"] = "module-next"


def _validate_composed(module: str, variant: Mapping[str, Any], depth_variant: Mapping[str, Any]) -> None:
    locale = _text(variant.get("locale"), "variant.locale")
    audience = _text(variant.get("audience"), "variant.audience")
    module_payload = _mapping(variant.get("module"), "variant.module")
    library = _mapping(module_payload.get("promptLibrary"), "variant.module.promptLibrary")
    prompts = _sequence(library.get("prompts"), "variant.module.promptLibrary.prompts")
    depth_root = _mapping(depth_variant.get("prompts"), "depth_variant.prompts")
    depth_items = _sequence(depth_root.get("items"), "depth_variant.prompts.items")
    if [item.get("id") for item in prompts] != list(PROMPT_IDS):
        raise PromptParityError("composed prompts: expected ordered direct 01..10 and meta M1..M4")
    if [item.get("id") for item in depth_items] != list(PROMPT_IDS):
        raise PromptParityError("composed depth prompts: id/order mismatch")
    surfaces = Counter("source_search" if item.get("surface") in ("sources", "source_search") else item.get("surface") for item in prompts)
    if surfaces != Counter({"chat": 12, "source_search": 2}):
        raise PromptParityError(f"composed surfaces: expected 12 chat + 2 source_search, got {dict(surfaces)}")

    prompt_by_id = {item["id"]: item for item in prompts}
    depth_by_id = {item["id"]: item for item in depth_items}
    for prompt_id in PROMPT_IDS:
        prompt = _mapping(prompt_by_id[prompt_id], f"prompt.{prompt_id}")
        depth = _mapping(depth_by_id[prompt_id], f"depth.{prompt_id}")
        kind = "meta" if prompt_id in META_IDS else "direct"
        if prompt.get("kind") != kind or depth.get("kind") != kind:
            raise PromptParityError(f"{prompt_id}: kind mismatch")
        family = _family(prompt_id)
        if prompt.get("family_id") != family or depth.get("family_id") != family:
            raise PromptParityError(f"{prompt_id}: family mismatch")
        syntax = _mapping(prompt.get("syntax"), f"{prompt_id}.syntax")
        inputs = _sequence(syntax.get("inputs"), f"{prompt_id}.syntax.inputs")
        if not 2 <= len(inputs) <= 6:
            raise PromptParityError(f"{prompt_id}: expected 2..6 inputs")
        for index, raw_input in enumerate(inputs):
            item = _mapping(raw_input, f"{prompt_id}.syntax.inputs[{index}]")
            for key in ("name", "description", "example", "demoValue"):
                _text(item.get(key), f"{prompt_id}.syntax.inputs[{index}].{key}")
            if item.get("required") is not True:
                raise PromptParityError(f"{prompt_id}.syntax.inputs[{index}]: required must be true")
        parameters = syntax.get("parameters")
        count = len(parameters) if isinstance(parameters, Mapping) else len(_sequence(parameters, f"{prompt_id}.syntax.parameters"))
        if not 4 <= count <= 6:
            raise PromptParityError(f"{prompt_id}: expected 4..6 parameters")
        levels = _sequence(prompt.get("levels"), f"{prompt_id}.levels")
        if len(levels) != 4 or [item.get("level") for item in levels] != [1, 2, 3, 4]:
            raise PromptParityError(f"{prompt_id}: expected levels 1..4")
        _text(prompt.get("template"), f"{prompt_id}.template")
        demo = _text(prompt.get("demo"), f"{prompt_id}.demo")
        if "<" in demo or ">" in demo or "{{" in demo:
            raise PromptParityError(f"{prompt_id}: unresolved Demo input")
        artifact = _mapping(prompt.get("produces"), f"{prompt_id}.produces")
        if artifact.get("artifactId") != f"{prompt_id}-output":
            raise PromptParityError(f"{prompt_id}: unstable produced artifact id")
        _text(artifact.get("label"), f"{prompt_id}.produces.label")
        if len(_sequence(depth.get("workflow"), f"{prompt_id}.workflow")) not in (5, 6):
            raise PromptParityError(f"{prompt_id}: expected 5..6 workflow steps")
        if len(_sequence(depth.get("frameworks"), f"{prompt_id}.frameworks")) != 3:
            raise PromptParityError(f"{prompt_id}: expected exactly 3 frameworks")
        if len(_sequence(depth.get("guardrails"), f"{prompt_id}.guardrails")) < 3:
            raise PromptParityError(f"{prompt_id}: expected at least 3 guardrails")
        if len(_sequence(depth.get("acceptance_criteria"), f"{prompt_id}.acceptance")) < 3:
            raise PromptParityError(f"{prompt_id}: expected at least 3 acceptance criteria")
        if len(_sequence(depth.get("edge_cases"), f"{prompt_id}.edge_cases")) != 3:
            raise PromptParityError(f"{prompt_id}: expected exactly 3 edge cases")
        if not _sequence(depth.get("limits"), f"{prompt_id}.limits"):
            raise PromptParityError(f"{prompt_id}: at least one limit required")
        _text(depth.get("demo_artifact"), f"{prompt_id}.demo_artifact")

    for index, prompt_id in enumerate(DIRECT_IDS, 1):
        prompt = prompt_by_id[prompt_id]
        expected_next = f"prompt-{index + 1:02d}" if index < 10 else "module-next"
        if depth_by_id[prompt_id].get("next") != expected_next:
            raise PromptParityError(f"{prompt_id}: direct next mismatch")
        if index == 1:
            consumes = _sequence(prompt.get("consumeIds"), "prompt-01.consumeIds")
            if any(str(reference).removesuffix("-output") in prompt_by_id for reference in consumes):
                raise PromptParityError("prompt-01: route cannot consume an internal prompt output")
        else:
            reference = f"prompt-{index - 1:02d}-output"
            if prompt.get("receive") != reference or prompt.get("consumeIds") != [reference]:
                raise PromptParityError(f"{prompt_id}: prior-output binding mismatch")
            if prompt_by_id[f"prompt-{index - 1:02d}"]["produces"]["artifactId"] != reference:
                raise PromptParityError(f"{prompt_id}: consumes an artifact the previous step does not produce")
    for prompt_id in META_IDS:
        if depth_by_id[prompt_id].get("next") != "module-next":
            raise PromptParityError(f"{prompt_id}: metaprompt must not enter the direct chain")
        consumes = _sequence(prompt_by_id[prompt_id].get("consumeIds"), f"{prompt_id}.consumeIds")
        if len(consumes) != 1 or not str(consumes[0]).startswith("prompt-"):
            raise PromptParityError(f"{prompt_id}: independent branch input missing")
        producer_id = str(consumes[0]).removesuffix("-output")
        if producer_id not in prompt_by_id or prompt_by_id[producer_id]["produces"]["artifactId"] != consumes[0]:
            raise PromptParityError(f"{prompt_id}: metaprompt branch artifact has no producer")

    marker = LOCAL[locale]["audience"][audience]["criterion"]
    if any(marker not in depth_by_id[prompt_id]["acceptance_criteria"] for prompt_id in PROMPT_IDS):
        raise PromptParityError(f"{module}:{locale}:{audience}: audience-specific acceptance missing")


def compose_prompt_parity(
    module_id: str,
    variant: Mapping[str, Any],
    depth_variant: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return prompt-parity copies for one exact locale/audience variant.

    The function accepts only the three governed modules and their current
    imported cardinalities.  This prevents applying the compatibility layer to
    an unknown or already-migrated payload by accident.
    """

    module = _module_key(module_id)
    original_variant = deepcopy(variant)
    original_depth = deepcopy(depth_variant)
    variant_copy = deepcopy(variant)
    depth_copy = deepcopy(depth_variant)

    locale = _text(variant_copy.get("locale"), "variant.locale")
    audience = _text(variant_copy.get("audience"), "variant.audience")
    if locale not in LOCALES or audience not in AUDIENCES:
        raise PromptParityError(f"variant: unsupported locale/audience {locale}:{audience}")
    if depth_copy.get("locale") != locale or depth_copy.get("audience") != audience:
        raise PromptParityError("depth_variant: locale/audience mismatch")

    module_payload = _mapping(variant_copy.get("module"), "variant.module")
    library = _mapping(module_payload.get("promptLibrary"), "variant.module.promptLibrary")
    imported_prompts = _sequence(library.get("prompts"), "variant.module.promptLibrary.prompts")
    depth_root = _mapping(depth_copy.get("prompts"), "depth_variant.prompts")
    imported_depth = _sequence(depth_root.get("items"), "depth_variant.prompts.items")
    expected = EXPECTED_IMPORTED[module]
    expected_ids = [f"prompt-{index:02d}" for index in range(1, expected + 1)]
    if [item.get("id") for item in imported_prompts] != expected_ids:
        raise PromptParityError(f"{module}: imported prompt set drifted")
    if [item.get("id") for item in imported_depth] != expected_ids:
        raise PromptParityError(f"{module}: imported depth prompt set drifted")

    prompts = [deepcopy(_mapping(item, "prompt")) for item in imported_prompts]
    depth_items = [deepcopy(_mapping(item, "depth prompt")) for item in imported_depth]
    depth_by_id = {item["id"]: item for item in depth_items}
    for prompt in prompts:
        prompt_id = _text(prompt.get("id"), "prompt.id")
        prompt["kind"] = "direct"
        prompt["family_id"] = _family(prompt_id)
        prompt["syntax"] = {
            "inputs": _normalize_imported_inputs(prompt, module, locale, audience),
            "parameters": _parameters(prompt),
            "optionalClauses": [{"text": LOCAL[locale]["optional"], "removable": True}],
        }
        # Direct keys make Template/Demo handling identical for legacy payloads.
        output = prompt["produces"]["label"] if isinstance(prompt.get("produces"), Mapping) else _text(prompt.get("produces"), f"{prompt_id}.produces")
        prompt["produces"] = _artifact(prompt_id, prompt.get("produces"))
        template, demo = _prompt_texts(locale, prompt["syntax"]["inputs"], output, MODULE[module]["themes"][locale])
        prompt["template"] = template
        prompt["demo"] = demo
        prompt["levels"] = _levels(locale, template, demo, output, LOCAL[locale]["system"])
        depth = depth_by_id[prompt_id]
        depth["kind"] = "direct"
        depth["family_id"] = _family(prompt_id)
        if "demo_artifact" not in depth:
            depth["demo_artifact"] = "; ".join(item["demoValue"] for item in prompt["syntax"]["inputs"])
        _enrich_depth(depth, module, locale, audience)

    evidence_ids = _module_evidence(prompts)
    concept_ids = _depth_refs(depth_items, "concept_ids")
    authority_refs = _depth_refs(depth_items, "authority_refs")
    for spec in _translated_added_direct(module, locale) if module in ("m02", "m04") else ():
        prompt, depth = _new_direct_base(spec, module, locale, audience, evidence_ids)
        depth["concept_ids"] = list(concept_ids[:2])
        depth["authority_refs"] = list(authority_refs[:3])
        _enrich_depth(depth, module, locale, audience)
        prompts.append(prompt)
        depth_items.append(depth)

    for index in range(1, 5):
        prompt, depth = _new_meta(index, module, locale, audience, evidence_ids, concept_ids, authority_refs)
        _enrich_depth(depth, module, locale, audience)
        prompts.append(prompt)
        depth_items.append(depth)

    order = {prompt_id: index for index, prompt_id in enumerate(PROMPT_IDS)}
    prompts.sort(key=lambda item: order.get(item["id"], 999))
    depth_items.sort(key=lambda item: order.get(item["id"], 999))
    if module == "m03":
        # Source contrast is the second source-search surface for this module.
        next(item for item in prompts if item["id"] == "prompt-07")["surface"] = "sources"
    _rewire(prompts, depth_items)
    library["prompts"] = prompts
    module_payload["promptLibrary"] = library
    variant_copy["module"] = module_payload
    depth_root["items"] = depth_items
    depth_copy["prompts"] = depth_root

    _validate_composed(module, variant_copy, depth_copy)
    if variant != original_variant or depth_variant != original_depth:
        raise PromptParityError("source mutation detected")
    return variant_copy, depth_copy


__all__ = ("PromptParityError", "compose_prompt_parity")
