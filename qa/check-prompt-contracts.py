#!/usr/bin/env python3
"""Standalone validator for src/prompt-contracts/*.json (prompt-intent-contract-v1).

An empty or missing contracts directory is a PASS with a note: the schema and
authority land in phase 1, the contracts themselves are authored in phase 3.
Built-in mutations guarantee the gate rejects known failure classes.
"""
from __future__ import annotations
import copy, hashlib, json, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
CONTRACTS_DIR = SRC / 'prompt-contracts'
LANGS = ('es', 'en', 'pt')
AUDIENCES = ('persona', 'empresa')
LIB_IDS = ('01', '02', '03', '04', '05', '06', '07', '08', '09', '10', 'M1', 'M2', 'M3', 'M4')
SURFACE_IDS = {
    'library': LIB_IDS,
    'workbook': tuple(f'W{i:02d}' for i in range(1, 11)),
    'workbook_brain': ('B1', 'B2', 'B3'),
}
ALL_IDS = [pid for ids in SURFACE_IDS.values() for pid in ids]
MATERIAL_FIELDS = ('purpose', 'when', 'example', 'evidence', 'prompt')
CELL_FIELDS = {'title', *MATERIAL_FIELDS, 'level_spec', 'why_it_works', 'traceability'}
LEVEL_SPEC_FIELDS = {'role', 'spec_role', 'objective', 'parameters', 'workflow', 'guardrails', 'output', 'dod', 'edge_cases'}
WHY_FIELDS = {'acceptance_criteria', 'edge_cases', 'tradeoffs', 'assumptions', 'limits'}
SELF_HASH_MODEL = 'sha256(sorted-json-without-self_sha256)'


def norm(value: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))


def canonical_self(value: dict, field: str) -> str:
    payload = {key: item for key, item in value.items() if key != field}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


LIBRARY = json.loads((SRC / 'prompt-library-spec-v1.json').read_text(encoding='utf-8'))
LEDGER = json.loads((SRC / 'claim-ledger.json').read_text(encoding='utf-8'))
AUTHORITY = json.loads((SRC / 'prompt-intent-authority-v2.json').read_text(encoding='utf-8'))
BASELINE = {locale: json.loads((ROOT / f'snapshots/baseline/prompt-snapshot-{locale}.json').read_text(encoding='utf-8')) for locale in LANGS}
MINIMUMS = LIBRARY['spec_contract']['semantic_specificity']['minimum_characters']
MIN_VARIABLES = LIBRARY['spec_contract']['semantic_specificity']['minimum_distinct_variables']
TRACE_ALLOWLIST = (
    {item['url'] for item in LIBRARY['reference_sources']}
    | {claim['source'] for claim in LEDGER['claims']}
    | {'method_internal'}
)

# Authority v2 integrity: shape essentials, canonical self hash, unique signatures.
if AUTHORITY.get('schema_version') != 'prompt-intent-authority-v2' or AUTHORITY.get('status') != 'provisional_until_phase_3':
    raise SystemExit('PROMPT_CONTRACT_AUTHORITY_SHAPE_INVALID')
if AUTHORITY.get('self_hash_model') != SELF_HASH_MODEL or AUTHORITY.get('self_sha256') != canonical_self(AUTHORITY, 'self_sha256'):
    raise SystemExit('PROMPT_CONTRACT_AUTHORITY_SELF_DRIFT')
if AUTHORITY.get('anchor_policy', {}).get('prompt_ids') != ALL_IDS or set(AUTHORITY.get('locales', {})) != set(LANGS):
    raise SystemExit('PROMPT_CONTRACT_AUTHORITY_MATRIX_INVALID')
for locale in LANGS:
    entries = AUTHORITY['locales'][locale]
    if set(entries) != set(ALL_IDS):
        raise SystemExit(f'PROMPT_CONTRACT_AUTHORITY_MATRIX_INVALID:{locale}')
    signatures = [tuple(sorted(entries[pid]['intent'] + entries[pid]['evidence'])) for pid in ALL_IDS]
    if len(set(signatures)) != len(signatures):
        raise SystemExit(f'PROMPT_CONTRACT_AUTHORITY_SIGNATURE_CLONE:{locale}')


