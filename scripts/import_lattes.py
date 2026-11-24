#!/usr/bin/env python3
"""Privacy-first Lattes XML/ZIP to public publications.json, with dry run and metadata preservation.
Usage: python scripts/import_lattes.py /private/cv.zip --dry-run
       python scripts/import_lattes.py /private/cv.zip
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
import re
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path
from xml.parsers import expat
from xml.etree import ElementTree as ET
from zlib import error as ZlibError

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'content'/'publications.json'
MAX_XML=15_000_000
MAX_ZIP=16_000_000
MAX_ZIP_ENTRIES=100
MAX_XML_ELEMENTS=250_000
MAX_XML_DEPTH=128

def read_xml(stream):
    data = stream.read(MAX_XML + 1)
    if len(data) > MAX_XML:
        raise ValueError('XML exceeds size limit')
    return data

def read_zip(stream):
    stream.seek(0, 2)
    if stream.tell() > MAX_ZIP:
        raise ValueError('ZIP exceeds size limit')
    stream.seek(0)
    with zipfile.ZipFile(stream) as bundle:
        entries = bundle.infolist()
        if len(entries) > MAX_ZIP_ENTRIES:
            raise ValueError('ZIP contains too many entries')
        items = [entry for entry in entries if not entry.is_dir() and entry.filename.lower().endswith('.xml')]
        if len(items) != 1:
            raise ValueError('ZIP must contain one XML file')
        item = items[0]
        if item.file_size > MAX_XML:
            raise ValueError('XML exceeds size limit')
        if item.flag_bits & 1 or item.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise ValueError('ZIP XML must be unencrypted and stored or deflated')
        # Read only the selected member. Never extract paths from the archive.
        with bundle.open(item) as member:
            return read_xml(member)

def check_xml(data):
    def reject_declaration(*args):
        raise ValueError('DTD/entity declarations are not accepted')

    depth = elements = 0

    def start_element(name, attrs):
        nonlocal depth, elements
        depth += 1
        elements += 1
        if depth > MAX_XML_DEPTH or elements > MAX_XML_ELEMENTS:
            raise ValueError('XML exceeds structural limits')

    def end_element(name):
        nonlocal depth
        depth -= 1

    # Expat recognizes declarations after decoding, before processing any DTD.
    parser = expat.ParserCreate()
    parser.StartDoctypeDeclHandler = reject_declaration
    parser.EntityDeclHandler = reject_declaration
    parser.ExternalEntityRefHandler = reject_declaration
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    parser.StartElementHandler = start_element
    parser.EndElementHandler = end_element
    parser.Parse(data, True)

def extract(path):
    suffix = path.suffix.lower()
    if suffix not in ('.xml', '.zip'):
        raise ValueError('Supply XML or ZIP only')
    with path.open('rb') as stream:
        data = read_zip(stream) if suffix == '.zip' else read_xml(stream)
    check_xml(data)
    return ET.fromstring(data)

def categories(title):
    t=title.casefold(); out=[]
    if any(k in t for k in ('bioenergy','bioenergia','biomass','biomassa','biofuel','torref','pyrolys','pirólis','gasific','gaseifica','hydrogen','hidrog','biochar','pellet','combustion','waste','resíduo')):out.append('bioenergy')
    if any(k in t for k in ('kinetic','model','simul','optimization','optimisation','cinética','modelagem','numéric')):out.append('modeling')
    if any(k in t for k in ('life cycle','environmental','sustainab','emission','impact','exerg','ciclo de vida','ambiental','carbon')):out.append('sustainability')
    return out or ['other']

def doi_normalize(value):
    return re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:)','',value.strip(),flags=re.I).strip().lower()

def article_doi(article):
    return doi_normalize(article.get('doi') or '')

def normalize_text(value):
    # Preserve accents, word boundaries and punctuation. Ignore case and whitespace.
    return ' '.join(unicodedata.normalize('NFC', value).casefold().split())

def signature(article):
    title = normalize_text(article.get('title') or '')
    authors = tuple(normalize_text(name) for name in (article.get('authors') or '').split(';'))
    year = article.get('year')
    complete_authors = all(name and not re.search(r'\bet al\.?$', name) for name in authors)
    if title and isinstance(year, int) and complete_authors:
        return title, year, authors
    return None

def parse(root):
    result=[]; seen=set()
    for art in root.iter('ARTIGO-PUBLICADO'):
        base=art.find('DADOS-BASICOS-DO-ARTIGO');detail=art.find('DETALHAMENTO-DO-ARTIGO')
        if base is None:continue
        title=(base.get('TITULO-DO-ARTIGO') or '').strip()
        year=(base.get('ANO-DO-ARTIGO') or '').strip()
        journal=(detail.get('TITULO-DO-PERIODICO-OU-REVISTA') or '').strip() if detail is not None else ''
        doi=doi_normalize(base.get('DOI') or (detail.get('DOI') if detail is not None else '') or '')
        if not title or not re.fullmatch(r'[0-9]{4}', year) or not journal:continue
        if not 1900 <= int(year) <= 2100:
            raise ValueError(f'Invalid publication year for article: {title}')
        if doi and not re.fullmatch(r'10\.\d{4,9}/\S+', doi):
            raise ValueError(f'Invalid DOI for article: {title}')
        authors=[(a.get('NOME-PARA-CITACAO') or a.get('NOME-COMPLETO-DO-AUTOR') or '').strip() for a in art.findall('AUTORES')]
        rec={'title':title,'year':int(year),'journal':journal,'authors':'; '.join(filter(None,authors)), 'doi':doi,'categories':categories(title),'source':'lattes'}
        k=('doi',doi) if doi else ('metadata',title,year,journal,rec['authors'])
        if k in seen:continue
        seen.add(k);result.append(rec)
    return result

def index_articles(articles, identify):
    index = defaultdict(list)
    for position, article in enumerate(articles):
        identity = identify(article)
        if identity:
            index[identity].append(position)
    return index

def merge_publications(prior, incoming):
    prior_dois = index_articles(prior, article_doi)
    prior_signatures = index_articles(prior, signature)
    incoming_signatures = index_articles(incoming, signature)
    matches = {}

    for position, article in enumerate(incoming):
        doi = article_doi(article)
        candidates = prior_dois.get(doi, [])
        if len(candidates) > 1:
            raise ValueError(f'Multiple catalog records already have DOI {doi}; review them before importing')
        if candidates:
            matches[position] = candidates[0]

    records = list(prior)
    new = []
    review = []
    matched_prior = set(matches.values())
    for position, article in enumerate(incoming):
        doi = article_doi(article)
        prior_position = matches.get(position)
        identity = signature(article)
        if prior_position is None and identity:
            candidates = prior_signatures.get(identity, [])
            if len(candidates) == 1 and len(incoming_signatures[identity]) == 1:
                candidate = candidates[0]
                if candidate not in matched_prior and (not doi or not article_doi(prior[candidate])):
                    prior_position = candidate
            if candidates and prior_position is None:
                review.append(article)

        if prior_position is None:
            new.append(article)
            records.append(article)
            continue

        previous = prior[prior_position]
        # Keep all prior editorial fields and fill missing bibliographic values only.
        merged = {**article, **previous}
        for field in ('title', 'year', 'journal', 'authors'):
            if not previous.get(field):
                merged[field] = article[field]
        merged['doi'] = article_doi(previous) or doi
        records[prior_position] = merged

    return records, new, review

def check_catalog_keys(records):
    # Keep the output compatible with the V2.1 build validator.
    seen = set()
    for article in records:
        doi = article_doi(article)
        identity = ('doi', doi) if doi else ('title', re.sub(r'\W', '', article['title'].casefold()))
        if identity in seen:
            raise ValueError('Conflicting catalog keys; review the matching publications before importing')
        seen.add(identity)

def write_catalog(payload):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=DEST.parent,
                                         suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        temporary.replace(DEST)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('file',type=Path);ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args(argv)
    try:
        root=extract(args.file)
        incoming=parse(root)
        old=json.loads(DEST.read_text('utf-8'))
        prior=old.get('items',[])
        records,new,review=merge_publications(prior,incoming)
        records.sort(key=lambda p:(p['year'],p['title'].casefold()),reverse=True)
        payload={**old,'source':'lattes','updated_at':root.attrib.get('DATA-ATUALIZACAO') or None,'items':records}
        print(f'Lattes publications: {len(incoming)} | New: {len(new)} | Previous catalog: {len(prior)} | Final: {len(records)}')
        for rec in new[:20]:print(f' + {rec["year"]} {rec["title"]}')
        for rec in review:
            print(f' REVIEW possible match kept separate: {rec["year"]} {rec["title"]}')
        check_catalog_keys(records)
        if args.dry_run:
            print('DRY RUN: no files changed. Review before import.');return 0
        write_catalog(payload)
        print('Updated content/publications.json; raw XML/ZIP not copied. Run python scripts/build.py --check and review git diff.')
        return 0
    except (OSError, ValueError, LookupError, ET.ParseError, expat.ExpatError,
            zipfile.BadZipFile, ZlibError, NotImplementedError) as err:
        print('ERROR:',str(err),file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
