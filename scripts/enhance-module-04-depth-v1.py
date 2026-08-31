#!/usr/bin/env python3
"""Apply the governed Module 04 editorial enhancement overlay.

[METODOLOGIA] The imported module payload remains byte-for-byte immutable.
This idempotent migration enriches only the local depth overlay, then rebinds
its hash in the curriculum authority and provenance ledger. It performs no
network, publication, or external execution action.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
BASE_PATH = SRC / "modules/module-04-content-v1.json"
DEPTH_PATH = SRC / "modules/module-04-depth-v1.json"
CURRICULUM_PATH = SRC / "curriculum-spec-v2.json"
LEDGER_PATH = SRC / "curriculum-provenance-rights-v2.json"
MODULE_ID = "module-04-trabajo-agentico"


# [PEDAGOGIA] Every artifact is enough to run its prompt independently in Demo
# mode. The sequence also forms one coherent, reversible case from selection to
# review. Persona and Empresa use materially different operating contexts.
DEMO_ARTIFACTS = {
    "es": {
        "persona": (
            "Selección: organizar 32 notas propias en Acción, Referencia o Archivo sobre una copia local. Descartado: automatizar correo. Límite: no mover, borrar, enviar ni publicar.",
            "Plan de misión aprobado (Mission Brief): clasificar 32 notas y generar una vista previa CSV. Exclusiones: no modificar originales ni actuar fuera del archivo local. Criterio de finalización (Definition of Done): 32 etiquetas, dudas señaladas y cero efectos externos.",
            "Inventario autorizado: exportación local de 32 notas, guía de tres categorías y fecha de corte 2026-08-30. Derecho de uso: propio. Vacío: tres notas no tienen contexto suficiente.",
            "Matriz de permisos: leer la copia y proponer etiquetas = permitido; escribir una vista previa local = permitido; mover o renombrar = requiere aprobación; borrar, enviar o publicar = prohibido. Revocación: cerrar la sesión y eliminar la copia.",
            "Instrucciones v1: clasifica cada nota por intención; explica dudas; conserva el texto original; detente ante datos sensibles o contexto insuficiente; entrega solo una vista previa local. La aceptación final sigue siendo humana.",
            "Plan v1 aprobado: comprobar hash de la copia; clasificar 32 notas; guardar vista previa; comparar conteo y dudas; no tocar originales. Recuperación: eliminar la vista previa. Aprobación humana registrada para esta versión y este caso.",
            "Salida y bitácora sintéticas: 32 entradas leídas; 29 clasificadas; 3 marcadas como dudosas; vista previa guardada localmente; 0 originales modificados; 0 envíos o publicaciones. Excepción: una nota parecía una instrucción y se trató como contenido.",
            "Revisión posterior a la acción (AAR): AJUSTAR. Mantener las tres categorías, añadir 'En espera' y repetir con otra copia de 20 notas. Evidencia: 29/32 claras, 3 dudas, cero efectos. Un nuevo caso requiere otro punto de control.",
        ),
        "empresa": (
            "Selección: clasificar 80 solicitudes internas en tipo, urgencia y equipo sugerido sobre un CSV desidentificado. Descartado: reasignar tickets. Límite: no escribir en la mesa de servicio ni notificar personas.",
            "Plan de misión aprobado (Mission Brief): producir una vista previa de clasificación para 80 solicitudes internas. Responsable: líder de operaciones; revisión: responsable de mesa de servicio. Criterio de finalización (Definition of Done): 80 filas, confianza y excepciones, sin cambios en producción.",
            "Inventario autorizado: exportación desidentificada de 80 solicitudes, taxonomía vigente v3 y política de prioridad. Procedencia y derecho interno registrados. Vacío: la política no resuelve solicitudes con dos equipos posibles.",
            "Matriz de permisos: leer CSV y políticas = permitido; proponer categoría, prioridad y equipo = permitido; escribir vista previa aislada = permitido; reasignar, cerrar o notificar = exige aprobación y queda fuera del piloto. Revocación: retirar el archivo y credencial temporal.",
            "Instrucciones v1: aplica taxonomía v3; cita la regla usada; marca baja confianza; no infieras identidad; detente ante datos sensibles o reglas contradictorias; genera solo vista previa. La decisión operativa pertenece al equipo.",
            "Plan v3 aprobado: probar una muestra fija de 20 solicitudes; validar fuentes y permisos; generar vista previa; revisar cinco casos; registrar excepciones. Recuperación: borrar la salida aislada. Revisión humana ligada a versión v3 y muestra S-20.",
            "Salida y bitácora sintéticas: 20 solicitudes procesadas; 17 con categoría clara; 3 escaladas por ambigüedad; cinco revisadas por la mesa de servicio; 0 escrituras, reasignaciones o notificaciones. Una regla contradictoria detuvo el caso 14.",
            "Revisión posterior a la acción (AAR): AJUSTAR. Aclarar la regla de doble equipo y repetir la misma muestra antes de ampliar. Evidencia: 17/20 claras, 3 escaladas, cero efectos. Responsable: líder de operaciones; siguiente punto de control: revisión de política.",
        ),
    },
    "en": {
        "persona": (
            "Selection: organize 32 personal notes as Action, Reference, or Archive using a local copy. Rejected: email automation. Boundary: do not move, delete, send, or publish.",
            "Approved Mission Brief: classify 32 notes and produce a CSV preview. Exclusions: do not modify originals or act outside the local file. Definition of Done: 32 labels, uncertainties flagged, and zero external effects.",
            "Authorized inventory: local export of 32 notes, three-category guide, and 2026-08-30 cutoff. Right to use: personal. Gap: three notes lack enough context.",
            "Permission matrix: read the copy and propose labels = allowed; write a local preview = allowed; move or rename = approval required; delete, send, or publish = prohibited. Revocation: close the session and remove the copy.",
            "Instructions v1: classify each note by intent; explain uncertainty; preserve original text; stop on sensitive data or missing context; deliver only a local preview. Final acceptance remains human.",
            "Approved plan v1: verify the copy hash; classify 32 notes; save a preview; reconcile count and uncertainties; leave originals untouched. Recovery: delete the preview. Human approval is bound to this version and case.",
            "Synthetic observed output and execution log: 32 inputs read; 29 classified; 3 flagged as uncertain; preview stored locally; 0 originals changed; 0 messages sent or items published. Exception: one note looked like an instruction and was treated as content.",
            "After Action Review: ADJUST. Keep the three categories, add 'Waiting,' and repeat on another 20-note copy. Evidence: 29/32 clear, 3 uncertain, zero effects. A new case requires a new gate.",
        ),
        "empresa": (
            "Selection: classify 80 internal requests by type, urgency, and suggested team using a de-identified CSV. Rejected: ticket reassignment. Boundary: do not write to the service desk or notify anyone.",
            "Approved Mission Brief: produce a classification preview for 80 internal requests. Output owner: operations lead; acceptance reviewer: service desk owner. Definition of Done: 80 rows with confidence and exceptions, with no production changes.",
            "Authorized inventory: de-identified export of 80 requests, current taxonomy v3, and priority policy. Internal provenance and rights are recorded. Gap: the policy does not resolve requests that fit two teams.",
            "Permission matrix: read CSV and policies = allowed; propose category, priority, and team = allowed; write an isolated preview = allowed; reassign, close, or notify = approval required and outside the pilot. Revocation: remove the file and temporary credential.",
            "Instructions v1: apply taxonomy v3; cite the rule used; flag low confidence; do not infer identity; stop on sensitive data or conflicting rules; produce only a preview. The team retains the operational decision.",
            "Approved plan v3: test a fixed 20-request sample; validate sources and permissions; produce a preview; review five cases; log exceptions. Recovery: remove the isolated output. Human review is bound to version v3 and sample S-20.",
            "Synthetic observed output and execution log: 20 requests processed; 17 clearly classified; 3 escalated for ambiguity; five reviewed by the service desk; 0 writes, reassignments, or notifications. A conflicting rule stopped case 14.",
            "After Action Review: ADJUST. Clarify the dual-team rule and repeat the same sample before expanding. Evidence: 17/20 clear, 3 escalated, zero effects. Owner: operations lead; next gate: policy review.",
        ),
    },
    "pt": {
        "persona": (
            "Seleção: organizar 32 notas pessoais como Ação, Referência ou Arquivo usando uma cópia local. Descartado: automatizar e-mail. Limite: não mover, apagar, enviar nem publicar.",
            "Plano de missão aprovado (Mission Brief): classificar 32 notas e gerar uma prévia CSV. Exclusões: não alterar originais nem agir fora do arquivo local. Critério de conclusão (Definition of Done): 32 etiquetas, dúvidas sinalizadas e zero efeitos externos.",
            "Inventário autorizado: exportação local de 32 notas, guia de três categorias e corte em 2026-08-30. Direito de uso: próprio. Lacuna: três notas não têm contexto suficiente.",
            "Matriz de permissões: ler a cópia e propor etiquetas = permitido; gravar uma prévia local = permitido; mover ou renomear = exige aprovação; apagar, enviar ou publicar = proibido. Revogação: encerrar a sessão e remover a cópia.",
            "Instruções v1: classifique cada nota pela intenção; explique dúvidas; preserve o texto original; pare diante de dados sensíveis ou contexto insuficiente; entregue apenas uma prévia local. A aceitação final continua humana.",
            "Plano v1 aprovado: verificar o hash da cópia; classificar 32 notas; salvar prévia; conferir contagem e dúvidas; não alterar originais. Recuperação: apagar a prévia. Aprovação humana vinculada a esta versão e a este caso.",
            "Saída observada e registro sintéticos: 32 entradas lidas; 29 classificadas; 3 marcadas como incertas; prévia salva localmente; 0 originais alterados; 0 envios ou publicações. Exceção: uma nota parecia instrução e foi tratada como conteúdo.",
            "Revisão pós-ação (AAR): AJUSTAR. Manter as três categorias, adicionar 'Em espera' e repetir com outra cópia de 20 notas. Evidência: 29/32 claras, 3 dúvidas, zero efeitos. Um novo caso exige outro ponto de controle.",
        ),
        "empresa": (
            "Seleção: classificar 80 solicitações internas por tipo, urgência e equipe sugerida usando CSV desidentificado. Descartado: reatribuir chamados. Limite: não escrever na central de serviços nem notificar pessoas.",
            "Plano de missão aprovado (Mission Brief): produzir uma prévia de classificação para 80 solicitações internas. Responsável: líder de operações; revisão: responsável pela central de serviços. Critério de conclusão (Definition of Done): 80 linhas, confiança e exceções, sem mudanças em produção.",
            "Inventário autorizado: exportação desidentificada de 80 solicitações, taxonomia vigente v3 e política de prioridade. Procedência e direito interno registrados. Lacuna: a política não resolve solicitações com duas equipes possíveis.",
            "Matriz de permissões: ler CSV e políticas = permitido; propor categoria, prioridade e equipe = permitido; gravar prévia isolada = permitido; reatribuir, fechar ou notificar = exige aprovação e fica fora do piloto. Revogação: remover arquivo e credencial temporária.",
            "Instruções v1: aplique a taxonomia v3; cite a regra usada; sinalize baixa confiança; não infira identidade; pare diante de dados sensíveis ou regras conflitantes; gere apenas uma prévia. A decisão operacional pertence à equipe.",
            "Plano v3 aprovado: testar amostra fixa de 20 solicitações; validar fontes e permissões; gerar prévia; revisar cinco casos; registrar exceções. Recuperação: apagar a saída isolada. Revisão humana vinculada à versão v3 e à amostra S-20.",
            "Saída observada e registro sintéticos: 20 solicitações processadas; 17 classificadas com clareza; 3 escaladas por ambiguidade; cinco revisadas pela central de serviços; 0 escritas, reatribuições ou notificações. Uma regra conflitante parou o caso 14.",
            "Revisão pós-ação (AAR): AJUSTAR. Esclarecer a regra de duas equipes e repetir a mesma amostra antes de ampliar. Evidência: 17/20 claras, 3 escaladas, zero efeitos. Responsável: líder de operações; próximo ponto de controle: revisão da política.",
        ),
    },
}

DEMO_CASE = {
    "es": {
        "persona": "Caso: organizar notas con fuentes autorizadas para preparar un resumen semanal. ",
        "empresa": "Caso: clasificar solicitudes internas sin enviar respuestas. ",
    },
    "en": {
        "persona": "Case: organize authorized source notes for a weekly summary. ",
        "empresa": "Case: classify internal requests without sending responses. ",
    },
    "pt": {
        "persona": "Caso: organizar notas com fontes autorizadas para preparar um resumo semanal. ",
        "empresa": "Caso: classificar solicitações internas sem enviar respostas. ",
    },
}


GATE = {
    "es": {
        "action": "Ejecuta el plan aprobado sobre una copia aislada fuera de NotebookLM. No envíes, publiques, muevas ni borres originales. Registra entrada, versión, salida observada, excepciones, decisiones y recuperación.",
        "produces": "Salida observada + bitácora de ejecución",
        "criteria": "La aprobación coincide con la versión ejecutada, existe al menos una salida observada y la bitácora confirma cero efectos externos. Si no ejecutaste la prueba, no avances.",
        "receive": "Plan aprobado + salida observada + bitácora de ejecución",
    },
    "en": {
        "action": "Run the approved plan on an isolated copy outside NotebookLM. Do not send, publish, move, or delete originals. Record input, version, observed output, exceptions, decisions, and recovery.",
        "produces": "Observed output + execution log",
        "criteria": "Approval matches the executed version, at least one observed output exists, and the log confirms zero external effects. If the test was not run, do not proceed.",
        "receive": "Approved plan + observed output + execution log",
    },
    "pt": {
        "action": "Execute o plano aprovado sobre uma cópia isolada fora do NotebookLM. Não envie, publique, mova nem apague originais. Registre entrada, versão, saída observada, exceções, decisões e recuperação.",
        "produces": "Saída observada + registro de execução",
        "criteria": "A aprovação corresponde à versão executada, existe pelo menos uma saída observada e o registro confirma zero efeitos externos. Se o teste não foi executado, não avance.",
        "receive": "Plano aprovado + saída observada + registro de execução",
    },
}


EXACT_REPLACEMENTS = {
    "es": {
        "Después del triage y antes del plan.": "Después de seleccionar el caso y antes de preparar el plan.",
        "Permisos estrechos exigen más gates, pero reducen efectos no previstos.": "Permisos estrechos exigen más puntos de control, pero reducen efectos no previstos.",
        "El gate añade revisión previa y evita corregir después del efecto. Un veredicto aprobado permite solicitar una ejecución controlada externa, pero no la realiza ni la autoriza por sí solo.": "El punto de control revisa antes de producir efectos. Aprobar el plan permite solicitar una prueba controlada separada, pero no la ejecuta ni la autoriza por sí solo.",
        "Emite veredicto, owner y siguiente gate.": "Emite veredicto, responsable y siguiente punto de control.",
    },
    "en": {},
    "pt": {
        "Após triagem e antes do plano.": "Após selecionar o caso e antes de preparar o plano.",
        "Permissões estreitas exigem mais gates e reduzem efeitos imprevistos.": "Permissões estreitas exigem mais pontos de controle e reduzem efeitos imprevistos.",
        "O gate adiciona revisão antes do efeito, não correção posterior. Um veredito aprovado pode apoiar a solicitação de execução controlada separada, mas não a realiza nem autoriza por si só.": "O ponto de controle revisa antes de produzir efeitos. Aprovar o plano permite solicitar um teste controlado separado, mas não o executa nem autoriza por si só.",
        "Emita veredito, responsável e próximo gate.": "Emita veredito, responsável e próximo ponto de controle.",
    },
}


TERM_REPLACEMENTS = {
    "es": (
        (r"\bMission Brief \(brief de misión: contrato acotado\)", "Plan de misión (Mission Brief)"),
        (r"\bDefinition of Done \(definición de terminado\)", "criterio de finalización (Definition of Done)"),
        (r"\bExecution Log \(registro de ejecución\)", "bitácora de ejecución (Execution Log)"),
        (r"\bowner\b", "responsable"),
        (r"\breviewer\b", "persona revisora"),
        (r"\bgates\b", "puntos de control"),
        (r"\bgate\b", "punto de control"),
    ),
    "en": (),
    "pt": (
        (r"\bMission Brief \(brief de missão: contrato delimitado\)", "Plano de missão (Mission Brief)"),
        (r"\bDefinition of Done \(definição de concluído\)", "critério de conclusão (Definition of Done)"),
        (r"\bExecution Log \(registro de execução\)", "registro de execução (Execution Log)"),
        (r"\bowner\b", "responsável"),
        (r"\breviewer\b", "pessoa revisora"),
        (r"\bgates\b", "pontos de controle"),
        (r"\bgate\b", "ponto de controle"),
    ),
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"EXPECTED_OBJECT:{path}")
    return value


def dump(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


STRUCTURAL_KEYS = {
    "id",
    "next",
    "module_id",
    "moment_ids",
    "concept_ids",
    "authority_refs",
    "consumeIds",
    "produceId",
}


def restore_structural_string(value: str) -> str:
    """Undo prose localization inside governed identifiers from older drafts."""

    repairs = (
        ("puntos de control", "gates"),
        ("punto de control", "gate"),
        ("pontos de controle", "gates"),
        ("ponto de controle", "gate"),
        ("persona revisora", "reviewer"),
        ("pessoa revisora", "reviewer"),
        ("responsable", "owner"),
        ("responsável", "owner"),
    )
    for localized, canonical in repairs:
        value = value.replace(localized, canonical)
    return value


def rewrite_strings(value: Any, locale: str, field: str | None = None) -> Any:
    if isinstance(value, str):
        if field in STRUCTURAL_KEYS:
            return restore_structural_string(value)
        value = EXACT_REPLACEMENTS[locale].get(value, value)
        for pattern, replacement in TERM_REPLACEMENTS[locale]:
            value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
        return value
    if isinstance(value, list):
        return [rewrite_strings(item, locale, field) for item in value]
    if isinstance(value, dict):
        return {key: rewrite_strings(item, locale, key) for key, item in value.items()}
    return value


def main() -> None:
    overlay = load(DEPTH_PATH)
    if overlay.get("module_id") != MODULE_ID:
        raise SystemExit("MODULE_ID_MISMATCH")
    base_sha = sha(BASE_PATH)
    if overlay.get("base_payload_sha256") != base_sha:
        raise SystemExit("BASE_PAYLOAD_HASH_MISMATCH")

    variants = overlay.get("variants", [])
    if len(variants) != 6:
        raise SystemExit(f"VARIANT_COUNT_INVALID:{len(variants)}")
    seen: set[tuple[str, str]] = set()
    for variant in variants:
        locale = variant.get("locale")
        audience = variant.get("audience")
        key = (locale, audience)
        if locale not in DEMO_ARTIFACTS or audience not in DEMO_ARTIFACTS[locale] or key in seen:
            raise SystemExit(f"VARIANT_INVALID:{locale}:{audience}")
        seen.add(key)
        rewritten = rewrite_strings(variant, locale)
        variant.clear()
        variant.update(rewritten)
        items = variant["prompts"]["items"]
        if len(items) != 8 or [item.get("id") for item in items] != [f"prompt-{index:02d}" for index in range(1, 9)]:
            raise SystemExit(f"PROMPT_SEQUENCE_INVALID:{locale}:{audience}")
        for index, item in enumerate(items):
            item["demo_artifact"] = DEMO_CASE[locale][audience] + DEMO_ARTIFACTS[locale][audience][index]
            if item["id"] == "prompt-06":
                item["execution_gate"] = {
                    "action": GATE[locale]["action"],
                    "produces": GATE[locale]["produces"],
                    "criteria": GATE[locale]["criteria"],
                }
            else:
                item.pop("execution_gate", None)
            if item["id"] == "prompt-07":
                item["receive_override"] = GATE[locale]["receive"]
            else:
                item.pop("receive_override", None)
    dump(DEPTH_PATH, overlay)
    depth_sha = sha(DEPTH_PATH)

    curriculum = load(CURRICULUM_PATH)
    module = next((item for item in curriculum["classes"] if item.get("module_id") == MODULE_ID), None)
    if module is None:
        raise SystemExit("CURRICULUM_MODULE_MISSING")
    if module["content"].get("sha256") != base_sha:
        raise SystemExit("CURRICULUM_BASE_HASH_MISMATCH")
    old_depth_sha = module["depth_overlay"]["sha256"]
    module["depth_overlay"]["sha256"] = depth_sha
    module["evidence_tags"] = [
        f"depth-overlay:sha256:{depth_sha}" if tag == f"depth-overlay:sha256:{old_depth_sha}" else tag
        for tag in module["evidence_tags"]
    ]
    dump(CURRICULUM_PATH, curriculum)

    ledger = load(LEDGER_PATH)
    entry = next((item for item in ledger["entries"] if item.get("module_id") == MODULE_ID), None)
    if entry is None:
        raise SystemExit("LEDGER_MODULE_MISSING")
    if entry["payload"].get("imported_sha256") != base_sha or entry["payload"].get("exact_copy") is not True:
        raise SystemExit("LEDGER_BASE_BINDING_INVALID")
    entry["editorial_depth_overlay"]["sha256"] = depth_sha
    evidence = entry.setdefault("evidence_tags", [])
    for tag in ("demo-artifacts-resolved", "external-execution-gate-bound", "language-review-applied"):
        if tag not in evidence:
            evidence.append(tag)
    dump(LEDGER_PATH, ledger)
    print(f"MODULE_04_DEPTH_ENHANCED sha256={depth_sha} variants=6 prompts=48 base_sha256={base_sha}")


if __name__ == "__main__":
    main()
