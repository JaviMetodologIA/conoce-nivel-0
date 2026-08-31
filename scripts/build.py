#!/usr/bin/env python3
from __future__ import annotations
import hashlib, html, io, json, posixpath, re, shutil, subprocess, sys, unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

import fontTools
from brand import (
    AUDIENCES, CHROME_SPEC, DEFAULT_MODULE_ID, EDITORIAL_PAGES, EDITORIAL_SPEC,
    MANIFEST_RAW, MODULE_IDS, MODULE_ROUTES, PAGES, PUBLIC, RECEIPT_RAW, RELEASE,
    breadcrumb_model as chrome_breadcrumb_model, canonical_url, hreflang_urls,
    page_dir as brand_page_dir, relative_page as brand_relative_page, shell,
    theme_bootstrap, validate_chrome_spec, validate_editorial_spec, validate_release,
)
from module_renderers import (
    WORKBOOK_STAGE_LABELS,
    render_masterclass,
    render_playbook,
    render_prompts,
    render_workbook,
)
from module_depth import DepthContractError, load_json as load_depth_json, sha256_file, validate_depth_overlay
from module_prompt_parity import PromptParityError, compose_prompt_parity
from ui_primitives import ui_icon

ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'src'; DIST=ROOT/'dist'
BUILD_ID='nivel-0-learning-resources-v17'
FORM='https://docs.google.com/forms/d/e/1FAIpQLSeLysigcdIjlq4xguRXhBkN0WbC7H6FOzxylqgJC_7Ws4OtWQ/viewform'
HELP_BY_LANG={
    'es':'https://support.google.com/notebooklm/answer/16164461?hl=es',
    'en':'https://support.google.com/notebooklm/answer/16164461?hl=en',
    'pt':'https://support.google.com/notebooklm/answer/16164461?hl=pt-BR',
}
NOTEBOOK='https://notebooklm.google.com/'
OPEN_NOTEBOOK='https://notebook.google.com/notebook/9fdf2de1-9d2f-40ec-a365-e00a4f444e51'
RESEARCH_BLUEPRINT='https://chatgpt.com/g/g-69d59bec507c819197750fbbc1e74aae-research-blueprint'
ANTIGRAVITY='https://antigravity.google/download'
ANTIGRAVITY_GUIDE='https://codelabs.developers.google.com/getting-started-agy-ide'
OPENAI_PLANS='https://openai.com/chatgpt/pricing/'
ANTHROPIC_RESEARCH='https://support.anthropic.com/en/articles/11088861-using-research-on-claude-ai'
NOTEBOOK_LIMITS='https://support.google.com/notebooklm/answer/16213268?hl=en'
NOTEBOOK_MCP='https://github.com/PleasePrompto/notebooklm-mcp'
REFERENCE_WORKBOOK='https://javimontano.github.io/trabajar-amplificado/aprender-aprehender-revolucionar-notebooklm.html'
LANGS=('es','en','pt')
CURRENT_AUDIENCE='persona'
CURRENT_MODULE=DEFAULT_MODULE_ID
LANDING=json.loads((SRC/'landing-spec-v2.json').read_text(encoding='utf-8'))
RESOURCES=json.loads((SRC/'public-resource-spec-v1.json').read_text(encoding='utf-8'))
ADVANCED=json.loads((SRC/'workbook-advanced-v1.json').read_text(encoding='utf-8'))
WORKBOOK_PROMPTS=json.loads((SRC/'workbook-prompts-v1.json').read_text(encoding='utf-8'))
PLAYBOOK=json.loads((SRC/'playbook-spec-v1.json').read_text(encoding='utf-8'))
METHOD_IDENTITY=PLAYBOOK.get('method_identity',{})
PROMPT_LIBRARY=json.loads((SRC/'prompt-library-spec-v1.json').read_text(encoding='utf-8'))
NOTEBOOK_EXECUTION=json.loads((SRC/'notebooklm-execution-spec-v1.json').read_text(encoding='utf-8'))
PROMPT_ARTIFACTS=json.loads((SRC/'prompt-artifact-labels-v1.json').read_text(encoding='utf-8'))
PROMPT_SPEC_AUTHORITY_PATH=SRC/'prompt-spec-authority-v1.json'
PROMPT_SPEC_AUTHORITY_RAW=hashlib.sha256(PROMPT_SPEC_AUTHORITY_PATH.read_bytes()).hexdigest()
PROMPT_SPEC_AUTHORITY_EXPECTED_SHA256='64baf1e2299faaca3ff6a89d11dbf92a07be946224960bfe1b60370a9e70753c'
PROMPT_SPEC_AUTHORITY_EXPECTED_SELF_SHA256='08743a264b78853859e4a6cf5e4cb47f8ccc490b2c523d4e6dadd11dc5d14eed'
PROMPT_SPEC_AUTHORITY=json.loads(PROMPT_SPEC_AUTHORITY_PATH.read_text(encoding='utf-8'))
PROMPT_INTENT_AUTHORITY_PATH=SRC/'prompt-intent-authority-v2.json'
PROMPT_INTENT_AUTHORITY_RAW=hashlib.sha256(PROMPT_INTENT_AUTHORITY_PATH.read_bytes()).hexdigest()
PROMPT_INTENT_AUTHORITY_EXPECTED_SHA256='4c2eae3eaa1e5395411bd543d67cad279b907b7c6c68d23de078b63df1bba5cd'
PROMPT_INTENT_AUTHORITY_EXPECTED_SELF_SHA256='fd8495b10414afccb8e6f26fff8e713cbe3a819429a16562a77c4093a4e8d0b4'
PROMPT_INTENT_AUTHORITY=json.loads(PROMPT_INTENT_AUTHORITY_PATH.read_text(encoding='utf-8'))
PROMPT_CONTRACTS_DIR=SRC/'prompt-contracts'
AUDIENCE_SPEC=json.loads((SRC/'audience-spec-v1.json').read_text(encoding='utf-8'))
INTRAPAGE_NAV=json.loads((SRC/'intrapage-navigation-spec-v1.json').read_text(encoding='utf-8'))
PARITY=json.loads((SRC/'editorial-parity-spec-v1.json').read_text(encoding='utf-8'))
CURRICULUM=json.loads((SRC/'curriculum-spec-v2.json').read_text(encoding='utf-8'))
CURRICULUM_PROVENANCE=json.loads((SRC/'curriculum-provenance-rights-v2.json').read_text(encoding='utf-8'))
MODULE_DOD=json.loads((SRC/'module-resource-definition-of-done-v1.json').read_text(encoding='utf-8'))
MODULE_PROMPT_GOLDEN_PATH=SRC/'module-01-prompt-inventory-v1.json'
MODULE_PROMPT_GOLDEN=json.loads(MODULE_PROMPT_GOLDEN_PATH.read_text(encoding='utf-8'))
MODULE_DEPTH_PROFILE=load_depth_json(SRC/'modules/module-depth-profile-v1.json')
RESOURCE_PAGE_KEYS=('deck','workbook','playbook','prompts')
RESOURCE_SPEC_KEYS={'deck':'masterclass','workbook':'workbook','playbook':'playbook','prompts':'prompt_library'}
RESOURCE_NAME_KEYS={'deck':'masterclass','workbook':'workbook','playbook':'playbook','prompts':'prompts'}
RESOURCE_PAYLOAD_KEYS={'deck':'masterclass','workbook':'workbook','playbook':'playbook','prompts':'promptLibrary'}
EXPECTED_CANONICAL_HTML=126
EXPECTED_RESOURCE_HTML=96
EDITORIAL=validate_editorial_spec()
EXPECTED_INTRAPAGE_ANCHORS={
  'landing':['entrada','tension','ruta','demostracion','experiencia','resultados','metodo','convocatoria'],
  'deck':['masterclass-inicio','masterclass-pdf','masterclass-guia'],
  'workbook':['workbook-inicio','guia','descarga','preparacion','sheet-session','sheet-depth','sheet-consolidation','transferencia'],
  'playbook':['founders','intro','frameworks','apprehend','tools','workflows','standards','close'],
  'prompts':['directos','prompt-01','prompt-06','metaprompts'],
  'level0':['level0-start','purpose','path','fit','metodologia'],
  'how':['how-start','before','during','after','evidence'],
  'resources_index':['resources-start','masterclass-resource','workbook-resource','playbook-resource','prompts-resource'],
  'intakes':['intakes-start','verification','process','requirements','interest'],
}
if INTRAPAGE_NAV.get('schema_version')!='intrapage-navigation-spec-v1' or INTRAPAGE_NAV.get('state')!='RENDERED_DRAFT' or INTRAPAGE_NAV.get('publication_authorized') is not False or INTRAPAGE_NAV.get('desktop_width_px')!=260:
  raise SystemExit('INTRAPAGE_NAV_CONTRACT_INVALID')
if set(INTRAPAGE_NAV.get('locales',{}))!=set(LANGS) or set(INTRAPAGE_NAV.get('pages',{}))!=set(EXPECTED_INTRAPAGE_ANCHORS):
  raise SystemExit('INTRAPAGE_NAV_PARITY_INVALID')
for page,expected in EXPECTED_INTRAPAGE_ANCHORS.items():
  items=INTRAPAGE_NAV['pages'][page].get('items',[])
  if [item.get('anchor') for item in items]!=expected or not 3<=len(items)<=8:
    raise SystemExit(f'INTRAPAGE_NAV_ANCHORS_INVALID:{page}')
  if any(set(item.get('labels',{}))!=set(LANGS) or not all(item['labels'].values()) for item in items):
    raise SystemExit(f'INTRAPAGE_NAV_LABELS_INVALID:{page}')
AUDIENCE_SURFACES=('hero','problem','benefits','method','evidence','cta','closing')

