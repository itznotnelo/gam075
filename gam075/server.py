"""Local web app for the GAM-075: python -m gam075  ->  http://localhost:7075

UI + /api/*      : only from this PC (127.0.0.1)
/api/ext/*       : from the LAN (HQ, Home Assistant), needs the token from Settings
"""
import json
import secrets
import threading
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import autostart, layout, watcher
from .engine import DATA, engine

PORT = 7075
URL = f'http://localhost:{PORT}'
HERE = Path(__file__).parent
ThreadingHTTPServer.allow_reuse_address = False  # never let two copies share the port


def log_error():
    """pythonw has no console, so keep a log the owner can send me."""
    DATA.mkdir(parents=True, exist_ok=True)
    with open(DATA / 'error.log', 'a', encoding='utf-8') as f:
        f.write(traceback.format_exc() + '\n')


def public_settings():
    s = dict(engine.settings)
    s['autostart'] = autostart.enabled()
    s['lan_ip'] = lan_ip()
    return s


def lan_ip():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sk:
        try:
            sk.connect(('192.168.1.1', 9))  # no packet is sent; just picks the LAN interface
            return sk.getsockname()[0]
        except OSError:
            return ''


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(n) or b'{}')

    def _local(self):
        return self.client_address[0] in ('127.0.0.1', '::1')

    def _authed(self, q):
        tok = self.headers.get('X-Token') or q.get('token', [''])[0]
        return bool(tok) and secrets.compare_digest(tok, engine.settings['token'])

    def do_GET(self):
        self._handle('GET')

    def do_POST(self):
        self._handle('POST')

    def _handle(self, method):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path.startswith('/api/ext/'):
                if not self._authed(q):
                    return self._json({'ok': False, 'error': 'bad token'}, 403)
                return self._ext(method, u.path[len('/api/ext/'):], q)
            if not self._local():
                return self._json({'ok': False, 'error': 'local only'}, 403)
            if method == 'GET':
                return self._get(u.path)
            return self._post(u.path, self._body())
        except Exception as e:
            log_error()
            self._json({'ok': False, 'error': str(e)}, 500)

    # ---- local UI ------------------------------------------------------------
    def _get(self, path):
        if path in ('/', '/index.html'):
            body = (HERE / 'index.html').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == '/api/state':
            self._json({
                'state': engine.state(),
                'keys': layout.KEYS,
                'targets': layout.TARGETS,
                'effects': layout.EFFECTS,
                'profiles': engine.profiles(),
                'active_profile': engine.active_profile,
                'settings': public_settings(),
                'deltaco': autostart.deltaco_running(),
            })
        elif path == '/api/apps':
            self._json({'apps': watcher.window_apps()})
        else:
            self.send_error(404)

    def _post(self, path, req):
        if path == '/api/apply':
            engine.apply(req['state'], req.get('what', ['lighting', 'remap']))
            self._json({'ok': True})
        elif path == '/api/profile/save':
            engine.save_profile(req['name'], req['state'])
            self._json({'ok': True})
        elif path == '/api/profile/load':
            self._json({'ok': True, 'state': engine.apply_profile(req['name'])})
        elif path == '/api/profile/delete':
            engine.delete_profile(req['name'])
            self._json({'ok': True})
        elif path == '/api/settings':
            for k in ('autoswitch', 'rules', 'default_profile', 'claude'):
                if k in req:
                    engine.settings[k] = req[k]
            if req.get('new_token'):
                engine.settings['token'] = secrets.token_urlsafe(18)
            engine.save_settings()
            if 'autostart' in req:
                autostart.set_enabled(req['autostart'])
            self._json({'ok': True, 'settings': public_settings()})
        elif path == '/api/test-notify':
            self._json({'ok': True, 'result': engine.notify(req.get('color', '#ff0000'), 4)})
        elif path == '/api/claude':
            self._json({'ok': True, 'result': engine.claude(req.get('event', ''))})
        else:
            self.send_error(404)

    # ---- LAN: HQ / Home Assistant -----------------------------------------
    def _ext(self, method, what, q):
        req = self._body() if method == 'POST' else {k: v[0] for k, v in q.items()}
        if what == 'status':
            return self._json({'ok': True, 'profile': engine.active_profile,
                               'profiles': engine.profiles(),
                               'writes_today': engine.settings['writes']})
        if what == 'notify':
            r = engine.notify(req.get('color', '#ff0000'), req.get('seconds', 5),
                              req.get('effect', 'breath'))
            return self._json({'ok': r == 'ok', 'result': r}, 200 if r == 'ok' else 429)
        if what == 'profile':
            engine.apply_profile(req['name'])
            return self._json({'ok': True})
        self.send_error(404)


def serve(open_browser=True):
    try:
        srv = ThreadingHTTPServer(('0.0.0.0', PORT), Handler)
    except OSError:  # already running: just show it
        if open_browser:
            webbrowser.open(URL)
        return None
    watcher.start()
    threading.Thread(target=srv.serve_forever, daemon=True, name='http').start()
    if open_browser:
        webbrowser.open(URL)
    return srv


def main():
    import sys
    args = sys.argv[1:]
    if '--tray' in args:
        from . import tray
        tray.run(open_browser='--no-browser' not in args)
        return
    if serve(open_browser='--no-browser' not in args):
        print(f'GAM-075 control running at {URL}')
        threading.Event().wait()
