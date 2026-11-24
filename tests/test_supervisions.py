"""Regression tests for the private review and the public supervision boundary."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

from test_pipeline import load_module, ROOT

sys.path.insert(0, str(ROOT/'scripts'))
try:
    import import_supervisions as importer
finally:
    sys.path.pop(0)


def source(**fields):
    return {
        'student': 'Synthetic Student', 'title': 'Título original de teste',
        'institution': 'Synthetic University', 'program': 'Programa de teste',
        'program_en': 'Test program', 'role': 'co-supervisor', 'level': 'masters',
        'year': 2024, 'status': 'ongoing', **fields,
    }


class SupervisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = load_module('supervision_build', ROOT/'scripts'/'build.py')

    def test_extracts_levels_status_roles_and_only_allowed_fields(self):
        xml = ElementTree.fromstring("""
        <CURRICULO-VITAE>
          <ORIENTACOES-CONCLUIDAS-PARA-MESTRADO>
            <DADOS-BASICOS-DE-ORIENTACOES-CONCLUIDAS-PARA-MESTRADO TITULO="Título original" ANO="2024" HOME-PAGE="https://example.invalid" />
            <DETALHAMENTO-DE-ORIENTACOES-CONCLUIDAS-PARA-MESTRADO NOME-DO-ORIENTADO="Synthetic Student"
              NOME-DA-INSTITUICAO="Synthetic University" NOME-DO-CURSO="Programa"
              TIPO-DE-ORIENTACAO="CO_ORIENTADOR" NUMERO-ID-ORIENTADO="private-sentinel" />
          </ORIENTACOES-CONCLUIDAS-PARA-MESTRADO>
          <ORIENTACAO-EM-ANDAMENTO-DE-DOUTORADO>
            <DADOS-BASICOS-DA-ORIENTACAO-EM-ANDAMENTO-DE-DOUTORADO TITULO-DO-TRABALHO="Provisional test title" ANO="2025" />
            <DETALHAMENTO-DA-ORIENTACAO-EM-ANDAMENTO-DE-DOUTORADO NOME-DO-ORIENTANDO="Synthetic Student"
              NOME-INSTITUICAO="Synthetic University" NOME-CURSO="Programa" NOME-CURSO-INGLES="Program"
              TIPO-DE-ORIENTACAO="ORIENTADOR_PRINCIPAL" />
          </ORIENTACAO-EM-ANDAMENTO-DE-DOUTORADO>
          <OUTRAS-ORIENTACOES-CONCLUIDAS>
            <DADOS-BASICOS-DE-OUTRAS-ORIENTACOES-CONCLUIDAS TITULO="Pesquisa" ANO="2024" NATUREZA="INICIACAO_CIENTIFICA" />
            <DETALHAMENTO-DE-OUTRAS-ORIENTACOES-CONCLUIDAS NOME-DO-ORIENTADO="Synthetic Student"
              NOME-DA-INSTITUICAO="Synthetic University" NOME-DO-CURSO="Programa" />
          </OUTRAS-ORIENTACOES-CONCLUIDAS>
        </CURRICULO-VITAE>""")
        records, issues = importer.extract_records(xml)
        self.assertEqual([(x['level'], x['status'], x['role']) for x in records], [
            ('masters', 'completed', 'co-supervisor'), ('phd', 'ongoing', 'supervisor'),
            ('undergraduate-research', 'completed', None),
        ])
        self.assertEqual(records[0]['title'], 'Título original')
        self.assertEqual(records[1]['program_en'], 'Program')
        self.assertEqual(issues['unclassified_role'], 1)
        self.assertNotIn('private-sentinel', json.dumps(records))
        self.assertNotIn('example.invalid', json.dumps(records))

    def test_defense_keeps_id_and_manual_fields_and_is_idempotent(self):
        previous, _ = importer.prepare_review([source()], [])
        previous[0]['editorial'] = {'student': 'Reviewed name', 'areas': ['bioenergy']}
        previous[0]['review_status'] = 'approved'
        done = source(status='completed', title='Título definitivo', year=2026)
        items, changes = importer.prepare_review([done, done], previous)
        self.assertEqual(changes, {'duplicates': 1, 'defense': 1})
        self.assertEqual(items[0]['id'], previous[0]['id'])
        self.assertEqual(items[0]['editorial'], previous[0]['editorial'])
        self.assertEqual(items[0]['review_status'], 'pending')
        again, changes = importer.prepare_review([done], items)
        self.assertEqual(changes, {'unchanged': 1})
        self.assertEqual(again[0]['id'], items[0]['id'])

    def test_conflicting_records_remain_in_private_review(self):
        previous, _ = importer.prepare_review([source()], [])
        done = source(status='completed', title='Definitive', year=2026)
        other = source(status='completed', title='Another candidate', year=2026)
        items, changes = importer.prepare_review([done, other], previous)
        self.assertEqual(changes, {'ambiguous': 2, 'missing_from_export': 1})
        self.assertEqual(len({item['id'] for item in items}), 3)
        self.assertIn(previous[0]['id'], {item['id'] for item in items})

    def test_missing_or_unsupported_fields_are_counted(self):
        xml = ElementTree.fromstring('<CURRICULO-VITAE><ORIENTACOES-CONCLUIDAS-PARA-MESTRADO/>'
                                    '<ORIENTACAO-EM-ANDAMENTO-DE-POS-DOUTORADO/></CURRICULO-VITAE>')
        records, issues = importer.extract_records(xml)
        self.assertFalse(records)
        self.assertEqual(issues, {'identified_masters_completed': 1, 'missing_source_fields': 1, 'unsupported_level': 1})

    def test_cli_rejects_review_output_inside_repository(self):
        result = subprocess.run(
            [sys.executable, '-B', str(ROOT/'scripts/import_supervisions.py'), 'missing.xml',
             '--review-output', str(ROOT/'content/supervisions.json')],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn('ValueError', result.stderr)

    def public_fixture(self, **fields):
        return {
            'id': 'test-1', 'approved': True, 'level': 'masters', 'status': 'completed',
            'student': 'Synthetic Student', 'title': 'Título original', 'year': 2024,
            'institution': 'Synthetic University', 'program': 'Programa',
            'role': 'co-supervisor', 'areas': ['bioenergy'], **fields,
        }

    def validate(self, *items):
        self.builder.validate_supervisions(
            {'areas': {'bioenergy': {'en': 'Bioenergy', 'pt': 'Bioenergia'}}, 'items': list(items)},
            {'items': [{'doi': '10.1234/example'}]}, [{'id': 'project', 'public': True}],
        )

    def test_public_validation_requires_approval_and_omits_provisional_titles(self):
        approved = self.public_fixture(publications=['10.1234/example'], projects=['project'])
        self.validate(approved)
        ongoing = {**approved, 'status': 'ongoing', 'topic': {'en': 'Reviewed topic', 'pt': 'Tema revisado'}}
        with self.assertRaisesRegex(ValueError, 'private field'):
            self.validate(ongoing)
        del ongoing['title']
        self.validate(ongoing)
        for fields in ({'approved': False}, {'private_identifier': 'sentinel'},
                       {'repository_url': 'https://example.invalid/thesis'}, {'areas': ['unknown']},
                       {'publications': ['10.1234/unknown']}, {'projects': ['unknown']}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                self.validate({**approved, **fields})
        with self.assertRaisesRegex(ValueError, 'duplicate supervision'):
            self.validate(approved, {**approved, 'id': 'test-2'})
        self.validate({**approved, 'repository_url': 'https://example.invalid/thesis', 'repository_verified': True})
        complementary = {**approved, 'level': 'undergraduate-research'}
        del complementary['program']
        del complementary['role']
        self.validate(complementary)

    def test_build_produces_public_bundle_without_pending_records(self):
        scratch = Path(self.enterContext(tempfile.TemporaryDirectory()))
        destination = scratch/'dist'
        load = self.builder.load
        with patch.object(self.builder, 'DIST', destination), patch.object(
            self.builder, 'load',
            side_effect=lambda name: {'areas': {}, 'items': []} if name == 'supervisions.json' else load(name),
        ):
            self.builder.build()
        bundle = (destination/'data/supervisions.js').read_text('utf-8')
        catalog = json.loads(bundle.split(' = ', 1)[1].rstrip().removesuffix(';'))
        self.assertEqual(catalog['items'], [])
        html = (destination/'index.html').read_text('utf-8')
        self.assertIn('href="#supervision"', html)
        self.assertRegex(html, r'src="data/supervisions\.js\?v=[0-9a-f]{12}"')


class UndergraduateReviewTests(unittest.TestCase):
    def test_lattes_keeps_distinct_students_and_levels_without_inventing_roles(self):
        root=ElementTree.Element('CURRICULO-VITAE')
        for student,nature,year in [('Student A','INICIACAO_CIENTIFICA','2020'),('Student A','TRABALHO_DE_CONCLUSAO_DE_CURSO_GRADUACAO','2021'),('Student B','TRABALHO_DE_CONCLUSAO_DE_CURSO_GRADUACAO','2021')]:
            record=ElementTree.SubElement(root,'OUTRAS-ORIENTACOES-CONCLUIDAS')
            ElementTree.SubElement(record,'DADOS-BASICOS-DE-OUTRAS-ORIENTACOES-CONCLUIDAS',NATUREZA=nature,TITULO='Same original title',ANO=year)
            ElementTree.SubElement(record,'DETALHAMENTO-DE-OUTRAS-ORIENTACOES-CONCLUIDAS',{'NOME-DO-ORIENTADO':student,'NOME-DA-INSTITUICAO':'Synthetic University','NUMERO-ID-ORIENTADO':'private-sentinel'})
        records,issues=importer.extract_records(root)
        self.assertEqual(len(records),3)
        self.assertEqual({r['level'] for r in records},{'undergraduate-research','undergraduate-thesis'})
        self.assertTrue(all(r['role'] is None and r['program']=='' for r in records))
        review,counts=importer.prepare_review(records,[])
        self.assertEqual(len({r['id'] for r in review}),3)
        self.assertTrue(all(r['review_status']=='pending' for r in review))
        self.assertNotIn('private-sentinel',json.dumps(review))

    def test_unapproved_undergraduate_cannot_enter_public_catalog(self):
        builder=load_module('undergraduate_boundary',ROOT/'scripts/build.py')
        catalog=json.loads((ROOT/'content/supervisions.json').read_text(encoding='utf-8'))
        catalog['items'].append({'id':'synthetic-undergrad','approved':False,'level':'undergraduate-thesis','status':'completed','student':'Synthetic Student','title':'Original title','institution':'Synthetic University','year':2024})
        with self.assertRaisesRegex(ValueError,'approved'):
            builder.validate_supervisions(catalog,builder.load('publications.json'),builder.load('projects.json'))
