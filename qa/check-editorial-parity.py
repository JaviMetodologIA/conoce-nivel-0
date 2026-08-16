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

def load(name):return json.loads((SRC/name).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def normalized(value):return ' '.join(value.split()).lower()

spec=load('editorial-parity-spec-v1.json')
compiler.validate_editorial_parity(spec)
if [item['id'] for item in spec['shared_allowlist']]!=['organization_and_method_marks','localized_chrome','official_spanish_pdf'] or any(len(item['reason'].split())<7 for item in spec['shared_allowlist']):
  raise SystemExit('EDITORIAL_PARITY_ALLOWLIST_REASON_MISSING')

inventory=json.loads((DIST/spec['string_inventory']['output']).read_text(encoding='utf-8'))
if inventory['self_sha256']!=compiler.canonical_self(inventory,'self_sha256') or inventory['route_count']!=54:
  raise SystemExit('EDITORIAL_PARITY_INVENTORY_INVALID')
html_outputs=sorted(DIST.rglob('index.html'))
actual=compiler.editorial_string_inventory(html_outputs)
if actual!=inventory:
  raise SystemExit('EDITORIAL_PARITY_INVENTORY_COVERAGE_DRIFT')

combos={(item['locale'],item['audience'],item['page']) for item in inventory['routes']}
expected=set(product(LANGS,AUDIENCES,PAGES))
if combos!=expected or len({item['route'] for item in inventory['routes']})!=54:
  raise SystemExit('EDITORIAL_PARITY_MATRIX_GAP')

audience=load('audience-spec-v1.json')
resources=load('public-resource-spec-v1.json')
compiler.validate_audience_spec(audience)

by_combo={}
forbidden_locale_literals={
  'en':('Antes de continuar','Casos de uso · destino provisional','Ruta experta · Spec → Build → Verify','Retrato de Javier Montaño','Aprender · Aprehender · Evolucionar'),
  'pt':('Casos de uso · destino provisional','Ruta experta · Spec → Build → Verify','Aprender · Aprehender · Evolucionar','Teach-back de 3 minutos'),
}
for item in inventory['routes']:
  path=DIST/item['route'];source=path.read_text(encoding='utf-8');text=normalized(source)
  key=(item['locale'],item['audience'],item['page']);by_combo[key]=item
  if f'<html lang="{item["locale"]}" data-audience="{item["audience"]}"' not in source:
    raise SystemExit(f'EDITORIAL_PARITY_DOCUMENT_VARIANT_DRIFT:{item["route"]}')
  if source.count(f'data-audience-content="{item["audience"]}"')!=1 or 'data-audience-positioning=' in source or '<aside class="editorial-audience">' in source:
    raise SystemExit(f'EDITORIAL_PARITY_BODY_ADAPTATION_MISSING:{item["route"]}')
  for literal in forbidden_locale_literals.get(item['locale'],()):
    if normalized(literal) in text:
      raise SystemExit(f'EDITORIAL_PARITY_CROSS_LOCALE_LITERAL:{item["route"]}:{literal}')
  localized=audience['locales'][item['locale']][item['audience']][item['page']]
  soup=BeautifulSoup(source,'html.parser');main=soup.find('main')
  for field in spec['required_audience_surfaces']:
    nodes=main.select(f'[data-audience-field="{field}"]')
    if len(nodes)!=1 or normalized(nodes[0].get_text(' ',strip=True))!=normalized(localized[field]):
      raise SystemExit(f'EDITORIAL_PARITY_LOCALIZED_FIELD_MISSING:{item["route"]}:{field}')

for locale,page in product(LANGS,PAGES):
  pair=[]
  for variant in AUDIENCES:
    item=by_combo[(locale,variant,page)];source=(DIST/item['route']).read_text(encoding='utf-8');soup=BeautifulSoup(source,'html.parser')
    for selector in ('[data-audience-positioning]','aside.editorial-audience'):
      for node in soup.select(selector):node.decompose()
    pair.append({field:normalized(soup.select_one(f'[data-audience-field="{field}"]').get_text(' ',strip=True)) for field in spec['required_audience_surfaces']})
  for field in spec['required_audience_surfaces']:
    if pair[0][field]==pair[1][field]:
      raise SystemExit(f'EDITORIAL_PARITY_AUDIENCE_FIELD_CLONE:{locale}:{page}:{field}')

pdf=SRC/'assets/masterclass-ia-nivel-0.pdf'
if sha(pdf)!=spec['official_pdf']['sha256'] or sha(DIST/'assets/masterclass-ia-nivel-0.pdf')!=spec['official_pdf']['sha256']:
  raise SystemExit('EDITORIAL_PARITY_PDF_BYTES_DRIFT')
for locale,variant in product(LANGS,AUDIENCES):
  item=by_combo[(locale,variant,'deck')];source=(DIST/item['route']).read_text(encoding='utf-8')
  localized=resources['deck']['locales'][locale]
  if any(value not in source for value in (localized['description'],localized['language_note'])):
    raise SystemExit(f'EDITORIAL_PARITY_PDF_GUIDE_NOTE_MISSING:{locale}:{variant}')

build_source=(ROOT/'scripts/build.py').read_text(encoding='utf-8')
if re.search(r"\.get\(['\"]locales['\"],\s*\{\}\)\.get\(",build_source):
  raise SystemExit('EDITORIAL_PARITY_SILENT_FALLBACK_PRESENT')

for mutate in ('state','matrix','protocols','source_root','allowlist'):
  candidate=copy.deepcopy(spec)
  if mutate=='state':candidate['state']='PUBLISHED'
  elif mutate=='matrix':candidate['matrix']['canonical_routes']=53
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
if manifest.get('state')!='RENDERED_DRAFT' or receipt.get('state')!='RENDERED_DRAFT' or manifest.get('publication_authorized') is not False:
  raise SystemExit('EDITORIAL_PARITY_STATE_DRIFT')

print(f'EDITORIAL_PARITY_OK routes=54 fields=378 mutations={audience_mutations+5} strings={sum(len(item["visible_text"])+len(item["accessible_text"]) for item in inventory["routes"])} pdf={spec["official_pdf"]["sha256"]}')
