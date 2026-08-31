(function(){'use strict';
  document.documentElement.classList.remove('no-js');document.documentElement.classList.add('js','mdg-enhanced');
  /* [METODOLOGIA] Governed Conoce chrome enhancement. SSR remains authoritative. */
  var allowedPreferenceKeys=['mdg_theme','mdg_locale','mdg_audience'];
  function readPreference(key){if(allowedPreferenceKeys.indexOf(key)<0)throw new Error('CONOCE_STORAGE_KEY_FORBIDDEN');try{return localStorage.getItem(key)}catch(error){return null}}
  function writePreference(key,value){if(allowedPreferenceKeys.indexOf(key)<0)throw new Error('CONOCE_STORAGE_KEY_FORBIDDEN');try{localStorage.setItem(key,value)}catch(error){}}
  var preferences=document.querySelector('[data-conoce-preferences]');
  var chromeMenu=document.querySelector('[data-conoce-menu]');
  var chromeNav=document.querySelector('[data-conoce-nav]');
  var chromeResources=document.querySelector('[data-conoce-resources]');
  function closeChromeMenu(restore){if(!chromeMenu||!chromeNav)return;var wasOpen=chromeMenu.getAttribute('aria-expanded')==='true';var resourcesWereOpen=Boolean(chromeResources&&chromeResources.open);var resourceSummary=chromeResources&&chromeResources.querySelector('summary');chromeMenu.setAttribute('aria-expanded','false');chromeMenu.setAttribute('aria-label',chromeMenu.dataset.openLabel||'Open navigation');chromeNav.dataset.open='false';if(chromeResources)chromeResources.open=false;if(restore){if(wasOpen)chromeMenu.focus();else if(resourcesWereOpen&&resourceSummary)resourceSummary.focus()}}
  if(chromeMenu&&chromeNav){
    chromeMenu.addEventListener('click',function(){var open=chromeMenu.getAttribute('aria-expanded')!=='true';if(!open){closeChromeMenu(true);return}document.dispatchEvent(new CustomEvent('conoce:close-intrapage'));chromeMenu.setAttribute('aria-expanded','true');chromeMenu.setAttribute('aria-label',chromeMenu.dataset.closeLabel||'Close navigation');chromeNav.dataset.open='true';var first=chromeNav.querySelector('a[href],summary');if(first)requestAnimationFrame(function(){first.focus()})});
    chromeNav.querySelectorAll('a[href]').forEach(function(link){link.addEventListener('click',function(){closeChromeMenu(false)})});
    document.addEventListener('conoce:close-menu',function(){closeChromeMenu(false)});
    document.addEventListener('pointerdown',function(event){if(chromeMenu.getAttribute('aria-expanded')==='true'&&!event.target.closest('[data-conoce-header]'))closeChromeMenu(false)});
    document.addEventListener('keydown',function(event){if(event.key==='Escape'&&(chromeMenu.getAttribute('aria-expanded')==='true'||(chromeResources&&chromeResources.open))){event.preventDefault();closeChromeMenu(true)}});
  }
  if(preferences){
    var variants={};try{variants=JSON.parse(preferences.dataset.variantLinks||'{}')}catch(error){throw new Error('CONOCE_VARIANT_MATRIX_INVALID')}
    var currentLocale=preferences.dataset.locale,currentAudience=preferences.dataset.audience;
    var storedLocale=readPreference('mdg_locale'),storedAudience=readPreference('mdg_audience');
    var wantedLocale=['es','en','pt'].indexOf(storedLocale)>=0?storedLocale:currentLocale;
    var wantedAudience=['persona','empresa'].indexOf(storedAudience)>=0?storedAudience:currentAudience;
    if((wantedLocale!==currentLocale||wantedAudience!==currentAudience)&&variants[wantedLocale]&&variants[wantedLocale][wantedAudience]){
      var redirect=variants[wantedLocale][wantedAudience];var target=new URL(redirect,location.href);
      if(target.origin===location.origin&&target.href!==location.href){target.search=location.search;target.hash=location.hash;location.replace(target.href);return}
    }
    var themeButton=preferences.querySelector('[data-mdg-theme]');
    var sun='<svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>';
    var moon='<svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
    function syncTheme(){if(!themeButton)return;var dark=document.documentElement.dataset.theme==='dark';var current=dark?preferences.dataset.darkLabel:preferences.dataset.lightLabel;var next=dark?preferences.dataset.lightLabel:preferences.dataset.darkLabel;themeButton.setAttribute('aria-checked',String(dark));themeButton.setAttribute('aria-label',preferences.dataset.themeLabel+': '+current+'. '+preferences.dataset.changeLabel+' '+next);themeButton.innerHTML=dark?sun:moon}
    syncTheme();
    if(themeButton)themeButton.addEventListener('click',function(){var next=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=next;writePreference('mdg_theme',next);syncTheme();var status=preferences.querySelector('[data-mdg-status]');if(status)status.textContent=preferences.dataset.themeLabel+': '+(next==='dark'?preferences.dataset.darkLabel:preferences.dataset.lightLabel)});
    function preservePromptState(link){var target=new URL(link.getAttribute('href'),location.href);target.search=location.search;target.hash=location.hash;link.href=target.href}
    preferences.querySelectorAll('[data-mdg-locale]').forEach(function(link){link.addEventListener('click',function(){writePreference('mdg_locale',link.dataset.mdgLocale);preservePromptState(link)})});
    preferences.querySelectorAll('[data-mdg-audience]').forEach(function(link){link.addEventListener('click',function(){writePreference('mdg_audience',link.dataset.mdgAudience);preservePromptState(link)})});
  }
  var intrapageLinks=[];
  function setIntrapageCurrent(id){intrapageLinks.forEach(function(link){if(link.hash==='#'+id)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current')})}
  document.querySelectorAll('[data-copy]').forEach(function(b){b.addEventListener('click',async function(){var el=document.getElementById(b.dataset.copy);if(!el)return;try{await navigator.clipboard.writeText(el.textContent);b.classList.add('done');var old=b.textContent;b.textContent='✓';setTimeout(function(){b.textContent=old;b.classList.remove('done')},1200)}catch(e){el.focus&&el.focus()}})});
  function promptSelection(library){var tab=library&&library.querySelector('[data-prompt-format][aria-selected="true"]');var mode=library&&library.querySelector('[data-prompt-mode-select][aria-pressed="true"]');return{level:tab?tab.getAttribute('aria-label'):'',compact:tab&&tab.dataset.levelNumber?'N'+tab.dataset.levelNumber:'',mode:mode?mode.textContent.trim():''}}
  function syncPromptCopy(library,override){if(!library)return;var button=library.querySelector('[data-brain-copy],[data-format-copy]');if(!button)return;var selection=promptSelection(library);var base=override||(button.dataset.copyLabel||'Copy');var compact=[base,selection.compact,selection.mode].filter(Boolean).join(' · ');var accessible=[base,selection.level,selection.mode].filter(Boolean).join(' · ');var text=button.querySelector('span');if(text)text.textContent=compact;button.setAttribute('aria-label',accessible)}
  function activePrompt(library){if(!library)return null;var mode=library.dataset.activeMode||'template';var level=library.querySelector('details[data-prompt-level][open]');if(!level)return null;var source=level.querySelector('[data-prompt-source][data-prompt-mode="'+mode+'"]');var panel=level.querySelector(mode==='demo'?'[data-prompt-demo]':'[data-prompt-template]');return panel?{panel:panel,text:source?source.value:panel.textContent}:null}
  function copyFeedback(button,ok){var library=button.closest('[data-prompt-library]');var status=library&&library.querySelector('.prompt-copy-status');var selection=promptSelection(library);var label=ok?(button.dataset.copiedLabel||'Copied'):(button.dataset.copyLabel||'Copy');syncPromptCopy(library,label);if(status)status.textContent=ok?[label,selection.level,selection.mode].filter(Boolean).join(' · '):'';if(ok){button.classList.add('done');setTimeout(function(){syncPromptCopy(library);button.classList.remove('done');if(status)status.textContent=''},1500)}}
  document.querySelectorAll('[data-brain-copy]').forEach(function(b){b.addEventListener('click',async function(){
    var library=b.closest('[data-prompt-library]');var promptState=activePrompt(library);var input=document.getElementById(b.dataset.brainInput);var status=input&&input.parentElement.querySelector('[data-brain-status]');
    if(!promptState||!input)return;var value=input.value.trim();var prompt=promptState.text;
    if(value&&library.dataset.activeMode!=='demo'){var label=b.dataset.brainLabel||'BRAIN DUMP';var pattern=new RegExp('<'+label.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'[^>]*>','g');prompt=prompt.replace(pattern,value)}
    if(status)status.textContent='';
    try{await navigator.clipboard.writeText(prompt);copyFeedback(b,true)}catch(e){copyFeedback(b,false);promptState.panel.focus&&promptState.panel.focus()}
  })});
  document.querySelectorAll('[data-format-copy]').forEach(function(b){b.addEventListener('click',async function(){var library=b.closest('[data-prompt-library]');var promptState=activePrompt(library);if(!promptState)return;try{await navigator.clipboard.writeText(promptState.text);copyFeedback(b,true)}catch(e){copyFeedback(b,false);promptState.panel.focus&&promptState.panel.focus()}})});
  var promptMode=(new URLSearchParams(location.search)).get('mode')==='demo'?'demo':'template';
  function setPromptMode(mode,updateUrl){promptMode=mode==='demo'?'demo':'template';document.querySelectorAll('[data-prompt-library]').forEach(function(library){library.dataset.activeMode=promptMode;library.querySelectorAll('[data-prompt-mode-select]').forEach(function(button){button.setAttribute('aria-pressed',String(button.dataset.promptModeSelect===promptMode))});library.querySelectorAll('[data-prompt-format]').forEach(function(tab){var templateId=tab.dataset.promptTemplateControls||tab.getAttribute('aria-controls').replace(/-demo$/,'');tab.dataset.promptTemplateControls=templateId;tab.setAttribute('aria-controls',promptMode==='demo'?templateId+'-demo':templateId)});library.querySelectorAll('details[data-prompt-level]').forEach(function(level){var template=level.querySelector('[data-prompt-template]');var demo=level.querySelector('.prompt-demo-native');if(template)template.hidden=promptMode==='demo';if(demo){demo.classList.toggle('is-active',promptMode==='demo');demo.open=promptMode==='demo'}});syncPromptCopy(library)});if(updateUrl){var url=new URL(location.href);if(promptMode==='demo')url.searchParams.set('mode','demo');else url.searchParams.delete('mode');history.replaceState(null,'',url.pathname+(url.search||'')+(url.hash||''))}}
  document.querySelectorAll('[data-prompt-mode-select]').forEach(function(button){button.addEventListener('click',function(){setPromptMode(button.dataset.promptModeSelect,true)})});
  document.querySelectorAll('[data-prompt-library]').forEach(function(library){var formatTabs=[].slice.call(library.querySelectorAll('[data-prompt-format]'));var panels=[].slice.call(library.querySelectorAll('.prompt-format-panel'));formatTabs.forEach(function(tab){tab.dataset.promptTemplateControls=tab.getAttribute('aria-controls').replace(/-demo$/,'')});function selectFormat(tab,focus){formatTabs.forEach(function(t,i){var on=t===tab;t.setAttribute('aria-selected',String(on));t.tabIndex=on?0:-1;var panel=document.getElementById(t.getAttribute('aria-controls'));if(panel){var details=panel.closest('details[data-prompt-level]');if(details)details.open=on}if(on){library.dataset.activeLevel=String(i+1);library.dataset.activeFormat=t.dataset.promptFormat;var card=library.closest('.library-prompt-card,.brain-prompt-card,.step');if(card)card.dataset.promptActiveLevel=String(i+1)}});syncPromptCopy(library);if(focus)tab.focus()}formatTabs.forEach(function(tab,index){tab.addEventListener('click',function(){selectFormat(tab,false)});tab.addEventListener('keydown',function(e){var target=index;if(e.key==='ArrowRight')target=(index+1)%formatTabs.length;else if(e.key==='ArrowLeft')target=(index-1+formatTabs.length)%formatTabs.length;else if(e.key==='Home')target=0;else if(e.key==='End')target=formatTabs.length-1;else return;e.preventDefault();selectFormat(formatTabs[target],true)})});if(formatTabs.length)selectFormat(formatTabs[0],false);else panels.forEach(function(panel){panel.hidden=false})});
  setPromptMode(promptMode,false);
  document.querySelectorAll('[data-brain-dump]').forEach(function(input){input.addEventListener('input',function(){var status=input.parentElement.querySelector('[data-brain-status]');if(status)status.textContent=''})});

  /* NotebookLM execution guide: compact tabs, route filters and prompt accordions. */
  var notebookGuide=document.querySelector('[data-notebook-execution-guide]');
  if(notebookGuide){
    var notebookTabs=[].slice.call(notebookGuide.querySelectorAll('[data-notebook-tab]'));
    function selectNotebookTab(tab,focus){
      notebookTabs.forEach(function(candidate){
        var selected=candidate===tab;
        candidate.setAttribute('aria-selected',String(selected));
        candidate.tabIndex=selected?0:-1;
        var panel=document.getElementById(candidate.getAttribute('aria-controls'));
        if(panel)panel.hidden=!selected;
      });
      if(focus)tab.focus();
    }
    notebookTabs.forEach(function(tab,index){
      tab.addEventListener('click',function(){selectNotebookTab(tab,false)});
      tab.addEventListener('keydown',function(event){
        var target=index;
        if(event.key==='ArrowRight')target=(index+1)%notebookTabs.length;
        else if(event.key==='ArrowLeft')target=(index-1+notebookTabs.length)%notebookTabs.length;
        else if(event.key==='Home')target=0;
        else if(event.key==='End')target=notebookTabs.length-1;
        else return;
        event.preventDefault();selectNotebookTab(notebookTabs[target],true);
      });
    });
    var selectedNotebookTab=notebookTabs.find(function(tab){return tab.getAttribute('aria-selected')==='true'})||notebookTabs[0];
    if(selectedNotebookTab)selectNotebookTab(selectedNotebookTab,false);
  }

  var promptSurfaceButtons=[].slice.call(document.querySelectorAll('[data-prompt-surface-filter]'));
  var promptSurfaceCards=[].slice.call(document.querySelectorAll('#directos [data-library-prompt]'));
  function filterPromptSurface(surface){
    promptSurfaceButtons.forEach(function(button){button.setAttribute('aria-pressed',String(button.dataset.promptSurfaceFilter===surface))});
    promptSurfaceCards.forEach(function(card){
      var visible=surface==='all'||card.dataset.notebookSurface===surface;
      card.hidden=!visible;
      if(!visible){var disclosure=card.querySelector('[data-prompt-card-disclosure]');if(disclosure)disclosure.open=false}
    });
  }
  promptSurfaceButtons.forEach(function(button){button.addEventListener('click',function(){filterPromptSurface(button.dataset.promptSurfaceFilter||'all')})});

  var promptDisclosures=[].slice.call(document.querySelectorAll('[data-prompt-card-disclosure]'));
  function syncPromptDisclosure(details){
    var summary=details.querySelector(':scope > summary');
    if(!summary)return;
    var title=summary.querySelector('.library-prompt-title');
    var action=details.open?(summary.dataset.closeLabel||'Close prompt'):(summary.dataset.openLabel||'Open prompt');
    var discovery=summary.dataset.discoveryLabel||'';
    summary.setAttribute('aria-label',action+(title&&title.textContent.trim()?' · '+title.textContent.trim():'')+(discovery?' · '+discovery:''));
  }
  promptDisclosures.forEach(function(details){
    syncPromptDisclosure(details);
    details.addEventListener('toggle',function(){
      if(details.open){
        var list=details.closest('.library-prompt-list');
        if(list)list.querySelectorAll('[data-prompt-card-disclosure][open]').forEach(function(other){if(other!==details)other.open=false});
      }
      syncPromptDisclosure(details);
    });
  });
  function revealPromptFromHash(){
    if(!location.hash)return;
    var target=document.getElementById(location.hash.slice(1));
    if(!target||!target.matches('[data-library-prompt]'))return;
    target.hidden=false;
    var details=target.querySelector('[data-prompt-card-disclosure]');
    if(details)details.open=true;
  }
  revealPromptFromHash();
  addEventListener('hashchange',revealPromptFromHash);

  var tabs=[].slice.call(document.querySelectorAll('[role=tab][data-sheet]'));
  function selectTab(tab,focus,updateHash){tabs.forEach(function(t){var on=t===tab;t.setAttribute('aria-selected',String(on));t.tabIndex=on?0:-1;var p=document.getElementById(t.getAttribute('aria-controls'));if(p)p.hidden=!on});if(focus)tab.focus();if(updateHash)history.replaceState(null,'','#'+tab.getAttribute('aria-controls'))}
  tabs.forEach(function(t,i){t.addEventListener('click',function(){selectTab(t,false,true)});t.addEventListener('keydown',function(e){if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();var d=e.key==='ArrowRight'?1:-1;selectTab(tabs[(i+d+tabs.length)%tabs.length],true,true)}})});
  if(tabs.length){var wanted=location.hash.slice(1);var tab=tabs.find(function(t){return t.dataset.sheet===wanted||t.getAttribute('aria-controls')===wanted})||tabs[0];selectTab(tab,false,false)}
  var slides=[].slice.call(document.querySelectorAll('.slide'));var outlines=[].slice.call(document.querySelectorAll('[data-slide]'));var prevButtons=[].slice.call(document.querySelectorAll('[data-prev]'));var nextButtons=[].slice.call(document.querySelectorAll('[data-next]'));var current=0;
  function show(n,updateHash){
    if(!slides.length)return;
    var viewX=window.scrollX,viewY=window.scrollY;
    current=Math.max(0,Math.min(slides.length-1,n));
    slides.forEach(function(s,i){var on=i===current;s.classList.toggle('active',on);s.setAttribute('aria-hidden',String(!on))});
    outlines.forEach(function(o,i){o.setAttribute('aria-current',i===current?'step':'false')});
    prevButtons.forEach(function(b){b.disabled=current===0});nextButtons.forEach(function(b){b.disabled=current===slides.length-1});
    var bar=document.querySelector('.deck-progress .progress span');if(bar){bar.style.width=((current+1)/slides.length*100)+'%';bar.parentElement.setAttribute('aria-valuenow',String(current+1))}
    var value=(current+1)+' / '+slides.length;document.querySelectorAll('[data-count],[data-outline-count]').forEach(function(count){count.textContent=value});
    var phase=document.querySelector('[data-phase-current]');var activePhase=slides[current].dataset.phase;var group=document.querySelector('.outline-group:nth-child('+activePhase+') h3');if(phase&&group)phase.textContent=group.textContent.replace(/^\d+\s*·\s*/,'');
    if(updateHash!==false)history.replaceState(null,'','#slide-'+(current+1));
    if(outlines[current]&&matchMedia('(min-width:981px)').matches)outlines[current].scrollIntoView({block:'nearest'});
    window.scrollTo(viewX,viewY);
  }
  outlines.forEach(function(b){b.addEventListener('click',function(){show(Number(b.dataset.slide));var outline=b.closest('details');if(outline&&matchMedia('(max-width:980px)').matches){outline.open=false;var title=slides[current]&&slides[current].querySelector('h2');if(title)title.focus({preventScroll:true})}})});
  prevButtons.forEach(function(b){b.addEventListener('click',function(){show(current-1)})});nextButtons.forEach(function(b){b.addEventListener('click',function(){show(current+1)})});
  if(slides.length){var outlinePanel=document.querySelector('details.outline');if(outlinePanel&&matchMedia('(max-width:980px)').matches)outlinePanel.open=false;var m=location.hash.match(/slide-(\d+)/);show(m?Number(m[1])-1:0,Boolean(m));requestAnimationFrame(function(){if(m)slides[current].scrollIntoView({block:'center'});else window.scrollTo(0,0)});document.addEventListener('keydown',function(e){var target=e.target;if(target&&target.closest&&target.closest('button,a,summary,input,textarea,select,[contenteditable="true"]'))return;if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();show(current+1)}if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();show(current-1)}if(e.key==='Home'){e.preventDefault();show(0)}if(e.key==='End'){e.preventDefault();show(slides.length-1)}})}
  document.querySelectorAll('.deck-mode[data-mode]').forEach(function(b){b.addEventListener('click',function(){var v=b.dataset.mode;var minutes=b.dataset.modeMinutes||v;document.body.dataset.mode=v;document.querySelectorAll('.deck-mode[data-mode]').forEach(function(x){x.setAttribute('aria-pressed',String(x===b))});var out=document.querySelector('[data-mode-label]');if(out)out.textContent=minutes+' min'})});

  /* Landing V2: all content exists before this progressive enhancement runs. */
  var landing=document.querySelector('.landing-v2');
  if(landing){
    var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var reveals=[].slice.call(document.querySelectorAll('.reveal'));
    if(!reduce&&'IntersectionObserver' in window){
      var revealObserver=new IntersectionObserver(function(entries){entries.forEach(function(entry){if(entry.isIntersecting){entry.target.classList.add('is-visible');revealObserver.unobserve(entry.target)}})},{threshold:.12});
      reveals.forEach(function(el){revealObserver.observe(el)});
    }else{reveals.forEach(function(el){el.classList.add('is-visible')})}

    var tensions=[].slice.call(document.querySelectorAll('[data-tension]'));
    var tensionOutput=document.querySelector('[data-tension-output]');
    tensions.forEach(function(button){button.addEventListener('click',function(){
      var selected=button.getAttribute('aria-pressed')!=='true';
      tensions.forEach(function(other){other.setAttribute('aria-pressed',String(selected&&other===button))});
      if(tensionOutput)tensionOutput.textContent=selected?button.querySelector('em').textContent:'';
    })});

    var chapters=[].slice.call(document.querySelectorAll('[data-chapter]'));
    var chapterLinks=[].slice.call(document.querySelectorAll('[data-chapter-link]'));
    var reading=document.querySelector('[data-reading-progress]');
    var routeStages=[].slice.call(document.querySelectorAll('[data-route-stage]'));
    var routeProgress=document.querySelector('[data-route-progress]');
    function updateProgress(){
      var max=document.documentElement.scrollHeight-innerHeight;
      var value=max>0?Math.max(0,Math.min(1,scrollY/max)):0;
      if(reading)reading.style.transform='scaleX('+value+')';
      if(routeProgress){
        var route=document.querySelector('.route-section');
        var start=route?route.offsetTop:0;var length=route?route.offsetHeight-innerHeight:1;
        routeProgress.style.transform='scaleY('+Math.max(0,Math.min(1,(scrollY-start+innerHeight*.35)/Math.max(1,length)))+')';
      }
    }
    updateProgress();addEventListener('scroll',updateProgress,{passive:true});addEventListener('resize',updateProgress);
    if('IntersectionObserver' in window){
      var chapterObserver=new IntersectionObserver(function(entries){entries.forEach(function(entry){if(entry.isIntersecting){chapterLinks.forEach(function(link){link.setAttribute('aria-current',String(link.hash==='#'+entry.target.id))})}})},{rootMargin:'-30% 0px -60% 0px'});
      chapters.forEach(function(section){chapterObserver.observe(section)});
      var stageObserver=new IntersectionObserver(function(entries){entries.forEach(function(entry){if(entry.isIntersecting){routeStages.forEach(function(stage){stage.classList.toggle('is-current',stage===entry.target)})}})},{rootMargin:'-28% 0px -55% 0px'});
      routeStages.forEach(function(stage){stageObserver.observe(stage)});
    }
  }

  /* Canonical intrapage navigation: SSR links remain useful without JS. */
  var intrapage=document.querySelector('[data-intrapage-nav]');
  if(intrapage){
    intrapageLinks=[].slice.call(intrapage.querySelectorAll('[data-intrapage-link]'));
    var intrapageOpen=document.querySelector('[data-intrapage-open]');
    var intrapageClose=intrapage.querySelector('[data-intrapage-close]');
    var intrapageBackdrop=document.querySelector('[data-intrapage-backdrop]');
    var intrapageMedia=matchMedia('(max-width:1180px)');
    var intrapageIsOpen=false;
    function syncIntrapageMode(){if(intrapageMedia.matches){if(!intrapageIsOpen)intrapage.hidden=true}else{intrapage.hidden=false;intrapage.removeAttribute('role');intrapage.removeAttribute('aria-modal')}}
    function openIntrapage(){if(!intrapageMedia.matches)return;document.dispatchEvent(new CustomEvent('conoce:close-menu'));intrapageIsOpen=true;intrapage.hidden=false;intrapage.setAttribute('role','dialog');intrapage.setAttribute('aria-modal','true');if(intrapageBackdrop)intrapageBackdrop.hidden=false;if(intrapageOpen)intrapageOpen.setAttribute('aria-expanded','true');requestAnimationFrame(function(){document.body.classList.add('intrapage-open');requestAnimationFrame(function(){if(intrapageClose)intrapageClose.focus()})})}
    function closeIntrapage(restore){if(!intrapageIsOpen)return;intrapageIsOpen=false;document.body.classList.remove('intrapage-open');intrapage.hidden=true;if(intrapageBackdrop)intrapageBackdrop.hidden=true;if(intrapageOpen)intrapageOpen.setAttribute('aria-expanded','false');if(restore&&intrapageOpen)intrapageOpen.focus()}
    function activateIntrapageTarget(id){
      var target=document.getElementById(id);if(!target)return null;
      var sheet=target.classList.contains('sheet')?target:target.closest('.sheet');
      if(sheet){var tab=tabs.find(function(item){return item.getAttribute('aria-controls')===sheet.id});if(tab)selectTab(tab,false,false)}
      var slideMatch=id.match(/^slide-(\d+)$/);if(slideMatch&&slides.length)show(Number(slideMatch[1])-1);
      return document.getElementById(id);
    }
    function navigateIntrapage(id){var target=activateIntrapageTarget(id);if(!target)return;history.replaceState(null,'','#'+id);setIntrapageCurrent(id);var focusTarget=target.matches('h1,h2,h3,a,button,[tabindex]')?target:target.querySelector('h1,h2,h3,[tabindex]');if(focusTarget&&!focusTarget.matches('a,button,input,select,textarea,[tabindex]'))focusTarget.setAttribute('tabindex','-1');closeIntrapage(false);target.scrollIntoView({block:'start'});if(focusTarget)focusTarget.focus({preventScroll:true})}
    if(intrapageOpen)intrapageOpen.addEventListener('click',openIntrapage);
    document.addEventListener('conoce:close-intrapage',function(){closeIntrapage(false)});
    if(intrapageClose)intrapageClose.addEventListener('click',function(){closeIntrapage(true)});
    if(intrapageBackdrop)intrapageBackdrop.addEventListener('click',function(){closeIntrapage(true)});
    intrapageLinks.forEach(function(link){link.addEventListener('click',function(event){var id=decodeURIComponent(link.hash.slice(1));if(document.getElementById(id)){event.preventDefault();navigateIntrapage(id)}})});
    document.addEventListener('keydown',function(event){
      if(!intrapageIsOpen)return;
      if(event.key==='Escape'){event.preventDefault();closeIntrapage(true);return}
      if(event.key!=='Tab')return;
      var focusable=[].slice.call(intrapage.querySelectorAll('button:not([disabled]),a[href]')).filter(function(item){return !item.hidden});if(!focusable.length)return;
      var first=focusable[0],last=focusable[focusable.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}
    });
    var observeTargets=intrapageLinks.map(function(link){return document.getElementById(decodeURIComponent(link.hash.slice(1)))}).filter(Boolean);
    if('IntersectionObserver' in window){var intrapageObserver=new IntersectionObserver(function(entries){var visible=entries.filter(function(entry){return entry.isIntersecting&&!entry.target.hidden});if(visible.length){visible.sort(function(a,b){return Math.abs(a.boundingClientRect.top)-Math.abs(b.boundingClientRect.top)});setIntrapageCurrent(visible[0].target.id)}},{rootMargin:'-22% 0px -62% 0px',threshold:0});observeTargets.forEach(function(target){intrapageObserver.observe(target)})}
    var initialId=location.hash.slice(1);var initialLink=initialId&&intrapageLinks.find(function(link){return link.hash==='#'+initialId});if(initialId&&document.getElementById(initialId))activateIntrapageTarget(initialId);setIntrapageCurrent(initialLink?initialId:intrapageLinks[0].hash.slice(1));
    if(initialLink){var alignInitialTarget=function(){requestAnimationFrame(function(){requestAnimationFrame(function(){var target=document.getElementById(initialId);if(target){target.scrollIntoView({block:'start'});setIntrapageCurrent(initialId)}})})};if(document.readyState==='complete')alignInitialTarget();else addEventListener('load',alignInitialTarget,{once:true})}
    addEventListener('hashchange',function(){var id=location.hash.slice(1);if(document.getElementById(id))navigateIntrapage(id)});
    if(intrapageMedia.addEventListener)intrapageMedia.addEventListener('change',function(){if(!intrapageMedia.matches)closeIntrapage(false);syncIntrapageMode()});
    syncIntrapageMode();
  }
})();
