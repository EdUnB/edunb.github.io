"""Synthetic API responses only; no live requests or private CVs in tests."""
from copy import deepcopy
from datetime import date
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
try:
    import scopus_client as client
    import update_sources as update
finally:
    sys.path.pop(0)


class OfficialAPIConnectorTests(unittest.TestCase):
    def response(self,path,params):
        if path.startswith('/content/author/'):
            return {'author-retrieval-response':[{'coredata':{'dc:identifier':'AUTHOR_ID:'+client.AUTHOR_ID,
                'document-count':'3','citation-count':'4','cited-by-count':'3'},'h-index':'1'}]}
        if path=='/content/search/scopus':
            return {'search-results':{'opensearch:totalResults':'3','entry':[
                {'dc:identifier':'SCOPUS_ID:100','prism:coverDate':'2024-05-01'},
                {'dc:identifier':'SCOPUS_ID:101','prism:coverDate':'2025-01-01'},
                {'dc:identifier':'SCOPUS_ID:102','prism:coverDate':'2025-06-01'}]}}
        return {'abstract-citations-response':{
            'citeColumnTotalXML':{'citeCountHeader':{'columnHeading':[{'$':str(y)} for y in (2024,2025,2026)]}},
            'citeInfoMatrix':{'citeInfoMatrixXML':{'citationMatrix':{'citeInfo':[
                {'dc:identifier':'SCOPUS_ID:'+identifier,'pcc':'0','cc':[{'$':str(v)} for v in values]}
                for identifier,values in [('100',[1,0,0]),('101',[0,2,0]),('102',[0,0,1])]]}}}}}

    def test_complete_automatic_collection_without_csv(self):
        calls=[]
        def request(path,params):calls.append(path);return self.response(path,params)
        result=client.fetch_metrics('SYNTHETIC_KEY',request=request,today=date(2026,11,16))
        self.assertEqual(result['documents'],3)
        self.assertEqual(result['citations'],4)
        self.assertEqual(result['annual_series']['documents'],[{'year':2024,'value':1},{'year':2025,'value':2},{'year':2026,'value':0}])
        self.assertEqual(result['annual_series']['citations'],[{'year':2024,'value':1},{'year':2025,'value':2},{'year':2026,'value':1}])
        self.assertEqual(result['collection_method'],'authorized_api')
        self.assertEqual(len(calls),3)
        self.assertNotIn('SYNTHETIC_KEY',json.dumps(result))

    def test_no_credentials_does_not_attempt_network(self):
        with patch.object(client,'json_request') as transport:
            with self.assertRaises(client.ScopusError):client.fetch_metrics('')
            transport.assert_not_called()

    def test_other_author_is_rejected(self):
        def request(path,params):
            data=self.response(path,params)
            if path.startswith('/content/author/'):data['author-retrieval-response'][0]['coredata']['dc:identifier']='AUTHOR_ID:999'
            return data
        with self.assertRaisesRegex(client.ScopusError,'another author'):client.fetch_metrics('test',request=request)

    def test_incomplete_search_is_not_a_partial_update(self):
        def request(path,params):
            data=self.response(path,params)
            if path=='/content/search/scopus':data['search-results']['opensearch:totalResults']='2'
            return data
        with self.assertRaisesRegex(client.ScopusError,'counts differ'):client.fetch_metrics('test',request=request)

    def test_missing_citation_year_is_not_zero(self):
        def request(path,params):
            data=self.response(path,params)
            if path.endswith('/citations'):data['abstract-citations-response']['citeColumnTotalXML']['citeCountHeader']['columnHeading'].pop()
            return data
        with self.assertRaisesRegex(client.ScopusError,'coverage'):client.fetch_metrics('test',request=request,today=date(2026,11,16))

    def test_duplicate_citation_document_is_rejected(self):
        data=self.response('/content/abstract/citations',{})
        rows=data['abstract-citations-response']['citeInfoMatrix']['citeInfoMatrixXML']['citationMatrix']['citeInfo']
        rows.append(deepcopy(rows[0]))
        with self.assertRaisesRegex(client.ScopusError,'mismatch'):client.citation_batch(data,['100','101','102'],[2024,2025,2026])

    def test_aggregate_disagreement_is_not_silently_published(self):
        def request(path,params):
            data=self.response(path,params)
            if path.startswith('/content/author/'):data['author-retrieval-response'][0]['coredata']['citation-count']='5'
            return data
        with self.assertRaisesRegex(client.ScopusError,'differs from profile'):client.fetch_metrics('test',request=request,today=date(2026,11,16))


