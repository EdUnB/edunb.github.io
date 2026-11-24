/* Site behavior (translations live in content/translations.json). */
const translations = window.SITE_TRANSLATIONS;
const menuButton = document.querySelector('.menu-toggle');
const nav = document.querySelector('.nav');
const activities = document.querySelector('.nav-activities');

const siteLocales = {en:'en',pt:'pt-BR',fr:'fr',zh:'zh-Hans'};
function siteLanguage() { return Object.keys(siteLocales).find(key=>siteLocales[key]===document.documentElement.lang)||'en'; }
function siteText(key, values = {}) {
  const lang = siteLanguage();
  return (translations[lang][key] || '').replace(/\{(\w+)\}/g, (_, name) => values[name] ?? '');
}

function setMenu(open) {
  nav.classList.toggle('open', open);
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', siteText(open ? 'ariaMenuClose' : 'ariaMenuOpen'));
  if (!open) activities.open = false;
}

function setLanguage(lang) {
  if (!Object.hasOwn(siteLocales,lang)) lang='en';
  document.documentElement.lang = siteLocales[lang];
  const name = window.SITE_PROFILE.display_name;
  document.querySelectorAll('[data-i18n]').forEach(element => {
    element.textContent = siteText(element.dataset.i18n);
  });
  document.querySelectorAll('[data-i18n-aria-label]').forEach(element => {
    element.setAttribute('aria-label', siteText(element.dataset.i18nAriaLabel, { name }));
  });
  document.querySelectorAll('[data-lang]').forEach(button => {
    const active = button.dataset.lang === lang;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  const cvLink=document.querySelector('[data-short-cv]');
  if(cvLink) cvLink.setAttribute('href','cv/'+lang+'.html');
  document.title = siteText('pageTitle', { name });
  document.querySelector('meta[name="description"]').content =
    siteText('pageDescription', { name: window.SITE_PROFILE.full_name });
  setMenu(nav.classList.contains('open'));
  try { localStorage.setItem('edgar-site-lang', lang); } catch (_) {}
  document.dispatchEvent(new CustomEvent('site:language', { detail: { lang } }));
}

let preferred = 'en';
try { const saved=localStorage.getItem('edgar-site-lang'); if(Object.hasOwn(siteLocales,saved)) preferred=saved; } catch (_) {}
setLanguage(preferred);
document.querySelectorAll('[data-lang]').forEach(button => {
  button.addEventListener('click', () => setLanguage(button.dataset.lang));
});
menuButton.addEventListener('click', () => setMenu(!nav.classList.contains('open')));
nav.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
  setMenu(false);
  const target = document.querySelector(link.getAttribute('href'));
  target.setAttribute('tabindex', '-1');
  target.focus({ preventScroll: true });
}));
document.addEventListener('keydown', event => {
  if (event.key !== 'Escape') return;
  if (activities.open) {
    activities.open = false;
    activities.querySelector('summary').focus();
  } else if (nav.classList.contains('open')) {
    setMenu(false);
    menuButton.focus();
  }
});
document.addEventListener('click', event => {
  if (!activities.contains(event.target)) activities.open = false;
});
nav.addEventListener('focusout', event => {
  if (!activities.contains(event.relatedTarget)) activities.open = false;
});
window.matchMedia('(max-width: 1450px)').addEventListener('change', () => setMenu(false));
document.querySelector('#year').textContent = new Date().getFullYear();
