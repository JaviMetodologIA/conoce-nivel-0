#!/usr/bin/env python3
from __future__ import annotations
import hashlib, html, io, json, posixpath, re, shutil, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'src'; DIST=ROOT/'dist'
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
PUBLIC='https://javimetodologia.github.io/'
LANGS=('es','en','pt')
LANDING=json.loads((SRC/'landing-spec-v2.json').read_text(encoding='utf-8'))
RESOURCES=json.loads((SRC/'public-resource-spec-v1.json').read_text(encoding='utf-8'))
ADVANCED=json.loads((SRC/'workbook-advanced-v1.json').read_text(encoding='utf-8'))
PLAYBOOK=json.loads((SRC/'playbook-spec-v1.json').read_text(encoding='utf-8'))
PROMPT_LIBRARY=json.loads((SRC/'prompt-library-spec-v1.json').read_text(encoding='utf-8'))
MONTHLY_INTAKE_COPY={
  'es':('1 convocatoria al mes · primera semana','Una convocatoria al mes · primera semana'),
  'en':('1 monthly intake · first week','One monthly intake · first week'),
  'pt':('1 turma por mês · primeira semana','Uma turma por mês · primeira semana'),
}
for locale,(offer_copy,final_copy) in MONTHLY_INTAKE_COPY.items():
  landing_locale=LANDING.get('locales',{}).get(locale,{})
  if offer_copy not in landing_locale.get('offer',[]) or landing_locale.get('final_eyebrow') != final_copy:
    raise SystemExit(f'LANDING_MONTHLY_INTAKE_CONTRACT_INVALID: {locale}')
if ADVANCED.get('prompt_format_contract',{}).get('formats') != ['natural','parameters','spec','pair']:
  raise SystemExit('PROMPT_FORMAT_CONTRACT_INVALID')
if PLAYBOOK.get('section_ids') != ['hero','intro','founders','assistants','scales','modes','fluency','frameworks','techniques','apprehend','method','integrity','evolve','tools','notebooklm','prompts','workflows','routines','standards','glossary','faq','close']:
  raise SystemExit('PLAYBOOK_SECTION_CONTRACT_INVALID')
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
if PROMPT_LIBRARY.get('level_formats') != ['natural','parameters','spec','pair'] or PROMPT_LIBRARY.get('publication_authorized') is not False:
  raise SystemExit('PROMPT_LIBRARY_CONTRACT_INVALID')

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

PROMPTS_ES=[
('Primera base con propósito','Quiero construir una base de conocimiento útil y verificable sobre [TEMA].\n\nLa necesito para [DECISIÓN, PROYECTO O RESULTADO]. Mi contexto es [CONTEXTO] y la audiencia es [AUDIENCIA].\n\nDelimita el alcance; explica conceptos esenciales y cambios recientes; prioriza fuentes primarias; muestra tensiones y límites; separa hechos, interpretaciones e incertidumbre; recomienda fuentes con título, autor, fecha, enlace y razón. Entrega un informe citado. No presentes como certeza lo que las fuentes no permiten afirmar.'),
('Auditar la base','Audita esta base usando únicamente las fuentes seleccionadas y cita cada hallazgo. Revisa cobertura, tensiones, ambigüedades, calidad, vigencia, sesgos y redundancias. Entrega un resumen de máximo 8 líneas, una tabla Hallazgo | Tipo | Evidencia | Impacto | Acción, vacíos priorizados y una conclusión honesta sobre qué puedo afirmar hoy.'),
('Investigación a medida','Usa el diagnóstico anterior. Elige el vacío de mayor impacto para [RESULTADO] y conviértelo en un prompt listo para Deep Research. Incluye objetivo, preguntas dentro y fuera, tensiones, fuentes prioritarias, contexto temporal o regional, evidencia mínima, formato citado y criterios de aceptación. Si falta contexto material, haz máximo 3 preguntas.'),
('Cerrar o repetir','Ya importé nuevas fuentes. Compara la base actual con la auditoría anterior: vacío cerrado, afirmaciones confirmadas o refutadas, tensiones nuevas, valor de fuentes y riesgo residual. Emite [BASE SUFICIENTE] con límites o [REPETIR INVESTIGACIÓN] con el siguiente prompt. No busques perfección: detente cuando la evidencia sea suficiente para el propósito.'),
('Activar un rol','Actúa como [PROFESOR | ASESOR | COACH] especializado en este Notebook. Basa todo en las fuentes y cítalas; distingue evidencia, inferencia y dato faltante; declara cuando la base no alcance; adapta la profundidad y cierra con el siguiente paso del rol. Confirma el rol y pregunta qué resultado quiero lograr.'),
('Generar contenido','Crea [TIPO DE CONTENIDO] para [AUDIENCIA] con objetivo [RESULTADO]. Identifica tesis, evidencia, tensión y límite; propone estructura; usa citas; no añadas hechos externos; marca inferencias. Entrega pieza final, fuentes y tres decisiones editoriales.'),
('Diseñar casos de uso','Diseña 10 casos de uso para [ROL/EQUIPO]. Para cada uno indica problema, usuario, evidencia citada, entrada, resultado, trabajo humano y de IA, riesgo y control, complejidad e impacto, y un experimento de 7 días. Ordena valor frente a esfuerzo y recomienda uno.'),
('Evaluar comprensión','Evalúame sobre [TEMA] usando solo las fuentes. Haz una pregunta a la vez y avanza por fundamentos, intermedio, avanzado y aplicación. Evalúa cada respuesta, explica y cita. Termina con fortalezas, lagunas, fuentes a revisar y una práctica.'),
('Simular una conversación','Simula una [ENTREVISTA | QBR | DEFENSA] sobre [TEMA]. Pregunta audiencia, resultado y tiempo. Haz una pregunta a la vez; incluye evidencia, alternativas, riesgos y límites. Evalúa cada respuesta y termina con fortalezas, vacíos y tres mejoras.'),
('Configurar el Notebook','Diseña la configuración final para [PROPÓSITO], [USUARIO], [RESULTADO] y [RESTRICCIONES]. Entrega: A) instrucción personalizada con rol, tareas, límites, citas y calidad; B) exactamente 10 prompts de inicio; C) guía de prueba en 5 líneas. Separa hechos, inferencias y datos faltantes.')]

PROMPTS_EN=[
('Build a purposeful source base','I want a useful, verifiable knowledge base about [TOPIC] for [DECISION OR RESULT]. My context is [CONTEXT] and audience is [AUDIENCE]. Define scope and questions; explain essentials and recent changes; prioritize primary sources; include tensions and evidence limits; separate facts, interpretations and uncertainty; recommend sources with title, author, date, link and reason. Deliver a cited report. Do not present more certainty than the sources support.'),
('Audit the source base','Audit this knowledge base using only selected sources and cite every finding. Review coverage, tensions, ambiguities, quality, freshness, bias and redundancy. Deliver: an eight-line executive summary; a Finding | Type | Evidence | Impact | Action table; prioritized gaps; and an honest conclusion about what can and cannot be claimed today.'),
('Create targeted research','Use the prior diagnosis. Choose the highest-impact gap for [RESULT] and turn it into a prompt ready for Deep Research. Include objective, in-scope and out-of-scope questions, tensions, preferred source types, time or region, minimum evidence, cited format and acceptance criteria. If material context is missing, ask at most three questions first.'),
('Stop or repeat','I imported new sources. Compare the current base with the previous audit: gap closed, claims confirmed or refuted, new tensions, source value and residual risk. Issue [BASE SUFFICIENT] with limits or [REPEAT RESEARCH] with the next research prompt. Do not seek perfection; stop when evidence is sufficient for the declared purpose.'),
('Activate a role','Act as a [TEACHER | ADVISOR | COACH] specialized in this Notebook. Ground every response in selected sources and cite them; distinguish evidence, inference and missing data; state when the base is insufficient; adapt depth; close with the role-appropriate next step. Confirm the role and ask what result I want.'),
('Create content','Create [CONTENT TYPE] for [AUDIENCE] to achieve [RESULT]. Identify thesis, strongest evidence, a tension and a limit; propose structure; cite verifiable claims; add no external facts; label inferences. Deliver the final piece, sources used and three editorial decisions.'),
('Design use cases','Design 10 use cases for [ROLE/TEAM]. For each: problem, user, cited support, input, expected output, human and AI work, risk and control, complexity and impact, and a seven-day experiment. Rank value against effort and recommend one place to start.'),
('Assess understanding','Assess me on [TOPIC] using only these sources. Ask one question at a time across foundations, intermediate, advanced and application. Grade each answer, explain and cite. End with strengths, gaps, sources to revisit and one practice.'),
('Simulate a conversation','Simulate an [INTERVIEW | QBR | DEFENSE] on [TOPIC]. First ask audience, desired outcome and time. Ask one question at a time about evidence, alternatives, risks and limits. Grade each answer and end with strengths, gaps and three improvements.'),
('Configure the Notebook','Design the final configuration for [PURPOSE], [USER], [RESULT] and [CONSTRAINTS]. Deliver: A) a personalized instruction defining role, tasks, limits, citations and quality; B) exactly 10 starter prompts; C) a five-line test guide. Separate facts, inferences and missing data.')]

