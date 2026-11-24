(() => {
  'use strict';
  const roles = {
    'review-editor': 'edReviewEditor', 'associate-editor': 'edAssociateEditor',
    'board-member': 'edBoardMember', 'guest-editor': 'edGuestEditor',
    'peer-reviewer': 'edPeerReviewer', contributor: 'edContributor',
  };
  const statuses = { active: 'edActive', completed: 'edCompleted' };
  function node(tag, text, className) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (className) element.className = className;
    return element;
  }
  function render() {
    const language = siteLanguage();
    for (const category of ['appointment', 'reviewing', 'contribution']) {
      const list = document.getElementById('editorial-' + category);
      list.replaceChildren();
      for (const item of window.SITE_EDITORIAL.items.filter(item => item.category === category)) {
        const card = node('li', undefined, 'supervision-card');
        if (item.logo) {
          const logo = node('img', undefined, 'editorial-logo');
          logo.src = item.logo;
          logo.alt = '';
          logo.loading = 'lazy';
          card.append(logo);
        }
        card.append(node('p', siteText(roles[item.role]), 'supervision-badge'), node('h4', item.journal));
        if (item.publisher) card.append(node('p', item.publisher));
        const period = item.start && item.end ? (item.start === item.end ? String(item.start) : item.start + '–' + item.end)
          : item.start ? siteText('edStart', { year: item.start })
          : item.end ? siteText('edEnd', { year: item.end }) : '';
        const details = [period, statuses[item.status] && siteText(statuses[item.status])].filter(Boolean);
        if (details.length) card.append(node('p', details.join(' · ')));
        if (item.notes) card.append(node('p', item.notes[language]));
        if (item.url) {
          const link = node('a', siteText('edJournalLink'), 'editorial-link');
          link.href = item.url;
          card.append(link);
        }
        list.append(card);
      }
      if (!list.childElementCount) list.append(node('li', siteText('edEmpty')));
    }
  }
  document.addEventListener('site:language', render);
  render();
})();