class UnifiedUpdateTests(unittest.TestCase):
    def setUp(self):
        discovery=patch.object(update,'discover_lattes',return_value=None)
        discovery.start();self.addCleanup(discovery.stop)

    def test_missing_initial_setup_is_reported_and_catalogs_unchanged(self):
        before={p.name:p.read_bytes() for p in (ROOT/'content').glob('*.json')}
        report=update.collect(environ={})
        self.assertEqual(report['sources']['scopus']['status'],'initial_setup_required')
        self.assertEqual(report['sources']['lattes']['status'],'initial_setup_required')
        self.assertEqual(report['proposals'],{})
        for name,content in before.items():self.assertEqual((ROOT/'content'/name).read_bytes(),content)

    def test_access_failure_preserves_snapshot_and_does_not_log_secret(self):
        def fail(*args):raise client.ScopusError('SYNTHETIC_SECRET')
        report=update.collect(environ={'SCOPUS_API_KEY':'SYNTHETIC_SECRET'},fetcher=fail)
        self.assertEqual(report['sources']['scopus']['status'],'access_or_data_review_required')
        self.assertNotIn('SYNTHETIC_SECRET',json.dumps(report))
        self.assertEqual(report['proposals'],{})

    def test_valid_api_proposal_is_staged_not_applied(self):
        candidate=update.build.load('scopus.json');candidate['citations']+=1
        candidate['collection_method']='authorized_api'
        report=update.collect(environ={'SCOPUS_API_KEY':'synthetic'},fetcher=lambda *args:candidate)
        self.assertEqual(report['sources']['scopus']['status'],'changes_ready_for_review')
        self.assertEqual(report['proposals']['scopus']['citations'],candidate['citations'])
        self.assertNotEqual(update.build.load('scopus.json')['citations'],candidate['citations'])

    def test_offline_does_not_claim_a_fresh_consultation(self):
        report=update.collect(offline=True,environ={'SCOPUS_API_KEY':'synthetic'})
        self.assertEqual(report['sources']['scopus']['status'],'not_checked_offline')
        self.assertNotIn('verified_on',report['sources']['scopus'])

    def test_review_output_inside_repository_is_rejected(self):
        with patch('sys.stderr'):
            self.assertEqual(update.main(['--review-dir',str(ROOT/'docs'/'private-update'),'--offline']),1)
        self.assertFalse((ROOT/'docs'/'private-update').exists())


class PrivateSourceDiscoveryTests(unittest.TestCase):
    def test_export_date_takes_priority_over_file_timestamp(self):
        with tempfile.TemporaryDirectory() as directory:
            old=Path(directory)/'older.xml';latest=Path(directory)/'latest.xml'
            latest.write_text('<CURRICULO-VITAE DATA-ATUALIZACAO="16112026"/>',encoding='utf-8')
            old.write_text('<CURRICULO-VITAE DATA-ATUALIZACAO="01112026"/>',encoding='utf-8')
            self.assertEqual(update.discover_lattes(directory),latest)

    def test_private_xml_prepares_all_review_sections_without_removing_catalogs(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'synthetic.xml'
            source.write_text('<CURRICULO-VITAE DATA-ATUALIZACAO="16112026"/>',encoding='utf-8')
            before=update.build.load('supervisions.json')
            report=update.collect(lattes=source,offline=True,environ={})
            self.assertEqual(report['sources']['lattes']['articles_identified'],0)
            self.assertEqual(len(report['proposals']['publications']['items']),50)
            self.assertIn('supervisions',report['proposals'])
            self.assertIn('editorial',report['proposals'])
            self.assertEqual(update.build.load('supervisions.json'),before)

    def test_private_source_inside_public_repository_is_rejected(self):
        report=update.collect(lattes=ROOT/'content'/'not-a-real-xml.xml',offline=True,environ={})
        self.assertEqual(report['sources']['lattes']['status'],'private_location_required')
        self.assertNotIn('publications',report['proposals'])


if __name__=='__main__':unittest.main()