def validate_contract(contract: dict) -> None:
    required = {'schema_version', 'intent_id', 'surface', 'phase', 'state', 'publication_authorized', 'boundary', 'locales', 'self_hash_model', 'self_sha256'}
    intent_id = contract.get('intent_id')
    if set(contract) != required or contract.get('schema_version') != 'prompt-intent-contract-v1':
        raise SystemExit(f'PROMPT_CONTRACT_SHAPE_INVALID:{intent_id}')
    surface = contract['surface']
    if surface not in SURFACE_IDS or intent_id not in SURFACE_IDS[surface]:
        raise SystemExit(f'PROMPT_CONTRACT_SURFACE_INVALID:{surface}:{intent_id}')
    if contract['state'] != 'RENDERED_DRAFT' or contract['publication_authorized'] is not False:
        raise SystemExit(f'PROMPT_CONTRACT_GOVERNANCE_INVALID:{intent_id}')
    if not isinstance(contract['phase'], str) or not contract['phase'].strip():
        raise SystemExit(f'PROMPT_CONTRACT_PHASE_INVALID:{intent_id}')
    boundary = contract['boundary']
    if set(boundary) != {'distinct_from', 'decision_rule'} or not isinstance(boundary['distinct_from'], list) or not str(boundary['decision_rule']).strip():
        raise SystemExit(f'PROMPT_CONTRACT_BOUNDARY_INVALID:{intent_id}')
    if contract['self_hash_model'] != SELF_HASH_MODEL or contract['self_sha256'] != canonical_self(contract, 'self_sha256'):
        raise SystemExit(f'PROMPT_CONTRACT_SELF_DRIFT:{intent_id}')
    if set(contract['locales']) != set(LANGS):
        raise SystemExit(f'PROMPT_CONTRACT_CELL_MATRIX:{intent_id}')
    for locale in LANGS:
        localized = contract['locales'][locale]
        if set(localized) != set(AUDIENCES):
            raise SystemExit(f'PROMPT_CONTRACT_CELL_MATRIX:{intent_id}:{locale}')
        anchors = AUTHORITY['locales'][locale][intent_id]
        for audience in AUDIENCES:
            cell = localized[audience]
            where = f'{locale}:{audience}:{intent_id}'
            if set(cell) != CELL_FIELDS or any(not isinstance(cell[field], str) or not cell[field].strip() for field in ('title', *MATERIAL_FIELDS)):
                raise SystemExit(f'PROMPT_CONTRACT_CELL_SHAPE_INVALID:{where}')
            level_spec = cell['level_spec']
            if set(level_spec) != LEVEL_SPEC_FIELDS or any(not level_spec[field] for field in LEVEL_SPEC_FIELDS):
                raise SystemExit(f'PROMPT_CONTRACT_LEVEL_SPEC_INVALID:{where}')
            if any(not isinstance(pair, list) or len(pair) != 2 or not all(isinstance(part, str) and part.strip() for part in pair) for pair in level_spec['parameters']):
                raise SystemExit(f'PROMPT_CONTRACT_LEVEL_SPEC_PARAMETERS_INVALID:{where}')
            why = cell['why_it_works']
            if set(why) != WHY_FIELDS or any(not isinstance(why[field], list) or not why[field] for field in WHY_FIELDS):
                raise SystemExit(f'PROMPT_CONTRACT_WHY_INVALID:{where}')
            for field, minimum in MINIMUMS.items():
                if len(cell[field].strip()) < minimum:
                    raise SystemExit(f'PROMPT_CONTRACT_FIELD_GENERIC:{where}:{field}')
            variables = {value.strip().casefold() for value in re.findall(r'\[([^]]+)\]', cell['prompt']) if value.strip()}
            if len(variables) < MIN_VARIABLES:
                raise SystemExit(f'PROMPT_CONTRACT_VARIABLES:{where}')
            prompt_text = norm(cell['prompt'])
            intro_text = norm(cell['title'] + ' ' + cell['purpose'])
            evidence_text = norm(cell['evidence'])
            for anchor in anchors['intent']:
                normalized = norm(anchor)
                if len(normalized) < 4 or (normalized not in prompt_text and normalized not in intro_text):
                    raise SystemExit(f'PROMPT_CONTRACT_INTENT_ANCHOR_MISSING:{where}:{anchor}')
            for anchor in anchors['evidence']:
                normalized = norm(anchor)
                if len(normalized) < 4 or normalized not in prompt_text or normalized not in evidence_text:
                    raise SystemExit(f'PROMPT_CONTRACT_EVIDENCE_ANCHOR_MISSING:{where}:{anchor}')
            baseline_key = f'{surface}/{intent_id}/{locale}/{audience}/natural'
            baseline = BASELINE[locale].get(baseline_key)
            if baseline is None:
                raise SystemExit(f'PROMPT_CONTRACT_BASELINE_MISSING:{where}')
            if len(cell['prompt']) > 2 * baseline['chars']:
                raise SystemExit(f'PROMPT_CONTRACT_LENGTH_EXCESS:{where}:{len(cell["prompt"])}>{2 * baseline["chars"]}')
            trace = cell['traceability']
            if not isinstance(trace, list) or not trace:
                raise SystemExit(f'PROMPT_CONTRACT_TRACE_INVALID:{where}')
            for entry in trace:
                if set(entry) != {'claim', 'source'} or not str(entry['claim']).strip() or entry['source'] not in TRACE_ALLOWLIST:
                    raise SystemExit(f'PROMPT_CONTRACT_TRACE_INVALID:{where}:{entry.get("source")}')
        persona, empresa = localized['persona'], localized['empresa']
        for field in MATERIAL_FIELDS:
            if persona[field].casefold() == empresa[field].casefold():
                raise SystemExit(f'PROMPT_CONTRACT_AUDIENCE_CLONE:{locale}:{intent_id}:{field}')


