# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import curses
import math
import sys
import threading
import time

class screen_kb(threading.Thread):
    def __init__(self, io):
        self.ram = [ 0 ] * 16384
        self.vdp_rw_pointer = 0
        self.vdp_addr_state = False
        self.vdp_addr_b1 = None
        self.registers = [ 0 ] * 8
        self.redraw = False
        self.cv = threading.Condition()
        self.stop_flag = False
        self.vdp_read_ahead = 0
        self.io = io

        self.keyboard_queue = []
        self.k_lock = threading.Lock()

        self.debug_msg = None
        self.debug_msg_lock = threading.Lock()

        self.init_kb()
        self.init_screen()

        super(screen_kb, self).__init__()

    def init_kb(self):
        self.kb_last_c = None
        self.kb_char_scanned = self.kb_shift_scanned = False
        self.kb_row_nr = None
        self.kb_row = None
        self.kb_shift = False

    def init_screen(self):
        pass

    def interrupts_enabled(self):
        return (self.registers[0] & 1) == 1

    def interrupt(self):
        self.registers[2] |= 128

    def video_mode(self):
        m1 = (self.registers[1] >> 4) & 1;
        m2 = (self.registers[1] >> 3) & 1;
        m3 = (self.registers[0] >> 1) & 1;

        return (m1 << 2) | (m2 << 1) | m3

    def getch(self, peek):
        c = -1

        self.k_lock.acquire()

        if len(self.keyboard_queue) > 0:
            c = self.keyboard_queue[0]

            if not peek:
                del self.keyboard_queue[0]

        self.k_lock.release()

        return c

    def debug(self, str_):
        self.debug_msg_lock.acquire()
        self.debug_msg = str_
        self.debug_msg_lock.release()

    def stop(self):
        self.stop_flag = True
        self.refresh()
        self.join()
        self.stop2()

    def stop2(self):
        pass

    def refresh(self):
        self.redraw = True

        with self.cv:
            self.cv.notify()

    def set_register(self, a, v):
        self.registers[a] = v

    def write_io(self, a, v):
        if a == 0x98:
            self.ram[self.vdp_rw_pointer] = v
            self.vdp_rw_pointer += 1
            self.vdp_rw_pointer &= 0x3fff
            self.vdp_addr_state = False
            self.refresh()
            self.vdp_read_ahead = v

        elif a == 0x99:
            if self.vdp_addr_state == False:
                self.vdp_addr_b1 = v

            else:
                if (v & 128) == 128:
                    v &= 7
                    self.set_register(v, self.vdp_addr_b1)

                else:
                    self.vdp_rw_pointer = ((v & 63) << 8) + self.vdp_addr_b1

                    if (v & 64) == 0:
                        self.vdp_read_ahead = self.ram[self.vdp_rw_pointer]
                        self.vdp_rw_pointer += 1
                        self.vdp_rw_pointer &= 0x3fff

            self.vdp_addr_state = not self.vdp_addr_state

    def read_io(self, a):
        rc = 0

        if a == 0x98:
            rc = self.vdp_read_ahead
            self.vdp_read_ahead = self.ram[self.vdp_rw_pointer]
            self.vdp_rw_pointer += 1
            self.vdp_rw_pointer &= 0x3fff

        if a == 0x99:
            rc = self.registers[2]
            self.registers[2] &= 127

        if a == 0xa9:
            return self.get_keyboard()

        return rc

    def find_char_row(self, c):
        if c < 0 or c > 255:
            return None

        chars = [ None ] * 256
        chars[ord(')')] = ( 0, (1 << 0) ^ 0xff, True )
        chars[ord('0')] = ( 0, (1 << 0) ^ 0xff, False )
        chars[ord('!')] = ( 0, (1 << 1) ^ 0xff, True )
        chars[ord('1')] = ( 0, (1 << 1) ^ 0xff, False )
        chars[ord('@')] = ( 0, (1 << 2) ^ 0xff, True )
        chars[ord('2')] = ( 0, (1 << 2) ^ 0xff, False )
        chars[ord('#')] = ( 0, (1 << 3) ^ 0xff, True )
        chars[ord('3')] = ( 0, (1 << 3) ^ 0xff, False )
        chars[ord('$')] = ( 0, (1 << 4) ^ 0xff, True )
        chars[ord('4')] = ( 0, (1 << 4) ^ 0xff, False )
        chars[ord('%')] = ( 0, (1 << 5) ^ 0xff, True )
        chars[ord('5')] = ( 0, (1 << 5) ^ 0xff, False )
        chars[ord('^')] = ( 0, (1 << 6) ^ 0xff, True )
        chars[ord('6')] = ( 0, (1 << 6) ^ 0xff, False )
        chars[ord('&')] = ( 0, (1 << 7) ^ 0xff, True )
        chars[ord('7')] = ( 0, (1 << 7) ^ 0xff, False )
        chars[ord('*')] = ( 1, (1 << 0) ^ 0xff, True )
        chars[ord('8')] = ( 1, (1 << 0) ^ 0xff, False )
        chars[ord('(')] = ( 1, (1 << 1) ^ 0xff, True )
        chars[ord('9')] = ( 1, (1 << 1) ^ 0xff, False )
        chars[ord('_')] = ( 1, (1 << 2) ^ 0xff, True )
        chars[ord('-')] = ( 1, (1 << 2) ^ 0xff, False )
        chars[ord('+')] = ( 1, (1 << 3) ^ 0xff, True )
        chars[ord('=')] = ( 1, (1 << 3) ^ 0xff, False )
        chars[ord('|')] = ( 1, (1 << 4) ^ 0xff, True )
        chars[ord('\\')] = ( 1, (1 << 4) ^ 0xff, False )
        chars[ord('{')] = ( 1, (1 << 5) ^ 0xff, True )
        chars[ord('[')] = ( 1, (1 << 5) ^ 0xff, False )
        chars[ord('}')] = ( 1, (1 << 6) ^ 0xff, True )
        chars[ord(']')] = ( 1, (1 << 6) ^ 0xff, False )
        chars[ord(':')] = ( 1, (1 << 7) ^ 0xff, True )
        chars[ord(';')] = ( 1, (1 << 7) ^ 0xff, False )
        chars[ord('"')] = ( 2, (1 << 0) ^ 0xff, True )
        chars[ord("'")] = ( 2, (1 << 0) ^ 0xff, False )
        chars[ord('~')] = ( 2, (1 << 1) ^ 0xff, True )
        chars[ord('`')] = ( 2, (1 << 1) ^ 0xff, False )
        chars[ord('<')] = ( 2, (1 << 2) ^ 0xff, True )
        chars[ord(',')] = ( 2, (1 << 2) ^ 0xff, False )
        chars[ord('>')] = ( 2, (1 << 3) ^ 0xff, True )
        chars[ord('.')] = ( 2, (1 << 3) ^ 0xff, False )
        chars[ord('?')] = ( 2, (1 << 4) ^ 0xff, True )
        chars[ord('/')] = ( 2, (1 << 4) ^ 0xff, False )
        chars[ord('A')] = ( 2, (1 << 6) ^ 0xff, True )
        chars[ord('a')] = ( 2, (1 << 6) ^ 0xff, False )
        chars[ord('B')] = ( 2, (1 << 7) ^ 0xff, True )
        chars[ord('b')] = ( 2, (1 << 7) ^ 0xff, False )
        chars[ord('C')] = ( 3, (1 << 0) ^ 0xff, True )
        chars[ord('c')] = ( 3, (1 << 0) ^ 0xff, False )
        chars[ord('D')] = ( 3, (1 << 1) ^ 0xff, True )
        chars[ord('d')] = ( 3, (1 << 1) ^ 0xff, False )
        chars[ord('E')] = ( 3, (1 << 2) ^ 0xff, True )
        chars[ord('e')] = ( 3, (1 << 2) ^ 0xff, False )
        chars[ord('F')] = ( 3, (1 << 3) ^ 0xff, True )
        chars[ord('f')] = ( 3, (1 << 3) ^ 0xff, False )
        chars[ord('G')] = ( 3, (1 << 4) ^ 0xff, True )
        chars[ord('g')] = ( 3, (1 << 4) ^ 0xff, False )
        chars[ord('H')] = ( 3, (1 << 5) ^ 0xff, True )
        chars[ord('h')] = ( 3, (1 << 5) ^ 0xff, False )
        chars[ord('I')] = ( 3, (1 << 6) ^ 0xff, True )
        chars[ord('i')] = ( 3, (1 << 6) ^ 0xff, False )
        chars[ord('J')] = ( 3, (1 << 7) ^ 0xff, True )
        chars[ord('j')] = ( 3, (1 << 7) ^ 0xff, False )
        chars[ord('K')] = ( 4, (1 << 0) ^ 0xff, True )
        chars[ord('k')] = ( 4, (1 << 0) ^ 0xff, False )
        chars[ord('L')] = ( 4, (1 << 1) ^ 0xff, True )
        chars[ord('l')] = ( 4, (1 << 1) ^ 0xff, False )
        chars[ord('M')] = ( 4, (1 << 2) ^ 0xff, True )
        chars[ord('m')] = ( 4, (1 << 2) ^ 0xff, False )
        chars[ord('N')] = ( 4, (1 << 3) ^ 0xff, True )
        chars[ord('n')] = ( 4, (1 << 3) ^ 0xff, False )
        chars[ord('O')] = ( 4, (1 << 4) ^ 0xff, True )
        chars[ord('o')] = ( 4, (1 << 4) ^ 0xff, False )
        chars[ord('P')] = ( 4, (1 << 5) ^ 0xff, True )
        chars[ord('p')] = ( 4, (1 << 5) ^ 0xff, False )
        chars[ord('Q')] = ( 4, (1 << 6) ^ 0xff, True )
        chars[ord('q')] = ( 4, (1 << 6) ^ 0xff, False )
        chars[ord('R')] = ( 4, (1 << 7) ^ 0xff, True )
        chars[ord('r')] = ( 4, (1 << 7) ^ 0xff, False )
        chars[ord('S')] = ( 5, (1 << 0) ^ 0xff, True )
        chars[ord('s')] = ( 5, (1 << 0) ^ 0xff, False )
        chars[ord('T')] = ( 5, (1 << 1) ^ 0xff, True )
        chars[ord('t')] = ( 5, (1 << 1) ^ 0xff, False )
        chars[ord('U')] = ( 5, (1 << 2) ^ 0xff, True )
        chars[ord('u')] = ( 5, (1 << 2) ^ 0xff, False )
        chars[ord('V')] = ( 5, (1 << 3) ^ 0xff, True )
        chars[ord('v')] = ( 5, (1 << 3) ^ 0xff, False )
        chars[ord('W')] = ( 5, (1 << 4) ^ 0xff, True )
        chars[ord('w')] = ( 5, (1 << 4) ^ 0xff, False )
        chars[ord('X')] = ( 5, (1 << 5) ^ 0xff, True )
        chars[ord('x')] = ( 5, (1 << 5) ^ 0xff, False )
        chars[ord('Y')] = ( 5, (1 << 6) ^ 0xff, True )
        chars[ord('y')] = ( 5, (1 << 6) ^ 0xff, False )
        chars[ord('Z')] = ( 5, (1 << 7) ^ 0xff, True )
        chars[ord('z')] = ( 5, (1 << 7) ^ 0xff, False )
        chars[8       ] = ( 7, (1 << 5) ^ 0xff, False )
        chars[127     ] = ( 7, (1 << 5) ^ 0xff, False )
        chars[10      ] = ( 7, (1 << 7) ^ 0xff, False )
        chars[13      ] = ( 7, (1 << 7) ^ 0xff, False )
        chars[ord(' ')] = ( 8, (1 << 0) ^ 0xff, False )

        return chars[c]

    def get_keyboard(self):
        rc = 255

        if self.kb_last_c == None:
            self.kb_last_c = self.getch(False)

            if self.kb_last_c == -1:
                self.kb_last_c = None

            else:
                lrc = self.find_char_row(self.kb_last_c)

                if lrc:
                    self.kb_row_nr, self.kb_row, self.kb_shift = lrc
                    print('lastc %c %s' % (self.kb_last_c, "{0:b}".format(self.kb_row)), file=sys.stderr)
                    print('keyb', lrc, file=sys.stderr)

                else:
                    self.kb_last_c = None

                self.kb_shift_scanned = False
                self.kb_char_scanned = False

        if (self.io[0xaa] & 15) == self.kb_row_nr:
            self.kb_char_scanned = True
            rc = self.kb_row

        if (self.io[0xaa] & 15) == 6:
            self.kb_shift_scanned = True

            if self.kb_shift:
                rc &= ~1

        if self.kb_shift_scanned and self.kb_char_scanned:
            self.kb_last_c = None
            self.kb_row_nr = None
            self.kb_row = None
            self.kb_shift = False

        if rc != 255:
            print('rc', rc, file=sys.stderr)

        return rc
