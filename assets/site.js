(function(){'use strict';
  var root=document.documentElement;
  root.classList.remove('no-js');root.classList.add('js');
  var lang=document.documentElement.lang||'es';
  var key='metodologia-n0-preferences-v1';
  function read(){try{return JSON.parse(localStorage.getItem(key)||'{}')}catch(e){return{}}}
  function write(v){try{localStorage.setItem(key,JSON.stringify(v))}catch(e){}}
  var prefs=read(); if(prefs.theme==='dark'||prefs.theme==='light')root.dataset.theme=prefs.theme;
  function syncThemeButton(b){var dark=root.dataset.theme==='dark';var next=dark?b.dataset.lightLabel:b.dataset.darkLabel;b.setAttribute('aria-pressed',String(dark));b.setAttribute('aria-label',next);var icon=b.querySelector('[data-theme-icon]');if(icon)icon.textContent=dark?'☀':'☾';var copy=b.querySelector('.theme-copy');if(copy)copy.textContent=next}
  document.querySelectorAll('button[data-theme]').forEach(function(b){syncThemeButton(b);b.addEventListener('click',function(e){e.stopPropagation();var t=root.dataset.theme==='dark'?'light':'dark';root.dataset.theme=t;write({theme:t,lang:lang});syncThemeButton(b)})});
  document.querySelectorAll('[data-lang]').forEach(function(a){var target=a.getAttribute('href').split('#')[0];a.href=target+(location.hash||'');a.addEventListener('click',function(){write({theme:root.dataset.theme,lang:a.dataset.lang})})});
  document.querySelectorAll('[data-copy]').forEach(function(b){b.addEventListener('click',async function(){var el=document.getElementById(b.dataset.copy);if(!el)return;try{await navigator.clipboard.writeText(el.textContent);b.classList.add('done');var old=b.textContent;b.textContent='✓';setTimeout(function(){b.textContent=old;b.classList.remove('done')},1200)}catch(e){el.focus&&el.focus()}})});
  function activeLevel(library){var tab=library&&library.querySelector('[data-prompt-format][aria-selected="true"]');return tab?tab.getAttribute('aria-label'):''}
  function copyFeedback(button,ok){var library=button.closest('[data-prompt-library]');var status=library&&library.querySelector('.prompt-copy-status');var level=activeLevel(library);var label=ok?(button.dataset.copiedLabel||'Copied'):(button.dataset.copyLabel||'Copy');button.setAttribute('aria-label',label+' · '+level);if(status)status.textContent=ok?label+' · '+level:'';if(ok){button.classList.add('done');setTimeout(function(){button.setAttribute('aria-label',(button.dataset.copyLabel||'Copy')+' · '+level);button.classList.remove('done');if(status)status.textContent=''},1500)}}
  document.querySelectorAll('[data-brain-copy]').forEach(function(b){b.addEventListener('click',async function(){
    var library=b.closest('[data-prompt-library]');var template=library&&library.querySelector('.prompt-format-panel:not([hidden])');var input=document.getElementById(b.dataset.brainInput);var status=input&&input.parentElement.querySelector('[data-brain-status]');
    if(!template||!input)return;var value=input.value.trim();
    if(!value){if(status)status.textContent=status.dataset.emptyMessage||'';input.focus();return}
    if(status)status.textContent='';var prompt=template.textContent.replace(/\{\{BRAIN_DUMP\}\}/g,value);
    try{await navigator.clipboard.writeText(prompt);copyFeedback(b,true)}catch(e){copyFeedback(b,false);template.focus&&template.focus()}
  })});
  document.querySelectorAll('[data-format-copy]').forEach(function(b){b.addEventListener('click',async function(){var library=b.closest('[data-prompt-library]');var template=library&&library.querySelector('.prompt-format-panel:not([hidden])');if(!template)return;try{await navigator.clipboard.writeText(template.textContent);copyFeedback(b,true)}catch(e){copyFeedback(b,false);template.focus&&template.focus()}})});
  document.querySelectorAll('[data-prompt-library]').forEach(function(library){var formatTabs=[].slice.call(library.querySelectorAll('[data-prompt-format]'));var panels=[].slice.call(library.querySelectorAll('.prompt-format-panel'));function selectFormat(tab,focus){formatTabs.forEach(function(t,i){var on=t===tab;t.setAttribute('aria-selected',String(on));t.tabIndex=on?0:-1;var panel=document.getElementById(t.getAttribute('aria-controls'));if(panel){panel.hidden=!on;var details=panel.closest('details');if(details)details.open=on}if(on)library.dataset.activeLevel=String(i+1)});var copy=library.querySelector('[data-brain-copy],[data-format-copy]');if(copy)copy.setAttribute('aria-label',(copy.dataset.copyLabel||'Copy')+' · '+tab.getAttribute('aria-label'));if(focus)tab.focus()}formatTabs.forEach(function(tab,index){tab.addEventListener('click',function(){selectFormat(tab,false)});tab.addEventListener('keydown',function(e){var target=index;if(e.key==='ArrowRight')target=(index+1)%formatTabs.length;else if(e.key==='ArrowLeft')target=(index-1+formatTabs.length)%formatTabs.length;else if(e.key==='Home')target=0;else if(e.key==='End')target=formatTabs.length-1;else return;e.preventDefault();selectFormat(formatTabs[target],true)})});if(formatTabs.length)selectFormat(formatTabs[0],false);else panels.forEach(function(panel){panel.hidden=false})});
  document.querySelectorAll('[data-brain-dump]').forEach(function(input){input.addEventListener('input',function(){var status=input.parentElement.querySelector('[data-brain-status]');if(status)status.textContent=''})});
  var tabs=[].slice.call(document.querySelectorAll('[role=tab][data-sheet]'));
  function selectTab(tab,focus,updateHash){tabs.forEach(function(t){var on=t===tab;t.setAttribute('aria-selected',String(on));var p=document.getElementById(t.getAttribute('aria-controls'));if(p)p.hidden=!on});if(focus)tab.focus();if(updateHash)history.replaceState(null,'','#'+tab.dataset.sheet)}
  tabs.forEach(function(t,i){t.addEventListener('click',function(){selectTab(t,false,true)});t.addEventListener('keydown',function(e){if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();var d=e.key==='ArrowRight'?1:-1;selectTab(tabs[(i+d+tabs.length)%tabs.length],true,true)}})});
  if(tabs.length){var wanted=location.hash.slice(1);var tab=tabs.find(function(t){return t.dataset.sheet===wanted})||tabs[0];selectTab(tab,false,false)}
  var slides=[].slice.call(document.querySelectorAll('.slide'));var outlines=[].slice.call(document.querySelectorAll('[data-slide]'));var current=0;
  function show(n){if(!slides.length)return;current=Math.max(0,Math.min(slides.length-1,n));slides.forEach(function(s,i){s.classList.toggle('active',i===current)});outlines.forEach(function(o,i){o.setAttribute('aria-current',String(i===current))});var bar=document.querySelector('.progress span');if(bar){bar.style.width=((current+1)/slides.length*100)+'%';bar.parentElement.setAttribute('aria-valuenow',String(current+1))}var count=document.querySelector('[data-count]');if(count)count.textContent=(current+1)+' / '+slides.length;history.replaceState(null,'','#slide-'+(current+1))}
  outlines.forEach(function(b){b.addEventListener('click',function(){show(Number(b.dataset.slide))})});
  document.querySelectorAll('[data-prev]').forEach(function(b){b.addEventListener('click',function(){show(current-1)})});document.querySelectorAll('[data-next]').forEach(function(b){b.addEventListener('click',function(){show(current+1)})});
  if(slides.length){var m=location.hash.match(/slide-(\d+)/);show(m?Number(m[1])-1:0);requestAnimationFrame(function(){window.scrollTo(0,0)});document.addEventListener('keydown',function(e){var target=e.target;if(target&&target.closest&&target.closest('button,a,input,textarea,select,[contenteditable="true"]'))return;if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();show(current+1)}if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();show(current-1)}if(e.key==='Home')show(0);if(e.key==='End')show(slides.length-1)})}
  document.querySelectorAll('[data-mode]').forEach(function(b){b.addEventListener('click',function(){var v=b.dataset.mode;document.body.dataset.mode=v;document.querySelectorAll('[data-mode]').forEach(function(x){x.setAttribute('aria-pressed',String(x===b))});var out=document.querySelector('[data-mode-label]');if(out)out.textContent=v+' min'})});

  var pdfPages=[].slice.call(document.querySelectorAll('.pdf-sheet'));
  var pdfIndex=[].slice.call(document.querySelectorAll('[data-pdf-page]'));
  var pdfPrev=[].slice.call(document.querySelectorAll('[data-pdf-prev]'));
  var pdfNext=[].slice.call(document.querySelectorAll('[data-pdf-next]'));
  var pdfCurrent=0;
  function showPdf(n,focus){
    if(!pdfPages.length)return;
    pdfCurrent=Math.max(0,Math.min(pdfPages.length-1,n));
    pdfPages.forEach(function(page,i){page.classList.toggle('active',i===pdfCurrent)});
    var activeImage=pdfPages[pdfCurrent].querySelector('img');if(activeImage)activeImage.loading='eager';
    pdfIndex.forEach(function(button,i){button.setAttribute('aria-current',String(i===pdfCurrent))});
    var progress=document.querySelector('.pdf-controls .progress');
    if(progress){progress.setAttribute('aria-valuenow',String(pdfCurrent+1));var fill=progress.querySelector('span');if(fill)fill.style.width=((pdfCurrent+1)/pdfPages.length*100)+'%'}
    document.querySelectorAll('[data-pdf-count],[data-pdf-count-summary]').forEach(function(count){count.textContent=(pdfCurrent+1)+' / '+pdfPages.length});
    pdfPrev.forEach(function(button){button.disabled=pdfCurrent===0});
    pdfNext.forEach(function(button){button.disabled=pdfCurrent===pdfPages.length-1});
    history.replaceState(null,'','#page-'+(pdfCurrent+1));
    if(focus&&pdfIndex[pdfCurrent])pdfIndex[pdfCurrent].focus();
  }
  if(pdfPages.length){
    pdfIndex.forEach(function(button){button.addEventListener('click',function(){showPdf(Number(button.dataset.pdfPage),false)})});
    pdfPrev.forEach(function(button){button.addEventListener('click',function(){showPdf(pdfCurrent-1,false)})});
    pdfNext.forEach(function(button){button.addEventListener('click',function(){showPdf(pdfCurrent+1,false)})});
    var pdfMatch=location.hash.match(/page-(\d+)/);showPdf(pdfMatch?Number(pdfMatch[1])-1:0,false);
    document.addEventListener('keydown',function(e){var target=e.target;if(target&&target.closest&&target.closest('button,a,input,textarea,select,[contenteditable="true"]'))return;if(e.key==='ArrowRight'||e.key==='PageDown'){e.preventDefault();showPdf(pdfCurrent+1,false)}if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();showPdf(pdfCurrent-1,false)}if(e.key==='Home')showPdf(0,false);if(e.key==='End')showPdf(pdfPages.length-1,false)});
  }

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
})();