PROMPTS_PT=[
('Construir uma base com propósito','Quero uma base de conhecimento útil e verificável sobre [TEMA] para [DECISÃO OU RESULTADO]. Meu contexto é [CONTEXTO] e o público é [PÚBLICO]. Delimite escopo e perguntas; explique fundamentos e mudanças recentes; priorize fontes primárias; inclua tensões e limites da evidência; separe fatos, interpretações e incerteza; recomende fontes com título, autor, data, link e motivo. Entregue relatório citado. Não apresente mais certeza do que as fontes permitem.'),
('Auditar a base','Audite esta base usando apenas as fontes selecionadas e cite cada achado. Revise cobertura, tensões, ambiguidades, qualidade, atualidade, vieses e redundâncias. Entregue: resumo de oito linhas; tabela Achado | Tipo | Evidência | Impacto | Ação; lacunas priorizadas; e conclusão honesta sobre o que pode ou não ser afirmado hoje.'),
('Criar pesquisa sob medida','Use o diagnóstico anterior. Escolha a lacuna de maior impacto para [RESULTADO] e transforme-a em prompt pronto para Deep Research. Inclua objetivo, perguntas dentro e fora do escopo, tensões, fontes prioritárias, tempo ou região, evidência mínima, formato citado e critérios de aceitação. Se faltar contexto material, faça no máximo três perguntas.'),
('Encerrar ou repetir','Importei novas fontes. Compare a base atual com a auditoria: lacuna fechada, afirmações confirmadas ou refutadas, novas tensões, valor das fontes e risco residual. Emita [BASE SUFICIENTE] com limites ou [REPETIR PESQUISA] com o próximo prompt. Não busque perfeição; pare quando a evidência for suficiente para o propósito.'),
('Ativar um papel','Atue como [PROFESSOR | ASSESSOR | COACH] especializado neste Notebook. Baseie tudo nas fontes selecionadas e cite-as; diferencie evidência, inferência e dado ausente; declare quando a base não alcançar; adapte a profundidade; encerre com o próximo passo do papel. Confirme o papel e pergunte qual resultado desejo.'),
('Criar conteúdo','Crie [TIPO DE CONTEÚDO] para [PÚBLICO] com objetivo [RESULTADO]. Identifique tese, evidência forte, tensão e limite; proponha estrutura; cite afirmações verificáveis; não adicione fatos externos; marque inferências. Entregue peça final, fontes e três decisões editoriais.'),
('Projetar casos de uso','Projete 10 casos de uso para [PAPEL/EQUIPE]. Para cada um: problema, usuário, suporte citado, entrada, resultado, trabalho humano e da IA, risco e controle, complexidade e impacto, e experimento de sete dias. Ordene valor versus esforço e recomende um.'),
('Avaliar compreensão','Avalie-me sobre [TEMA] usando apenas as fontes. Faça uma pergunta por vez nos níveis fundamentos, intermediário, avançado e aplicação. Avalie cada resposta, explique e cite. Termine com forças, lacunas, fontes a revisar e uma prática.'),
('Simular uma conversa','Simule uma [ENTREVISTA | QBR | DEFESA] sobre [TEMA]. Primeiro pergunte público, resultado desejado e tempo. Faça uma pergunta por vez sobre evidência, alternativas, riscos e limites. Avalie cada resposta e termine com forças, lacunas e três melhorias.'),
('Configurar o Notebook','Projete a configuração final para [PROPÓSITO], [USUÁRIO], [RESULTADO] e [RESTRIÇÕES]. Entregue: A) instrução personalizada com papel, tarefas, limites, citações e qualidade; B) exatamente 10 prompts iniciais; C) guia de teste em cinco linhas. Separe fatos, inferências e dados ausentes.')]

def prompt_for(lang,n,title,text):
    return (PROMPTS_ES if lang=='es' else PROMPTS_EN if lang=='en' else PROMPTS_PT)[n-1]

def esc(s): return html.escape(s,quote=True)
def ui_icon(name):
  paths={
    'arrow':'<path d="M5 12h14M13 6l6 6-6 6"></path>',
    'back':'<path d="M19 12H5m6 6-6-6 6-6"></path>',
    'external':'<path d="M14 5h5v5M19 5l-8 8"></path><path d="M17 13v5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1h5"></path>',
    'download':'<path d="M12 4v11m-4-4 4 4 4-4M5 20h14"></path>',
    'print':'<path d="M7 9V4h10v5M7 17H5a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2"></path><path d="M7 14h10v6H7z"></path>',
  }
  return f'<svg class="ui-icon" aria-hidden="true" viewBox="0 0 24 24">{paths[name]}</svg>'

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
def page_dir(lang,page):
    parts=[] if lang=='es' else [lang]
    if page!='landing': parts.append(page)
    return '/'.join(parts) or '.'
def rel_dir(lang,page,target_lang,target_page=None):
    target_page=page if target_page is None else target_page
    rel=posixpath.relpath(page_dir(target_lang,target_page),page_dir(lang,page))
    return './' if rel=='.' else rel.rstrip('/')+'/'
def rel_page(lang,page,target_lang,target_page=None):
    target_page=page if target_page is None else target_page
    target=posixpath.join(page_dir(target_lang,target_page), 'index.html')
    return posixpath.relpath(target,page_dir(lang,page))
def asset_base(lang,page): return rel_dir(lang,page,'es','landing')
def head(lang,title,page):
    base=asset_base(lang,page)
    l=LANDING['locales'][lang]
    desc=l['meta_description'] if page=='landing' else {'es':'Ruta Nivel 0 de MetodologIA: aprendizaje y práctica con IA basada en fuentes.','en':'MetodologIA Level 0: source-grounded AI learning and practice.','pt':'Rota Nível 0 da MetodologIA: aprendizagem e prática com IA baseada em fontes.'}[lang]
    canonical=PUBLIC+('' if lang=='es' else f'{lang}/')+('' if page=='landing' else f'{page}/')
    alternates=''.join(f'<link rel="alternate" hreflang="{code}" href="{PUBLIC}{"" if code=="es" else code+"/"}{"" if page=="landing" else page+"/"}">' for code in LANGS)
    alternates+=f'<link rel="alternate" hreflang="x-default" href="{PUBLIC}{"" if page=="landing" else page+"/"}">'
    social=f'''<meta property="og:type" content="website"><meta property="og:site_name" content="MetodologIA"><meta property="og:title" content="{esc(title)} · MetodologIA"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{canonical}"><meta name="twitter:card" content="summary">'''
    return f'''<!doctype html><html lang="{lang}" data-theme="light" class="no-js"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · MetodologIA</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{canonical}">{alternates}{social}<link rel="stylesheet" href="{base}assets/site.css"><link rel="stylesheet" href="{base}assets/forms.css"><noscript><style>.sheet[hidden],.slide{{display:block!important}}</style></noscript></head><body data-page="{page}"><a class="skip" href="#main">{T[lang]['skip']}</a>{header(lang,page)}'''
def header(lang,page):
    home=rel_page(lang,page,lang,'landing')
    navlabel={'es':'Principal','en':'Primary','pt':'Principal'}[lang]; langlabel={'es':'Idioma','en':'Language','pt':'Idioma'}[lang]
    darklabel={'es':'Tema oscuro','en':'Dark theme','pt':'Tema escuro'}[lang]; lightlabel={'es':'Tema claro','en':'Light theme','pt':'Tema claro'}[lang]
    links={target:rel_page(lang,page,target) for target in LANGS}
    asset=asset_base(lang,page)
    l=LANDING['locales'][lang]
    nav=''.join(f'<a data-chapter-link href="{home}#{anchor}">{label}</a>' for label,anchor in zip(l['nav'],('entrada','ruta','experiencia','metodo')))
    return f'''<header class="top"><div class="shell top-in"><a class="brand" href="{home}"><img class="mark" src="{asset}assets/metodologia-logo.svg" alt=""><span><span class="brand-name">Metodolog<b>IA</b></span><span class="brand-role">{T[lang]['route']}</span></span></a><nav class="nav" aria-label="{navlabel}">{nav}</nav><div class="tools"><div class="brand-controls"><div class="langs" aria-label="{langlabel}"><a class="lang" href="{links['es']}" data-lang="es" aria-current="{'true' if lang=='es' else 'false'}">ES</a><a class="lang" href="{links['en']}" data-lang="en" aria-current="{'true' if lang=='en' else 'false'}">EN</a><a class="lang" href="{links['pt']}" data-lang="pt" aria-current="{'true' if lang=='pt' else 'false'}">PT</a></div><button class="theme-toggle" type="button" data-theme data-dark-label="{darklabel}" data-light-label="{lightlabel}" aria-label="{darklabel}" aria-pressed="false"><span data-theme-icon aria-hidden="true">☾</span><span class="theme-copy">{darklabel}</span></button></div><a class="btn top-cta" href="{FORM}" target="_blank" rel="noopener noreferrer">{l['enroll']}{ui_icon('arrow')}</a></div></div><div class="chapter-progress" aria-hidden="true"><span data-reading-progress></span></div></header>'''
def end(lang,page):
    l=LANDING['locales'][lang]
    resources_label={'es':'Recursos','en':'Resources','pt':'Recursos'}[lang]
    return f'''<footer class="footer"><div class="shell footer-grid"><div><span class="brand-name">Metodolog<b>IA</b></span><p>{T[lang]['footer']}</p></div><nav aria-label="{resources_label}"><a href="{rel_page(lang,page,lang,'deck')}">Masterclass</a><a href="{rel_page(lang,page,lang,'workbook')}">Workbook</a><a href="{rel_page(lang,page,lang,'playbook')}">Playbook</a><a href="{rel_page(lang,page,lang,'prompts')}">{esc(T[lang]['prompts'])}</a></nav><div><p>{esc(l['footer_privacy'])}</p><span class="draft-state">RENDERED_DRAFT · {lang.upper()}</span></div></div></footer><script src="{asset_base(lang,page)}assets/site.js"></script></body></html>'''

def breadcrumb(lang,page,resource):
    home=rel_page(lang,page,lang,'landing')
    label={'es':'Migas de pan','en':'Breadcrumb','pt':'Navegação estrutural'}[lang]
    class_label={'es':'Clase 01','en':'Class 01','pt':'Aula 01'}[lang]
    return f'''<nav class="breadcrumbs" aria-label="{label}"><ol><li><a href="{home}">{esc(T[lang]['route'])}</a></li><li><a href="{home}#ruta">{class_label}</a></li><li aria-current="page">{esc(resource)}</li></ol></nav>'''

