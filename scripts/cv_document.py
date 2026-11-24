"""Short CV derived exclusively from reviewed public site catalogs; no XML access.

The printable HTML is the document source. Browser Print/Save as PDF creates
a PDF in the visitor's locale without adding a server or a build dependency.
"""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re

LANGUAGES = {'en': 'en', 'pt': 'pt-BR', 'fr': 'fr', 'zh': 'zh-Hans'}
SECTIONS = ['profile', 'education', 'research', 'publications', 'supervision', 'editorial', 'contact']


def normalized_doi(value):
    return re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)', '', value.strip(), flags=re.I).lower()


def prepare(config, profile, publications, supervisions, editorial, translations):
    """Materialize an allowlisted snapshot; unresolved selections fail closed."""
    expected = {'schema_version', 'status', 'sections', 'max_publications', 'selected_publications'}
    if not isinstance(config, dict) or set(config) != expected:
        raise ValueError('cv: unexpected configuration fields')
    if config['schema_version'] != 1 or config['status'] not in ('draft', 'approved'):
        raise ValueError('cv: invalid schema or editorial status')
    if config['sections'] != SECTIONS:
        raise ValueError('cv: expected the seven reviewed section types')
    if type(config['max_publications']) is not int or not 1 <= config['max_publications'] <= 5:
        raise ValueError('cv: select between one and five publications')
    references = config['selected_publications']
    if not isinstance(references, list) or len(references) > config['max_publications']:
        raise ValueError('cv: invalid publication selection')
    if config['status'] == 'approved' and not references:
        raise ValueError('cv: publication selection must be reviewed before approval')
    selected, identities = [], set()
    for reference in references:
        if not isinstance(reference, dict):
            raise ValueError('cv: expected DOI or exact title/year reference')
        if set(reference) == {'doi'} and isinstance(reference['doi'], str) and reference['doi'].strip():
            doi = normalized_doi(reference['doi'])
            matches = [p for p in publications['items'] if normalized_doi(p.get('doi', '')) == doi]
        elif set(reference) == {'title', 'year'} and isinstance(reference['title'], str) and type(reference['year']) is int:
            matches = [p for p in publications['items'] if p['title'] == reference['title'] and p['year'] == reference['year']]
        else:
            raise ValueError('cv: invalid publication reference')
        if len(matches) != 1:
            raise ValueError('cv: missing or ambiguous publication; review selection')
        publication = matches[0]
        identity = (publication['title'], publication['year'])
        if identity in identities:
            raise ValueError('cv: duplicate publication selection')
        identities.add(identity)
        selected.append({key: publication[key] for key in ('title', 'year', 'journal', 'authors', 'doi') if publication.get(key)})

    # No students, provisional titles, internal IDs, arbitrary profile fields,
    # importer staging data or confidential editorial notes enter this snapshot.
    counts = Counter((item['status'], item['level']) for item in supervisions['items']
                     if item.get('approved') is True and item['level'] in ('masters', 'phd'))
    roles = {'review-editor': 'edReviewEditor', 'associate-editor': 'edAssociateEditor',
             'board-member': 'edBoardMember', 'guest-editor': 'edGuestEditor'}
    appointments = [item for item in editorial['items'] if item.get('approved') is True
                    and item['category'] == 'appointment' and item['role'] in roles]
    shared = {
        'profile': {key: profile[key] for key in ('display_name', 'full_name', 'email', 'lattes_url', 'orcid_url', 'site_url')},
        'publication_count': len(publications['items']),
        'publications': selected,
        'supervisions': {state: {level: counts[state, level] for level in ('masters', 'phd')}
                         for state in ('completed', 'ongoing')},
        'editorial': [{key: item[key] for key in ('journal', 'role', 'status', 'url')} for item in appointments],
    }
    documents = {}
    for lang in LANGUAGES:
        t = translations[lang]
        documents[lang] = {**shared, 'lang': lang, 'status': config['status'],
                          'position': t['metaPosition'], 'affiliations': t['metaLab'], 'fellowship': t['metaCnpq'],
                          'summary': t['aboutLead'], 'education': t['aboutBioB'],
                          'research': [t[f'area{i}Title'] for i in range(1, 5)],
                          'labels': {key: value for key, value in t.items() if key.startswith('cv')},
                          'role_labels': {role: t[key] for role, key in roles.items()},
                          'status_labels': {state: t[key] for state, key in [('active', 'edActive'), ('completed', 'edCompleted')]}}
    fingerprint = sha256(json.dumps(documents, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return {'schema_version': 1, 'status': config['status'], 'source_digest': fingerprint,
            'documents': documents}


def render(document, digest, built_on):
    t = document['labels']
    e = lambda value: escape(str(value), quote=True)
    paragraphs = lambda values: ''.join(f'<p>{e(value)}</p>' for value in values)
    section = lambda title, body, css='': f'<section class="{css}"><h2>{e(title)}</h2>{body}</section>'
    profile = document['profile']
    body = f'<header><p class="eyebrow">{e(t["cvTitle"])}</p><h1>{e(profile["display_name"])}</h1>{paragraphs([document["position"],document["affiliations"],document["fellowship"]])}</header>'
    if document['status'] == 'draft':
        body += f'<aside class="draft">{e(t["cvDraft"])}</aside>'
    body += section(t['cvProfile'], paragraphs([document['summary']]))
    body += section(t['cvEducation'], paragraphs([document['education']]))
    body += section(t['cvResearch'], '<ul>'+''.join(f'<li>{e(topic)}</li>' for topic in document['research'])+'</ul>')
    stats = [t['cvPublicationCount'].replace('{count}', str(document['publication_count']))]
    for state, key in [('completed', 'cvCompleted'), ('ongoing', 'cvOngoing')]:
        counts = document['supervisions'][state]
        stats.append(t[key].replace('{masters}', str(counts['masters'])).replace('{phd}', str(counts['phd'])))
    body += section(t['cvSupervision'], paragraphs(stats))
    body += section(t['cvEditorial'], '<ul>'+''.join(
        f'<li>{e(document["role_labels"][item["role"]])} — {e(item["journal"])}'
        +(f' · {e(document["status_labels"][item["status"]])}' if item['status'] in document['status_labels'] else '')+'</li>'
        for item in document['editorial'])+'</ul>')
    if document['publications']:
        citations = []
        for item in document['publications']:
            doi = normalized_doi(item.get('doi', ''))
            link = f' <a href="https://doi.org/{e(doi)}">DOI: {e(doi)}</a>' if doi else ''
            authors=item.get('authors','')
            if ';' in authors: authors=authors.split(';',1)[0].strip()+' et al.'
            citations.append(f'<li><strong>{e(item["title"])}</strong><p>{e(authors)}</p><p>{e(item["journal"])} · {e(item["year"])}.{link}</p></li>')
        body += section(t['cvPublications'], '<ol>'+''.join(citations)+'</ol>', 'publications')
    elif document['status'] == 'draft':
        body += section(t['cvPublications'], paragraphs([t['cvPendingSelection']]))
    links = [('mailto:'+profile['email'], profile['email']), (profile['orcid_url'], 'ORCID'),
             (profile['lattes_url'], 'Lattes'), (profile['site_url'], t['cvWebsite'])]
    body += section(t['cvContact'], '<p class="contacts">'+' · '.join(f'<a href="{e(url)}">{e(label)}</a>' for url,label in links)+'</p>')
    footer = t['cvBuiltOn'].replace('{date}', built_on)
    body += f'<footer>{e(footer)} · {e(t["cvSnapshot"])} {digest[:12]}</footer>'
    return f'''<!doctype html><html lang="{LANGUAGES[document['lang']]}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><link rel="icon" href="data:,">
<title>{e(profile['display_name'])} — {e(t['cvTitle'])}</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#edf2ef;color:#183540;font:14px/1.5 Arial,"Microsoft YaHei",sans-serif}}
main{{max-width:820px;margin:28px auto;padding:42px;background:white}}h1{{font-size:30px;margin:0 0 12px}}h2{{font-size:15px;color:#176b63;border-bottom:1px solid #d5e2dd;padding-bottom:5px;margin:20px 0 8px}}p{{margin:5px 0}}ul,ol{{padding-left:20px;margin:8px 0}}li{{margin:5px 0}}a{{color:#176b63;overflow-wrap:anywhere}}header p{{font-size:13px}}.eyebrow{{letter-spacing:2px;color:#176b63}}.draft{{padding:10px;background:#f3eee1;margin-top:20px}}footer{{border-top:1px solid #d5e2dd;margin-top:24px;padding-top:10px;font-size:10px;color:#526b67}}.toolbar{{max-width:820px;margin:20px auto;display:flex;align-items:center;gap:12px;padding:0 12px}}button{{padding:10px 15px;min-height:44px;border:1px solid #176b63;background:#176b63;color:white;border-radius:4px;cursor:pointer}}button:focus-visible,a:focus-visible{{outline:3px solid #22998c;outline-offset:3px}}.toolbar p{{font-size:12px}}
@media(max-width:600px){{main{{margin:0;padding:24px}}.toolbar{{flex-wrap:wrap}}}}
@page{{size:A4;margin:16mm}}@media print{{body{{background:white;font-size:10pt}}main{{max-width:none;padding:0;margin:0}}.toolbar{{display:none}}h1{{font-size:23pt}}h2{{break-after:avoid}}li{{break-inside:avoid}}.publications{{break-before:page}}a{{color:inherit;text-decoration:none}}footer{{font-size:8pt}}}}
</style></head><body><div class="toolbar"><button type="button" onclick="window.print()">{e(t['cvPrint'])}</button><p>{e(t['cvPrintHint'])}</p></div><main>{body}</main></body></html>'''


def write_documents(snapshot, output, *, preview=False, built_on=None):
    output = Path(output)
    if snapshot['status'] != 'approved' and not preview:
        return []
    output.mkdir(parents=True, exist_ok=True)
    built_on = built_on or datetime.now(timezone.utc).date().isoformat()
    paths = []
    for lang, document in snapshot['documents'].items():
        path = output/f'{lang}.html'
        path.write_text(render(document, snapshot['source_digest'], built_on), encoding='utf-8')
        paths.append(path)
    return paths
