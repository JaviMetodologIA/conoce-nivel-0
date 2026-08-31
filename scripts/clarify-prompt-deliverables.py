#!/usr/bin/env python3
"""Replace ambiguous prompt nouns with concrete document and result names.

The migration is deterministic and idempotent. It updates the 27 typed prompt
contracts in place, preserves their release state and refreshes each self hash.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "src" / "prompt-contracts"

ARTIFACT_RENAMES = {
    "BLUEPRINT_DE_INVESTIGACION": "PLAN_INICIAL_DE_INVESTIGACION",
    "ENCARGO_DE_INVESTIGACION": "INFORME_DE_INVESTIGACION",
    "DESCARGA_CONFIRMADA": "NOTAS_CONFIRMADAS",
    "BRIEF_DE_APRENDIZAJE": "PLAN_DE_ESTUDIO",
    "PREPLAN_NOTEBOOKLM": "PLAN_DE_NOTEBOOKLM",
    "ENCARGO_DE_RESEARCH": "PLAN_DE_INVESTIGACION",
}


def canonical_self(document: dict) -> str:
    payload = {key: value for key, value in document.items() if key != "self_sha256"}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def replace(value, rules):
    if isinstance(value, str):
        for old, new in rules:
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [replace(item, rules) for item in value]
    if isinstance(value, dict):
        return {key: replace(item, rules) for key, item in value.items()}
    return value


COMMON = {
    "es": [
        ("encargos de aprendizaje", "planes de estudio"),
        ("Encargos de aprendizaje", "Planes de estudio"),
        ("encargo de aprendizaje", "plan de estudio"),
        ("Encargo de aprendizaje", "Plan de estudio"),
        ("encargo confirmado", "plan de estudio confirmado"),
        ("Encargo confirmado", "Plan de estudio confirmado"),
    ],
    "en": [
        ("learning assignments", "study plans"),
        ("Learning assignments", "Study plans"),
        ("learning assignment", "study plan"),
        ("Learning assignment", "Study plan"),
        ("confirmed assignment", "confirmed study plan"),
        ("Confirmed assignment", "Confirmed study plan"),
    ],
    "pt": [
        ("encargos de aprendizagem", "planos de estudo"),
        ("Encargos de aprendizagem", "Planos de estudo"),
        ("encargo de aprendizagem", "plano de estudo"),
        ("Encargo de aprendizagem", "Plano de estudo"),
        ("encargo confirmado", "plano de estudo confirmado"),
        ("Encargo confirmado", "Plano de estudo confirmado"),
    ],
}

FILE_RULES = {
    "library-01.json": {
        "es": [("Plan inicial de investigación de investigación", "Plan inicial de investigación"), ("Blueprint", "Plan inicial de investigación"), ("blueprint", "plan inicial de investigación")],
        "en": [("Team research blueprint", "Initial team research plan"), ("Research blueprint", "Initial research plan"), ("blueprint", "research plan"), ("Blueprint", "Research plan")],
        "pt": [("Plano inicial de pesquisa de pesquisa", "Plano inicial de pesquisa"), ("Blueprint", "Plano inicial de pesquisa"), ("blueprint", "plano inicial de pesquisa")],
    },
    "library-02.json": {
        "es": [("reencuadrar el encargo", "redefinir el objetivo")],
        "en": [("reframe the assignment", "redefine the goal")],
        "pt": [("reformular o encargo", "redefinir o objetivo")],
    },
    "library-03.json": {
        "es": [("Research brief · pregunta, alcance y criterio", "Plan de investigación · pregunta, alcance y criterios")],
        "en": [("Research brief · question, scope and criterion", "Research plan · question, scope and criteria")],
        "pt": [("Research brief · pergunta, escopo e critério", "Plano de pesquisa · pergunta, escopo e critérios")],
    },
    "workbook-brain-1.json": {
        "es": [("<DICTADO>", "<NOTAS INICIALES>"), ("Descargar, limpiar y confirmar el dictado de una sesión", "Ordenar y confirmar las notas de una sesión"), ("Descargar, limpiar y confirmar", "Ordenar y confirmar notas iniciales"), ("descargar y ordenar mi dictado", "ordenar mis notas iniciales"), ("descarga mental", "captura de notas iniciales"), ("el encargo", "el plan de estudio"), ("encargo", "plan de estudio"), ("preplanificar el Notebook", "crear el plan de NotebookLM"), ("preplan del Notebook", "plan de NotebookLM")],
        "en": [("<BRAIN DUMP>", "<STARTING NOTES>"), ("Dump, clean and confirm a session dictation", "Organize and confirm notes from a session"), ("Dump, clean and confirm", "Organize and confirm starting notes"), ("dump and order my dictation", "organize my starting notes"), ("brain dump prompt", "starting-notes prompt"), ("the assignment", "the study plan"), ("assignment", "study plan"), ("preplanning the Notebook", "creating the NotebookLM plan"), ("Notebook preplan", "NotebookLM plan")],
        "pt": [("<DITADO>", "<NOTAS INICIAIS>"), ("Descarregar, limpar e confirmar o ditado de uma sessão", "Organizar e confirmar as notas de uma sessão"), ("Descarregar, limpar e confirmar", "Organizar e confirmar notas iniciais"), ("descarregar e organizar meu ditado", "organizar minhas notas iniciais"), ("descarga mental", "captura de notas iniciais"), ("o encargo", "o plano de estudo"), ("encargo", "plano de estudo"), ("pré-planejar o Notebook", "criar o plano do NotebookLM"), ("pré-plano do Notebook", "plano do NotebookLM")],
    },
    "workbook-brain-2.json": {
        "es": [("<DICTADO>", "<NOTAS INICIALES>"), ("briefs", "planes de estudio"), ("Brief", "Plan de estudio"), ("brief", "plan de estudio"), ("encargos", "planes de estudio"), ("Encargo", "Plan de estudio"), ("encargo", "plan de estudio")],
        "en": [("<BRAIN DUMP>", "<STARTING NOTES>"), ("assignments", "study plans"), ("Assignments", "Study plans"), ("Assignment", "Study plan"), ("assignment", "study plan"), ("briefs", "study plans"), ("Brief", "Study plan"), ("brief", "study plan")],
        "pt": [("<DITADO>", "<NOTAS INICIAIS>"), ("briefs", "planos de estudo"), ("Brief", "Plano de estudo"), ("brief", "plano de estudo"), ("encargos", "planos de estudo"), ("Encargo", "Plano de estudo"), ("encargo", "plano de estudo")],
    },
    "workbook-brain-3.json": {
        "es": [("<DICTADO>", "<NOTAS INICIALES>"), ("una plan de NotebookLM", "un plan de NotebookLM"), ("Convertir en preplan de NotebookLM del equipo", "Convertir el plan de estudio en un plan de NotebookLM del equipo"), ("Convertir en preplan de NotebookLM", "Convertir el plan de estudio en un plan de NotebookLM"), ("preplanificación", "plan"), ("preplanificar", "planificar"), ("preplan", "plan"), ("<ENCARGO>", "<PLAN DE ESTUDIO>"), ("Encargo", "Plan de estudio"), ("encargo", "plan de estudio"), ("ASSIGNMENT", "STUDY PLAN")],
        "en": [("<BRAIN DUMP>", "<STARTING NOTES>"), ("Turn it into a NotebookLM preplan for a team", "Turn the study plan into a NotebookLM plan for a team"), ("Turn it into a NotebookLM preplan", "Turn the study plan into a NotebookLM plan"), ("preplanning", "planning"), ("preplan", "plan"), ("<ASSIGNMENT>", "<STUDY PLAN>"), ("assignment", "study plan")],
        "pt": [("<DITADO>", "<NOTAS INICIAIS>"), ("Converter em pré-plano de NotebookLM da equipe", "Converter o plano de estudo em plano do NotebookLM da equipe"), ("Converter em pré-plano de NotebookLM", "Converter o plano de estudo em plano do NotebookLM"), ("pré-planejamento", "plano"), ("pré-planejar", "planejar"), ("pré-plano", "plano"), ("<ENCARGO>", "<PLANO DE ESTUDO>"), ("Encargo", "Plano de estudo"), ("encargo", "plano de estudo")],
    },
    "workbook-01.json": {
        "es": [("Research brief · pregunta, alcance y criterio", "Plan de investigación · pregunta, alcance y criterios"), ("encargo de investigación", "plan de investigación")],
        "en": [("Research brief · question, scope and criterion", "Research plan · question, scope and criteria"), ("research assignment", "research plan"), ("research brief", "research plan")],
        "pt": [("Research brief · pergunta, escopo e critério", "Plano de pesquisa · pergunta, escopo e critérios"), ("encargo de pesquisa", "plano de pesquisa")],
    },
    "workbook-02.json": {
        "es": [("encargo de investigación", "plan de investigación")],
        "en": [("research assignment", "research plan"), ("research brief", "research plan")],
        "pt": [("encargo de pesquisa", "plano de pesquisa")],
    },
    "workbook-03.json": {
        "es": [("crítico para <RESULTADO> —", "crítico para mi <RESULTADO> —"), ("de mayor impacto para", "crítico para"), ("en mi camino hacia <RESULTADO>", "para <RESULTADO>"), ("Research brief · pregunta, alcance y criterio", "Plan de investigación · pregunta, alcance y criterios"), ("Encargo pegable", "Plan de investigación listo para usar"), ("Encargo transferible", "Plan de investigación transferible"), ("encargos de investigación", "planes de investigación"), ("Encargo de investigación", "Plan de investigación"), ("encargo de investigación", "plan de investigación"), ("encargos", "planes de investigación"), ("encargo", "plan de investigación"), ("aquí solo se plan de investigación", "aquí solo se prepara el plan de investigación")],
        "en": [("critical gap for <OUTCOME> —", "critical gap for my <OUTCOME> —"), ("on my way to <OUTCOME>", "for <OUTCOME>"), ("highest-impact gap", "critical gap"), ("Research brief · question, scope and criterion", "Research plan · question, scope and criteria"), ("research briefs", "research plans"), ("Research brief", "Research plan"), ("research brief", "research plan"), ("briefs", "research plans"), ("brief", "research plan"), ("commissioned", "planned")],
        "pt": [("este passo só redige", "aqui só redige"), ("para <RESULTADO> —", "para meu <RESULTADO> —"), ("Research brief · pergunta, escopo e critério", "Plano de pesquisa · pergunta, escopo e critérios"), ("Encargo colável", "Plano de pesquisa pronto para usar"), ("Encargo transferível", "Plano de pesquisa transferível"), ("encargos de pesquisa", "planos de pesquisa"), ("Encargo de pesquisa", "Plano de pesquisa"), ("encargo de pesquisa", "plano de pesquisa"), ("encargos", "planos de pesquisa"), ("encargo", "plano de pesquisa"), ("encomendada", "planejada")],
    },
    "workbook-04.json": {
        "es": [("encargo de investigación", "plan de investigación"), ("encargo", "plan de investigación")],
        "en": [("research brief", "research plan"), ("brief", "research plan")],
        "pt": [("encargo de pesquisa", "plano de pesquisa"), ("encargo", "plano de pesquisa"), ("encomendada", "planejada")],
    },
    "workbook-05.json": {
        "es": [("encargo", "plan de investigación")],
        "en": [("brief", "research plan")],
        "pt": [("encargo", "plano de pesquisa")],
    },
    "workbook-06.json": {
        "es": [("La contenido", "El contenido"), ("Crea la contenido; no la publica", "Crea el contenido; no lo publica"), ("entregar la contenido", "entregar el contenido"), ("responde por la contenido", "responde por el contenido"), ("No priorices casos: sale un contenido.", "No priorices casos."), ("<TIPO DE CONTENIDO> breve", "<TIPO DE CONTENIDO> en versión breve"), ("<TIPO DE CONTENIDO> de extensión breve", "<TIPO DE CONTENIDO> en versión breve"), ("<TIPO DE CONTENIDO> de concisa", "<TIPO DE CONTENIDO> en versión breve"), ("un contenido citada", "un contenido citado"), ("contenido final citada", "contenido final citado"), ("Contenido menos vistosa", "Contenido menos vistoso"), ("Contenido citada", "Contenido citado"), ("una contenido", "un contenido"), ("Pieza", "Contenido"), ("pieza", "contenido"), ("encarga", "solicita")],
        "en": [("Do not rank use cases: produce one deliverable.", "Do not rank use cases."), ("produce one content deliverable", "produce one deliverable"), ("you need a content content", "you need content"), ("requires a content issued by the team", "requires team-authored content"), ("into a content issued by the team", "into team-authored content"), ("exchange for a content defensible", "exchange for content that is defensible"), ("a cited final content", "source-cited final content"), ("into <CONTENT TYPE> of concise", "into concise <CONTENT TYPE>"), ("one content comes out", "produce one deliverable"), ("produces a cited content", "produces source-cited content"), ("produces a cited, reviewable content", "produces cited, reviewable content"), ("a content with", "source-cited content with"), ("a content that", "content that"), ("a content based", "content based"), ("Team piece", "Team content"), ("Cited piece", "Cited content"), ("piece", "content"), ("Piece", "Content"), ("Commissioned thesis", "Requested thesis"), ("commissioned thesis", "requested thesis")],
        "pt": [("A conteúdo não é publicada", "O conteúdo não é publicado"), ("A conteúdo", "O conteúdo"), ("Cria a conteúdo; não a publica", "Cria o conteúdo; não o publica"), ("entregar a conteúdo", "entregar o conteúdo"), ("pela conteúdo", "pelo conteúdo"), ("conteúdos assinadas", "conteúdos assinados"), ("Não priorize casos: sai um conteúdo.", "Não priorize casos."), ("<TIPO DE CONTEÚDO> conciso", "<TIPO DE CONTEÚDO> em versão breve"), ("<TIPO DE CONTEÚDO> em formato conciso", "<TIPO DE CONTEÚDO> em versão breve"), ("o processo exige um conteúdo em nome da equipe e alguém responde pelo que ela afirma", "o processo exige conteúdo em nome da equipe e um responsável responde por suas afirmações"), ("um conteúdo citada", "um conteúdo citado"), ("do oficina", "da oficina"), ("<TIPO DE CONTEÚDO> de concisa", "<TIPO DE CONTEÚDO> em versão breve"), ("conteúdo final citada", "conteúdo final citado"), ("Conteúdo menos vistosa", "Conteúdo menos vistoso"), ("Conteúdo citada", "Conteúdo citado"), ("numa conteúdo", "em conteúdo"), ("uma conteúdo", "um conteúdo"), ("Peça", "Conteúdo"), ("peça", "conteúdo"), ("Tese encomendada", "Tese solicitada"), ("tese encomendada", "tese solicitada"), ("quem encomenda", "responsável editorial")],
    },
    "workbook-07.json": {
        "es": [("la contenido citado", "el contenido citado"), ("pieza de contenido", "contenido citado"), ("la pieza", "el contenido"), ("una pieza", "un contenido")],
        "en": [("content piece", "source-cited content"), ("the piece", "the content"), ("a piece", "content")],
        "pt": [("a conteúdo citado", "o conteúdo citado"), ("peça de conteúdo", "conteúdo citado"), ("a peça", "o conteúdo"), ("uma peça", "um conteúdo")],
    },
    "workbook-09.json": {
        "es": [("Verificar que el contenido o decisión esté documentada y detenerse si no lo está", "Verificar que exista contenido o una decisión documentada; detenerse si falta"), ("pieza que debe quedar lista", "entregable que debe quedar listo"), ("pieza de contenido", "contenido citado"), ("Sin pieza que defender", "Sin contenido que defender"), ("pieza documentada", "contenido documentado"), ("la pieza", "el contenido"), ("una pieza", "un contenido"), ("pieza o decisión", "contenido o decisión"), ("pieza ya", "contenido ya")],
        "en": [("piece that must be ready", "deliverable that must be ready"), ("content piece", "source-cited content"), ("No piece to defend", "No content to defend"), ("documented decision or piece", "documented decision or content"), ("the piece", "the content"), ("a piece", "content"), ("piece or decision", "content or decision")],
        "pt": [("Submeter umo conteúdo ou decisão já feita", "Submeter conteúdo ou decisão já produzidos"), ("Verificar que existo conteúdo ou decisão a defender e parar se não existir", "Verificar que exista conteúdo ou decisão a defender; parar se faltar"), ("Verificar que o conteúdo ou decisão esteja documentada e parar se não estiver", "Verificar que exista conteúdo ou decisão documentada; parar se faltar"), ("peça que deve ficar pronta", "entregável que deve ficar pronto"), ("peça de conteúdo", "conteúdo citado"), ("Sem peça a defender", "Sem conteúdo a defender"), ("decisão ou peça documentada", "decisão ou conteúdo documentado"), ("a peça", "o conteúdo"), ("uma peça", "um conteúdo"), ("peça ou decisão", "conteúdo ou decisão")],
    },
    "library-m4.json": {
        "es": [("pieza que debe quedar lista", "entregable que debe quedar listo"), ("El encargo de M4", "El diseño de M4"), ("Generador de preparador de entrega del equipo", "Generador de guía para preparar la entrega del equipo"), ("Generador de preparador de entrega", "Generador de guía para preparar una entrega")],
        "en": [("The M4 brief", "The M4 design"), ("piece that must be ready", "deliverable that must be ready"), ("Team delivery preparer generator", "Team delivery-preparation guide generator"), ("Delivery preparer generator", "Delivery-preparation guide generator")],
        "pt": [("peça que deve ficar pronta", "entregável que deve ficar pronto"), ("O encargo de M4", "O desenho de M4"), ("Gerador de preparador de entrega da equipe", "Gerador de guia para preparar a entrega da equipe"), ("Gerador de preparador de entrega", "Gerador de guia para preparar uma entrega")],
    },
    "library-m3.json": {
        "es": [("El encargo de M3", "El diseño de M3")],
        "en": [("The M3 assignment", "The M3 design"), ("The M3 brief", "The M3 design")],
        "pt": [("O encargo de M3", "O desenho de M3")],
    },
    "library-m1.json": {
        "es": [("coach como pieza", "coach como guía reutilizable"), ("El encargo de M1", "El diseño de M1")],
        "en": [("coach as a piece", "coach as a reusable guide"), ("The M1 assignment", "The M1 design"), ("The M1 brief", "The M1 design")],
        "pt": [("coach como peça", "coach como guia reutilizável"), ("O encargo de M1", "O desenho de M1")],
    },
    "library-m2.json": {
        "es": [("El encargo de M2", "El diseño de M2")],
        "en": [("The M2 assignment", "The M2 design"), ("The M2 brief", "The M2 design")],
        "pt": [("O encargo de M2", "O desenho de M2")],
    },
}

BOUNDARY_RULES = {
    "workbook-brain-1.json": [("un encargo", "un plan de estudio"), ("en encargo", "en plan de estudio"), ("el encargo", "el plan de estudio"), ("preplanificar el Notebook", "crear el plan de NotebookLM"), ("preplan del Notebook", "plan de NotebookLM")],
    "workbook-brain-2.json": [("un encargo", "un plan de estudio"), ("el encargo", "el plan de estudio"), ("preplanificar el Notebook", "crear el plan de NotebookLM"), ("preplanifica", "planifica")],
    "workbook-brain-3.json": [("el encargo", "el plan de estudio"), ("preplanificar el Notebook", "crear el plan de NotebookLM"), ("preplanifica", "planifica"), ("rehace el encargo", "redefine el plan de estudio")],
    "workbook-02.json": [("encargo de investigación", "plan de investigación")],
    "workbook-03.json": [("el encargo escrito", "el plan de investigación escrito"), ("respuesta al encargo", "informe de investigación")],
    "workbook-04.json": [("respuesta del encargo", "informe de investigación")],
    "workbook-06.json": [("una sola contenido citado", "un solo contenido citado"), ("probarla", "probarlo"), ("pieza citada", "contenido citado"), ("la pieza", "el contenido")],
    "workbook-07.json": [("una contenido citado", "un contenido citado"), ("pieza citada", "contenido citado"), ("la pieza", "el contenido")],
    "workbook-08.json": [("una pieza ya escrita", "un contenido ya escrito")],
    "workbook-09.json": [("una pieza", "un contenido"), ("la pieza", "el contenido")],
}

AUXILIARY_RULES = {
    "src/prompt-library-spec-v1.json": [
        ("Blueprint de investigación", "Plan inicial de investigación"),
        ("Research blueprint", "Initial research plan"),
        ("Blueprint de pesquisa", "Plano inicial de pesquisa"),
    ],
    "src/playbook-spec-v1.json": [
        ("La investigación comienza por el encargo, no por la herramienta.", "La investigación comienza por el plan, no por la herramienta."),
        ("Una IA conversacional para estructurar el encargo.", "Una IA conversacional para estructurar el plan de investigación."),
        ("Blueprint · encargo verificable de investigación.", "Plan de investigación · preguntas, fuentes y criterios verificables."),
        ("Prompt · encargo ejecutable para una IA.", "Prompt · instrucción ejecutable para una IA."),
        ("Research begins with the assignment, not the tool.", "Research begins with the plan, not the tool."),
        ("A conversational AI to structure the assignment.", "A conversational AI to structure the research plan."),
        ("Blueprint · a verifiable research assignment.", "Research plan · verifiable questions, sources and criteria."),
        ("Prompt · an executable assignment for AI.", "Prompt · an executable instruction for AI."),
        ("A pesquisa começa pelo encargo, não pela ferramenta.", "A pesquisa começa pelo plano, não pela ferramenta."),
        ("Uma IA conversacional para estruturar o encargo.", "Uma IA conversacional para estruturar o plano de pesquisa."),
        ("Blueprint · encargo verificável de pesquisa.", "Plano de pesquisa · perguntas, fontes e critérios verificáveis."),
        ("Prompt · encargo executável para uma IA.", "Prompt · instrução executável para uma IA."),
        ('"es": "Blueprint de investigación"', '"es": "Plan inicial de investigación"'),
        ('"en": "Research blueprint"', '"en": "Initial research plan"'),
        ('"pt": "Blueprint de pesquisa"', '"pt": "Plano inicial de pesquisa"'),
    ],
}


def update_inputs(cell, lang):
    labels = {
        "es": ("PLAN DE ESTUDIO", "plan confirmado que define propósito, alcance y evidencia", "aprender a verificar respuestas de IA"),
        "en": ("STUDY PLAN", "confirmed plan defining purpose, scope and evidence", "learn to verify AI answers"),
        "pt": ("PLANO DE ESTUDO", "plano confirmado que define propósito, escopo e evidência", "aprender a verificar respostas de IA"),
    }
    notes = {
        "es": ("NOTAS INICIALES", "ideas o dictado todavía sin ordenar"),
        "en": ("STARTING NOTES", "ideas or dictation not yet organized"),
        "pt": ("NOTAS INICIAIS", "ideias ou ditado ainda sem organizar"),
    }
    for item in cell["inputs"]:
        if item["key"] in {"assignment", "study plan"}:
            item["key"] = "study_plan"
            item["label"], item["help"], item["example"] = labels[lang]
        elif item["key"] == "brain_dump":
            item["label"], item["help"] = notes[lang]


def main():
    changed = 0
    for path in sorted(CONTRACTS.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        flow = document["flow"]
        flow["consumes"] = [ARTIFACT_RENAMES.get(item, item) for item in flow["consumes"]]
        flow["produces"] = ARTIFACT_RENAMES.get(flow["produces"], flow["produces"])
        for lang, audiences in document["locales"].items():
            rules = [*COMMON[lang], *FILE_RULES.get(path.name, {}).get(lang, [])]
            for audience, cell in audiences.items():
                updated = replace(cell, rules)
                update_inputs(updated, lang)
                audiences[audience] = updated
        document["boundary"] = replace(document.get("boundary", {}), BOUNDARY_RULES.get(path.name, []))
        document["self_sha256"] = canonical_self(document)
        rendered = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
        if rendered != path.read_text(encoding="utf-8"):
            path.write_text(rendered, encoding="utf-8")
            changed += 1
    auxiliary_changed = 0
    for relative_path, rules in AUXILIARY_RULES.items():
        path = ROOT / relative_path
        original = path.read_text(encoding="utf-8")
        updated = replace(original, rules)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            auxiliary_changed += 1
    print(f"PROMPT_DELIVERABLE_LANGUAGE_UPDATED contracts={changed} auxiliary={auxiliary_changed}")


if __name__ == "__main__":
    main()
