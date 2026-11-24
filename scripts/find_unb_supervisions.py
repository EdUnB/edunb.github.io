"""Review completed graduate work against public UnB repository metadata."""
import argparse
from collections import defaultdict
from difflib import SequenceMatcher
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
import unicodedata
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from xml.etree import ElementTree

from import_lattes import check_xml, extract
from import_supervisions import extract_records

BASE = 'https://repositorio.unb.br'
ROOT = Path(__file__).resolve().parents[1]
ADVISOR = 'Silveira, Edgar Amaral'
HANDLE = re.compile(r'10482/[0-9]+')
TTL = 7 * 86400
LIMIT = 2_000_000


def words(value):
    plain = unicodedata.normalize('NFKD', value.casefold())
    return re.findall(r'[^\W_]+', ''.join(c for c in plain if not unicodedata.combining(c)))


def name_key(value):
    return sorted(word for word in words(value) if word not in {'da', 'das', 'de', 'do', 'dos', 'e'})


class MetadataTable(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = defaultdict(list)
        self.cells = []
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.cells = []
        if tag == 'td':
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == 'td' and self.cell is not None:
            self.cells.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        if tag == 'tr' and len(self.cells) >= 2 and self.cells[0].startswith('dc.'):
            self.rows[self.cells[0]].append(self.cells[1])


def dim_fields(payload):
    check_xml(payload)
    root = ElementTree.fromstring(payload)
    rows = defaultdict(list)
    for field in root.iter('{http://www.dspace.org/xmlns/dspace/dim}field'):
        key = '.'.join(field.get(part) for part in ('mdschema', 'element', 'qualifier') if field.get(part))
        if field.text:
            rows[key].append(field.text.strip())
    return rows


def repository_item(handle, fields):
    citation = ' '.join(fields.get('dc.identifier.citation', []))
    levels = {'dissertacao': 'masters', 'mestrado': 'masters', 'masterthesis': 'masters',
              'tese': 'phd', 'doutorado': 'phd', 'doctoralthesis': 'phd'}
    typed = {levels[word] for word in words(' '.join(fields.get('dc.type', []))) if word in levels}
    cited = {levels[kind] for kind in re.findall(r'\b(dissertacao|tese)\s*\(\s*(?:mestrado|doutorado)',
                                                unicodedata.normalize('NFKD', citation.casefold())
                                                .encode('ascii', 'ignore').decode())}
    candidates = typed or cited
    years = {int(value[:4]) for value in fields.get('dc.date.submitted', [])
             if re.match(r'^[0-9]{4}(?:-|$)', value)}
    return {
        'url': BASE + '/handle/' + handle,
        'titles': fields.get('dc.title', []) + fields.get('dc.title.alternative', []),
        'authors': fields.get('dc.contributor.author', []),
        'year': next(iter(years)) if len(years) == 1 else None,
        'level': next(iter(candidates)) if len(candidates) == 1 else None,
        'level_conflict': len(typed | cited) > 1,
        'institution': 'Universidade de Brasília' if 'universidade de brasilia' in ' '.join(words(citation))
                       else '',
        'advisors': fields.get('dc.contributor.advisor', []),
        'coadvisors': [value for key, values in fields.items()
                       if key.casefold() in ('dc.contributor.advisorco', 'dc.contributor.coadvisor', 'dc.contributor.co-advisor')
                       for value in values],
    }


def classify(record, candidates):
    if words(record['institution']) != words('Universidade de Brasília'):
        return {'status': 'not-found', 'reason': 'outside-unb', 'candidates': []}
    confirmed, possible, conflicts = [], [], []
    title = words(record['title'])
    student = name_key(record['student'])
    for item in candidates:
        authors = [name_key(name) for name in item['authors']]
        author = bool(student) and student in authors
        similar_author = any(min(len(student), len(name)) >= 2 and
                             (set(student) < set(name) or set(name) < set(student)) for name in authors)
        titles = [words(value) for value in item['titles']]
        exact_title = bool(title) and title in titles
        role = 'advisors' if record['role'] == 'supervisor' else 'coadvisors'
        advisor = any(name_key(name) == name_key(ADVISOR) for name in item[role])
        if not (author or exact_title or (similar_author and advisor and item['year'] == record['year'])):
            continue
        checks = {'student': author, 'title': exact_title, 'year': item['year'] == record['year'],
                  'level': not item.get('level_conflict') and item['level'] == record['level'], 'role': advisor,
                  'institution': words(item['institution']) == words(record['institution'])}
        evidence = {'url': item['url'], 'checks': checks}
        if all(checks.values()):
            confirmed.append(evidence)
        elif (item.get('level_conflict')
              or (item['year'] is not None and not checks['year'])
              or (item['level'] is not None and not checks['level'])
              or (item[role] and not advisor)
              or (titles and not exact_title and max(SequenceMatcher(None, title, value).ratio()
                                                        for value in titles) < .65)
              or (item['authors'] and not author and not similar_author)):
            conflicts.append(evidence)
        else:
            possible.append(evidence)
    if len(confirmed) == 1 and not possible:
        return {'status': 'confirmed', 'candidates': confirmed}
    if len(confirmed) > 1 or (confirmed and possible) or len(possible) > 1:
        return {'status': 'conflicting', 'candidates': confirmed + possible + conflicts}
    if possible:
        return {'status': 'probable', 'candidates': possible + conflicts}
    if conflicts:
        return {'status': 'conflicting', 'candidates': conflicts}
    return {'status': 'not-found', 'candidates': []}


class Repository:
    def __init__(self, cache, refresh=False, offline=False):
        self.cache = cache
        self.refresh = refresh
        self.offline = offline
        self.last_request = None

    def fetch(self, path, params):
        url = BASE + path + '?' + urlencode(params)
        file = self.cache / (hashlib.sha256(url.encode()).hexdigest() + '.cache')
        if not self.refresh and file.exists() and (self.offline or time.time() - file.stat().st_mtime < TTL):
            return file.read_bytes()
        if self.offline:
            raise ValueError('Required repository response is missing from the offline cache')
        if self.last_request is not None:
            time.sleep(max(0, 1 - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()
        with urlopen(Request(url, headers={'User-Agent': 'Academic site maintenance / bibliographic verification'}),
                     timeout=12) as response:
            if urlsplit(response.url).hostname not in ('repositorio.unb.br', 'www.repositorio.unb.br'):
                raise ValueError('Unexpected repository redirect')
            data = response.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise ValueError('Repository response too large')
        file.write_bytes(data)
        return data

    def discover(self):
        data = self.fetch('/browse', {'type': 'advisor', 'value': ADVISOR, 'rpp': 100})
        handles = sorted(set(re.findall(rb'/handle/(10482/[0-9]+)(?=["\x27?])', data)))
        if not handles:
            raise ValueError('Advisor browse returned no identifiable records')
        return [value.decode('ascii') for value in handles]

    def formats(self):
        try:
            data = self.fetch('/oai/request', {'verb': 'ListMetadataFormats'})
        except HTTPError as error:
            if error.code not in (404, 405):
                raise
            return []
        check_xml(data)
        root = ElementTree.fromstring(data)
        return [x.text for x in root.iter('{http://www.openarchives.org/OAI/2.0/}metadataPrefix')]

    def lookup(self, handle, formats):
        if 'dim' in formats:
            data = self.fetch('/oai/request', {'verb': 'GetRecord', 'metadataPrefix': 'dim',
                                               'identifier': 'oai:repositorio.unb.br:' + handle})
            fields = dim_fields(data)
            item = repository_item(handle, fields)
            if all(item[key] for key in ('titles', 'authors', 'year', 'level', 'institution')) and (
                    item['advisors'] or item['coadvisors']):
                return item
        page = self.fetch('/handle/' + handle, {'mode': 'full'})
        parser = MetadataTable()
        parser.feed(page.decode('utf-8'))
        if not parser.rows.get('dc.title'):
            raise ValueError('Full metadata page returned no title')
        return repository_item(handle, parser.rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export', type=Path)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--handle', action='append', default=[], help='Additional official candidate, for example a co-advised work')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--refresh', action='store_true')
    mode.add_argument('--offline', action='store_true', help='Require cached responses and disable network access')
    parser.add_argument('--review-output', type=Path)
    args = parser.parse_args()
    try:
        if args.cache.resolve().is_relative_to(ROOT) or (
                args.review_output and (args.review_output.resolve().is_relative_to(ROOT)
                                        or args.review_output.suffix.lower() != '.json')):
            raise ValueError('Use cache and review paths outside the repository')
        if any(not HANDLE.fullmatch(handle) for handle in args.handle):
            raise ValueError('Expected a UnB handle')
        records, _ = extract_records(extract(args.export))
        records = [r for r in records if r['status'] == 'completed' and r['level'] in ('masters', 'phd')]
        args.cache.mkdir(exist_ok=True)
        repository = Repository(args.cache, args.refresh, args.offline)
        formats = repository.formats()
        handles = sorted(set(repository.discover() + args.handle))
        candidates = [repository.lookup(handle, formats) for handle in handles]
        results = [classify(record, candidates) for record in records]
        print(json.dumps({'formats': formats, 'handles': len(handles),
                          'results': [{'number': n, **result} for n, result in enumerate(results, 1)]}, indent=2))
        if args.review_output:
            with args.review_output.open('x', encoding='utf-8') as stream:
                json.dump([{'source': record, **result} for record, result in zip(records, results)],
                          stream, ensure_ascii=False, indent=2)
                stream.write('\n')
        return 0
    except (OSError, ValueError, URLError, HTTPError, ElementTree.ParseError) as error:
        print('Repository review failed:', type(error).__name__, getattr(error, 'code', ''), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
