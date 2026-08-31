#!/usr/bin/env python3
"""Standalone validator for src/prompt-contracts/*.json (prompt-intent-contract-v2).

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
OUTPUTS = {
    '01': 'PLAN_INICIAL_DE_INVESTIGACION', '02': 'COACH_CONFIGURADO', '03': 'INFORME_DE_INVESTIGACION',
    '04': 'VERIFICACION_CRUZADA', '05': 'BASE_AUDITADA', '06': 'PRACTICA_GENERADA',
    '07': 'MAPA_DE_CASOS', '08': 'EVALUACION_PROGRESIVA', '09': 'BORRADOR_DE_ENTREGA',
    '10': 'ENSAYO_DE_ENTREGA', 'M1': 'CONFIG_COACH', 'M2': 'CONFIG_EVALUADOR',
    'M3': 'CONFIG_ENTREVISTADOR', 'M4': 'CONFIG_PREPARADOR', 'B1': 'NOTAS_CONFIRMADAS',
    'B2': 'PLAN_DE_ESTUDIO', 'B3': 'PLAN_DE_NOTEBOOKLM', 'W01': 'BASE_INICIAL',
    'W02': 'DIAGNOSTICO_DE_BASE', 'W03': 'PLAN_DE_INVESTIGACION', 'W04': 'VEREDICTO_DE_BASE',
    'W05': 'ROL_ACTIVADO', 'W06': 'MATERIAL_DE_APRENDIZAJE', 'W07': 'CASOS_PRIORIZADOS',
    'W08': 'PREGUNTAS_DE_COMPRENSION', 'W09': 'ENSAYO_DE_DEFENSA', 'W10': 'PLAN_DE_TRANSFERENCIA',
}
ARTIFACT_KEYS = set(OUTPUTS.values())
MATERIAL_FIELDS = ('purpose', 'when', 'example', 'evidence', 'prompt')
CELL_FIELDS = {'title', *MATERIAL_FIELDS, 'inputs', 'parameters', 'optional_clauses', 'level_spec', 'why_it_works', 'traceability'}
LEVEL_SPEC_FIELDS = {'role', 'spec_role', 'objective', 'constraints', 'frameworks', 'workflow', 'guardrails', 'output', 'dod', 'edge_cases'}
WHY_FIELDS = {'acceptance_criteria', 'edge_cases', 'tradeoffs', 'assumptions', 'limits'}
INPUT_FIELDS = {'key', 'label', 'help', 'example', 'required', 'type', 'source', 'demo_value'}
PARAMETER_FIELDS = {'key', 'label', 'default', 'choices'}
OPTIONAL_FIELDS = {'key', 'text', 'default_enabled'}
FLOW_FIELDS = {'route', 'order', 'previous', 'next', 'branches', 'consumes', 'produces', 'external_gate', 'loop_to', 'standalone'}
SELF_HASH_MODEL = 'sha256(sorted-json-without-self_sha256)'


def norm(value: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))


# Length cap = max(2 x baseline natural chars, LENGTH_FLOOR).
# Ratified 2026-08: the pure 2x rule is unsatisfiable on the short workbook
# baselines (239-286c => caps of 478-572c). The mandatory quality tokens of an
# elevated prompt -- epistemic floor (~31c), negation-by-mechanism (55-100c),
# the E1 organizational variable (8-10c) -- eat 20-29% of a 478c cap, leaving
# no room for the rules the elevation exists to encode. The 600c floor is the
# smallest value that keeps the 30 cells of W06-W10 authorable; long baselines
# (library 01-M4, brain B1-B3) stay governed by the stricter 2x term.
LENGTH_FLOOR = 600


def length_cap(baseline_chars: int) -> int:
    return max(2 * baseline_chars, LENGTH_FLOOR)


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

# --- Tone charter §E of prompt-elevation-briefs.md (FROZEN; mirrored, never edited here).
# Evaluated exactly like the rest of the gate: substring over NFKD-without-accents
# + casefold, literal brackets.
#
# Three readings, all stricter than or narrower than the bare marker lists:
#  1. Scope. E3 says "(en prompt o evidence)". This gate scores E2-E5 over the
#     PROMPT ONLY. The evidence escape hatch is what let four defective cells pass
#     adversarial review: an organizational word sitting in `evidence` does not
#     make the text the user pastes organizational.
#  2. E3 applicability (ratified into the charter, phase 4). E3 -- the governance
#     lexicon -- does not apply to intents without decision authority; the named
#     case is 02, the source-grounded coach, whose F3 border forbids issuing
#     levels or verdicts. Demanding that lexicon there can only be satisfied by
#     writing a governance term no instruction produces, which is exactly the
#     promise-without-producer R8 rejects. There is NO special case in this code
#     and none is needed: the ">=2 markers" threshold is satisfied by E2, E4 and
#     E5, which do describe what such a cell delivers. E1 and the >=2 threshold
#     are never relaxed, and no other intent changes markers.
#  3. E5 variable form (applied here; NOT yet written into the frozen charter).
#     The charter lists only the literal `reutilizable por el equipo` /
#     `reusable by the team` / `reutilizavel pela equipe`. The variable form
#     `reutilizable por [EQUIPO]` / `reusable by [TEAM]` /
#     `reutilizavel pela [EQUIPE]` is semantically identical and is what a
#     well-formed empresa prompt actually writes -- 10/en/empresa scores E5 on it
#     today. Both forms are accepted. The charter text itself stays frozen, so
#     this one reading is still wider here than in §E.
PERSONA_TONE = {
    'es': {
        'p1': ['quiero', 'necesito', 'ayudame', 'mi contexto'],
        'p2': (['mi ', 'mis '], 2),
        'p3_forbidden': ['[equipo]', '[proceso]', '[area]', 'nuestro equipo', 'nuestra organizacion'],
        'p4_card': ['necesitas', 'quieres', 'debes', 'tu '],
        'p6_forbidden': ['gobernanza', 'comite', 'aprobacion', 'trazabilidad del proceso'],
    },
    'en': {
        'p1': ['i want', 'i need', 'help me', 'my context'],
        'p2': (['my '], 2),
        'p3_forbidden': ['[team]', '[process]', '[business area]', 'our team', 'our organization'],
        'p4_card': ['you want', 'you need', 'you must', 'your '],
        'p6_forbidden': ['governance', 'approval', 'sign-off', 'committee'],
    },
    'pt': {
        'p1': ['quero', 'preciso', 'ajude-me', 'meu contexto'],
        'p2': (['meu ', 'minha '], 2),
        'p3_forbidden': ['[equipe]', '[processo]', '[area]', 'nossa equipe', 'nossa organizacao'],
        'p4_card': ['voce', 'deve', 'sua ', 'seu '],
        'p6_forbidden': ['governanca', 'comite', 'aprovacao', 'rastreabilidade'],
    },
}
EMPRESA_TONE = {
    'es': {
        'e1': ['[equipo]', '[proceso]', '[area]', '[rol responsable]'],
        'markers': {
            'E2': ['nuestro equipo', 'nuestra organizacion', 'del equipo', 'el proceso'],
            'E3': ['gobernanza', 'aprobacion', 'responsable', 'trazabilidad', 'comite', 'direccion'],
            'E4': ['riesgo operativo', 'riesgo organizacional', 'impacto en el proceso'],
            'E5': ['reutilizable por el equipo', 'reutilizable por [equipo]', 'listo para revision',
                   'para compartir con', 'comparable entre'],
        },
    },
    'en': {
        'e1': ['[team]', '[process]', '[business area]', '[owner role]'],
        'markers': {
            'E2': ['our team', 'the team', 'our organization'],
            'E3': ['governance', 'approval', 'accountable', 'traceability', 'leadership'],
            'E4': ['operational risk', 'organizational risk', 'process impact'],
            'E5': ['reusable by the team', 'reusable by [team]', 'ready for review',
                   'to share with', 'comparable across'],
        },
    },
    'pt': {
        'e1': ['[equipe]', '[processo]', '[area]', '[responsavel]'],
        'markers': {
            'E2': ['nossa equipe', 'nosso time', 'nossa organizacao', 'da equipe'],
            'E3': ['governanca', 'aprovacao', 'responsavel', 'rastreabilidade', 'comite', 'diretoria'],
            'E4': ['risco operacional', 'risco organizacional', 'impacto no processo'],
            'E5': ['reutilizavel pela equipe', 'reutilizavel pela [equipe]', 'pronto para revisao',
                   'para compartilhar com', 'comparavel entre'],
        },
    },
}


def anchor_excuses(term: str, anchors: dict) -> bool:
    """Charter §E: authority anchors prevail over any charter prohibition."""
    for anchor in anchors['intent'] + anchors['evidence']:
        normalized = norm(anchor)
        if normalized and (normalized in term or term in normalized):
            return True
    return False


def tone_violations(cell: dict, locale: str, audience: str, anchors: dict, where: str) -> list[str]:
    # The frozen charter names legacy [INPUT] markers. v2 uses <INPUT>; map the
    # delimiters only for tone scoring, never for contract syntax validation.
    prompt = norm(cell['prompt']).replace('<', '[').replace('>', ']')
    card = norm(cell['purpose'] + ' ' + cell['when'])
    found = []
    if audience == 'persona':
        cfg = PERSONA_TONE[locale]
        leaked = [token for token in cfg['p3_forbidden'] if token in prompt]
        if leaked:
            found.append(f'PROMPT_CONTRACT_TONE_MARKER:{where}:P3:{leaked[0]}')
        satisfied = []
        if any(token in prompt for token in cfg['p1']):
            satisfied.append('P1')
        tokens, needed = cfg['p2']
        if sum(prompt.count(token) for token in tokens) >= needed:
            satisfied.append('P2')
        if not [t for t in cfg['p6_forbidden'] if t in prompt and not anchor_excuses(t, anchors)]:
            satisfied.append('P6')
        if len(satisfied) < 2:
            found.append(f'PROMPT_CONTRACT_TONE_MARKER:{where}:prompt_markers={"+".join(satisfied) or "none"}<2')
        if not any(token in card for token in cfg['p4_card']):
            found.append(f'PROMPT_CONTRACT_TONE_MARKER:{where}:P4_card_absent')
        return found
    cfg = EMPRESA_TONE[locale]
    if not any(token in prompt for token in cfg['e1']):
        found.append(f'PROMPT_CONTRACT_TONE_MARKER:{where}:E1_absent')
    hits = [name for name, tokens in sorted(cfg['markers'].items()) if any(t in prompt for t in tokens)]
    if len(hits) < 2:
        found.append(f'PROMPT_CONTRACT_TONE_MARKER:{where}:prompt_markers={"+".join(hits) or "none"}<2')
    if not any(t in card for tokens in cfg['markers'].values() for t in tokens):
        found.append(f'PROMPT_CONTRACT_TONE_MARKER:{where}:card_marker_absent')
    return found


# --- R8: no promise without a producer.
# Every content term promised in `evidence` and `level_spec.dod` must be produced
# by an instruction of the SAME cell (`prompt` + `level_spec.workflow` +
# `level_spec.output`). Matching is by 4-char root prefix so inflection
# (importable/importar, citada/citar) does not create false positives; the rule
# still catches whole promises nobody generates (e.g. "riesgo operativo
# declarado" in dod with no instruction asking for it).
WORD_RE = re.compile(r'[a-z0-9]+')
ROOT_LEN = 4
PROMISE_STOPWORDS = {
    # es
    'cuando', 'donde', 'porque', 'segun', 'sobre', 'entre', 'desde', 'hasta', 'aunque', 'mientras',
    'tambien', 'ademas', 'luego', 'antes', 'despues', 'todos', 'todas', 'otros', 'otras', 'mismo',
    'misma', 'cada', 'para', 'como', 'esta', 'este', 'estos', 'estas', 'segundo', 'menos', 'sino',
    'cuales', 'cual', 'quien', 'quienes', 'sus', 'una', 'unos', 'unas', 'segun',
    # en
    'which', 'where', 'when', 'that', 'with', 'from', 'their', 'there', 'these', 'those', 'while',
    'after', 'before', 'about', 'every', 'other', 'should', 'would', 'could', 'being', 'because',
    'across', 'within', 'each', 'into', 'than', 'then', 'they', 'them',
    # pt
    'quando', 'onde', 'sobre', 'entre', 'desde', 'embora', 'enquanto', 'depois', 'mesma', 'mesmo',
    'pelos', 'pelas', 'pela', 'pelo', 'nesta', 'neste', 'essa', 'esse', 'essas', 'esses',
}


FRAGMENT_RE = re.compile(r'[;,:.()\[\]—–]| y | e | and | o | or | ou ')
# Calibration against the 25 authored contracts: term-by-term matching produced
# 276 false positives (inflection and evaluative adjectives: "revisable",
# "observable", "tercero"). The rule that survives calibration is per FRAGMENT
# and asks for one producer, not all: a fragment is unproduced only when NOT ONE
# of its content terms is generated anywhere in the cell's instructions.
# Fragments carrying >=3 content terms block (a whole promised clause nobody
# writes); 2-term fragments are reported as warnings, because at that size the
# fragment is usually a quality adjective pair ("Ensayo revisable") rather than
# a promise. ponytail: fixed threshold, not a per-locale model — revisit only if
# a real defect ever hides in a 2-term fragment.
PROMISE_BLOCK_TERMS = 3


def promise_terms(text: str) -> list[str]:
    return [w for w in WORD_RE.findall(norm(text))
            if len(w) >= 5 and not w.isdigit() and w not in PROMISE_STOPWORDS]


def producer_roots(texts: list[str]) -> set[str]:
    return {word[:ROOT_LEN] for word in WORD_RE.findall(norm(' '.join(texts)))}


def promise_violations(cell: dict, where: str) -> list[str]:
    level_spec = cell['level_spec']
    roots = producer_roots([cell['prompt'], *level_spec['workflow'], *level_spec['output']])
    found = []
    for field, text in (('evidence', cell['evidence']), ('dod', level_spec['dod'])):
        for fragment in FRAGMENT_RE.split(f' {text} '):
            terms = promise_terms(fragment)
            if len(terms) < 2 or any(term[:ROOT_LEN] in roots for term in terms):
                continue
            code = f'PROMPT_CONTRACT_PROMISE_NO_PRODUCER:{where}:{field}:{" ".join(terms)}'
            found.append(code if len(terms) >= PROMISE_BLOCK_TERMS else f'WARN:{code}')
    return found


# --- R9: a cited authority must resolve.
FILE_RE = re.compile(r'[A-Za-z0-9_][A-Za-z0-9_./\-]*\.(?:json|md|py|yml)\b')
PROHIBITION_MARKERS = ('prohib', 'proib', 'forbid', 'veta ', 'impide', 'no permite', 'bans ')
LEDGER_MARKERS = ('ledger', 'claim-ledger')
PROHIBITED_CLAIMS = tuple(norm(claim) for claim in LEDGER.get('prohibited_claims', []))


def repo_files() -> set[str]:
    names = set()
    skip = {'.git', 'node_modules', '__pycache__'}
    for path in ROOT.rglob('*'):
        if not path.is_file() or skip & set(path.parts):
            continue
        names.add(path.name)
        names.add(str(path.relative_to(ROOT)))
    return names


REPO_FILES = repo_files()


def authority_violations(cell: dict, where: str) -> list[str]:
    texts = [text for values in cell['why_it_works'].values() for text in values]
    texts += [entry['claim'] for entry in cell['traceability'] if isinstance(entry, dict)]
    found = []
    for text in texts:
        for cited in FILE_RE.findall(text):
            if cited not in REPO_FILES and cited.lstrip('./') not in REPO_FILES:
                found.append(f'PROMPT_CONTRACT_AUTHORITY_UNRESOLVED:{where}:file:{cited}')
        lowered = norm(text)
        if any(marker in lowered for marker in LEDGER_MARKERS) and any(m in lowered for m in PROHIBITION_MARKERS):
            if not any(claim in lowered for claim in PROHIBITED_CLAIMS):
                found.append(f'PROMPT_CONTRACT_AUTHORITY_UNRESOLVED:{where}:ledger_prohibition')
    return found


# --- R10: no bare library id in material text.
# The prompt is text the user pastes into a chat: an id there is a dangling
# reference. Ids stay legal in boundary, guardrails, limits and assumptions.
BARE_ID_RE = re.compile(r'(?<![0-9A-Za-z_/#.\-])(?:0[1-9]|10|M[1-4]|W0[1-9]|W10|B[1-3])(?![0-9A-Za-z_/#.\-])')
# In material text the bare `10` is indistinguishable from the cardinal ten, and
# the corpus uses it that way ("10 casos de uso", "exactamente 10 prompts": 18
# cells). Material scanning therefore drops the bare `10` only; `W10` and the
# zero-padded 01-09 stay, and reference contexts (guardrails/limits) keep the
# full pattern, where "eso es 10" really is the library id.
# ponytail: ceiling accepted — a genuine bare `10` reference in a prompt escapes.
MATERIAL_ID_RE = re.compile(r'(?<![0-9A-Za-z_/#.\-])(?:0[1-9]|M[1-4]|W0[1-9]|W10|B[1-3])(?![0-9A-Za-z_/#.\-])')


def bare_id_violations(cell: dict, where: str) -> list[str]:
    found = []
    for field in ('title', *MATERIAL_FIELDS):
        hits = sorted(set(MATERIAL_ID_RE.findall(cell[field])))
        if hits:
            found.append(f'PROMPT_CONTRACT_BARE_ID:{where}:{field}:{",".join(hits)}')
    return found


# Authority v2 integrity: shape essentials, canonical self hash, unique signatures.
if AUTHORITY.get('schema_version') != 'prompt-intent-authority-v2' or AUTHORITY.get('status') not in ('provisional_until_phase_3', 'frozen_phase_3'):
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


def validate_contract(contract: dict) -> list[str]:
    """Structural defects raise (they make the rest unreadable); content defects
    are collected so one run reports every offending cell, not just the first."""
    found: list[str] = []
    required = {'schema_version', 'intent_id', 'surface', 'phase', 'state', 'publication_authorized', 'boundary', 'flow', 'locales', 'self_hash_model', 'self_sha256'}
    intent_id = contract.get('intent_id')
    if set(contract) != required or contract.get('schema_version') != 'prompt-intent-contract-v2':
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
    flow = contract['flow']
    if set(flow) != FLOW_FIELDS or flow['route'] not in {'library', 'workbook'} or not isinstance(flow['order'], int) or flow['order'] < 1:
        raise SystemExit(f'PROMPT_CONTRACT_FLOW_INVALID:{intent_id}')
    if any(value is not None and value not in ALL_IDS for value in (flow['previous'], flow['next'], flow['loop_to'])):
        raise SystemExit(f'PROMPT_CONTRACT_FLOW_TARGET_INVALID:{intent_id}')
    if any(value not in ALL_IDS for value in flow['branches']) or any(value not in ARTIFACT_KEYS for value in flow['consumes']) or flow['produces'] != OUTPUTS[intent_id] or flow['standalone'] is not True:
        raise SystemExit(f'PROMPT_CONTRACT_FLOW_TARGET_INVALID:{intent_id}')
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
            if any(not isinstance(pair, list) or len(pair) != 2 or not all(isinstance(part, str) and part.strip() for part in pair) for pair in level_spec['constraints']):
                raise SystemExit(f'PROMPT_CONTRACT_LEVEL_SPEC_PARAMETERS_INVALID:{where}')
            if not isinstance(level_spec['frameworks'], list) or not 1 <= len(level_spec['frameworks']) <= 3 or any(
                    not isinstance(item, str) or ' · ' not in item or len(item) > 90 for item in level_spec['frameworks']):
                raise SystemExit(f'PROMPT_CONTRACT_FRAMEWORK_INVALID:{where}')
            if len({norm(item.split(' · ', 1)[0]) for item in level_spec['frameworks']}) != len(level_spec['frameworks']):
                raise SystemExit(f'PROMPT_CONTRACT_FRAMEWORK_DUPLICATE:{where}')
            inputs = cell['inputs']
            if not isinstance(inputs, list) or len(inputs) < MIN_VARIABLES or any(
                    set(item) != INPUT_FIELDS or not all(str(item[field]).strip() for field in ('key', 'label', 'help', 'example', 'type', 'source', 'demo_value'))
                    or item['required'] is not True or item['source'] not in {'user', 'previous_output'}
                    for item in inputs):
                raise SystemExit(f'PROMPT_CONTRACT_INPUT_INVALID:{where}')
            if len({item['key'] for item in inputs}) != len(inputs) or len({item['label'] for item in inputs}) != len(inputs):
                raise SystemExit(f'PROMPT_CONTRACT_INPUT_DUPLICATE:{where}')
            parameters = cell['parameters']
            if not isinstance(parameters, list) or not parameters or any(
                    set(item) != PARAMETER_FIELDS or not all(str(item[field]).strip() for field in ('key', 'label', 'default'))
                    or not isinstance(item['choices'], list) or item['default'] not in item['choices']
                    for item in parameters):
                raise SystemExit(f'PROMPT_CONTRACT_PARAMETER_INVALID:{where}')
            optional = cell['optional_clauses']
            if not isinstance(optional, list) or any(
                    set(item) != OPTIONAL_FIELDS or not str(item['key']).strip() or not str(item['text']).strip()
                    or not isinstance(item['default_enabled'], bool) for item in optional):
                raise SystemExit(f'PROMPT_CONTRACT_OPTIONAL_INVALID:{where}')
            why = cell['why_it_works']
            if set(why) != WHY_FIELDS or any(not isinstance(why[field], list) or not why[field] for field in WHY_FIELDS):
                raise SystemExit(f'PROMPT_CONTRACT_WHY_INVALID:{where}')
        # Audience separation is checked before content so a cloned cell reports
        # the clone, not the downstream tone defect the clone happens to create.
        persona, empresa = localized['persona'], localized['empresa']
        for field in MATERIAL_FIELDS:
            if persona[field].casefold() == empresa[field].casefold():
                raise SystemExit(f'PROMPT_CONTRACT_AUDIENCE_CLONE:{locale}:{intent_id}:{field}')
        for audience in AUDIENCES:
            cell = localized[audience]
            level_spec = cell['level_spec']
            where = f'{locale}:{audience}:{intent_id}'
            for field, minimum in MINIMUMS.items():
                if len(cell[field].strip()) < minimum:
                    raise SystemExit(f'PROMPT_CONTRACT_FIELD_GENERIC:{where}:{field}')
            if '{{' in cell['prompt'] or '}}' in cell['prompt']:
                raise SystemExit(f'PROMPT_CONTRACT_LEGACY_MARKER:{where}')
            variables = [value.strip() for value in re.findall(r'<([^>]+)>', cell['prompt']) if value.strip()]
            expected_variables = [item['label'] for item in cell['inputs']]
            if set(variables) != set(expected_variables) or len(set(variables)) < MIN_VARIABLES:
                raise SystemExit(f'PROMPT_CONTRACT_VARIABLES:{where}')
            optional_texts={item['text'] for item in cell['optional_clauses']}
            square_values={value.strip() for value in re.findall(r'\[([^]]+)\]', cell['prompt']) if value.strip()}
            if not square_values.issubset(optional_texts):
                raise SystemExit(f'PROMPT_CONTRACT_OPTIONAL_SYNTAX:{where}')
            prompt_text = norm(cell['prompt'])
            intro_text = norm(cell['title'] + ' ' + cell['purpose'])
            evidence_text = norm(cell['evidence'])
            # Harmonized 2026-08 with build.py `validate_prompt_library`, which is
            # the strict reading and wins the conflict: an anchor must exist
            # somewhere in prompt+intro, AND at least one anchor must sit in the
            # prompt *and* in title+purpose at the same time. Otherwise the
            # intention the reader sees on the card can diverge from the one the
            # pasted prompt executes.
            intent_shared = 0
            for anchor in anchors['intent']:
                normalized = norm(anchor)
                in_prompt, in_intro = normalized in prompt_text, normalized in intro_text
                if len(normalized) < 4 or not (in_prompt or in_intro):
                    raise SystemExit(f'PROMPT_CONTRACT_INTENT_ANCHOR_MISSING:{where}:{anchor}')
                intent_shared += in_prompt and in_intro
            if not intent_shared:
                raise SystemExit(f'PROMPT_CONTRACT_INTENT_DIVERGENCE:{where}')
            for anchor in anchors['evidence']:
                normalized = norm(anchor)
                if len(normalized) < 4 or normalized not in prompt_text or normalized not in evidence_text:
                    raise SystemExit(f'PROMPT_CONTRACT_EVIDENCE_ANCHOR_MISSING:{where}:{anchor}')
            baseline_key = f'{surface}/{intent_id}/{locale}/{audience}/natural'
            baseline = BASELINE[locale].get(baseline_key)
            if baseline is None:
                raise SystemExit(f'PROMPT_CONTRACT_BASELINE_MISSING:{where}')
            cap = length_cap(baseline['chars'])
            if len(cell['prompt']) > cap:
                raise SystemExit(f'PROMPT_CONTRACT_LENGTH_EXCESS:{where}:{len(cell["prompt"])}>{cap}')
            trace = cell['traceability']
            if not isinstance(trace, list) or not trace:
                raise SystemExit(f'PROMPT_CONTRACT_TRACE_INVALID:{where}')
            for entry in trace:
                if set(entry) != {'claim', 'source'} or not str(entry['claim']).strip() or entry['source'] not in TRACE_ALLOWLIST:
                    raise SystemExit(f'PROMPT_CONTRACT_TRACE_INVALID:{where}:{entry.get("source")}')
            found += tone_violations(cell, locale, audience, anchors, where)
            found += promise_violations(cell, where)
            found += authority_violations(cell, where)
            found += bare_id_violations(cell, where)
            # R11b: an id named in guardrails/limits must be declared as a border
            # of this very contract, otherwise the exclusion is unverifiable.
            declared = set(boundary['distinct_from']) | {intent_id}
            named = {pid for text in (*level_spec['guardrails'], *cell['why_it_works']['limits'])
                     for pid in BARE_ID_RE.findall(text)}
            for pid in sorted(named - declared):
                found.append(f'PROMPT_CONTRACT_ID_NOT_IN_BOUNDARY:{where}:{pid}')
    return found


def boundary_symmetry_violations(contracts: list[dict]) -> list[str]:
    """R11a: if A declares B a distinct neighbour and B is on disk, B must say so too."""
    by_id = {contract.get('intent_id'): contract for contract in contracts
             if isinstance(contract.get('boundary'), dict)}
    found = []
    for intent_id, contract in sorted(by_id.items(), key=lambda item: str(item[0])):
        for other in contract['boundary'].get('distinct_from', []):
            twin = by_id.get(other)
            if twin is not None and intent_id not in twin['boundary'].get('distinct_from', []):
                found.append(f'PROMPT_CONTRACT_ASYMMETRIC_BOUNDARY:{intent_id}->{other}')
    return found


def cross_intent_clone_violations(contracts: list[dict]) -> list[str]:
    """Cross-intent twin: build.py's PROMPT_LIBRARY_SEMANTIC_CLONE compares every
    contract inside a (locale, audience) column, while the per-contract clone gate
    only compares persona against empresa within one intent. An echo cell that
    repeats its original verbatim (W08 vs 08) is invisible to the second and fatal
    to the first."""
    found = []
    for locale in LANGS:
        for audience in AUDIENCES:
            for field in MATERIAL_FIELDS:
                seen: dict[str, str] = {}
                for contract in contracts:
                    cell = contract.get('locales', {}).get(locale, {}).get(audience)
                    if not isinstance(cell, dict) or not isinstance(cell.get(field), str):
                        continue
                    intent_id = str(contract.get('intent_id'))
                    twin = seen.setdefault(' '.join(cell[field].split()).casefold(), intent_id)
                    if twin != intent_id:
                        found.append(f'PROMPT_CONTRACT_CROSS_INTENT_CLONE:{locale}:{audience}:{field}:{twin}={intent_id}')
    return found


def set_violations(contracts: list[dict]) -> list[str]:
    """Rules a single contract cannot express."""
    return boundary_symmetry_violations(contracts) + cross_intent_clone_violations(contracts)


def collect_violations(contracts: list[dict]) -> list[str]:
    seen = [contract.get('intent_id') for contract in contracts]
    if len(set(seen)) != len(seen):
        raise SystemExit(f'PROMPT_CONTRACT_DUPLICATE_INTENT:{sorted(pid for pid in set(seen) if seen.count(pid) > 1)}')
    found = set_violations(contracts)
    for contract in contracts:
        found += validate_contract(contract)
    return found


def validate_set(contracts: list[dict]) -> None:
    # Set-level borders first: they are the only rule a single contract cannot
    # express, and structural checks below raise instead of collecting.
    for item in set_violations(contracts):
        raise SystemExit(item)
    blocking = [item for item in collect_violations(contracts) if not item.startswith('WARN:')]
    if blocking:
        raise SystemExit(blocking[0])


# --- Built-in mutations: a synthetic valid contract must pass, mutants must fail.

PROMPT_EXTRA = {
    ('persona', 'es'): '',
    ('persona', 'en'): '',
    ('persona', 'pt'): '',
    ('empresa', 'es'): ' Ajusta el resultado a [EQUIPO] y el proceso, con riesgo operativo declarado y responsable nombrado.',
    ('empresa', 'en'): ' Adapt the result for [TEAM] and the process, with operational risk stated and an accountable owner.',
    ('empresa', 'pt'): ' Ajuste o resultado para [EQUIPE] e o processo, com risco operacional declarado e responsavel nomeado.',
}
CARD_EXTRA = {
    ('persona', 'es'): ' Decides tú qué entra y qué queda fuera.',
    ('persona', 'en'): ' You decide what stays inside the scope.',
    ('persona', 'pt'): ' Voce decide o que entra no recorte.',
    ('empresa', 'es'): ' Nuestro equipo revisa el resultado con gobernanza declarada.',
    ('empresa', 'en'): ' Our team reviews the result with declared governance.',
    ('empresa', 'pt'): ' Nossa equipe revisa o resultado com governanca declarada.',
}
EVIDENCE_EXTRA = {
    ('persona', 'es'): '', ('persona', 'en'): '', ('persona', 'pt'): '',
    ('empresa', 'es'): ' Incluye un responsable nombrado.',
    ('empresa', 'en'): ' It includes an accountable owner.',
    ('empresa', 'pt'): ' Inclui um responsavel nomeado.',
}
SYNTHETIC_DOD = 'Entrega revisable con límites declarados y fuentes citadas.'
SYNTHETIC_STEP = 'Entregar un resultado revisable con límites declarados y fuentes citadas.'


def synthetic_contract() -> dict:
    """Positive control: must satisfy every rule of this gate, tone charter included."""
    locales = {}
    for locale in LANGS:
        item = next(entry for entry in LIBRARY['locales'][locale]['items'] if entry['id'] == '01')
        cells = {}
        for audience in AUDIENCES:
            key = (audience, locale)
            card, evidence = CARD_EXTRA[key], item['evidence'] + EVIDENCE_EXTRA[key]
            prompt = re.sub(r'\[([^]]+)\]', r'<\1>', item['prompt'] + PROMPT_EXTRA[key])
            labels = list(dict.fromkeys(value.strip() for value in re.findall(r'<([^>]+)>', prompt)))
            cells[audience] = {
                'title': item['title'],
                'purpose': item['purpose'] + card,
                'when': item['when'] + card,
                'example': item['example'] + card,
                'evidence': evidence,
                'prompt': prompt,
                'inputs': [
                    {'key': f'input_{index}', 'label': label, 'help': 'Dato concreto del caso',
                     'example': 'ejemplo breve', 'required': True, 'type': 'text',
                     'source': 'user', 'demo_value': 'valor demo'}
                    for index, label in enumerate(labels, 1)],
                'parameters': [
                    {'key': 'length', 'label': 'LONGITUD', 'default': 'concisa', 'choices': ['concisa', 'media']},
                    {'key': 'structure', 'label': 'ESTRUCTURA', 'default': 'dos párrafos', 'choices': ['dos párrafos', 'tabla']},
                ],
                'optional_clauses': [],
                'level_spec': {
                    'role': 'Asistente MetodologIA orientado a evidencia',
                    'spec_role': LIBRARY['locales'][locale]['spec_format']['default_role'],
                    'objective': item['title'],
                    'constraints': [['profundidad', 'operativa'], ['formato', 'estructurado']],
                    'frameworks': ['MECE · sin solapamientos ni vacíos'],
                    'workflow': [item['purpose'], SYNTHETIC_STEP],
                    'guardrails': ['No inventar fuentes, citas o capacidades'],
                    'output': [evidence],
                    'dod': SYNTHETIC_DOD,
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
        'schema_version': 'prompt-intent-contract-v2',
        'intent_id': '01',
        'surface': 'library',
        'phase': 'Aprender',
        'state': 'RENDERED_DRAFT',
        'publication_authorized': False,
        'boundary': {'distinct_from': ['02'], 'decision_rule': 'Usar 01 cuando el objetivo es delimitar una investigación nueva.'},
        'flow': {'route': 'library', 'order': 1, 'previous': None, 'next': None, 'branches': [], 'consumes': [],
                 'produces': OUTPUTS['01'], 'external_gate': False, 'loop_to': None, 'standalone': True},
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
    while len(cell['prompt']) <= length_cap(BASELINE['es']['library/01/es/persona/natural']['chars']):
        cell['prompt'] += filler
    mutations.append(('length_excess_2x', reseal(candidate), 'PROMPT_CONTRACT_LENGTH_EXCESS'))

    candidate = copy.deepcopy(baseline_contract)
    for audience in AUDIENCES:
        cell = candidate['locales']['es'][audience]
        cell['prompt'] = cell['prompt'].replace('tensiones', 'fricciones')
    mutations.append(('anchor_missing', reseal(candidate), 'PROMPT_CONTRACT_EVIDENCE_ANCHOR_MISSING'))

    candidate = copy.deepcopy(baseline_contract)
    cell = candidate['locales']['es']['persona']
    # Both intent anchors of 01/es stay in the prompt; neither survives in
    # title+purpose. The lax rule accepted this; the strict one must not.
    cell['title'] = 'Blueprint de investigación acotada'
    cell['purpose'] = 'Convierte un asunto amplio en una investigación acotada y verificable con fuentes propias.'
    mutations.append(('intent_anchor_only_in_prompt', reseal(candidate), 'PROMPT_CONTRACT_INTENT_DIVERGENCE'))

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

    candidate = copy.deepcopy(baseline_contract)
    candidate['locales']['es']['persona']['inputs'][0]['help'] = ''
    mutations.append(('input_help_missing', reseal(candidate), 'PROMPT_CONTRACT_INPUT_INVALID'))

    candidate = copy.deepcopy(baseline_contract)
    candidate['locales']['es']['persona']['inputs'][0]['demo_value'] = ''
    mutations.append(('demo_value_missing', reseal(candidate), 'PROMPT_CONTRACT_INPUT_INVALID'))

    candidate = copy.deepcopy(baseline_contract)
    candidate['locales']['es']['persona']['parameters'][0]['default'] = 'valor no permitido'
    mutations.append(('parameter_default_outside_choices', reseal(candidate), 'PROMPT_CONTRACT_PARAMETER_INVALID'))

    candidate = copy.deepcopy(baseline_contract)
    candidate['locales']['es']['persona']['prompt'] += ' {{LEGACY_INPUT}}'
    mutations.append(('legacy_curly_marker', reseal(candidate), 'PROMPT_CONTRACT_LEGACY_MARKER'))

    candidate = copy.deepcopy(baseline_contract)
    candidate['locales']['es']['persona']['prompt'] += ' [BASE SUFICIENTE]'
    mutations.append(('pseudo_input_square_marker', reseal(candidate), 'PROMPT_CONTRACT_OPTIONAL_SYNTAX'))

    candidate = copy.deepcopy(baseline_contract)
    candidate['flow']['next'] = 'UNKNOWN'
    mutations.append(('flow_target_missing', reseal(candidate), 'PROMPT_CONTRACT_FLOW_TARGET_INVALID'))

    candidate = copy.deepcopy(baseline_contract)
    candidate['flow']['produces'] = OUTPUTS['02']
    mutations.append(('flow_output_incompatible', reseal(candidate), 'PROMPT_CONTRACT_FLOW_TARGET_INVALID'))

    candidate = copy.deepcopy(baseline_contract)
    candidate['flow']['consumes'] = ['ARTIFACT_UNKNOWN']
    mutations.append(('flow_input_orphan', reseal(candidate), 'PROMPT_CONTRACT_FLOW_TARGET_INVALID'))

    candidate = copy.deepcopy(baseline_contract)
    candidate['locales']['es']['persona']['level_spec']['frameworks'] = []
    mutations.append(('framework_missing', reseal(candidate), 'PROMPT_CONTRACT_LEVEL_SPEC_INVALID'))

    candidate = copy.deepcopy(baseline_contract)
    candidate['locales']['es']['persona']['level_spec']['frameworks'] = [
        'MECE · sin solapamientos ni vacíos',
        'MECE · todo debe caber en una categoría',
    ]
    mutations.append(('framework_duplicate', reseal(candidate), 'PROMPT_CONTRACT_FRAMEWORK_DUPLICATE'))

    # --- Mutations for the rules hardened in this pass.

    candidate = copy.deepcopy(baseline_contract)
    cell = candidate['locales']['es']['empresa']
    cell['prompt'] = cell['prompt'].replace(
        PROMPT_EXTRA[('empresa', 'es')].replace('[', '<').replace(']', '>'),
        ' Ajusta el resultado a <EQUIPO> con responsable nombrado.')
    mutations.append(('tone_charter_single_marker', reseal(candidate), 'PROMPT_CONTRACT_TONE_MARKER'))

    candidate = copy.deepcopy(baseline_contract)
    candidate['locales']['es']['persona']['evidence'] += ' Ranking nominal de individuos por desempeno trimestral.'
    mutations.append(('promise_without_producer', reseal(candidate), 'PROMPT_CONTRACT_PROMISE_NO_PRODUCER'))

    candidate = copy.deepcopy(baseline_contract)
    candidate['locales']['es']['persona']['why_it_works']['limits'] = [
        'El ledger prohíbe el ranking de individuos.']
    mutations.append(('invented_authority', reseal(candidate), 'PROMPT_CONTRACT_AUTHORITY_UNRESOLVED'))

    candidate = copy.deepcopy(baseline_contract)
    candidate['locales']['es']['persona']['prompt'] += ' Complementa con W07 cuando el taller ya tenga base.'
    mutations.append(('bare_id_in_prompt', reseal(candidate), 'PROMPT_CONTRACT_BARE_ID'))

    twin = copy.deepcopy(baseline_contract)
    twin['intent_id'] = '02'
    twin['boundary'] = {'distinct_from': ['03'], 'decision_rule': twin['boundary']['decision_rule']}
    twin['flow']['produces'] = OUTPUTS['02']
    mutations.append(('asymmetric_boundary', [copy.deepcopy(baseline_contract), reseal(twin)],
                      'PROMPT_CONTRACT_ASYMMETRIC_BOUNDARY'))

    twin = copy.deepcopy(baseline_contract)
    twin['intent_id'] = '02'
    twin['boundary'] = {'distinct_from': ['01'], 'decision_rule': twin['boundary']['decision_rule']}
    twin['flow']['produces'] = OUTPUTS['02']
    mutations.append(('cross_intent_clone', [copy.deepcopy(baseline_contract), reseal(twin)],
                      'PROMPT_CONTRACT_CROSS_INTENT_CLONE'))

    for name, mutant, expected in mutations:
        try:
            validate_set(mutant if isinstance(mutant, list) else [mutant])
        except SystemExit as error:
            if not str(error).startswith(expected):
                raise SystemExit(f'PROMPT_CONTRACT_MUTATION_WRONG_REJECTION:{name}:{error}')
            continue
        raise SystemExit(f'PROMPT_CONTRACT_MUTATION_PASSED:{name}')
    return len(mutations)


def main() -> None:
    paths = sorted(CONTRACTS_DIR.glob('*.json')) if CONTRACTS_DIR.is_dir() else []
    contracts = [json.loads(path.read_text(encoding='utf-8')) for path in paths]
    found = collect_violations(contracts)
    violations = [item for item in found if not item.startswith('WARN:')]
    warnings = [item for item in found if item.startswith('WARN:')]
    for item in warnings:
        print(item)
    if violations:
        for violation in violations:
            print(violation)
        raise SystemExit(f'PROMPT_CONTRACTS_FAILED violations={len(violations)} warnings={len(warnings)}')
    mutation_count = run_mutations(synthetic_contract())
    note = '' if contracts else ' note=contracts_dir_empty_pass'
    print(f'PROMPT_CONTRACTS_OK contracts={len(contracts)} ids={len(ALL_IDS)} locales={len(LANGS)} '
          f'audiences={len(AUDIENCES)} mutations={mutation_count} warnings={len(warnings)}{note}')


if __name__ == '__main__':
    main()
