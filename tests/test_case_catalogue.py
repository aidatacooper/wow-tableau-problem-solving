import copy
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import yaml
from scripts import case_catalogue as catalog
from scripts import prepare_case
from scripts import validate_iteration


class CaseCatalogueTests(unittest.TestCase):
    def test_posix_artifact_paths_work_on_windows_and_reject_backslashes(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / 'outputs').mkdir()
            artifact = root / 'outputs' / 'replica.twbx'
            artifact.write_bytes(b'fixture')
            self.assertEqual(catalog.relative_file(root, 'outputs/replica.twbx'), artifact)
            with self.assertRaisesRegex(AssertionError, 'Unsafe'):
                catalog.relative_file(root, r'outputs\replica.twbx')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'iterations').mkdir()
        (self.root / 'usage').mkdir()

    def make_case(self, name='2026-01-01-ww01-example', year=2026):
        directory = self.root / 'iterations' / name
        directory.mkdir()
        (directory / 'outputs').mkdir()
        (directory / catalog.PRIMARY).write_bytes(b'synthetic generated artifact')
        _, week, _ = catalog.folder_identity(name)
        case = {
            'schema_version': '1.1.0', 'iteration_id': name,
            'case_id': catalog.canonical_id(name, year), 'legacy_case_ids': {},
            'article_date': name[:10], 'challenge_year': year,
            'challenge_week': week, 'challenge_date': None,
            'post': f'https://example.test/articles/{name}/',
            'source': {'article': {'url': f'https://example.test/articles/{name}/'},
                       'workbook': {'url': f'https://public.tableau.com/views/{name}/View',
                                    'sha256': hashlib.sha256(name.encode()).hexdigest()}},
            'functional_status': 'replicated', 'visual_status': 'not_evaluated',
            'verification_status': 'historical', 'cwtwb_result': 'pass',
            'cwtwb': {'tested_version': '0.26.0'},
            'artifacts': {'primary_workbook': catalog.PRIMARY,
                          'cloud_author': None, 'cloud_replica': None},
            'artifact_aliases': {}, 'historical_artifacts': [], 'evidence': [],
        }
        self.save(directory, case)
        return directory, case

    def save(self, directory, case):
        (directory / 'case.yaml').write_text(yaml.safe_dump(case, sort_keys=False))

    def write_views(self):
        index = catalog.catalogue(self.root)
        (self.root / 'usage/case-index.json').write_text(json.dumps(index))
        (self.root / 'usage/consumed-cases.json').write_text(json.dumps(catalog.compatibility_view(index)))
        return index

    def test_challenge_year_can_differ_from_article_year(self):
        directory, case = self.make_case(year=2025)
        catalog.validate_identity(directory, case, self.root)
        self.assertEqual(case['case_id'], 'wow-2025-ww01-example')
        self.assertEqual(case['article_date'], '2026-01-01')

    def test_challenge_date_requires_valid_date_and_evidence(self):
        directory, case = self.make_case()
        for value in ('2026-02-30', '2026-1-1'):
            case['challenge_date'] = value
            with self.assertRaisesRegex(AssertionError, 'challenge_date'):
                catalog.validate_identity(directory, case, self.root)
        case['challenge_date'] = '2025-12-30'
        with self.assertRaisesRegex(AssertionError, 'source URL'):
            catalog.validate_identity(directory, case, self.root)
        case['source']['challenge'] = {'url': 'https://www.workout-wednesday.com/example/'}
        case['date_evidence'] = {'challenge_date': 'Official publication date'}
        catalog.validate_identity(directory, case, self.root)
        case['source_workbook_date'] = '2025-12-31'
        with self.assertRaisesRegex(AssertionError, 'retired'):
            catalog.validate_identity(directory, case, self.root)

    def test_challenge_date_matches_official_snapshot(self):
        directory, case = self.make_case()
        case['challenge_date'] = '2025-12-30'
        case['source']['challenge'] = {'url': 'https://www.workout-wednesday.com/example/'}
        case['date_evidence'] = {'challenge_date': 'Official publication date'}
        evidence = self.root / 'docs/protocols/challenge-date-sources.json'
        evidence.parent.mkdir(parents=True)
        evidence.write_text(json.dumps({'challenges': [{'challenge_year': 2026,
            'challenge_week': 1, 'challenge_date': '2025-12-30',
            'url': case['source']['challenge']['url']}]}))
        catalog.validate_identity(directory, case, self.root)
        case['challenge_date'] = '2025-12-31'
        with self.assertRaisesRegex(AssertionError, 'official date evidence'):
            catalog.validate_identity(directory, case, self.root)

    def test_invalid_real_date_and_week_are_rejected(self):
        for name in ['2026-02-30-ww01-example', '2026-01-01-ww00-example',
                     '2026-01-01-ww54-example', '2026-01-01-ww1-example',
                     '../2026-01-01-ww01-example']:
            with self.subTest(name=name), self.assertRaises(AssertionError):
                catalog.folder_identity(name)

    def test_stale_iteration_id_and_primary_path_are_rejected(self):
        directory, case = self.make_case()
        broken = copy.deepcopy(case)
        broken['iteration_id'] = 'other'
        with self.assertRaisesRegex(AssertionError, 'iteration_id'):
            catalog.validate_identity(directory, broken, self.root)
        broken = copy.deepcopy(case)
        broken['artifacts']['primary_workbook'] = 'outputs/old-name.twbx'
        with self.assertRaisesRegex(AssertionError, 'Primary workbook'):
            catalog.validate_identity(directory, broken, self.root)

    def test_old_id_collision_across_cases_is_rejected(self):
        first, a = self.make_case()
        second, b = self.make_case('2026-01-02-ww02-second')
        a['legacy_case_ids'] = {'old-id': a['case_id']}
        b['legacy_case_ids'] = {'old-id': b['case_id']}
        with self.assertRaisesRegex(AssertionError, 'ID/alias collision'):
            catalog.validate_unique([(first, a), (second, b)], self.root)

    def test_alias_to_other_case_is_rejected(self):
        directory, case = self.make_case()
        case['legacy_case_ids'] = {'old-id': 'wow-2025-ww01-other'}
        with self.assertRaisesRegex(AssertionError, 'legacy_case_ids'):
            catalog.validate_identity(directory, case, self.root)

    def test_tableau_url_forms_identify_same_original_workbook(self):
        first, a = self.make_case()
        second, b = self.make_case('2026-01-02-ww02-second')
        a['source']['workbook']['url'] = 'https://public.tableau.com/app/profile/author/viz/Original/View'
        b['source']['workbook']['url'] = 'https://public.tableau.com/views/Original/Other?:showVizHome=no'
        with self.assertRaisesRegex(AssertionError, 'Duplicate source'):
            catalog.validate_unique([(first, a), (second, b)], self.root)

    def test_original_hash_duplicate_is_case_insensitive(self):
        first, a = self.make_case()
        second, b = self.make_case('2026-01-02-ww02-second')
        b['source']['workbook']['sha256'] = a['source']['workbook']['sha256'].upper()
        with self.assertRaisesRegex(AssertionError, 'Duplicate source'):
            catalog.validate_unique([(first, a), (second, b)], self.root)

    def test_article_url_and_archived_path_duplicate_are_detected(self):
        first, a = self.make_case()
        second, b = self.make_case('2026-01-02-ww02-second')
        (self.root / 'index.json').write_text(json.dumps({'posts': [
            {'file': 'original.html', 'link': a['source']['article']['url'], 'date': '2026-01-01'}
        ]}))
        b['source']['article'] = {'path': 'posts/original.html'}
        with self.assertRaisesRegex(AssertionError, 'Duplicate source'):
            catalog.validate_unique([(first, a), (second, b)], self.root)

    def test_shared_extracted_data_does_not_duplicate_distinct_originals(self):
        pairs = [self.make_case(), self.make_case('2026-01-02-ww02-second')]
        for directory, case in pairs:
            (directory / 'inputs').mkdir()
            lock = {'source_workbook': {'url': case['source']['workbook']['url'],
                                       'sha256': case['source']['workbook']['sha256']},
                    'extracted_data': [{'file': 'inputs/Superstore.hyper', 'sha256': 'f' * 64}]}
            (directory / 'inputs/source-lock.json').write_text(json.dumps(lock))
        catalog.validate_unique(pairs, self.root)

    def test_catalogue_rejects_omitted_and_stale_cases(self):
        self.make_case()
        index = self.write_views()
        self.assertEqual(catalog.check_catalogue(self.root), index)
        self.make_case('2026-01-02-ww02-second')
        with self.assertRaisesRegex(AssertionError, 'differs from source metadata'):
            catalog.check_catalogue(self.root)
        self.write_views()
        path = self.root / 'usage/case-index.json'
        stale = json.loads(path.read_text())
        stale['cases'][0]['visual_status'] = 'matched'
        path.write_text(json.dumps(stale))
        with self.assertRaisesRegex(AssertionError, 'differs from source metadata'):
            catalog.check_catalogue(self.root)

    def test_aliases_do_not_inflate_active_count_and_archive_is_excluded(self):
        directory, case = self.make_case()
        case['legacy_case_ids'] = {'old-one': case['case_id'], 'old-two': case['case_id']}
        self.save(directory, case)
        (self.root / 'iterations/_template').mkdir()
        (self.root / 'archive/pilot').mkdir(parents=True)
        index = self.write_views()
        self.assertEqual(index['active_case_count'], 1)
        self.assertEqual(len(index['legacy_case_ids']), 2)
        self.assertEqual(len(catalog.compatibility_view(index)['consumed_cases']), 1)

    def test_unindexed_malformed_folder_is_not_silently_skipped(self):
        self.make_case()
        (self.root / 'iterations/untracked-pilot').mkdir()
        with self.assertRaisesRegex(AssertionError, 'Invalid iteration folder'):
            catalog.catalogue(self.root)

    def test_missing_primary_and_stale_builder_alias_are_rejected(self):
        directory, case = self.make_case()
        (directory / catalog.PRIMARY).unlink()
        with self.assertRaisesRegex(AssertionError, 'Missing artifact'):
            catalog.validate_identity(directory, case, self.root)
        (directory / catalog.PRIMARY).write_bytes(b'fixture')
        case['artifact_aliases'] = {'outputs/old.twbx': catalog.PRIMARY}
        (directory / 'build_replication.py').write_text("output = 'old.twbx'\n")
        with self.assertRaisesRegex(AssertionError, 'Stale output reference'):
            catalog.validate_identity(directory, case, self.root)

    def test_artifact_cannot_escape_case_directory(self):
        directory, case = self.make_case()
        case['artifacts']['other'] = '../outside.png'
        with self.assertRaisesRegex(AssertionError, 'Unsafe artifact'):
            catalog.validate_identity(directory, case, self.root)


    def test_legacy_contract_is_only_allowed_for_grandfathered_directories(self):
        directory, case = self.make_case()
        case['schema_version'] = 'legacy-summary-1.0'
        with self.assertRaisesRegex(AssertionError, 'grandfathered'):
            catalog.validate_identity(directory, case, self.root)

    def test_legacy_validation_checks_index_but_never_rebuilds(self):
        directory, case = self.make_case('2019-07-18-ww29-high-orders', 2019)
        case['schema_version'] = 'legacy-summary-1.0'
        self.save(directory, case)
        self.write_views()
        with patch.object(validate_iteration, 'LAB_ROOT', self.root), \
                patch.object(validate_iteration, 'run_case_script') as runner, \
                patch.object(validate_iteration, 'validate_source_lock') as source_lock, \
                patch.object(validate_iteration, 'validate_builder_boundary') as boundary:
            validate_iteration.validate_iteration(directory, run_scripts=True)
            runner.assert_not_called()
            source_lock.assert_not_called()
            boundary.assert_not_called()
            (self.root / 'usage/case-index.json').write_text('{}')
            with self.assertRaisesRegex(AssertionError, 'Catalogue differs'):
                validate_iteration.validate_iteration(directory, run_scripts=False)


