# Copyright 2014 Dirk Pranke. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from typ import json_results


class FakeArtifacts(object):
    def __init__(self):
        self.files = {}


class TestMakeUploadRequest(unittest.TestCase):
    maxDiff = 4096

    def test_basic_upload(self):
        results = json_results.ResultSet()
        full_results = json_results.make_full_results({}, 0, [], results)
        url, content_type, data = json_results.make_upload_request(
            'localhost', 'fake_builder_name', 'fake_master', 'fake_test_type',
            full_results)

        self.assertEqual(
            content_type,
            'multipart/form-data; '
            'boundary=-J-S-O-N-R-E-S-U-L-T-S---B-O-U-N-D-A-R-Y-')

        self.assertEqual(url, 'https://localhost/testfile/upload')
        self.assertMultiLineEqual(
            data,
            ('---J-S-O-N-R-E-S-U-L-T-S---B-O-U-N-D-A-R-Y-\r\n'
             'Content-Disposition: form-data; name="builder"\r\n'
             '\r\n'
             'fake_builder_name\r\n'
             '---J-S-O-N-R-E-S-U-L-T-S---B-O-U-N-D-A-R-Y-\r\n'
             'Content-Disposition: form-data; name="master"\r\n'
             '\r\n'
             'fake_master\r\n'
             '---J-S-O-N-R-E-S-U-L-T-S---B-O-U-N-D-A-R-Y-\r\n'
             'Content-Disposition: form-data; name="testtype"\r\n'
             '\r\n'
             'fake_test_type\r\n'
             '---J-S-O-N-R-E-S-U-L-T-S---B-O-U-N-D-A-R-Y-\r\n'
             'Content-Disposition: form-data; name="file"; '
             'filename="full_results.json"\r\n'
             'Content-Type: application/json\r\n'
             '\r\n'
             '{"version": 3, "interrupted": false, "path_delimiter": ".", '
             '"seconds_since_epoch": 0, '
             '"num_failures_by_type": {"FAIL": 0, "PASS": 0, "SKIP": 0}, '
             '"num_regressions": 0, '
             '"tests": {}}\r\n'
             '---J-S-O-N-R-E-S-U-L-T-S---B-O-U-N-D-A-R-Y---\r\n'))


class TestMakeFullResults(unittest.TestCase):
    maxDiff = 2048

    def test_basic(self):
        test_names = ['foo_test.FooTest.test_fail',
                      'foo_test.FooTest.test_pass',
                      'foo_test.FooTest.test_skip']

        result_set = json_results.ResultSet()
        result_set.add(
            json_results.Result('foo_test.FooTest.test_fail',
                                json_results.ResultType.Failure, 0, 0.1, 0,
                                unexpected=True))
        result_set.add(json_results.Result('foo_test.FooTest.test_pass',
                                           json_results.ResultType.Pass,
                                           0, 0.2, 0))
        result_set.add(json_results.Result('foo_test.FooTest.test_skip',
                                           json_results.ResultType.Skip,
                                           0, 0.3, 0, 
                                           expected=[json_results.ResultType.Skip],
                                           unexpected=False))

        full_results = json_results.make_full_results(
            {'foo': 'bar'}, 0, test_names, result_set)
        expected_full_results = {
            'foo': 'bar',
            'metadata': {
                'foo': 'bar'},
            'interrupted': False,
            'num_failures_by_type': {
                'FAIL': 1,
                'PASS': 1,
                'SKIP': 1},
            'num_regressions': 1,
            'path_delimiter': '.',
            'seconds_since_epoch': 0,
            'tests': {
                'foo_test': {
                    'FooTest': {
                        'test_fail': {
                            'expected': 'PASS',
                            'actual': 'FAIL',
                            'times': [0.1],
                            'is_unexpected': True,
                            'is_regression': True,
                        },
                        'test_pass': {
                            'expected': 'PASS',
                            'actual': 'PASS',
                            'times': [0.2],
                        },
                        'test_skip': {
                            'expected': 'SKIP',
                            'actual': 'SKIP',
                            'times': [0.3],
                        }}}},
            'version': 3}
        self.assertEqual(full_results, expected_full_results)

    def test_artifacts_and_types_added(self):
        ar = FakeArtifacts()
        ar.files = {'artifact_name': 'a/b/c.txt'}

        test_names = [ 'foo_test.FooTest.foobar' ]

        result_set = json_results.ResultSet()
        result_set.add(json_results.Result(
                'foo_test.FooTest.foobar', json_results.ResultType.Pass,
                0, 0.2, 0, artifacts=ar))

        full_results = json_results.make_full_results(
                {'foo': 'bar'}, 0, test_names, result_set)

        tests = full_results['tests']['foo_test']['FooTest']
        self.assertIn('artifacts', tests['foobar'])
        self.assertEqual(tests['foobar']['artifacts'],
                         {'artifact_name': ['a/b/c.txt']})

    def test_artifacts_merged(self):
        test_names = [ 'foo_test.FooTest.foobar' ]
        result_set = json_results.ResultSet()

        ar = FakeArtifacts()
        ar.files = {'artifact_name': 'a/b/c.txt'}
        result_set.add(json_results.Result(
                'foo_test.FooTest.foobar', json_results.ResultType.Failure,
                0, 0.2, 0, artifacts=ar))

        ar2 = FakeArtifacts()
        ar2.files = {'artifact_name': 'd/e/f.txt'}
        result_set.add(json_results.Result(
                'foo_test.FooTest.foobar', json_results.ResultType.Failure,
                0, 0.2, 0, artifacts=ar2))

        full_results = json_results.make_full_results(
                {'foo': 'bar'}, 0, test_names, result_set)

        tests = full_results['tests']['foo_test']['FooTest']
        self.assertIn('artifacts', tests['foobar'])
        # Order is not guaranteed for the list of paths, so don't use
        # assertEqual if there are multiple entries
        artifacts = tests['foobar']['artifacts']
        self.assertIn('artifact_name', artifacts)
        self.assertEqual(len(artifacts['artifact_name']), 2)
        self.assertIn('a/b/c.txt', artifacts['artifact_name'])
        self.assertIn('d/e/f.txt', artifacts['artifact_name'])
