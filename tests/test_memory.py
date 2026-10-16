import http.client
import importlib.util
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/personal-memory/scripts'))
from memory import Store, safe_vault, today
from server import make_server


def record(statement='Fictional preference', **fields):
    return dict(statement=statement, topic='preferences', source='Fictional unit-test data',
                kind='user-stated', sensitivity='ordinary', status='active', **fields)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='personal-memory-test-')
        self.vault = Path(self.temp.name) / 'vault'
        self.store = Store(self.vault)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def add(self, text='Fictional preference', **fields):
        data = record(text)
        data.update(fields)
        return self.store.add('default', data)['id']

    def test_empty_vault_contains_no_invented_profile(self):
        self.assertEqual(self.store.list(), [])
        self.assertEqual(self.store.doctor('default')['active'], 0)

    def test_unicode_whitespace_deduplication(self):
        first = self.add('ＡＢＣ   preference')
        result = self.store.add('default', record('abc preference'))
        self.assertTrue(result['duplicate'])
        self.assertEqual(result['id'], first)
        self.assertEqual(len(self.store.list()), 1)

    def test_profiles_separate_search_update_history_and_deletion(self):
        row = self.add('Private in default')
        self.store.add('work', record('Private in work'))
        self.assertEqual(len(self.store.list('work')), 1)
        self.assertNotIn('default', self.store.list('work')[0]['statement'])
        for operation in [lambda: self.store.get('work', row),
                          lambda: self.store.update('work', row, {'statement': 'wrong'}, 1),
                          lambda: self.store.history('work', row), lambda: self.store.forget('work', row)]:
            with self.assertRaises(ValueError):
                operation()
        self.assertEqual(self.store.get('default', row)['version'], 1)

    def test_import_is_pending_and_deduplicated(self):
        data = record('Imported active claim')
        result = self.store.import_records('default', [data, data])
        self.assertFalse(result[0]['duplicate'])
        self.assertTrue(result[1]['duplicate'])
        self.assertEqual(self.store.list()[0]['status'], 'pending')
        self.assertEqual(self.store.capsule('default')['included'], 0)

    def test_invalid_batch_has_no_partial_writes(self):
        with self.assertRaises(ValueError):
            self.store.import_records('default', [record(), {'statement': ''}])
        self.assertEqual(self.store.list(), [])

    def test_tentative_claim_cannot_become_active(self):
        row = self.add(kind='tentative')
        self.assertEqual(self.store.get('default', row)['status'], 'pending')
        result = self.store.update('default', row, {'status': 'active'}, 1)
        self.assertEqual(result['status'], 'pending')

    def test_capsule_filters_pending_expired_sensitive_and_topics(self):
        self.add('Keep this preference')
        self.add('Pending', status='pending')
        self.add('Expired', expires='2000-01-01')
        self.add('Sensitive', sensitivity='sensitive')
        self.add('Education item', topic='education')
        result = self.store.capsule('default', topics=['preferences'])
        self.assertEqual(result['included'], 1)
        self.assertIn('Keep this preference', result['text'])
        for text in ('Pending', 'Expired', 'Sensitive', 'Education item'):
            self.assertNotIn(text, result['text'])

    def test_explicit_sensitive_capsule_opt_in(self):
        self.add('Private detail', sensitivity='sensitive')
        self.assertEqual(self.store.capsule('default')['included'], 0)
        self.assertEqual(self.store.capsule('default', sensitive=True)['included'], 1)

    def test_capsule_budget_does_not_cut_records(self):
        self.add('x' * 300)
        result = self.store.capsule('default', budget=200)
        self.assertEqual(result['included'], 0)
        self.assertEqual(result['omitted'], 1)
        self.assertLessEqual(len(result['text']), 200)

    def test_search_handles_unicode_and_literal_sql(self):
        self.add("我在学习 Python；喜欢清晰的解释。 DROP TABLE memories;")
        self.assertEqual(len(self.store.list(query='python 清晰')), 1)
        self.assertEqual(len(self.store.list(query="' OR 1=1 --")), 0)
        self.assertEqual(len(self.store.list()), 1)

    def test_expiry_today_is_still_valid(self):
        self.add(expires=today())
        self.assertEqual(self.store.capsule('default')['included'], 1)

    def test_conflicting_key_requires_resolution(self):
        self.add('School A', topic='education', key='current-school')
        new = self.store.add('default', {**record('School B'), 'topic': 'education', 'key': 'current-school'})
        self.assertTrue(new['conflict'])
        with self.assertRaises(ValueError):
            self.store.update('default', new['id'], {'status': 'active'}, 1)
        self.assertEqual(self.store.get('default', new['id'])['version'], 1)

    def test_expired_key_does_not_block_new_value(self):
        self.add('Old plan', key='plan', expires='2000-01-01')
        result = self.store.add('default', {**record('New plan'), 'key': 'plan'})
        self.assertFalse(result['conflict'])

    def test_concurrent_edit_rejects_stale_version(self):
        row = self.add()
        other = Store(self.vault)
        try:
            self.store.update('default', row, {'statement': 'Current truth'}, 1)
            with self.assertRaises(ValueError):
                other.update('default', row, {'statement': 'Stale truth'}, 1)
            self.assertEqual(other.get('default', row)['statement'], 'Current truth')
        finally:
            other.close()

    def test_duplicate_update_rolls_back_history(self):
        one = self.add('First')
        self.add('Second')
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.update('default', one, {'statement': 'Second'}, 1)
        self.assertEqual(self.store.history('default', one), [])
        self.assertEqual(self.store.get('default', one)['statement'], 'First')

    def test_forget_deletes_revisions(self):
        row = self.add('Original sensitive description')
        self.store.update('default', row, {'statement': 'Corrected sensitive description'}, 1)
        self.assertEqual(len(self.store.history('default', row)), 1)
        self.store.forget('default', row)
        self.assertEqual(self.store.list(), [])
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM revisions').fetchone()[0], 0)

    def test_export_is_current_profile_without_revisions(self):
        row = self.add('Old')
        self.store.update('default', row, {'statement': 'New'}, 1)
        self.store.add('work', record('Other profile'))
        exported = self.store.export('default')
        self.assertEqual(len(exported['memories']), 1)
        self.assertEqual(exported['memories'][0]['statement'], 'New')
        self.assertNotIn('Old', json.dumps(exported))

    def test_invalid_profiles_dates_and_types_rejected(self):
        for name in ('../escape', '', 'A', 'x' * 33):
            with self.assertRaises(ValueError):
                self.store.add(name, record())
        for patch in ({'expires': '2026-02-30'}, {'expires': '20260101'}, {'statement': 123}):
            with self.assertRaises(ValueError):
                self.store.add('default', {**record(), **patch})

    def test_public_package_and_git_vault_rejected(self):
        with self.assertRaises(ValueError):
            safe_vault(ROOT / 'private')
        (Path(self.temp.name) / '.git').write_text('gitdir: imaginary')
        with self.assertRaises(ValueError):
            safe_vault(Path(self.temp.name) / 'nested/vault')

    def test_legacy_files_reported_without_automatic_migration(self):
        (self.vault / 'education.md').write_text('Old private data', encoding='utf-8')
        self.assertEqual(self.store.doctor('default')['old_markdown'], ['education.md'])
        self.assertEqual(self.store.list(), [])


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='personal-memory-http-')
        self.server = make_server(Path(self.temp.name) / 'vault')
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_port
        self.origin = f'http://127.0.0.1:{self.port}'
        status, html, _ = self.request('GET', '/')
        self.assertEqual(status, 200)
        self.token = re.search(r'name="memory-token" content="([^"]+)"', html).group(1)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        self.temp.cleanup()

    def request(self, method, path, data=None, headers=None):
        client = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        payload = json.dumps(data) if data is not None else None
        all_headers = {'Content-Type': 'application/json'}
        all_headers.update(headers or {})
        client.request(method, path, payload, all_headers)
        response = client.getresponse()
        body = response.read().decode()
        result = response.status, body, dict(response.getheaders())
        client.close()
        return result

    def test_requires_token_and_same_origin(self):
        for headers in ({}, {'X-Memory-Token': 'wrong'},
                        {'X-Memory-Token': self.token, 'Origin': 'https://evil.example'},
                        {'X-Memory-Token': self.token, 'Host': 'evil.example'},
                        {'X-Memory-Token': self.token, 'Sec-Fetch-Site': 'cross-site'}):
            status, _, _ = self.request('POST', '/api/add', {'record': record()}, headers)
            self.assertEqual(status, 403)

    def test_api_get_requires_token(self):
        self.assertEqual(self.request('GET', '/api/records')[0], 403)

    def test_valid_create_read_update_forget(self):
        headers = {'X-Memory-Token': self.token, 'Origin': self.origin}
        status, body, _ = self.request('POST', '/api/add', {'record': record()}, headers)
        self.assertEqual(status, 200)
        record_id = json.loads(body)['id']
        status, body, _ = self.request('GET', '/api/records', headers=headers)
        self.assertEqual(json.loads(body)[0]['id'], record_id)
        self.assertEqual(self.request('POST', '/api/update', {'id': record_id, 'record': {'statement': 'Updated'}, 'version': 1}, headers)[0], 200)
        self.assertEqual(self.request('POST', '/api/forget', {'id': record_id}, headers)[0], 200)
        self.assertEqual(json.loads(self.request('GET', '/api/records', headers=headers)[1]), [])

    def test_no_cache_no_external_script_and_no_directory_traversal(self):
        _, html, headers = self.request('GET', '/')
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])
        self.assertNotIn('src="http', html)
        self.assertEqual(self.request('GET', '/../memory.sqlite3')[0], 404)

    def test_sensitive_records_hidden_from_default_api(self):
        headers = {'X-Memory-Token': self.token}
        self.request('POST', '/api/add', {'record': {**record(), 'sensitivity': 'sensitive'}}, headers)
        self.assertEqual(json.loads(self.request('GET', '/api/records', headers=headers)[1]), [])
        self.assertEqual(len(json.loads(self.request('GET', '/api/records?sensitive=1', headers=headers)[1])), 1)


class InstallerTests(unittest.TestCase):
    def test_install_upgrade_never_copies_vault(self):
        spec = importlib.util.spec_from_file_location('pm_installer', ROOT / 'install.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(prefix='personal-memory-install-') as temp:
            target = Path(temp) / 'skills/personal-memory'
            module.install(target)
            with self.assertRaises(ValueError):
                module.install(target)
            module.install(target, upgrade=True)
            self.assertTrue((target / 'scripts/memory.py').exists())
            self.assertEqual(list(target.rglob('*.sqlite3')), [])


if __name__ == '__main__':
    unittest.main()