def validate_set(contracts: list[dict]) -> None:
    seen = [contract.get('intent_id') for contract in contracts]
    if len(set(seen)) != len(seen):
        raise SystemExit(f'PROMPT_CONTRACT_DUPLICATE_INTENT:{sorted(pid for pid in set(seen) if seen.count(pid) > 1)}')
    for contract in contracts:
        validate_contract(contract)


# --- Built-in mutations: a synthetic valid contract must pass, mutants must fail.

def synthetic_contract() -> dict:
    suffix = {
        'es': ' Ajusta el resultado al equipo de la organización.',
        'en': ' Adapt the result to the organization team.',
        'pt': ' Ajuste o resultado à equipe da organização.',
    }
    locales = {}
    for locale in LANGS:
        item = next(entry for entry in LIBRARY['locales'][locale]['items'] if entry['id'] == '01')
        cells = {}
        for audience in AUDIENCES:
            extra = '' if audience == 'persona' else suffix[locale]
            cells[audience] = {
                'title': item['title'],
                'purpose': item['purpose'] + extra,
                'when': item['when'] + extra,
                'example': item['example'] + extra,
                'evidence': item['evidence'] + extra,
                'prompt': item['prompt'] + extra,
                'level_spec': {
                    'role': 'Asistente MetodologIA orientado a evidencia',
                    'spec_role': LIBRARY['locales'][locale]['spec_format']['default_role'],
                    'objective': item['title'],
                    'parameters': [['profundidad', 'operativa'], ['formato', 'estructurado']],
                    'workflow': [item['purpose']],
                    'guardrails': ['No inventar fuentes, citas o capacidades'],
                    'output': [item['evidence']],
                    'dod': 'Entrega revisable con límites declarados.',
                    'edge_cases': ['Fuentes insuficientes: declarar coverage_gap.'],
                },
                'why_it_works': {
                    'acceptance_criteria': ['Cita fuentes revisables.'],
                    'edge_cases': ['Base insuficiente: se declara.'],
                    'tradeoffs': ['Menos amplitud, más verificabilidad.'],
                    'assumptions': ['Existen fuentes con derechos de uso.'],
                    'limits': ['No garantiza exactitud.'],
                },
                'traceability': [{'claim': 'Convención de cuatro niveles del método.', 'source': LIBRARY['reference_sources'][0]['url']}],
            }
        locales[locale] = cells
    contract = {
        'schema_version': 'prompt-intent-contract-v1',
        'intent_id': '01',
        'surface': 'library',
        'phase': 'Aprender',
        'state': 'RENDERED_DRAFT',
        'publication_authorized': False,
        'boundary': {'distinct_from': ['02'], 'decision_rule': 'Usar 01 cuando el objetivo es delimitar una investigación nueva.'},
        'locales': locales,
        'self_hash_model': SELF_HASH_MODEL,
    }
    contract['self_sha256'] = canonical_self(contract, 'self_sha256')
    return contract