class PrepareIdentityTests(unittest.TestCase):
    def test_prepare_challenge_date_is_explicit_and_never_comes_from_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / '2026_01_07_Original.twbx'
            with zipfile.ZipFile(source, 'w') as archive:
                archive.writestr('Data/Superstore.hyper', b'synthetic-data')
            arguments = dict(source=source, iteration_id='2026-01-08-ww01-example',
                             case_id=None, post='https://example.test/article',
                             iterations_root=root / 'iterations', challenge_year=2026)
            with self.assertRaisesRegex(ValueError, 'challenge_url'):
                prepare_case.prepare_case(**arguments, challenge_date='2026-01-06')
            with self.assertRaisesRegex(ValueError, 'challenge_date'):
                prepare_case.prepare_case(**arguments, challenge_date='2026-02-30',
                                          challenge_url='https://www.workout-wednesday.com/example/')
            directory = prepare_case.prepare_case(**arguments, challenge_date='2026-01-06',
                          challenge_url='https://www.workout-wednesday.com/example/')
            case = yaml.safe_load((directory / 'case.yaml').read_text())
            self.assertEqual(case['article_date'], '2026-01-08')
            self.assertEqual(case['challenge_date'], '2026-01-06')
            self.assertEqual(case['source']['workbook']['filename'], '2026_01_07_Original.twbx')
            self.assertNotIn('source_workbook_date', case)

    def test_prepare_requires_explicit_year_and_generates_cross_year_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / '2025_12_31_Original.twbx'
            with zipfile.ZipFile(source, 'w') as archive:
                archive.writestr('Data/Superstore.hyper', b'synthetic-data')
            arguments = dict(source=source, iteration_id='2026-01-01-ww53-example',
                             case_id=None, post='https://example.test/article',
                             iterations_root=root / 'iterations')
            with self.assertRaisesRegex(ValueError, 'challenge_year is required'):
                prepare_case.prepare_case(**arguments)
            with self.assertRaisesRegex(ValueError, 'case_id must be'):
                prepare_case.prepare_case(**dict(arguments, case_id='wow-2026-ww53-example'),
                                          challenge_year=2025)
            directory = prepare_case.prepare_case(**arguments, challenge_year=2025)
            case = yaml.safe_load((directory / 'case.yaml').read_text())
            self.assertEqual(case['case_id'], 'wow-2025-ww53-example')
            self.assertEqual(case['article_date'], '2026-01-01')
            self.assertIsNone(case['challenge_date'])
            self.assertNotIn('source_workbook_date', case)
            self.assertNotIn('source_workbook_date', case['date_evidence'])
            self.assertEqual(case['source']['workbook']['filename'], source.name)
            self.assertEqual(case['legacy_case_ids'], {})
            self.assertFalse((directory / source.name).exists())


if __name__ == '__main__':
    unittest.main()
