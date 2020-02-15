# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

class screen_kb_dummy:
    def __init__(self, io):
        pass

    def interrupt(self):
        pass

    def IE0(self):
        pass

    def write_io(self, a, v):
        pass

    def read_io(self, a):
        return 0xff

    def debug(self, str_):
        pass

    def stop(self):
        pass

    def start(self):
        pass
