#!/usr/bin/env python3
"""One-way, deterministic migration to prompt-intent-contract-v2.

The script is intentionally data-heavy: it records the canonical input naming
policy, audience-aware demo fixture, execution parameters and journey graph in
one reviewable place. It never changes editorial claims or raises release state.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "src" / "prompt-contracts"
LANGS = ("es", "en", "pt")
AUDIENCES = ("persona", "empresa")
SELF_HASH_MODEL = "sha256(sorted-json-without-self_sha256)"

# Governed, intentionally small practice vocabulary. A prompt may name at most
# three items: enough to make the operating method explicit without turning the
# instruction into a catalogue of fashionable acronyms.
PRACTICES = {
    "mece": {"es": "MECE · sin solapamientos ni vacíos", "en": "MECE · no overlaps or gaps", "pt": "MECE · sem sobreposições nem lacunas"},
    "source_hierarchy": {"es": "Jerarquía de fuentes · fuentes primarias primero", "en": "Source hierarchy · primary sources first", "pt": "Hierarquia de fontes · fontes primárias primeiro"},
    "definition_of_done": {"es": "Definition of Done · cierre observable", "en": "Definition of Done · observable completion", "pt": "Definition of Done · conclusão observável"},
    "evidence_matrix": {"es": "Matriz de evidencia · afirmación, fuente y decisión", "en": "Evidence matrix · claim, source and decision", "pt": "Matriz de evidências · afirmação, fonte e decisão"},
    "triangulation": {"es": "Triangulación · orígenes independientes", "en": "Triangulation · independent origins", "pt": "Triangulação · origens independentes"},
    "gap_analysis": {"es": "Análisis de brechas · prioriza lo que bloquea", "en": "Gap analysis · prioritize what blocks progress", "pt": "Análise de lacunas · priorize o que bloqueia"},
    "research_brief": {"es": "Research brief · pregunta, alcance y criterio", "en": "Research brief · question, scope and criterion", "pt": "Research brief · pergunta, escopo e critério"},
    "acceptance_criteria": {"es": "Criterios de aceptación · prueba observable", "en": "Acceptance criteria · observable test", "pt": "Critérios de aceitação · teste observável"},
    "red_team": {"es": "Red teaming · busca fallos antes de decidir", "en": "Red teaming · find flaws before deciding", "pt": "Red teaming · encontre falhas antes de decidir"},
    "claim_evidence_reasoning": {"es": "Claim–Evidence–Reasoning · conecta afirmación y soporte", "en": "Claim–Evidence–Reasoning · connect claim and support", "pt": "Claim–Evidence–Reasoning · conecte afirmação e suporte"},
    "jtbd": {"es": "Jobs to Be Done · problema, usuario y resultado", "en": "Jobs to Be Done · problem, user and outcome", "pt": "Jobs to Be Done · problema, usuário e resultado"},
    "impact_effort": {"es": "Impacto–esfuerzo · prioriza lo viable", "en": "Impact–effort · prioritize what is viable", "pt": "Impacto–esforço · priorize o que é viável"},
    "socratic": {"es": "Método socrático · una pregunta por turno", "en": "Socratic method · one question per turn", "pt": "Método socrático · uma pergunta por turno"},
    "feynman": {"es": "Técnica Feynman · explica con palabras simples", "en": "Feynman technique · explain in plain language", "pt": "Técnica Feynman · explique com linguagem simples"},
    "deliberate_practice": {"es": "Práctica deliberada · reto, feedback y reintento", "en": "Deliberate practice · challenge, feedback and retry", "pt": "Prática deliberada · desafio, feedback e nova tentativa"},
    "feedback_loop": {"es": "Feedback loop · observa, corrige y repite", "en": "Feedback loop · observe, correct and repeat", "pt": "Feedback loop · observe, corrija e repita"},
    "bloom": {"es": "Taxonomía de Bloom · de comprender a aplicar", "en": "Bloom's taxonomy · from understanding to application", "pt": "Taxonomia de Bloom · de compreender a aplicar"},
    "analytic_rubric": {"es": "Rúbrica analítica · criterios y niveles observables", "en": "Analytic rubric · observable criteria and levels", "pt": "Rubrica analítica · critérios e níveis observáveis"},
    "bluf": {"es": "BLUF · conclusión primero", "en": "BLUF · conclusion first", "pt": "BLUF · conclusão primeiro"},
    "pyramid": {"es": "Principio de la Pirámide · idea, razones y evidencia", "en": "Pyramid Principle · idea, reasons and evidence", "pt": "Princípio da Pirâmide · ideia, razões e evidência"},
    "premortem": {"es": "Pre-mortem · anticipa objeciones y fallos", "en": "Pre-mortem · anticipate objections and failure", "pt": "Pre-mortem · antecipe objeções e falhas"},
    "role_charter": {"es": "Role charter · rol, límites y escalamiento", "en": "Role charter · role, boundaries and escalation", "pt": "Role charter · papel, limites e escalonamento"},
    "brain_dump": {"es": "Brain dump · captura antes de ordenar", "en": "Brain dump · capture before organizing", "pt": "Brain dump · capture antes de organizar"},
    "affinity_mapping": {"es": "Mapeo de afinidad · agrupa patrones", "en": "Affinity mapping · group patterns", "pt": "Mapeamento de afinidade · agrupe padrões"},
    "five_w_one_h": {"es": "5W1H · quién, qué, cuándo, dónde, por qué y cómo", "en": "5W1H · who, what, when, where, why and how", "pt": "5W1H · quem, o quê, quando, onde, por quê e como"},
    "scqa": {"es": "SCQA · situación, tensión, pregunta y respuesta", "en": "SCQA · situation, complication, question and answer", "pt": "SCQA · situação, complicação, pergunta e resposta"},
    "backward_design": {"es": "Diseño inverso · resultado, evidencia y pasos", "en": "Backward design · outcome, evidence and steps", "pt": "Design reverso · resultado, evidência e passos"},
    "go_no_go": {"es": "Gate Go/No-Go · decide con criterio explícito", "en": "Go/No-Go gate · decide with an explicit criterion", "pt": "Gate Go/No-Go · decida com critério explícito"},
    "active_recall": {"es": "Recuperación activa · responde antes de consultar", "en": "Active recall · answer before consulting", "pt": "Recuperação ativa · responda antes de consultar"},
    "raci": {"es": "RACI · un responsable por decisión", "en": "RACI · one accountable owner per decision", "pt": "RACI · um responsável por decisão"},
    "smart": {"es": "SMART · resultado específico y medible", "en": "SMART · specific and measurable outcome", "pt": "SMART · resultado específico e mensurável"},
}

PRACTICES_BY_INTENT = {
    "01": ("mece", "source_hierarchy", "definition_of_done"),
    "05": ("evidence_matrix", "gap_analysis", "go_no_go"),
    "03": ("research_brief", "acceptance_criteria", "source_hierarchy"),
    "04": ("triangulation", "red_team", "claim_evidence_reasoning"),
    "07": ("jtbd", "red_team", "definition_of_done"),
    "02": ("socratic", "feynman", "source_hierarchy"),
    "06": ("deliberate_practice", "feedback_loop", "active_recall"),
    "08": ("bloom", "analytic_rubric", "acceptance_criteria"),
    "10": ("bluf", "pyramid", "definition_of_done"),
    "09": ("red_team", "premortem", "analytic_rubric"),
    "M1": ("role_charter", "socratic", "red_team"),
    "M2": ("analytic_rubric", "bloom", "definition_of_done"),
    "M3": ("red_team", "premortem", "analytic_rubric"),
    "M4": ("bluf", "pyramid", "go_no_go"),
    "B1": ("brain_dump", "affinity_mapping", "definition_of_done"),
    "B2": ("five_w_one_h", "scqa", "acceptance_criteria"),
    "B3": ("backward_design", "mece", "definition_of_done"),
    "W01": ("source_hierarchy", "research_brief", "mece"),
    "W02": ("evidence_matrix", "gap_analysis", "go_no_go"),
    "W03": ("research_brief", "acceptance_criteria", "source_hierarchy"),
    "W04": ("go_no_go", "definition_of_done", "gap_analysis"),
    "W05": ("role_charter", "socratic", "definition_of_done"),
    "W06": ("feynman", "bluf", "claim_evidence_reasoning"),
    "W07": ("jtbd", "impact_effort", "smart"),
    "W08": ("bloom", "analytic_rubric", "active_recall"),
    "W09": ("red_team", "premortem", "analytic_rubric"),
    "W10": ("raci", "smart", "definition_of_done"),
}


def canonical_self(value: dict) -> str:
    payload = {key: item for key, item in value.items() if key != "self_sha256"}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def norm(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(char)
    )


# One semantic key across languages. Aliases are the literal legacy markers.
INPUTS = {
    "topic": {
        "aliases": {"es": ["TEMA"], "en": ["TOPIC"], "pt": ["TEMA"]},
        "label": {"es": "TEMA", "en": "TOPIC", "pt": "TEMA"},
        "help": {"es": "asunto concreto", "en": "specific subject", "pt": "assunto concreto"},
        "example": {"es": "verificar respuestas de IA", "en": "verify AI answers", "pt": "verificar respostas de IA"},
    },
    "audience": {
        "aliases": {"es": ["AUDIENCIA"], "en": ["AUDIENCE"], "pt": ["PÚBLICO"]},
        "label": {"es": "AUDIENCIA", "en": "AUDIENCE", "pt": "PÚBLICO"},
        "help": {"es": "quién usará el resultado", "en": "who will use the result", "pt": "quem usará o resultado"},
        "example": {"es": "profesionales no técnicos", "en": "non-technical professionals", "pt": "profissionais não técnicos"},
    },
    "base": {
        "aliases": {"es": ["BASE"], "en": ["BASE"], "pt": ["BASE"]},
        "label": {"es": "BASE", "en": "BASE", "pt": "BASE"},
        "help": {"es": "fuentes o síntesis disponibles", "en": "available sources or synthesis", "pt": "fontes ou síntese disponíveis"},
        "example": {"es": "tres fuentes y su mapa", "en": "three sources and their map", "pt": "três fontes e seu mapa"},
        "source": "previous_output",
    },
    "sources": {
        "aliases": {"es": ["FUENTES"], "en": ["SOURCES"], "pt": ["FONTES"]},
        "label": {"es": "FUENTES", "en": "SOURCES", "pt": "FONTES"},
        "help": {"es": "material que sí puede citarse", "en": "material that may be cited", "pt": "material que pode ser citado"},
        "example": {"es": "guía, informe y registro", "en": "guide, report and log", "pt": "guia, relatório e registro"},
    },
    "sources_or_notebook": {
        "aliases": {"es": ["FUENTES O NOTEBOOK"], "en": ["SOURCES OR NOTEBOOK"], "pt": ["FONTES OU NOTEBOOK"]},
        "label": {"es": "FUENTES O NOTEBOOK", "en": "SOURCES OR NOTEBOOK", "pt": "FONTES OU NOTEBOOK"},
        "help": {"es": "base que limitará la respuesta", "en": "base that will bound the answer", "pt": "base que limitará a resposta"},
        "example": {"es": "Notebook del piloto", "en": "pilot Notebook", "pt": "Notebook do piloto"},
        "source": "previous_output",
    },
    "context": {
        "aliases": {"es": ["CONTEXTO"], "en": ["CONTEXT"], "pt": ["CONTEXTO"]},
        "label": {"es": "CONTEXTO", "en": "CONTEXT", "pt": "CONTEXTO"},
        "help": {"es": "situación y restricciones relevantes", "en": "relevant situation and constraints", "pt": "situação e restrições relevantes"},
        "example": {"es": "45 minutos al día", "en": "45 minutes a day", "pt": "45 minutos por dia"},
    },
    "purpose": {
        "aliases": {"es": ["PROPÓSITO", "PROPÓSITO DE LA SESIÓN"], "en": ["PURPOSE", "SESSION PURPOSE"], "pt": ["PROPÓSITO", "PROPÓSITO DA SESSÃO"]},
        "label": {"es": "PROPÓSITO", "en": "PURPOSE", "pt": "PROPÓSITO"},
        "help": {"es": "para qué necesitas el resultado", "en": "why you need the result", "pt": "para que precisa do resultado"},
        "example": {"es": "repetir una práctica útil", "en": "repeat a useful practice", "pt": "repetir uma prática útil"},
    },
    "decision": {
        "aliases": {
            "es": ["DECISIÓN BLOQUEADA", "DECISIÓN DEL EQUIPO", "DECISIÓN O ENTREGA", "DECISIÓN O RESULTADO", "DECISIÓN O USO", "DECISIÓN, PROYECTO O RESULTADO"],
            "en": ["DECISION AT STAKE", "TEAM DECISION", "DECISION OR DELIVERY", "DECISION OR OUTCOME", "DECISION OR RESULT", "DECISION OR USE"],
            "pt": ["DECISÃO TRAVADA", "DECISÃO DA EQUIPE", "DECISÃO OU ENTREGA", "DECISÃO OU RESULTADO", "DECISÃO OU USO"],
        },
        "label": {"es": "DECISIÓN", "en": "DECISION", "pt": "DECISÃO"},
        "help": {"es": "elección que debe quedar informada", "en": "choice the work must inform", "pt": "escolha que o trabalho deve informar"},
        "example": {"es": "escalar o ajustar el piloto", "en": "scale or adjust the pilot", "pt": "escalar ou ajustar o piloto"},
    },
    "deliverable": {
        "aliases": {"es": ["ENTREGABLE"], "en": ["DELIVERABLE"], "pt": ["ENTREGÁVEL"]},
        "label": {"es": "ENTREGABLE", "en": "DELIVERABLE", "pt": "ENTREGÁVEL"},
        "help": {"es": "pieza que debe quedar lista", "en": "piece that must be ready", "pt": "peça que deve ficar pronta"},
        "example": {"es": "memo de una página", "en": "one-page memo", "pt": "memo de uma página"},
    },
    "content_type": {
        "aliases": {"es": ["TIPO DE CONTENIDO"], "en": ["CONTENT TYPE"], "pt": ["TIPO DE CONTEÚDO"]},
        "label": {"es": "TIPO DE CONTENIDO", "en": "CONTENT TYPE", "pt": "TIPO DE CONTEÚDO"},
        "help": {"es": "formato final", "en": "final format", "pt": "formato final"},
        "example": {"es": "guía breve", "en": "short guide", "pt": "guia breve"},
    },
    "outcome": {
        "aliases": {"es": ["RESULTADO"], "en": ["OUTCOME", "RESULT"], "pt": ["RESULTADO"]},
        "label": {"es": "RESULTADO", "en": "OUTCOME", "pt": "RESULTADO"},
        "help": {"es": "cambio observable esperado", "en": "observable change expected", "pt": "mudança observável esperada"},
        "example": {"es": "una práctica repetible", "en": "a repeatable practice", "pt": "uma prática repetível"},
    },
    "use": {
        "aliases": {"es": ["USO"], "en": ["USE"], "pt": ["USO"]},
        "label": {"es": "USO", "en": "USE", "pt": "USO"},
        "help": {"es": "situación donde se aplicará", "en": "situation where it will be applied", "pt": "situação em que será aplicado"},
        "example": {"es": "revisión semanal", "en": "weekly review", "pt": "revisão semanal"},
    },
    "user": {
        "aliases": {"es": ["USUARIO"], "en": ["USER"], "pt": ["USUÁRIO"]},
        "label": {"es": "USUARIO", "en": "USER", "pt": "USUÁRIO"},
        "help": {"es": "persona que operará la solución", "en": "person who will operate the solution", "pt": "pessoa que operará a solução"},
        "example": {"es": "líder del piloto", "en": "pilot lead", "pt": "líder do piloto"},
    },
    "team": {
        "aliases": {"es": ["EQUIPO"], "en": ["TEAM"], "pt": ["EQUIPE"]},
        "label": {"es": "EQUIPO", "en": "TEAM", "pt": "EQUIPE"},
        "help": {"es": "grupo que participa", "en": "group taking part", "pt": "grupo participante"},
        "example": {"es": "equipo de operaciones", "en": "operations team", "pt": "equipe de operações"},
    },
    "process": {
        "aliases": {"es": ["PROCESO"], "en": ["PROCESS"], "pt": ["PROCESSO"]},
        "label": {"es": "PROCESO", "en": "PROCESS", "pt": "PROCESSO"},
        "help": {"es": "flujo que cambiará", "en": "workflow that will change", "pt": "fluxo que mudará"},
        "example": {"es": "preparación de decisiones", "en": "decision preparation", "pt": "preparação de decisões"},
    },
    "time_horizon": {
        "aliases": {"es": ["HORIZONTE TEMPORAL"], "en": ["TIME HORIZON"], "pt": ["HORIZONTE TEMPORAL"]},
        "label": {"es": "HORIZONTE", "en": "HORIZON", "pt": "HORIZONTE"},
        "help": {"es": "periodo relevante", "en": "relevant period", "pt": "período relevante"},
        "example": {"es": "próximos 7 días", "en": "next 7 days", "pt": "próximos 7 dias"},
    },
    "region": {
        "aliases": {"es": ["REGIÓN O JURISDICCIÓN"], "en": ["REGION OR JURISDICTION"], "pt": ["REGIÃO OU JURISDIÇÃO"]},
        "label": {"es": "REGIÓN", "en": "REGION", "pt": "REGIÃO"},
        "help": {"es": "lugar o marco aplicable", "en": "applicable place or framework", "pt": "local ou marco aplicável"},
        "example": {"es": "Colombia", "en": "Colombia", "pt": "Colômbia"},
    },
    "cutoff_date": {
        "aliases": {"es": ["FECHA DE CORTE"], "en": ["CUTOFF DATE"], "pt": ["DATA DE CORTE"]},
        "label": {"es": "FECHA DE CORTE", "en": "CUTOFF DATE", "pt": "DATA DE CORTE"},
        "help": {"es": "última fecha aceptada", "en": "latest accepted date", "pt": "última data aceita"},
        "example": {"es": "agosto de 2026", "en": "August 2026", "pt": "agosto de 2026"},
    },
    "gap": {
        "aliases": {"es": ["VACÍO", "VACÍO AUDITADO"], "en": ["GAP", "AUDITED GAP"], "pt": ["LACUNA", "LACUNA AUDITADA"]},
        "label": {"es": "VACÍO", "en": "GAP", "pt": "LACUNA"},
        "help": {"es": "pregunta aún sin soporte", "en": "question still unsupported", "pt": "questão ainda sem suporte"},
        "example": {"es": "qué evidencia demuestra transferencia", "en": "what proves transfer", "pt": "o que demonstra transferência"},
        "source": "previous_output",
    },
    "claim": {
        "aliases": {"es": ["AFIRMACIÓN"], "en": ["CLAIM"], "pt": ["AFIRMAÇÃO"]},
        "label": {"es": "AFIRMACIÓN", "en": "CLAIM", "pt": "AFIRMAÇÃO"},
        "help": {"es": "frase concreta que debe verificarse", "en": "specific statement to verify", "pt": "frase concreta a verificar"},
        "example": {"es": "la práctica reduce retrabajo", "en": "the practice reduces rework", "pt": "a prática reduz retrabalho"},
        "source": "previous_output",
    },
    "acceptance_criterion": {
        "aliases": {"es": ["CRITERIO DE ACEPTACIÓN"], "en": ["ACCEPTANCE CRITERION"], "pt": ["CRITÉRIO DE ACEITAÇÃO"]},
        "label": {"es": "CRITERIO DE ACEPTACIÓN", "en": "ACCEPTANCE CRITERION", "pt": "CRITÉRIO DE ACEITAÇÃO"},
        "help": {"es": "prueba observable de éxito", "en": "observable success test", "pt": "teste observável de sucesso"},
        "example": {"es": "otro puede repetir el flujo", "en": "someone else can repeat the flow", "pt": "outra pessoa repete o fluxo"},
    },
    "constraints": {
        "aliases": {"es": ["RESTRICCIONES"], "en": ["CONSTRAINTS"], "pt": ["RESTRIÇÕES"]},
        "label": {"es": "RESTRICCIONES", "en": "CONSTRAINTS", "pt": "RESTRIÇÕES"},
        "help": {"es": "límites que no deben romperse", "en": "limits that must not be broken", "pt": "limites que não devem ser rompidos"},
        "example": {"es": "sin datos confidenciales", "en": "no confidential data", "pt": "sem dados confidenciais"},
    },
    "materials": {
        "aliases": {"es": ["MATERIALES DISPONIBLES"], "en": ["AVAILABLE MATERIAL"], "pt": ["MATERIAL DISPONÍVEL"]},
        "label": {"es": "MATERIALES", "en": "MATERIAL", "pt": "MATERIAL"},
        "help": {"es": "insumos que sí puedes usar", "en": "inputs you may use", "pt": "insumos que pode usar"},
        "example": {"es": "notas y tres fuentes", "en": "notes and three sources", "pt": "notas e três fontes"},
    },
    "case": {
        "aliases": {"es": ["MI CASO"], "en": ["MY CASE"], "pt": ["MEU CASO"]},
        "label": {"es": "CASO", "en": "CASE", "pt": "CASO"},
        "help": {"es": "situación real a trabajar", "en": "real situation to work on", "pt": "situação real a trabalhar"},
        "example": {"es": "piloto de 7 días", "en": "7-day pilot", "pt": "piloto de 7 dias"},
    },
    "level": {
        "aliases": {"es": ["MI NIVEL", "NIVEL"], "en": ["MY LEVEL", "LEVEL"], "pt": ["MEU NÍVEL", "NÍVEL"]},
        "label": {"es": "NIVEL", "en": "LEVEL", "pt": "NÍVEL"},
        "help": {"es": "punto de partida observable", "en": "observable starting point", "pt": "ponto de partida observável"},
        "example": {"es": "puedo explicar, no transferir", "en": "can explain, not transfer", "pt": "consigo explicar, não transferir"},
    },
    "role": {
        "aliases": {"es": ["ROL"], "en": ["ROLE"], "pt": ["PAPEL"]},
        "label": {"es": "ROL", "en": "ROLE", "pt": "PAPEL"},
        "help": {"es": "función que debe cumplir la IA", "en": "function the AI should perform", "pt": "função que a IA deve cumprir"},
        "example": {"es": "coach basado en fuentes", "en": "source-grounded coach", "pt": "coach baseado em fontes"},
    },
    "scenario": {
        "aliases": {"es": ["ESCENARIO"], "en": ["SCENARIO"], "pt": ["CENÁRIO"]},
        "label": {"es": "ESCENARIO", "en": "SCENARIO", "pt": "CENÁRIO"},
        "help": {"es": "situación que se simulará", "en": "situation to simulate", "pt": "situação a simular"},
        "example": {"es": "revisión del piloto", "en": "pilot review", "pt": "revisão do piloto"},
    },
    "time": {
        "aliases": {"es": ["TIEMPO"], "en": ["TIME"], "pt": ["TEMPO"]},
        "label": {"es": "TIEMPO", "en": "TIME", "pt": "TEMPO"},
        "help": {"es": "duración disponible", "en": "available duration", "pt": "duração disponível"},
        "example": {"es": "15 minutos", "en": "15 minutes", "pt": "15 minutos"},
    },
    "study_plan": {
        "aliases": {"es": ["PLAN DE ESTUDIO CONFIRMADO"], "en": ["CONFIRMED STUDY PLAN"], "pt": ["PLANO DE ESTUDO CONFIRMADO"]},
        "label": {"es": "PLAN DE ESTUDIO", "en": "STUDY PLAN", "pt": "PLANO DE ESTUDO"},
        "help": {"es": "plan confirmado que define propósito, alcance y evidencia", "en": "confirmed plan defining purpose, scope and evidence", "pt": "plano confirmado que define propósito, escopo e evidência"},
        "example": {"es": "diseñar y probar una práctica", "en": "design and test a practice", "pt": "projetar e testar uma prática"},
        "source": "previous_output",
    },
    "brain_dump": {
        "aliases": {"es": ["BRAIN_DUMP"], "en": ["BRAIN_DUMP"], "pt": ["BRAIN_DUMP"]},
        "label": {"es": "NOTAS INICIALES", "en": "STARTING NOTES", "pt": "NOTAS INICIAIS"},
        "help": {"es": "ideas o dictado todavía sin ordenar", "en": "ideas or dictation not yet organized", "pt": "ideias ou ditado ainda sem organizar"},
        "example": {"es": "quiero aprender IA para mejorar…", "en": "I want to learn AI to improve…", "pt": "quero aprender IA para melhorar…"},
    },
}

OPTION_ALIASES = {
    "role_mode": {
        "aliases": {"es": ["PROFESOR | ASESOR | COACH"], "en": ["TEACHER | ADVISOR | COACH"], "pt": ["PROFESSOR | ASSESSOR | COACH"]},
        "label": {"es": "ROL", "en": "ROLE", "pt": "PAPEL"},
        "default": {"es": "coach", "en": "coach", "pt": "coach"},
        "choices": {"es": ["profesor", "asesor", "coach"], "en": ["teacher", "advisor", "coach"], "pt": ["professor", "assessor", "coach"]},
    },
    "conversation_mode": {
        "aliases": {"es": ["ENTREVISTA | QBR | DEFENSA"], "en": ["INTERVIEW | QBR | DEFENSE"], "pt": ["ENTREVISTA | QBR | DEFESA"]},
        "label": {"es": "TIPO DE CONVERSACIÓN", "en": "CONVERSATION TYPE", "pt": "TIPO DE CONVERSA"},
        "default": {"es": "defensa", "en": "defense", "pt": "defesa"},
        "choices": {"es": ["entrevista", "QBR", "defensa"], "en": ["interview", "QBR", "defense"], "pt": ["entrevista", "QBR", "defesa"]},
    },
}

SETTING_COPY = {
    "es": {
        "length": ("LONGITUD", "concisa", ["concisa", "media"]),
        "structure": ("ESTRUCTURA", "2 párrafos + bullets clave", ["2 párrafos + bullets clave", "tabla breve"]),
        "tone_persona": ("TONO", "claro y personal", ["claro y personal", "didáctico"]),
        "tone_empresa": ("TONO", "ejecutivo y operativo", ["ejecutivo y operativo", "facilitador"]),
        "depth": ("PROFUNDIDAD", "práctica", ["práctica", "profunda"]),
        "aesthetic": ("ESTÉTICA", "minimalista", ["minimalista", "editorial"]),
        "opening": ("APERTURA", "diagrama antes del detalle", ["diagrama antes del detalle", "idea clave primero"]),
        "cleaning": ("NIVEL DE LIMPIEZA", "conservar vocabulario", ["conservar vocabulario", "síntesis estricta"]),
    },
    "en": {
        "length": ("LENGTH", "concise", ["concise", "medium"]),
        "structure": ("STRUCTURE", "2 paragraphs + key bullets", ["2 paragraphs + key bullets", "short table"]),
        "tone_persona": ("TONE", "clear and personal", ["clear and personal", "instructional"]),
        "tone_empresa": ("TONE", "executive and operational", ["executive and operational", "facilitative"]),
        "depth": ("DEPTH", "practical", ["practical", "deep"]),
        "aesthetic": ("AESTHETIC", "minimal", ["minimal", "editorial"]),
        "opening": ("OPENING", "diagram before detail", ["diagram before detail", "bottom line first"]),
        "cleaning": ("CLEANING LEVEL", "preserve vocabulary", ["preserve vocabulary", "strict synthesis"]),
    },
    "pt": {
        "length": ("EXTENSÃO", "concisa", ["concisa", "média"]),
        "structure": ("ESTRUTURA", "2 parágrafos + bullets-chave", ["2 parágrafos + bullets-chave", "tabela breve"]),
        "tone_persona": ("TOM", "claro e pessoal", ["claro e pessoal", "didático"]),
        "tone_empresa": ("TOM", "executivo e operacional", ["executivo e operacional", "facilitador"]),
        "depth": ("PROFUNDIDADE", "prática", ["prática", "profunda"]),
        "aesthetic": ("ESTÉTICA", "minimalista", ["minimalista", "editorial"]),
        "opening": ("ABERTURA", "diagrama antes do detalhe", ["diagrama antes do detalhe", "ideia-chave primeiro"]),
        "cleaning": ("NÍVEL DE LIMPEZA", "preservar vocabulário", ["preservar vocabulário", "síntese estrita"]),
    },
}

VISUAL_INTENTS = {"06", "10", "M4", "W06", "W10"}
OPTIONAL_INTENTS = {"06", "09", "10", "M3", "M4", "W06", "W09", "W10"}
OPTIONAL_COPY = {
    "es": "Si mejora la comprensión, abre con un esquema breve.",
    "en": "If it improves understanding, open with a short diagram.",
    "pt": "Se melhorar a compreensão, abra com um esquema breve.",
}

LIBRARY_ROUTE = ["01", "05", "03", "04", "07", "02", "06", "08", "10", "09"]
WORKBOOK_ROUTE = ["B1", "B2", "B3"] + [f"W{i:02d}" for i in range(1, 11)]
BRANCHES = {"07": ["M1"], "06": ["M2"], "08": ["M4"], "10": ["M3"]}
BRANCH_POSITION = {"M1": ("07", "02"), "M2": ("06", "08"), "M4": ("08", "10"), "M3": ("10", "09")}
CONSUMES = {
    "05": ["01"], "03": ["05"], "04": ["03"], "07": ["05", "04"],
    "02": ["07"], "06": ["02"], "08": ["06"], "10": ["04", "08"], "09": ["10"],
    "M1": ["07"], "M2": ["06"], "M4": ["08"], "M3": ["10"],
    "B2": ["B1"], "B3": ["B2"], "W01": ["B3"], "W02": ["W01"],
    "W03": ["W02"], "W04": ["W03"], "W05": ["W04"], "W06": ["W04", "W05"],
    "W07": ["W04", "W06"], "W08": ["W04", "W05"], "W09": ["W06", "W08"],
    "W10": ["W04", "W07", "W09"],
}

# Stable artifact keys make handoffs inspectable without turning prior outputs
# into ordinary user inputs.
OUTPUTS = {
    "01": "PLAN_INICIAL_DE_INVESTIGACION", "05": "BASE_AUDITADA",
    "03": "INFORME_DE_INVESTIGACION", "04": "VERIFICACION_CRUZADA",
    "07": "MAPA_DE_CASOS", "02": "COACH_CONFIGURADO",
    "06": "PRACTICA_GENERADA", "08": "EVALUACION_PROGRESIVA",
    "10": "ENSAYO_DE_ENTREGA", "09": "BORRADOR_DE_ENTREGA",
    "M1": "CONFIG_COACH", "M2": "CONFIG_EVALUADOR",
    "M3": "CONFIG_ENTREVISTADOR", "M4": "CONFIG_PREPARADOR",
    "B1": "NOTAS_CONFIRMADAS", "B2": "PLAN_DE_ESTUDIO",
    "B3": "PLAN_DE_NOTEBOOKLM", "W01": "BASE_INICIAL",
    "W02": "DIAGNOSTICO_DE_BASE", "W03": "PLAN_DE_INVESTIGACION",
    "W04": "VEREDICTO_DE_BASE", "W05": "ROL_ACTIVADO",
    "W06": "MATERIAL_DE_APRENDIZAJE", "W07": "CASOS_PRIORIZADOS",
    "W08": "PREGUNTAS_DE_COMPRENSION", "W09": "ENSAYO_DE_DEFENSA",
    "W10": "PLAN_DE_TRANSFERENCIA",
}

DEMO = {
    "es": {
        "persona": {
            "topic": "cómo aprender a aprender con IA mediante una práctica semanal de alto rendimiento",
            "audience": "profesionales no técnicos que empiezan con IA",
            "context": "trabajo individual con 45 minutos disponibles al día",
            "purpose": "crear una práctica verificable que pueda repetir y explicar",
            "decision": "qué forma de trabajo probar durante siete días",
            "outcome": "una práctica repetible, citada y explicable",
            "team": "grupo de aprendizaje entre pares", "process": "revisión semanal",
        },
        "empresa": {
            "topic": "cómo aprender a aprender con IA mediante formas de trabajo de alto rendimiento",
            "audience": "equipo de operaciones que inicia un piloto de IA",
            "context": "piloto controlado de siete días con revisión humana",
            "purpose": "probar una forma de trabajo compartida, verificable y repetible",
            "decision": "si escalar, ajustar o detener el piloto",
            "outcome": "un flujo compartible con responsable, evidencia y control",
            "team": "equipo piloto de operaciones", "process": "preparación y revisión semanal de decisiones",
        },
    },
    "en": {
        "persona": {
            "topic": "how to learn with AI through a weekly high-performance practice",
            "audience": "non-technical professionals starting with AI", "context": "individual work with 45 minutes available each day",
            "purpose": "build a verifiable practice I can repeat and explain", "decision": "which way of working to test for seven days",
            "outcome": "a repeatable, cited and explainable practice", "team": "peer learning group", "process": "weekly review",
        },
        "empresa": {
            "topic": "how to learn with AI through high-performance ways of working",
            "audience": "operations team starting an AI pilot", "context": "controlled seven-day pilot with human review",
            "purpose": "test a shared, verifiable and repeatable way of working", "decision": "whether to scale, adjust or stop the pilot",
            "outcome": "a shareable workflow with an owner, evidence and control", "team": "operations pilot team", "process": "weekly decision preparation and review",
        },
    },
    "pt": {
        "persona": {
            "topic": "como aprender a aprender com IA por meio de uma prática semanal de alto desempenho",
            "audience": "profissionais não técnicos iniciando com IA", "context": "trabalho individual com 45 minutos disponíveis por dia",
            "purpose": "criar uma prática verificável que eu consiga repetir e explicar", "decision": "qual forma de trabalho testar por sete dias",
            "outcome": "uma prática repetível, citada e explicável", "team": "grupo de aprendizagem entre pares", "process": "revisão semanal",
        },
        "empresa": {
            "topic": "como aprender a aprender com IA por meio de formas de trabalho de alto desempenho",
            "audience": "equipe de operações iniciando um piloto de IA", "context": "piloto controlado de sete dias com revisão humana",
            "purpose": "testar uma forma de trabalho compartilhada, verificável e repetível", "decision": "se deve escalar, ajustar ou interromper o piloto",
            "outcome": "um fluxo compartilhável com responsável, evidência e controle", "team": "equipe piloto de operações", "process": "preparação e revisão semanal de decisões",
        },
    },
}


def alias_index(locale: str) -> dict[str, str]:
    index = {}
    for key, definition in INPUTS.items():
        for alias in definition["aliases"][locale]:
            index[norm(alias)] = key
    return index


def option_index(locale: str) -> dict[str, str]:
    index = {}
    for key, definition in OPTION_ALIASES.items():
        for alias in definition["aliases"][locale]:
            index[norm(alias)] = key
    return index


def marker_values(prompt: str) -> list[str]:
    values = re.findall(r"\[([^]]+)\]", prompt)
    values += re.findall(r"\{\{([^}]+)\}\}", prompt)
    return list(dict.fromkeys(value.strip() for value in values))


def demo_value(key: str, locale: str, audience: str, definition: dict) -> str:
    direct = DEMO[locale][audience].get(key)
    if direct:
        return direct
    if key in {"base", "sources", "sources_or_notebook", "materials"}:
        return {
            "es": "dossier sintético Demo: guía del método, registro de práctica y criterios de revisión",
            "en": "synthetic Demo dossier: method guide, practice log and review criteria",
            "pt": "dossiê sintético Demo: guia do método, registro de prática e critérios de revisão",
        }[locale]
    if key in {"gap", "claim", "study_plan"}:
        return {
            "es": "artefacto sintético del paso anterior: falta demostrar transferencia a un segundo contexto",
            "en": "synthetic prior-step artifact: transfer to a second context still needs evidence",
            "pt": "artefato sintético da etapa anterior: ainda falta demonstrar transferência para um segundo contexto",
        }[locale]
    return definition["example"][locale]


def input_record(key: str, locale: str, audience: str) -> dict:
    definition = INPUTS[key]
    return {
        "key": key,
        "label": definition["label"][locale],
        "help": definition["help"][locale],
        "example": definition["example"][locale],
        "required": True,
        "type": "long_text" if key in {"base", "sources", "sources_or_notebook", "materials", "brain_dump"} else "text",
        "source": definition.get("source", "user"),
        "demo_value": demo_value(key, locale, audience, definition),
    }


def parameter(key: str, locale: str, audience: str) -> dict:
    actual = "tone_empresa" if key == "tone" and audience == "empresa" else "tone_persona" if key == "tone" else key
    label, default, choices = SETTING_COPY[locale][actual]
    return {"key": key, "label": label, "default": default, "choices": choices}


def flow_for(intent_id: str) -> dict:
    route = LIBRARY_ROUTE if intent_id in LIBRARY_ROUTE or intent_id in BRANCH_POSITION else WORKBOOK_ROUTE
    if intent_id in BRANCH_POSITION:
        previous, next_id = BRANCH_POSITION[intent_id]
        order = route.index(next_id)
    else:
        order = route.index(intent_id)
        previous = route[order - 1] if order else None
        next_id = route[order + 1] if order + 1 < len(route) else None
    return {
        "route": "library" if route is LIBRARY_ROUTE else "workbook",
        "order": order + 1,
        "previous": previous,
        "next": next_id,
        "branches": BRANCHES.get(intent_id, []),
        "consumes": [OUTPUTS[item] for item in CONSUMES.get(intent_id, [])],
        "produces": OUTPUTS[intent_id],
        "external_gate": intent_id in {"01", "03", "W03"},
        "loop_to": "W03" if intent_id == "W04" else None,
        "standalone": True,
    }


def migrate_cell(cell: dict, locale: str, audience: str, intent_id: str) -> None:
    index = alias_index(locale)
    options = option_index(locale)
    prompt = cell["prompt"].replace("{{BRAIN_DUMP}}", "[BRAIN_DUMP]")
    inputs = []
    option_parameters = []
    seen_inputs = set()
    for raw in marker_values(prompt):
        normalized = norm(raw)
        if normalized in {norm("BASE SUFICIENTE"), norm("REPETIR INVESTIGACIÓN"), norm("BASE SUFFICIENT"), norm("REPEAT RESEARCH"), norm("REPETIR PESQUISA")}:
            prompt = prompt.replace(f"[{raw}]", raw)
            continue
        if normalized in {norm("EXTENSIÓN"), norm("EXTENSÃO"), norm("LENGTH"), norm("NIVEL DE LIMPIEZA"), norm("CLEANING LEVEL"), norm("NÍVEL DE LIMPEZA")}:
            prompt = prompt.replace(f"[{raw}]", SETTING_COPY[locale]["length" if "limp" not in normalized and "clean" not in normalized else "cleaning"][1])
            continue
        if normalized in options:
            key = options[normalized]
            definition = OPTION_ALIASES[key]
            prompt = prompt.replace(f"[{raw}]", definition["default"][locale])
            option_parameters.append({
                "key": key, "label": definition["label"][locale],
                "default": definition["default"][locale], "choices": definition["choices"][locale],
            })
            continue
        key = index.get(normalized)
        if not key:
            raise SystemExit(f"PROMPT_V2_UNKNOWN_INPUT:{intent_id}:{locale}:{audience}:{raw}")
        definition = INPUTS[key]
        label = definition["label"][locale]
        prompt = prompt.replace(f"[{raw}]", f"<{label}>")
        if key not in seen_inputs:
            inputs.append(input_record(key, locale, audience))
            seen_inputs.add(key)
    settings = [parameter("length", locale, audience), parameter("structure", locale, audience), parameter("tone", locale, audience), parameter("depth", locale, audience)]
    if intent_id in VISUAL_INTENTS:
        settings += [parameter("aesthetic", locale, audience), parameter("opening", locale, audience)]
    if intent_id == "B1":
        settings.append(parameter("cleaning", locale, audience))
    settings += option_parameters
    optional = []
    if intent_id in OPTIONAL_INTENTS:
        clause = OPTIONAL_COPY[locale]
        optional.append({"key": "visual_opening", "text": clause, "default_enabled": True})
        prompt = prompt.rstrip() + f" [{clause}]"
    cell["prompt"] = prompt
    cell["inputs"] = inputs
    cell["parameters"] = settings
    cell["optional_clauses"] = optional
    spec = cell["level_spec"]
    spec["constraints"] = spec.pop("parameters")


def ensure_standalone_inputs(document: dict) -> None:
    """A prompt that works alone must name the material it consumes.

    W05 and W09 previously depended on an implicit Notebook/deliverable. The v2
    contract makes those handoffs explicit without changing their boundaries.
    """
    intent_id = document["intent_id"]
    if intent_id not in {"W05", "W09"}:
        return
    if intent_id == "W09":
        for audience in AUDIENCES:
            cell = document["locales"]["pt"][audience]
            if cell["purpose"].startswith("Simula "):
                cell["purpose"] = "Simule " + cell["purpose"][7:]
    for locale in LANGS:
        cell = document["locales"][locale]["persona"]
        if intent_id == "W05" and not any(item["key"] == "sources_or_notebook" for item in cell["inputs"]):
            token = f'<{INPUTS["sources_or_notebook"]["label"][locale]}>'
            replacements = {
                "es": ("especializado en este Notebook", f"especializado en {token}"),
                "en": ("specialized in this Notebook", f"specialized in {token}"),
                "pt": ("especializado neste Notebook", f"especializado em {token}"),
            }
            old, new = replacements[locale]
            cell["prompt"] = cell["prompt"].replace(old, new, 1)
            cell["inputs"].insert(0, input_record("sources_or_notebook", locale, "persona"))
        if intent_id == "W09" and not any(item["key"] == "deliverable" for item in cell["inputs"]):
            token = f'<{INPUTS["deliverable"]["label"][locale]}>'
            replacements = {
                "es": ("Simula una defensa sobre", f"Simula una defensa de {token} sobre"),
                "en": ("Simulate an defense on", f"Simulate a defense of {token} on"),
                "pt": ("Simule uma defesa sobre", f"Simule uma defesa de {token} sobre"),
            }
            old, new = replacements[locale]
            cell["prompt"] = cell["prompt"].replace(old, new, 1)
            cell["inputs"].insert(0, input_record("deliverable", locale, "persona"))


def normalize_optional_projection(document: dict) -> None:
    """Keep N1 direct; N2-N4 project the governed optional clauses."""
    for locale in LANGS:
        for audience in AUDIENCES:
            cell = document["locales"][locale][audience]
            for clause in cell["optional_clauses"]:
                suffix = f' [{clause["text"]}]'
                if cell["prompt"].endswith(suffix):
                    cell["prompt"] = cell["prompt"][:-len(suffix)]


def refresh_input_metadata(document: dict) -> None:
    """Keep governed labels, examples and Demo values reproducible on reruns."""
    for locale in LANGS:
        for audience in AUDIENCES:
            cell = document["locales"][locale][audience]
            cell["inputs"] = [input_record(item["key"], locale, audience) for item in cell["inputs"]]


def preserve_persona_voice(document: dict) -> None:
    """Keep the frozen persona tone charter after marker normalization."""
    intent_id = document["intent_id"]
    if intent_id == "01":
        replacements = {
            ("es", "persona"): ("Quiero comprender <TEMA> para tomar <DECISIÓN>.", "Quiero comprender <TEMA>. Debo resolver <DECISIÓN>."),
            ("es", "empresa"): ("antes de <DECISIÓN>, con responsable definido", "antes de resolver <DECISIÓN>, con responsable definido"),
            ("en", "persona"): ("I need to understand <TOPIC> to make <DECISION>.", "I need to understand <TOPIC>. The decision at stake is <DECISION>."),
            ("en", "empresa"): ("before <DECISION>, with a defined owner", "before resolving <DECISION>, with a defined owner"),
            ("pt", "persona"): ("Quero compreender <TEMA> para tomar <DECISÃO>.", "Quero compreender <TEMA>. Preciso resolver <DECISÃO>."),
            ("pt", "empresa"): ("antes de <DECISÃO>, com responsável definido", "antes de resolver <DECISÃO>, com responsável definido"),
        }
        for (locale, audience), (old, new) in replacements.items():
            cell = document["locales"][locale][audience]
            cell["prompt"] = cell["prompt"].replace(old, new, 1)
    if intent_id == "06":
        cell = document["locales"]["pt"]["persona"]
        cell["prompt"] = cell["prompt"].replace("Crie uma prática", "Crie minha prática", 1)
    if intent_id == "W01":
        replacements = {
            ("es", "persona"): ("La necesito para <DECISIÓN>;", "Debe ayudarme a resolver <DECISIÓN>;"),
            ("es", "empresa"): ("antes de <DECISIÓN>.", "y debe ayudar a resolver <DECISIÓN>."),
            ("en", "persona"): ("I need it for <DECISION>;", "It must help me resolve <DECISION>;"),
            ("en", "empresa"): ("before <DECISION>.", "and must help resolve <DECISION>."),
            ("pt", "persona"): ("Preciso dela para <DECISÃO>;", "Ela deve me ajudar a resolver <DECISÃO>;"),
            ("pt", "empresa"): ("antes de <DECISÃO>.", "e deve ajudar a resolver <DECISÃO>."),
        }
        for (locale, audience), (old, new) in replacements.items():
            cell = document["locales"][locale][audience]
            cell["prompt"] = cell["prompt"].replace(old, new, 1)
    if intent_id == "B2":
        replacements = {
            "es": ("y lo usaré para <DECISIÓN>.", "y lo usaré para resolver <DECISIÓN>."),
            "en": ("and I will use it for <DECISION>.", "and I will use it to resolve <DECISION>."),
            "pt": ("e vou usá-lo para <DECISÃO>.", "e vou usá-lo para resolver <DECISÃO>."),
        }
        for locale, (old, new) in replacements.items():
            cell = document["locales"][locale]["persona"]
            cell["prompt"] = cell["prompt"].replace(old, new, 1)
    if intent_id == "W03":
        replacements = {
            "es": (("para mi <RESULTADO>", "para lograr <RESULTADO>", "para que yo logre <RESULTADO>", "para <RESULTADO>"), "en mi camino hacia <RESULTADO>"),
            "en": (("for my <OUTCOME>", "to achieve <OUTCOME>", "so I can achieve <OUTCOME>", "so I achieve <OUTCOME>", "in my path to <OUTCOME>", "for <OUTCOME>"), "on my way to <OUTCOME>"),
            "pt": (("no meu caminho para meu <RESULTADO>", "para alcançar <RESULTADO>", "para que eu alcance <RESULTADO>", "para eu alcançar <RESULTADO>", "no meu caminho para <RESULTADO>", "para <RESULTADO>"), "para meu <RESULTADO>"),
        }
        for locale, (olds, new) in replacements.items():
            cell = document["locales"][locale]["persona"]
            for old in olds:
                if old in cell["prompt"]:
                    cell["prompt"] = cell["prompt"].replace(old, new, 1)
                    break
        pt_cell = document["locales"]["pt"]["persona"]
        for item in pt_cell["inputs"]:
            if item["key"] == "outcome":
                item["example"] = "aprendizado repetível"
                item["demo_value"] = "aprendizado repetível, citado e explicável"


def refresh_named_practices(document: dict) -> None:
    """Bind each intent to a small, localized operating-method set."""
    intent_id = document["intent_id"]
    keys = PRACTICES_BY_INTENT[intent_id]
    if not 1 <= len(keys) <= 3:
        raise SystemExit(f"PROMPT_V2_PRACTICE_COUNT:{intent_id}")
    for locale in LANGS:
        values = [PRACTICES[key][locale] for key in keys]
        for audience in AUDIENCES:
            document["locales"][locale][audience]["level_spec"]["frameworks"] = values


def main() -> int:
    migrated = 0
    for path in sorted(CONTRACTS.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        if document.get("schema_version") not in {"prompt-intent-contract-v1", "prompt-intent-contract-v2"}:
            raise SystemExit(f"PROMPT_V2_SOURCE_SCHEMA:{path.name}")
        intent_id = document["intent_id"]
        if document["schema_version"] == "prompt-intent-contract-v1":
            document["schema_version"] = "prompt-intent-contract-v2"
            for locale in LANGS:
                for audience in AUDIENCES:
                    migrate_cell(document["locales"][locale][audience], locale, audience, intent_id)
        document["flow"] = flow_for(intent_id)
        ensure_standalone_inputs(document)
        refresh_input_metadata(document)
        normalize_optional_projection(document)
        preserve_persona_voice(document)
        refresh_named_practices(document)
        document["self_sha256"] = canonical_self(document)
        path.write_text(json.dumps(document, ensure_ascii=False, sort_keys=False, indent=2) + "\n", encoding="utf-8")
        migrated += 1
    print(f"PROMPT_CONTRACT_V2_MIGRATION_OK contracts={migrated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
