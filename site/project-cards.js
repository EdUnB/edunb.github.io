/* Bilingual cards from content/projects.json; no HTML snippets in editorial data. */
(() => {
  'use strict';
  const host = document.getElementById('project-list');
  if (!host) return;
  const projects = (window.SITE_PROJECTS || []).filter(p => p.public === true);
  const lang = () => siteLanguage();
  const text = (value, lng) => typeof value === 'string' ? value : ((value && (value[lng] || value.en)) || '');
  const element = (tag, className, content) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined) node.textContent = content;
    return node;
  };
  const safeHref = raw => {
    if (typeof raw !== 'string') return null;
    if (/^mailto:[A-Za-z0-9_.+%-]+@[A-Za-z0-9.-]+(?:\?.*)?$/.test(raw)) return raw;
    try { const url = new URL(raw); return url.protocol === 'https:' ? url.href : null; }
    catch (_) { return null; }
  };
  function render() {
    const open=new Set([...host.querySelectorAll('details[open]')].map(node=>node.id));
    host.replaceChildren();
    const lng = lang();
    projects.forEach((p, index) => {
      const article = element('article','project-card' + (p.featured ? ' featured' : ''));
      const top = element('div', 'project-top');
      top.append(element('span','project-type'+(p.status==='emerging'?' planned':''),text(p.label,lng)));
      top.append(element('span','',String(index+1).padStart(2,'0')+' / '+String(projects.length).padStart(2,'0')));
      article.append(top);
      article.dataset.project=p.id;
      const symbol = element('div','project-symbol',p.symbol || '◇'); symbol.setAttribute('aria-hidden','true');
      if(p.story){
        article.classList.add('project-story');
        const image=element('img','project-diagram');image.src='assets/project-biomass.svg';image.alt='';image.width=300;image.height=90;image.setAttribute('aria-hidden','true');article.append(image);
      }else article.append(symbol);
      article.append(element('h3','',text(p.title,lng)));
      article.append(element('p','',text(p.description,lng)));
      let linkHost=article;
      if(p.story){
        const tags=element('div','tag-row project-topics');
        for(const topic of p.story.topics)tags.append(element('span','',text(topic,lng)));
        article.append(tags);
        const details=element('details','project-details');details.id='project-details-'+p.id;details.open=open.has(details.id);
        const summary=element('summary','',siteText('projectExploreTheme'));details.append(summary);
        const body=element('div','project-detail-body');
        body.append(element('h4','',siteText('projectQuestion')),element('p','',text(p.story.question,lng)),element('h4','',siteText('projectFocus')),element('p','',text(p.story.focus,lng)));
        details.append(body);article.append(details);linkHost=body;
      }
      const href = safeHref(p.link);
      if (href) {
        const a = element('a','project-anchor',text(p.link_text,lng)+' ↗'); a.href=href;
        if (href.startsWith('https:')) {a.target='_blank';a.rel='noopener noreferrer';}
        linkHost.append(a);
      }
      host.append(article);
    });
  }
  render();
  document.addEventListener('site:language',render);
})();
