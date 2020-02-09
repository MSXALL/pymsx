# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import curses
import math
import sys
import threading
import time

from screen_kb import screen_kb

class screen_kb_dummy(screen_kb):
    def __init__(self, io):
        super(screen_kb_dummy, self).__init__(io)

    def init_kb(self):
        pass

    def init_screen(self):
        pass

    def stop2(self):
        pass

    def run(self):
        pass

    def get_keyboard(self):
        return 255
