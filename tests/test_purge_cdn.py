import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location(
    'purge_cdn', pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'purge_cdn.py')
purge_cdn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(purge_cdn)


class CompletedTest(unittest.TestCase):
    def test_current_response_finished(self):
        result = {'id': 'x', 'status': 'finished', 'paths': {
            '/gh/o/r@main/rules/ai.yaml': {'throttled': False, 'providers': {'CF': True, 'FY': True}}}}
        self.assertTrue(purge_cdn.completed(result))

    def test_current_response_rejects_pending_throttled_or_failed_provider(self):
        path = '/gh/o/r@main/rules/ai.yaml'
        self.assertFalse(purge_cdn.completed({'status': 'pending', 'paths': {}}))
        self.assertFalse(purge_cdn.completed({'status': 'finished', 'paths': {
            path: {'throttled': True, 'providers': {'CF': True}}}}))
        self.assertFalse(purge_cdn.completed({'status': 'finished', 'paths': {
            path: {'throttled': False, 'providers': {'CF': True, 'FY': False}}}}))
        self.assertFalse(purge_cdn.completed({'status': 'finished', 'paths': {}}))

    def test_legacy_response(self):
        self.assertTrue(purge_cdn.completed({'success': True}))
        self.assertFalse(purge_cdn.completed({'success': False}))


if __name__ == '__main__':
    unittest.main()
