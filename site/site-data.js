/* Public bibliography and collaboration atlas. */
(() => {
  'use strict';

  const lang = () => siteLanguage();
  const t = siteText;
  const element = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const link = (url, text, className) => {
    const node = element('a', className, text);
    node.href = url;
    node.target = '_blank';
    node.rel = 'noopener noreferrer';
    return node;
  };
  const safeLink = (url, text) => {
    try {
      const parsed = new URL(url);
      if (parsed.protocol === 'https:') return link(parsed.href, text);
    } catch (_) {}
    return null;
  };

  const publications = window.SITE_PUBLICATIONS;
  const pubHost = document.getElementById('publication-list');
  const filters = [...document.querySelectorAll('[data-filter]')];
  const categories = {
    bioenergy: 'filterBioenergy', modeling: 'filterModeling',
    sustainability: 'filterSustainability', other: 'filterOther',
  };
  const note = document.querySelector('.pub-note');
  const imported = publications.source === 'lattes';
  if (imported) note.removeAttribute('data-i18n');
  let filter = 'all';
  let publicationsExpanded=false;
  const publicationToggle=document.getElementById('publication-toggle');
  const search = document.getElementById('publication-search');
  const yearSelect = document.getElementById('publication-year');
  const resultCount = document.getElementById('publication-results');
  const normalizeSearch = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();
  const years = [...new Set(publications.items.map(item => item.year))].sort((a, b) => b - a);
  yearSelect.replaceChildren(new Option(t('filterAll'), ''),
    ...years.map(year => new Option(String(year), String(year))));

  function renderPublications() {
    pubHost.replaceChildren();
    yearSelect.options[0].textContent = t('filterAll');
    const query = normalizeSearch(search.value.trim());
    let count = 0;
    for (const publication of publications.items) {
      if (filter !== 'all' && !publication.categories.includes(filter)) continue;
      if (yearSelect.value && String(publication.year) !== yearSelect.value) continue;
      const searchable = normalizeSearch([publication.title, publication.authors,
        publication.journal, publication.doi].join(' '));
      if (query && !searchable.includes(query)) continue;
      count += 1;
      const article = element('article', 'publication-item');
      article.dataset.category = publication.categories.join(' ');
      article.hidden=!publicationsExpanded && count>4;
      article.append(element('div', 'publication-year', String(publication.year)));
      const body = element('div', 'publication-body');
      body.append(element('p', 'pub-journal', publication.journal), element('h3', '', publication.title));
      if (publication.authors) body.append(element('p', 'pub-authors', publication.authors));
      const tags = element('div', 'tag-row');
      for (const category of publication.categories) tags.append(element('span', '', t(categories[category])));
      body.append(tags);
      article.append(body);
      const doi = publication.doi || '';
      if (/^10\.\d{4,9}\/\S+$/.test(doi)) {
        const doiLink = link('https://doi.org/' + encodeURI(doi), 'DOI ↗', 'publication-link');
        doiLink.setAttribute('aria-label', t('ariaDoi', { title: publication.title }));
        article.append(doiLink);
      }
      pubHost.append(article);
    }
    if (!pubHost.childElementCount) pubHost.append(element('p', 'map-no-partners', t('pubEmpty')));
    resultCount.textContent = t(count === 1 ? 'pubResultOne' : 'pubResultMany', {
      count: new Intl.NumberFormat(lang()).format(count),
    });
    publicationToggle.hidden=count<=4;
    publicationToggle.setAttribute('aria-expanded',String(publicationsExpanded));
    publicationToggle.textContent=t(publicationsExpanded?'pubShowLess':'pubShowAll',{count:new Intl.NumberFormat(lang()).format(count)});
    if (imported) note.textContent = t('pubImported');
  }

  const resetPublicationPreview=()=>{publicationsExpanded=false;renderPublications();};
  search.addEventListener('input', resetPublicationPreview);
  yearSelect.addEventListener('change', resetPublicationPreview);
  publicationToggle.addEventListener('click',()=>{
    publicationsExpanded=!publicationsExpanded;renderPublications();
    if(!publicationsExpanded)publicationToggle.scrollIntoView({block:'nearest',behavior:'instant'});
  });
  document.getElementById('publication-reset').addEventListener('click', () => {
    search.value = '';
    yearSelect.value = '';
    filters.find(button => button.dataset.filter === 'all').click();
  });
  for (const button of filters) {
    button.addEventListener('click', () => {
      filter = button.dataset.filter;
      publicationsExpanded=false;
      for (const control of filters) {
        const active = control === button;
        control.classList.toggle('active', active);
        control.setAttribute('aria-pressed', String(active));
      }
      renderPublications();
    });
  }
  renderPublications();
  document.addEventListener('site:language', renderPublications);

  const world = document.getElementById('map-world');
  const brazil = document.getElementById('map-brazil');
  const france = document.getElementById('map-france');
  const territorySelect = document.getElementById('map-territory');
  const territoryField = document.querySelector('.map-territory-field');
  const franceNote = document.querySelector('.map-france-note');
  const host = document.getElementById('collaboration-cards');
  const title = document.getElementById('map-selection-title');
  const count = document.getElementById('map-selection-count');
  const countrySelect = document.getElementById('map-country');
  const citySelect = document.getElementById('map-city');
  const entries = window.SITE_COLLABORATIONS.filter(record => record.public === true && record.scope !== 'negotiation');
  const countries = [...new Set(entries.map(record => record.country))];
  const worldSvg=world.querySelector('svg');
  const zoomControls=document.getElementById('world-map-controls');
  const zoomIn=document.getElementById('world-zoom-in');
  const zoomOut=document.getElementById('world-zoom-out');
  let worldZoom=1, lastWorldWidth=0, zoomRevision=0, pendingWorldCenter=null;
  function applyWorldZoom(value, center=null) {
    if (!world.clientWidth) return;
    if(!center && pendingWorldCenter) center=pendingWorldCenter;
    lastWorldWidth=world.clientWidth;
    const vb=worldSvg.viewBox.baseVal;
    const previousWidth=worldSvg.getBoundingClientRect().width || world.clientWidth;
    const cx=(world.scrollLeft+world.clientWidth/2)/previousWidth;
    const cy=(world.scrollTop+world.clientHeight/2)/previousWidth;
    worldZoom=Math.max(1,Math.min(8,value));
    const width=world.clientWidth*worldZoom;
    const stage=document.getElementById('world-map-stage');
    stage.style.width=width+'px';stage.style.height=(width*vb.height/vb.width)+'px';
    worldSvg.style.width=width+'px';worldSvg.style.height=(width*vb.height/vb.width)+'px';
    const left=(center?center.x/vb.width:cx)*width-world.clientWidth/2;
    const top=(center?center.y/vb.width:cy)*width-world.clientHeight/2;
    const revision=++zoomRevision;
    world.scrollTo({left,top,behavior:'instant'});
    requestAnimationFrame(()=>{if(revision===zoomRevision&&!world.hidden) world.scrollTo({left,top,behavior:'instant'});});
    world.dataset.zoom=String(worldZoom);
    world.style.touchAction=worldZoom>1?'none':'pan-x pan-y';
    document.getElementById('world-zoom-level').value=Math.round(worldZoom*100)+'%';
    zoomOut.disabled=worldZoom===1;zoomIn.disabled=worldZoom===8;
  }
  function resetWorldZoom(){pendingWorldCenter=null;applyWorldZoom(1,{x:0,y:0});world.scrollLeft=0;world.scrollTop=0;}
  function focusWorldCountry(code){
    const paths=[...world.querySelectorAll('.country')].filter(p=>p.dataset.code===code);
    if(!paths.length)return;
    const boxes=paths.map(p=>p.getBBox());
    const x=Math.min(...boxes.map(b=>b.x)),y=Math.min(...boxes.map(b=>b.y));
    const right=Math.max(...boxes.map(b=>b.x+b.width)),bottom=Math.max(...boxes.map(b=>b.y+b.height));
    const vb=worldSvg.viewBox.baseVal;
    const fit=Math.min(vb.width*.55/Math.max(1,right-x),world.clientHeight/world.clientWidth*vb.width*.65/Math.max(1,bottom-y));
    pendingWorldCenter={x:(x+right)/2,y:(y+bottom)/2};
    applyWorldZoom(Math.min(6,Math.max(2,fit)),pendingWorldCenter);
  }
  function bindZoomControl(button, activate) {
    let directTouch=0;
    button.addEventListener('pointerup',event=>{
      if(!['touch','pen'].includes(event.pointerType))return;
      event.preventDefault();directTouch=performance.now();activate();
    });
    button.addEventListener('click',event=>{
      if(['touch','pen'].includes(event.pointerType)||(event.detail>0&&performance.now()-directTouch<700))return;
      activate();
    });
  }
  bindZoomControl(zoomIn,()=>applyWorldZoom(worldZoom*1.5));
  bindZoomControl(zoomOut,()=>applyWorldZoom(worldZoom/1.5));
  bindZoomControl(document.getElementById('world-zoom-reset'),resetWorldZoom);
  world.addEventListener('keydown',event=>{
    if(event.target!==world)return;
    if(event.key==='+'||event.key==='='){event.preventDefault();applyWorldZoom(worldZoom*1.5);}
    if(event.key==='-'){event.preventDefault();applyWorldZoom(worldZoom/1.5);}
    if(event.key==='Home'){event.preventDefault();resetWorldZoom();}
  });
  let pan=null,suppressMapClick=false;
  world.addEventListener('pointerdown',event=>{
    if(!['mouse','touch','pen'].includes(event.pointerType)||event.button!==0||worldZoom===1)return;
    zoomRevision++;pendingWorldCenter=null;
    pan={id:event.pointerId,x:event.clientX,y:event.clientY,left:world.scrollLeft,top:world.scrollTop,moved:false};
  });
  world.addEventListener('pointermove',event=>{
    if(!pan||pan.id!==event.pointerId)return;
    const dx=event.clientX-pan.x,dy=event.clientY-pan.y;
    if(!pan.moved&&Math.hypot(dx,dy)<5)return;
    pan.moved=true;world.setPointerCapture(event.pointerId);world.classList.add('panning');
    world.scrollLeft=pan.left-dx;world.scrollTop=pan.top-dy;event.preventDefault();
  });
  function finishPan(event){
    if(!pan||pan.id!==event.pointerId)return;
    suppressMapClick=pan.moved;pan=null;world.classList.remove('panning');
    if(world.hasPointerCapture(event.pointerId))world.releasePointerCapture(event.pointerId);
    setTimeout(()=>{suppressMapClick=false;},0);
  }
  world.addEventListener('pointerup',finishPan);world.addEventListener('pointercancel',finishPan);
  world.addEventListener('click',event=>{if(suppressMapClick){event.preventDefault();event.stopImmediatePropagation();}},true);
  function positionPendingCountry(){
    if(!pendingWorldCenter||world.hidden)return;
    const vb=worldSvg.viewBox.baseVal,width=worldSvg.getBoundingClientRect().width;
    world.scrollTo({left:pendingWorldCenter.x/vb.width*width-world.clientWidth/2,top:pendingWorldCenter.y/vb.width*width-world.clientHeight/2,behavior:'instant'});
  }
  new ResizeObserver(()=>requestAnimationFrame(positionPendingCountry)).observe(document.getElementById('world-map-stage'));
  new IntersectionObserver(items=>{if(items.some(item=>item.isIntersecting)) requestAnimationFrame(positionPendingCountry);}).observe(world);
  new ResizeObserver(()=>{if(world.clientWidth && Math.abs(world.clientWidth-lastWorldWidth)>1) applyWorldZoom(worldZoom);}).observe(world);

  const countryPaths = [...world.querySelectorAll('.country')].filter(path => countries.includes(path.dataset.code));
  const markers = new Map();
  const alpha2 = {
    ARG: 'AR', AUS: 'AU', AUT: 'AT', BEL: 'BE', BOL: 'BO', BRA: 'BR', CAN: 'CA', CHE: 'CH',
    CHL: 'CL', CHN: 'CN', COL: 'CO', DEU: 'DE', DNK: 'DK', ESP: 'ES', FIN: 'FI', FRA: 'FR',
    GBR: 'GB', IDN: 'ID', IND: 'IN', ITA: 'IT', JPN: 'JP', MEX: 'MX', MYS: 'MY', NLD: 'NL',
    NOR: 'NO', NZL: 'NZ', PER: 'PE', PRT: 'PT', PRY: 'PY', SWE: 'SE', TWN: 'TW', URY: 'UY',
    USA: 'US', ZAF: 'ZA',
  };
  const names = {
    en: new Intl.DisplayNames('en', { type: 'region' }),
    pt: new Intl.DisplayNames('pt-BR', { type: 'region' }),
    fr: new Intl.DisplayNames('fr', { type: 'region' }),
    zh: new Intl.DisplayNames('zh-Hans', { type: 'region' }),
  };
  const countryName = code => alpha2[code]
    ? names[lang()].of(alpha2[code])
    : countryPaths.find(path => path.dataset.code === code)?.dataset.name || code;
  const scopeLabels = {
    personal: 'collabPersonal', institutional: 'collabInstitutional',
    academic: 'collabAcademic', research: 'collabResearch',
  };
  const statusLabels = {
    active: 'collabActive', completed: 'collabCompleted', historical: 'collabHistorical',
  };

  let view = 'world';
  let country = countries.includes('BRA') ? 'BRA' : countries[0] || '';
  let worldCountry = country;
  let city = '';
  let territory = '';
  const cityName = name => name==='campus-pending' ? t('mapCampusPending') : name;
  const territoryOf = record => record.territory ||
    (record.country==='FRA' && record.lat>40 && record.lat<52 && record.lon>-7 && record.lon<11 ? 'MET' :
      record.country==='FRA' && record.lat>-22 && record.lat<-20 && record.lon>55 && record.lon<56 ? 'REU' : '');
  const territoryName = code => t(code==='REU'?'mapReunion':'mapMetropolitan');

  function fillOptions(select, options, selected) {
    select.replaceChildren(...options.map(([value, label]) => new Option(label, value)));
    select.value = selected;
  }

  function appendList(parent, label, values) {
    if (!values.length) return;
    parent.append(element('p', 'collab-small', t(label)));
    const list = element('ul');
    for (const value of values) {
      const item = element('li');
      item.append(value);
      list.append(item);
    }
    parent.append(list);
  }

  function renderRecord(record) {
    const section = element('div', 'collab-record');
    const type = t(scopeLabels[record.scope], { owner: record.institutional_owner });
    const status = statusLabels[record.status] ? t(statusLabels[record.status]) : '';
    section.append(element('span', 'collab-type', status ? type + ' · ' + status : type));
    if(record.program==='BRAFITEC') section.append(element('p','collab-brafitec',t('mapBrafitec')));
    section.append(element('p', '', record['relation_' + lang()]));
    if (record.topic) section.append(element('p', '', t('mapTopic') + ' · ' + record.topic[lang()]));
    if (record.period) {
      const { start, end } = record.period;
      const period = start && end ? (start === end ? String(start) : start + '–' + end)
        : t(start ? 'mapPeriodStart' : 'mapPeriodEnd', { year: start || end });
      section.append(element('p', '', t('mapPeriod') + ' · ' + period));
    }
    appendList(section, 'mapPeople', record.people.map(person => {
      const text = person.name + ' — ' + person['role_' + lang()];
      return safeLink(person.url, text) || text;
    }));
    appendList(section, 'mapPublications', (record.publications || []).map(item =>
      safeLink(item.url, item.title) || item.title));
    const website = safeLink(record.website, t('mapWebsite'));
    if (website) section.append(website);
    appendList(section, 'mapLinks', (record.links || []).flatMap(item => {
      const itemLink = safeLink(item.url, item.label[lang()]);
      return itemLink ? [itemLink] : [];
    }));
    return section;
  }

  function renderMap(preserveOpen = false) {
    document.getElementById('map-brafitec-legend').hidden = view === 'world';
    const options = view === 'world' ? countries : [view==='brazil'?'BRA':'FRA'];
    const countryOptions = options.map(code => [code, countryName(code)])
      .sort((a, b) => a[1].localeCompare(b[1], lang()));
    fillOptions(countrySelect, countryOptions.length ? countryOptions : [['', t('mapNoCountries')]], country);
    countrySelect.disabled = countryOptions.length === 0;

    territoryField.hidden=view!=='france';
    fillOptions(territorySelect,[['',t('mapAllFrance')],['MET',t('mapMetropolitan')],['REU',t('mapReunion')]],territory);
    const inCountry = entries.filter(record => record.country === country &&
      (view!=='france'||!territory||territoryOf(record)===territory));
    const cities = [...new Set(inCountry.map(record => record.city))].sort((a, b) => a.localeCompare(b, lang()));
    fillOptions(citySelect, [['', t('mapAllCities')], ...cities.map(name => [name, cityName(name)])], city);
    citySelect.disabled = cities.length === 0;

    for (const path of countryPaths) {
      const code = path.dataset.code;
      path.setAttribute('aria-label', countryName(code));
      path.setAttribute('aria-pressed', String(code === country));
      path.classList.toggle('selected-country', code === country);
    }
    for (const [name, marker] of markers) {
      const markerCity=marker.dataset.city||name;
      const selected=city===markerCity && marker.dataset.country===country &&
        (view!=='france'||!territory||marker.dataset.territory===territory);
      marker.setAttribute('aria-label', markerCity);
      marker.setAttribute('aria-pressed', String(selected));
      marker.classList.toggle('selected', selected);
    }
    france.querySelectorAll('.france-territory[data-territory]').forEach(node=>{
      node.setAttribute('aria-label',territoryName(node.dataset.territory));
      node.setAttribute('aria-pressed',String(territory===node.dataset.territory));
      node.classList.toggle('selected',territory===node.dataset.territory);
    });

    const institutions = new Map();
    for (const record of inCountry) {
      if (city && record.city !== city) continue;
      const key = JSON.stringify([territoryOf(record),record.city, record.institution]);
      if (!institutions.has(key)) institutions.set(key, []);
      institutions.get(key).push(record);
    }

    const place = (city && cityName(city)) || (view==='france' && territory ? territoryName(territory) : country ? countryName(country) : t('mapSelectionDefault'));
    title.textContent = place;
    count.textContent = t(institutions.size === 1 ? 'mapCountOne' : 'mapCountMany', {
      place, count: institutions.size,
    });
    const openIds = new Set([...host.querySelectorAll('details[open]')].map(card => card.id));
    host.replaceChildren();
    if (!institutions.size) host.append(element('p', 'map-no-partners', t('mapEmpty')));
    for (const records of institutions.values()) {
      const first = records[0];
      const card = element('details', 'collab-card');
      card.id = 'partner-' + first.id;
      card.open = preserveOpen ? openIds.has(card.id) : host.childElementCount === 0;
      const summary = element('summary', 'collab-summary', first['institution_'+lang()] || first.institution);
      summary.append(element('span', 'collab-small', cityName(first.city)));
      card.append(summary, ...records.map(renderRecord));
      host.append(card);
    }
  }

  function selectCountry(code) {
    if (view === 'world') focusWorldCountry(code);
    if (code === country) return;
    country = code;
    city = '';
    if (view === 'world') worldCountry = code;
    renderMap();
  }

  function selectCity(name) {
    if (name === city) return;
    city = name;
    renderMap();
  }

  function bindSvgButton(node, activate) {
    node.setAttribute('role', 'button');
    node.setAttribute('tabindex', '0');
    node.addEventListener('click', activate);
    node.addEventListener('keydown', event => {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      event.preventDefault();
      if (!event.repeat) activate();
    });
  }

  for (const path of countryPaths) {
    path.classList.add('has-partners');
    bindSvgButton(path, () => selectCountry(path.dataset.code));
  }

  const brazilianCities = new Map();
  for (const record of entries.filter(record => record.country === 'BRA')) {
    if (!brazilianCities.has(record.city)) brazilianCities.set(record.city, []);
    brazilianCities.get(record.city).push(record);
  }
  const markerHost = brazil.querySelector('#brazil-markers');
  const svgNode = tag => document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [name, records] of brazilianCities) {
    const { lat, lon } = records[0];
    const x = (lon + 76) * 11.2 + 32;
    const y = (6 - lat) * 11.2 + 23;
    const marker = svgNode('g');
    marker.setAttribute('class', 'map-marker'+(records.some(r=>r.program==='BRAFITEC')?' brafitec-marker':''));
    marker.dataset.country='BRA';
    marker.dataset.city=name;
    marker.setAttribute('transform', 'translate(' + x.toFixed(1) + ' ' + y.toFixed(1) + ')');
    const circle = svgNode('circle');
    circle.setAttribute('class', 'outer');
    circle.setAttribute('r', '7');
    const label = svgNode('text');
    label.setAttribute('class', 'map-marker-label');
    label.setAttribute('x', '13');
    label.setAttribute('y', '4');
    label.setAttribute('aria-hidden', 'true');
    label.textContent = name;
    const hit=svgNode('circle');hit.setAttribute('r','12');hit.setAttribute('class','marker-hit');
    marker.append(hit,circle,label);
    bindSvgButton(marker, () => selectCity(name));
    markerHost.append(marker);
    markers.set(name, marker);
  }

  function selectTerritory(code){territory=code;city='';renderMap();}
  france.querySelectorAll('.france-territory[data-territory]').forEach(node=>bindSvgButton(node,()=>selectTerritory(node.dataset.territory)));
  const franceCities=new Map();
  entries.filter(record=>record.country==='FRA' && !record.location_pending).forEach(record=>{
    const area=territoryOf(record);if(!area)return;
    const key=JSON.stringify([area,record.city]);
    if(!franceCities.has(key))franceCities.set(key,[]);franceCities.get(key).push(record);
  });
  const franceSvg=france.querySelector('svg');
  for(const [key,records] of franceCities){
    const first=records[0],area=territoryOf(first);
    const projection=JSON.parse(franceSvg.getAttribute(area==='REU'?'data-reunion-projection':'data-main-projection'));
    const x=projection.x+(first.lon-projection.west)*projection.cos*projection.scale;
    const y=projection.y+(projection.north-first.lat)*projection.scale;
    const marker=svgNode('g');marker.setAttribute('class','map-marker france-marker'+(records.some(r=>r.program==='BRAFITEC')?' brafitec-marker':''));
    marker.setAttribute('transform',`translate(${x.toFixed(2)} ${y.toFixed(2)})`);
    marker.dataset.city=first.city;marker.dataset.country='FRA';marker.dataset.territory=area;
    const circle=svgNode('circle');circle.setAttribute('class','outer');circle.setAttribute('r','7');
    const label=svgNode('text');label.setAttribute('class','map-marker-label');label.setAttribute('x','13');label.setAttribute('y','4');label.setAttribute('aria-hidden','true');label.textContent=first.city;
    const hit=svgNode('circle');hit.setAttribute('r','12');hit.setAttribute('class','marker-hit');
    marker.append(hit,circle,label);
    bindSvgButton(marker,()=>{territory=area;city=first.city;renderMap();});
    france.querySelector('#france-markers').append(marker);markers.set('FRA|'+key,marker);
  }

  const views = [...document.querySelectorAll('[data-map]')];
  for (const button of views) {
    button.addEventListener('click', () => {
      if (button.dataset.map === view) return;
      view = button.dataset.map;
      world.hidden = view !== 'world';
      zoomControls.hidden = view !== 'world';
      if(view==='world') requestAnimationFrame(()=>applyWorldZoom(worldZoom));
      brazil.hidden = view !== 'brazil';
      france.hidden = view !== 'france';
      franceNote.hidden = view !== 'france';
      country = view === 'world' ? worldCountry : view==='brazil'?'BRA':'FRA';
      city = '';
      territory = '';
      for (const control of views) {
        const active = control === button;
        control.classList.toggle('active', active);
        control.setAttribute('aria-pressed', String(active));
      }
      renderMap();
    });
  }
  countrySelect.addEventListener('change', () => selectCountry(countrySelect.value));
  citySelect.addEventListener('change', () => selectCity(citySelect.value));
  territorySelect.addEventListener('change',()=>selectTerritory(territorySelect.value));
  document.addEventListener('site:language', () => renderMap(true));
  renderMap();
})();
