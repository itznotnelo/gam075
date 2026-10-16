"""Convert between the app's settings (plain dict) and the keyboard's raw blocks.

Lighting block (0x13, 1152 bytes):
    0..303     19 effect records of 16 bytes (effect ids 1..19)
    304..319   record for effect 0x80 (Custom / per-key)
    512..1087  144 per-key colours, 4 bytes each: 80 RR GG BB
    1088..1103 copy of the active effect's record (this is what selects the effect)
  record: id RR GG BB 00 00 00 00 random brightness speed direction 00 00 aa 55
          brightness and speed run 1..16 (the Deltaco app's level + 1)

Keymap block (0x11, 640 bytes): 160 x 4 bytes, last two bytes aa 55.
  entry: 00 00 00 00 = default, 02 00 HID 00 = send that key instead.
"""

LIGHT_LEN = 1152
KEYMAP_LEN = 640
CUSTOM = 0x80


def _hex(r, g, b):
    return '#%02x%02x%02x' % (r, g, b)


def _rgb(h):
    h = h.lstrip('#')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _record(eid, m):
    r, g, b = _rgb(m['color'])
    return bytes([eid, r, g, b, 0, 0, 0, 0, 1 if m['random'] else 0,
                  m['brightness'], m['speed'], m['direction'], 0, 0, 0xAA, 0x55])


def _parse_record(rec):
    return {'color': _hex(*rec[1:4]), 'random': bool(rec[8]), 'brightness': rec[9],
            'speed': rec[10], 'direction': rec[11]}


def parse_lighting(d: bytes) -> dict:
    modes = {str(d[i * 16]): _parse_record(d[i * 16:i * 16 + 16]) for i in range(19)}
    custom = _parse_record(d[304:320])
    if custom['brightness'] == 0:
        custom['brightness'] = 16
    return {
        'effect': d[1088],
        'modes': modes,
        'custom_brightness': custom['brightness'],
        'keys': {str(i): _hex(*d[512 + i * 4 + 1:512 + i * 4 + 4]) for i in range(144)},
    }


def build_lighting(s: dict) -> bytes:
    d = bytearray(LIGHT_LEN)
    for eid in range(1, 20):
        d[(eid - 1) * 16:eid * 16] = _record(eid, s['modes'][str(eid)])
    custom = {'color': '#000000', 'random': False, 'brightness': s['custom_brightness'],
              'speed': 0, 'direction': 0}
    d[304:320] = _record(CUSTOM, custom)
    for i in range(144):
        o = 512 + i * 4
        d[o:o + 4] = bytes([0x80, *_rgb(s['keys'].get(str(i), '#000000'))])
    eff = s['effect']
    d[1088:1104] = d[304:320] if eff == CUSTOM else d[(eff - 1) * 16:eff * 16]
    return bytes(d)


def parse_keymap(d: bytes) -> dict:
    out = {}
    for i in range(159):
        e = d[i * 4:i * 4 + 4]
        if e[0] == 0x02:
            out[str(i)] = e[2]
    return out


def build_keymap(remap: dict) -> bytes:
    d = bytearray(KEYMAP_LEN)
    for idx, hid in remap.items():
        i = int(idx)
        if hid and 0 <= i < 159:
            d[i * 4:i * 4 + 4] = bytes([0x02, 0, hid, 0])
    d[-2:] = b'\xaa\x55'
    return bytes(d)
