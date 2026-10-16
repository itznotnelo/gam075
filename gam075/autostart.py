"""Windows integration: start with Windows, detect the Deltaco app."""
import ctypes
import ctypes.wintypes as wt
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHONW = ROOT / '.venv' / 'Scripts' / 'pythonw.exe'
STARTUP = Path(os.environ['APPDATA']) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
LINK = STARTUP / 'GAM-075 Control.lnk'


def make_shortcut(path, args):
    """Create a .lnk via the WScript COM object (no pywin32 needed)."""
    import subprocess
    ps = (f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{path}');"
          f"$s.TargetPath='{PYTHONW}';$s.Arguments='{args}';$s.WorkingDirectory='{ROOT}';"
          f"$s.IconLocation='{ROOT / 'gam075' / 'icon.ico'}';$s.Save()")
    subprocess.run(['powershell', '-NoProfile', '-Command', ps], stdin=subprocess.DEVNULL,
                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, check=True)


def enabled():
    return LINK.exists()


def set_enabled(on):
    if on:
        make_shortcut(LINK, '-m gam075 --tray --no-browser')
    else:
        LINK.unlink(missing_ok=True)


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [('dwSize', wt.DWORD), ('cntUsage', wt.DWORD), ('th32ProcessID', wt.DWORD),
                ('th32DefaultHeapID', ctypes.c_size_t), ('th32ModuleID', wt.DWORD),
                ('cntThreads', wt.DWORD), ('th32ParentProcessID', wt.DWORD),
                ('pcPriClassBase', ctypes.c_long), ('dwFlags', wt.DWORD),
                ('szExeFile', ctypes.c_wchar * 260)]


def deltaco_running():
    """Ask Windows directly (no tasklist: subprocess output breaks under pythonw)."""
    k32 = ctypes.windll.kernel32
    snap = k32.CreateToolhelp32Snapshot(0x2, 0)  # TH32CS_SNAPPROCESS
    entry = PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(entry)
    found = False
    ok = k32.Process32FirstW(snap, ctypes.byref(entry))
    while ok:
        if entry.szExeFile.lower() == 'deltaco_gam075.exe':
            found = True
            break
        ok = k32.Process32NextW(snap, ctypes.byref(entry))
    k32.CloseHandle(snap)
    return found
