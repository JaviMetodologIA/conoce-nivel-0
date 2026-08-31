#!/usr/bin/env python3
"""Unit contract for the pure Nivel 0 module renderers."""

from __future__ import annotations

import importlib.util
import sys
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("module_renderers", ROOT / "scripts" / "module_renderers.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.ids.extend(value for key, value in attrs if key == "id" and value is not None)


def fixture() -> dict:
    evidence = ["ev-official-pdf"]
    prompt_base = "Analiza <CONTEXTO>. [Explica un límite.]"
    return {
        "locale": "es",
        "audience": "persona",
        "module": {
            "moduleId": "module-02-demo",
            "order": 2,
            "title": "Demo segura",
            "challenge": "Separar actividad de avance.",
            "promise": "Construir una práctica visible.",
            "practice": "Probar una decisión acotada.",
            "evidence": "Un resultado revisable.",
            "transfer": "Repetir la práctica en otro contexto.",
            "claimIds": ["claim-demo"],
            "masterclass": {
                "title": "Masterclass demo",
                "lede": "El PDF ocupa el centro de la experiencia.",
                "accessibleGuide": {
                    "languageDeclared": True,
                    "landmarks": True,
                    "keyboardNavigable": True,
                    "pdfTagged": False,
                    "warning": "El PDF no está etiquetado; usa la guía HTML.",
                },
                "moments": [
                    {
                        "id": "moment-01",
                        "title": "Observar",
                        "body": "Describe el punto de partida.",
                        "baseMinutes": 5,
                        "extendedMinutes": 2,
                        "pdfPage": 1,
                        "evidenceIds": evidence,
                    },
                    {
                        "id": "moment-02",
                        "title": "Decidir",
                        "body": "Elige el siguiente paso.",
                        "baseMinutes": 5,
                        "extendedMinutes": 2,
                        "pdfPage": 2,
                        "evidenceIds": evidence,
                    },
                ],
            },
            "workbook": {
                "title": "Workbook demo",
                "lede": "Tres recorridos breves.",
                "routes": [
                    {
                        "id": f"wb-{route}",
                        "title": route.title(),
                        "purpose": f"Propósito {route}.",
                        "steps": [
                            {
                                "id": f"wb-{route}-01",
                                "instruction": f"Ejecuta {route}.",
                                "evidenceIds": evidence,
                            }
                        ],
                    }
                    for route in ("preparar", "practicar", "transferir")
                ],
            },
            "playbook": {
                "title": "Playbook demo",
                "lede": "Una secuencia operativa.",
                "chapters": [
                    {
                        "id": "pb-observar",
                        "title": "Observar",
                        "purpose": "Entender antes de cambiar.",
                        "steps": [
                            {
                                "id": "pb-observar-01",
                                "instruction": "Registra el estado actual.",
                                "evidenceIds": evidence,
                            }
                        ],
                    }
                ],
            },
            "promptLibrary": {
                "title": "Prompts demo",
                "lede": "Usa Chat o Fuentes según la tarea.",
                "prompts": [
                    {
                        "id": "prompt-01",
                        "title": "Diagnóstico",
                        "receive": "wb-preparar-01",
                        "produces": "Mapa inicial",
                        "consumeIds": ["wb-preparar-01"],
                        "evidenceIds": evidence,
                        "surface": "chat",
                        "syntax": {
                            "inputs": [
                                {
                                    "name": "CONTEXTO",
                                    "description": "Describe el caso",
                                    "example": "una semana real",
                                    "required": True,
                                }
                            ],
                            "parameters": {"length": "concise"},
                            "optionalInstruction": True,
                        },
                        "template": prompt_base,
                        "demo": "Analiza una semana sintética; no inventes datos.",
                        "levels": [
                            {"level": level, "body": f"N{level}: {prompt_base}"}
                            for level in range(1, 5)
                        ],
                    }
                ],
            },
        },
    }


URLS = {
    "masterclass": "../masterclass/index.html",
    "workbook": "../workbook/index.html",
    "playbook": "../playbook/index.html",
    "prompts": "../prompts/index.html",
    "resources": "../../../recursos/index.html",
    "pdf": "../../../assets/module-02.pdf",
    "pdf_sha256": "a" * 64,
    "pdf_tagged": False,
    "next": "../../03-demo/masterclass/index.html",
    "next_label": "Módulo 03",
}

ARTIFACT_LABELS = {"wb-preparar-01": "bitácora de la semana"}


def main() -> None:
    variant = fixture()
    first = MODULE.render_module_bundle(variant, URLS, artifact_labels=ARTIFACT_LABELS)
    second = MODULE.render_module_bundle(variant, URLS, artifact_labels=ARTIFACT_LABELS)
    assert first == second, "renderers must be deterministic"
    assert set(first) == {"masterclass", "workbook", "playbook", "prompts"}
    assert first["masterclass"].count('class="slide active"') == 1
    assert 'aria-valuemax="2"' in first["masterclass"]
    assert all(f'id="{panel}"' in first["workbook"] for panel in ("sheet-session", "sheet-depth", "sheet-consolidation"))
    assert tuple(MODULE.WORKBOOK_STAGE_LABELS["es"]) == ("En clase", "Profundización", "Consolidación")
    assert all(f'data-workbook-stage="{stage}"' in first["workbook"] for stage in ("in-class", "deepening", "consolidation"))
    assert 'id="intro"' in first["playbook"] and 'id="close"' in first["playbook"]
    assert first["prompts"].count("data-prompt-level=") == 4
    assert 'href="../../03-demo/masterclass/index.html"' in first["prompts"]
    assert 'href="../../03-demo/masterclass/index.html"' not in first["workbook"]
    for resource, markup in first.items():
        collector = IdCollector()
        collector.feed(markup)
        assert len(collector.ids) == len(set(collector.ids)), f"duplicate id in {resource}"
        assert "A²" not in markup and "method-mark" not in markup and "founder" not in markup
        assert "<img" not in markup
    unsafe = dict(URLS, pdf="javascript:alert(1)")
    try:
        MODULE.render_module_bundle(variant, unsafe, artifact_labels=ARTIFACT_LABELS)
    except MODULE.RendererContractError:
        pass
    else:
        raise AssertionError("unsafe PDF URL was accepted")
    print("MODULE_RENDERERS_V2_OK: 4 deterministic interiors, unique IDs, safe URLs")


if __name__ == "__main__":
    main()
