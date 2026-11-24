(() => {
  'use strict';

  const { items, areas } = window.SITE_SUPERVISIONS;
  const graduate = items.filter(item => item.level === 'masters' || item.level === 'phd');
  const complementary = items.filter(item => item.level !== 'masters' && item.level !== 'phd');
  const levels = {
    masters: 'supMasters', phd: 'supPhD',
    'undergraduate-research': 'supUndergradResearch', 'undergraduate-thesis': 'supUndergradThesis',
  };
  const statuses = { completed: 'supDone', ongoing: 'supActive' };
  const roles = { supervisor: 'supSupervisor', 'co-supervisor': 'supCoSupervisor' };
  const byId = suffix => document.getElementById('supervision-' + suffix);
  const filters = ['level', 'status', 'year', 'area'].map(byId);
  const language = () => siteLanguage();
  const expanded = {completed:false,ongoing:false,'undergraduate-research':false,'undergraduate-thesis':false};
  const undergraduateFilters=['type','status','year'].map(key=>byId('undergraduate-'+key));
  const previewLimit = 4;

  function node(tag, text, className) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (className) element.className = className;
    return element;
  }

  function setOptions(select, values) {
    const selected = select.value;
    select.replaceChildren(new Option(siteText('supAll'), ''),
      ...values.map(([value, label]) => new Option(label, value)));
    select.value = selected;
  }

  function renderCard(item) {
    const card = node('li', undefined, 'supervision-card');
    card.dataset.level=item.level;
    card.dataset.status=item.status;
    const current = language();
    const badges = siteText(levels[item.level]) + ' · ' + siteText(statuses[item.status]);
    card.append(node('p', badges, 'supervision-badge'));
    card.append(node(graduate.includes(item)?'h4':'h5', item.status === 'completed' ? item.title : item.topic[language()]));
    const detail = node('dl');
    const fields = [
      ['supStudent', item.student],
      ['supInstitution', item['institution_'+current] || item.institution],
      [graduate.includes(item)?'supProgram':'supCourse', item['program_'+current] || item.program || (!graduate.includes(item)&&siteText('supCourseUnspecified'))],
      ['supRole', item.role ? siteText(roles[item.role]) : !graduate.includes(item)&&siteText('supRoleUnspecified')],
      [item.status === 'ongoing' ? 'supYear' : graduate.includes(item) ? 'supDefenseYear' : 'supCompletionYear', item.year],
      ['supArea', (item.areas || []).map(area => areas[area][language()]).join(' · ')],
    ];
    for (const [label, value] of fields) {
      if (value) detail.append(node('dt', siteText(label)), node('dd', value));
    }
    card.append(detail);
    if (item.repository_url) {
      const label = item.level === 'phd' ? 'supViewThesis'
        : item.level === 'masters' ? 'supViewDissertation' : 'supRepository';
      const link = node('a', siteText(label), 'supervision-repository');
      link.href = item.repository_url;
      card.append(link);
    }
    return card;
  }

  function renderList(group, records, hasApproved) {
    const sorted = [...records].sort((a, b) => (b.year || 0) - (a.year || 0) ||
      a.student.localeCompare(b.student, language()));
    const compact = Object.hasOwn(expanded, group);
    byId(group + '-list').replaceChildren(...sorted.map((item,index)=>{
      const card=renderCard(item);
      card.hidden=compact && !expanded[group] && index>=previewLimit;
      return card;
    }));
    if(compact){
      const button=byId(group+'-toggle');
      button.hidden=sorted.length<=previewLimit;
      button.setAttribute('aria-expanded',String(expanded[group]));
      button.textContent=siteText(expanded[group]?'supShowLess':({completed:'supShowAllCompleted',ongoing:'supShowAllOngoing','undergraduate-research':'supShowAllResearch','undergraduate-thesis':'supShowAllTheses'})[group],{
        count:new Intl.NumberFormat(language()).format(sorted.length),
      });
    }
    const empty = byId(group + '-empty');
    empty.hidden = records.length > 0;
    empty.textContent = siteText(hasApproved ? 'supNoMatch' : 'supNoApproved');
  }

  function renderFiltered() {
    const [level, status, year, area] = filters.map(select => select.value);
    const matches = graduate.filter(item =>
      (!level || item.level === level) && (!status || item.status === status) &&
      (!year || String(item.year) === year) && (!area || item.areas?.includes(area)));
    for (const state of Object.keys(statuses)) {
      byId(state).hidden = Boolean(status && state !== status);
      renderList(state, matches.filter(item => item.status === state), graduate.some(item => item.status === state));
    }
    byId('results').textContent = siteText(matches.length === 1 ? 'supResultOne' : 'supResultMany', {
      count: new Intl.NumberFormat(language()).format(matches.length),
    });
  }

  function renderUndergraduate(){
    const [type,status,year]=undergraduateFilters.map(select=>select.value);
    const matches=complementary.filter(item=>(!type||item.level===type)&&(!status||item.status===status)&&(!year||String(item.year)===year));
    for(const level of ['undergraduate-research','undergraduate-thesis']){
      byId(level).hidden=Boolean(type&&type!==level);
      renderList(level,matches.filter(item=>item.level===level),complementary.some(item=>item.level===level));
      byId(level+'-count').textContent=new Intl.NumberFormat(language()).format(complementary.filter(item=>item.level===level&&item.status==='completed').length);
    }
    byId('undergraduate-results').textContent=siteText('supUndergradResults',{count:new Intl.NumberFormat(language()).format(matches.length)});
  }

  function renderLanguage() {
    const format = new Intl.NumberFormat(language());
    for (const state of Object.keys(statuses)) {
      byId(state + '-count').textContent = format.format(graduate.filter(item => item.status === state).length);
    }
    const years = [...new Set(graduate.flatMap(item => item.year ? [item.year] : []))].sort((a, b) => b - a);
    const areaOptions = Object.entries(areas).map(([key, labels]) => [key, labels[language()]]);
    const assignedAreas = new Set(graduate.flatMap(item => item.areas || []));
    setOptions(filters[0], ['masters', 'phd'].map(level => [level, siteText(levels[level])]));
    setOptions(filters[1], Object.entries(statuses).map(([key, label]) => [key, siteText(label)]));
    setOptions(filters[2], years.map(year => [String(year), String(year)]));
    setOptions(filters[3], areaOptions.filter(([key]) => assignedAreas.has(key)));
    filters[3].disabled = assignedAreas.size === 0;
    byId('opportunities').replaceChildren(...areaOptions.map(([, label]) => node('li', label)));
    setOptions(undergraduateFilters[0],['undergraduate-research','undergraduate-thesis'].map(key=>[key,siteText(levels[key])]));
    setOptions(undergraduateFilters[1],Object.entries(statuses).filter(([key])=>complementary.some(item=>item.status===key)).map(([key,label])=>[key,siteText(label)]));
    setOptions(undergraduateFilters[2],[...new Set(complementary.map(item=>item.year).filter(Boolean))].sort((a,b)=>b-a).map(year=>[String(year),String(year)]));
    renderUndergraduate();
    renderFiltered();
  }

  for(const state of Object.keys(expanded)) byId(state+'-toggle').addEventListener('click',()=>{
    expanded[state]=!expanded[state];
    if(state.startsWith('undergraduate'))renderUndergraduate();else renderFiltered();
    if(!expanded[state]) byId(state+'-toggle').scrollIntoView({block:'nearest',behavior:'instant'});
  });
  for (const select of filters) select.addEventListener('change', ()=>{
    expanded.completed=false;expanded.ongoing=false;
    renderFiltered();
  });
  for(const select of undergraduateFilters) select.addEventListener('change',()=>{
    expanded['undergraduate-research']=false;expanded['undergraduate-thesis']=false;renderUndergraduate();
  });
  document.addEventListener('site:language', renderLanguage);
  renderLanguage();
})();