def canonical_document_hash(document,field='self_sha256'):
  raw=json.dumps({key:value for key,value in document.items() if key!=field},ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n'
  return hashlib.sha256(raw.encode('utf-8')).hexdigest()

if (
  MODULE_PROMPT_GOLDEN.get('schema_version')!='module-01-prompt-inventory-v1'
  or MODULE_PROMPT_GOLDEN.get('state')!='RENDERED_DRAFT'
  or MODULE_PROMPT_GOLDEN.get('publication_authorized') is not False
  or MODULE_PROMPT_GOLDEN.get('self_hash_model')!='sha256(sorted-json-without-self_sha256)'
  or MODULE_PROMPT_GOLDEN.get('self_sha256')!=canonical_document_hash(MODULE_PROMPT_GOLDEN)
  or MODULE_PROMPT_GOLDEN.get('cardinality',{}).get('cards_per_variant')!=14
  or MODULE_PROMPT_GOLDEN.get('cardinality',{}).get('direct_prompts')!=10
  or MODULE_PROMPT_GOLDEN.get('cardinality',{}).get('metaprompts')!=4
):
  raise SystemExit('MODULE_PROMPT_GOLDEN_INVALID')

def validate_curriculum(document=None):
  spec=CURRICULUM if document is None else document
  if spec.get('schema_version')!='curriculum-spec-v2' or spec.get('local_only') is not True or spec.get('publication_authorized') is not False:
    raise SystemExit('CURRICULUM_GOVERNANCE_INVALID')
  if spec.get('languages')!=list(LANGS) or spec.get('audiences')!=list(AUDIENCES):
    raise SystemExit('CURRICULUM_VARIANT_DIMENSIONS_INVALID')
  required_variants={(lang,audience) for lang in LANGS for audience in AUDIENCES}
  declared_variants={(item.get('locale'),item.get('audience')) for item in spec.get('required_variants',[])}
  if declared_variants!=required_variants or len(spec.get('required_variants',[]))!=6:
    raise SystemExit('CURRICULUM_VARIANT_MATRIX_INVALID')
  authority=spec.get('authority_bindings',{})
  if authority!={'approved_program_proposal_sha256':'4ef3371f2baab2bc13d305e925d38875e942cb5d80c2207bdf4a011a5eefb68e','source_bundle_sha256':'22bab6b848dd42f47f0d3c9a9d3e560909a8950eab250169b0231d64927f9488'}:
    raise SystemExit('CURRICULUM_AUTHORITY_BINDING_INVALID')
  classes=spec.get('classes',[])
  if [item.get('id') for item in classes]!=list(MODULE_IDS) or [item.get('order') for item in classes]!=[1,2,3,4]:
    raise SystemExit('CURRICULUM_MODULE_ORDER_INVALID')
  kits={}
  for item in classes:
    if set(item.get('resource_state',{}))!=set(RESOURCE_SPEC_KEYS.values()) or any(state not in {'available','imported_local_draft'} for state in item['resource_state'].values()):
      raise SystemExit(f'CURRICULUM_RESOURCE_STATE_INVALID:{item.get("id")}')
    if item['id']==DEFAULT_MODULE_ID:
      continue
    content_ref=item.get('content',{}).get('ref','')
    content_path=SRC/content_ref
    if not content_path.is_file() or hashlib.sha256(content_path.read_bytes()).hexdigest()!=item.get('content',{}).get('sha256'):
      raise SystemExit(f'CURRICULUM_CONTENT_HASH_INVALID:{item["id"]}')
    pdf_ref=item.get('official_pdf',{}).get('ref','')
    pdf_path=SRC/pdf_ref
    if not pdf_path.is_file() or hashlib.sha256(pdf_path.read_bytes()).hexdigest()!=item.get('official_pdf',{}).get('sha256'):
      raise SystemExit(f'CURRICULUM_PDF_HASH_INVALID:{item["id"]}')
    if item['official_pdf'].get('image_only') is not True or item['official_pdf'].get('tagged') is not False:
      raise SystemExit(f'CURRICULUM_PDF_ACCESSIBILITY_INVALID:{item["id"]}')
    payload=json.loads(content_path.read_text(encoding='utf-8'))
    variants=payload.get('variants',[])
    actual_variants={(variant.get('locale'),variant.get('audience')) for variant in variants}
    if len(variants)!=6 or actual_variants!=required_variants:
      raise SystemExit(f'CURRICULUM_CONTENT_VARIANTS_INVALID:{item["id"]}')
    expected=item['variant_validation']
    for variant in variants:
      module=variant.get('module',{})
      counts={
        'moments_per_variant':len(module.get('masterclass',{}).get('moments',[])),
        'workbook_steps_per_variant':sum(len(route.get('steps',[])) for route in module.get('workbook',{}).get('routes',[])),
        'playbook_chapters_per_variant':len(module.get('playbook',{}).get('chapters',[])),
        'prompts_per_variant':len(module.get('promptLibrary',{}).get('prompts',[])),
      }
      if any(counts[key]!=expected[key] for key in counts):
        raise SystemExit(f'CURRICULUM_CONTENT_COUNT_INVALID:{item["id"]}:{variant.get("locale")}:{variant.get("audience")}')
      def prompt_mode_present(prompt,mode):
        direct=prompt.get(mode)
        if isinstance(direct,str) and direct.strip(): return True
        modes=prompt.get('modes',{})
        if isinstance(modes,dict) and isinstance(modes.get(mode),dict) and modes[mode].get('body'): return True
        return all(level.get(mode) for level in prompt.get('levels',[]))
      if len(module.get('workbook',{}).get('routes',[]))!=3 or any(len(prompt.get('levels',[]))!=4 or not prompt_mode_present(prompt,'template') or not prompt_mode_present(prompt,'demo') for prompt in module.get('promptLibrary',{}).get('prompts',[])):
        raise SystemExit(f'CURRICULUM_CONTENT_CONTRACT_INVALID:{item["id"]}:{variant.get("locale")}:{variant.get("audience")}')
    depth_ref=item.get('depth_overlay',{}).get('ref','')
    depth_path=SRC/depth_ref
    if not depth_path.is_file() or sha256_file(depth_path)!=item.get('depth_overlay',{}).get('sha256'):
      raise SystemExit(f'CURRICULUM_DEPTH_HASH_INVALID:{item["id"]}')
    depth_overlay=load_depth_json(depth_path)
    try:
      depth_variants=validate_depth_overlay(MODULE_DEPTH_PROFILE,depth_overlay,payload,item['content']['sha256'])
    except DepthContractError as error:
      raise SystemExit(f'CURRICULUM_DEPTH_CONTRACT_INVALID:{item["id"]}:{error}') from error
    imported_variants={(variant['locale'],variant['audience']):variant for variant in variants}
    composed_variants={};composed_depth_variants={}
    for variant_key,variant in imported_variants.items():
      try:
        composed_variant,composed_depth=compose_prompt_parity(item['id'],variant,depth_variants[variant_key])
      except PromptParityError as error:
        raise SystemExit(f'CURRICULUM_PROMPT_PARITY_INVALID:{item["id"]}:{variant_key[0]}:{variant_key[1]}:{error}') from error
      composed_variants[variant_key]=composed_variant
      composed_depth_variants[variant_key]=composed_depth
    kits[item['id']]={'spec':item,'payload':payload,'imported_variants':imported_variants,'variants':composed_variants,'depth_overlay':depth_overlay,'imported_depth_variants':depth_variants,'depth_variants':composed_depth_variants}
  ledger=CURRICULUM_PROVENANCE
  if ledger.get('schema_version')!='curriculum-provenance-rights-v2' or ledger.get('scope',{}).get('local_only') is not True or ledger.get('scope',{}).get('publication_authorized') is not False or ledger.get('scope',{}).get('run_dependency_at_build_time') is not False:
    raise SystemExit('CURRICULUM_PROVENANCE_INVALID')
  depth_policy=ledger.get('editorial_depth_policy',{})
  if (
    depth_policy.get('profile_ref')!='modules/module-depth-profile-v1.json'
    or depth_policy.get('profile_sha256')!=sha256_file(SRC/'modules/module-depth-profile-v1.json')
    or depth_policy.get('base_payloads_immutable') is not True
    or depth_policy.get('local_only') is not True
    or depth_policy.get('publication_authorized') is not False
    or depth_policy.get('notebooklm_queries',{}).get('authority_granted') is not False
  ):
    raise SystemExit('CURRICULUM_DEPTH_PROVENANCE_POLICY_INVALID')
  ledger_entries={entry.get('module_id'):entry for entry in ledger.get('entries',[])}
  if set(ledger_entries)!={kit['spec']['module_id'] for kit in kits.values()}:
    raise SystemExit('CURRICULUM_DEPTH_PROVENANCE_MODULES_INVALID')
  for kit in kits.values():
    item=kit['spec']
    module_id=item['module_id']
    binding=ledger_entries[module_id].get('editorial_depth_overlay',{})
    required_evidence={'depth-overlay-hash-verified','depth-base-bound','audience-depth-verified'}
    if (
      binding.get('ref')!=item['depth_overlay']['ref']
      or binding.get('sha256')!=item['depth_overlay']['sha256']
      or binding.get('base_payload_sha256')!=item['content']['sha256']
      or binding.get('profile_ref')!='modules/module-depth-profile-v1.json'
      or binding.get('exact_copy_of_external_run') is not False
      or binding.get('local_only') is not True
      or binding.get('publication_authorized') is not False
      or not required_evidence.issubset(set(ledger_entries[module_id].get('evidence_tags',[])))
    ):
      raise SystemExit(f'CURRICULUM_DEPTH_PROVENANCE_BINDING_INVALID:{module_id}')
  return kits

def validate_module_definition_of_done(document=None):
  spec=MODULE_DOD if document is None else document
  required={'schema_version','contract_id','state','publication_authorized','reference_module','comparison_policy','sequence','common_criteria','resource_criteria','editorial_criteria','module_gate','visual_matrix','self_hash_model','self_sha256'}
  if set(spec)!=required or spec.get('schema_version')!='module-resource-definition-of-done-v1':
    raise SystemExit('MODULE_DOD_SHAPE_INVALID')
  if spec.get('state')!='RENDERED_DRAFT' or spec.get('publication_authorized') is not False or spec.get('reference_module')!=DEFAULT_MODULE_ID:
    raise SystemExit('MODULE_DOD_GOVERNANCE_INVALID')
  if spec.get('self_hash_model')!='sha256(sorted-json-without-self_sha256)':
    raise SystemExit('MODULE_DOD_HASH_MODEL_INVALID')
  canonical=json.dumps({key:value for key,value in spec.items() if key!='self_sha256'},ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n'
  if hashlib.sha256(canonical.encode('utf-8')).hexdigest()!=spec.get('self_sha256'):
    raise SystemExit('MODULE_DOD_SELF_HASH_INVALID')
  policy=spec.get('comparison_policy',{})
  if policy.get('required_parity')!='semantic-visual-functional' or policy.get('code_identity_required') is not False or policy.get('topic_copy_reuse')!='forbidden':
    raise SystemExit('MODULE_DOD_COMPARISON_POLICY_INVALID')
  expected_sequence=['capture-reference-and-candidate','freeze-gap-report','approve-definition-of-done','improve-candidate-from-source','rebuild-candidate','verify-candidate','authorize-next-module']
  if spec.get('sequence')!=expected_sequence:
    raise SystemExit('MODULE_DOD_SEQUENCE_INVALID')
  if set(spec.get('resource_criteria',{}))!={'masterclass','workbook','playbook','prompts'}:
    raise SystemExit('MODULE_DOD_RESOURCES_INVALID')
  criteria=[*spec.get('common_criteria',[]),*spec.get('editorial_criteria',[]),*(criterion for group in spec['resource_criteria'].values() for criterion in group)]
  ids=[criterion.get('id') for criterion in criteria]
  if len(ids)!=len(set(ids)) or any(not isinstance(criterion.get('requirement'),str) or not criterion['requirement'].strip() or criterion.get('severity') not in {'P0','P1','P2'} for criterion in criteria):
    raise SystemExit('MODULE_DOD_CRITERIA_INVALID')
  if spec.get('module_gate')!={'blocking_severities':['P0','P1'],'next_module_requires':'PASS','verifier_must_be_independent':True,'guardian_required_before_freeze':True,'maximum_state':'RENDERED_DRAFT'}:
    raise SystemExit('MODULE_DOD_GATE_INVALID')
  if spec.get('visual_matrix')!={'widths':[320,390,768,1440],'themes':['light','dark'],'locales':['es','en','pt'],'audiences':['persona','empresa'],'zoom_percent':200,'no_js':True,'print':True}:
    raise SystemExit('MODULE_DOD_VISUAL_MATRIX_INVALID')
  return spec

MODULE_KITS=validate_curriculum()
MODULE_DOD=validate_module_definition_of_done()
def validate_audience_spec(document=None):
  spec=AUDIENCE_SPEC if document is None else document
  required={'schema_version','state','publication_authorized','audiences','pages','fields','body_roles','locales'}
  if set(spec)!=required or spec.get('schema_version')!='nivel-0-audience-positioning-v2' or spec.get('state')!='RENDERED_DRAFT' or spec.get('audiences')!=list(AUDIENCES) or spec.get('pages')!=list(PAGES) or set(spec.get('locales',{}))!=set(LANGS) or spec.get('publication_authorized') is not False:
    raise SystemExit('AUDIENCE_POSITIONING_CONTRACT_INVALID')
  if spec.get('fields')!=list(AUDIENCE_SURFACES) or set(spec.get('body_roles',{}))!=set(AUDIENCE_SURFACES):
    raise SystemExit('AUDIENCE_POSITIONING_FIELDS_INVALID')
  for locale in LANGS:
    if set(spec['locales'][locale])!=set(AUDIENCES):
      raise SystemExit(f'AUDIENCE_LOCALE_MATRIX_INVALID:{locale}')
    for audience in AUDIENCES:
      variant=spec['locales'][locale][audience]
      if set(variant)!=set(PAGES):
        raise SystemExit(f'AUDIENCE_VARIANT_SHAPE_INVALID:{locale}:{audience}')
      for page in PAGES:
        if set(variant[page])!=set(AUDIENCE_SURFACES) or any(not isinstance(variant[page][field],str) or not variant[page][field].strip() for field in AUDIENCE_SURFACES):
          raise SystemExit(f'AUDIENCE_PAGE_FIELDS_INVALID:{locale}:{audience}:{page}')
  for locale in LANGS:
    for page in PAGES:
      for field in AUDIENCE_SURFACES:
        if spec['locales'][locale]['persona'][page][field].casefold()==spec['locales'][locale]['empresa'][page][field].casefold():
          raise SystemExit(f'AUDIENCE_PAGE_FIELD_CLONE:{locale}:{page}:{field}')
  return spec

validate_audience_spec()

def canonical_self(value,field):
  payload={key:item for key,item in value.items() if key!=field}
  raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n'
  return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def nested(document,path):
  value=document
  for key in path.split('.'):
    if not isinstance(value,dict) or key not in value:
      raise SystemExit(f'EDITORIAL_PARITY_SOURCE_ROOT_MISSING:{path}')
    value=value[key]
  return value

def validate_editorial_parity(spec=None):
  spec=PARITY if spec is None else spec
  required={'schema_version','state','publication_authorized','network_required','fallback_policy','self_hash_model','self_sha256','matrix','localized_sources','required_audience_surfaces','shared_allowlist','string_inventory','official_pdf','preference_controls'}
  if set(spec)!=required or spec.get('schema_version')!='editorial-parity-spec-v1':
    raise SystemExit('EDITORIAL_PARITY_SHAPE_INVALID')
  if spec.get('state')!='RENDERED_DRAFT' or spec.get('publication_authorized') is not False or spec.get('network_required') is not False or spec.get('fallback_policy')!='forbidden':
    raise SystemExit('EDITORIAL_PARITY_GOVERNANCE_INVALID')
  if spec.get('self_hash_model')!='sha256(sorted-json-without-self_sha256)' or spec.get('self_sha256')!=canonical_self(spec,'self_sha256'):
    raise SystemExit('EDITORIAL_PARITY_SELF_DRIFT')
  matrix=spec.get('matrix',{})
  if matrix!={'locales':list(LANGS),'audiences':list(AUDIENCES),'pages':list(PAGES),'canonical_routes':EXPECTED_CANONICAL_HTML}:
    raise SystemExit('EDITORIAL_PARITY_MATRIX_INVALID')
  if spec.get('required_audience_surfaces')!=list(AUDIENCE_SURFACES):
    raise SystemExit('EDITORIAL_PARITY_AUDIENCE_SURFACES_INVALID')
  if [item.get('id') for item in spec.get('shared_allowlist',[])]!=['organization_and_method_marks','localized_chrome','official_spanish_pdf'] or any(set(item)!={'id','scope','reason'} or not item['scope'] or not item['reason'].strip() for item in spec['shared_allowlist']):
    raise SystemExit('EDITORIAL_PARITY_ALLOWLIST_INVALID')
  for source in spec.get('localized_sources',[]):
    if set(source)!={'path','root','dimensions'} or not source['path'].startswith('src/'):
      raise SystemExit('EDITORIAL_PARITY_SOURCE_INVALID')
    path=ROOT/source['path']
    document=json.loads(path.read_text(encoding='utf-8'))
    value=nested(document,source['root'])
    if set(value)!=set(LANGS):
      raise SystemExit(f'EDITORIAL_PARITY_LOCALE_GAP:{source["path"]}:{source["root"]}')
    if source['dimensions']==['locale','audience']:
      for locale in LANGS:
        if set(value[locale])!=set(AUDIENCES):
          raise SystemExit(f'EDITORIAL_PARITY_AUDIENCE_GAP:{source["path"]}:{source["root"]}:{locale}')
    elif source['dimensions']!=['locale']:
      raise SystemExit('EDITORIAL_PARITY_DIMENSION_INVALID')
  pdf=spec.get('official_pdf',{})
  pdf_path=ROOT/pdf.get('source','')
  deck_resource=RESOURCES['deck']
  if pdf.get('sha256')!=deck_resource.get('sha256') or not pdf_path.is_file() or hashlib.sha256(pdf_path.read_bytes()).hexdigest()!=pdf['sha256'] or pdf.get('document_language')!='es' or pdf.get('bytes_immutable') is not True:
    raise SystemExit('EDITORIAL_PARITY_PDF_INVALID')
  for locale in LANGS:
    deck_copy=deck_resource['locales'][locale]
    if not deck_copy['description'].strip() or not deck_copy['language_note'].strip():
      raise SystemExit(f'EDITORIAL_PARITY_PDF_LOCALIZATION_MISSING:{locale}')
  controls=spec.get('preference_controls',{})
  if controls.get('keys')!=['mdg_theme','mdg_locale','mdg_audience'] or controls.get('protocols')!=['file','http'] or controls.get('real_click_required') is not True:
    raise SystemExit('EDITORIAL_PARITY_CONTROLS_INVALID')

validate_editorial_parity()
MONTHLY_INTAKE_COPY={
  'es':('1 convocatoria al mes · primera semana','Una convocatoria al mes · primera semana'),
  'en':('1 monthly intake · first week','One monthly intake · first week'),
  'pt':('1 turma por mês · primeira semana','Uma turma por mês · primeira semana'),
}
for locale,(offer_copy,final_copy) in MONTHLY_INTAKE_COPY.items():
  landing_locale=LANDING['locales'][locale]
  if offer_copy not in landing_locale['offer'] or landing_locale['final_eyebrow'] != final_copy:
    raise SystemExit(f'LANDING_MONTHLY_INTAKE_CONTRACT_INVALID: {locale}')
if ADVANCED.get('prompt_format_contract',{}).get('formats') != ['natural','parameters','spec','pair']:
  raise SystemExit('PROMPT_FORMAT_CONTRACT_INVALID')
if PLAYBOOK.get('section_ids') != ['hero','intro','founders','assistants','scales','modes','fluency','frameworks','techniques','apprehend','method','integrity','evolve','tools','notebooklm','prompts','workflows','routines','standards','glossary','faq','close']:
  raise SystemExit('PLAYBOOK_SECTION_CONTRACT_INVALID')
if METHOD_IDENTITY.get('schema_version')!='method-identity-v1' or METHOD_IDENTITY.get('display_label')!='A²(R)E' or METHOD_IDENTITY.get('role')!='method_mark':
  raise SystemExit('METHOD_IDENTITY_CONTRACT_INVALID')
if set(METHOD_IDENTITY.get('locales',{}))!=set(LANGS) or set(METHOD_IDENTITY.get('assets',{}))!={'primary','compact'}:
  raise SystemExit('METHOD_IDENTITY_PARITY_INVALID')
if METHOD_IDENTITY.get('usage',{}).get('resources')!=['landing','playbook','prompts'] or METHOD_IDENTITY['usage'].get('excluded_resources')!=['workbook','deck'] or METHOD_IDENTITY['usage'].get('organization_logo_replacement') is not False:
  raise SystemExit('METHOD_IDENTITY_USAGE_INVALID')
DECK_RESOURCE=RESOURCES.get('deck',{})
if DECK_RESOURCE.get('media_type')!='application/pdf' or DECK_RESOURCE.get('document_language')!='es' or DECK_RESOURCE.get('page_count')!=18 or set(DECK_RESOURCE.get('locales',{}))!=set(LANGS):
  raise SystemExit('OFFICIAL_MASTERCLASS_CONTRACT_INVALID')
if any(not DECK_RESOURCE['locales'][locale].get('language_note') for locale in LANGS):
  raise SystemExit('OFFICIAL_MASTERCLASS_LANGUAGE_NOTE_MISSING')
assistant_ids=[item.get('id') for item in PLAYBOOK.get('assistants',[])]
if assistant_ids != ['prompting','study','research-blueprint'] or any(not item.get('url','').startswith('https://chatgpt.com/g/') or set(item.get('labels',{}))!=set(LANGS) for item in PLAYBOOK.get('assistants',[])):
  raise SystemExit('PLAYBOOK_ASSISTANT_CONTRACT_INVALID')
for locale in LANGS:
  expected=[x for x in PLAYBOOK['section_ids'] if x not in ('hero','founders','close')]
  if [x['id'] for x in PLAYBOOK['locales'][locale]['sections']] != expected:
    raise SystemExit(f'PLAYBOOK_LOCALE_PARITY_INVALID: {locale}')
  assistant_section=next(item for item in PLAYBOOK['locales'][locale]['sections'] if item['id']=='assistants')
  if assistant_section.get('items') != []:
    raise SystemExit(f'PLAYBOOK_ASSISTANT_SOURCE_DUPLICATED: {locale}')
  items=PROMPT_LIBRARY['locales'][locale]['items']
  if len(items)!=14 or [x['id'] for x in items]!=['01','02','03','04','05','06','07','08','09','10','M1','M2','M3','M4']:
    raise SystemExit(f'PROMPT_LIBRARY_COUNT_INVALID: {locale}')
prompt_spec_contract=PROMPT_LIBRARY.get('spec_contract',{})
if PROMPT_LIBRARY.get('level_formats') != ['natural','parameters','spec','pair'] or PROMPT_LIBRARY.get('publication_authorized') is not False:
  raise SystemExit('PROMPT_LIBRARY_CONTRACT_INVALID')
if prompt_spec_contract.get('anatomy') != ['situation','request','execution','criterion'] or prompt_spec_contract.get('chain_of_thought_policy') != 'never_request_store_or_expose_private_reasoning':
  raise SystemExit('PROMPT_LIBRARY_SPEC_CONTRACT_INVALID')
if prompt_spec_contract.get('provenance_required') is not True or prompt_spec_contract.get('publication_authorized') is not False:
  raise SystemExit('PROMPT_LIBRARY_SPEC_GOVERNANCE_INVALID')
for locale in LANGS:
  spec_copy=PROMPT_LIBRARY['locales'][locale].get('spec_format',{})
  required=('situation','request','execution','criterion','expert_role','default_role','deliverable','scope_in','scope_out','steps','edge_cases','output','observable_criteria','criterion_items','dod','dod_value','provenance','provenance_items','metadata','metadata_items','reasoning_policy')
  if any(not spec_copy.get(key) for key in required):
    raise SystemExit(f'PROMPT_LIBRARY_SPEC_LOCALE_INVALID:{locale}')
  expected_labels={
    'es':('Situación','Pedido','Ejecución','Criterio'),
    'en':('Situation','Request','Execution','Criterion'),
    'pt':('Situação','Pedido','Execução','Critério'),
  }[locale]
  if tuple(spec_copy[key] for key in ('situation','request','execution','criterion')) != expected_labels:
    raise SystemExit(f'PROMPT_LIBRARY_SPEC_LANGUAGE_INVALID:{locale}')

def prompt_semantic_words(value):
  normalized=''.join(character for character in unicodedata.normalize('NFKD',value.casefold()) if not unicodedata.combining(character))
  return set(re.findall(r'[a-z]{5,}',normalized))

def prompt_semantic_text(value):
  return ''.join(character for character in unicodedata.normalize('NFKD',value.casefold()) if not unicodedata.combining(character))

PROMPT_LIBRARY_IDS=('01','02','03','04','05','06','07','08','09','10','M1','M2','M3','M4')
WORKBOOK_PROMPT_IDS=tuple(f'W{index:02d}' for index in range(1,11))
BRAIN_PROMPT_IDS=('B1','B2','B3')
PROMPT_INTENT_IDS=PROMPT_LIBRARY_IDS+WORKBOOK_PROMPT_IDS+BRAIN_PROMPT_IDS
PROMPT_CONTRACT_SURFACES={'library':PROMPT_LIBRARY_IDS,'workbook':WORKBOOK_PROMPT_IDS,'workbook_brain':BRAIN_PROMPT_IDS}
NOTEBOOK_EXECUTION_FIELDS={'schema_version','state','publication_authorized','last_verified','product','official_sources','intent_routes','locales'}
if set(NOTEBOOK_EXECUTION)!=NOTEBOOK_EXECUTION_FIELDS or NOTEBOOK_EXECUTION.get('schema_version')!='notebooklm-execution-spec-v1' or NOTEBOOK_EXECUTION.get('state')!='RENDERED_DRAFT' or NOTEBOOK_EXECUTION.get('publication_authorized') is not False:
  raise SystemExit('NOTEBOOK_EXECUTION_CONTRACT_INVALID')
if set(NOTEBOOK_EXECUTION.get('intent_routes',{}))!=set(PROMPT_INTENT_IDS) or set(NOTEBOOK_EXECUTION.get('locales',{}))!=set(LANGS):
  raise SystemExit('NOTEBOOK_EXECUTION_MATRIX_INVALID')
for intent_id,route in NOTEBOOK_EXECUTION['intent_routes'].items():
  if set(route)!={'launch','mode','handoff'} or route['launch'] not in {'chat','source_search'} or route['handoff'] not in {None,'chat','source_search'}:
    raise SystemExit(f'NOTEBOOK_EXECUTION_ROUTE_INVALID:{intent_id}')
for locale,copy in NOTEBOOK_EXECUTION['locales'].items():
  required={'eyebrow','title','lead','chat_tab','chat_title','chat_body','search_tab','search_title','search_body','bridge','open','official','run_in','selected_sources','deep_research','research_brief','details','filter_label','all_prompts','open_prompt','close_prompt'}
  if set(copy)!=required or any(not isinstance(value,str) or not value.strip() for value in copy.values()):
    raise SystemExit(f'NOTEBOOK_EXECUTION_LOCALE_INVALID:{locale}')

def load_prompt_contracts():
  """The 27 prompt-intent contracts are the single source of the rendered prompt
  matrix (fallback_policy: forbidden). Missing keys must raise, never degrade."""
  contracts={}
  for path in sorted(PROMPT_CONTRACTS_DIR.glob('*.json')):
    contract=json.loads(path.read_text(encoding='utf-8'))
    intent_id=contract['intent_id']
    if intent_id in contracts:
      raise SystemExit(f'PROMPT_CONTRACT_DUPLICATE_INTENT:{intent_id}')
    if intent_id not in PROMPT_CONTRACT_SURFACES.get(contract['surface'],()):
      raise SystemExit(f'PROMPT_CONTRACT_SURFACE_INVALID:{contract["surface"]}:{intent_id}')
    if contract['schema_version']!='prompt-intent-contract-v2' or contract['state']!='RENDERED_DRAFT' or contract['publication_authorized'] is not False:
      raise SystemExit(f'PROMPT_CONTRACT_GOVERNANCE_INVALID:{intent_id}')
    if contract['self_hash_model']!='sha256(sorted-json-without-self_sha256)' or contract['self_sha256']!=canonical_self(contract,'self_sha256'):
      raise SystemExit(f'PROMPT_CONTRACT_SELF_DRIFT:{intent_id}')
    if set(contract['locales'])!=set(LANGS) or any(set(contract['locales'][locale])!=set(AUDIENCES) for locale in LANGS):
      raise SystemExit(f'PROMPT_CONTRACT_CELL_MATRIX:{intent_id}')
    contracts[intent_id]=contract
  if tuple(sorted(contracts))!=tuple(sorted(PROMPT_INTENT_IDS)):
    raise SystemExit(f'PROMPT_CONTRACT_SET_INCOMPLETE:{len(contracts)}')
  return {intent_id:contracts[intent_id] for intent_id in PROMPT_INTENT_IDS}

PROMPT_CONTRACTS=load_prompt_contracts()
PROMPT_ARTIFACT_KEYS={contract['flow']['produces'] for contract in PROMPT_CONTRACTS.values()}
if PROMPT_ARTIFACTS.get('schema_version')!='prompt-artifact-labels-v1' or PROMPT_ARTIFACTS.get('state')!='RENDERED_DRAFT' or PROMPT_ARTIFACTS.get('publication_authorized') is not False or PROMPT_ARTIFACTS.get('policy',{}).get('fallback')!='forbidden':
  raise SystemExit('PROMPT_ARTIFACT_LABELS_CONTRACT_INVALID')
if set(PROMPT_ARTIFACTS.get('artifacts',{}))!=PROMPT_ARTIFACT_KEYS:
  raise SystemExit('PROMPT_ARTIFACT_LABELS_MATRIX_INVALID')
for artifact,labels in PROMPT_ARTIFACTS['artifacts'].items():
  if set(labels)!=set(LANGS) or any(not isinstance(value,str) or not value.strip() for value in labels.values()):
    raise SystemExit(f'PROMPT_ARTIFACT_LABEL_INVALID:{artifact}')
module_artifacts=PROMPT_ARTIFACTS.get('module_artifacts',{})
if set(module_artifacts)!=set(MODULE_IDS[1:]):
  raise SystemExit('PROMPT_MODULE_ARTIFACT_MODULES_INVALID')
for module_id,localized in module_artifacts.items():
  if set(localized)!=set(LANGS):
    raise SystemExit(f'PROMPT_MODULE_ARTIFACT_LOCALES_INVALID:{module_id}')
  for locale in LANGS:
    expected=set()
    for audience in AUDIENCES:
      prompts=MODULE_KITS[module_id]['variants'][(locale,audience)]['module']['promptLibrary']['prompts']
      prompt_ids={prompt['id'] for prompt in prompts}
      for prompt in prompts:
        refs=[prompt['receive'],*prompt.get('consumeIds',[])]
        expected.update(
          ref for ref in refs
          if ref not in prompt_ids and not (isinstance(ref,str) and ref.endswith('-output') and ref[:-7] in prompt_ids)
        )
    labels=localized[locale]
    if not expected.issubset(set(labels)) or any(not isinstance(value,str) or not value.strip() for value in labels.values()):
      raise SystemExit(f'PROMPT_MODULE_ARTIFACT_MATRIX_INVALID:{module_id}:{locale}')

def assert_distinct_intent_parameters(contracts=None):
  """Anti-template tripwire: a shared `parameters` block between two intents is
  the signature of the generic level-2 shell this cutover removed."""
  contracts=PROMPT_CONTRACTS if contracts is None else contracts
  for locale in LANGS:
    for audience in AUDIENCES:
      seen={}
      for intent_id,contract in contracts.items():
        signature=tuple(tuple(pair) for pair in contract['locales'][locale][audience]['level_spec']['constraints'])
        if signature in seen:
          raise SystemExit(f'PROMPT_CONTRACT_PARAMETER_TEMPLATE:{locale}:{audience}:{seen[signature]}={intent_id}')
        seen[signature]=intent_id

assert_distinct_intent_parameters()

def contract_cell(intent_id,lang):
  return PROMPT_CONTRACTS[intent_id]['locales'][lang][CURRENT_AUDIENCE]

def validate_prompt_spec_authority(document=None,*,schema_version='prompt-spec-authority-v1',prompt_ids=PROMPT_LIBRARY_IDS,expected_self_sha256=PROMPT_SPEC_AUTHORITY_EXPECTED_SELF_SHA256,source_sha256=None,expected_source_sha256=None,allowed_extra_keys=frozenset()):
  authority=PROMPT_SPEC_AUTHORITY if document is None else document
  required={'schema_version','authority','purpose','state','publication_authorized','source_provenance','anchor_policy','locales','self_hash_model','self_sha256'}|set(allowed_extra_keys)
  if set(authority)!=required or authority.get('schema_version')!=schema_version or authority.get('authority')!='MetodologIA':
    raise SystemExit('PROMPT_SPEC_AUTHORITY_SHAPE_INVALID')
  if document is None:
    source_sha256,expected_source_sha256=PROMPT_SPEC_AUTHORITY_RAW,PROMPT_SPEC_AUTHORITY_EXPECTED_SHA256
  if expected_source_sha256 is not None and source_sha256!=expected_source_sha256:
    raise SystemExit('PROMPT_SPEC_AUTHORITY_PIN_DRIFT')
  if authority.get('self_hash_model')!='sha256(sorted-json-without-self_sha256)' or (expected_self_sha256 is not None and authority.get('self_sha256')!=expected_self_sha256) or authority.get('self_sha256')!=canonical_self(authority,'self_sha256'):
    raise SystemExit('PROMPT_SPEC_AUTHORITY_SELF_DRIFT')
  if authority.get('state')!='RENDERED_DRAFT' or authority.get('publication_authorized') is not False:
    raise SystemExit('PROMPT_SPEC_AUTHORITY_GOVERNANCE_INVALID')
  provenance=authority.get('source_provenance',{})
  if set(provenance)!={'kind','derived_from','method','rights'} or provenance.get('kind')!='governed_local_contract' or len(provenance.get('derived_from',[]))!=2 or not provenance.get('method') or not provenance.get('rights'):
    raise SystemExit('PROMPT_SPEC_AUTHORITY_PROVENANCE_INVALID')
  policy=authority.get('anchor_policy',{})
  ids=list(prompt_ids)
  if policy!={'prompt_ids':ids,'anchor_kinds':['intent','evidence'],'minimum_per_kind':2,'require_unique_signatures':True,'consumer_may_override':False}:
    raise SystemExit('PROMPT_SPEC_AUTHORITY_POLICY_INVALID')
  anchors=authority.get('locales',{})
  if set(anchors)!=set(LANGS) or any(set(anchors[locale])!=set(ids) for locale in LANGS):
    raise SystemExit('PROMPT_SPEC_AUTHORITY_MATRIX_INVALID')
  return authority

def validate_prompt_library(document=None,authority_document=None,*,prompt_ids=PROMPT_LIBRARY_IDS,intent_authority_binding=None,authority_options=None):
  source=PROMPT_LIBRARY if document is None else document
  authority=validate_prompt_spec_authority(authority_document,**(authority_options or {'prompt_ids':prompt_ids}))
  contract=source.get('spec_contract',{})
  specificity=contract.get('semantic_specificity',{})
  material_fields=specificity.get('material_fields')
  minimums=specificity.get('minimum_characters',{})
  if material_fields!=['purpose','when','example','evidence','prompt'] or set(minimums)!=set(material_fields):
    raise SystemExit('PROMPT_LIBRARY_SPECIFICITY_CONTRACT_INVALID')
  if specificity.get('minimum_distinct_variables',0)<2 or specificity.get('minimum_evidence_anchor_overlap',0)<1 or specificity.get('require_unique_within_locale') is not True:
    raise SystemExit('PROMPT_LIBRARY_SPECIFICITY_DEPTH_INVALID')
  forbidden=specificity.get('forbidden_locale_signals',{})
  allowlist={prompt_semantic_text(value) for value in specificity.get('locale_cognate_allowlist',[])}
  authority_binding=specificity.get('intent_authority',{})
  expected_binding=intent_authority_binding if intent_authority_binding is not None else {'source':'src/prompt-spec-authority-v1.json','source_sha256':PROMPT_SPEC_AUTHORITY_EXPECTED_SHA256,'self_sha256':authority['self_sha256'],'consumer_override':False}
  if authority_binding!=expected_binding:
    raise SystemExit('PROMPT_LIBRARY_AUTHORITY_BINDING_INVALID')
  anchors=authority['locales']
  if set(forbidden)!=set(LANGS) or specificity.get('locale_leak_threshold')!=1 or not allowlist:
    raise SystemExit('PROMPT_LIBRARY_LOCALE_AUTHORITY_INVALID')
  if any(not value or not re.fullmatch(r'[a-z0-9_]+',value) for value in allowlist):
    raise SystemExit('PROMPT_LIBRARY_LOCALE_ALLOWLIST_INVALID')
  minimum_anchor_count=specificity.get('minimum_anchor_count',0)
  minimum_diversity=specificity.get('minimum_lexical_diversity',0)
  if minimum_anchor_count<2 or not 0.65<=minimum_diversity<=1:
    raise SystemExit('PROMPT_LIBRARY_ANCHOR_CONTRACT_INVALID')
  locales=source.get('locales')
  if not isinstance(locales,dict) or set(locales)!=set(LANGS):
    raise SystemExit('PROMPT_LIBRARY_SEMANTIC_LOCALES_INVALID')
  for locale in LANGS:
    localized=locales[locale]
    items=localized.get('items',[])
    if [item.get('id') for item in items]!=list(prompt_ids):
      raise SystemExit(f'PROMPT_LIBRARY_SEMANTIC_MATRIX_INVALID:{locale}')
    if set(anchors[locale])!={item['id'] for item in items}:
      raise SystemExit(f'PROMPT_LIBRARY_ANCHOR_MATRIX_INVALID:{locale}')
    signatures=[]
    for field in material_fields:
      values=[' '.join(item.get(field,'').split()).casefold() for item in items]
      if len(set(values))!=len(items):
        raise SystemExit(f'PROMPT_LIBRARY_SEMANTIC_CLONE:{locale}:{field}')
    for item in items:
      anchor_set=anchors[locale][item['id']]
      if set(anchor_set)!= {'intent','evidence'} or any(not isinstance(anchor_set[kind],list) or len(anchor_set[kind])<minimum_anchor_count or len(set(anchor_set[kind]))!=len(anchor_set[kind]) for kind in ('intent','evidence')):
        raise SystemExit(f'PROMPT_LIBRARY_ANCHOR_SHAPE_INVALID:{locale}:{item["id"]}')
      signatures.append(tuple(sorted(anchor_set['intent']+anchor_set['evidence'])))
      for field in material_fields:
        if len(item.get(field,'').strip())<minimums[field]:
          raise SystemExit(f'PROMPT_LIBRARY_SEMANTIC_GENERIC:{locale}:{item.get("id")}:{field}')
      variables={value.strip().casefold() for value in re.findall(r'<([^>]+)>',item['prompt']) if value.strip()}
      variables|={value.strip().casefold() for value in re.findall(r'\[([^]]+)\]',item['prompt']) if value.strip()}
      if len(variables)<specificity['minimum_distinct_variables']:
        raise SystemExit(f'PROMPT_LIBRARY_SEMANTIC_VARIABLES:{locale}:{item["id"]}')
      overlap=prompt_semantic_words(item['evidence']) & prompt_semantic_words(item['prompt'])
      if len(overlap)<specificity['minimum_evidence_anchor_overlap']:
        raise SystemExit(f'PROMPT_LIBRARY_SEMANTIC_ANCHOR:{locale}:{item["id"]}')
      prompt_text=prompt_semantic_text(item['prompt'])
      intro_text=prompt_semantic_text(item['title']+' '+item['purpose'])
      evidence_text=prompt_semantic_text(item['evidence'])
      intent_shared=0
      for anchor in anchor_set['intent']:
        normalized_anchor=prompt_semantic_text(anchor)
        if len(normalized_anchor)<4 or normalized_anchor not in prompt_text+intro_text:
          raise SystemExit(f'PROMPT_LIBRARY_INTENT_ANCHOR_MISSING:{locale}:{item["id"]}:{anchor}')
        intent_shared += normalized_anchor in prompt_text and normalized_anchor in intro_text
      if intent_shared<1:
        raise SystemExit(f'PROMPT_LIBRARY_INTENT_DIVERGENCE:{locale}:{item["id"]}')
      for anchor in anchor_set['evidence']:
        normalized_anchor=prompt_semantic_text(anchor)
        if len(normalized_anchor)<4 or normalized_anchor not in prompt_text or normalized_anchor not in evidence_text:
          raise SystemExit(f'PROMPT_LIBRARY_EVIDENCE_ANCHOR_MISSING:{locale}:{item["id"]}:{anchor}')
      words=re.findall(r'[a-z]{4,}',prompt_text)
      if not words or len(set(words))/len(words)<minimum_diversity:
        raise SystemExit(f'PROMPT_LIBRARY_REDUNDANT_FILLER:{locale}:{item["id"]}')
      combined=' '+prompt_semantic_text(' '.join(item[field] for field in material_fields))+' '
      for sentence in re.split(r'[.!?\n]+',combined):
        hits=[signal for signal in forbidden[locale] if prompt_semantic_text(signal) not in allowlist and re.search(rf'(?<!\w){re.escape(prompt_semantic_text(signal))}(?!\w)',sentence)]
        if hits:
          raise SystemExit(f'PROMPT_LIBRARY_LOCALE_LEAK:{locale}:{item["id"]}:{hits[0]}')
    if len(set(signatures))!=len(signatures):
      raise SystemExit(f'PROMPT_LIBRARY_ANCHOR_SIGNATURE_CLONE:{locale}')

def compose_prompt_documents(contracts,intent_authority=None):
  """Assemble one synthetic per-audience document (items per locale) from
  prompt-intent-contract-v2 contracts, shaped for validate_prompt_library.
  This is how the build submits the 27 contracts to the semantic gate."""
  documents={}
  for audience in AUDIENCES:
    locales={}
    for locale in LANGS:
      items=[]
      for contract in contracts:
        cell=contract['locales'][locale][audience]
        items.append({'id':contract['intent_id'],'title':cell['title'],'purpose':cell['purpose'],'when':cell['when'],'example':cell['example'],'evidence':cell['evidence'],'prompt':cell['prompt']})
      locales[locale]={'items':items,'spec_format':PROMPT_LIBRARY['locales'][locale]['spec_format']}
    spec_contract=json.loads(json.dumps(PROMPT_LIBRARY['spec_contract']))
    if intent_authority is not None:
      spec_contract['semantic_specificity']['intent_authority']=dict(intent_authority)
    documents[audience]={'schema_version':'prompt-intent-contract-composite-v2','state':'RENDERED_DRAFT','publication_authorized':False,'spec_contract':spec_contract,'locales':locales}
  return documents

validate_prompt_library()
# Triple pin of the contract authority: the literals above, the self hash inside
# the file, and the consumer binding carried by the composed 27-contract document
# (re-emitted to the manifest by build()). All three now name v2.
PROMPT_INTENT_AUTHORITY_OPTIONS={
  'schema_version':'prompt-intent-authority-v2',
  'prompt_ids':PROMPT_INTENT_IDS,
  'expected_self_sha256':PROMPT_INTENT_AUTHORITY_EXPECTED_SELF_SHA256,
  'source_sha256':PROMPT_INTENT_AUTHORITY_RAW,
  'expected_source_sha256':PROMPT_INTENT_AUTHORITY_EXPECTED_SHA256,
  'allowed_extra_keys':frozenset({'status'})}
PROMPT_INTENT_AUTHORITY_BINDING={'source':'src/prompt-intent-authority-v2.json','source_sha256':PROMPT_INTENT_AUTHORITY_EXPECTED_SHA256,'self_sha256':PROMPT_INTENT_AUTHORITY_EXPECTED_SELF_SHA256,'consumer_override':False}
validate_prompt_spec_authority(PROMPT_INTENT_AUTHORITY,**PROMPT_INTENT_AUTHORITY_OPTIONS)
for _audience_document in compose_prompt_documents(list(PROMPT_CONTRACTS.values()),PROMPT_INTENT_AUTHORITY_BINDING).values():
  validate_prompt_library(_audience_document,PROMPT_INTENT_AUTHORITY,prompt_ids=PROMPT_INTENT_IDS,intent_authority_binding=PROMPT_INTENT_AUTHORITY_BINDING,authority_options=PROMPT_INTENT_AUTHORITY_OPTIONS)

T={
'es':{'skip':'Saltar al contenido','route':'Ruta Nivel 0','nav_route':'La ruta','nav_resources':'Recursos','enroll':'Inscribirme','open':'Próxima cohorte · Inscripciones abiertas','eyebrow':'Ruta de entrada · 4 clases · práctica real','hero':'Intro al mundo de la <span class="gold">IA</span>','lead':'Aprende a aprender, producir y trabajar con IA. Pasa de entender qué ocurre a dirigir un primer flujo agéntico sin delegar tu criterio.','see':'Ver las 4 clases','media':'Comprender. Priorizar. Amplificar. Orquestar.','classes':'clases conectadas','available':'recursos disponibles','routes':'rutas de autoentrenamiento','entry':'entrada común','progression':'Una progresión clara','four':'Cuatro clases. Una nueva forma de trabajar.','progress_lead':'Cada clase produce una práctica observable y abre el siguiente paso.','explore':'Explorar recursos','library':'Biblioteca viva','continues':'La clase termina. La práctica continúa.','library_lead':'Entra a lo disponible. Lo que sigue se muestra con honestidad, sin enlaces vacíos.','masterclass':'Masterclass','workbook':'Workbook','playbook':'Playbook','prompts':'Biblioteca de prompts','ready':'Disponible →','soon':'Próximamente','purpose_master':'Comprende el panorama y sigue una práctica guiada.','purpose_work':'Construye una base verificable durante la sesión.','purpose_play':'Repite el método después de la clase.','purpose_prompts':'Adapta instrucciones por objetivo y contexto.','footer':'Método + IA = Soberanía','class1':'IA: qué está pasando y cómo sacarle provecho','class1p':'Aprende a aprender con IA y usa NotebookLM como asistente basado en tus fuentes.','class2':'De ocupado a productivo','class2p':'Convierte la IA en coach para elegir, planificar y sostener lo importante.','class3':'Trabajar amplificado','class3p':'Integra método e IA para acelerar sin delegar tu criterio.','class4':'Trabajo agéntico','class4p':'Diseña un flujo supervisado con roles, memoria, herramientas y límites.','verbs':['Comprender','Priorizar','Amplificar','Orquestar']},
'en':{'skip':'Skip to content','route':'Level 0 Route','nav_route':'The route','nav_resources':'Resources','enroll':'Join the next cohort','open':'Next cohort · Enrollment open','eyebrow':'Entry route · 4 classes · real practice','hero':'Intro to the world of <span class="gold">AI</span>','lead':'Learn how to learn, produce and work with AI. Move from understanding what is happening to directing a first agentic workflow without giving up your judgment.','see':'See the 4 classes','media':'Understand. Prioritize. Amplify. Orchestrate.','classes':'connected classes','available':'available resources','routes':'self-training routes','entry':'common entry point','progression':'A clear progression','four':'Four classes. A new way to work.','progress_lead':'Each class produces observable practice and opens the next step.','explore':'Explore resources','library':'Living library','continues':'Class ends. Practice continues.','library_lead':'Open what is available. What comes next is shown honestly, without dead links.','masterclass':'Masterclass','workbook':'Workbook','playbook':'Playbook','prompts':'Prompt library','ready':'Available →','soon':'Coming soon','purpose_master':'Understand the landscape and follow a guided practice.','purpose_work':'Build a verifiable source base during class.','purpose_play':'Repeat the method after class.','purpose_prompts':'Adapt instructions by goal and context.','footer':'Method + AI = Sovereignty','class1':'AI: what is happening and how to benefit','class1p':'Learn how to learn with AI and use NotebookLM as a source-grounded assistant.','class2':'From busy to productive','class2p':'Turn AI into a coach to choose, plan and sustain what matters.','class3':'Amplified work','class3p':'Combine method and AI to accelerate without outsourcing judgment.','class4':'Agentic work','class4p':'Design a supervised workflow with roles, memory, tools and boundaries.','verbs':['Understand','Prioritize','Amplify','Orchestrate']},
'pt':{'skip':'Pular para o conteúdo','route':'Rota Nível 0','nav_route':'A rota','nav_resources':'Recursos','enroll':'Inscrever-me','open':'Próxima turma · Inscrições abertas','eyebrow':'Rota de entrada · 4 aulas · prática real','hero':'Introdução ao mundo da <span class="gold">IA</span>','lead':'Aprenda a aprender, produzir e trabalhar com IA. Passe de entender o que acontece a dirigir um primeiro fluxo agêntico sem delegar seu critério.','see':'Ver as 4 aulas','media':'Compreender. Priorizar. Amplificar. Orquestrar.','classes':'aulas conectadas','available':'recursos disponíveis','routes':'rotas de autoformação','entry':'entrada comum','progression':'Uma progressão clara','four':'Quatro aulas. Uma nova forma de trabalhar.','progress_lead':'Cada aula produz uma prática observável e abre o próximo passo.','explore':'Explorar recursos','library':'Biblioteca viva','continues':'A aula termina. A prática continua.','library_lead':'Acesse o que está disponível. O que vem depois aparece com honestidade, sem links vazios.','masterclass':'Masterclass','workbook':'Workbook','playbook':'Playbook','prompts':'Biblioteca de prompts','ready':'Disponível →','soon':'Em breve','purpose_master':'Compreenda o panorama e siga uma prática guiada.','purpose_work':'Construa uma base verificável durante a aula.','purpose_play':'Repita o método depois da aula.','purpose_prompts':'Adapte instruções por objetivo e contexto.','footer':'Método + IA = Soberania','class1':'IA: o que está acontecendo e como aproveitar','class1p':'Aprenda a aprender com IA e use o NotebookLM como assistente baseado em fontes.','class2':'De ocupado a produtivo','class2p':'Transforme a IA em coach para escolher, planejar e sustentar o importante.','class3':'Trabalho amplificado','class3p':'Integre método e IA para acelerar sem delegar seu critério.','class4':'Trabalho agêntico','class4p':'Projete um fluxo supervisionado com papéis, memória, ferramentas e limites.','verbs':['Compreender','Priorizar','Amplificar','Orquestrar']}}

RESOURCE_NAMES={
'es':[
  {'masterclass':'IA: qué está pasando y cómo sacarle provecho','workbook':'Aprende a aprender con NotebookLM','playbook':'De fuentes a aprendizaje continuo','prompts':'Aprende, investiga y comprende con IA'},
  {'masterclass':'De ocupado a productivo','workbook':'Convierte prioridades en un sistema','playbook':'Tu pauta de productividad con IA','prompts':'Planifica, prioriza y haz seguimiento'},
  {'masterclass':'Trabajar amplificado','workbook':'Diseña tu flujo de trabajo amplificado','playbook':'Método para amplificar lo que haces','prompts':'Acelera, mejora y sistematiza tu trabajo'},
  {'masterclass':'Trabajo agéntico','workbook':'Diseña tu primer flujo agéntico','playbook':'Orquesta agentes con supervisión humana','prompts':'Asistentes, agentes, herramientas y control'},
],
'en':[
  {'masterclass':'AI: what is happening and how to benefit','workbook':'Learn how to learn with NotebookLM','playbook':'From sources to continuous learning','prompts':'Learn, research and understand with AI'},
  {'masterclass':'From busy to productive','workbook':'Turn priorities into a system','playbook':'Your AI productivity pattern','prompts':'Plan, prioritize and follow through'},
  {'masterclass':'Amplified work','workbook':'Design your amplified workflow','playbook':'A method to amplify your work','prompts':'Accelerate, improve and systematize your work'},
  {'masterclass':'Agentic work','workbook':'Design your first agentic workflow','playbook':'Orchestrate agents with human supervision','prompts':'Assistants, agents, tools and control'},
],
'pt':[
  {'masterclass':'IA: o que está acontecendo e como aproveitar','workbook':'Aprenda a aprender com NotebookLM','playbook':'De fontes à aprendizagem contínua','prompts':'Aprenda, pesquise e compreenda com IA'},
  {'masterclass':'De ocupado a produtivo','workbook':'Transforme prioridades em um sistema','playbook':'Sua pauta de produtividade com IA','prompts':'Planeje, priorize e acompanhe'},
  {'masterclass':'Trabalho amplificado','workbook':'Projete seu fluxo de trabalho amplificado','playbook':'Método para amplificar o que você faz','prompts':'Acelere, melhore e sistematize seu trabalho'},
  {'masterclass':'Trabalho agêntico','workbook':'Projete seu primeiro fluxo agêntico','playbook':'Orquestre agentes com supervisão humana','prompts':'Assistentes, agentes, ferramentas e controle'},
]}

def esc(s): return html.escape(s,quote=True)
def decorate_ui(text, lang):
  """Keep visible actions concise and reinforce them with inline icons."""
  limits={'es':'Ver límites','en':'View limits','pt':'Ver limites'}[lang]
  print_label={'es':'Imprimir','en':'Print','pt':'Imprimir'}[lang]
  for source,target in {
    'Consultar límites oficiales de NotebookLM':limits,
    'Read official NotebookLM limits':limits,
    'Consultar limites oficiais do NotebookLM':limits,
    'PDF / Print':print_label+ui_icon('print'),
  }.items():
    text=text.replace(source,target)
  return (text
    .replace(' →</a>',ui_icon('arrow')+'</a>')
    .replace(' ↗</a>',ui_icon('external')+'</a>')
    .replace(' ↓</a>',ui_icon('download')+'</a>')
    .replace(' →</button>',ui_icon('arrow')+'</button>')
    .replace('>←</button>','>'+ui_icon('back')+'</button>')
    .replace('>→</button>','>'+ui_icon('arrow')+'</button>')
    .replace('>← ','>'+ui_icon('back'))
    .replace(' ↗</strong>',ui_icon('external')+'</strong>')
    .replace(' ↗</em>',ui_icon('external')+'</em>'))
def module_id(value=None):
    return CURRENT_MODULE if value is None else value

def page_dir(lang,page,current_module=None):
    return brand_page_dir(lang,CURRENT_AUDIENCE,page,module_id(current_module))
def rel_dir(lang,page,target_lang,target_page=None,current_module=None,target_module=None):
    target_page=page if target_page is None else target_page
    source_module=module_id(current_module)
    target_module=source_module if target_module is None else target_module
    rel=posixpath.relpath(page_dir(target_lang,target_page,target_module),page_dir(lang,page,source_module))
    return './' if rel=='.' else rel.rstrip('/')+'/'
def rel_page(lang,page,target_lang,target_page=None,current_module=None,target_module=None):
    target_page=page if target_page is None else target_page
    source_module=module_id(current_module)
    target_module=source_module if target_module is None else target_module
    return brand_relative_page(
      lang,CURRENT_AUDIENCE,page,target_lang,CURRENT_AUDIENCE,target_page,
      source_module,target_module,
    )
def asset_base(lang,page,current_module=None):
    rel=posixpath.relpath('.',page_dir(lang,page,current_module))
    return './' if rel=='.' else rel.rstrip('/')+'/'
def method_mark(lang,page,variant='compact',class_name='method-mark',decorative=False,loading='lazy'):
    asset=METHOD_IDENTITY['assets'][variant]
    alt='' if decorative else esc(METHOD_IDENTITY['locales'][lang]['accessible_name'])
    hidden=' aria-hidden="true"' if decorative else ''
    return f'''<img class="{esc(class_name)}" src="{asset_base(lang,page)}{esc(asset['path'])}" alt="{alt}" width="{asset['width']}" height="{asset['height']}" loading="{loading}" decoding="async" data-method-mark="{variant}"{hidden}>'''
def intrapage_navigation(lang,page,items=None):
    ui=INTRAPAGE_NAV['locales'][lang]
    items=INTRAPAGE_NAV['pages'][page]['items'] if items is None else items
    links=''.join(f'''<li><a href="#{esc(item['anchor'])}" data-intrapage-link><span aria-hidden="true">{index:02d}</span><strong>{esc(item.get('label',item.get('labels',{}).get(lang,'')))}</strong></a></li>''' for index,item in enumerate(items,1))
    menu_icon='<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 7h14M5 12h14M5 17h9"></path></svg>'
    close_icon='<svg aria-hidden="true" viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18"></path></svg>'
    return f'''<button class="intrapage-trigger" type="button" aria-label="{esc(ui['open'])}" aria-expanded="false" aria-controls="intrapage-navigation" data-intrapage-open>{menu_icon}<span>{esc(ui['open'])}</span></button><div class="intrapage-backdrop" data-intrapage-backdrop hidden></div><aside class="intrapage-nav" id="intrapage-navigation" aria-label="{esc(ui['title'])}" data-intrapage-nav tabindex="-1"><header><span>{esc(ui['title'])}</span><button type="button" aria-label="{esc(ui['close'])}" data-intrapage-close>{close_icon}</button></header><nav aria-label="{esc(ui['title'])}"><ol>{links}</ol></nav></aside>'''
def breadcrumb_model(lang,page,current_module=None):
    current_module=module_id(current_module)
    labels={
      'es':{'nav':'Migas de pan','home':'Inicio','resources':'Recursos'},
      'en':{'nav':'Breadcrumb','home':'Home','resources':'Resources'},
      'pt':{'nav':'Navegação estrutural','home':'Início','resources':'Recursos'},
    }[lang]
    resource_index={'deck':'masterclass','workbook':'workbook','playbook':'playbook','prompts':'prompts'}
    current=(EDITORIAL['copy'][lang][page]['title'] if page in EDITORIAL_PAGES else {
      'landing':labels['home'],'deck':T[lang]['masterclass'],'workbook':T[lang]['workbook'],
      'playbook':T[lang]['playbook'],'prompts':T[lang]['prompts'],
    }[page])
    if current_module!=DEFAULT_MODULE_ID and page in resource_index:
      current=RESOURCE_NAMES[lang][MODULE_ROUTES[current_module]['order']-1][resource_index[page]]
    items=[{'label':labels['home'],'page':'landing','module_id':DEFAULT_MODULE_ID}]
    if page in ('deck','workbook','playbook','prompts'):
      items.append({'label':labels['resources'],'page':'resources_index','module_id':DEFAULT_MODULE_ID})
      if current_module!=DEFAULT_MODULE_ID:
        overview=rel_page(lang,page,lang,'resources_index',current_module,DEFAULT_MODULE_ID)
        items.append({'label':MODULE_ROUTES[current_module]['labels'][lang],'href':f'{overview}#module-{MODULE_ROUTES[current_module]["order"]:02d}'})
    if page!='landing':
      items.append({'label':current,'page':page,'module_id':current_module})
    return labels['nav'],items
def breadcrumb(lang,page,*legacy,current_module=None):
    if legacy:
      return ''
    current_module=module_id(current_module)
    label,items=breadcrumb_model(lang,page,current_module)
    rendered=[]
    for index,item in enumerate(items):
      current=index==len(items)-1
      if current:
        rendered.append(f'<li><span aria-current="page">{esc(item["label"])}</span></li>')
      else:
        href=item.get('href') or rel_page(lang,page,lang,item['page'],current_module,item.get('module_id',DEFAULT_MODULE_ID))
        rendered.append(f'<li><a href="{esc(href)}">{esc(item["label"])}</a></li>')
    return f'''<div class="conoce-breadcrumbs-shell"><nav class="breadcrumbs conoce-breadcrumbs" aria-label="{esc(label)}" data-conoce-breadcrumbs><ol>{''.join(rendered)}</ol></nav></div>'''
def head(lang,title,page,current_module=None,nav_items=None):
    current_module=module_id(current_module)
    base=asset_base(lang,page,current_module)
    l=LANDING['locales'][lang]
    desc=(EDITORIAL['copy'][lang][page]['meta_description'] if page in EDITORIAL_PAGES else l['meta_description'] if page=='landing' else {'es':'Ruta Nivel 0 de MetodologIA: aprendizaje y práctica con IA basada en fuentes.','en':'MetodologIA Level 0: source-grounded AI learning and practice.','pt':'Rota Nível 0 da MetodologIA: aprendizagem e prática com IA baseada em fontes.'}[lang])
    route=page_dir(lang,page,current_module); canonical=canonical_url(current_module,page,lang,CURRENT_AUDIENCE,PUBLIC)
    alternate_urls=hreflang_urls(current_module,page,lang,CURRENT_AUDIENCE,PUBLIC)
    alternates=''.join(f'<link rel="alternate" hreflang="{code}" href="{href}">' for code,href in alternate_urls.items())
    document_title=f'{title} · Conoce · Nivel 0 · MetodologIA'
    social=f'''<meta property="og:type" content="website"><meta property="og:site_name" content="MetodologIA"><meta property="og:title" content="{esc(document_title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{canonical}"><meta name="twitter:card" content="summary">'''
    organization={'@type':'Organization','name':'MetodologIA','url':'https://metodologia.info/'}
    _,crumbs=breadcrumb_model(lang,page,current_module)
    breadcrumb_items=[]
    for index,item in enumerate(crumbs,1):
      target_page=item.get('page','resources_index')
      target_module=item.get('module_id',DEFAULT_MODULE_ID)
      item_url=canonical_url(target_module,target_page,lang,CURRENT_AUDIENCE,PUBLIC)
      breadcrumb_items.append({'@type':'ListItem','position':index,'name':item['label'],'item':item_url})
    breadcrumb_json={'@type':'BreadcrumbList','@id':canonical+'#breadcrumb','itemListElement':breadcrumb_items}
    structured={'@context':'https://schema.org','@graph':[{'@type':'WebSite','@id':PUBLIC+'#website','name':'Conoce · Nivel 0','url':PUBLIC,'publisher':organization,'isPartOf':{'@type':'WebSite','name':'MetodologIA','url':'https://metodologia.info/'}},{'@type':'CollectionPage','@id':canonical+'#webpage','name':'Conoce · Nivel 0','headline':title,'url':canonical,'inLanguage':lang,'publisher':organization,'isPartOf':{'@type':'WebSite','name':'MetodologIA','url':'https://metodologia.info/'}},breadcrumb_json]}
    structured_json=json.dumps(structured,ensure_ascii=False,sort_keys=True,separators=(',',':')).replace('</','<\\/')
    brand=shell(lang,CURRENT_AUDIENCE,page,current_module)
    return f'''<!doctype html><html lang="{lang}" data-audience="{CURRENT_AUDIENCE}" data-theme="light" class="no-js"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(document_title)}</title><meta name="description" content="{esc(desc)}"><link rel="icon" href="{base}assets/brand/assets/metodologia-logo.svg" type="image/svg+xml"><link rel="canonical" href="{canonical}">{alternates}{social}<script type="application/ld+json" data-conoce-structured>{structured_json}</script>{theme_bootstrap()}<link rel="stylesheet" href="{brand['stylesheetBase']}/brand-shell.css"><link rel="stylesheet" href="{base}assets/site.css"><link rel="stylesheet" href="{base}assets/forms.css"><noscript><style>.sheet[hidden],.slide{{display:block!important}}</style></noscript></head><body data-page="{page}" data-module-id="{esc(current_module)}"><div class="mdg-shell conoce-shell">{brand['header']}</div><div class="mdg-shell conoce-preferences-shell">{brand['controls']}</div>{intrapage_navigation(lang,page,nav_items)}{breadcrumb(lang,page,current_module=current_module)}'''
def end(lang,page,current_module=None):
    current_module=module_id(current_module)
    brand=shell(lang,CURRENT_AUDIENCE,page,current_module)
    return f'''<div class="mdg-shell conoce-shell">{brand['footer']}</div><script src="{asset_base(lang,page,current_module)}assets/site.js"></script></body></html>'''

def adapt_audience_body(content,lang,page):
  copy=AUDIENCE_SPEC['locales'][lang][CURRENT_AUDIENCE][page]
  main=re.search(r'<main\b[^>]*>',content)
  if not main:raise RuntimeError(f'AUDIENCE_MAIN_MISSING:{lang}:{CURRENT_AUDIENCE}:{page}')
  content=content[:main.end()-1]+f' data-audience-content="{CURRENT_AUDIENCE}">'+content[main.end():]
  h1=re.search(r'<h1\b([^>]*)>[\s\S]*?</h1>',content)
  if not h1:raise RuntimeError(f'AUDIENCE_HERO_MISSING:{lang}:{CURRENT_AUDIENCE}:{page}')
  content=content[:h1.start()]+f'<h1{h1.group(1)} data-audience-field="hero">{esc(copy["hero"])}</h1>'+content[h1.end():]
  lead=re.search(r'<p\b([^>]*\bclass="[^"]*\blead\b[^"]*"[^>]*)>[\s\S]*?</p>',content)
  if not lead:raise RuntimeError(f'AUDIENCE_LEAD_MISSING:{lang}:{CURRENT_AUDIENCE}:{page}')
  problem=f'<p{lead.group(1)} data-audience-field="problem">{esc(copy["problem"])}</p>'
  benefit=''
  content=content[:lead.start()]+problem+benefit+content[lead.end():]
  section_end=content.find('</section>',main.end())
  if section_end<0:raise RuntimeError(f'AUDIENCE_PRIMARY_SURFACE_MISSING:{lang}:{CURRENT_AUDIENCE}:{page}')
  benefit_card=''
  if page not in EDITORIAL_PAGES:
    official_context=f'<p data-official-localized-guide-context>{esc(DECK_RESOURCE["locales"][lang]["description"])}</p>' if page=='deck' else ''
    benefit_card=f'<article class="card evidence"><p data-audience-field="benefits">{esc(copy["benefits"])}</p>{official_context}</article>'
  guidance=f'''<div class="shell rubric" data-audience-guidance="{CURRENT_AUDIENCE}">{benefit_card}<article class="card evidence"><p data-audience-field="method">{esc(copy['method'])}</p></article><article class="card evidence"><p data-audience-field="evidence">{esc(copy['evidence'])}</p></article></div>'''
  point=section_end+len('</section>');content=content[:point]+guidance+content[point:]
  close=content.rfind('</main>')
  if close<0:raise RuntimeError(f'AUDIENCE_MAIN_CLOSE_MISSING:{lang}:{CURRENT_AUDIENCE}:{page}')
  anchor=EXPECTED_INTRAPAGE_ANCHORS[page][-1]
  action=f'''<section class="section" data-audience-action="{CURRENT_AUDIENCE}"><div class="shell"><a class="btn primary" href="#{esc(anchor)}" data-audience-field="cta">{esc(copy['cta'])}</a><p class="lead" data-audience-field="closing">{esc(copy['closing'])}</p></div></section>'''
  content=content[:close]+action+content[close:]
  for field in AUDIENCE_SURFACES:
    if content.count(f'data-audience-field="{field}"')!=1:
      raise RuntimeError(f'AUDIENCE_FIELD_RENDER_INVALID:{lang}:{CURRENT_AUDIENCE}:{page}:{field}')
  return content

def module_variant(module_key,lang,audience):
  try:
    return MODULE_KITS[module_key]['variants'][(lang,audience)]
  except KeyError as error:
    raise RuntimeError(f'CURRICULUM_VARIANT_MISSING:{module_key}:{lang}:{audience}') from error

def module_depth_variant(module_key,lang,audience):
  try:
    return MODULE_KITS[module_key]['depth_variants'][(lang,audience)]
  except KeyError as error:
    raise RuntimeError(f'CURRICULUM_DEPTH_VARIANT_MISSING:{module_key}:{lang}:{audience}') from error

def module_resource_urls(lang,page,module_key):
  resource_urls={
    key:rel_page(lang,page,lang,key,module_key,module_key)
    for key in RESOURCE_PAGE_KEYS
  }
  # The renderer contract uses the editorial name while the route authority
  # keeps the historical technical key `deck` for backwards compatibility.
  resource_urls['masterclass']=resource_urls['deck']
  catalog=rel_page(lang,page,lang,'resources_index',module_key,DEFAULT_MODULE_ID)
  resource_urls['resources']=f'{catalog}#module-{MODULE_ROUTES[module_key]["order"]:02d}'
  spec=MODULE_KITS[module_key]['spec']
  resource_urls['pdf']=f'{asset_base(lang,page,module_key)}{spec["official_pdf"]["ref"]}'
  resource_urls['pdf_sha256']=spec['official_pdf']['sha256']
  resource_urls['pdf_tagged']=spec['official_pdf']['tagged']
  next_page={'deck':'workbook','workbook':'playbook','playbook':'prompts'}.get(page)
  if next_page:
    resource_urls['next']=resource_urls[next_page]
    resource_urls['next_label']=RESOURCE_NAMES[lang][MODULE_ROUTES[module_key]['order']-1][RESOURCE_NAME_KEYS[next_page]]
  else:
    order=MODULE_ROUTES[module_key]['order']
    if order<4:
      next_module=MODULE_IDS[order]
      resource_urls['next']=rel_page(lang,page,lang,'deck',module_key,next_module)
      resource_urls['next_label']=RESOURCE_NAMES[lang][order]['masterclass']
    else:
      resource_urls['next']=resource_urls['resources']
      resource_urls['next_label']={'es':'Volver al mapa de Nivel 0','en':'Return to the Level 0 map','pt':'Voltar ao mapa do Nível 0'}[lang]
  return resource_urls

def module_intrapage_items(lang,page,module):
  if page=='deck':
    return [
      {'anchor':'masterclass-inicio','label':{'es':'Presentación','en':'Introduction','pt':'Apresentação'}[lang]},
      {'anchor':'masterclass-pdf','label':{'es':'PDF oficial','en':'Official PDF','pt':'PDF oficial'}[lang]},
      {'anchor':'masterclass-guia','label':{'es':'Guía accesible','en':'Accessible guide','pt':'Guia acessível'}[lang]},
    ]
  if page=='workbook':
    stage_labels=WORKBOOK_STAGE_LABELS[lang]
    return [
      {'anchor':'workbook-inicio','label':{'es':'Inicio','en':'Start','pt':'Início'}[lang]},
      {'anchor':'guia','label':{'es':'Guía','en':'Guide','pt':'Guia'}[lang]},
      {'anchor':'descarga','label':{'es':'Recursos','en':'Resources','pt':'Recursos'}[lang]},
      {'anchor':'preparacion','label':{'es':'Preparación','en':'Preparation','pt':'Preparação'}[lang]},
      {'anchor':'sheet-session','label':stage_labels[0]},
      {'anchor':'sheet-depth','label':stage_labels[1]},
      {'anchor':'sheet-consolidation','label':stage_labels[2]},
      {'anchor':'transferencia','label':{'es':'Transferencia','en':'Transfer','pt':'Transferência'}[lang]},
    ]
  if page=='playbook':
    chapters=module['playbook']['chapters']
    middle=[{'anchor':chapter['id'],'label':chapter['title']} for chapter in chapters[:5]]
    return [
      {'anchor':'playbook-inicio','label':{'es':'Inicio','en':'Start','pt':'Início'}[lang]},
      {'anchor':'intro','label':{'es':'Punto de partida','en':'Starting point','pt':'Ponto de partida'}[lang]},
      *middle,
      {'anchor':'close','label':{'es':'Cierre','en':'Close','pt':'Fechamento'}[lang]},
    ]
  prompts=module['promptLibrary']['prompts']
  midpoint=prompts[min(5,len(prompts)-1)]
  return [
    {'anchor':'prompts-inicio','label':{'es':'Inicio','en':'Start','pt':'Início'}[lang]},
    {'anchor':'directos','label':{'es':'Biblioteca','en':'Library','pt':'Biblioteca'}[lang]},
    {'anchor':prompts[0]['id'],'label':prompts[0]['title']},
    {'anchor':midpoint['id'],'label':midpoint['title']},
    {'anchor':'metaprompts','label':{'es':'Metaprompts','en':'Metaprompts','pt':'Metaprompts'}[lang]},
  ]

def bind_module_audience(content,variant,page,urls):
  editorial=variant.get('editorial',{})
  required={'hero','problem','benefits','method','evidence','cta'}
  if set(editorial)!=required:
    raise RuntimeError(f'CURRICULUM_EDITORIAL_FIELDS_INVALID:{variant.get("locale")}:{variant.get("audience")}:{page}')
  opening=re.search(r'<main\b[^>]*>',content)
  if not opening:
    raise RuntimeError('CURRICULUM_MAIN_MISSING')
  content=content[:opening.end()-1]+f' data-audience-content="{esc(variant["audience"])}"'+content[opening.end()-1:]
  hero=editorial['hero'];problem=editorial['problem'];benefits=editorial['benefits'];method=editorial['method'];evidence=editorial['evidence'];cta=editorial['cta']
  current_anchor={'deck':'#masterclass-guia','workbook':'#sheet-session','playbook':'#intro','prompts':'#directos'}[page]
  block=f'''<section class="module-positioning" data-module-positioning><div class="shell module-positioning-grid"><header><span class="eyebrow">{esc(hero['eyebrow'])}</span><h2 data-audience-field="hero">{esc(hero['title'])}</h2><p data-audience-field="problem">{esc(problem['body'])}</p></header><div class="module-positioning-points"><article><strong>{esc(benefits['title'])}</strong><p data-audience-field="benefits">{esc(benefits['body'])}</p></article><article><strong>{esc(method['title'])}</strong><p data-audience-field="method">{esc(method['body'])}</p></article><article><strong>{esc(evidence['title'])}</strong><p data-audience-field="evidence">{esc(evidence['body'])}</p></article></div><footer><a class="btn" href="{current_anchor}" data-audience-field="cta">{esc(cta['action'])}{ui_icon('arrow')}</a><p data-audience-field="closing">{esc(variant['module']['transfer'])}</p></footer></div></section>'''
  search_from=opening.end()
  if page=='prompts':
    direct_section=content.find('<section class="prompt-library-section shell" id="directos"',search_from)
    if direct_section<0:
      raise RuntimeError('CURRICULUM_PROMPT_LIBRARY_SECTION_MISSING')
    section_start=direct_section
  else:
    section_start=content.find('<section',search_from)
  if section_start<0:
    raise RuntimeError('CURRICULUM_PRIMARY_SECTION_MISSING')
  depth=0;point=-1
  for match in re.finditer(r'<(/?)section\b[^>]*>',content[section_start:],re.I):
    depth += -1 if match.group(1) else 1
    if depth==0:
      point=section_start+match.end()
      break
  if point<0:
    raise RuntimeError('CURRICULUM_PRIMARY_SECTION_UNBALANCED')
  content=content[:point]+block+content[point:]
  for field in AUDIENCE_SURFACES:
    if content.count(f'data-audience-field="{field}"')!=1:
      raise RuntimeError(f'CURRICULUM_AUDIENCE_FIELD_INVALID:{variant["locale"]}:{variant["audience"]}:{page}:{field}')
  return content

def module_resource_page(lang,page,module_key):
  variant=module_variant(module_key,lang,CURRENT_AUDIENCE)
  depth=module_depth_variant(module_key,lang,CURRENT_AUDIENCE)
  module=variant['module']
  urls=module_resource_urls(lang,page,module_key)
  renderer={'deck':render_masterclass,'workbook':render_workbook,'playbook':render_playbook,'prompts':render_prompts}[page]
  resource_key=RESOURCE_PAYLOAD_KEYS[page]
  if page=='prompts':
    convention=ADVANCED['locales'][lang]['level_convention']
    guide=notebook_execution_guide(lang,convention,include_method_mark=False)
    content=renderer(
      module[resource_key],lang,CURRENT_AUDIENCE,module,urls,depth=depth,execution_guide=guide,
      execution_copy=NOTEBOOK_EXECUTION['locales'][lang],
      level_convention=convention,
      artifact_labels=PROMPT_ARTIFACTS['module_artifacts'][module_key][lang],
    )
  elif page=='workbook':
    content=renderer(
      module[resource_key],lang,CURRENT_AUDIENCE,module,urls,depth=depth,
      artifact_labels=PROMPT_ARTIFACTS['module_artifacts'][module_key][lang],
    )
  else:
    content=renderer(module[resource_key],lang,CURRENT_AUDIENCE,module,urls,depth=depth)
  content=bind_module_audience(content,variant,page,urls)
  nav_items=module_intrapage_items(lang,page,module)
  title=module[resource_key]['title']
  return head(lang,title,page,module_key,nav_items)+content+end(lang,page,module_key),nav_items,urls


def resource_catalog(lang,classes,source_page='landing'):
    labels={'masterclass':T[lang]['masterclass'],'workbook':T[lang]['workbook'],'playbook':T[lang]['playbook'],'prompts':T[lang]['prompts']}
    class_word={'es':'Clase','en':'Class','pt':'Aula'}[lang]
    path_label={'es':'Ruta del recurso','en':'Resource path','pt':'Caminho do recurso'}[lang]
    groups=[]
    for index,(course,names,module_key) in enumerate(zip(classes,RESOURCE_NAMES[lang],MODULE_IDS),1):
      cards=[]
      for kind in ('masterclass','workbook','playbook','prompts'):
        page={'masterclass':'deck','workbook':'workbook','playbook':'playbook','prompts':'prompts'}[kind]
        href=rel_page(lang,source_page,lang,page,DEFAULT_MODULE_ID,module_key)
        cards.append(f'''<a class="catalog-resource available" href="{esc(href)}" data-curriculum-resource="{esc(module_key)}:{esc(page)}"><span class="resource-path" aria-label="{path_label}"><span>{esc(T[lang]['route'])}</span><i aria-hidden="true">/</i><span>{class_word} {index:02d}</span><i aria-hidden="true">/</i><span>{esc(labels[kind])}</span></span><strong>{esc(names[kind])}</strong><small>{esc(T[lang]['ready'])}</small></a>''')
      groups.append(f'''<section class="catalog-class" id="module-{index:02d}" aria-labelledby="catalog-class-{index}-{lang}" data-curriculum-module="{esc(module_key)}"><header><span>{class_word} {index:02d}</span><h3 id="catalog-class-{index}-{lang}">{esc(course['title'])}</h3></header><div class="catalog-grid">{''.join(cards)}</div></section>''')
    return ''.join(groups)

def landing(lang):
    l=LANDING['locales'][lang]
    base=asset_base(lang,'landing')
    evidence_label={'es':'Evidencia','en':'Evidence','pt':'Evidência'}[lang]
    routes_label={'es':'3 rutas','en':'3 routes','pt':'3 rotas'}[lang]
    organic_label={'es':'Ciclo de aprendizaje orgánico','en':'Organic learning loop','pt':'Ciclo de aprendizagem orgânica'}[lang]
    help_url=HELP_BY_LANG[lang]
    offer=''.join(f'<li><span aria-hidden="true">✓</span>{esc(x)}</li>' for x in l['offer'])
    n0_principles=''.join(f'''<div class="n0-principle"><strong aria-hidden="true">{esc(x['value'])}</strong><span>{esc(x['label'])}</span><small>{esc(x['note'])}</small></div>''' for x in l['n0_principles'])
    verbs=''.join(f'<span>{esc(x)}</span>' for x in l['verbs'])
    tensions=''.join(f'<button class="tension-card" type="button" data-tension aria-pressed="false"><span class="tension-num">0{i}</span><strong>{esc(x[0])}</strong><span>{esc(x[1])}</span><em>{esc(x[2])} →</em></button>' for i,x in enumerate(l['tensions'],1))
    video=next(item for item in RESOURCES['videos'] if item['id']=='de-ocupado-a-productivo'); video_l=video['locales'][lang]
    class_cards=[]
    for i,c in enumerate(l['classes'],1):
      video_link=f'''<a class="route-video" href="{video['url']}" target="_blank" rel="noopener noreferrer"><span aria-hidden="true">▶</span><span><small>{esc(video_l['label'])}</small><strong>{esc(video_l['title'])}</strong></span><em>{esc(video_l['cta'])} ↗</em></a>''' if i==video['class_order'] else ''
      class_cards.append(f'''<article class="route-stage reveal" data-route-stage data-step="0{i}"><div class="route-stage-head"><span class="route-number" aria-hidden="true">0{i}</span><span class="eyebrow">{esc(c['verb'])}</span><span class="state-pill active">{esc(c['state'])}</span></div><h3>{esc(c['title'])}</h3><p class="route-hook">{esc(c['hook'])}</p><p class="route-question">{esc(c['question'])}</p><dl><div><dt>{'Prerrequisito' if lang=='es' else 'Prerequisite' if lang=='en' else 'Pré-requisito'}</dt><dd>{esc(c['prerequisite'])}</dd></div><div><dt>{'Práctica' if lang=='es' else 'Practice' if lang=='en' else 'Prática'}</dt><dd>{esc(c['practice'])}</dd></div><div><dt>{evidence_label}</dt><dd>{esc(c['evidence'])}</dd></div></dl><div class="route-takeaway"><span>{esc(l['story_labels']['takeaway'])}</span><p>{esc(c['takeaway'])}</p></div><p class="route-punchline">{esc(c['punchline'])}</p>{video_link}<p class="route-bridge">→ {esc(c['bridge'])}</p></article>''')
    class_cards=''.join(class_cards)
    demo_steps=''.join(f'<li><span>{i:02d}</span>{esc(x)}</li>' for i,x in enumerate(l['demo_steps'],1))
    artifacts=''.join(f'<article class="evidence-chip reveal"><span>{i:02d}</span><strong>{esc(x)}</strong></article>' for i,x in enumerate(l['demo_artifacts'],1))
    outcomes=''.join(f'<article class="outcome-card reveal"><span class="state-pill active">{esc(x[1])}</span><span class="outcome-num" aria-hidden="true">0{i}</span><h3>{esc(x[0])}</h3><p>{esc(x[2])}</p></article>' for i,x in enumerate(l['outcomes'],1))
    method=''.join(f'<article class="method-card reveal"><span>0{i}</span><h3>{esc(x[0])}</h3><p>{esc(x[1])}</p></article>' for i,x in enumerate(l['method_points'],1))
    requirements=''.join(f'<li>{esc(x)}</li>' for x in l['requirements'])
    faq=''.join(f'<details><summary>{esc(x[0])}</summary><p>{esc(x[1])}</p></details>' for x in l['faq'])
    ambassadors=l['ambassador_letter']; javier=l['javier_letter']
    ambassador_paragraphs=''.join(f'<p>{esc(x)}</p>' for x in ambassadors['paragraphs'])
    javier_paragraphs=''.join(f'<p>{esc(x)}</p>' for x in javier['paragraphs'])
    deck=RESOURCES['deck']['locales'][lang]
    featured_videos=[item for item in RESOURCES['videos'] if item.get('featured')]
    featured_cards=''.join(f'''<a class="resource-cover video-cover {'video-masterclass' if item['kind']=='masterclass_recording' else 'video-intro'} reveal" href="{item['url']}" target="_blank" rel="noopener noreferrer"><span class="cover-type">{esc(item['locales'][lang]['label'])}</span><span class="cover-number" aria-hidden="true">{'90' if item['kind']=='masterclass_recording' else 'AI'}</span><span class="video-platform">YouTube · MetodologIA</span><h3>{esc(item['locales'][lang]['title'])}</h3><p>{esc(item['locales'][lang]['description'])}</p><strong>{esc(item['locales'][lang]['cta'])}{ui_icon('external')}</strong></a>''' for item in featured_videos)
    playbook_l=PLAYBOOK['locales'][lang]
    playbook_card=f'''<a class="resource-cover playbook-cover reveal" href="playbook/index.html"><span class="cover-type">Playbook · MetodologIA</span>{method_mark(lang,'landing','primary','cover-method-mark')}<h3>{esc(playbook_l['title'])}</h3><p>{esc(playbook_l['lead'])}</p><strong>{esc(playbook_l['primary_cta'])}{ui_icon('arrow')}</strong></a>'''
    skill=RESOURCES['open_skill']
    skill_l=skill['locales'][lang]
    open_skill=f'''<a class="open-skill-card reveal" href="{skill['url']}" target="_blank" rel="noopener noreferrer" data-open-skill>{method_mark(lang,'landing','compact','open-skill-mark')}<span class="eyebrow">{esc(skill_l['eyebrow'])}</span><h3>{esc(skill_l['title'])}</h3><p>{esc(skill_l['description'])}</p><span class="open-skill-meta">{esc(skill['tag'])} · {esc(skill['license'])}</span><strong>{esc(skill_l['cta'])}{ui_icon('external')}</strong></a>'''
    catalog=resource_catalog(lang,l['classes'])
    catalog_title={'es':'Mapa de los 16 entregables','en':'Map of the 16 deliverables','pt':'Mapa dos 16 entregáveis'}[lang]
    course_json=json.dumps({"@context":"https://schema.org","@type":"Course","name":l['meta_title'],"description":l['meta_description'],"provider":{"@type":"Organization","name":"MetodologIA","url":"https://metodologia.info/"},"isAccessibleForFree":True,"inLanguage":lang,"hasCourseInstance":{"@type":"CourseInstance","courseMode":"online"}},ensure_ascii=False,separators=(',',':'))
    return head(lang,l['meta_title'],'landing')+f'''<main id="main" class="landing-v2">
<section class="chapter hero-v2" id="entrada" data-chapter="01"><div class="shell hero-v2-grid"><div class="hero-copy"><span class="badge">{esc(l['offer'][0])} · {esc(l['offer'][1])}</span><div class="eyebrow">{esc(l['hero_eyebrow'])}</div><h1 class="h1 hero-title">{l['hero_title']}</h1><p class="lead">{esc(l['hero_lead'])}</p><div class="actions"><a class="btn" href="{FORM}" target="_blank" rel="noopener noreferrer">{esc(l['enroll'])} →</a><a class="btn secondary" href="#experiencia">{esc(l['open_resources'])}</a></div></div><div class="n0-scene" aria-label="{esc(T[lang]['route'])}"><div class="n0-core" aria-hidden="true"><span>N</span><strong>0</strong></div><p class="n0-caption">{esc(l['n0_caption'])}</p><div class="n0-principles">{n0_principles}</div><div class="n0-line" aria-hidden="true"></div></div></div><div class="shell"><ul class="offer-strip">{offer}</ul></div></section>
<section class="chapter tension-section" id="tension" data-chapter="02"><div class="shell"><div class="section-head reveal"><span class="eyebrow">{esc(l['tension_eyebrow'])}</span><h2 class="h2">{esc(l['tension_title'])}</h2><p class="lead">{esc(l['tension_lead'])}</p></div><div class="tension-grid">{tensions}</div><p class="tension-output" data-tension-output aria-live="polite"></p></div></section>
<section class="chapter route-section" id="ruta" data-chapter="03"><div class="shell route-layout"><div class="route-intro"><span class="eyebrow">{esc(l['route_eyebrow'])}</span><h2 class="h2">{esc(l['route_title'])}</h2><p class="lead">{esc(l['route_lead'])}</p><div class="route-rail" aria-hidden="true"><span data-route-progress></span></div></div><div class="route-stages">{class_cards}</div></div></section>
<section class="chapter demo-section" id="demostracion" data-chapter="04"><div class="shell"><div class="section-head reveal"><span class="eyebrow">{esc(l['demo_eyebrow'])}</span><h2 class="h2">{esc(l['demo_title'])}</h2><p class="lead">{esc(l['demo_lead'])}</p></div><div class="demo-grid"><ol class="method-flow">{demo_steps}</ol><div class="artifact-board"><div class="artifact-source-cloud" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span></div>{artifacts}<div class="actions"><a class="btn secondary" href="workbook/index.html#step-1">{esc(l['workbook_cta'])} →</a><a class="text-link" href="deck/index.html#page-9">{esc(deck['open'])} →</a></div></div></div></div></section>
<section class="chapter experience-section" id="experiencia" data-chapter="05"><div class="shell"><div class="section-head reveal"><span class="eyebrow">{esc(l['experience_eyebrow'])}</span><h2 class="h2">{esc(l['experience_title'])}</h2><p class="lead">{esc(l['experience_lead'])}</p></div><div class="experience-grid">{featured_cards}{playbook_card}</div>{open_skill}<details class="roadmap" open><summary>{catalog_title}<span>16</span></summary><p>{esc(l['roadmap'])}</p><div class="resource-catalog">{catalog}</div></details></div></section>
<section class="chapter outcomes-section" id="resultados" data-chapter="06"><div class="shell"><div class="section-head reveal"><span class="eyebrow">{esc(l['outcomes_eyebrow'])}</span><h2 class="h2">{esc(l['outcomes_title'])}</h2><p class="lead">{esc(l['outcomes_lead'])}</p></div><div class="outcome-grid">{outcomes}</div><div class="organic-loop"><span class="eyebrow">{organic_label}</span><p>{esc(l['organic_loop'])}</p></div></div></section>
<section class="chapter method-section" id="metodo" data-chapter="07"><div class="shell"><div class="section-head reveal"><span class="eyebrow">{esc(l['method_eyebrow'])}</span><h2 class="h2">{esc(l['method_title'])}</h2><p class="lead">{esc(l['method_lead'])}</p></div><div class="method-grid">{method}</div><div class="trust-grid"><div><h3>{esc(l['requirements_title'])}</h3><ul class="requirements">{requirements}</ul><a class="official-link" href="{help_url}" target="_blank" rel="noopener noreferrer">{'Consultar límites oficiales de NotebookLM' if lang=='es' else 'Read official NotebookLM limits' if lang=='en' else 'Consultar limites oficiais do NotebookLM'} ↗</a></div><div class="faq">{faq}</div></div><article class="letter-card ambassador-letter reveal" aria-labelledby="ambassador-letter-title"><div class="letter-mark pristino-mark"><img src="{base}assets/javier-montano.jpg" alt="Prístino · MetodologIA" width="460" height="460" loading="lazy" decoding="async"></div><div class="letter-body"><span class="eyebrow">{esc(ambassadors['label'])}</span><h3 id="ambassador-letter-title">{esc(ambassadors['title'])}</h3>{ambassador_paragraphs}<footer><strong>{esc(ambassadors['signature'])}</strong><span>{esc(ambassadors['role'])}</span></footer></div></article></div></section>
<section class="chapter final-section" id="convocatoria" data-chapter="08"><div class="shell"><article class="letter-card javier-letter reveal" aria-labelledby="javier-letter-title"><a class="letter-mark portrait founder-portrait" href="https://github.com/JaviMontano" target="_blank" rel="noopener noreferrer" aria-label="Javier Montaño · GitHub"><img src="{base}assets/team-javier-montano.webp" alt="{esc(javier['portrait_alt'])}" width="560" height="560" loading="lazy" decoding="async"></a><div class="letter-body"><span class="eyebrow">{esc(javier['label'])}</span><h3 id="javier-letter-title">{esc(javier['title'])}</h3>{javier_paragraphs}<footer><strong>{esc(javier['signature'])}</strong><span>{esc(javier['role'])}</span></footer></div></article><div class="final-grid"><div><span class="eyebrow">{esc(l['final_eyebrow'])}</span><h2 class="h2">{esc(l['final_title'])}</h2><p class="lead">{esc(l['final_lead'])}</p><div class="actions"><a class="btn" href="{FORM}" target="_blank" rel="noopener noreferrer">{esc(l['enroll'])} →</a><a class="btn secondary" href="workbook/index.html">{esc(l['workbook_cta'])}</a></div><p class="form-note">{esc(l['form_note'])}</p></div><div class="final-mark" aria-hidden="true"><span>N</span><strong>0</strong><i></i></div></div></div></section>
</main><script type="application/ld+json">{course_json}</script>'''+end(lang,'landing')

W={
'es':{'title':'Workbook · Aprende a aprender con NotebookLM','lead':'Tres hojas para empezar en clase, profundizar y consolidar de forma autónoma.','tabs':['En clase','Profundización','Consolidación'],'sheet1':'Cinco pasos esenciales','sheet1p':'Avanza en orden. La persona define propósito, revisa fuentes y decide cuándo la evidencia es suficiente.','sheet2':'De la base a una práctica defendible','sheet2p':'Prompts 6–10 para crear, aplicar, evaluar y ensayar sin salir de las fuentes.','sheet3':'Demuestra, transfiere y decide','sheet3p':'La consolidación exige evidencia y explicación propia; no basta con que la respuesta suene bien.','copy':'Copiar','open':'Abrir NotebookLM ↗','official':'Ayuda oficial ↗','expected':'Evidencia esperada','checks':['Puedo explicar el propósito de mi Notebook en una frase.','Puedo nombrar dos fuentes decisivas y un vacío aceptado.','Puedo mostrar una respuesta con citas y revisar su soporte.','Puedo enseñar el proceso a otra persona sin leer el prompt.'],'states':['Completado: existe evidencia revisable.','Pendiente: sé cuál es el siguiente paso.','coverage_gap: falta fuente, contexto o prueba.'],'challenge':'Reto autónomo','challengep':'Crea un Notebook para una decisión real, ejecuta el ciclo 1–5 y usa un prompt de profundidad. Entrega un mapa de fuentes, el veredicto de suficiencia y una explicación de 3 minutos.','note':'NotebookLM puede responder con base en las fuentes seleccionadas y mostrar citas; esas ayudas no garantizan precisión. Revisa siempre la fuente y conserva tu criterio. Deep Research exige 18 años o más y su disponibilidad puede variar según cuenta, plan y superficie; consulta la ayuda oficial.'},
'en':{'title':'Workbook · Learn how to learn with NotebookLM','lead':'Three sheets to start in class, go deeper and consolidate independently.','tabs':['In class','Deepening','Consolidation'],'sheet1':'Five essential steps','sheet1p':'Move in order. You define purpose, review sources and decide when evidence is sufficient.','sheet2':'From a source base to defensible practice','sheet2p':'Prompts 6–10 to create, apply, assess and rehearse without leaving the sources.','sheet3':'Demonstrate, transfer and decide','sheet3p':'Consolidation requires evidence and your own explanation; fluent output is not enough.','copy':'Copy','open':'Open NotebookLM ↗','official':'Official help ↗','expected':'Expected evidence','checks':['I can explain my Notebook purpose in one sentence.','I can name two decisive sources and one accepted gap.','I can show a cited answer and inspect its support.','I can teach the process without reading the prompt.'],'states':['Complete: reviewable evidence exists.','Pending: the next action is clear.','coverage_gap: a source, context or test is missing.'],'challenge':'Independent challenge','challengep':'Create a Notebook for a real decision, run steps 1–5 and use one deepening prompt. Deliver a source map, a sufficiency verdict and a three-minute explanation.','note':'NotebookLM can answer from selected sources and show citations; these aids do not guarantee accuracy. Inspect the source and keep human judgment. Deep Research requires users to be 18 or older and availability can vary by account, plan and surface; check official help.'},
'pt':{'title':'Workbook · Aprenda a aprender com NotebookLM','lead':'Três folhas para começar em aula, aprofundar e consolidar com autonomia.','tabs':['Em aula','Aprofundamento','Consolidação'],'sheet1':'Cinco passos essenciais','sheet1p':'Avance em ordem. A pessoa define o propósito, revisa fontes e decide quando a evidência é suficiente.','sheet2':'Da base a uma prática defensável','sheet2p':'Prompts 6–10 para criar, aplicar, avaliar e ensaiar sem sair das fontes.','sheet3':'Demonstre, transfira e decida','sheet3p':'A consolidação exige evidência e explicação própria; não basta uma resposta fluente.','copy':'Copiar','open':'Abrir NotebookLM ↗','official':'Ajuda oficial ↗','expected':'Evidência esperada','checks':['Consigo explicar o propósito do Notebook em uma frase.','Consigo nomear duas fontes decisivas e uma lacuna aceita.','Consigo mostrar uma resposta citada e revisar seu suporte.','Consigo ensinar o processo sem ler o prompt.'],'states':['Concluído: existe evidência revisável.','Pendente: o próximo passo está claro.','coverage_gap: falta fonte, contexto ou teste.'],'challenge':'Desafio autônomo','challengep':'Crie um Notebook para uma decisão real, execute os passos 1–5 e use um prompt de aprofundamento. Entregue mapa de fontes, veredito de suficiência e explicação de três minutos.','note':'O NotebookLM pode responder a partir das fontes selecionadas e mostrar citações; isso não garante precisão. Revise a fonte e preserve o critério humano. Deep Research exige 18 anos ou mais e a disponibilidade pode variar por conta, plano e interface; consulte a ajuda oficial.'}}
W['es'].update(tabs=list(WORKBOOK_STAGE_LABELS['es']),lead='Tres hojas para empezar en clase, profundizar y consolidar con evidencia.',sheet1='Cinco pasos',sheet1p='Define propósito, revisa fuentes y decide cuándo la evidencia es suficiente.',sheet2='Práctica guiada',sheet2p='Prompts 6–10 para crear, aplicar, evaluar y ensayar desde las fuentes.',sheet3='Transfiere y decide',sheet3p='Consolida con evidencia revisable, explicación propia y una prueba en otro contexto.')
W['en'].update(tabs=list(WORKBOOK_STAGE_LABELS['en']),lead='Three sheets to start in class, deepen, and consolidate with evidence.',sheet1='Five steps',sheet1p='Define purpose, review sources and decide when evidence is sufficient.',sheet2='Guided practice',sheet2p='Prompts 6–10 to create, apply, assess and rehearse from the sources.',sheet3='Transfer and decide',sheet3p='Consolidate with reviewable evidence, your own explanation, and a test in another context.')
W['pt'].update(tabs=list(WORKBOOK_STAGE_LABELS['pt']),lead='Três folhas para começar em aula, aprofundar e consolidar com evidência.',sheet1='Cinco passos',sheet1p='Defina propósito, revise fontes e decida quando a evidência é suficiente.',sheet2='Prática guiada',sheet2p='Prompts 6–10 para criar, aplicar, avaliar e ensaiar a partir das fontes.',sheet3='Transfira e decida',sheet3p='Consolide com evidência revisável, explicação própria e um teste em outro contexto.')

FORMAT_COPY={
  'es':{'parameters':'# PARÁMETROS','inputs':'# INPUTS','task':'# Tarea','workflow':'# Flujo','guardrails':'# Límites','output':'# Salida esperada','dod':'# Definition of Done','frameworks':'# MARCOS Y BUENAS PRÁCTICAS','role':'# Rol','objective':'# Objetivo','base':'# Prompt base','optional':'# Ajustes opcionales','example':'ej.','template':'Plantilla','demo':'Demo','mode':'Modo del prompt','syntax':'<INPUT> se reemplaza · [texto] se ajusta o borra','receives':'Recibe','produces':'Produce','previous':'Anterior','next':'Siguiente','branches':'Ramas','gate':'Gate externo','inputs_help':'Qué debes reemplazar','source_user':'Lo aportas tú','source_previous':'Viene de un paso previo','exec_objective':'Objetivo','exec_data':'Datos','exec_apply':'Aplica','exec_order':'Orden','exec_deliver':'Entrega','exec_close':'Cierra cuando la entrega sea revisable y cumpla el objetivo','exec_limit':'Límite'},
  'en':{'parameters':'# PARAMETERS','inputs':'# INPUTS','task':'# Task','workflow':'# Workflow','guardrails':'# Boundaries','output':'# Expected output','dod':'# Definition of Done','frameworks':'# FRAMEWORKS AND BEST PRACTICES','role':'# Role','objective':'# Objective','base':'# Base prompt','optional':'# Optional adjustments','example':'e.g.','template':'Template','demo':'Demo','mode':'Prompt mode','syntax':'Replace <INPUT> · adjust or delete [text]','receives':'Receives','produces':'Produces','previous':'Previous','next':'Next','branches':'Branches','gate':'External gate','inputs_help':'What you need to replace','source_user':'You provide it','source_previous':'From a previous step','exec_objective':'Objective','exec_data':'Data','exec_apply':'Apply','exec_order':'Order','exec_deliver':'Deliver','exec_close':'Close when the deliverable is reviewable and meets the objective','exec_limit':'Boundary'},
  'pt':{'parameters':'# PARÂMETROS','inputs':'# INPUTS','task':'# Tarefa','workflow':'# Fluxo','guardrails':'# Limites','output':'# Saída esperada','dod':'# Definition of Done','frameworks':'# FRAMEWORKS E BOAS PRÁTICAS','role':'# Papel','objective':'# Objetivo','base':'# Prompt base','optional':'# Ajustes opcionais','example':'ex.','template':'Modelo','demo':'Demo','mode':'Modo do prompt','syntax':'Substitua <INPUT> · ajuste ou apague [texto]','receives':'Recebe','produces':'Produz','previous':'Anterior','next':'Próximo','branches':'Ramos','gate':'Gate externo','inputs_help':'O que deve substituir','source_user':'Você fornece','source_previous':'Vem de uma etapa anterior','exec_objective':'Objetivo','exec_data':'Dados','exec_apply':'Aplique','exec_order':'Ordem','exec_deliver':'Entregue','exec_close':'Conclua quando a entrega for revisável e cumprir o objetivo','exec_limit':'Limite'}}

def prompt_input_token(item):
  return f'<{item["label"]} · {item["help"]} · {FORMAT_COPY[CURRENT_LANG]["example"]}: {item["example"]}>'

def resolve_prompt_mode(value,context,mode):
  """Resolve canonical <LABEL> tokens from the cell contract.

  Square brackets are reserved for declared optional clauses. Demo keeps their
  content but removes the editing notation; template keeps the notation.
  """
  inputs={item['label']:item for item in context['inputs']}
  resolved=value
  for label,item in inputs.items():
    replacement=(f'<{label} · {item["help"]} · {FORMAT_COPY[CURRENT_LANG]["example"]}: {item["example"]}>'
                 if mode=='template' else item['demo_value'])
    resolved=resolved.replace(f'<{label}>',replacement)
  if mode=='demo':
    for clause in context['optional_clauses']:
      resolved=resolved.replace(f'[{clause["text"]}]',clause['text'] if clause['default_enabled'] else '')
  return resolved

def prompt_parameters(context):
  return '\n'.join(f'{item["label"]} = {item["default"]}' for item in context['parameters'])

def prompt_inputs(context,mode):
  lines=[]
  for item in context['inputs']:
    value=(f'<{item["label"]} · {item["help"]} · {FORMAT_COPY[CURRENT_LANG]["example"]}: {item["example"]}>'
           if mode=='template' else item['demo_value'])
    lines.append(f'{item["label"]} = {value}')
  return '\n'.join(lines) or ('Ninguno' if CURRENT_LANG=='es' else 'None' if CURRENT_LANG=='en' else 'Nenhum')

def prompt_optionals(context,mode):
  if not context['optional_clauses']:
    return ''
  values=[]
  for clause in context['optional_clauses']:
    values.append(f'[{clause["text"]}]' if mode=='template' else clause['text'])
  return '\n'.join(values)

def safe_provenance_lines(items):
  """SPEC provenance labels are metadata, not optional clauses."""
  return '\n'.join('- '+re.sub(r'^\[([^]]+)\]\s*',r'\1: ',item) for item in items)

def executive_natural(spec,context,mode):
  """Project N1 as a concise executive instruction from the full contract."""
  c=FORMAT_COPY[CURRENT_LANG]
  data='; '.join(f'{item["label"]}=<{item["label"]}>' for item in context['inputs'])
  workflow=spec['workflow']
  actions=workflow[len(workflow)//2]
  deliver='; '.join(spec['output'])
  practices='; '.join(item.split(' · ',1)[0] for item in spec['frameworks'])
  value=(
    f'{c["exec_objective"]}: {spec["objective"]}.\n\n'
    f'{c["exec_data"]}: {data}.\n'
    f'{c["exec_apply"]}: {practices}.\n'
    f'{c["exec_order"]}: {actions}.\n'
    f'{c["exec_deliver"]}: {deliver}.\n'
    f'{c["exec_limit"]}: {spec["guardrails"][0]}.'
  )
  return resolve_prompt_mode(value,context,mode)

def structured_variants(lang,title,natural,spec,context,mode='template'):
  """Levels 2-4 are derived from the intent's own `level_spec`. There is no
  generic template fallback: `spec` is required and indexed by key so a missing
  contract field raises instead of silently rendering a shell."""
  c=FORMAT_COPY[lang]
  global CURRENT_LANG
  CURRENT_LANG=lang
  params=prompt_parameters(context)
  workflow='\n'.join(f'{i}. {step}' for i,step in enumerate(spec['workflow'],1))
  guardrails='\n'.join(f'- {item}' for item in spec['guardrails'])
  output='\n'.join(f'- {item}' for item in spec['output'])
  frameworks='\n'.join(f'- {item}' for item in spec['frameworks'])
  inputs=prompt_inputs(context,mode)
  optional=prompt_optionals(context,mode)
  optional_block=f"\n\n{c['optional']}\n{optional}" if optional else ''
  resolved_natural=executive_natural(spec,context,mode)
  parameter=f"{c['parameters']}\n{params}\n\n{c['inputs']}\n{inputs}{optional_block}\n\n{c['task']}\n{spec['objective']}\n\n{c['frameworks']}\n{frameworks}\n\n{c['workflow']}\n{workflow}\n\n{c['guardrails']}\n{guardrails}\n\n{c['output']}\n{output}"
  anatomy=PROMPT_LIBRARY['locales'][lang]['spec_format']
  execution_steps=[*spec['workflow'],anatomy['step_review'],anatomy['step_finish']]
  execution='\n'.join(f'{index}. {step}' for index,step in enumerate(execution_steps,1))
  edge_cases='\n'.join(f'- {item}' for item in anatomy['edge_case_items'])
  criteria='\n'.join(f'- {item}' for item in anatomy['criterion_items'])
  provenance=safe_provenance_lines(anatomy['provenance_items'])
  metadata='\n'.join(f'- {item}' for item in anatomy['metadata_items'])
  spec_role=spec['spec_role']
  spec_text=(
    '# SPEC MetodologIA\nversion: 2.0\nstatus: executable\n\n'
    f"## S — {anatomy['situation']}\n"
    f"{anatomy['context']}: {context['when']}\n"
    f"{anatomy['example_label']}: {context['example']}\n"
    f"{c['parameters']}\n{params}\n\n"
    f"{c['inputs']}\n{inputs}{optional_block}\n\n"
    f"## P — {anatomy['request']}\n"
    f"{anatomy['expert_role']}: {spec_role}\n"
    f"{anatomy['deliverable']}: {context['evidence']}\n"
    f"{anatomy['scope_in']}: {context['purpose']}\n"
    f"{anatomy['scope_out']}: {anatomy['scope_out_value']}\n\n"
    f"## E — {anatomy['execution']}\n"
    f"### {c['frameworks'].lstrip('# ')}\n{frameworks}\n\n"
    f"{anatomy['steps']}:\n{execution}\n\n"
    f"### {anatomy['edge_cases']}\n{edge_cases}\n\n"
    f"## C — {anatomy['criterion']}\n"
    f"{anatomy['output']}:\n{output}\n\n"
    f"{anatomy['observable_criteria']}:\n{criteria}\n\n"
    f"{anatomy['dod']}: {anatomy['dod_value']}\n\n"
    f"## {anatomy['provenance']}\n{provenance}\n\n"
    f"## {anatomy['metadata']}\n{metadata}\n\n"
    f"{anatomy['reasoning_policy']}"
  )
  pair=f"# system\n{spec['role']}\n\n{c['frameworks']}\n{frameworks}\n\n{c['guardrails']}\n{guardrails}\n\n{c['dod']}\n{spec['dod']}\n\n# user\n{c['parameters']}\n{params}\n\n{c['inputs']}\n{inputs}{optional_block}\n\n{c['task']}\n{spec['objective']}\n\n{c['workflow']}\n{workflow}\n\n{c['output']}\n{output}"
  return {'natural':resolved_natural,'parameters':parameter,'spec':spec_text,'pair':pair}

def prompt_visual_lines(value):
  """Render prompt source as readable, styleable lines without changing copy bytes."""
  lines=[]
  for line in value.split('\n'):
    stripped=line.strip()
    kind='body'
    if not stripped: kind='empty'
    elif stripped.startswith('### '): kind='subheading'
    elif stripped.startswith('## '): kind='section'
    elif stripped.startswith('# '): kind='heading'
    elif re.match(r'^\d+\.\s',stripped): kind='step'
    elif stripped.startswith('- '): kind='list'
    elif re.match(r'^[^:]{1,34}:\s',stripped): kind='field'
    lines.append(f'<span class="prompt-line prompt-line-{kind}">{esc(line)}</span>')
  return ''.join(lines)

WHY_SECTIONS=('acceptance_criteria','edge_cases','tradeoffs','assumptions','limits')

PROMPT_LIMIT_LABELS={'es':'Límite','en':'Limit','pt':'Limite'}

def prompt_limit_markup(lang,why,as_definition=False):
  """Expose one selection boundary without duplicating the full rationale.

  The complete list remains in the native ``prompt-why`` disclosure.  Cards use
  only the first governed limit so a reader can reject the wrong prompt before
  opening or copying it.
  """
  limit=why['limits'][0]
  label=PROMPT_LIMIT_LABELS[lang]
  if as_definition:
    return f'<div class="prompt-limit-compact"><dt>{esc(label)}</dt><dd>{esc(limit)}</dd></div>'
  return f'<p class="prompt-limit-compact"><strong>{esc(label)}</strong><span>{esc(limit)}</span></p>'

def prompt_why_markup(lang,group_id,why):
  """Expandable rationale next to the copyable prompt. Native <details>: no JS,
  and no data-prompt-template/data-prompt-format so the level panel counts hold."""
  labels=PROMPT_LIBRARY['locales'][lang]['why_format']
  sections=''.join(
    f'''<section><h4>{esc(labels[key])}</h4><ul>{''.join(f'<li>{esc(entry)}</li>' for entry in why[key])}</ul></section>'''
    for key in WHY_SECTIONS)
  return f'''<details class="prompt-why" data-prompt-why="{group_id}"><summary>{esc(labels['summary'])}</summary><div class="prompt-why-body">{sections}</div></details>'''

def prompt_input_guide_markup(lang,cell):
  c=FORMAT_COPY[lang]
  items=''.join(
    f'''<li><code>&lt;{esc(item['label'])}&gt;</code><span><strong>{esc(item['help'])}</strong><small>{esc(c['example'])}: {esc(item['example'])} · {esc(c['source_previous'] if item['source']=='previous_output' else c['source_user'])}</small></span></li>'''
    for item in cell['inputs'])
  if not items:
    return ''
  return f'''<details class="prompt-input-guide"><summary>{esc(c['inputs_help'])} <span>{len(cell['inputs'])}</span></summary><ul>{items}</ul></details>'''

def prompt_anchor(intent_id):
  if intent_id.startswith('W'):
    return f'#step-{int(intent_id[1:])}'
  if intent_id.startswith('B'):
    return f'#prompt-{intent_id.lower()}'
  return f'#prompt-{intent_id.lower()}'

def prompt_flow_markup(lang,intent_id):
  c=FORMAT_COPY[lang]; flow=PROMPT_CONTRACTS[intent_id]['flow']
  receives=(
    ', '.join(PROMPT_ARTIFACTS['artifacts'][artifact][lang] for artifact in flow['consumes'])
    if flow['consumes'] else
    ('Tus inputs' if lang=='es' else 'Your inputs' if lang=='en' else 'Seus inputs'))
  produces=PROMPT_ARTIFACTS['artifacts'][flow['produces']][lang]
  links=[]
  if flow['previous']:
    links.append(f'<a href="{prompt_anchor(flow["previous"])}">← {esc(c["previous"])} · {esc(contract_cell(flow["previous"],lang)["title"])}</a>')
  if flow['next']:
    links.append(f'<a href="{prompt_anchor(flow["next"])}">{esc(c["next"])} · {esc(contract_cell(flow["next"],lang)["title"])} →</a>')
  for branch in flow['branches']:
    links.append(f'<a class="prompt-flow-branch" href="{prompt_anchor(branch)}">{esc(c["branches"])} · {esc(contract_cell(branch,lang)["title"])} ↗</a>')
  gate=f'<span class="prompt-flow-gate">{esc(c["gate"])}</span>' if flow['external_gate'] else ''
  return f'''<div class="prompt-flow" data-prompt-flow="{esc(intent_id)}"><div><span>{esc(c['receives'])}</span><code>{esc(receives)}</code></div><i aria-hidden="true">→</i><div><span>{esc(c['produces'])}</span><code>{esc(produces)}</code></div>{gate}<nav aria-label="{esc(c['previous'])} / {esc(c['next'])}">{''.join(links)}</nav></div>'''

def prompt_formats_markup(lang,group_id,variant_modes,convention,cell,brain_input=None):
  tabs=[]; panels=[]
  items={item['key']:item for item in convention['items']}
  c=FORMAT_COPY[lang]
  for index,key in enumerate(('natural','parameters','spec','pair')):
    panel_id=f'{group_id}-{key}'
    context_id=f'{panel_id}-context'
    item=items[key]
    label=f'{item["level"]} · {item["name"]}'
    tabs.append(f'<button type="button" role="tab" tabindex="{0 if index==0 else -1}" aria-selected="{str(index==0).lower()}" aria-label="{esc(label)}" aria-controls="{panel_id}" data-prompt-format="{key}" data-level-number="{index+1}"><span class="prompt-tab-number" aria-hidden="true">{index+1}</span><span class="prompt-tab-copy" aria-hidden="true"><strong>{esc(item["name"])}</strong><small>{esc(item["level"])}</small></span></button>')
    template=variant_modes['template'][key]; demo=variant_modes['demo'][key]
    panels.append(f'''<details class="prompt-level-fallback" data-prompt-level="{index+1}"{" open" if index==0 else ""}><summary><span class="prompt-summary-number" aria-hidden="true">{index+1}</span><span><strong>{esc(label)}</strong><small>{esc(item["description"])}</small></span></summary><div class="prompt-level-context" id="{context_id}"><span>{esc(item["level"])}</span><strong>{esc(item["name"])}</strong><p>{esc(item["description"])}</p></div><pre class="prompt-format-panel prompt-format-panel-{key}" id="{panel_id}" role="tabpanel" tabindex="0" aria-label="{esc(label)} · {esc(c['template'])}" aria-describedby="{context_id}" data-prompt-template data-prompt-mode-panel="template">{prompt_visual_lines(template)}</pre><textarea class="prompt-format-source" hidden aria-hidden="true" tabindex="-1" data-prompt-source data-prompt-mode="template">{esc(template)}</textarea><details class="prompt-demo-native" data-prompt-mode-panel="demo"><summary>{esc(c['demo'])} · {esc(label)}</summary><pre class="prompt-format-panel prompt-format-panel-{key}" id="{panel_id}-demo" role="tabpanel" tabindex="0" aria-label="{esc(label)} · {esc(c['demo'])}" aria-describedby="{context_id}" data-prompt-demo>{prompt_visual_lines(demo)}</pre><textarea class="prompt-format-source" hidden aria-hidden="true" tabindex="-1" data-prompt-source data-prompt-mode="demo">{esc(demo)}</textarea></details></details>''')
  brain_item=next((item for item in cell['inputs'] if item['key']=='brain_dump'),None)
  brain_attr=(f' data-brain-input="{brain_input}" data-brain-label="{esc(brain_item["label"])}"' if brain_input and brain_item else '')
  copy_attr=f' data-brain-copy="{group_id}"{brain_attr}' if brain_input else f' data-format-copy="{group_id}"'
  copy_icon='<svg aria-hidden="true" viewBox="0 0 24 24"><rect x="8" y="8" width="11" height="11" rx="2"></rect><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"></path></svg>'
  copy_aria=f"{convention['copy']} · {convention['items'][0]['level']} · {convention['items'][0]['name']}"
  mode_controls=f'''<div class="prompt-mode-switch" role="group" aria-label="{esc(c['mode'])}"><button type="button" aria-pressed="true" data-prompt-mode-select="template">{esc(c['template'])}</button><button type="button" aria-pressed="false" data-prompt-mode-select="demo">{esc(c['demo'])}</button></div>'''
  return f'''<div class="prompt-library" data-prompt-library="{group_id}" data-active-level="1" data-active-format="natural" data-active-mode="template"><div class="prompt-library-toolbar">{mode_controls}<span class="prompt-syntax">{esc(c['syntax'])}</span></div>{prompt_input_guide_markup(lang,cell)}<div class="prompt-format-tabs" role="tablist" aria-label="{esc(convention['tablist'])}">{''.join(tabs)}</div><div class="prompt-format-panels">{''.join(panels)}</div><div class="prompt-library-actions"><button class="copy prompt-format-copy" type="button" aria-label="{esc(copy_aria)}"{copy_attr} data-copy-label="{esc(convention['copy'])}" data-copied-label="{esc(convention['copied'])}">{copy_icon}<span>{esc(convention['copy'])}</span></button><span class="prompt-copy-status sr-only" role="status" aria-live="polite"></span></div></div>'''

def level_convention_markup(lang):
  return ''

def prompt_cards(lang,start,end):
  w=W[lang]; out=[]
  deep_meta={locale:WORKBOOK_PROMPTS['locales'][locale]['deep_meta'] for locale in ('es','en','pt')}
  for n in range(start,end+1):
    cell=contract_cell(f'W{n:02d}',lang); title=cell['title']; pid=f'p{n}-{lang}'
    variants={mode:structured_variants(lang,title,cell['prompt'],cell['level_spec'],cell,mode) for mode in ('template','demo')}
    format_ui=prompt_formats_markup(lang,pid,variants,ADVANCED['locales'][lang]['level_convention'],cell)+prompt_why_markup(lang,pid,cell['why_it_works'])
    flow=('Entradas: tema, propósito y contexto · Acción: ejecutar y revisar · Salida: respuesta citada · Comprobación: contrastar con la fuente · Siguiente: decidir si avanzar.' if lang=='es' else 'Inputs: topic, purpose and context · Action: run and review · Output: cited response · Check: inspect the source · Next: decide whether to continue.' if lang=='en' else 'Entradas: tema, propósito e contexto · Ação: executar e revisar · Saída: resposta citada · Verificação: conferir a fonte · Próximo: decidir se avança.')
    meta=''
    if n>=6:
      when,inputs,output,limits,example=deep_meta[lang][n-6]
      ml={'es':('Entradas','Salida','Límites','Ejemplo'),'en':('Inputs','Output','Limits','Example'),'pt':('Entradas','Saída','Limites','Exemplo')}[lang]
      meta=f'<p><strong>{esc(when)}</strong><br>{ml[0]}: {esc(inputs)} · {ml[1]}: {esc(output)} · {ml[2]}: {esc(limits)} · {ml[3]}: {esc(example)}</p>'
    out.append(f'''<article class="card step" id="step-{n}"><span class="step-num">{n}</span><div><h3 class="h3">{esc(title)}</h3><p>{w['expected']}: {esc(('decisión y evidencia citada' if lang=='es' else 'a decision and cited evidence' if lang=='en' else 'uma decisão e evidência citada'))}.</p><p><strong>{esc(flow)}</strong></p>{meta}{prompt_limit_markup(lang,cell['why_it_works'])}</div>{prompt_flow_markup(lang,f'W{n:02d}')}<div class="prompt"><div class="prompt-head"><span>Prompt {n}</span></div>{format_ui}</div></article>''')
  return ''.join(out)

def workbook(lang):
  w=W[lang]
  help_url=HELP_BY_LANG[lang]
  intro={
    'es':{
      'eyebrow':'Clase 01 · Workbook de práctica','promise':'Construye un Notebook que puedas explicar y defender.','outcome':'Resultado del recorrido','outcome_body':'Una base con propósito, fuentes revisadas, un veredicto de suficiencia y un rol de IA elegido con criterio.','start':'Prompts para llegar preparado','start_lead':'Tres instrucciones breves convierten una idea suelta en insumos útiles antes de abrir las hojas.','routes':'Elige cómo recorrerlo','practical':'Ruta práctica','practical_body':'Llegas con cuenta, tema y fuentes. Copias los prompts, produces evidencia y avanzas por los gates.','guided':'Ruta de seguimiento','guided_body':'Sigues la lógica durante la clase, marcas lo que falta y completas la práctica después.','prepare':'Prepara el taller','prereq':'Prerrequisitos','inputs':'Insumos','boundaries':'Límites de trabajo','prereqs':['Cuenta Google con acceso a NotebookLM.','Navegador actualizado en computador; celular como apoyo.','Familiaridad básica con chats de IA: escribir, iterar y revisar.','Disposición para aprender una nueva forma de trabajar.'],'inputs_list':['Un tema, decisión o problema real.','Entre 3 y 8 fuentes que tengas derecho a usar.','Audiencia y resultado que quieres producir.','Un criterio para decidir cuándo la base es suficiente.'],'boundaries_list':['No cargues datos personales, confidenciales o restringidos.','Las citas ayudan a revisar; no garantizan exactitud.','El workbook no guarda ni envía respuestas.','La decisión final y el riesgo permanecen en la persona.'],
      'kickoffs':[('Aterriza el propósito','Ayúdame a convertir [TEMA] en un propósito de NotebookLM. Pregunta por la decisión, la audiencia, el plazo y el resultado. Después redacta una frase: “Este Notebook existe para…”.'),('Haz inventario de fuentes','Clasifica estas fuentes para [PROPÓSITO]: [LISTA]. Indica autoridad, vigencia, cobertura, tensiones y restricciones de uso. No inventes contenido que no hayas visto.'),('Define la evidencia de salida','Para [PROPÓSITO], define la evidencia mínima que demostraría una base útil: entregable, citas revisables, vacío aceptado, límite y decisión humana final.')]},
    'en':{
      'eyebrow':'Class 01 · Practice workbook','promise':'Build a Notebook you can explain and defend.','outcome':'Journey outcome','outcome_body':'A purposeful source base, reviewed evidence, a sufficiency verdict and an AI role chosen with judgment.','start':'Prompts to arrive prepared','start_lead':'Three short instructions turn a loose idea into useful inputs before opening the sheets.','routes':'Choose how to use it','practical':'Practical route','practical_body':'Arrive with an account, topic and sources. Copy prompts, produce evidence and advance through the gates.','guided':'Guided-follow route','guided_body':'Follow the logic during class, mark what is missing and complete the practice afterwards.','prepare':'Prepare for the workshop','prereq':'Prerequisites','inputs':'Inputs','boundaries':'Working boundaries','prereqs':['Google account with access to NotebookLM.','Updated desktop browser; phone as a secondary device.','Basic familiarity with AI chat: write, iterate and review.','Willingness to learn a new way of working.'],'inputs_list':['A real topic, decision or problem.','Three to eight sources you are allowed to use.','The audience and outcome you want to produce.','A criterion for deciding when the base is sufficient.'],'boundaries_list':['Do not upload personal, confidential or restricted data.','Citations support review; they do not guarantee accuracy.','The workbook does not save or send answers.','The final decision and risk remain human.'],
      'kickoffs':[('Ground the purpose','Help me turn [TOPIC] into a NotebookLM purpose. Ask about the decision, audience, deadline and outcome. Then write one sentence: “This Notebook exists to…”.'),('Inventory the sources','Classify these sources for [PURPOSE]: [LIST]. Identify authority, freshness, coverage, tensions and usage restrictions. Do not invent content you have not seen.'),('Define exit evidence','For [PURPOSE], define the minimum evidence of a useful base: deliverable, reviewable citations, accepted gap, limitation and final human decision.')]},
    'pt':{
      'eyebrow':'Aula 01 · Workbook de prática','promise':'Construa um Notebook que você consiga explicar e defender.','outcome':'Resultado do percurso','outcome_body':'Uma base com propósito, fontes revisadas, veredito de suficiência e papel da IA escolhido com critério.','start':'Prompts para chegar preparado','start_lead':'Três instruções curtas transformam uma ideia solta em insumos úteis antes de abrir as folhas.','routes':'Escolha como percorrer','practical':'Rota prática','practical_body':'Chegue com conta, tema e fontes. Copie prompts, produza evidência e avance pelos gates.','guided':'Rota de acompanhamento','guided_body':'Siga a lógica durante a aula, marque o que falta e complete a prática depois.','prepare':'Prepare a oficina','prereq':'Pré-requisitos','inputs':'Insumos','boundaries':'Limites de trabalho','prereqs':['Conta Google com acesso ao NotebookLM.','Navegador atualizado no computador; celular como apoio.','Familiaridade básica com chats de IA: escrever, iterar e revisar.','Disposição para aprender uma nova forma de trabalhar.'],'inputs_list':['Um tema, decisão ou problema real.','De três a oito fontes que você possa usar.','O público e o resultado que deseja produzir.','Um critério para decidir quando a base é suficiente.'],'boundaries_list':['Não carregue dados pessoais, confidenciais ou restritos.','As citações ajudam na revisão; não garantem precisão.','O workbook não salva nem envia respostas.','A decisão final e o risco permanecem com a pessoa.'],
      'kickoffs':[('Aterre o propósito','Ajude-me a transformar [TEMA] em propósito de NotebookLM. Pergunte sobre decisão, público, prazo e resultado. Depois escreva uma frase: “Este Notebook existe para…”.'),('Faça inventário das fontes','Classifique estas fontes para [PROPÓSITO]: [LISTA]. Indique autoridade, atualidade, cobertura, tensões e restrições de uso. Não invente conteúdo que não tenha visto.'),('Defina a evidência de saída','Para [PROPÓSITO], defina a evidência mínima de uma base útil: entregável, citações revisáveis, lacuna aceita, limite e decisão humana final.')]}
  }[lang]
  intro['start']={'es':'Ver prompts','en':'View prompts','pt':'Ver prompts'}[lang]
  checks=''.join(f'<label class="check"><input type="checkbox"> <span>{esc(x)}</span></label>' for x in w['checks'])
  states=''.join(f'<article class="card"><h3 class="h3">{esc(x.split(":")[0])}</h3><p>{esc(x)}</p></article>' for x in w['states'])
  rubric=('Rúbrica de fuentes: cobertura · autoridad · vigencia · diversidad · citas · suficiencia.' if lang=='es' else 'Source rubric: coverage · authority · freshness · diversity · citations · sufficiency.' if lang=='en' else 'Rubrica de fontes: cobertura · autoridade · atualidade · diversidade · citações · suficiência.')
  transfer=('Teach-back: explica el método en 3 minutos. Segundo contexto: repítelo con otra decisión. Continuidad: agenda una revisión en 7 días.' if lang=='es' else 'Teach-back: explain the method in 3 minutes. Second context: repeat it for another decision. Continuity: schedule a review in 7 days.' if lang=='en' else 'Teach-back: explique o método em 3 minutos. Segundo contexto: repita com outra decisão. Continuidade: agende revisão em 7 dias.')
  setup={'es':'W00 · Duración total 60–120 min · Requisito: cuenta Google, navegador y tema real. Privacidad: no cargues datos personales o confidenciales. Este documento no guarda ni envía tus respuestas; imprime o guarda localmente si lo decides. Tú decides; NotebookLM organiza y cita; el facilitador guía.','en':'W00 · Total duration 60–120 min · Requirement: Google account, browser and real topic. Privacy: do not upload personal or confidential data. This document does not save or send your answers; print or save locally only if you choose. You decide; NotebookLM organizes and cites; the facilitator guides.','pt':'W00 · Duração total 60–120 min · Requisito: conta Google, navegador e tema real. Privacidade: não carregue dados pessoais ou confidenciais. Este documento não salva nem envia suas respostas; imprima ou salve localmente apenas se decidir. Você decide; o NotebookLM organiza e cita; o facilitador guia.'}[lang]
  gate={'es':'Gate P10: propósito, dos fuentes decisivas, un vacío aceptado y veredicto BASE SUFICIENTE o REPETIR INVESTIGACIÓN.','en':'P10 gate: purpose, two decisive sources, one accepted gap and a BASE SUFFICIENT or REPEAT RESEARCH verdict.','pt':'Gate P10: propósito, duas fontes decisivas, uma lacuna aceita e veredito BASE SUFICIENTE ou REPETIR PESQUISA.'}[lang]
  labels={'es':['Propósito','Fuentes decisivas','Hallazgos de auditoría','Veredicto','Rol elegido'],'en':['Purpose','Decisive sources','Audit findings','Verdict','Selected role'],'pt':['Propósito','Fontes decisivas','Achados da auditoria','Veredito','Papel escolhido']}[lang]
  surfaces='<section class="card evidence"><h3 class="h3">W05 · '+('Superficies de trabajo imprimibles' if lang=='es' else 'Printable work surfaces' if lang=='en' else 'Superfícies de trabalho imprimíveis')+'</h3>'+''.join(f'<label class="field"><strong>{x}</strong><textarea aria-label="{x}"></textarea></label>' for x in labels)+'</section>'
  roles={'es':[('Profesor','Explica por etapas y comprueba comprensión','¿Qué quieres aprender?','Explicación + comprobación','No avanzar sin evidencia de comprensión'),('Asesor','Compara opciones, costos, riesgos y tensiones','¿Qué decisión debes tomar?','Recomendación con criterios','No decidir por la persona'),('Coach','Pregunta, refleja patrones y convierte en compromisos','¿Qué resultado y bloqueo tienes?','Compromiso + siguiente paso','No prescribir sin contexto')],'en':[('Teacher','Explains progressively and checks understanding','What do you want to learn?','Explanation + check','Do not advance without evidence of understanding'),('Advisor','Compares options, costs, risks and tensions','What decision must you make?','Criteria-based recommendation','Do not decide for the person'),('Coach','Asks, reflects patterns and turns them into commitments','What outcome and blocker do you have?','Commitment + next step','Do not prescribe without context')],'pt':[('Professor','Explica por etapas e verifica compreensão','O que deseja aprender?','Explicação + verificação','Não avançar sem evidência de compreensão'),('Assessor','Compara opções, custos, riscos e tensões','Que decisão precisa tomar?','Recomendação com critérios','Não decidir pela pessoa'),('Coach','Pergunta, reflete padrões e converte em compromissos','Qual resultado e bloqueio você tem?','Compromisso + próximo passo','Não prescrever sem contexto')]}[lang]
  rh={'es':['Rol','Conducta','Pregunta','Salida','No-go'],'en':['Role','Behavior','Question','Output','No-go'],'pt':['Papel','Conduta','Pergunta','Saída','Não fazer']}[lang]
  roles_title={'es':'W04 · Profesor / Asesor / Coach','en':'W04 · Teacher / Advisor / Coach','pt':'W04 · Professor / Assessor / Coach'}[lang]
  roles_table=f'<div class="table-wrap" tabindex="0" role="region" aria-label="{esc(roles_title)}"><table><thead><tr>'+''.join(f'<th>{esc(x)}</th>' for x in rh)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{esc(v)}</td>' for v in row)+'</tr>' for row in roles)+'</tbody></table></div>'
  levels={'es':['Insuficiente: falta evidencia o predominan fuentes débiles.','En progreso: cobertura parcial y citas revisables.','Suficiente: cobertura, autoridad, vigencia, diversidad, citas y riesgo residual explícitos.'],'en':['Insufficient: evidence is missing or weak sources dominate.','In progress: partial coverage and reviewable citations.','Sufficient: coverage, authority, freshness, diversity, citations and residual risk are explicit.'],'pt':['Insuficiente: falta evidência ou predominam fontes fracas.','Em progresso: cobertura parcial e citações revisáveis.','Suficiente: cobertura, autoridade, atualidade, diversidade, citações e risco residual explícitos.']}[lang]
  rubric_table='<div class="rubric">'+''.join(f'<article class="card"><p>{esc(x)}</p></article>' for x in levels)+'</div>'
  consolidation={
    'es':{'label':'Criterio de consolidación','criterion':'Puedes repetir el método sin guía, explicar tus decisiones y mostrar una base suficiente con fuentes revisables.','evidence':'Mapa de fuentes, veredicto de suficiencia, respuesta citada y explicación de tres minutos.','review':'Repítelo en otro contexto y revisa el resultado en siete días.'},
    'en':{'label':'Consolidation criterion','criterion':'You can repeat the method without guidance, explain your decisions, and show a sufficient base with reviewable sources.','evidence':'Source map, sufficiency verdict, cited answer, and a three-minute explanation.','review':'Repeat it in another context and review the result in seven days.'},
    'pt':{'label':'Critério de consolidação','criterion':'Você consegue repetir o método sem orientação, explicar suas decisões e mostrar uma base suficiente com fontes revisáveis.','evidence':'Mapa de fontes, veredito de suficiência, resposta citada e explicação de três minutos.','review':'Repita em outro contexto e revise o resultado em sete dias.'},
  }[lang]
  consolidation_gate=f'''<aside class="workbook-consolidation-gate" id="workbook-rubric" data-consolidation-gate aria-labelledby="workbook-consolidation-criterion"><span class="eyebrow">{esc(consolidation['label'])}</span><h3 id="workbook-consolidation-criterion">{esc(levels[-1].split(':',1)[0])}</h3><p>{esc(consolidation['criterion'])}</p><dl><div><dt>{esc(w['expected'])}</dt><dd>{esc(consolidation['evidence'])}</dd></div><div><dt>{esc('Revisión' if lang=='es' else 'Review' if lang=='en' else 'Revisão')}</dt><dd>{esc(consolidation['review'])}</dd></div></dl></aside>'''
  states=consolidation_gate+states
  back={'es':'Ver masterclass','en':'View masterclass','pt':'Ver masterclass'}[lang]
  advanced=ADVANCED['locales'][lang]
  access_urls=(NOTEBOOK,RESEARCH_BLUEPRINT,OPEN_NOTEBOOK)
  access_cards=''.join(f'''<a class="access-card" href="{url}" target="_blank" rel="noopener noreferrer"><span>0{i}</span><h3>{esc(item[0])}</h3><p>{esc(item[1])}</p><strong>{esc(item[2])} ↗</strong></a>''' for i,(item,url) in enumerate(zip(advanced['links'],access_urls),1))
  routes=''.join(f'''<article><span>0{i}</span><strong class="route-time">{esc(item[2])}</strong><h3>{esc(item[0])}</h3><p>{esc(item[1])}</p></article>''' for i,item in enumerate(advanced['routes'],1))
  expert_steps=''.join(f'''<li><span>{i:02d}</span><p>{esc(item)}</p></li>''' for i,item in enumerate(advanced['expert_steps'],1))
  prep_columns=''.join(f'''<article class="prep-card"><span>{i:02d}</span><h3>{esc(title)}</h3><ul>{''.join(f'<li>{esc(x)}</li>' for x in items)}</ul></article>''' for i,(title,items) in enumerate(((intro['prereq'],intro['prereqs']),(intro['inputs'],intro['inputs_list']),(intro['boundaries'],intro['boundaries_list'])),1))
  guide_steps=''.join(f'<li><span>{i:02d}</span><p>{esc(item)}</p></li>' for i,item in enumerate(advanced['guide_steps'],1))
  provider_links={
    'es':(('OpenAI · planes',OPENAI_PLANS),('Anthropic · Research',ANTHROPIC_RESEARCH),('NotebookLM · límites',NOTEBOOK_LIMITS),('Antigravity · guía',ANTIGRAVITY_GUIDE)),
    'en':(('OpenAI · plans',OPENAI_PLANS),('Anthropic · Research',ANTHROPIC_RESEARCH),('NotebookLM · limits',NOTEBOOK_LIMITS),('Antigravity · guide',ANTIGRAVITY_GUIDE)),
    'pt':(('OpenAI · planos',OPENAI_PLANS),('Anthropic · Research',ANTHROPIC_RESEARCH),('NotebookLM · limites',NOTEBOOK_LIMITS),('Antigravity · guia',ANTIGRAVITY_GUIDE)),
  }[lang]
  provider_link_html=''.join(f'<a href="{url}" target="_blank" rel="noopener noreferrer">{esc(label)} ↗</a>' for label,url in provider_links)
  guide=f'''<section class="workbook-guide" id="guia" aria-labelledby="guide-title-{lang}"><div class="section-head"><span class="eyebrow">00 · {esc(advanced['guide_title'])}</span><h2 class="h2" id="guide-title-{lang}">{esc(advanced['guide_title'])}</h2><p class="lead">{esc(advanced['guide_body'])}</p></div><ol class="guide-steps">{guide_steps}</ol><aside class="provider-notice"><span aria-hidden="true">i</span><div><strong>{esc('Condiciones de uso' if lang=='es' else 'Usage conditions' if lang=='en' else 'Condições de uso')}</strong><p>{esc(advanced['provider_notice'])}</p><nav aria-label="{esc('Fuentes oficiales' if lang=='es' else 'Official sources' if lang=='en' else 'Fontes oficiais')}">{provider_link_html}</nav></div></aside></section>'''
  brain_prompt_cards=[]
  for i,intent_id in enumerate(BRAIN_PROMPT_IDS,1):
    cell=contract_cell(intent_id,lang); title=cell['title']
    pid=f'brain-prompt-{lang}-{i}'
    variants={mode:structured_variants(lang,title,cell['prompt'],cell['level_spec'],cell,mode) for mode in ('template','demo')}
    format_ui=prompt_formats_markup(lang,pid,variants,advanced['level_convention'],cell,f'brain-dump-{lang}')+prompt_why_markup(lang,pid,cell['why_it_works'])
    brain_prompt_cards.append(f'''<article class="brain-prompt-card" id="prompt-{intent_id.lower()}"><header><span>0{i}</span><h3>{esc(title)}</h3></header>{prompt_limit_markup(lang,cell['why_it_works'])}{prompt_flow_markup(lang,intent_id)}<div class="prompt"><div class="prompt-head"><span>Prompt 0{i}</span></div>{format_ui}</div></article>''')
  prep_eyebrow=('Preparación · una entrada, tres movimientos' if lang=='es' else 'Preparation · one input, three moves' if lang=='en' else 'Preparação · uma entrada, três movimentos')
  brain=f'''<section class="brain-section" aria-labelledby="brain-title-{lang}"><div class="section-head"><span class="eyebrow">{esc(prep_eyebrow)}</span><h2 class="h2" id="brain-title-{lang}">{esc(advanced['brain_title'])}</h2><p class="lead">{esc(advanced['brain_body'])}</p></div><label class="brain-input"><strong>{esc(advanced['brain_label'])}</strong><textarea id="brain-dump-{lang}" rows="8" placeholder="{esc(advanced['brain_placeholder'])}" data-brain-dump></textarea><small>{esc(advanced['brain_dictation'])}</small><span class="brain-status" data-brain-status aria-live="polite" data-empty-message="{esc(advanced['brain_empty'])}"></span></label><div class="brain-prompt-grid">{''.join(brain_prompt_cards)}</div></section>'''
  use_cases=''.join(f'<li><span>{i:02d}</span><p>{esc(item)}</p></li>' for i,item in enumerate(advanced['use_cases'],1))
  cases=f'''<section class="use-cases" aria-labelledby="cases-title-{lang}"><div class="section-head"><span class="eyebrow">{esc(advanced['use_cases_label'])}</span><h2 class="h2" id="cases-title-{lang}">{esc(advanced['use_cases_title'])}</h2><p class="lead">{esc(advanced['use_cases_body'])}</p></div><ol>{use_cases}</ol></section>'''
  start=f'''<section class="workshop-start" id="descarga"><div class="section-head"><span class="eyebrow">00 · {esc(advanced['start_label'])}</span><h2 class="h2">{esc(advanced['start_title'])}</h2><p class="lead">{esc(advanced['start_body'])}</p></div><div class="access-grid">{access_cards}</div></section>'''
  route_map=f'''<section class="workbook-routes" id="transferencia"><div class="section-head"><span class="eyebrow">05 · {esc(advanced['route_map_label'])}</span><h2 class="h2">{esc(advanced['routes_title'])}</h2><p class="route-duration-note">{esc(advanced['route_note'])}</p></div><div class="route-choice-grid three">{routes}</div></section>'''
  concepts=f'''<section class="concept-section"><div class="concept-grid"><article><span>01</span><h2>{esc(advanced['assistant_title'])}</h2><p>{esc(advanced['assistant_body'])}</p></article><article><span>02</span><h2>{esc(advanced['skill_title'])}</h2><p>{esc(advanced['skill_body'])}</p></article></div></section>'''
  expert=f'''<section class="expert-section"><div class="section-head"><span class="eyebrow">{esc(advanced['expert_label'])}</span><h2 class="h2">{esc(advanced['expert_title'])}</h2></div><ol class="expert-steps">{expert_steps}</ol><div class="expert-tools"><article><h3>{esc(advanced['setup_title'])}</h3><p>{esc(advanced['setup_body'])}</p><div class="actions"><a class="btn secondary" href="{ANTIGRAVITY}" target="_blank" rel="noopener noreferrer">Antigravity ↗</a><a class="text-link" href="{ANTIGRAVITY_GUIDE}" target="_blank" rel="noopener noreferrer">Google Codelab ↗</a></div></article><article class="warning-card"><h3>NotebookLM MCP</h3><p>{esc(advanced['mcp_warning'])}</p><div class="actions"><a class="btn secondary" href="{NOTEBOOK_MCP}" target="_blank" rel="noopener noreferrer">GitHub · MCP ↗</a><a class="text-link" href="{REFERENCE_WORKBOOK}" target="_blank" rel="noopener noreferrer">Workbook original ↗</a></div></article></div></section>'''
  prep=f'''<section class="workbook-prep" id="preparacion"><div class="section-head"><span class="eyebrow">{esc(advanced['prep_label'])}</span><h2 class="h2">{esc(intro['prepare'])}</h2></div><div class="prep-grid">{prep_columns}</div><p class="fac-note"><strong>{setup}</strong><br>{w['note']}</p></section>'''
  return head(lang,w['title'],'workbook')+f'''<main id="main" class="workbook-v2"><section class="doc-hero workbook-hero" id="workbook-inicio"><div class="shell">{breadcrumb(lang,'workbook',T[lang]['workbook'])}</div><div class="shell workbook-hero-grid"><div class="workbook-hero-copy"><span class="eyebrow">MetodologIA · {esc(intro['eyebrow'])}</span><h1 class="h1">{w['title']}</h1><p class="lead">{esc(intro['promise'])}</p></div><aside class="workbook-outcome"><span>{esc(intro['outcome'])}</span><strong>{esc(intro['outcome_body'])}</strong></aside><nav class="workbook-hero-actions" aria-label="Workbook"><a class="btn" href="#brain-title-{lang}">{esc(intro['start'])} →</a><a class="text-link" href="../deck/index.html#page-1">{back} →</a><button class="print-link" type="button" onclick="window.print()">PDF / Print</button></nav></div></section><div class="shell workbook-flow">{guide}{brain}{start}{prep}{cases}<section class="workbook-sheets"><div class="section-head"><span class="eyebrow">01–03 · Workbook</span><h2 class="h2">{esc(w['lead'])}</h2></div>{level_convention_markup(lang)}<div class="sheet-tabs" role="tablist" aria-label="Workbook"><button class="tab" role="tab" aria-selected="true" aria-controls="sheet-session" data-sheet="session">1 · {w['tabs'][0]} · 5</button><button class="tab" role="tab" aria-selected="false" aria-controls="sheet-depth" data-sheet="depth">2 · {w['tabs'][1]} · 10</button><button class="tab" role="tab" aria-selected="false" aria-controls="sheet-consolidation" data-sheet="consolidation">3 · {w['tabs'][2]}</button></div><section class="sheet" id="sheet-session" role="tabpanel"><div class="section-head"><span class="eyebrow">01 · {w['tabs'][0]}</span><h2 class="h2">{w['sheet1']}</h2><p class="lead">{w['sheet1p']}</p></div><div class="step-list">{prompt_cards(lang,1,5)}</div>{surfaces}<h3 class="h3">{roles_title}</h3>{roles_table}</section><section class="sheet" id="sheet-depth" role="tabpanel" hidden><div class="section-head"><span class="eyebrow">02 · {w['tabs'][1]}</span><h2 class="h2">{w['sheet2']}</h2><p class="lead">{w['sheet2p']}</p><p class="fac-note"><strong>{rubric}</strong></p></div>{rubric_table}<div class="step-list">{prompt_cards(lang,6,10)}</div><p class="fac-note"><strong>{gate}</strong></p></section><section class="sheet" id="sheet-consolidation" role="tabpanel" hidden><div class="section-head"><span class="eyebrow">03 · {w['tabs'][2]}</span><h2 class="h2">{w['sheet3']}</h2><p class="lead">{w['sheet3p']}</p></div><article class="card evidence"><h3 class="h3">{w['challenge']}</h3><p>{w['challengep']}</p><p><strong>{transfer}</strong></p><div class="checklist">{checks}</div></article><div class="rubric" style="margin-top:1rem">{states}</div></section></section>{route_map}{concepts}{expert}</div></main>'''+end(lang,'workbook')

def playbook_icon(name):
  icons={
    'compass':'<circle cx="12" cy="12" r="9"></circle><path d="m15 9-2 4-4 2 2-4 4-2Z"></path>',
    'spark':'<path d="m12 3 1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6L12 3Z"></path>',
    'steps':'<path d="M4 19h5v-5h5V9h6"></path>',
    'route':'<circle cx="6" cy="18" r="2"></circle><circle cx="18" cy="6" r="2"></circle><path d="M8 18h2a4 4 0 0 0 4-4v-4a4 4 0 0 1 4-4"></path>',
    'eye':'<path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"></path><circle cx="12" cy="12" r="2.5"></circle>',
    'layers':'<path d="m12 3 9 5-9 5-9-5 9-5Z"></path><path d="m3 12 9 5 9-5M3 16l9 5 9-5"></path>',
    'practice':'<path d="M4 19h16M7 16l3-8 3 5 2-3 2 6"></path>',
    'anchor':'<circle cx="12" cy="5" r="2"></circle><path d="M12 7v13M5 13a7 7 0 0 0 14 0M8 10H4m12 0h4"></path>',
    'search':'<circle cx="10" cy="10" r="6"></circle><path d="m15 15 5 5"></path>',
    'shield':'<path d="M12 3 4 6v5c0 5 3.4 8.3 8 10 4.6-1.7 8-5 8-10V6l-8-3Z"></path><path d="m9 12 2 2 4-4"></path>',
    'refresh':'<path d="M20 7v5h-5M4 17v-5h5"></path><path d="M6.1 8A7 7 0 0 1 18 6l2 2M17.9 16A7 7 0 0 1 6 18l-2-2"></path>',
    'tools':'<path d="m14 7 3-3 3 3-3 3M4 20l8-8M7 4l3 3-3 3-3-3 3-3Z"></path>',
    'notebook':'<path d="M5 4h12a2 2 0 0 1 2 2v14H7a2 2 0 0 1-2-2V4Z"></path><path d="M8 4v16M11 8h5M11 12h5"></path>',
    'terminal':'<path d="m5 7 4 5-4 5M11 17h8"></path>',
    'workflow':'<rect x="3" y="4" width="6" height="5" rx="1"></rect><rect x="15" y="15" width="6" height="5" rx="1"></rect><path d="M9 6.5h4a4 4 0 0 1 4 4V15"></path>',
    'calendar':'<rect x="3" y="5" width="18" height="16" rx="2"></rect><path d="M8 3v4m8-4v4M3 10h18"></path>',
    'check':'<path d="m4 12 5 5L20 6"></path>',
    'book':'<path d="M4 5a3 3 0 0 1 3-3h5v18H7a3 3 0 0 0-3 2V5Zm16 0a3 3 0 0 0-3-3h-5v18h5a3 3 0 0 1 3 2V5Z"></path>',
    'help':'<circle cx="12" cy="12" r="9"></circle><path d="M9.5 9a2.5 2.5 0 1 1 3.4 2.3c-.9.4-.9 1-.9 1.7M12 17h.01"></path>'
  }
  return f'<svg class="playbook-icon" aria-hidden="true" viewBox="0 0 24 24">{icons[name]}</svg>'

def playbook(lang):
  p=PLAYBOOK['locales'][lang]; skill=PLAYBOOK['skill']; base=asset_base(lang,'playbook')
  complete_sections=[
    {'id':'hero','title':p['title']},
    {'id':'founders','title':p['founder_title']},
    *p['sections'],
    {'id':'close','title':p['close_title']},
  ]
  if len(complete_sections)!=22:
    raise RuntimeError(f'PLAYBOOK_COMPLETE_INDEX_INVALID:{lang}:{len(complete_sections)}')
  toc=''.join(f'<a href="#{esc(section["id"])}"><span>{index:02d}</span>{esc(section["title"])}</a>' for index,section in enumerate(complete_sections,1))
  founder_cards=''.join(f'''<li><img src="{base}{esc(x['photo'])}" alt="{esc(x['name'])}" width="560" height="560" decoding="async"><span class="founder-card-copy"><strong>{esc(x['name'])}</strong><span>{esc(x['role'])}</span></span></li>''' for x in PLAYBOOK['founders'])
  assistant_cards=''.join(f'''<a class="playbook-assistant" href="{esc(item['url'])}" target="_blank" rel="noopener noreferrer" data-custom-gpt="{esc(item['id'])}"><span class="eyebrow">ChatGPT · Custom GPT</span><strong>{esc(item['labels'][lang]['title'])}</strong><p>{esc(item['labels'][lang]['description'])}</p><em>{esc(item['labels'][lang]['cta'])}{ui_icon('external')}</em></a>''' for item in PLAYBOOK['assistants'])
  letters=''.join(f'<p>{esc(x)}</p>' for x in p['founder_paragraphs'])
  prompt_cards=''.join(f'''<a class="playbook-prompt" href="../prompts/index.html#prompt-{item['id'].lower()}"><span>{esc(item['id'])}</span><strong>{esc(item['labels'][lang])}</strong><em>{esc(p['prompt_cta'])}{ui_icon('arrow')}</em></a>''' for item in PLAYBOOK['prompts'])
  sections=[]
  for index,section in enumerate(p['sections'],1):
    items=''.join(f'<li>{esc(item)}</li>' for item in section['items'])
    extra=prompt_cards if section['id']=='prompts' else ''
    material=f'<div class="playbook-assistant-grid">{assistant_cards}</div>' if section['id']=='assistants' else (f'<ul>{items}</ul>' if items else '')
    sections.append(f'''<section class="playbook-section" id="{esc(section['id'])}" data-playbook-section><div class="playbook-section-index"><span>{index:02d}</span>{playbook_icon(section['icon'])}</div><div class="playbook-section-body"><span class="eyebrow">{esc(p['section_label'])} {index:02d}</span><h2>{esc(section['title'])}</h2><p class="lead">{esc(section['lead'])}</p>{material}{f'<div class="playbook-prompt-grid">{extra}</div>' if extra else ''}</div></section>''')
  journey={'es':('Mapa de lectura','19 capítulos · 4 fases','Fuentes → criterio → práctica → transferencia','Aprender<br>Aprehender<br>(R)Evolucionar','Carta abierta'),'en':('Reading map','19 chapters · 4 phases','Sources → judgment → practice → transfer','Learn<br>Embody<br>(R)Evolve','Open letter'),'pt':('Mapa de leitura','19 capítulos · 4 fases','Fontes → critério → prática → transferência','Aprender<br>Apreender<br>(R)Evoluir','Carta aberta')}[lang]
  hero_title=esc(p['title']).replace('. (R)', '.<br>(R)')
  full_index=INTRAPAGE_NAV['locales'][lang]['full_index']
  return head(lang,p['meta_title'],'playbook')+f'''<main id="main" class="playbook-v1"><section class="playbook-hero" id="hero"><div class="shell">{breadcrumb(lang,'playbook',T[lang]['playbook'])}</div><div class="shell playbook-hero-grid"><div class="playbook-hero-copy"><span class="eyebrow">{esc(p['eyebrow'])}</span><h1>{hero_title}</h1><p class="lead">{esc(p['lead'])}</p><div class="actions"><a class="btn" href="#intro">{esc(p['primary_cta'])}{ui_icon('arrow')}</a><a class="btn secondary" href="{skill['url']}" target="_blank" rel="noopener noreferrer">{esc(p['secondary_cta'])}{ui_icon('external')}</a></div><dl class="playbook-hero-facts"><div><dt>{journey[0]}</dt><dd>{journey[1]}</dd></div><div><dt>{method_mark(lang,'playbook','compact','playbook-fact-mark')}</dt><dd>{journey[2]}</dd></div></dl></div><figure class="playbook-mark">{method_mark(lang,'playbook','primary','playbook-primary-mark',loading='eager')}<figcaption>{journey[3]}</figcaption></figure></div></section><div class="shell playbook-layout"><details class="playbook-toc"><summary><strong>{esc(full_index)}</strong><span>22</span></summary><nav aria-label="{esc(full_index)}">{toc}</nav></details><div class="playbook-content"><section class="founders-letter" id="founders" data-letter-label="{esc(journey[4])}"><div class="founders-letter-copy"><div class="founders-letter-heading"><span class="eyebrow">{esc(p['founder_label'])}</span><h2>{esc(p['founder_title'])}</h2></div><div class="founders-letter-body">{letters}</div></div><ul>{founder_cards}</ul></section>{''.join(sections)}<section class="playbook-close" id="close">{method_mark(lang,'playbook','primary','playbook-close-mark',decorative=True)}{method_mark(lang,'playbook','compact','playbook-close-lockup')}<span class="eyebrow">MetodologIA · {esc(METHOD_IDENTITY['locales'][lang]['descriptor'])}</span><h2>{esc(p['close_title'])}</h2><p>{esc(p['close_lead'])}</p><div class="actions"><a class="btn" href="../workbook/index.html">{esc(p['close_primary'])}{ui_icon('arrow')}</a><a class="btn secondary" href="../deck/index.html">{esc(p['close_secondary'])}{ui_icon('arrow')}</a></div><small>{esc(skill['version'])} · {esc(skill['license'])}</small></section></div></div></main>'''+end(lang,'playbook')

def notebook_launch_badge(lang,intent_id):
  copy=NOTEBOOK_EXECUTION['locales'][lang]
  route=NOTEBOOK_EXECUTION['intent_routes'][intent_id]
  if route['mode']=='deep_research':
    label=f"{copy['search_tab']} · {copy['deep_research']}"
  elif route['mode']=='research_brief':
    label=copy['research_brief']
  else:
    label=f"{copy['chat_tab']} · {copy['selected_sources']}"
  return f'''<span class="prompt-launch-badge" data-launch="{esc(route['launch'])}"><small>{esc(copy['run_in'])}</small><strong>{esc(label)}</strong></span>'''

def prompt_discovery_markup(lang,convention):
  copy=NOTEBOOK_EXECUTION['locales'][lang]
  modes=f"{FORMAT_COPY[lang]['template']} / {FORMAT_COPY[lang]['demo']}"
  label=f"4 · {convention['tablist']} · {modes}"
  markup=(f'''<span class="prompt-card-discovery"><strong>4 · {esc(convention['tablist'])}</strong>'''
          f'''<span>{esc(modes)}</span>'''
          f'''<em>{esc(copy['open_prompt'])} →</em></span>''')
  return markup,label

def notebook_execution_guide(lang,convention,include_method_mark=True):
  copy=NOTEBOOK_EXECUTION['locales'][lang]
  sources=NOTEBOOK_EXECUTION['official_sources']
  chat_id=f'notebook-chat-{lang}'; search_id=f'notebook-search-{lang}'
  mark=method_mark(lang,'prompts','compact','prompt-method-mark') if include_method_mark else ''
  return f'''<aside class="notebook-execution-guide" aria-labelledby="notebook-execution-title" data-notebook-execution-guide><header><span class="eyebrow">{esc(copy['eyebrow'])}</span><h2 id="notebook-execution-title">{esc(copy['title'])}</h2><p>{esc(copy['lead'])}</p></header><div class="notebook-execution-tabs" role="tablist" aria-label="{esc(copy['eyebrow'])}"><button type="button" role="tab" aria-selected="true" aria-controls="{chat_id}" id="{chat_id}-tab" tabindex="0" data-notebook-tab="chat">{esc(copy['chat_tab'])}</button><button type="button" role="tab" aria-selected="false" aria-controls="{search_id}" id="{search_id}-tab" tabindex="-1" data-notebook-tab="source_search">{esc(copy['search_tab'])}</button></div><div class="notebook-execution-panels"><article id="{chat_id}" role="tabpanel" aria-labelledby="{chat_id}-tab" data-notebook-panel="chat"><strong>{esc(copy['chat_title'])}</strong><p>{esc(copy['chat_body'])}</p><a href="{esc(sources['chat']['url'])}" target="_blank" rel="noopener noreferrer">{esc(copy['official'])}{ui_icon('external')}</a></article><article id="{search_id}" role="tabpanel" aria-labelledby="{search_id}-tab" data-notebook-panel="source_search" hidden><strong>{esc(copy['search_title'])}</strong><p>{esc(copy['search_body'])}</p><a href="{esc(sources['source_search']['url'])}" target="_blank" rel="noopener noreferrer">{esc(copy['official'])}{ui_icon('external')}</a></article></div><footer><p>{esc(copy['bridge'])}</p><a class="btn" href="{esc(NOTEBOOK_EXECUTION['product']['url'])}" target="_blank" rel="noopener noreferrer">{esc(copy['open'])}{ui_icon('external')}</a><span class="notebook-guide-meta">{mark}<span>4 · {esc(convention['tablist'])}</span></span></footer></aside>'''

def prompt_library_page(lang):
  p=PROMPT_LIBRARY['locales'][lang]
  convention=ADVANCED['locales'][lang]['level_convention']
  hero_cta={'es':'Ver 10 prompts','en':'View 10 prompts','pt':'Ver 10 prompts'}[lang]
  hero_map=notebook_execution_guide(lang,convention)
  # The spec keeps only page chrome; the localized phase eyebrow is its last
  # per-item field (contracts carry a single untranslated `phase`).
  phases={item['id']:item['phase'] for item in p['items']}
  direct=[]; meta=[]
  for intent_id in PROMPT_LIBRARY_IDS:
    cell=contract_cell(intent_id,lang)
    group=f'library-{lang}-{intent_id.lower()}'
    formats={mode:structured_variants(lang,cell['title'],cell['prompt'],cell['level_spec'],cell,mode) for mode in ('template','demo')}
    controls=prompt_formats_markup(lang,group,formats,ADVANCED['locales'][lang]['level_convention'],cell)+prompt_why_markup(lang,group,cell['why_it_works'])
    route=NOTEBOOK_EXECUTION['intent_routes'][intent_id]
    discovery,discovery_label=prompt_discovery_markup(lang,convention)
    card=f'''<article class="library-prompt-card" id="prompt-{intent_id.lower()}" data-library-prompt data-prompt-kind="{'meta' if intent_id.startswith('M') else 'direct'}" data-notebook-surface="{esc(route['launch'])}"><details class="library-prompt-disclosure" data-prompt-card-disclosure><summary data-open-label="{esc(NOTEBOOK_EXECUTION['locales'][lang]['open_prompt'])}" data-close-label="{esc(NOTEBOOK_EXECUTION['locales'][lang]['close_prompt'])}" data-discovery-label="{esc(discovery_label)}"><span class="library-prompt-number" aria-hidden="true">{esc(intent_id)}</span><span class="library-prompt-summary-copy"><span class="eyebrow">{esc(phases[intent_id])}</span><strong class="library-prompt-title">{esc(cell['title'])}</strong><small>{esc(cell['purpose'])}</small>{discovery}</span>{notebook_launch_badge(lang,intent_id)}<span class="library-prompt-chevron" aria-hidden="true">⌄</span></summary><div class="library-prompt-card-body"><div class="library-prompt-side"><details class="prompt-card-context"><summary>{esc(NOTEBOOK_EXECUTION['locales'][lang]['details'])}</summary><dl class="library-prompt-brief"><div><dt>{esc(p['use'])}</dt><dd>{esc(cell['when'])}</dd></div><div><dt>{esc(p['example'])}</dt><dd>{esc(cell['example'])}</dd></div><div><dt>{esc(p['evidence'])}</dt><dd>{esc(cell['evidence'])}</dd></div>{prompt_limit_markup(lang,cell['why_it_works'],as_definition=True)}</dl></details>{prompt_flow_markup(lang,intent_id)}</div>{controls}</div></details></article>'''
    (meta if intent_id.startswith('M') else direct).append(card)
  skill=RESOURCES['open_skill']
  filters=NOTEBOOK_EXECUTION['locales'][lang]
  filter_ui=f'''<div class="prompt-surface-filter" role="group" aria-label="{esc(filters['filter_label'])}"><button type="button" aria-pressed="true" data-prompt-surface-filter="all">{esc(filters['all_prompts'])}</button><button type="button" aria-pressed="false" data-prompt-surface-filter="chat">{esc(filters['chat_tab'])}</button><button type="button" aria-pressed="false" data-prompt-surface-filter="source_search">{esc(filters['search_tab'])}</button></div>'''
  return head(lang,p['meta_title'],'prompts')+f'''<main id="main" class="prompt-library-page"><section class="prompt-library-hero"><div class="shell">{breadcrumb(lang,'prompts',T[lang]['prompts'])}<div class="prompt-library-hero-grid"><div class="prompt-library-hero-copy"><span class="eyebrow">{esc(p['eyebrow'])}</span><h1>{esc(p['title'])}</h1><p class="lead">{esc(p['lead'])}</p><div class="actions"><a class="btn" href="#directos">{esc(hero_cta)}{ui_icon('arrow')}</a><a class="btn secondary" href="../playbook/index.html">{esc(p['back'])}{ui_icon('arrow')}</a></div></div>{hero_map}</div></div></section><section class="prompt-library-section shell" id="directos"><div class="prompt-library-section-heading"><div class="section-head"><span class="eyebrow">{esc(p['direct_label'])}</span><h2 class="h2">{esc(p['direct_title'])}</h2></div>{filter_ui}</div><div class="library-prompt-list">{''.join(direct)}</div></section><section class="prompt-library-section prompt-library-meta" id="metaprompts"><div class="shell"><div class="section-head"><span class="eyebrow">{esc(p['meta_label'])}</span><h2 class="h2">{esc(p['meta_title_section'])}</h2></div><div class="library-prompt-list">{''.join(meta)}</div><aside class="prompt-library-source"><p>{esc(p['skill_note'])}</p><a class="btn secondary" href="{skill['url']}" target="_blank" rel="noopener noreferrer">{esc(skill['locales'][lang]['cta'])}{ui_icon('external')}</a><a class="btn" href="../workbook/index.html">{esc(p['workbook'])}{ui_icon('arrow')}</a></aside></div></section></main>'''+end(lang,'prompts')

S={
'es':[('Bienvenida','IA: qué está pasando y cómo sacarle provecho','Hoy no vienes a aprender botones. Vienes a construir criterio y una práctica basada en fuentes.'),('Resultado','Al final podrás demostrar esto','Explicar qué puede aportar la IA, construir una base en NotebookLM y decidir cuándo confiar, verificar o detenerte.'),('Acuerdo','La IA propone. Tú respondes.','Ninguna respuesta sustituye la revisión de fuentes, el contexto ni la decisión humana.'),('Panorama','¿Qué cambió?','La IA generativa volvió conversacionales tareas de búsqueda, síntesis, creación y apoyo a decisiones.'),('Mapa','Modelo, producto y flujo no son lo mismo','Distingue la capacidad base, la interfaz que usas y el proceso donde produces un resultado.'),('Criterio','Fluidez no es evidencia','Una respuesta convincente puede estar incompleta. La pregunta útil es: ¿qué fuente sostiene esta afirmación?'),('Aprender','Aprender a aprender con IA','Define un propósito, reúne fuentes, detecta vacíos, practica recuperación y explica con tus palabras.'),('NotebookLM','Una conversación anclada en tus fuentes','NotebookLM ayuda a consultar fuentes seleccionadas y revisar citas. Tú decides qué importar y cómo usarlo.'),('Práctica 1','Construye la primera base','Abre la hoja En clase, paso 1. Declara tema, decisión, contexto y audiencia.'),('Práctica 2','Audita antes de acumular','Paso 2. Busca cobertura, tensiones, ambigüedad, calidad, vigencia y sesgo.'),('Práctica 3','Investiga el vacío que importa','Paso 3. Convierte el hallazgo prioritario en investigación a medida.'),('Práctica 4','Detente con criterio','Paso 4. Compara la mejora y decide: base suficiente o repetir investigación.'),('Práctica 5','Activa profesor, asesor o coach','Paso 5. Elige un rol y exige citas, límites y siguiente paso.'),('Puesta en común','¿Qué cambió entre la primera y la segunda base?','Comparte una fuente decisiva, una tensión y un vacío que aceptaste.'),('Transferencia','Llévalo a una decisión real','Elige una reunión, propuesta, aprendizaje o problema donde una base verificable reduzca improvisación.'),('Profundiza','La práctica continúa','La hoja 2 convierte la base en contenido, casos, evaluación, simulación y configuración.'),('Consolida','Demuestra que puedes hacerlo sin guía','La hoja 3 pide evidencia, teach-back y transferencia a otro contexto.'),('Cierre','Tu siguiente paso en 24 horas','Crea o mejora un Notebook, registra el veredicto de suficiencia y explica el proceso en tres minutos.')],
'en':[('Welcome','AI: what is happening and how to benefit','You are not here to memorize buttons. You are here to build judgment and source-grounded practice.'),('Outcome','By the end you can demonstrate this','Explain what AI can contribute, build a NotebookLM source base and decide when to trust, verify or stop.'),('Agreement','AI proposes. You remain accountable.','No answer replaces source review, context or human decision.'),('Landscape','What changed?','Generative AI made search, synthesis, creation and decision support conversational.'),('Map','Model, product and workflow are different','Separate the base capability, the interface you use and the process that produces an outcome.'),('Judgment','Fluency is not evidence','A persuasive answer can be incomplete. Ask: which source supports this claim?'),('Learning','Learn how to learn with AI','Set a purpose, gather sources, find gaps, retrieve from memory and explain in your own words.'),('NotebookLM','A conversation grounded in your sources','NotebookLM helps query selected sources and inspect citations. You decide what to import and how to use it.'),('Practice 1','Build the first source base','Open In class, step 1. State topic, decision, context and audience.'),('Practice 2','Audit before accumulating','Step 2. Inspect coverage, tensions, ambiguity, quality, recency and bias.'),('Practice 3','Research the gap that matters','Step 3. Turn the priority finding into targeted research.'),('Practice 4','Stop with judgment','Step 4. Compare improvement and choose: sufficient base or repeat.'),('Practice 5','Activate teacher, advisor or coach','Step 5. Choose a role and require citations, boundaries and a next step.'),('Debrief','What changed between the first and second base?','Share one decisive source, one tension and one accepted gap.'),('Transfer','Take it to a real decision','Choose a meeting, proposal, learning goal or problem where a verifiable source base reduces improvisation.'),('Go deeper','Practice continues','Sheet 2 turns the base into content, use cases, assessment, simulation and configuration.'),('Consolidate','Prove you can do it without guidance','Sheet 3 asks for evidence, teach-back and transfer to another context.'),('Close','Your next step within 24 hours','Create or improve a Notebook, record the sufficiency verdict and explain the process in three minutes.')],
'pt':[('Boas-vindas','IA: o que está acontecendo e como aproveitar','Você não veio memorizar botões. Veio construir critério e prática baseada em fontes.'),('Resultado','Ao final você poderá demonstrar isto','Explicar a contribuição da IA, construir uma base no NotebookLM e decidir quando confiar, verificar ou parar.'),('Acordo','A IA propõe. Você responde.','Nenhuma resposta substitui a revisão das fontes, o contexto ou a decisão humana.'),('Panorama','O que mudou?','A IA generativa tornou conversacionais tarefas de busca, síntese, criação e apoio à decisão.'),('Mapa','Modelo, produto e fluxo são diferentes','Separe a capacidade base, a interface usada e o processo que produz um resultado.'),('Critério','Fluência não é evidência','Uma resposta convincente pode estar incompleta. Pergunte: qual fonte sustenta esta afirmação?'),('Aprender','Aprender a aprender com IA','Defina propósito, reúna fontes, detecte lacunas, recupere da memória e explique com suas palavras.'),('NotebookLM','Uma conversa ancorada em suas fontes','O NotebookLM ajuda a consultar fontes selecionadas e revisar citações. Você decide o que importar e como usar.'),('Prática 1','Construa a primeira base','Abra Em aula, passo 1. Declare tema, decisão, contexto e público.'),('Prática 2','Audite antes de acumular','Passo 2. Busque cobertura, tensões, ambiguidade, qualidade, atualidade e viés.'),('Prática 3','Pesquise a lacuna importante','Passo 3. Transforme o achado prioritário em pesquisa sob medida.'),('Prática 4','Pare com critério','Passo 4. Compare a melhoria e decida: base suficiente ou repetir.'),('Prática 5','Ative professor, assessor ou coach','Passo 5. Escolha um papel e exija citações, limites e próximo passo.'),('Discussão','O que mudou entre a primeira e a segunda base?','Compartilhe uma fonte decisiva, uma tensão e uma lacuna aceita.'),('Transferência','Leve para uma decisão real','Escolha reunião, proposta, aprendizagem ou problema em que uma base verificável reduza improvisação.'),('Aprofunde','A prática continua','A folha 2 transforma a base em conteúdo, casos, avaliação, simulação e configuração.'),('Consolide','Demonstre que consegue sem guia','A folha 3 exige evidência, teach-back e transferência para outro contexto.'),('Fechamento','Seu próximo passo em 24 horas','Crie ou melhore um Notebook, registre o veredito de suficiência e explique o processo em três minutos.')]
}

def masterclass(lang):
  deck=RESOURCES['deck']; deck_l=deck['locales'][lang]; base=asset_base(lang,'deck')
  labels={
    'es':{'title':'Guía accesible del recorrido','journey':'Recorrido','previous':'Anterior','next':'Siguiente','note':'Guía para facilitar','workbook':'Abrir workbook','class':'Clase 01','moments':'18 láminas','duration':'Duración de la guía','base':'Ruta base','extended':'Con práctica extendida','open_pdf':'Abrir PDF','download':'Descargar PDF','pdf_label':'PDF oficial de la masterclass','pdf_fallback':'Tu navegador no puede mostrar el PDF integrado. Ábrelo en una pestaña o descárgalo.','guide_lead':'Este recorrido textual localizado acompaña el documento oficial y mejora su acceso. No sustituye el contenido ni el diseño del PDF.','phases':('Comprender','Practicar','Transferir')},
    'en':{'title':'Accessible journey guide','journey':'Outline','previous':'Previous','next':'Next','note':'Facilitation guide','workbook':'Open workbook','class':'Class 01','moments':'18 pages','duration':'Guide duration','base':'Core route','extended':'With extended practice','open_pdf':'Open PDF','download':'Download PDF','pdf_label':'Official masterclass PDF','pdf_fallback':'Your browser cannot display the embedded PDF. Open it in a new tab or download it.','guide_lead':'This localized text journey accompanies the official document and improves access. It does not replace the PDF content or design.','phases':('Understand','Practice','Transfer')},
    'pt':{'title':'Guia acessível do percurso','journey':'Percurso','previous':'Anterior','next':'Próximo','note':'Guia de facilitação','workbook':'Abrir workbook','class':'Aula 01','moments':'18 páginas','duration':'Duração da guia','base':'Rota base','extended':'Com prática estendida','open_pdf':'Abrir PDF','download':'Baixar PDF','pdf_label':'PDF oficial da masterclass','pdf_fallback':'Seu navegador não consegue exibir o PDF incorporado. Abra-o em uma nova aba ou baixe-o.','guide_lead':'Este percurso textual localizado acompanha o documento oficial e melhora o acesso. Não substitui o conteúdo nem o design do PDF.','phases':('Compreender','Praticar','Transferir')}
  }[lang]
  help_url=HELP_BY_LANG[lang]
  progress_label={'es':'Progreso de la masterclass','en':'Masterclass progress','pt':'Progresso da masterclass'}[lang]
  timings=['0–3','3–7','7–10','10–15','15–20','20–25','25–30','30–35','35–41','41–47','47–53','53–59','59–65','65–70','70–80','80–84','84–87','87–90']
  video=RESOURCES['videos'][0]; video_l=video['locales'][lang]
  slides=[]; outline_groups=[[],[],[]]
  for i,(k,title,body) in enumerate(S[lang],1):
    link='';
    if i==8: link+=f'<a class="btn secondary" href="{help_url}" target="_blank" rel="noopener noreferrer">{("Ayuda oficial" if lang=="es" else "Official help" if lang=="en" else "Ajuda oficial")} ↗</a>'
    if 9<=i<=13: link=f'<a class="btn" href="../workbook/index.html#step-{i-8}">{labels["workbook"]} →</a>'
    if i==18: link+=f'<a class="btn secondary" href="{video["url"]}" target="_blank" rel="noopener noreferrer">{esc(video_l["cta"])} ↗</a>'
    note=(f'Di: “{title}”. Haz: conecta esta idea con un ejemplo del grupo. Observa: una respuesta que distinga evidencia de opinión.' if lang=='es' else f'Say: “{title}”. Do: connect it to one group example. Observe: an answer that separates evidence from opinion.' if lang=='en' else f'Diga: “{title}”. Faça: conecte a ideia a um exemplo do grupo. Observe: resposta que separa evidência de opinião.')
    extended=(f'<aside class="extended"><strong>+30 min:</strong> {esc("Ejecuta un prompt 6–10, revisa la rúbrica y comparte una mejora." if lang=="es" else "Run one prompt 6–10, review the rubric and share one improvement." if lang=="en" else "Execute um prompt 6–10, revise a rubrica e compartilhe uma melhoria.")}</aside>' if i==16 else '')
    phase=0 if i<=8 else 1 if i<=13 else 2
    actions=f'<div class="slide-actions">{link}</div>' if link else ''
    slides.append(f'''<section class="slide{' active' if i==1 else ''}" id="slide-{i}" aria-labelledby="slide-title-{i}" data-phase="{phase+1}"><header class="slide-kicker"><span class="eyebrow">{esc(k)} · {timings[i-1]} min</span><span>{i:02d} / 18</span></header><h2 class="h1" id="slide-title-{i}" tabindex="-1">{esc(title)}</h2><p class="lead">{esc(body)}</p>{actions}{extended}<details class="fac-note"><summary>{labels["note"]}</summary><p>{esc(note)}</p></details><div class="slide-foot"><span>MetodologIA · {T[lang]['route']}</span><span>{esc(labels['phases'][phase])}</span></div></section>''')
    outline_groups[phase].append(f'<button type="button" data-slide="{i-1}" aria-current="{"step" if i==1 else "false"}"><span>{i:02d}</span><strong>{esc(title)}</strong></button>')
  outline=''.join(f'<section class="outline-group"><h3>{index+1:02d} · {esc(labels["phases"][index])}</h3>{"".join(items)}</section>' for index,items in enumerate(outline_groups))
  pdf_url=f'{base}{deck["source_asset"]}'
  official=f'''<section class="official-masterclass" id="masterclass-inicio"><div class="shell">{breadcrumb(lang,'deck',T[lang]['masterclass'])}<header class="official-masterclass-head"><div><span class="eyebrow">MetodologIA · {esc(deck_l['language_note'])}</span><h1>{esc(deck_l['display_title'])}</h1><p class="lead">{esc(deck_l['description'])}</p></div><dl class="official-masterclass-facts"><div><dt>PDF</dt><dd>{deck['page_count']} · {esc(labels['moments'])}</dd></div><div><dt>SHA-256</dt><dd><code>{deck['sha256'][:12]}…</code></dd></div></dl></header><div class="official-pdf-card" id="masterclass-pdf" data-official-masterclass data-official-masterclass-sha256="{deck['sha256']}"><div class="official-pdf-toolbar"><div><h2 tabindex="-1">{esc(labels['pdf_label'])}</h2><span>{esc(deck_l['language_note'])}</span></div><div class="actions"><a class="btn secondary" href="{pdf_url}" target="_blank" rel="noopener">{esc(labels['open_pdf'])}{ui_icon('external')}</a><a class="btn" href="{pdf_url}" download>{esc(labels['download'])} ↓</a></div></div><object class="official-pdf-object" data="{pdf_url}#page=1&amp;view=FitH" type="application/pdf" aria-label="{esc(labels['pdf_label'])}" title="{esc(labels['pdf_label'])}"><div class="official-pdf-fallback"><p>{esc(labels['pdf_fallback'])}</p><a class="btn" href="{pdf_url}" target="_blank" rel="noopener">{esc(labels['open_pdf'])}{ui_icon('external')}</a></div></object></div></div></section>'''
  guide=f'''<section class="masterclass-player" id="masterclass-guia"><div class="shell"><header class="masterclass-player-head"><div><span class="eyebrow">{esc(labels['class'])} · {esc(labels['title'])}</span><h2>{esc(labels['title'])}</h2><p class="lead">{esc(labels['guide_lead'])}</p></div><dl class="masterclass-facts"><div><dt>{esc(labels['moments'])}</dt><dd>90 min</dd></div><div><dt>{esc(labels['extended'])}</dt><dd>120 min</dd></div></dl></header><div class="deck"><details class="outline" open><summary><span>{esc(labels['journey'])}</span><strong data-outline-count>01 / 18</strong></summary><div class="outline-list">{outline}</div></details><div class="stage"><div class="slide-wrap">{''.join(slides)}</div><nav class="deck-controls" aria-label="{progress_label}"><button class="deck-nav deck-prev" type="button" data-prev aria-label="{esc(labels['previous'])}">{ui_icon('back')}<span>{esc(labels['previous'])}</span></button><div class="deck-progress"><div class="progress" role="progressbar" aria-label="{progress_label}" aria-valuemin="1" aria-valuemax="18" aria-valuenow="1"><span></span></div><div><strong data-count aria-live="polite">1 / 18</strong><span data-phase-current>{esc(labels['phases'][0])}</span></div></div><div class="deck-tools"><div class="deck-mode-group" role="group" aria-label="{esc(labels['duration'])}"><button class="deck-mode" type="button" data-mode="90" aria-pressed="true" aria-label="{esc(labels['base'])} · 90 min"><strong>90</strong><span>min</span></button><button class="deck-mode" type="button" data-mode="120" aria-pressed="false" aria-label="{esc(labels['extended'])} · 120 min"><strong>120</strong><span>min</span></button></div><span class="sr-only" data-mode-label>90 min</span><button class="deck-nav deck-next" type="button" data-next aria-label="{esc(labels['next'])}"><span>{esc(labels['next'])}</span>{ui_icon('arrow')}</button></div></nav></div></div></div></section>'''
  return head(lang,deck_l['title'],'deck')+f'''<main id="main" class="masterclass-page">{official}{guide}</main>'''+end(lang,'deck')

def editorial_page(lang,page):
  content=EDITORIAL['copy'][lang][page]
  audience=AUDIENCE_SPEC['locales'][lang][CURRENT_AUDIENCE][page]
  anchors=EDITORIAL['pages'][page]['anchors']
  resource_targets={
    'masterclass-resource':('deck',{'es':'Abrir masterclass','en':'Open masterclass','pt':'Abrir masterclass'}[lang]),
    'workbook-resource':('workbook',{'es':'Abrir workbook','en':'Open workbook','pt':'Abrir workbook'}[lang]),
    'playbook-resource':('playbook',{'es':'Abrir playbook','en':'Open playbook','pt':'Abrir playbook'}[lang]),
    'prompts-resource':('prompts',{'es':'Abrir biblioteca','en':'Open library','pt':'Abrir biblioteca'}[lang]),
  }
  sections=[]
  for section in content['sections']:
    points=''.join(f'<li>{esc(item)}</li>' for item in section['points'])
    extra=''
    if section['id'] in resource_targets:
      target,label=resource_targets[section['id']]
      extra=f'<a class="editorial-link" href="{esc(rel_page(lang,page,lang,target))}">{esc(label)}{ui_icon("arrow")}</a>'
    elif page=='intakes' and section['id']=='interest':
      label={'es':'Registrar interés','en':'Register interest','pt':'Registrar interesse'}[lang]
      extra=f'<a class="editorial-link" href="{FORM}" target="_blank" rel="noopener noreferrer">{esc(label)}{ui_icon("external")}</a>'
    elif page=='level0' and section['id']=='metodologia':
      label={'es':'Conocer MetodologIA','en':'Explore MetodologIA','pt':'Conhecer a MetodologIA'}[lang]
      extra=f'<a class="editorial-link" href="https://metodologia.info/">{esc(label)}{ui_icon("external")}</a>'
    sections.append(f'''<section class="editorial-section" id="{esc(section['id'])}"><div class="editorial-section-number" aria-hidden="true">{len(sections)+1:02d}</div><div><h2>{esc(section['title'])}</h2><p>{esc(section['body'])}</p>{f'<ul>{points}</ul>' if points else ''}{extra}</div></section>''')
  catalog=''
  if page=='resources_index':
    catalog_title={'es':'Los 16 recursos de Nivel 0','en':'The 16 Level 0 resources','pt':'Os 16 recursos do Nível 0'}[lang]
    catalog_lead={'es':'Cuatro módulos. En cada uno: Masterclass, workbook, playbook y prompts para pasar de comprender a aplicar.','en':'Four modules. Each includes a Masterclass, workbook, playbook and prompts to move from understanding to application.','pt':'Quatro módulos. Cada um inclui Masterclass, workbook, playbook e prompts para passar da compreensão à aplicação.'}[lang]
    catalog=f'''<section class="resource-catalog editorial-resource-catalog" data-curriculum-catalog><div class="section-head"><span class="eyebrow">01–04 · Nivel 0</span><h2 class="h2">{esc(catalog_title)}</h2><p class="lead">{esc(catalog_lead)}</p></div>{resource_catalog(lang,LANDING['locales'][lang]['classes'],'resources_index')}</section>'''
  return head(lang,content['meta_title'],page)+f'''<main id="main" class="editorial-page" data-editorial-page="{page}" data-editorial-audience="{CURRENT_AUDIENCE}"><section class="editorial-hero" id="{esc(anchors[0])}"><div class="shell editorial-hero-grid"><div><span class="eyebrow">{esc(content['eyebrow'])}</span><h1>{esc(content['title'])}</h1><p class="lead">{esc(content['lead'])}</p></div><div class="card evidence" data-audience-field="benefits"><p>{esc(audience['benefits'])}</p></div></div></section><div class="shell editorial-sections">{''.join(sections)}{catalog}</div></main>'''+end(lang,page)

def write(path,text): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text,encoding='utf-8')

def normalized_string(value):
  return ' '.join(html.unescape(value).split())

class EditorialStringParser(HTMLParser):
  excluded={'script','style','template','svg'}
  void={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
  accessible=('aria-label','alt','title','placeholder')
  def __init__(self):
    super().__init__(convert_charrefs=True)
    self.stack=[];self.in_body=False;self.visible=Counter();self.access=Counter()
  def handle_starttag(self,tag,attrs):
    attrs=dict(attrs);parent_hidden=self.stack[-1][1] if self.stack else False
    hidden=parent_hidden or tag in self.excluded or 'hidden' in attrs or attrs.get('aria-hidden')=='true'
    if tag=='body': self.in_body=True
    if self.in_body and not hidden:
      for attribute in self.accessible:
        value=normalized_string(attrs.get(attribute,''))
        if value:self.access[(attribute,value)]+=1
      if tag in ('input','button') and attrs.get('type','').lower() in ('submit','reset','button'):
        value=normalized_string(attrs.get('value',''))
        if value:self.access[('input_value',value)]+=1
    if tag not in self.void:self.stack.append((tag,hidden))
  def handle_startendtag(self,tag,attrs): self.handle_starttag(tag,attrs)
  def handle_endtag(self,tag):
    if tag in self.void:return
    while self.stack:
      opened,_=self.stack.pop()
      if opened==tag:break
    if tag=='body':self.in_body=False
  def handle_data(self,data):
    if self.in_body and not (self.stack and self.stack[-1][1]):
      value=normalized_string(data)
      if value:self.visible[value]+=1

def editorial_string_inventory(html_outputs):
  routes=[]
  for page_path in html_outputs:
    source=page_path.read_text(encoding='utf-8');parser=EditorialStringParser();parser.feed(source)
    locale=re.search(r'<html lang="([^"]+)"',source).group(1)
    audience=re.search(r'<html[^>]+data-audience="([^"]+)"',source).group(1)
    page=re.search(r'<body data-page="([^"]+)"',source).group(1)
    module_match=re.search(r'<body[^>]+data-module-id="([^"]+)"',source)
    module_id=module_match.group(1) if module_match else DEFAULT_MODULE_ID
    routes.append({
      'route':str(page_path.relative_to(DIST)),'locale':locale,'audience':audience,'module_id':module_id,'page':page,
      'visible_text':[{'text':text,'count':count} for text,count in sorted(parser.visible.items())],
      'accessible_text':[{'attribute':attribute,'text':text,'count':count} for (attribute,text),count in sorted(parser.access.items())],
    })
  inventory={'schema_version':'editorial-string-inventory-v1','state':'RENDERED_DRAFT','publication_authorized':False,'source_spec':'src/editorial-parity-spec-v1.json','source_spec_self_sha256':PARITY['self_sha256'],'route_count':len(routes),'routes':routes,'self_hash_model':'sha256(sorted-json-without-self_sha256)'}
  inventory['self_sha256']=canonical_self(inventory,'self_sha256')
  return inventory
def validate_method_identity():
  subprocess.run([sys.executable,str(ROOT/'scripts/build_method_identity.py'),'--check'],check=True,stdout=subprocess.DEVNULL)
  source=METHOD_IDENTITY['source']
  if hashlib.sha256((SRC/source['font']).read_bytes()).hexdigest()!=source['font_sha256'] or f'fontTools {fontTools.__version__}'!=source['toolchain']:
    raise RuntimeError('METHOD_IDENTITY_SOURCE_DRIFT')
  forbidden_tags={'script','foreignObject','iframe','object','embed','image','text'}
  for variant,asset in METHOD_IDENTITY['assets'].items():
    path=SRC/asset['path']; payload=path.read_bytes(); text=payload.decode('utf-8')
    if hashlib.sha256(payload).hexdigest()!=asset['sha256'] or not asset.get('rights') or asset.get('minimum_css_px',0)<40:
      raise RuntimeError(f'METHOD_IDENTITY_ASSET_DRIFT:{variant}')
    try: root=ET.fromstring(text)
    except ET.ParseError as error: raise RuntimeError(f'METHOD_IDENTITY_SVG_INVALID:{variant}') from error
    local=lambda value:value.rsplit('}',1)[-1]
    if local(root.tag)!='svg' or root.attrib.get('viewBox')!=asset['viewBox'] or any(local(node.tag) in forbidden_tags for node in root.iter()):
      raise RuntimeError(f'METHOD_IDENTITY_GEOMETRY_INVALID:{variant}')
    for node in root.iter():
      for key,value in node.attrib.items():
        if local(key)=='href' or re.search(r'(?:https?:|//|data:|javascript:|\\)',value,re.I):
          raise RuntimeError(f'METHOD_IDENTITY_EXTERNAL_REFERENCE:{variant}')
    if not any(local(node.tag)=='path' for node in root.iter()):
      raise RuntimeError(f'METHOD_IDENTITY_OUTLINE_MISSING:{variant}')

def build():
  global CURRENT_AUDIENCE,CURRENT_MODULE
  brand_manifest,brand_receipt,_=validate_release()
  chrome_spec=validate_chrome_spec()
  validate_method_identity()
  declared_assets=[RESOURCES['deck'],RESOURCES['identity_assets']['logo'],RESOURCES['identity_assets']['pristino_mark'],RESOURCES['identity_assets']['javier_photo'],*METHOD_IDENTITY['assets'].values(),*PLAYBOOK['founders']]
  for declared in declared_assets:
    asset_ref=declared['source_asset'] if 'source_asset' in declared else declared['path'] if 'path' in declared else declared['photo']
    source=SRC/asset_ref
    if not source.is_file():
      raise RuntimeError(f'Missing declared public asset: {source.relative_to(SRC)}')
    actual=hashlib.sha256(source.read_bytes()).hexdigest()
    expected=declared.get('sha256',declared.get('photo_sha256'))
    if actual!=expected:
      raise RuntimeError(f'Public asset hash mismatch: {source.relative_to(SRC)}')
  if DIST.exists(): shutil.rmtree(DIST)
  (DIST/'assets').mkdir(parents=True)
  brand_dist=DIST/'assets'/'brand'
  for folder in ('runtime','assets'):
    (brand_dist/folder).mkdir(parents=True)
  for ref in ('runtime/brand-shell.css','assets/metodologia-logo.svg','assets/Poppins-Regular.ttf','assets/Poppins-Bold.ttf','assets/Montserrat-Variable.ttf','assets/Poppins-OFL.txt','assets/Montserrat-OFL.txt'):
    shutil.copyfile(RELEASE/ref,brand_dist/ref)
  css=(SRC/'site.css').read_text(encoding='utf-8')
  write(DIST/'assets/site.css',css); shutil.copyfile(SRC/'forms.css',DIST/'assets/forms.css'); shutil.copyfile(SRC/'site.js',DIST/'assets/site.js')
  inactive_legacy_assets={'metodologia-logo.svg','Poppins-Regular.ttf','Poppins-Bold.ttf','Montserrat-Variable.ttf','Poppins-OFL.txt','Montserrat-OFL.txt'}
  for p in sorted((SRC/'assets').iterdir()):
    if p.name not in inactive_legacy_assets: shutil.copyfile(p,DIST/'assets'/p.name)
  outputs=[]
  for audience in AUDIENCES:
    CURRENT_AUDIENCE=audience
    for lang in LANGS:
      CURRENT_MODULE=DEFAULT_MODULE_ID
      rendered=[
        ('landing',landing(lang),DEFAULT_MODULE_ID,None,False),
        ('workbook',workbook(lang),DEFAULT_MODULE_ID,None,False),
        ('playbook',playbook(lang),DEFAULT_MODULE_ID,None,False),
        ('prompts',prompt_library_page(lang),DEFAULT_MODULE_ID,None,False),
        ('deck',masterclass(lang),DEFAULT_MODULE_ID,None,False),
      ]
      rendered += [(page,editorial_page(lang,page),DEFAULT_MODULE_ID,None,False) for page in EDITORIAL_PAGES]
      for current_module in MODULE_IDS[1:]:
        CURRENT_MODULE=current_module
        for resource_page in RESOURCE_PAGE_KEYS:
          content,nav_items,_=module_resource_page(lang,resource_page,current_module)
          rendered.append((resource_page,content,current_module,nav_items,True))
      CURRENT_MODULE=DEFAULT_MODULE_ID
      for page,content,current_module,nav_items,is_imported in rendered:
        CURRENT_MODULE=current_module
        if page not in EDITORIAL_PAGES:
          content=content.replace('aria-label="Nivel 0"',f'aria-label="{T[lang]["route"]}"').replace('MetodologIA · Nivel 0',f'MetodologIA · {T[lang]["route"]}')
          content=content.replace('W04 · Profesor / Asesor / Coach',{'es':'W04 · Profesor / Asesor / Coach','en':'W04 · Teacher / Advisor / Coach','pt':'W04 · Professor / Assessor / Coach'}[lang] if page=='workbook' else 'W04 · Profesor / Asesor / Coach')
          content=decorate_ui(content,lang).replace('#page-','#slide-')
        else:
          content=decorate_ui(content,lang)
        if not is_imported:
          content=adapt_audience_body(content,lang,page)
        if content.count('data-intrapage-nav')!=1 or content.count('data-intrapage-open')!=1:
          raise RuntimeError(f'INTRAPAGE_NAV_RENDER_INVALID:{lang}:{CURRENT_AUDIENCE}:{current_module}:{page}')
        if content.count('data-conoce-header')!=1 or content.count('data-conoce-footer')!=1 or content.count('data-conoce-preferences')!=1:
          raise RuntimeError(f'CONOCE_CHROME_RENDER_INVALID:{lang}:{CURRENT_AUDIENCE}:{current_module}:{page}')
        if any(slot in content for slot in ('data-mdg-header','data-mdg-controls','data-mdg-footer')):
          raise RuntimeError(f'CONOCE_CHROME_CORPORATE_SLOT_DRIFT:{lang}:{CURRENT_AUDIENCE}:{current_module}:{page}')
        if 'brand-shell.js' in content or 'MetodologiaBrand.mount' in content or content.count('data-conoce-parent')!=1:
          raise RuntimeError(f'CONOCE_CHROME_AUTHORITY_DRIFT:{lang}:{CURRENT_AUDIENCE}:{current_module}:{page}')
        if re.search(r'<a[^>]*(?:data-conoce-parent[^>]*target=|target=[^>]*data-conoce-parent)',content):
          raise RuntimeError(f'CONOCE_CHROME_PARENT_TARGET_DRIFT:{lang}:{CURRENT_AUDIENCE}:{current_module}:{page}')
        if content.count(f'data-audience-content="{CURRENT_AUDIENCE}"')!=1 or 'data-audience-positioning=' in content or '<aside class="editorial-audience">' in content:
          raise RuntimeError(f'EDITORIAL_PARITY_AUDIENCE_RENDER_INVALID:{lang}:{CURRENT_AUDIENCE}:{current_module}:{page}')
        expected_anchors=[item['anchor'] for item in nav_items] if nav_items else EXPECTED_INTRAPAGE_ANCHORS[page]
        for anchor in expected_anchors:
          if len(re.findall(rf'\bid="{re.escape(anchor)}"',content))!=1 or content.count(f'href="#{anchor}"')<1:
            raise RuntimeError(f'INTRAPAGE_NAV_TARGET_INVALID:{lang}:{CURRENT_AUDIENCE}:{current_module}:{page}:{anchor}')
        if page=='deck':
          if current_module==DEFAULT_MODULE_ID:
            pdf=DECK_RESOURCE;pdf_ref=f'{asset_base(lang,"deck",current_module)}{pdf["source_asset"]}'
          else:
            pdf=MODULE_KITS[current_module]['spec']['official_pdf'];pdf_ref=f'{asset_base(lang,"deck",current_module)}{pdf["ref"]}'
          if content.count('data-official-masterclass ')!=1 or content.count(f'data-official-masterclass-sha256="{pdf["sha256"]}"')!=1 or content.count(f'href="{pdf_ref}"')<3:
            raise RuntimeError(f'OFFICIAL_MASTERCLASS_RENDER_INVALID:{lang}:{CURRENT_AUDIENCE}:{current_module}')
        route=page_dir(lang,page,current_module)
        p=(DIST if route=='.' else DIST/route)/'index.html';write(p,content);outputs.append(p)
      CURRENT_MODULE=DEFAULT_MODULE_ID
  html_outputs=sorted(p for p in outputs if p.suffix=='.html')
  if len(html_outputs)!=EXPECTED_CANONICAL_HTML:
    raise RuntimeError(f'METHOD_IDENTITY_ROUTE_COUNT:{len(html_outputs)}')
  expected_marks={'landing':2,'playbook':4,'prompts':1,'workbook':0,'deck':0,'level0':0,'how':0,'resources_index':0,'intakes':0}
  stale='A'+chr(179)
  relevant_pages=0
  for page_path in html_outputs:
    content=page_path.read_text(encoding='utf-8')
    match=re.search(r'<body data-page="([^"]+)"',content)
    if not match or match.group(1) not in expected_marks:
      raise RuntimeError(f'METHOD_IDENTITY_PAGE_UNKNOWN:{page_path.relative_to(DIST)}')
    page=match.group(1); count=content.count('data-method-mark=')
    module_match=re.search(r'<body[^>]*data-module-id="([^"]+)"',content)
    rendered_module=module_match.group(1) if module_match else DEFAULT_MODULE_ID
    expected_count=expected_marks[page] if rendered_module==DEFAULT_MODULE_ID else 0
    if count!=expected_count or stale in content:
      raise RuntimeError(f'METHOD_IDENTITY_RENDER_DRIFT:{page_path.relative_to(DIST)}:{count}')
    relevant_pages += rendered_module==DEFAULT_MODULE_ID and page in METHOD_IDENTITY['usage']['resources']
  if relevant_pages!=18:
    raise RuntimeError(f'METHOD_IDENTITY_SURFACE_COUNT:{relevant_pages}')
  inventory=editorial_string_inventory(html_outputs)
  if inventory['route_count']!=PARITY['matrix']['canonical_routes']:
    raise RuntimeError(f'EDITORIAL_PARITY_INVENTORY_COUNT:{inventory["route_count"]}')
  inventory_path=DIST/PARITY['string_inventory']['output']
  write(inventory_path,json.dumps(inventory,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
  outputs.append(inventory_path)
  sitemap=[]
  for audience in AUDIENCES:
    CURRENT_AUDIENCE=audience
    for lang in LANGS:
      for page in PAGES:
        route=page_dir(lang,page,DEFAULT_MODULE_ID)
        sitemap.append(f'  <url><loc>{PUBLIC}{"" if route=="." else route+"/"}</loc></url>')
      for current_module in MODULE_IDS[1:]:
        for page in RESOURCE_PAGE_KEYS:
          route=page_dir(lang,page,current_module)
          sitemap.append(f'  <url><loc>{PUBLIC}{route}/</loc></url>')
  if len(sitemap)!=EXPECTED_CANONICAL_HTML or len(set(sitemap))!=EXPECTED_CANONICAL_HTML:
    raise RuntimeError(f'CURRICULUM_SITEMAP_COUNT_INVALID:{len(sitemap)}:{len(set(sitemap))}')
  write(DIST/'sitemap.xml','<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+'\n'.join(sitemap)+'\n</urlset>\n')
  write(DIST/'robots.txt',f'User-agent: *\nAllow: /\nSitemap: {PUBLIC}sitemap.xml\n')
  outputs += [DIST/'sitemap.xml',DIST/'robots.txt']
  outputs += [p for p in (DIST/'assets').rglob('*') if p.is_file()]
  hashes={str(p.relative_to(DIST)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(outputs)}
  source_hashes={str(p.relative_to(SRC)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SRC.rglob('*')) if p.is_file() and not (p.parent==SRC/'assets' and p.name in inactive_legacy_assets)}
  chrome_binding={'schema_version':chrome_spec['schema_version'],'site_id':chrome_spec['site_id'],'display_label':chrome_spec['identity']['display_label'],'source':'src/conoce-chrome-spec-v1.json','source_sha256':source_hashes['conoce-chrome-spec-v1.json'],'self_sha256':chrome_spec['self_sha256'],'canonical_origin':chrome_spec['canonical_origin'],'parent':chrome_spec['parent'],'rendered_pages':len(html_outputs),'storage_keys':chrome_spec['allowed_storage_keys'],'brand_release_immutable':chrome_spec['brand_authority']['immutable'],'state':chrome_spec['state'],'publication_authorized':False}
  chrome_binding['breadcrumbs']=chrome_spec['breadcrumbs']
  editorial_binding={'schema_version':EDITORIAL['schema_version'],'source':'src/editorial-sitemap-spec-v1.json','source_sha256':source_hashes['editorial-sitemap-spec-v1.json'],'self_sha256':EDITORIAL['self_sha256'],'pages':list(EDITORIAL_PAGES),'rendered_pages':len(EDITORIAL_PAGES)*len(LANGS)*len(AUDIENCES),'canonical_count':len(html_outputs),'state':EDITORIAL['state'],'publication_authorized':False}
  parity_binding={'schema_version':PARITY['schema_version'],'source':'src/editorial-parity-spec-v1.json','source_sha256':source_hashes['editorial-parity-spec-v1.json'],'self_sha256':PARITY['self_sha256'],'matrix':PARITY['matrix'],'fallback_policy':PARITY['fallback_policy'],'shared_allowlist':[item['id'] for item in PARITY['shared_allowlist']],'inventory':str(inventory_path.relative_to(DIST)),'inventory_sha256':hashes[str(inventory_path.relative_to(DIST))],'inventory_self_sha256':inventory['self_sha256'],'state':PARITY['state'],'publication_authorized':False}
  contract_binding={'schema_version':'prompt-intent-contract-v2','source':'src/prompt-contracts','surfaces':{surface:list(ids) for surface,ids in PROMPT_CONTRACT_SURFACES.items()},'contract_count':len(PROMPT_CONTRACTS),'rendered_cells':len(PROMPT_CONTRACTS)*len(LANGS)*len(AUDIENCES),'rendered_prompts':len(PROMPT_CONTRACTS)*len(LANGS)*len(AUDIENCES)*4*2,'modes':['template','demo'],'routes':{'library':['01','05','03','04','07','02','06','08','10','09'],'workbook':['B1','B2','B3',*WORKBOOK_PROMPT_IDS]},'syntax':{'input':'<LABEL · help · example>','optional':'[editable or removable text]','parameters':'named block with editable defaults'},'runtime_sha256':source_hashes['site.js'],'self_sha256':{intent_id:contract['self_sha256'] for intent_id,contract in PROMPT_CONTRACTS.items()},'fallback_policy':'forbidden','why_panel':True,'intent_authority':{'schema_version':PROMPT_INTENT_AUTHORITY['schema_version'],'source':'src/prompt-intent-authority-v2.json','source_sha256':source_hashes['prompt-intent-authority-v2.json'],'self_sha256':PROMPT_INTENT_AUTHORITY['self_sha256'],'status':PROMPT_INTENT_AUTHORITY['status'],'rights':PROMPT_INTENT_AUTHORITY['source_provenance']['rights'],'state':PROMPT_INTENT_AUTHORITY['state'],'publication_authorized':False},'state':'RENDERED_DRAFT','publication_authorized':False}
  contract_binding['artifact_labels']={'schema_version':PROMPT_ARTIFACTS['schema_version'],'source':'src/prompt-artifact-labels-v1.json','source_sha256':source_hashes['prompt-artifact-labels-v1.json'],'artifact_count':len(PROMPT_ARTIFACTS['artifacts']),'module_artifact_count':sum(len(labels) for module in PROMPT_ARTIFACTS['module_artifacts'].values() for labels in module.values()),'modules':list(PROMPT_ARTIFACTS['module_artifacts']),'locales':list(LANGS),'fallback_policy':PROMPT_ARTIFACTS['policy']['fallback'],'state':PROMPT_ARTIFACTS['state'],'publication_authorized':False}
  prompt_binding={'schema_version':PROMPT_LIBRARY['schema_version'],'source':'src/prompt-library-spec-v1.json','source_sha256':source_hashes['prompt-library-spec-v1.json'],'format':prompt_spec_contract['format'],'anatomy':prompt_spec_contract['anatomy'],'prompt_count':PROMPT_LIBRARY['prompt_count']+PROMPT_LIBRARY['meta_prompt_count'],'rendered_variants':len(LANGS)*len(AUDIENCES),'reference_sources':[item['url'] for item in PROMPT_LIBRARY['reference_sources']],'chain_of_thought_policy':prompt_spec_contract['chain_of_thought_policy'],'intent_authority':{'schema_version':PROMPT_SPEC_AUTHORITY['schema_version'],'source':'src/prompt-spec-authority-v1.json','source_sha256':source_hashes['prompt-spec-authority-v1.json'],'self_sha256':PROMPT_SPEC_AUTHORITY['self_sha256'],'rights':PROMPT_SPEC_AUTHORITY['source_provenance']['rights'],'state':PROMPT_SPEC_AUTHORITY['state'],'publication_authorized':False},'notebooklm_execution':{'schema_version':NOTEBOOK_EXECUTION['schema_version'],'source':'src/notebooklm-execution-spec-v1.json','source_sha256':source_hashes['notebooklm-execution-spec-v1.json'],'last_verified':NOTEBOOK_EXECUTION['last_verified'],'official_sources':{key:value['url'] for key,value in NOTEBOOK_EXECUTION['official_sources'].items()},'routes':NOTEBOOK_EXECUTION['intent_routes'],'state':NOTEBOOK_EXECUTION['state'],'publication_authorized':False},'state':PROMPT_LIBRARY['state'],'publication_authorized':False,'prompt_contracts':contract_binding}
  official_masterclasses=[
    {'module_id':DEFAULT_MODULE_ID,'source':DECK_RESOURCE['source_asset'],'sha256':DECK_RESOURCE['sha256'],'media_type':DECK_RESOURCE['media_type'],'document_language':DECK_RESOURCE['document_language'],'page_count':DECK_RESOURCE['page_count'],'image_only':True,'tagged':False,'rights':DECK_RESOURCE['rights'],'rendered_variants':len(LANGS)*len(AUDIENCES),'primary_surface':True,'publication_authorized':False},
    *[
      {'module_id':module_id,'source':MODULE_KITS[module_id]['spec']['official_pdf']['ref'],'sha256':MODULE_KITS[module_id]['spec']['official_pdf']['sha256'],'media_type':'application/pdf','document_language':'es','page_count':MODULE_KITS[module_id]['spec']['official_pdf']['page_count'],'image_only':MODULE_KITS[module_id]['spec']['official_pdf']['image_only'],'tagged':MODULE_KITS[module_id]['spec']['official_pdf']['tagged'],'rights':CURRICULUM_PROVENANCE['rights']['status'],'rendered_variants':len(LANGS)*len(AUDIENCES),'primary_surface':True,'publication_authorized':False}
      for module_id in MODULE_IDS[1:]
    ],
  ]
  curriculum_binding={
    'schema_version':CURRICULUM['schema_version'],'source':'src/curriculum-spec-v2.json','source_sha256':source_hashes['curriculum-spec-v2.json'],
    'provenance_source':'src/curriculum-provenance-rights-v2.json','provenance_sha256':source_hashes['curriculum-provenance-rights-v2.json'],
    'authority_bindings':CURRICULUM['authority_bindings'],'modules':[{'id':item['id'],'order':item['order']} for item in CURRICULUM['classes']],
    'payloads':{module_id:MODULE_KITS[module_id]['spec']['content']['sha256'] for module_id in MODULE_IDS[1:]},
    'depth_profile':{'ref':'src/modules/module-depth-profile-v1.json','sha256':source_hashes['modules/module-depth-profile-v1.json'],'profile_id':MODULE_DEPTH_PROFILE['profile_id']},
    'depth_overlays':{module_id:MODULE_KITS[module_id]['spec']['depth_overlay']['sha256'] for module_id in MODULE_IDS[1:]},
    'official_masterclasses':official_masterclasses,'logical_resources':len(MODULE_IDS)*len(RESOURCE_PAGE_KEYS),
    'rendered_resource_pages':len(MODULE_IDS)*len(RESOURCE_PAGE_KEYS)*len(LANGS)*len(AUDIENCES),'canonical_pages':len(html_outputs),
    'run_dependency_at_build_time':False,'state':'RENDERED_DRAFT','publication_authorized':False,
  }
  curriculum_binding['prompt_parity']={
    'schema_version':MODULE_PROMPT_GOLDEN['schema_version'],
    'golden_source':'src/module-01-prompt-inventory-v1.json',
    'golden_source_sha256':source_hashes['module-01-prompt-inventory-v1.json'],
    'golden_self_sha256':MODULE_PROMPT_GOLDEN['self_sha256'],
    'scope':MODULE_PROMPT_GOLDEN['ecosystem_cardinality']['parity_scope_of_this_inventory'],
    'integral_module_parity_status':MODULE_PROMPT_GOLDEN['ecosystem_cardinality']['integral_module_parity_status'],
    'imported_prompt_counts':{
      module_id:MODULE_KITS[module_id]['spec']['variant_validation']['prompts_per_variant']
      for module_id in MODULE_IDS[1:]
    },
    'rendered_prompt_counts':{module_id:14 for module_id in MODULE_IDS[1:]},
    'rendered_cards':252,'rendered_levels':1008,'rendered_copyable_prompts':2016,
    'families':{'direct':10,'meta':4,'learn':4,'embody':4,'evolve':2},
    'surfaces':{'chat':12,'source_search':2},
    'composer':{'ref':'scripts/module_prompt_parity.py','sha256':hashlib.sha256((ROOT/'scripts/module_prompt_parity.py').read_bytes()).hexdigest()},
    'fallback_policy':'forbidden','state':'RENDERED_DRAFT','publication_authorized':False,
  }
  module_dod_binding={'schema_version':MODULE_DOD['schema_version'],'contract_id':MODULE_DOD['contract_id'],'source':'src/module-resource-definition-of-done-v1.json','source_sha256':source_hashes['module-resource-definition-of-done-v1.json'],'self_sha256':MODULE_DOD['self_sha256'],'reference_module':MODULE_DOD['reference_module'],'required_parity':MODULE_DOD['comparison_policy']['required_parity'],'code_identity_required':False,'next_module_requires':'PASS','state':'RENDERED_DRAFT','publication_authorized':False}
  manifest={'schema_version':'build-manifest-v2','build_id':BUILD_ID,'state':'RENDERED_DRAFT','publication_authorized':False,'compiler':{'ref':'scripts/build.py','sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'module_renderer':{'ref':'scripts/module_renderers.py','sha256':hashlib.sha256((ROOT/'scripts/module_renderers.py').read_bytes()).hexdigest()},'ui_primitives':{'ref':'scripts/ui_primitives.py','sha256':hashlib.sha256((ROOT/'scripts/ui_primitives.py').read_bytes()).hexdigest()},'depth_validator':{'ref':'scripts/module_depth.py','sha256':hashlib.sha256((ROOT/'scripts/module_depth.py').read_bytes()).hexdigest()},'prompt_parity_composer':{'ref':'scripts/module_prompt_parity.py','sha256':hashlib.sha256((ROOT/'scripts/module_prompt_parity.py').read_bytes()).hexdigest()}},'variants':{'locales':list(LANGS),'audiences':list(AUDIENCES),'resources':['landing','workbook','playbook','prompts','deck'],'editorial_pages':list(EDITORIAL_PAGES),'modules':list(MODULE_IDS),'logical_resources':len(MODULE_IDS)*len(RESOURCE_PAGE_KEYS),'rendered_resource_pages':len(MODULE_IDS)*len(RESOURCE_PAGE_KEYS)*len(LANGS)*len(AUDIENCES),'canonical_pages':len(html_outputs)},'digital_brand':{'release_id':brand_manifest['releaseId'],'manifest_sha256':MANIFEST_RAW,'receipt_sha256':RECEIPT_RAW,'usage':['tokens','fonts','organization_mark','asset_rights'],'runtime_mount':False,'network_required':False,'publication_authority':False},'conoce_chrome':chrome_binding,'curriculum':curriculum_binding,'module_definition_of_done':module_dod_binding,'editorial_sitemap':editorial_binding,'editorial_parity':parity_binding,'prompt_library':prompt_binding,'official_masterclass':official_masterclasses[0],'official_masterclasses':official_masterclasses,'intrapage_navigation':{'schema_version':INTRAPAGE_NAV['schema_version'],'source':'src/intrapage-navigation-spec-v1.json','source_sha256':source_hashes['intrapage-navigation-spec-v1.json'],'desktop_width_px':INTRAPAGE_NAV['desktop_width_px'],'rendered_pages':len(html_outputs),'publication_authorized':False},'method_identity':{'schema_version':METHOD_IDENTITY['schema_version'],'display_label':METHOD_IDENTITY['display_label'],'role':METHOD_IDENTITY['role'],'generator_sha256':hashlib.sha256((ROOT/METHOD_IDENTITY['source']['generator']).read_bytes()).hexdigest(),'assets':{name:item['sha256'] for name,item in METHOD_IDENTITY['assets'].items()},'resources':METHOD_IDENTITY['usage']['resources'],'rendered_pages':relevant_pages},'outputs':hashes,'sources':source_hashes,'self_hash_model':'sha256(sorted-json-without-self_sha256)'}
  manifest['self_sha256']=hashlib.sha256((json.dumps({key:value for key,value in manifest.items() if key!='self_sha256'},ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode('utf-8')).hexdigest()
  write(DIST/'build-manifest.json',json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
  receipt={'schema_version':'build-receipt-v1','build_id':manifest['build_id'],'manifest_sha256':hashlib.sha256((DIST/'build-manifest.json').read_bytes()).hexdigest(),'manifest_self_sha256':manifest['self_sha256'],'output_count':len(hashes),'deterministic_inputs':True,'state':'RENDERED_DRAFT','publication_authorized':False,'conoce_chrome':manifest['conoce_chrome'],'curriculum':manifest['curriculum'],'module_definition_of_done':manifest['module_definition_of_done'],'editorial_sitemap':manifest['editorial_sitemap'],'editorial_parity':manifest['editorial_parity'],'prompt_library':manifest['prompt_library'],'official_masterclass':manifest['official_masterclass'],'official_masterclasses':manifest['official_masterclasses'],'intrapage_navigation':manifest['intrapage_navigation'],'method_identity':manifest['method_identity'],'self_hash_model':'sha256(sorted-json-without-self)'}
  receipt['self_sha256']=hashlib.sha256(json.dumps(receipt,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
  write(DIST/'build-receipt.json',json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
if __name__=='__main__': build()