def resource_catalog(lang,classes):
    labels={'masterclass':T[lang]['masterclass'],'workbook':T[lang]['workbook'],'playbook':T[lang]['playbook'],'prompts':T[lang]['prompts']}
    class_word={'es':'Clase','en':'Class','pt':'Aula'}[lang]
    path_label={'es':'Ruta del recurso','en':'Resource path','pt':'Caminho do recurso'}[lang]
    groups=[]
    for index,(course,names) in enumerate(zip(classes,RESOURCE_NAMES[lang]),1):
      cards=[]
      for kind in ('masterclass','workbook','playbook','prompts'):
        available=index==1 and kind in ('masterclass','workbook','playbook','prompts')
        href={'masterclass':'deck/index.html','workbook':'workbook/index.html','playbook':'playbook/index.html','prompts':'prompts/index.html'}[kind]
        tag='a' if available else 'article'
        link=f' href="{href}"' if available else ''
        state=T[lang]['ready'] if available else T[lang]['soon']
        cards.append(f'''<{tag} class="catalog-resource{' available' if available else ' pending'}"{link}><span class="resource-path" aria-label="{path_label}"><span>{esc(T[lang]['route'])}</span><i aria-hidden="true">/</i><span>{class_word} {index:02d}</span><i aria-hidden="true">/</i><span>{esc(labels[kind])}</span></span><strong>{esc(names[kind])}</strong><small>{esc(state)}</small></{tag}>''')
      groups.append(f'''<section class="catalog-class" aria-labelledby="catalog-class-{index}-{lang}"><header><span>{class_word} {index:02d}</span><h3 id="catalog-class-{index}-{lang}">{esc(course['title'])}</h3></header><div class="catalog-grid">{''.join(cards)}</div></section>''')
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
      class_cards.append(f'''<article class="route-stage reveal" data-route-stage data-step="0{i}"><div class="route-stage-head"><span class="route-number" aria-hidden="true">0{i}</span><span class="eyebrow">{esc(c['verb'])}</span><span class="state-pill{' active' if i==1 else ''}">{esc(c['state'])}</span></div><h3>{esc(c['title'])}</h3><p class="route-hook">{esc(c['hook'])}</p><p class="route-question">{esc(c['question'])}</p><dl><div><dt>{'Prerrequisito' if lang=='es' else 'Prerequisite' if lang=='en' else 'Pré-requisito'}</dt><dd>{esc(c['prerequisite'])}</dd></div><div><dt>{'Práctica' if lang=='es' else 'Practice' if lang=='en' else 'Prática'}</dt><dd>{esc(c['practice'])}</dd></div><div><dt>{evidence_label}</dt><dd>{esc(c['evidence'])}</dd></div></dl><div class="route-takeaway"><span>{esc(l['story_labels']['takeaway'])}</span><p>{esc(c['takeaway'])}</p></div><p class="route-punchline">{esc(c['punchline'])}</p>{video_link}<p class="route-bridge">→ {esc(c['bridge'])}</p></article>''')
    class_cards=''.join(class_cards)
    demo_steps=''.join(f'<li><span>{i:02d}</span>{esc(x)}</li>' for i,x in enumerate(l['demo_steps'],1))
    artifacts=''.join(f'<article class="evidence-chip reveal"><span>{i:02d}</span><strong>{esc(x)}</strong></article>' for i,x in enumerate(l['demo_artifacts'],1))
    outcomes=''.join(f'<article class="outcome-card reveal"><span class="state-pill{" active" if i==1 else ""}">{esc(x[1])}</span><span class="outcome-num" aria-hidden="true">0{i}</span><h3>{esc(x[0])}</h3><p>{esc(x[2])}</p></article>' for i,x in enumerate(l['outcomes'],1))
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
    playbook_card=f'''<a class="resource-cover playbook-cover reveal" href="playbook/index.html"><span class="cover-type">Playbook · A³</span><span class="cover-number" aria-hidden="true">A³</span><h3>{esc(playbook_l['title'])}</h3><p>{esc(playbook_l['lead'])}</p><strong>{esc(playbook_l['primary_cta'])}{ui_icon('arrow')}</strong></a>'''
    skill=RESOURCES['open_skill']
    skill_l=skill['locales'][lang]
    open_skill=f'''<a class="open-skill-card reveal" href="{skill['url']}" target="_blank" rel="noopener noreferrer" data-open-skill><span class="open-skill-mark" aria-hidden="true">A³</span><span class="eyebrow">{esc(skill_l['eyebrow'])}</span><h3>{esc(skill_l['title'])}</h3><p>{esc(skill_l['description'])}</p><span class="open-skill-meta">{esc(skill['tag'])} · {esc(skill['license'])}</span><strong>{esc(skill_l['cta'])}{ui_icon('external')}</strong></a>'''
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
<section class="chapter method-section" id="metodo" data-chapter="07"><div class="shell"><div class="section-head reveal"><span class="eyebrow">{esc(l['method_eyebrow'])}</span><h2 class="h2">{esc(l['method_title'])}</h2><p class="lead">{esc(l['method_lead'])}</p></div><div class="method-grid">{method}</div><div class="trust-grid"><div><h3>{esc(l['requirements_title'])}</h3><ul class="requirements">{requirements}</ul><a class="official-link" href="{help_url}" target="_blank" rel="noopener noreferrer">{'Consultar límites oficiales de NotebookLM' if lang=='es' else 'Read official NotebookLM limits' if lang=='en' else 'Consultar limites oficiais do NotebookLM'} ↗</a></div><div class="faq">{faq}</div></div><article class="letter-card ambassador-letter reveal" aria-labelledby="ambassador-letter-title"><div class="letter-mark" aria-hidden="true">M<span>IA</span></div><div class="letter-body"><span class="eyebrow">{esc(ambassadors['label'])}</span><h3 id="ambassador-letter-title">{esc(ambassadors['title'])}</h3>{ambassador_paragraphs}<footer><strong>{esc(ambassadors['signature'])}</strong><span>{esc(ambassadors['role'])}</span></footer></div></article></div></section>
<section class="chapter final-section" id="convocatoria" data-chapter="08"><div class="shell"><article class="letter-card javier-letter reveal" aria-labelledby="javier-letter-title"><a class="letter-mark portrait" href="https://github.com/JaviMontano" target="_blank" rel="noopener noreferrer" aria-label="Javier Montaño · GitHub"><img src="{base}assets/javier-montano.jpg" alt="Javier Montaño" width="460" height="460" loading="lazy" decoding="async"></a><div class="letter-body"><span class="eyebrow">{esc(javier['label'])}</span><h3 id="javier-letter-title">{esc(javier['title'])}</h3>{javier_paragraphs}<footer><strong>{esc(javier['signature'])}</strong><span>{esc(javier['role'])}</span></footer></div></article><div class="final-grid"><div><span class="eyebrow">{esc(l['final_eyebrow'])}</span><h2 class="h2">{esc(l['final_title'])}</h2><p class="lead">{esc(l['final_lead'])}</p><div class="actions"><a class="btn" href="{FORM}" target="_blank" rel="noopener noreferrer">{esc(l['enroll'])} →</a><a class="btn secondary" href="workbook/index.html">{esc(l['workbook_cta'])}</a></div><p class="form-note">{esc(l['form_note'])}</p></div><div class="final-mark" aria-hidden="true"><span>N</span><strong>0</strong><i></i></div></div></div></section>
</main><script type="application/ld+json">{course_json}</script>'''+end(lang,'landing')

W={
'es':{'title':'Workbook · Aprende a aprender con NotebookLM','lead':'Tres hojas para empezar en clase, profundizar y consolidar de forma autónoma.','tabs':['En sesión','Profundización','Consolidación'],'sheet1':'Cinco pasos esenciales','sheet1p':'Avanza en orden. La persona define propósito, revisa fuentes y decide cuándo la evidencia es suficiente.','sheet2':'De la base a una práctica defendible','sheet2p':'Prompts 6–10 para crear, aplicar, evaluar y ensayar sin salir de las fuentes.','sheet3':'Demuestra, transfiere y decide','sheet3p':'La consolidación exige evidencia y explicación propia; no basta con que la respuesta suene bien.','copy':'Copiar','open':'Abrir NotebookLM ↗','official':'Ayuda oficial ↗','expected':'Evidencia esperada','checks':['Puedo explicar el propósito de mi Notebook en una frase.','Puedo nombrar dos fuentes decisivas y un vacío aceptado.','Puedo mostrar una respuesta con citas y revisar su soporte.','Puedo enseñar el proceso a otra persona sin leer el prompt.'],'states':['Completado: existe evidencia revisable.','Pendiente: sé cuál es el siguiente paso.','coverage_gap: falta fuente, contexto o prueba.'],'challenge':'Reto autónomo','challengep':'Crea un Notebook para una decisión real, ejecuta el ciclo 1–5 y usa un prompt de profundidad. Entrega un mapa de fuentes, el veredicto de suficiencia y una explicación de 3 minutos.','note':'NotebookLM puede responder con base en las fuentes seleccionadas y mostrar citas; esas ayudas no garantizan precisión. Revisa siempre la fuente y conserva tu criterio. Deep Research exige 18 años o más y su disponibilidad puede variar según cuenta, plan y superficie; consulta la ayuda oficial.'},
'en':{'title':'Workbook · Learn how to learn with NotebookLM','lead':'Three sheets to start in class, go deeper and consolidate independently.','tabs':['In session','Deepening','Consolidation'],'sheet1':'Five essential steps','sheet1p':'Move in order. You define purpose, review sources and decide when evidence is sufficient.','sheet2':'From a source base to defensible practice','sheet2p':'Prompts 6–10 to create, apply, assess and rehearse without leaving the sources.','sheet3':'Demonstrate, transfer and decide','sheet3p':'Consolidation requires evidence and your own explanation; fluent output is not enough.','copy':'Copy','open':'Open NotebookLM ↗','official':'Official help ↗','expected':'Expected evidence','checks':['I can explain my Notebook purpose in one sentence.','I can name two decisive sources and one accepted gap.','I can show a cited answer and inspect its support.','I can teach the process without reading the prompt.'],'states':['Complete: reviewable evidence exists.','Pending: the next action is clear.','coverage_gap: a source, context or test is missing.'],'challenge':'Independent challenge','challengep':'Create a Notebook for a real decision, run steps 1–5 and use one deepening prompt. Deliver a source map, a sufficiency verdict and a three-minute explanation.','note':'NotebookLM can answer from selected sources and show citations; these aids do not guarantee accuracy. Inspect the source and keep human judgment. Deep Research requires users to be 18 or older and availability can vary by account, plan and surface; check official help.'},
'pt':{'title':'Workbook · Aprenda a aprender com NotebookLM','lead':'Três folhas para começar em aula, aprofundar e consolidar com autonomia.','tabs':['Em aula','Aprofundamento','Consolidação'],'sheet1':'Cinco passos essenciais','sheet1p':'Avance em ordem. A pessoa define o propósito, revisa fontes e decide quando a evidência é suficiente.','sheet2':'Da base a uma prática defensável','sheet2p':'Prompts 6–10 para criar, aplicar, avaliar e ensaiar sem sair das fontes.','sheet3':'Demonstre, transfira e decida','sheet3p':'A consolidação exige evidência e explicação própria; não basta uma resposta fluente.','copy':'Copiar','open':'Abrir NotebookLM ↗','official':'Ajuda oficial ↗','expected':'Evidência esperada','checks':['Consigo explicar o propósito do Notebook em uma frase.','Consigo nomear duas fontes decisivas e uma lacuna aceita.','Consigo mostrar uma resposta citada e revisar seu suporte.','Consigo ensinar o processo sem ler o prompt.'],'states':['Concluído: existe evidência revisável.','Pendente: o próximo passo está claro.','coverage_gap: falta fonte, contexto ou teste.'],'challenge':'Desafio autônomo','challengep':'Crie um Notebook para uma decisão real, execute os passos 1–5 e use um prompt de aprofundamento. Entregue mapa de fontes, veredito de suficiência e explicação de três minutos.','note':'O NotebookLM pode responder a partir das fontes selecionadas e mostrar citações; isso não garante precisão. Revise a fonte e preserve o critério humano. Deep Research exige 18 anos ou mais e a disponibilidade pode variar por conta, plano e interface; consulte a ajuda oficial.'}}
W['es'].update(lead='Tres rutas prácticas.',sheet1='Cinco pasos',sheet1p='Define propósito, revisa fuentes y decide cuándo la evidencia es suficiente.',sheet2='Práctica guiada',sheet2p='Prompts 6–10 para crear, aplicar, evaluar y ensayar desde las fuentes.',sheet3='Transfiere y decide',sheet3p='Consolida con evidencia y explicación propia.')
W['en'].update(lead='Three practice routes.',sheet1='Five steps',sheet1p='Define purpose, review sources and decide when evidence is sufficient.',sheet2='Guided practice',sheet2p='Prompts 6–10 to create, apply, assess and rehearse from the sources.',sheet3='Transfer and decide',sheet3p='Consolidate with evidence and your own explanation.')
W['pt'].update(lead='Três rotas práticas.',sheet1='Cinco passos',sheet1p='Defina propósito, revise fontes e decida quando a evidência é suficiente.',sheet2='Prática guiada',sheet2p='Prompts 6–10 para criar, aplicar, avaliar e ensaiar a partir das fontes.',sheet3='Transfira e decida',sheet3p='Consolide com evidência e explicação própria.')

FORMAT_COPY={
  'es':{'parameters':'# Parámetros','inputs':'# Inputs','task':'# Tarea','workflow':'# Flujo','guardrails':'# Guardrails','output':'# Salida esperada','dod':'# Definition of Done','role':'# Rol','objective':'# Objetivo','base':'# Prompt base','adjust':'Completa o ajusta los valores entre corchetes antes de ejecutar.'},
  'en':{'parameters':'# Parameters','inputs':'# Inputs','task':'# Task','workflow':'# Workflow','guardrails':'# Guardrails','output':'# Expected output','dod':'# Definition of Done','role':'# Role','objective':'# Objective','base':'# Base prompt','adjust':'Complete or adjust values in brackets before running.'},
  'pt':{'parameters':'# Parâmetros','inputs':'# Inputs','task':'# Tarefa','workflow':'# Fluxo','guardrails':'# Guardrails','output':'# Saída esperada','dod':'# Definition of Done','role':'# Papel','objective':'# Objetivo','base':'# Prompt base','adjust':'Complete ou ajuste os valores entre colchetes antes de executar.'}}

def structured_variants(lang,title,natural,spec=None):
  c=FORMAT_COPY[lang]
  if spec is None:
    spec={
      'role':('Asistente MetodologIA orientado a evidencia' if lang=='es' else 'Evidence-oriented MetodologIA assistant' if lang=='en' else 'Assistente MetodologIA orientado a evidências'),
      'objective':title,
      'parameters':[['profundidad','operativa'],['formato','estructurado'],['fuentes','solo fuentes disponibles'],['vacíos','declarar coverage_gap']] if lang=='es' else [['depth','operational'],['format','structured'],['sources','available sources only'],['gaps','declare coverage_gap']] if lang=='en' else [['profundidade','operacional'],['formato','estruturado'],['fontes','somente fontes disponíveis'],['lacunas','declarar coverage_gap']],
      'workflow':[natural],
      'guardrails':(['No inventar fuentes, citas o capacidades','Separar evidencia, inferencia y dato faltante','Mantener la decisión final en la persona'] if lang=='es' else ['Do not invent sources, citations or capabilities','Separate evidence, inference and missing data','Keep the final decision with the person'] if lang=='en' else ['Não inventar fontes, citações ou capacidades','Separar evidência, inferência e dado ausente','Manter a decisão final com a pessoa']),
      'output':([title,'Fuentes o límites utilizados','Siguiente decisión verificable'] if lang=='es' else [title,'Sources or boundaries used','Next verifiable decision'] if lang=='en' else [title,'Fontes ou limites utilizados','Próxima decisão verificável']),
      'dod':('El entregable responde al propósito, permite revisar evidencia y declara límites.' if lang=='es' else 'The deliverable answers the purpose, supports evidence review and states boundaries.' if lang=='en' else 'A entrega responde ao propósito, permite revisar evidências e declara limites.')}
  params='\n'.join(f'{name} = {default}' for name,default in spec['parameters'])
  workflow='\n'.join(f'{i}. {step}' for i,step in enumerate(spec['workflow'],1))
  guardrails='\n'.join(f'- {item}' for item in spec['guardrails'])
  output='\n'.join(f'- {item}' for item in spec['output'])
  input_line=('Dictado: <copia y pega tu dictado, instrucción o prompt aquí>' if lang=='es' else 'Dictation: <paste your dictation, instruction or prompt here>' if lang=='en' else 'Ditado: <cole seu ditado, instrução ou prompt aqui>')
  uses_dump='{{BRAIN_DUMP}}' in natural
  inputs=f'{input_line}\n\n{{{{BRAIN_DUMP}}}}' if uses_dump else c['adjust']
  parameter=f"{c['parameters']}\n{params}\n\n{c['inputs']}\n{inputs}\n\n{c['task']}\n{spec['objective']}\n\n{c['workflow']}\n{workflow}\n\n{c['guardrails']}\n{guardrails}\n\n{c['output']}\n{output}"
  spec_text=f"# SPEC MetodologIA\nversion: 1.0\nstatus: executable\n\n{c['role']}\n{spec['role']}\n\n{c['objective']}\n{spec['objective']}\n\n{c['inputs']}\n{inputs}\n\n{c['workflow']}\n{workflow}\n\n{c['guardrails']}\n{guardrails}\n\n{c['output']}\n{output}\n\n{c['dod']}\n{spec['dod']}"
  pair=f"# system\n{spec['role']}\n\n{c['guardrails']}\n{guardrails}\n\n{c['dod']}\n{spec['dod']}\n\n# user\n{c['inputs']}\n{inputs}\n\n{c['task']}\n{spec['objective']}\n\n{c['workflow']}\n{workflow}\n\n{c['output']}\n{output}"
  return {'natural':natural,'parameters':parameter,'spec':spec_text,'pair':pair}

def prompt_formats_markup(lang,group_id,variants,convention,brain_input=None):
  tabs=[]; panels=[]
  items={item['key']:item for item in convention['items']}
  for index,key in enumerate(('natural','parameters','spec','pair')):
    panel_id=f'{group_id}-{key}'
    item=items[key]
    tabs.append(f'<button type="button" role="tab" tabindex="{0 if index==0 else -1}" aria-selected="{str(index==0).lower()}" aria-label="{esc(item["level"])}" aria-controls="{panel_id}" data-prompt-format="{key}" data-level-number="{index+1}"><span aria-hidden="true">{index+1}</span></button>')
    panels.append(f'<details class="prompt-level-fallback"{" open" if index==0 else ""}><summary><span aria-hidden="true">{index+1}</span><span class="sr-only">{esc(item["level"])}</span></summary><pre class="prompt-format-panel" id="{panel_id}" role="tabpanel" aria-label="{esc(item["level"])}" data-prompt-template>{esc(variants[key])}</pre></details>')
  brain_attr=f' data-brain-input="{brain_input}"' if brain_input else ''
  copy_attr=f' data-brain-copy="{group_id}"{brain_attr}' if brain_input else f' data-format-copy="{group_id}"'
  copy_icon='<svg aria-hidden="true" viewBox="0 0 24 24"><rect x="8" y="8" width="11" height="11" rx="2"></rect><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"></path></svg>'
  copy_aria=f"{convention['copy']} · {convention['items'][0]['level']}"
  return f'''<div class="prompt-library" data-prompt-library="{group_id}" data-active-level="1"><div class="prompt-format-tabs" role="tablist" aria-label="{esc(convention['tablist'])}">{''.join(tabs)}</div><div class="prompt-format-panels">{''.join(panels)}</div><div class="prompt-library-actions"><button class="copy prompt-format-copy" type="button" aria-label="{esc(copy_aria)}"{copy_attr} data-copy-label="{esc(convention['copy'])}" data-copied-label="{esc(convention['copied'])}">{copy_icon}</button><span class="prompt-copy-status sr-only" role="status" aria-live="polite"></span></div></div>'''

def level_convention_markup(lang):
  return ''

def prompt_cards(lang,start,end):
  w=W[lang]; out=[]
  deep_meta={
    'es':[
      ('Cuando necesitas una pieza','tipo, audiencia, resultado','pieza + fuentes + decisiones','no sumar hechos externos','Un memo ejecutivo citado'),
      ('Cuando buscas oportunidades','rol, equipo, contexto','10 casos priorizados','no inventar ROI','Un piloto de 7 días'),
      ('Cuando debes comprobar dominio','tema, nivel, fuentes','diagnóstico + práctica','no evaluar fuera de la base','Quiz aplicado de cuatro niveles'),
      ('Antes de una conversación exigente','audiencia, resultado, tiempo','ensayo + mejoras','no simular certeza','QBR con preguntas hostiles'),
      ('Cuando la base ya es suficiente','propósito, usuario, límites','configuración + 10 inicios','no inventar capacidades','Coach basado en fuentes')],
    'en':[
      ('When you need a content piece','type, audience, outcome','piece + sources + decisions','do not add external facts','A cited executive memo'),
      ('When exploring opportunities','role, team, context','10 ranked use cases','do not invent ROI','A seven-day pilot'),
      ('When checking mastery','topic, level, sources','diagnosis + practice','do not assess beyond the base','A four-level applied quiz'),
      ('Before a demanding conversation','audience, outcome, time','rehearsal + improvements','do not simulate certainty','A QBR with hostile questions'),
      ('When the base is sufficient','purpose, user, limits','configuration + 10 starters','do not invent capabilities','A source-grounded coach')],
    'pt':[
      ('Quando precisa de uma peça','tipo, público, resultado','peça + fontes + decisões','não somar fatos externos','Um memo executivo citado'),
      ('Quando busca oportunidades','papel, equipe, contexto','10 casos priorizados','não inventar ROI','Um piloto de sete dias'),
      ('Quando verifica domínio','tema, nível, fontes','diagnóstico + prática','não avaliar além da base','Quiz aplicado de quatro níveis'),
      ('Antes de conversa exigente','público, resultado, tempo','ensaio + melhorias','não simular certeza','QBR com perguntas hostis'),
      ('Quando a base é suficiente','propósito, usuário, limites','configuração + 10 inícios','não inventar capacidades','Coach baseado em fontes')]}
  for n in range(start,end+1):
    title,text=prompt_for(lang,n,*PROMPTS_ES[n-1]); pid=f'p{n}-{lang}'
    variants=structured_variants(lang,title,text)
    format_ui=prompt_formats_markup(lang,pid,variants,ADVANCED['locales'][lang]['level_convention'])
    flow=('Entradas: tema, propósito y contexto · Acción: ejecutar y revisar · Salida: respuesta citada · Comprobación: contrastar con la fuente · Siguiente: decidir si avanzar.' if lang=='es' else 'Inputs: topic, purpose and context · Action: run and review · Output: cited response · Check: inspect the source · Next: decide whether to continue.' if lang=='en' else 'Entradas: tema, propósito e contexto · Ação: executar e revisar · Saída: resposta citada · Verificação: conferir a fonte · Próximo: decidir se avança.')
    meta=''
    if n>=6:
      when,inputs,output,limits,example=deep_meta[lang][n-6]
      ml={'es':('Entradas','Salida','Límites','Ejemplo'),'en':('Inputs','Output','Limits','Example'),'pt':('Entradas','Saída','Limites','Exemplo')}[lang]
      meta=f'<p><strong>{esc(when)}</strong><br>{ml[0]}: {esc(inputs)} · {ml[1]}: {esc(output)} · {ml[2]}: {esc(limits)} · {ml[3]}: {esc(example)}</p>'
    out.append(f'''<article class="card step" id="step-{n}"><span class="step-num">{n}</span><div><h3 class="h3">{esc(title)}</h3><p>{w['expected']}: {esc(('decisión y evidencia citada' if lang=='es' else 'a decision and cited evidence' if lang=='en' else 'uma decisão e evidência citada'))}.</p><p><strong>{esc(flow)}</strong></p>{meta}</div><div class="prompt"><div class="prompt-head"><span>Prompt {n}</span></div>{format_ui}</div></article>''')
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
  guide=f'''<section class="workbook-guide" aria-labelledby="guide-title-{lang}"><div class="section-head"><span class="eyebrow">00 · {esc(advanced['guide_title'])}</span><h2 class="h2" id="guide-title-{lang}">{esc(advanced['guide_title'])}</h2><p class="lead">{esc(advanced['guide_body'])}</p></div><ol class="guide-steps">{guide_steps}</ol><aside class="provider-notice"><span aria-hidden="true">i</span><div><strong>{esc('Condiciones de uso' if lang=='es' else 'Usage conditions' if lang=='en' else 'Condições de uso')}</strong><p>{esc(advanced['provider_notice'])}</p><nav aria-label="{esc('Fuentes oficiales' if lang=='es' else 'Official sources' if lang=='en' else 'Fontes oficiais')}">{provider_link_html}</nav></div></aside></section>'''
  brain_prompt_cards=[]
  for i,(title,template) in enumerate(advanced['brain_prompts'],1):
    pid=f'brain-prompt-{lang}-{i}'
    variants=structured_variants(lang,title,template,advanced['brain_prompt_specs'][i-1])
    format_ui=prompt_formats_markup(lang,pid,variants,advanced['level_convention'],f'brain-dump-{lang}')
    brain_prompt_cards.append(f'''<article class="brain-prompt-card"><header><span>0{i}</span><h3>{esc(title)}</h3></header><div class="prompt"><div class="prompt-head"><span>Prompt 0{i}</span></div>{format_ui}</div></article>''')
  prep_eyebrow=('Preparación · una entrada, tres movimientos' if lang=='es' else 'Preparation · one input, three moves' if lang=='en' else 'Preparação · uma entrada, três movimentos')
  brain=f'''<section class="brain-section" aria-labelledby="brain-title-{lang}"><div class="section-head"><span class="eyebrow">{esc(prep_eyebrow)}</span><h2 class="h2" id="brain-title-{lang}">{esc(advanced['brain_title'])}</h2><p class="lead">{esc(advanced['brain_body'])}</p></div><label class="brain-input"><strong>{esc(advanced['brain_label'])}</strong><textarea id="brain-dump-{lang}" rows="8" placeholder="{esc(advanced['brain_placeholder'])}" data-brain-dump></textarea><small>{esc(advanced['brain_dictation'])}</small><span class="brain-status" data-brain-status aria-live="polite" data-empty-message="{esc(advanced['brain_empty'])}"></span></label><div class="brain-prompt-grid">{''.join(brain_prompt_cards)}</div></section>'''
  use_cases=''.join(f'<li><span>{i:02d}</span><p>{esc(item)}</p></li>' for i,item in enumerate(advanced['use_cases'],1))
  cases=f'''<section class="use-cases" aria-labelledby="cases-title-{lang}"><div class="section-head"><span class="eyebrow">Casos de uso · destino provisional</span><h2 class="h2" id="cases-title-{lang}">{esc(advanced['use_cases_title'])}</h2><p class="lead">{esc(advanced['use_cases_body'])}</p></div><ol>{use_cases}</ol></section>'''
  start=f'''<section class="workshop-start"><div class="section-head"><span class="eyebrow">00 · {esc(advanced['start_label'])}</span><h2 class="h2">{esc(advanced['start_title'])}</h2><p class="lead">{esc(advanced['start_body'])}</p></div><div class="access-grid">{access_cards}</div></section>'''
  route_map=f'''<section class="workbook-routes"><div class="section-head"><span class="eyebrow">05 · Aprender · Aprehender · Evolucionar</span><h2 class="h2">{esc(advanced['routes_title'])}</h2><p class="route-duration-note">{esc(advanced['route_note'])}</p></div><div class="route-choice-grid three">{routes}</div></section>'''
  concepts=f'''<section class="concept-section"><div class="concept-grid"><article><span>01</span><h2>{esc(advanced['assistant_title'])}</h2><p>{esc(advanced['assistant_body'])}</p></article><article><span>02</span><h2>{esc(advanced['skill_title'])}</h2><p>{esc(advanced['skill_body'])}</p></article></div></section>'''
  expert=f'''<section class="expert-section"><div class="section-head"><span class="eyebrow">Ruta experta · Spec → Build → Verify</span><h2 class="h2">{esc(advanced['expert_title'])}</h2></div><ol class="expert-steps">{expert_steps}</ol><div class="expert-tools"><article><h3>{esc(advanced['setup_title'])}</h3><p>{esc(advanced['setup_body'])}</p><div class="actions"><a class="btn secondary" href="{ANTIGRAVITY}" target="_blank" rel="noopener noreferrer">Antigravity ↗</a><a class="text-link" href="{ANTIGRAVITY_GUIDE}" target="_blank" rel="noopener noreferrer">Google Codelab ↗</a></div></article><article class="warning-card"><h3>NotebookLM MCP</h3><p>{esc(advanced['mcp_warning'])}</p><div class="actions"><a class="btn secondary" href="{NOTEBOOK_MCP}" target="_blank" rel="noopener noreferrer">GitHub · MCP ↗</a><a class="text-link" href="{REFERENCE_WORKBOOK}" target="_blank" rel="noopener noreferrer">Workbook original ↗</a></div></article></div></section>'''
  prep=f'''<section class="workbook-prep"><div class="section-head"><span class="eyebrow">Antes de continuar</span><h2 class="h2">{esc(intro['prepare'])}</h2></div><div class="prep-grid">{prep_columns}</div><p class="fac-note"><strong>{setup}</strong><br>{w['note']}</p></section>'''
  return head(lang,w['title'],'workbook')+f'''<main id="main" class="workbook-v2"><section class="doc-hero workbook-hero"><div class="shell">{breadcrumb(lang,'workbook',T[lang]['workbook'])}</div><div class="shell workbook-hero-grid"><div class="workbook-hero-copy"><span class="eyebrow">MetodologIA · {esc(intro['eyebrow'])}</span><h1 class="h1">{w['title']}</h1><p class="lead">{esc(intro['promise'])}</p></div><aside class="workbook-outcome"><span>{esc(intro['outcome'])}</span><strong>{esc(intro['outcome_body'])}</strong></aside><nav class="workbook-hero-actions" aria-label="Workbook"><a class="btn" href="#brain-title-{lang}">{esc(intro['start'])} →</a><a class="text-link" href="../deck/index.html#page-1">{back} →</a><button class="print-link" type="button" onclick="window.print()">PDF / Print</button></nav></div></section><div class="shell workbook-flow">{guide}{brain}{start}{prep}{cases}<section class="workbook-sheets"><div class="section-head"><span class="eyebrow">01–03 · Workbook</span><h2 class="h2">{esc(w['lead'])}</h2></div>{level_convention_markup(lang)}<div class="sheet-tabs" role="tablist" aria-label="Workbook"><button class="tab" role="tab" aria-selected="true" aria-controls="sheet-session" data-sheet="session">1 · {w['tabs'][0]} · 5</button><button class="tab" role="tab" aria-selected="false" aria-controls="sheet-depth" data-sheet="depth">2 · {w['tabs'][1]} · 10</button><button class="tab" role="tab" aria-selected="false" aria-controls="sheet-consolidation" data-sheet="consolidation">3 · {w['tabs'][2]}</button></div><section class="sheet" id="sheet-session" role="tabpanel"><div class="section-head"><span class="eyebrow">01 · {w['tabs'][0]}</span><h2 class="h2">{w['sheet1']}</h2><p class="lead">{w['sheet1p']}</p></div><div class="step-list">{prompt_cards(lang,1,5)}</div>{surfaces}<h3 class="h3">{roles_title}</h3>{roles_table}</section><section class="sheet" id="sheet-depth" role="tabpanel" hidden><div class="section-head"><span class="eyebrow">02 · {w['tabs'][1]}</span><h2 class="h2">{w['sheet2']}</h2><p class="lead">{w['sheet2p']}</p><p class="fac-note"><strong>{rubric}</strong></p></div>{rubric_table}<div class="step-list">{prompt_cards(lang,6,10)}</div><p class="fac-note"><strong>{gate}</strong></p></section><section class="sheet" id="sheet-consolidation" role="tabpanel" hidden><div class="section-head"><span class="eyebrow">03 · {w['tabs'][2]}</span><h2 class="h2">{w['sheet3']}</h2><p class="lead">{w['sheet3p']}</p></div><article class="card evidence"><h3 class="h3">{w['challenge']}</h3><p>{w['challengep']}</p><p><strong>{transfer}</strong></p><div class="checklist">{checks}</div></article><div class="rubric" style="margin-top:1rem">{states}</div></section></section>{route_map}{concepts}{expert}</div></main>'''+end(lang,'workbook')

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
  toc=''.join(f'<a href="#{esc(section["id"])}"><span>{index:02d}</span>{esc(section["title"])}</a>' for index,section in enumerate(p['sections'],1))
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
  return head(lang,p['meta_title'],'playbook')+f'''<main id="main" class="playbook-v1"><section class="playbook-hero"><div class="shell">{breadcrumb(lang,'playbook',T[lang]['playbook'])}</div><div class="shell playbook-hero-grid"><div class="playbook-hero-copy"><span class="eyebrow">{esc(p['eyebrow'])}</span><h1>{hero_title}</h1><p class="lead">{esc(p['lead'])}</p><div class="actions"><a class="btn" href="#intro">{esc(p['primary_cta'])}{ui_icon('arrow')}</a><a class="btn secondary" href="{skill['url']}" target="_blank" rel="noopener noreferrer">{esc(p['secondary_cta'])}{ui_icon('external')}</a></div><dl class="playbook-hero-facts"><div><dt>{journey[0]}</dt><dd>{journey[1]}</dd></div><div><dt>A³</dt><dd>{journey[2]}</dd></div></dl></div><div class="playbook-mark" aria-hidden="true"><span>A</span><strong>³</strong><i></i><b>{journey[3]}</b></div></div></section><div class="shell playbook-layout"><aside class="playbook-toc"><strong>{esc(p['read'])}</strong><nav>{toc}</nav></aside><div class="playbook-content"><section class="founders-letter" id="founders" data-letter-label="{esc(journey[4])}"><div class="founders-letter-copy"><div class="founders-letter-heading"><span class="eyebrow">{esc(p['founder_label'])}</span><h2>{esc(p['founder_title'])}</h2></div><div class="founders-letter-body">{letters}</div></div><ul>{founder_cards}</ul></section>{''.join(sections)}<section class="playbook-close" id="close"><span class="eyebrow">MetodologIA · A³</span><h2>{esc(p['close_title'])}</h2><p>{esc(p['close_lead'])}</p><div class="actions"><a class="btn" href="../workbook/index.html">{esc(p['close_primary'])}{ui_icon('arrow')}</a><a class="btn secondary" href="../deck/index.html">{esc(p['close_secondary'])}{ui_icon('arrow')}</a></div><small>{esc(skill['version'])} · {esc(skill['license'])}</small></section></div></div></main>'''+end(lang,'playbook')

def prompt_library_page(lang):
  p=PROMPT_LIBRARY['locales'][lang]
  hero_cta={'es':'Ver 10 prompts','en':'View 10 prompts','pt':'Ver 10 prompts'}[lang]
  direct=[]; meta=[]
  for item in p['items']:
    group=f'library-{lang}-{item["id"].lower()}'
    formats=structured_variants(lang,item['title'],item['prompt'])
    controls=prompt_formats_markup(lang,group,formats,ADVANCED['locales'][lang]['level_convention'])
    card=f'''<article class="library-prompt-card" id="prompt-{item['id'].lower()}" data-library-prompt data-prompt-kind="{'meta' if item['id'].startswith('M') else 'direct'}"><header><span class="library-prompt-number" aria-hidden="true">{esc(item['id'])}</span><div><span class="eyebrow">{esc(item['phase'])}</span><h3>{esc(item['title'])}</h3><p>{esc(item['purpose'])}</p></div></header><dl class="library-prompt-brief"><div><dt>{esc(p['use'])}</dt><dd>{esc(item['when'])}</dd></div><div><dt>{esc(p['example'])}</dt><dd>{esc(item['example'])}</dd></div><div><dt>{esc(p['evidence'])}</dt><dd>{esc(item['evidence'])}</dd></div></dl>{controls}</article>'''
    (meta if item['id'].startswith('M') else direct).append(card)
  skill=RESOURCES['open_skill']
  return head(lang,p['meta_title'],'prompts')+f'''<main id="main" class="prompt-library-page"><section class="prompt-library-hero"><div class="shell">{breadcrumb(lang,'prompts',T[lang]['prompts'])}<div class="prompt-library-hero-grid"><div><span class="eyebrow">{esc(p['eyebrow'])}</span><h1>{esc(p['title'])}</h1><p class="lead">{esc(p['lead'])}</p><div class="actions"><a class="btn" href="#directos">{esc(hero_cta)}{ui_icon('arrow')}</a><a class="btn secondary" href="../playbook/index.html">{esc(p['back'])}{ui_icon('arrow')}</a></div></div><div class="prompt-library-score" aria-label="{esc(p['eyebrow'])}"><strong>10</strong><span>+</span><strong>4</strong><small>A³ · MetodologIA</small></div></div></div></section><section class="prompt-library-section shell" id="directos"><div class="section-head"><span class="eyebrow">{esc(p['direct_label'])}</span><h2 class="h2">{esc(p['direct_title'])}</h2></div><div class="library-prompt-list">{''.join(direct)}</div></section><section class="prompt-library-section prompt-library-meta" id="metaprompts"><div class="shell"><div class="section-head"><span class="eyebrow">{esc(p['meta_label'])}</span><h2 class="h2">{esc(p['meta_title_section'])}</h2></div><div class="library-prompt-list">{''.join(meta)}</div><aside class="prompt-library-source"><p>{esc(p['skill_note'])}</p><a class="btn secondary" href="{skill['url']}" target="_blank" rel="noopener noreferrer">{esc(skill['locales'][lang]['cta'])}{ui_icon('external')}</a><a class="btn" href="../workbook/index.html">{esc(p['workbook'])}{ui_icon('arrow')}</a></aside></div></section></main>'''+end(lang,'prompts')

S={
'es':[('Bienvenida','IA: qué está pasando y cómo sacarle provecho','Hoy no vienes a aprender botones. Vienes a construir criterio y una práctica basada en fuentes.'),('Resultado','Al final podrás demostrar esto','Explicar qué puede aportar la IA, construir una base en NotebookLM y decidir cuándo confiar, verificar o detenerte.'),('Acuerdo','La IA propone. Tú respondes.','Ninguna respuesta sustituye la revisión de fuentes, el contexto ni la decisión humana.'),('Panorama','¿Qué cambió?','La IA generativa volvió conversacionales tareas de búsqueda, síntesis, creación y apoyo a decisiones.'),('Mapa','Modelo, producto y flujo no son lo mismo','Distingue la capacidad base, la interfaz que usas y el proceso donde produces un resultado.'),('Criterio','Fluidez no es evidencia','Una respuesta convincente puede estar incompleta. La pregunta útil es: ¿qué fuente sostiene esta afirmación?'),('Aprender','Aprender a aprender con IA','Define un propósito, reúne fuentes, detecta vacíos, practica recuperación y explica con tus palabras.'),('NotebookLM','Una conversación anclada en tus fuentes','NotebookLM ayuda a consultar fuentes seleccionadas y revisar citas. Tú decides qué importar y cómo usarlo.'),('Práctica 1','Construye la primera base','Abre la hoja En sesión, paso 1. Declara tema, decisión, contexto y audiencia.'),('Práctica 2','Audita antes de acumular','Paso 2. Busca cobertura, tensiones, ambigüedad, calidad, vigencia y sesgo.'),('Práctica 3','Investiga el vacío que importa','Paso 3. Convierte el hallazgo prioritario en investigación a medida.'),('Práctica 4','Detente con criterio','Paso 4. Compara la mejora y decide: base suficiente o repetir investigación.'),('Práctica 5','Activa profesor, asesor o coach','Paso 5. Elige un rol y exige citas, límites y siguiente paso.'),('Puesta en común','¿Qué cambió entre la primera y la segunda base?','Comparte una fuente decisiva, una tensión y un vacío que aceptaste.'),('Transferencia','Llévalo a una decisión real','Elige una reunión, propuesta, aprendizaje o problema donde una base verificable reduzca improvisación.'),('Profundiza','La práctica continúa','La hoja 2 convierte la base en contenido, casos, evaluación, simulación y configuración.'),('Consolida','Demuestra que puedes hacerlo sin guía','La hoja 3 pide evidencia, teach-back y transferencia a otro contexto.'),('Cierre','Tu siguiente paso en 24 horas','Crea o mejora un Notebook, registra el veredicto de suficiencia y explica el proceso en tres minutos.')],
'en':[('Welcome','AI: what is happening and how to benefit','You are not here to memorize buttons. You are here to build judgment and source-grounded practice.'),('Outcome','By the end you can demonstrate this','Explain what AI can contribute, build a NotebookLM source base and decide when to trust, verify or stop.'),('Agreement','AI proposes. You remain accountable.','No answer replaces source review, context or human decision.'),('Landscape','What changed?','Generative AI made search, synthesis, creation and decision support conversational.'),('Map','Model, product and workflow are different','Separate the base capability, the interface you use and the process that produces an outcome.'),('Judgment','Fluency is not evidence','A persuasive answer can be incomplete. Ask: which source supports this claim?'),('Learning','Learn how to learn with AI','Set a purpose, gather sources, find gaps, retrieve from memory and explain in your own words.'),('NotebookLM','A conversation grounded in your sources','NotebookLM helps query selected sources and inspect citations. You decide what to import and how to use it.'),('Practice 1','Build the first source base','Open In session, step 1. State topic, decision, context and audience.'),('Practice 2','Audit before accumulating','Step 2. Inspect coverage, tensions, ambiguity, quality, recency and bias.'),('Practice 3','Research the gap that matters','Step 3. Turn the priority finding into targeted research.'),('Practice 4','Stop with judgment','Step 4. Compare improvement and choose: sufficient base or repeat.'),('Practice 5','Activate teacher, advisor or coach','Step 5. Choose a role and require citations, boundaries and a next step.'),('Debrief','What changed between the first and second base?','Share one decisive source, one tension and one accepted gap.'),('Transfer','Take it to a real decision','Choose a meeting, proposal, learning goal or problem where a verifiable source base reduces improvisation.'),('Go deeper','Practice continues','Sheet 2 turns the base into content, use cases, assessment, simulation and configuration.'),('Consolidate','Prove you can do it without guidance','Sheet 3 asks for evidence, teach-back and transfer to another context.'),('Close','Your next step within 24 hours','Create or improve a Notebook, record the sufficiency verdict and explain the process in three minutes.')],
'pt':[('Boas-vindas','IA: o que está acontecendo e como aproveitar','Você não veio memorizar botões. Veio construir critério e prática baseada em fontes.'),('Resultado','Ao final você poderá demonstrar isto','Explicar a contribuição da IA, construir uma base no NotebookLM e decidir quando confiar, verificar ou parar.'),('Acordo','A IA propõe. Você responde.','Nenhuma resposta substitui a revisão das fontes, o contexto ou a decisão humana.'),('Panorama','O que mudou?','A IA generativa tornou conversacionais tarefas de busca, síntese, criação e apoio à decisão.'),('Mapa','Modelo, produto e fluxo são diferentes','Separe a capacidade base, a interface usada e o processo que produz um resultado.'),('Critério','Fluência não é evidência','Uma resposta convincente pode estar incompleta. Pergunte: qual fonte sustenta esta afirmação?'),('Aprender','Aprender a aprender com IA','Defina propósito, reúna fontes, detecte lacunas, recupere da memória e explique com suas palavras.'),('NotebookLM','Uma conversa ancorada em suas fontes','O NotebookLM ajuda a consultar fontes selecionadas e revisar citações. Você decide o que importar e como usar.'),('Prática 1','Construa a primeira base','Abra Em aula, passo 1. Declare tema, decisão, contexto e público.'),('Prática 2','Audite antes de acumular','Passo 2. Busque cobertura, tensões, ambiguidade, qualidade, atualidade e viés.'),('Prática 3','Pesquise a lacuna importante','Passo 3. Transforme o achado prioritário em pesquisa sob medida.'),('Prática 4','Pare com critério','Passo 4. Compare a melhoria e decida: base suficiente ou repetir.'),('Prática 5','Ative professor, assessor ou coach','Passo 5. Escolha um papel e exija citações, limites e próximo passo.'),('Discussão','O que mudou entre a primeira e a segunda base?','Compartilhe uma fonte decisiva, uma tensão e uma lacuna aceita.'),('Transferência','Leve para uma decisão real','Escolha reunião, proposta, aprendizagem ou problema em que uma base verificável reduza improvisação.'),('Aprofunde','A prática continua','A folha 2 transforma a base em conteúdo, casos, avaliação, simulação e configuração.'),('Consolide','Demonstre que consegue sem guia','A folha 3 exige evidência, teach-back e transferência para outro contexto.'),('Fechamento','Seu próximo passo em 24 horas','Crie ou melhore um Notebook, registre o veredito de suficiência e explique o processo em três minutos.')]
}

def masterclass(lang):
  labels={'es':('Masterclass','Recorrido','Anterior','Siguiente','Nota de facilitación','Abrir workbook'), 'en':('Masterclass','Outline','Previous','Next','Facilitator note','Open workbook'), 'pt':('Masterclass','Percurso','Anterior','Próximo','Nota de facilitação','Abrir workbook')}[lang]
  help_url=HELP_BY_LANG[lang]
  progress_label={'es':'Progreso de la masterclass','en':'Masterclass progress','pt':'Progresso da masterclass'}[lang]
  timings=['0–3','3–7','7–10','10–15','15–20','20–25','25–30','30–35','35–41','41–47','47–53','53–59','59–65','65–70','70–80','80–84','84–87','87–90']
  deck=RESOURCES['deck']['locales'][lang]
  video=RESOURCES['videos'][0]; video_l=video['locales'][lang]
  slides=[]; outline=[]
  for i,(k,title,body) in enumerate(S[lang],1):
    link='';
    if i in (1,8): link+=f'<a class="btn secondary" href="../deck/index.html#page-{i}">{esc(deck["open"])} · {i:02d} →</a>'
    if i==8: link+=f'<a class="btn secondary" href="{help_url}" target="_blank" rel="noopener noreferrer">{("Ayuda oficial" if lang=="es" else "Official help" if lang=="en" else "Ajuda oficial")} ↗</a>'
    if 9<=i<=13: link=f'<a class="btn" href="../workbook/index.html#step-{i-8}">{labels[5]} · {i-8} →</a>'
    if i==18: link+=f'<a class="btn secondary" href="{video["url"]}" target="_blank" rel="noopener noreferrer">{esc(video_l["cta"])} · {esc(video_l["title"])} ↗</a>'
    note=(f'Di: “{title}”. Haz: conecta esta idea con un ejemplo del grupo. Observa: una respuesta que distinga evidencia de opinión.' if lang=='es' else f'Say: “{title}”. Do: connect it to one group example. Observe: an answer that separates evidence from opinion.' if lang=='en' else f'Diga: “{title}”. Faça: conecte a ideia a um exemplo do grupo. Observe: resposta que separa evidência de opinião.')
    extended=(f'<aside class="extended"><strong>+30 min:</strong> {esc("Ejecuta un prompt 6–10, revisa la rúbrica y comparte una mejora." if lang=="es" else "Run one prompt 6–10, review the rubric and share one improvement." if lang=="en" else "Execute um prompt 6–10, revise a rubrica e compartilhe uma melhoria.")}</aside>' if i==16 else '')
    slides.append(f'''<section class="slide{' active' if i==1 else ''}" id="slide-{i}" aria-label="{i} / 18"><span class="eyebrow">{esc(k)} · {timings[i-1]} min</span><h1 class="h1">{esc(title)}</h1><p class="lead">{esc(body)}</p>{link}{extended}<aside class="fac-note"><strong>{labels[4]}:</strong> {esc(note)}</aside><div class="slide-foot"><span>MetodologIA · {T[lang]['route']}</span><span>{i} / 18</span></div></section>''')
    outline.append(f'<button type="button" data-slide="{i-1}" aria-current="{"true" if i==1 else "false"}">{i:02d} · {esc(title)}</button>')
  return head(lang,labels[0],'masterclass')+f'''<main id="main" class="deck"><aside class="outline"><h2>{labels[1]}</h2>{''.join(outline)}</aside><div class="stage"><div class="slide-wrap">{''.join(slides)}</div><div class="deck-controls"><button class="btn secondary" type="button" data-prev>← {labels[2]}</button><div><div class="progress" role="progressbar" aria-label="{progress_label}" aria-valuemin="1" aria-valuemax="18" aria-valuenow="1"><span></span></div><span class="mode" data-count></span></div><div class="tools"><button class="lang" type="button" data-mode="90" aria-pressed="true">90</button><button class="lang" type="button" data-mode="120" aria-pressed="false">120</button><span class="mode" data-mode-label>90 min</span><button class="btn" type="button" data-next>{labels[3]} →</button></div></div></div></main>'''+end(lang,'masterclass')

def deck_viewer(lang):
  d=RESOURCES['deck']; l=d['locales'][lang]; base=asset_base(lang,'deck')
  labels={
    'es':{'index':'Ver las 18 láminas','prev':'Lámina anterior','next':'Lámina siguiente','page':'Lámina','of':'de','download':'Descargar PDF','source':'Masterclass oficial','hint':'Usa ← → o abre el índice. Sin JavaScript, las 18 láminas aparecen en orden.','next_class':'De ocupado a productivo','continuation':'Al terminar, continúa con la clase 2','facilitator':'Facilitada por','role':'Javier Montaño · Fundador de MetodologIA'},
    'en':{'index':'See all 18 pages','prev':'Previous page','next':'Next page','page':'Page','of':'of','download':'Download PDF','source':'Official masterclass','hint':'Use ← → or open the index. Without JavaScript, all 18 pages appear in order.','next_class':'From busy to productive','continuation':'When finished, continue with class 2','facilitator':'Facilitated by','role':'Javier Montaño · Founder of MetodologIA'},
    'pt':{'index':'Ver as 18 páginas','prev':'Página anterior','next':'Próxima página','page':'Página','of':'de','download':'Baixar PDF','source':'Masterclass oficial','hint':'Use ← → ou abra o índice. Sem JavaScript, as 18 páginas aparecem em ordem.','next_class':'De ocupado a produtivo','continuation':'Ao terminar, continue com a aula 2','facilitator':'Facilitada por','role':'Javier Montaño · Fundador da MetodologIA'}
  }[lang]
  pages=[]; index=[]
  for i in range(1,d['page_count']+1):
    page_label=f'{labels["page"]} {i} {labels["of"]} {d["page_count"]}'
    src=f'{base}assets/masterclass-pages/page-{i:02d}.webp'
    pages.append(f'<figure class="pdf-sheet{" active" if i==1 else ""}" data-page-id="page-{i}" aria-label="{page_label}"><img src="{src}" alt="{page_label}: {esc(l["display_title"])}" width="1376" height="768" loading="{"eager" if i==1 else "lazy"}" decoding="async"><figcaption>{page_label}</figcaption></figure>')
    index.append(f'<button type="button" data-pdf-page="{i-1}" aria-current="{"true" if i==1 else "false"}" aria-label="{page_label}">{i:02d}</button>')
  video=RESOURCES['videos'][0]; video_l=video['locales'][lang]
  return head(lang,l['title'],'deck')+f'''<main id="main" class="pdf-experience"><section class="pdf-stage">{breadcrumb(lang,'deck',T[lang]['masterclass'])}<header class="pdf-intro"><div><span class="eyebrow">{labels['source']} · PDF · {d['page_count']}</span><h1>{esc(l['display_title'])}</h1><p>{esc(l['description'])}</p><div class="masterclass-author"><a href="https://github.com/JaviMontano" target="_blank" rel="noopener noreferrer" aria-label="Javier Montaño · GitHub"><img src="{base}assets/javier-montano.jpg" alt="Javier Montaño" width="460" height="460" loading="lazy" decoding="async"></a><p><span>{labels['facilitator']}</span><strong>{labels['role']}</strong></p></div><p class="pdf-hint">{labels['hint']}</p></div><div class="pdf-intro-actions"><a class="pdf-download" href="{base}{d['source_asset']}" download>{labels['download']} ↓</a></div></header><details class="pdf-index"><summary>{labels['index']}<span data-pdf-count-summary>1 / {d['page_count']}</span></summary><div>{''.join(index)}</div></details><div class="pdf-viewer"><nav class="pdf-controls" aria-label="{labels['index']}"><button type="button" data-pdf-prev aria-label="{labels['prev']}" disabled>←</button><div><div class="progress" role="progressbar" aria-label="{labels['index']}" aria-valuemin="1" aria-valuemax="{d['page_count']}" aria-valuenow="1"><span></span></div><span class="mode" data-pdf-count aria-live="polite">1 / {d['page_count']}</span></div><button type="button" data-pdf-next aria-label="{labels['next']}">→</button></nav><div class="pdf-pages">{''.join(pages)}</div></div><aside class="pdf-continuation"><span>{labels['continuation']}</span><a href="{video['url']}" target="_blank" rel="noopener noreferrer"><strong>{esc(video_l['title'])}</strong><em>{labels['next_class']} ↗</em></a></aside></section></main>'''+end(lang,'deck')

def write(path,text): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text,encoding='utf-8')
def build():
  declared_assets=[RESOURCES['deck'],RESOURCES['identity_assets']['logo'],RESOURCES['identity_assets']['javier_photo'],*PLAYBOOK['founders']]
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
  css=(SRC/'site.css').read_text(encoding='utf-8').replace("Poppins-Regular.ttf') format('truetype')","Poppins-Regular.woff2') format('woff2')").replace("Poppins-Bold.ttf') format('truetype')","Poppins-Bold.woff2') format('woff2')").replace("Montserrat-Variable.ttf') format('truetype')","Montserrat-Variable.woff2') format('woff2')")
  write(DIST/'assets/site.css',css); shutil.copyfile(SRC/'forms.css',DIST/'assets/forms.css'); shutil.copyfile(SRC/'site.js',DIST/'assets/site.js')
  for p in sorted((SRC/'assets').iterdir()): shutil.copyfile(p,DIST/'assets'/p.name)
  font_jobs=(('Poppins-Regular.ttf','Poppins-Regular.woff2'),('Poppins-Bold.ttf','Poppins-Bold.woff2'),('Montserrat-Variable.ttf','Montserrat-Variable.woff2'))
  for source,target in font_jobs:
    subprocess.run([sys.executable,'-m','fontTools.subset',str(SRC/'assets'/source),f'--output-file={DIST/"assets"/target}','--flavor=woff2','--unicodes=U+0000-00FF,U+0100-024F,U+2000-206F,U+20AC','--layout-features=*','--no-hinting'],check=True,stdout=subprocess.DEVNULL)
    (DIST/'assets'/source).unlink()
  import fitz
  from PIL import Image
  page_dir=DIST/'assets'/'masterclass-pages'; page_dir.mkdir()
  pdf=fitz.open(SRC/RESOURCES['deck']['source_asset'])
  if len(pdf)!=RESOURCES['deck']['page_count']:
    raise RuntimeError(f'PDF page count mismatch: expected {RESOURCES["deck"]["page_count"]}, got {len(pdf)}')
  for i,page in enumerate(pdf,1):
    pix=page.get_pixmap(matrix=fitz.Matrix(1280/page.rect.width,1280/page.rect.width),alpha=False)
    image=Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
    image.save(page_dir/f'page-{i:02d}.webp','WEBP',quality=82,method=6,exact=True)
  pdf.close()
  outputs=[]
  for lang in LANGS:
    base=DIST if lang=='es' else DIST/lang
    for rel,content in [('index.html',landing(lang)),('workbook/index.html',workbook(lang)),('playbook/index.html',playbook(lang)),('prompts/index.html',prompt_library_page(lang)),('deck/index.html',deck_viewer(lang))]:
      content=content.replace('aria-label="Nivel 0"',f'aria-label="{T[lang]["route"]}"').replace('MetodologIA · Nivel 0',f'MetodologIA · {T[lang]["route"]}')
      content=content.replace('W04 · Profesor / Asesor / Coach',{'es':'W04 · Profesor / Asesor / Coach','en':'W04 · Teacher / Advisor / Coach','pt':'W04 · Professor / Assessor / Coach'}[lang] if rel=='workbook/index.html' else 'W04 · Profesor / Asesor / Coach')
      content=decorate_ui(content,lang)
      p=base/rel;write(p,content);outputs.append(p)
  sitemap=[]
  for lang in LANGS:
    prefix='' if lang=='es' else f'{lang}/'
    for page in ('','workbook/','playbook/','prompts/','deck/'):
      sitemap.append(f'  <url><loc>{PUBLIC}{prefix}{page}</loc></url>')
  write(DIST/'sitemap.xml','<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+'\n'.join(sitemap)+'\n</urlset>\n')
  write(DIST/'robots.txt',f'User-agent: *\nAllow: /\nSitemap: {PUBLIC}sitemap.xml\n')
  outputs += [DIST/'sitemap.xml',DIST/'robots.txt']
  outputs += [p for p in (DIST/'assets').rglob('*') if p.is_file()]
  hashes={str(p.relative_to(DIST)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(outputs)}
  source_hashes={str(p.relative_to(SRC)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SRC.rglob('*')) if p.is_file()}
  manifest={'schema_version':'build-manifest-v1','build_id':'nivel-0-learning-resources-v5','state':'RENDERED_DRAFT','publication_authorized':False,'compiler':{'ref':'scripts/build.py','sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},'outputs':hashes,'sources':source_hashes}
  write(DIST/'build-manifest.json',json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
  receipt={'schema_version':'build-receipt-v1','build_id':manifest['build_id'],'manifest_sha256':hashlib.sha256((DIST/'build-manifest.json').read_bytes()).hexdigest(),'output_count':len(hashes),'deterministic_inputs':True,'state':'RENDERED_DRAFT'}
  write(DIST/'build-receipt.json',json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
if __name__=='__main__': build()
