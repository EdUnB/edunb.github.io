from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('scopus_test_build',ROOT/'scripts/build.py')
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ScopusMetricsTests(unittest.TestCase):
    def setUp(self):self.data=deepcopy(builder.load('scopus.json'))

    def test_dated_observation_is_separate_from_lattes(self):
        builder.validate_scopus(self.data)
        self.assertEqual(self.data['documents'],87)
        self.assertEqual(self.data['citations'],1243)
        self.assertEqual(self.data['h_index'],22)
        self.assertEqual(self.data['verified_on'],'2026-11-15')
        self.assertIsNone(self.data['annual_series'])
        self.assertEqual(len(builder.load('publications.json')['items']),50)

    def test_identity_and_credentials_are_not_accepted_silently(self):
        self.data['author_id']='123'
        with self.assertRaisesRegex(ValueError,'identity'):builder.validate_scopus(self.data)
        self.setUp();self.data['api_key']='SYNTHETIC_SECRET'
        with self.assertRaisesRegex(ValueError,'fields'):builder.validate_scopus(self.data)

    def test_invalid_counts_and_dates_fail(self):
        for key,value in [('citations',-1),('h_index',True),('documents','87'),('verified_on','not-a-date')]:
            with self.subTest(key=key):
                data=deepcopy(self.data);data[key]=value
                with self.assertRaises(ValueError):builder.validate_scopus(data)

    def test_inconsistent_totals_fail(self):
        self.data['h_index']=88
        with self.assertRaisesRegex(ValueError,'inconsistent'):builder.validate_scopus(self.data)

    def test_verified_series_structure(self):
        self.data['collection_method']='reviewed_export'
        self.data['annual_series']={'documents':[{'year':2020,'value':2}],'citations':[{'year':2020,'value':3}]}
        builder.validate_scopus(self.data)
        self.data['annual_series']['citations'].append({'year':2020,'value':4})
        with self.assertRaisesRegex(ValueError,'duplicate'):builder.validate_scopus(self.data)

    def test_missing_series_is_not_filled_with_zeroes(self):
        self.data['annual_series']={'documents':[],'citations':[]}
        with self.assertRaisesRegex(ValueError,'verified data'):builder.validate_scopus(self.data)


if __name__=='__main__':unittest.main()
