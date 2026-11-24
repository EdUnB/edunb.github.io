/* Dated, verified Scopus snapshots. No credentials or requests from visitors. */
(() => {
  const data=window.SITE_SCOPUS, host=document.getElementById('scopus-impact');
  if(!data||!host)return;
  const element=(tag,text)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;return node;};
  function chart(rows,key){
    const figure=element('figure'),caption=element('figcaption',siteText(key));
    const id=key+'-title';caption.id=id;figure.append(caption);
    const sorted=[...rows].sort((a,b)=>a.year-b.year);
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('viewBox','0 0 640 240');svg.setAttribute('role','img');svg.setAttribute('aria-labelledby',id);
    const max=Math.max(1,...sorted.map(p=>p.value)),step=560/sorted.length;
    sorted.forEach((p,i)=>{
      const bar=document.createElementNS(svg.namespaceURI,'rect');
      const height=p.value/max*170;
      for(const [k,v] of Object.entries({x:45+i*step,y:190-height,width:Math.max(1,step*.65),height,fill:'#267e71'}))bar.setAttribute(k,v);
      const title=document.createElementNS(svg.namespaceURI,'title');title.textContent=p.year+': '+new Intl.NumberFormat(document.documentElement.lang).format(p.value);bar.append(title);svg.append(bar);
      if(sorted.length<=15||i%Math.ceil(sorted.length/12)===0){
        const label=document.createElementNS(svg.namespaceURI,'text');label.setAttribute('x',45+i*step);label.setAttribute('y','214');label.setAttribute('font-size','11');label.setAttribute('fill','#526b67');label.textContent=p.year;svg.append(label);
      }
    });
    figure.append(svg);
    const details=element('details');details.append(element('summary',siteText('scopusTable')));
    const table=element('table'),head=element('tr');
    head.append(element('th',siteText('scopusYear')),element('th',siteText('scopusValue')));table.append(head);
    sorted.forEach(p=>{const row=element('tr');row.append(element('td',p.year),element('td',new Intl.NumberFormat(document.documentElement.lang).format(p.value)));table.append(row);});
    details.append(table);figure.append(details);return figure;
  }
  function render(){
    const format=new Intl.NumberFormat(document.documentElement.lang);
    const list=host.querySelector('.scopus-indicators');list.replaceChildren();
    for(const [key,label] of [['documents','scopusDocuments'],['citations','scopusCitations'],['h_index','scopusHIndex'],['citing_documents','scopusCitingDocuments']]){
      const group=element('div');group.dataset.metric=key;group.append(element('dt',siteText(label)),element('dd',format.format(data[key])));list.append(group);
    }
    const date=new Date(data.verified_on+'T12:00:00Z');
    host.querySelector('.scopus-checked').textContent=siteText('scopusChecked',{date:new Intl.DateTimeFormat(document.documentElement.lang,{timeZone:'UTC'}).format(date)});
    const charts=host.querySelector('.scopus-charts');charts.replaceChildren();
    if(data.annual_series){
      charts.append(chart(data.annual_series.documents,'scopusAnnualDocuments'),chart(data.annual_series.citations,'scopusAnnualCitations'));
    }
    host.hidden=false;
  }
  render();document.addEventListener('site:language',render);
})();
