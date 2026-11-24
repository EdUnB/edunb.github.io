"""Synchronization, review gates and privacy of the short academic CV."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cv_build_tests',ROOT/'scripts/build.py')
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ShortCVTests(unittest.TestCase):
    def setUp(self):
        self.config=builder.load('cv.json')
        self.config['status']='draft'
        self.config['selected_publications']=[]
        self.profile,self.pubs,_,_,self.translations,self.supervisions,self.editorial=builder.validate()

    def snapshot(self):
        return builder.CV.prepare(self.config,self.profile,self.pubs,self.supervisions,self.editorial,self.translations)

    def select_first(self):
        self.config['selected_publications']=[{'doi':self.pubs['items'][0]['doi']}]

    def test_counts_and_four_languages_come_from_approved_catalogs(self):
        snapshot=self.snapshot()
        self.assertEqual(set(snapshot['documents']),{'en','pt','fr','zh'})
        for document in snapshot['documents'].values():
            self.assertEqual(document['publication_count'],50)
            self.assertEqual(document['supervisions']['completed'],{'masters':12,'phd':1})
            self.assertEqual(document['supervisions']['ongoing'],{'masters':5,'phd':9})
            self.assertEqual(len(document['editorial']),2)

    def test_review_is_required_and_draft_stays_out_of_build(self):
        snapshot=self.snapshot()
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'cv'
            self.assertEqual(builder.CV.write_documents(snapshot,output),[])
            self.assertFalse(output.exists())
            original_load=builder.load
            with patch.object(builder,'DIST',Path(directory)/'dist'),patch.object(builder,'load',side_effect=lambda name:self.config if name=='cv.json' else original_load(name)):
                builder.build()
                self.assertFalse((builder.DIST/'cv').exists())
                self.assertNotIn('data-short-cv',(builder.DIST/'index.html').read_text('utf-8'))
        self.config['status']='approved'
        with self.assertRaisesRegex(ValueError,'selection must be reviewed'):self.snapshot()

    def test_editorial_publication_selection_is_stable_after_new_article(self):
        self.select_first()
        before=self.snapshot()
        new=deepcopy(self.pubs['items'][0]);new['doi']='10.1234/synthetic-new';new['title']='SYNTHETIC NEW ARTICLE'
        self.pubs['items'].append(new)
        after=self.snapshot()
        self.assertEqual(before['documents']['en']['publications'],after['documents']['en']['publications'])
        self.assertEqual(after['documents']['en']['publication_count'],51)
        self.assertNotEqual(before['source_digest'],after['source_digest'])

    def test_bibliographic_corrections_flow_from_the_same_catalog(self):
        self.select_first()
        self.pubs['items'][0]['year']=2022
        self.pubs['items'][0]['title']='EDITORIALLY CORRECTED TITLE'
        for document in self.snapshot()['documents'].values():
            self.assertEqual(document['publications'][0]['year'],2022)
            self.assertEqual(document['publications'][0]['title'],'EDITORIALLY CORRECTED TITLE')

    def test_confirmed_energy_article_keeps_bibliographic_year(self):
        self.config['selected_publications']=[{'doi':'https://doi.org/10.1016/j.energy.2021.122208'}]
        for document in self.snapshot()['documents'].values():
            self.assertEqual(document['publications'][0]['year'],2022)

    def test_doi_added_to_doi_less_selection_remains_synchronized(self):
        article=next(p for p in self.pubs['items'] if not p.get('doi'))
        self.config['selected_publications']=[{'title':article['title'],'year':article['year']}]
        article['doi']='10.1234/synthetic-doi'
        self.assertEqual(self.snapshot()['documents']['en']['publications'][0]['doi'],article['doi'])

    def test_missing_ambiguous_and_duplicate_references_fail_closed(self):
        self.config['selected_publications']=[{'doi':'10.1234/absent'}]
        with self.assertRaisesRegex(ValueError,'missing or ambiguous'):self.snapshot()
        self.select_first();self.pubs['items'].append(deepcopy(self.pubs['items'][0]))
        with self.assertRaisesRegex(ValueError,'missing or ambiguous'):self.snapshot()
        self.pubs['items'].pop();self.config['selected_publications']*=2
        with self.assertRaisesRegex(ValueError,'duplicate'):self.snapshot()

    def test_private_fields_and_unapproved_records_never_enter_cv(self):
        self.select_first()
        self.profile['private_note']='PRIVATE_SENTINEL'
        self.pubs['items'][0]['private_note']='PRIVATE_SENTINEL'
        pending=deepcopy(self.supervisions['items'][0]);pending['approved']=False;pending['student']='PRIVATE_SENTINEL'
        self.supervisions['items'].append(pending)
        self.assertNotIn('PRIVATE_SENTINEL',json.dumps(self.snapshot()))
        self.assertNotIn(self.supervisions['items'][0]['student'],json.dumps(self.snapshot()))

    def test_approved_build_generates_four_documents_and_link_without_xml(self):
        self.select_first();self.config['status']='approved'
        original_load=builder.load
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(builder,'DIST',Path(directory)/'dist'),patch.object(builder,'load',side_effect=lambda name:self.config if name=='cv.json' else original_load(name)):
                builder.build()
                self.assertIn('data-short-cv',(builder.DIST/'index.html').read_text('utf-8'))
                for lang in ('en','pt','fr','zh'):
                    text=(builder.DIST/'cv'/f'{lang}.html').read_text('utf-8')
                    self.assertIn('window.print()',text)
                    self.assertIn(self.pubs['items'][0]['title'],text)
                    self.assertNotIn('PRIVATE_SENTINEL',text)

    def test_preview_is_localized_and_escapes_catalog_text(self):
        self.select_first();self.pubs['items'][0]['title']='<script>unsafe</script>'
        snapshot=self.snapshot()
        with tempfile.TemporaryDirectory() as directory:
            files=builder.CV.write_documents(snapshot,directory,preview=True,built_on='2026-11-15')
            self.assertEqual(len(files),4)
            text=(Path(directory)/'pt.html').read_text('utf-8')
            self.assertIn('Prévia editorial',text)
            self.assertIn('&lt;script&gt;unsafe&lt;/script&gt;',text)
            self.assertNotIn('<script>unsafe',text)


if __name__=='__main__':unittest.main()
