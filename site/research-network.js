/* Conceptual exploration only: these edges do not assert bibliographic links. */
(() => {
  const host = document.querySelector('.research-art');
  if (!host) return;
  const graph = host.querySelector('.research-network');
  const original = host.querySelector('.network-original');
  const nodes = host.querySelector('.research-nodes');
  const keywords = host.querySelector('.research-keywords');
  const edges = host.querySelector('.research-edges');
  const switcher = host.querySelector('.network-view-switch');
  const status = host.querySelector('.network-selection');
  const stage = host.querySelector('.network-stage');
  const motionButton = host.querySelector('.network-motion');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const topics = [
    {id:'bio', key:'graphBio', x:29, y:28, related:['thermo','environment'], words:['graphBiomass','graphWaste','graphSolidFuels','graphPellets','graphBiochar'], points:[[12,10],[35,8],[55,12],[10,41],[35,46]]},
    {id:'thermo', key:'graphThermo', x:71, y:28, related:['bio','hydrogen','model'], words:['graphTorrefaction','graphPyrolysis','graphHTC','graphGasification','graphCatalysis'], points:[[64,8],[87,12],[90,44],[65,46],[43,12]]},
    {id:'hydrogen', key:'graphHydrogen', x:79, y:60, related:['thermo','environment'], words:['graphH2Production','graphSyngas','graphSteamGas','graphSAF','graphBiodiesel'], points:[[90,45],[89,80],[67,93],[54,57],[58,40]]},
    {id:'environment', key:'graphEnvironment', x:48, y:78, related:['bio','hydrogen','model'], words:['graphExergy4E','graphLCA','graphCarbonAccounting','graphCarbonFootprint','graphEmissionQuantification','graphCarbonCredits'], points:[[13,73],[17,91],[40,96],[64,96],[85,87],[88,73]]},
    {id:'model', key:'graphModel', x:20, y:57, related:['thermo','environment'], words:['graphKinetics','graphNumerical','graphOptimization','graphRSM','graphMCDA'], points:[[10,41],[10,75],[31,90],[42,61],[34,43]]},
  ];
  const pairs = [['bio','thermo'],['bio','environment'],['thermo','hydrogen'],['thermo','model'],['hydrogen','environment'],['model','environment']];
  topics.forEach((t,i)=>Object.assign(t,{homeX:t.x,homeY:t.y,vx:0,vy:0,phase:i*1.7}));
  let paused=false, inView=false, frame=0, previousTime=0, drag=null;
  const clamp=(v,min,max)=>Math.min(max,Math.max(min,v));
  let pinned = null, preview = null, focused = null;
  const active = () => preview || focused || pinned;
  function line(a,b,cls) {
    // Connect the dots above labels, rather than crossing through their text.
    const bounds=stage.getBoundingClientRect();
    const point=topic=>{
      if (!topic.id || !bounds.height) return topic;
      const rect=nodes.querySelector(`[data-topic="${topic.id}"]`).getBoundingClientRect();
      return {x:topic.x,y:(rect.top+7-bounds.top)/bounds.height*100};
    };
    a=point(a);b=point(b);
    const el = document.createElementNS('http://www.w3.org/2000/svg','line');
    for (const [key,value] of Object.entries({x1:a.x,y1:a.y,x2:b.x,y2:b.y})) el.setAttribute(key,value);
    el.setAttribute('class',cls); edges.append(el); return el;
  }
  function position(el,x,y) { el.style.left=x+'%'; el.style.top=y+'%'; }
  function draw(announce=false) {
    const selected = topics.find(t => t.id === active());
    graph.classList.toggle('has-selection',Boolean(selected));
    edges.replaceChildren(); keywords.replaceChildren();
    pairs.forEach(([a,b]) => line(topics.find(t=>t.id===a),topics.find(t=>t.id===b),selected && [a,b].includes(selected.id) ? 'is-connected' : ''));
    topics.forEach(topic => {
      const button=nodes.querySelector(`[data-topic="${topic.id}"]`);
      button.textContent=siteText(topic.key);
      button.title=siteText('graphDragHelp');
      button.setAttribute('aria-pressed',String(pinned===topic.id));
      button.classList.toggle('is-active',selected?.id===topic.id);
      button.classList.toggle('is-related',Boolean(selected?.related.includes(topic.id)));
    });
    if (selected) selected.words.forEach((key,i) => {
      const [x,y]=selected.points[i];
      line(selected,{x,y},'keyword-edge');
      const word=document.createElement('span'); word.className='research-keyword';
      word.textContent=siteText(key); position(word,x,y); keywords.append(word);
    });
    if (announce) status.textContent=selected ? `${siteText(selected.key)}: ${selected.words.map(siteTextKey=>siteText(siteTextKey)).join(' · ')}` : siteText('graphHelp');
    motionButton.disabled=reducedMotion.matches;
    motionButton.textContent=siteText(reducedMotion.matches?'graphMotionReduced':paused?'graphResume':'graphPause');
    motionButton.setAttribute('aria-pressed',String(paused||reducedMotion.matches));
    geometry();
  }
  // Update only positions and existing edges each frame; keep labels and focus intact.
  function geometry(){
    const bounds=stage.getBoundingClientRect(); if(!bounds.height)return;
    topics.forEach(t=>position(nodes.querySelector(`[data-topic="${t.id}"]`),t.x,t.y));
    const dot=t=>{
      const r=nodes.querySelector(`[data-topic="${t.id}"]`).getBoundingClientRect();
      return {x:t.x,y:(r.top+7-bounds.top)/bounds.height*100};
    };
    const existing=[...edges.children];
    const set=(el,a,b)=>{if(el)for(const [k,v] of Object.entries({x1:a.x,y1:a.y,x2:b.x,y2:b.y}))el.setAttribute(k,v);};
    pairs.forEach(([a,b],i)=>set(existing[i],dot(topics.find(t=>t.id===a)),dot(topics.find(t=>t.id===b))));
    const selected=topics.find(t=>t.id===active());
    if(selected) [...keywords.children].forEach((word,i)=>{
      const [px,py]=selected.points[i];
      const x=clamp(px+(selected.x-selected.homeX)*.65,10,90);
      const y=clamp(py+(selected.y-selected.homeY)*.65,7,95);
      position(word,x,y);const r=word.getBoundingClientRect();
      set(existing[pairs.length+i],dot(selected),{x,y:(r.top+2-bounds.top)/bounds.height*100});
    });
  }
  function canAnimate(){return inView&&!graph.hidden&&!document.hidden&&!paused&&!reducedMotion.matches;}
  function schedule(){if(canAnimate()&&!frame)frame=requestAnimationFrame(tick);}
  function tick(time){
    frame=0;if(!canAnimate()){previousTime=0;return;}
    const dt=Math.min((time-(previousTime||time-16.7))/16.7,2);previousTime=time;
    topics.forEach(t=>{
      if(drag?.topic===t||active()===t.id){t.vx=t.vy=0;return;}
      // Anchored springs preserve the readable composition while neighbours respond.
      let fx=(t.homeX+Math.sin(time*.00035+t.phase)*2.1-t.x)*.012;
      let fy=(t.homeY+Math.cos(time*.00029+t.phase)*1.7-t.y)*.012;
      topics.forEach(other=>{
        if(t===other)return;const dx=t.x-other.x,dy=t.y-other.y;
        const distance=Math.max(1,Math.hypot(dx,dy));
        if(distance<29){fx+=dx/distance*(29-distance)*.012;fy+=dy/distance*(29-distance)*.012;}
        if(pairs.some(pair=>pair.includes(t.id)&&pair.includes(other.id))){
          const rest=Math.hypot(t.homeX-other.homeX,t.homeY-other.homeY);
          fx-=dx/distance*(distance-rest)*.002;fy-=dy/distance*(distance-rest)*.002;
        }
      });
      t.vx=(t.vx+fx*dt)*Math.pow(.85,dt);t.vy=(t.vy+fy*dt)*Math.pow(.85,dt);
      t.x=clamp(t.x+t.vx*dt,17,83);t.y=clamp(t.y+t.vy*dt,22,80);
    });
    geometry();schedule();
  }
  function motionChanged(){cancelAnimationFrame(frame);frame=0;previousTime=0;draw();schedule();}
  topics.forEach(topic => {
    const button=document.createElement('button'); button.type='button';
    button.className='research-node'; button.dataset.topic=topic.id;
    button.setAttribute('aria-describedby','network-drag-help');
    position(button,topic.x,topic.y); nodes.append(button);
    button.addEventListener('pointerenter',event=>{if(event.pointerType==='mouse'&&!drag){preview=topic.id;draw();}});
    button.addEventListener('pointerleave',()=>{preview=null;draw();});
    button.addEventListener('focus',()=>{focused=topic.id;draw(true);});
    button.addEventListener('blur',()=>{focused=null;draw();});
    let suppressClickUntil=0;
    button.addEventListener('click',()=>{if(performance.now()<suppressClickUntil)return;pinned=pinned===topic.id?null:topic.id;preview=null;focused=null;draw(true);});
    button.addEventListener('pointerdown',event=>{
      if(event.button!==0)return;
      drag={topic,pointerId:event.pointerId,startX:event.clientX,startY:event.clientY,x:topic.x,y:topic.y,moved:false};
      button.setPointerCapture(event.pointerId);
    });
    button.addEventListener('pointermove',event=>{
      if(!drag||drag.pointerId!==event.pointerId||drag.topic!==topic)return;
      const dx=event.clientX-drag.startX,dy=event.clientY-drag.startY;
      if(!drag.moved&&Math.hypot(dx,dy)<5)return;
      drag.moved=true;button.classList.add('is-dragging');
      const r=stage.getBoundingClientRect();
      topic.x=clamp(drag.x+dx/r.width*100,17,83);topic.y=clamp(drag.y+dy/r.height*100,22,80);
      topic.vx=topic.vy=0;geometry();
    });
    const release=event=>{
      if(!drag||drag.topic!==topic||drag.pointerId!==event.pointerId)return;
      if(drag.moved){suppressClickUntil=performance.now()+400;pinned=topic.id;}
      drag=null;button.classList.remove('is-dragging');
      if(button.hasPointerCapture(event.pointerId))button.releasePointerCapture(event.pointerId);
      draw(true);schedule();
    };
    button.addEventListener('pointerup',release);button.addEventListener('pointercancel',release);
    button.addEventListener('lostpointercapture',release);
    button.addEventListener('keydown',event=>{
      const delta={ArrowLeft:[-3,0],ArrowRight:[3,0],ArrowUp:[0,-3],ArrowDown:[0,3]}[event.key];
      if(!delta)return;event.preventDefault();topic.x=clamp(topic.x+delta[0],17,83);topic.y=clamp(topic.y+delta[1],22,80);geometry();
    });
  });
  function reset(){
    if(drag){
      const current=drag;drag=null;
      const button=nodes.querySelector(`[data-topic="${current.topic.id}"]`);
      button.classList.remove('is-dragging');
      if(button.hasPointerCapture(current.pointerId))button.releasePointerCapture(current.pointerId);
    }
    pinned=null;preview=null;focused=null;
    topics.forEach(t=>{t.x=t.homeX;t.y=t.homeY;t.vx=t.vy=0;});draw(true);
  }
  // Touch activation remains responsive after a captured node-drag gesture.
  function activateControl(button,action){
    let lastTouch=0;
    button.addEventListener('pointerup',event=>{
      if(event.pointerType!=='touch'||button.disabled)return;
      const r=button.getBoundingClientRect();
      if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)return;
      lastTouch=performance.now();action();
    });
    button.addEventListener('click',event=>{
      if(event.detail!==0&&performance.now()-lastTouch<700)return;
      action();
    });
  }
  activateControl(motionButton,()=>{paused=!paused;motionChanged();});
  activateControl(host.querySelector('.network-reset'),reset);
  host.addEventListener('keydown',event=>{if(event.key==='Escape'){reset();event.stopPropagation();}});
  switcher.querySelectorAll('button').forEach(button=>activateControl(button,()=>{
    const interactive=button.dataset.networkView==='interactive';
    graph.hidden=!interactive;original.hidden=interactive;
    host.classList.toggle('show-original',!interactive);
    switcher.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
    motionChanged();
  }));
  document.addEventListener('site:language',()=>{graph.setAttribute('aria-label',siteText('graphRegion'));draw(true);});
  graph.setAttribute('role','group');graph.setAttribute('aria-label',siteText('graphRegion'));
  graph.hidden=false;original.hidden=true;switcher.hidden=false;draw();
  new ResizeObserver(()=>draw()).observe(host.querySelector('.network-stage'));
  new IntersectionObserver(entries=>{inView=entries[0].isIntersecting;motionChanged();}).observe(stage);
  reducedMotion.addEventListener('change',motionChanged);
  document.addEventListener('visibilitychange',motionChanged);
})();
