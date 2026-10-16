"""System tray icon: open the app, switch profiles, toggle auto-switch, quit."""
import os
import webbrowser

import pystray
from PIL import Image

from . import server
from .engine import engine


def _profile_items():
    def make(name):
        return pystray.MenuItem(name, lambda: engine.apply_profile(name),
                                checked=lambda _: engine.active_profile == name, radio=True)
    names = engine.profiles()
    return [make(n) for n in names] or [pystray.MenuItem('No profiles yet', None, enabled=False)]


def _toggle_auto(icon, _):
    engine.settings['autoswitch'] = not engine.settings['autoswitch']
    engine.save_settings()


def run(open_browser=False):
    if server.serve(open_browser) is None:
        return  # another copy owns the port and already opened the page
    icon = pystray.Icon(
        'gam075',
        Image.open(os.path.join(os.path.dirname(__file__), 'icon.ico')),
        'GAM-075 Control',
        pystray.Menu(
            pystray.MenuItem('Open', lambda: webbrowser.open(server.URL), default=True),
            pystray.MenuItem('Profiles', pystray.Menu(_profile_items)),
            pystray.MenuItem('Auto-switch per app', _toggle_auto,
                             checked=lambda _: engine.settings['autoswitch']),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Quit', lambda icon: icon.stop()),
        ),
    )
    icon.run()
