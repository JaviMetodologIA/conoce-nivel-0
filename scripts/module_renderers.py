#!/usr/bin/env python3
"""Pure HTML renderers for Nivel 0 modules 02-04.

[METODOLOGIA] This module is deliberately independent from ``build.py`` and
``brand.py``.  It consumes one already-resolved ``variant.module`` payload and
returns exactly one ``<main>`` element per resource.  Chrome, breadcrumbs,
canonical URLs, the intrapage rail and the footer remain responsibilities of
the caller.

Public integration surface::

    render_masterclass(payload, locale, audience, module, urls) -> str
    render_workbook(payload, locale, audience, module, urls) -> str
    render_playbook(payload, locale, audience, module, urls) -> str
    render_prompts(payload, locale, audience, module, urls) -> str
    render_module_bundle(variant, urls) -> dict[str, str]

``payload`` may be the resource mapping itself or the complete module mapping.
``module`` is always the complete module mapping.  ``urls`` must contain safe
URLs for ``masterclass``, ``workbook``, ``playbook``, ``prompts`` and
``resources``.  Masterclass additionally requires ``pdf`` and a governed
64-character ``pdf_sha256`` value.

No filesystem, clock, network, environment or mutable global state is read.
All content is escaped, identifiers are constrained, and unsafe URL schemes
fail closed.  The existing Nivel 0 CSS and progressive-enhancement selectors
are intentionally reused; essential content remains operable without JS.
"""

from __future__ import annotations

import html
import re
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from ui_primitives import ui_icon


LOCALES = ("es", "en", "pt")
AUDIENCES = ("persona", "empresa")
RESOURCE_KEYS = ("masterclass", "workbook", "playbook", "prompts")
_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class RendererContractError(ValueError):
    """Raised when a normalized module payload is incomplete or unsafe."""


UI = {
    "es": {
        "module": "Módulo",
        "module_resources": "Recursos de este módulo",
        "masterclass": "Masterclass",
        "workbook": "Workbook",
        "playbook": "Playbook",
        "prompts": "Prompts",
        "resources": "Todos los recursos",
        "open_pdf": "Abrir PDF",
        "download_pdf": "Descargar PDF",
        "pdf_label": "PDF oficial de la masterclass",
        "pdf_fallback": "Tu navegador no puede mostrar el PDF integrado. Ábrelo en otra pestaña o descárgalo.",
        "pdf_access_warning": "El PDF oficial no está etiquetado. Usa la guía HTML accesible para seguir su contenido.",
        "access_notice": "Aviso de accesibilidad",
        "accessible_guide": "Guía HTML accesible",
        "guide_lead": "Sigue el contenido por momentos. Esta guía acompaña el PDF; no sustituye su contenido ni su diseño.",
        "document_note": "Nota sobre el documento",
        "moments": "Momentos",
        "moment": "Momento",
        "page": "Página",
        "base_route": "Ruta base",
        "extended_route": "Con práctica extendida",
        "previous": "Anterior",
        "next": "Siguiente",
        "progress": "Progreso de la masterclass",
        "duration_not_declared": "Duración no declarada",
        "adaptive_route": "Recorrido completo",
        "deepen": "Profundiza este momento antes de avanzar.",
        "outcome": "Resultado del recorrido",
        "start": "Empezar",
        "print": "Imprimir",
        "guide": "Cómo usar este workbook",
        "guide_lead_workbook": "Empieza en clase, profundiza con práctica y consolida solo con evidencia revisable.",
        "workbook_guide_steps": (
            ("Orienta el caso", "Declara el caso, el resultado y la evidencia que quieres observar."),
            ("Prepara los insumos", "Reúne lo necesario, reconoce los límites y usa los tres prompts de preparación."),
            ("Trabaja en clase", "Completa la práctica esencial y conserva una primera evidencia."),
            ("Profundiza", "Abre cada detalle para revisar acciones, criterios, ejemplos y conexiones."),
            ("Consolida y transfiere", "Supera el criterio, revisa la evidencia y prueba la práctica en otro contexto."),
        ),
        "workbook_stages": ("En clase", "Profundización", "Consolidación"),
        "consolidation_criterion": "Criterio de consolidación",
        "preparation": "Antes de empezar",
        "challenge": "Reto",
        "practice": "Práctica",
        "evidence": "Evidencia",
        "route": "Recorrido",
        "step": "Paso",
        "your_evidence": "Tu evidencia",
        "transfer": "Transferencia",
        "next_step": "Siguiente paso",
        "open_next": "Abrir",
        "resource_handoff": "Continúa con el siguiente recurso del recorrido.",
        "full_index": "Índice completo",
        "introduction": "Punto de partida",
        "chapter": "Capítulo",
        "library_map": "Cómo usar esta biblioteca",
        "library_map_lead": "Elige la superficie, abre un prompt y copia el nivel y modo visibles.",
        "view_prompts": "Ver prompts",
        "all": "Todos",
        "chat": "Chat",
        "sources": "Fuentes",
        "surface": "Ejecutar en",
        "open_prompt": "Abrir prompt",
        "close_prompt": "Cerrar prompt",
        "details": "Antes de copiar",
        "receives": "Recibe",
        "produces": "Produce",
        "consumes": "Consume",
        "mode": "Modo",
        "template": "Plantilla",
        "demo": "Demo",
        "syntax": "< > reemplaza · [ ] opcional · PARÁMETROS ajusta",
        "inputs": "Inputs",
        "example": "Ejemplo",
        "required": "Obligatorio",
        "optional": "Opcional",
        "parameters": "Parámetros",
        "copy": "Copiar prompt",
        "copied": "Copiado",
        "deepen_content": "Profundizar",
        "key_points": "Puntos clave",
        "application": "Aplicación",
        "check_question": "Comprueba tu comprensión",
        "micro_practice": "Práctica breve",
        "takeaway": "Idea para conservar",
        "handoff": "Conecta con el siguiente recurso",
        "orientation": "Orientación",
        "case_intake": "Define tu caso",
        "case_intake_lead": "Escribe solo lo necesario para orientar la práctica. Estos campos no se guardan ni se envían.",
        "case_label": "Caso o situación",
        "result_label": "Resultado que buscas",
        "success_label": "Evidencia de avance",
        "ephemeral_note": "Uso temporal: el contenido se pierde al recargar la página.",
        "prerequisites": "Prerrequisitos",
        "workbook_limits": (
            "Trabaja con un caso acotado y autorizado.",
            "No incluyas datos personales, confidenciales o restringidos.",
            "Detente si falta evidencia, permiso o una persona responsable de revisar.",
        ),
        "reference": "Referencia",
        "use_case": "Caso de uso",
        "ready_when": "Estás listo cuando",
        "preparation_prompts": "Prompts de preparación",
        "criteria": "Criterios de calidad",
        "watch_out": "Evita",
        "reflection": "Reflexiona",
        "connection": "Conexión",
        "rubric": "Rúbrica de cierre",
        "transfer_challenge": "Desafío de transferencia",
        "review_after": "Revisión",
        "principle": "Principio",
        "decision": "Decisión que resuelve",
        "actions": "Cómo aplicarlo",
        "rule": "Regla de decisión",
        "antipattern": "Antipatrón",
        "checklist": "Checklist",
        "expected_evidence": "Evidencia esperada",
        "limit": "Límite",
        "glossary": "Glosario",
        "faq": "Preguntas frecuentes",
        "prompt_contract": "Por qué funciona",
        "direct_prompts": "10 prompts de trabajo",
        "direct_prompts_lead": "Avanza de la situación al resultado con una secuencia verificable.",
        "meta_prompts": "4 metaprompts",
        "meta_prompts_lead": "Crea instrumentos reutilizables para repetir y adaptar la práctica.",
        "purpose": "Propósito",
        "when": "Cuándo usarlo",
        "workflow": "Flujo",
        "frameworks": "Best practices y frameworks",
        "guardrails": "Guardrails",
        "acceptance": "Criterios de aceptación",
        "edge_cases": "Casos borde",
        "tradeoff": "Trade-off",
        "tradeoffs": "Compensaciones",
        "assumptions": "Supuestos",
        "prompt_assumption": "Los inputs, permisos y fuentes declarados representan el caso que se revisará.",
        "limits": "Límites",
        "independent_use": "Uso independiente",
        "demo_artifact": "Datos sintéticos disponibles",
        "synthetic_demo_rule": "Trata los datos de demostración como sintéticos.",
        "execution_gate": "Acción fuera de NotebookLM",
        "gate_produces": "Debes aportar",
        "gate_criteria": "Continúa cuando",
        "level_names": ("Directo", "Estructurado", "Especificado", "Orquestado"),
        "level_desc": (
            "Una orden clara y breve.",
            "Inputs y parámetros explícitos.",
            "Situación, propósito, estándares y criterios.",
            "Reglas invariantes separadas de los datos del caso.",
        ),
    },
    "en": {
        "module": "Module",
        "module_resources": "Resources in this module",
        "masterclass": "Masterclass",
        "workbook": "Workbook",
        "playbook": "Playbook",
        "prompts": "Prompts",
        "resources": "All resources",
        "open_pdf": "Open PDF",
        "download_pdf": "Download PDF",
        "pdf_label": "Official masterclass PDF",
        "pdf_fallback": "Your browser cannot display the embedded PDF. Open it in another tab or download it.",
        "pdf_access_warning": "The official PDF is not tagged. Use the accessible HTML guide to follow its content.",
        "access_notice": "Accessibility notice",
        "accessible_guide": "Accessible HTML guide",
        "guide_lead": "Follow the content moment by moment. This guide accompanies the PDF; it does not replace its content or design.",
        "document_note": "Document note",
        "moments": "Moments",
        "moment": "Moment",
        "page": "Page",
        "base_route": "Core route",
        "extended_route": "With extended practice",
        "previous": "Previous",
        "next": "Next",
        "progress": "Masterclass progress",
        "duration_not_declared": "Duration not declared",
        "adaptive_route": "Complete journey",
        "deepen": "Explore this moment further before moving on.",
        "outcome": "Journey outcome",
        "start": "Start",
        "print": "Print",
        "guide": "How to use this workbook",
        "guide_lead_workbook": "Start in class, deepen through practice, and consolidate only with reviewable evidence.",
        "workbook_guide_steps": (
            ("Frame the case", "State the case, desired result and evidence you want to observe."),
            ("Prepare the inputs", "Gather what is needed, acknowledge boundaries and use the three preparation prompts."),
            ("Work in class", "Complete the essential practice and retain initial evidence."),
            ("Go deeper", "Open each detail to review actions, criteria, examples and connections."),
            ("Consolidate and transfer", "Meet the criterion, review the evidence and test the practice in another context."),
        ),
        "workbook_stages": ("In class", "Deepening", "Consolidation"),
        "consolidation_criterion": "Consolidation criterion",
        "preparation": "Before you begin",
        "challenge": "Challenge",
        "practice": "Practice",
        "evidence": "Evidence",
        "route": "Route",
        "step": "Step",
        "your_evidence": "Your evidence",
        "transfer": "Transfer",
        "next_step": "Next step",
        "open_next": "Open",
        "resource_handoff": "Continue with the next resource in the journey.",
        "full_index": "Full index",
        "introduction": "Starting point",
        "chapter": "Chapter",
        "library_map": "How to use this library",
        "library_map_lead": "Choose the surface, open a prompt, then copy the visible level and mode.",
        "view_prompts": "View prompts",
        "all": "All",
        "chat": "Chat",
        "sources": "Sources",
        "surface": "Run in",
        "open_prompt": "Open prompt",
        "close_prompt": "Close prompt",
        "details": "Before copying",
        "receives": "Receives",
        "produces": "Produces",
        "consumes": "Consumes",
        "mode": "Mode",
        "template": "Template",
        "demo": "Demo",
        "syntax": "< > replace · [ ] optional · PARAMETERS adjust",
        "inputs": "Inputs",
        "example": "Example",
        "required": "Required",
        "optional": "Optional",
        "parameters": "Parameters",
        "copy": "Copy prompt",
        "copied": "Copied",
        "deepen_content": "Go deeper",
        "key_points": "Key points",
        "application": "Application",
        "check_question": "Check your understanding",
        "micro_practice": "Short practice",
        "takeaway": "Keep this idea",
        "handoff": "Connect to the next resource",
        "orientation": "Orientation",
        "case_intake": "Define your case",
        "case_intake_lead": "Write only what is needed to frame the practice. These fields are neither saved nor sent.",
        "case_label": "Case or situation",
        "result_label": "Desired result",
        "success_label": "Evidence of progress",
        "ephemeral_note": "Temporary use: the content is lost when the page reloads.",
        "prerequisites": "Prerequisites",
        "workbook_limits": (
            "Work with a bounded, authorized case.",
            "Do not include personal, confidential or restricted data.",
            "Stop when evidence, permission or an accountable reviewer is missing.",
        ),
        "reference": "Reference",
        "use_case": "Use case",
        "ready_when": "You are ready when",
        "preparation_prompts": "Preparation prompts",
        "criteria": "Quality criteria",
        "watch_out": "Avoid",
        "reflection": "Reflect",
        "connection": "Connection",
        "rubric": "Closing rubric",
        "transfer_challenge": "Transfer challenge",
        "review_after": "Review",
        "principle": "Principle",
        "decision": "Decision it resolves",
        "actions": "How to apply it",
        "rule": "Decision rule",
        "antipattern": "Antipattern",
        "checklist": "Checklist",
        "expected_evidence": "Expected evidence",
        "limit": "Limit",
        "glossary": "Glossary",
        "faq": "Frequently asked questions",
        "prompt_contract": "Why it works",
        "direct_prompts": "10 working prompts",
        "direct_prompts_lead": "Move from the situation to the outcome through a verifiable sequence.",
        "meta_prompts": "4 metaprompts",
        "meta_prompts_lead": "Create reusable instruments to repeat and adapt the practice.",
        "purpose": "Purpose",
        "when": "When to use it",
        "workflow": "Workflow",
        "frameworks": "Best practices and frameworks",
        "guardrails": "Guardrails",
        "acceptance": "Acceptance criteria",
        "edge_cases": "Edge cases",
        "tradeoff": "Trade-off",
        "tradeoffs": "Trade-offs",
        "assumptions": "Assumptions",
        "prompt_assumption": "The declared inputs, permissions and sources represent the case under review.",
        "limits": "Limits",
        "independent_use": "Independent use",
        "demo_artifact": "Available synthetic data",
        "synthetic_demo_rule": "Treat demo data as synthetic.",
        "execution_gate": "Action outside NotebookLM",
        "gate_produces": "You must provide",
        "gate_criteria": "Continue when",
        "level_names": ("Direct", "Structured", "Specified", "Orchestrated"),
        "level_desc": (
            "A clear, concise instruction.",
            "Explicit inputs and parameters.",
            "Situation, purpose, standards and criteria.",
            "Invariant rules separated from case data.",
        ),
    },
    "pt": {
        "module": "Módulo",
        "module_resources": "Recursos deste módulo",
        "masterclass": "Masterclass",
        "workbook": "Workbook",
        "playbook": "Playbook",
        "prompts": "Prompts",
        "resources": "Todos os recursos",
        "open_pdf": "Abrir PDF",
        "download_pdf": "Baixar PDF",
        "pdf_label": "PDF oficial da masterclass",
        "pdf_fallback": "Seu navegador não consegue exibir o PDF incorporado. Abra-o em outra aba ou baixe-o.",
        "pdf_access_warning": "O PDF oficial não está etiquetado. Use o guia HTML acessível para acompanhar seu conteúdo.",
        "access_notice": "Aviso de acessibilidade",
        "accessible_guide": "Guia HTML acessível",
        "guide_lead": "Acompanhe o conteúdo por momentos. Este guia acompanha o PDF; não substitui seu conteúdo nem seu design.",
        "document_note": "Nota sobre o documento",
        "moments": "Momentos",
        "moment": "Momento",
        "page": "Página",
        "base_route": "Rota base",
        "extended_route": "Com prática estendida",
        "previous": "Anterior",
        "next": "Próximo",
        "progress": "Progresso da masterclass",
        "duration_not_declared": "Duração não declarada",
        "adaptive_route": "Percurso completo",
        "deepen": "Aprofunde este momento antes de avançar.",
        "outcome": "Resultado do percurso",
        "start": "Começar",
        "print": "Imprimir",
        "guide": "Como usar este workbook",
        "guide_lead_workbook": "Comece em aula, aprofunde com prática e consolide somente com evidência revisável.",
        "workbook_guide_steps": (
            ("Oriente o caso", "Declare o caso, o resultado e a evidência que deseja observar."),
            ("Prepare os insumos", "Reúna o necessário, reconheça os limites e use os três prompts de preparação."),
            ("Trabalhe em aula", "Conclua a prática essencial e preserve uma primeira evidência."),
            ("Aprofunde", "Abra cada detalhe para revisar ações, critérios, exemplos e conexões."),
            ("Consolide e transfira", "Atenda ao critério, revise a evidência e teste a prática em outro contexto."),
        ),
        "workbook_stages": ("Em aula", "Aprofundamento", "Consolidação"),
        "consolidation_criterion": "Critério de consolidação",
        "preparation": "Antes de começar",
        "challenge": "Desafio",
        "practice": "Prática",
        "evidence": "Evidência",
        "route": "Percurso",
        "step": "Passo",
        "your_evidence": "Sua evidência",
        "transfer": "Transferência",
        "next_step": "Próximo passo",
        "open_next": "Abrir",
        "resource_handoff": "Continue com o próximo recurso do percurso.",
        "full_index": "Índice completo",
        "introduction": "Ponto de partida",
        "chapter": "Capítulo",
        "library_map": "Como usar esta biblioteca",
        "library_map_lead": "Escolha a superfície, abra um prompt e copie o nível e modo visíveis.",
        "view_prompts": "Ver prompts",
        "all": "Todos",
        "chat": "Chat",
        "sources": "Fontes",
        "surface": "Executar em",
        "open_prompt": "Abrir prompt",
        "close_prompt": "Fechar prompt",
        "details": "Antes de copiar",
        "receives": "Recebe",
        "produces": "Produz",
        "consumes": "Consome",
        "mode": "Modo",
        "template": "Modelo",
        "demo": "Demo",
        "syntax": "< > substitua · [ ] opcional · PARÂMETROS ajuste",
        "inputs": "Inputs",
        "example": "Exemplo",
        "required": "Obrigatório",
        "optional": "Opcional",
        "parameters": "Parâmetros",
        "copy": "Copiar prompt",
        "copied": "Copiado",
        "deepen_content": "Aprofundar",
        "key_points": "Pontos-chave",
        "application": "Aplicação",
        "check_question": "Verifique sua compreensão",
        "micro_practice": "Prática breve",
        "takeaway": "Ideia para conservar",
        "handoff": "Conecte com o próximo recurso",
        "orientation": "Orientação",
        "case_intake": "Defina seu caso",
        "case_intake_lead": "Escreva apenas o necessário para orientar a prática. Estes campos não são salvos nem enviados.",
        "case_label": "Caso ou situação",
        "result_label": "Resultado desejado",
        "success_label": "Evidência de avanço",
        "ephemeral_note": "Uso temporário: o conteúdo é perdido ao recarregar a página.",
        "prerequisites": "Pré-requisitos",
        "workbook_limits": (
            "Trabalhe com um caso delimitado e autorizado.",
            "Não inclua dados pessoais, confidenciais ou restritos.",
            "Pare quando faltar evidência, permissão ou uma pessoa responsável pela revisão.",
        ),
        "reference": "Referência",
        "use_case": "Caso de uso",
        "ready_when": "Você está pronto quando",
        "preparation_prompts": "Prompts de preparação",
        "criteria": "Critérios de qualidade",
        "watch_out": "Evite",
        "reflection": "Reflita",
        "connection": "Conexão",
        "rubric": "Rubrica de fechamento",
        "transfer_challenge": "Desafio de transferência",
        "review_after": "Revisão",
        "principle": "Princípio",
        "decision": "Decisão que resolve",
        "actions": "Como aplicar",
        "rule": "Regra de decisão",
        "antipattern": "Antipadrão",
        "checklist": "Checklist",
        "expected_evidence": "Evidência esperada",
        "limit": "Limite",
        "glossary": "Glossário",
        "faq": "Perguntas frequentes",
        "prompt_contract": "Por que funciona",
        "direct_prompts": "10 prompts de trabalho",
        "direct_prompts_lead": "Avance da situação ao resultado por uma sequência verificável.",
        "meta_prompts": "4 metaprompts",
        "meta_prompts_lead": "Crie instrumentos reutilizáveis para repetir e adaptar a prática.",
        "purpose": "Propósito",
        "when": "Quando usar",
        "workflow": "Fluxo",
        "frameworks": "Boas práticas e frameworks",
        "guardrails": "Guardrails",
        "acceptance": "Critérios de aceitação",
        "edge_cases": "Casos-limite",
        "tradeoff": "Trade-off",
        "tradeoffs": "Compensações",
        "assumptions": "Suposições",
        "prompt_assumption": "Os inputs, permissões e fontes declarados representam o caso em revisão.",
        "limits": "Limites",
        "independent_use": "Uso independente",
        "demo_artifact": "Dados sintéticos disponíveis",
        "synthetic_demo_rule": "Trate os dados de demonstração como sintéticos.",
        "execution_gate": "Ação fora do NotebookLM",
        "gate_produces": "Você deve fornecer",
        "gate_criteria": "Continue quando",
        "level_names": ("Direto", "Estruturado", "Especificado", "Orquestrado"),
        "level_desc": (
            "Uma instrução clara e curta.",
            "Inputs e parâmetros explícitos.",
            "Situação, propósito, padrões e critérios.",
            "Regras invariantes separadas dos dados do caso.",
        ),
    },
}

