"""Loopback-only UI. No external assets, telemetry, or cloud requests."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import secrets
import sqlite3
from urllib.parse import parse_qs, urlparse
from memory import LIMIT, Store, profile_name

ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'ui'


def make_server(vault, port=0):
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # No URL or private-data logs.

        def send(self, status, body, mime='application/json; charset=utf-8'):
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            self.end_headers()
            self.wfile.write(body)

        def trusted(self, api=False):
            origin = f'http://127.0.0.1:{self.server.server_port}'
            if self.headers.get('Host') != origin.removeprefix('http://'):
                return False
            if self.headers.get('Sec-Fetch-Site') == 'cross-site':
                return False
            if self.headers.get('Origin') not in (None, origin):
                return False
            return not api or secrets.compare_digest(self.headers.get('X-Memory-Token', ''), token)

        def do_GET(self):
            route = urlparse(self.path)
            api = route.path.startswith('/api/')
            if not self.trusted(api):
                return self.send(403, {'error': 'Local request token/origin required.'})
            if not api:
                names = {'/': ('index.html', 'text/html; charset=utf-8'),
                         '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                         '/style.css': ('style.css', 'text/css; charset=utf-8')}
                if route.path not in names:
                    return self.send(404, {'error': 'Not found.'})
                name, mime = names[route.path]
                data = (ASSETS / name).read_bytes().replace(b'__MEMORY_TOKEN__', token.encode())
                return self.send(200, data, mime)
            query = parse_qs(route.query)
            profile = query.get('profile', ['default'])[0]
            store = None
            try:
                profile_name(profile)
                store = Store(vault)
                if route.path == '/api/records':
                    result = store.list(profile, query.get('q', [''])[0], query.get('topic', [''])[0],
                                        sensitive=query.get('sensitive', ['0'])[0] == '1')
                elif route.path == '/api/profiles':
                    result = sorted(set(['default', profile, *store.profiles()]))
                elif route.path == '/api/doctor':
                    result = store.doctor(profile)
                else:
                    return self.send(404, {'error': 'Not found.'})
                self.send(200, result)
            except (ValueError, OSError) as exc:
                self.send(400, {'error': str(exc)})
            except sqlite3.Error:
                self.send(409, {'error': 'Storage error. Refresh and retry.'})
            finally:
                if store:
                    store.close()

        def do_POST(self):
            if not self.trusted(True):
                return self.send(403, {'error': 'Local request token/origin required.'})
            store = None
            try:
                if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    raise ValueError('JSON requests required.')
                length = int(self.headers.get('Content-Length', '-1'))
                if length < 0 or length > LIMIT:
                    raise ValueError('Request limit: 8 MiB.')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError('Object required.')
                profile = profile_name(data.get('profile', 'default'))
                store = Store(vault)
                route = urlparse(self.path).path
                if route == '/api/add':
                    result = store.add(profile, data['record'])
                elif route == '/api/update':
                    result = store.update(profile, data['id'], data['record'], data['version'])
                elif route == '/api/forget':
                    result = store.forget(profile, data['id'])
                elif route == '/api/history':
                    result = store.history(profile, data['id'])
                elif route == '/api/import':
                    result = store.import_records(profile, data['payload'])
                elif route == '/api/export':
                    result = store.export(profile)
                elif route == '/api/capsule':
                    result = store.capsule(profile, data.get('query', ''), data.get('topics', []),
                                           data.get('sensitive', False), int(data.get('budget', 3000)))
                else:
                    return self.send(404, {'error': 'Not found.'})
                self.send(200, result)
            except (ValueError, OSError, KeyError, TypeError) as exc:
                self.send(400, {'error': str(exc)})
            except Exception:
                self.send(409, {'error': 'Storage conflict or error. Refresh and retry.'})
            finally:
                if store:
                    store.close()

    server = HTTPServer(('127.0.0.1', port), Handler)
    server.timeout = 1
    return server


def serve(vault, port=0, open_browser=False):
    # Validate path/database before exposing the UI.
    store = Store(vault)
    store.close()
    server = make_server(vault, port)
    print(f'Personal Memory: http://127.0.0.1:{server.server_port}', flush=True)
    print('Local-only UI; plaintext storage. Ctrl+C stops the server.', flush=True)
    if open_browser:
        import webbrowser
        webbrowser.open(f'http://127.0.0.1:{server.server_port}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
