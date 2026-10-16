"""Per-app profiles: switch profile when a matching app gets focus."""
import ctypes
import ctypes.wintypes as wt
import threading
import time

from .engine import engine

user32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
STABLE_SECONDS = 2   # focus must stay this long before switching (alt-tab spam = flash writes)


def foreground_exe():
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ''
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return exe_of(pid.value)


def exe_of(pid):
    h = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return ''
    buf = ctypes.create_unicode_buffer(1024)
    n = wt.DWORD(len(buf))
    ok = k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n))
    k32.CloseHandle(h)
    return buf.value.rsplit('\\', 1)[-1].lower() if ok else ''


def window_apps():
    """Exe names of apps that currently have a visible window (for the rule picker)."""
    apps = set()

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd) and user32.GetWindowTextLengthW(hwnd):
            pid = wt.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            exe = exe_of(pid.value)
            if exe and exe not in ('explorer.exe', 'textinputhost.exe', 'applicationframehost.exe'):
                apps.add(exe)
        return True

    user32.EnumWindows(cb, 0)
    return sorted(apps)


def wanted_profile(exe):
    s = engine.settings
    return s['rules'].get(exe) or s['default_profile']


def loop():
    candidate, since = None, 0.0
    while True:
        time.sleep(0.5)
        try:
            if not engine.settings['autoswitch']:
                continue
            want = wanted_profile(foreground_exe())
            if not want or want == engine.active_profile:
                candidate = None
                continue
            if want != candidate:
                candidate, since = want, time.time()
            elif time.time() - since >= STABLE_SECONDS:
                engine.apply_profile(want)
                candidate = None
        except Exception:
            time.sleep(5)  # keyboard unplugged, profile deleted, ... try again later


def start():
    threading.Thread(target=loop, daemon=True, name='autoswitch').start()
