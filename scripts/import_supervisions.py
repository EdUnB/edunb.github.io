"""Prepare a private supervision review using the existing safe Lattes XML reader."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
from xml.etree import ElementTree
from xml.parsers import expat
import zipfile
from zlib import error as ZlibError

from import_lattes import extract, normalize_text

ROOT = Path(__file__).resolve().parents[1]
LEVELS = {
    'MESTRADO': 'masters',
    'DOUTORADO': 'phd',
    'INICIACAO-CIENTIFICA': 'undergraduate-research',
    'GRADUACAO': 'undergraduate-thesis',
}
COMPLEMENTARY = {
    'INICIACAO_CIENTIFICA': 'undergraduate-research',
    'TRABALHO_DE_CONCLUSAO_DE_CURSO_GRADUACAO': 'undergraduate-thesis',
}
ROLES = {'ORIENTADOR_PRINCIPAL': 'supervisor', 'CO_ORIENTADOR': 'co-supervisor'}
COMPLETED = 'ORIENTACOES-CONCLUIDAS'
ONGOING = 'ORIENTACAO-EM-ANDAMENTO'
OTHER = 'OUTRAS-ORIENTACOES-CONCLUIDAS'


def extract_records(root):
    if root.tag != 'CURRICULO-VITAE':
        raise ValueError('Expected a Lattes CV export')
    records, issues = [], Counter()
    for node in root.iter():
        tag = node.tag
        if tag == OTHER:
            basic = node.find('DADOS-BASICOS-DE-' + tag)
            level = COMPLEMENTARY.get(basic.get('NATUREZA', '')) if basic is not None else None
            if not level:
                issues['unsupported_complementary'] += 1
                continue
            status = 'completed'
        elif tag.startswith(COMPLETED + '-PARA-'):
            level = LEVELS.get(tag.removeprefix(COMPLETED + '-PARA-'))
            status = 'completed'
        elif tag.startswith(ONGOING + '-DE-'):
            level = LEVELS.get(tag.removeprefix(ONGOING + '-DE-'))
            status = 'ongoing'
        else:
            continue
        if not level:
            issues['unsupported_level'] += 1
            continue

        issues['identified_' + level + '_' + status] += 1
        prefix = 'DA-' if status == 'ongoing' else 'DE-'
        basic = node.find('DADOS-BASICOS-' + prefix + tag)
        detail = node.find('DETALHAMENTO-' + prefix + tag)
        if basic is None or detail is None:
            issues['missing_source_fields'] += 1
            continue
        ongoing = status == 'ongoing'
        source = {
            'level': level,
            'status': status,
            'student': detail.get('NOME-DO-ORIENTANDO' if ongoing else 'NOME-DO-ORIENTADO', '').strip(),
            'title': basic.get('TITULO-DO-TRABALHO' if ongoing else 'TITULO', '').strip(),
            'institution': detail.get('NOME-INSTITUICAO' if ongoing else 'NOME-DA-INSTITUICAO', '').strip(),
            'program': detail.get('NOME-CURSO' if ongoing else 'NOME-DO-CURSO', '').strip(),
            'program_en': detail.get('NOME-CURSO-INGLES' if ongoing else 'NOME-DO-CURSO-INGLES', '').strip(),
            'role': ROLES.get(detail.get('TIPO-DE-ORIENTACAO') or detail.get('TIPO-DE-ORIENTACAO-CONCLUIDA')),
        }
        year = basic.get('ANO', '').strip()
        source['year'] = int(year) if len(year) == 4 and year.isascii() and year.isdigit() and 1900 <= int(year) <= 2100 else None
        if not source['role']:
            issues['unclassified_role'] += 1
        if not all(source[key] for key in ('student', 'title', 'institution', 'program', 'year')):
            issues['incomplete_record'] += 1
        records.append(source)
    return records, issues


def identity(record):
    return tuple(normalize_text(record[key]) for key in ('student', 'level', 'institution', 'program'))


def exact_key(record):
    return (*identity(record), normalize_text(record['title']), record['status'], record['year'], record['role'])


def index(items, key):
    result = defaultdict(list)
    for item in items:
        result[key(item)].append(item)
    return result


def prepare_review(records, previous):
    counts = Counter()
    candidates = list({json.dumps(record, sort_keys=True): record for record in records}.values())
    if len(records) != len(candidates):
        counts['duplicates'] = len(records) - len(candidates)
    used_ids = {item['id'] for item in previous}
    if len(used_ids) != len(previous):
        raise ValueError('Previous review has duplicate IDs')
    previous_exact = index(previous, lambda item: exact_key(item['source']))
    previous_person = index(previous, lambda item: identity(item['source']))
    incoming_person = index(candidates, identity)
    incoming_exact = index(candidates, exact_key)
    output, matched = [], set()

    for record in candidates:
        key, person = exact_key(record), identity(record)
        exact = previous_exact[key]
        related = previous_person[person]
        literal = [item for item in exact if item['source'] == record]
        prior = literal[0] if len(literal) == 1 else None
        if prior is None and len(exact) == len(incoming_exact[key]) == 1:
            prior = exact[0]
        ambiguous = len(exact) > 1 or len(incoming_exact[key]) > 1
        if prior is None and related:
            if all(person) and len(related) == len(incoming_person[person]) == 1:
                old = related[0]['source']
                same_title = normalize_text(old['title']) == normalize_text(record['title']) != ''
                defense = (old['status'] == 'ongoing' and record['status'] == 'completed'
                           and old['year'] is not None and record['year'] is not None
                           and record['year'] >= old['year'])
                if defense or (same_title and old['status'] == record['status']):
                    prior = related[0]
            ambiguous = prior is None
        # Flag simultaneous ongoing/completed rows without guessing which should survive.
        peers = incoming_person[person]
        ambiguous |= len({entry['status'] for entry in peers}) > 1
        title = normalize_text(record['title'])
        if title:
            ambiguous |= sum(normalize_text(entry['title']) == title for entry in peers) > 1
        fingerprint = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()[:24]
        if prior and prior['id'] not in matched:
            matched.add(prior['id'])
            old = prior['source']
            change = 'unchanged' if old == record else 'updated'
            if old['status'] == 'ongoing' and record['status'] == 'completed':
                change = 'defense'
            item = {**prior, 'source': record, 'change': change}
        else:
            item_id = 'sup-' + fingerprint
            while item_id in used_ids:
                item_id += '-review'
            used_ids.add(item_id)
            item = {'id': item_id, 'source': record, 'editorial': {}, 'change': 'new'}
        if ambiguous:
            item['change'] = 'ambiguous'
        if item['change'] != 'unchanged':
            item['review_status'] = 'pending'
        counts[item['change']] += 1
        output.append(item)

    for item in previous:
        if item['id'] not in matched:
            counts['missing_from_export'] += 1
            output.append({**item, 'change': 'missing_from_export', 'review_status': 'pending'})
    return output, counts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export', type=Path)
    parser.add_argument('--previous', type=Path, help='Previous private review JSON')
    parser.add_argument('--review-output', type=Path, help='Write a new review JSON outside the repository')
    args = parser.parse_args(argv)
    try:
        if args.review_output:
            target = args.review_output.resolve()
            if target.is_relative_to(ROOT) or target.suffix.lower() != '.json':
                raise ValueError('Review output must be a new JSON outside the repository')
        previous = json.loads(args.previous.read_text('utf-8'))['items'] if args.previous else []
        records, issues = extract_records(extract(args.export))
        items, changes = prepare_review(records, previous)
        print(json.dumps({'extracted': len(records), 'diagnostics': dict(issues), 'changes': dict(changes)}, sort_keys=True))
        if args.review_output:
            with target.open('x', encoding='utf-8') as stream:
                json.dump({'items': items}, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
        return 0
    except (OSError, ValueError, KeyError, TypeError, LookupError, ElementTree.ParseError,
            expat.ExpatError, zipfile.BadZipFile, ZlibError, NotImplementedError) as error:
        print('Supervision review failed:', type(error).__name__, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
