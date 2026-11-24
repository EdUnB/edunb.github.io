"""Compare two private Lattes exports and optionally stage a private editorial review."""
from collections import Counter, defaultdict
import argparse
import json
from pathlib import Path
import sys
from xml.parsers import expat
from xml.etree import ElementTree
from zipfile import BadZipFile
from zlib import error as ZlibError

from import_lattes import article_doi, extract, normalize_text, parse, signature
from import_supervisions import extract_records, prepare_review

ROOT = Path(__file__).resolve().parents[1]
ROLES = {
    'review editor': 'review-editor',
    'editor revisor': 'review-editor',
    'associate editor': 'associate-editor',
    'editor associado': 'associate-editor',
    'editorial board member': 'board-member',
    'membro de corpo editorial': 'board-member',
    'guest editor': 'guest-editor',
    'editor convidado': 'guest-editor',
    'revisor de periódico': 'peer-reviewer',
    'journal reviewer': 'peer-reviewer',
}


def editorial_records(root):
    records = []
    for institution in root.iter('ATUACAO-PROFISSIONAL'):
        journal = institution.get('NOME-INSTITUICAO', '').strip()
        for appointment in institution.iter('VINCULOS'):
            role = ROLES.get(normalize_text(appointment.get('OUTRO-VINCULO-INFORMADO', '')))
            if not journal or not role:
                continue
            record = {'journal': journal, 'role': role}
            for field, attribute in (('start', 'ANO-INICIO'), ('end', 'ANO-FIM')):
                value = appointment.get(attribute, '')
                if len(value) == 4 and value.isascii() and value.isdigit():
                    record[field] = int(value)
            records.append(record)
    return records


def compare_records(old, new, key):
    def group(records):
        groups = defaultdict(list)
        for record in records:
            groups[key(record)].append(record)
        return groups

    left, right = group(old), group(new)
    counts = Counter(dict.fromkeys(('new', 'modified', 'preserved', 'absent', 'ambiguous'), 0))
    pairs = []
    for identity in dict.fromkeys([*left, *right]):
        before, after = list(left[identity]), list(right[identity])
        for row in before[:]:
            if row in after:
                before.remove(row)
                after.remove(row)
                counts['preserved'] += 1
                pairs.append(('preserved', row, row))
        if identity is not None and len(before) == len(after) == 1 and len(left[identity]) == len(right[identity]) == 1:
            counts['modified'] += 1
            pairs.append(('modified', before[0], after[0]))
        elif before and after:
            counts['ambiguous'] += len(after)
            pairs.extend(('ambiguous', None, row) for row in after)
            pairs.extend(('ambiguous', row, None) for row in before)
        else:
            counts['absent'] += len(before)
            counts['new'] += len(after)
            pairs.extend(('absent', row, None) for row in before)
            pairs.extend(('new', None, row) for row in after)
    return dict(counts), pairs


def compare_articles(old, new):
    counts, pairs = compare_records(old, new, lambda row: article_doi(row) or signature(row))
    # Same bibliographic signature with a DOI change is evidence for review, not a merge.
    absent = [a for status, a, _ in pairs if status == 'absent' and signature(a)]
    added = [b for status, _, b in pairs if status == 'new' and signature(b)]
    doi_candidates = [(a['doi'], b['doi']) for a in absent for b in added
                      if signature(a) == signature(b) and article_doi(a) != article_doi(b)]
    return counts, pairs, doi_candidates


def editorial_review(pairs, manual):
    prior = defaultdict(list)
    for row in manual:
        prior[(normalize_text(row['journal']), row['role'])].append(row.get('editorial', row))
    result, consumed = [], set()
    for status, old, new in pairs:
        row = new or old
        identity = (normalize_text(row['journal']), row['role'])
        corrections = prior.get(identity, [])
        item = {'source': row, 'editorial': corrections, 'change': status}
        if status == 'modified':
            item['previous_source'] = old
        result.append(item)
        consumed.add(identity)
    for identity, row in prior.items():
        if identity not in consumed:
            result.append({'source': None, 'editorial': row, 'change': 'manual-only'})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('previous', type=Path)
    parser.add_argument('latest', type=Path)
    parser.add_argument('--manual', type=Path, help='Optional private JSON list of journal, role and editorial overrides')
    parser.add_argument('--review-output', type=Path, help='New private JSON path outside the repository')
    args = parser.parse_args()
    try:
        if args.review_output and (args.review_output.resolve().is_relative_to(ROOT)
                                   or args.review_output.suffix.lower() != '.json'):
            raise ValueError('Use a private JSON path')
        old, new = extract(args.previous), extract(args.latest)
        articles, article_pairs, dois = compare_articles(parse(old), parse(new))
        old_supervision, _ = extract_records(old)
        new_supervision, _ = extract_records(new)
        previous, _ = prepare_review(old_supervision, [])
        supervision_items, supervisions = prepare_review(new_supervision, previous)
        editorial, pairs = compare_records(editorial_records(old), editorial_records(new),
                                           lambda row: (normalize_text(row['journal']), row['role']))
        sections = {tag: [ElementTree.tostring(x) for x in old.findall(tag)] ==
                         [ElementTree.tostring(x) for x in new.findall(tag)]
                    for tag in sorted({node.tag for root in (old, new) for node in root})}
        summary = {'sections_preserved': sections, 'root_attributes_preserved': old.attrib == new.attrib,
                   'articles': articles, 'possible_doi_changes': len(dois),
                   'supervisions': dict(supervisions), 'editorial': editorial}
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if args.review_output:
            manual = (json.loads(args.manual.read_text('utf-8')) if args.manual else
                      json.loads((ROOT/'content'/'editorial.json').read_text('utf-8'))['items'])
            with args.review_output.open('x', encoding='utf-8') as stream:
                json.dump({'summary': summary, 'editorial': editorial_review(pairs, manual),
                           'article_changes': [{'change': change, 'before': before, 'after': after}
                                               for change, before, after in article_pairs if change != 'preserved'],
                           'supervision_changes': [item for item in supervision_items if item['change'] != 'unchanged'],
                           'possible_doi_changes': dois}, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
        return 0
    except (OSError, ValueError, TypeError, KeyError, ElementTree.ParseError, expat.ExpatError,
            BadZipFile, ZlibError, NotImplementedError, LookupError) as error:
        print('Lattes comparison failed:', type(error).__name__, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
