import copy
import unittest

from scripts.capture_case_cloud import apply_state, csv_state


class CloudCaptureScopeTests(unittest.TestCase):
    def test_default_scope_merges_explicit_role_filters_without_mutation(self):
        state = {"parameters": {"Metric": 2}, "filters": {"State": "CA"},
                 "author_filters": {"Source State": "CA"}}
        original = copy.deepcopy(state)
        actual = csv_state(state, "author", {})
        self.assertEqual(actual, {"parameters": {"Metric": 2},
                                 "filters": {"State": "CA", "Source State": "CA"}})
        self.assertEqual(state, original)

    def test_unfiltered_diagnostic_keeps_parameters_and_image_state(self):
        state = {"parameters": {"Metric": 2}, "filters": {"State": "CA"}}
        request = {"author_ignore_state_filters": True}
        self.assertEqual(csv_state(state, "author", request),
                         {"parameters": {"Metric": 2}, "filters": {}})
        self.assertEqual(csv_state(state, "replica", request), state)

        class Options:
            def __init__(self):
                self.filters = {}
                self.parameters = {}

            def parameter(self, key, value):
                self.parameters[key] = value

            def vf(self, key, value):
                self.filters[key] = value

        image = apply_state(Options(), state)
        self.assertEqual(image.filters, {"State": "CA"})
        self.assertEqual(image.parameters, {"Metric": "2"})

    def test_explicit_overrides_remain_and_invalid_flags_fail(self):
        state = {"filters": {"State": "CA"}, "author_filters": {"Country": "US"}}
        self.assertEqual(csv_state(state, "author", {"author_ignore_state_filters": True})["filters"],
                         {"Country": "US"})
        with self.assertRaises(ValueError):
            csv_state(state, "author", {"author_ignore_state_filters": "true"})
