"""Low-level protocol for the Deltaco GAM-075 (Sonix chip, USB 05AC:0256).

Everything goes through 64-byte HID feature reports on interface 0.
Commands start with 0x04 <cmd>; the keyboard answers with 04 <cmd> 00 01 (01 = ok).

Write flow (same as the Deltaco app):
    04 18          -> ready check
    04 ab + 64 random bytes + 04 02 -> unlock handshake (see unlock())
    04 <blk> .. n  -> start block write, n = number of 64-byte data packets (byte 8)
    n data packets
    04 02          -> keyboard returns 16-bit sum of the data it received (bytes 4-5)
    04 f0          -> commit
"""
import os
import time
import hid

VID, PID = 0x05AC, 0x0256
PKT = 64

BLK_KEYMAP = 0x11   # 10 packets: 160 x 4-byte key entries
BLK_LIGHTING = 0x13  # 18 packets: 19 effect slots + per-key colour table + active slot
BLK_MACROS = 0x15   # 9 packets
BLK_PROFILE = 0x17


def unlock_answer(p: bytes) -> int:
    """What a genuine GAM-075 replies to the unlock challenge (from GamingKeyboardWriter.dll)."""
    a = (p[12] + p[3]) & 0xFF
    b = (p[63] * 8) & 0xFF
    c = (p[6] - p[13]) & 0xFF
    d = p[36] & 0xA5
    return ((a << 24) | (b << 16) | (c << 8) | d) ^ 0x54711688


class ProtocolError(Exception):
    pass


class Keyboard:
    def __init__(self):
        devs = [d for d in hid.enumerate(VID, PID) if d['interface_number'] == 0]
        if not devs:
            raise ProtocolError('GAM-075 not found (05AC:0256 interface 0)')
        self.dev = hid.device()
        self.dev.open_path(devs[0]['path'])

    def close(self):
        self.dev.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def _send(self, data: bytes):
        buf = bytes(data) + bytes(PKT - len(data))
        self.dev.send_feature_report(b'\x00' + buf)  # report id 0

    def _recv(self) -> bytes:
        r = bytes(self.dev.get_feature_report(0, PKT + 1))
        return r[1:] if len(r) == PKT + 1 else r

    def cmd(self, c: int, *args, expect_reply=True) -> bytes:
        self._send(bytes([0x04, c]) + bytes(args))
        if not expect_reply:
            return b''
        # Reply byte 3: 01 = ok, 00 = busy (e.g. still hashing the unlock packet), ff = error.
        # The app retries the same command up to 5 times, so do the same.
        for attempt in range(10):
            time.sleep(0.02 + 0.03 * attempt)
            r = self._recv()
            if r[0] != 0x04 or r[1] != c:
                raise ProtocolError(f'unexpected reply to 04 {c:02x}: {r[:8].hex(" ")}')
            if r[3] == 0x01:
                return r
            if r[3] == 0xFF:
                break
            self._send(bytes([0x04, c]) + bytes(args))
        raise ProtocolError(f'keyboard refused 04 {c:02x}: {r[:8].hex(" ")}')

    def unlock(self):
        """Handshake the app does before every write: 04 ab, 64 random bytes, 04 02.
        The keyboard answers with a 4-byte hash the app uses to check it is a genuine
        board (see unlock_answer); the keyboard does not check us."""
        self.cmd(0xAB)
        challenge = os.urandom(PKT)
        self._send(challenge)
        time.sleep(0.05)
        r = self.cmd(0x02)
        return int.from_bytes(r[4:8], 'little') == unlock_answer(challenge)

    def read_block(self, blk: int, n: int) -> bytes:
        start = [0] * 14
        start[6] = n
        self.cmd(blk, *start)
        data = b''.join(self._recv() for _ in range(n))
        self.cmd(0x02)
        return data

    def info(self) -> bytes:
        """04 05: device info (VID/PID/firmware)."""
        return self.read_block(0x05, 2)

    def write_block(self, blk: int, data: bytes):
        if len(data) % PKT:
            raise ValueError('block data must be a multiple of 64 bytes')
        n = len(data) // PKT
        # If this sequence breaks halfway the keyboard stays busy for ~16 s, then resets itself.
        self.cmd(0x18)
        self.unlock()
        start = [0] * 14
        start[6] = n  # byte 8 of the packet
        self.cmd(blk, *start)
        for i in range(n):
            self._send(data[i * PKT:(i + 1) * PKT])
            time.sleep(0.002)
        r = self.cmd(0x02)
        got = r[4] | (r[5] << 8)
        want = sum(data) & 0xFFFF
        self.cmd(0xF0, expect_reply=False)
        if got != want:
            raise ProtocolError(f'checksum mismatch: keyboard {got:04x}, expected {want:04x}')
        return got
