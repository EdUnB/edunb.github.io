#!/usr/bin/env python3
"""Build dependency-free static website from reviewed editorial JSON.
Usage: python scripts/build.py ; optionally --check for validation only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import sys
import importlib.util
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT/'content'
SITE = ROOT/'site'
DIST = ROOT/'dist'
_cv_spec = importlib.util.spec_from_file_location('cv_document', ROOT/'scripts'/'cv_document.py')
CV = importlib.util.module_from_spec(_cv_spec)
_cv_spec.loader.exec_module(CV)
ALLOWED_CATEGORIES = {'bioenergy', 'modeling', 'sustainability', 'other'}
ALLOWED_COUNTRIES = {'BRA','FRA','PRT','AUS','USA','CAN','ESP','URY','ARG','CHL','FIN','NOR','SWE','DNK','NZL','DEU','GBR','ITA','BEL','AUT','CHE','NLD','COL','PRY','PER','BOL','TWN','MYS','IDN','JPN','CHN','IND','ZAF','MEX'}

COLLABORATION_STATUSES = {
    'personal': {'active', 'completed'},
    'institutional': {'active', 'completed', 'historical', 'documented'},
    'academic': {'active', 'completed', 'historical', 'documented'},
    'research': {'documented'},
    'negotiation': {'pending'},
}

def fail(msg: str): raise ValueError(msg)
def load(name): return json.loads((CONTENT/name).read_text('utf-8'))

def validate_scopus(data):
    fields={'source','author_id','orcid','profile_url','verified_on','collection_method',
            'documents','citations','citing_documents','h_index','annual_series'}
    if not isinstance(data,dict) or set(data)!=fields: fail('scopus: unsupported fields')
    if data['source']!='Scopus' or data['author_id']!='57195100508' or data['orcid']!='0000-0002-7582-5010':
        fail('scopus: author identity requires review')
    if data['profile_url']!='https://www.scopus.com/authid/detail.uri?authorId='+data['author_id']:
        fail('scopus: invalid profile URL')
    try: date.fromisoformat(data['verified_on'])
    except (ValueError,TypeError): fail('scopus: invalid consultation date')
    if data['collection_method'] not in ('preview_observation','reviewed_export','authorized_api'):
        fail('scopus: unsupported source method')
    for key in ('documents','citations','citing_documents','h_index'):
        if type(data[key]) is not int or data[key]<0: fail('scopus: invalid '+key)
    if data['h_index']>data['documents'] or data['citing_documents']>data['citations']:
        fail('scopus: inconsistent totals')
    series=data['annual_series']
    if series is not None:
        if not isinstance(series,dict) or set(series)!={'documents','citations'}: fail('scopus: invalid annual series')
        for name,rows in series.items():
            if not isinstance(rows,list) or not rows: fail('scopus: annual series must have verified data')
            years=set()
            for row in rows:
                if not isinstance(row,dict) or set(row)!={'year','value'}: fail('scopus: invalid annual point')
                year,value=row['year'],row['value']
                if type(year) is not int or not 1900<=year<=date.fromisoformat(data['verified_on']).year or year in years:
                    fail('scopus: invalid or duplicate year')
                if type(value) is not int or value<0: fail('scopus: invalid annual value')
                years.add(year)
    return data
def require_string(value, context):
    if not isinstance(value, str) or not value.strip(): fail(f'{context}: required nonempty string')
def validate_localized(value, context):
    if not isinstance(value, dict): fail(f'{context}: expected bilingual object')
    for lang in ('en','pt'): require_string(value.get(lang),f'{context}.{lang}')
def validate_url(value, context, mailto=False):
    require_string(value, context)
    if mailto and re.fullmatch(r'mailto:[^\s@]+@[^\s@?]+(?:\?[^\s]*)?',value): return
    parts = urlsplit(value)
    if parts.scheme!='https' or not parts.netloc: fail(f'{context}: HTTPS URL required')

def validate_collaboration(record, index):
    context = f'collaborations[{index}]'
    if not isinstance(record, dict): fail(f'{context}: expected object')
    for key in ('id', 'country', 'institution', 'status', 'scope', 'city', 'relation_en', 'relation_pt'):
        require_string(record.get(key), f'{context}.{key}')
    scope, status = record['scope'], record['status']
    if status not in COLLABORATION_STATUSES.get(scope, ()):
        fail(f'{context}: invalid scope/status combination')
    if type(record.get('public')) is not bool:
        fail(f'{context}.public must be true or false')
    if scope == 'negotiation' and record['public']:
        fail(f'{context}: cannot publish a negotiation')
    if record['country'] not in ALLOWED_COUNTRIES:
        fail(f'{context}: unsupported country {record["country"]}')
    owner = record.get('institutional_owner')
    if (scope == 'institutional' and owner not in ('LEA', 'UnB')) or (scope != 'institutional' and owner is not None):
        fail(f'{context}.institutional_owner: expected LEA or UnB for institutional partnerships only')
    if 'program' in record and (record['program']!='BRAFITEC' or scope!='institutional'):
        fail(f'{context}.program: BRAFITEC requires an institutional record')
    if 'location_pending' in record and type(record['location_pending']) is not bool:
        fail(f'{context}.location_pending must be boolean')
    if record.get('location_pending'):
        if record.get('lat') is not None or record.get('lon') is not None or record['city']!='campus-pending':
            fail(f'{context}: pending location cannot claim coordinates or a city')
    else:
        for key, limit in (('lat', 90), ('lon', 180)):
            value = record.get(key)
            if type(value) not in (int, float) or not -limit <= value <= limit:
                fail(f'{context}.{key} invalid')
    if 'territory' in record:
        if record['country']!='FRA' or record['territory'] not in ('MET','REU'):
            fail(f'{context}.territory: expected MET or REU for France')
    if 'institution_en' in record:
        require_string(record['institution_en'], f'{context}.institution_en')
    if 'website' in record:
        validate_url(record['website'], f'{context}.website')
    if 'topic' in record:
        validate_localized(record['topic'], f'{context}.topic')
    if 'period' in record:
        period = record['period']
        if (not isinstance(period, dict) or not period or set(period) - {'start', 'end'}
                or any(type(year) is not int or not 1900 <= year <= 2100 for year in period.values())
                or period.get('start', 1900) > period.get('end', 2100)):
            fail(f'{context}.period: expected ordered start/end years')
    for key in ('people', 'publications', 'links'):
        items = record.get(key, [] if key != 'people' else None)
        if not isinstance(items, list):
            fail(f'{context}.{key} must be a list')
        for i, item in enumerate(items):
            label = f'{context}.{key}[{i}]'
            if not isinstance(item, dict):
                fail(f'{label}: expected object')
            if key == 'people':
                for field in ('name', 'role_en', 'role_pt'):
                    require_string(item.get(field), f'{label}.{field}')
                if 'url' not in item:
                    continue
            elif key == 'publications':
                require_string(item.get('title'), f'{label}.title')
            else:
                validate_localized(item.get('label'), f'{label}.label')
            validate_url(item.get('url'), f'{label}.url')

def validate_supervisions(catalog, publications, projects):
    if not isinstance(catalog, dict) or set(catalog) != {'areas', 'items'}:
        fail('supervisions: expected areas and items only')
    areas, items = catalog['areas'], catalog['items']
    if not isinstance(areas, dict) or not isinstance(items, list):
        fail('supervisions: expected area labels and a list of items')
    for area, labels in areas.items():
        if not re.fullmatch(r'[a-z0-9-]+', area) or not isinstance(labels, dict) or not {'en','pt'}.issubset(labels) or set(labels)-{'en','pt','fr','zh'}:
            fail('supervisions: invalid area ID or labels')
        validate_localized(labels, f'supervisions.areas.{area}')
    project_ids = {item['id'] for item in projects if item['public']}
    publication_dois = {item['doi'].strip().lower() for item in publications['items'] if item.get('doi')}
    base_fields = {'id', 'approved', 'level', 'status', 'student', 'institution', 'institution_en',
                   'program', 'program_en', 'program_fr', 'program_zh', 'institution_fr', 'institution_zh', 'role', 'year', 'areas', 'publications', 'projects'}
    ids, identities = set(), set()
    for index, item in enumerate(items):
        context = f'supervisions.items[{index}]'
        if not isinstance(item, dict) or item.get('approved') is not True:
            fail(f'{context}: only editorially approved records belong in content/')
        level, status = item.get('level'), item.get('status')
        graduate = level in ('masters', 'phd')
        if not graduate and level not in ('undergraduate-research', 'undergraduate-thesis'):
            fail(f'{context}: unknown level')
        if status not in ('completed', 'ongoing'):
            fail(f'{context}: unknown status')
        fields = {'title', 'repository_url', 'repository_verified'} if status == 'completed' else {'topic'}
        if set(item) - base_fields - fields:
            fail(f'{context}: unrecognized or private field')
        for key in ('id', 'student', 'institution'):
            require_string(item.get(key), f'{context}.{key}')
        if graduate or 'program' in item:
            require_string(item.get('program'), f'{context}.program')
        if not re.fullmatch(r'[a-z0-9-]+', item['id']) or item['id'] in ids:
            fail(f'{context}: invalid or duplicate ID')
        ids.add(item['id'])
        for key in ('institution_en', 'program_en','institution_fr','institution_zh','program_fr','program_zh'):
            if key in item:
                require_string(item[key], f'{context}.{key}')
        if (graduate or 'role' in item) and item.get('role') not in ('supervisor', 'co-supervisor'):
            fail(f'{context}: unknown supervision role')
        if status == 'completed' or 'year' in item:
            year = item.get('year')
            if type(year) is not int or not 1900 <= year <= 2100:
                fail(f'{context}: invalid year')
        if status == 'completed':
            require_string(item.get('title'), f'{context}.title')
        else:
            validate_localized(item.get('topic'), f'{context}.topic')
            if not {'en','pt'}.issubset(item['topic']) or set(item['topic'])-{'en','pt','fr','zh'}:
                fail(f'{context}.topic: only supported-language public summaries are allowed')
        if 'repository_url' in item or 'repository_verified' in item:
            if item.get('repository_verified') is not True:
                fail(f'{context}: repository link must be verified')
            validate_url(item.get('repository_url'), f'{context}.repository_url')
            repository = urlsplit(item['repository_url'])
            if repository.username is not None:
                fail(f'{context}: repository link cannot contain credentials')
            if repository.hostname in ('repositorio.unb.br', 'www.repositorio.unb.br') and (
                    not re.fullmatch(r'/handle/10482/[0-9]+', repository.path)
                    or repository.query or repository.fragment):
                fail(f'{context}: use the permanent UnB record link')
        for field, allowed in (('areas', areas), ('publications', publication_dois), ('projects', project_ids)):
            values = item.get(field, [])
            if (not isinstance(values, list)
                    or any(not isinstance(value, str) or value not in allowed for value in values)
                    or len(values) != len(set(values))):
                fail(f'{context}.{field}: unknown or duplicate reference')
        identity = (level, status, item.get('year'), *(
            ' '.join(item.get(key, '').casefold().split()) for key in ('student', 'institution', 'program')
        ), ' '.join(item.get('title', item.get('topic', {}).get('pt', '')).casefold().split()))
        if identity in identities:
            fail(f'{context}: duplicate supervision')
        identities.add(identity)

def validate_editorial(catalog):
    roles = {
        'appointment': {'review-editor', 'associate-editor', 'board-member', 'guest-editor'},
        'reviewing': {'peer-reviewer'},
        'contribution': {'guest-editor', 'contributor'},
    }
    fields = {'id', 'approved', 'category', 'journal', 'publisher', 'role', 'start', 'end',
              'status', 'url', 'notes', 'logo'}
    if not isinstance(catalog, dict) or set(catalog) != {'items'} or not isinstance(catalog['items'], list):
        fail('editorial: expected an items list')
    ids = set()
    for item in catalog['items']:
        if not isinstance(item, dict) or set(item) - fields or item.get('approved') is not True:
            fail('editorial: only approved public fields are allowed')
        for key in ('id', 'journal'):
            require_string(item.get(key), f'editorial.{key}')
        if item['id'] in ids or not re.fullmatch(r'[a-z0-9-]+', item['id']):
            fail('editorial: invalid or duplicate ID')
        ids.add(item['id'])
        if item.get('role') not in roles.get(item.get('category'), ()):
            fail('editorial: invalid category or role')
        if item.get('status') not in ('documented', 'active', 'completed'):
            fail('editorial: invalid status')
        for key in ('start', 'end'):
            if key in item and (type(item[key]) is not int or not 1900 <= item[key] <= 2100):
                fail('editorial: invalid period')
        if item.get('start', 1900) > item.get('end', 2100):
            fail('editorial: reversed period')
        if 'publisher' in item:
            require_string(item['publisher'], 'editorial.publisher')
        if 'notes' in item:
            validate_localized(item['notes'], 'editorial.notes')
            if not {'en','pt'}.issubset(item['notes']) or set(item['notes'])-{'en','pt','fr','zh'}:
                fail('editorial: only bilingual public notes are allowed')
        if 'url' in item:
            validate_url(item['url'], 'editorial.url')
            if urlsplit(item['url']).username is not None:
                fail('editorial: credentials in URL')
        if 'logo' in item:
            require_string(item['logo'], 'editorial.logo')
            if not re.fullmatch(r'assets/[a-zA-Z0-9_-]+\.(?:svg|png|webp)', item['logo']) or not (SITE/item['logo']).is_file():
                fail('editorial: expected a local approved logo')

def validate():
    profile=load('profile.json'); publications=load('publications.json'); collaborations=load('collaborations.json')
    projects=load('projects.json'); translations=load('translations.json')
    for key in ('display_name','full_name','email','site_url','lattes_url','orcid_url','lea_url','pcmec_url'):
        require_string(profile.get(key),f'profile.{key}')
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',profile['email']):fail('profile.email invalid')
    for k in ('site_url','lattes_url','orcid_url','lea_url','pcmec_url'):validate_url(profile[k],f'profile.{k}')
    for lang in ('en','pt','fr','zh'):
        if not isinstance(translations.get(lang),dict): fail(f'translations.{lang}: missing')
    for lang in ('pt','fr','zh'):
        if set(translations['en'])!=set(translations[lang]): fail(f'EN/{lang} translation keys mismatch')
        for key,value in translations['en'].items():
            require_string(translations[lang].get(key),f'translations.{lang}.{key}')
            if set(re.findall(r'{(\w+)}',value))!=set(re.findall(r'{(\w+)}',translations[lang][key])):
                fail(f'translations.{lang}.{key}: placeholder mismatch')
    html = (SITE/'index.html').read_text('utf-8')
    html += (SITE/'assets'/'france-map.svg').read_text('utf-8')
    translated_keys = set(re.findall(r'data-i18n(?:-aria-label)?="([^"]+)"', html))
    for key in translated_keys:
        for lang in ('en', 'pt', 'fr', 'zh'):
            require_string(translations[lang].get(key), f'translations.{lang}.{key}')
    if not isinstance(publications.get('items'),list):fail('publications.items missing')
    seen=set()
    for i,p in enumerate(publications['items']):
        for k in ('title','journal'): require_string(p.get(k),f'publications[{i}].{k}')
        if not isinstance(p.get('year'),int) or not 1900<=p['year']<=2100:fail(f'publications[{i}].year invalid')
        doi=p.get('doi','').strip().lower()
        if doi and not re.fullmatch(r'10\.\d{4,9}/\S+',doi,re.I):fail(f'publications[{i}].doi invalid')
        key=('doi',doi) if doi else ('title', re.sub(r'\W','',p['title'].casefold()))
        if key in seen:fail(f'duplicate publication {key}')
        seen.add(key)
        cats=p.get('categories',[])
        if not isinstance(cats,list) or not cats or not set(cats).issubset(ALLOWED_CATEGORIES):fail(f'publications[{i}].categories invalid')
    if not isinstance(collaborations,list):fail('collaborations expected list')
    ids=set()
    map_codes = set(re.findall(r'data-code="([A-Z]{3})"', html))
    for i,c in enumerate(collaborations):
        validate_collaboration(c, i)
        if c['id'] in ids:fail('duplicate collaborator id')
        ids.add(c['id'])
        if c['public'] and c['country'] not in map_codes:
            fail(f'collaboration {c["id"]}: country missing from world map')
    if not isinstance(projects,list):fail('projects expected list')
    ids=set()
    for i,p in enumerate(projects):
        require_string(p.get('id'),f'projects[{i}].id')
        if p['id'] in ids:fail('duplicate project id')
        ids.add(p['id'])
        if not isinstance(p.get('public'),bool):fail('project.public must be bool')
        for k in ('label','title','description','link_text'):validate_localized(p.get(k),f'projects[{i}].{k}')
        validate_url(p.get('link'),f'projects[{i}].link',mailto=True)
        if 'story' in p:
            story=p['story']
            if not isinstance(story,dict) or set(story)!={'diagram','question','focus','topics'}:
                fail(f'projects[{i}].story: unsupported fields')
            if story['diagram']!='biomass-conversion':fail(f'projects[{i}].story: unsupported diagram')
            for key in ('question','focus'):validate_localized(story[key],f'projects[{i}].story.{key}')
            if not isinstance(story['topics'],list) or not 1<=len(story['topics'])<=5:
                fail(f'projects[{i}].story: expected one to five topics')
            for topic in story['topics']:validate_localized(topic,f'projects[{i}].story.topic')
    supervisions = load('supervisions.json')
    validate_supervisions(supervisions, publications, projects)
    editorial = load('editorial.json')
    validate_editorial(editorial)
    CV.prepare(load('cv.json'), profile, publications, supervisions, editorial, translations)
    validate_scopus(load('scopus.json'))
    return profile,publications,collaborations,projects,translations,supervisions,editorial

def bundle(name,data):
    return f'/* GENERATED — edit content/*.json instead. */\nwindow.{name} = '+json.dumps(data,ensure_ascii=False,indent=2)+';\n'

def build():
    profile,publications,collaborations,projects,translations,supervisions,editorial=validate()
    cv_snapshot=CV.prepare(load('cv.json'), profile, publications, supervisions, editorial, translations)
    if DIST.exists():shutil.rmtree(DIST)
    shutil.copytree(SITE,DIST)
    (DIST/'data').mkdir()
    (DIST/'data'/'profile.js').write_text(bundle('SITE_PROFILE',profile),'utf-8')
    (DIST/'data'/'publications.js').write_text(bundle('SITE_PUBLICATIONS',publications),'utf-8')
    (DIST/'data'/'collaborations.js').write_text(bundle('SITE_COLLABORATIONS',[c for c in collaborations if c['public']]),'utf-8')
    (DIST/'data'/'projects.js').write_text(bundle('SITE_PROJECTS',[p for p in projects if p['public']]),'utf-8')
    (DIST/'data'/'translations.js').write_text(bundle('SITE_TRANSLATIONS',translations),'utf-8')
    (DIST/'data'/'supervisions.js').write_text(bundle('SITE_SUPERVISIONS',supervisions),'utf-8')
    (DIST/'data'/'editorial.js').write_text(bundle('SITE_EDITORIAL',editorial),'utf-8')
    (DIST/'data'/'scopus.js').write_text(bundle('SITE_SCOPUS',validate_scopus(load('scopus.json'))),'utf-8')
    html_file=DIST/'index.html'; html=html_file.read_text('utf-8')
    html=html.replace('{{FRANCE_MAP}}',(SITE/'assets'/'france-map.svg').read_text('utf-8'))
    cv_link=''
    if cv_snapshot['status']=='approved':
        CV.write_documents(cv_snapshot,DIST/'cv')
        cv_link='<a href="cv/en.html" target="_blank" rel="noopener noreferrer" data-short-cv data-i18n="cvLink">Short CV (print / PDF) ↗</a>'
    html=html.replace('<!-- SHORT_CV_LINK -->',cv_link)
    placeholders={
        '{{EMAIL}}': profile['email'], '{{DISPLAY_NAME}}':profile['display_name'], '{{FULL_NAME}}':profile['full_name'], '{{LATTES_URL}}':profile['lattes_url'],
        '{{ORCID_URL}}':profile['orcid_url'], '{{LEA_URL}}':profile['lea_url'],
        '{{PCMEC_URL}}':profile['pcmec_url'], '{{SITE_URL}}':profile['site_url'].rstrip('/')+'/',
        '{{LEA_PROFILE_URL}}': 'https://lea.unb.br/arquivos/pessoa/edgar-amaral-silveira',
        '{{PCMEC_PROFILE_URL}}':'https://pcmec.unb.br/edgar-amaral-silveira/'
    }
    for k,v in placeholders.items(): html=html.replace(k,v.replace('&','&amp;').replace('"','&quot;'))
    if re.search(r'\{\{[A-Z_]+\}\}',html): fail('unresolved HTML placeholders')
    css_version = hashlib.sha256((DIST/'styles.css').read_bytes()).hexdigest()[:12]
    html = html.replace('href="styles.css"', f'href="styles.css?v={css_version}"')
    # Version both application code and generated data: an old cached renderer
    # must not be paired with a newer language selector or translation catalog.
    def version_script(match):
        path = match.group(1)
        version = hashlib.sha256((DIST/path).read_bytes()).hexdigest()[:12]
        return f'src="{path}?v={version}"'
    html = re.sub(r'src="([a-zA-Z0-9_./-]+\.js)"', version_script, html)
    html_file.write_text(html,'utf-8')
    (DIST/'.nojekyll').write_text('','utf-8')
    (DIST/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+profile['site_url'].rstrip('/')+'/sitemap.xml\n','utf-8')
    url=profile['site_url'].rstrip('/')+'/'
    (DIST/'sitemap.xml').write_text('<?xml version="1.0" encoding="utf-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+xml_escape(url)+'</loc></url></urlset>\n','utf-8')
    print(f'BUILD OK: {len(publications["items"])} publications, {len([c for c in collaborations if c["public"]])} public collaborations, {len([p for p in projects if p["public"]])} projects. Output: dist/')

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--check',action='store_true',help='validate content without writing')
    args=parser.parse_args()
    try:
        if args.check:
            validate();print('VALIDATION OK')
        else:build()
    except (ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print('ERROR:',exc,file=sys.stderr);return 1
    return 0
if __name__=='__main__':sys.exit(main())