def reseal(contract: dict) -> dict:
    contract['self_sha256'] = canonical_self(contract, 'self_sha256')
    return contract


def run_mutations(baseline_contract: dict) -> int:
    validate_set([baseline_contract])  # positive control: the synthetic contract must pass

    mutations = []

    candidate = copy.deepcopy(baseline_contract)
    candidate['locales']['es']['empresa'] = copy.deepcopy(candidate['locales']['es']['persona'])
    mutations.append(('audience_clone', reseal(candidate), 'PROMPT_CONTRACT_AUDIENCE_CLONE'))

    candidate = copy.deepcopy(baseline_contract)
    cell = candidate['locales']['es']['persona']
    filler = ' Revisa las fuentes primarias con tensiones y criterio observable antes de decidir.'
    while len(cell['prompt']) <= 2 * BASELINE['es']['library/01/es/persona/natural']['chars']:
        cell['prompt'] += filler
    mutations.append(('length_excess_2x', reseal(candidate), 'PROMPT_CONTRACT_LENGTH_EXCESS'))

    candidate = copy.deepcopy(baseline_contract)
    for audience in AUDIENCES:
        cell = candidate['locales']['es'][audience]
        cell['prompt'] = cell['prompt'].replace('tensiones', 'fricciones')
    mutations.append(('anchor_missing', reseal(candidate), 'PROMPT_CONTRACT_EVIDENCE_ANCHOR_MISSING'))

    candidate = copy.deepcopy(baseline_contract)
    candidate['self_sha256'] = '0' * 64
    mutations.append(('false_self_pin', candidate, 'PROMPT_CONTRACT_SELF_DRIFT'))

    candidate = copy.deepcopy(baseline_contract)
    candidate['locales']['en']['persona']['traceability'][0]['source'] = 'https://example.com/unverified'
    mutations.append(('trace_outside_allowlist', reseal(candidate), 'PROMPT_CONTRACT_TRACE_INVALID'))

    candidate = copy.deepcopy(baseline_contract)
    del candidate['locales']['es']['empresa']
    mutations.append(('single_audience', reseal(candidate), 'PROMPT_CONTRACT_CELL_MATRIX'))

    candidate = copy.deepcopy(baseline_contract)
    candidate['publication_authorized'] = True
    mutations.append(('publication_flag', reseal(candidate), 'PROMPT_CONTRACT_GOVERNANCE_INVALID'))

    candidate = copy.deepcopy(baseline_contract)
    candidate['intent_id'] = 'W01'
    mutations.append(('surface_id_mismatch', reseal(candidate), 'PROMPT_CONTRACT_SURFACE_INVALID'))

    for name, mutant, expected in mutations:
        try:
            validate_set([mutant])
        except SystemExit as error:
            if not str(error).startswith(expected):
                raise SystemExit(f'PROMPT_CONTRACT_MUTATION_WRONG_REJECTION:{name}:{error}')
            continue
        raise SystemExit(f'PROMPT_CONTRACT_MUTATION_PASSED:{name}')
    return len(mutations)


def main() -> None:
    paths = sorted(CONTRACTS_DIR.glob('*.json')) if CONTRACTS_DIR.is_dir() else []
    contracts = [json.loads(path.read_text(encoding='utf-8')) for path in paths]
    validate_set(contracts)
    mutation_count = run_mutations(synthetic_contract())
    note = '' if contracts else ' note=contracts_dir_empty_pass'
    print(f'PROMPT_CONTRACTS_OK contracts={len(contracts)} ids={len(ALL_IDS)} locales={len(LANGS)} audiences={len(AUDIENCES)} mutations={mutation_count}{note}')


if __name__ == '__main__':
    main()
