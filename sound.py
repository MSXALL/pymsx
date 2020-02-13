# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import math
import os
import pyaudio
import pygame.midi
import struct
import sys
import threading
import time

class sound():
    T_AY_3_8910 = 0

    def __init__(self, debug):
        self.debug = debug

        self.ri = 0
        self.regs = [ 0 ] * 16
        self.prev_reg13 = None

        self.sr = 44100

        self.phase1 = self.phase2 = self.phase3 = 0
        self.f1 = self.f2 = self.f3 = 0
        self.l1 = self.l2 = self.l3 = 0

        self.channel_on = [ [ 0, 0 ] ] * 16

        self.pipein, self.pipeout = os.pipe()       
        self.lock = threading.Lock()

        self.pid = self.start_audio()

        super(sound, self).__init__()

    def start_audio(self):
        pid = os.fork()

        if pid == 0:
            try:
                self.p = pyaudio.PyAudio()
                self.stream = self.p.open(format=self.p.get_format_from_width(2, unsigned=False), channels=1, rate=self.sr, output=True, stream_callback=self.callback)

                while True:
                    type_ = struct.unpack('<B', os.read(self.pipein, 1))[0]

                    if type_ == sound.T_AY_3_8910:
                        a = struct.unpack('<B', os.read(self.pipein, 1))[0]
                        if a > 15:
                            self.debug('SOUND: index out of range %d' % a)
                            break

                        v = struct.unpack('<B', os.read(self.pipein, 1))[0]

                        print('SOUND: set reg %d to %d' % (a, v), file=sys.stderr)

                        with self.lock:
                            self.regs[a] = v

                            self.recalc_channels(False)

                    else:
                        assert False

                self.stream.stop_stream()
                self.stream.close()
                self.p.terminate()
            
            except Exception as e:
                print('audio-process failed: %s' % e, file=sys.stderr)

            sys.exit(1)

        pygame.midi.init()

        self.mp = pygame.midi.Output(pygame.midi.get_default_output_id())

        return pid

    def send_midi(self, ch, f, v, upd_instr):
        now = time.time()

        if f == 0:
            n = v = 0
        else:
            n = int(69 + 12 * math.log(f / 440.0))
            v = int(v * 127)

        if v == 0:
            # channel is set to volume 0,
            # stop playing note
            if self.channel_on[ch][1] != 0:
                self.mp.write_short(0x80 + ch, self.channel_on[ch][0], 0)
                #print('%f] %02x %02x %d' % (now, 0x80 + ch, self.channel_on[ch][0], 0), file=sys.stderr)

            self.channel_on[ch] = [ 0, 0 ]
        else:
            # already a note playing?
            if self.channel_on[ch][1] != 0:
                # switch it off
                self.mp.write_short(0x80 + ch, self.channel_on[ch][0], 0)

            if self.channel_on[ch][1] == 0 or upd_instr:
                # make sure we use the correct instrument
                self.mp.set_instrument(81 + (self.regs[13] & 15), channel=ch)

            self.channel_on[ch] = [ n, v ]

            self.mp.write_short(0x90 + ch, n, v)
            #print('%f] %02x %02x %d' % (now, 0x90 + ch, n, v), file=sys.stderr)

    def callback(self, in_data, frame_count, time_info, status):
        with self.lock:
            self.p1a = 2.0 * math.pi * self.f1 / self.sr

            self.p2a = 2.0 * math.pi * self.f2 / self.sr

            self.p3a = 2.0 * math.pi * self.f3 / self.sr

        b = [ 0 ] * frame_count

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

            os.write(self.pipeout, sound.T_AY_3_8910.to_bytes(1, 'big'))
            os.write(self.pipeout, self.ri.to_bytes(1, 'big'))
            os.write(self.pipeout, v.to_bytes(1, 'big'))

            self.recalc_channels(True)

    def recalc_channels(self, midi):
        # base_freq = 3579545 / 16.0
        base_freq = 1789772.5 / 16.0

        self.f1 = self.f2 = self.f3 = 0
        self.l1 = self.l2 = self.l3 = 0

        fi1 = self.regs[0] + ((self.regs[1] & 15) << 8)
        if fi1:
            self.f1 = base_freq / fi1
        fi2 = self.regs[2] + ((self.regs[3] & 15) << 8)
        if fi2:
            self.f2 = base_freq / fi2
        fi3 = self.regs[4] + ((self.regs[5] & 15) << 8)
        if fi3:
            self.f3 = base_freq / fi3

        self.l1 = 1.0 if self.regs[8] & 16 else (self.regs[8] & 15) / 15.0
        self.l2 = 1.0 if self.regs[9] & 16 else (self.regs[9] & 15) / 15.0
        self.l3 = 1.0 if self.regs[10] & 16 else (self.regs[10] & 15) / 15.0

        if self.ri == 8 and self.l1 == 0:
            self.phase1 = 0
        elif self.ri == 9 and self.l2 == 0:
            self.phase2 = 0
        elif self.ri == 10 and self.l3 == 0:
            self.phase3 = 0

        upd_instr = self.prev_reg13 != self.regs[13]
        self.prev_reg13 = self.regs[13]

        if midi:
            self.send_midi(1, self.f1, self.l1, upd_instr)
            self.send_midi(2, self.f2, self.l2, upd_instr)
            self.send_midi(3, self.f3, self.l3, upd_instr)

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
        del self.mp
        pygame.midi.quite()

        os.close(self.pipein)
        os.close(self.pipeout)
        os.kill(-9, self.pid)
