import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const root=path.resolve(import.meta.dirname,'..');
const dist=path.join(root,'dist');
const inventory=JSON.parse(fs.readFileSync(path.join(dist,'editorial-string-inventory.json'),'utf8'));
const playwrightModule=process.env.PLAYWRIGHT_MODULE||path.resolve(root,'..','..','frames-n0-kit-01','node_modules','playwright','index.mjs');
const {chromium}=await import(pathToFileURL(playwrightModule));
const executablePath=process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

function local(route){return pathToFileURL(path.join(dist,route)).href}
function serverUrl(origin,route){return `${origin}/${route}`}
function serve(){
  const server=http.createServer((request,response)=>{
    const url=new URL(request.url,'http://127.0.0.1');
    const relative=decodeURIComponent(url.pathname).replace(/^\/+/, '')||'index.html';
    const target=path.resolve(dist,relative.endsWith('/')?`${relative}index.html`:relative);
    if(!target.startsWith(`${dist}${path.sep}`)||!fs.existsSync(target)||!fs.statSync(target).isFile()){response.writeHead(404);response.end('Not found');return}
    const type=target.endsWith('.html')?'text/html; charset=utf-8':target.endsWith('.js')?'text/javascript; charset=utf-8':target.endsWith('.css')?'text/css; charset=utf-8':'application/octet-stream';
    response.writeHead(200,{'content-type':type,'cache-control':'no-store'});fs.createReadStream(target).pipe(response);
  });
  return new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',()=>resolve(server))});
}

async function assertVariant(page,{locale,audience,pageType,theme}){
  const state=await page.evaluate(()=>({
    locale:document.documentElement.lang,
    audience:document.documentElement.dataset.audience,
    page:document.body.dataset.page,
    theme:document.documentElement.dataset.theme,
    stored:{theme:localStorage.getItem('mdg_theme'),locale:localStorage.getItem('mdg_locale'),audience:localStorage.getItem('mdg_audience')},
    preferenceGroups:document.querySelectorAll('[data-conoce-preferences]').length,
  }));
  if(state.locale!==locale||state.audience!==audience||state.page!==pageType||state.theme!==theme||state.preferenceGroups!==1)throw new Error(`Variant state drift: ${JSON.stringify({expected:{locale,audience,pageType,theme},state,url:page.url()})}`);
  return state;
}

async function exercise(browser,protocol,startRoute,expectedStart){
  const context=await browser.newContext({viewport:{width:390,height:844}});const page=await context.newPage();const errors=[];
  page.on('pageerror',(error)=>errors.push(error.message));
  const start=protocol.name==='file'?local(startRoute):serverUrl(protocol.origin,startRoute);
  await page.goto(start,{waitUntil:'load'});await page.evaluate(()=>localStorage.clear());await page.reload({waitUntil:'load'});
  await assertVariant(page,{...expectedStart,theme:'light'});

  const theme=page.locator('[data-mdg-theme]');await theme.click();
  let state=await assertVariant(page,{...expectedStart,theme:'dark'});
  if(state.stored.theme!=='dark'||await theme.getAttribute('aria-checked')!=='true')throw new Error(`${protocol.name} theme click did not persist`);

  const localeLink=page.locator('[data-mdg-locale]');const nextLocale=await localeLink.getAttribute('data-mdg-locale');
  await Promise.all([page.waitForNavigation({waitUntil:'load'}),localeLink.click()]);
  state=await assertVariant(page,{locale:nextLocale,audience:expectedStart.audience,pageType:expectedStart.pageType,theme:'dark'});
  if(state.stored.locale!==nextLocale)throw new Error(`${protocol.name} locale click did not persist`);

  const audienceLink=page.locator('[data-mdg-audience]');const nextAudience=await audienceLink.getAttribute('data-mdg-audience');
  await Promise.all([page.waitForNavigation({waitUntil:'load'}),audienceLink.click()]);
  state=await assertVariant(page,{locale:nextLocale,audience:nextAudience,pageType:expectedStart.pageType,theme:'dark'});
  if(state.stored.audience!==nextAudience)throw new Error(`${protocol.name} audience click did not persist`);

  await page.locator('[data-mdg-theme]').click();
  state=await assertVariant(page,{locale:nextLocale,audience:nextAudience,pageType:expectedStart.pageType,theme:'light'});
  if(state.stored.theme!=='light'||errors.length)throw new Error(`${protocol.name} toggle errors: ${JSON.stringify({state,errors})}`);
  await context.close();
  return `${protocol.name}:${expectedStart.pageType}:${expectedStart.locale}/${expectedStart.audience}->${nextLocale}/${nextAudience}`;
}

const server=await serve();const address=server.address();const origin=`http://127.0.0.1:${address.port}`;
const browser=await chromium.launch({headless:true,executablePath});
try{
  const results=[];
  for(const protocol of [{name:'file'},{name:'http',origin}]){
    for(const route of inventory.routes){
      results.push(await exercise(browser,protocol,route.route,{locale:route.locale,audience:route.audience,pageType:route.page}));
    }
  }
  console.log(`PREFERENCE_TOGGLES_OK routes=${inventory.route_count} protocols=2 scenarios=${results.length} clicks=${results.length*4}`);
}finally{
  await browser.close();await new Promise((resolve)=>server.close(resolve));
}
