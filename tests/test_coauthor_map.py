import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class CoauthorMapTests(unittest.TestCase):
    def setUp(self):
        self.records=json.loads((ROOT/'content/collaborations.json').read_text(encoding='utf-8'))
        self.by_id={r['id']:r for r in self.records}

    def test_approved_country_selection_and_exclusions(self):
        self.assertEqual({r['country'] for r in self.records},{'BRA','FRA','PRT','TWN','FIN'})
        names=' '.join(r['institution'] for r in self.records).casefold()
        for excluded in ('milho e sorgo','censipam','science inovatech','unicamp','esalq','uberlândia'):
            self.assertNotIn(excluded,names)

    def test_coauthorship_has_catalog_evidence_without_claiming_active_partnership(self):
        pubs=json.loads((ROOT/'content/publications.json').read_text(encoding='utf-8'))['items']
        evidence={('https://doi.org/'+p['doi'],p['title']) for p in pubs if p.get('doi')}
        for r in self.records:
            if not r.get('publications'): continue
            self.assertEqual((r['scope'],r['status']),('research','documented'))
            self.assertNotIn('institutional_owner',r)
            for p in r['publications']: self.assertIn((p['url'],p['title']),evidence)
            for person in r['people']:
                for lang in ('en','pt','fr','zh'): self.assertTrue(person['role_'+lang])

    def test_existing_historical_links_are_preserved(self):
        for key in ('br-embrapa','fr-cirad'):
            r=self.by_id[key]
            self.assertEqual((r['scope'],r['status']),('institutional','historical'))
            self.assertEqual(r['period'],{'start':2019,'end':2023})
        self.assertEqual(self.by_id['fr-lorraine']['city'],'Nancy')
        self.assertEqual(self.by_id['fr-lorraine-coauthors']['city'],'Épinal')
        self.assertFalse(any(r.get('territory')=='REU' for r in self.records))

    def test_distinct_affiliations_of_same_author_are_retained(self):
        ids=('br-ufla','br-ufra-parauapebas')
        for key in ids:
            self.assertIn('Thiago de Paula Protásio',[p['name'] for p in self.by_id[key]['people']])
        self.assertIn('Luis Alberto Follegatti-Romero',[p['name'] for p in self.by_id['br-usp-poli']['people']])

    def test_brazil_brafitec_preserves_unb_coauthorship(self):
        selected=[r for r in self.records if r.get('program')=='BRAFITEC' and r['country']=='BRA']
        self.assertEqual({r['city'] for r in selected},{'Brasília','Itajubá','Salvador'})
        for r in selected:
            self.assertEqual((r['scope'],r['status']),('institutional','documented'))
        self.assertEqual(self.by_id['br-unb-coauthors']['scope'],'research')
        self.assertEqual(self.by_id['br-brafitec-unb']['institution'],self.by_id['br-unb-coauthors']['institution'])
