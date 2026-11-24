"""Run with: python -m unittest discover -s tests -v"""
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

def load_module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class ContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder=load_module('build_site',ROOT/'scripts'/'build.py')
        cls.importer=load_module('lattes_import',ROOT/'scripts'/'import_lattes.py')

    def test_content_validation(self):
        self.builder.validate()

    def test_files_do_not_embed_sensitive_cv(self):
        # Guard against accidentally committing raw exports.
        for path in ROOT.rglob('*'):
            if 'dist' in path.parts or 'private' in path.parts or '.git' in path.parts:
                continue
            if path.is_file() and path.suffix.lower() in {'.xml','.zip','.rar'}:
                self.fail(f'Raw export unexpectedly in repository source: {path}')

    def test_four_language_translations_and_placeholders(self):
        import re
        data=json.loads((ROOT/'content/translations.json').read_text('utf-8'))
        for lang in ('pt','fr','zh'):
            self.assertEqual(set(data['en']),set(data[lang]))
            for key,source in data['en'].items():
                self.assertTrue(data[lang][key].strip(),(lang,key))
                self.assertEqual(set(re.findall(r'{(\w+)}',source)),set(re.findall(r'{(\w+)}',data[lang][key])),(lang,key))

    def test_multilingual_dynamic_content(self):
        def check(value):
            if isinstance(value,dict):
                if isinstance(value.get('en'),str) and 'pt' in value:
                    for lang in ('en','pt','fr','zh'):
                        self.assertTrue(isinstance(value.get(lang),str) and value[lang].strip(),(lang,value))
                else:
                    for child in value.values(): check(child)
            elif isinstance(value,list):
                for child in value: check(child)
        for filename in ('projects.json','supervisions.json','editorial.json'):
            check(json.loads((ROOT/'content'/filename).read_text('utf-8')))
        for record in json.loads((ROOT/'content/collaborations.json').read_text('utf-8')):
            for lang in ('en','pt','fr','zh'):
                self.assertTrue(record['relation_'+lang].strip())
                for person in record['people']: self.assertTrue(person['role_'+lang].strip())

    def test_build_versions_all_script_urls(self):
        import re, hashlib
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'dist'
            with patch.object(self.builder,'DIST',output): self.builder.build()
            html=(output/'index.html').read_text('utf-8')
            urls=re.findall(r'<script src="([^"]+)"',html)
            self.assertTrue(urls)
            for url in urls:
                path,version=url.split('?v=')
                self.assertEqual(version,hashlib.sha256((output/path).read_bytes()).hexdigest()[:12])
            previous=re.search(r'src="(data/translations.js[^"]+)"',html).group(1)
            self.assertIn('?v=',previous)

    def test_bilingual_translations_complete(self):
        data=json.loads((ROOT/'content/translations.json').read_text('utf-8'))
        self.assertEqual(set(data['en']),set(data['pt']))
        self.assertGreater(len(data['en']),80)

    def test_no_unverified_public_collaborations(self):
        cs=json.loads((ROOT/'content/collaborations.json').read_text('utf-8'))
        self.assertTrue(all(c.get('status') not in {'prospective','private','pending','unverified'} for c in cs if c['public']))
        self.assertTrue(all('people' in c for c in cs))

    def test_lattes_parse_and_categories(self):
        import xml.etree.ElementTree as ET
        root=ET.fromstring('''<CURRICULO-VITAE DATA-ATUALIZACAO="07112026"><PRODUCAO-BIBLIOGRAFICA><ARTIGOS-PUBLICADOS>
        <ARTIGO-PUBLICADO><DADOS-BASICOS-DO-ARTIGO TITULO-DO-ARTIGO="Bioenergy life cycle modeling" ANO-DO-ARTIGO="2026" DOI="10.1234/example"/>
        <DETALHAMENTO-DO-ARTIGO TITULO-DO-PERIODICO-OU-REVISTA="Journal Example"/>
        <AUTORES NOME-PARA-CITACAO="SILVEIRA, E. A."/></ARTIGO-PUBLICADO>
        </ARTIGOS-PUBLICADOS></PRODUCAO-BIBLIOGRAFICA></CURRICULO-VITAE>''')
        items=self.importer.parse(root)
        self.assertEqual(len(items),1)
        self.assertEqual(items[0]['doi'],'10.1234/example')
        self.assertIn('bioenergy',items[0]['categories'])
        self.assertIn('sustainability',items[0]['categories'])

    def test_lattes_import_dry_run_does_not_change_json(self):
        existing=(ROOT/'content/publications.json').read_bytes()
        with tempfile.TemporaryDirectory() as d:
            xml=Path(d)/'curriculo.xml'
            xml.write_text('''<CURRICULO-VITAE><ARTIGO-PUBLICADO><DADOS-BASICOS-DO-ARTIGO TITULO-DO-ARTIGO="A study" ANO-DO-ARTIGO="2026"/><DETALHAMENTO-DO-ARTIGO TITULO-DO-PERIODICO-OU-REVISTA="A Journal"/></ARTIGO-PUBLICADO></CURRICULO-VITAE>''',encoding='utf8')
            p=subprocess.run([sys.executable,str(ROOT/'scripts/import_lattes.py'),str(xml),'--dry-run'],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertIn('DRY RUN',p.stdout)
            self.assertEqual(existing,(ROOT/'content/publications.json').read_bytes())

    def test_site_structure(self):
        source=(ROOT/'site/index.html').read_text('utf-8')
        self.assertIn('id="project-list"',source)
        self.assertIn('id="map-world"',source)
        self.assertIn('id="map-brazil"',source)
        self.assertIn('data/translations.js',source)
        self.assertIn('project-cards.js',source)

class LattesRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.importer = load_module('lattes_regression', ROOT/'scripts'/'import_lattes.py')

    def setUp(self):
        scratch = self.enterContext(tempfile.TemporaryDirectory())
        self.directory = Path(scratch)

    def test_dtd_and_entities_are_rejected_after_decoding(self):
        declarations = (
            '<!DOCTYPE CURRICULO-VITAE>',
            '<!DOCTYPE CURRICULO-VITAE [<!ENTITY payload "expanded">]>',
            '<!DOCTYPE CURRICULO-VITAE SYSTEM "file:///private.xml">',
            '<!DOCTYPE CURRICULO-VITAE [<!ENTITY % remote SYSTEM "https://example.invalid/dtd">%remote;]>',
        )
        for encoding in ('utf-8', 'utf-16', 'utf-16-le', 'utf-16-be'):
            for declaration in declarations:
                with self.subTest(encoding=encoding, declaration=declaration):
                    path = self.directory/'cv.xml'
                    xml = '<?xml version="1.0"?>' + declaration + '<CURRICULO-VITAE/>'
                    path.write_bytes(xml.encode(encoding))
                    with self.assertRaisesRegex(ValueError, 'DTD/entity'):
                        self.importer.extract(path)

    def test_safe_utf16_and_predefined_entities_are_supported(self):
        path = self.directory/'cv.xml'
        xml = '<CURRICULO-VITAE TITLE="Energy &amp; heat"><!-- <!DOCTYPE example> --></CURRICULO-VITAE>'
        path.write_bytes(xml.encode('utf-16'))
        self.assertEqual(self.importer.extract(path).attrib['TITLE'], 'Energy & heat')

    def test_oversized_raw_and_compressed_xml_are_rejected(self):
        raw = self.directory/'cv.xml'
        raw.write_bytes(b'x' * 2048)
        archive = self.directory/'cv.zip'
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
            bundle.write(raw, 'cv.xml')
        with patch.object(self.importer, 'MAX_XML', 1024):
            for path in (raw, archive):
                with self.subTest(path=path.suffix), self.assertRaisesRegex(ValueError, 'XML exceeds size limit'):
                    self.importer.extract(path)
            with self.assertRaisesRegex(ValueError, 'XML exceeds size limit'):
                self.importer.read_xml(io.BytesIO(b'x' * 2048))
        with patch.object(self.importer, 'MAX_ZIP', 1):
            with self.assertRaisesRegex(ValueError, 'ZIP exceeds size limit'):
                self.importer.extract(archive)

    def test_zip_rejects_multiple_xml_files_and_too_many_entries(self):
        archive = self.directory/'cv.zip'
        with zipfile.ZipFile(archive, 'w') as bundle:
            bundle.writestr('one.xml', '<CURRICULO-VITAE/>')
            bundle.writestr('two.xml', '<CURRICULO-VITAE/>')
        with self.assertRaisesRegex(ValueError, 'one XML'):
            self.importer.extract(archive)
        with patch.object(self.importer, 'MAX_ZIP_ENTRIES', 1):
            with self.assertRaisesRegex(ValueError, 'too many entries'):
                self.importer.extract(archive)

    def test_zip_does_not_extract_member_paths_and_blocks_utf16_dtd(self):
        nested = self.directory/'archives'
        nested.mkdir()
        archive = nested/'cv.zip'
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr('../cv.xml', '<CURRICULO-VITAE/>'.encode('utf-16'))
        self.assertEqual(self.importer.extract(archive).tag, 'CURRICULO-VITAE')
        self.assertEqual(list(self.directory.iterdir()), [nested])
        self.assertEqual(list(nested.iterdir()), [archive])
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr('cv.xml', '<!DOCTYPE CURRICULO-VITAE><CURRICULO-VITAE/>'.encode('utf-16'))
        with self.assertRaisesRegex(ValueError, 'DTD/entity'):
            self.importer.extract(archive)

    def test_zip_rejects_unsupported_compression(self):
        archive = self.directory/'cv.zip'
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_LZMA) as bundle:
            bundle.writestr('cv.xml', '<CURRICULO-VITAE/>')
        with self.assertRaisesRegex(ValueError, 'stored or deflated'):
            self.importer.extract(archive)

    def test_xml_structural_limits(self):
        path = self.directory/'cv.xml'
        path.write_text('<cv><a><b/></a></cv>', encoding='utf-8')
        for limit in ('MAX_XML_DEPTH', 'MAX_XML_ELEMENTS'):
            with self.subTest(limit=limit), patch.object(self.importer, limit, 2):
                with self.assertRaisesRegex(ValueError, 'structural limits'):
                    self.importer.extract(path)

    def article(self, **fields):
        return {
            'title': 'Conversão de biomassa', 'year': 2022, 'journal': 'Original journal',
            'authors': 'Ana Silva; Edgar Silveira', 'doi': '', 'categories': ['bioenergy'],
            **fields,
        }

    def test_doi_promotion_preserves_existing_record_and_is_idempotent(self):
        previous = self.article(categories=['other'], title_override='Reviewed title',
                                journal_override='Reviewed journal', note='Editorial note', featured=False)
        manual = self.article(title='An unrelated manual record', source='manual')
        incoming = self.article(title='  CONVERSA\u0303O  DE BIOMASSA ', journal='Incoming journal',
                                authors='ana silva ; EDGAR SILVEIRA', doi=' HTTPS://DX.DOI.ORG/10.1234/NEW ')
        records, new, review = self.importer.merge_publications([previous, manual], [incoming])
        self.assertEqual(records, [{**previous, 'doi': '10.1234/new'}, manual])
        self.assertEqual((new, review), ([], []))
        self.assertEqual(self.importer.merge_publications(records, [incoming]), (records, [], []))
        self.assertEqual(previous['doi'], '')

    def test_exact_normalized_doi_wins_and_fills_missing_authors(self):
        previous = self.article(doi='DOI:10.1234/SAME', authors='', title='Reviewed title')
        other = self.article()
        incoming = self.article(doi='https://doi.org/10.1234/same')
        records, new, review = self.importer.merge_publications([previous, other], [incoming])
        self.assertEqual(records, [{**previous, 'doi': '10.1234/same', 'authors': incoming['authors']}, other])
        self.assertEqual((new, review), ([], []))

    def test_no_fallback_when_year_or_authors_differ_or_are_missing(self):
        previous = self.article()
        for fields in ({'year': 2023}, {'authors': 'Ana Silva'}, {'authors': ''},
                       {'authors': 'Edgar Silveira; Ana Silva'}):
            with self.subTest(fields=fields):
                incoming = self.article(doi='10.1234/new', **fields)
                records, new, _ = self.importer.merge_publications([previous], [incoming])
                self.assertEqual((records, new), ([previous, incoming], [incoming]))
        abbreviated = self.article(authors='Ana Silva et al.')
        incoming = {**abbreviated, 'doi': '10.1234/new'}
        records, new, _ = self.importer.merge_publications([abbreviated], [incoming])
        self.assertEqual((records, new), ([abbreviated, incoming], [incoming]))

    def test_ambiguity_and_distinct_dois_keep_records_separate(self):
        without_doi = self.article()
        first_doi = self.article(doi='10.1234/first')
        second_doi = self.article(doi='10.1234/second')
        for prior, incoming in (([without_doi, first_doi], [second_doi]),
                                ([without_doi], [first_doi, second_doi]),
                                ([first_doi], [second_doi])):
            with self.subTest(prior=prior, incoming=incoming):
                records, new, review = self.importer.merge_publications(prior, incoming)
                self.assertEqual(records, prior + incoming)
                self.assertEqual(new, incoming)
                self.assertEqual(review, incoming)

    def test_cli_updates_only_scratch_catalog_and_rejects_conflicting_keys(self):
        catalog = self.directory/'publications.json'
        xml = self.directory/'cv.xml'
        old = self.article(note='Preserve this')
        unrelated = self.article(title='Unrelated manual entry')
        catalog.write_text(json.dumps({'items': [old, unrelated]}), encoding='utf-8')
        document = (
            '<CURRICULO-VITAE><ARTIGO-PUBLICADO><DADOS-BASICOS-DO-ARTIGO '
            'TITULO-DO-ARTIGO="Conversão de biomassa" ANO-DO-ARTIGO="{year}" {doi}/>'
            '<DETALHAMENTO-DO-ARTIGO TITULO-DO-PERIODICO-OU-REVISTA="Imported journal"/>'
            '<AUTORES NOME-PARA-CITACAO="Ana Silva"/><AUTORES NOME-PARA-CITACAO="Edgar Silveira"/>'
            '</ARTIGO-PUBLICADO></CURRICULO-VITAE>'
        )
        xml.write_text(document.format(year=2022, doi='DOI="10.1234/new"'), encoding='utf-8')
        with patch.object(self.importer, 'DEST', catalog), patch('sys.stdout', new_callable=io.StringIO):
            self.assertEqual(self.importer.main([str(xml)]), 0)
            updated = catalog.read_bytes()
            self.assertCountEqual(json.loads(updated)['items'], [{**old, 'doi': '10.1234/new', 'source': 'lattes'}, unrelated])
            builder = load_module('lattes_regression_build', ROOT/'scripts'/'build.py')
            for source in (ROOT/'content').glob('*.json'):
                if source.name != catalog.name:
                    (self.directory/source.name).write_bytes(source.read_bytes())
            scratch_cv=json.loads((self.directory/'cv.json').read_text('utf-8'))
            scratch_cv.update(status='draft',selected_publications=[])
            (self.directory/'cv.json').write_text(json.dumps(scratch_cv),encoding='utf-8')
            with patch.object(builder, 'CONTENT', self.directory):
                builder.validate()
            xml.write_text(document.format(year=2023, doi='').replace(old['title'], unrelated['title']),
                           encoding='utf-8')
            with patch('sys.stderr', new_callable=io.StringIO) as errors:
                self.assertEqual(self.importer.main([str(xml)]), 1)
                self.assertIn('Conflicting catalog keys', errors.getvalue())
            self.assertEqual(catalog.read_bytes(), updated)
            xml.write_text(document.format(year=2022, doi='DOI="invalid"'), encoding='utf-8')
            with patch('sys.stderr', new_callable=io.StringIO) as errors:
                self.assertEqual(self.importer.main([str(xml)]), 1)
                self.assertIn('Invalid DOI', errors.getvalue())
            self.assertEqual(catalog.read_bytes(), updated)

class CollaborationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = load_module('collaboration_build', ROOT/'scripts'/'build.py')
        cls.records = json.loads((ROOT/'content/collaborations.json').read_text('utf-8'))

    def test_scope_and_status_are_independent(self):
        fixture = self.records[0]
        combinations = [
            {'scope': 'personal', 'status': 'active'},
            {'scope': 'personal', 'status': 'completed'},
            {'scope': 'institutional', 'status': 'historical', 'institutional_owner': 'LEA'},
            {'scope': 'institutional', 'status': 'documented', 'institutional_owner': 'UnB'},
            {'scope': 'academic', 'status': 'historical'},
            {'scope': 'research', 'status': 'documented'},
            {'scope': 'negotiation', 'status': 'pending', 'public': False},
        ]
        for fields in combinations:
            with self.subTest(fields=fields):
                self.builder.validate_collaboration({**fixture, **fields}, 0)
        for fields in (
            {'scope': 'personal', 'status': 'historical'},
            {'scope': 'research', 'status': 'active'},
            {'scope': 'institutional', 'status': 'historical'},
            {'scope': 'negotiation', 'status': 'pending'},
        ):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                self.builder.validate_collaboration({**fixture, **fields}, 0)

    def test_optional_details_require_bilingual_metadata_and_safe_links(self):
        fixture = {
            **self.records[0],
            'topic': {'en': 'Synthetic topic', 'pt': 'Tema sintético'},
            'period': {'start': 2020, 'end': 2023},
            'people': [{'name': 'Synthetic name', 'role_en': 'Researcher', 'role_pt': 'Pesquisador'}],
            'publications': [{'title': 'Synthetic paper', 'url': 'https://example.invalid/paper'}],
            'links': [{'label': {'en': 'Lab', 'pt': 'Laboratório'}, 'url': 'https://example.invalid/lab'}],
        }
        self.builder.validate_collaboration(fixture, 0)
        for invalid in (
            {'topic': {'en': 'Missing translation'}},
            {'period': {'start': 2023, 'end': 2020}},
            {'people': [{'name': 'Synthetic name', 'role_en': 'Researcher'}]},
            {'publications': [{'title': 'Synthetic paper', 'url': 'javascript:alert(1)'}]},
            {'links': [{'label': {'en': 'Lab'}, 'url': 'https://example.invalid/lab'}]},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.builder.validate_collaboration({**fixture, **invalid}, 0)

    def test_build_filters_private_and_negotiation_records(self):
        fixture = self.records[0]
        hidden = [
            {**fixture, 'id': 'test-private', 'public': False},
            {**fixture, 'id': 'test-negotiation', 'scope': 'negotiation', 'status': 'pending', 'public': False},
        ]
        scratch = Path(self.enterContext(tempfile.TemporaryDirectory()))
        output = scratch/'dist'
        load = self.builder.load
        with patch.object(self.builder, 'DIST', output), patch.object(
            self.builder, 'load',
            side_effect=lambda name: self.records + hidden if name == 'collaborations.json' else load(name),
        ), patch('sys.stdout', new_callable=io.StringIO):
            self.builder.build()
        bundle = (output/'data/collaborations.js').read_text('utf-8')
        payload = json.loads(bundle.split(' = ', 1)[1].rstrip().removesuffix(';'))
        self.assertEqual(payload, self.records)

    def test_build_rejects_missing_accessible_translation(self):
        load = self.builder.load
        translations = load('translations.json')
        for language in translations.values():
            del language['ariaWorld']
        with patch.object(self.builder, 'load', side_effect=lambda name:
                          translations if name == 'translations.json' else load(name)):
            with self.assertRaisesRegex(ValueError, r'translations\.en\.ariaWorld'):
                self.builder.validate()

if __name__=='__main__': unittest.main()
