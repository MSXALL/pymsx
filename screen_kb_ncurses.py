# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import curses
import math
import sys
import threading
import time

from screen_kb import screen_kb

class screen_kb_ncurses(screen_kb):
    def __init__(self, io):
        super(screen_kb_ncurses, self).__init__(io)

    def init_kb(self):
        pass

    def init_screen(self):
        stdscr = curses.initscr()
        curses.start_color()
        curses.use_default_colors()
        self.win = curses.newwin(26, 80, 0, 0)
        curses.cbreak(True)
        curses.noecho()
        self.win.nodelay(True)
        curses.nonl()

        try:
            for mfg in range(0, 16):
                for mbg in range(0, 16):
                    pair = mfg * 16 + mbg
                    if pair == 0:
                        continue

                    fg = self.find_color(mfg)
                    bg = self.find_color(mbg)

                    curses.init_pair(pair, fg, bg)
        except curses.error:
            pass

    # find msx color 'nr' in curses
    def find_color(self, nr):
        msxcolors = [ () ] * 16
        msxcolors[0] = (0, 0, 0)
        msxcolors[1] = (0, 0, 0)
        msxcolors[2] = (33, 200, 66)
        msxcolors[3] = (94, 220, 120)
        msxcolors[4] = (84, 85, 237)
        msxcolors[5] = (125, 118, 252)
        msxcolors[6] = (212, 82, 77)
        msxcolors[7] = (66, 235, 245)
        msxcolors[8] = (252, 85, 84)
        msxcolors[9] = (255, 121, 120)
        msxcolors[10] = (212, 193, 84)
        msxcolors[11] = (230, 206, 128)
        msxcolors[12] = (33, 176, 59)
        msxcolors[13] = (201, 91, 186)
        msxcolors[14] = (204, 204, 204)
        msxcolors[15] = (255, 255, 255)

        best = 4000000000
        chosen = None
        for cnr in range(0, curses.COLORS):
            nrgb = curses.color_content(cnr)

            diff = math.sqrt(math.pow(msxcolors[nr][0] * 1000 / 255 - nrgb[0], 2) + math.pow(msxcolors[nr][1] * 1000 / 255 - nrgb[1], 2) + math.pow(msxcolors[nr][2] * 1000 / 255 - nrgb[2], 2))
            if diff < best:
                best = diff
                chosen = cnr

        return chosen

    def stop2(self):
        curses.endwin()

    def run(self):
        while not self.stop_flag:
            with self.cv:
                while self.redraw == False and self.stop_flag == False:
                    c = self.win.getch()

                    if c != -1:
                        if c == 13 or c == 10:
                            print('MARKER', file=sys.stderr)

                        self.k_lock.acquire()
                        self.keyboard_queue.append(c)
                        self.k_lock.release()

                    self.cv.wait()

                self.redraw = False

            msg = self.debug_msg[0:79]

            # redraw
            vm = self.video_mode()
            if vm == 4:  # 40 x 24
                bg_map   = (self.registers[2] & 15) << 10
                bg_tiles = (self.registers[4] &  7) << 11

                fg = self.registers[7] >> 4
                bg = self.registers[7] & 15
                cp = curses.color_pair(fg * 16 + bg)
                self.win.attron(cp)

                for y in range(0, 24):
                    for x in range(0, 40):
                        c = self.ram[bg_map + y * 40 + x]
                        self.win.addch(y, x, c)

                self.win.attroff(cp)

            elif vm == 0:  # 32 x 24
                bg_map    = (self.registers[2] &  15) << 10
                bg_colors = (self.registers[3] & 128) <<  6
                bg_tiles  = (self.registers[4] &   4) << 11

                for y in range(0, 24):
                    for x in range(0, 32):
                        c = self.ram[bg_map + y * 32 + x]
                        col = self.ram[bg_colors + (c >> 3)]
                        fg = col >> 4
                        bg = col & 15
                        self.win.addch(y, x, c, curses.color_pair(fg * 16 + bg))

            else:
                msg = 'Unsupported resolution'

            self.debug_msg_lock.acquire()
            if self.debug_msg:
                self.win.addstr(25, 0, msg)
            self.debug_msg_lock.release()

            self.win.noutrefresh()
            curses.doupdate()
