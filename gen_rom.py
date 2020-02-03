# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import sys
from pagetype import PageType

class gen_rom:
    def __init__(self, gen_rom_file, debug):
        print('Loading gen rom %s...' % gen_rom_file, file=sys.stderr)

        fh = open(gen_rom_file, 'rb')
        self.gen_rom = [ int(b) for b in fh.read() ]
        fh.close()

        self.debug = debug

    def get_signature(self):
        return (self.gen_rom, PageType.ROM, self)

    def write_mem(self, a, v):
        pass

    def read_mem(self, a):
        offset = a - 0x4000
        return self.gen_rom[offset]
