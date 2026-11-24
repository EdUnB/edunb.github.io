from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest
from xml.etree import ElementTree

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('france_map_build',ROOT/'scripts/build.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)


class FranceMapTests(unittest.TestCase):
    def setUp(self):self.svg=ElementTree.parse(ROOT/'site/assets/france-map.svg').getroot()

    def test_metropolitan_and_reunion_are_separate_views_of_france(self):
        groups=self.svg.findall('.//{http://www.w3.org/2000/svg}g')
        self.assertEqual({g.get('data-territory') for g in groups if g.get('data-territory')},{'MET','REU'})
        self.assertIsNotNone(self.svg.find('.//{http://www.w3.org/2000/svg}g[@id="france-markers"]'))

    def test_projection_places_existing_nancy_and_montpellier_in_mainland(self):
        m=json.loads(self.svg.get('data-main-projection'))
        for lat,lon in [(48.69,6.18),(43.61,3.88)]:
            x=m['x']+(lon-m['west'])*m['cos']*m['scale'];y=m['y']+(m['north']-lat)*m['scale']
            self.assertTrue(25<x<425);self.assertTrue(48<y<398)

    def test_reunion_projection_stays_in_inset(self):
        m=json.loads(self.svg.get('data-reunion-projection'))
        x=m['x']+(55.45-m['west'])*m['cos']*m['scale'];y=m['y']+(m['north']+20.88)*m['scale']
        self.assertTrue(448<x<620);self.assertTrue(253<y<418)

    def test_territory_metadata_cannot_change_country(self):
        record=deepcopy(builder.load('collaborations.json')[0]);record['territory']='REU'
        with self.assertRaisesRegex(ValueError,'territory'):builder.validate_collaboration(record,'synthetic')

    def test_brafitec_is_institutional_and_ensam_is_in_confirmed_bordeaux(self):
        records=[r for r in builder.load('collaborations.json') if r.get('program')=='BRAFITEC' and r['country']=='FRA']
        self.assertEqual(len(records),3)
        for r in records:
            self.assertEqual((r['scope'],r['status'],r['institutional_owner']),('institutional','documented','UnB'))
            builder.validate_collaboration(r,'approved')
        ensam=next(r for r in records if r['id']=='fr-brafitec-ensam')
        self.assertFalse(ensam.get('location_pending',False))
        self.assertEqual(ensam['city'],'Bordeaux')
        self.assertAlmostEqual(ensam['lat'],44.84)
        self.assertAlmostEqual(ensam['lon'],-0.58)
        self.assertEqual({r['city'] for r in records},{'Nancy','Nevers','Bordeaux'})

    def test_pending_campus_rejects_fabricated_coordinates(self):
        record=deepcopy(builder.load('collaborations.json')[0])
        record.update(location_pending=True,lat=None,lon=None,city='campus-pending')
        for fields in ({'lat':48.8,'lon':2.3},{'city':'Paris'},{'location_pending':False}):
            with self.subTest(fields=fields),self.assertRaises(ValueError):
                builder.validate_collaboration({**record,**fields},'invalid')

    def test_brafitec_label_cannot_reclassify_coauthorship(self):
        record=deepcopy(builder.load('collaborations.json')[0]);record['program']='BRAFITEC'
        with self.assertRaises(ValueError):builder.validate_collaboration(record,'invalid')


if __name__=='__main__':unittest.main()