# Public, locale-stable learning-cycle labels. ``build.py`` consumes the same
# authority for the intrapage rail so navigation and workbook tabs cannot drift.
WORKBOOK_STAGE_LABELS = {
    locale: tuple(UI[locale]["workbook_stages"])
    for locale in LOCALES
}


# [METODOLOGIA] Module prompt pages consume immutable imported payloads, but
# project their four execution levels through the same semantic convention as
# the M1 golden library.  Keeping this copy in the renderer prevents legacy
# ``levels[].body`` strings from deciding what N2, N3 or N4 mean.
PROMPT_FORMAT = {
    "es": {
        "parameters": "# PARÁMETROS",
        "inputs": "# INPUTS",
        "task": "# Tarea",
        "workflow": "# Flujo",
        "guardrails": "# Límites",
        "output": "# Salida esperada",
        "dod": "# Definition of Done",
        "frameworks": "# MARCOS Y BUENAS PRÁCTICAS",
        "optional": "# Ajustes opcionales",
        "objective": "Objetivo",
        "data": "Datos",
        "apply": "Aplica",
        "order": "Orden",
        "deliver": "Entrega",
        "limit": "Límite",
        "example": "ej.",
        "none": "Ninguno",
        "synthetic": "Demo sintética",
        "demo_artifact": "ARTEFACTO_DEMO",
        "demo_available": "Datos sintéticos disponibles:",
        "role_prefix": "Especialista responsable de",
        "audience_scope": {
            "persona": "La decisión final y la evidencia permanecen bajo tu responsabilidad.",
            "empresa": "El equipo nombra una persona responsable y una revisión independiente.",
        },
        "situation": "Situación",
        "context": "Contexto",
        "request": "Propósito y alcance",
        "expert_role": "Rol experto",
        "deliverable": "Entregable",
        "scope_in": "Incluye",
        "scope_out": "No incluye",
        "execution": "Estándares y ejecución",
        "steps": "Pasos",
        "criterion": "Criterios verificables",
        "observable": "Criterios observables",
        "provenance": "Procedencia",
        "metadata": "Metadata",
        "case_data": "Datos del caso",
        "authority": "Autoridades declaradas",
        "reasoning_policy": "Devuelve conclusiones, evidencia y metadata auditable; no expongas razonamiento privado ni cadena de pensamiento.",
    },
    "en": {
        "parameters": "# PARAMETERS",
        "inputs": "# INPUTS",
        "task": "# Task",
        "workflow": "# Workflow",
        "guardrails": "# Boundaries",
        "output": "# Expected output",
        "dod": "# Definition of Done",
        "frameworks": "# FRAMEWORKS AND BEST PRACTICES",
        "optional": "# Optional adjustments",
        "objective": "Objective",
        "data": "Data",
        "apply": "Apply",
        "order": "Order",
        "deliver": "Deliver",
        "limit": "Boundary",
        "example": "e.g.",
        "none": "None",
        "synthetic": "Synthetic demo",
        "demo_artifact": "DEMO_ARTIFACT",
        "demo_available": "Available synthetic data:",
        "role_prefix": "Specialist accountable for",
        "audience_scope": {
            "persona": "The final decision and evidence remain under your responsibility.",
            "empresa": "The team names an accountable owner and an independent reviewer.",
        },
        "situation": "Situation",
        "context": "Context",
        "request": "Purpose and scope",
        "expert_role": "Expert role",
        "deliverable": "Deliverable",
        "scope_in": "Include",
        "scope_out": "Exclude",
        "execution": "Standards and execution",
        "steps": "Steps",
        "criterion": "Verifiable criteria",
        "observable": "Observable criteria",
        "provenance": "Provenance",
        "metadata": "Metadata",
        "case_data": "Case data",
        "authority": "Declared authorities",
        "reasoning_policy": "Return conclusions, evidence and auditable metadata; do not expose private reasoning or chain of thought.",
    },
    "pt": {
        "parameters": "# PARÂMETROS",
        "inputs": "# INPUTS",
        "task": "# Tarefa",
        "workflow": "# Fluxo",
        "guardrails": "# Limites",
        "output": "# Saída esperada",
        "dod": "# Definition of Done",
        "frameworks": "# FRAMEWORKS E BOAS PRÁTICAS",
        "optional": "# Ajustes opcionais",
        "objective": "Objetivo",
        "data": "Dados",
        "apply": "Aplique",
        "order": "Ordem",
        "deliver": "Entregue",
        "limit": "Limite",
        "example": "ex.",
        "none": "Nenhum",
        "synthetic": "Demo sintética",
        "demo_artifact": "ARTEFATO_DEMO",
        "demo_available": "Dados sintéticos disponíveis:",
        "role_prefix": "Especialista responsável por",
        "audience_scope": {
            "persona": "A decisão final e a evidência permanecem sob sua responsabilidade.",
            "empresa": "A equipe nomeia uma pessoa responsável e uma revisão independente.",
        },
        "situation": "Situação",
        "context": "Contexto",
        "request": "Propósito e escopo",
        "expert_role": "Papel especialista",
        "deliverable": "Entregável",
        "scope_in": "Inclui",
        "scope_out": "Não inclui",
        "execution": "Padrões e execução",
        "steps": "Passos",
        "criterion": "Critérios verificáveis",
        "observable": "Critérios observáveis",
        "provenance": "Procedência",
        "metadata": "Metadata",
        "case_data": "Dados do caso",
        "authority": "Autoridades declaradas",
        "reasoning_policy": "Retorne conclusões, evidência e metadata auditável; não exponha raciocínio privado nem cadeia de pensamento.",
    },
}


PARAMETER_KEYS = {
    "es": {"length": "LONGITUD", "structure": "ESTRUCTURA", "depth": "PROFUNDIDAD", "approval": "APROBACIÓN"},
    "en": {"length": "LENGTH", "structure": "STRUCTURE", "depth": "DEPTH", "approval": "APPROVAL"},
    "pt": {"length": "EXTENSÃO", "structure": "ESTRUTURA", "depth": "PROFUNDIDADE", "approval": "APROVAÇÃO"},
}


PARAMETER_VALUES = {
    "es": {
        "concise": "concisa",
        "table-and-decision": "tabla breve + decisión",
        "short-table-and-decision": "tabla breve + decisión",
        "table-and-verdict": "tabla breve + veredicto",
        "executive": "ejecutiva",
        "operational": "operativa",
        "human-required": "humana obligatoria",
    },
    "en": {
        "concise": "concise",
        "table-and-decision": "short table + decision",
        "short-table-and-decision": "short table + decision",
        "table-and-verdict": "short table + verdict",
        "executive": "executive",
        "operational": "operational",
        "human-required": "human required",
    },
    "pt": {
        "concise": "concisa",
        "table-and-decision": "tabela breve + decisão",
        "short-table-and-decision": "tabela breve + decisão",
        "table-and-verdict": "tabela breve + veredito",
        "executive": "executiva",
        "operational": "operacional",
        "human-required": "humana obrigatória",
    },
}


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RendererContractError(f"{path}: expected mapping")
    return value


def _sequence(value: Any, path: str, *, minimum: int = 0) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise RendererContractError(f"{path}: expected sequence")
    if len(value) < minimum:
        raise RendererContractError(f"{path}: expected at least {minimum} items")
    return value


