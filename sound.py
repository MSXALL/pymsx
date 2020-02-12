# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import math
import pyaudio
import struct
import sys
import threading
import time

class sound():
    def __init__(self, debug):
        self.debug = debug

        self.ri = 0
        self.regs = [ 0 ] * 16

        self.sr = 44100
        self.phase1 = self.phase2 = self.phase3 = 0
        self.l1 = self.l2 = self.l3 = 0
        self.p1a = self.p2a = self.p3a = 0

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.p.get_format_from_width(2, unsigned=False), channels=1, rate=self.sr, output=True, stream_callback=self.callback)

        super(sound, self).__init__()

    def callback(self, in_data, frame_count, time_info, status):
        out = bytes()

        for i in range(0, frame_count):
            s = math.sin(self.phase1) * self.l1 + math.sin(self.phase2) * self.l2 + math.sin(self.phase3) * self.l3
            word = int(s / 3.0 * 32767)

            out += struct.pack('<h', word)

            self.phase1 += self.p1a
            self.phase2 += self.p2a
            self.phase3 += self.p3a

        return (out, pyaudio.paContinue)

    def read_io(self, a):
        return self.regs[self.ri]

    def write_io(self, a, v):
        if a == 0xa0:
            self.ri = v & 15

        elif a == 0xa1:
            self.regs[self.ri] = v
            self.debug('Sound %02x: %02x (%d)' % (self.ri, v, v))

            if self.ri == 8 and (v & 15) == 0:
                self.phase1 = 0
            elif self.ri == 9 and (v & 15) == 0:
                self.phase2 = 0
            elif self.ri == 10 and (v & 15) == 0:
                self.phase3 = 0

            base_freq = 3579545 / 16.0

            f1 = f2 = f3 = 0

            fi1 = self.regs[0] + ((self.regs[1] & 15) << 8)
            if fi1:
                f1 = base_freq / fi1
            self.p1a = 2.0 * math.pi * f1 / self.sr

            fi2 = self.regs[2] + ((self.regs[3] & 15) << 8)
            if fi2:
                f2 = base_freq / fi2
            self.p2a = 2.0 * math.pi * f2 / self.sr

            fi3 = self.regs[4] + ((self.regs[5] & 15) << 8)
            if fi3:
                f3 = base_freq / fi3
            self.p3a = 2.0 * math.pi * f3 / self.sr

            self.l1 = 1.0 if self.regs[8] & 16 else (self.regs[8] & 15) / 15.0
            self.l2 = 1.0 if self.regs[9] & 16 else (self.regs[9] & 15) / 15.0
            self.l3 = 1.0 if self.regs[10] & 16 else (self.regs[10] & 15) / 15.0

    def stop(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
