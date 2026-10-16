"""Physical layout of the GAM-075 (60%, Swiss-German ISO).

idx  = position in the keyboard's 144-slot matrix (same index for the lighting
       table and the key-remap table). The matrix is 18 columns wide; a few keys
       (Backspace, $, <, Menu, RCtrl, Fn) sit outside the normal grid.
       Found with colour-coded calibration photos on 2026-10-08.
hid  = HID usage the key sends by default (positional, so QWERTZ Z = HID 'Y').
x/y/w/h in key units.
"""

# (label, idx, x, y, w, h, hid)
KEYS = [
    ('Esc', 19, 0, 0, 1, 1, 0x29),
    ('1', 20, 1, 0, 1, 1, 0x1E), ('2', 21, 2, 0, 1, 1, 0x1F), ('3', 22, 3, 0, 1, 1, 0x20),
    ('4', 23, 4, 0, 1, 1, 0x21), ('5', 24, 5, 0, 1, 1, 0x22), ('6', 25, 6, 0, 1, 1, 0x23),
    ('7', 26, 7, 0, 1, 1, 0x24), ('8', 27, 8, 0, 1, 1, 0x25), ('9', 28, 9, 0, 1, 1, 0x26),
    ('0', 29, 10, 0, 1, 1, 0x27), ("'", 30, 11, 0, 1, 1, 0x2D), ('^', 31, 12, 0, 1, 1, 0x2E),
    ('Backspace', 103, 13, 0, 2, 1, 0x2A),

    ('Tab', 37, 0, 1, 1.5, 1, 0x2B),
    ('Q', 38, 1.5, 1, 1, 1, 0x14), ('W', 39, 2.5, 1, 1, 1, 0x1A), ('E', 40, 3.5, 1, 1, 1, 0x08),
    ('R', 41, 4.5, 1, 1, 1, 0x15), ('T', 42, 5.5, 1, 1, 1, 0x17), ('Z', 43, 6.5, 1, 1, 1, 0x1C),
    ('U', 44, 7.5, 1, 1, 1, 0x18), ('I', 45, 8.5, 1, 1, 1, 0x0C), ('O', 46, 9.5, 1, 1, 1, 0x12),
    ('P', 47, 10.5, 1, 1, 1, 0x13), ('Ü', 48, 11.5, 1, 1, 1, 0x2F), ('¨', 49, 12.5, 1, 1, 1, 0x30),
    ('Enter', 85, 13.75, 1, 1.25, 2, 0x28),

    ('Caps', 55, 0, 2, 1.75, 1, 0x39),
    ('A', 56, 1.75, 2, 1, 1, 0x04), ('S', 57, 2.75, 2, 1, 1, 0x16), ('D', 58, 3.75, 2, 1, 1, 0x07),
    ('F', 59, 4.75, 2, 1, 1, 0x09), ('G', 60, 5.75, 2, 1, 1, 0x0A), ('H', 61, 6.75, 2, 1, 1, 0x0B),
    ('J', 62, 7.75, 2, 1, 1, 0x0D), ('K', 63, 8.75, 2, 1, 1, 0x0E), ('L', 64, 9.75, 2, 1, 1, 0x0F),
    ('Ö', 65, 10.75, 2, 1, 1, 0x33), ('Ä', 66, 11.75, 2, 1, 1, 0x34), ('$', 108, 12.75, 2, 1, 1, 0x32),

    ('Shift', 73, 0, 3, 1.25, 1, 0xE1), ('<', 109, 1.25, 3, 1, 1, 0x64),
    ('Y', 74, 2.25, 3, 1, 1, 0x1D), ('X', 75, 3.25, 3, 1, 1, 0x1B), ('C', 76, 4.25, 3, 1, 1, 0x06),
    ('V', 77, 5.25, 3, 1, 1, 0x19), ('B', 78, 6.25, 3, 1, 1, 0x05), ('N', 79, 7.25, 3, 1, 1, 0x11),
    ('M', 80, 8.25, 3, 1, 1, 0x10), (',', 81, 9.25, 3, 1, 1, 0x36), ('.', 82, 10.25, 3, 1, 1, 0x37),
    ('-', 83, 11.25, 3, 1, 1, 0x38), ('Shift', 84, 12.25, 3, 2.75, 1, 0xE5),

    ('Ctrl', 91, 0, 4, 1.25, 1, 0xE0), ('Win', 92, 1.25, 4, 1.25, 1, 0xE3),
    ('Alt', 93, 2.5, 4, 1.25, 1, 0xE2), ('Space', 94, 3.75, 4, 6.25, 1, 0x2C),
    ('AltGr', 95, 10, 4, 1.25, 1, 0xE6), ('Menu', 96, 11.25, 4, 1.25, 1, 0x65),
    ('Ctrl', 97, 12.5, 4, 1.25, 1, 0xE4), ('Fn', 98, 13.75, 4, 1.25, 1, None),
]

# Remap targets: (HID usage, name). Swiss labels where they differ from US.
TARGETS = (
    [(0x04 + i, c) for i, c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWX')]
    + [(0x1D, 'Y (key right of Shift)'), (0x1C, 'Z (key right of T)')]
    + [(0x1E + i, str((i + 1) % 10)) for i in range(10)]
    + [(0x28, 'Enter'), (0x29, 'Esc'), (0x2A, 'Backspace'), (0x2B, 'Tab'), (0x2C, 'Space'),
       (0x2D, "'"), (0x2E, '^'), (0x2F, 'Ü'), (0x30, '¨'), (0x32, '$'), (0x33, 'Ö'), (0x34, 'Ä'),
       (0x35, '§'), (0x36, ','), (0x37, '.'), (0x38, '-'), (0x39, 'Caps Lock'), (0x64, '<')]
    + [(0x3A + i, f'F{i + 1}') for i in range(12)]
    + [(0x68 + i, f'F{i + 13}') for i in range(12)]
    + [(0x46, 'Print Screen'), (0x47, 'Scroll Lock'), (0x48, 'Pause'), (0x49, 'Insert'),
       (0x4A, 'Home'), (0x4B, 'Page Up'), (0x4C, 'Delete'), (0x4D, 'End'), (0x4E, 'Page Down'),
       (0x4F, 'Right'), (0x50, 'Left'), (0x51, 'Down'), (0x52, 'Up'), (0x65, 'Menu'),
       (0xE0, 'Left Ctrl'), (0xE1, 'Left Shift'), (0xE2, 'Left Alt'), (0xE3, 'Left Win'),
       (0xE4, 'Right Ctrl'), (0xE5, 'Right Shift'), (0xE6, 'AltGr'), (0xE7, 'Right Win')]
)

EFFECTS = ['Static', 'Single On', 'Single Off', 'Glittering', 'Falling', 'Colourful', 'Breath',
           'Spectrum', 'Outward', 'Scrolling', 'Rolling', 'Rotating', 'Explode', 'Launch',
           'Ripples', 'Flowing', 'Pulsating', 'Tilt', 'Shuttle']  # ids 1..19; 0x80 = Custom