def _text(mapping: Mapping[str, Any], key: str, path: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RendererContractError(f"{path}.{key}: expected non-empty text")
    return value.strip()


def _integer(mapping: Mapping[str, Any], key: str, path: str, *, minimum: int = 0) -> int:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise RendererContractError(f"{path}.{key}: expected integer >= {minimum}")
    return value


def _stable_id(value: Any, path: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise RendererContractError(f"{path}: expected stable kebab-case identifier")
    return value


def _context(locale: str, audience: str, module: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    if locale not in LOCALES:
        raise RendererContractError(f"locale: unsupported value {locale!r}")
    if audience not in AUDIENCES:
        raise RendererContractError(f"audience: unsupported value {audience!r}")
    module = _mapping(module, "module")
    _stable_id(module.get("moduleId"), "module.moduleId")
    _integer(module, "order", "module", minimum=1)
    for key in ("title", "challenge", "promise", "practice", "evidence", "transfer"):
        _text(module, key, "module")
    claim_ids = _sequence(module.get("claimIds"), "module.claimIds")
    for index, claim_id in enumerate(claim_ids):
        _stable_id(claim_id, f"module.claimIds[{index}]")
    return UI[locale], module


def _resource(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    payload = _mapping(payload, "payload")
    if key in payload:
        return _mapping(payload[key], f"payload.{key}")
    return payload


def _depth_resource(depth: Mapping[str, Any] | None, key: str) -> Mapping[str, Any] | None:
    if depth is None:
        return None
    depth = _mapping(depth, "depth")
    return _mapping(depth.get(key), f"depth.{key}")


def _by_id(items: Sequence[Any], path: str) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(items):
        item = _mapping(raw, f"{path}[{index}]")
        item_id = _stable_id(item.get("id"), f"{path}[{index}].id")
        if item_id in indexed:
            raise RendererContractError(f"{path}: duplicate id {item_id}")
        indexed[item_id] = item
    return indexed


def _bullet_list(items: Sequence[Any], css: str = "module-depth-list") -> str:
    return f'<ul class="{_e(css)}">' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul>"


def _definition(label: str, value: Any) -> str:
    return f"<div><dt>{_e(label)}</dt><dd>{_e(value)}</dd></div>"


def _safe_url(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RendererContractError(f"{path}: expected non-empty URL")
    value = value.strip()
    if any(ord(character) < 32 for character in value):
        raise RendererContractError(f"{path}: control character in URL")
    parsed = urlsplit(value)
    if parsed.scheme not in ("", "http", "https") or (not parsed.scheme and value.startswith("//")):
        raise RendererContractError(f"{path}: unsafe URL scheme")
    return value


def _url(urls: Mapping[str, Any], key: str) -> str:
    return _safe_url(_mapping(urls, "urls").get(key), f"urls.{key}")


def _external_attrs(url: str) -> str:
    return ' target="_blank" rel="noopener noreferrer"' if urlsplit(url).scheme in ("http", "https") else ""


def _link(href: str, label: str, css: str = "btn secondary", *, current: bool = False) -> str:
    current_attr = ' aria-current="page"' if current else ""
    return f'<a class="{_e(css)}" href="{_e(href)}"{_external_attrs(href)}{current_attr}>{_e(label)}</a>'


def _module_attrs(module: Mapping[str, Any], locale: str, audience: str, resource: str) -> str:
    return (
        f'data-module-id="{_e(module["moduleId"])}" '
        f'data-module-order="{module["order"]}" data-module-resource="{resource}" '
        f'data-locale="{locale}" data-audience="{audience}"'
    )


def _depth_attr(depth: Mapping[str, Any] | None) -> str:
    return ' data-editorial-depth="nivel-0-editorial-depth-v1"' if depth is not None else ""


def _sibling_nav(current: str, urls: Mapping[str, Any], labels: Mapping[str, Any]) -> str:
    links = [
        _link(_url(urls, key), labels[key], "btn secondary", current=key == current)
        for key in RESOURCE_KEYS
    ]
    links.append(_link(_url(urls, "resources"), labels["resources"], "text-link"))
    return (
        f'<nav class="actions" data-module-siblings aria-label="{_e(labels["module_resources"])}">'
        + "".join(links)
        + "</nav>"
    )


def _next_step(current: str, default_next: str, urls: Mapping[str, Any], labels: Mapping[str, Any]) -> str:
    urls = _mapping(urls, "urls")
    custom_next = urls.get("next") if current == "prompts" else None
    if custom_next is not None:
        href = _safe_url(custom_next, "urls.next")
        raw_label = urls.get("next_label", labels[default_next])
        if not isinstance(raw_label, str) or not raw_label.strip():
            raise RendererContractError("urls.next_label: expected non-empty text")
        destination_label = raw_label.strip()
        destination_key = "next"
    else:
        href = _url(urls, default_next)
        destination_label = labels[default_next]
        destination_key = default_next
    cta = f'{labels["open_next"]} {destination_label}'
    return (
        f'<section class="playbook-close" id="resource-next-step" data-resource-next="{_e(destination_key)}">'
        f'<span class="eyebrow">{_e(labels["next_step"])}</span>'
        f'<h2>{_e(destination_label)}</h2>'
        f'<p>{_e(labels["resource_handoff"])}</p>'
        f'<div class="actions">{_link(href, cta, "btn")}</div>'
        f'<small>{_e(labels[current])} → {_e(destination_label)}</small>'
        "</section>"
    )


def _pdf_page_url(pdf_url: str, page: int) -> str:
    parsed = urlsplit(pdf_url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, f"page={page}&view=FitH"))


def _evidence_attr(mapping: Mapping[str, Any], path: str) -> str:
    evidence_ids = _sequence(mapping.get("evidenceIds"), f"{path}.evidenceIds", minimum=1)
    values = [_stable_id(value, f"{path}.evidenceIds[{index}]") for index, value in enumerate(evidence_ids)]
    return _e(" ".join(values))


def render_masterclass(
    payload: Mapping[str, Any],
    locale: str,
    audience: str,
    module: Mapping[str, Any],
    urls: Mapping[str, Any],
    *,
    depth: Mapping[str, Any] | None = None,
) -> str:
    """Render the local PDF as the primary surface plus an HTML moment guide."""

    labels, module = _context(locale, audience, module)
    resource = _resource(payload, "masterclass")
    title = _text(resource, "title", "masterclass")
    lede = _text(resource, "lede", "masterclass")
    raw_guide_contract = resource.get("accessibleGuide")
    if raw_guide_contract is None:
        guide_contract: Mapping[str, Any] = {}
        pdf_tagged = _mapping(urls, "urls").get("pdf_tagged")
        if not isinstance(pdf_tagged, bool):
            raise RendererContractError("urls.pdf_tagged: required when accessibleGuide is absent")
        warning = labels["pdf_access_warning"]
        # The legacy payload repeats the PDF limitation inside its lede. Keep
        # the first two editorial sentences in the hero; the governed toolbar
        # carries the accessibility notice once, beside the document.
        lede_sentences = re.split(r"(?<=[.!?])\s+", lede)
        display_lede = " ".join(lede_sentences[:2]).strip()
        source_note = (
            f'<details class="masterclass-source-note"><summary>{_e(labels["document_note"])}</summary>'
            f'<p>{_e(lede)}</p></details>'
        )
    else:
        guide_contract = _mapping(raw_guide_contract, "masterclass.accessibleGuide")
        warning = _text(guide_contract, "warning", "masterclass.accessibleGuide")
        if not isinstance(guide_contract.get("pdfTagged"), bool):
            raise RendererContractError("masterclass.accessibleGuide.pdfTagged: expected boolean")
        pdf_tagged = guide_contract["pdfTagged"]
        display_lede = lede
        source_note = ""
    moments = _sequence(resource.get("moments"), "masterclass.moments", minimum=1)
    depth_resource = _depth_resource(depth, "masterclass")
    depth_moments: dict[str, Mapping[str, Any]] = {}
    depth_phases: Sequence[Any] = ()
    phase_number_by_id: dict[str, int] = {}
    phase_label_by_id: dict[str, str] = {}
    if depth_resource is not None:
        depth_moments = _by_id(_sequence(depth_resource.get("moments"), "depth.masterclass.moments", minimum=1), "depth.masterclass.moments")
        depth_phases = _sequence(depth_resource.get("phases"), "depth.masterclass.phases", minimum=3)
        for phase_number, raw_phase in enumerate(depth_phases, 1):
            phase = _mapping(raw_phase, f"depth.masterclass.phases[{phase_number - 1}]")
            phase_id = _stable_id(phase.get("id"), f"depth.masterclass.phases[{phase_number - 1}].id")
            phase_number_by_id[phase_id] = phase_number
            phase_label_by_id[phase_id] = _text(phase, "label", f"depth.masterclass.phases[{phase_number - 1}]")

    pdf_url = _url(urls, "pdf")
    pdf_sha256 = _mapping(urls, "urls").get("pdf_sha256")
    if not isinstance(pdf_sha256, str) or not _SHA256_RE.fullmatch(pdf_sha256):
        raise RendererContractError("urls.pdf_sha256: expected lowercase SHA-256")

    normalized: list[Mapping[str, Any]] = []
    base_total = 0
    extended_total = 0
    timing_contracts: list[bool] = []
    pages: list[int] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(moments, 1):
        moment = _mapping(raw, f"masterclass.moments[{index - 1}]")
        moment_id = _stable_id(moment.get("id"), f"masterclass.moments[{index - 1}].id")
        if moment_id in seen_ids:
            raise RendererContractError(f"masterclass.moments: duplicate id {moment_id}")
        seen_ids.add(moment_id)
        _text(moment, "title", f"masterclass.moments[{index - 1}]")
        _text(moment, "body", f"masterclass.moments[{index - 1}]")
        has_base = "baseMinutes" in moment
        has_extended = "extendedMinutes" in moment
        if has_base != has_extended:
            raise RendererContractError(
                f"masterclass.moments[{index - 1}]: baseMinutes and extendedMinutes must appear together"
            )
        if has_base:
            base = _integer(moment, "baseMinutes", f"masterclass.moments[{index - 1}]", minimum=1)
            extended = _integer(moment, "extendedMinutes", f"masterclass.moments[{index - 1}]", minimum=0)
            base_total += base
            extended_total += base + extended
        timing_contracts.append(has_base)
        page = _integer(moment, "pdfPage", f"masterclass.moments[{index - 1}]", minimum=1)
        _evidence_attr(moment, f"masterclass.moments[{index - 1}]")
        pages.append(page)
        normalized.append(moment)

    if any(timing_contracts) and not all(timing_contracts):
        raise RendererContractError("masterclass.moments: timing contract must be complete or absent")
    timing_declared = all(timing_contracts)

    count = len(normalized)
    page_count = max(pages)
    outline_buttons: list[str] = []
    outline_button_by_id: dict[str, str] = {}
    slide_markup: list[str] = []
    for index, moment in enumerate(normalized, 1):
        moment_title = _text(moment, "title", f"masterclass.moments[{index - 1}]")
        moment_body = _text(moment, "body", f"masterclass.moments[{index - 1}]")
        depth_moment = depth_moments.get(moment["id"])
        phase_number = 1
        phase_label = labels["moments"]
        depth_markup = ""
        if depth_moment is not None:
            moment_body = _text(depth_moment, "explanation", f"depth.masterclass.moments[{index - 1}]")
            phase_id = _stable_id(depth_moment.get("phase"), f"depth.masterclass.moments[{index - 1}].phase")
            phase_number = phase_number_by_id[phase_id]
            phase_label = phase_label_by_id[phase_id]
            key_points = _sequence(depth_moment.get("key_points"), f"depth.masterclass.moments[{index - 1}].key_points", minimum=2)
            depth_markup = (
                f'<details class="module-depth-disclosure masterclass-depth"><summary><strong>{_e(labels["deepen_content"])}</strong>'
                f'<span>{_e(phase_label)}</span></summary><div class="module-depth-grid">'
                f'<section><h3>{_e(labels["key_points"])}</h3>{_bullet_list(key_points)}</section>'
                f'<dl>{_definition(labels["application"], _text(depth_moment, "application", "depth.moment"))}'
                f'{_definition(labels["check_question"], _text(depth_moment, "check_question", "depth.moment"))}'
                f'{_definition(labels["micro_practice"], _text(depth_moment, "micro_practice", "depth.moment"))}'
                f'{_definition(labels["takeaway"], _text(depth_moment, "takeaway", "depth.moment"))}'
                f'{_definition(labels["handoff"], _text(depth_moment, "handoff", "depth.moment"))}</dl>'
                f'</div></details>'
            )
        base = moment.get("baseMinutes")
        extended = moment.get("extendedMinutes")
        page = moment["pdfPage"]
        pdf_page_label = f'{labels["page"]} {page} · PDF'
        outline_button = (
            f'<button type="button" data-slide="{index - 1}" aria-current="{"step" if index == 1 else "false"}">'
            f'<span>{index:02d}</span><strong>{_e(moment_title)}</strong></button>'
        )
        outline_buttons.append(outline_button)
        outline_button_by_id[moment["id"]] = outline_button
        extended_markup = (
            f'<aside class="extended"><strong>+{extended} min</strong> {_e(labels["deepen"])}</aside>'
            if extended
            else ""
        )
        kicker_time = f" · {base} min" if base is not None else ""
        slide_markup.append(
            f'<section class="slide{" active" if index == 1 else ""}" id="slide-{index}" aria-labelledby="slide-title-{index}" '
            f'data-phase="{phase_number}" data-moment-id="{_e(moment["id"])}" data-evidence-ids="{_evidence_attr(moment, f"masterclass.moments[{index - 1}]")}">'
            f'<header class="slide-kicker"><span class="eyebrow">{_e(labels["moment"])} {index:02d}{kicker_time}</span>'
            f'<span>{index:02d} / {count:02d}</span></header>'
            f'<h2 class="h1" id="slide-title-{index}" tabindex="-1">{_e(moment_title)}</h2>'
            f'<p class="lead">{_e(moment_body)}</p>{extended_markup}{depth_markup}'
            f'<div class="slide-actions">{_link(_pdf_page_url(pdf_url, page), pdf_page_label, "btn secondary")}</div>'
            f'<div class="slide-foot"><span>{_e(module["title"])}</span><span>{_e(labels["page"])} {page}</span></div>'
            "</section>"
        )

    if depth_phases:
        phase_groups: list[str] = []
        for phase_number, raw_phase in enumerate(depth_phases, 1):
            phase = _mapping(raw_phase, "depth.phase")
            phase_groups.append(
                f'<section class="outline-group"><h3>{phase_number:02d} · {_e(_text(phase, "label", "depth.phase"))}</h3>'
                f'<p>{_e(_text(phase, "purpose", "depth.phase"))}</p>'
                + "".join(outline_button_by_id[moment_id] for moment_id in phase["moment_ids"])
                + "</section>"
            )
        outline_markup = "".join(phase_groups)
        initial_phase_label = _text(_mapping(depth_phases[0], "depth.phase"), "label", "depth.phase")
    else:
        outline_markup = f'<section class="outline-group"><h3>01 · {_e(labels["moments"])}</h3>{"".join(outline_buttons)}</section>'
        initial_phase_label = labels["moments"]
    sibling_nav = _sibling_nav("masterclass", urls, labels)
    pdf_object_url = _pdf_page_url(pdf_url, 1)
    tagged = "unknown" if pdf_tagged is None else ("true" if pdf_tagged else "false")
    guide_facts = (
        f'<dl class="masterclass-facts"><div><dt>{_e(labels["base_route"])}</dt><dd>{base_total} min</dd></div>'
        f'<div><dt>{_e(labels["extended_route"])}</dt><dd>{extended_total} min</dd></div></dl>'
        if timing_declared
        else f'<dl class="masterclass-facts"><div><dt>{_e(labels["moments"])}</dt><dd>{count}</dd></div>'
        f'<div><dt>{_e(labels["base_route"])}</dt><dd>{_e(labels["duration_not_declared"])}</dd></div></dl>'
    )
    mode_controls = (
        f'<div class="deck-mode-group" role="group" aria-label="{_e(labels["extended_route"])}">'
        f'<button class="deck-mode" type="button" data-mode="base" data-mode-minutes="{base_total}" aria-pressed="true"><strong>{base_total}</strong><span>min</span></button>'
        f'<button class="deck-mode" type="button" data-mode="extended" data-mode-minutes="{extended_total}" aria-pressed="false"><strong>{extended_total}</strong><span>min</span></button></div>'
        f'<span class="sr-only" data-mode-label>{base_total} min</span>'
        if timing_declared
        else f'<div class="deck-mode-group" aria-label="{_e(labels["adaptive_route"])}">'
        f'<span class="deck-mode-static"><strong>{count}</strong><span>{_e(labels["moments"])}</span></span></div>'
    )
    next_step = _next_step("masterclass", "workbook", urls, labels)
    return (
        f'<main id="main" class="masterclass-page" {_module_attrs(module, locale, audience, "masterclass")}{_depth_attr(depth)}> '
        f'<section class="official-masterclass" id="masterclass-inicio"><div class="shell">'
        f'<header class="official-masterclass-head"><div><span class="eyebrow">{_e(labels["module"])} {module["order"]:02d} · {_e(module["title"])}</span>'
        f'<h1>{_e(title)}</h1><p class="lead">{_e(display_lede)}</p></div>'
        f'<dl class="official-masterclass-facts"><div><dt>PDF</dt><dd>{page_count} · {_e(labels["moments"])}</dd></div>'
        f'<div><dt>SHA-256</dt><dd><code>{pdf_sha256[:12]}…</code></dd></div></dl></header>'
        f'<div class="official-pdf-card" id="masterclass-pdf" data-official-masterclass data-official-masterclass-sha256="{pdf_sha256}">'
        f'<div class="official-pdf-toolbar"><div><h2 tabindex="-1">{_e(labels["pdf_label"])}</h2><span>{_e(warning)}</span></div>'
        f'<div class="actions">{_link(pdf_url, labels["open_pdf"], "btn secondary")} '
        f'<a class="btn" href="{_e(pdf_url)}" download>{_e(labels["download_pdf"])} ↓</a></div></div>'
        f'<object class="official-pdf-object" data="{_e(pdf_object_url)}" type="application/pdf" aria-label="{_e(labels["pdf_label"])}" title="{_e(labels["pdf_label"])}">'
        f'<div class="official-pdf-fallback"><p>{_e(labels["pdf_fallback"])}</p>{_link(pdf_url, labels["open_pdf"], "btn")}</div>'
        f'</object></div><div class="module-resource-strip" data-pdf-tagged="{tagged}">{sibling_nav}</div></div></section>'
        f'<section class="masterclass-player" id="masterclass-guia"><div class="shell">'
        f'<header class="masterclass-player-head"><div><span class="eyebrow">{_e(labels["accessible_guide"])}</span>'
        f'<h2>{_e(labels["moments"])}</h2><p class="lead">{_e(labels["guide_lead"])}</p></div>{guide_facts}</header>'
        f'{source_note}<div class="deck"><details class="outline" open><summary><span>{_e(labels["moments"])}</span>'
        f'<strong data-outline-count>01 / {count:02d}</strong></summary><div class="outline-list">'
        f'{outline_markup}'
        f'</div></details><div class="stage"><div class="slide-wrap">{"".join(slide_markup)}</div>'
        f'<nav class="deck-controls" aria-label="{_e(labels["progress"])}">'
        f'<button class="deck-nav deck-prev" type="button" data-prev aria-label="{_e(labels["previous"])}">{ui_icon("back")}<span>{_e(labels["previous"])}</span></button>'
        f'<div class="deck-progress"><div class="progress" role="progressbar" aria-label="{_e(labels["progress"])}" aria-valuemin="1" aria-valuemax="{count}" aria-valuenow="1"><span></span></div>'
        f'<div><strong data-count aria-live="polite">1 / {count}</strong><span data-phase-current>{_e(initial_phase_label)}</span></div></div>'
        f'<div class="deck-tools">{mode_controls}'
        f'<button class="deck-nav deck-next" type="button" data-next aria-label="{_e(labels["next"])}"><span>{_e(labels["next"])}</span>{ui_icon("arrow")}</button>'
        f'</div></nav></div></div>{next_step}</div></section></main>'
    )


def render_workbook(
    payload: Mapping[str, Any],
    locale: str,
    audience: str,
    module: Mapping[str, Any],
    urls: Mapping[str, Any],
    *,
    depth: Mapping[str, Any] | None = None,
    artifact_labels: Mapping[str, str] | None = None,
) -> str:
    """Render exactly three workbook routes with progressive tabs."""

    labels, module = _context(locale, audience, module)
    resource = _resource(payload, "workbook")
    title = _text(resource, "title", "workbook")
    lede = _text(resource, "lede", "workbook")
    routes = _sequence(resource.get("routes"), "workbook.routes")
    depth_resource = _depth_resource(depth, "workbook")
    depth_routes: dict[str, Mapping[str, Any]] = {}
    if depth_resource is not None:
        depth_routes = _by_id(_sequence(depth_resource.get("routes"), "depth.workbook.routes", minimum=3), "depth.workbook.routes")
    if len(routes) != 3:
        raise RendererContractError("workbook.routes: expected exactly three routes")
    panel_ids = ("sheet-session", "sheet-depth", "sheet-consolidation")
    stage_ids = ("in-class", "deepening", "consolidation")
    stage_labels = labels["workbook_stages"]
    if not isinstance(stage_labels, tuple) or len(stage_labels) != 3:
        raise RendererContractError("workbook stages: expected exactly three localized labels")
    seen_ids: set[str] = set()
    normalized: list[Mapping[str, Any]] = []
    for route_index, raw in enumerate(routes):
        route = _mapping(raw, f"workbook.routes[{route_index}]")
        route_id = _stable_id(route.get("id"), f"workbook.routes[{route_index}].id")
        if route_id in seen_ids:
            raise RendererContractError(f"workbook.routes: duplicate id {route_id}")
        seen_ids.add(route_id)
        _text(route, "title", f"workbook.routes[{route_index}]")
        _text(route, "purpose", f"workbook.routes[{route_index}]")
        steps = _sequence(route.get("steps"), f"workbook.routes[{route_index}].steps", minimum=1)
        step_ids: set[str] = set()
        for step_index, raw_step in enumerate(steps):
            step = _mapping(raw_step, f"workbook.routes[{route_index}].steps[{step_index}]")
            step_id = _stable_id(step.get("id"), f"workbook.routes[{route_index}].steps[{step_index}].id")
            if step_id in step_ids:
                raise RendererContractError(f"workbook route {route_id}: duplicate step id {step_id}")
            step_ids.add(step_id)
            _text(step, "instruction", f"workbook.routes[{route_index}].steps[{step_index}]")
            _evidence_attr(step, f"workbook.routes[{route_index}].steps[{step_index}]")
        normalized.append(route)

    guide_contract = labels["workbook_guide_steps"]
    if not isinstance(guide_contract, tuple) or len(guide_contract) != 5:
        raise RendererContractError("workbook guide: expected exactly five localized milestones")
    guide_items: list[str] = []
    for index, (milestone_title, milestone_body) in enumerate(guide_contract, 1):
        stage_attr = f' data-workbook-stage="{stage_ids[index - 3]}"' if index >= 3 else ""
        guide_items.append(
            f'<li{stage_attr}><span>{index:02d}</span><p><strong>{_e(milestone_title)}</strong>'
            f'<small>{_e(milestone_body)}</small></p></li>'
        )
    guide_steps = "".join(guide_items)
    tabs = "".join(
        f'<button class="tab" type="button" role="tab" tabindex="{0 if index == 1 else -1}" '
        f'aria-selected="{"true" if index == 1 else "false"}" aria-controls="{panel_ids[index - 1]}" '
        f'data-sheet="{panel_ids[index - 1]}" data-workbook-stage="{stage_ids[index - 1]}">'
        f'<span class="workbook-stage-number" aria-hidden="true">{index:02d}</span>'
        f'<span class="workbook-stage-label">{_e(stage_labels[index - 1])}</span></button>'
        for index, _route in enumerate(normalized, 1)
    )
    panels: list[str] = []
    for route_index, (route, panel_id) in enumerate(zip(normalized, panel_ids), 1):
        depth_route = depth_routes.get(route["id"])
        route_title = _text(depth_route, "title", "depth.workbook.route") if depth_route else route["title"]
        route_purpose = _text(depth_route, "brief", "depth.workbook.route") if depth_route else route["purpose"]
        steps_markup: list[str] = []
        depth_steps = _by_id(_sequence(depth_route.get("steps"), "depth.workbook.route.steps", minimum=1), "depth.workbook.route.steps") if depth_route else {}
        for step_index, step in enumerate(route["steps"], 1):
            path = f"workbook.routes[{route_index - 1}].steps[{step_index - 1}]"
            instruction = _text(step, "instruction", path)
            step_title = f'{labels["step"]} {step_index:02d}'
            depth_step = depth_steps.get(step["id"])
            depth_markup = ""
            if depth_step is not None:
                step_title = _text(depth_step, "title", "depth.workbook.step")
                instruction = _text(depth_step, "brief", "depth.workbook.step")
                prompt_href = f'{_url(urls, "prompts")}#{_stable_id(depth_step.get("prompt_ref"), "depth.workbook.step.prompt_ref")}'
                depth_markup = (
                    f'<details class="module-depth-disclosure workbook-step-depth"><summary><strong>{_e(labels["deepen_content"])}</strong>'
                    f'<span>{_e(labels["criteria"])}</span></summary><div class="module-depth-grid">'
                    f'<section><h4>{_e(labels["actions"])}</h4>{_bullet_list(_sequence(depth_step.get("actions"), "depth.workbook.step.actions", minimum=2))}'
                    f'<h4>{_e(labels["criteria"])}</h4>{_bullet_list(_sequence(depth_step.get("criteria"), "depth.workbook.step.criteria", minimum=2))}</section>'
                    f'<dl>{_definition(labels["produces"], _text(depth_step, "deliverable", "depth.workbook.step"))}'
                    f'{_definition(labels["example"], _text(depth_step, "example", "depth.workbook.step"))}'
                    f'{_definition(labels["watch_out"], _text(depth_step, "watch_out", "depth.workbook.step"))}'
                    f'{_definition(labels["reflection"], _text(depth_step, "reflection", "depth.workbook.step"))}'
                    f'{_definition(labels["connection"], _text(depth_step, "next_connection", "depth.workbook.step"))}</dl>'
                    f'<a class="text-link" href="{_e(prompt_href)}">{_e(labels["prompts"])} · {_e(depth_step["prompt_ref"])} →</a>'
                    f'</div></details>'
                )
            textarea_label = f'{labels["your_evidence"]} · {labels["route"]} {route_index} · {labels["step"]} {step_index}'
            steps_markup.append(
                f'<article class="card step" id="{_e(step["id"])}" data-evidence-ids="{_evidence_attr(step, path)}">'
                f'<span class="step-num">{step_index}</span><div><h3 class="h3">{_e(step_title)}</h3>'
                f'<p>{_e(instruction)}</p>{depth_markup}</div><label class="field"><strong>{_e(labels["your_evidence"])}</strong>'
                f'<textarea aria-label="{_e(textarea_label)}"></textarea></label></article>'
            )
        panels.append(
            f'<section class="sheet" id="{panel_id}" role="tabpanel" data-route-id="{_e(route["id"])}" '
            f'data-workbook-stage="{stage_ids[route_index - 1]}">'
            f'<div class="section-head"><span class="eyebrow">{route_index:02d} · {_e(stage_labels[route_index - 1])}</span>'
            f'<h2 class="h2">{_e(route_title)}</h2><p class="lead">{_e(route_purpose)}</p></div>'
            f'<div class="step-list">{"".join(steps_markup)}</div></section>'
        )

    prep_cards = "".join(
        f'<article class="prep-card"><span>{index:02d}</span><h3>{_e(label)}</h3><p>{_e(module[key])}</p></article>'
        for index, (key, label) in enumerate(
            (("challenge", labels["challenge"]), ("practice", labels["practice"]), ("evidence", labels["evidence"])), 1
        )
    )
    orientation_markup = ""
    preparation_prompts_markup = ""
    consolidation_markup = ""
    if depth_resource is not None:
        orientation = _mapping(depth_resource.get("orientation"), "depth.workbook.orientation")
        orientation_inputs = _sequence(orientation.get("inputs"), "depth.workbook.orientation.inputs", minimum=2)
        case_fields = (
            (labels["case_label"], _text(orientation, "use_case", "depth.workbook.orientation"), "case"),
            (labels["result_label"], module["promise"], "result"),
            (labels["success_label"], module["evidence"], "evidence"),
        )
        case_inputs = "".join(
            f'<label class="field"><strong>{_e(label)}</strong>'
            f'<textarea rows="4" autocomplete="off" data-ephemeral-input="{_e(key)}" placeholder="{_e(placeholder)}"></textarea>'
            f'<small>{_e(labels["ephemeral_note"])}</small></label>'
            for label, placeholder, key in case_fields
        )
        orientation_markup = (
            f'<section class="module-depth-orientation" id="workbook-orientation"><div class="section-head">'
            f'<span class="eyebrow">{_e(labels["orientation"])}</span><h2 class="h2">{_e(_text(orientation, "title", "depth.workbook.orientation"))}</h2>'
            f'<p class="lead">{_e(_text(orientation, "body", "depth.workbook.orientation"))}</p></div>'
            f'<div class="module-depth-grid"><dl>{_definition(labels["use_case"], _text(orientation, "use_case", "depth.workbook.orientation"))}'
            f'{_definition(labels["ready_when"], _text(orientation, "ready_when", "depth.workbook.orientation"))}</dl>'
            f'<section><h3>{_e(labels["inputs"])}</h3>{_bullet_list(orientation_inputs)}</section></div></section>'
            f'<section class="workbook-case-intake" id="workbook-case" aria-labelledby="workbook-case-title">'
            f'<div class="section-head"><span class="eyebrow">{_e(labels["case_intake"])}</span>'
            f'<h2 class="h2" id="workbook-case-title">{_e(labels["case_intake"])}</h2>'
            f'<p class="lead">{_e(labels["case_intake_lead"])}</p></div>'
            f'<div class="workbook-case-grid">{case_inputs}</div></section>'
        )
        prep_cards = (
            f'<article class="prep-card"><span>01</span><h3>{_e(labels["prerequisites"])}</h3>'
            f'{_bullet_list((_text(orientation, "ready_when", "depth.workbook.orientation"),))}</article>'
            f'<article class="prep-card"><span>02</span><h3>{_e(labels["inputs"])}</h3>{_bullet_list(orientation_inputs)}</article>'
            f'<article class="prep-card"><span>03</span><h3>{_e(labels["limits"])}</h3>'
            f'{_bullet_list(labels["workbook_limits"])}</article>'
        )
        if not isinstance(artifact_labels, Mapping) or not artifact_labels:
            raise RendererContractError("workbook.artifactLabels: governed localized labels are required")
        normalized_artifact_labels: dict[str, str] = {}
        for key, value in artifact_labels.items():
            if not isinstance(key, str) or not key.strip() or not isinstance(value, str) or not value.strip():
                raise RendererContractError("workbook.artifactLabels: expected non-empty text pairs")
            normalized_artifact_labels[key] = value.strip()
        prompt_library = _resource(module, "promptLibrary")
        base_prompts = _by_id(_sequence(prompt_library.get("prompts"), "module.promptLibrary.prompts", minimum=1), "module.promptLibrary.prompts")
        prompt_cards: list[str] = []
        for prompt_index, raw_prompt in enumerate(_sequence(depth_resource.get("preparation_prompts"), "depth.workbook.preparation_prompts", minimum=3), 1):
            prompt = _mapping(raw_prompt, f"depth.workbook.preparation_prompts[{prompt_index - 1}]")
            prompt_id = f'{module["moduleId"]}-{_stable_id(prompt.get("id"), "depth.workbook.preparation_prompt.id")}'
            library_ref = _stable_id(prompt.get("library_ref"), "depth.workbook.preparation_prompt.library_ref")
            library_prompt = base_prompts.get(library_ref)
            if library_prompt is None:
                raise RendererContractError(f"depth.workbook.preparation_prompt.library_ref: unknown prompt {library_ref}")
            receive_ref = _text(library_prompt, "receive", "module.promptLibrary.prompt")
            receive_label = normalized_artifact_labels.get(receive_ref)
            if receive_label is None and receive_ref.endswith("-output"):
                producer = base_prompts.get(receive_ref[:-7])
                if producer is not None:
                    receive_label = _prompt_artifact_label(producer, "module.promptLibrary.prompt")
            if receive_label is None:
                raise RendererContractError(
                    f"workbook.artifactLabels: missing governed localized artifact label for {receive_ref}"
                )
            reference_href = f'{_url(urls, "prompts")}#{library_ref}'
            prompt_cards.append(
                f'<article class="card module-depth-prompt"><span class="eyebrow">{prompt_index:02d}</span>'
                f'<h3>{_e(_text(prompt, "title", "depth.workbook.preparation_prompt"))}</h3>'
                f'<p>{_e(_text(prompt, "purpose", "depth.workbook.preparation_prompt"))}</p>'
                f'<dl class="workbook-prompt-flow"><div><dt>{_e(labels["receives"])}</dt><dd>{_e(receive_label)}</dd></div>'
                f'<div><dt>{_e(labels["produces"])}</dt><dd>{_e(_text(prompt, "produces", "depth.workbook.preparation_prompt"))}</dd></div></dl>'
                f'<pre id="{_e(prompt_id)}" tabindex="0">{_e(_text(prompt, "prompt", "depth.workbook.preparation_prompt"))}</pre>'
                f'<footer><a class="text-link" data-preparation-reference href="{_e(reference_href)}">'
                f'{_e(labels["reference"])} · {_e(library_ref)} →</a>'
                f'<button class="copy" type="button" data-copy="{_e(prompt_id)}">{_e(labels["copy"])}</button></footer></article>'
            )
        preparation_prompts_markup = (
            f'<section class="module-depth-prompts" id="workbook-preparation-prompts"><div class="section-head">'
            f'<span class="eyebrow">{_e(labels["preparation_prompts"])}</span><h2 class="h2">{_e(labels["preparation_prompts"])}</h2></div>'
            f'<details class="module-depth-disclosure module-depth-preparation" open><summary><strong>{_e(labels["deepen_content"])}</strong>'
            f'<span>3 · {_e(labels["preparation_prompts"])}</span></summary>'
            f'<div class="module-depth-card-grid">{"".join(prompt_cards)}</div></details></section>'
        )
        raw_rubric = _sequence(depth_resource.get("rubric"), "depth.workbook.rubric", minimum=3)
        if len(raw_rubric) != 3:
            raise RendererContractError("depth.workbook.rubric: expected exactly three levels")
        rubric_items: list[Mapping[str, Any]] = []
        for expected_level, raw_item in enumerate(raw_rubric, 1):
            item = _mapping(raw_item, f"depth.workbook.rubric[{expected_level - 1}]")
            if item.get("level") != expected_level:
                raise RendererContractError("depth.workbook.rubric: levels must be ordered 1, 2, 3")
            _text(item, "label", f"depth.workbook.rubric[{expected_level - 1}]")
            _text(item, "description", f"depth.workbook.rubric[{expected_level - 1}]")
            rubric_items.append(item)
        rubric_cards = "".join(
            f'<article class="card"><span class="step-num">{item["level"]}</span>'
            f'<h3>{_e(item["label"])}</h3><p>{_e(item["description"])}</p></article>'
            for item in rubric_items
        )
        rubric_markup = (
            f'<section class="module-depth-rubric" id="workbook-rubric"><div class="section-head"><span class="eyebrow">{_e(labels["rubric"])}</span>'
            f'<h2 class="h2">{_e(labels["rubric"])}</h2></div><div class="module-depth-card-grid">{rubric_cards}</div></section>'
        )
        transfer = _mapping(depth_resource.get("transfer_challenge"), "depth.workbook.transfer_challenge")
        transfer_evidence = _text(transfer, "evidence", "depth.workbook.transfer")
        review_after = _text(transfer, "review_after", "depth.workbook.transfer")
        transfer_depth_markup = (
            f'<article class="module-depth-transfer"><h3>{_e(_text(transfer, "title", "depth.workbook.transfer"))}</h3>'
            f'<p>{_e(_text(transfer, "brief", "depth.workbook.transfer"))}</p>'
            f'{_bullet_list(_sequence(transfer.get("actions"), "depth.workbook.transfer.actions", minimum=2))}'
            f'<dl>{_definition(labels["evidence"], transfer_evidence)}'
            f'{_definition(labels["review_after"], review_after)}</dl></article>'
        )
        highest_level = rubric_items[-1]
        criterion_markup = (
            f'<aside class="workbook-consolidation-gate" data-consolidation-gate '
            f'aria-labelledby="workbook-consolidation-criterion">'
            f'<span class="eyebrow">{_e(labels["consolidation_criterion"])}</span>'
            f'<h3 id="workbook-consolidation-criterion">{_e(highest_level["label"])}</h3>'
            f'<p>{_e(highest_level["description"])}</p>'
            f'<dl>{_definition(labels["expected_evidence"], transfer_evidence)}'
            f'{_definition(labels["review_after"], review_after)}</dl></aside>'
        )
        consolidation_markup = (
            f'<section class="workbook-consolidation" id="transferencia">'
            f'<div class="section-head"><span class="eyebrow">{_e(labels["transfer"])}</span>'
            f'<h2 class="h2">{_e(module["transfer"])}</h2><p class="lead">{_e(module["promise"])}</p></div>'
            f'{criterion_markup}{transfer_depth_markup}{rubric_markup}</section>'
        )
        closing = "</section>"
        if not panels[2].endswith(closing):
            raise RendererContractError("workbook consolidation panel: invalid renderer structure")
        panels[2] = f'{panels[2][:-len(closing)]}{consolidation_markup}{closing}'

    transfer_markup = ""
    if depth_resource is None:
        transfer_markup = (
            f'<section class="workbook-routes" id="transferencia"><div class="section-head">'
            f'<span class="eyebrow">{_e(labels["transfer"])}</span><h2 class="h2">{_e(module["transfer"])}</h2>'
            f'<p class="lead">{_e(module["promise"])}</p></div></section>'
        )
    sibling_nav = _sibling_nav("workbook", urls, labels)
    return (
        f'<main id="main" class="workbook-v2" {_module_attrs(module, locale, audience, "workbook")}{_depth_attr(depth)}> '
        f'<section class="doc-hero workbook-hero" id="workbook-inicio"><div class="shell workbook-hero-grid">'
        f'<div class="workbook-hero-copy"><span class="eyebrow">{_e(labels["module"])} {module["order"]:02d} · Workbook</span>'
        f'<h1 class="h1">{_e(title)}</h1><p class="lead">{_e(lede)}</p></div>'
        f'<aside class="workbook-outcome" data-module-number="{module["order"]:02d}"><span>{_e(labels["outcome"])}</span><strong>{_e(module["evidence"])}</strong></aside>'
        f'<nav class="workbook-hero-actions" aria-label="Workbook"><a class="btn" href="#sheet-session">{_e(labels["start"])} →</a>'
        f'{_link(_url(urls, "masterclass"), labels["masterclass"], "text-link")}'
        f'<button class="print-link" type="button" onclick="window.print()">{_e(labels["print"])}</button></nav></div></section>'
        f'<div class="shell workbook-flow"><section class="workbook-guide" id="guia" aria-labelledby="workbook-guide-title">'
        f'<div class="section-head"><span class="eyebrow">00 · {_e(labels["guide"])}</span><h2 class="h2" id="workbook-guide-title">{_e(labels["guide"])}</h2>'
        f'<p class="lead">{_e(labels["guide_lead_workbook"])}</p></div><ol class="guide-steps">{guide_steps}</ol></section>{orientation_markup}{preparation_prompts_markup}'
        f'<section class="workshop-start" id="descarga"><div class="section-head"><span class="eyebrow">{_e(labels["module_resources"])}</span>'
        f'<h2 class="h2">{_e(module["title"])}</h2></div>{sibling_nav}</section>'
        f'<section class="workbook-prep" id="preparacion"><div class="section-head"><span class="eyebrow">00 · {_e(labels["preparation"])}</span>'
        f'<h2 class="h2">{_e(labels["preparation"])}</h2></div><div class="prep-grid">{prep_cards}</div></section>'
        f'<section class="workbook-sheets"><div class="section-head"><span class="eyebrow">01–03 · Workbook</span>'
        f'<h2 class="h2">{_e(lede)}</h2></div><div class="sheet-tabs" role="tablist" aria-label="Workbook">{tabs}</div>'
        f'{"".join(panels)}</section>{transfer_markup}{_next_step("workbook", "playbook", urls, labels)}</div></main>'
    )


def render_playbook(
    payload: Mapping[str, Any],
    locale: str,
    audience: str,
    module: Mapping[str, Any],
    urls: Mapping[str, Any],
    *,
    depth: Mapping[str, Any] | None = None,
) -> str:
    """Render an editorial playbook without method marks or portrait blocks."""

    labels, module = _context(locale, audience, module)
    resource = _resource(payload, "playbook")
    title = _text(resource, "title", "playbook")
    lede = _text(resource, "lede", "playbook")
    chapters = _sequence(resource.get("chapters"), "playbook.chapters", minimum=1)
    depth_resource = _depth_resource(depth, "playbook")
    depth_chapters = _by_id(_sequence(depth_resource.get("chapters"), "depth.playbook.chapters", minimum=1), "depth.playbook.chapters") if depth_resource else {}
    normalized: list[Mapping[str, Any]] = []
    seen_ids = {"intro", "close", "resource-next-step"}
    for chapter_index, raw in enumerate(chapters):
        chapter = _mapping(raw, f"playbook.chapters[{chapter_index}]")
        chapter_id = _stable_id(chapter.get("id"), f"playbook.chapters[{chapter_index}].id")
        if chapter_id in seen_ids:
            raise RendererContractError(f"playbook.chapters: duplicate or reserved id {chapter_id}")
        seen_ids.add(chapter_id)
        _text(chapter, "title", f"playbook.chapters[{chapter_index}]")
        _text(chapter, "purpose", f"playbook.chapters[{chapter_index}]")
        steps = _sequence(chapter.get("steps"), f"playbook.chapters[{chapter_index}].steps", minimum=1)
        step_ids: set[str] = set()
        for step_index, raw_step in enumerate(steps):
            step = _mapping(raw_step, f"playbook.chapters[{chapter_index}].steps[{step_index}]")
            step_id = _stable_id(step.get("id"), f"playbook.chapters[{chapter_index}].steps[{step_index}].id")
            if step_id in step_ids:
                raise RendererContractError(f"playbook chapter {chapter_id}: duplicate step id {step_id}")
            step_ids.add(step_id)
            _text(step, "instruction", f"playbook.chapters[{chapter_index}].steps[{step_index}]")
            _evidence_attr(step, f"playbook.chapters[{chapter_index}].steps[{step_index}]")
        normalized.append(chapter)

    toc_entries = [
        f'<a href="#intro"><span>00</span>{_e(labels["introduction"])}</a>'
    ] + [
        f'<a href="#{_e(chapter["id"])}"><span>{index:02d}</span>{_e(chapter["title"])}</a>'
        for index, chapter in enumerate(normalized, 1)
    ]
    if depth_resource is not None:
        toc_entries.extend(
            (
                f'<a href="#playbook-glossary"><span>{len(normalized) + 1:02d}</span>{_e(labels["glossary"])}</a>',
                f'<a href="#playbook-faq"><span>{len(normalized) + 2:02d}</span>{_e(labels["faq"])}</a>',
            )
        )
    toc_entries.append(
        f'<a href="#close"><span>{len(normalized) + (3 if depth_resource is not None else 1):02d}</span>{_e(labels["next_step"])}</a>'
    )

    intro_items = "".join(
        f'<li><strong>{_e(label)}</strong><p>{_e(module[key])}</p></li>'
        for key, label in (("challenge", labels["challenge"]), ("practice", labels["practice"]), ("evidence", labels["evidence"]))
    )
    sections: list[str] = [
        f'<section class="playbook-section" id="intro" data-playbook-section><div class="playbook-section-index"><span>00</span></div>'
        f'<div class="playbook-section-body"><span class="eyebrow">{_e(labels["introduction"])}</span>'
        f'<h2>{_e(labels["introduction"])}</h2><p class="lead">{_e(module["promise"])}</p><p>{_e(lede)}</p>'
        f'<ul>{intro_items}</ul></div></section>'
    ]
    for chapter_index, chapter in enumerate(normalized, 1):
        depth_chapter = depth_chapters.get(chapter["id"])
        if depth_chapter is None:
            steps_markup = "".join(
                f'<li id="{_e(step["id"])}" data-evidence-ids="{_evidence_attr(step, f"playbook.chapters[{chapter_index - 1}].steps[{step_index}]")}">'
                f'{_e(_text(step, "instruction", f"playbook.chapters[{chapter_index - 1}].steps[{step_index}]"))}</li>'
                for step_index, step in enumerate(chapter["steps"])
            )
            chapter_body = f'<p class="lead">{_e(chapter["purpose"])}</p><ul>{steps_markup}</ul>'
        else:
            base_step_ids = [step["id"] for step in chapter["steps"]]
            action_items = []
            for action_index, action in enumerate(_sequence(depth_chapter.get("actions"), "depth.playbook.chapter.actions", minimum=3)):
                action_id = base_step_ids[action_index] if action_index < len(base_step_ids) else f'{chapter["id"]}-action-{action_index + 1:02d}'
                action_items.append(f'<li id="{_e(action_id)}">{_e(action)}</li>')
            prompt_href = f'{_url(urls, "prompts")}#{_stable_id(depth_chapter.get("prompt_ref"), "depth.playbook.chapter.prompt_ref")}'
            chapter_body = (
                f'<p class="playbook-principle"><strong>{_e(labels["principle"])}:</strong> {_e(_text(depth_chapter, "principle", "depth.playbook.chapter"))}</p>'
                f'<p class="lead">{_e(_text(depth_chapter, "explanation", "depth.playbook.chapter"))}</p>'
                f'<aside class="module-depth-decision"><span>{_e(labels["decision"])}</span><strong>{_e(_text(depth_chapter, "decision", "depth.playbook.chapter"))}</strong></aside>'
                f'<details class="module-depth-disclosure playbook-depth"><summary><strong>{_e(labels["deepen_content"])}</strong>'
                f'<span>{_e(labels["actions"])}</span></summary><div class="module-depth-grid">'
                f'<section><h3>{_e(labels["actions"])}</h3><ol>{"".join(action_items)}</ol>'
                f'<h3>{_e(labels["checklist"])}</h3>{_bullet_list(_sequence(depth_chapter.get("checklist"), "depth.playbook.chapter.checklist", minimum=2))}</section>'
                f'<dl>{_definition(labels["rule"], _text(depth_chapter, "rule", "depth.playbook.chapter"))}'
                f'{_definition(labels["example"], _text(depth_chapter, "example", "depth.playbook.chapter"))}'
                f'{_definition(labels["antipattern"], _text(depth_chapter, "antipattern", "depth.playbook.chapter"))}'
                f'{_definition(labels["expected_evidence"], _text(depth_chapter, "expected_evidence", "depth.playbook.chapter"))}'
                f'{_definition(labels["limit"], _text(depth_chapter, "limit", "depth.playbook.chapter"))}</dl>'
                f'<a class="text-link" href="{_e(prompt_href)}">{_e(labels["prompts"])} · {_e(depth_chapter["prompt_ref"])} →</a>'
                f'</div></details>'
            )
        sections.append(
            f'<section class="playbook-section" id="{_e(chapter["id"])}" data-playbook-section>'
            f'<div class="playbook-section-index"><span>{chapter_index:02d}</span></div>'
            f'<div class="playbook-section-body"><span class="eyebrow">{_e(labels["chapter"])} {chapter_index:02d}</span>'
            f'<h2>{_e(chapter["title"])}</h2>{chapter_body}</div></section>'
        )

    depth_reference_markup = ""
    closing_checklist_markup = ""
    if depth_resource is not None:
        glossary_items = "".join(
            f'<div><dt>{_e(item["term"])}</dt><dd>{_e(item["definition"])}</dd></div>'
            for item in _sequence(depth_resource.get("glossary"), "depth.playbook.glossary", minimum=4)
        )
        faq_items = "".join(
            f'<details><summary>{_e(item["question"])}</summary><p>{_e(item["answer"])}</p></details>'
            for item in _sequence(depth_resource.get("faq"), "depth.playbook.faq", minimum=3)
        )
        depth_reference_markup = (
            f'<section class="playbook-section module-depth-reference" id="playbook-glossary" data-playbook-section>'
            f'<div class="playbook-section-index"><span>{len(normalized)+1:02d}</span></div><div class="playbook-section-body">'
            f'<span class="eyebrow">{_e(labels["glossary"])}</span><h2>{_e(labels["glossary"])}</h2><dl>{glossary_items}</dl></div></section>'
            f'<section class="playbook-section module-depth-reference" id="playbook-faq" data-playbook-section>'
            f'<div class="playbook-section-index"><span>{len(normalized)+2:02d}</span></div><div class="playbook-section-body">'
            f'<span class="eyebrow">FAQ</span><h2>{_e(labels["faq"])}</h2><div class="module-depth-faq">{faq_items}</div></div></section>'
        )
        closing_checklist_markup = (
            f'<div class="module-depth-closing"><strong>{_e(labels["checklist"])}</strong>'
            f'{_bullet_list(_sequence(depth_resource.get("closing_checklist"), "depth.playbook.closing_checklist", minimum=3))}</div>'
        )

    sibling_nav = _sibling_nav("playbook", urls, labels)
    return (
        f'<main id="main" class="playbook-v1" {_module_attrs(module, locale, audience, "playbook")}{_depth_attr(depth)}> '
        f'<section class="playbook-hero" id="playbook-inicio"><div class="shell"><div class="playbook-hero-grid">'
        f'<div class="playbook-hero-copy"><span class="eyebrow">{_e(labels["module"])} {module["order"]:02d} · Playbook</span>'
        f'<h1>{_e(title)}</h1><p class="lead">{_e(lede)}</p>'
        f'<div class="actions"><a class="btn" href="#intro">{_e(labels["start"])}{ui_icon("arrow")}</a></div>'
        f'<dl class="playbook-hero-facts"><div><dt>{_e(labels["practice"])}</dt><dd>{_e(module["practice"])}</dd></div>'
        f'<div><dt>{_e(labels["transfer"])}</dt><dd>{_e(module["transfer"])}</dd></div></dl></div>'
        f'<aside class="workbook-outcome" data-module-number="{module["order"]:02d}"><span>{_e(labels["outcome"])}</span><strong>{_e(module["evidence"])}</strong></aside>'
        f'</div><div class="module-resource-strip">{sibling_nav}</div></div></section><div class="shell playbook-layout"><details class="playbook-toc"><summary><strong>{_e(labels["full_index"])}</strong>'
        f'<span>{len(toc_entries)}</span></summary><nav aria-label="{_e(labels["full_index"])}">{"".join(toc_entries)}</nav></details>'
        f'<div class="playbook-content">{"".join(sections)}{depth_reference_markup}<section class="playbook-close" id="close">'
        f'<span class="eyebrow">{_e(labels["next_step"])}</span><h2>{_e(module["transfer"])}</h2><p>{_e(module["promise"])}</p>'
        f'{closing_checklist_markup}'
        f'<div class="actions">{_link(_url(urls, "workbook"), labels["workbook"], "btn secondary")}'
        f'{_link(_url(urls, "prompts"), labels["prompts"], "btn")}</div><small>{_e(module["title"])}</small>'
        f'</section></div></div></main>'
    )


def _prompt_lines(value: str) -> str:
    lines: list[str] = []
    for line in value.split("\n"):
        stripped = line.strip()
        kind = "body"
        if not stripped:
            kind = "empty"
        elif stripped.startswith("### "):
            kind = "subheading"
        elif stripped.startswith("## "):
            kind = "section"
        elif stripped.startswith("# "):
            kind = "heading"
        elif re.match(r"^\d+\.\s", stripped):
            kind = "step"
        elif stripped.startswith("- "):
            kind = "list"
        elif re.match(r"^[^:]{1,34}:\s", stripped):
            kind = "field"
        lines.append(f'<span class="prompt-line prompt-line-{kind}">{_e(line)}</span>')
    return "".join(lines)


def _prompt_surface(value: Any, path: str) -> str:
    if value == "chat":
        return "chat"
    if value in ("sources", "source_search"):
        return "source_search"
    raise RendererContractError(f"{path}: expected chat or sources")


def _prompt_input_contract(prompt: Mapping[str, Any], locale: str, path: str) -> list[dict[str, Any]]:
    """Normalize both legacy and v2 input shapes without mutating payloads."""

    syntax = _mapping(prompt.get("syntax"), f"{path}.syntax")
    inputs = _sequence(syntax.get("inputs"), f"{path}.syntax.inputs", minimum=1)
    normalized: list[dict[str, Any]] = []
    for index, raw_input in enumerate(inputs):
        item = _mapping(raw_input, f"{path}.syntax.inputs[{index}]")
        name = next(
            (
                item.get(candidate).strip()
                for candidate in ("name", "label", "key")
                if isinstance(item.get(candidate), str) and item.get(candidate).strip()
            ),
            None,
        )
        if name is None:
            raise RendererContractError(f"{path}.syntax.inputs[{index}]: missing name, label or key")
        description = _text(item, "description", f"{path}.syntax.inputs[{index}]")
        example = _text(item, "example", f"{path}.syntax.inputs[{index}]")
        if not isinstance(item.get("required"), bool):
            raise RendererContractError(f"{path}.syntax.inputs[{index}].required: expected boolean")
        demo_value = item.get("demoValue")
        if not isinstance(demo_value, str) or not demo_value.strip():
            demo_value = f'{PROMPT_FORMAT[locale]["synthetic"]}: {example}'
        normalized.append(
            {
                "name": name,
                "description": description,
                "example": example,
                "required": item["required"],
                "demo": demo_value.strip(),
            }
        )
    return normalized


def _prompt_parameter_contract(prompt: Mapping[str, Any], locale: str, path: str) -> list[tuple[str, str]]:
    """Localize parameter names and defaults so ES/PT never leak EN internals."""

    syntax = _mapping(prompt.get("syntax"), f"{path}.syntax")
    raw_parameters = syntax.get("parameters")
    if isinstance(raw_parameters, Mapping):
        parameters = list(raw_parameters.items())
    else:
        parameters = []
        for index, raw_parameter in enumerate(_sequence(raw_parameters, f"{path}.syntax.parameters", minimum=1)):
            parameter = _mapping(raw_parameter, f"{path}.syntax.parameters[{index}]")
            key = _text(parameter, "key", f"{path}.syntax.parameters[{index}]")
            if "default" not in parameter:
                raise RendererContractError(f"{path}.syntax.parameters[{index}].default: missing")
            parameters.append((key, parameter["default"]))
    if not parameters:
        raise RendererContractError(f"{path}.syntax.parameters: expected at least one parameter")
    normalized: list[tuple[str, str]] = []
    for key, value in parameters:
        if not isinstance(key, str) or not key.strip() or not isinstance(value, (str, int, float)) or isinstance(value, bool):
            raise RendererContractError(f"{path}.syntax.parameters: invalid parameter")
        canonical_key = key.strip().casefold()
        label = PARAMETER_KEYS[locale].get(canonical_key, key.strip().upper())
        raw_value = str(value).strip()
        localized_value = PARAMETER_VALUES[locale].get(raw_value.casefold(), raw_value.replace("-", " "))
        normalized.append((label, localized_value))
    return normalized


def _prompt_optional_clauses(prompt: Mapping[str, Any], path: str) -> list[str]:
    syntax = _mapping(prompt.get("syntax"), f"{path}.syntax")
    raw_clauses = syntax.get("optionalClauses")
    clauses: list[str] = []
    if raw_clauses is not None:
        for index, raw_clause in enumerate(_sequence(raw_clauses, f"{path}.syntax.optionalClauses")):
            clause = _mapping(raw_clause, f"{path}.syntax.optionalClauses[{index}]")
            if clause.get("removable") is not True:
                raise RendererContractError(f"{path}.syntax.optionalClauses[{index}]: must be removable")
            clauses.append(_text(clause, "text", f"{path}.syntax.optionalClauses[{index}]"))
    if not clauses and syntax.get("optionalInstruction") is True:
        template = _prompt_mode_text(prompt, "template", path)
        clauses = [item.strip() for item in re.findall(r"\[([^]]+)\]", template) if item.strip()]
    return clauses


def _prompt_input_guide(prompt: Mapping[str, Any], labels: Mapping[str, Any], locale: str, path: str) -> str:
    inputs = _prompt_input_contract(prompt, locale, path)
    items: list[str] = []
    for item in inputs:
        requirement = labels["required"] if item["required"] else labels["optional"]
        items.append(
            f'<li><code>&lt;{_e(item["name"])}&gt;</code><span><strong>{_e(item["description"])}</strong>'
            f'<small>{_e(labels["example"])}: {_e(item["example"])} · {_e(requirement)}</small></span></li>'
        )
    parameter_items = []
    for key, value in _prompt_parameter_contract(prompt, locale, path):
        parameter_items.append(f'<li><code>{_e(key)} = {_e(value)}</code></li>')
    return (
        f'<details class="prompt-input-guide"><summary>{_e(labels["inputs"])} <span>{len(items)}</span></summary>'
        f'<ul>{"".join(items)}</ul><strong>{_e(labels["parameters"])}</strong><ul>{"".join(parameter_items)}</ul></details>'
    )


def _prompt_artifact_label(prompt: Mapping[str, Any], path: str) -> str:
    value = prompt.get("produces")
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, Mapping):
        return _text(value, "label", f"{path}.produces")
    raise RendererContractError(f"{path}.produces: expected text or labeled artifact")


def _prompt_text_value(value: Any, path: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, Mapping):
        system = value.get("system")
        user = value.get("user")
        if isinstance(system, str) and system.strip() and isinstance(user, str) and user.strip():
            return f"# system\n{system.strip()}\n\n# user\n{user.strip()}"
    raise RendererContractError(f"{path}: expected prompt text or System/User pair")


def _prompt_mode_text(prompt: Mapping[str, Any], mode: str, path: str) -> str:
    direct = prompt.get(mode)
    if direct is not None:
        return _prompt_text_value(direct, f"{path}.{mode}")
    modes = _mapping(prompt.get("modes"), f"{path}.modes")
    mode_contract = _mapping(modes.get(mode), f"{path}.modes.{mode}")
    return _prompt_text_value(mode_contract.get("body"), f"{path}.modes.{mode}.body")


_DEMO_PLACEHOLDER_PATTERNS = (
    r"\s*Usa el artefacto sintético del paso anterior:\s*[^.\n]+\.\s*",
    r"\s*Use the synthetic artifact from the previous step:\s*[^.\n]+\.\s*",
    r"\s*Use o artefato sintético da etapa anterior:\s*[^.\n]+\.\s*",
    r"\s*El artefacto sintético está disponible y se identifica como demostración\.\s*\([^)]+\)\.\s*",
    r"\s*The synthetic artifact is available and identified as a demonstration\.\s*\([^)]+\)\.\s*",
    r"\s*O artefato sintético está disponível e identificado como demonstração\.\s*\([^)]+\)\.\s*",
)


def _prompt_demo_text(
    value: Any,
    contract: Mapping[str, Any] | None,
    labels: Mapping[str, Any],
    path: str,
) -> str:
    """Resolve a runnable demo without mutating the imported source payload.

    The local depth overlay may carry a concrete synthetic artifact.  When it
    does, generic "previous artifact" prose is removed and the actual data is
    inserted into the copied prompt.  This keeps the immutable import intact
    while making every rendered Demo independently executable.
    """

    text = _prompt_text_value(value, path).replace(
        "Treat demo artifacts as synthetic.", labels["synthetic_demo_rule"]
    )
    if contract is None or "demo_artifact" not in contract:
        return text
    artifact = _text(contract, "demo_artifact", "depth.prompt")
    for pattern in _DEMO_PLACEHOLDER_PATTERNS:
        text = re.sub(pattern, " ", text)
    block = f"{labels['demo_artifact']}: {artifact}"
    if "# user\n" in text:
        return text.replace("# user\n", f"# user\n{block}\n\n", 1)
    return f"{block}\n\n{text.strip()}"


def _prompt_role(prompt: Mapping[str, Any], locale: str, path: str) -> str:
    """Recover the governed role from legacy N4 instead of inventing one."""

    levels = _sequence(prompt.get("levels"), f"{path}.levels", minimum=4)
    level = _mapping(levels[3], f"{path}.levels[3]")
    value = level.get("body", level.get("template"))
    if isinstance(value, Mapping):
        system = value.get("system")
        if isinstance(system, str) and system.strip():
            return system.strip()
    if value is not None:
        text = _prompt_text_value(value, f"{path}.levels[3]")
        if text.startswith("# system\n"):
            role = text.removeprefix("# system\n").split("\n\n# user", 1)[0].strip()
            if role:
                return role
        match = re.match(r"SYSTEM:\s*(.+?)(?:\nUSER:|$)", text, re.S | re.I)
        if match and match.group(1).strip():
            return match.group(1).strip()
    return f'{PROMPT_FORMAT[locale]["role_prefix"]} {_text(prompt, "title", path).casefold()}.'


def _prompt_semantic_inputs(
    prompt: Mapping[str, Any],
    depth_prompt: Mapping[str, Any],
    locale: str,
    mode: str,
    path: str,
) -> tuple[str, str]:
    """Return compact inline data and the explicit INPUTS block."""

    fmt = PROMPT_FORMAT[locale]
    inline: list[str] = []
    block: list[str] = []
    for item in _prompt_input_contract(prompt, locale, path):
        value = (
            f'<{item["name"]} · {item["description"]} · {fmt["example"]}: {item["example"]}>'
            if mode == "template"
            else item["demo"]
        )
        inline.append(f'{item["name"]}={value}')
        block.append(f'{item["name"]} = {value}')
    if mode == "demo" and "demo_artifact" in depth_prompt:
        artifact = _text(depth_prompt, "demo_artifact", "depth.prompt")
        inline.append(f'{fmt["demo_available"]} {fmt["demo_artifact"]}={artifact}')
        block.append(f'{fmt["demo_available"]} {fmt["demo_artifact"]} = {artifact}')
    return "; ".join(inline), "\n".join(block) or fmt["none"]


def _prompt_sentence(value: str) -> str:
    value = value.strip()
    return value if value.endswith((".", "!", "?")) else f"{value}."


def _prompt_semantic_levels(
    prompt: Mapping[str, Any],
    depth_prompt: Mapping[str, Any],
    module_id: str,
    locale: str,
    audience: str,
    mode: str,
    path: str,
) -> tuple[str, str, str, str]:
    """Project N1–N4 from one governed execution contract.

    [PEDAGOGIA] Each level adds useful control: direct order, explicit
    parameters, verifiable SPEC, and reusable System/User separation.
    """

    fmt = PROMPT_FORMAT[locale]
    purpose = _text(depth_prompt, "purpose", "depth.prompt")
    when = _text(depth_prompt, "when", "depth.prompt")
    tradeoff = _text(depth_prompt, "tradeoff", "depth.prompt")
    produces = _prompt_artifact_label(prompt, path)
    role = _prompt_role(prompt, locale, path)
    workflow_items = [str(item).strip() for item in _sequence(depth_prompt.get("workflow"), "depth.prompt.workflow", minimum=3)]
    framework_items = [str(item).strip() for item in _sequence(depth_prompt.get("frameworks"), "depth.prompt.frameworks", minimum=1)]
    guardrail_items = [str(item).strip() for item in _sequence(depth_prompt.get("guardrails"), "depth.prompt.guardrails", minimum=2)]
    acceptance_items = [str(item).strip() for item in _sequence(depth_prompt.get("acceptance_criteria"), "depth.prompt.acceptance", minimum=2)]
    edge_items = [str(item).strip() for item in _sequence(depth_prompt.get("edge_cases"), "depth.prompt.edge_cases", minimum=1)]
    limit_items = [str(item).strip() for item in _sequence(depth_prompt.get("limits"), "depth.prompt.limits", minimum=1)]
    authority_items = [str(item).strip() for item in _sequence(depth_prompt.get("authority_refs"), "depth.prompt.authority_refs", minimum=1)]
    parameters = "\n".join(
        f"{key} = {value}" for key, value in _prompt_parameter_contract(prompt, locale, path)
    )
    inline_inputs, inputs = _prompt_semantic_inputs(prompt, depth_prompt, locale, mode, path)
    optionals = _prompt_optional_clauses(prompt, path)
    optional_values = [f"[{item}]" if mode == "template" else item for item in optionals]
    optional_block = f"\n\n{fmt['optional']}\n" + "\n".join(optional_values) if optional_values else ""
    workflow = "\n".join(f"{index}. {item}" for index, item in enumerate(workflow_items, 1))
    frameworks = "\n".join(f"- {item}" for item in framework_items)
    guardrails = "\n".join(f"- {item}" for item in guardrail_items)
    output = "\n".join(f"- {item}" for item in (produces, *acceptance_items))
    edges = "\n".join(f"- {item}" for item in edge_items)
    limits = "\n".join(f"- {item}" for item in limit_items)
    observable = "\n".join(f"- {item}" for item in acceptance_items)
    practices = "; ".join(item.split(" · ", 1)[0] for item in framework_items)
    order = " → ".join((workflow_items[0], workflow_items[-1]))
    optional_n1 = f"\n" + "\n".join(optional_values) if optional_values else ""

    natural = (
        f'{fmt["objective"]}: {_prompt_sentence(purpose)} {fmt["audience_scope"][audience]}\n\n'
        f'{fmt["data"]}: {_prompt_sentence(inline_inputs)}\n'
        f'{fmt["apply"]}: {_prompt_sentence(practices)}\n'
        f'{fmt["order"]}: {_prompt_sentence(order)}\n'
        f'{fmt["deliver"]}: {_prompt_sentence(f"{produces}; {acceptance_items[0]}")}\n'
        f'{fmt["limit"]}: {_prompt_sentence(guardrail_items[0])}{optional_n1}'
    )
    parameterized = (
        f'{fmt["parameters"]}\n{parameters}\n\n'
        f'{fmt["inputs"]}\n{inputs}{optional_block}\n\n'
        f'{fmt["task"]}\n{purpose}\n\n'
        f'{fmt["frameworks"]}\n{frameworks}\n\n'
        f'{fmt["workflow"]}\n{workflow}\n\n'
        f'{fmt["guardrails"]}\n{guardrails}\n{limits}\n\n'
        f'{fmt["output"]}\n{output}'
    )
    provenance_case = fmt["synthetic"] if mode == "demo" else fmt["case_data"]
    spec = (
        '# SPEC MetodologIA\nversion: 2.0\nstatus: executable\n\n'
        f'## S — {fmt["situation"]}\n'
        f'{fmt["context"]}: {when}\n'
        f'{fmt["parameters"]}\n{parameters}\n\n'
        f'{fmt["inputs"]}\n{inputs}{optional_block}\n\n'
        f'## P — {fmt["request"]}\n'
        f'{fmt["expert_role"]}: {role}\n'
        f'{fmt["deliverable"]}: {produces}\n'
        f'{fmt["scope_in"]}: {purpose}\n'
        f'{fmt["scope_out"]}: {"; ".join(limit_items)}\n\n'
        f'## E — {fmt["execution"]}\n'
        f'### {fmt["frameworks"].lstrip("# ")}\n{frameworks}\n\n'
        f'{fmt["steps"]}:\n{workflow}\n\n'
        f'### {UI[locale]["edge_cases"]}\n{edges}\n\n'
        f'## C — {fmt["criterion"]}\n'
        f'{fmt["output"]}:\n{output}\n\n'
        f'{fmt["observable"]}:\n{observable}\n\n'
        f'{fmt["dod"]}: {"; ".join(acceptance_items)}\n'
        f'{UI[locale]["tradeoff"]}: {tradeoff}\n\n'
        f'## {fmt["provenance"]}\n'
        f'- {provenance_case}\n'
        f'- {fmt["authority"]}: {", ".join(authority_items)}\n\n'
        f'## {fmt["metadata"]}\n'
        f'- module: {module_id.split("-", 2)[1]}\n'
        f'- prompt: {_stable_id(prompt.get("id"), f"{path}.id")}\n'
        f'- surface: {_prompt_surface(prompt.get("surface"), f"{path}.surface")}\n\n'
        f'{fmt["reasoning_policy"]}'
    )
    pair = (
        f'# system\n{role}\n\n'
        f'{fmt["frameworks"]}\n{frameworks}\n\n'
        f'{fmt["guardrails"]}\n{guardrails}\n{limits}\n\n'
        f'{fmt["dod"]}\n{"; ".join(acceptance_items)}\n\n'
        f'# user\n{fmt["parameters"]}\n{parameters}\n\n'
        f'{fmt["inputs"]}\n{inputs}{optional_block}\n\n'
        f'{fmt["task"]}\n{purpose}\n\n'
        f'{fmt["workflow"]}\n{workflow}\n\n'
        f'{fmt["output"]}\n{output}'
    )
    return natural, parameterized, spec, pair


def _prompt_contract_suffix(contract: Mapping[str, Any] | None, labels: Mapping[str, Any], level: int) -> str:
    if contract is None:
        return ""
    sections: list[tuple[str, Sequence[Any]]] = []
    if level >= 2:
        sections.append((labels["workflow"], _sequence(contract.get("workflow"), "depth.prompt.workflow", minimum=3)))
    if level >= 3:
        sections.extend(
            (
                (labels["frameworks"], _sequence(contract.get("frameworks"), "depth.prompt.frameworks", minimum=1)),
                (labels["guardrails"], _sequence(contract.get("guardrails"), "depth.prompt.guardrails", minimum=2)),
                (labels["edge_cases"], _sequence(contract.get("edge_cases"), "depth.prompt.edge_cases", minimum=1)),
            )
        )
    sections.append((labels["acceptance"], _sequence(contract.get("acceptance_criteria"), "depth.prompt.acceptance", minimum=2)))
    sections.append((labels["limits"], _sequence(contract.get("limits"), "depth.prompt.limits", minimum=1)))
    lines = [f"## {labels['prompt_contract']}", f"{labels['purpose']}: {_text(contract, 'purpose', 'depth.prompt')}"]
    for heading, items in sections:
        lines.append(f"### {heading}")
        lines.extend(f"- {item}" for item in items)
    if level >= 3:
        lines.append(f"{labels['tradeoff']}: {_text(contract, 'tradeoff', 'depth.prompt')}")
    return "\n\n" + "\n".join(lines)


def _prompt_contract_ui(
    contract: Mapping[str, Any] | None,
    labels: Mapping[str, Any],
    next_label: str | None = None,
) -> str:
    if contract is None:
        return ""
    group_markup = "".join(
        (
            f'<section><h4>{_e(labels["acceptance"])}</h4>{_bullet_list(_sequence(contract.get("acceptance_criteria"), "depth.prompt.acceptance_criteria", minimum=3))}</section>',
            f'<section><h4>{_e(labels["edge_cases"])}</h4>{_bullet_list(_sequence(contract.get("edge_cases"), "depth.prompt.edge_cases", minimum=2))}</section>',
            f'<section><h4>{_e(labels["tradeoffs"])}</h4>{_bullet_list((_text(contract, "tradeoff", "depth.prompt"),))}</section>',
            f'<section><h4>{_e(labels["assumptions"])}</h4>{_bullet_list((labels["prompt_assumption"],))}</section>',
            f'<section><h4>{_e(labels["limits"])}</h4>{_bullet_list(_sequence(contract.get("limits"), "depth.prompt.limits", minimum=1))}</section>',
        )
    )
    return (
        f'<details class="module-depth-disclosure prompt-contract-depth prompt-why" data-prompt-why>'
        f'<summary><strong>{_e(labels["prompt_contract"])}</strong><span>{_e(labels["acceptance"])}</span></summary>'
        f'<div class="prompt-why-body">{group_markup}</div></details>'
    )


def _prompt_execution_gate_ui(contract: Mapping[str, Any] | None, labels: Mapping[str, Any]) -> str:
    if contract is None or "execution_gate" not in contract:
        return ""
    gate = _mapping(contract["execution_gate"], "depth.prompt.execution_gate")
    return (
        f'<aside class="prompt-execution-gate" data-prompt-execution-gate>'
        f'<span class="eyebrow">{_e(labels["execution_gate"])}</span>'
        f'<p>{_e(_text(gate, "action", "depth.prompt.execution_gate"))}</p>'
        f'<dl>{_definition(labels["gate_produces"], _text(gate, "produces", "depth.prompt.execution_gate"))}'
        f'{_definition(labels["gate_criteria"], _text(gate, "criteria", "depth.prompt.execution_gate"))}</dl>'
        f'</aside>'
    )


def _prompt_level_ui(
    prompt: Mapping[str, Any],
    module_id: str,
    locale: str,
    audience: str,
    labels: Mapping[str, Any],
    path: str,
    depth_prompt: Mapping[str, Any] | None = None,
    next_label: str | None = None,
) -> str:
    levels = _sequence(prompt.get("levels"), f"{path}.levels")
    if len(levels) != 4:
        raise RendererContractError(f"{path}.levels: expected exactly four levels")
    normalized: list[tuple[int, Mapping[str, Any]]] = []
    for index, raw in enumerate(levels, 1):
        level = _mapping(raw, f"{path}.levels[{index - 1}]")
        number = _integer(level, "level", f"{path}.levels[{index - 1}]", minimum=1)
        if number != index:
            raise RendererContractError(f"{path}.levels: expected ordered levels 1..4")
        normalized.append((number, level))

    template = _prompt_mode_text(prompt, "template", path)
    demo = _prompt_mode_text(prompt, "demo", path)
    semantic_template = (
        _prompt_semantic_levels(prompt, depth_prompt, module_id, locale, audience, "template", path)
        if depth_prompt is not None
        else None
    )
    semantic_demo = (
        _prompt_semantic_levels(prompt, depth_prompt, module_id, locale, audience, "demo", path)
        if depth_prompt is not None
        else None
    )
    prompt_id = _stable_id(prompt.get("id"), f"{path}.id")
    group_id = f"{module_id}-{prompt_id}"
    tabs: list[str] = []
    panels: list[str] = []
    format_ids = ("natural", "parameters", "spec", "pair")
    for index, (_, level) in enumerate(normalized, 1):
        format_id = format_ids[index - 1]
        panel_id = f"{group_id}-{format_id}"
        context_id = f"{panel_id}-context"
        name = labels["level_names"][index - 1]
        description = labels["level_desc"][index - 1]
        if semantic_template is not None and semantic_demo is not None:
            level_template = semantic_template[index - 1]
            level_demo = semantic_demo[index - 1]
        else:
            level_template = _prompt_text_value(
                level.get("body", level.get("template", template)),
                f"{path}.levels[{index - 1}].template",
            )
            level_demo = _prompt_demo_text(
                level.get("demo", demo),
                depth_prompt,
                labels,
                f"{path}.levels[{index - 1}].demo",
            )
            contract_suffix = _prompt_contract_suffix(depth_prompt, labels, index)
            level_template += contract_suffix
            level_demo += contract_suffix
        label = f"N{index} · {name}"
        tabs.append(
            f'<button type="button" role="tab" tabindex="{0 if index == 1 else -1}" '
            f'aria-selected="{"true" if index == 1 else "false"}" aria-label="{_e(label)}" '
            f'aria-controls="{panel_id}" data-prompt-format="{format_id}" data-level-number="{index}">'
            f'<span class="prompt-tab-number" aria-hidden="true">{index}</span>'
            f'<span class="prompt-tab-copy" aria-hidden="true"><strong>{_e(name)}</strong><small>N{index}</small></span></button>'
        )
        panels.append(
            f'<details class="prompt-level-fallback" data-prompt-level="{index}"{" open" if index == 1 else ""}>'
            f'<summary><span class="prompt-summary-number" aria-hidden="true">{index}</span><span><strong>{_e(label)}</strong>'
            f'<small>{_e(description)}</small></span></summary>'
            f'<div class="prompt-level-context" id="{context_id}"><span>N{index}</span><strong>{_e(name)}</strong><p>{_e(description)}</p></div>'
            f'<pre class="prompt-format-panel prompt-format-panel-{format_id}" id="{panel_id}" role="tabpanel" tabindex="0" '
            f'aria-label="{_e(label)} · {_e(labels["template"])}" aria-describedby="{context_id}" data-prompt-template data-prompt-mode-panel="template">'
            f'{_prompt_lines(level_template)}</pre>'
            f'<textarea class="prompt-format-source" hidden aria-hidden="true" tabindex="-1" data-prompt-source data-prompt-mode="template">{_e(level_template)}</textarea>'
            f'<details class="prompt-demo-native" data-prompt-mode-panel="demo"><summary>{_e(labels["demo"])} · {_e(label)}</summary>'
            f'<pre class="prompt-format-panel prompt-format-panel-{format_id}" id="{panel_id}-demo" role="tabpanel" tabindex="0" '
            f'aria-label="{_e(label)} · {_e(labels["demo"])}" aria-describedby="{context_id}" data-prompt-demo>{_prompt_lines(level_demo)}</pre>'
            f'<textarea class="prompt-format-source" hidden aria-hidden="true" tabindex="-1" data-prompt-source data-prompt-mode="demo">{_e(level_demo)}</textarea>'
            f'</details></details>'
        )

    copy_aria = f'{labels["copy"]} · N1 · {labels["level_names"][0]}'
    return (
        f'<div class="prompt-library" data-prompt-library="{_e(group_id)}" data-active-level="1" data-active-format="natural" data-active-mode="template">'
        f'<div class="prompt-library-toolbar"><div class="prompt-mode-switch" role="group" aria-label="{_e(labels["mode"])}">'
        f'<button type="button" aria-pressed="true" data-prompt-mode-select="template">{_e(labels["template"])}</button>'
        f'<button type="button" aria-pressed="false" data-prompt-mode-select="demo">{_e(labels["demo"])}</button></div>'
        f'<span class="prompt-syntax">{_e(labels["syntax"])}</span></div>'
        f'{_prompt_input_guide(prompt, labels, locale, path)}'
        f'<div class="prompt-format-tabs" role="tablist" aria-label="N1–N4">{"".join(tabs)}</div>'
        f'<div class="prompt-format-panels">{"".join(panels)}</div>'
        f'<div class="prompt-library-actions"><button class="copy prompt-format-copy" type="button" aria-label="{_e(copy_aria)}" '
        f'data-format-copy="{_e(group_id)}" data-copy-label="{_e(labels["copy"])}" data-copied-label="{_e(labels["copied"])}">'
        f'<span>{_e(labels["copy"])}</span></button><span class="prompt-copy-status sr-only" role="status" aria-live="polite"></span></div></div>'
    )


def render_prompts(
    payload: Mapping[str, Any],
    locale: str,
    audience: str,
    module: Mapping[str, Any],
    urls: Mapping[str, Any],
    *,
    depth: Mapping[str, Any] | None = None,
    execution_guide: str | None = None,
    artifact_labels: Mapping[str, str] | None = None,
) -> str:
    """Render a compact prompt library with four levels and two modes."""

    labels, module = _context(locale, audience, module)
    if execution_guide is not None:
        if not isinstance(execution_guide, str) or execution_guide.count("data-notebook-execution-guide") != 1:
            raise RendererContractError("promptLibrary.executionGuide: expected one governed NotebookLM guide")
        if "<script" in execution_guide.lower():
            raise RendererContractError("promptLibrary.executionGuide: scripts are forbidden")
    if not isinstance(artifact_labels, Mapping) or not artifact_labels:
        raise RendererContractError("promptLibrary.artifactLabels: governed localized labels are required")
    normalized_artifact_labels: dict[str, str] = {}
    for key, value in artifact_labels.items():
        if not isinstance(key, str) or not key.strip() or not isinstance(value, str) or not value.strip():
            raise RendererContractError("promptLibrary.artifactLabels: expected non-empty text pairs")
        normalized_artifact_labels[key] = value.strip()

    resource = _resource(payload, "promptLibrary")
    title = _text(resource, "title", "promptLibrary")
    lede = _text(resource, "lede", "promptLibrary")
    prompts = _sequence(resource.get("prompts"), "promptLibrary.prompts", minimum=1)
    depth_resource = _depth_resource(depth, "prompts")
    depth_prompts = _by_id(_sequence(depth_resource.get("items"), "depth.prompts.items", minimum=1), "depth.prompts.items") if depth_resource else {}
    normalized: list[Mapping[str, Any]] = []
    seen_ids: set[str] = set()
    surfaces = {"chat": 0, "source_search": 0}
    kinds = {"direct": 0, "meta": 0}
    for prompt_index, raw in enumerate(prompts):
        path = f"promptLibrary.prompts[{prompt_index}]"
        prompt = _mapping(raw, path)
        prompt_id = _stable_id(prompt.get("id"), f"{path}.id")
        if prompt_id in seen_ids:
            raise RendererContractError(f"promptLibrary.prompts: duplicate id {prompt_id}")
        seen_ids.add(prompt_id)
        _text(prompt, "title", path)
        _text(prompt, "receive", path)
        _prompt_artifact_label(prompt, path)
        consume_ids = _sequence(prompt.get("consumeIds"), f"{path}.consumeIds")
        for index, consume_id in enumerate(consume_ids):
            _stable_id(consume_id, f"{path}.consumeIds[{index}]")
        _evidence_attr(prompt, path)
        surface = _prompt_surface(prompt.get("surface"), f"{path}.surface")
        kind = prompt.get("kind", "direct")
        if kind not in kinds:
            raise RendererContractError(f"{path}.kind: expected direct or meta")
        family_id = prompt.get("family_id", "learn" if prompt_index < 4 else "embody" if prompt_index < 8 else "evolve")
        if family_id not in {"learn", "embody", "evolve", "meta"}:
            raise RendererContractError(f"{path}.family_id: invalid capability family")
        if (kind == "meta") != (family_id == "meta"):
            raise RendererContractError(f"{path}: kind and family_id disagree")
        surfaces[surface] += 1
        kinds[kind] += 1
        normalized.append(prompt)

    prompt_titles = {prompt["id"]: _text(prompt, "title", "promptLibrary.prompt") for prompt in normalized}
    prompt_outputs = {
        prompt["id"]: _prompt_artifact_label(prompt, "promptLibrary.prompt")
        for prompt in normalized
    }

    def resolve_artifact(reference: str, path: str) -> str:
        if reference in normalized_artifact_labels:
            return normalized_artifact_labels[reference]
        if reference in prompt_outputs:
            return prompt_outputs[reference]
        if reference.endswith("-output") and reference[:-7] in prompt_outputs:
            return prompt_outputs[reference[:-7]]
        raise RendererContractError(f"{path}: missing governed localized artifact label for {reference}")

    cards: dict[str, list[str]] = {"direct": [], "meta": []}
    for prompt_index, prompt in enumerate(normalized):
        path = f"promptLibrary.prompts[{prompt_index}]"
        depth_prompt = depth_prompts.get(prompt["id"])
        kind = prompt.get("kind", "direct")
        family_id = prompt.get("family_id", "learn" if prompt_index < 4 else "embody" if prompt_index < 8 else "evolve")
        surface = _prompt_surface(prompt["surface"], f"{path}.surface")
        surface_label = labels["chat"] if surface == "chat" else labels["sources"]
        receive = (
            _text(depth_prompt, "receive_override", "depth.prompt")
            if depth_prompt is not None and "receive_override" in depth_prompt
            else resolve_artifact(prompt["receive"], f"{path}.receive")
        )
        consume_labels = [resolve_artifact(item, f"{path}.consumeIds") for item in prompt["consumeIds"]]
        consume_labels = list(dict.fromkeys(item for item in consume_labels if item.casefold() != receive.casefold()))
        produces = _prompt_artifact_label(prompt, path)
        consume_gate = (
            f'<span class="prompt-flow-gate">{_e(labels["consumes"])} · {_e(" · ".join(consume_labels))}</span>'
            if consume_labels
            else ""
        )
        flow = (
            f'<div class="prompt-flow" data-prompt-flow="{_e(prompt["id"])}"><div><span>{_e(labels["receives"])}</span>'
            f'<code>{_e(receive)}</code></div><i aria-hidden="true">→</i><div><span>{_e(labels["produces"])}</span>'
            f'<code>{_e(produces)}</code></div>{consume_gate}</div>'
        )
        next_label = None
        if depth_prompt is not None:
            next_id = _text(depth_prompt, "next", "depth.prompt")
            next_label = labels["next_step"] if next_id == "module-next" else prompt_titles.get(next_id)
            if next_label is None:
                raise RendererContractError(f"{path}: unresolved depth next prompt {next_id}")
        level_ui = _prompt_level_ui(prompt, module["moduleId"], locale, audience, labels, path, depth_prompt, next_label)
        if depth_prompt is not None:
            prompt_inputs = _prompt_input_contract(prompt, locale, path)
            context_when = _text(depth_prompt, "when", "depth.prompt")
            context_example = _text(depth_prompt, "demo_artifact", "depth.prompt")
            context_evidence = "; ".join(
                str(item).strip() for item in _sequence(
                    depth_prompt.get("acceptance_criteria"), "depth.prompt.acceptance", minimum=3
                )[:2]
            )
            context_limit = str(_sequence(depth_prompt.get("limits"), "depth.prompt.limits", minimum=1)[0]).strip()
        else:
            prompt_inputs = _prompt_input_contract(prompt, locale, path)
            context_when = receive
            context_example = prompt_inputs[0]["example"]
            context_evidence = produces
            context_limit = labels["synthetic_demo_rule"]
        context_markup = (
            f'<dl class="library-prompt-brief"><div><dt>{_e(labels["when"])}</dt><dd>{_e(context_when)}</dd></div>'
            f'<div><dt>{_e(labels["example"])}</dt><dd>{_e(context_example)}</dd></div>'
            f'<div><dt>{_e(labels["evidence"])}</dt><dd>{_e(context_evidence)}</dd></div>'
            f'<div class="prompt-limit-compact"><dt>{_e(labels["limit"])}</dt><dd>{_e(context_limit)}</dd></div></dl>'
        )
        summary_text = _text(depth_prompt, "purpose", "depth.prompt") if depth_prompt is not None else produces
        display_number = f'M{len(cards["meta"]) + 1}' if kind == "meta" else f'{len(cards["direct"]) + 1:02d}'
        cards[kind].append(
            f'<article class="library-prompt-card" id="{_e(prompt["id"])}" data-library-prompt data-prompt-kind="{kind}" '
            f'data-prompt-family="{family_id}" data-prompt-slot="{_e(display_number)}" '
            f'data-notebook-surface="{surface}" data-evidence-ids="{_evidence_attr(prompt, path)}">'
            f'<details class="library-prompt-disclosure" data-prompt-card-disclosure>'
            f'<summary data-open-label="{_e(labels["open_prompt"])}" data-close-label="{_e(labels["close_prompt"])}">'
            f'<span class="library-prompt-number" aria-hidden="true">{_e(display_number)}</span>'
            f'<span class="library-prompt-summary-copy"><span class="eyebrow">{_e(labels["surface"])} · {_e(surface_label)}</span>'
            f'<strong class="library-prompt-title">{_e(prompt["title"])}</strong><small>{_e(summary_text)}</small></span>'
            f'<span class="prompt-launch-badge" data-launch="{surface}"><small>{_e(labels["surface"])}</small><strong>{_e(surface_label)}</strong></span>'
            f'<span class="library-prompt-chevron" aria-hidden="true">⌄</span></summary>'
            f'<div class="library-prompt-card-body"><div class="library-prompt-side"><details class="prompt-card-context">'
            f'<summary>{_e(labels["details"])}</summary>{context_markup}'
            f'</details>{flow}{_prompt_execution_gate_ui(depth_prompt, labels)}</div>{level_ui}'
            f'{_prompt_contract_ui(depth_prompt, labels, next_label)}</div></details></article>'
        )

    sibling_nav = _sibling_nav("prompts", urls, labels)
    metrics = (
        f'<div class="prompt-library-metrics"><a href="#directos"><strong>{len(normalized)}</strong><span>{_e(labels["prompts"])}</span></a>'
        f'<a href="#directos"><strong>{surfaces["chat"]}</strong><span>{_e(labels["chat"])}</span></a>'
        f'<a href="#directos"><strong>{surfaces["source_search"]}</strong><span>{_e(labels["sources"])}</span></a></div>'
    )
    level_map = "".join(
        f'<li><span>N{index}</span><strong>{_e(name)}</strong><p>{_e(labels["level_desc"][index - 1])}</p></li>'
        for index, name in enumerate(labels["level_names"], 1)
    )
    map_markup = (
        f'<aside class="prompt-library-map"><header><span class="eyebrow">{_e(labels["library_map"])}</span>'
        f'<h2>{_e(labels["library_map_lead"])}</h2></header>{metrics}'
        f'<ul class="prompt-library-level-map">{level_map}</ul><footer><span>{_e(labels["syntax"])}</span></footer></aside>'
    )
    hero_companion = execution_guide if execution_guide is not None else map_markup
    secondary_map = (
        f'<details class="shell prompt-library-secondary-map"><summary><strong>{_e(labels["library_map"])}</strong>'
        f'<span>{len(normalized)} · N1–N4</span></summary>{map_markup}</details>'
        if execution_guide is not None
        else ""
    )
    filter_ui = (
        f'<div class="prompt-surface-filter" role="group" aria-label="{_e(labels["surface"])}">'
        f'<button type="button" aria-pressed="true" data-prompt-surface-filter="all">{_e(labels["all"])}</button>'
        f'<button type="button" aria-pressed="false" data-prompt-surface-filter="chat">{_e(labels["chat"])}</button>'
        f'<button type="button" aria-pressed="false" data-prompt-surface-filter="source_search">{_e(labels["sources"])}</button></div>'
    )
    graph_markup = ""
    if depth_resource is not None:
        graph = _mapping(depth_resource.get("graph_summary"), "depth.prompts.graph_summary")
        graph_markup = (
            f'<details class="module-depth-graph"><summary><span class="eyebrow">{_e(labels["workflow"])}</span>'
            f'<strong>{_e(_text(graph, "title", "depth.prompts.graph_summary"))}</strong></summary><div>'
            f'<p>{_e(_text(graph, "body", "depth.prompts.graph_summary"))}</p>'
            f'<small><strong>{_e(labels["independent_use"])}:</strong> {_e(_text(graph, "independent_use", "depth.prompts.graph_summary"))}</small></div></details>'
        )
    return (
        f'<main id="main" class="prompt-library-page" {_module_attrs(module, locale, audience, "prompts")}{_depth_attr(depth)}> '
        f'<section class="prompt-library-hero" id="prompts-inicio"><div class="shell"><div class="prompt-library-hero-grid">'
        f'<div class="prompt-library-hero-copy"><span class="eyebrow">{_e(labels["module"])} {module["order"]:02d} · Prompts</span>'
        f'<h1>{_e(title)}</h1><p class="lead">{_e(lede)}</p><div class="actions"><a class="btn" href="#directos">{_e(labels["view_prompts"])} →</a>'
        f'{_link(_url(urls, "playbook"), labels["playbook"], "btn secondary")}</div></div>'
        f'{hero_companion}</div>{sibling_nav}</div></section>{secondary_map}<section class="prompt-library-section shell" id="directos">'
        f'<div class="prompt-library-section-heading"><div class="section-head"><span class="eyebrow">{_e(labels["direct_prompts"])}</span>'
        f'<h2 class="h2">{_e(labels["direct_prompts_lead"])}</h2></div>{filter_ui}</div>{graph_markup}<div class="library-prompt-list">{"".join(cards["direct"])}</div></section>'
        f'<section class="prompt-library-section prompt-library-meta" id="metaprompts"><div class="shell">'
        f'<div class="section-head"><span class="eyebrow">{_e(labels["meta_prompts"])}</span>'
        f'<h2 class="h2">{_e(labels["meta_prompts_lead"])}</h2></div>'
        f'<div class="library-prompt-list">{"".join(cards["meta"])}</div>'
        f'{_next_step("prompts", "resources", urls, labels)}</div></section></main>'
    )


def render_module_bundle(
    variant: Mapping[str, Any],
    urls: Mapping[str, Any],
    depth: Mapping[str, Any] | None = None,
    artifact_labels: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Render all four resource interiors from one exact variant and depth overlay."""

    variant = _mapping(variant, "variant")
    locale = _text(variant, "locale", "variant")
    audience = _text(variant, "audience", "variant")
    module = _mapping(variant.get("module"), "variant.module")
    return {
        "masterclass": render_masterclass(module["masterclass"], locale, audience, module, urls, depth=depth),
        "workbook": render_workbook(
            module["workbook"], locale, audience, module, urls, depth=depth,
            artifact_labels=artifact_labels,
        ),
        "playbook": render_playbook(module["playbook"], locale, audience, module, urls, depth=depth),
        "prompts": render_prompts(
            module["promptLibrary"], locale, audience, module, urls, depth=depth,
            artifact_labels=artifact_labels,
        ),
    }


__all__ = (
    "RendererContractError",
    "WORKBOOK_STAGE_LABELS",
    "render_masterclass",
    "render_workbook",
    "render_playbook",
    "render_prompts",
    "render_module_bundle",
)
