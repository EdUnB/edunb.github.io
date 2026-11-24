const {spawn} = require('node:child_process');
const {once} = require('node:events');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'academic-browser-'));
const baseUrl = process.argv[2] || 'http://127.0.0.1:8000/';
assert.equal(new URL(baseUrl).hostname,'127.0.0.1');
const browser = spawn(process.env.BROWSER_EXE || 'C:/Program Files/Google/Chrome/Application/chrome.exe', [
  '--headless', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--disable-background-networking', '--remote-debugging-port=0',
  '--user-data-dir=' + profile, 'about:blank',
], {windowsHide:true, stdio:['ignore','ignore','pipe']});
const timer = setTimeout(() => { console.error('Browser audit timed out'); browser.kill(); process.exit(1); }, 55000);
let socket;
async function main() {
  const endpoint = await new Promise((resolve,reject) => {
    let stderr = '';
    browser.stderr.on('data', data => {
      stderr += data;
      const match = stderr.match(/DevTools listening on (ws:\/\/[^\s]+)/);
      if (match) resolve(new URL(match[1]));
    });
    browser.once('error',reject);
    browser.once('exit',code => reject(new Error('Chrome exited '+code+' '+stderr)));
  });
  const targets = await (await fetch('http://' + endpoint.host + '/json/list')).json();
  socket = new WebSocket(targets.find(target => target.type === 'page').webSocketDebuggerUrl);
  await once(socket,'open');
  let id=0;
  const pending = new Map();
  const errors = [];
  socket.addEventListener('message', ({data}) => {
    const message = JSON.parse(data);
    if (message.method === 'Runtime.exceptionThrown') errors.push(message.params.exceptionDetails.text);
    if (!message.id) return;
    const {resolve,reject} = pending.get(message.id);
    pending.delete(message.id);
    if (message.error) reject(new Error(message.error.message));
    else resolve(message.result);
  });
  const cdp = (method,params={}) => new Promise((resolve,reject) => {
    pending.set(++id,{resolve,reject});
    socket.send(JSON.stringify({id,method,params}));
  });
  async function evaluate(expression) {
    const response = await cdp('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
    if (response.exceptionDetails) throw new Error(response.exceptionDetails.exception?.description);
    return response.result.value;
  }
  async function key(key,code,virtualKey) {
    const params={key,code,windowsVirtualKeyCode:virtualKey,nativeVirtualKeyCode:virtualKey};
    await cdp('Input.dispatchKeyEvent',{type:key === 'Enter' ? 'keyDown' : 'rawKeyDown', text:key === 'Enter' ? '\r' : '', ...params});
    await cdp('Input.dispatchKeyEvent',{type:'keyUp',...params});
  }
  async function tap(selector) {
    const point = await evaluate(`(() => {
      const node=document.querySelector(${JSON.stringify(selector)});
      node.scrollIntoView({block:'center',behavior:'instant'});
      const rect=node.getBoundingClientRect();
      return {x:rect.x+rect.width/2,y:rect.y+rect.height/2};
    })()`);
    await cdp('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[point]});
    await new Promise(resolve=>setTimeout(resolve,60));
    await cdp('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
    await new Promise(resolve=>setTimeout(resolve,350));
  }



  await cdp('Runtime.enable');
  await cdp('Page.enable');
  await cdp('Emulation.setFocusEmulationEnabled',{enabled:true});
  await cdp('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await cdp('Network.enable');
  const failedAssets = [];
  socket.addEventListener('message', ({data}) => {
    const message = JSON.parse(data);
    if (message.method === 'Network.responseReceived') {
      const response = message.params.response;
      if (response.url.startsWith(baseUrl) && response.status >= 400) failedAssets.push(response.url);
    }
  });
  await cdp('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  await cdp('Page.navigate',{url:baseUrl});
  for (let retry=0; retry<70; retry++) {
    if(await evaluate("document.querySelectorAll('.publication-item').length === 50 && document.querySelector('#supervision-ongoing-count')?.textContent === '14'")) break;
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  async function click(selector) { await evaluate('document.querySelector('+JSON.stringify(selector)+').click()'); }
  async function select(selector,value) {
    await evaluate("(() => { const s=document.querySelector("+JSON.stringify(selector)+"); s.value="+JSON.stringify(value)+"; s.dispatchEvent(new Event('change',{bubbles:true})); })()");
  }
  async function search(value) {
    await evaluate("(() => { const s=document.querySelector('#publication-search'); s.value="+JSON.stringify(value)+"; s.dispatchEvent(new Event('input',{bubbles:true})); })()");
  }
  async function screenshot(name) {
    if (!process.env.AUDIT_SCREENSHOTS) return;
    await new Promise(resolve=>setTimeout(resolve,180));
    const {data} = await cdp('Page.captureScreenshot',{format:'png'});
    fs.writeFileSync(path.join(process.env.AUDIT_SCREENSHOTS,name+'.png'),Buffer.from(data,'base64'));
  }
  assert.equal(await evaluate("document.querySelectorAll('.publication-item').length"),50);
  assert.equal(await evaluate("(() => {const sections=[...document.querySelector('#main').children].map(n=>n.id);return sections.indexOf('projects')===sections.indexOf('research')+1 && sections.indexOf('supervision')===sections.indexOf('projects')+1;})()"),true);
  assert.equal(await evaluate("(() => {const links=[...document.querySelectorAll('#primary-nav a')].map(a=>a.hash);return links.indexOf('#projects')===links.indexOf('#research')+1 && links.indexOf('#supervision')>links.indexOf('#projects');})()"),true);

  assert.equal(await evaluate("document.querySelectorAll('.publication-item:not([hidden])').length"),4);
  for(const locale of ['en','pt','fr','zh']){
    await click('[data-lang='+locale+']');
    await evaluate("document.querySelector('#publication-toggle').focus()");await key('Enter','Enter',13);
    assert.equal(await evaluate("document.querySelectorAll('.publication-item:not([hidden])').length"),50);
    assert.equal(await evaluate("document.querySelector('#publication-toggle').getAttribute('aria-expanded')"),'true');
    await click('#publication-toggle');
    assert.equal(await evaluate("document.querySelectorAll('.publication-item:not([hidden])').length"),4);
  }
  await click('#publication-toggle');
  await search('10.1016/j.energy.2021.122208');
  assert.equal(await evaluate("document.querySelectorAll('.publication-item:not([hidden])').length"),1);
  assert.equal(await evaluate("document.querySelector('#publication-toggle').hidden"),true);
  await click('#publication-reset');
  assert.equal(await evaluate("document.querySelectorAll('.publication-item:not([hidden])').length"),4);
  assert.equal(await evaluate("document.querySelector('#publication-results').textContent.includes('50')"),true);
  await click('[data-lang=en]');

  for (const route of ['content/publications.json', 'scripts/build.py', '.git/config', 'lattes-xml.xml']) {
    assert.equal((await fetch(baseUrl + route)).status,404,'Preview must expose only generated assets');
  }
  assert.equal(await evaluate("document.querySelector('#scopus-impact').hidden"),false);
  assert.equal(await evaluate("document.querySelectorAll('.scopus-charts figure').length"),0,'No annual chart without source data');
  for(const language of ['en','pt','fr','zh']) {
    await click('[data-lang='+language+']');
    assert.equal(await evaluate("document.querySelector('[data-metric=documents] dd').textContent.replace(/\\D/g,'')"),'87');
    assert.equal(await evaluate("document.querySelector('[data-metric=citations] dd').textContent.replace(/\\D/g,'')"),'1243');
    assert.equal(await evaluate("document.querySelector('[data-metric=h_index] dd').textContent"),'22');
    assert.equal(await evaluate("document.querySelector('.scopus-provenance a').href"),'https://www.scopus.com/authid/detail.uri?authorId=57195100508');
  }
  // Synthetic series exist only in this test page, never in editorial data.
  await evaluate("window.SITE_SCOPUS.annual_series={documents:[{year:2020,value:2}],citations:[{year:2020,value:3}]}; document.dispatchEvent(new CustomEvent('site:language'))");
  assert.equal(await evaluate("document.querySelectorAll('.scopus-charts figure').length"),2);
  assert.equal(await evaluate("document.querySelectorAll('.scopus-charts table').length"),2);
  await evaluate("window.SITE_SCOPUS.annual_series=null;document.dispatchEvent(new CustomEvent('site:language'))");
  await click('[data-lang=en]');
  assert.equal(await evaluate("document.querySelectorAll('h1').length"),1);
  assert.equal(await evaluate("document.querySelector('link[rel=canonical]').href"),'https://edunb.github.io/');
  assert.equal(await evaluate("document.querySelectorAll('#project-list .project-card').length"),4);
  assert.equal(await evaluate("document.querySelectorAll('.project-story').length"),1);
  await evaluate("document.querySelector('.project-details summary').focus()");await key('Enter','Enter',13);
  assert.equal(await evaluate("document.querySelector('.project-details').open"),true);
  for(const locale of ['en','pt','fr','zh']){
    await click('[data-lang='+locale+']');
    assert.equal(await evaluate("document.querySelector('.project-details').open"),true);
    assert.equal(await evaluate("document.querySelector('.project-detail-body h4').textContent===siteText('projectQuestion')"),true);
    assert.equal(await evaluate("document.querySelector('.project-details p').textContent===window.SITE_PROJECTS[0].story.question[siteLanguage()]"),true);
  }
  await click('[data-lang=pt]');
  await evaluate("document.querySelector('#projects').scrollIntoView({block:'start',behavior:'instant'})");
  await screenshot('project-story-desktop');
  await click('.project-details summary');
  assert.equal(await evaluate("document.querySelector('.project-details').open"),false);
  await click('[data-lang=en]');

  assert.equal(await evaluate("document.querySelector('#supervision-completed-count').textContent"),'13');
  for (const state of ['completed','ongoing']) {
    assert.equal(await evaluate("document.querySelectorAll('#supervision-"+state+"-list > li:not([hidden])').length"),4);
    assert.equal(await evaluate("document.querySelector('#supervision-"+state+"-toggle').getAttribute('aria-expanded')"),'false');
    await evaluate("document.querySelector('#supervision-"+state+"-toggle').focus()");
    await key('Enter','Enter',13);
    assert.equal(await evaluate("document.querySelectorAll('#supervision-"+state+"-list > li:not([hidden])').length"),state==='completed'?13:14);
    const other=state==='completed'?'ongoing':'completed';
    if(state==='completed') assert.equal(await evaluate("document.querySelectorAll('#supervision-"+other+"-list > li:not([hidden])').length"),4);
    await click('[data-lang=fr]');
    assert.equal(await evaluate("document.querySelector('#supervision-"+state+"-toggle').textContent"),'Afficher moins');
    await click('#supervision-'+state+'-toggle');
    assert.equal(await evaluate("document.querySelectorAll('#supervision-"+state+"-list > li:not([hidden])').length"),4);
  }
  await select('#supervision-level','phd');
  assert.equal(await evaluate("document.querySelector('#supervision-completed-toggle').hidden"),true);
  assert.equal(await evaluate("document.querySelectorAll('#supervision-ongoing-list > li:not([hidden])').length"),4);
  await click('#supervision-ongoing-toggle');
  assert.equal(await evaluate("document.querySelectorAll('#supervision-ongoing-list > li:not([hidden])').length"),9);
  await select('#supervision-level','');
  assert.equal(await evaluate("document.querySelectorAll('#supervision-ongoing-list > li:not([hidden])').length"),4);
  await click('[data-lang=en]');
  for (const locale of ['en','pt','fr','zh']) {
    await click('[data-lang='+locale+']');
    for(const level of ['masters','phd']) for(const status of ['completed','ongoing']) {
      await select('#supervision-level',level);await select('#supervision-status',status);
      const badge=await evaluate("(() => {const c=document.querySelector('#supervision-"+status+"-list > li:not([hidden])'),b=c.querySelector('.supervision-badge'),s=getComputedStyle(b);return {level:c.dataset.level,status:c.dataset.status,color:s.color,background:s.backgroundColor,border:s.borderTopColor,text:b.textContent,expected:siteText('"+(level==='masters'?'supMasters':'supPhD')+"')+' · '+siteText('"+(status==='completed'?'supDone':'supActive')+"')};})()");
      assert.equal(badge.level,level);assert.equal(badge.status,status);assert.equal(badge.text,badge.expected);
      assert.equal(badge.color,level==='masters'?'rgb(21, 91, 83)':'rgb(33, 77, 126)');
      assert.equal(badge.background,status==='ongoing'?'rgb(255, 255, 255)':level==='masters'?'rgb(225, 241, 235)':'rgb(229, 238, 251)');
      assert.equal(badge.border,status==='completed'?'rgba(0, 0, 0, 0)':level==='masters'?'rgb(39, 134, 121)':'rgb(56, 104, 152)');
    }
  }
  await click('[data-lang=pt]');
  await select('#supervision-level','');await select('#supervision-status','');
  await evaluate("document.querySelector('#supervision-completed').scrollIntoView({block:'start',behavior:'instant'})");
  await screenshot('supervision-level-colours');
  await click('[data-lang=en]');
  const undergradCounts=await evaluate("['undergraduate-research','undergraduate-thesis'].map(level=>window.SITE_SUPERVISIONS.items.filter(i=>i.level===level&&i.status==='completed').length)");
  for(const locale of ['en','pt','fr','zh']) {
    await click('[data-lang='+locale+']');
    for(const [index,level] of ['undergraduate-research','undergraduate-thesis'].entries()){
      assert.equal(await evaluate("Number(document.querySelector('#supervision-"+level+"-count').textContent)"),undergradCounts[index]);
      assert.equal(await evaluate("document.querySelectorAll('#supervision-"+level+"-list > li:not([hidden])').length"),Math.min(4,undergradCounts[index]));
      if(undergradCounts[index]>4){
        await evaluate("document.querySelector('#supervision-"+level+"-toggle').focus()");await key('Enter','Enter',13);
        assert.equal(await evaluate("document.querySelectorAll('#supervision-"+level+"-list > li:not([hidden])').length"),undergradCounts[index]);
        await click('#supervision-'+level+'-toggle');
      }
    }
    await select('#supervision-undergraduate-type','undergraduate-research');
    assert.equal(await evaluate("document.querySelector('#supervision-undergraduate-thesis').hidden"),true);
    assert.equal(await evaluate("document.querySelector('#supervision-completed-count').textContent"),'13');
    await select('#supervision-undergraduate-type','');
  }
  if(undergradCounts[0]){
    await select('#supervision-undergraduate-type','undergraduate-research');await select('#supervision-undergraduate-year','2020');
    assert.equal(await evaluate("[...document.querySelectorAll('#supervision-undergraduate-research-list h5')].every(n=>window.SITE_SUPERVISIONS.items.some(i=>i.title===n.textContent))"),true);
    assert.equal(await evaluate("document.querySelector('#supervision-undergraduate-research-list').textContent.includes(siteText('supCourseUnspecified'))"),true);
    assert.equal(await evaluate("(() => {const list=document.querySelector('#supervision-undergraduate-research-list'),unknown=window.SITE_SUPERVISIONS.items.some(i=>i.level==='undergraduate-research'&&i.year===2020&&!i.role);return list.textContent.includes(siteText(unknown?'supRoleUnspecified':'supSupervisor'));})()"),true);
    await select('#supervision-undergraduate-type','');await select('#supervision-undergraduate-year','');
  }
  await click('[data-lang=pt]');
  await evaluate("document.querySelector('#undergraduate').scrollIntoView({block:'start',behavior:'instant'})");
  await screenshot('undergraduate-desktop');
  await click('[data-lang=en]');
  assert.equal(await evaluate("document.querySelectorAll('.supervision-repository').length"),12);
  assert.equal(await evaluate("document.querySelector('#supervision-area').disabled"),true);
  assert.equal(await evaluate("document.querySelectorAll('#editorial-appointment .supervision-card').length"),2);
  const structural = await evaluate("(() => { const ids=[...document.querySelectorAll('[id]')].map(n=>n.id); return {duplicateIds:ids.filter((id,i)=>ids.indexOf(id)!==i),brokenAnchors:[...document.querySelectorAll('a[href^=\"#\"]')].map(a=>a.getAttribute('href')).filter(h=>h.length>1&&!document.getElementById(h.slice(1))),brokenLabels:[...document.querySelectorAll('[aria-labelledby],[aria-controls]')].flatMap(n=>(n.getAttribute('aria-labelledby')||n.getAttribute('aria-controls')).split(' ')).filter(id=>!document.getElementById(id)),emptyButtons:[...document.querySelectorAll('button,summary')].filter(n=>!(n.textContent.trim()||n.getAttribute('aria-label'))).length,blankUnsafeLinks:[...document.querySelectorAll('a[target=\"_blank\"]')].filter(a=>!a.rel.includes('noopener')).length};})()");
  assert.deepEqual(structural,{duplicateIds:[],brokenAnchors:[],brokenLabels:[],emptyButtons:0,blankUnsafeLinks:0});
  // Research-network prototype: selection, keyboard, translations and fallback.
  assert.equal(await evaluate("document.querySelectorAll('.research-node').length"),5);
  assert.equal(await evaluate("document.querySelector('.research-network').hidden"),false);
  const hoverPoint=await evaluate("(() => {const n=document.querySelector('[data-topic=bio]');n.scrollIntoView({block:'center',behavior:'instant'});const r=n.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()");
  await cdp('Input.dispatchMouseEvent',{type:'mouseMoved',...hoverPoint});
  assert.equal(await evaluate("document.querySelectorAll('.research-keyword').length"),5);
  await cdp('Input.dispatchMouseEvent',{type:'mouseMoved',x:1,y:1});
  assert.equal(await evaluate("document.querySelectorAll('.research-keyword').length"),0);
  await evaluate("document.querySelector('[data-topic=bio]').focus()");
  assert.equal(await evaluate("document.querySelectorAll('.research-keyword').length"),5);
  await key('Enter','Enter',13);
  assert.equal(await evaluate("document.querySelector('[data-topic=bio]').getAttribute('aria-pressed')"),'true');
  await click('[data-lang=pt]');
  assert.match(await evaluate("document.querySelector('.research-keywords').textContent"),/Biomassa/);
  assert.match(await evaluate("document.querySelector('.research-network').getAttribute('aria-label')"),/Temas/);
  assert.equal(await evaluate("document.querySelector('[data-topic=bio]').getAttribute('aria-pressed')"),'true');
  await evaluate("document.querySelector('[data-topic=bio]').focus()");
  await key('Escape','Escape',27);
  assert.equal(await evaluate("document.querySelectorAll('.research-keyword').length"),0);
  assert.equal(await evaluate("document.querySelector('.network-original').hidden"),true);
  assert.equal(await evaluate("document.querySelectorAll('[data-network-view]').length"),0);
  await click('[data-lang=en]');
  await click('[data-topic=thermo]');
  await evaluate("document.querySelector('.research-art').scrollIntoView({block:'center',behavior:'instant'})");
  await screenshot('research-network-desktop');
  await click('.network-reset');
  await new Promise(resolve=>setTimeout(resolve,60));
  assert.equal(await evaluate("document.querySelector('.network-motion').disabled"),true);
  await cdp('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'no-preference'}]});
  await evaluate("document.querySelector('.research-art').scrollIntoView({block:'center',behavior:'instant'});document.activeElement.blur()");
  await cdp('Input.dispatchMouseEvent',{type:'mouseMoved',x:1,y:1});
  const xBefore=await evaluate("parseFloat(document.querySelector('[data-topic=model]').style.left)");
  await new Promise(resolve=>setTimeout(resolve,350));
  assert.ok(Math.abs(await evaluate("parseFloat(document.querySelector('[data-topic=model]').style.left)")-xBefore)>.005,'Nodes should float');
  await click('.network-motion');
  const pausedPosition=await evaluate("document.querySelector('[data-topic=model]').style.left");
  await new Promise(resolve=>setTimeout(resolve,140));
  assert.equal(await evaluate("document.querySelector('[data-topic=model]').style.left"),pausedPosition,'Pause must stop motion');
  await evaluate("document.querySelector('[data-topic=bio]').scrollIntoView({block:'center',behavior:'instant'})");
  const dragStart=await evaluate("(() => {const n=document.querySelector('[data-topic=bio]');const r=n.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,left:parseFloat(n.style.left)};})()");
  await cdp('Input.dispatchMouseEvent',{type:'mouseMoved',x:dragStart.x,y:dragStart.y});
  await cdp('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',buttons:1,clickCount:1,x:dragStart.x,y:dragStart.y});
  await new Promise(resolve=>setTimeout(resolve,40));
  await cdp('Input.dispatchMouseEvent',{type:'mouseMoved',button:'left',buttons:1,x:dragStart.x+45,y:dragStart.y+25});
  await new Promise(resolve=>setTimeout(resolve,80));
  await cdp('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',buttons:0,clickCount:1,x:dragStart.x+45,y:dragStart.y+25});
  await new Promise(resolve=>setTimeout(resolve,100));
  assert.ok(await evaluate("parseFloat(document.querySelector('[data-topic=bio]').style.left)")>dragStart.left+3,'Mouse drag moves node');
  assert.equal(await evaluate("document.querySelector('[data-topic=bio]').getAttribute('aria-pressed')"),'true','Drag release keeps selection');
  await evaluate("document.querySelector('[data-topic=bio]').focus()");
  const arrowStart=await evaluate("parseFloat(document.querySelector('[data-topic=bio]').style.left)");
  await key('ArrowRight','ArrowRight',39);
  assert.equal(await evaluate("parseFloat(document.querySelector('[data-topic=bio]').style.left)"),arrowStart+3);
  const edgeX=await evaluate("Number(document.querySelector('.research-edges line').getAttribute('x1'))");
  assert.ok(Math.abs(edgeX-arrowStart-3)<.001,'Edges must follow node');
  await click('.network-reset');
  assert.equal(await evaluate("parseFloat(document.querySelector('[data-topic=bio]').style.left)"),29);
  await click('.network-motion');
  await cdp('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await new Promise(resolve=>setTimeout(resolve,60));
  assert.equal(await evaluate("document.querySelector('.network-motion').disabled"),true);
  const reducedPosition=await evaluate("document.querySelector('[data-topic=model]').style.left");
  await new Promise(resolve=>setTimeout(resolve,100));
  assert.equal(await evaluate("document.querySelector('[data-topic=model]').style.left"),reducedPosition);
  for(const language of ['en','pt']) {
    await click('[data-lang='+language+']');
    await click('.network-reset');
    await click('[data-topic=environment]');
    assert.equal(await evaluate("document.querySelectorAll('.research-keyword').length"),6);
    const carbonWords=await evaluate("document.querySelector('.research-keywords').textContent");
    assert.match(carbonWords,/CBIOs/);
    assert.match(carbonWords,language==='en'?/Carbon accounting/:/Contabilidade de carbono/);
    assert.match(carbonWords,language==='en'?/Emissions quantification/:/Quantificação de emissões/);
    assert.match(carbonWords,language==='en'?/Carbon footprint/:/Pegada de carbono/);
  }
  await click('.network-reset');
  console.log('PASS research network: hover, keyboard, float/pause/reduced motion, mouse drag, edge tracking, reset, EN/PT and network-only view');
  await screenshot('desktop-home');
  const contrast = await evaluate("(" + (() => {
    const linear = x => (x/=255) <= .04045 ? x/12.92 : Math.pow((x+.055)/1.055,2.4);
    const rgb = value => value.match(/[0-9.]+/g)?.map(Number);
    const luminance = a => .2126*linear(a[0])+.7152*linear(a[1])+.0722*linear(a[2]);
    const failures = new Map();
    for (const node of document.querySelectorAll('.pub-authors,.pub-note,.publication-year,.collab-small,.map-legend,.map-footnote,.project-top,.credential>span:last-child')) {
      const style=getComputedStyle(node); let parent=node,bg;
      while(parent) {
        const computed=getComputedStyle(parent);
        if(computed.backgroundImage!=='none') break;
        const value=rgb(computed.backgroundColor);
        if(value && value[3]!==0) { bg=value;break; }
        parent=parent.parentElement;
      }
      if(!bg)continue;
      const fg=rgb(style.color),a=luminance(fg),b=luminance(bg);
      const ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
      if(ratio<4.5) failures.set(node.className,{selector:node.className,ratio:Number(ratio.toFixed(2)),color:style.color});
    }
    return [...failures.values()];
  }).toString() + ")()");
  assert.deepEqual(contrast, [], 'Supporting text contrast must reach 4.5:1');
  console.log('PASS supporting text contrast');

  await cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1000,deviceScaleFactor:1,mobile:false});
  for (const language of ['en','pt']) {
    await click('[data-lang='+language+']');
    const missing=await evaluate('Object.keys(translations.en).filter(key=>!translations.'+language+'[key])');
    assert.deepEqual(missing,[]);
    await evaluate("document.querySelector('.nav-activities summary').focus()");
    await key('Enter','Enter',13);
    assert.equal(await evaluate("document.querySelector('.nav-activities').open"),true);
    await key('Escape','Escape',27);
    assert.equal(await evaluate("document.querySelector('.nav-activities').open"),false);
    await key('Enter','Enter',13);
    await click('.nav-submenu a[href="#editorial"]');
    assert.equal(await evaluate("document.activeElement.id"),'editorial');
    assert.equal(await evaluate("document.querySelector('.nav-activities').open"),false);
    await search('10.1016/j.energy.2021.122208');
    assert.equal(await evaluate("document.querySelectorAll('.publication-item').length"),1);
    assert.equal(await evaluate("document.querySelector('.publication-year').textContent"),'2022');
    await search('');
    await evaluate("document.querySelector('#publication-search').focus()");
    await cdp('Input.insertText',{text:'10.1016/j.energy.2021.122208'});
    assert.equal(await evaluate("document.querySelectorAll('.publication-item').length"),1);
    await select('#publication-year','2025');
    assert.equal(await evaluate("document.querySelectorAll('.publication-item').length"),0);
    await click('#publication-reset');
    assert.equal(await evaluate("document.querySelectorAll('.publication-item').length"),50);
    await search('model');
    assert.ok(await evaluate("document.querySelectorAll('.publication-item').length")>0);
    await click('[data-filter=modeling]');
    assert.ok(await evaluate("[...document.querySelectorAll('.publication-item')].every(n=>n.dataset.category.includes('modeling'))"));
    await click('[data-lang='+(language==='en'?'pt':'en')+']');
    assert.equal(await evaluate("document.querySelector('#publication-search').value"),'model');
    await click('[data-lang='+language+']');
    await search('<script>test</script>');
    assert.equal(await evaluate("document.querySelectorAll('.publication-item').length"),0);
    await click('#publication-reset');
    for (const category of ['bioenergy','modeling','sustainability','other']) {
      await click('[data-filter='+category+']');
      const expected=await evaluate("window.SITE_PUBLICATIONS.items.filter(p=>p.categories.includes("+JSON.stringify(category)+")).length");
      assert.equal(await evaluate("document.querySelectorAll('.publication-item').length"),expected);
    }
    await click('#publication-reset');
    for (const year of await evaluate("Array.from(document.querySelector('#publication-year').options).map(o=>o.value).filter(Boolean)")) {
      await select('#publication-year',year);
      const expected=await evaluate("window.SITE_PUBLICATIONS.items.filter(p=>String(p.year)==="+JSON.stringify(year)+").length");
      assert.equal(await evaluate("document.querySelectorAll('.publication-item').length"),expected);
    }
    await click('#publication-reset');
    await select('#supervision-status','ongoing');
    await select('#supervision-level','phd');
    assert.equal(await evaluate("document.querySelectorAll('#supervision-ongoing-list li').length"),9);
    assert.equal(await evaluate("document.querySelector('#supervision-completed').hidden"),true);
    await click('[data-lang='+(language==='en'?'pt':'en')+']');
    assert.equal(await evaluate("document.querySelector('#supervision-level').value"),'phd');
    await select('#supervision-status','completed');
    assert.equal(await evaluate("document.querySelectorAll('#supervision-completed-list .supervision-repository').length"),1);
    assert.equal(await evaluate("document.querySelector('#supervision-completed-list .supervision-repository').textContent"),language==='en'?'Acessar tese':'View Thesis');
    await select('#supervision-level','');
    await select('#supervision-year','2024');
    assert.ok(await evaluate("document.querySelectorAll('#supervision-completed-list li').length")>0);
    await select('#supervision-year','');
    await select('#supervision-status','');
    await click('[data-lang='+language+']');
    await click('[data-map=world]');
    await evaluate("document.querySelector('.country.has-partners[data-code=FRA]').focus()");
    await key('Enter','Enter',13);
    assert.equal(await evaluate("document.querySelector('#map-country').value"),'FRA');
    await select('#map-city','Nancy');
    assert.equal(await evaluate("document.querySelectorAll('#collaboration-cards details').length"),2);
    assert.match(await evaluate("document.querySelector('#collaboration-cards').textContent"),/Anélie Pétrissans/);
    await evaluate("document.querySelector('#collaborations').scrollIntoView({behavior:'instant'})");
    await screenshot('desktop-map-'+language);
    await click('[data-map=brazil]');
    await evaluate("document.querySelector('.map-marker').focus()");
    await key(' ','Space',32);
    assert.equal(await evaluate("document.querySelector('#map-city').value"),'Brasília');
    assert.equal(await evaluate("document.querySelectorAll('#collaboration-cards details').length"),7);
  }
  const originalTitles=await evaluate("window.SITE_PUBLICATIONS.items.map(p=>p.title)");
  for(const language of ['fr','zh']) {
    await click('[data-lang='+language+']');
    assert.equal(await evaluate('document.documentElement.lang'),language==='fr'?'fr':'zh-Hans');
    assert.equal(await evaluate("localStorage.getItem('edgar-site-lang')"),language);
    assert.equal(await evaluate("document.querySelector('[data-i18n=navAbout]').textContent"),language==='fr'?'À propos':'个人简介');
    assert.equal(await evaluate("document.querySelector('.project-card h3').textContent===window.SITE_PROJECTS[0].title[siteLanguage()]"),true);
    assert.match(await evaluate("document.querySelector('#supervision-ongoing-list').textContent"),language==='fr'?/hydrogène/:/制氢/);
    assert.equal(await evaluate("[...document.querySelectorAll('#supervision-completed-list h4')].every(n=>window.SITE_SUPERVISIONS.items.some(i=>i.title===n.textContent))"),true);
    await click('[data-map=world]');
    await select('#map-country','FRA');
    await select('#map-city','Nancy');
    assert.match(await evaluate("document.querySelector('#collaboration-cards').textContent"),language==='fr'?/Directrice de thèse/:/博士导师/);
    await click('[data-topic=environment]');
    assert.match(await evaluate("document.querySelector('.research-keywords').textContent"),language==='fr'?/Comptabilité carbone/:/碳核算/);
    await click('.network-reset');
    assert.deepEqual(await evaluate("window.SITE_PUBLICATIONS.items.map(p=>p.title)"),originalTitles);
    assert.equal(await evaluate("document.querySelector('#editorial-appointment .supervision-badge').textContent"),language==='fr'?'Éditeur chargé de l’évaluation':'评审编辑');
    await search('10.1016/j.energy.2021.122208');
    assert.equal(await evaluate("document.querySelectorAll('.publication-item').length"),1);
    await click('#publication-reset');
    await cdp('Page.reload');
    for(let retry=0;retry<50;retry++){
      if(await evaluate("document.documentElement.lang==='"+(language==='fr'?'fr':'zh-Hans')+"' && document.querySelectorAll('.publication-item').length===50"))break;
      await new Promise(resolve=>setTimeout(resolve,60));
    }
    assert.equal(await evaluate('siteLanguage()'),language);
    await evaluate('window.scrollTo({top:0,behavior:"instant"})');
    await screenshot('desktop-home-'+language);
  }
  for(const language of ['en','pt','fr','zh']) {
    await click('[data-lang='+language+']');
    const cvHref=await evaluate("document.querySelector('[data-short-cv]').getAttribute('href')");
    assert.equal(cvHref,'cv/'+language+'.html','CV must follow current page language');
    const response=await fetch(new URL(cvHref,baseUrl));
    assert.equal(response.status,200);
    const cvHtml=await response.text();
    assert.ok(cvHtml.includes('lang="'+({en:'en',pt:'pt-BR',fr:'fr',zh:'zh-Hans'}[language])+'"'));
    assert.ok(cvHtml.includes('window.print()'));
    assert.ok(cvHtml.includes('A critical review of holistic 4E approaches'));
    assert.ok(cvHtml.includes('10.1016/j.energy.2021.122208'));
    assert.ok(!cvHtml.includes('<aside class="draft">'));
    await cdp('Page.navigate',{url:new URL(cvHref,baseUrl).href});
    for(let retry=0;retry<50;retry++){
      if(await evaluate("Boolean(document.querySelector('.toolbar button'))"))break;
      await new Promise(resolve=>setTimeout(resolve,50));
    }
    assert.equal(await evaluate('document.documentElement.lang'),{en:'en',pt:'pt-BR',fr:'fr',zh:'zh-Hans'}[language]);
    assert.equal(await evaluate("document.querySelectorAll('.publications li').length"),5);
    await cdp('Emulation.setEmulatedMedia',{media:'print'});
    assert.equal(await evaluate("getComputedStyle(document.querySelector('.toolbar')).display"),'none');
    await screenshot('cv-print-'+language);
    await cdp('Emulation.setEmulatedMedia',{media:'screen',features:[{name:'prefers-reduced-motion',value:'reduce'}]});
    await cdp('Page.navigate',{url:baseUrl});
    for(let retry=0;retry<60;retry++){
      if(await evaluate("document.querySelectorAll('.publication-item').length===50"))break;
      await new Promise(resolve=>setTimeout(resolve,50));
    }
    assert.equal(await evaluate("document.querySelector('[data-short-cv]').getAttribute('href')"),'cv/'+language+'.html');
  }
  console.log('PASS CV follows EN/PT/FR/ZH, opens five approved articles and prints localized content');
  for(const language of ['en','pt','fr','zh']) {
    await click('[data-lang='+language+']');
    await click('[data-map=france]');
    assert.equal(await evaluate("document.querySelector('#map-france').hidden"),false);
    assert.equal(await evaluate("getComputedStyle(document.querySelector('#map-brafitec-legend')).display!=='none'"),true);
    assert.equal(await evaluate("document.querySelector('#map-country').value"),'FRA');
    assert.equal(await evaluate("document.querySelector('#map-brazil').hidden"),true);
    assert.equal(await evaluate("document.querySelector('#map-world').hidden"),true);
    await evaluate("document.querySelector('.france-marker[data-city=Nancy]').focus()");
    await key('Enter','Enter',13);
    assert.equal(await evaluate("document.querySelector('#map-city').value"),'Nancy');
    assert.match(await evaluate("document.querySelector('#collaboration-cards').textContent"),/Anélie Pétrissans/);
    await select('#map-territory','REU');
    assert.equal(await evaluate("document.querySelector('#map-country').value"),'FRA');
    assert.equal(await evaluate("document.querySelectorAll('#collaboration-cards details').length"),0,'No invented Reunion partnerships');
    await evaluate("document.querySelector('.france-territory[data-territory=MET]').focus()");
    await key(' ','Space',32);
    assert.equal(await evaluate("document.querySelector('#map-territory').value"),'MET');
    assert.equal(await evaluate("document.querySelectorAll('#collaboration-cards details').length"),6);
    await evaluate("document.querySelector('#map-france').scrollIntoView({block:'center',behavior:'instant'})");
    assert.equal(await evaluate("document.querySelectorAll('.map-city-leader').length"),0);
    assert.equal(await evaluate("[...document.querySelectorAll('.map-marker text')].every(n=>n.classList.contains('map-marker-label'))"),true);
    assert.equal(await evaluate("document.querySelectorAll('#map-france .brafitec-marker').length"),3);
    await select('#map-city','Nevers');
    assert.match(await evaluate("document.querySelector('#collaboration-cards').textContent"),/BRAFITEC/);
    assert.match(await evaluate("document.querySelector('#collaboration-cards').textContent"),/Béatrice Lay/);
    await select('#map-city','Bordeaux');
    assert.match(await evaluate("document.querySelector('#collaboration-cards').textContent"),/Antonio Rodriguez de Castro/);
    assert.equal(await evaluate("document.querySelector('.france-marker[data-city=Bordeaux]').classList.contains('brafitec-marker')"),true);
    await select('#map-city','Nevers');
    assert.equal(await evaluate("document.querySelectorAll('.france-marker.selected').length"),1);
    assert.equal(await evaluate("document.querySelector('.france-marker[data-city=Nevers]').getAttribute('aria-label')"),'Nevers');
    assert.equal(await evaluate("getComputedStyle(document.querySelector('.france-marker[data-city=Nancy] .map-marker-label')).visibility"),'hidden');
    await screenshot('france-map-'+language);
    await click('[data-map=brazil]');
    assert.equal(await evaluate("document.querySelector('#map-country').value"),'BRA');
    assert.equal(await evaluate("document.querySelector('#map-france').hidden"),true);
    assert.equal(await evaluate("getComputedStyle(document.querySelector('#map-brafitec-legend')).display!=='none'"),true);
    assert.equal(await evaluate("document.querySelectorAll('#map-brazil .brafitec-marker').length"),3);
    for (const city of ['Brasília','Itajubá','Salvador']) {
      await select('#map-city',city);
      assert.match(await evaluate("document.querySelector('#collaboration-cards').textContent"),/BRAFITEC/);
      assert.equal(await evaluate("[...document.querySelectorAll('#map-brazil .brafitec-marker')].some(m=>m.dataset.city==="+JSON.stringify(city)+" && getComputedStyle(m.querySelector('.outer')).fill==='rgb(167, 112, 36)')"),true);
    }
    await select('#map-city','');
    await screenshot('brazil-map-'+language);
    await click('[data-map=world]');
    await select('#map-country','BRA');
    assert.equal(await evaluate("getComputedStyle(document.querySelector('#map-brafitec-legend')).display"),'none');
    await select('#map-country','FRA');
    assert.equal(await evaluate("getComputedStyle(document.querySelector('#map-brafitec-legend')).display"),'none');
  }
  await click('[data-map=world]');
  for (const [code,name] of [['BRA','Grace Ferreira Ghesti'],['PRT','Ana F. Ferreira'],['TWN','Wei-Hsin Chen'],['FIN','Clara Mendoza-Martinez']]) {
    await select('#map-country',code);
    assert.match(await evaluate("document.querySelector('#collaboration-cards').textContent"),new RegExp(name.replaceAll('.','\\.')));
    assert.equal(await evaluate("[...document.querySelectorAll('#collaboration-cards a')].some(a=>a.href.startsWith('https://doi.org/'))"),true);
  }
  await click('[data-map=france]');
  await select('#map-city','Épinal');
  assert.match(await evaluate("document.querySelector('#collaboration-cards').textContent"),/Mathieu Pétrissans/);
  await click('[data-map=brazil]');
  await click('[data-map=world]');
  await select('#map-country','TWN');
  await evaluate("document.querySelector('#map-world').scrollIntoView({block:'center',behavior:'instant'})");
  assert.equal(await evaluate("Number(document.querySelector('#map-world').dataset.zoom)"),6);
  assert.equal(await evaluate("(() => {const w=document.querySelector('#map-world'),b=w.getBoundingClientRect(),r=w.querySelector('[data-code=TWN]').getBoundingClientRect();return w.scrollWidth>w.clientWidth && w.scrollHeight>w.clientHeight && r.width>12 && r.x+r.width/2>b.left && r.x+r.width/2<b.right;})()"),true);
  const panBox=await evaluate("(() => {const r=document.querySelector('#map-world').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,left:document.querySelector('#map-world').scrollLeft};})()");
  await cdp('Input.dispatchMouseEvent',{type:'mouseMoved',x:panBox.x,y:panBox.y});
  await cdp('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',buttons:1,clickCount:1,x:panBox.x,y:panBox.y});
  await cdp('Input.dispatchMouseEvent',{type:'mouseMoved',button:'left',buttons:1,x:panBox.x-50,y:panBox.y-25});
  await cdp('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',buttons:0,clickCount:1,x:panBox.x-50,y:panBox.y-25});
  assert.ok(await evaluate("document.querySelector('#map-world').scrollLeft")>panBox.left);
  assert.equal(await evaluate("document.querySelector('#map-country').value"),'TWN','Dragging must not select another country');
  await screenshot('world-map-taiwan-zoom');
  await click('#world-zoom-in');
  assert.equal(await evaluate("Number(document.querySelector('#map-world').dataset.zoom)"),8);
  await click('#world-zoom-reset');
  assert.equal(await evaluate("Number(document.querySelector('#map-world').dataset.zoom)"),1);
  assert.equal(await evaluate("document.querySelector('#map-world').scrollLeft+document.querySelector('#map-world').scrollTop"),0);
  await evaluate("document.querySelector('#map-world').focus()");
  await key('+','Equal',187);
  assert.equal(await evaluate("Number(document.querySelector('#map-world').dataset.zoom)"),1.5);
  await key('Home','Home',36);
  assert.equal(await evaluate("Number(document.querySelector('#map-world').dataset.zoom)"),1);
  await click('[data-map=brazil]');
  assert.equal(await evaluate("document.querySelector('#world-map-controls').hidden"),true);
  assert.equal(await evaluate("document.querySelectorAll('#research .research-diagram[aria-hidden=true]').length"),4);
  assert.equal(await evaluate("document.querySelectorAll('#research .research-lines').length"),0);
  await evaluate("document.querySelector('#research').scrollIntoView({block:'start',behavior:'instant'})");
  await screenshot('research-diagrams-desktop');
  console.log('PASS world zoom: Taiwan framing, scrollbars, real mouse drag, click suppression, limits, reset and keyboard');
  console.log('PASS France map: mainland/Reunion, four languages, city keyboard, empty unconfirmed region, preserved Brazil');
  console.log('PASS functional EN/PT/FR/ZH: translated interface, dynamic content, filters, maps, original academic titles and persistent preference');

  for (const width of [1920,1440,1280,1101,1100,1024,768,390,360,320]) {
    await cdp('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:width<500});
    for (const language of ['en','pt','fr','zh']) {
      await click('[data-lang='+language+']');
      const overflow=await evaluate("({viewport:document.documentElement.clientWidth,content:document.documentElement.scrollWidth,elements:[...document.querySelectorAll('body *')].filter(n=> {const r=n.getBoundingClientRect();return r.width&&getComputedStyle(n).position!=='fixed'&&r.right>document.documentElement.clientWidth+2;}).slice(0,8).map(n=>n.tagName+'.'+n.className)})");
      assert.equal(overflow.content,overflow.viewport, JSON.stringify({width,language,...overflow}));
      const headerOverflow=await evaluate("(() => {const header=document.querySelector('.header-inner').getBoundingClientRect(); return [...document.querySelectorAll('.header-inner > *')].filter(n=>getComputedStyle(n).display!=='none').some(n=>{const r=n.getBoundingClientRect();return r.right>header.right+1});})()");
      assert.equal(headerOverflow,false,'Header overflow '+width+' '+language);
    }
  }
  await cdp('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  for(const language of ['fr','zh']) {
    await click('[data-lang='+language+']');
    await evaluate('window.scrollTo({top:0,behavior:"instant"})');
    await screenshot('mobile-home-'+language);
    await click('[data-topic=environment]');
    await evaluate("document.querySelector('.research-network').scrollIntoView({block:'center',behavior:'instant'})");
    await screenshot('mobile-network-'+language);
    await click('.network-reset');
  }
  console.log('PASS responsive widths 320–1920 in EN/PT/FR/ZH');
  await cdp('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  await cdp('Emulation.setTouchEmulationEnabled',{enabled:true});
  await tap('[data-topic=hydrogen]');
  assert.equal(await evaluate("document.querySelector('[data-topic=hydrogen]').getAttribute('aria-pressed')"),'true');
  assert.equal(await evaluate("document.querySelectorAll('.research-keyword').length"),5);
  await screenshot('research-network-mobile');
  const touchStart=await evaluate("(() => {const n=document.querySelector('[data-topic=hydrogen]');const r=n.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,left:parseFloat(n.style.left)};})()");
  const scrollBeforeDrag=await evaluate('window.scrollY');
  await cdp('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:touchStart.x,y:touchStart.y}]});
  await cdp('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:touchStart.x-35,y:touchStart.y-20}]});
  await cdp('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  assert.ok(await evaluate("parseFloat(document.querySelector('[data-topic=hydrogen]').style.left)")<touchStart.left-3,'Touch drag moves node');
  assert.equal(await evaluate('window.scrollY'),scrollBeforeDrag,'Node drag should not scroll page');
  await new Promise(resolve=>setTimeout(resolve,400));
  await tap('.network-reset');
  assert.equal(await evaluate("document.querySelectorAll('.research-keyword').length"),0);
  await evaluate("document.querySelector('#research').scrollIntoView({block:'start',behavior:'instant'})");
  await screenshot('research-diagrams-mobile');
  await tap('.project-details summary');
  assert.equal(await evaluate("document.querySelector('.project-details').open"),true);
  await screenshot('project-story-mobile');
  await tap('.project-details summary');
  await tap('[data-map=world]');
  await select('#map-country','TWN');
  await tap('#world-zoom-in');
  assert.equal(await evaluate("Number(document.querySelector('#map-world').dataset.zoom)"),8);
  await evaluate("document.querySelector('#map-world').scrollIntoView({block:'center',behavior:'instant'})");
  await new Promise(resolve=>setTimeout(resolve,150));
  assert.equal(await evaluate("(() => {const b=document.querySelector('#map-world').getBoundingClientRect(),r=document.querySelector('#map-world [data-code=TWN]').getBoundingClientRect();return r.x+r.width/2>b.left && r.x+r.width/2<b.right;})()"),true,'Taiwan stays in view on mobile');
  const mobileWorld=await evaluate("(() => {const w=document.querySelector('#map-world'),r=w.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,left:w.scrollLeft};})()");
  await cdp('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:mobileWorld.x,y:mobileWorld.y}]});
  await cdp('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:mobileWorld.x-60,y:mobileWorld.y-20}]});
  await cdp('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  await screenshot('world-map-mobile-taiwan');
  const mobilePanAfter=await evaluate("({left:document.querySelector('#map-world').scrollLeft,top:document.querySelector('#map-world').scrollTop,width:document.querySelector('#map-world').clientWidth,scroll:document.querySelector('#map-world').scrollWidth,hit:document.elementFromPoint("+mobileWorld.x+","+mobileWorld.y+")?.tagName})");
  assert.notEqual(mobilePanAfter.left,mobileWorld.left,JSON.stringify({mobileWorld,mobilePanAfter}));
  assert.equal(await evaluate("document.documentElement.scrollWidth===document.documentElement.clientWidth"),true);
  await screenshot('world-map-mobile-taiwan');
  await tap('#world-zoom-reset');
  assert.equal(await evaluate("Number(document.querySelector('#map-world').dataset.zoom)"),1);
  await tap('[data-map=france]');
  await tap('.france-territory[data-territory=REU]');
  assert.equal(await evaluate("document.querySelector('#map-territory').value"),'REU');
  assert.equal(await evaluate("document.querySelectorAll('#collaboration-cards details').length"),0);
  await screenshot('france-map-mobile-reunion');
  await tap('[data-map=brazil]');
  await tap('.menu-toggle');
  assert.equal(await evaluate("document.querySelector('.menu-toggle').getAttribute('aria-expanded')"),'true');
  await tap('.nav-activities summary');
  await tap('.nav-submenu a[href="#supervision"]');
  assert.equal(await evaluate("document.querySelector('.menu-toggle').getAttribute('aria-expanded')"),'false');
  assert.equal(await evaluate("document.activeElement.id"),'supervision');
  await evaluate("document.querySelector('#supervision').scrollIntoView({behavior:'instant'})");
  await screenshot('mobile-supervision');
  await evaluate("document.querySelector('#undergraduate').scrollIntoView({block:'start',behavior:'instant'})");
  if(undergradCounts[0]>4){
    await tap('#supervision-undergraduate-research-toggle');
    assert.equal(await evaluate("document.querySelectorAll('#supervision-undergraduate-research-list > li:not([hidden])').length"),undergradCounts[0]);
    await tap('#supervision-undergraduate-research-toggle');
  }
  await screenshot('undergraduate-mobile');
  await evaluate("document.querySelector('#publications').scrollIntoView({behavior:'instant'})");
  await tap('#publication-toggle');
  assert.equal(await evaluate("document.querySelectorAll('.publication-item:not([hidden])').length"),50);
  await tap('#publication-toggle');
  assert.equal(await evaluate("document.querySelectorAll('.publication-item:not([hidden])').length"),4);
  await screenshot('mobile-publications');
  await evaluate("document.querySelector('#editorial').scrollIntoView({behavior:'instant'})");
  await screenshot('mobile-editorial');
  await evaluate('window.scrollTo({top:0,behavior:"instant"})');
  await evaluate("document.activeElement.blur(); window.scrollTo({top:0,behavior:'instant'});");
  await screenshot('mobile-home');
  assert.deepEqual(errors,[]);
  assert.deepEqual(failedAssets,[]);
  console.log('PASS mobile touch, local assets, no JavaScript exceptions');
}
main().catch(error=>{console.error(error);process.exitCode=1;}).finally(()=>{
  clearTimeout(timer); if(socket) socket.close(); browser.kill();
});
