#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from itertools import product
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import build as compiler

SRC=ROOT/'src';DIST=ROOT/'dist'
LANGS=('es','en','pt');AUDIENCES=('persona','empresa')
PAGES=('landing','deck','workbook','playbook','prompts','level0','how','resources_index','intakes')
GLOBAL_PAGES=('landing','level0','how','resources_index','intakes')
RESOURCE_PAGES=('deck','workbook','playbook','prompts')
DEFAULT_MODULE_ID='ia-panorama'
MODULE_IDS=(DEFAULT_MODULE_ID,'ocupado-productivo','trabajo-amplificado','trabajo-agentico')
EXPECTED_ROUTES=126
RESOURCE_PAYLOAD_KEYS={'deck':'masterclass','workbook':'workbook','playbook':'playbook','prompts':'promptLibrary'}
DEPTH_PAYLOAD_KEYS={'deck':'masterclass','workbook':'workbook','playbook':'playbook','prompts':'prompts'}
DEPTH_ORACLE_SKIP={'id','phase','prompt_ref','library_ref','authority_refs','concept_ids','moment_ids','next','level'}

def load(name):return json.loads((SRC/name).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def normalized(value):return ' '.join(value.split()).lower()

def depth_oracle_strings(value,parent_key=''):
  if isinstance(value,str):
    return [] if parent_key in DEPTH_ORACLE_SKIP or not value.strip() else [value]
  if isinstance(value,dict):
    values=[]
    for key,child in value.items():values.extend(depth_oracle_strings(child,key))
    return values
  if isinstance(value,list):
    values=[]
    for child in value:values.extend(depth_oracle_strings(child,parent_key))
    return values
  return []

def module_oracle_strings(module,page,depth):
  resource=module[RESOURCE_PAYLOAD_KEYS[page]]
  values=[resource['title'],resource['lede']]
  if page=='deck':
    values.extend(item['title'] for item in resource['moments'])
  elif page=='playbook':
    values.extend(chapter['title'] for chapter in resource['chapters'])
  elif page=='prompts':
    values.extend(prompt['title'] for prompt in resource['prompts'])
  values.extend(depth_oracle_strings(depth[DEPTH_PAYLOAD_KEYS[page]]))
  return [value for value in values if isinstance(value,str) and value.strip()]

spec=load('editorial-parity-spec-v1.json')
compiler.validate_editorial_parity(spec)
if [item['id'] for item in spec['shared_allowlist']]!=['organization_and_method_marks','localized_chrome','official_spanish_pdf'] or any(len(item['reason'].split())<7 for item in spec['shared_allowlist']):
  raise SystemExit('EDITORIAL_PARITY_ALLOWLIST_REASON_MISSING')

inventory=json.loads((DIST/spec['string_inventory']['output']).read_text(encoding='utf-8'))
if inventory['self_sha256']!=compiler.canonical_self(inventory,'self_sha256') or inventory['route_count']!=EXPECTED_ROUTES:
  raise SystemExit('EDITORIAL_PARITY_INVENTORY_INVALID')
html_outputs=sorted(DIST.rglob('index.html'))
actual=compiler.editorial_string_inventory(html_outputs)
if actual!=inventory:
  raise SystemExit('EDITORIAL_PARITY_INVENTORY_COVERAGE_DRIFT')

combos={(item['locale'],item['audience'],item.get('module_id'),item['page']) for item in inventory['routes']}
expected={
  (locale,audience,DEFAULT_MODULE_ID,page)
  for locale,audience,page in product(LANGS,AUDIENCES,GLOBAL_PAGES)
}|{
  (locale,audience,module_id,page)
  for locale,audience,module_id,page in product(LANGS,AUDIENCES,MODULE_IDS,RESOURCE_PAGES)
}
if combos!=expected or len({item['route'] for item in inventory['routes']})!=EXPECTED_ROUTES:
  raise SystemExit('EDITORIAL_PARITY_MATRIX_GAP')

audience=load('audience-spec-v1.json')
resources=load('public-resource-spec-v1.json')
curriculum=load('curriculum-spec-v2.json')
compiler.validate_audience_spec(audience)
module_payloads={item['id']:load(item['content']['ref']) for item in curriculum['classes'][1:]}
module_depth_payloads={item['id']:load(item['depth_overlay']['ref']) for item in curriculum['classes'][1:]}
module_variants={
  (module_id,variant['locale'],variant['audience']):variant['module']
  for module_id,payload in module_payloads.items()
  for variant in payload['variants']
}
module_depth_variants={
  (module_id,variant['locale'],variant['audience']):variant
  for module_id,payload in module_depth_payloads.items()
  for variant in payload['variants']
}

by_combo={}
forbidden_locale_literals={
  'en':('Antes de continuar','Casos de uso · destino provisional','Ruta experta · Spec → Build → Verify','Retrato de Javier Montaño','Aprender · Aprehender · Evolucionar'),
  'pt':('Casos de uso · destino provisional','Ruta experta · Spec → Build → Verify','Aprender · Aprehender · Evolucionar','Teach-back de 3 minutos'),
}
for item in inventory['routes']:
  path=DIST/item['route'];source=path.read_text(encoding='utf-8');text=normalized(source)
  module_id=item.get('module_id')
  key=(item['locale'],item['audience'],module_id,item['page']);by_combo[key]=item
  if f'<html lang="{item["locale"]}" data-audience="{item["audience"]}"' not in source:
    raise SystemExit(f'EDITORIAL_PARITY_DOCUMENT_VARIANT_DRIFT:{item["route"]}')
  if f'<body data-page="{item["page"]}" data-module-id="{module_id}"' not in source:
    raise SystemExit(f'EDITORIAL_PARITY_MODULE_VARIANT_DRIFT:{item["route"]}')
  if source.count(f'data-audience-content="{item["audience"]}"')!=1 or 'data-audience-positioning=' in source or '<aside class="editorial-audience">' in source:
    raise SystemExit(f'EDITORIAL_PARITY_BODY_ADAPTATION_MISSING:{item["route"]}')
  for literal in forbidden_locale_literals.get(item['locale'],()):
    if normalized(literal) in text:
      raise SystemExit(f'EDITORIAL_PARITY_CROSS_LOCALE_LITERAL:{item["route"]}:{literal}')
  soup=BeautifulSoup(source,'html.parser');main=soup.find('main')
  if module_id==DEFAULT_MODULE_ID:
    localized=audience['locales'][item['locale']][item['audience']][item['page']]
  else:
    variant=module_variants[(module_id,item['locale'],item['audience'])]
    editorial=next(
      candidate['editorial'] for candidate in module_payloads[module_id]['variants']
      if candidate['locale']==item['locale'] and candidate['audience']==item['audience']
    )
    localized={
      'hero':editorial['hero']['title'],
      'problem':editorial['problem']['body'],
      'benefits':editorial['benefits']['body'],
      'method':editorial['method']['body'],
      'evidence':editorial['evidence']['body'],
      'cta':editorial['cta']['action'],
      'closing':variant['transfer'],
    }
  for field in spec['required_audience_surfaces']:
    nodes=main.select(f'[data-audience-field="{field}"]')
    if len(nodes)!=1 or normalized(nodes[0].get_text(' ',strip=True))!=normalized(localized[field]):
      raise SystemExit(f'EDITORIAL_PARITY_LOCALIZED_FIELD_MISSING:{item["route"]}:{field}')
  if module_id!=DEFAULT_MODULE_ID:
    main_text=normalized(main.get_text(' ',strip=True))
    depth_variant=module_depth_variants[(module_id,item['locale'],item['audience'])]
    missing=[value for value in module_oracle_strings(variant,item['page'],depth_variant) if normalized(value) not in main_text]
    if missing:
      raise SystemExit(f'EDITORIAL_PARITY_MODULE_ORACLE_MISSING:{item["route"]}:{missing[0]}')

# [EVIDENCE:AUDIENCE_PARITY] Seven material surfaces differ across all 126 routes.
pair_dimensions=[
  (locale,DEFAULT_MODULE_ID,page)
  for locale,page in product(LANGS,GLOBAL_PAGES)
]+[
  (locale,module_id,page)
  for locale,module_id,page in product(LANGS,MODULE_IDS,RESOURCE_PAGES)
]
for locale,module_id,page in pair_dimensions:
  pair=[]
  for variant in AUDIENCES:
    item=by_combo[(locale,variant,module_id,page)];source=(DIST/item['route']).read_text(encoding='utf-8');soup=BeautifulSoup(source,'html.parser')
    for selector in ('[data-audience-positioning]','aside.editorial-audience'):
      for node in soup.select(selector):node.decompose()
    pair.append({field:normalized(soup.select_one(f'[data-audience-field="{field}"]').get_text(' ',strip=True)) for field in spec['required_audience_surfaces']})
  for field in spec['required_audience_surfaces']:
    if module_id==DEFAULT_MODULE_ID and pair[0][field]==pair[1][field]:
      raise SystemExit(f'EDITORIAL_PARITY_AUDIENCE_FIELD_CLONE:{locale}:{module_id}:{page}:{field}')
  # Imported M2-M4 variants are hash-bound authorities and intentionally share
  # some field values. They must remain exact, while the rendered surface as a
  # whole still differs materially between persona and empresa.
  if module_id!=DEFAULT_MODULE_ID and pair[0]==pair[1]:
    raise SystemExit(f'EDITORIAL_PARITY_AUDIENCE_VARIANT_CLONE:{locale}:{module_id}:{page}')

pdf=SRC/'assets/masterclass-ia-nivel-0.pdf'
if sha(pdf)!=spec['official_pdf']['sha256'] or sha(DIST/'assets/masterclass-ia-nivel-0.pdf')!=spec['official_pdf']['sha256']:
  raise SystemExit('EDITORIAL_PARITY_PDF_BYTES_DRIFT')
for locale,variant in product(LANGS,AUDIENCES):
  item=by_combo[(locale,variant,DEFAULT_MODULE_ID,'deck')];source=(DIST/item['route']).read_text(encoding='utf-8')
  localized=resources['deck']['locales'][locale]
  if any(value not in source for value in (localized['description'],localized['language_note'])):
    raise SystemExit(f'EDITORIAL_PARITY_PDF_GUIDE_NOTE_MISSING:{locale}:{variant}')

build_source=(ROOT/'scripts/build.py').read_text(encoding='utf-8')
if re.search(r"\.get\(['\"]locales['\"],\s*\{\}\)\.get\(",build_source):
  raise SystemExit('EDITORIAL_PARITY_SILENT_FALLBACK_PRESENT')

for mutate in ('state','matrix','protocols','source_root','allowlist'):
  candidate=copy.deepcopy(spec)
  if mutate=='state':candidate['state']='PUBLISHED'
  elif mutate=='matrix':candidate['matrix']['canonical_routes']=EXPECTED_ROUTES-1
  elif mutate=='protocols':candidate['preference_controls']['protocols']=['http']
  elif mutate=='source_root':candidate['localized_sources'][0]['root']='missing'
  else:candidate['shared_allowlist'][0]['reason']=''
  candidate['self_sha256']=compiler.canonical_self(candidate,'self_sha256')
  rejected=False
  try:compiler.validate_editorial_parity(candidate)
  except SystemExit:rejected=True
  if not rejected:raise SystemExit(f'EDITORIAL_PARITY_MUTATION_PASSED:{mutate}')

audience_mutations=0
for locale,page,field in product(LANGS,PAGES,spec['required_audience_surfaces']):
  candidate=copy.deepcopy(audience)
  candidate['locales'][locale]['persona'][page][field]=candidate['locales'][locale]['empresa'][page][field]
  rejected=False
  try:compiler.validate_audience_spec(candidate)
  except SystemExit:rejected=True
  if not rejected:raise SystemExit(f'EDITORIAL_PARITY_FIELD_CLONE_MUTATION_PASSED:{locale}:{page}:{field}')
  audience_mutations+=1
for page in PAGES:
  for mode in ('missing','unknown'):
    candidate=copy.deepcopy(audience)
    if mode=='missing':candidate['locales']['es']['persona'][page].pop('method')
    else:candidate['locales']['es']['persona'][page]['unknown']='x'
    rejected=False
    try:compiler.validate_audience_spec(candidate)
    except SystemExit:rejected=True
    if not rejected:raise SystemExit(f'EDITORIAL_PARITY_FIELD_{mode.upper()}_MUTATION_PASSED:{page}')
    audience_mutations+=1
for mode in ('missing_page','unknown_page'):
  candidate=copy.deepcopy(audience)
  if mode=='missing_page':candidate['locales']['es']['persona'].pop('landing')
  else:candidate['locales']['es']['persona']['unknown']=copy.deepcopy(candidate['locales']['es']['persona']['landing'])
  rejected=False
  try:compiler.validate_audience_spec(candidate)
  except SystemExit:rejected=True
  if not rejected:raise SystemExit(f'EDITORIAL_PARITY_{mode.upper()}_MUTATION_PASSED')
  audience_mutations+=1

manifest=json.loads((DIST/'build-manifest.json').read_text(encoding='utf-8'))
receipt=json.loads((DIST/'build-receipt.json').read_text(encoding='utf-8'))
binding=manifest.get('editorial_parity',{})
if binding.get('source_sha256')!=sha(SRC/'editorial-parity-spec-v1.json') or binding.get('inventory_sha256')!=sha(DIST/'editorial-string-inventory.json') or receipt.get('editorial_parity')!=binding:
  raise SystemExit('EDITORIAL_PARITY_RECEIPT_BINDING_DRIFT')
if manifest.get('state')!='RENDERED_DRAFT' or receipt.get('state')!='RENDERED_DRAFT' or manifest.get('publication_authorized') is not False or receipt.get('publication_authorized') is not False:
  raise SystemExit('EDITORIAL_PARITY_STATE_DRIFT')

print(f'[EVIDENCE:EDITORIAL_PARITY] EDITORIAL_PARITY_OK routes={EXPECTED_ROUTES} fields={EXPECTED_ROUTES*len(spec["required_audience_surfaces"])} mutations={audience_mutations+5} strings={sum(len(item["visible_text"])+len(item["accessible_text"]) for item in inventory["routes"])} pdf={spec["official_pdf"]["sha256"]} state=RENDERED_DRAFT publication=false')
