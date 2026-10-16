"""Everything that touches the keyboard goes through here.

Each block write lands in the keyboard's flash memory (a write without the final
commit leaves the board dark after a replug), so:
  - identical blocks are never rewritten,
  - external notifications are rate limited,
  - writes are counted per day (shown in the UI).
"""
import json
import os
import secrets
import threading
import time
from datetime import date
from pathlib import Path

from . import blocks
from .proto import BLK_KEYMAP, BLK_LIGHTING, Keyboard

HERE = Path(__file__).parent
DATA = Path(os.environ.get('APPDATA', Path.home())) / 'gam075'
STATE = DATA / 'state.json'
SETTINGS = DATA / 'settings.json'
PROFILES = DATA / 'profiles'

NOTIFY_MIN_GAP = 20      # seconds between two external notifications
NOTIFY_DAILY_CAP = 60    # each notification = 2 flash writes

DEFAULT_SETTINGS = {
    'autoswitch': False,
    'rules': {},              # 'game.exe' -> profile name
    'default_profile': '',    # used when no rule matches ('' = leave as is)
    'token': '',
    'writes': {'day': '', 'count': 0, 'notifies': 0},
}


def _read(path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def _write(path, obj):
    DATA.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=1), encoding='utf-8')
    tmp.replace(path)


class Engine:
    def __init__(self):
        self.lock = threading.RLock()
        self.last = {}           # block id -> bytes last written this session
        self.active_profile = ''
        self.last_notify = 0.0
        self.notify_timer = None
        s = _read(SETTINGS, {})
        self.settings = {**DEFAULT_SETTINGS, **s}
        if not self.settings['token']:
            self.settings['token'] = secrets.token_urlsafe(18)
            self.save_settings()

    # ---- persistence -------------------------------------------------------
    def state(self):
        s = _read(STATE, None)
        if s is None:
            s = {'lighting': blocks.parse_lighting((HERE / 'initial_lighting.bin').read_bytes()),
                 'remap': {}}
        return s

    def save_settings(self):
        _write(SETTINGS, self.settings)

    def profiles(self):
        PROFILES.mkdir(parents=True, exist_ok=True)
        return sorted(p.stem for p in PROFILES.glob('*.json'))

    def profile(self, name):
        return _read(PROFILES / f'{name}.json', None)

    def save_profile(self, name, state):
        PROFILES.mkdir(parents=True, exist_ok=True)
        _write(PROFILES / f'{name}.json', state)

    def delete_profile(self, name):
        (PROFILES / f'{name}.json').unlink(missing_ok=True)

    # ---- writing -----------------------------------------------------------
    def _count(self, n=1, notify=False):
        w = self.settings['writes']
        today = date.today().isoformat()
        if w['day'] != today:
            w.update(day=today, count=0, notifies=0)
        w['count'] += n
        if notify:
            w['notifies'] += 1
        self.save_settings()

    def _write_blocks(self, state, what=('lighting', 'remap')):
        todo = []
        if 'lighting' in what:
            todo.append((BLK_LIGHTING, blocks.build_lighting(state['lighting'])))
        if 'remap' in what:
            todo.append((BLK_KEYMAP, blocks.build_keymap(state['remap'])))
        todo = [(b, d) for b, d in todo if self.last.get(b) != d]
        if not todo:
            return 0
        with Keyboard() as kb:
            for b, d in todo:
                kb.write_block(b, d)
                self.last[b] = d
        self._count(len(todo))
        return len(todo)

    def apply(self, state, what=('lighting', 'remap'), profile=None):
        """Write state to the keyboard and make it the saved state."""
        with self.lock:
            self._cancel_notify()
            self._write_blocks(state, what)
            _write(STATE, state)
            if profile is not None:
                self.active_profile = profile

    def apply_profile(self, name):
        s = self.profile(name)
        if s is None:
            raise KeyError(f'no profile {name!r}')
        self.apply(s, profile=name)
        return s

    # ---- external notifications -------------------------------------------
    def _cancel_notify(self):
        if self.notify_timer:
            self.notify_timer.cancel()
            self.notify_timer = None

    def notify(self, color='#ff0000', seconds=5, effect='breath'):
        """Light the whole board in one colour for a few seconds, then restore."""
        with self.lock:
            w = self.settings['writes']
            if w['day'] == date.today().isoformat() and w['notifies'] >= NOTIFY_DAILY_CAP:
                return 'daily limit reached'
            if time.time() - self.last_notify < NOTIFY_MIN_GAP:
                return 'too soon'
            self.last_notify = time.time()
            base = self.state()
            tmp = json.loads(json.dumps(base))
            eid = {'static': 1, 'breath': 7}.get(effect, 7)
            m = tmp['lighting']['modes'][str(eid)]
            m.update(color=color, random=False, brightness=16, speed=12)
            tmp['lighting']['effect'] = eid
            self._cancel_notify()
            self._write_blocks(tmp, ('lighting',))
            self._count(0, notify=True)
            seconds = max(2, min(int(seconds), 120))
            self.notify_timer = threading.Timer(seconds, self._restore)
            self.notify_timer.daemon = True
            self.notify_timer.start()
            return 'ok'

    def _restore(self):
        with self.lock:
            self.notify_timer = None
            self._write_blocks(self.state(), ('lighting',))


engine = Engine()
