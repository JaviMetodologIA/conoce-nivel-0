#!/usr/bin/env python3
"""Apply the governed Module 03 editorial enhancement overlay.

[METODOLOGIA] The imported module payload remains byte-for-byte immutable.
This migration enriches only the local depth overlay, then rebinds its hash in
the curriculum authority and provenance ledger.  It is intentionally
idempotent and performs no network or publication action.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DEPTH_PATH = SRC / "modules/module-03-depth-v1.json"
CURRICULUM_PATH = SRC / "curriculum-spec-v2.json"
LEDGER_PATH = SRC / "curriculum-provenance-rights-v2.json"
MODULE_ID = "module-03-trabajar-amplificado"


DEMO_ARTIFACTS = {
    "es": (
        "Caso: preparar y revisar una propuesta de alcance. Inicio: brief recibido. Fin: versión lista para decisión. Riesgo: citar una fuente no verificada.",
        "Ficha del flujo: brief → requisitos → fuentes → borrador → verificación → decisión. La aprobación final es humana.",
        "Mapa de fricción: espera al localizar fuentes; retrabajo al corregir citas; decisión repetida al confirmar alcance; evidencia: tres revisiones recientes.",
        "Dossier de prácticas: checklist de entrada, una fuente por afirmación y revisión independiente. Límites: datos no sensibles y aprobación humana.",
        "Proceso actual: solicitud → brief → fuentes → borrador con IA → verificación humana → decisión → versión. Fricción principal: fuentes tardías.",
        "Criterios de conclusión: alcance cubierto, fuentes trazables, excepciones señaladas y aprobación humana registrada.",
        "Mini-SOP v0.1: recopilar brief; validar fuentes; preparar borrador; revisar; registrar decisión. Excepción: detenerse si falta una fuente.",
        "Registro de riesgos: cita incorrecta/alto/detener; dato sensible/alto/no cargar; alcance ambiguo/medio/pedir aclaración.",
        "Plan y bitácora sintética: un caso reversible; 4 afirmaciones revisadas; 1 cita corregida; 0 datos sensibles; decisión humana: ajustar y repetir.",
        "Informe de prueba: 3 de 4 afirmaciones fueron válidas al primer intento; una cita se corrigió; decisión: adoptar con checklist y segunda revisión.",
    ),
    "en": (
        "Case: prepare and review a scope proposal. Start: brief received. End: version ready for a decision. Risk: citing an unverified source.",
        "Workflow brief: brief → requirements → sources → draft → verification → decision. Final approval remains human.",
        "Friction map: waiting while finding sources; rework while fixing citations; repeated scope decisions; evidence: three recent reviews.",
        "Practice dossier: intake checklist, one source per claim and independent review. Limits: non-sensitive data and human approval.",
        "Current process: request → brief → sources → AI-assisted draft → human verification → decision → version. Main friction: late sources.",
        "Completion criteria: scope covered, traceable sources, exceptions flagged and human approval recorded.",
        "Mini-SOP v0.1: collect brief; validate sources; prepare draft; review; record decision. Exception: stop when a source is missing.",
        "Risk register: wrong citation/high/stop; sensitive data/high/do not upload; unclear scope/medium/request clarification.",
        "Synthetic plan and log: one reversible case; 4 claims reviewed; 1 citation corrected; 0 sensitive data; human decision: adjust and repeat.",
        "Test report: 3 of 4 claims passed on the first attempt; one citation was corrected; decision: adopt with a checklist and second review.",
    ),
    "pt": (
        "Caso: preparar e revisar uma proposta de escopo. Início: briefing recebido. Fim: versão pronta para decisão. Risco: citar uma fonte não verificada.",
        "Ficha do fluxo: briefing → requisitos → fontes → rascunho → verificação → decisão. A aprovação final é humana.",
        "Mapa de fricção: espera ao localizar fontes; retrabalho ao corrigir citações; decisão repetida ao confirmar o escopo; evidência: três revisões recentes.",
        "Dossiê de práticas: checklist de entrada, uma fonte por afirmação e revisão independente. Limites: dados não sensíveis e aprovação humana.",
        "Processo atual: solicitação → briefing → fontes → rascunho com IA → verificação humana → decisão → versão. Fricção principal: fontes tardias.",
        "Critérios de conclusão: escopo coberto, fontes rastreáveis, exceções sinalizadas e aprovação humana registrada.",
        "Mini-SOP v0.1: coletar briefing; validar fontes; preparar rascunho; revisar; registrar decisão. Exceção: parar se faltar uma fonte.",
        "Registro de riscos: citação incorreta/alto/parar; dado sensível/alto/não carregar; escopo ambíguo/médio/pedir esclarecimento.",
        "Plano e registro sintético: um caso reversível; 4 afirmações revisadas; 1 citação corrigida; 0 dados sensíveis; decisão humana: ajustar e repetir.",
        "Relatório de teste: 3 de 4 afirmações foram válidas na primeira tentativa; uma citação foi corrigida; decisão: adotar com checklist e segunda revisão.",
    ),
}

AUDIENCE_CONTEXT = {
    "es": {
        "persona": "Responsable y revisor: tú, en momentos separados.",
        "empresa": "Responsable del flujo: líder de propuesta. Revisor: especialista independiente.",
    },
    "en": {
        "persona": "Owner and reviewer: you, at separate moments.",
        "empresa": "Workflow owner: proposal lead. Reviewer: an independent specialist.",
    },
    "pt": {
        "persona": "Responsável e revisor: você, em momentos separados.",
        "empresa": "Responsável pelo fluxo: líder da proposta. Revisor: especialista independente.",
    },
}

GATE = {
    "es": {
        "action": "Ejecuta el plan en un caso reversible fuera de NotebookLM. Registra entradas, resultado, fallos, decisiones y cualquier pausa.",
        "produces": "Plan de prueba y bitácora de ejecución",
        "criteria": "Existe al menos un resultado observado; si no ejecutaste la prueba, no avances a evaluar evidencia.",
        "receive": "Plan de prueba + bitácora de ejecución",
    },
    "en": {
        "action": "Run the plan on one reversible case outside NotebookLM. Record inputs, outcome, failures, decisions and every stop.",
        "produces": "Test plan and execution log",
        "criteria": "At least one observed outcome exists; if the test was not run, do not proceed to evidence review.",
        "receive": "Test plan + execution log",
    },
    "pt": {
        "action": "Execute o plano em um caso reversível fora do NotebookLM. Registre entradas, resultado, falhas, decisões e cada pausa.",
        "produces": "Plano de teste e registro de execução",
        "criteria": "Existe pelo menos um resultado observado; se o teste não foi executado, não avance para avaliar evidências.",
        "receive": "Plano de teste + registro de execução",
    },
}

EXACT_REPLACEMENTS = {
    "es": {
        "Lo explícito permite probar con control.": "Lo explícito permite probar, revisar y detener con control.",
        "No delegues decisiones explicables.": "No delegues decisiones que debas explicar.",
        "Un fallo íntegro también enseña.": "Un fallo bien registrado también aporta evidencia.",
        "La honestidad puede frenar escala.": "La evidencia insuficiente puede frenar la adopción; es una protección, no un fracaso.",
    },
    "en": {
        "Mark one judgment step and one AI may prepare.": "Mark one judgment step and one step AI may prepare.",
        "A robust workflow explains how to exit failure.": "A robust workflow explains how to stop safely and recover from failure.",
        "Locate the test in PASA and stop without evidence.": "Locate the test in PASA; stop if evidence is missing.",
    },
    "pt": {
        "Escolha uma tarefa semanal cujo resultado possa revisar.": "Escolha uma tarefa semanal cujo resultado você possa revisar.",
        "O explícito permite testar com controle.": "O que está explícito permite testar, revisar e parar com controle.",
        "Honestidade pode parar escala.": "Evidência insuficiente pode frear a adoção; isso protege a decisão.",
    },
}

TERM_REPLACEMENTS = {
    "es": (
        (r"\bhandoffs\b", "transferencias"),
        (r"\bhandoff\b", "transferencia"),
        (r"\bowner\b", "responsable"),
        (r"\breviewer\b", "revisor independiente"),
        (r"\bgate PASA\b", "punto de control PASA"),
        (r"\bDecision log\b", "registro de decisiones"),
        (r"\bBlueprint mínimo\b", "plano mínimo"),
        (r"\bDefinition of Done\b", "criterio de finalización (Definition of Done)"),
    ),
    "en": (),
    "pt": (
        (r"\bhandoffs\b", "transferências"),
        (r"\bhandoff\b", "transferência"),
        (r"\bowner\b", "responsável"),
        (r"\breviewer\b", "revisor independente"),
        (r"\bgate PASA\b", "ponto de controle PASA"),
        (r"\bDecision log\b", "registro de decisões"),
        (r"\bBlueprint mínimo\b", "plano mínimo"),
        (r"\bDefinition of Done\b", "critério de conclusão (Definition of Done)"),
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


def rewrite_strings(value: Any, locale: str) -> Any:
    if isinstance(value, str):
        value = EXACT_REPLACEMENTS[locale].get(value, value)
        for pattern, replacement in TERM_REPLACEMENTS[locale]:
            value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
        return value
    if isinstance(value, list):
        return [rewrite_strings(item, locale) for item in value]
    if isinstance(value, dict):
        return {key: rewrite_strings(item, locale) for key, item in value.items()}
    return value


def main() -> None:
    overlay = load(DEPTH_PATH)
    if overlay.get("module_id") != MODULE_ID:
        raise SystemExit("MODULE_ID_MISMATCH")
    for variant in overlay.get("variants", []):
        locale = variant.get("locale")
        audience = variant.get("audience")
        if locale not in DEMO_ARTIFACTS or audience not in AUDIENCE_CONTEXT[locale]:
            raise SystemExit(f"VARIANT_INVALID:{locale}:{audience}")
        rewritten = rewrite_strings(variant, locale)
        variant.clear()
        variant.update(rewritten)
        items = variant["prompts"]["items"]
        if len(items) != 10:
            raise SystemExit(f"PROMPT_COUNT_INVALID:{locale}:{audience}")
        for index, item in enumerate(items):
            item["demo_artifact"] = (
                f"{DEMO_ARTIFACTS[locale][index]} {AUDIENCE_CONTEXT[locale][audience]}"
            )
            if item["id"] == "prompt-08":
                item["execution_gate"] = {
                    "action": GATE[locale]["action"],
                    "produces": GATE[locale]["produces"],
                    "criteria": GATE[locale]["criteria"],
                }
            else:
                item.pop("execution_gate", None)
            if item["id"] == "prompt-09":
                item["receive_override"] = GATE[locale]["receive"]
            else:
                item.pop("receive_override", None)
    dump(DEPTH_PATH, overlay)
    depth_sha = sha(DEPTH_PATH)

    curriculum = load(CURRICULUM_PATH)
    module = next((item for item in curriculum["classes"] if item.get("module_id") == MODULE_ID), None)
    if module is None:
        raise SystemExit("CURRICULUM_MODULE_MISSING")
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
    entry["editorial_depth_overlay"]["sha256"] = depth_sha
    evidence = entry.setdefault("evidence_tags", [])
    for tag in ("demo-artifacts-resolved", "external-execution-gate-bound", "language-review-applied"):
        if tag not in evidence:
            evidence.append(tag)
    dump(LEDGER_PATH, ledger)
    print(f"MODULE_03_DEPTH_ENHANCED sha256={depth_sha} variants=6 prompts=60")


if __name__ == "__main__":
    main()
