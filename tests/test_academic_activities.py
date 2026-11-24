"""Regression tests for editorial review and institutional repository matching."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

from test_pipeline import ROOT, load_module

sys.path.insert(0, str(ROOT/'scripts'))
try:
    from compare_lattes import compare_articles, compare_records, editorial_records, editorial_review
    from find_unb_supervisions import Repository, classify, dim_fields, repository_item
finally:
    sys.path.pop(0)


class AcademicActivityTests(unittest.TestCase):
    def test_editorial_extraction_ignores_private_notes_and_funding_review(self):
        root = ElementTree.fromstring("""
        <CURRICULO-VITAE><ATUACAO-PROFISSIONAL NOME-INSTITUICAO="Journal">
          <ATIVIDADES><VINCULOS OUTRO-VINCULO-INFORMADO="Membro de corpo editorial"
              ANO-INICIO="2021" OUTRAS-INFORMACOES="private sentinel"/>
            <VINCULOS OUTRO-VINCULO-INFORMADO="Revisor de projeto de fomento" ANO-INICIO="2022"/>
          </ATIVIDADES>
        </ATUACAO-PROFISSIONAL></CURRICULO-VITAE>""")
        self.assertEqual(editorial_records(root), [
            {'journal': 'Journal', 'role': 'board-member', 'start': 2021},
        ])

    def test_period_changes_preserve_editorial_overrides_and_absences(self):
        old = {'journal': 'Journal', 'role': 'board-member', 'start': 2021}
        absent = {'journal': 'Other', 'role': 'peer-reviewer'}
        new = {**old, 'end': 2025}
        added = {'journal': 'New', 'role': 'review-editor'}
        counts, pairs = compare_records([old, absent], [new, added], lambda row: (row['journal'], row['role']))
        self.assertEqual(counts, {'modified': 1, 'absent': 1, 'new': 1, 'preserved': 0, 'ambiguous': 0})
        manual = [{'journal': 'JOURNAL', 'role': 'board-member', 'editorial': {'start': 2020}}]
        staged = editorial_review(pairs, manual)
        self.assertEqual(staged[0]['source']['end'], 2025)
        self.assertEqual(staged[0]['editorial'], [{'start': 2020}])
        self.assertTrue(any(row['change'] == 'absent' for row in staged))

    def test_publication_comparison_flags_doi_change_without_merging(self):
        old = {'title': 'Synthetic article', 'year': 2022, 'authors': 'Test Author', 'doi': ''}
        new = {**old, 'doi': '10.1234/example'}
        counts, pairs, candidates = compare_articles([old], [new])
        self.assertEqual((counts['new'], counts['absent'], counts['modified']), (1, 1, 0))
        self.assertEqual(candidates, [('', '10.1234/example')])
        self.assertEqual(len(pairs), 2)

    def test_repository_requires_identity_title_degree_year_and_role(self):
        record = {'student': 'Ana da Silva Costa', 'title': 'Torrefação de biomassa',
                  'level': 'masters', 'year': 2024, 'role': 'co-supervisor',
                  'institution': 'Universidade de Brasília'}
        metadata = {
            'url': 'https://repositorio.unb.br/handle/10482/42',
            'authors': ['Costa, Ana da Silva'], 'titles': ['Torrefação de biomassa'],
            'year': 2024, 'level': 'masters', 'institution': 'Universidade de Brasília',
            'advisors': ['Advisor, Other'], 'coadvisors': ['Silveira, Edgar Amaral'],
        }
        self.assertEqual(classify(record, [metadata])['status'], 'confirmed')
        self.assertEqual(classify(record, [{**metadata, 'coadvisors': []}])['status'], 'probable')
        self.assertEqual(classify(record, [{**metadata, 'authors': ['Other Name']}])['status'], 'conflicting')
        self.assertEqual(classify(record, [{**metadata, 'level': 'phd'}])['status'], 'conflicting')
        self.assertEqual(classify(record, [{**metadata, 'level_conflict': True}])['status'], 'conflicting')
        self.assertEqual(classify(record, [{**metadata, 'titles': ['Unrelated subject']}])['status'], 'conflicting')
        self.assertEqual(classify(record, [])['status'], 'not-found')

    def test_dim_understands_unb_coadvisor_and_defense_year(self):
        fields = dim_fields(b"""<dim xmlns="http://www.dspace.org/xmlns/dspace/dim">
            <field mdschema="dc" element="contributor" qualifier="advisorco">Silveira, Edgar Amaral</field>
            <field mdschema="dc" element="date" qualifier="submitted">2024-01-09</field>
            <field mdschema="dc" element="date" qualifier="issued">2025</field>
        </dim>""")
        item = repository_item('10482/42', fields)
        self.assertEqual(item['coadvisors'], ['Silveira, Edgar Amaral'])
        self.assertEqual(item['year'], 2024)
        contradictory = repository_item('10482/42', {
            'dc.type': ['Dissertação'],
            'dc.identifier.citation': ['Título. Tese (Doutorado) — Universidade de Brasília.'],
        })
        self.assertTrue(contradictory['level_conflict'])

    def test_offline_repository_does_not_fetch(self):
        scratch = Path(self.enterContext(tempfile.TemporaryDirectory()))
        repo = Repository(scratch, offline=True)
        with patch('find_unb_supervisions.urlopen') as request:
            with self.assertRaisesRegex(ValueError, 'offline cache'):
                repo.formats()
        request.assert_not_called()

    def test_editorial_catalog_excludes_invitation_and_private_fields(self):
        build = load_module('editorial_build', ROOT/'scripts'/'build.py')
        record = {'id': 'review', 'approved': True, 'category': 'reviewing',
                  'role': 'peer-reviewer', 'journal': 'Journal', 'status': 'documented'}
        build.validate_editorial({'items': [record]})
        for invalid in ({'approved': False}, {'status': 'invited'}, {'manuscript': 'private'},
                        {'start': 2025, 'end': 2024}, {'url': 'javascript:alert(1)'}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                build.validate_editorial({'items': [{**record, **invalid}]})
